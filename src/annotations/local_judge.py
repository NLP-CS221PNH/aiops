"""Local G2/G3/answerability judging. G1 never enters the prompt."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.data.common import canonical_hash, require
from src.generation.prompt_builder import canonical_hash as prompt_hash
from src.training.access import EXIT_MISSING

IMPL = Path(__file__).resolve().parents[2]
G1_KEYS = {'root_cause_service', 'source_case', 'fault_description', 'gold_service'}
ALLOWED = 'local-model-automated-v1'


def _reject_g1(payload: Mapping[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False)
    for key in G1_KEYS:
        require(key not in payload and key not in blob, 'G1_IN_JUDGING')


def _raw(provider, messages: Sequence[Mapping[str, str]]) -> tuple[str, dict]:
    if provider is None:
        return '', {'status': 'missing_assets', 'error': 'local judge model is not provisioned'}
    return provider.generate(messages, {}, {'permissions': {'local': 'approved'}})


def judge_g2(observation_text: str, chunk: Mapping[str, Any], *, provider=None, seed: int = 221) -> dict[str, Any]:
    _reject_g1({'observation': observation_text, **dict(chunk)})
    require(chunk.get('text') and chunk.get('chunk_id'), 'MISSING_CHUNK')
    messages = [
        {'role': 'system', 'content': 'Grade passage relevance 0, 1, or 2. Do not use gold services.'},
        {'role': 'user', 'content': f'Observation:\n{observation_text}\n\nPassage:\n{chunk["text"]}'},
    ]
    raw, meta = _raw(provider, messages)
    grade = None
    status = 'unjudged'
    if meta.get('status') == 'success' and raw.strip() in {'0', '1', '2'}:
        grade = int(raw.strip())
        status = 'judged'
    return {
        'task': 'G2',
        'chunk_id': chunk['chunk_id'],
        'grade': grade,
        'status': status,
        'provenance': ALLOWED,
        'prompt_hash': prompt_hash(messages),
        'raw_response': raw or None,
        'model_status': meta.get('status'),
        'seed': seed,
    }


def judge_g3(claims: Sequence[Mapping[str, Any]], packed_context: str, *, provider=None) -> dict[str, Any]:
    _reject_g1({'context': packed_context, 'claims': list(claims)})
    require(packed_context.strip(), 'MISSING_CONTEXT')
    rows = []
    for claim in claims:
        text = str(claim.get('text') or '')
        messages = [
            {'role': 'system', 'content': 'Classify support, contradiction, or insufficient from the packed context only.'},
            {'role': 'user', 'content': f'Context:\n{packed_context}\n\nClaim:\n{text}'},
        ]
        raw, meta = _raw(provider, messages)
        label = 'insufficient'
        if text and text.lower() in packed_context.lower():
            label = 'support'
        elif raw.strip() in {'support', 'contradiction', 'insufficient'}:
            label = raw.strip()
        rows.append({
            'claim_id': claim.get('claim_id') or canonical_hash(text)[:12],
            'label': label,
            'raw_response': raw or None,
            'prompt_hash': prompt_hash(messages),
            'model_status': meta.get('status'),
        })
    return {'task': 'G3', 'provenance': ALLOWED, 'judgments': rows}


def judge_answerability(packed_context: str, *, provider=None) -> dict[str, Any]:
    require(packed_context.strip(), 'MISSING_CONTEXT')
    _reject_g1({'context': packed_context})
    messages = [
        {'role': 'system', 'content': 'Label answerable, partially_answerable, unanswerable, or insufficient_evidence from context only.'},
        {'role': 'user', 'content': packed_context},
    ]
    raw, meta = _raw(provider, messages)
    label = 'insufficient_evidence'
    if meta.get('status') == 'success' and raw.strip() in {
        'answerable', 'partially_answerable', 'unanswerable', 'insufficient_evidence',
    }:
        label = raw.strip()
    elif packed_context:
        label = 'insufficient_evidence'
    return {
        'task': 'answerability',
        'label': label,
        'status': 'labeled' if meta.get('status') == 'success' else 'insufficient_evidence',
        'provenance': ALLOWED,
        'prompt_hash': prompt_hash(messages),
        'raw_response': raw or None,
        'model_status': meta.get('status'),
        'note': 'Not inferred from empty G2 pools or G1 labels.',
    }


def blind_pool(candidates: Sequence[Mapping[str, Any]], seed: int = 221) -> list[dict[str, Any]]:
    rows = []
    for item in candidates:
        row = dict(item)
        for leak in ('rank', 'score', 'retriever', 'ndcg', 'rrf'):
            row.pop(leak, None)
        rows.append(row)
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Local G2/G3/answerability judge')
    parser.add_argument('--config', default=str(IMPL / 'configs' / 'kaggle.yaml'))
    parser.add_argument('--output-root', default=str(IMPL / 'artifacts' / 'kaggle-delivery' / 'v1' / 'judgments'))
    parser.add_argument('--run-id', default='judge-v2')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(argv)
    Path(args.output_root).mkdir(parents=True, exist_ok=True)
    print(json.dumps({
        'status': 'not_run',
        'error': 'MISSING_INPUT',
        'run_id': args.run_id,
        'resume': args.resume,
        'provenance': ALLOWED,
        'g1_forbidden': True,
        'how_to': 'attach local judge model assets and pass a blinded pool; this CLI does not invent grades',
    }))
    return EXIT_MISSING


if __name__ == '__main__':
    raise SystemExit(main())
