"""Management selection and offline, reproducible representation artifacts.

Only ``load_manager_selection`` may read the split sidecar. The runtime loader
and renderer receive opaque IDs and strict safe-export records. No test CLI is
provided: plan 08 owns authentication of its future F1 freeze.
"""
from __future__ import annotations

import csv
import hashlib
import platform
import re
from importlib import metadata
from pathlib import Path

from .data.common import (
    DataContractError, FILES, IMPL, INCIDENT, PRIVATE_KEYS, canonical_bytes, canonical_hash,
    read_json, read_jsonl, require, sha256, validate_inference,
)

DEFAULT_CONFIG = IMPL / 'configs/representation.yaml'
DEFAULT_MANAGER = IMPL / 'configs/representation-manager.json'
DEFAULT_INPUT = IMPL / 'data/inference'
DEFAULT_OUTPUT = IMPL / 'queries'
STAGING_OUTPUT = IMPL / '.representation-check'
SCHEMA_PATH = DEFAULT_OUTPUT / 'representation-schema.json'
MANIFEST_NAME = 'query-manifest.json'
ARTIFACT_NAMES = (
    'variants.train-dev.jsonl', 'selection-ledger.jsonl',
    'token-ledger.jsonl', 'observation-bundles.jsonl',
)
HASH_KEYS = (
    'input_manifest_hash', 'config_hash', 'tokenizer_hash',
    'implementation_hash', 'dependencies_hash', 'schema_hash',
    'manager_selection_hash', 'manager_config_hash',
)


def assert_test_f1_gate(role, frozen=None, authenticated_hashes=None):
    """Check an externally authenticated F1 snapshot; never mint a freeze.

    Plan 08 must authenticate ``authenticated_hashes`` outside this function,
    e.g. against its accepted freeze receipt. Caller-provided JSON alone is not
    authentication. This small guard does not enable test materialization in
    the current builder. Synthetic fixtures do not need a real-data freeze.
    """
    require(role in {'train-dev', 'synthetic-fixture', 'test'}, 'MATERIALIZATION_ROLE')
    if role != 'test':
        return True
    require(isinstance(frozen, dict) and isinstance(authenticated_hashes, dict), 'F1_REQUIRED')
    require(frozen.get('gate') == 'F1' and frozen.get('status') == 'frozen', 'F1_REQUIRED')
    required = {'config_hash', 'input_manifest_hash', 'tokenizer_hash',
                'implementation_hash', 'query_manifest_hash'}
    require(required <= set(authenticated_hashes), 'F1_AUTHENTICATED_HASHES_REQUIRED')
    for key in required:
        value = authenticated_hashes[key]
        require(isinstance(value, str) and len(value) == 64
                and all(ch in '0123456789abcdef' for ch in value), 'F1_HASH_SCHEMA')
        require(frozen.get(key) == value, 'F1_HASH_MISMATCH')
    return True


def load_manager_selection(manager_path=DEFAULT_MANAGER, input_dir=DEFAULT_INPUT):
    """Management-only split verification; returns IDs and hashes, no labels."""
    manager = read_json(manager_path)
    require(isinstance(manager, dict)
            and manager.get('schema_version') == 'cs221-representation-manager-v1'
            and manager.get('management_only') is True, 'MANAGER_SCHEMA')
    ids = manager.get('train_dev_incident_ids')
    require(isinstance(ids, list) and all(isinstance(item, str)
            and INCIDENT.fullmatch(item) for item in ids), 'MANAGER_IDS')
    require(ids == sorted(set(ids)) and len(ids) == 72, 'MANAGER_IDS')
    require(manager.get('counts', {}).get('train_incidents') == 54
            and manager['counts'].get('dev_incidents') == 18
            and manager['counts'].get('train_dev_incidents') == 72, 'MANAGER_COUNTS')
    require(manager.get('input_manifest_hash') == sha256(Path(input_dir) / 'input-manifest.json'),
            'MANAGER_INPUT_HASH')
    split_path = IMPL / 'data/private/split-map.tsv'
    require(manager.get('source_split_map_sha256') == sha256(split_path), 'MANAGER_SPLIT_HASH')
    with split_path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    require(len({row['incident_id'] for row in rows}) == len(rows), 'MANAGER_DUPLICATE_ID')
    allowed = sorted(row['incident_id'] for row in rows if row['split'] in {'train', 'dev'})
    require(ids == allowed, 'MANAGER_SPLIT_BOUNDARY')
    require(sum(row['split'] == 'train' for row in rows) == 54
            and sum(row['split'] == 'dev' for row in rows) == 18, 'MANAGER_COUNTS')
    return tuple(ids), {
        'manager_selection_hash': canonical_hash(ids),
        'manager_config_hash': sha256(manager_path),
    }


