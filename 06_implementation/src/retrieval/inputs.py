"""Strict allowlisted input adapters. Never read a split map, gold or qrels."""
from __future__ import annotations

from pathlib import Path
import re

from .common import (HASH, IMPL, TOKENIZER_HASH, digest, exact_fields, finite, local_schema, read_json, read_jsonl,
                     reject_private, require, safe_path, sha256, text_hash)

CONFIG_FIELDS = {'schema_version', 'code_version', 'content_policy', 'task_version',
                 'corpus_manifest', 'corpus_manifest_sha256', 'query_manifest',
                 'query_manifest_sha256', 'query_file', 'query_schema', 'query_schema_sha256',
                 'input_manifest', 'input_manifest_sha256', 'representation', 'depth',
                 'bm25', 'dense', 'rrf', 'reranker', 'cache_dir', 'run_root', 'fixture'}
MODEL_FIELDS = {'model_id', 'revision', 'model_dir', 'assets', 'query_prefix',
                'passage_prefix', 'normalize_embeddings', 'max_tokens', 'batch_size',
                'device', 'dtype'}


def load_config(path=IMPL / 'configs/retrieval.yaml'):
    config = read_json(safe_path(path))
    return validate_config(config)


def validate_config(config):
    exact_fields(config, CONFIG_FIELDS, 'CONFIG_FIELDS')
    require(config['schema_version'] == 'cs221-retrieval-config-v1', 'CONFIG_VERSION')
    require(config['code_version'] == 'retrieval-v1', 'CODE_VERSION')
    require(config['content_policy'] == 'section_heading + newline + text', 'CONTENT_POLICY')
    require(isinstance(config['task_version'], str) and bool(config['task_version']), 'TASK_VERSION')
    require(type(config['fixture']) is bool, 'CONFIG_FIXTURE')
    require(type(config['depth']) is int and 1 <= config['depth'] <= 50, 'DEPTH')
    require(config['representation'] in {'R1', 'R2', 'R3'}, 'REPRESENTATION')
    exact_fields(config['bm25'], {'k1', 'b', 'tokenizer_version'}, 'BM25_CONFIG')
    require(finite(config['bm25']['k1']) and config['bm25']['k1'] > 0
            and finite(config['bm25']['b']) and 0 <= config['bm25']['b'] <= 1, 'BM25_PARAMETERS')
    from .bm25 import TOKENIZER_VERSION
    require(config['bm25']['tokenizer_version'] == TOKENIZER_VERSION, 'BM25_TOKENIZER')
    exact_fields(config['dense'], MODEL_FIELDS, 'DENSE_CONFIG')
    model = config['dense']
    require(model['model_id'] == 'intfloat/e5-small-v2'
            and model['revision'] == 'ffb93f3bd4047442299a41ebb6fa998a38507c52', 'PINNED_E5_REVISION')
    require(model['query_prefix'] == 'query: ' and model['passage_prefix'] == 'passage: '
            and model['normalize_embeddings'] is True, 'E5_POLICY')
    require(type(model['max_tokens']) is int and model['max_tokens'] == 512, 'SHARED_QUERY_BUDGET')
    require(type(model['batch_size']) is int and model['batch_size'] > 0, 'BATCH_SIZE')
    require(model['device'] == 'cpu' and model['dtype'] == 'float32', 'CPU_RUNTIME_POLICY')
    require(isinstance(model['assets'], dict), 'MODEL_ASSETS')
    for name, value in model['assets'].items():
        require(isinstance(name, str) and Path(name).name == name
                and isinstance(value, str) and HASH.fullmatch(value), 'MODEL_ASSET_SCHEMA')
    exact_fields(config['rrf'], {'constant', 'weights'}, 'RRF_CONFIG')
    require(finite(config['rrf']['constant']) and config['rrf']['constant'] >= 0, 'RRF_CONSTANT')
    require(isinstance(config['rrf']['weights'], list) and len(config['rrf']['weights']) == 2
            and all(finite(v) and v > 0 for v in config['rrf']['weights']), 'RRF_WEIGHTS')
    exact_fields(config['reranker'], {'enabled', 'model_id', 'revision', 'model_dir',
                 'assets', 'max_tokens', 'batch_size', 'device'}, 'RERANK_CONFIG')
    rerank = config['reranker']
    require(type(rerank['enabled']) is bool and rerank['model_id'] == 'BAAI/bge-reranker-base'
            and rerank['revision'] == '2cfc18c9415c912f9d8155881c133215df768a70', 'RERANK_REVISION')
    require(type(rerank['max_tokens']) is int and rerank['max_tokens'] == 512
            and type(rerank['batch_size']) is int and rerank['batch_size'] > 0
            and rerank['device'] == 'cpu' and isinstance(rerank['assets'], dict), 'RERANK_POLICY')
    for name, value in rerank['assets'].items():
        require(isinstance(name, str) and Path(name).name == name
                and isinstance(value, str) and HASH.fullmatch(value), 'MODEL_ASSET_SCHEMA')
    for field in ('corpus_manifest_sha256', 'query_manifest_sha256',
                  'query_schema_sha256', 'input_manifest_sha256'):
        require(isinstance(config[field], str) and HASH.fullmatch(config[field]), 'CONFIG_HASH:' + field)
    for field in ('corpus_manifest', 'query_manifest', 'query_schema', 'input_manifest'):
        safe_path(config[field])
    safe_path(model['model_dir'], roots=('vendor', '.test-work/retrieval'))
    safe_path(rerank['model_dir'], roots=('vendor', '.test-work/retrieval'))
    safe_path(config['cache_dir'], write=True)
    safe_path(config['run_root'], write=True)
    return config


def _verified(path, expected):
    path = safe_path(path)
    require(path.is_file(), 'INPUT_MISSING:' + path.name)
    require(sha256(path) == expected, 'INPUT_HASH:' + path.name)
    return read_json(path)


def _fixture_path(path):
    return safe_path(path, roots=('tests/fixtures/retrieval', '.test-work/retrieval'))


def load_corpus(config, *, mode='pilot'):
    validate_config(config)
    path = safe_path(config['corpus_manifest'])
    manifest = _verified(path, config['corpus_manifest_sha256'])
    require(mode in {'pilot', 'frozen', 'fixture'}, 'MODE')
    fixture = mode == 'fixture'
    require(config['fixture'] is fixture, 'FIXTURE_MODE_MISMATCH')
    if fixture:
        _fixture_path(path)
        require(manifest.get('schema_version') == 'cs221-synthetic-corpus-v1'
                and manifest.get('synthetic') is True, 'SYNTHETIC_CORPUS_REQUIRED')
    else:
        require(manifest.get('schema_version') == 'cs221-corpus-manifest-v1', 'CORPUS_SCHEMA')
        # This gate intentionally fails for the current Plan03 candidate. No
        # candidate whitelist or filename can stand in for a reviewed release.
        require(manifest.get('status') == 'released' and manifest.get('release_ready') is True
                and manifest.get('validation_receipt', {}).get('release_ready') is True,
                'CORPUS_RELEASE_PENDING: owner A/B must supply a reviewed release')
        require(manifest.get('tokenizer', {}).get('sha256') == TOKENIZER_HASH
                and manifest['tokenizer'].get('revision') == config['dense']['revision']
                and manifest['tokenizer'].get('max_length') == config['dense']['max_tokens'], 'CORPUS_TOKENIZER_POLICY')
        if config['dense']['assets']:
            require(config['dense']['assets'].get('tokenizer.json') == TOKENIZER_HASH, 'MODEL_TOKENIZER_POLICY')
    whitelist = manifest.get('index_whitelist')
    require(isinstance(whitelist, list) and all(isinstance(v, str) and v for v in whitelist)
            and len(whitelist) == len(set(whitelist)), 'CORPUS_WHITELIST')
    require(fixture or bool(whitelist), 'CORPUS_NO_RELEASED_DOCUMENTS')
    chunk_path = safe_path(path.parent / 'chunks.jsonl')
    expected = manifest.get('derived_file_hashes', {}).get('chunks.jsonl')
    require(isinstance(expected, str) and HASH.fullmatch(expected), 'CHUNKS_HASH_REQUIRED')
    require(sha256(chunk_path) == expected, 'CHUNKS_FILE_HASH')
    require(isinstance(manifest.get('corpus_hash'), str) and HASH.fullmatch(manifest['corpus_hash']), 'CORPUS_HASH')
    chunks, seen = [], set()
    for row in read_jsonl(chunk_path):
        require(isinstance(row, dict), 'CHUNK_SCHEMA')
        for key in ('chunk_id', 'document_id', 'content', 'text', 'section_heading', 'content_hash', 'corpus_hash'):
            require(isinstance(row.get(key), str), 'CHUNK_FIELD:' + key)
        require(row['chunk_id'] and row['document_id'] and row['chunk_id'] not in seen, 'CHUNK_DUPLICATE_OR_EMPTY_ID')
        seen.add(row['chunk_id'])
        require(row['content'] == row['section_heading'] + '\n' + row['text'], 'CHUNK_CONTENT_POLICY')
        require(row['content_hash'] == text_hash(row['content']), 'CHUNK_CONTENT_HASH')
        require(row['corpus_hash'] == manifest['corpus_hash'], 'CHUNK_CORPUS_HASH')
        if fixture:
            require(row['chunk_id'].startswith('fixture-') and row['document_id'].startswith('fixture-'), 'FIXTURE_ID')
        if row['document_id'] in whitelist:
            require(fixture or (row.get('index_eligible') is True and row.get('review_state') == 'reviewed'), 'CHUNK_NOT_REVIEWED')
            # Only these fields enter the retrieval engine. Applicability and
            # source/citation metadata remain in the upstream registry.
            chunks.append({key: row[key] for key in ('chunk_id', 'document_id', 'content', 'content_hash')})
    require(set(c['document_id'] for c in chunks) == set(whitelist), 'WHITELIST_DOCUMENT_MISSING')
    require(fixture or bool(chunks), 'EMPTY_RELEASED_CORPUS')
    return sorted(chunks, key=lambda c: c['chunk_id']), manifest


