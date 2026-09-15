"""Acquire only files present in immutable pre-2024 commits. No forward filling."""
import importlib.util
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("acquire_knowledge", HERE / "acquire-knowledge.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.OUT = module.ROOT / "03_collection_plan" / "knowledge-corpus-historical"
module.RAW = module.OUT / "raw" / "source-snapshots"
module.SNAPSHOT_ID = "cs221-knowledge-pre2024-v1"
module.DOCUMENT_PREFIX = "KBH"
module.EXPERIMENT_POLICY = "pre2024_snapshot_candidate_requires_per_incident_cutoff_and_deployment_review"
HISTORICAL = {
    "D057": ("80bea9bfd97bec107361d4663e207aa8d3f312c6", "2023-12-28T18:03:44Z"),
    "D058": ("7e631d0318dc279cb2d31231d8823360e61e9304", "2023-12-31T15:40:05Z"),
    "D059": ("f8061f3e9b3337d90107aa2f10a0111f3f6dc86f", "2023-09-07T14:21:57Z"),
}


def main():
    path_sets = {}
    for sid, (revision, date) in HISTORICAL.items():
        source = module.REPOS[sid]
        source["revision"] = revision
        source["snapshot_commit_time"] = date
        data, _ = module.acquire(f'https://api.github.com/repos/{source["repo"]}/git/trees/{revision}?recursive=1', module.RAW / sid / "repository-tree.json")
        tree = json.loads(data)
        if tree.get("truncated"):
            raise ValueError(f"Historical tree truncated: {sid}")
        path_sets[sid] = {row["path"] for row in tree["tree"] if row["type"] == "blob"}
    module.OB_DOCS = [path for path in module.OB_DOCS if path in path_sets["D057"]]
    module.K8S_DOCS = [path for path in module.K8S_DOCS if path in path_sets["D058"]]
    module.RUNBOOK_NAMES &= {Path(path).stem for path in path_sets["D059"] if path.startswith("content/runbooks/")}
    module.main()
    current = [json.loads(line) for line in (module.ROOT / "03_collection_plan" / "knowledge-corpus" / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    historical = [json.loads(line) for line in (module.OUT / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    current_paths = {(doc["source_id"], doc["source_path"]): doc for doc in current}
    historical_paths = {(doc["source_id"], doc["source_path"]): doc for doc in historical}
    diff = {
        "current_snapshot_id": "cs221-knowledge-2026-09-12-v1", "historical_snapshot_id": module.SNAPSHOT_ID,
        "policy": "only_files_present_at_historical_commit_no_forward_filling",
        "historical_file_count": len(historical), "current_file_count": len(current),
        "missing_from_historical": [{"source_id": sid, "source_path": path} for sid, path in sorted(current_paths.keys() - historical_paths.keys())],
        "historical_only": [{"source_id": sid, "source_path": path} for sid, path in sorted(historical_paths.keys() - current_paths.keys())],
        "same_path_same_text_count": sum(historical_paths[key]["text_hash"] == current_paths[key]["text_hash"] for key in current_paths.keys() & historical_paths.keys()),
        "same_path_changed_text_count": sum(historical_paths[key]["text_hash"] != current_paths[key]["text_hash"] for key in current_paths.keys() & historical_paths.keys()),
        "all_historical_snapshot_times_before_2024": all(doc["available_at"] < "2024-01-01T00:00:00Z" for doc in historical),
        "per_incident_cutoff_check": "pending_observation_records", "deployment_version_mapping": "unverified",
    }
    observation_path = module.ROOT / "02_datasets" / "processed" / "observations.jsonl"
    if observation_path.exists():
        observations = [json.loads(line) for line in observation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        earliest = min((parse(row["observation_start"]) for row in observations), default=None)
        diff["per_incident_cutoff_check"] = "passed_before_all_observation_starts" if earliest and all(parse(doc["available_at"]) <= earliest for doc in historical) else "failed_or_no_observations"
        diff["observation_count_checked"] = len(observations)
        diff["earliest_observation_start"] = earliest.isoformat() if earliest else None
        diff["cutoff_check_limit"] = "time_eligibility_only_deployment_and_evidence_relevance_unverified"
    (module.OUT / "comparison-with-current.json").write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diff, indent=2))


if __name__ == "__main__":
    main()
