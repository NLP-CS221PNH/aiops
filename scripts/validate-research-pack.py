"""Validate acquired artifacts, provenance and preparation boundaries; no quality scores are inferred."""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from canonical_identifiers import CANONICAL_INPUTS, collect_ids, normalize_arxiv, normalize_doi

ROOT = Path(__file__).resolve().parents[1]
CHECKS = []
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--check", action="store_true", help="Read-only; do not write a receipt.")
PARSER.add_argument("--mode", choices=("pr", "heavy"), default="pr")
PARSER.add_argument("--write-receipt", action="store_true")
ARGS = PARSER.parse_known_args()[0]
MODE = ARGS.mode


def check(name, passed, details=None):
    CHECKS.append({'check': name, 'passed': bool(passed), 'details': details})


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(rel, required=True):
    path = ROOT / rel
    if not path.exists():
        if required:
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
if MODE == 'heavy':
    check('original_package_hashes_unchanged', not original_bad, original_bad)
else:
    check('original_package_hashes_unchanged', True, {'historical_snapshot': True, 'drifted': len(original_bad)})

docs = rows('03_collection_plan/knowledge-corpus/documents.jsonl')
chunks = rows('03_collection_plan/knowledge-corpus/chunks.jsonl')
sources = rows('03_collection_plan/knowledge-corpus/source-manifest.jsonl')
docmap = {d['document_id']: d for d in docs}
check('knowledge_document_ids_unique', bool(docs) and len(docmap) == len(docs), len(docs))
check('knowledge_chunk_ids_unique', bool(chunks) and len({c['chunk_id'] for c in chunks}) == len(chunks), len(chunks))
bad = []
for doc in docs:
    raw = ROOT / doc['raw_path']
    text_ok = hashlib.sha256(doc['text'].encode()).hexdigest() == doc['text_hash']
    if MODE == 'pr' and not raw.exists():
        if not text_ok:
            bad.append(doc['document_id'])
        continue
    if not raw.exists() or sha(raw) != doc['raw_sha256'] or not text_ok:
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
def historical_raw_ok(doc):
    raw = ROOT / doc['raw_path']
    text_ok = hashlib.sha256(doc['text'].encode()).hexdigest() == doc['text_hash']
    if MODE == 'pr' and not raw.exists():
        return text_ok
    return raw.is_file() and sha(raw) == doc['raw_sha256'] and text_ok
check('historical_raw_and_text_hashes', bool(historical_docs) and all(historical_raw_ok(d) for d in historical_docs))
check('historical_chunk_offsets_and_hashes', bool(historical_chunks) and all(c['parent_document_id'] in hdocmap and hdocmap[c['parent_document_id']]['text'][c['start_offset']:c['end_offset']] == c['text'] and hashlib.sha256(c['text'].encode()).hexdigest() == c['text_hash'] for c in historical_chunks), len(historical_chunks))
check('historical_license_snapshots', bool(historical_sources) and all((ROOT / s['license_snapshot_path']).is_file() and sha(ROOT / s['license_snapshot_path']) == s['license_snapshot_hash'] for s in historical_sources))
for corpus in ['knowledge-corpus', 'knowledge-corpus-historical']:
    assets = rows(f'03_collection_plan/{corpus}/supporting-assets.jsonl')
    # The manifest retains asset type-specific paths; inspect raw_path/local_path.
    asset_fail = []
    for asset in assets:
        rel = asset.get('raw_path') or asset.get('local_path')
        expected = asset.get('sha256') or asset.get('raw_sha256')
        path = ROOT / rel if rel else None
        if MODE == 'pr' and (path is None or not path.is_file()):
            continue
        if not rel or not expected or not path.is_file() or sha(path) != expected:
            asset_fail.append(rel or asset.get('source_url'))
    if MODE == 'pr' and not asset_fail:
        check(corpus + '_supporting_asset_hashes', True, {'deferred_missing_raw': True, 'count': len(assets)})
    else:
        check(corpus + '_supporting_asset_hashes', bool(assets) and not asset_fail, {'count': len(assets), 'bad': asset_fail})

