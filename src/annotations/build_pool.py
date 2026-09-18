"""Build a blinded G2 pool from retrieval rankings. No rank leak, no G1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.annotations.local_judge import blind_pool
from src.data.common import IMPL, require, write_json


def union_topk(runs: list[dict], depth: int) -> list[dict]:
    seen = set()
    rows = []
    for run in runs:
        incident_id = run['incident_id']
        ranking = list(run.get('ranking') or run.get('chunk_ids') or [])[:depth]
        retriever = run.get('retriever')
        for rank, chunk_id in enumerate(ranking, start=1):
            key = (incident_id, chunk_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'incident_id': incident_id,
                'chunk_id': chunk_id,
                'rank': rank,
                'retriever': retriever,
                'score': run.get('scores', [None] * depth)[rank - 1] if isinstance(run.get('scores'), list) else None,
            })
    return rows


def build_pool(runs: list[dict], depth: int = 10, seed: int = 221) -> dict:
    union = union_topk(runs, depth)
    blinded = blind_pool(union, seed=seed)
    for row in blinded:
        require('rank' not in row and 'score' not in row and 'retriever' not in row, 'RANK_LEAK')
    return {
        'schema_version': 'cs221-g2-pool-v2',
        'depth': depth,
        'seed': seed,
        'n': len(blinded),
        'candidates': blinded,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Build annotation pool from retrieval rankings.')
    parser.add_argument('--runs', nargs='+', required=True)
    parser.add_argument('--depth', type=int, default=10)
    parser.add_argument('--seed', type=int, default=221)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    runs = []
    for path in args.runs:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
        runs.extend(payload if isinstance(payload, list) else payload.get('runs') or [payload])
    pool = build_pool(runs, depth=args.depth, seed=args.seed)
    write_json(Path(args.output), pool)
    print(json.dumps({'n': pool['n'], 'output': args.output}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
