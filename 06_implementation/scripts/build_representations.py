"""Build/validate plan 04 candidate artifacts; deliberately no test-data mode."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))

from src.representation_pipeline import (  # noqa: E402
    DEFAULT_CONFIG, DEFAULT_INPUT, DEFAULT_MANAGER, DEFAULT_OUTPUT,
    build_representations, validate_artifacts,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'validate'))
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--manager', type=Path, default=DEFAULT_MANAGER)
    parser.add_argument('--input-dir', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--receipt', type=Path, help='Validate an existing review receipt (validate only).')
    args = parser.parse_args(argv)
    if args.receipt and args.command != 'validate':
        parser.error('--receipt is only accepted for validate')
    arguments = dict(output_dir=args.output_dir, config_path=args.config,
                     manager_path=args.manager, input_dir=args.input_dir)
    try:
        if args.command == 'build':
            manifest = build_representations(**arguments)
            result = {'status': 'pass', 'milestone': manifest['milestone'], 'counts': manifest['counts']}
        else:
            result = validate_artifacts(**arguments, receipt_path=args.receipt)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Contract errors contain opaque IDs only; never dump telemetry/private rows.
        print(json.dumps({'status': 'fail', 'error_type': type(exc).__name__,
                          'error': str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
