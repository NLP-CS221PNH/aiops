"""Adversarial release tests; every mutable payload comes from TRAIN fixtures."""
from __future__ import annotations

import copy
import csv
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from src.data.common import (
    DEFAULT_CONFIG, FILES, IMPL, ROOT, DataContractError, canonical_hash,
    load_config, parse_json, read_jsonl, safe_path, sha256, validate_inference,
    validate_record, write_json, write_jsonl,
)
from src.data.export_inference_data import export_inference_data
from src.data.package_inference import package_inference


class TrainFixture(unittest.TestCase):
    """Use split administration to select content before constructing fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()
        with (ROOT / cls.base_config['private_sources']['split-map.tsv']['path']).open(
                encoding='utf-8-sig', newline='') as stream:
            train_ids = sorted(row['incident_id'] for row in csv.DictReader(stream, delimiter='\t')
                               if row['split'] == 'train')
        cls.train_id, cls.other_train_id = train_ids[:2]
        cls.templates = {}
        for name, spec in cls.base_config['inference_sources'].items():
            # Only selected train content is retained or exposed to assertions.
            with (ROOT / spec['path']).open(encoding='utf-8-sig') as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    row = parse_json(line)
                    if row['incident_id'] == cls.train_id:
                        cls.templates[name] = [row]
                        break
            if name not in cls.templates:
                raise AssertionError('Selected train incident has missing modality')
        observation = cls.templates['observations.jsonl'][0]
        for key, name in [('log_span_ids', 'logs-evidence.jsonl'),
                          ('metric_summary_ids', 'metric-summaries.jsonl'),
                          ('trace_span_ids', 'trace-evidence.jsonl')]:
            observation[key] = [cls.templates[name][0]['evidence_id']]

    def setUp(self):
        temp_parent = IMPL / '.test-work'
        temp_parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='boundary-', dir=temp_parent)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.source = self.work / 'source'
        self.config_path = self.work / 'data.yaml'
        self.output = self.work / 'inference'
        self.config = copy.deepcopy(self.base_config)
        self.config['incident_ids'] = [self.train_id]
        self.config['expected_counts']['incidents'] = 1
        self.rows = copy.deepcopy(self.templates)
        self.refresh_sources()

    def refresh_sources(self):
        for name, rows in self.rows.items():
            path = self.source / self.config['inference_sources'][name]['path']
            write_jsonl(path, rows)
            self.config['inference_sources'][name]['sha256'] = sha256(path)
        write_json(self.config_path, self.config)

    def export(self, output=None):
        return export_inference_data(self.config_path, self.source, output or self.output)

    def reject_export(self, codes=None):
        self.refresh_sources()
        with self.assertRaises(DataContractError) as caught:
            self.export()
        if codes:
            self.assertIn(caught.exception.code, codes)
        self.assertFalse(self.output.exists(), 'Rejected data must not be published')
        self.assertFalse(list(self.work.glob('.inference-staging-*')))

    def rewrite_release(self, name, rows):
        """Adversary can recompute content hashes, so schemas/joins must still gate."""
        write_jsonl(self.output / name, rows)
        manifest = parse_json((self.output / 'input-manifest.json').read_text())
        entry = next(row for row in manifest['files'] if row['path'] == name)
        entry.update(sha256=sha256(self.output / name),
                     bytes=(self.output / name).stat().st_size, rows=len(rows))
        manifest['content_hash'] = canonical_hash(manifest['files'])
        write_json(self.output / 'input-manifest.json', manifest)


class DataBoundaryTests(TrainFixture):
    def test_train_fixture_exports_without_private_source_files(self):
        self.assertFalse((self.source / self.config['private_sources']['ground_truth.jsonl']['path']).exists())
        result = self.export()
        self.assertEqual(result['incident_count'], 1)
        self.assertEqual(validate_inference(self.output, self.config)['evidence_count'], 3)

    def test_exact_public_schemas_reject_added_and_missing_fields(self):
        self.export()
        for name, kind in FILES.items():
            template = read_jsonl(self.output / name)[0]
            with self.subTest(kind=kind, mutation='extra'):
                row = copy.deepcopy(template)
                row['unclassified'] = 'value'
                with self.assertRaises(DataContractError):
                    validate_record(kind, row, self.config)
            with self.subTest(kind=kind, mutation='missing'):
                row = copy.deepcopy(template)
                row.pop('redaction_version')
                with self.assertRaises(DataContractError):
                    validate_record(kind, row, self.config)

    def test_source_nested_gold_fault_and_source_case_rejected(self):
        for private_key in ('gold', 'fault', 'source_case', 'source-case'):
            with self.subTest(private_key=private_key):
                self.rows = copy.deepcopy(self.templates)
                self.rows['logs-evidence.jsonl'][0]['text'] = {'wrapper': {private_key: 'hidden'}}
                self.reject_export({'SOURCE_SCHEMA'})

    def test_private_keys_rejected_even_with_attacker_modified_allowlist(self):
        self.export()
        for key in ('gold', 'fault', 'source_case', 'source-case', 'scenario_family_id', 'split'):
            with self.subTest(key=key):
                row = read_jsonl(self.output / 'logs-evidence.jsonl')[0]
                row[key] = 'private-value'
                config = copy.deepcopy(self.config)
                config['allowed_fields']['logs'].append(key)
                with self.assertRaises(DataContractError):
                    validate_record('logs', row, config)

    def test_public_nested_private_value_rejected_with_valid_outer_schema(self):
        self.export()
        row = read_jsonl(self.output / 'logs-evidence.jsonl')[0]
        row['text'] = {'gold': 'hidden'}
        self.rewrite_release('logs-evidence.jsonl', [row])
        with self.assertRaises(DataContractError):
            validate_inference(self.output, self.config)

    def test_duplicate_incident_rejected(self):
        self.rows['observations.jsonl'] *= 2
        self.reject_export({'INCIDENT_COUNT', 'INDEX_IDS'})

    def test_duplicate_evidence_rejected(self):
        self.rows['logs-evidence.jsonl'] *= 2
        self.reject_export({'DUPLICATE_EVIDENCE'})

    def test_duplicate_evidence_reference_rejected(self):
        self.rows['observations.jsonl'][0]['log_span_ids'] *= 2
        self.reject_export({'FIELD_TYPE', 'DUPLICATE_EVIDENCE'})

    def test_foreign_source_rejected(self):
        self.rows['logs-evidence.jsonl'][0]['source_file_id'] = self.other_train_id + ':logs'
        self.reject_export({'FOREIGN_SOURCE'})

    def test_foreign_evidence_join_rejected(self):
        self.rows['observations.jsonl'][0]['log_span_ids'] = [self.other_train_id + ':log:0']
        self.reject_export({'EVIDENCE_JOIN'})

    def test_cross_modality_join_rejected(self):
        self.rows['observations.jsonl'][0]['log_span_ids'] = self.rows['observations.jsonl'][0]['trace_span_ids']
        self.reject_export({'EVIDENCE_JOIN'})

    def test_unreferenced_evidence_rejected(self):
        orphan = copy.deepcopy(self.rows['logs-evidence.jsonl'][0])
        orphan['source_row_index'] += 1
        orphan['evidence_id'] = self.train_id + ':log:' + str(orphan['source_row_index'])
        self.rows['logs-evidence.jsonl'].append(orphan)
        self.reject_export({'EVIDENCE_COVERAGE'})

    def test_missing_modality_reference_rejected(self):
        self.rows['observations.jsonl'][0]['log_span_ids'] = []
        self.reject_export({'MISSING_MODALITY'})

    def test_additional_metrics_remain_available_beyond_top_metric_references(self):
        extra = copy.deepcopy(self.rows['metric-summaries.jsonl'][0])
        extra['metric_name'] = 'fixture_extra_metric'
        extra['evidence_id'] = self.train_id + ':metric:fixture_extra_metric'
        self.rows['metric-summaries.jsonl'].append(extra)
        self.refresh_sources()
        self.export()
        self.assertEqual(len(read_jsonl(self.output / 'metric-summaries.jsonl')), 2)
        self.assertEqual(len(read_jsonl(self.output / 'observations.jsonl')[0]['metric_summary_ids']), 1)

    def test_foreign_incident_cannot_replace_configured_id(self):
        self.export()
        wrong = copy.deepcopy(self.config)
        wrong['incident_ids'] = [self.other_train_id]
        with self.assertRaises(DataContractError):
            validate_inference(self.output, wrong)

    def test_wrong_source_hash_rejects_before_publication(self):
        source = self.source / self.config['inference_sources']['logs-evidence.jsonl']['path']
        source.write_bytes(source.read_bytes() + b'\n')
        with self.assertRaises(DataContractError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, 'HASH_MISMATCH')
        self.assertFalse(self.output.exists())

    def test_missing_source_rejects_before_publication(self):
        (self.source / self.config['inference_sources']['logs-evidence.jsonl']['path']).unlink()
        with self.assertRaises(DataContractError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, 'MISSING_FILE')
        self.assertFalse(self.output.exists())

    def test_path_traversal_absolute_ads_and_private_source_rejected(self):
        for relative in ('../../private/gold.json', '..\\private\\gold.json',
                         'C:\\private\\gold.json', '/private/gold.json',
                         'allowed/file.json:secret', 'private/gold.json'):
            with self.subTest(relative=relative), self.assertRaises(DataContractError):
                safe_path(self.work, relative, ['allowed'])

    def test_inference_source_cannot_target_private_even_under_processed_root(self):
        self.config['inference_sources']['logs-evidence.jsonl']['path'] = '02_datasets/processed/labels/ground_truth.jsonl'
        write_json(self.config_path, self.config)
        with self.assertRaises(DataContractError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, 'PATH_NOT_ALLOWED')

    @unittest.skipUnless(os.name == 'nt', 'Windows junction behavior requires Windows')
    def test_actual_windows_junction_cannot_escape_allowed_root(self):
        allowed, private = self.work / 'allowed', self.work / 'private'
        allowed.mkdir()
        private.mkdir()
        (private / 'gold.json').write_text('{}')
        junction = allowed / 'linked'
        def quote(path):
            return "'" + str(path).replace("'", "''") + "'"
        command = f"New-Item -ItemType Junction -Path {quote(junction)} -Target {quote(private)} | Out-Null"
        completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, 'Workspace junction fixture creation failed')
        try:
            self.assertEqual(junction.resolve(), private.resolve())
            with self.assertRaises(DataContractError):
                safe_path(self.work, 'allowed/linked/gold.json', ['allowed'])
        finally:
            os.rmdir(junction)

    def test_last_millisecond_is_retained_and_end_exclusive_rejected(self):
        end = dt.datetime.fromisoformat(self.rows['observations.jsonl'][0]['observation_end'])
        self.rows['trace-evidence.jsonl'][0]['timestamp'] = (end - dt.timedelta(milliseconds=1)).isoformat()
        self.refresh_sources()
        self.export()
        exported = read_jsonl(self.output / 'trace-evidence.jsonl')[0]
        self.assertEqual(exported['timestamp'], (end - dt.timedelta(milliseconds=1)).isoformat())
        self.rows['trace-evidence.jsonl'][0]['timestamp'] = end.isoformat()
        self.refresh_sources()
        with self.assertRaises(DataContractError) as caught:
            self.export(self.work / 'end-exclusive')
        self.assertEqual(caught.exception.code, 'WINDOW')
        self.assertFalse((self.work / 'end-exclusive').exists())

    def test_metric_all_null_preserves_missing_and_does_not_impute(self):
        metric = self.rows['metric-summaries.jsonl'][0]
        numeric = ('minimum', 'maximum', 'mean', 'first_quarter_mean', 'last_quarter_mean', 'change_score')
        metric['null_count'] = metric['row_count']
        metric.update({key: None for key in numeric})
        self.refresh_sources()
        self.export()
        result = read_jsonl(self.output / 'metric-summaries.jsonl')[0]
        self.assertEqual(result['missing_state'], 'all_missing')
        self.assertEqual(result['missing_reason'], 'all_source_values_null')
        self.assertTrue(all(result[key] is None for key in numeric))
        metric['mean'] = 0
        self.refresh_sources()
        with self.assertRaises(DataContractError) as caught:
            self.export(self.work / 'imputed')
        self.assertEqual(caught.exception.code, 'NULL_IMPUTED')

    def test_partial_metric_null_and_trace_null_status_are_preserved(self):
        metric = self.rows['metric-summaries.jsonl'][0]
        metric['null_count'] = 1
        self.assertGreater(metric['row_count'], 1)
        self.rows['trace-evidence.jsonl'][0]['status_code'] = None
        self.refresh_sources()
        self.export()
        self.assertEqual(read_jsonl(self.output / 'metric-summaries.jsonl')[0]['missing_state'], 'partial')
        trace = read_jsonl(self.output / 'trace-evidence.jsonl')[0]
        self.assertIsNone(trace['status_code'])
        self.assertEqual(trace['status_code_semantics'], 'unknown')
        self.assertEqual(trace['duration_raw'], self.rows['trace-evidence.jsonl'][0]['duration_raw'])
        self.assertEqual(trace['duration_unit'], 'unknown')

    def test_nonfinite_json_and_duplicate_keys_rejected(self):
        for text in ('{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}', '{"x":1,"x":2}'):
            with self.subTest(text=text), self.assertRaises(DataContractError):
                parse_json(text)
        self.export()
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=str(value)):
                row = read_jsonl(self.output / 'metric-summaries.jsonl')[0]
                row['mean'] = value
                with self.assertRaises(DataContractError):
                    validate_record('metrics', row, self.config)

    def test_label_only_changes_leave_all_public_bytes_and_manifest_identical(self):
        first = self.export()
        observation = self.rows['observations.jsonl'][0]
        observation['split'] = 'changed-administration-only'
        observation['scenario_family_id'] = 'changed-private-family'
        # Source-case/gold changes occur only in private fixture files/config.
        write_json(self.source / '02_datasets/processed/labels/fixture.json',
                   {'gold': 'changed', 'fault': 'changed', 'source_case': 'changed'})
        self.config['private_sources']['ground_truth.jsonl']['sha256'] = '0' * 64
        self.config['source_hashes']['02_datasets/processed/labels/fixture.json'] = '1' * 64
        self.config['split_version'] = 'private-new-version'
        self.refresh_sources()
        second_dir = self.work / 'second'
        second = self.export(second_dir)
        self.assertEqual(first, second)
        self.assertEqual({p.name: sha256(p) for p in self.output.iterdir()},
                         {p.name: sha256(p) for p in second_dir.iterdir()})

    def test_manifest_extra_private_field_and_content_hash_tamper_rejected(self):
        self.export()
        original = parse_json((self.output / 'input-manifest.json').read_text())
        for mutation in ({'gold': 'hidden'}, {'content_hash': '0' * 64},
                         {'schema_version': 'unknown-schema'}, {'config_hash': '0' * 64}):
            with self.subTest(field=next(iter(mutation))):
                manifest = {**original, **mutation}
                write_json(self.output / 'input-manifest.json', manifest)
                with self.assertRaises(DataContractError):
                    validate_inference(self.output, self.config)

    def test_file_content_hash_mismatch_is_rejected(self):
        self.export()
        path = self.output / 'logs-evidence.jsonl'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(DataContractError) as caught:
            validate_inference(self.output, self.config)
        self.assertEqual(caught.exception.code, 'HASH_MISMATCH')

    def test_package_rejects_private_and_extra_files(self):
        self.export()
        for name in ('ground_truth.jsonl', 'data-audit.json', 'private', 'raw.parquet', 'notes.txt'):
            with self.subTest(name=name):
                path = self.output / name
                path.write_text('not part of inference')
                try:
                    with self.assertRaises(DataContractError):
                        package_inference(self.output, self.work / 'bad.zip', self.config_path)
                    self.assertFalse((self.work / 'bad.zip').exists())
                finally:
                    path.unlink()

    def test_local_package_contains_only_exact_public_inventory_and_is_deterministic(self):
        self.export()
        first = package_inference(self.output, self.work / 'first.zip', self.config_path)
        second = package_inference(self.output, self.work / 'second.zip', self.config_path)
        self.assertEqual(first['sha256'], second['sha256'])
        with zipfile.ZipFile(self.work / 'first.zip') as archive:
            self.assertEqual(set(archive.namelist()), set(FILES) | {'incident-index.parquet', 'input-manifest.json'})
            self.assertIsNone(archive.testzip())
            for name in archive.namelist():
                self.assertEqual(archive.read(name), (self.output / name).read_bytes())

    def test_crash_during_staging_never_publishes_and_retry_is_clean(self):
        original_write = write_jsonl
        calls = []
        def crash_after_first(path, rows):
            calls.append(Path(path).name)
            if len(calls) == 2:
                raise OSError('simulated staging failure')
            return original_write(path, rows)
        with mock.patch('src.data.export_inference_data.write_jsonl', side_effect=crash_after_first):
            with self.assertRaises(OSError):
                self.export()
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.work.glob('.inference-staging-*')))
        self.export()
        self.assertEqual(validate_inference(self.output, self.config)['incident_count'], 1)

    def test_failed_changed_release_preserves_existing_release_bytes(self):
        self.export()
        before = {p.name: sha256(p) for p in self.output.iterdir()}
        self.rows['logs-evidence.jsonl'][0]['text'] = 'A changed train fixture message.'
        self.refresh_sources()
        with self.assertRaises(DataContractError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, 'OUTPUT_VERSION_CHANGE_REQUIRED')
        self.assertEqual(before, {p.name: sha256(p) for p in self.output.iterdir()})
        self.assertFalse(list(self.work.glob('.inference-staging-*')))


if __name__ == '__main__':
    unittest.main()
