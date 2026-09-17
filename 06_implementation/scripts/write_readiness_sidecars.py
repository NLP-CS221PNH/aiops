"""Deterministic readiness metadata; never judge, index, or change freeze bytes."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
ROOT = IMPL.parent
PROVENANCE_COLUMNS = ["provenance", "annotator_id", "adjudication_state", "annotation_version"]
CANDIDATE_COLUMNS = ["mapping_id", "incident_id", "document_id", "chunk_id", "mapping_layer",
                     "mapping_basis", "source_id", "service_scope", "symptom_family",
                     "version_compatibility", "is_qrel", "relevance_grade", "evidence_role",
                     "review_state", "annotation_version"]
BASE_SYMPTOM_FAMILIES = {"application_architecture_or_rpc_contract", "general_operational_reference"}
GENERIC_SERVICE_SCOPES = {"application_wide", "platform_generic"}
METRIC_SYMPTOM_HINTS = (
    ("cpu", "cpu_pressure_or_throttling"),
    ("mem", "memory_pressure_or_oom"),
    ("disk", "storage_or_filesystem_pressure"),
    ("latency", "network_dns_or_service_unreachable"),
    ("socket", "network_dns_or_service_unreachable"),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def symptom_families(observation):
    metric_names = " ".join(observation["metric_summary_ids"]).lower()
    families = set(BASE_SYMPTOM_FAMILIES)
    families.update(family for token, family in METRIC_SYMPTOM_HINTS if token in metric_names)
    return families


def candidate_row(incident_id, hint, doc):
    row = {key: "" for key in CANDIDATE_COLUMNS}
    row.update(mapping_id=f"candidate-{incident_id}-{hint['mapping_id']}", incident_id=incident_id,
               document_id=doc["document_id"], mapping_layer="incident_candidate",
               mapping_basis="observed_inventory_metric_hint_title_candidate_not_evidence",
               source_id=doc["source_id"], service_scope=hint["service_scope"],
               symptom_family=hint["symptom_family"], version_compatibility=doc["version_compatibility"],
               is_qrel="false", review_state="needs_human_review", annotation_version="coverage-candidate-v1")
    return row


def pilot_candidates(ids, observations, documents, hints):
    """Intersect historical hints with observed services and metric names, cap at 40."""
    docs = {row["original_document_id"]: row for row in documents}
    result = []
    for incident_id in ids:
        observation = observations[incident_id]
        services = set(observation["service_inventory"])
        families = symptom_families(observation)
        eligible = []
        for hint in hints:
            doc = docs.get(hint["document_id"])
            if not doc or not doc["candidate_eligible"]:
                continue
            if hint["service_scope"] not in services | GENERIC_SERVICE_SCOPES:
                continue
            if hint["symptom_family"] not in families:
                continue
            title_hits = sum(service in doc["title"].lower() for service in services)
            eligible.append((-title_hits, hint["mapping_id"], hint, doc))
        seen = set()
        for _, _, hint, doc in sorted(eligible):
            if doc["document_id"] in seen:
                continue
            seen.add(doc["document_id"])
            result.append(candidate_row(incident_id, hint, doc))
            if len(seen) == 40:
                break
    return result


def load_proxy_qrels(sidecar):
    payloads = []
    for split in ("train", "dev", "test"):
        path = IMPL / f"annotations/qrels/{split}/qrels.tsv"
        record = sidecar["qrels_files"][split]
        if digest(path) != record["sha256"]:
            raise ValueError(f"QRELS_CHANGED:{split}")
        fields, rows = read_tsv(path)
        if any(row.get("provenance", "llm_lexical_proxy") != "llm_lexical_proxy" for row in rows):
            raise ValueError("refusing to relabel non-proxy judgments")
        payloads.append((path, record, fields, rows))
    return payloads


def stamp_proxy_qrels(payloads):
    for path, record, fields, rows in payloads:
        record.setdefault("historical_sha256", record["sha256"])
        for key in PROVENANCE_COLUMNS:
            if key not in fields:
                fields.append(key)
        for row in rows:
            row.update(provenance="llm_lexical_proxy", annotator_id="lexical-personas-A+B",
                       adjudication_state="automated_proxy", annotation_version="historical-lexical-proxy-v1")
        write_tsv(path, fields, rows)
        record["sha256"] = digest(path)


def sample_train_ids(splits):
    train_ids = sorted(row["incident_id"] for row in splits if row["split"] == "train")
    if len(train_ids) != 54 or len(set(train_ids)) != 54:
        raise ValueError("TRAIN_POPULATION")
    rng = random.Random(221)
    ids = rng.sample(train_ids, 6)
    rng.shuffle(ids)
    return ids


def main():
    # Only migrate the historical dump identified by the existing forensic receipt.
    sidecar_path = IMPL / "freezes/F2.provenance.json"
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    qrels_payloads = load_proxy_qrels(sidecar)

    split_path = ROOT / "02_datasets/processed/split-map.tsv"
    private_path = IMPL / "data/private/split-map.tsv"
    _, splits = read_tsv(split_path)
    if private_path.exists() and read_tsv(private_path) != read_tsv(split_path):
        raise ValueError("SPLIT_MAP_DRIFT")
    ids = sample_train_ids(splits)
    observations_path = IMPL / "data/inference/observations.jsonl"
    documents_path = IMPL / "data/knowledge/documents.jsonl"
    hints_path = ROOT / "03_collection_plan/knowledge-corpus-historical/proposed-mappings.jsonl"
    observations = {row["incident_id"]: row for row in read_jsonl(observations_path)}
    hints = read_jsonl(hints_path)
    if len(hints) != 83:
        raise ValueError("HISTORICAL_HINT_COUNT")
    candidates = pilot_candidates(ids, observations, read_jsonl(documents_path), hints)
    pilot = IMPL / "annotations/coverage-pilot"
    judgments = pilot / "judgments.tsv"
    if judgments.exists() and read_tsv(judgments)[1]:
        raise ValueError("refusing to overwrite pilot with existing judgments")

    stamp_proxy_qrels(qrels_payloads)
    sidecar.update(current_qrels_hash=sidecar["qrels_files"]["test"]["sha256"],
                   f1_sha256=digest(IMPL / "freezes/F1.json"), f1_evaluation_eligible=False,
                   f2_evaluation_eligible=False,
                   invalidation_reason="empty released whitelist and pool-circular lexical proxy judgments")
    sidecar["authoritative_note"] = ("F1/F2 bytes are historical and invalid for evaluation. qrels_hash is the "
                                     "historical F2 binding; current_qrels_hash binds the provenance-stamped test dump.")
    write_json(sidecar_path, sidecar)

    pilot.mkdir(parents=True, exist_ok=True)
    write_tsv(pilot / "candidate-ids.tsv", ["incident_id"], [{"incident_id": value} for value in ids])
    candidate_path = ROOT / "03_collection_plan/annotation-kit/incident-document-candidates.tsv"
    write_tsv(candidate_path, CANDIDATE_COLUMNS, candidates)
    fields = ["incident_id", "chunk_id", "document_id", "relevance_grade", "evidence_role", "answerability",
              "grade2_document_count", "grade2_chunk_count", "missing_evidence_note",
              *PROVENANCE_COLUMNS, "pool_construction", "review_state"]
    write_tsv(judgments, fields, [])
    write_json(pilot / "manifest.json", {
        "schema_version": "coverage-pilot-candidates-v1", "seed": 221, "population": 54, "sample_size": 6,
        "sampling": "Random(221).sample(sorted(train_ids), 6), then shuffle with the same RNG",
        "coverage": "unmeasured_no_reviewer", "coverage_rate": None, "human_judgments": 0,
        "pool_construction": "symptom_hint_capped_40", "candidate_count": len(candidates),
        "candidate_counts": {value: sum(row["incident_id"] == value for row in candidates) for value in ids},
        "input_hashes": {str(p.relative_to(ROOT)): digest(p) for p in
                         (split_path, observations_path, documents_path, hints_path)},
        "candidate_sha256": digest(candidate_path), "candidate_ids_sha256": digest(pilot / "candidate-ids.tsv")})

    result_path = IMPL / "results/per-incident.tsv"
    fields, rows = read_tsv(result_path)
    if "qrels_provenance" not in fields:
        fields.append("qrels_provenance")
    for row in rows:
        row.update(qrels_provenance="llm_lexical_proxy", eligible="false",
                   undefined_reason="historical_synthetic_output_not_evaluation_evidence")
    write_tsv(result_path, fields, rows)
    write_json(IMPL / "results/per-incident.provenance.json", {
        "qrels_version": "06.F2-v1", "qrels_provenance": "llm_lexical_proxy",
        "headline_ndcg_eligible": False, "file": str(result_path.relative_to(ROOT)),
        "sha256": digest(result_path), "rows": len(rows)})
    print(json.dumps({"pilot_incidents": 6, "candidate_count": len(candidates), "coverage": "unmeasured_no_reviewer"}))


if __name__ == "__main__":
    main()
