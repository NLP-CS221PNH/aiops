"""Family-clustered bootstrap with pairing preserved."""
from __future__ import annotations

import math
import random
from typing import Mapping, Sequence


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    if not sorted_values:
        return float("nan")
    rank = (len(sorted_values) - 1) * fraction
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(sorted_values[int(rank)])
    weight = rank - low
    return float(sorted_values[low]) * (1.0 - weight) + float(sorted_values[high]) * weight


def family_clustered_mean_ci(
    values_by_family: Mapping[str, Sequence[float]],
    seed: int,
    resamples: int,
    alpha: float = 0.05,
) -> dict[str, float | int]:
    """Resample families with replacement; keep all incident values inside each family."""
    families = sorted(values_by_family)
    if not families:
        return {"mean": float("nan"), "low": float("nan"), "high": float("nan"), "n_families": 0, "resamples": resamples, "seed": seed}
    observed = [value for family in families for value in values_by_family[family]]
    point = sum(observed) / len(observed)
    rng = random.Random(seed)
    stats: list[float] = []
    for _ in range(resamples):
        draw = [rng.choice(families) for _ in families]
        sample = [value for family in draw for value in values_by_family[family]]
        stats.append(sum(sample) / len(sample))
    stats.sort()
    lower = alpha / 2.0
    upper = 1.0 - lower
    return {
        "mean": point,
        "low": _percentile(stats, lower),
        "high": _percentile(stats, upper),
        "n_families": len(families),
        "resamples": resamples,
        "seed": seed,
    }


def paired_delta_ci(
    treatment_by_family: Mapping[str, Sequence[float]],
    baseline_by_family: Mapping[str, Sequence[float]],
    seed: int,
    resamples: int,
) -> dict[str, float | int]:
    deltas: dict[str, list[float]] = {}
    for family, treatment in treatment_by_family.items():
        baseline = baseline_by_family.get(family)
        if baseline is None or len(baseline) != len(treatment):
            raise ValueError("paired_delta_family_mismatch")
        deltas[family] = [float(left) - float(right) for left, right in zip(treatment, baseline)]
    return family_clustered_mean_ci(deltas, seed=seed, resamples=resamples)
