"""Export disjoint private train/dev/test roots for Kaggle LoRA training.

This is an administrative exporter. It may read the canonical 90-row G1 sidecar.
Trainer commands must not import this script or the resulting test root.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

_IMPL = Path(__file__).resolve().parents[1]
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from src.data.common import (
    DEFAULT_CONFIG, IMPL, DataContractError, load_config, read_jsonl, require,
    sha256, write_json,
)
from src.data.export_inference_data import _cleanup_staging, _output_path
from src.data.export_private_sidecars import _commit_staging_dir
from src.training.access import EXIT_OK, exit_code_for
from src.training.data import EXPECTED_COUNTS, EXPECTED_FAMILIES
from src.training.partition import write_partition

KAGGLE_CONFIG = IMPL / 'configs/kaggle.yaml'
OUTPUT_DEFAULT = IMPL / 'data/training-inputs/v1'
PARENT_GOLD = 'bd02f4e8393e9ccfab3dd8b9bb1e016abee79bacb58aa9a8888c05240b8ee893'
PARENT_SPLIT = 'd7941d1487d4ec7e3943692b2911ea422bf6b14d620fd8e150324161fc17b8c7'


def _read_split_rows(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def validate_prepared(output: Path, data_config: dict) -> dict:
    output = Path(output).resolve()
    prepared = json.loads((output / 'prepared-manifest.json').read_text(encoding='utf-8'))
    require(prepared.get('schema_version') == 'cs221-training-inputs-v1', 'PARTITION_SCHEMA')
    sidecar = json.loads((output / 'prepared-manifest.sha256.json').read_text(encoding='utf-8'))
    require(sha256(output / 'prepared-manifest.json') == sidecar['prepared_manifest_sha256'], 'HASH_MISMATCH')
    require('self_manifest_sha256_excluded' not in prepared, 'PARTITION_SCHEMA')
    families = {}
    for split in ('train', 'dev', 'test'):
        part = output / f'private-{split}'
        recorded = prepared['partitions'][split]
        live = json.loads((part / 'partition-manifest.json').read_text(encoding='utf-8'))
        require(sha256(part / 'partition-manifest.json') == recorded['manifest_sha256'], 'HASH_MISMATCH')
        require(live['incident_count'] == EXPECTED_COUNTS[split], 'SPLIT_COUNTS')
        require(live['family_count'] == EXPECTED_FAMILIES[split], 'FAMILY_OVERLAP')
        for entry in live['files']:
            path = part / entry['path']
            require(path.stat().st_size == entry['bytes'] and sha256(path) == entry['sha256'], 'HASH_MISMATCH')
        for family in live['family_ids']:
            require(family not in families, 'FAMILY_OVERLAP')
            families[family] = split
    require(len(families) == 30, 'FAMILY_OVERLAP')
    private = data_config.get('private_sources') or {}
    gold_hash = (private.get('ground_truth.jsonl') or {}).get('sha256') or PARENT_GOLD
    split_hash = (private.get('split-map.tsv') or {}).get('sha256') or PARENT_SPLIT
    require(prepared['parent_ground_truth_sha256'] == gold_hash, 'HASH_MISMATCH')
    require(prepared['parent_split_map_sha256'] == split_hash, 'HASH_MISMATCH')
    return {'status': 'pass', 'output': str(output), 'family_count': len(families)}


def prepare_kaggle_inputs(data_config_path=DEFAULT_CONFIG, output_dir=OUTPUT_DEFAULT,
                          kaggle_config_path=KAGGLE_CONFIG, validate_only=False) -> dict:
    data_config = load_config(Path(data_config_path))
    gold_source = IMPL / 'data/private/ground_truth.jsonl'
    split_source = IMPL / 'data/private/split-map.tsv'
    require(gold_source.is_file() and split_source.is_file(), 'MISSING_FILE')
    private = data_config.get('private_sources') or {}
    gold_hash = (private.get('ground_truth.jsonl') or {}).get('sha256') or PARENT_GOLD
    split_hash = (private.get('split-map.tsv') or {}).get('sha256') or PARENT_SPLIT
    require(sha256(gold_source) == gold_hash == PARENT_GOLD, 'HASH_MISMATCH')
    require(sha256(split_source) == split_hash == PARENT_SPLIT, 'HASH_MISMATCH')
    gold_rows = read_jsonl(gold_source)
    split_rows = _read_split_rows(split_source)
    require(len(gold_rows) == len(split_rows) == 90, 'SPLIT_COUNTS')
    by_split = defaultdict(list)
    gold_by_id = {row['incident_id']: row for row in gold_rows}
    require(len(gold_by_id) == 90, 'DUPLICATE_ID')
    for row in split_rows:
        by_split[row['split']].append(row)
        require(row['incident_id'] in gold_by_id, 'GOLD_IDS')
        require(gold_by_id[row['incident_id']]['scenario_family_id'] == row['scenario_family_id'], 'GOLD_LINEAGE')
    output = _output_path(Path(output_dir))
    if validate_only:
        return validate_prepared(output, data_config)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.training-inputs-staging-', dir=output.parent))
    try:
        partitions = {}
        for split in ('train', 'dev', 'test'):
            split_subset = by_split[split]
            gold_subset = [gold_by_id[row['incident_id']] for row in split_subset]
            partitions[split] = write_partition(staging, split, gold_subset, split_subset, data_config)
        kaggle = json.loads(Path(kaggle_config_path).read_text(encoding='utf-8')) if Path(kaggle_config_path).is_file() else {}
        resolved = {
            'schema_version': 'cs221-kaggle-resolved-v1',
            'platform': sys.platform,
            'kaggle_paths_unused_on_author_machine': True,
            'inference_root': 'data/inference',
            'private_train_root': 'data/training-inputs/v1/private-train',
            'private_dev_root': 'data/training-inputs/v1/private-dev',
            'knowledge_root': kaggle.get('roots', {}).get('knowledge_root', 'data/knowledge-preparation'),
            'e5_assets': kaggle.get('roots', {}).get('e5_assets', 'vendor/e5-small-v2'),
            'output_root': 'artifacts/kaggle-delivery/v1',
        }
        write_json(staging / 'kaggle.resolved.json', resolved)
        train_resolved = IMPL / 'configs' / 'kaggle.resolved.json'
        write_json(train_resolved, resolved)
        prepared = {
            'schema_version': 'cs221-training-inputs-v1',
            'source_revision': data_config['source_revision'],
            'split_version': data_config['split_version'],
            'parent_ground_truth_sha256': PARENT_GOLD,
            'parent_split_map_sha256': PARENT_SPLIT,
            'inference_manifest_sha256': sha256(IMPL / 'data/inference/input-manifest.json'),
            'partitions': {
                split: {
                    'incident_count': spec['incident_count'],
                    'family_count': spec['family_count'],
                    'manifest_sha256': sha256(staging / f'private-{split}/partition-manifest.json'),
                    'service_counts': spec['service_counts'],
                }
                for split, spec in partitions.items()
            },
            'reconstruction': kaggle.get('reconstruction', {}),
        }
        write_json(staging / 'prepared-manifest.json', prepared)
        write_json(staging / 'prepared-manifest.sha256.json',
                   {'prepared_manifest_sha256': sha256(staging / 'prepared-manifest.json')})
        if output.exists():
            names = {item.name for item in output.iterdir()}
            expected = {'private-train', 'private-dev', 'private-test', 'kaggle.resolved.json',
                        'prepared-manifest.json', 'prepared-manifest.sha256.json'}
            if names != expected:
                raise DataContractError('OUTPUT_VERSION_CHANGE_REQUIRED')
            return validate_prepared(output, data_config)
        _commit_staging_dir(staging, output)
        return validate_prepared(output, data_config)
    finally:
        _cleanup_staging(staging, output.parent, '.training-inputs-staging-')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=KAGGLE_CONFIG)
    parser.add_argument('--data-config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args(argv)
    try:
        receipt = prepare_kaggle_inputs(args.data_config, args.output, args.config, args.validate)
    except Exception as error:
        print(json.dumps({'status': 'failed', 'code': getattr(error, 'code', type(error).__name__)}))
        return exit_code_for(error)
    print(json.dumps({'status': receipt.get('status', 'pass'), 'output': receipt.get('output')}))
    return EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