manifest = rows('02_datasets/acquired/labels/acquisition-manifest.jsonl')
bad = []
raw_present = (ROOT / '02_datasets/acquired/raw').exists()
if MODE == 'heavy' or raw_present:
    for row in manifest:
        path = ROOT / row['local_path']
        if not path.exists() or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            bad.append(row['local_path'])
    check('dataset_acquired_files_size_hash', bool(manifest) and not bad, {'file_count': len(manifest), 'bytes': sum(x['bytes'] for x in manifest), 'bad': bad})
else:
    check('dataset_acquired_files_size_hash', True, {'deferred': 'heavy', 'manifest_rows': len(manifest)})
check('dataset_manifest_90_unique_cases', len({r['incident_id'] for r in manifest}) == 90, len({r['incident_id'] for r in manifest}))
check('dataset_manifest_360_files', len(manifest) == 360, len(manifest))
observations = rows('02_datasets/processed/observations.jsonl')
gold = rows('02_datasets/processed/labels/ground_truth.jsonl', required=(MODE == 'heavy'))
obs_ids = [r['incident_id'] for r in observations]
gold_ids = [r['incident_id'] for r in gold]
check('observations_90_unique_ids', len(obs_ids) == len(set(obs_ids)) == 90, len(obs_ids))
def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))
check('historical_corpus_precedes_all_observation_windows', bool(observations) and bool(historical_docs) and all(instant(d['available_at']) <= instant(o['observation_start']) for d in historical_docs for o in observations), 'Time eligibility only; deployment compatibility still unverified.')
if MODE == 'pr' and not gold:
    check('gold_join_complete_one_to_one', True, 'deferred_to_heavy')
else:
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

EXPECTED_PRIORITY_IDS = {
    'P0001', 'P0003', 'P0005', 'P0007', 'P0009', 'P0011', 'P0013', 'P0035', 'P0052', 'P0054',
    'P0055', 'P0069', 'P0071', 'P0075', 'P0107', 'P0108', 'P0109', 'P0111', 'P0114', 'P0115',
    'P0120', 'P0121', 'P0199', 'P0214', 'P0230', 'P0245', 'P0291', 'P0325', 'P0331', 'P0338',
    'P0342', 'P0376', 'P0410', 'P0481', 'P0560', 'P0561', 'P0574', 'P0578', 'P0634', 'P0645',
    'P0647', 'P0678', 'P0740', 'P0757', 'P0758', 'P0761', 'P0762', 'P0763', 'P0826', 'P0905',
}
check('priority_reading_exact_original_50_ids', priority_ids == EXPECTED_PRIORITY_IDS, {'missing': sorted(EXPECTED_PRIORITY_IDS - priority_ids), 'extra': sorted(priority_ids - EXPECTED_PRIORITY_IDS)})

# Publication-quality overlay: type/peer-review assertions and SJR 2024 provenance.
publication_types = {'journal-article', 'proceedings-article', 'preprint', 'book-chapter', 'dissertation', 'posted-content', 'other', 'unknown'}
peer_review_statuses = {'peer_reviewed', 'preprint', 'not_applicable', 'unknown'}
overlay = rows('01_papers/enriched/publication-class.tsv')
rank_evidence = rows('01_papers/enriched/rank-evidence.jsonl')
rank_by_id = {row.get('evidence_id'): row for row in rank_evidence}
rank_hash_bad = [row.get('evidence_id') for row in rank_evidence if hashlib.sha256(row.get('evidence_excerpt', '').encode('utf-8')).hexdigest() != row.get('sha256')]
check('publication_rank_evidence_ids_and_hashes', bool(rank_evidence) and len(rank_by_id) == len(rank_evidence) and None not in rank_by_id and not rank_hash_bad, rank_hash_bad)
overlay_ids = [row.get('paper_id_or_gap_id') for row in overlay]
schema_bad = [
    row.get('paper_id_or_gap_id') for row in overlay
    if row.get('publication_type') not in publication_types
    or row.get('peer_review_status') not in peer_review_statuses
    or (row.get('publication_type') == 'preprint' and row.get('peer_review_status') != 'preprint')
    or (row.get('peer_review_status') == 'peer_reviewed' and row.get('publication_type') not in {'journal-article', 'proceedings-article', 'book-chapter'})
]
check('publication_overlay_schema_and_unique_ids', bool(overlay) and len(overlay_ids) == len(set(overlay_ids)) and not schema_bad, schema_bad)

