"""Deterministic representations of already exported observations, never labels.

All clipping drops whole evidence blocks. Offsets address Unicode code points in
the redacted safe export, not unredacted raw telemetry. No model/network calls.
"""
from __future__ import annotations

import copy
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass

from .corpus.tokenizer import CorpusTokenizer
from .data.common import (IMPL, canonical_hash, read_json, require, timestamp,
                          validate_record)

DEFAULT_CONFIG = IMPL / 'configs/representation.yaml'
CODE_VERSION = 'whole-evidence-representations-v1'
WINDOW_POLICY = ('half-open [first metric second, last metric second + 1s); '
                 'retrospective offline window; no injection time used')
SAFE_SCHEMA = {'allowed_fields': read_json(IMPL / 'configs/data.yaml')['allowed_fields']}


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def load_config(path=DEFAULT_CONFIG):
    config = read_json(path)
    require(config['schema_version'] == 'cs221-representation-config-v1', 'CONFIG_SCHEMA')
    require(config['code_version'] == CODE_VERSION, 'CODE_VERSION')
    require(config['normalization_version'] == 'whitespace-only-v1', 'NORMALIZATION')
    require(config['selection']['algorithm'] == 'service-round-robin-v1', 'SELECTOR')
    require(config['budget']['algorithm'] == 'whole-block-joint-v1', 'BUDGET_POLICY')
    require(config['tokenizer']['prefix'] == 'query: ', 'QUERY_PREFIX')
    require(config['tokenizer']['max_length'] == 512, 'ENCODER_LIMIT')
    require(config['tokenizer']['truncation'] is False, 'IMPLICIT_TRUNCATION')
    for group, keys in [('selection', ('logs_per_service', 'max_logs', 'max_metrics', 'max_traces')),
                        ('bundle', ('max_tokens', 'max_metrics', 'max_traces'))]:
        for key in keys:
            require(type(config[group][key]) is int and config[group][key] > 0, 'CONFIG_BUDGET')
    require(type(config['budget']['max_query_tokens']) is int and
            0 < config['budget']['max_query_tokens'] <= 512, 'QUERY_LIMIT')
    return config


class QueryTokenizer(CorpusTokenizer):
    """Reuse verified local E5 assets; never truncate implicitly."""

    def count_bundle(self, content):
        # Candidate planning tokenizer only; plan07 must count its actual model.
        return len(self.encode(content, add_special_tokens=True).ids)


@dataclass
class SafeIncident:
    observation: dict
    logs: list
    metrics: list
    traces: list

    def __post_init__(self):
        # Copy caller-owned data and canonicalize unordered reference sets.
        self.observation = copy.deepcopy(self.observation)
        validate_record('observations', self.observation, SAFE_SCHEMA)
        require(self.observation['window_policy'] == WINDOW_POLICY, 'WINDOW_POLICY')
        for key, value in self.observation.items():
            if isinstance(value, list):
                value.sort()
        start, end = (timestamp(self.observation[key]) for key in
                      ('observation_start', 'observation_end_exclusive'))
        all_ids = set()
        for kind, refs in [('logs', 'log_span_ids'), ('metrics', 'metric_summary_ids'),
                           ('traces', 'trace_span_ids')]:
            rows = copy.deepcopy(getattr(self, kind))
            ids = set()
            for row in rows:
                validate_record(kind, row, SAFE_SCHEMA)
                require(row['incident_id'] == self.incident_id, 'FOREIGN_INCIDENT')
                require(row['evidence_id'] not in all_ids, 'DUPLICATE_EVIDENCE')
                all_ids.add(row['evidence_id'])
                ids.add(row['evidence_id'])
                if kind == 'metrics':
                    require(timestamp(row['observation_start']) == start and
                            timestamp(row['observation_end_exclusive']) == end, 'WINDOW')
                else:
                    require(start <= timestamp(row['timestamp']) < end, 'WINDOW')
                require(row['redaction_version'] == self.observation['redaction_version'] and
                        row['transform_version'] == self.observation['transform_version'], 'TRANSFORM_VERSION')
            references = set(self.observation[refs])
            require(references <= ids, 'EVIDENCE_JOIN')
            if kind != 'metrics':
                require(references == ids, 'EVIDENCE_COVERAGE')
            setattr(self, kind, sorted(rows, key=lambda row: row['evidence_id']))
        require(set(self.observation['input_source_ids']) ==
                {self.incident_id + ':' + kind for kind in ('logs', 'metrics', 'traces')}, 'SOURCE_IDS')
        self._observation_hash = canonical_hash(self.observation)
        self._evidence_hashes = {ref: canonical_hash(row) for ref, row in self.evidence.items()}

    def assert_unchanged(self, evidence_ids=None):
        """Reject mutation after validation at each public consumption boundary.

        Render calls check their selected rows; selectors check the full universe.
        These private snapshots are validation state, never serialized payloads.
        """
        require(canonical_hash(self.observation) == self._observation_hash, 'SAFE_INCIDENT_MUTATED')
        rows = self.logs + self.metrics + self.traces
        require(all(isinstance(row, dict) for row in rows), 'SAFE_INCIDENT_MUTATED')
        require(all(isinstance(row.get('evidence_id'), str) for row in rows), 'SAFE_INCIDENT_MUTATED')
        evidence = self.evidence
        require(len(evidence) == len(rows) and set(evidence) == set(self._evidence_hashes), 'SAFE_INCIDENT_MUTATED')
        ids = evidence if evidence_ids is None else evidence_ids
        for ref in ids:
            require(ref in evidence, 'EVIDENCE_JOIN')
            require(canonical_hash(evidence[ref]) == self._evidence_hashes[ref], 'SAFE_INCIDENT_MUTATED')

    @property
    def incident_id(self):
        return self.observation['incident_id']

    @property
    def evidence(self):
        return {row['evidence_id']: row for row in self.logs + self.metrics + self.traces}

    @property
    def window(self):
        return {key: self.observation[key] for key in
                ('observation_start', 'observation_end_exclusive', 'window_policy')}


