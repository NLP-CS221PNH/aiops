"""Oracle/random packers and historical-vs-current leakage overlap. No F1 index mix."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.generation.context_builder import pack_context

ORACLE_NDCG5 = 1.0


def _as_knowledge(chunk_id: str, chunk: Mapping[str, Any] | None = None) -> dict[str, Any]:
    text = ""
    if chunk:
        text = str(chunk.get("text") or chunk.get("content") or "")
    return {
        "chunk_id": chunk_id,
        "evidence_id": chunk_id,
        "text": text,
        "source_kind": "knowledge",
        "source_revision": "locked-historical",
        "start_codepoint": 0,
        "end_codepoint": len(text),
    }


def pack_oracle(
    qrels: Mapping[str, int],
    chunks_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    k: int = 5,
    observations: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ranked = sorted(
        (chunk_id for chunk_id, grade in qrels.items() if grade > 0),
        key=lambda chunk_id: (-int(qrels[chunk_id]), chunk_id),
    )[:k]
    knowledge = [_as_knowledge(chunk_id, (chunks_by_id or {}).get(chunk_id)) for chunk_id in ranked]
    actual_obs, actual_know, context_hash, ledger = pack_context(list(observations or []), knowledge)
    return {
        "condition": "G-oracle",
        "chunk_ids": [item.get("chunk_id") or item.get("evidence_id") for item in actual_know],
        "actual_obs": actual_obs,
        "actual_know": actual_know,
        "context_hash": context_hash,
        "ledger": ledger,
        "retrieval_ndcg5": ORACLE_NDCG5 if ranked else 0.0,
        "generation_status": "NOT_RUN",
    }


def pack_random(
    qrels: Mapping[str, int],
    corpus_ids: Sequence[str],
    seed: int,
    k: int = 5,
    chunks_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    observations: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    judged_negative = sorted(chunk_id for chunk_id, grade in qrels.items() if grade == 0)
    pool = judged_negative or sorted(set(corpus_ids) - {chunk_id for chunk_id, grade in qrels.items() if grade > 0})
    rng = random.Random(seed)
    sample = pool[:]
    rng.shuffle(sample)
    chosen = sample[:k]
    knowledge = [_as_knowledge(chunk_id, (chunks_by_id or {}).get(chunk_id)) for chunk_id in chosen]
    actual_obs, actual_know, context_hash, ledger = pack_context(list(observations or []), knowledge)
    return {
        "condition": "G-random",
        "chunk_ids": [item.get("chunk_id") or item.get("evidence_id") for item in actual_know],
        "actual_obs": actual_obs,
        "actual_know": actual_know,
        "context_hash": context_hash,
        "ledger": ledger,
        "seed": seed,
        "generation_status": "NOT_RUN",
    }


def _document_index(path: Path) -> tuple[set[str], set[tuple[str, str]]]:
    ids: set[str] = set()
    paths: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        ids.add(row["document_id"])
        paths.add((row.get("source_id", ""), row.get("source_path", "")))
    return ids, paths


def leakage_overlap(historical_docs: Path, current_docs: Path) -> dict[str, Any]:
    hist_ids, hist_paths = _document_index(historical_docs)
    curr_ids, curr_paths = _document_index(current_docs)
    shared_ids = hist_ids & curr_ids
    shared_paths = hist_paths & curr_paths
    return {
        "historical_documents": len(hist_ids),
        "current_documents": len(curr_ids),
        "shared_document_ids": len(shared_ids),
        "shared_source_paths": len(shared_paths),
        "ir_h_ndcg5_delta": "NOT_RUN",
        "status": "diagnostic_only",
        "note": "Sensitivity only. Historical F1 corpus is unchanged. IR delta is NOT_RUN without a separate current index.",
    }


def answerability_slice(incident_ids: Sequence[str], labels: Mapping[str, str]) -> dict[str, Any]:
    if not labels:
        return {"status": "NOT_RUN", "reason": "no_answerability_labels"}
    answerable = [item for item in incident_ids if labels.get(item) == "answerable"]
    unanswerable = [item for item in incident_ids if labels.get(item) == "unanswerable"]
    return {
        "status": "labeled",
        "answerable_n": len(answerable),
        "unanswerable_n": len(unanswerable),
        "unanswerable_ir": "undefined",
        "note": "Do not mix empty-Gq into primary nDCG. Unanswerable IR metrics stay undefined.",
    }
