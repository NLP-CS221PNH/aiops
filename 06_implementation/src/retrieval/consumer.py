"""Verified ranking reader for pooling (06), context (07), and evaluation (08)."""
from __future__ import annotations
import re

from .common import (IMPL, digest, exact_fields, local_schema, read_json, require, safe_path, sha256)
from .fusion import validate_ranking


def read_run(manifest_path, *, expected_manifest_hash=None, expected=None):
    path = safe_path(manifest_path, write=True)
    if expected_manifest_hash is not None:
        require(sha256(path) == expected_manifest_hash, 'RUN_MANIFEST_HASH')
    manifest = read_json(path)
    from jsonschema import Draft202012Validator
    schema_path = safe_path('schemas/retrieval-run.schema.json')
    schema = local_schema(read_json(schema_path))
    validator = Draft202012Validator(schema)
    require(not list(validator.iter_errors(manifest)), 'RUN_MANIFEST_SCHEMA')
    spec = manifest['specification']
    require(spec.get('run_schema_hash') == sha256(schema_path), 'RUN_SCHEMA_HASH')
    require(manifest['fingerprint'] == digest(spec), 'RUN_FINGERPRINT')
    require(spec['config_hash'] == digest(spec['config'])
            and spec['environment_hash'] == digest(spec['environment'])
            and spec['implementation_hash'] == digest(spec['implementation_hashes']), 'RUN_SPEC_HASHES')
    for key, value in (expected or {}).items():
        require(spec.get(key) == value, 'CONSUMER_PROVENANCE_MISMATCH:' + key)
    require(len(spec['conditions']) == len(set(spec['conditions'])) and spec['conditions'], 'RUN_CONDITIONS')
    queries = {q['incident_id']: q for q in spec['queries']}
    chunks = {c['chunk_id']: c for c in spec['chunks']}
    require(len(queries) == len(spec['queries']) and len(chunks) == len(spec['chunks']), 'RUN_SPEC_DUPLICATE')
    expected_keys = {iid + ':' + condition for iid in queries for condition in spec['conditions']}
    entries = {entry['record_key']: entry for entry in manifest['records']}
    require(len(entries) == len(manifest['records']) and set(entries) == expected_keys, 'RUN_RECORD_COMPLETENESS')
    checkpoint_path = safe_path(path.parent / 'checkpoint-index.json', write=True)
    require(sha256(checkpoint_path) == manifest['checkpoint_index_sha256'], 'RUN_CHECKPOINT_INDEX_HASH')
    index = read_json(checkpoint_path)
    require(index.get('fingerprint') == manifest['fingerprint'] and index.get('specification') == spec, 'RUN_INDEX_BINDING')
    require(set(index['records']) == {key for key, entry in entries.items() if entry['status'] != 'pending'}, 'RUN_INDEX_RECORD_SET')
    rows = []
    record_validator = Draft202012Validator({'$defs': schema['$defs'], '$ref': '#/$defs/record'})
    for key, entry in entries.items():
        if entry['status'] == 'pending':
            require(entry['path'] is None and entry['sha256'] is None and entry['candidate_count'] is None, 'PENDING_RECORD')
            continue
        filename = index['records'][key]['path']
        require(re.fullmatch(digest(key) + r'-[0-9a-f]{64}\.json', filename) is not None, 'RUN_RECORD_PATH')
        require(entry['path'] == 'records/' + filename, 'RUN_RECORD_PATH')
        record_path = safe_path(path.parent / entry['path'], write=True)
        require(sha256(record_path) == entry['sha256'], 'RUN_RECORD_CHECKSUM')
        require(index['records'][key] == {'path': filename, 'sha256': entry['sha256']}, 'RUN_INDEX_ENTRY')
        row = read_json(record_path)
        require(filename == digest(key) + '-' + digest(row) + '.json', 'RUN_RECORD_CONTENT_ID')
        require(not list(record_validator.iter_errors(row)), 'RUN_RECORD_SCHEMA')
        require(row['record_key'] == key and row['run_id'] == manifest['run_id']
                and row['fingerprint'] == manifest['fingerprint'], 'RUN_RECORD_BINDING')
        require(row['incident_id'] in queries and row['condition'] in spec['conditions']
                and key == row['incident_id'] + ':' + row['condition'], 'RUN_RECORD_ID')
        query = queries[row['incident_id']]
        for name in ('query_hash', 'window_hash', 'task_version', 'representation_id'):
            require(row[name] == query[name], 'RUN_QUERY_PROVENANCE:' + name)
        for name in ('corpus_hash', 'config_hash'):
            require(row[name] == spec[name], 'RUN_PROVENANCE:' + name)
        require(row['synthetic'] == manifest['synthetic'] == (spec['mode'] == 'fixture'), 'RUN_SYNTHETIC_LABEL')
        require(row['status'] == entry['status'] and row['candidate_count'] == entry['candidate_count']
                == len(row['hits']), 'RUN_CANDIDATE_COUNT')
        require(row['requested_depth'] == spec['depth'] and len(row['hits']) <= spec['depth'], 'RUN_DEPTH')
        validate_ranking(row['hits'])
        ordered = sorted(row['hits'], key=lambda h: (-h['score'], h['chunk_id']))
        require(row['hits'] == ordered, 'RUN_SCORE_OR_TIE_ORDER')
        for hit in row['hits']:
            require(hit['chunk_id'] in chunks, 'RUN_UNKNOWN_CHUNK')
            chunk = chunks[hit['chunk_id']]
            require(hit['document_id'] == chunk['document_id'] and hit['content_hash'] == chunk['content_hash'], 'RUN_CHUNK_PROVENANCE')
        require(row['empty'] == (row['status'] == 'complete' and not row['hits'])
                and row['short'] == (row['status'] == 'complete' and len(row['hits']) < spec['depth']), 'RUN_EMPTY_SHORT')
        require((row['status'] == 'complete' and row['error'] is None)
                or (row['status'] == 'failed' and row['error'] is not None and not row['hits']), 'RUN_ERROR_STATE')
        rows.append(row)
    counts = {status: sum(entry['status'] == status for entry in entries.values()) for status in ('complete', 'failed', 'pending')}
    require(manifest['counts'] == counts, 'RUN_COUNTS')
    state = 'interrupted' if counts['pending'] else ('complete_with_errors' if counts['failed'] else 'complete')
    require(manifest['state'] == state, 'RUN_STATE')
    return manifest, rows


