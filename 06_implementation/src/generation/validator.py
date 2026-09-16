import json
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError
from src.generation.schemas import GenerationPayload

def validate_response(raw_response: str, actual_context_ids: List[str]) -> Tuple[Optional[GenerationPayload], str, str]:
    if not raw_response:
        return None, "invalid_response", "Empty response"
        
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        return None, "invalid_response", "JSON parse error"
        
    try:
        payload = GenerationPayload(**data)
    except ValidationError as e:
        return None, "invalid_response", f"Schema validation error: {str(e)}"
        
    # Verify that all evidence_ids in claims exist in actual_context_ids
    context_set = set(actual_context_ids)
    for claim in payload.supported_claims:
        for eid in claim.evidence_ids:
            if eid not in context_set:
                return None, "invalid_citation", f"Citation {eid} not found in actual context"
                
    return payload, "success", ""
