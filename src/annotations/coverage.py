"""Top-k judged coverage. Unjudged is never grade 0; incomplete coverage fails closed."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def load_qrels_grades(path: Path) -> dict[str, dict[str, str]]:
    tables: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            query = row.get("incident_id") or row.get("qid")
            doc = row.get("chunk_id") or row.get("doc_id")
            grade = (row.get("relevance_grade") or row.get("grade") or "").strip()
            if not query or not doc:
                continue
            tables.setdefault(query, {})[doc] = grade
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
        for row in reader:
            query = row.get("incident_id") or row.get("qid")
            doc = row.get("chunk_id") or row.get("doc_id")
            rankings.setdefault(query, []).append(doc)
    return rankings


def coverage_at_k(rankings: dict[str, list[str]], qrels: dict[str, dict[str, str]], k: int) -> dict:
    judged = 0
    returned = 0
    incomplete = []
    for incident, ranking in rankings.items():
        top = list(ranking)[:k]
        returned += len(top)
        judged_map = qrels.get(incident) or {}
        for doc in top:
            grade = judged_map.get(doc, "")
            if grade in {"0", "1", "2"}:
                judged += 1
            else:
                incomplete.append({"incident_id": incident, "chunk_id": doc, "k": k})
    return {
        f"top{k}_judged": judged,
        f"top{k}_returned": returned,
        f"top{k}_coverage_ratio": (judged / returned) if returned else None,
        "incomplete": incomplete,
    }


def check_coverage(runs_paths: list[Path], qrels_path: Path, ks: list[int]) -> dict:
    if not qrels_path.is_file():
        raise FileNotFoundError(qrels_path)
    qrels = load_qrels_grades(qrels_path)
    rankings: dict[str, list[str]] = {}
    for path in runs_paths:
        rankings.update(load_rankings(path))
    report: dict = {"schema_version": "cs221-coverage-v1", "ks": ks, "complete": True, "incomplete": []}
    for k in ks:
        part = coverage_at_k(rankings, qrels, k)
        report["complete"] = report["complete"] and not part["incomplete"]
        report.update({key: value for key, value in part.items() if key != "incomplete"})
        report["incomplete"].extend(part["incomplete"])
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check evaluation coverage of final runs against qrels.")
    parser.add_argument("--runs", nargs="+", required=True, help="Paths to frozen runs")
    parser.add_argument("--qrels", required=True, help="Path to qrels file")
    parser.add_argument("--required-k", default="5,10", help="Required k depths, e.g., 5,10")
    args = parser.parse_args(argv)
    ks = [int(item.strip()) for item in str(args.required_k).split(",") if item.strip()]
    report = check_coverage([Path(item) for item in args.runs], Path(args.qrels), ks)
    print(json.dumps(report))
    return 0 if report["complete"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
