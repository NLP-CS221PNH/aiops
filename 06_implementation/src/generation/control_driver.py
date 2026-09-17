"""Emit G-oracle / G-random contexts without changing the GH generation path."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.generation.provider import check_permissions, generate_response, load_config
from src.evaluation.controls import pack_oracle, pack_random

MOCK_MARKERS = ("mock logic", '"svc_a"')


def _looks_like_mock(raw: str, metadata: Mapping[str, Any]) -> bool:
    blob = raw or ""
    return any(marker in blob for marker in MOCK_MARKERS) or metadata.get("mock") is True


def generation_allowed(config: Mapping[str, Any]) -> bool:
    return bool(check_permissions(dict(config))) and config.get("approved_cap_usd") is not None


def run_control_generation(
    packed: Mapping[str, Any],
    incident_id: str,
    config_path: str = "configs/generation.yaml",
) -> dict[str, Any]:
    config = load_config(config_path)
    record = dict(packed)
    if not generation_allowed(config):
        record["generation_status"] = "NOT_RUN"
        record["generation_reason"] = "permission_or_cap_pending"
        return record
    raw, metadata = generate_response("control prompt", {"incident_id": incident_id}, config)
    if _looks_like_mock(raw, metadata):
        raise SystemExit("refusing_mock_as_result")
    record["generation_status"] = metadata.get("status", "NOT_RUN")
    record["generation_error"] = metadata.get("error")
    return record


def write_control_receipts(
    out_dir: Path,
    incidents: Sequence[str],
    qrels: Mapping[str, Mapping[str, int]],
    corpus_ids: Sequence[str],
    seed: int,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for incident_id in incidents:
        judged = qrels.get(incident_id, {})
        oracle = pack_oracle(judged)
        random_pack = pack_random(judged, corpus_ids, seed=seed)
        oracle_run = run_control_generation(oracle, incident_id)
        random_run = run_control_generation(random_pack, incident_id)
        rows.append({"incident_id": incident_id, "G-oracle": oracle_run, "G-random": random_run})
    path = out_dir / "control-contexts.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {"path": str(path), "n": len(rows), "generation_status": "NOT_RUN"}
