"""Pack observations and knowledge with content hashes and token budgets."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Sequence, Tuple

CountTokens = Callable[[str], int]


def compute_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


class WordTokenizer:
    """Deterministic stand-in used when Qwen assets are absent in tests."""

    name = "word-tokenizer-v1"

    def count(self, text: str) -> int:
        return max(1, len(text.split())) if text.strip() else 0


def content_hash_items(items: Sequence[Dict[str, Any]]) -> str:
    rows = []
    for index, item in enumerate(items):
        rows.append({
            'order': index,
            'evidence_id': item.get('evidence_id') or item.get('chunk_id'),
            'text': item.get('text', ''),
            'source_revision': item.get('source_revision'),
        })
    return compute_hash(rows)


def _truncate(items: Sequence[Dict[str, Any]], budget: int, tokenizer: Any, prefix: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    kept: List[Dict[str, Any]] = []
    dropped: List[str] = []
    used = tokenizer.count(prefix) if prefix else 0
    for item in items:
        text = str(item.get('text') or '')
        cost = tokenizer.count(text)
        evid = item.get('evidence_id') or item.get('chunk_id') or 'unknown'
        if kept and used + cost > budget:
            dropped.append(str(evid))
            continue
        if not kept and cost > budget:
            dropped.append(str(evid))
            continue
        kept.append(dict(item))
        used += cost
    return kept, dropped


def pack_context(
    observations: List[Dict[str, Any]],
    knowledge: List[Dict[str, Any]],
    obs_budget: int = 2048,
    know_budget: int = 4096,
    tokenizer: Any = None,
    max_knowledge_chunks: int = 5,
    max_observations: int = 100,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, Dict[str, Any]]:
    tokenizer = tokenizer or WordTokenizer()
    capped_obs = list(observations[:max_observations])
    dropped_obs_ids = [
        str(item.get('evidence_id') or item.get('chunk_id') or 'unknown')
        for item in observations[max_observations:]
    ]
    actual_obs, dropped_obs = _truncate(capped_obs, obs_budget, tokenizer, 'observations')
    dropped_obs = dropped_obs_ids + dropped_obs
    seen = set()
    unique_know = []
    overflow_know = []
    for item in knowledge:
        cid = item.get('chunk_id') or item.get('evidence_id')
        if cid in seen:
            continue
        seen.add(cid)
        if len(unique_know) >= max_knowledge_chunks:
            overflow_know.append(str(cid or 'unknown'))
            continue
        unique_know.append(item)
    actual_know, dropped_know = _truncate(unique_know, know_budget, tokenizer, 'knowledge')
    dropped_know = overflow_know + dropped_know
    context_hash = compute_hash({
        'observation_content_sha256': content_hash_items(actual_obs),
        'knowledge_content_sha256': content_hash_items(actual_know),
        'tokenizer': getattr(tokenizer, 'name', type(tokenizer).__name__),
        'obs_budget': obs_budget,
        'know_budget': know_budget,
    })
    ledger = {
        'observations_truncated': bool(dropped_obs) or len(actual_obs) < len(observations),
        'knowledge_truncated': bool(dropped_know) or len(actual_know) < len(knowledge),
        'dropped_observation_ids': dropped_obs,
        'dropped_knowledge_ids': dropped_know,
        'observation_tokens': sum(tokenizer.count(str(item.get('text') or '')) for item in actual_obs),
        'knowledge_tokens': sum(tokenizer.count(str(item.get('text') or '')) for item in actual_know),
        'tokenizer': getattr(tokenizer, 'name', type(tokenizer).__name__),
    }
    return actual_obs, actual_know, context_hash, ledger
