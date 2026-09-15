"""Validate acquired artifacts, provenance and preparation boundaries; no quality scores are inferred."""
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = []


def check(name, passed, details=None):
    CHECKS.append({'check': name, 'passed': bool(passed), 'details': details})


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(rel):
    path = ROOT / rel
    if not path.exists():
        check('required_file:' + rel, False, 'missing')
        return []
    try:
        if path.suffix == '.tsv':
            with path.open(encoding='utf-8-sig', newline='') as file:
                return list(csv.DictReader(file, delimiter='\t'))
        with path.open(encoding='utf-8-sig') as file:
            return [json.loads(line) for line in file if line.strip()]
    except Exception as exc:
        check('parse:' + rel, False, str(exc))
        return []


def jsonfile(rel):
    path = ROOT / rel
    if not path.exists():
        check('required_file:' + rel, False, 'missing')
        return {}
    return json.loads(path.read_text(encoding='utf-8-sig'))


original_bad = []
for line in (ROOT / 'MANIFEST_SHA256.txt').read_text(encoding='utf-8-sig').splitlines():
    expected, rel = line.split(maxsplit=1)
    path = ROOT / rel.strip()
    if not path.exists() or sha(path) != expected:
        original_bad.append(rel)
check('original_package_hashes_unchanged', not original_bad, original_bad)

docs = rows('03_collection_plan/knowledge-corpus/documents.jsonl')
chunks = rows('03_collection_plan/knowledge-corpus/chunks.jsonl')
sources = rows('03_collection_plan/knowledge-corpus/source-manifest.jsonl')
docmap = {d['document_id']: d for d in docs}
check('knowledge_document_ids_unique', bool(docs) and len(docmap) == len(docs), len(docs))
check('knowledge_chunk_ids_unique', bool(chunks) and len({c['chunk_id'] for c in chunks}) == len(chunks), len(chunks))
bad = []
for doc in docs:
    raw = ROOT / doc['raw_path']
    if not raw.exists() or sha(raw) != doc['raw_sha256'] or hashlib.sha256(doc['text'].encode()).hexdigest() != doc['text_hash']:
        bad.append(doc['document_id'])
check('knowledge_raw_and_text_hashes', bool(docs) and not bad, bad)
bad = []
for chunk in chunks:
    doc = docmap.get(chunk['parent_document_id'])
    if not doc or doc['text'][chunk['start_offset']:chunk['end_offset']] != chunk['text'] or hashlib.sha256(chunk['text'].encode()).hexdigest() != chunk['text_hash']:
        bad.append(chunk['chunk_id'])
check('chunk_offsets_and_hashes', bool(chunks) and not bad, bad)
check('knowledge_license_snapshots', bool(sources) and all((ROOT / s['license_snapshot_path']).is_file() and sha(ROOT / s['license_snapshot_path']) == s['license_snapshot_hash'] for s in sources), len(sources))
check('knowledge_not_falsely_historical', bool(docs) and all(d['version_compatibility'] == 'unverified' and d['available_at'] for d in docs))
historical_docs = rows('03_collection_plan/knowledge-corpus-historical/documents.jsonl')
historical_chunks = rows('03_collection_plan/knowledge-corpus-historical/chunks.jsonl')
historical_sources = rows('03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl')
hdocmap = {d['document_id']: d for d in historical_docs}
check('historical_document_and_chunk_ids_unique', bool(historical_docs) and len(hdocmap) == len(historical_docs) and len({c['chunk_id'] for c in historical_chunks}) == len(historical_chunks))
check('historical_raw_and_text_hashes', bool(historical_docs) and all((ROOT / d['raw_path']).is_file() and sha(ROOT / d['raw_path']) == d['raw_sha256'] and hashlib.sha256(d['text'].encode()).hexdigest() == d['text_hash'] for d in historical_docs))
check('historical_chunk_offsets_and_hashes', bool(historical_chunks) and all(c['parent_document_id'] in hdocmap and hdocmap[c['parent_document_id']]['text'][c['start_offset']:c['end_offset']] == c['text'] and hashlib.sha256(c['text'].encode()).hexdigest() == c['text_hash'] for c in historical_chunks), len(historical_chunks))
check('historical_license_snapshots', bool(historical_sources) and all((ROOT / s['license_snapshot_path']).is_file() and sha(ROOT / s['license_snapshot_path']) == s['license_snapshot_hash'] for s in historical_sources))
for corpus in ['knowledge-corpus', 'knowledge-corpus-historical']:
    assets = rows(f'03_collection_plan/{corpus}/supporting-assets.jsonl')
    # The manifest retains asset type-specific paths; inspect raw_path/local_path.
    asset_fail = []
    for asset in assets:
        rel = asset.get('raw_path') or asset.get('local_path')
        expected = asset.get('sha256') or asset.get('raw_sha256')
        if not rel or not expected or not (ROOT / rel).is_file() or sha(ROOT / rel) != expected:
            asset_fail.append(rel or asset.get('source_url'))
    check(corpus + '_supporting_asset_hashes', bool(assets) and not asset_fail, {'count': len(assets), 'bad': asset_fail})

