"""Reciprocal rank fusion with strict ranking contracts."""

import math

from .bm25 import validate_depth


def validate_ranking(ranking):
    if not isinstance(ranking, (list, tuple)):
        raise ValueError("ranking must be a list or tuple")
    seen = set()
    for position, hit in enumerate(ranking, 1):
        if not isinstance(hit, dict):
            raise ValueError("ranking hit must be an object")
        chunk_id, document_id = hit.get("chunk_id"), hit.get("document_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError("ranking chunk_id must be a nonempty string")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("ranking document_id must be a nonempty string")
        if chunk_id in seen:
            raise ValueError(f"duplicate ranking chunk_id: {chunk_id}")
        seen.add(chunk_id)
        if type(hit.get("rank")) is not int or hit["rank"] != position:
            raise ValueError("ranking ranks must be sequential integers starting at one")
        score = hit.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError("ranking score must be a finite number")


def rrf(rankings, constant=60, weights=None, depth=50):
    validate_depth(depth)
    if isinstance(constant, bool) or not isinstance(constant, (int, float)) or not math.isfinite(constant) or constant < 0:
        raise ValueError("RRF constant must be finite and nonnegative")
    if not isinstance(rankings, (list, tuple)):
        raise ValueError("rankings must be a list or tuple")
    if weights is None:
        weights = [1.0] * len(rankings)
    if not isinstance(weights, (list, tuple)) or len(weights) != len(rankings):
        raise ValueError("weights must contain one value for each ranking")
    if any(isinstance(weight, bool) or not isinstance(weight, (int, float)) or
           not math.isfinite(weight) or weight < 0 for weight in weights):
        raise ValueError("RRF weights must be finite and nonnegative")
    if rankings and not any(weights):
        raise ValueError("at least one RRF weight must be positive")
    documents, contributions = {}, {}
    for ranking, weight in zip(rankings, weights):
        validate_ranking(ranking)
        for hit in ranking:
            chunk_id = hit["chunk_id"]
            if chunk_id in documents and documents[chunk_id] != hit["document_id"]:
                raise ValueError(f"conflicting document_id for chunk_id: {chunk_id}")
            documents[chunk_id] = hit["document_id"]
            if weight:
                contributions.setdefault(chunk_id, []).append(weight / (constant + hit["rank"]))
    try:
        scores = {chunk_id: math.fsum(values) for chunk_id, values in contributions.items()}
    except OverflowError as exc:
        raise ValueError("RRF weights produced a nonfinite total score") from exc
    if not all(math.isfinite(score) for score in scores.values()):
        raise ValueError("RRF produced a nonfinite score")
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[:depth]
    return [{"chunk_id": chunk_id, "document_id": documents[chunk_id], "rank": rank,
             "score": scores[chunk_id]} for rank, chunk_id in enumerate(ordered, 1)]
