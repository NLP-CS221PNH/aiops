"""Synthetic cache, resume and input boundary checks; no gold or private reads."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from src.retrieval import cache, common, inputs
from src.retrieval.cache import ArtifactCache, Checkpoints, cache_key, run_lock
from src.retrieval.common import RetrievalError, digest, text_hash
from src.retrieval.dense import verify_model_assets


class WorkspaceFixture(unittest.TestCase):
    def setUp(self):
        base = common.IMPL / '.test-work' / 'retrieval'
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='tester-', dir=base)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')


class CacheFingerprintTests(WorkspaceFixture):
    def setUp(self):
        super().setUp()
        self.policy = {
            'corpus_hash': 'a' * 64,
            'chunks': [
                {'chunk_id': 'fixture-A', 'document_id': 'fixture-doc-A',
                 'content_hash': text_hash('alpha')},
                {'chunk_id': 'fixture-B', 'document_id': 'fixture-doc-B',
                 'content_hash': text_hash('beta')},
            ],
            'model': {'model_id': 'synthetic-model-policy', 'revision': 'old-revision',
                      'tokenizer_revision': 'old-tokenizer-revision',
                      'assets': {'tokenizer.json': 'b' * 64, 'weights': 'c' * 64},
                      'query_prefix': 'query: ', 'passage_prefix': 'passage: ',
                      'normalize_embeddings': True, 'max_tokens': 512},
            'content_policy': 'section_heading + newline + text',
        }

    def test_every_embedding_semantics_change_invalidates_fingerprint(self):
        baseline = cache_key(**self.policy)
        mutations = [
            ('corpus', lambda p: p.update(corpus_hash='d' * 64)),
            ('content policy', lambda p: p.update(content_policy='text-only')),
            ('content', lambda p: p['chunks'][0].update(content_hash=text_hash('changed'))),
            ('chunk ID', lambda p: p['chunks'][0].update(chunk_id='fixture-C')),
            ('document ID', lambda p: p['chunks'][0].update(document_id='fixture-doc-C')),
            ('row order', lambda p: p['chunks'].reverse()),
            ('model', lambda p: p['model'].update(model_id='different-model')),
            ('model revision', lambda p: p['model'].update(revision='different-revision')),
            ('tokenizer revision', lambda p: p['model'].update(tokenizer_revision='new-tokenizer')),
            ('tokenizer bytes', lambda p: p['model']['assets'].update({'tokenizer.json': 'd' * 64})),
            ('weight bytes', lambda p: p['model']['assets'].update(weights='d' * 64)),
            ('query prefix', lambda p: p['model'].update(query_prefix='question: ')),
            ('passage prefix', lambda p: p['model'].update(passage_prefix='document: ')),
            ('normalization', lambda p: p['model'].update(normalize_embeddings=False)),
            ('max tokens', lambda p: p['model'].update(max_tokens=256)),
        ]
        for name, mutate in mutations:
            changed = copy.deepcopy(self.policy)
            mutate(changed)
            with self.subTest(policy=name):
                self.assertNotEqual(cache_key(**changed), baseline)
        reordered = {key: self.policy[key] for key in reversed(self.policy)}
        self.assertEqual(cache_key(**reordered), baseline)

    def test_cache_miss_hit_idempotency_and_conflicting_payload_rejection(self):
        storage = ArtifactCache(self.work / 'cache')
        key = cache_key(**self.policy)
        payload = {'synthetic': True, 'vectors': [[1, 0], [0, 1]]}
        self.assertIsNone(storage.load(key))
        storage.store(key, payload)
        self.assertEqual(storage.load(key), payload)
        original = (storage.root / (key + '.json')).read_bytes()
        storage.store(key, copy.deepcopy(payload))
        self.assertEqual((storage.root / (key + '.json')).read_bytes(), original)
        with self.assertRaisesRegex(RetrievalError, 'CACHE_IMMUTABILITY'):
            storage.store(key, {'synthetic': True, 'vectors': [[0, 1], [1, 0]]})

    def test_payload_tampering_and_invalid_cache_key_rejected(self):
        storage = ArtifactCache(self.work / 'cache')
        key = cache_key(**self.policy)
        storage.store(key, {'synthetic': True})
        path = storage.root / (key + '.json')
        row = common.read_json(path)
        row['payload']['synthetic'] = 'tampered'
        self.write(path, row)
        with self.assertRaisesRegex(RetrievalError, 'CACHE_CHECKSUM'):
            storage.load(key)
        for invalid in ('../foreign', 'a' * 63, 'g' * 64):
            with self.subTest(key=invalid), self.assertRaisesRegex(RetrievalError, 'CACHE_KEY'):
                storage.load(invalid)

    def test_shared_cache_key_lock_blocks_a_second_publisher(self):
        storage = ArtifactCache(self.work / 'cache')
        key = cache_key(**self.policy)
        with run_lock(storage.root / ('lock-' + key)):
            with self.assertRaisesRegex(RetrievalError, 'RUN_LOCKED'):
                storage.store(key, {'synthetic': True})
            self.assertIsNone(storage.load(key))
        storage.store(key, {'synthetic': True})
        self.assertEqual(storage.load(key), {'synthetic': True})


class CheckpointTests(WorkspaceFixture):
    def setUp(self):
        super().setUp()
        self.directory = self.work / 'run'
        self.spec = {'synthetic': True, 'config_hash': 'a' * 64, 'methods': ['bm25']}
        self.fingerprint = digest(self.spec)

    def checkpoints(self, *, resume=False, fingerprint=None, specification=None):
        return Checkpoints(self.directory, fingerprint or self.fingerprint,
                           self.spec if specification is None else specification, resume=resume)

    def row(self, key):
        return {'fingerprint': self.fingerprint, 'record_key': key,
                'synthetic': True, 'status': 'complete', 'hits': []}

    def test_resume_keeps_completed_records_and_missing_records_explicit(self):
        store = self.checkpoints()
        store.put('fixture-A:IR-B', self.row('fixture-A:IR-B'))
        resumed = self.checkpoints(resume=True)
        self.assertEqual(resumed.get('fixture-A:IR-B'), self.row('fixture-A:IR-B'))
        self.assertIsNone(resumed.get('fixture-B:IR-B'))
        self.assertEqual(len(resumed.index['records']), 1)
        with self.assertRaisesRegex(RetrievalError, 'RUN_EXISTS'):
            self.checkpoints()

    def test_resume_rejects_changed_config_fingerprint_or_specification(self):
        self.checkpoints()
        for changes in ({'fingerprint': 'b' * 64},
                        {'specification': dict(self.spec, methods=['dense'])}):
            with self.subTest(changes=changes), self.assertRaisesRegex(RetrievalError, 'RESUME_FINGERPRINT_MISMATCH'):
                self.checkpoints(resume=True, **changes)

    def test_missing_resume_corrupt_record_and_wrong_binding_rejected(self):
        with self.assertRaisesRegex(RetrievalError, 'RESUME_NOT_FOUND'):
            self.checkpoints(resume=True)
        store = self.checkpoints()
        with self.assertRaisesRegex(RetrievalError, 'CHECKPOINT_BINDING'):
            store.put('fixture-A:IR-B', self.row('fixture-B:IR-B'))
        store.put('fixture-A:IR-B', self.row('fixture-A:IR-B'))
        record_path = self.directory / 'records' / store.index['records']['fixture-A:IR-B']['path']
        record_path.write_text('{"synthetic":"corrupt"}\n', encoding='utf-8')
        with self.assertRaisesRegex(RetrievalError, 'CHECKPOINT_CHECKSUM'):
            self.checkpoints(resume=True)

    def test_interrupted_checkpoint_publication_resumes_only_committed_records(self):
        store = self.checkpoints()
        store.put('fixture-A:IR-B', self.row('fixture-A:IR-B'))
        atomic_write = cache.atomic_json

        def interrupt_index(path, value):
            if Path(path) == store.path:
                raise OSError('synthetic interrupted publication')
            return atomic_write(path, value)

        with mock.patch.object(cache, 'atomic_json', side_effect=interrupt_index):
            with self.assertRaisesRegex(OSError, 'synthetic interrupted'):
                store.put('fixture-B:IR-B', self.row('fixture-B:IR-B'))
        resumed = self.checkpoints(resume=True)
        self.assertEqual(len(resumed.index['records']), 1)
        self.assertIsNone(resumed.get('fixture-B:IR-B'))
        resumed.put('fixture-B:IR-B', self.row('fixture-B:IR-B'))
        complete = self.checkpoints(resume=True)
        self.assertEqual(set(complete.index['records']), {'fixture-A:IR-B', 'fixture-B:IR-B'})

    def test_foreign_record_path_and_concurrent_writer_are_rejected(self):
        store = self.checkpoints()
        store.put('fixture-A:IR-B', self.row('fixture-A:IR-B'))
        store.index['records']['fixture-A:IR-B']['path'] = '../outside.json'
        self.write(store.path, store.index)
        with self.assertRaisesRegex(RetrievalError, 'CHECKPOINT_PATH'):
            self.checkpoints(resume=True)
        with run_lock(self.directory):
            with self.assertRaisesRegex(RetrievalError, 'RUN_LOCKED'):
                with run_lock(self.directory):
                    self.fail('second writer must not enter')
        self.assertFalse((self.directory / '.writer.lock').exists())

    def test_interrupted_retry_preserves_the_previous_committed_failed_attempt(self):
        store = self.checkpoints()
        key = 'fixture-A:IR-B'
        prior = dict(self.row(key), status='failed', attempt=1)
        store.put(key, prior)
        prior_path = self.directory / 'records' / store.index['records'][key]['path']
        prior_bytes = prior_path.read_bytes()
        atomic_write = cache.atomic_json

        def interrupt_index(path, value):
            if Path(path) == store.path:
                raise OSError('synthetic interrupted retry publication')
            return atomic_write(path, value)

        retry = dict(self.row(key), status='complete', attempt=2)
        with mock.patch.object(cache, 'atomic_json', side_effect=interrupt_index):
            with self.assertRaisesRegex(OSError, 'synthetic interrupted retry'):
                store.put(key, retry)
        resumed = self.checkpoints(resume=True)
        self.assertEqual(resumed.get(key), prior)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        resumed.put(key, retry)
        self.assertEqual(self.checkpoints(resume=True).get(key), retry)
        self.assertEqual(len(resumed.index['records']), 1)


class InputPrimitiveTests(unittest.TestCase):
    def test_private_and_traversal_paths_rejected_before_read(self):
        for path in ('data/private/split-map.tsv', 'data/private/gold.jsonl',
                     'queries/../data/private/secret.json', 'annotations/judgments.tsv'):
            with self.subTest(path=path), self.assertRaises(RetrievalError):
                common.safe_path(path)

    def test_nested_private_fields_rejected_but_legitimate_observed_words_allowed(self):
        for field in ('scenario_family_id', 'source_case', 'injection_target',
                      'qrels', 'gold', 'relevance_grade'):
            with self.subTest(field=field), self.assertRaisesRegex(RetrievalError, 'PRIVATE_FIELD'):
                common.reject_private({'metadata': [{'nested': {field: 'synthetic forbidden'}}]})
        common.reject_private({'query_text': 'Service source_case-api reported a gold cache key failure.'})

    def test_duplicate_json_keys_and_nonfinite_json_are_rejected(self):
        for value in ('{"score":1,"score":2}', '{"score":NaN}', '{"score":Infinity}'):
            with self.subTest(value=value), self.assertRaises(RetrievalError):
                common.parse_json(value)

    def test_frozen_missing_f1_stops_before_any_corpus_or_query_loading(self):
        config = inputs.load_config()
        with mock.patch.object(inputs, 'load_corpus', side_effect=AssertionError('must not read corpus')):
            with self.assertRaisesRegex(RetrievalError, 'F1_AUTHENTICATED_HASH_REQUIRED'):
                inputs.load_inputs(config, 'not-opened.json', mode='frozen')

    def test_candidate_manifest_cannot_authorize_real_pilot(self):
        config = inputs.load_config()
        candidate = {'schema_version': 'cs221-corpus-manifest-v1',
                     'status': 'candidate', 'release_ready': False,
                     'validation_receipt': {'release_ready': False},
                     'index_whitelist': ['synthetic-document']}
        with mock.patch.object(inputs, '_verified', return_value=candidate), mock.patch.object(
                inputs, 'read_jsonl', side_effect=AssertionError('must not read candidate chunks')):
            with self.assertRaisesRegex(RetrievalError, 'CORPUS_RELEASE_PENDING'):
                inputs.load_corpus(config, mode='pilot')


class ModelAssetBoundaryTests(WorkspaceFixture):
    def setUp(self):
        super().setUp()
        self.assets = self.work / 'synthetic-assets'
        self.assets.mkdir()
        # These are deliberately non-loadable fixture bytes, never model weights.
        self.hashes = {}
        for name in ('config.json', 'tokenizer_config.json', 'tokenizer.json', 'model.safetensors'):
            path = self.assets / name
            path.write_text('synthetic hash-check fixture only: ' + name, encoding='utf-8')
            self.hashes[name] = common.sha256(path)

    def test_declared_asset_hashes_are_verified_without_model_loading(self):
        self.assertEqual(verify_model_assets(self.assets, self.hashes), self.hashes)
        (self.assets / 'tokenizer.json').write_text('changed tokenizer fixture', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            verify_model_assets(self.assets, self.hashes)

    def test_missing_and_untracked_assets_rejected(self):
        (self.assets / 'model.safetensors').unlink()
        with self.assertRaisesRegex(ValueError, 'missing pinned model asset'):
            verify_model_assets(self.assets, self.hashes)
        (self.assets / 'model.safetensors').write_text(
            'synthetic hash-check fixture only: model.safetensors', encoding='utf-8')
        (self.assets / 'vocab.txt').write_text('untracked synthetic vocab', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'untracked'):
            verify_model_assets(self.assets, self.hashes)

    def test_asset_manifest_cannot_read_outside_model_directory(self):
        for name in ('../outside.json', 'C:/outside.json', 'nested\\outside.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                verify_model_assets(self.assets, {name: 'a' * 64})


class IntegrationFixture(WorkspaceFixture):
    def setUp(self):
        super().setUp()
        sys.path.insert(0, str(common.IMPL / '.corpus-deps'))
        builder_path = Path(__file__).parent / 'fixtures' / 'retrieval' / 'build_fixture.py'
        module_spec = importlib.util.spec_from_file_location('retrieval_fixture_builder', builder_path)
        builder = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(builder)
        result = builder.build_fixture(self.work)
        self.config_path = result['config_path']
        self.allowlist_path = result['allowlist_path']
        self.config = inputs.load_config(self.config_path)

    def load(self, **kwargs):
        return inputs.load_inputs(self.config, self.allowlist_path, mode='fixture', **kwargs)

    def save_config(self):
        self.write(self.config_path, self.config)

    def rewrite_queries(self, rows):
        path = common.safe_path(self.config['query_manifest']).parent / self.config['query_file']
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        manifest_path = common.safe_path(self.config['query_manifest'])
        manifest = common.read_json(manifest_path)
        manifest['outputs'][0].update(rows=len(rows), sha256=common.sha256(path))
        self.write(manifest_path, manifest)
        self.config['query_manifest_sha256'] = common.sha256(manifest_path)
        allowlist = common.read_json(self.allowlist_path)
        allowlist['query_manifest_hash'] = self.config['query_manifest_sha256']
        self.write(self.allowlist_path, allowlist)
        self.save_config()

    def query_rows(self):
        return common.read_jsonl(common.safe_path(self.config['query_manifest']).parent / self.config['query_file'])

    def rewrite_chunks(self, rows):
        manifest_path = common.safe_path(self.config['corpus_manifest'])
        path = manifest_path.parent / 'chunks.jsonl'
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        manifest = common.read_json(manifest_path)
        manifest['derived_file_hashes']['chunks.jsonl'] = common.sha256(path)
        self.write(manifest_path, manifest)
        self.config['corpus_manifest_sha256'] = common.sha256(manifest_path)
        self.save_config()

    def run_fixture(self, **kwargs):
        from src.retrieval.runner import run
        return run(self.config, self.allowlist_path, mode='fixture', **kwargs)


class InputManifestTests(IntegrationFixture):
    def test_valid_fixture_has_only_shared_text_and_provenance_fields(self):
        result = self.load()
        self.assertEqual(len(result['chunks']), 3)
        self.assertEqual([q['incident_id'] for q in result['queries']], ['fixture-empty', 'fixture-one'])
        self.assertEqual({q['query_text'] for q in result['queries']}, {'alpha', 'zzznomatchzzz'})
        for chunk in result['chunks']:
            self.assertEqual(set(chunk), {'chunk_id', 'document_id', 'content', 'content_hash'})
        for query in result['queries']:
            self.assertEqual(set(query), {'incident_id', 'representation_id', 'query_text',
                                         'query_hash', 'window_hash', 'task_version'})
        self.assertEqual(result['mode'], 'fixture')

    def test_fixture_cannot_be_used_as_real_pilot_or_have_real_incident_ids(self):
        with self.assertRaisesRegex(RetrievalError, 'FIXTURE_MODE_MISMATCH'):
            inputs.load_inputs(self.config, self.allowlist_path, mode='pilot')
        rows = self.query_rows()
        rows[0]['incident_id'] = 'inc_0123456789abcdef'
        self.rewrite_queries(rows)
        with self.assertRaisesRegex(RetrievalError, 'FIXTURE_ID'):
            self.load()
        with self.assertRaisesRegex(RetrievalError, 'PATH_NOT_ALLOWED'):
            inputs._fixture_path('queries/pretend-fixture.json')

    def test_unknown_config_fields_model_aliases_and_invalid_budgets_rejected(self):
        original = copy.deepcopy(self.config)
        cases = [
            (lambda c: c.update(debug=True), 'CONFIG_FIELDS'),
            (lambda c: c['bm25'].update(debug=True), 'BM25_CONFIG'),
            (lambda c: c['dense'].update(revision='main'), 'PINNED_E5_REVISION'),
            (lambda c: c['dense'].update(max_tokens=511), 'SHARED_QUERY_BUDGET'),
            (lambda c: c.update(depth=True), 'DEPTH'),
            (lambda c: c.update(depth=51), 'DEPTH'),
            (lambda c: c.update(corpus_manifest='data/private/gold.jsonl'), 'PATH_NOT_ALLOWED'),
        ]
        for mutate, expected in cases:
            self.config = copy.deepcopy(original)
            mutate(self.config)
            self.save_config()
            with self.subTest(expected=expected), self.assertRaisesRegex(RetrievalError, expected):
                inputs.load_config(self.config_path)

    def test_rehashed_query_file_cannot_hide_changed_body_private_or_unknown_fields(self):
        original = self.query_rows()
        cases = [
            (lambda r: r[0].update(query_text='changed without query content hash'), 'QUERY_TEXT_HASH'),
            (lambda r: r[0].update(gold='synthetic forbidden'), 'PRIVATE_FIELD'),
            (lambda r: r[0]['window'].update(qrels='synthetic forbidden'), 'PRIVATE_FIELD'),
            (lambda r: r[0].update(unapproved_metadata='synthetic'), 'QUERY_SCHEMA'),
            (lambda r: r.append(copy.deepcopy(r[0])), 'QUERY_DUPLICATE'),
        ]
        for mutate, expected in cases:
            rows = copy.deepcopy(original)
            mutate(rows)
            self.rewrite_queries(rows)
            with self.subTest(expected=expected), self.assertRaisesRegex(RetrievalError, expected):
                self.load()

    def test_rehashed_corpus_cannot_hide_bad_content_hashes_or_duplicate_ids(self):
        original = common.read_jsonl(self.work / 'chunks.jsonl')
        cases = [
            (lambda r: r[0].update(content='different body'), 'CHUNK_CONTENT_POLICY'),
            (lambda r: r[0].update(content_hash='0' * 64), 'CHUNK_CONTENT_HASH'),
            (lambda r: r[0].update(corpus_hash='0' * 64), 'CHUNK_CORPUS_HASH'),
            (lambda r: r.append(copy.deepcopy(r[0])), 'CHUNK_DUPLICATE_OR_EMPTY_ID'),
        ]
        for mutate, expected in cases:
            rows = copy.deepcopy(original)
            mutate(rows)
            self.rewrite_chunks(rows)
            with self.subTest(expected=expected), self.assertRaisesRegex(RetrievalError, expected):
                self.load()

    def test_missing_and_duplicate_allowlist_ids_are_not_silently_dropped(self):
        original = common.read_json(self.allowlist_path)
        for ids, expected in ((['fixture-missing'], 'ALLOWLIST_QUERY_MISSING'),
                              (['fixture-one', 'fixture-one'], 'ALLOWLIST_IDS')):
            allowlist = dict(original, incident_ids=ids)
            self.write(self.allowlist_path, allowlist)
            with self.subTest(ids=ids), self.assertRaisesRegex(RetrievalError, expected):
                self.load()

    def test_external_schema_references_rejected_before_resolution(self):
        path = common.safe_path(self.config['query_schema'])
        original = common.read_json(path)
        for reference in ('https://synthetic.invalid/schema.json', 'file:///synthetic/gold.json'):
            schema = copy.deepcopy(original)
            schema['$defs']['query']['properties']['window']['$ref'] = reference
            self.write(path, schema)
            self.config['query_schema_sha256'] = common.sha256(path)
            with self.subTest(reference=reference), self.assertRaisesRegex(RetrievalError, 'EXTERNAL_SCHEMA_REFERENCE'):
                self.load()

    def test_changed_input_bytes_fail_even_when_filename_is_unchanged(self):
        path = common.safe_path(self.config['query_manifest'])
        path.write_text('{"changed":"synthetic manifest"}\n', encoding='utf-8')
        with self.assertRaisesRegex(RetrievalError, 'INPUT_HASH'):
            self.load()

    def test_invalid_or_stale_f1_fails_before_corpus_loading(self):
        with mock.patch.object(inputs, 'load_corpus', side_effect=AssertionError('must not read corpus')):
            with mock.patch.object(inputs, '_verified', return_value={'gate': 'F1', 'status': 'draft', 'owner_plan': '08'}):
                with self.assertRaisesRegex(RetrievalError, 'F1_REQUIRED'):
                    inputs.load_inputs(self.config, self.allowlist_path, mode='frozen',
                                       f1_path='synthetic-f1.json', trusted_f1_hash='a' * 64)
            with mock.patch.object(inputs, '_verified', return_value={
                    'gate': 'F1', 'status': 'frozen', 'owner_plan': '08', 'retrieval_policy_hash': '0' * 64}):
                with self.assertRaisesRegex(RetrievalError, 'F1_HASH_MISMATCH'):
                    inputs.load_inputs(self.config, self.allowlist_path, mode='frozen',
                                       f1_path='synthetic-f1.json', trusted_f1_hash='a' * 64)


class RunnerAndReaderTests(IntegrationFixture):
    def setUp(self):
        super().setUp()
        from src.retrieval import consumer
        self.consumer = consumer

    def test_all_incident_conditions_kept_when_real_dense_assets_are_missing(self):
        path, result = self.run_fixture(run_id='synthetic-missing-model')
        manifest, rows = self.consumer.read_run(path)
        self.assertEqual(result['state'], 'complete_with_errors')
        self.assertEqual(manifest['counts'], {'complete': 2, 'failed': 4, 'pending': 0})
        self.assertEqual(len(rows), 6)
        self.assertEqual({(r['incident_id'], r['condition']) for r in rows},
                         {(iid, condition) for iid in ('fixture-empty', 'fixture-one')
                          for condition in ('IR-B', 'IR-D', 'IR-H')})
        for row in rows:
            self.assertTrue(row['synthetic'])
            if row['condition'] != 'IR-B':
                self.assertEqual(row['status'], 'failed')
                self.assertEqual(row['error']['code'], 'MODEL_UNAVAILABLE')
                self.assertEqual(row['hits'], [])
        self.assertEqual(manifest['quality_evaluation'], 'not_performed')
        empty = self.consumer.read_hits(path, 'fixture-empty', 'IR-B')
        self.assertEqual(empty['hits'], [])
        self.assertEqual(empty['available_count'], 0)
        short = self.consumer.read_hits(path, 'fixture-one', 'IR-B')
        self.assertLess(short['available_count'], 5)
        self.assertEqual(len(short['hits']), short['available_count'])

    def test_interrupted_run_resumes_without_duplicates_or_recomputing_complete_record(self):
        from src.retrieval import runner
        path, result = self.run_fixture(methods=['bm25'], run_id='synthetic-restart', stop_after=1)
        self.assertEqual(result['state'], 'interrupted')
        manifest, rows = self.consumer.read_run(path)
        self.assertEqual(manifest['counts'], {'complete': 1, 'failed': 0, 'pending': 1})
        self.assertEqual(len(rows), 1)
        entry = next(e for e in manifest['records'] if e['status'] == 'complete')
        record_path = path.parent / entry['path']
        preserved = record_path.read_bytes()
        actual_search = runner.BM25.search
        calls = []

        def counted_search(index, query, depth=50):
            calls.append(query)
            return actual_search(index, query, depth)

        with mock.patch.object(runner.BM25, 'search', counted_search):
            self.run_fixture(methods=['bm25'], run_id='synthetic-restart', resume=True)
        self.assertEqual(calls, ['alpha'])
        self.assertEqual(record_path.read_bytes(), preserved)
        manifest, rows = self.consumer.read_run(path)
        self.assertEqual(manifest['counts'], {'complete': 2, 'failed': 0, 'pending': 0})
        self.assertEqual(len({r['record_key'] for r in rows}), 2)
        with mock.patch.object(runner.BM25, 'search', side_effect=AssertionError('complete run must not search')):
            self.run_fixture(methods=['bm25'], run_id='synthetic-restart', resume=True)
        self.assertEqual(record_path.read_bytes(), preserved)

    def test_runner_resume_rejects_changed_configuration(self):
        self.run_fixture(methods=['bm25'], run_id='synthetic-config-change')
        self.config['bm25']['k1'] = 1.3
        with self.assertRaisesRegex(RetrievalError, 'RESUME_FINGERPRINT_MISMATCH'):
            self.run_fixture(methods=['bm25'], run_id='synthetic-config-change', resume=True)

    def test_consumer_rejects_missing_records_and_wrong_provenance(self):
        path, _ = self.run_fixture(methods=['bm25'], run_id='synthetic-reader')
        with self.assertRaisesRegex(RetrievalError, 'CONSUMER_PROVENANCE_MISMATCH'):
            self.consumer.read_run(path, expected={'query_manifest_hash': '0' * 64})
        with self.assertRaisesRegex(RetrievalError, 'RUN_MANIFEST_HASH'):
            self.consumer.read_run(path, expected_manifest_hash='0' * 64)
        manifest = common.read_json(path)
        manifest['records'].pop()
        self.write(path, manifest)
        with self.assertRaisesRegex(RetrievalError, 'RUN_RECORD_COMPLETENESS'):
            self.consumer.read_run(path)

    def test_semantic_hit_tamper_rejected_after_all_outer_checksums_are_recomputed(self):
        path, _ = self.run_fixture(methods=['bm25'], run_id='synthetic-semantic-tamper')
        manifest = common.read_json(path)
        entry = next(e for e in manifest['records'] if e['candidate_count'])
        record_path = path.parent / entry['path']
        record = common.read_json(record_path)
        record['hits'][0]['document_id'] = 'fixture-forged-document'
        new_name = digest(entry['record_key']) + '-' + digest(record) + '.json'
        new_path = record_path.parent / new_name
        self.write(new_path, record)
        entry.update(path='records/' + new_name, sha256=common.sha256(new_path))
        index_path = path.parent / 'checkpoint-index.json'
        index = common.read_json(index_path)
        index['records'][entry['record_key']].update(path=new_name, sha256=entry['sha256'])
        self.write(index_path, index)
        manifest['checkpoint_index_sha256'] = common.sha256(index_path)
        self.write(path, manifest)
        with self.assertRaisesRegex(RetrievalError, 'RUN_CHUNK_PROVENANCE'):
            self.consumer.read_run(path)


if __name__ == '__main__':
    unittest.main()
