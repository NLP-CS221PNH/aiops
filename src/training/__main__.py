"""Trainer CLI: preflight, prepare, train, export, verify-export."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.data.common import IMPL, DataContractError
from src.training.access import EXIT_CLI, EXIT_MISSING, EXIT_OK, EXIT_RUNTIME, exit_code_for
from src.training.config import load_resolved_kaggle, load_training_config
from src.training.export import export_adapter, verify_export
from src.training.preflight import prepare_examples, preflight
from src.training.trainer import train_run


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='G1 LoRA trainer. Test roots stay unmounted.')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('preflight', 'prepare', 'train', 'export', 'verify-export'):
        item = sub.add_parser(name)
        item.add_argument('--config', default=str(IMPL / 'configs' / 'kaggle.resolved.json'))
        if name == 'preflight':
            item.add_argument('--data-only', action='store_true')
            item.add_argument('--require-gpu', action='store_true')
        if name == 'prepare':
            item.add_argument('--output', default=None)
        if name == 'train':
            item.add_argument('--mode', choices=('smoke', 'full'), default='smoke')
            item.add_argument('--max-steps', type=int, default=None)
            item.add_argument('--run-id', default='technical-smoke')
            item.add_argument('--resume', default=None)
        if name == 'export':
            item.add_argument('--checkpoint', default='best-dev')
            item.add_argument('--run-dir', required=True)
            item.add_argument('--output', required=True)
        if name == 'verify-export':
            item.add_argument('--export-dir', required=True)
            item.add_argument('--example-json', required=True)
    return parser


def main(argv=None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            return EXIT_OK
        return int(exc.code)
    try:
        if args.command == 'preflight':
            result = preflight(args.config, data_only=args.data_only or not args.require_gpu, require_gpu=args.require_gpu)
        elif args.command == 'prepare':
            result = prepare_examples(args.config, args.output)
        elif args.command == 'train':
            resolved = load_resolved_kaggle(args.config)
            from src.training.data import join_training_examples
            forbidden = [resolved['private_test_root']] if resolved.get('private_test_root') else []
            joined = join_training_examples(
                resolved['inference_root'], resolved['private_train_root'],
                private_dev_root=resolved.get('private_dev_root') if args.mode != 'smoke' else None,
                forbidden_roots=forbidden,
            )
            result = train_run(
                joined['examples'][:8] if args.mode == 'smoke' else joined['examples'],
                run_id=args.run_id,
                mode=args.mode,
                max_steps=args.max_steps,
                resume=args.resume,
                recipe=load_training_config(),
                output_root=resolved.get('output_root') or IMPL,
                qwen_assets=resolved.get('qwen_assets'),
                require_qwen=(args.mode == 'full'),
            )
        elif args.command == 'export':
            result = export_adapter(Path(args.run_dir), Path(args.output), checkpoint=args.checkpoint)
        elif args.command == 'verify-export':
            example = json.loads(Path(args.example_json).read_text(encoding='utf-8'))
            result = verify_export(Path(args.export_dir), example)
        else:
            return EXIT_CLI
        print(json.dumps(result, default=str))
        return EXIT_OK
    except DataContractError as exc:
        print(json.dumps({'error': exc.code, 'exit': exit_code_for(exc)}), file=sys.stderr)
        return exit_code_for(exc)
    except FileNotFoundError as exc:
        print(json.dumps({'error': 'MISSING_FILE', 'detail': str(exc)}), file=sys.stderr)
        return EXIT_MISSING
    except RuntimeError as exc:
        code = 'MISSING_RUNTIME' if 'missing_runtime' in str(exc) else 'TRAIN_FAIL'
        print(json.dumps({'error': code, 'detail': str(exc)}), file=sys.stderr)
        return EXIT_MISSING if code == 'MISSING_RUNTIME' else EXIT_RUNTIME


if __name__ == '__main__':
    raise SystemExit(main())