def normalize_log(text):
    """Whitespace only: preserve every non-whitespace code point and its order.

    Map segments are half-open source and output offsets, including whitespace
    replacements. No numeric replacement, timestamp stripping or translation.
    """
    output, mapping, cursor = [], [], 0
    for match in re.finditer(r'\s+|\S+', text):
        original = match.group()
        replacement = ' ' if original.isspace() else original
        output.append(replacement)
        mapping.append({'source_start': match.start(), 'source_end': match.end(),
                        'output_start': cursor, 'output_end': cursor + len(replacement),
                        'operation': 'copy' if replacement == original else 'whitespace'})
        cursor += len(replacement)
    return ''.join(output), mapping


def _round_robin(rows, service_key):
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda row: (timestamp(row['timestamp']), row[service_key], row['evidence_id'])):
        groups[row[service_key]].append(row)
    return [groups[service][index] for index in range(max(map(len, groups.values()), default=0))
            for service in sorted(groups) if index < len(groups[service])]


def _metric_order(rows):
    # Descriptive selection only; null scores are last, never imputed.
    return sorted(rows, key=lambda row: (row['change_score'] is None,
                                        -(row['change_score'] or 0), row['metric_name'], row['evidence_id']))


def _span(row):
    result = {key: row[key] for key in ('evidence_id', 'source_file_id', 'transform_version', 'redaction_version')}
    if row['modality'] == 'metrics':
        result.update(source_row_start=row['source_row_start'],
                      source_row_end_exclusive=row['source_row_end_exclusive'])
    else:
        result['source_row_index'] = row['source_row_index']
    if row['modality'] == 'logs':
        result.update(source_char_start=0, source_char_end=len(row['text']),
                      source_text_hash=text_hash(row['text']), offset_unit='unicode_codepoint')
    return result


def select_evidence(incident, config):
    incident.assert_unchanged()
    rules = config['selection']
    chosen, dropped, service_counts = [], [], defaultdict(int)
    for row in _round_robin(incident.logs, 'service'):
        reason = ('service_quota' if service_counts[row['service']] >= rules['logs_per_service']
                  else 'incident_quota' if len(chosen) >= rules['max_logs']
                  else 'empty_text' if not row['text'].strip() else None)
        if reason:
            dropped.append({'evidence_id': row['evidence_id'], 'reason': reason})
        else:
            chosen.append(row['evidence_id'])
            service_counts[row['service']] += 1
    metrics = _metric_order(incident.metrics)
    traces = _round_robin(incident.traces, 'serviceName')
    return {'incident_id': incident.incident_id, 'window': incident.window,
            'selection_version': config['selection_version'],
            'universe_hash': canonical_hash(incident.logs + incident.metrics + incident.traces),
            'candidate_log_ids': [row['evidence_id'] for row in incident.logs],
            'selected_log_ids': chosen, 'dropped_log_ids': [row['evidence_id'] for row in dropped],
            'dropped_logs': dropped,
            'selected_metric_ids': [row['evidence_id'] for row in metrics[:rules['max_metrics']]],
            'selected_trace_ids': [row['evidence_id'] for row in traces[:rules['max_traces']]],
            'enrichment_dropped': [{'evidence_id': row['evidence_id'], 'reason': 'modality_quota'}
                                   for row in metrics[rules['max_metrics']:] + traces[rules['max_traces']:]],
            'source_selection_loss': 'unknown_outside_safe_export; upstream numeric dedup cannot be reversed',
            'ordering': 'service round robin; within service UTC timestamp/evidence ID; no downstream error filter'}


