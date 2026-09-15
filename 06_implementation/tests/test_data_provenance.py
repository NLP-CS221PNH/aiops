"""Provenance, immutable private sidecars and exact-release receipt checks."""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from src.data.common import (
    DEFAULT_CONFIG, IMPL, ROOT, DataContractError, canonical_hash, load_config,
    parse_json, read_jsonl, sha256, timestamp, validate_inference, write_json,
)
from src.data.export_private_sidecars import export_private_sidecars
from src.data.review_receipt import validate_review_receipt
from test_data_boundary import TrainFixture


class PrivateSidecarTests(TrainFixture):
    def prepare_private(self):
        # Deliberately retain CRLF and whitespace to catch parse/reserialize copies.
        payloads = {
            'split-map.tsv': ('incident_id\tscenario_family_id\tsplit\tsplit_version\r\n'
                              f'{self.train_id}\tfixture-family\ttrain\tfixture-v1\r\n').encode(),
            'ground_truth.jsonl': ('{ "incident_id": "' + self.train_id +
                                   '", "gold": "fixture label", "source_case": "fixture-case" }\r\n').encode(),
        }
        for name, data in payloads.items():
            path = self.source / self.config['private_sources'][name]['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.config['private_sources'][name]['sha256'] = sha256(path)
        write_json(self.config_path, self.config)
        self.census = {'incident_ids': [self.train_id], 'source_revision': self.config['source_revision'],
                       'source_hash': canonical_hash(sorted(payloads)), 'files': []}
        self.private_output = self.work / 'private'
        return payloads

    def export_private(self):
        return export_private_sidecars(self.config_path, self.source, self.private_output, self.census)

    def test_private_sidecars_preserve_bytes_and_hashes(self):
        payloads = self.prepare_private()
        audit = self.export_private()
        self.assertEqual(audit['incident_ids'], [self.train_id])
        self.assertEqual(audit['incident_count'], 1)
        for entry in audit['files']:
            name = entry['path']
            self.assertEqual((self.private_output / name).read_bytes(), payloads[name])
            self.assertEqual(sha256(self.private_output / name), self.config['private_sources'][name]['sha256'])
            self.assertEqual(entry['role'], 'evaluator_only')

    def test_private_sidecar_hash_change_rejected(self):
        self.prepare_private()
        path = self.source / self.config['private_sources']['ground_truth.jsonl']['path']
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(DataContractError) as caught:
            self.export_private()
        self.assertEqual(caught.exception.code, 'HASH_MISMATCH')
        self.assertFalse(self.private_output.exists())

    def test_private_sidecar_duplicate_ids_rejected(self):
        self.prepare_private()
        path = self.source / self.config['private_sources']['ground_truth.jsonl']['path']
        path.write_bytes(path.read_bytes() * 2)
        self.config['private_sources']['ground_truth.jsonl']['sha256'] = sha256(path)
        write_json(self.config_path, self.config)
        with self.assertRaises(DataContractError) as caught:
            self.export_private()
        self.assertEqual(caught.exception.code, 'PRIVATE_ID_MISMATCH')
        self.assertFalse(self.private_output.exists())

    def test_private_sidecar_foreign_id_rejected(self):
        self.prepare_private()
        path = self.source / self.config['private_sources']['ground_truth.jsonl']['path']
        path.write_bytes(path.read_bytes().replace(self.train_id.encode(), self.other_train_id.encode()))
        self.config['private_sources']['ground_truth.jsonl']['sha256'] = sha256(path)
        write_json(self.config_path, self.config)
        with self.assertRaises(DataContractError) as caught:
            self.export_private()
        self.assertEqual(caught.exception.code, 'PRIVATE_ID_MISMATCH')

    def test_private_copy_crash_does_not_publish_partial_release(self):
        self.prepare_private()
        original = shutil.copyfile
        calls = []
        def interrupt_copy(source, destination):
            calls.append(Path(source).name)
            if len(calls) == 2:
                raise OSError('simulated private copy failure')
            return original(source, destination)
        with mock.patch('src.data.export_private_sidecars.shutil.copyfile', side_effect=interrupt_copy):
            with self.assertRaises(OSError):
                self.export_private()
        self.assertFalse(self.private_output.exists())
        self.assertFalse(list(self.work.glob('.private-staging-*')))
        self.export_private()
        self.assertTrue((self.private_output / 'data-audit.json').is_file())

    def test_private_fixture_label_changes_do_not_change_public_manifest(self):
        self.prepare_private()
        public_before = self.export()
        self.export_private()
        path = self.source / self.config['private_sources']['ground_truth.jsonl']['path']
        path.write_bytes(path.read_bytes().replace(b'fixture label', b'changed label').replace(b'fixture-case', b'changed-case'))
        self.config['private_sources']['ground_truth.jsonl']['sha256'] = sha256(path)
        write_json(self.config_path, self.config)
        public_after = self.export(self.work / 'second-inference')
        self.assertEqual(public_before, public_after)
        self.assertEqual(sha256(self.output / 'input-manifest.json'),
                         sha256(self.work / 'second-inference/input-manifest.json'))
        before_private = {p.name: sha256(p) for p in self.private_output.iterdir()}
        with self.assertRaises(DataContractError) as caught:
            self.export_private()
        self.assertEqual(caught.exception.code, 'OUTPUT_VERSION_CHANGE_REQUIRED')
        self.assertEqual(before_private, {p.name: sha256(p) for p in self.private_output.iterdir()})


class TrainRawProvenanceTests(TrainFixture):
    def raw_row(self, modality, offset, columns):
        import pyarrow.parquet as pq
        path = ROOT / f'02_datasets/acquired/raw/{self.train_id}/{modality}.parquet'
        parquet = pq.ParquetFile(path)
        remaining = offset
        for group in range(parquet.num_row_groups):
            count = parquet.metadata.row_group(group).num_rows
            if remaining < count:
                return parquet.read_row_group(group, columns=columns).slice(remaining, 1).to_pylist()[0]
            remaining -= count
        self.fail('Train source row offset is out of range')

    def test_train_trace_row_resolves_to_raw_timestamp_duration_and_status(self):
        self.export()
        row = read_jsonl(self.output / 'trace-evidence.jsonl')[0]
        raw = self.raw_row('traces', row['source_row_index'], ['startTimeMillis', 'duration', 'statusCode'])
        self.assertEqual(timestamp(row['timestamp']), raw['startTimeMillis'] / 1000)
        self.assertEqual(row['duration_raw'], raw['duration'])
        self.assertEqual(row['status_code'], raw['statusCode'])
        self.assertEqual(row['duration_unit'], 'unknown')

    def test_train_log_row_resolves_to_raw_timestamp_and_service(self):
        self.export()
        row = read_jsonl(self.output / 'logs-evidence.jsonl')[0]
        raw = self.raw_row('logs', row['source_row_index'], ['timestamp', 'container_name'])
        self.assertEqual(timestamp(row['timestamp']), raw['timestamp'])
        self.assertEqual(row['service'], raw['container_name'])

    def test_train_metric_null_counts_and_statistics_match_raw_values(self):
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        self.export()
        row = read_jsonl(self.output / 'metric-summaries.jsonl')[0]
        table = pq.read_table(ROOT / f'02_datasets/acquired/raw/{self.train_id}/metrics.parquet',
                              columns=['time', row['metric_name']])
        values = table[row['metric_name']]
        self.assertEqual(row['null_count'], values.null_count)
        self.assertEqual(row['row_count'], len(values))
        self.assertEqual(row['source_row_start'], 0)
        self.assertEqual(row['source_row_end_exclusive'], len(values))
        self.assertEqual(row['minimum'], pc.min(values).as_py())
        self.assertEqual(row['maximum'], pc.max(values).as_py())
        self.assertEqual(row['mean'], pc.mean(values).as_py())
        self.assertEqual(timestamp(row['observation_start']), pc.min(table['time']).as_py())
        self.assertEqual(timestamp(row['observation_end_exclusive']), pc.max(table['time']).as_py() + 1)


class ActualReleaseProvenanceTests(unittest.TestCase):
    """No test payload review: all-90 checks use IDs, schemas, hashes and joins."""

    def test_actual_release_validates_all_90_incidents_and_expected_ids(self):
        config = load_config()
        root = IMPL / 'data/inference'
        self.assertTrue(root.is_dir(), 'Final all-90 inference release is required')
        report = validate_inference(root, config)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['incident_count'], 90)
        self.assertEqual({row['incident_id'] for row in read_jsonl(root / 'observations.jsonl')},
                         set(config['incident_ids']))

    def test_actual_private_sidecars_match_all_source_bytes_and_90_ids(self):
        config = load_config()
        for name, spec in config['private_sources'].items():
            with self.subTest(name=name):
                private = IMPL / 'data/private' / name
                self.assertTrue(private.is_file(), 'Final private sidecar is required')
                self.assertEqual(private.read_bytes(), (ROOT / spec['path']).read_bytes())
                self.assertEqual(sha256(private), spec['sha256'])
                if name.endswith('.tsv'):
                    with private.open(encoding='utf-8-sig', newline='') as stream:
                        rows = list(csv.DictReader(stream, delimiter='\t'))
                else:
                    rows = read_jsonl(private)
                self.assertEqual(len(rows), 90)
                self.assertEqual({row['incident_id'] for row in rows}, set(config['incident_ids']))

    def test_source_processed_files_and_inventory_hashes_remain_pinned(self):
        for relative, digest in load_config()['source_hashes'].items():
            with self.subTest(source_role=Path(relative).name):
                self.assertEqual(sha256(ROOT / relative), digest)

    def test_private_split_retains_54_18_18_and_disjoint_30_families(self):
        config = load_config()
        with (IMPL / 'data/private/split-map.tsv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        self.assertEqual({split: sum(row['split'] == split for row in rows)
                          for split in ('train', 'dev', 'test')}, {'train': 54, 'dev': 18, 'test': 18})
        families = {}
        for row in rows:
            families.setdefault(row['scenario_family_id'], []).append(row['split'])
            self.assertEqual(row['split_version'], config['split_version'])
        self.assertEqual(len(families), 30)
        self.assertTrue(all(len(values) == 3 and len(set(values)) == 1 for values in families.values()))


class ReviewReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='.receipt-fixture-', dir=IMPL / 'tests')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.inference = self.work / 'inference'
        release = IMPL / 'data/inference'
        self.assertTrue(release.is_dir(), 'Final inference release is required for receipt checks')
        shutil.copytree(release, self.inference)
        self.evidence = self.work / 'evidence.txt'
        self.evidence.write_text('Synthetic technical test receipt, no human approval.\n')
        self.receipt_path = self.work / 'receipt.json'
        self.receipt = {
            'schema_version': 'cs221-data-review-v1',
            'manifest_hash': sha256(self.inference / 'input-manifest.json'),
            'local_gate': 'pass',
            'evidence': [{'path': self.evidence.relative_to(IMPL).as_posix(), 'sha256': sha256(self.evidence)}],
            'human_reviews': [{'owner': owner, 'status': 'pending', 'reviewer': None}
                              for owner in ('A', 'B', 'C')],
        }
        write_json(self.receipt_path, self.receipt)

    def test_technical_receipt_passes_without_asserting_human_review(self):
        result = validate_review_receipt(self.receipt_path, self.inference)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['human_gate'], 'not_asserted')

    def test_manifest_change_invalidates_receipt(self):
        manifest = self.inference / 'input-manifest.json'
        manifest.write_bytes(manifest.read_bytes() + b'\n')
        with self.assertRaises(DataContractError) as caught:
            validate_review_receipt(self.receipt_path, self.inference)
        self.assertEqual(caught.exception.code, 'RECEIPT_MANIFEST')

    def test_evidence_artifact_change_invalidates_receipt(self):
        self.evidence.write_text('Changed technical evidence.\n')
        with self.assertRaises(DataContractError) as caught:
            validate_review_receipt(self.receipt_path, self.inference)
        self.assertEqual(caught.exception.code, 'RECEIPT_EVIDENCE_HASH')

    def test_pending_human_review_cannot_be_treated_as_approved(self):
        with self.assertRaises(DataContractError) as caught:
            validate_review_receipt(self.receipt_path, self.inference, require_human=True)
        self.assertEqual(caught.exception.code, 'HUMAN_REVIEW_PENDING')


if __name__ == '__main__':
    unittest.main()
