import json
import yaml
import os
from typing import Dict, Any, Tuple

def load_config(config_path: str = "configs/generation.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check_permissions(config: Dict[str, Any]) -> bool:
    perms = config.get("permissions", {})
    return perms.get("api") == "approved" or perms.get("local") == "approved"

def generate_response(prompt: str, context: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    if not check_permissions(config):
        return "", {"status": "blocked_permission", "error": "API/Local permission not approved."}
    
    if config.get("approved_cap_usd") is None:
        return "", {"status": "budget_stopped", "error": "approved_cap_usd is null"}

    # Mock response for pilot if permissions are approved
    mock_payload = {
        "incident_id": context.get("incident_id", "unknown"),
        "candidate_causes": [{"service_id": "svc_a", "fault_type": "cpu_spike", "reason": "mock logic"}],
        "supported_claims": [],
        "missing_information": [],
        "next_checks": [],
        "abstain": False,
        "confidence_label": "low"
    }
    
    raw_response = json.dumps(mock_payload)
    metadata = {
        "status": "success",
        "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
        "model_returned": config.get("provider", {}).get("model", "unknown")
    }
    return raw_response, metadata