def load_safe_incidents(input_dir, requested_ids):
    """Validate and read only the safe export; pass no manager dict downstream."""
    from .representations import SafeIncident
    input_dir = Path(input_dir)
    validation = validate_inference(input_dir)
    ids = tuple(requested_ids)
    require(len(ids) == len(set(ids)) and all(isinstance(item, str)
            and INCIDENT.fullmatch(item) for item in ids), 'SELECTED_INCIDENT_IDS')
    selected = set(ids)
    data = {kind: {} for kind in ('observations', 'logs', 'metrics', 'traces')}
    for filename, kind in FILES.items():
        for row in read_jsonl(input_dir / filename):
            if row['incident_id'] in selected:
                data[kind].setdefault(row['incident_id'], []).append(row)
    require(set(data['observations']) == selected, 'SELECTED_INCIDENT_MISSING')
    incidents = []
    for incident_id in sorted(ids):
        observation = data['observations'][incident_id]
        require(len(observation) == 1, 'DUPLICATE_OBSERVATION', incident_id)
        incidents.append(SafeIncident(
            observation[0], tuple(data['logs'].get(incident_id, [])),
            tuple(data['metrics'].get(incident_id, [])),
            tuple(data['traces'].get(incident_id, [])),
        ))
    return incidents, validation['manifest_hash']


def _output_directory(output_dir):
    """Only dedicated derivative directories, with no aliases or traversal."""
    path = Path(output_dir).absolute()
    resolved = path.resolve()
    roots = (DEFAULT_OUTPUT, STAGING_OUTPUT)
    require(path == resolved and any(resolved.is_relative_to(root.resolve()) for root in roots), 'REPRESENTATION_OUTPUT_PATH')
    require(all(root.absolute() == root.resolve() for root in roots), 'REPRESENTATION_OUTPUT_PATH')
    require(not resolved.exists() or resolved.is_dir(), 'REPRESENTATION_OUTPUT_PATH')
    for name in (*ARTIFACT_NAMES, MANIFEST_NAME):
        candidate = resolved / name
        require(candidate.resolve() == candidate and (not candidate.exists() or candidate.is_file()),
                'REPRESENTATION_OUTPUT_PATH')
    return resolved


def _implementation_hashes():
    names = (
        'src/representations.py', 'src/representation_pipeline.py',
        'scripts/build_representations.py', 'src/data/common.py',
        'src/data/export_inference_data.py', 'src/corpus/tokenizer.py', 'src/corpus/common.py',
        'src/data/__init__.py', 'src/corpus/__init__.py', 'configs/data.yaml',
    )
    return {name: sha256(IMPL / name) for name in names}


def _dependencies():
    names = ('configs/requirements-lock.txt', 'configs/corpus-requirements-lock.txt')
    return {
        'python': platform.python_version(),
        'packages': {name: metadata.version(name) for name in ('pyarrow', 'tokenizers')},
        'lock_hashes': {name: sha256(IMPL / name) for name in names},
    }


def _reject_private_fields(value):
    if isinstance(value, dict):
        require(not PRIVATE_KEYS.intersection(value), 'PRIVATE_REPRESENTATION_FIELD')
        for item in value.values():
            _reject_private_fields(item)
    elif isinstance(value, list):
        for item in value:
            _reject_private_fields(item)