manifest = rows('02_datasets/acquired/labels/acquisition-manifest.jsonl')
bad = []
for row in manifest:
    path = ROOT / row['local_path']
    if not path.exists() or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
        bad.append(row['local_path'])
check('dataset_acquired_files_size_hash', bool(manifest) and not bad, {'file_count': len(manifest), 'bytes': sum(x['bytes'] for x in manifest), 'bad': bad})
check('dataset_manifest_90_unique_cases', len({r['incident_id'] for r in manifest}) == 90, len({r['incident_id'] for r in manifest}))
check('dataset_manifest_360_files', len(manifest) == 360, len(manifest))
observations = rows('02_datasets/processed/observations.jsonl')
gold = rows('02_datasets/processed/labels/ground_truth.jsonl')
obs_ids = [r['incident_id'] for r in observations]
gold_ids = [r['incident_id'] for r in gold]
check('observations_90_unique_ids', len(obs_ids) == len(set(obs_ids)) == 90, len(obs_ids))
def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))
check('historical_corpus_precedes_all_observation_windows', bool(observations) and bool(historical_docs) and all(instant(d['available_at']) <= instant(o['observation_start']) for d in historical_docs for o in observations), 'Time eligibility only; deployment compatibility still unverified.')
check('gold_join_complete_one_to_one', set(obs_ids) == set(gold_ids) and len(gold_ids) == len(set(gold_ids)) == 90)
forbidden = {'ground_truth', 'root_cause_service', 'fault_type', 'fault', 'inject_time', 'injection_time', 'source_case', 'source_path'}
leaks = []
def walk(value, path):
    if isinstance(value, dict):
        for key, sub in value.items():
            if key in forbidden:
                leaks.append(path + '.' + key)
            walk(sub, path + '.' + key)
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            walk(sub, path + f'[{i}]')
    elif isinstance(value, str) and re.search(r're2ob_\w+_(?:cpu|mem|memory|disk|delay|loss)_\d', value):
        leaks.append(path + ':source_case_name')
for obs in observations:
    walk(obs, obs['incident_id'])
check('observations_no_gold_fields_or_named_case_paths', bool(observations) and not leaks, leaks[:20])
split = rows('02_datasets/processed/split-map.tsv')
families = defaultdict(set)
for row in split:
    families[row['scenario_family_id']].add(row['split'])
