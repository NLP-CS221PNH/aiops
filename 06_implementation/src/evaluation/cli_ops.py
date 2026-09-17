"""Read-only evaluation commands and fail-closed handoff validation."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

from src.evaluation.metrics import calculate_mrr, calculate_ndcg, calculate_recall

IMPL = Path(__file__).resolve().parents[2]
ROOT = IMPL.parent
PLACEHOLDER = {"handoff": "ready"}


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_dirty() -> bool:
    return bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())


def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    files = [path] if path.is_file() else sorted(path.glob("*.tsv")) if path.is_dir() else []
    if not files:
        raise SystemExit("qrels_missing")
    tables: dict[str, dict[str, int]] = {}
    for file_path in files:
        with file_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            required = {"provenance", "annotator_id", "adjudication_state", "annotation_version"}
            if not required.issubset(reader.fieldnames or []):
                raise SystemExit("qrels_provenance_missing")
            for row in reader:
                if row["provenance"] != "human-double-adjudicated":
                    raise SystemExit("qrels_not_human_gold")
                if not all(row[key].strip() for key in required):
                    raise SystemExit("qrels_provenance_incomplete")
                query = row.get("incident_id") or row.get("qid") or row.get("query_id")
                doc = row.get("chunk_id") or row.get("doc_id") or row.get("document_id")
                grade = row.get("relevance_grade", row.get("relevance", row.get("rel", "")))
                if grade == "":
                    continue  # Unjudged is never converted to grade zero.
                if grade not in {"0", "1", "2"}:
                    raise SystemExit("qrels_invalid_grade")
                rel = int(grade)
                if not query or not doc:
                    raise SystemExit("qrels_missing_columns")
                tables.setdefault(query, {})[doc] = rel
    if not tables:
        raise SystemExit("qrels_empty")
    return tables


def load_rankings(path: Path) -> dict[str, list[str]]:
    rankings: dict[str, list[str]] = {}
    if path.suffix == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            query = row.get("incident_id") or row.get("qid")
            order = row.get("ranking") or row.get("chunk_ids") or []
            rankings[query] = list(order)
        return rankings
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        ranked = []
        for row in reader:
            ranked.append(row)
        for row in ranked:
            query = row.get("incident_id") or row.get("qid")
            doc = row.get("chunk_id") or row.get("doc_id")
            rankings.setdefault(query, []).append(doc)
    return rankings


def _nonzero_hash(value) -> bool:
    return bool(value) and set(str(value)) != {"0"}


def _hash_qrels(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    files = sorted(path.glob("*.tsv")) if path.is_dir() else []
    if not files:
        raise SystemExit("qrels_missing")
    digest = hashlib.sha256()
    for file_path in files:
        digest.update(file_path.read_bytes())
    return digest.hexdigest()


def verify_freezes(system_path: str, qrels_path: str) -> None:
    load_qrels(Path(qrels_path))
    system = Path(system_path)
    if not system.is_file():
        raise SystemExit("freeze_inputs_missing")
    invalidation_path = IMPL / "freezes" / "F2.provenance.json"
    if invalidation_path.is_file():
        invalidation = json.loads(invalidation_path.read_text(encoding="utf-8"))
        system_hash = hashlib.sha256(system.read_bytes()).hexdigest()
        for gate in ("f1", "f2"):
            if (invalidation.get(f"{gate}_evaluation_eligible") is False
                    and invalidation.get(f"{gate}_sha256") == system_hash):
                raise SystemExit("historical_freeze_invalidated")
    payload = json.loads(system.read_text(encoding="utf-8"))
    if payload == PLACEHOLDER or payload.get("hashes", {}).get("retriever") == "fixed_hash_retriever":
        raise SystemExit("placeholder_freeze")
    bound = 0
    declared_qrels = payload.get("qrels_hash")
    if _nonzero_hash(declared_qrels):
        qrels = Path(qrels_path)
        if not qrels.exists():
            raise SystemExit("qrels_missing")
        if _hash_qrels(qrels) != declared_qrels:
            raise SystemExit("freeze_hash_mismatch")
        bound += 1
    input_hash = payload.get("input_manifest_hash")
    if _nonzero_hash(input_hash):
        input_path = IMPL / "data" / "inference" / "input-manifest.json"
        if not input_path.is_file() or sha256_file(input_path) != input_hash:
            raise SystemExit("input_manifest_mismatch")
        bound += 1
    corpus_hash = payload.get("corpus_manifest_hash")
    if _nonzero_hash(corpus_hash):
        corpus_path = IMPL / "data" / "knowledge" / "corpus-manifest.json"
        if not corpus_path.is_file() or sha256_file(corpus_path) != corpus_hash:
            raise SystemExit("corpus_manifest_mismatch")
        bound += 1
    if bound == 0:
        raise SystemExit("freeze_missing_bind")
    print(json.dumps({
        "status": "passed",
        "system_sha256": sha256_file(system),
        "bindings": bound,
    }))


def score_runs(system_path: str, qrels_path: str, runs_path: str, output_path: str) -> None:
    output = Path(output_path)
    if output.resolve() == (IMPL / "results" / "per-incident.tsv").resolve():
        raise SystemExit("refusing_to_overwrite_canonical_results")
    qrels = load_qrels(Path(qrels_path))
    verify_freezes(system_path, qrels_path)
    rankings = load_rankings(Path(runs_path))
    if not Path(system_path).is_file():
        raise SystemExit("system_freeze_missing")
    rows = []
    for incident_id, ranking in rankings.items():
        judged = qrels.get(incident_id)
        if judged is None:
            raise SystemExit(f"missing_qrels:{incident_id}")
        ndcg = calculate_ndcg(ranking, judged, k=5)
        mrr = calculate_mrr(ranking, judged, k=10)
        recall = calculate_recall(ranking, judged, k=20)
        for metric, result in (("ndcg_5", ndcg), ("mrr_10", mrr), ("recall_20", recall)):
            rows.append({
                "metric": metric,
                "condition": "run",
                "incident_id": incident_id,
                "split": "test",
                "run_id": Path(runs_path).name,
                "qrels_version": _hash_qrels(Path(qrels_path)),
                "qrels_provenance": "human-double-adjudicated",
                "eligible": result.status.name.lower() == "eligible",
                "value": "" if result.value is None else result.value,
                "undefined_reason": result.reason or "",
            })
    if not rows:
        raise SystemExit("no_scores")
    output = Path(output_path)
    if output.resolve() == (IMPL / "results" / "per-incident.tsv").resolve():
        raise SystemExit("refusing_to_overwrite_canonical_results")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"status": "scored", "rows": len(rows), "output": str(output)}))


def analyze(results_path: str, group: str, output_path: str) -> None:
    path = Path(results_path)
    if not path.is_file():
        raise SystemExit("results_missing")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or group not in rows[0]:
        raise SystemExit("analyze_group_missing")
    buckets: dict[str, list[float]] = {}
    for row in rows:
        if str(row.get("eligible")).lower() != "true":
            continue
        try:
            value = float(row.get("value") or "")
        except ValueError:
            continue
        buckets.setdefault(row[group], []).append(value)
    if not buckets:
        raise SystemExit("analyze_empty")
    output = Path(output_path)
    if output.resolve() == (IMPL / "results" / "family-comparison.tsv").resolve():
        raise SystemExit("refusing_to_overwrite_canonical_results")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[group, "n", "mean"], delimiter="\t")
        writer.writeheader()
        for key, values in sorted(buckets.items()):
            writer.writerow({group: key, "n": len(values), "mean": sum(values) / len(values)})
    print(json.dumps({"status": "analyzed", "groups": len(buckets), "output": str(output)}))


def validate_handoff(manifest_path: str) -> None:
    path = Path(manifest_path)
    if not path.is_file():
        raise SystemExit("manifest_missing")
    before = (path.stat().st_mtime_ns, path.stat().st_size, sha256_file(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload == PLACEHOLDER or payload.get("handoff") == "ready" and "artifacts" not in payload:
        raise SystemExit("placeholder_manifest")
    revision = git_head()
    recorded = payload.get("code_revision")
    if not recorded or recorded in {"rel-v1.0.0", "placeholder"}:
        raise SystemExit("unresolved_revision")
    if recorded != revision:
        raise SystemExit("revision_mismatch")
    artifacts = payload.get("artifacts") or []
    if not artifacts:
        raise SystemExit("artifacts_missing")
    for item in artifacts:
        rel = item.get("path")
        expected = item.get("sha256")
        license_ref = item.get("license_ref")
        if not rel or not expected or not license_ref:
            raise SystemExit("artifact_incomplete")
        file_path = IMPL / rel
        if not file_path.is_file():
            raise SystemExit(f"artifact_missing:{rel}")
        if sha256_file(file_path) != expected:
            raise SystemExit(f"artifact_mismatch:{rel}")
    after = (path.stat().st_mtime_ns, path.stat().st_size, sha256_file(path))
    if after != before:
        raise SystemExit("validator_mutated_manifest")
    print(json.dumps({"status": "passed", "artifacts": len(artifacts), "code_revision": revision}))