def _jsonl_bytes(rows):
    return b''.join(canonical_bytes(row) + b'\n' for row in rows)


def _materialize(config_path, manager_path, input_dir):
    from .representations import QueryTokenizer, generate_incident, load_config
    implementation = _implementation_hashes()
    config_file_hash, schema_file_hash = sha256(config_path), sha256(SCHEMA_PATH)
    config = load_config(config_path)
    ids, management_hashes = load_manager_selection(manager_path, input_dir)
    incidents, input_hash = load_safe_incidents(input_dir, ids)
    tokenizer = QueryTokenizer(config)
    queries, selections, tokens, bundles = [], [], [], []
    for incident in incidents:
        try:
            result_queries, selection, result_tokens, bundle = generate_incident(
                incident, config, tokenizer, input_manifest_hash=input_hash)
        except DataContractError as exc:
            raise DataContractError(exc.code, incident.incident_id) from exc
        require(len(result_queries) == len(result_tokens) == 3, 'VARIANT_COUNT')
        queries.extend(result_queries)
        selections.append(selection)
        tokens.extend(result_tokens)
        bundles.append(bundle)
    rowsets = dict(zip(ARTIFACT_NAMES, (queries, selections, tokens, bundles)))
    for rows in rowsets.values():
        _reject_private_fields(rows)
    _validate_records(rowsets, tokenizer, config, ids, incidents)
    contents = {name: _jsonl_bytes(rows) for name, rows in rowsets.items()}
    dependencies = _dependencies()
    require(implementation == _implementation_hashes() and config_file_hash == sha256(config_path)
            and schema_file_hash == sha256(SCHEMA_PATH), 'MATERIALIZATION_INPUT_CHANGED')
    manifest = {
        'schema_version': 'cs221-query-manifest-v1',
        'milestone': '04.variants', 'status': 'candidate',
        'representation_version': config['representation_version'],
        'input_manifest_hash': input_hash,
        'config_hash': config_file_hash, 'config_content_hash': canonical_hash(config),
        'tokenizer_hash': canonical_hash(config['tokenizer']),
        'implementation_hash': canonical_hash(implementation), 'implementation': implementation,
        'dependencies_hash': canonical_hash(dependencies), 'dependencies': dependencies,
        'schema_hash': schema_file_hash, **management_hashes,
        'variant_ids': ['R1', 'R2', 'R3'],
        'counts': {'incidents': len(ids), 'queries': len(queries),
                   'selections': len(selections), 'token_ledgers': len(tokens), 'bundles': len(bundles)},
        'outputs': [{'path': name, 'sha256': hashlib.sha256(contents[name]).hexdigest(),
                     'bytes': len(contents[name]), 'rows': len(rowsets[name])} for name in ARTIFACT_NAMES],
        'errors': [], 'test_materialization': 'not_performed_requires_plan08_F1',
    }
    schema = read_json(SCHEMA_PATH)
    _validate_shape(manifest, schema['$defs']['manifest'], schema)
    return contents, manifest


def _validate_shape(value, spec, schema):
    """Check the authored schema's deliberately small JSON Schema subset."""
    if '$ref' in spec:
        return _validate_shape(value, schema['$defs'][spec['$ref'].split('/')[-1]], schema)
    types = {'object': lambda item: isinstance(item, dict),
             'array': lambda item: isinstance(item, list),
             'string': lambda item: isinstance(item, str),
             'integer': lambda item: type(item) is int,
             'boolean': lambda item: type(item) is bool}
    if 'type' in spec:
        require(types[spec['type']](value), 'ARTIFACT_SCHEMA_TYPE')
    if 'enum' in spec:
        require(value in spec['enum'], 'ARTIFACT_SCHEMA_ENUM')
    if 'const' in spec:
        require(value == spec['const'], 'ARTIFACT_SCHEMA_CONST')
    if 'pattern' in spec:
        require(re.fullmatch(spec['pattern'], value) is not None, 'ARTIFACT_SCHEMA_PATTERN')
    if 'minimum' in spec:
        require(value >= spec['minimum'], 'ARTIFACT_SCHEMA_MINIMUM')
    if isinstance(value, dict) and 'properties' in spec:
        require(set(spec.get('required', [])) <= set(value), 'ARTIFACT_SCHEMA_FIELDS')
        if spec.get('additionalProperties') is False:
            require(set(value) <= set(spec['properties']), 'ARTIFACT_SCHEMA_FIELDS')
        for key, item in value.items():
            if key in spec['properties']:
                _validate_shape(item, spec['properties'][key], schema)
    if isinstance(value, list) and 'items' in spec:
        if spec.get('uniqueItems'):
            require(len({canonical_hash(item) for item in value}) == len(value), 'ARTIFACT_SCHEMA_UNIQUE')
        for item in value:
            _validate_shape(item, spec['items'], schema)


