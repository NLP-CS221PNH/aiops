"""Run local generation over packed R2 observations. No fixture prompts."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import List, Mapping

from src.data.common import read_json
from src.generation.context_builder import WordTokenizer, compute_hash, pack_context
from src.generation.prompt_builder import build_messages, request_fingerprint
from src.generation.provider import generate_response, load_config
from src.generation.schemas import RunRecord
from src.generation.validator import validate_response
from src.representations import load_config as load_representation_config
from src.representations import render_representation, select_evidence
from src.representation_pipeline import load_safe_incidents


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _complete_record(record: Mapping) -> bool:
    return record.get('status') == 'success' and record.get('request_fingerprint') and record.get('raw_response')


def _load_frozen(path: str | None) -> dict | None:
    if not path:
        return None
    return read_json(path)


def run_generation(
    run_id: str,
    incident_ids: List[str],
    config_path: str = "configs/generation.yaml",
    *,
    inference_root: str | os.PathLike | None = None,
    condition: str = "G0",
    freeze_path: str | None = None,
    input_manifest: str | None = None,
    knowledge_by_incident: Mapping[str, list] | None = None,
    provider=None,
) -> dict:
    config = load_config(config_path)
    config_hash = compute_hash(config)
    frozen = _load_frozen(freeze_path)
    if freeze_path and frozen:
        expected = frozen.get('config_hash') or ((frozen.get('hashes') or {}).get('evaluation_config'))
        if expected and expected != config_hash:
            raise SystemExit('freeze_config_mismatch')
        adapter = frozen.get('adapter_hash') or ((frozen.get('hashes') or {}).get('generator'))
        if adapter and adapter != (config.get('adapter') or {}).get('sha256'):
            raise SystemExit('freeze_adapter_mismatch')
    if input_manifest:
        from src.data.common import sha256
        live_hash = sha256(input_manifest)
        frozen_input = None if not frozen else (
            frozen.get('input_manifest_sha256') or frozen.get('input_manifest_hash')
        )
        if frozen and frozen_input and frozen_input != live_hash:
            raise SystemExit('freeze_input_manifest_mismatch')
        if not frozen:
            raise SystemExit('input_manifest_requires_freeze')

    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    responses_path = run_dir / "responses.jsonl"
    attempts_path = run_dir / "attempts.jsonl"
    completed = {}
    if responses_path.is_file():
        for line in responses_path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if _complete_record(record):
                completed[record['request_id']] = record

    by_id = {}
    if inference_root:
        loaded, _manifest_hash = load_safe_incidents(inference_root, incident_ids)
        by_id = {item.incident_id: item for item in loaded}
        representation_config = load_representation_config()
    else:
        representation_config = None

    tokenizer = WordTokenizer()
    manifest = {
        "cohort": run_id,
        "config_hash": config_hash,
        "condition": condition,
        "planned": len(incident_ids),
        "attempted": len(completed),
        "failed": 0,
        "stopped": 0,
        "schema_version": "cs221-generation-response-v2",
    }
    with attempts_path.open("a", encoding="utf-8") as attempts_log, responses_path.open("a", encoding="utf-8") as responses_log:
        for incident_id in incident_ids:
            req_id = f"{run_id}_{incident_id}_{condition}"
            if req_id in completed:
                continue
            manifest["attempted"] += 1
            if by_id:
                incident = by_id[incident_id]
                selection = select_evidence(incident, representation_config)
                observation_text = render_representation(incident, "R2", selection["selected_log_ids"])
                observations = [{"evidence_id": evid, "text": observation_text} for evid in selection["selected_log_ids"][:1]] or [
                    {"evidence_id": incident.incident_id + ":r2", "text": observation_text}
                ]
            else:
                observation_text = ""
                observations = []
            knowledge = list((knowledge_by_incident or {}).get(incident_id, []))
            actual_obs, actual_know, ctx_hash, ledger = pack_context(
                observations, knowledge, tokenizer=tokenizer)
            messages = build_messages(observation_text or "\n".join(item.get("text", "") for item in actual_obs),
                                      actual_know, condition=condition)
            actual_context_ids = [item.get("evidence_id") for item in actual_obs + actual_know if item.get("evidence_id")]
            fingerprint = request_fingerprint(
                messages,
                incident_id=incident_id,
                condition=condition,
                context_hash=ctx_hash,
                config_hash=config_hash,
                adapter_hash=(config.get("adapter") or {}).get("sha256"),
                tokenizer_hash=getattr(tokenizer, "name", "unknown"),
                model_revision=str((config.get("local_qwen") or config.get("provider") or {}).get("revision") or ""),
            )
            attempts = 0
            max_attempts = int((config.get("retries") or {}).get("max_attempts", 2))
            status = "pending"
            error = None
            raw_resp = ""
            payload = None
            usage = None
            model_returned = None
            while attempts < max_attempts:
                attempts += 1
                raw_resp, metadata = generate_response(messages, {"incident_id": incident_id, "seed": 221}, config, provider=provider)
                status = metadata.get("status")
                error = metadata.get("error")
                usage = metadata.get("usage")
                model_returned = metadata.get("model_returned")
                attempts_log.write(json.dumps({
                    "attempt_id": f"{req_id}_{attempts}",
                    "request_key": req_id,
                    "attempt_index": attempts,
                    "started_at": _utc(),
                    "status": status,
                    "error": error,
                    "usage": usage,
                    "request_fingerprint": fingerprint,
                    "ledger": ledger,
                }, sort_keys=True) + "\n")
                attempts_log.flush()
                if status in {"blocked_permission", "budget_stopped", "remote_api_disabled", "missing_assets", "missing_runtime"}:
                    manifest["stopped"] += 1
                    break
                if status == "success":
                    payload, val_status, val_err = validate_response(raw_resp, actual_context_ids, incident_id)
                    if val_status != "success":
                        status = val_status
                        error = val_err
                        if attempts < max_attempts:
                            continue
                    break
            if status not in {"success", "blocked_permission", "budget_stopped", "remote_api_disabled", "missing_assets", "missing_runtime"}:
                manifest["failed"] += 1
            record = RunRecord(
                raw_response=raw_resp,
                parsed_payload=payload,
                actual_context_ids=actual_context_ids,
                actual_context_hash=ctx_hash,
                model_requested=str((config.get("local_qwen") or config.get("provider") or {}).get("model", "unknown")),
                model_returned=model_returned,
                provider_epoch="local-1",
                status=status,
                error=error,
                attempts=attempts,
                usage=usage,
                UTC=_utc(),
                request_id=req_id,
                request_fingerprint=fingerprint,
            )
            responses_log.write(record.model_dump_json() + "\n")
            responses_log.flush()
    manifest_path = Path("runs") / run_id / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_pilot(run_id: str, incident_ids: List[str], config_path: str = "configs/generation.yaml"):
    """Backward-compatible entry used by the existing CLI."""
    return run_generation(run_id, incident_ids, config_path)