def _lookup(incident, ids, modality):
    require(len(ids) == len(set(ids)), 'DUPLICATE_SELECTION')
    evidence = incident.evidence
    require(all(ref in evidence and evidence[ref]['modality'] == modality for ref in ids), 'EVIDENCE_JOIN')
    return [evidence[ref] for ref in ids]


def _log_block(row, normalize):
    value = normalize_log(row['text'])[0] if normalize else row['text']
    return f"Log {row['service']} @ {row['timestamp']}: {value}"


def _metric_block(row):
    return (f"Metric {row['metric_name']}: first={row['first_quarter_mean']}; last={row['last_quarter_mean']}; "
            f"change_score={row['change_score']} (descriptive); unit={row['unit']}; "
            f"missing={row['missing_state']} ({row['missing_reason']}); nulls={row['null_count']}/{row['row_count']}.")


def _trace_block(row):
    return (f"Trace {row['serviceName']} @ {row['timestamp']}: {row['operationName']}; "
            f"method={row['methodName']}; duration_raw={row['duration_raw']}; unit={row['duration_unit']}; "
            f"status_code={row['status_code']}; semantics={row['status_code_semantics']}.")


def _missing(incident, log_ids, metric_ids, trace_ids, multimodal=True):
    result = []
    for kind, selected in [('logs', log_ids)] + ([('metrics', metric_ids), ('traces', trace_ids)] if multimodal else []):
        if not selected:
            result.append(kind + (':unavailable_in_safe_export' if not getattr(incident, kind)
                                  else ':no_evidence_retained_by_selection_or_budget'))
    if multimodal and any(row['missing_state'] != 'complete' for row in incident.metrics
                          if row['evidence_id'] in metric_ids):
        result.append('metrics:source_null_values_preserved')
    if multimodal:
        result.extend(['metric_units:unknown', 'trace_duration_units:unknown', 'trace_status_semantics:unknown'])
    return result


def render_representation(incident, representation_id, log_ids, metric_ids=(), trace_ids=()):
    incident.assert_unchanged(list(log_ids) + list(metric_ids) + list(trace_ids))
    require(representation_id in ('R1', 'R2', 'R3'), 'REPRESENTATION_ID')
    require(representation_id == 'R3' or (not metric_ids and not trace_ids), 'MODALITY_CONTRACT')
    logs = _lookup(incident, log_ids, 'logs')
    metrics = _lookup(incident, metric_ids, 'metrics')
    traces = _lookup(incident, trace_ids, 'traces')
    lines = ['Incident observations. Retrospective window [' + incident.window['observation_start'] +
             ', ' + incident.window['observation_end_exclusive'] + ').']
    lines.extend(_log_block(row, representation_id != 'R1') for row in
                 sorted(logs, key=lambda row: (row['service'], timestamp(row['timestamp']), row['evidence_id'])))
    if representation_id == 'R3':
        lines.extend(_metric_block(row) for row in sorted(metrics, key=lambda row: row['metric_name']))
        lines.extend(_trace_block(row) for row in sorted(traces, key=lambda row:
                     (row['serviceName'], timestamp(row['timestamp']), row['evidence_id'])))
    missing = _missing(incident, log_ids, metric_ids, trace_ids, representation_id == 'R3')
    if missing:
        lines.append('Missing information: ' + '; '.join(missing) + '.')
    return '\n'.join(lines)


def _provenance(incident, log_ids, metric_ids=(), trace_ids=(), normalized=False):
    evidence = incident.evidence
    spans = [_span(evidence[ref]) for ref in list(log_ids) + list(metric_ids) + list(trace_ids)]
    maps = []
    for ref in log_ids:
        source = evidence[ref]['text']
        value, mapping = normalize_log(source) if normalized else (source, [
            {'source_start': 0, 'source_end': len(source), 'output_start': 0,
             'output_end': len(source), 'operation': 'copy'}])
        maps.append({'evidence_id': ref, 'source_text_hash': text_hash(source),
                     'rendered_text_hash': text_hash(value), 'segments': mapping})
    return spans, maps


