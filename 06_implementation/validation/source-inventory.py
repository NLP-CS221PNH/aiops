"""Read source preparation inventory; optionally write only this derivative receipt.

Usage from the pack root:
  python 06_implementation/validation/source-inventory.py
  python 06_implementation/validation/source-inventory.py --write-report

Standard library only. No acquisition, model execution, or source-pack writes.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = set()


def rows(rel):
    SOURCES.add(rel)
    path = ROOT / rel
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return (list(csv.DictReader(handle, delimiter="\t")) if path.suffix == ".tsv"
                else [json.loads(line) for line in handle if line.strip()])


def obj(rel):
    SOURCES.add(rel)
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def digest(rel):
    path = ROOT / rel
    return {"path": rel, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    split = rows("02_datasets/processed/split-map.tsv")
    observations = rows("02_datasets/processed/observations.jsonl")
    gold = rows("02_datasets/processed/labels/ground_truth.jsonl")
    inventory = rows("02_datasets/acquired/inventory.tsv")
    tasks = rows("03_collection_plan/annotation-kit/task-index.tsv")
    status = obj("03_collection_plan/annotation-kit/status.json")
    pilot = obj("05_research/retrieval-preview/pilot-pool-status.json")
    candidates = rows("05_research/retrieval-preview/candidate-diagnostics.jsonl")
    families = defaultdict(list)
    for row in split:
        families[row["scenario_family_id"]].append(row)
    split_counts = dict(sorted(Counter(r["split"] for r in split).items()))
    family_counts = dict(sorted(Counter(r[0]["split"] for r in families.values()).items()))
    ids = {r["incident_id"] for r in split}
    split_by_id = {r["incident_id"]: r for r in split}
    gold_by_family = defaultdict(set)
    repetitions = defaultdict(set)
    for row in gold:
        gold_by_family[row["scenario_family_id"]].add((row["root_cause_service"], row["fault"]))
        repetitions[row["scenario_family_id"]].add(row["repetition"])
    annotation_forms = {}
    grade_specs = {
        "03_collection_plan/annotation-kit/qrels-annotator-A.tsv": ["relevance_grade"],
        "03_collection_plan/annotation-kit/qrels-annotator-B.tsv": ["relevance_grade"],
        "03_collection_plan/annotation-kit/qrels-adjudication.tsv": ["annotator_A_grade", "annotator_B_grade", "adjudicated_grade"],
        "05_research/retrieval-preview/annotator-a.tsv": ["relevance_grade"],
        "05_research/retrieval-preview/annotator-b.tsv": ["relevance_grade"],
    }
    for rel, keys in grade_specs.items():
        form = rows(rel)
        annotation_forms[rel] = {
            "rows": len(form),
            "nonempty_grade_cells": sum(bool(row.get(key, "").strip()) for row in form for key in keys),
            "states": dict(Counter(row.get("review_state", row.get("annotation_state")) for row in form)),
        }
    references = rows("03_collection_plan/annotation-kit/reference-answers.tsv")
    judgments = sum(form["nonempty_grade_cells"] for form in annotation_forms.values())
    historical_docs = rows("03_collection_plan/knowledge-corpus-historical/documents.jsonl")
    historical_chunks = rows("03_collection_plan/knowledge-corpus-historical/chunks.jsonl")
    current_docs = rows("03_collection_plan/knowledge-corpus/documents.jsonl")
    current_chunks = rows("03_collection_plan/knowledge-corpus/chunks.jsonl")
    checks = {
        "90_unique_incidents": len(split) == len(ids) == 90,
        "observation_gold_split_ids_match": ids == {r["incident_id"] for r in observations} == {r["incident_id"] for r in gold} and len(observations) == len(gold) == 90,
        "54_18_18_split": split_counts == {"dev": 18, "test": 18, "train": 54},
        "30_families_with_3_repetitions": len(families) == len(gold_by_family) == 30 and all(len(r) == 3 for r in families.values()) and all(v == {1, 2, 3} for v in repetitions.values()),
        "families_do_not_cross_splits": all(len({r["split"] for r in group}) == 1 for group in families.values()),
        "family_is_service_fault_pair": all(len(v) == 1 for v in gold_by_family.values()) and len(set().union(*gold_by_family.values())) == 30 and all(split_by_id[r["incident_id"]]["scenario_family_id"] == r["scenario_family_id"] for r in gold),
        "6_test_families": family_counts.get("test") == 6,
        "90_annotation_task_rows": len(tasks) == len({r["incident_id"] for r in tasks}) == 90 and {r["incident_id"] for r in tasks} == ids,
        "zero_human_passage_judgments": judgments == 0 and status["human_judgments_completed"] == pilot["human_judgments_completed"] == 0,
        "reference_answers_blank": not any(r["reference_answer"].strip() for r in references),
        "20_train_seed_incidents_400_candidates": len(candidates) == 400 and len({r["incident_id"] for r in candidates}) == len(pilot["incident_ids"]) == 20 and {r["incident_id"] for r in candidates} == set(pilot["incident_ids"]) and all(split_by_id[i]["split"] == "train" for i in pilot["incident_ids"]),
        "seed_includes_all_18_train_families": len({split_by_id[i]["scenario_family_id"] for i in pilot["incident_ids"]}) == 18,
        "raw_inventory_360_files_90_incidents": len(inventory) == 360 and {r["incident_id"] for r in inventory} == ids,
        "inventory_paths_exist_and_sizes_match": all((ROOT / r["local_path"]).is_file() and (ROOT / r["local_path"]).stat().st_size == int(r["bytes"]) for r in inventory),
        "corpus_counts": (len(historical_docs), len(historical_chunks), len(current_docs), len(current_chunks)) == (74, 580, 73, 598),
        "historical_corpus_matches_seed_hash": hashlib.sha256((ROOT / pilot["corpus_path"]).read_bytes()).hexdigest() == pilot["corpus_hash"],
    }
    # Bind the reviewed contract snapshot; live plan checkboxes track completion.
    SOURCES.update(["START-HERE.md", "00_plan/project_proposal.md", "00_plan/experiments_and_evaluation.md", "00_plan/timeline_and_scope.md", "05_research/method-and-experiment-design.md", "05_research/experiment-proposal.json", "plans/reports/260913-independent-plans-contracts.md", "04_audit/data-runtime.json", "scripts/validate-research-pack.py", "scripts/check-handoff-files.py"])
    SOURCES.update("06_implementation/freezes/G0/plan-source/" + name for name in (
        "plan.md", "phase-01-start.md", "phase-02-build.md", "phase-03-validate-and-handoff.md"))
    report = {
        "schema_version": "source-inventory-v1", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": all(checks.values()), "checks": checks,
        "counts": {"incidents": len(ids), "families": len(families), "splits": split_counts,
                   "families_by_split": family_counts, "human_passage_judgments": judgments,
                   "raw_inventory_files": len(inventory), "raw_inventory_bytes": sum(int(r["bytes"]) for r in inventory),
                   "upstream_hash_verified_inventory_files": sum(r["upstream_hash_verified"].lower() == "true" for r in inventory),
                   "pilot_incidents": len(pilot["incident_ids"]), "pilot_candidates": len(candidates)},
        "split_versions": sorted({r["split_version"] for r in split}),
        "dataset_release_revisions": sorted({r["label_release_revision"] for r in gold}),
        "qrels_core": {"train": 20, "dev": 18, "test": 18, "total": 56,
                       "status": "planned_not_existing_human_qrels",
                       "source": "plans/reports/260913-independent-plans-contracts.md",
                       "note": "20 train seed IDs are observed; no final core selection or adjudicated qrels are claimed."},
        "annotation_forms": annotation_forms,
        "observations_contain_manager_fields": sorted({key for row in observations for key in ("split", "scenario_family_id") if key in row}),
        "sources": [digest(rel) for rel in sorted(SOURCES)],
        "limitations": ["Source inventory sizes are checked; all raw bytes were not rehashed in this lightweight scope audit.",
                        "Preparation observations include family/split: plan 02 must create an explicit inference allowlist export.",
                        "Historical document dates do not establish deployment applicability or evidence coverage.",
            "This inventory audit grants no model permission and creates no human review, annotation, acquisition, or experiment; G0 acceptance is checked separately.",
                        "Legacy validators write 04_audit and require blank judgments/NOT_RUN; they do not validate implementation results."],
    }
    if args.write_report:
        target = Path(__file__).with_suffix(".json")
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
