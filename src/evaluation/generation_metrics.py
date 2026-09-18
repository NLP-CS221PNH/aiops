"""Generation metrics with explicit denominators. Abstain/fail/invalid are misses."""
from __future__ import annotations

from typing import Iterable, Sequence

from src.evaluation.metrics import CalculationResult, Status


def service_hit_at_k(
    predicted_services: Sequence[str],
    gold_service: str,
    k: int,
    *,
    abstained: bool = False,
    invalid: bool = False,
    failed: bool = False,
) -> CalculationResult:
    if abstained or invalid or failed:
        return CalculationResult(Status.ELIGIBLE, value=0.0, reason="miss_failed_invalid_or_abstain")
    hit = gold_service in list(predicted_services)[:k]
    return CalculationResult(Status.ELIGIBLE, value=1.0 if hit else 0.0)


def citation_precision(cited_ids: Sequence[str], actual_context_ids: Sequence[str]) -> CalculationResult:
    if not cited_ids:
        return CalculationResult(Status.UNDEFINED, reason="zero_citations")
    allowed = set(actual_context_ids)
    valid = sum(1 for item in cited_ids if item in allowed)
    return CalculationResult(Status.ELIGIBLE, value=valid / len(cited_ids), diagnostics={"n_citations": len(cited_ids)})


def evidence_recall(required_ids: Sequence[str], cited_ids: Sequence[str], actual_context_ids: Sequence[str]) -> CalculationResult:
    if not required_ids:
        return CalculationResult(Status.UNDEFINED, reason="no_required_evidence")
    allowed = set(actual_context_ids)
    cited_ok = {item for item in cited_ids if item in allowed}
    found = sum(1 for item in required_ids if item in cited_ok)
    return CalculationResult(Status.ELIGIBLE, value=found / len(required_ids))


def unsupported_claim_rate(evidence_requiring_claims: int, unsupported_claims: int, zero_claim_responses: int) -> CalculationResult:
    if evidence_requiring_claims <= 0:
        return CalculationResult(
            Status.UNDEFINED,
            reason="zero_claims",
            diagnostics={"zero_claim_responses": zero_claim_responses},
        )
    return CalculationResult(Status.ELIGIBLE, value=unsupported_claims / evidence_requiring_claims)


def abstention_rates(answered: int, abstained: int, correct_refuse: int, unanswerable: int) -> dict[str, CalculationResult]:
    total = answered + abstained
    coverage = CalculationResult(Status.ELIGIBLE, value=answered / total) if total else CalculationResult(Status.UNDEFINED, reason="no_responses")
    if unanswerable <= 0:
        refuse = CalculationResult(Status.UNDEFINED, reason="no_unanswerable_labels")
    else:
        refuse = CalculationResult(Status.ELIGIBLE, value=correct_refuse / unanswerable)
    return {"coverage": coverage, "correct_refuse": refuse}


def mean_hits(hits: Iterable[CalculationResult]) -> CalculationResult:
    eligible = [item.value for item in hits if item.status == Status.ELIGIBLE]
    if not eligible:
        return CalculationResult(Status.UNDEFINED, reason="no_eligible_incidents")
    return CalculationResult(Status.ELIGIBLE, value=sum(eligible) / len(eligible), diagnostics={"n": len(eligible)})
