"""Load LLM-judge qrels for forensic/control scoring. Never treat them as human gold."""
from __future__ import annotations

import csv
from pathlib import Path

EXPERIMENTAL_PROVENANCE = {"llm_judge_adjudicated", "llm_lexical_proxy"}
HUMAN_GOLD = "human-double-adjudicated"


def load_experimental_qrels(path: Path) -> tuple[dict[str, dict[str, int]], str]:
    files = [path] if path.is_file() else sorted(path.glob("*.tsv")) if path.is_dir() else []
    if not files:
        raise SystemExit("qrels_missing")
    tables: dict[str, dict[str, int]] = {}
    seen: set[str] = set()
    for file_path in files:
        with file_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            required = {"provenance", "annotator_id", "adjudication_state", "annotation_version"}
            if not required.issubset(reader.fieldnames or []):
                raise SystemExit("qrels_provenance_missing")
            for row in reader:
                provenance = row["provenance"].strip()
                if provenance == HUMAN_GOLD:
                    raise SystemExit("use_human_gold_loader")
                if provenance not in EXPERIMENTAL_PROVENANCE:
                    raise SystemExit("qrels_unknown_provenance")
                seen.add(provenance)
                if not all(row[key].strip() for key in required):
                    raise SystemExit("qrels_provenance_incomplete")
                query = row.get("incident_id") or row.get("qid") or row.get("query_id")
                doc = row.get("chunk_id") or row.get("doc_id") or row.get("document_id")
                grade = row.get("relevance_grade", row.get("relevance", row.get("rel", "")))
                if grade == "":
                    continue
                if grade not in {"0", "1", "2"}:
                    raise SystemExit("qrels_invalid_grade")
                if not query or not doc:
                    raise SystemExit("qrels_missing_columns")
                tables.setdefault(query, {})[doc] = int(grade)
    if not tables:
        raise SystemExit("qrels_empty")
    if len(seen) != 1:
        raise SystemExit("qrels_mixed_provenance")
    return tables, next(iter(seen))


def load_answerability(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    labeled: dict[str, str] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            incident = row.get("incident_id") or row.get("query_id")
            label = (row.get("answerability") or "").strip()
            if incident and label:
                labeled[incident] = label
    return labeled
