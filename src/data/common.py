"""Small, fail-closed primitives shared by management and inference tools."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

IMPL = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = IMPL / 'configs/data.yaml'


def research_pack_root():
    raw = os.environ.get('CS221_RESEARCH_PACK_ROOT')
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


ROOT = research_pack_root()
FILES = {'observations.jsonl': 'observations', 'logs-evidence.jsonl': 'logs',
         'metric-summaries.jsonl': 'metrics', 'trace-evidence.jsonl': 'traces'}
INCIDENT = re.compile(r'inc_[0-9a-f]{16}\Z')
PRIVATE_KEYS = {'scenario_family_id', 'family', 'split', 'gold', 'ground_truth',
                'source_case', 'source-case', 'fault', 'injection_time', 'label',
                'root_cause_service', 'local_path', 'source_url', 'private'}
PRIVACY = {
    'email': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    'ipv4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    'bearer': r'(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}',
    'private_key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'aws_access_key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'credential': r'(?i)(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]+',
    'uuid': r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
}
UNSAFE_TEXT = re.compile(r'(?i)(?:fam_[0-9a-f]{16}|(?:^|[\s"\x27])(?:[a-z]:[\\/]|\.\.[\\/])|(?:02_datasets|data/private|acquired/labels|source_case)[\\/=:]|RE[123]-[A-Z]{2}_[A-Za-z0-9_-]+)')


class DataContractError(ValueError):
    def __init__(self, code, opaque_id=''):
        self.code = code
        self.opaque_id = opaque_id if INCIDENT.fullmatch(str(opaque_id)) else ''
        super().__init__(code + (':' + self.opaque_id if self.opaque_id else ''))


def require(condition, code, opaque_id=''):
    if not condition:
        raise DataContractError(code, opaque_id)


def require_research_pack_root():
    root = research_pack_root()
    if root is None:
        raise DataContractError('MISSING_RESEARCH_PACK_ROOT')
    return root


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def canonical_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_KEY')
        result[key] = value
    return result


def parse_json(text):
    try:
        return json.loads(text, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(DataContractError('NONFINITE')))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise DataContractError('INVALID_JSON') from exc


def read_json(path):
    try:
        return parse_json(Path(path).read_text(encoding='utf-8-sig'))
    except UnicodeError as exc:
        raise DataContractError('INVALID_JSON') from exc


def load_config(path=DEFAULT_CONFIG):
    # JSON is a YAML subset; no optional YAML parser or constructors needed.
    value = read_json(path)
    require(isinstance(value, dict), 'CONFIG_SCHEMA')
    require(value.get('api_enabled') is False, 'API_POLICY')
    required = {'schema_version','data_version','source_revision','allowed_fields','expected_counts',
                'incident_ids','inference_sources','source_fields','allowed_roots'}
    require(required <= set(value), 'CONFIG_SCHEMA')
    require(isinstance(value['incident_ids'], list) and all(isinstance(x,str) and INCIDENT.fullmatch(x) for x in value['incident_ids']), 'CONFIG_IDS')
    require(isinstance(value['expected_counts'], dict) and type(value['expected_counts'].get('incidents')) is int, 'CONFIG_COUNTS')
    require(len(value['incident_ids']) == len(set(value['incident_ids'])) == value['expected_counts']['incidents'], 'CONFIG_IDS')
    for key in ('allowed_fields','inference_sources','source_fields','allowed_roots'):
        require(isinstance(value[key], dict), 'CONFIG_SCHEMA')
    for key in ('private_sources', 'source_hashes'):
        if key in value:
            require(isinstance(value[key], dict), 'CONFIG_SCHEMA')
    return value


def read_jsonl(path):
    try:
        with Path(path).open(encoding='utf-8-sig') as handle:
            return [parse_json(line) for line in handle if line.strip()]
    except UnicodeError as exc:
        raise DataContractError('INVALID_JSON') from exc


def write_json(path, value):
    path = writable_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b'\n')


def write_jsonl(path, rows):
    path = writable_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as handle:
        for row in rows:
            handle.write(canonical_bytes(row) + b'\n')


def writable_path(path):
    """Refuse any source overwrite or redirected output, including junctions."""
    path = Path(path).absolute()
    resolved = path.resolve()
    require(resolved == path and resolved.is_relative_to(IMPL.resolve()), 'OUTPUT_PATH')
    return resolved


def safe_path(root, relative, allowed_roots):
    """Resolve before opening; reject traversal, absolute paths, ADS and escapes."""
    root = Path(root).resolve()
    text = str(relative).replace('\\', '/')
    require(bool(text) and ':' not in text and not PureWindowsPath(text).is_absolute()
            and not PurePosixPath(text).is_absolute() and '..' not in PurePosixPath(text).parts,
            'PATH_FORBIDDEN')
    candidate = (root / text).resolve()
    require(candidate.is_relative_to(root), 'PATH_ESCAPE')
    require(candidate == (root / text).absolute(), 'PATH_ALIAS')
    allowed = [(root / entry).resolve() for entry in allowed_roots]
    require(all(entry.is_relative_to(root) for entry in allowed), 'PATH_ESCAPE')
    # Lexical AND resolved containment prevent aliases into a disallowed role.
    require(any((root / text).is_relative_to(root / entry) and candidate.is_relative_to(resolved)
                for entry, resolved in zip(allowed_roots, allowed)), 'PATH_FORBIDDEN')
    require(candidate.is_file(), 'MISSING_FILE')
    return candidate


def redact(text, incident_id):
    require(isinstance(text, str), 'FIELD_TYPE', incident_id)
    for kind, pattern in PRIVACY.items():
        text = re.sub(pattern, lambda match: '[' + kind.upper() + '_' +
                      hashlib.sha256((incident_id + ':' + match.group()).encode()).hexdigest()[:12] + ']', text)
    require(not UNSAFE_TEXT.search(text), 'PRIVATE_VALUE', incident_id)
    return text


def timestamp(value):
    require(isinstance(value, str), 'TIMESTAMP_TYPE')
    try:
        dt = datetime.fromisoformat(value)
        require(dt.utcoffset() is not None and dt.utcoffset().total_seconds() == 0, 'TIMEZONE')
        result = dt.timestamp()
        require(1_000_000_000 < result < 3_000_000_000, 'TIME_UNIT')
        return result
    except (ValueError, OverflowError) as exc:
        raise DataContractError('TIMESTAMP_INVALID') from exc


def _safe_value(value, incident_id):
    if isinstance(value, dict):
        raise DataContractError('NESTED_FIELD', incident_id)
    if isinstance(value, list):
        for item in value:
            require(isinstance(item, str), 'FIELD_TYPE', incident_id)
            _safe_value(item, incident_id)
    elif isinstance(value, str):
        require(not UNSAFE_TEXT.search(value), 'PRIVATE_VALUE', incident_id)
        require(all(re.search(pattern, value) is None for pattern in PRIVACY.values()), 'PRIVACY_PATTERN', incident_id)
    elif isinstance(value, float):
        require(math.isfinite(value), 'NONFINITE', incident_id)
    else:
        require(value is None or isinstance(value, (int, bool)), 'FIELD_TYPE', incident_id)


def validate_record(kind, record, config):
    require(isinstance(record, dict), 'RECORD_TYPE')
    incident = record.get('incident_id', '')
    require(isinstance(incident, str) and INCIDENT.fullmatch(incident), 'INCIDENT_ID')
    require(not PRIVATE_KEYS.intersection(record), 'PRIVATE_FIELD', incident)
    require(set(record) == set(config['allowed_fields'][kind]), 'SCHEMA_FIELDS', incident)
    for value in record.values():
        _safe_value(value, incident)
    lists = {'service_inventory', 'input_source_ids', 'log_span_ids', 'metric_summary_ids', 'trace_span_ids', 'evidence_file_ids'}
    integers = {'source_row_index', 'source_row_start', 'source_row_end_exclusive', 'row_count', 'null_count', 'status_code', 'duration_raw'}
    numbers = {'minimum', 'maximum', 'mean', 'first_quarter_mean', 'last_quarter_mean', 'change_score'}
    for key, value in record.items():
        if key in lists:
            require(isinstance(value, list) and len(value) == len(set(value)), 'FIELD_TYPE', incident)
        elif key in integers:
            require((key == 'status_code' and value is None) or (type(value) is int and value >= 0), 'FIELD_TYPE', incident)
        elif key in numbers:
            require(value is None or type(value) in (int, float), 'FIELD_TYPE', incident)
        elif key == 'telemetry_is_synthetic':
            require(type(value) is bool, 'FIELD_TYPE', incident)
        else:
            require(isinstance(value, str), 'FIELD_TYPE', incident)
    if kind in ('observations', 'index', 'metrics'):
        require(timestamp(record['observation_start']) < timestamp(record['observation_end_exclusive']), 'WINDOW', incident)
    if kind in ('logs', 'traces', 'metrics'):
        require(record['modality'] == kind, 'MODALITY', incident)
        require(record['source_file_id'] == incident + ':' + kind, 'FOREIGN_SOURCE', incident)
        require(record['evidence_id'].startswith(incident + ':' + {'logs':'log','traces':'trace','metrics':'metric'}[kind] + ':'), 'FOREIGN_EVIDENCE', incident)
    if kind in ('logs', 'traces'):
        require(record['evidence_id'] == incident + ':' + ('log' if kind == 'logs' else 'trace') + ':' + str(record['source_row_index']), 'ROW_ID', incident)
        timestamp(record['timestamp'])
    if kind == 'metrics':
        require(record['evidence_id'] == incident + ':metric:' + record['metric_name'], 'ROW_ID', incident)
        require(record['source_row_start'] == 0 and record['source_row_end_exclusive'] == record['row_count'] and record['row_count'] > 0, 'ROW_RANGE', incident)
        require(0 <= record['null_count'] <= record['row_count'], 'NULL_COUNT', incident)
        state = 'all_missing' if record['null_count'] == record['row_count'] else 'partial' if record['null_count'] else 'complete'
        reason = {'all_missing':'all_source_values_null','partial':'source_null_values','complete':'none'}[state]
        require(record['missing_state'] == state and record['missing_reason'] == reason, 'NULL_STATE', incident)
        if state == 'all_missing':
            require(all(record[key] is None for key in numbers), 'NULL_IMPUTED', incident)
        require(timestamp(record['source_sample_end_inclusive']) + 1 == timestamp(record['observation_end_exclusive']), 'END_CONVERSION', incident)
        require(record['unit'] == 'unknown', 'UNIT_SEMANTICS', incident)
    if kind == 'traces':
        require(record['duration_unit'] == 'unknown' and record['status_code_semantics'] == 'unknown', 'UNIT_SEMANTICS', incident)
    return True


def validate_inference(root, config=None, *, require_live_transform=False):
    """Source-free strict consumer gate; never opens private metadata.

    Frozen bundles bind file hashes. Live exporter identity is optional because
    portable implementation-root edits change common.py bytes without changing
    released inference bytes.
    """
    import pyarrow.parquet as pq
    root = Path(root).resolve()
    config = config or load_config()
    manifest = read_json(safe_path(root, 'input-manifest.json', ['.']))
    require(isinstance(manifest, dict) and set(manifest) == {
        'schema_version','data_version','source_revision','source_hash','config_hash',
        'transform_hash','content_hash','incident_count','files'}, 'MANIFEST_SCHEMA')
    require(type(manifest['incident_count']) is int, 'MANIFEST_SCHEMA')
    for key in ('source_hash','config_hash','transform_hash','content_hash'):
        require(isinstance(manifest[key], str) and re.fullmatch(r'[0-9a-f]{64}', manifest[key]), 'MANIFEST_HASH')
    require(manifest['schema_version'] == config['schema_version'] and
            manifest['data_version'] == config['data_version'] and
            manifest['source_revision'] == config['source_revision'], 'MANIFEST_VERSION')
    from .export_inference_data import public_policy, transform_hash
    require(manifest['config_hash'] == canonical_hash(public_policy(config)), 'CONFIG_HASH')
    if require_live_transform:
        require(manifest['transform_hash'] == transform_hash(), 'TRANSFORM_HASH')
    expected_names = set(FILES) | {'incident-index.parquet'}
    entries = manifest.get('files', [])
    require(isinstance(entries, list) and len(entries) == len(expected_names), 'MANIFEST_FILES')
    require(all(isinstance(entry, dict) for entry in entries), 'MANIFEST_SCHEMA')
    require(all(isinstance(entry.get('path'), str) for entry in entries), 'MANIFEST_SCHEMA')
    require({entry.get('path') for entry in entries} == expected_names, 'MANIFEST_FILES')
    require(manifest['content_hash'] == canonical_hash(entries), 'CONTENT_HASH')
    require({p.name for p in root.iterdir()} == expected_names | {'input-manifest.json'}, 'EXTRA_FILE')
    data = {}
    for entry in entries:
        require(set(entry) == {'path', 'sha256', 'bytes', 'rows'}, 'MANIFEST_SCHEMA')
        require(all(type(entry[key]) is int and entry[key] >= 0 for key in ('bytes','rows')) and
                isinstance(entry['sha256'],str) and re.fullmatch(r'[0-9a-f]{64}',entry['sha256']), 'MANIFEST_SCHEMA')
        path = safe_path(root, entry['path'], ['.'])
        require(path.stat().st_size == entry['bytes'] and sha256(path) == entry['sha256'], 'HASH_MISMATCH')
        kind = FILES.get(entry['path'], 'index')
        rows = pq.read_table(path).to_pylist() if kind == 'index' else read_jsonl(path)
        require(len(rows) == entry['rows'], 'ROW_COUNT')
        for row in rows:
            validate_record(kind, row, config)
        data[kind] = rows
    obs = {row['incident_id']: row for row in data['observations']}
    require(len(obs) == len(data['observations']) == manifest['incident_count'] == config['expected_counts']['incidents'], 'INCIDENT_COUNT')
    require(set(obs) == set(config['incident_ids']), 'INCIDENT_IDS')
    index = {row['incident_id']: row for row in data['index']}
    require(len(index) == len(data['index']) and set(index) == set(obs), 'INDEX_IDS')
    evidence = {}
    for kind in ('metrics', 'logs', 'traces'):
        for row in data[kind]:
            incident = row['incident_id']
            require(incident in obs, 'FOREIGN_INCIDENT', incident)
            require(row['evidence_id'] not in evidence, 'DUPLICATE_EVIDENCE', incident)
            evidence[row['evidence_id']] = row
            window = obs[incident]
            start, end = timestamp(window['observation_start']), timestamp(window['observation_end_exclusive'])
            if kind == 'metrics':
                require(timestamp(row['observation_start']) == start and timestamp(row['observation_end_exclusive']) == end, 'WINDOW', incident)
            else:
                require(start <= timestamp(row['timestamp']) < end, 'WINDOW', incident)
    for incident, row in obs.items():
        ix = index[incident]
        require(all(ix[key] == row[key] for key in ('observation_start', 'observation_end_exclusive')), 'INDEX_WINDOW', incident)
        sources = {incident + ':' + kind for kind in ('metrics', 'logs', 'traces')}
        require(set(ix['evidence_file_ids']) == set(row['input_source_ids']) == sources, 'SOURCE_IDS', incident)
        for key, modality in [('log_span_ids','logs'),('metric_summary_ids','metrics'),('trace_span_ids','traces')]:
            require(bool(row[key]), 'MISSING_MODALITY', incident)
            for evidence_id in row[key]:
                require(evidence_id in evidence and evidence[evidence_id]['incident_id'] == incident and evidence[evidence_id]['modality'] == modality, 'EVIDENCE_JOIN', incident)
            if modality in ('logs','traces'):
                require(set(row[key]) == {ref for ref,item in evidence.items() if item['incident_id'] == incident and item['modality'] == modality}, 'EVIDENCE_COVERAGE', incident)
    return {'status': 'pass', 'incident_count': len(obs), 'evidence_count': len(evidence),
            'rows': {kind:len(rows) for kind, rows in data.items()}, 'manifest_hash': sha256(root/'input-manifest.json')}
