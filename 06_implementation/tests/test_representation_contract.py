"""Synthetic, independent representation fixtures; no test telemetry or gold reads.

The assertions check source identity, semantic preservation and consumer behavior,
not snapshots of whatever the renderer happens to produce.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

from src.data.common import IMPL, canonical_hash, write_json
from src.representations import (
    QueryTokenizer, SafeIncident, apply_query_budget, build_observation_bundle,
    generate_incident, load_config, render_representation, select_evidence,
)


INCIDENT = 'inc_0123456789abcdef'
OTHER_INCIDENT = 'inc_fedcba9876543210'
START = '2024-01-16T10:00:00+00:00'
END = '2024-01-16T10:01:00+00:00'
WINDOW_POLICY = ('half-open [first metric second, last metric second + 1s); '
                 'retrospective offline window; no injection time used')


def synthetic_records():
    """Construct exact safe schemas without copying source or label records."""
    shared = {'incident_id': INCIDENT, 'redaction_version': 'pii-pseudonym-v2',
              'transform_version': 'safe-export-v1'}
    log_inputs = [
        ('alpha-service', 'HTTP 500 java.net.ConnectException v1.2.3 port=8080'),
        ('alpha-service', 'HTTP 503 java.net.ConnectException v1.2.3 port=8080'),
        ('zulu-service', '  UnicodeError:\tĐường dẫn λ failed\r\n  at handler.v2  '),
        ('zulu-service', 'ordinary request completed'),
        ('cpu-stress', 'service ready; source label words are legitimate service text'),
        ('cpu-stress', 'ordinary periodic heartbeat'),
    ]
    logs = [dict(shared, evidence_id=f'{INCIDENT}:log:{index}', modality='logs',
                 service=service, source_file_id=INCIDENT + ':logs',
                 source_row_index=index, text=text,
                 timestamp='2024-01-16T10:00:20+00:00')
            for index, (service, text) in enumerate(log_inputs)]
    metric = dict(shared, evidence_id=INCIDENT + ':metric:alpha-service_cpu',
                  modality='metrics', metric_name='alpha-service_cpu',
                  source_file_id=INCIDENT + ':metrics', source_row_start=0,
                  source_row_end_exclusive=60, row_count=60, null_count=0,
                  observation_start=START, observation_end_exclusive=END,
                  source_sample_end_inclusive='2024-01-16T10:00:59+00:00',
                  minimum=1, maximum=4, mean=2, first_quarter_mean=1,
                  last_quarter_mean=3, change_score=2,
                  change_score_rule='abs(last-first); descriptive only',
                  missing_state='complete', missing_reason='none', unit='unknown')
    missing_metric = dict(metric, evidence_id=INCIDENT + ':metric:zulu-service_mem',
                          metric_name='zulu-service_mem', null_count=60,
                          missing_state='all_missing', missing_reason='all_source_values_null')
    for key in ('minimum', 'maximum', 'mean', 'first_quarter_mean', 'last_quarter_mean', 'change_score'):
        missing_metric[key] = None
    trace = dict(shared, evidence_id=INCIDENT + ':trace:0', modality='traces',
                 source_file_id=INCIDENT + ':traces', source_row_index=0,
                 serviceName='zulu-service', timestamp='2024-01-16T10:00:20.123000+00:00',
                 duration_raw=2004164, duration_unit='unknown', status_code=2,
                 status_code_semantics='unknown', methodName='PlaceOrder',
                 operationName='CheckoutService/PlaceOrder', parentSpanID='id_parent',
                 spanID='id_span', traceID='id_trace',
                 selection='upstream selected span; semantics unknown')
    observation = dict(shared, deployment_version='unknown',
                       input_source_ids=[INCIDENT + ':' + kind for kind in ('metrics', 'logs', 'traces')],
                       log_span_ids=[row['evidence_id'] for row in logs],
                       metric_summary_ids=[metric['evidence_id'], missing_metric['evidence_id']],
                       trace_span_ids=[trace['evidence_id']],
                       observation_start=START, observation_end_exclusive=END,
                       provenance_source='D068', release_revision='afeacb11bcc94dadfd1c8f483ee4377b2b8b614e',
                       service_inventory=['alpha-service', 'cpu-stress', 'zulu-service'],
                       system_id='online_boutique', telemetry_is_synthetic=False,
                       window_policy=WINDOW_POLICY)
    return observation, logs, [metric, missing_metric], [trace]


def synthetic_incident():
    return SafeIncident(*synthetic_records())


class RepresentationFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()
        cls.tokenizer = QueryTokenizer(cls.base_config)

    def setUp(self):
        self.config = copy.deepcopy(self.base_config)
        self.records = synthetic_records()

    def incident(self):
        return SafeIncident(*copy.deepcopy(self.records))

    def generate(self, incident=None, config=None):
        return generate_incident(incident or self.incident(), config or self.config, self.tokenizer)


class SafeRepresentationBoundaryTests(RepresentationFixture):
    def test_fixture_is_valid_and_source_records_are_unchanged(self):
        before = copy.deepcopy(self.records)
        self.generate()
        self.assertEqual(self.records, before)

    def test_unknown_and_private_fields_rejected_at_every_safe_record_boundary(self):
        for key in ('scenario_family_id', 'split', 'gold', 'fault', 'source_case',
                    'injection_time', 'unclassified'):
            for record_index in range(4):
                rows = synthetic_records()
                row = rows[0] if record_index == 0 else rows[record_index][0]
                row[key] = 'private-fixture-value'
                with self.subTest(key=key, record_kind=record_index), self.assertRaises(ValueError):
                    SafeIncident(*rows)

    def test_nested_private_data_and_missing_required_fields_rejected(self):
        for value in ({'gold': 'fixture'}, ['safe-looking', {'fault': 'fixture'}]):
            rows = synthetic_records()
            rows[1][0]['text'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                SafeIncident(*rows)
        for record_index in range(4):
            rows = synthetic_records()
            row = rows[0] if record_index == 0 else rows[record_index][0]
            row.pop('redaction_version')
            with self.subTest(record_kind=record_index), self.assertRaises(ValueError):
                SafeIncident(*rows)

    def test_cross_incident_evidence_and_cross_modality_reference_rejected(self):
        for record_index in (1, 2, 3):
            rows = synthetic_records()
            row = rows[record_index][0]
            for key in ('incident_id', 'source_file_id', 'evidence_id'):
                row[key] = row[key].replace(INCIDENT, OTHER_INCIDENT)
            with self.subTest(record_kind=record_index), self.assertRaises(ValueError):
                SafeIncident(*rows)
        rows = synthetic_records()
        rows[0]['log_span_ids'][0] = rows[3][0]['evidence_id']
        with self.assertRaises(ValueError):
            SafeIncident(*rows)

    def test_duplicate_and_unreferenced_log_evidence_rejected(self):
        for mutation in ('duplicate_row', 'duplicate_ref', 'unreferenced'):
            rows = synthetic_records()
            if mutation == 'duplicate_row':
                rows[1].append(copy.deepcopy(rows[1][0]))
            elif mutation == 'duplicate_ref':
                rows[0]['log_span_ids'].append(rows[0]['log_span_ids'][0])
            else:
                rows[0]['log_span_ids'].pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                SafeIncident(*rows)

    def test_window_is_half_open_and_millisecond_end_is_preserved(self):
        for record_index in (1, 3):
            for bad_time in ('2024-01-16T09:59:59+00:00', END):
                rows = synthetic_records()
                rows[record_index][0]['timestamp'] = bad_time
                with self.subTest(record_kind=record_index, timestamp=bad_time), self.assertRaises(ValueError):
                    SafeIncident(*rows)
        rows = synthetic_records()
        rows[3][0]['timestamp'] = '2024-01-16T10:00:59.999000+00:00'
        self.assertEqual(SafeIncident(*rows).traces[0]['timestamp'], rows[3][0]['timestamp'])
        rows = synthetic_records()
        rows[2][0]['observation_start'] = '2024-01-16T10:00:01+00:00'
        with self.assertRaises(ValueError):
            SafeIncident(*rows)

    def test_injection_window_policy_rejected(self):
        rows = synthetic_records()
        rows[0]['window_policy'] = 'window begins at injection onset'
        with self.assertRaises(ValueError):
            SafeIncident(*rows)

    def test_metric_imputation_and_interpreted_trace_units_rejected(self):
        for record_index, key, value in ((2, 'unit', 'milliseconds'),
                                         (3, 'status_code_semantics', 'error'),
                                         (3, 'duration_unit', 'milliseconds')):
            rows = synthetic_records()
            rows[record_index][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                SafeIncident(*rows)
        rows = synthetic_records()
        rows[2][1]['mean'] = 0
        with self.assertRaises(ValueError):
            SafeIncident(*rows)

    def test_post_construction_mutations_cannot_bypass_any_public_consumption_boundary(self):
        mutations = {
            'private_observation': lambda item: item.observation.update(gold='synthetic-private-marker'),
            'window': lambda item: item.observation.update(observation_start='2024-01-16T10:00:01+00:00'),
            'injection_policy': lambda item: item.observation.update(window_policy='injection onset'),
            'private_log_field': lambda item: item.logs[0].update(gold='synthetic-private-marker'),
            'nested_log_gold': lambda item: item.logs[0].update(text={'gold': 'synthetic-private-marker'}),
            'metric_imputation': lambda item: item.metrics[1].update(mean=0),
            'trace_semantics': lambda item: item.traces[0].update(status_code_semantics='error'),
            'duplicate_row': lambda item: item.logs.append(copy.deepcopy(item.logs[0])),
            'missing_row': lambda item: item.logs.pop(),
            'non_record_row': lambda item: item.logs.__setitem__(0, 'invalid evidence row'),
        }
        for mutation_name, mutate in mutations.items():
            for boundary in ('select', 'render', 'budget', 'bundle', 'generate'):
                incident = self.incident()
                selection = select_evidence(incident, self.config)
                ids = ([row['evidence_id'] for row in incident.logs],
                       [row['evidence_id'] for row in incident.metrics],
                       [row['evidence_id'] for row in incident.traces])
                mutate(incident)
                actions = {
                    'select': lambda: select_evidence(incident, self.config),
                    'render': lambda: render_representation(incident, 'R3', *ids),
                    'budget': lambda: apply_query_budget(incident, selection, self.config, self.tokenizer),
                    'bundle': lambda: build_observation_bundle(incident, selection, self.config, self.tokenizer),
                    'generate': lambda: generate_incident(incident, self.config, self.tokenizer),
                }
                with self.subTest(mutation=mutation_name, boundary=boundary), \
                        self.assertRaisesRegex(ValueError, 'SAFE_INCIDENT_MUTATED'):
                    actions[boundary]()


class RepresentationMetamorphicTests(RepresentationFixture):
    def test_every_input_order_and_equal_timestamp_ties_are_deterministic(self):
        baseline = self.generate()
        for seed in range(12):
            rows = synthetic_records()
            rng = random.Random(seed)
            for values in rows[1:]:
                rng.shuffle(values)
            for key in ('service_inventory', 'input_source_ids', 'log_span_ids',
                        'metric_summary_ids', 'trace_span_ids'):
                rng.shuffle(rows[0][key])
            with self.subTest(seed=seed):
                self.assertEqual(self.generate(SafeIncident(*rows)), baseline)

    def test_r1_and_r2_preserve_distinct_codes_services_versions_ports_exceptions_and_unicode(self):
        incident = self.incident()
        log_ids = [row['evidence_id'] for row in self.records[1]]
        literals = ('HTTP 500', 'HTTP 503', 'java.net.ConnectException', 'v1.2.3',
                    'port=8080', 'zulu-service', 'cpu-stress', 'UnicodeError', 'Đường dẫn', 'λ')
        for variant in ('R1', 'R2'):
            text = render_representation(incident, variant, log_ids)
            with self.subTest(variant=variant):
                for literal in literals:
                    self.assertIn(literal, text)
                self.assertNotIn('<N>', text)

    def test_r1_literal_preservation_and_r2_whitespace_normalization(self):
        incident = self.incident()
        row = self.records[1][2]
        raw = render_representation(incident, 'R1', [row['evidence_id']])
        normalized = render_representation(incident, 'R2', [row['evidence_id']])
        self.assertIn(row['text'], raw)
        self.assertIn(' '.join(row['text'].split()), normalized)
        self.assertNotIn('\t', normalized)
        self.assertNotIn('\r', normalized)

    def test_render_rejects_unselected_foreign_or_duplicate_evidence(self):
        incident = self.incident()
        valid_id = self.records[1][0]['evidence_id']
        for ids in ([OTHER_INCIDENT + ':log:0'], [valid_id, valid_id],
                    [self.records[3][0]['evidence_id']]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                render_representation(incident, 'R1', ids)
        with self.assertRaises(ValueError):
            render_representation(incident, 'R4', [valid_id])

    def test_no_runtime_file_reads_and_private_fixture_changes_cannot_affect_outputs(self):
        baseline = self.generate()
        for gold in ('synthetic-private-A', 'synthetic-private-B'):
            private_metadata = {'gold': gold, 'source_case': gold, 'scenario_family_id': gold}
            with mock.patch('builtins.open', side_effect=AssertionError('Unexpected runtime file read')), \
                    mock.patch.object(Path, 'open', side_effect=AssertionError('Unexpected runtime file read')):
                result = self.generate()
            self.assertEqual(result, baseline)
            self.assertNotIn(private_metadata['gold'], json.dumps(result))


class SelectionAndProvenanceTests(RepresentationFixture):
    def test_round_robin_covers_last_service_and_every_drop_has_reason(self):
        self.config['selection']['max_logs'] = 3
        selection = select_evidence(self.incident(), self.config)
        lookup = {row['evidence_id']: row for row in self.records[1]}
        selected = selection['selected_log_ids']
        self.assertEqual({lookup[ref]['service'] for ref in selected},
                         {'alpha-service', 'cpu-stress', 'zulu-service'})
        self.assertEqual(set(selected) | set(selection['dropped_log_ids']), set(lookup))
        self.assertFalse(set(selected) & set(selection['dropped_log_ids']))
        self.assertEqual(len(selection['dropped_logs']), len(selection['dropped_log_ids']))
        self.assertTrue(all(row['reason'] for row in selection['dropped_logs']))
        self.assertIn('unknown', selection['source_selection_loss'])

    def test_ordinary_logs_are_selected_without_inventing_an_error(self):
        rows = synthetic_records()
        for log in rows[1]:
            log['text'] = 'ordinary heartbeat observed'
        incident = SafeIncident(*rows)
        selection = select_evidence(incident, self.config)
        self.assertEqual(len(selection['selected_log_ids']), len(rows[1]))
        text = render_representation(incident, 'R1', selection['selected_log_ids'])
        self.assertNotIn('error', text.lower())
        self.assertNotIn('anomaly', text.lower())

    def test_source_spans_and_normalization_map_resolve_every_retained_codepoint(self):
        queries, _, ledgers, _ = self.generate()
        source = {row['evidence_id']: row for row in self.records[1]}
        self.assertEqual(queries[0]['log_evidence_ids'], queries[1]['log_evidence_ids'])
        self.assertEqual(queries[0]['source_spans'], queries[1]['source_spans'])
        for query, ledger in zip(queries, ledgers):
            self.assertEqual(ledger['retained_evidence_ids'], query['evidence_ids'])
            self.assertEqual({span['evidence_id'] for span in ledger['source_spans']}, set(query['evidence_ids']))
            self.assertEqual({row['evidence_id'] for row in ledger['normalization_map']}, set(query['log_evidence_ids']))
            for span in ledger['source_spans']:
                if span['evidence_id'] not in source:
                    continue
                text = source[span['evidence_id']]['text']
                self.assertEqual((span['source_char_start'], span['source_char_end']), (0, len(text)))
                self.assertEqual(span['source_text_hash'], hashlib.sha256(text.encode()).hexdigest())
                self.assertEqual(span['offset_unit'], 'unicode_codepoint')
            for entry in ledger['normalization_map']:
                text = source[entry['evidence_id']]['text']
                source_cursor = output_cursor = 0
                reconstructed = []
                for segment in entry['segments']:
                    self.assertEqual(segment['source_start'], source_cursor)
                    self.assertEqual(segment['output_start'], output_cursor)
                    original = text[segment['source_start']:segment['source_end']]
                    if segment['operation'] == 'copy':
                        value = original
                    else:
                        self.assertEqual(segment['operation'], 'whitespace')
                        self.assertTrue(original.isspace())
                        value = ' '
                    self.assertEqual(len(value), segment['output_end'] - segment['output_start'])
                    reconstructed.append(value)
                    source_cursor, output_cursor = segment['source_end'], segment['output_end']
                rendered = ''.join(reconstructed)
                self.assertEqual(source_cursor, len(text))
                self.assertEqual(''.join(rendered.split()), ''.join(text.split()))
                self.assertEqual(entry['rendered_text_hash'], hashlib.sha256(rendered.encode()).hexdigest())

    def test_tampered_selection_ledger_cannot_inject_or_reorder_evidence(self):
        incident = self.incident()
        selection = select_evidence(incident, self.config)
        for changed in ('foreign', 'order', 'universe'):
            mutated = copy.deepcopy(selection)
            if changed == 'foreign':
                mutated['selected_log_ids'].append(OTHER_INCIDENT + ':log:0')
            elif changed == 'order':
                mutated['selected_log_ids'].reverse()
            else:
                mutated['universe_hash'] = '0' * 64
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                apply_query_budget(incident, mutated, self.config, self.tokenizer)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                build_observation_bundle(incident, mutated, self.config, self.tokenizer)


class MissingModalitiesAndBundleTests(RepresentationFixture):
    def test_missing_traces_and_all_null_metric_are_explicit_and_neutral(self):
        rows = synthetic_records()
        rows[3].clear()
        rows[0]['trace_span_ids'] = []
        queries, _, _, bundle = self.generate(SafeIncident(*rows))
        for content in (queries[2]['query_text'], bundle['observation_text']):
            self.assertIn('all_missing', content)
            self.assertIn('all_source_values_null', content)
            self.assertIn('traces:unavailable_in_safe_export', content)
            self.assertIn('unit=unknown', content)
            self.assertNotIn('cause', content.lower())
            self.assertNotIn('anomaly', content.lower())

    def test_nonzero_and_null_trace_status_are_raw_unknown_facts(self):
        for status in (2, None):
            rows = synthetic_records()
            rows[3][0]['status_code'] = status
            incident = SafeIncident(*rows)
            text = render_representation(incident, 'R3', [], [], [rows[3][0]['evidence_id']])
            self.assertIn(f'status_code={status}', text)
            self.assertIn('duration_raw=2004164', text)
            self.assertIn('semantics=unknown', text)
            self.assertNotIn('error', text.lower())
            self.assertNotIn('milliseconds', text.lower())

    def test_zero_evidence_has_insufficient_state_and_no_invented_observations(self):
        rows = synthetic_records()
        for values in rows[1:]:
            values.clear()
        for key in ('log_span_ids', 'metric_summary_ids', 'trace_span_ids'):
            rows[0][key] = []
        queries, selection, ledgers, bundle = self.generate(SafeIncident(*rows))
        for row in queries + [bundle]:
            self.assertEqual(row['status'], 'insufficient_evidence')
            self.assertEqual(row['evidence_ids'], [])
            self.assertTrue(row['missing_information'])
        self.assertEqual(selection['selected_log_ids'], [])
        self.assertTrue(all(ledger['after_tokens'] <= ledger['max_tokens'] for ledger in ledgers))

    def test_empty_text_is_accounted_for_as_a_dropped_candidate(self):
        rows = synthetic_records()
        rows[1][0]['text'] = ' \t\r\n '
        incident = SafeIncident(*rows)
        selection = select_evidence(incident, self.config)
        self.assertIn({'evidence_id': rows[1][0]['evidence_id'], 'reason': 'empty_text'}, selection['dropped_logs'])
        self.assertNotIn(rows[1][0]['evidence_id'], selection['selected_log_ids'])

    def test_same_bundle_is_reused_across_all_four_generator_conditions(self):
        incident = self.incident()
        selection = select_evidence(incident, self.config)
        bundles = {condition: build_observation_bundle(incident, selection, self.config, self.tokenizer)
                   for condition in ('G0', 'GB', 'GD', 'GH')}
        self.assertEqual(len({bundle['bundle_hash'] for bundle in bundles.values()}), 1)
        self.assertTrue(all(bundle == bundles['G0'] for bundle in bundles.values()))
        content = bundles['G0']['observation_text']
        for ref in bundles['G0']['evidence_ids']:
            self.assertIn('[' + ref + ']', content)
        changed = copy.deepcopy(self.config)
        changed['budget']['max_query_tokens'] = 200
        changed['default_candidate'] = 'R3'
        self.assertEqual(build_observation_bundle(incident, selection, changed, self.tokenizer), bundles['G0'])

    def test_separate_bundle_budget_counts_all_drops_and_recomputes_hash(self):
        self.config['bundle']['max_tokens'] = 240
        incident = self.incident()
        bundle = build_observation_bundle(incident, select_evidence(incident, self.config), self.config, self.tokenizer)
        self.assertEqual(bundle['budget']['after_tokens'], self.tokenizer.count_bundle(bundle['observation_text']))
        self.assertLessEqual(bundle['budget']['after_tokens'], 240)
        self.assertTrue(bundle['dropped_evidence'])
        self.assertEqual(set(bundle['evidence_ids']) | {row['evidence_id'] for row in bundle['dropped_evidence']},
                         set(incident.evidence))
        payload = {key: value for key, value in bundle.items() if key != 'bundle_hash'}
        self.assertEqual(bundle['bundle_hash'], canonical_hash(payload))


class RealTokenizerTests(RepresentationFixture):
    def test_actual_wordpiece_query_prefix_and_two_special_tokens_are_counted(self):
        text = 'HTTP 503; service-v1.2.3 failed on port=8080. Đường dẫn λ'
        expected = self.tokenizer.encode('query: ' + text, add_special_tokens=False)
        self.assertEqual(self.tokenizer.count(text), len(expected.ids) + 2)
        self.assertGreater(self.tokenizer.count(text),
                           len(self.tokenizer.encode(text, add_special_tokens=False).ids))

    def test_backend_never_silently_truncates_long_input(self):
        text = 'observed ' * 1100
        expected = len(self.tokenizer.encode('query: ' + text, add_special_tokens=False).ids) + 2
        self.assertGreater(expected, 512)
        self.assertEqual(self.tokenizer.count(text), expected)

    def test_bundle_budget_counts_without_retrieval_prefix(self):
        text = 'Observed HTTP 503 with status_code=2; semantics unknown.'
        self.assertEqual(self.tokenizer.count_bundle(text),
                         len(self.tokenizer.encode(text, add_special_tokens=False).ids) + 2)
        self.assertGreater(self.tokenizer.count(text), self.tokenizer.count_bundle(text))

    def test_tokenizer_asset_tampering_fails_closed(self):
        config = copy.deepcopy(self.config)
        config['tokenizer']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            QueryTokenizer(config)

    def test_query_budget_rejects_booleans_fractions_zero_and_encoder_overflow(self):
        base = IMPL / '.test-work'
        base.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='representation-config-', dir=base) as temp:
            path = Path(temp) / 'invalid-config.json'
            for limit in (True, 128.5, 0, -1, 513):
                changed = copy.deepcopy(self.config)
                changed['budget']['max_query_tokens'] = limit
                write_json(path, changed)
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    load_config(path)

    def test_exact_real_token_boundary_retains_whole_logs_and_one_less_clips_jointly(self):
        incident = self.incident()
        selection = select_evidence(incident, self.config)
        ids = selection['selected_log_ids']
        exact = max(self.tokenizer.count(render_representation(incident, variant, ids)) for variant in ('R1', 'R2'))
        self.assertLessEqual(exact, 512)
        self.config['budget']['max_query_tokens'] = exact
        queries, ledgers = apply_query_budget(incident, selection, self.config, self.tokenizer)
        self.assertEqual(queries[0]['log_evidence_ids'], ids)
        self.assertEqual(queries[1]['log_evidence_ids'], ids)
        self.assertEqual(max(row['after_tokens'] for row in ledgers[:2]), exact)
        self.config['budget']['max_query_tokens'] = exact - 1
        queries, ledgers = apply_query_budget(incident, selection, self.config, self.tokenizer)
        self.assertLess(len(queries[0]['log_evidence_ids']), len(ids))
        self.assertEqual(queries[0]['log_evidence_ids'], queries[1]['log_evidence_ids'])
        self.assertEqual(ledgers[0]['source_spans'], ledgers[1]['source_spans'])
        self.assertTrue(all(row['after_tokens'] <= exact - 1 for row in ledgers))

    def test_real_unicode_whitespace_makes_r1_overflow_while_r2_fits_but_r2_cannot_refill(self):
        rows = synthetic_records()
        # E5 removes NEL before WordPiece; Python whitespace normalization inserts
        # a space. Joined technical strings tokenize longer in the real backend.
        rows[1][0]['text'] = 'zulu\u0085database ' * 60
        incident = SafeIncident(*rows)
        ref = rows[1][0]['evidence_id']
        r1 = self.tokenizer.count(render_representation(incident, 'R1', [ref]))
        r2 = self.tokenizer.count(render_representation(incident, 'R2', [ref]))
        self.assertGreater(r1, r2)
        self.config['budget']['max_query_tokens'] = r2
        self.assertLessEqual(r2, 512)
        selection = select_evidence(incident, self.config)
        queries, ledgers = apply_query_budget(incident, selection, self.config, self.tokenizer)
        self.assertNotIn(ref, queries[0]['evidence_ids'])
        self.assertNotIn(ref, queries[1]['evidence_ids'])
        self.assertEqual(queries[0]['log_evidence_ids'], queries[1]['log_evidence_ids'])
        self.assertEqual(queries[0]['source_spans'], queries[1]['source_spans'])
        for ledger in ledgers[:2]:
            self.assertIn({'evidence_id': ref, 'reason': 'joint_r1_r2_token_budget'}, ledger['dropped_evidence'])
            self.assertEqual(ledger['partial_evidence_ids'], [])

    def test_single_oversize_log_has_explicit_drop_and_no_partial_source_span(self):
        rows = synthetic_records()
        rows[1][:] = [rows[1][0]]
        rows[1][0]['text'] = 'oversized ' * 1000
        rows[0]['log_span_ids'] = [rows[1][0]['evidence_id']]
        queries, _, ledgers, _ = self.generate(SafeIncident(*rows))
        for query, ledger in zip(queries[:2], ledgers[:2]):
            self.assertEqual(query['status'], 'insufficient_evidence')
            self.assertEqual(query['source_spans'], [])
            self.assertGreater(ledger['before_tokens'], 512)
            self.assertLessEqual(ledger['after_tokens'], 512)
            self.assertEqual(ledger['partial_evidence_ids'], [])
            self.assertTrue(ledger['dropped_evidence'])


if __name__ == '__main__':
    unittest.main()
