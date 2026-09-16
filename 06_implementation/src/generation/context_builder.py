import hashlib
import json
from typing import List, Dict, Any, Tuple
from src.generation.schemas import ContextItem

def compute_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def pack_context(
    observations: List[Dict[str, Any]], 
    knowledge: List[Dict[str, Any]],
    obs_budget: int = 2048,
    know_budget: int = 4096
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    Deduplicate and truncate context to fit budgets.
    In a real implementation, this would use a tokenizer.
    Here we keep it simple for the pilot.
    """
    actual_obs = observations[:100]  # rough limit
    
    # Dedup knowledge by chunk_id
    seen_chunks = set()
    actual_know = []
    for k in knowledge:
        cid = k.get("chunk_id", k.get("evidence_id"))
        if cid not in seen_chunks:
            seen_chunks.add(cid)
            actual_know.append(k)
        if len(actual_know) >= 5:  # max 5 chunks per requirements
            break
            
    actual_context_ids = [obs.get("evidence_id") for obs in actual_obs if "evidence_id" in obs] + \
                         [k.get("evidence_id") for k in actual_know if "evidence_id" in k]
                         
    context_hash = compute_hash(actual_context_ids)
    
    ledger = {
        "observations_truncated": len(observations) > len(actual_obs),
        "knowledge_truncated": len(knowledge) > len(actual_know)
    }
    
    return actual_obs, actual_know, context_hash, ledger