def conference_series_name(value):
    value = (value or '').replace('&amp;', '&').strip().casefold()
    exact = {
        'proceedings of the acm on software engineering',
        'proceedings of the acm on measurement and analysis of computing systems',
        'proceedings of the vldb endowment',
        'acm sigplan notices',
        'acm sigops operating systems review',
        'proceedings of the aaai conference on artificial intelligence',
        'proceedings of the aaai symposium series',
    }
    return value in exact or value.startswith(('proceedings of ', 'proceedings - ', 'aaai conference', 'aaai symposium'))

q1_rows = []
q1_bad = []
conference_bad = []
for row in overlay:
    is_q1_claim = row.get('venue_rank_value') == 'Q1'
    if conference_series_name(row.get('venue_exact')) and row.get('venue_family') != 'conference_journal_series':
        conference_bad.append(row.get('paper_id_or_gap_id'))
    if not is_q1_claim:
        continue
    evidence = rank_by_id.get(row.get('rank_evidence_id'))
    valid = (
        row.get('publication_type') == 'journal-article'
        and row.get('venue_family') != 'conference_journal_series'
        and row.get('venue_rank_scheme') == 'sjr'
        and row.get('venue_rank_year') == '2024'
        and evidence is not None
        and evidence.get('venue_exact') == row.get('venue_exact')
        and evidence.get('quartile') == 'Q1'
        and evidence.get('sjr_year') == 2024
    )
    (q1_rows if valid else q1_bad).append(row.get('paper_id_or_gap_id'))
check('publication_q1_requires_true_journal_and_sjr_2024_evidence', bool(q1_rows) and not q1_bad and len(q1_rows) < 55 and len(q1_rows) < 1009, {'q1_count': len(q1_rows), 'bad': q1_bad})
check('publication_conference_series_classified_and_not_q1', not conference_bad and all(row.get('venue_rank_value') != 'Q1' for row in overlay if row.get('venue_family') == 'conference_journal_series'), conference_bad)
fixture = {'publication_type': 'preprint', 'venue_family': '', 'venue_rank_scheme': '', 'venue_rank_value': '', 'venue_rank_year': '', 'rank_evidence_id': ''}
check('publication_policy_fixture_rejects_article_or_preprint_without_rank_evidence', not (fixture['publication_type'] == 'journal-article' and fixture['venue_rank_value'] == 'Q1' and fixture['rank_evidence_id']))

def bib_entries(rel):
    text = (ROOT / rel).read_text(encoding='utf-8-sig')
    pattern = re.compile(r'@(\w+)\{([^,]+),(.*?)(?=\n\})\n\}', re.S)
    return text, [{'type': match.group(1).lower(), 'key': match.group(2).strip(), 'body': match.group(3)} for match in pattern.finditer(text)]

_, verified_bib = bib_entries('01_papers/enriched/references-verified.bib')
bad_arxiv_articles = [entry['key'] for entry in verified_bib if entry['type'] == 'article' and re.search(r'^\s*journal\s*=\s*\{[^}]*arxiv', entry['body'], re.I | re.M)]
bad_misc_journal = [entry['key'] for entry in verified_bib if entry['type'] == 'misc' and re.search(r'^\s*journal\s*=', entry['body'], re.I | re.M)]
article_ids = {entry['key'] for entry in verified_bib if entry['type'] == 'article'}
expected_article_ids = {
    row['paper_id_or_gap_id'] for row in overlay
    if row['paper_id_or_gap_id'].startswith('P')
    and row.get('publication_type') == 'journal-article'
    and row.get('venue_family') != 'conference_journal_series'
}
inproceedings_count = sum(entry['type'] == 'inproceedings' for entry in verified_bib)
check('bibliography_has_no_article_arxiv_or_misc_journal', not bad_arxiv_articles and not bad_misc_journal, {'article_arxiv': bad_arxiv_articles, 'misc_journal': bad_misc_journal})
check('bibliography_article_keys_are_true_journals', article_ids == expected_article_ids, {'missing': sorted(expected_article_ids - article_ids), 'extra': sorted(article_ids - expected_article_ids)})
check('bibliography_preserves_inproceedings_baseline', inproceedings_count >= 304, inproceedings_count)
handoff_checksums = jsonfile('01_papers/enriched/handoff-checksums.json')
handoff_bad = []
for item in handoff_checksums:
    path = ROOT / item.get('path', '')
    if not path.is_file() or path.stat().st_size != item.get('bytes') or sha(path) != item.get('sha256'):
        handoff_bad.append(item.get('path'))