def _validate_provenance(record, incident):
    evidence = incident.evidence
    spans = record['source_spans']
    ids = record.get('evidence_ids', record.get('retained_evidence_ids'))
    require([span['evidence_id'] for span in spans] == ids, 'SOURCE_SPAN_JOIN')
    for span in spans:
        require(span['evidence_id'] in evidence, 'SOURCE_SPAN_UNKNOWN')
        source = evidence[span['evidence_id']]
        for key in ('source_file_id', 'redaction_version', 'transform_version'):
            require(span[key] == source[key], 'SOURCE_SPAN_PROVENANCE')
        if source['modality'] == 'metrics':
            require(span['source_row_start'] == source['source_row_start'] and
                    span['source_row_end_exclusive'] == source['source_row_end_exclusive'], 'SOURCE_ROW_SPAN')
        else:
            require(span['source_row_index'] == source['source_row_index'], 'SOURCE_ROW_SPAN')
        if source['modality'] == 'logs':
            require(span['source_char_start'] == 0 and span['source_char_end'] == len(source['text']), 'SOURCE_CHAR_SPAN')
            require(span['source_text_hash'] == hashlib.sha256(source['text'].encode()).hexdigest(), 'SOURCE_TEXT_HASH')
    for mapping in record.get('normalization_map', []):
        require(mapping['evidence_id'] in ids, 'NORMALIZATION_JOIN')
        source_text = evidence[mapping['evidence_id']]['text']
        require(mapping['source_text_hash'] == hashlib.sha256(source_text.encode()).hexdigest(), 'NORMALIZATION_SOURCE_HASH')
        source_cursor, output_cursor, output_parts = 0, 0, []
        for segment in mapping['segments']:
            require(segment['source_start'] == source_cursor and segment['output_start'] == output_cursor,
                    'NORMALIZATION_CONTINUITY')
            require(source_cursor <= segment['source_end'] <= len(source_text), 'NORMALIZATION_RANGE')
            source_slice = source_text[source_cursor:segment['source_end']]
            replacement = source_slice if segment['operation'] == 'copy' else ' '
            require(segment['operation'] == 'copy' or source_slice.isspace(), 'NORMALIZATION_LITERAL_CHANGE')
            require(segment['output_end'] == output_cursor + len(replacement), 'NORMALIZATION_RANGE')
            output_parts.append(replacement)
            source_cursor, output_cursor = segment['source_end'], segment['output_end']
        require(source_cursor == len(source_text), 'NORMALIZATION_COVERAGE')
        require(mapping['rendered_text_hash'] == hashlib.sha256(''.join(output_parts).encode()).hexdigest(),
                'NORMALIZATION_OUTPUT_HASH')


