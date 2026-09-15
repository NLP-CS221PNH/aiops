"""Synthetic pipeline replay/mutation tests with real schema and tokenizer.

Only management/input loading is replaced: no test incidents or labels are read.
Materialization, hashing, publication and validation run the real implementation.
"""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from src.data.common import IMPL, read_json, read_jsonl, sha256, write_json, write_jsonl
from src.representations import load_config
from src.representation_pipeline import (
    ARTIFACT_NAMES, HASH_KEYS, assert_test_f1_gate, build_representations, validate_artifacts,
)
from test_representation_contract import INCIDENT, synthetic_incident


class F1GuardTests(unittest.TestCase):
    def test_test_requires_explicit_externally_authenticated_f1_snapshot(self):
        for frozen, authenticated in ((None, None), ({'gate': 'F1', 'status': 'frozen'}, None),
                                      ({'gate': 'F1', 'status': 'candidate'}, {})):
            with self.subTest(frozen=frozen), self.assertRaises(ValueError):
                assert_test_f1_gate('test', frozen, authenticated)
        self.assertTrue(assert_test_f1_gate('synthetic-fixture'))
        self.assertTrue(assert_test_f1_gate('train-dev'))
        with self.assertRaises(ValueError):
            assert_test_f1_gate('test-like')

    def test_each_frozen_hash_is_required_and_drift_is_rejected(self):
        hashes = {key: str(index) * 64 for index, key in enumerate((
            'config_hash', 'input_manifest_hash', 'tokenizer_hash',
            'implementation_hash', 'query_manifest_hash'))}
        frozen = dict(hashes, gate='F1', status='frozen')
        self.assertTrue(assert_test_f1_gate('test', frozen, hashes))
        for key in hashes:
            missing = {field: value for field, value in hashes.items() if field != key}
            with self.subTest(key=key, mutation='missing'), self.assertRaises(ValueError):
                assert_test_f1_gate('test', frozen, missing)
            with self.subTest(key=key, mutation='drift'), self.assertRaises(ValueError):
                assert_test_f1_gate('test', {**frozen, key: 'f' * 64}, hashes)


class RepresentationPipelineTests(unittest.TestCase):
    def setUp(self):
        staging = IMPL / '.representation-check'
        staging.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='synthetic-tests-', dir=staging)
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.output = self.work / 'queries'
        self.config_path = self.work / 'representation.json'
        self.config = load_config()
        write_json(self.config_path, self.config)
        self.input_hash = 'a' * 64
        manager = mock.patch('src.representation_pipeline.load_manager_selection',
                             return_value=((INCIDENT,), {'manager_selection_hash': 'b' * 64,
                                                        'manager_config_hash': 'c' * 64}))
        inputs = mock.patch('src.representation_pipeline.load_safe_incidents',
                            side_effect=lambda *_: ([synthetic_incident()], self.input_hash))
        manager.start()
        inputs.start()
        self.addCleanup(manager.stop)
        self.addCleanup(inputs.stop)

    def build(self):
        return build_representations(self.output, self.config_path)

    def validate(self, receipt=None):
        return validate_artifacts(self.output, self.config_path, receipt_path=receipt)

    def test_synthetic_pipeline_rebuild_and_replay_are_identical(self):
        manifest = self.build()
        self.assertEqual(manifest['counts'], {'incidents': 1, 'queries': 3, 'selections': 1,
                                              'token_ledgers': 3, 'bundles': 1})
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.assertEqual(self.build(), manifest)
        self.assertEqual({path.name: path.read_bytes() for path in self.output.iterdir()}, before)
        verified = self.validate()
        self.assertEqual(verified['status'], 'pass')
        self.assertTrue(verified['deterministic_replay'])
        self.assertEqual(verified['test_materialization'], 'not_performed')

    def test_query_byte_tampering_cannot_pass_replay(self):
        self.build()
        path = self.output / ARTIFACT_NAMES[0]
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'ARTIFACT_REPLAY_MISMATCH'):
            self.validate()

    def test_forged_source_span_and_refreshed_outer_hashes_cannot_pass(self):
        self.build()
        name = ARTIFACT_NAMES[2]
        path = self.output / name
        rows = read_jsonl(path)
        rows[0]['source_spans'][0]['source_char_end'] -= 1
        write_jsonl(path, rows)
        manifest_path = self.output / 'query-manifest.json'
        manifest = read_json(manifest_path)
        entry = next(row for row in manifest['outputs'] if row['path'] == name)
        entry.update(sha256=sha256(path), bytes=path.stat().st_size)
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ValueError, 'MANIFEST_STALE'):
            self.validate()

    def test_config_change_invalidates_old_outputs_and_cannot_overwrite_same_version(self):
        self.build()
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.config['selection']['logs_per_service'] = 1
        write_json(self.config_path, self.config)
        with self.assertRaisesRegex(ValueError, 'MANIFEST_STALE'):
            self.validate()
        with self.assertRaisesRegex(ValueError, 'SAME_VERSION_DRIFT'):
            self.build()
        self.assertEqual({path.name: path.read_bytes() for path in self.output.iterdir()}, before)

    def test_upstream_manifest_drift_invalidates_receipt_and_outputs(self):
        self.build()
        self.input_hash = 'd' * 64
        with self.assertRaisesRegex(ValueError, 'MANIFEST_STALE'):
            self.validate()

    def test_new_version_requires_new_output_directory(self):
        self.build()
        self.config['representation_version'] = 'synthetic-next-version'
        write_json(self.config_path, self.config)
        with self.assertRaisesRegex(ValueError, 'NEW_VERSION_REQUIRES_NEW_DIRECTORY'):
            self.build()

    def test_receipt_binds_exact_query_and_each_dependency_hash(self):
        self.build()
        verification = self.validate()
        receipt_path = self.work / 'receipt.json'
        for key in ('query_manifest_hash', *HASH_KEYS):
            receipt = dict(verification, technical_gate='pass')
            receipt[key] = '0' * 64
            write_json(receipt_path, receipt)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'REVIEW_RECEIPT_STALE'):
                self.validate(receipt_path)

    def test_valid_synthetic_receipt_requires_current_evidence_and_both_review_roles(self):
        self.build()
        relative = Path(__file__).resolve().relative_to(IMPL).as_posix()
        receipt = dict(self.validate(), evidence=[{'path': relative, 'sha256': sha256(__file__)}],
                       automated_reviews=[{'role': role, 'actor_kind': 'codex_agent', 'status': 'pass',
                                           'reviewer': 'synthetic-fixture-' + role,
                                           'evidence_path': relative}
                                          for role in ('tester', 'code-reviewer')])
        path = self.work / 'synthetic-receipt.json'
        write_json(path, receipt)
        self.assertEqual(self.validate(path)['status'], 'pass')
        for mutation in ('stale_evidence', 'missing_role', 'pending_review', 'private_path'):
            changed = copy.deepcopy(receipt)
            if mutation == 'stale_evidence':
                changed['evidence'][0]['sha256'] = '0' * 64
            elif mutation == 'missing_role':
                changed['automated_reviews'][1]['role'] = 'unrelated-reviewer'
            elif mutation == 'pending_review':
                changed['automated_reviews'][0]['status'] = 'pending'
            else:
                changed['evidence'][0]['path'] = 'data/private/split-map.tsv'
            write_json(path, changed)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(path)

    def test_output_cannot_target_source_or_other_implementation_directories(self):
        for target in (IMPL / 'data/inference', IMPL / 'src', IMPL / 'configs'):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'REPRESENTATION_OUTPUT_PATH'):
                build_representations(target, self.config_path)


if __name__ == '__main__':
    unittest.main()