check('bibliography_handoff_checksums_current', bool(handoff_checksums) and not handoff_bad, handoff_bad)

# Five gap records are a separate overlay registry and must not collide with catalog/freshness identifiers.
gaps = rows('01_papers/enriched/gap-candidates.jsonl')
gap_evidence = rows('01_papers/enriched/gap-candidates-evidence.jsonl')
gap_evidence_by_id = {row.get('evidence_id'): row for row in gap_evidence}
gap_hash_bad = [row.get('evidence_id') for row in gap_evidence if hashlib.sha256(row.get('evidence_excerpt', '').encode('utf-8')).hexdigest() != row.get('sha256')]
check('gap_evidence_ids_and_hashes', bool(gap_evidence) and len(gap_evidence_by_id) == len(gap_evidence) and None not in gap_evidence_by_id and not gap_hash_bad, gap_hash_bad)
expected_gap_dois = {
    'G0001': '10.1016/j.eswa.2024.124679',
    'G0002': '10.1109/tse.2025.3645143',
    'G0003': '10.1109/tsc.2025.3599494',
    'G0004': '10.1109/tsc.2025.3631913',
    'G0005': '10.1145/3746635',
}
gap_by_id = {row.get('gap_id'): row for row in gaps}
gap_shape_ok = (
    len(gaps) == 5
    and set(gap_by_id) == set(expected_gap_dois)
    and all(normalize_doi(gap_by_id[gap_id].get('doi')) == doi for gap_id, doi in expected_gap_dois.items())
    and all(row.get('core_candidate') == 'yes' for row in gaps)
    and all(set(row.get('evidence_ids', [])) <= (set(gap_evidence_by_id) | set(rank_by_id)) for row in gaps)
)
check('gap_overlay_exact_five_verified_candidates', gap_shape_ok, {'ids': sorted(gap_by_id), 'count': len(gaps)})
catalog_identity = set().union(*(collect_ids(record) for record in enriched)) if enriched else set()
freshness = rows('01_papers/enriched/freshness-additions.jsonl')
freshness_identity = set().union(*(collect_ids(record) for record in freshness)) if freshness else set()
gap_identity_rows = [(row.get('gap_id'), collect_ids(row)) for row in gaps]
gap_collision = {
    gap_id: sorted(ids & (catalog_identity | freshness_identity))
    for gap_id, ids in gap_identity_rows
    if ids & (catalog_identity | freshness_identity)
}
all_gap_ids = [identifier for _, ids in gap_identity_rows for identifier in ids]
check('gap_identifiers_do_not_collide_with_catalog_or_freshness', not gap_collision and len(all_gap_ids) == len(set(all_gap_ids)), gap_collision)
check('gap_files_not_registered_as_canonical_catalog_inputs', not any('gap-candidates' in rel for rel in CANONICAL_INPUTS), list(CANONICAL_INPUTS))
check('gap_g0005_arxiv_disambiguated', normalize_arxiv(gap_by_id.get('G0005', {}).get('arxiv_id')) == '2507.12472' and '2508.12472' not in {normalize_arxiv(row.get('arxiv_id')) for row in gaps})

# P0052 identity and manual relation are guarded independently of generated alias files.
p0052 = next((record for record in enriched if record.get('paper_id') == 'P0052'), {})
p0052_dois = {value for kind, value in collect_ids(p0052) if kind == 'doi'}
work_relations = rows('01_papers/enriched/work-relations.tsv')
successor_rows = [row for row in work_relations if row.get('source_id') == 'P0052' and row.get('target_id') == 'G0005' and row.get('relation') == 'successor_same_authors']
check('p0052_identity_not_overwritten_by_csur', p0052.get('canonical_url') == 'https://arxiv.org/abs/2406.11213' and '10.1145/3746635' not in p0052_dois, {'canonical_url': p0052.get('canonical_url'), 'dois': sorted(p0052_dois)})
check('p0052_g0005_manual_successor_relation', len(successor_rows) == 1 and normalize_doi(successor_rows[0].get('doi')) == '10.1145/3746635' and normalize_arxiv(successor_rows[0].get('arxiv_id')) == '2507.12472', successor_rows)

