"""Join safe inference observations with train-only G1 labels.

This module is the trainer data contract. It must not import management census
or inference exporters, and it must not open a test-label root.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.data.common import (
    DEFAULT_CONFIG, FILES, IMPL, INCIDENT, DataContractError,
    canonical_bytes, canonical_hash, load_config, parse_json, read_json,
    read_jsonl, require, sha256, validate_inference, write_json, write_jsonl,
)
from src.generation.prompt_builder import SYSTEM_PROMPT
from src.representations import load_config as load_representation_config
from src.representations import SafeIncident, render_representation, select_evidence
from src.training.access import TrainingAccessGuard

SCHEMA_PATH = IMPL / 'schemas/training-example.schema.json'
EXPECTED_COUNTS = {'train': 54, 'dev': 18, 'test': 18}
EXPECTED_FAMILIES = {'train': 18, 'dev': 6, 'test': 6}
LEAK_FIELDS = (
    'source_case', 'fault_description', 'fault', 'injection_time',
    'scenario_family_id', 'label_source', 'root_cause_indicator',
)


def _validate_example(example: dict) -> None:
    schema = read_json(SCHEMA_PATH)
    require(set(example) == set(schema['required']), 'EXAMPLE_SCHEMA')
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return
    Draft202012Validator(schema).validate(example)


def load_partition(root, expected_split, guard: TrainingAccessGuard) -> dict:
    """Load one private split root. Trainer never calls this with test split."""
    require(expected_split in EXPECTED_COUNTS, 'SPLIT_MISMATCH')
    root = Path(root).resolve()
    manifest_path = root / 'partition-manifest.json'
    require(guard.is_file(manifest_path), 'MISSING_FILE')
    manifest = parse_json(guard.open(manifest_path, encoding='utf-8-sig').read())
    require(isinstance(manifest, dict) and manifest.get('schema_version') == 'cs221-training-partition-v1',
            'PARTITION_SCHEMA')
    require(manifest.get('split') == expected_split, 'SPLIT_MISMATCH')
    files = {entry['path']: entry for entry in manifest.get('files', [])}
    require(set(files) == {'ground_truth.jsonl', 'split-map.tsv'}, 'PARTITION_SCHEMA')
    loaded = {}
    for name in ('ground_truth.jsonl', 'split-map.tsv'):
        path = root / name
        entry = files[name]
        require(guard.stat(path).st_size == entry['bytes'] and guard.sha256(path) == entry['sha256'],
                'HASH_MISMATCH')
        if name.endswith('.tsv'):
            with guard.open(path, encoding='utf-8-sig', newline='') as handle:
                rows = list(csv.DictReader(handle, delimiter='\t'))
        else:
            with guard.open(path, encoding='utf-8-sig') as handle:
                rows = [parse_json(line) for line in handle if line.strip()]
        require(len(rows) == entry['rows'] == manifest['incident_count'], 'SPLIT_COUNTS')
        loaded[name] = rows
    gold, splits = loaded['ground_truth.jsonl'], loaded['split-map.tsv']
    gold_ids = [row['incident_id'] for row in gold]
    split_ids = [row['incident_id'] for row in splits]
    require(len(gold_ids) == len(set(gold_ids)) == len(split_ids) == len(set(split_ids)), 'DUPLICATE_ID')
    require(set(gold_ids) == set(split_ids) == set(manifest['incident_ids']), 'GOLD_IDS')
    families = {}
    for row in splits:
        require(INCIDENT.fullmatch(row['incident_id']), 'INCIDENT_ID')
        require(row['split'] == expected_split, 'SPLIT_MISMATCH', row['incident_id'])
        require(row['split_version'] == manifest['split_version'], 'SPLIT_VERSION', row['incident_id'])
        families.setdefault(row['scenario_family_id'], []).append(row['split'])
    role = manifest.get('role', 'research')
    require(role in {'research', 'synthetic-fixture'}, 'PARTITION_SCHEMA')
    require(len(families) == manifest['family_count'], 'FAMILY_OVERLAP')
    if role == 'research':
        require(manifest['incident_count'] == EXPECTED_COUNTS[expected_split], 'SPLIT_COUNTS')
        require(len(families) == EXPECTED_FAMILIES[expected_split], 'FAMILY_OVERLAP')
        require(all(len(values) == 3 and len(set(values)) == 1 for values in families.values()),
                'FAMILY_OVERLAP')
    gold_by_id = {}
    for row in gold:
        require(row['incident_id'] not in gold_by_id, 'DUPLICATE_ID', row['incident_id'])
        require(row['scenario_family_id'] in families, 'GOLD_LINEAGE', row['incident_id'])
        gold_by_id[row['incident_id']] = row
    return {
        'manifest': manifest,
        'gold': gold_by_id,
        'splits': {row['incident_id']: row for row in splits},
        'incident_ids': list(manifest['incident_ids']),
        'family_ids': sorted(families),
        'g1_source_sha256': files['ground_truth.jsonl']['sha256'],
        'split_sha256': files['split-map.tsv']['sha256'],
    }


def _load_safe_incidents(inference_root, incident_ids, data_config, guard: TrainingAccessGuard):
    root = Path(inference_root).resolve()
    guard.check(root / 'input-manifest.json', 'stat')
    validation = validate_inference(root, data_config, require_live_transform=False)
    selected = set(incident_ids)
    require(all(INCIDENT.fullmatch(item) for item in incident_ids), 'INCIDENT_ID')
    require(len(incident_ids) == len(selected), 'DUPLICATE_ID')
    data = {kind: {} for kind in ('observations', 'logs', 'metrics', 'traces')}
    for filename, kind in FILES.items():
        path = root / filename
        guard.check(path, 'open')
        for row in read_jsonl(path):
            if row['incident_id'] in selected:
                data[kind].setdefault(row['incident_id'], []).append(row)
    require(set(data['observations']) == selected, 'FOREIGN_INCIDENT')
    incidents = []
    for incident_id in incident_ids:
        observation = data['observations'][incident_id]
        require(len(observation) == 1, 'DUPLICATE_ID', incident_id)
        incidents.append(SafeIncident(
            observation[0], tuple(data['logs'].get(incident_id, [])),
            tuple(data['metrics'].get(incident_id, [])),
            tuple(data['traces'].get(incident_id, [])),
        ))
    return incidents, validation['manifest_hash']


def _assert_prompt_safe(content: str, gold: dict):
    for field in ('source_case', 'scenario_family_id'):
        value = gold.get(field)
        if value:
            require(str(value) not in content, 'PROMPT_LEAK')
    require('source_case' not in content, 'PROMPT_LEAK')
    require('fault_description' not in content, 'PROMPT_LEAK')
    require('injection_time' not in content, 'PROMPT_LEAK')


def _target_text(service_id: str) -> str:
    require(isinstance(service_id, str) and service_id.strip(), 'TARGET_EMPTY')
    payload = {'candidate_causes': [{'service_id': service_id}]}
    return canonical_bytes(payload).decode('utf-8')


def _build_example(incident, gold, partition, representation_config) -> dict:
    selection = select_evidence(incident, representation_config)
    observations = render_representation(incident, 'R2', selection['selected_log_ids'])
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': observations},
    ]
    serialized = json.dumps(messages, ensure_ascii=False)
    _assert_prompt_safe(serialized, gold)
    example = {
        'example_id': 'ex_' + incident.incident_id[4:] + '_g1_service_g0_r2',
        'incident_id': incident.incident_id,
        'input_messages': messages,
        'target_text': _target_text(gold['root_cause_service']),
        'safe_input_sha256': canonical_hash(incident.observation),
        'g1_source_sha256': partition['g1_source_sha256'],
        'split_sha256': partition['split_sha256'],
        'label_revision': gold['label_release_revision'],
        'target_kind': 'g1_service',
    }
    _validate_example(example)
    require(gold['root_cause_service'] not in SYSTEM_PROMPT, 'PROMPT_LEAK')
    return example


def join_training_examples(
    inference_root,
    private_train_root,
    data_config_path=DEFAULT_CONFIG,
    representation_config_path=None,
    private_dev_root=None,
    forbidden_roots=(),
) -> dict:
    """Join train-only G1 with safe observations. Test roots are forbidden."""
    data_config = load_config(Path(data_config_path))
    inference_root = Path(inference_root).resolve()
    train_root = Path(private_train_root).resolve()
    allowed = [inference_root, train_root, Path(data_config_path).resolve().parent, IMPL / 'configs', IMPL / 'schemas']
    if representation_config_path:
        allowed.append(Path(representation_config_path).resolve().parent)
    else:
        allowed.append((IMPL / 'configs').resolve())
        allowed.append((IMPL / 'vendor').resolve())
    forbidden = [Path(root).resolve() for root in forbidden_roots if root]
    if private_dev_root:
        allowed.append(Path(private_dev_root).resolve())
    guard = TrainingAccessGuard(allowed, forbidden)
    train = load_partition(train_root, 'train', guard)
    incidents, manifest_hash = _load_safe_incidents(
        inference_root, train['incident_ids'], data_config, guard)
    require(len(incidents) == train['manifest']['incident_count'], 'SPLIT_COUNTS')
    require({item.incident_id for item in incidents} == set(train['gold']), 'BIJECTION')
    representation_config = load_representation_config(
        Path(representation_config_path) if representation_config_path
        else IMPL / 'configs/representation.yaml')
    examples = [_build_example(incident, train['gold'][incident.incident_id], train, representation_config)
                for incident in incidents]
    receipt = {
        'schema_version': 'cs221-training-join-v1',
        'split': 'train',
        'incident_count': len(examples),
        'family_count': len(train['family_ids']),
        'inference_manifest_sha256': manifest_hash,
        'g1_source_sha256': train['g1_source_sha256'],
        'split_sha256': train['split_sha256'],
        'examples': examples,
        'touched_paths': list(guard.touched),
    }
    if private_dev_root:
        load_partition(Path(private_dev_root).resolve(), 'dev', guard)
    return receipt


def write_examples(receipt: dict, output_path: Path) -> dict:
    path = Path(output_path)
    write_jsonl(path, receipt['examples'])
    sidecar = {
        key: value for key, value in receipt.items() if key not in ('examples', 'touched_paths')
    }
    sidecar['example_count'] = len(receipt['examples'])
    sidecar['examples_sha256'] = sha256(path)
    write_json(path.with_suffix('.manifest.json'), sidecar)
    return sidecar
