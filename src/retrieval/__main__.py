"""Command line entry; local dependency roots only, no download side effects."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

IMPL = Path(__file__).resolve().parents[2]
for dependency in (IMPL / '.corpus-deps', IMPL / '.retrieval-deps'):
    if dependency.is_dir():
        sys.path.insert(0, str(dependency))

from .common import digest, require, safe_path
from .inputs import load_config, load_corpus


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    for command in ('preflight', 'index', 'run'):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument('--config', default='configs/retrieval.yaml')
        command_parser.add_argument('--mode', choices=('pilot', 'fixture', 'frozen'), default='pilot')
        if command != 'preflight':
            command_parser.add_argument('--methods', default='bm25,dense,hybrid')
        if command == 'run':
            command_parser.add_argument('--incident-list', required=True)
            command_parser.add_argument('--run-id')
            command_parser.add_argument('--resume', action='store_true')
            command_parser.add_argument('--depth', type=int)
            command_parser.add_argument('--f1')
            command_parser.add_argument('--trusted-f1-sha256')
            command_parser.add_argument('--test-input-manifest')
            command_parser.add_argument('--trusted-test-input-sha256')
            command_parser.add_argument('--stop-after', type=int, help='Synthetic fixture interruption only')
    validation = subparsers.add_parser('validate-run')
    validation.add_argument('--manifest', required=True)
    validation.add_argument('--expected-sha256')
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate-run':
            from .consumer import read_run
            manifest, rows = read_run(args.manifest, expected_manifest_hash=args.expected_sha256)
            print(json.dumps({'valid': True, 'state': manifest['state'], 'counts': manifest['counts'],
                              'synthetic': manifest['synthetic'], 'records_validated': len(rows)}))
            return 0
        config = load_config(args.config)
        if args.command == 'run':
            from .runner import run
            if args.depth is not None:
                require(1 <= args.depth <= 50, 'DEPTH')
                config['depth'] = args.depth
            path, result = run(config, args.incident_list, mode=args.mode,
                    methods=args.methods.split(','), run_id=args.run_id, resume=args.resume,
                    f1_path=args.f1, trusted_f1_hash=args.trusted_f1_sha256,
                    test_input_manifest=args.test_input_manifest, trusted_test_input_hash=args.trusted_test_input_sha256,
                    stop_after=args.stop_after)
            print(json.dumps({'manifest': str(path), 'state': result['state'], 'counts': result['counts'],
                              'synthetic': result['synthetic']}))
            return 0 if result['state'] == 'complete' else 1
        require(args.mode != 'frozen', 'FROZEN_INDEX_REQUIRES_RUN_F1_GATES')
        chunks, manifest = load_corpus(config, mode=args.mode)
        if args.command == 'preflight':
            print(json.dumps({'input_valid': True, 'corpus_chunks': len(chunks),
                              'models': {'dense': 'requires_explicit_asset_manifest' if not config['dense']['assets'] else 'not_loaded',
                                         'reranker': 'disabled' if not config['reranker']['enabled'] else 'not_loaded'},
                              'mode': args.mode, 'indexing_performed': False}))
            return 0
        methods = args.methods.split(',')
        require(methods and len(set(methods)) == len(methods)
                and all(method in {'bm25', 'dense', 'hybrid'} for method in methods), 'METHODS')
        from .bm25 import BM25
        from .runner import prepare_dense
        BM25(chunks, k1=config['bm25']['k1'], b=config['bm25']['b'])
        info = None
        if any(method in methods for method in ('dense', 'hybrid')):
            _, _, info = prepare_dense({'chunks': chunks, 'corpus_hash': manifest['corpus_hash']}, config)
        print(json.dumps({'index_valid': True, 'corpus_chunks': len(chunks), 'dense': info,
                          'bm25_persistence': 'rebuilt deterministically from hashed canonical content'}))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError) as exc:
        # Contract errors name fields/IDs; never print raw input or model exception payloads.
        from .common import RetrievalError
        from .dense import ModelUnavailableError
        code = str(exc) if isinstance(exc, RetrievalError) else ('MODEL_UNAVAILABLE' if isinstance(exc, ModelUnavailableError) else type(exc).__name__)
        print(json.dumps({'valid': False, 'error': code}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
