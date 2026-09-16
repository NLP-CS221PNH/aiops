from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class CandidateCause(BaseModel):
    service_id: str
    fault_type: str
    reason: str

class SupportedClaim(BaseModel):
    claim_id: str
    text: str
    type: Literal["observation", "inference"]
    evidence_ids: List[str]

class ContextItem(BaseModel):
    evidence_id: str
    source_kind: str
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    text: str
    start_codepoint: int
    end_codepoint: int
    source_revision: str

class GenerationPayload(BaseModel):
    incident_id: str
    candidate_causes: List[CandidateCause]
    supported_claims: List[SupportedClaim]
    missing_information: List[str]
    next_checks: List[str]
    abstain: bool
    confidence_label: str

class GenerationRequest(BaseModel):
    incident_id: str
    condition: str
    run_id: str
    observations: List[Dict[str, Any]]
    bundle_hash: str
    knowledge_context: List[ContextItem]
    context_hash: str
    prompt_hash: str
    config_hash: str

class RunRecord(BaseModel):
    raw_response: str
    parsed_payload: Optional[GenerationPayload] = None
    actual_context_ids: List[str]
    actual_context_hash: str
    model_requested: str
    model_returned: Optional[str] = None
    provider_epoch: str
    status: str
    error: Optional[str] = None
    attempts: int
    usage: Optional[Dict[str, Any]] = None
    UTC: str
    request_id: str
