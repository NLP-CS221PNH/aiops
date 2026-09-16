import json
import os
import datetime
from typing import List

from src.generation.schemas import RunRecord
from src.generation.context_builder import pack_context, compute_hash
from src.generation.provider import generate_response, load_config
from src.generation.validator import validate_response

def run_pilot(run_id: str, incident_ids: List[str], config_path: str = "configs/generation.yaml"):
    config = load_config(config_path)
    config_hash = compute_hash(config)
    
    run_dir = os.path.join("runs", run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    manifest_path = os.path.join(run_dir, "manifest.json")
    responses_path = os.path.join(run_dir, "responses.jsonl")
    attempts_path = os.path.join(run_dir, "attempts.jsonl")
    
    completed_ids = set()
    if os.path.exists(responses_path):
        with open(responses_path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                req_id = record.get("request_id")
                if req_id:
                    completed_ids.add(req_id)
                    
    attempts_log = open(attempts_path, "a", encoding="utf-8")
    responses_log = open(responses_path, "a", encoding="utf-8")
    
    manifest = {
        "cohort": run_id,
        "config_hash": config_hash,
        "planned": len(incident_ids),
        "attempted": len(completed_ids),
        "failed": 0,
        "stopped": 0
    }
    
    for incident_id in incident_ids:
        req_id = f"{run_id}_{incident_id}"
        if req_id in completed_ids:
            continue
            
        manifest["attempted"] += 1
        
        obs = [{"evidence_id": "obs_1", "text": "CPU high"}]
        know = [{"evidence_id": "know_1", "text": "Check processes", "start_codepoint":0, "end_codepoint":10, "source_kind": "doc", "source_revision": "v1"}]
        
        actual_obs, actual_know, ctx_hash, ledger = pack_context(obs, know)
        actual_context_ids = [o["evidence_id"] for o in actual_obs] + [k["evidence_id"] for k in actual_know]
        
        attempts = 0
        max_attempts = config.get("retries", {}).get("max_attempts", 3)
        status = "pending"
        error = None
        raw_resp = ""
        payload = None
        usage = None
        model_returned = None
        
        while attempts < max_attempts:
            attempts += 1
            
            raw_resp, metadata = generate_response("mock prompt", {"incident_id": incident_id}, config)
            status = metadata.get("status")
            error = metadata.get("error")
            usage = metadata.get("usage")
            model_returned = metadata.get("model_returned")
            
            attempt_record = {
                "attempt_id": f"{req_id}_{attempts}",
                "request_key": req_id,
                "attempt_index": attempts,
                "started_at": datetime.datetime.utcnow().isoformat() + "Z",
                "status": status,
                "error": error,
                "usage": usage
            }
            attempts_log.write(json.dumps(attempt_record) + "\n")
            attempts_log.flush()
            
            if status in ["blocked_permission", "budget_stopped"]:
                manifest["stopped"] += 1
                break
                
            if status == "success":
                payload, val_status, val_err = validate_response(raw_resp, actual_context_ids)
                if val_status != "success":
                    status = val_status
                    error = val_err
                break
                
        if status not in ["success", "blocked_permission", "budget_stopped"]:
            manifest["failed"] += 1
            
        record = RunRecord(
            raw_response=raw_resp,
            parsed_payload=payload,
            actual_context_ids=actual_context_ids,
            actual_context_hash=ctx_hash,
            model_requested=config.get("provider", {}).get("model", "unknown"),
            model_returned=model_returned,
            provider_epoch="1",
            status=status,
            error=error,
            attempts=attempts,
            usage=usage,
            UTC=datetime.datetime.utcnow().isoformat() + "Z",
            request_id=req_id
        )
        
        responses_log.write(record.model_dump_json() + "\n")
        responses_log.flush()
        
    attempts_log.close()
    responses_log.close()
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest
