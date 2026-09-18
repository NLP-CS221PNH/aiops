"""Run every requested incident/condition with atomic, validated receipts."""
from __future__ import annotations

from importlib import metadata
from pathlib import Path
import platform
import re
from time import perf_counter

from .bm25 import BM25
from .cache import ArtifactCache, Checkpoints, cache_key, run_lock
from .common import (IMPL, TOKENIZER_HASH, atomic_json, digest, read_json, require, safe_path,
                     sha256, text_hash, utc_now)
from .dense import DenseIndex, E5Encoder, ModelUnavailableError
from .fusion import rrf
from .inputs import load_inputs

CONDITIONS = {'bm25': 'IR-B', 'dense': 'IR-D', 'hybrid': 'IR-H', 'rerank': 'IR-R'}


def environment():
    versions = {}
    for name in ('numpy', 'tokenizers', 'torch', 'transformers', 'jsonschema'):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'platform': platform.platform(), 'machine': platform.machine(),
            'processor': platform.processor(), 'device': 'cpu', 'dtype': 'float32',
            'packages': versions}


def implementation_hashes():
    return {path.name: sha256(path) for path in sorted(Path(__file__).parent.glob('*.py'))}


def shared_query_audit(queries, config):
    from tokenizers import Tokenizer
    path = safe_path('vendor/e5-small-v2/tokenizer.json')
    require(sha256(path) == TOKENIZER_HASH, 'SHARED_TOKENIZER_HASH')
    require(metadata.version('tokenizers') == '0.21.4', 'SHARED_TOKENIZER_VERSION')
    backend = Tokenizer.from_file(str(path))
    backend.no_truncation()
    backend.no_padding()
    result = {}
    for query in queries:
        count = len(backend.encode(config['dense']['query_prefix'] + query['query_text'], add_special_tokens=True).ids)
        require(count <= config['dense']['max_tokens'], 'QUERY_BUDGET_EXCEEDED:' + query['incident_id'])
        result[query['incident_id']] = {'kind': 'shared_query_budget', 'input_tokens': count,
                    'output_tokens': count, 'removed_tokens': 0, 'truncated': False,
                    'max_tokens': 512, 'token_count_kind': 'actual_pinned_e5_tokenizer',
                    'tokenizer_hash': TOKENIZER_HASH}
    return result


def prepare_dense(inputs, config):
    model = config['dense']
    started = perf_counter()
    encoder = E5Encoder(safe_path(model['model_dir']), model['assets'], revision=model['revision'],
                       max_tokens=model['max_tokens'], batch_size=model['batch_size'],
                       device=model['device'], query_prefix=model['query_prefix'],
                       passage_prefix=model['passage_prefix'])
    model_seconds = perf_counter() - started
    policy = dict(model, implementation_hashes=implementation_hashes(), environment=environment())
    key = cache_key(corpus_hash=inputs['corpus_hash'], chunks=inputs['chunks'],
                    model=policy, content_policy=config['content_policy'])
    cache = ArtifactCache(config['cache_dir'])
    started = perf_counter()
    payload = cache.load(key)
    warm = payload is not None
    if payload is None:
        embeddings, audits = encoder.encode([c['content'] for c in inputs['chunks']], kind='passage')
        payload = {'chunk_ids': [c['chunk_id'] for c in inputs['chunks']], 'vectors': embeddings.tolist(),
                   'token_audits': audits, 'dimension': encoder.dimension}
        cache.store(key, payload)
    require(payload['chunk_ids'] == [c['chunk_id'] for c in inputs['chunks']], 'CACHE_ROW_REGISTRY')
    require(payload['dimension'] == encoder.dimension, 'CACHE_DIMENSION')
    index = DenseIndex(inputs['chunks'], payload['vectors'])
    require(not inputs['chunks'] or index.dimension == encoder.dimension, 'CACHE_VECTOR_DIMENSION')
    return encoder, index, {'cache_key': key, 'cache_state': 'warm' if warm else 'cold',
            'model_load_seconds': model_seconds, 'corpus_encode_or_cache_seconds': perf_counter() - started,
            'passage_token_audits': payload['token_audits']}


def _error(exc):
    # Keep opaque diagnostics; never serialize exception text containing input text.
    return {'code': 'MODEL_UNAVAILABLE' if isinstance(exc, ModelUnavailableError) else 'RETRIEVAL_FAILED',
            'exception_type': type(exc).__name__}


def run(config, incident_list, *, mode='pilot', methods=('bm25', 'dense', 'hybrid'),
        run_id=None, resume=False, f1_path=None, trusted_f1_hash=None,
        test_input_manifest=None, trusted_test_input_hash=None, stop_after=None):
    require(isinstance(methods, (list, tuple)) and methods and len(set(methods)) == len(methods)
            and all(m in CONDITIONS for m in methods), 'METHODS')
    methods = sorted(methods, key=list(CONDITIONS).index)
    require('rerank' not in methods or config['reranker']['enabled'], 'RERANK_DISABLED')
    require(stop_after is None or (mode == 'fixture' and type(stop_after) is int and stop_after > 0), 'STOP_AFTER_FIXTURE_ONLY')
    inputs = load_inputs(config, incident_list, mode=mode, f1_path=f1_path, trusted_f1_hash=trusted_f1_hash,
                         test_input_manifest=test_input_manifest, trusted_test_input_hash=trusted_test_input_hash)
    query_audits = shared_query_audit(inputs['queries'], config)
    env = environment()
    code_hashes = implementation_hashes()
    spec = {'schema_version': 'cs221-retrieval-spec-v1', 'mode': mode, 'config_hash': digest(config),
            'config': config, 'environment': env, 'environment_hash': digest(env),
            'implementation_hashes': code_hashes, 'implementation_hash': digest(code_hashes),
            'corpus_hash': inputs['corpus_hash'], 'corpus_manifest_hash': inputs['corpus_manifest_hash'],
            'query_manifest_hash': inputs['query_manifest_hash'], 'input_manifest_hash': inputs['input_manifest_hash'],
            'allowlist_hash': inputs['allowlist_hash'], 'f1_hash': inputs['f1_hash'], 'test_input_hash': inputs['test_input_hash'],
            'representation': config['representation'], 'task_version': config['task_version'],
            'depth': config['depth'], 'conditions': [CONDITIONS[m] for m in methods],
            'queries': [{k: v for k, v in q.items() if k != 'query_text'} for q in inputs['queries']],
            'chunks': [{k: v for k, v in c.items() if k != 'content'} for c in inputs['chunks']],
            'tokenizer_asset_hash': TOKENIZER_HASH,
            'run_schema_hash': sha256(safe_path('schemas/retrieval-run.schema.json'))}
    fingerprint = digest(spec)
    run_id = run_id or ('fixture-' if mode == 'fixture' else mode + '-') + fingerprint[:16]
    require(isinstance(run_id, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', run_id), 'RUN_ID')
    directory = safe_path(Path(config['run_root']) / mode / run_id, write=True)
    with run_lock(directory):
        checkpoints = Checkpoints(directory, fingerprint, spec, resume=resume)
        expected = [q['incident_id'] + ':' + CONDITIONS[m] for q in inputs['queries'] for m in methods]
        require(set(checkpoints.index['records']) <= set(expected), 'CHECKPOINT_UNEXPECTED_RECORD')
        bm25, encoder, dense_index, reranker = None, None, None, None
        dense_error, rerank_error = None, None
        index_info = {'bm25_index_seconds': 0.0, 'dense': None, 'reranker': 'disabled',
                      'warmup_performed': False, 'runtime_note': 'times measured by perf_counter; no quality evaluation'}
        need_work = any((checkpoints.get(key) or {}).get('status') != 'complete' for key in expected)
        if need_work:
            started = perf_counter()
            bm25 = BM25(inputs['chunks'], k1=config['bm25']['k1'], b=config['bm25']['b'])
            index_info['bm25_index_seconds'] = perf_counter() - started
            if any(m in methods for m in ('dense', 'hybrid', 'rerank')):
                try:
                    encoder, dense_index, index_info['dense'] = prepare_dense(inputs, config)
                except (ValueError, OSError, ImportError, RuntimeError) as exc:
                    dense_error = _error(exc)
                    index_info['dense'] = {'status': 'failed', 'error': dense_error}
            if 'rerank' in methods:
                from .rerank import BGEReranker
                model = config['reranker']
                try:
                    reranker = BGEReranker(safe_path(model['model_dir']), model['assets'],
                            revision=model['revision'], max_tokens=model['max_tokens'],
                            batch_size=model['batch_size'], device=model['device'])
                    index_info['reranker'] = 'available'
                except (ValueError, OSError, ImportError, RuntimeError) as exc:
                    rerank_error = _error(exc)
                    index_info['reranker'] = {'status': 'unavailable', 'error': rerank_error}
        prior_manifest = directory / 'run-manifest.json'
        if resume and prior_manifest.is_file():
            prior = read_json(safe_path(prior_manifest, write=True))
            require(prior.get('fingerprint') == fingerprint, 'RESUME_MANIFEST_FINGERPRINT')
            prior_indexing = prior.get('indexing_history', [])
        else:
            prior_indexing = []
        indexing_history = prior_indexing + ([index_info] if need_work else [])
        written = 0

        def publish():
            records = []
            for key in expected:
                row = checkpoints.get(key)
                entry = checkpoints.index['records'].get(key)
                records.append({'record_key': key, 'status': row['status'] if row else 'pending',
                                'path': 'records/' + entry['path'] if entry else None,
                                'sha256': entry['sha256'] if entry else None,
                                'candidate_count': row['candidate_count'] if row else None})
            counts = {status: sum(r['status'] == status for r in records) for status in ('complete', 'failed', 'pending')}
            result = {'schema_version': 'cs221-retrieval-run-v1', 'run_id': run_id, 'fingerprint': fingerprint,
                      'specification': spec, 'timestamp': utc_now(), 'records': records, 'counts': counts,
                      'state': 'interrupted' if counts['pending'] else ('complete_with_errors' if counts['failed'] else 'complete'),
                      'checkpoint_index_sha256': sha256(checkpoints.path), 'indexing_history': indexing_history,
                      'quality_evaluation': 'not_performed', 'annotation_depth': 10, 'context_max_hits': 5,
                      'optional_reranker': index_info['reranker'] if need_work else prior.get('optional_reranker', 'disabled'),
                      'synthetic': mode == 'fixture'}
            atomic_json(directory / 'run-manifest.json', result)
            return result

        publish()
        registry = {c['chunk_id']: c for c in inputs['chunks']}
        for query in inputs['queries']:
            branch_hits, branch_times, query_encoded = {}, {}, None
            for method in methods:
                condition = CONDITIONS[method]
                key = query['incident_id'] + ':' + condition
                previous = checkpoints.get(key)
                if previous and previous['status'] == 'complete':
                    continue
                started = perf_counter()
                timings = {'query_encode_seconds': 0.0, 'search_seconds': 0.0,
                           'fusion_seconds': 0.0, 'rerank_seconds': 0.0}
                audits, error, hits = [query_audits[query['incident_id']]], None, []
                status = 'complete'
                try:
                    if 'bm25' not in branch_hits:
                        clock = perf_counter()
                        branch_hits['bm25'] = bm25.search(query['query_text'], depth=config['depth'])
                        branch_times['bm25'] = perf_counter() - clock
                    if method != 'bm25':
                        if dense_error:
                            raise ModelUnavailableError('dense prerequisite unavailable')
                        if 'dense' not in branch_hits:
                            clock = perf_counter()
                            vectors, token_audits = encoder.encode([query['query_text']], kind='query')
                            require(all(a['removed_tokens'] == 0 for a in token_audits), 'QUERY_BRANCH_TRUNCATION')
                            query_encoded = token_audits
                            branch_times['query_encode'] = perf_counter() - clock
                            clock = perf_counter()
                            branch_hits['dense'] = dense_index.search(vectors[0], depth=config['depth'])
                            branch_times['dense'] = perf_counter() - clock
                        audits += query_encoded or []
                        timings['query_encode_seconds'] = branch_times['query_encode']
                    if method in {'hybrid', 'rerank'}:
                        if 'hybrid' not in branch_hits:
                            clock = perf_counter()
                            branch_hits['hybrid'] = rrf([branch_hits['bm25'], branch_hits['dense']],
                                    constant=config['rrf']['constant'], weights=config['rrf']['weights'], depth=config['depth'])
                            branch_times['hybrid'] = perf_counter() - clock
                        timings['fusion_seconds'] = branch_times['hybrid']
                        timings['search_seconds'] = branch_times['bm25'] + branch_times['dense']
                    else:
                        timings['search_seconds'] = branch_times[method]
                    if method == 'rerank':
                        if rerank_error:
                            raise ModelUnavailableError('reranker prerequisite unavailable')
                        clock = perf_counter()
                        hits, pair_audits = reranker.rerank(query['query_text'], branch_hits['hybrid'], inputs['chunks'], depth=config['depth'])
                        audits += pair_audits
                        timings['rerank_seconds'] = perf_counter() - clock
                    else:
                        hits = branch_hits[method]
                except (ValueError, OSError, ImportError, RuntimeError) as exc:
                    error = (dense_error if method != 'bm25' and dense_error else
                             rerank_error if method == 'rerank' and rerank_error else _error(exc))
                    status, hits = 'failed', []
                enriched = [{**hit, 'content_hash': registry[hit['chunk_id']]['content_hash']} for hit in hits]
                row = {'schema_version': 'cs221-retrieval-record-v1', 'record_key': key,
                       'run_id': run_id, 'fingerprint': fingerprint, 'condition': condition,
                       'incident_id': query['incident_id'], 'representation_id': query['representation_id'],
                       'query_hash': query['query_hash'], 'task_version': query['task_version'],
                       'window_hash': query['window_hash'], 'corpus_hash': inputs['corpus_hash'],
                       'config_hash': digest(config), 'status': status, 'error': error,
                       'hits': enriched, 'candidate_count': len(enriched), 'requested_depth': config['depth'],
                       'empty': status == 'complete' and not enriched,
                       'short': status == 'complete' and len(enriched) < config['depth'],
                       'timestamp': utc_now(), 'timings': dict(timings, total_seconds=perf_counter() - started),
                       'timing_semantics': 'stage costs reused across dependent branches; do not sum across conditions',
                       'token_audits': audits, 'synthetic': mode == 'fixture'}
                checkpoints.put(key, row)
                written += 1
                manifest = publish()
                if stop_after is not None and written >= stop_after:
                    return directory / 'run-manifest.json', manifest
        return directory / 'run-manifest.json', publish()