def read_hits(manifest_path, incident_id, condition, *, limit=5, expected=None, expected_manifest_hash=None):
    require(type(limit) is int and 0 <= limit <= 50, 'HITS_LIMIT')
    manifest, rows = read_run(manifest_path, expected=expected, expected_manifest_hash=expected_manifest_hash)
    selected = [row for row in rows if row['incident_id'] == incident_id and row['condition'] == condition]
    require(len(selected) == 1, 'HITS_RECORD_MISSING_OR_PENDING')
    row = selected[0]
    return {'run_id': manifest['run_id'], 'incident_id': incident_id, 'condition': condition,
            'status': row['status'], 'error': row['error'], 'query_hash': row['query_hash'],
            'corpus_hash': row['corpus_hash'], 'config_hash': row['config_hash'],
            'hits': row['hits'][:limit], 'available_count': row['candidate_count'],
            'synthetic': row['synthetic']}


def comparable_runs(manifest_paths):
    manifests = [read_run(path)[0] for path in manifest_paths]
    require(bool(manifests), 'COMPARISON_EMPTY')
    fields = ('corpus_hash', 'corpus_manifest_hash', 'query_manifest_hash', 'input_manifest_hash',
              'representation', 'task_version', 'queries', 'chunks', 'mode')
    first = manifests[0]['specification']
    for manifest in manifests[1:]:
        for field in fields:
            require(manifest['specification'][field] == first[field], 'INCOMPARABLE_RUNS:' + field)
    return manifests
