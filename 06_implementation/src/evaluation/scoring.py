"""Score IR rankings with undefined-when-unjudged semantics."""
from __future__ import annotations

from typing import Mapping, Sequence

from src.evaluation.metrics import CalculationResult, Status, calculate_mrr, calculate_ndcg, calculate_recall

PRIMARY_RQ2 = ("IR-B", "IR-D", "IR-H")


def score_ranking(ranking: Sequence[str], qrels: Mapping[str, int]) -> dict[str, CalculationResult]:
    return {
        "passage_ndcg_5": calculate_ndcg(list(ranking), dict(qrels), k=5),
        "mrr_10": calculate_mrr(list(ranking), dict(qrels), k=10),
        "recall_20": calculate_recall(list(ranking), dict(qrels), k=20),
        "recall_50": calculate_recall(list(ranking), dict(qrels), k=50),
    }


def eligible_mean(results: Sequence[CalculationResult]) -> CalculationResult:
    values = [item.value for item in results if item.status == Status.ELIGIBLE]
    if not values:
        return CalculationResult(Status.UNDEFINED, reason="no_eligible_incidents")
    return CalculationResult(Status.ELIGIBLE, value=sum(values) / len(values), diagnostics={"n": len(values)})


def format_ci(interval: Mapping[str, float | int] | None) -> str:
    if not interval or any(
        isinstance(interval.get(key), float) and interval[key] != interval[key]
        for key in ("low", "high")
    ):
        return "NOT_RUN"
    return f"[{interval['low']:+.3f}, {interval['high']:+.3f}]"