def frozen_policy_hash(config):
    """Pre-test choices, excluding later test artifact paths and hashes."""
    return digest({key: config[key] for key in ('code_version', 'content_policy', 'task_version',
                   'representation', 'depth', 'bm25', 'dense', 'rrf', 'reranker')})


def load_inputs(config, incident_list, *, mode='pilot', f1_path=None, trusted_f1_hash=None,
                test_input_manifest=None, trusted_test_input_hash=None):
    validate_config(config)
    require(mode in {'pilot', 'frozen', 'fixture'}, 'MODE')
    # Check the test gate before loading any test or real corpus text.
    frozen = None
    test_input = None
    if mode == 'frozen':
        require(f1_path is not None and isinstance(trusted_f1_hash, str)
                and HASH.fullmatch(trusted_f1_hash), 'F1_AUTHENTICATED_HASH_REQUIRED')
        frozen = _verified(f1_path, trusted_f1_hash)
        require(frozen.get('gate') == 'F1' and frozen.get('status') == 'frozen'
                and frozen.get('owner_plan') == '08', 'F1_REQUIRED')
        from .runner import implementation_hashes, environment
        for key, value in {'retrieval_policy_hash': frozen_policy_hash(config),
                           'corpus_manifest_hash': config['corpus_manifest_sha256'],
                           'input_manifest_hash': config['input_manifest_sha256'],
                           'implementation_hash': digest(implementation_hashes()),
                           'environment_hash': digest(environment()),
                           'query_schema_hash': config['query_schema_sha256'],
                           'tokenizer_hash': TOKENIZER_HASH}.items():
            require(frozen.get(key) == value, 'F1_HASH_MISMATCH:' + key)
        # F1 precedes test materialization. A separate owner08 receipt binds the
        # later test inputs to that frozen policy, never rewriting F1 itself.
        require(test_input_manifest is not None and isinstance(trusted_test_input_hash, str)
                and HASH.fullmatch(trusted_test_input_hash), 'TEST_INPUT_AUTHENTICATED_HASH_REQUIRED')
        test_input = _verified(test_input_manifest, trusted_test_input_hash)
        exact_fields(test_input, {'schema_version', 'owner_plan', 'f1_hash', 'input_manifest_hash',
                     'query_manifest_hash', 'incident_ids', 'query_hashes'}, 'TEST_INPUT_SCHEMA')
        require(test_input['schema_version'] == 'cs221-frozen-retrieval-input-v1'
                and test_input['owner_plan'] == '08', 'TEST_INPUT_SCHEMA')
        require(test_input['f1_hash'] == trusted_f1_hash
                and test_input['input_manifest_hash'] == config['input_manifest_sha256']
                and test_input['query_manifest_hash'] == config['query_manifest_sha256'], 'TEST_INPUT_HASH_MISMATCH')
    chunks, corpus = load_corpus(config, mode=mode)
    query_manifest_path = safe_path(config['query_manifest'])
    query_manifest = _verified(query_manifest_path, config['query_manifest_sha256'])
    allowlist = read_json(safe_path(incident_list))
    exact_fields(allowlist, {'schema_version', 'mode', 'incident_ids', 'query_manifest_hash'}, 'ALLOWLIST_SCHEMA')
    require(allowlist['schema_version'] == 'cs221-retrieval-allowlist-v1'
            and allowlist['mode'] == mode
            and allowlist['query_manifest_hash'] == config['query_manifest_sha256'], 'ALLOWLIST_BINDING')
    ids = allowlist['incident_ids']
    require(isinstance(ids, list) and ids and all(isinstance(v, str) and v for v in ids)
            and len(ids) == len(set(ids)), 'ALLOWLIST_IDS')
    require(Path(config['query_file']).name == config['query_file'], 'QUERY_FILENAME')
    query_path = safe_path(query_manifest_path.parent / config['query_file'])
    fixture = mode == 'fixture'
    if fixture:
        _fixture_path(query_manifest_path)
        _fixture_path(query_path)
        require(query_manifest.get('schema_version') == 'cs221-synthetic-queries-v1'
                and query_manifest.get('synthetic') is True, 'SYNTHETIC_QUERIES_REQUIRED')
    else:
        require(query_manifest.get('schema_version') == 'cs221-query-manifest-v1'
                and query_manifest.get('milestone') == '04.variants', 'QUERY_MANIFEST_SCHEMA')
        if mode == 'pilot':
            require(config['query_file'] == 'variants.train-dev.jsonl'
                    and query_manifest.get('test_materialization') == 'not_performed_requires_plan08_F1', 'PILOT_TEST_BOUNDARY')
        else:
            require(query_manifest.get('materialization_role') == 'test', 'FROZEN_TEST_INPUT_REQUIRED')
    entries = [entry for entry in query_manifest.get('outputs', []) if entry.get('path') == config['query_file']]
    require(len(entries) == 1 and sha256(query_path) == entries[0].get('sha256'), 'QUERY_FILE_HASH')
    input_manifest = _verified(config['input_manifest'], config['input_manifest_sha256'])
    require(query_manifest.get('input_manifest_hash') == config['input_manifest_sha256'], 'QUERY_INPUT_MANIFEST')
    schema = local_schema(_verified(config['query_schema'], config['query_schema_sha256']))
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator({'$defs': schema.get('$defs', {}), '$ref': '#/$defs/query'})
    queries, seen = [], set()
    rows = read_jsonl(query_path)
    require(len(rows) == entries[0].get('rows'), 'QUERY_ROW_COUNT')
    for row in rows:
        reject_private(row)
        errors = sorted(validator.iter_errors(row), key=lambda error: str(error.path))
        require(not errors, 'QUERY_SCHEMA:' + (str(list(errors[0].path)) if errors else ''))
        pair = (row['incident_id'], row['representation_id'])
        require(pair not in seen, 'QUERY_DUPLICATE')
        seen.add(pair)
        require(row['query_hash'] == text_hash(row['query_text']), 'QUERY_TEXT_HASH:' + row['incident_id'])
        require(row['input_manifest_hash'] == config['input_manifest_sha256'], 'QUERY_INPUT_HASH')
        if fixture:
            require(row['incident_id'].startswith('fixture-'), 'FIXTURE_ID')
        else:
            require(re.fullmatch(r'inc_[0-9a-f]{16}', row['incident_id']) is not None, 'INCIDENT_ID')
            require(row['config_hash'] == query_manifest['config_content_hash'], 'QUERY_CONFIG_HASH')
            require(row['tokenizer_hash'] == TOKENIZER_HASH, 'QUERY_TOKENIZER_POLICY')
        if row['incident_id'] in ids and row['representation_id'] == config['representation']:
            queries.append({'incident_id': row['incident_id'], 'representation_id': row['representation_id'],
                            'query_text': row['query_text'], 'query_hash': row['query_hash'],
                            'window_hash': digest(row['window']), 'task_version': config['task_version']})
    require({q['incident_id'] for q in queries} == set(ids), 'ALLOWLIST_QUERY_MISSING')
    if frozen is not None:
        require(test_input['incident_ids'] == sorted(ids), 'TEST_INPUT_INCIDENT_ALLOWLIST')
        require(test_input['query_hashes'] == {q['incident_id']: q['query_hash'] for q in queries}, 'TEST_INPUT_ACTUAL_QUERY_HASHES')
    return {'chunks': chunks, 'queries': sorted(queries, key=lambda q: q['incident_id']),
            'corpus_hash': corpus['corpus_hash'], 'corpus_manifest_hash': config['corpus_manifest_sha256'],
            'query_manifest_hash': config['query_manifest_sha256'], 'input_manifest_hash': config['input_manifest_sha256'],
            'allowlist_hash': digest(allowlist), 'f1_hash': trusted_f1_hash if frozen else None,
            'test_input_hash': trusted_test_input_hash if frozen else None,
            'mode': mode, 'input_schema_version': input_manifest.get('schema_version')}
