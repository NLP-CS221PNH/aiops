import json
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError
from src.generation.schemas import GenerationPayload, GenerationPayloadV1


def validate_response(
    raw_response: str,
    actual_context_ids: List[str],
    incident_id: Optional[str] = None,
) -> Tuple[Optional[GenerationPayload], str, str]:
    if not raw_response:
        return None, "invalid_response", "Empty response"
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        return None, "invalid_response", "JSON parse error"
    if not isinstance(data, dict):
        return None, "invalid_response", "JSON object required"
    try:
        payload = GenerationPayload(**data)
    except ValidationError:
        try:
            historic = GenerationPayloadV1(**data)
        except ValidationError as exc:
            return None, "invalid_response", f"Schema validation error: {str(exc)}"
        payload = GenerationPayload(**historic.model_dump())
    if incident_id and payload.incident_id and payload.incident_id != incident_id:
        return None, "invalid_incident", "Model incident_id does not match request"
    context_set = set(actual_context_ids)
    for claim in payload.supported_claims:
        for eid in claim.evidence_ids:
            if eid not in context_set:
                return None, "invalid_citation", f"Citation {eid} not found in actual context"
    for cause in payload.candidate_causes:
        if not cause.service_id.strip():
            return None, "invalid_response", "Empty service_id"
    return payload, "success", ""