def apply_query_budget(incident, selection, config, tokenizer):
    require(selection == select_evidence(incident, config), 'SELECTION_MISMATCH')
    limit = config['budget']['max_query_tokens']
    original = selection['selected_log_ids']
    retained, log_drops = [], []
    for ref in original:
        trial = retained + [ref]
        if all(tokenizer.count(render_representation(incident, variant, trial)) <= limit for variant in ('R1', 'R2')):
            retained = trial
        else:
            log_drops.append({'evidence_id': ref, 'reason': 'joint_r1_r2_token_budget'})
    # Intentional modality enrichment: one metric and one trace have priority,
    # then common retained logs, then remaining modality candidates.
    metric_ids, trace_ids = selection['selected_metric_ids'], selection['selected_trace_ids']
    priority = [('metrics', ref) for ref in metric_ids[:1]] + [('traces', ref) for ref in trace_ids[:1]]
    priority += [('logs', ref) for ref in retained]
    priority += [('metrics', ref) for ref in metric_ids[1:]] + [('traces', ref) for ref in trace_ids[1:]]
    r3, r3_drops = {'logs': [], 'metrics': [], 'traces': []}, []
    for kind, ref in priority:
        trial = copy.deepcopy(r3)
        trial[kind].append(ref)
        content = render_representation(incident, 'R3', trial['logs'], trial['metrics'], trial['traces'])
        if tokenizer.count(content) <= limit:
            r3 = trial
        else:
            r3_drops.append({'evidence_id': ref, 'reason': 'r3_token_budget'})
    queries, ledgers = [], []
    for variant in ('R1', 'R2', 'R3'):
        logs, metrics, traces = ((retained, [], []) if variant != 'R3' else
                                 (r3['logs'], r3['metrics'], r3['traces']))
        before = render_representation(incident, variant, original if variant != 'R3' else retained,
                                       metric_ids if variant == 'R3' else [], trace_ids if variant == 'R3' else [])
        content = render_representation(incident, variant, logs, metrics, traces)
        require(tokenizer.count(content) <= limit, 'INSUFFICIENT_SCAFFOLD_BUDGET')
        ids = list(logs) + list(metrics) + list(traces)
        spans, maps = _provenance(incident, logs, metrics, traces, variant != 'R1')
        query_id = incident.incident_id + ':' + variant + ':' + config['representation_version']
        missing = _missing(incident, logs, metrics, traces, variant == 'R3')
        query = {'incident_id': incident.incident_id, 'query_id': query_id,
                 'representation_id': variant, 'representation_version': config['representation_version'],
                 'query_text': content, 'query_hash': text_hash(content), 'window': incident.window,
                 'evidence_ids': ids, 'log_evidence_ids': list(logs), 'source_spans': spans,
                 'missing_information': missing, 'query_is_synthetic': True,
                 'telemetry_is_synthetic': incident.observation['telemetry_is_synthetic'],
                 'status': 'ok' if ids else 'insufficient_evidence'}
        drops = log_drops if variant != 'R3' else log_drops + r3_drops
        ledger = {'incident_id': incident.incident_id, 'query_id': query_id,
                  'representation_id': variant, 'tokenizer_revision': tokenizer.revision,
                  'tokenizer_hash': config['tokenizer']['sha256'], 'prefix': tokenizer.prefix,
                  'special_tokens': 2, 'prefix_and_special_tokens': tokenizer.count(''),
                  'max_tokens': limit, 'before_tokens': tokenizer.count(before),
                  'after_tokens': tokenizer.count(content), 'retained_evidence_ids': ids,
                  'retained_log_ids': list(logs), 'source_spans': spans, 'normalization_map': maps,
                  'dropped_evidence': drops, 'partial_evidence_ids': [],
                  'clipping_unit': 'whole_evidence_block', 'query_hash': query['query_hash'],
                  'joint_retained_log_ids': retained, 'joint_dropped_logs': log_drops}
        queries.append(query)
        ledgers.append(ledger)
    return queries, ledgers