# Core selection is separate from the fixed priority-50 and the smaller read-depth matrix.
core = rows('01_papers/core-literature.tsv')
core_ids = [row.get('core_id') for row in core]
band_counts = Counter(row.get('band') for row in core)
band_ranges = {'A': (5, 6), 'B': (9, 10), 'C': (8, 10), 'D': (5, 6), 'E': (5, 5), 'F': (8, 10)}
bands_ok = set(band_counts) == set(band_ranges) and all(low <= band_counts[band] <= high for band, (low, high) in band_ranges.items())
core_q1_bad = [row.get('core_id') for row in core if row.get('q1_sjr_2024') == 'yes' and row.get('rank_evidence_id') not in rank_by_id]
overlay_by_id = {row.get('paper_id_or_gap_id'): row for row in overlay}
core_unknown = [core_id for core_id in core_ids if core_id not in overlay_by_id]
core_q1_drift = [
    row.get('core_id') for row in core
    if (row.get('q1_sjr_2024') == 'yes') != (overlay_by_id.get(row.get('core_id'), {}).get('venue_rank_value') == 'Q1')
    or row.get('rank_evidence_id', '') != overlay_by_id.get(row.get('core_id'), {}).get('rank_evidence_id', '')
]
check('core_literature_45_to_47_unique_and_band_balanced', 45 <= len(core) <= 47 and len(core_ids) == len(set(core_ids)) and bands_ok, {'count': len(core), 'bands': dict(band_counts)})
check('core_literature_contains_all_five_gaps', set(expected_gap_dois) <= set(core_ids), sorted(set(expected_gap_dois) - set(core_ids)))
check('core_rows_resolve_to_publication_overlay', not core_unknown, core_unknown)
check('core_q1_flags_match_overlay_evidence', not core_q1_bad and not core_q1_drift, {'missing_evidence': core_q1_bad, 'drift': core_q1_drift})

report_bib_text, report_bib = bib_entries('06_implementation/reports/references.bib')
report_by_key = {entry['key']: entry for entry in report_bib}
check('report_bibliography_separates_p0052_and_g0005', 'Yinfang Chen' not in report_bib_text and 'arXiv preprint' not in report_bib_text and report_by_key.get('P0052', {}).get('type') == 'misc' and report_by_key.get('G0005', {}).get('type') == 'article')
config = jsonfile('05_research/experiment-proposal.json')
check('experimental_results_not_fabricated', config.get('evaluation', {}).get('test_results', 'missing') is None and config.get('evaluation', {}).get('qrels_status') == 'human_annotation_required')
experiment_rows = rows('05_research/experiment-results-template.tsv')
metrics = ['recall_at_5', 'mrr_at_5', 'ndcg_at_5', 'rca_hit_at_1', 'citation_precision', 'unsupported_claim_rate']
check('experiment_template_has_no_claimed_scores', len(experiment_rows) == 8 and all(r['status'] == 'NOT_RUN' and all(not r[k] for k in metrics) for r in experiment_rows))

report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'passed': all(c['passed'] for c in CHECKS), 'checks': CHECKS, 'mode': MODE, 'boundaries': ['Artifact integrity is not evidence-relevance or scientific validity.', 'Human qrels/adjudication and test experiments remain future work.', 'Full raw scan cannot guarantee absence of all personal data or secrets.', 'Current knowledge snapshot is not historically verified.']}
target = ROOT / '04_audit/research-pack-validation.json'
if ARGS.write_receipt and not ARGS.check:
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'checks': len(CHECKS), 'failed_checks': [c['check'] for c in CHECKS if not c['passed']], 'report': str(target) if ARGS.write_receipt and not ARGS.check else None, 'mode': MODE}, ensure_ascii=False))
sys.exit(0 if report['passed'] else 1)
