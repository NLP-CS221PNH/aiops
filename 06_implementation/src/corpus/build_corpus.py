"""Build an offline historical corpus candidate without releasing it for indexing."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from .chunking import chunk_document
from .common import (DEFAULT_CONFIG, DEFAULT_OUTPUT, IMPL, ROOT, canonical_hash, load_config,
                     read_json, read_jsonl, require, safe_path, sha256, write_json, write_jsonl)
from .normalize import normalize_document, raw_units
from .tokenizer import CorpusTokenizer

ARTIFACTS = {'documents.jsonl', 'chunks.jsonl', 'citation-registry.jsonl', 'chunk-lineage.jsonl',
             'applicability.tsv', 'source-registry.jsonl', 'token-audit.json', 'corpus-manifest.json'}


def build_digest_payload(config, source_checksums, documents, chunks, citations, lineage, applicability):
    def unstamped(rows):
        return [{key: value for key, value in row.items() if key != 'corpus_hash'} for row in rows]
    return {'config': config, 'source_checksums': source_checksums,
            'documents': unstamped(documents), 'chunks': unstamped(chunks),
            'citations': unstamped(citations), 'lineage': unstamped(lineage),
            'applicability': applicability}


def _output_path(output):
    requested = Path(output).absolute()
    for parent in (requested, *requested.parents):
        require(not parent.is_symlink() and not (hasattr(parent, 'is_junction') and parent.is_junction()),
                f'OUTPUT_SYMLINK: {parent}')
    output = requested.resolve()
    knowledge = (IMPL / 'data/knowledge').resolve()
    allowed = [IMPL / '.test-work', ROOT / '.test-work']
    require(output == knowledge or (output.parent == knowledge.parent and output.name.startswith('knowledge-'))
            or any(output != base.resolve() and output.is_relative_to(base.resolve()) for base in allowed),
            'OUTPUT_OUTSIDE_DERIVATIVE_ROOT')
    preparation = (IMPL / 'data/knowledge-preparation').resolve()
    require(output != preparation and not output.is_relative_to(preparation), 'OUTPUT_IS_PREPARATION_INPUT')
    if output.exists():
        require(output.is_dir(), 'OUTPUT_NOT_DIRECTORY')
        require({path.name for path in output.iterdir()} <= ARTIFACTS, 'OUTPUT_CONTAINS_FOREIGN_FILES')
        require(all(path.is_file() and not path.is_symlink() for path in output.iterdir()), 'OUTPUT_UNSAFE_CONTENT')
        if any(output.iterdir()):
            require((output / 'corpus-manifest.json').is_file(), 'OUTPUT_UNOWNED_ARTIFACTS')
            require(read_json(output / 'corpus-manifest.json').get('status') == 'candidate', 'OUTPUT_NOT_CANDIDATE')
    return output


def _read_applicability(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def _load_audit():
    path = IMPL / 'scripts/audit_corpus_sources.py'
    require(path.is_file(), 'SOURCE_AUDIT_NOT_AVAILABLE')
    spec = importlib.util.spec_from_file_location('corpus_source_audit', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_sources(ROOT)


def _source_checksums(config):
    source_root = safe_path(ROOT, config['source_root'])
    checksums = {}
    # All immutable snapshot bytes, including receipts and license evidence, are bound.
    for path in sorted(source_root.rglob('*')):
        if path.is_file():
            require(not path.is_symlink(), 'SOURCE_SYMLINK')
            checksums[path.relative_to(ROOT).as_posix()] = sha256(path)
    for filename in ('source-registry.jsonl', 'applicability.tsv'):
        path = safe_path(IMPL, config['preparation_root']) / filename
        checksums[path.relative_to(ROOT).as_posix()] = sha256(path)
    paths = sorted((IMPL / 'src/corpus').glob('*.py')) + [IMPL / 'scripts/audit_corpus_sources.py']
    paths += [safe_path(IMPL, asset['path']) for asset in config['tokenizer'].get('assets', [])]
    for path in paths:
        checksums[path.relative_to(ROOT).as_posix()] = sha256(path)
    return checksums


def _lineage(old_chunks, sources, documents, chunks, config):
    source_by_id = {source['document_id']: source for source in sources}
    documents_by_id = {document['document_id']: document for document in documents}
    chunks_by_id = {}
    for chunk in chunks:
        chunks_by_id.setdefault(chunk['document_id'], []).append(chunk)
    units_by_id = {}
    for source in sources:
        raw = safe_path(ROOT, source['raw_path']).read_bytes().decode('utf-8')
        units_by_id[source['document_id']] = raw_units(raw)
    rows = []
    for old in old_chunks:
        document_id = old['parent_document_id']
        source = source_by_id[document_id]
        original_units = units_by_id[document_id]
        old_start, old_end = old['start_offset'], old['end_offset']
        require(source['text'][old_start:old_end] == old['text'], 'OLD_CHUNK_OFFSETS')
        raw_start = original_units[old_start][1]
        raw_end = original_units[old_end - 1][2]
        matches = []
        for chunk in chunks_by_id.get(document_id, []):
            overlaps = []
            for span in chunk['source_spans']:
                if span['raw_path'] == source['raw_path']:
                    lo, hi = max(raw_start, span['raw_start']), min(raw_end, span['raw_end'])
                    if lo < hi:
                        if span['transform'] == 'identity':
                            norm_start = span['normalized_start'] + lo - span['raw_start']
                            norm_end = norm_start + hi - lo
                        else:
                            norm_start, norm_end = span['normalized_start'], span['normalized_end']
                        overlaps.append({'normalized_start': norm_start, 'normalized_end': norm_end,
                                         'raw_start': lo, 'raw_end': hi, 'mapping': 'direct'})
                origin = span.get('include_origin')
                if origin and origin['raw_path'] == source['raw_path']:
                    lo, hi = max(raw_start, origin['raw_start']), min(raw_end, origin['raw_end'])
                    if lo < hi:
                        overlaps.append({'normalized_start': span['normalized_start'],
                                         'normalized_end': span['normalized_end'],
                                         'raw_start': lo, 'raw_end': hi, 'mapping': 'local_include_expansion',
                                         'asset_raw_path': span['raw_path']})
            if overlaps:
                matches.append({'chunk_id': chunk['chunk_id'], 'spans': overlaps})
        document = documents_by_id[document_id]
        if matches:
            relation = 'one_to_many' if len(matches) > 1 else 'overlap'
            reason = ''
        elif document['applicability']['decision'] == 'excluded':
            relation, reason = 'excluded', document['applicability']['reason']
        else:
            relation = 'removed'
            removed = [span['reason'] for span in document['removed_spans']
                       if span['raw_path'] == source['raw_path']
                       and max(raw_start, span['raw_start']) < min(raw_end, span['raw_end'])]
            reason = ';'.join(sorted(set(removed))) or 'whitespace_or_html_marker_only'
        rows.append({'old_chunk_id': old['chunk_id'], 'parent_document_id': document_id,
                     'document_id': document_id, 'old_start_offset': old_start, 'old_end_offset': old_end,
                     'old_text_hash': old['text_hash'], 'old_raw_start': raw_start, 'old_raw_end': raw_end,
                     'new_chunk_ids': [match['chunk_id'] for match in matches], 'new_spans': matches,
                     'relation': relation, 'reason': reason, 'normalization_version': config['normalization_version'],
                     'chunking_version': config['chunking_version'], 'qrel_transfer': 'prohibited_requires_rejudgment'})
    return rows


def _publish(stage, output):
    require(stage.resolve().parent == output.resolve().parent and stage.name.startswith(f'.{output.name}-build-'),
            'STAGING_PATH_BOUNDARY')
    backup = None
    if output.exists():
        backup = Path(tempfile.mkdtemp(prefix=f'.{output.name}-backup-', dir=output.parent))
        backup.rmdir()
        os.replace(output, backup)
    try:
        os.replace(stage, output)
    except BaseException:
        if backup is not None:
            os.replace(backup, output)
        raise
    if backup is not None:
        require(backup.resolve().parent == output.resolve().parent
                and backup.name.startswith(f'.{output.name}-backup-'), 'BACKUP_PATH_BOUNDARY')
        shutil.rmtree(backup)


def build_corpus(config_path=DEFAULT_CONFIG, output=DEFAULT_OUTPUT, *, replace_candidate=False):
    config_path = Path(config_path).resolve()
    config = load_config(config_path)
    output = _output_path(output)
    source_root = safe_path(ROOT, config['source_root'])
    for name, expected in config['source_hashes'].items():
        require(sha256(safe_path(source_root, name)) == expected, f'SOURCE_INPUT_HASH: {name}')
    audit, source_registry, proposed_applicability = _load_audit()
    require(audit.get('status') == 'pass' and not audit.get('findings'), 'SOURCE_AUDIT_FAILED')
    preparation = safe_path(IMPL, config['preparation_root'])
    require(read_jsonl(preparation / 'source-registry.jsonl') == source_registry, 'STALE_SOURCE_REGISTRY')
    applicability_path = safe_path(IMPL, config['applicability_path'])
    applicability = _read_applicability(applicability_path)
    # The preparation contract remains authoritative; no invented human signatures.
    serialized_proposals = [
        {key: json.dumps(value, ensure_ascii=False, separators=(',', ':')) if isinstance(value, (list, dict))
         else str(value) if value is not None else '' for key, value in row.items()}
        for row in proposed_applicability]
    require(applicability == serialized_proposals, 'STALE_APPLICABILITY_PROPOSALS')
    by_applicability = {row['document_id']: row for row in applicability}
    typed_applicability = {row['document_id']: row for row in proposed_applicability}
    require(len(by_applicability) == len(applicability), 'DUPLICATE_APPLICABILITY_DOCUMENT')
    sources = read_jsonl(source_root / 'documents.jsonl')
    assets = read_jsonl(source_root / 'supporting-assets.jsonl')
    manifests = {row['source_id']: row for row in read_jsonl(source_root / 'source-manifest.jsonl')}
    require(Counter(source['source_id'] for source in sources) == config['expected_source_counts'], 'SOURCE_COUNTS')
    require(set(by_applicability) == {source['document_id'] for source in sources}, 'APPLICABILITY_POPULATION')
    tokenizer = CorpusTokenizer(config)
    documents, chunks, omitted = [], [], []
    for source in sources:
        require(source.get('derived_from_incident_ids') == [] and source.get('is_synthetic') is False,
                'SOURCE_IS_INCIDENT_DERIVED_OR_SYNTHETIC')
        applicability_row = typed_applicability[source['document_id']]
        require(applicability_row['decision'] in ('allowed', 'excluded', 'unknown') and applicability_row['reason'],
                'APPLICABILITY_DECISION')
        document = {key: value for key, value in source.items() if key != 'text'}
        document.update(normalize_document(source, assets, root=ROOT))
        document.update(original_document_id=source['document_id'], original_text_hash=source['text_hash'],
                        source_revision=source['version_scope'], source_manifest=manifests[source['source_id']],
                        normalization_version=config['normalization_version'], applicability=applicability_row,
                        candidate_eligible=applicability_row['decision'] != 'excluded', index_eligible=False,
                        review_state='pending',
                        change_notice='Versioned derivative: metadata/frontmatter/initial license comment normalization; '
                                      'verified local Hugo assets may be expanded. Raw source, license and attribution retained.')
        documents.append(document)
        if document['candidate_eligible']:
            new_chunks, exclusions = chunk_document(document, tokenizer, config, root=ROOT)
            chunks.extend(new_chunks)
            omitted.extend(exclusions)
    require(len({chunk['chunk_id'] for chunk in chunks}) == len(chunks), 'CHUNK_ID_COLLISION')
    citations = [{key: chunk[key] for key in
                  ('chunk_id', 'document_id', 'source_url', 'source_revision', 'source_id', 'source_spans',
                   'text_hash', 'content_hash', 'license', 'attribution', 'applicability')}
                 | {'normalized_span': {'start': chunk['start_offset'], 'end': chunk['end_offset']},
                    'offset_unit': chunk['offset_unit'], 'review_state': 'pending'} for chunk in chunks]
    lineage = _lineage(read_jsonl(source_root / 'chunks.jsonl'), sources, documents, chunks, config)
    checksums = _source_checksums(config)
    corpus_hash = canonical_hash(build_digest_payload(config, checksums, documents, chunks, citations, lineage, applicability))
    for rows in (documents, chunks, citations, lineage):
        for row in rows:
            row['corpus_hash'] = corpus_hash
    previous_path = output / 'corpus-manifest.json'
    if previous_path.is_file():
        previous = read_json(previous_path)
        require(previous['corpus_hash'] == corpus_hash or replace_candidate
                or previous.get('versions', {}).get('corpus_version') != config['corpus_version'],
                'OUTPUT_VERSION_CONFLICT: use a new version/output or explicitly replace the local candidate')
    counts = {'documents': len(documents), 'candidate_documents': sum(doc['candidate_eligible'] for doc in documents),
              'candidate_chunks': len(chunks), 'indexed_documents': 0, 'indexed_chunks': 0,
              'excluded_documents': sum(row['decision'] == 'excluded' for row in applicability),
              'unknown_documents': sum(row['decision'] == 'unknown' for row in applicability),
              'allowed_documents': sum(row['decision'] == 'allowed' for row in applicability),
              'source_chunks': len(lineage), 'supporting_assets': len(assets)}
    token_audit = {
        'corpus_hash': corpus_hash, 'tokenizer_revision': tokenizer.revision, 'tokenizer_sha256': config['tokenizer']['sha256'],
        'library_version': config['tokenizer']['library_version'], 'max_length': tokenizer.max_length,
        'encoder_prefix': tokenizer.prefix, 'special_tokens': 2, 'content_policy': config['content_policy'],
        'token_count_includes_prefix_and_special_tokens': True, 'truncation': False,
        'candidate_chunk_count': len(chunks), 'max_tokens': max((chunk['token_count'] for chunk in chunks), default=0),
        'over_limit_count': sum(chunk['token_count'] > tokenizer.max_length for chunk in chunks),
        'short_chunk_count': sum(chunk['short_chunk'] for chunk in chunks),
        'overlap_chunk_count': sum(chunk['overlap_characters'] > 0 for chunk in chunks),
        'excluded_document_count': counts['excluded_documents'], 'omitted_spans': omitted,
        'chunks': [{'chunk_id': chunk['chunk_id'], 'token_count': chunk['token_count'],
                    'characters': len(chunk['text']), 'overlap_tokens': chunk['overlap_tokens'],
                    'short_chunk': chunk['short_chunk']} for chunk in chunks],
    }
    manifest = {
        'schema_version': 'cs221-corpus-manifest-v1', 'status': 'candidate', 'review_state': 'pending',
        'release_ready': False, 'corpus_hash': corpus_hash, 'config': config, 'config_hash': sha256(config_path),
        'config_content_hash': canonical_hash(config), 'source_checksums': checksums,
        'versions': {key: config[key] for key in ('corpus_version', 'normalization_version', 'chunking_version')},
        'tokenizer': config['tokenizer'], 'counts': counts, 'selected_sources': config['selected_sources'],
        'candidate_whitelist': [doc['document_id'] for doc in documents if doc['candidate_eligible']],
        'index_whitelist': [], 'chunk_whitelist': [chunk['chunk_id'] for chunk in chunks],
        'exclusions': [{'document_id': row['document_id'], 'reason': row['reason']} for row in applicability
                       if row['decision'] == 'excluded'],
        'omitted_spans': omitted, 'coverage': 'unjudged', 'relevance': 'unjudged',
        'validation_receipt': {'status': 'pending_independent_validation', 'release_ready': False},
        'release_blockers': ['plan02_human_acceptance_pending', 'applicability_A_review_pending',
                             'tokenizer_and_citation_B_review_pending'],
        'hash_policy': 'canonical_digest_payload_before_corpus_hash_stamps; artifact_hashes_and_receipt_excluded',
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{output.name}-build-', dir=output.parent))
    try:
        for name, rows in (('documents.jsonl', documents), ('chunks.jsonl', chunks),
                           ('citation-registry.jsonl', citations), ('chunk-lineage.jsonl', lineage),
                           ('source-registry.jsonl', source_registry)):
            write_jsonl(stage / name, rows)
        (stage / 'applicability.tsv').write_bytes(applicability_path.read_bytes())
        write_json(stage / 'token-audit.json', token_audit)
        manifest['derived_file_hashes'] = {path.name: sha256(path) for path in sorted(stage.iterdir())}
        write_json(stage / 'corpus-manifest.json', manifest)
        from .validate_corpus import validate_corpus
        receipt = validate_corpus(stage, config_path)
        require(receipt.get('technical_valid') is True, 'PREPUBLICATION_VALIDATION_FAILED')
        manifest['validation_receipt'] = {'status': 'technical_pass', 'release_ready': False,
                                          'validator': 'src/corpus/validate_corpus.py', 'corpus_hash': corpus_hash}
        write_json(stage / 'corpus-manifest.json', manifest)
        _publish(stage, output)
    finally:
        if stage.exists():
            require(stage.resolve().parent == output.resolve().parent
                    and stage.name.startswith(f'.{output.name}-build-'), 'STAGING_PATH_BOUNDARY')
            shutil.rmtree(stage)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--replace-candidate', action='store_true', help='Explicitly replace an existing local candidate.')
    args = parser.parse_args(argv)
    manifest = build_corpus(args.config, args.output, replace_candidate=args.replace_candidate)
    print(json.dumps({'status': manifest['status'], 'corpus_hash': manifest['corpus_hash'], 'counts': manifest['counts']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