def build_observation_bundle(incident, selection, config, tokenizer):
    require(selection == select_evidence(incident, config), 'SELECTION_MISMATCH')
    # Independent of representation and retrieval condition; candidate budget.
    candidates = [('metrics', row['evidence_id']) for row in _metric_order(incident.metrics)[:config['bundle']['max_metrics']]]
    candidates += [('traces', row['evidence_id']) for row in _round_robin(incident.traces, 'serviceName')[:config['bundle']['max_traces']]]
    # Interleave modalities to retain observations from each when space allows.
    by_kind = {'logs': selection['selected_log_ids'],
               'metrics': [ref for kind, ref in candidates if kind == 'metrics'],
               'traces': [ref for kind, ref in candidates if kind == 'traces']}
    priority = [(kind, refs[index]) for index in range(max(map(len, by_kind.values()), default=0))
                for kind, refs in by_kind.items() if index < len(refs)]
    selected = {'logs': [], 'metrics': [], 'traces': []}
    drops = list(selection['dropped_logs'])
    considered = {ref for _, ref in priority}
    drops.extend({'evidence_id': ref, 'reason': 'bundle_modality_quota'} for ref in sorted(incident.evidence)
                 if ref not in considered and ref not in selection['dropped_log_ids'])
    def render(chosen):
        # IDs are part of generator text so observation citations are usable.
        parts = ['Observation evidence. Retrospective window [' + incident.window['observation_start'] +
                 ', ' + incident.window['observation_end_exclusive'] + ').']
        evidence = incident.evidence
        for kind in ('logs', 'metrics', 'traces'):
            for ref in chosen[kind]:
                row = evidence[ref]
                body = (_log_block(row, False) if kind == 'logs' else _metric_block(row)
                        if kind == 'metrics' else _trace_block(row))
                parts.append('[' + ref + '] ' + body)
        parts.append('Missing information: ' + '; '.join(_missing(incident, chosen['logs'], chosen['metrics'], chosen['traces'])) + '.')
        return '\n'.join(parts)
    for kind, ref in priority:
        trial = copy.deepcopy(selected)
        trial[kind].append(ref)
        if tokenizer.count_bundle(render(trial)) <= config['bundle']['max_tokens']:
            selected = trial
        else:
            drops.append({'evidence_id': ref, 'reason': 'bundle_token_budget'})
    content = render(selected)
    require(tokenizer.count_bundle(content) <= config['bundle']['max_tokens'], 'INSUFFICIENT_BUNDLE_BUDGET')
    ids = selected['logs'] + selected['metrics'] + selected['traces']
    spans, maps = _provenance(incident, selected['logs'], selected['metrics'], selected['traces'])
    bundle = {'incident_id': incident.incident_id, 'bundle_version': config['bundle']['version'],
              'window': incident.window, 'observation_text': content, 'evidence_ids': ids,
              'observations': {key: copy.deepcopy(incident.observation[key]) for key in
                               ('system_id', 'deployment_version', 'service_inventory', 'telemetry_is_synthetic')},
              'source_spans': spans, 'normalization_map': maps, 'dropped_evidence': drops,
              'missing_information': _missing(incident, selected['logs'], selected['metrics'], selected['traces']),
              'status': 'ok' if ids else 'insufficient_evidence',
              'budget': {'tokenizer_revision': tokenizer.revision, 'tokenizer_hash': config['tokenizer']['sha256'],
                         'before_tokens': tokenizer.count_bundle(render(by_kind)),
                         'after_tokens': tokenizer.count_bundle(content), 'max_tokens': config['bundle']['max_tokens'],
                         'prefix': '', 'special_tokens': 2,
                         'scope': 'candidate_e5_planning_count; actual_generator_tokenizer_required_at_plan07'}}
    bundle['bundle_hash'] = canonical_hash(bundle)
    return bundle


def generate_incident(incident, config, tokenizer, input_manifest_hash='fixture'):
    selection = select_evidence(incident, config)
    queries, ledgers = apply_query_budget(incident, selection, config, tokenizer)
    config_hash = canonical_hash(config)
    for row in queries:
        row.update(input_manifest_hash=input_manifest_hash, config_hash=config_hash,
                   tokenizer_hash=config['tokenizer']['sha256'],
                   normalization_version=config['normalization_version'],
                   redaction_version=incident.observation['redaction_version'],
                   transform_version=incident.observation['transform_version'])
    selection['retained_log_ids'] = queries[0]['log_evidence_ids']
    selection['budget_dropped_logs'] = ledgers[0]['joint_dropped_logs']
    # Build using the selector's original contract, before attaching final audit.
    bundle = build_observation_bundle(incident, select_evidence(incident, config), config, tokenizer)
    return queries, selection, ledgers, bundle