check('split_ids_cover_observations_once', len(split) == len({r['incident_id'] for r in split}) == 90 and {r['incident_id'] for r in split} == set(obs_ids))
check('scenario_families_do_not_cross_splits', bool(families) and all(len(s) == 1 for s in families.values()), {'families': len(families), 'split_counts': dict(Counter(r['split'] for r in split))})
evidence_by_kind = {}
obsmap = {o['incident_id']: o for o in observations}
for filename, obs_key in [('logs-evidence.jsonl', 'log_span_ids'), ('metric-summaries.jsonl', 'metric_summary_ids'), ('trace-evidence.jsonl', 'trace_span_ids')]:
    erows = rows('02_datasets/processed/' + filename)
    emap = {r['evidence_id']: r for r in erows}
    check('evidence_references:' + obs_key, bool(erows) and len(emap) == len(erows) and all(eid in emap and emap[eid]['incident_id'] == o['incident_id'] for o in observations for eid in o[obs_key]), len(erows))
    leaks = []
    time_bad = []
    for erow in erows:
        walk(erow, erow['evidence_id'])
        obs = obsmap.get(erow['incident_id'])
        if not obs:
            time_bad.append(erow['evidence_id'])
            continue
        start, end = instant(obs['observation_start']), instant(obs['observation_end'])
        if 'timestamp' in erow:
            if not start <= instant(erow['timestamp']) < end:
                time_bad.append(erow['evidence_id'])
        elif 'observation_start' in erow and 'observation_end' in erow:
            if not start <= instant(erow['observation_start']) <= instant(erow['observation_end']) <= end:
                time_bad.append(erow['evidence_id'])
    check('evidence_no_gold_fields_or_named_paths:' + filename, bool(erows) and not leaks, leaks[:20])
    check('evidence_within_observation_window:' + filename, bool(erows) and not time_bad, time_bad[:20])

annotation = jsonfile('03_collection_plan/annotation-kit/status.json')
check('annotation_pending_not_gold', annotation.get('human_judgments_completed') == 0 and annotation.get('gold_qrels_available') is False and annotation.get('observation_records_found') == 90, annotation)

original = rows('01_papers/catalog.jsonl')
enriched = rows('01_papers/enriched/catalog-enriched.jsonl')
check('bibliography_preserves_all_1009_original_ids', len(enriched) == 1009 and len({r['paper_id'] for r in enriched}) == 1009 and {r['paper_id'] for r in enriched} == {r['paper_id'] for r in original}, len(enriched))
notes = list((ROOT / '01_papers/reading-notes').glob('P*.md'))
priority_ids = set(re.findall(r'P\d{4}', (ROOT / '01_papers/priority_reading.md').read_text(encoding='utf-8')))
note_ids = {p.stem.split('-')[0] for p in notes}
check('priority_paper_notes_present', len(priority_ids) == 50 and priority_ids.issubset(note_ids), {'expected': len(priority_ids), 'present': len(note_ids & priority_ids), 'missing': sorted(priority_ids - note_ids)})
config = jsonfile('05_research/experiment-proposal.json')
check('experimental_results_not_fabricated', config.get('evaluation', {}).get('test_results', 'missing') is None and config.get('evaluation', {}).get('qrels_status') == 'human_annotation_required')
experiment_rows = rows('05_research/experiment-results-template.tsv')
metrics = ['recall_at_5', 'mrr_at_5', 'ndcg_at_5', 'rca_hit_at_1', 'citation_precision', 'unsupported_claim_rate']
check('experiment_template_has_no_claimed_scores', len(experiment_rows) == 8 and all(r['status'] == 'NOT_RUN' and all(not r[k] for k in metrics) for r in experiment_rows))

report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'passed': all(c['passed'] for c in CHECKS), 'checks': CHECKS, 'boundaries': ['Artifact integrity is not evidence-relevance or scientific validity.', 'Human qrels/adjudication and test experiments remain future work.', 'Full raw scan cannot guarantee absence of all personal data or secrets.', 'Current knowledge snapshot is not historically verified.']}
target = ROOT / '04_audit/research-pack-validation.json'
target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'checks': len(CHECKS), 'failed_checks': [c['check'] for c in CHECKS if not c['passed']], 'report': str(target)}, ensure_ascii=False))
sys.exit(0 if report['passed'] else 1)
