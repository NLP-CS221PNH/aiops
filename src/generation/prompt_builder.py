"""Shared G0/G* prompt serialization. Metadata stays outside messages."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

SYSTEM_PROMPT = (
    'You are a local service-localization assistant. Use only the observations '
    'in the user message. Reply with JSON object candidate_causes ranked best '
    'first. Each candidate must include service_id. fault_type and reason may be '
    'null. supported_claims, missing_information, next_checks, confidence_label '
    'and abstain are optional. Do not invent gold labels, family ids, source '
    'case names, injection times, or fault descriptions. Do not pad a ranking '
    'with extra services. Incident identifiers are bound by the caller, not by '
    'this completion.'
)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def build_messages(
    observation_text: str,
    knowledge_items: Sequence[Mapping[str, Any]] = (),
    condition: str = 'G0',
) -> list[dict[str, str]]:
    parts = [observation_text.rstrip()]
    if condition != 'G0' and knowledge_items:
        parts.append('Retrieved evidence:')
        for item in knowledge_items:
            evid = item.get('evidence_id') or item.get('chunk_id') or 'unknown'
            text = str(item.get('text') or '')
            parts.append(f'[{evid}] {text}')
    return [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': '\n'.join(parts)},
    ]


def request_fingerprint(
    messages: Sequence[Mapping[str, str]],
    *,
    incident_id: str,
    condition: str,
    context_hash: str,
    config_hash: str,
    adapter_hash: str | None,
    tokenizer_hash: str,
    model_revision: str,
) -> str:
    return canonical_hash({
        'incident_id': incident_id,
        'condition': condition,
        'messages': list(messages),
        'context_hash': context_hash,
        'config_hash': config_hash,
        'adapter_hash': adapter_hash,
        'tokenizer_hash': tokenizer_hash,
        'model_revision': model_revision,
    })
