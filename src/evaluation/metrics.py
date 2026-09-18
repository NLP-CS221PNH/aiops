from enum import Enum
from typing import Dict, List, Any, Optional
import math

class Status(Enum):
    ELIGIBLE = "eligible"
    UNDEFINED = "undefined"

class CalculationResult:
    def __init__(self, status: Status, value: float = 0.0, reason: Optional[str] = None, diagnostics: dict = None):
        self.status = status
        self.value = value
        self.reason = reason
        self.diagnostics = diagnostics or {}

def _check_missing_judgments(ranking: List[str], qrels: Dict[str, int], k: int) -> bool:
    """Check if any document in top k is unjudged."""
    for doc in ranking[:k]:
        if doc not in qrels:
            return True
    return False

def _has_relevant_qrels(qrels: Dict[str, int]) -> bool:
    return any(v > 0 for v in qrels.values())

def calculate_ndcg(ranking: List[str], qrels: Dict[str, int], k: int) -> CalculationResult:
    if not _has_relevant_qrels(qrels):
        return CalculationResult(Status.UNDEFINED, reason="no_relevant_qrels")
        
    if _check_missing_judgments(ranking, qrels, k):
        return CalculationResult(Status.UNDEFINED, reason="unjudged_in_top_k")
        
    if not ranking:
        return CalculationResult(Status.ELIGIBLE, value=0.0)

    dcg = 0.0
    for i, doc in enumerate(ranking[:k]):
        rel = qrels.get(doc, 0)
        if rel > 0:
            gain = (2 ** rel) - 1
            discount = math.log2(i + 1 + 1)
            dcg += gain / discount

    # Calculate IDCG from pooled adjudicated qrels
    ideal_ranking = sorted([rel for rel in qrels.values() if rel > 0], reverse=True)
    idcg = 0.0
    for i, rel in enumerate(ideal_ranking[:k]):
        gain = (2 ** rel) - 1
        discount = math.log2(i + 1 + 1)
        idcg += gain / discount

    value = dcg / idcg if idcg > 0 else 0.0
    return CalculationResult(Status.ELIGIBLE, value=value)

def calculate_mrr(ranking: List[str], qrels: Dict[str, int], k: int) -> CalculationResult:
    if not _has_relevant_qrels(qrels):
        return CalculationResult(Status.UNDEFINED, reason="no_relevant_qrels")
        
    if _check_missing_judgments(ranking, qrels, k):
        return CalculationResult(Status.UNDEFINED, reason="unjudged_in_top_k")
        
    for i, doc in enumerate(ranking[:k]):
        if qrels.get(doc, 0) > 0:
            return CalculationResult(Status.ELIGIBLE, value=1.0 / (i + 1))
            
    return CalculationResult(Status.ELIGIBLE, value=0.0)

def calculate_recall(ranking: List[str], qrels: Dict[str, int], k: int) -> CalculationResult:
    if not _has_relevant_qrels(qrels):
        return CalculationResult(Status.UNDEFINED, reason="no_relevant_qrels")
        
    relevant_in_pool = sum(1 for v in qrels.values() if v > 0)
    if relevant_in_pool == 0:
        return CalculationResult(Status.UNDEFINED, reason="no_relevant_qrels")
        
    judged_at_k = sum(1 for doc in ranking[:k] if doc in qrels)
    retrieved_relevant = sum(1 for doc in ranking[:k] if qrels.get(doc, 0) > 0)
    
    value = retrieved_relevant / relevant_in_pool
    diagnostics = {
        "judged_at_k": judged_at_k,
        "relevant_in_pool": relevant_in_pool
    }
    
    return CalculationResult(Status.ELIGIBLE, value=value, diagnostics=diagnostics)

def collapse_to_documents(ranking: List[Dict[str, str]]) -> List[str]:
    seen = set()
    collapsed = []
    for item in ranking:
        doc_id = item.get("doc_id")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            collapsed.append(doc_id)
    return collapsed
