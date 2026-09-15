"""Prepare blank annotation forms using observations only; never manufacture gold.

Existing non-empty annotation fields are protected from overwrite.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "03_collection_plan" / "knowledge-corpus"
OUT = ROOT / "03_collection_plan" / "annotation-kit"
JUDGMENT_FIELDS = {"relevance_grade", "evidence_role", "reviewer_notes", "adjudicated_grade", "adjudication_rationale", "answerability", "reference_answer", "reviewed_compatibility", "reviewer_id", "reviewed_at", "supported_claim", "claim_label", "judgment", "adjudicated_answerability", "span_start", "span_end", "version_scope_check", "required_claims", "missing_evidence", "sufficient_evidence_ids", "annotator_A_grade", "annotator_B_grade", "annotator_A_answerability", "annotator_B_answerability", "evidence_ids", "allowed_abstention", "response_id", "claim_id", "claim_text", "citation_ids", "task_correctness", "citation_correctness", "symptom_family"}
PENDING_WRITES = []


def write_blank(name, fields, rows):
    PENDING_WRITES.append((OUT / name, fields, rows))


def flush_blanks():
    """Preflight every destination before changing any file in the batch."""
    for path, fields, _ in PENDING_WRITES:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter="\t")
            old_fields = reader.fieldnames or []
            old = list(reader)
        if set(old_fields) - set(fields):
            raise RuntimeError(f"Refusing to discard unrecognized columns in {path}")
        if any((row.get(field) or "").strip() for row in old for field in JUDGMENT_FIELDS):
            raise RuntimeError(f"Refusing to overwrite human judgments or partial annotation work in {path}")
        if any(row.get("review_state", "") not in ("", "needs_human_review") for row in old):
            raise RuntimeError(f"Refusing to overwrite changed review states in {path}")
    for path, fields, rows in PENDING_WRITES:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    PENDING_WRITES.clear()


def main():
    PENDING_WRITES.clear()
    OUT.mkdir(parents=True, exist_ok=True)
    docs = [json.loads(line) for line in (KB / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    historical_path = KB.with_name("knowledge-corpus-historical") / "documents.jsonl"
    historical_docs = [json.loads(line) for line in historical_path.read_text(encoding="utf-8").splitlines()] if historical_path.exists() else []
    active_docs = historical_docs or docs
    snapshot_id = "cs221-knowledge-pre2024-v1" if historical_docs else "cs221-knowledge-2026-09-12-v1"
    observation_path = ROOT / "02_datasets" / "processed" / "observations.jsonl"
    observations = [json.loads(line) for line in observation_path.read_text(encoding="utf-8").splitlines()] if observation_path.exists() else []
    split_path = ROOT / "02_datasets" / "processed" / "split-map.tsv"
    split_rows = list(csv.DictReader(split_path.open(encoding="utf-8", newline=""), delimiter="\t")) if split_path.exists() else []
    task_inputs = observations if observations else split_rows
    tasks = []
    for observation in task_inputs:
        incident = observation["incident_id"]
        tasks.append({"task_id": "ANN-" + hashlib.sha256(incident.encode()).hexdigest()[:12], "query_id": observation.get("query_id", incident), "incident_id": incident, "observation_record_source": "02_datasets/processed/observations.jsonl" if observations else "pending_observations_ids_from_split-map.tsv", "knowledge_snapshot_id": snapshot_id, "candidate_pool_state": "not_yet_pooled_bm25_dense_hybrid", "review_state": "needs_human_review", "annotation_version": "human-v1-pending"})
    tasks.sort(key=lambda row: row["task_id"])
    write_blank("task-index.tsv", ["task_id", "query_id", "incident_id", "observation_record_source", "knowledge_snapshot_id", "candidate_pool_state", "review_state", "annotation_version"], tasks)
    qfields = ["task_id", "query_id", "incident_id", "document_id", "chunk_id", "span_start", "span_end", "relevance_grade", "evidence_role", "supported_claim", "version_scope_check", "reviewer_id", "reviewed_at", "reviewer_notes", "review_state", "annotation_version"]
    for name in ["qrels-annotator-A.tsv", "qrels-annotator-B.tsv"]:
        write_blank(name, qfields, tasks)
    for name in ["answerability-annotator-A.tsv", "answerability-annotator-B.tsv"]:
        write_blank(name, ["task_id", "query_id", "incident_id", "answerability", "required_claims", "missing_evidence", "sufficient_evidence_ids", "reviewer_id", "reviewed_at", "reviewer_notes", "review_state", "annotation_version"], tasks)
    write_blank("qrels-adjudication.tsv", ["task_id", "query_id", "incident_id", "document_id", "chunk_id", "annotator_A_grade", "annotator_B_grade", "adjudicated_grade", "evidence_role", "adjudication_rationale", "reviewer_id", "reviewed_at", "review_state", "annotation_version"], tasks)
    write_blank("answerability-adjudication.tsv", ["task_id", "query_id", "incident_id", "annotator_A_answerability", "annotator_B_answerability", "adjudicated_answerability", "adjudication_rationale", "reviewer_id", "reviewed_at", "review_state", "annotation_version"], tasks)
    write_blank("reference-answers.tsv", ["task_id", "query_id", "incident_id", "reference_answer", "required_claims", "evidence_ids", "allowed_abstention", "reviewer_id", "reviewed_at", "review_state", "annotation_version"], tasks)
    write_blank("claim-evaluation.tsv", ["response_id", "query_id", "incident_id", "claim_id", "claim_text", "citation_ids", "claim_label", "task_correctness", "citation_correctness", "reviewer_id", "reviewed_at", "reviewer_notes", "review_state"], [])
    applicability_fields = ["document_id", "source_id", "title", "source_url", "version_scope", "available_at", "reviewed_compatibility", "symptom_family", "allowed_experiment_mode", "reviewer_id", "reviewed_at", "reviewer_notes", "review_state"]
    current_rows = [{**doc, "allowed_experiment_mode": "offline_assistance_only_pending_review", "review_state": "needs_human_review"} for doc in docs]
    historical_rows = [{**doc, "allowed_experiment_mode": "historical_candidate_pending_cutoff_and_deployment_review", "review_state": "needs_human_review"} for doc in historical_docs]
    write_blank("document-applicability-current.tsv", applicability_fields, current_rows)
    if historical_docs:
        write_blank("document-applicability-historical.tsv", applicability_fields, historical_rows)
    write_blank("document-applicability.tsv", applicability_fields, historical_rows or current_rows)
    write_blank("candidate-pool-template.tsv", ["query_id", "document_id", "chunk_id", "retriever", "rank", "score", "pool_version", "knowledge_snapshot_hash"], [])
    flush_blanks()
    status = {"schema_version": "annotation-kit-v1", "observation_records_found": len(observations), "task_rows": len(tasks), "active_knowledge_snapshot_id": snapshot_id, "document_applicability_rows": len(active_docs), "current_document_applicability_rows": len(docs), "historical_document_applicability_rows": len(historical_docs), "human_judgments_completed": 0, "gold_qrels_available": False, "reference_answers_available": False, "candidate_pool_complete": False, "status": "blank_forms_ready_human_annotation_required"}
    (OUT / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