def _validate_records(rowsets, tokenizer, config, ids, incidents):
    """Consumer joins are checked here; exact regeneration checks every span."""
    queries, selections, tokens, bundles = (rowsets[name] for name in ARTIFACT_NAMES)
    schema = read_json(SCHEMA_PATH)
    for name, definition in zip(ARTIFACT_NAMES, ('query', 'selection', 'token_ledger', 'bundle')):
        for row in rowsets[name]:
            _validate_shape(row, schema['$defs'][definition], schema)
    incident_index = {incident.incident_id: incident for incident in incidents}
    require(len(queries) == len(tokens) == len(ids) * 3, 'ARTIFACT_COUNTS')
    require(len(selections) == len(bundles) == len(ids), 'ARTIFACT_COUNTS')
    require({row['incident_id'] for row in queries} == set(ids), 'ARTIFACT_INCIDENTS')
    for rows in (selections, bundles):
        require(len({row['incident_id'] for row in rows}) == len(ids)
                and {row['incident_id'] for row in rows} == set(ids), 'ARTIFACT_INCIDENTS')
    require(len({row['query_id'] for row in queries}) == len(queries), 'DUPLICATE_QUERY_ID')
    require(len({row['query_id'] for row in tokens}) == len(tokens), 'DUPLICATE_TOKEN_QUERY_ID')
    token_index = {row['query_id']: row for row in tokens}
    for incident_id in ids:
        variants = [row for row in queries if row['incident_id'] == incident_id]
        require(sorted(row['representation_id'] for row in variants) == ['R1', 'R2', 'R3'], 'VARIANT_IDS')
        pair = {row['representation_id']: row for row in variants}
        require(pair['R1']['log_evidence_ids'] == pair['R2']['log_evidence_ids'] and
                pair['R1']['source_spans'] == pair['R2']['source_spans'], 'JOINT_LOG_SPANS')
        require(all(row['window'] == incident_index[incident_id].window for row in variants), 'QUERY_WINDOW')
    for row in queries:
        require(row['query_id'] in token_index, 'TOKEN_QUERY_JOIN')
        require(row['query_hash'] == hashlib.sha256(row['query_text'].encode('utf-8')).hexdigest(), 'QUERY_TEXT_HASH')
        actual = tokenizer.count(row['query_text'])
        require(actual <= config['budget']['max_query_tokens'] <= config['tokenizer']['max_length'], 'QUERY_TOKEN_OVERFLOW')
        token = token_index[row['query_id']]
        require(token['incident_id'] == row['incident_id'], 'TOKEN_INCIDENT_JOIN')
        require(token['after_tokens'] == actual and token['query_hash'] == row['query_hash'], 'TOKEN_ACTUAL_COUNT')
        require(token['prefix'] == tokenizer.prefix and token['prefix_and_special_tokens'] == tokenizer.count(''), 'TOKEN_PREFIX_COUNT')
        require(token['retained_evidence_ids'] == row['evidence_ids'] and
                token['source_spans'] == row['source_spans'], 'TOKEN_EVIDENCE_JOIN')
        _validate_provenance(row, incident_index[row['incident_id']])
        _validate_provenance(token, incident_index[row['incident_id']])
    for bundle in bundles:
        require(bundle['bundle_hash'] == canonical_hash({key: value for key, value in bundle.items()
                                                       if key != 'bundle_hash'}), 'BUNDLE_HASH')
        require(bundle['budget']['after_tokens'] == tokenizer.count_bundle(bundle['observation_text'])
                <= config['bundle']['max_tokens'], 'BUNDLE_ACTUAL_COUNT')
        require(bundle['window'] == incident_index[bundle['incident_id']].window, 'BUNDLE_WINDOW')
        _validate_provenance(bundle, incident_index[bundle['incident_id']])


def build_representations(output_dir=DEFAULT_OUTPUT, config_path=DEFAULT_CONFIG,
                          manager_path=DEFAULT_MANAGER, input_dir=DEFAULT_INPUT):
    """Build all 72 train/dev incidents without overwriting reviewed content."""
    output_dir = _output_directory(output_dir)
    contents, manifest = _materialize(config_path, manager_path, input_dir)
    manifest_bytes = canonical_bytes(manifest) + b'\n'
    manifest_path = output_dir / MANIFEST_NAME
    if manifest_path.exists():
        old = read_json(manifest_path)
        same_version = old.get('representation_version') == manifest['representation_version']
        require(manifest_path.read_bytes() == manifest_bytes,
                'SAME_VERSION_DRIFT' if same_version else 'NEW_VERSION_REQUIRES_NEW_DIRECTORY')
        for name, data in contents.items():
            require((output_dir / name).is_file() and (output_dir / name).read_bytes() == data, 'EXISTING_ARTIFACT_DRIFT')
        return manifest
    for name in ARTIFACT_NAMES:
        require(not (output_dir / name).exists(), 'UNMANIFESTED_OUTPUT_EXISTS')
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in contents.items():
        (output_dir / name).write_bytes(data)
    # Written last, so interrupted writes never appear accepted.
    manifest_path.write_bytes(manifest_bytes)
    return manifest


def validate_artifacts(output_dir=DEFAULT_OUTPUT, config_path=DEFAULT_CONFIG,
                       manager_path=DEFAULT_MANAGER, input_dir=DEFAULT_INPUT,
                       receipt_path=None):
    """Verify current inputs/config/code/assets and replay all canonical outputs."""
    output_dir = _output_directory(output_dir)
    manifest_path = output_dir / MANIFEST_NAME
    actual_manifest = read_json(manifest_path)
    contents, expected_manifest = _materialize(config_path, manager_path, input_dir)
    require(actual_manifest == expected_manifest
            and manifest_path.read_bytes() == canonical_bytes(expected_manifest) + b'\n', 'MANIFEST_STALE')
    for name, data in contents.items():
        require((output_dir / name).is_file() and (output_dir / name).read_bytes() == data, 'ARTIFACT_REPLAY_MISMATCH')
    result = {
        'status': 'pass', 'technical_gate': 'pass', 'milestone': '04.variants',
        'query_manifest_hash': sha256(manifest_path),
        **{key: expected_manifest[key] for key in HASH_KEYS},
        'counts': expected_manifest['counts'], 'deterministic_replay': True,
        'test_materialization': 'not_performed',
    }
    if receipt_path is not None:
        receipt = read_json(receipt_path)
        require(isinstance(receipt, dict) and receipt.get('technical_gate') == 'pass', 'REVIEW_RECEIPT_SCHEMA')
        for key in ('query_manifest_hash', *HASH_KEYS):
            require(receipt.get(key) == result[key], 'REVIEW_RECEIPT_STALE')
        evidence = receipt.get('evidence')
        require(isinstance(evidence, list) and evidence, 'REVIEW_EVIDENCE_REQUIRED')
        seen = set()
        for entry in evidence:
            require(isinstance(entry, dict) and set(entry) == {'path', 'sha256'}, 'REVIEW_EVIDENCE_SCHEMA')
            relative = entry['path']
            require(isinstance(relative, str) and relative not in seen, 'REVIEW_DUPLICATE_EVIDENCE')
            require(not Path(relative).is_absolute() and ':' not in relative
                    and '..' not in Path(relative).parts, 'REVIEW_EVIDENCE_PATH')
            candidate = (IMPL / relative).absolute()
            resolved = candidate.resolve()
            require(candidate == resolved and any(resolved.is_relative_to(IMPL / directory)
                    for directory in ('reports', 'tests', 'configs')), 'REVIEW_EVIDENCE_PATH')
            require(resolved.is_file() and sha256(resolved) == entry['sha256'], 'REVIEW_EVIDENCE_STALE')
            seen.add(relative)
        reviews = receipt.get('automated_reviews')
        require(isinstance(reviews, list) and len(reviews) >= 2, 'AUTOMATED_REVIEWS_REQUIRED')
        require({'tester', 'code-reviewer'} <= {review.get('role') for review in reviews}, 'AUTOMATED_REVIEW_ROLES')
        require(all(review.get('actor_kind') == 'codex_agent' and review.get('status') == 'pass'
                    and review.get('reviewer') and review.get('evidence_path') in seen
                    for review in reviews), 'AUTOMATED_REVIEW_EVIDENCE')
    return result
