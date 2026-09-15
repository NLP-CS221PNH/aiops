"""Independent source-span, content, token and release checks for plan 03."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

from .common import (ROOT, IMPL, DEFAULT_CONFIG, DEFAULT_OUTPUT, CorpusError,
                     canonical_hash, load_config, read_json, read_jsonl, require,
                     safe_path, sha256, text_hash, write_json)
from .tokenizer import CorpusTokenizer


def _rows_by_id(rows, key):
    require(isinstance(rows, list), f'ROWS_REQUIRED: {key}')
    require(all(isinstance(row, dict) and isinstance(row.get(key), str) and row[key] for row in rows), f'RECORD_ID: {key}')
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), f'DUPLICATE_ID: {key}')
    return result


def _integer(value, label):
    require(type(value) is int and value >= 0, f'OFFSET_INTEGER: {label}')
    return value


def _source_catalog(config):
    source_root = safe_path(ROOT, config['source_root'])
    for name, digest in config['source_hashes'].items():
        require(sha256(safe_path(source_root, name)) == digest, f'SOURCE_INPUT_HASH: {name}')
    sources = read_jsonl(source_root / 'documents.jsonl')
    assets = read_jsonl(source_root / 'supporting-assets.jsonl')
    manifest = _rows_by_id(read_jsonl(source_root / 'source-manifest.jsonl'), 'source_id')
    require(set(manifest) == set(config['selected_sources']), 'SOURCE_WHITELIST')
    require(dict(Counter(row['source_id'] for row in sources)) == config['expected_source_counts'], 'SOURCE_CENSUS')
    require(len(assets) == 12, 'ASSET_CENSUS')
    catalog = {}
    for row in sources + assets:
        path = safe_path(ROOT, row['raw_path'])
        require(path.is_relative_to(source_root / 'raw'), 'FOREIGN_RAW_SOURCE')
        digest = row.get('raw_sha256', row.get('sha256'))
        require(sha256(path) == digest, f'RAW_SOURCE_HASH: {row["raw_path"]}')
        source = manifest[row['source_id']]
        revision = row.get('version_scope', row.get('release_revision'))
        require(revision == source['release_revision'], 'SOURCE_REVISION')
        require(row['source_url'] == source['official_url'] + '/blob/' + revision + '/' + row['source_path'], 'SOURCE_URL')
        catalog[row['raw_path']] = dict(row, verified_raw_hash=digest, verified_revision=revision,
                                       raw_bytes=path.read_bytes())
    for source in manifest.values():
        require(sha256(safe_path(ROOT, source['license_snapshot_path'])) == source['license_snapshot_hash'], 'LICENSE_HASH')
        require(source['attribution'] and source['license_data'], 'LICENSE_PROVENANCE')
    return source_root, _rows_by_id(sources, 'document_id'), catalog


def _raw_span(span, catalog):
    require(isinstance(span, dict), 'SPAN_SCHEMA')
    require(span.get('raw_path') in catalog, 'FOREIGN_RAW_SOURCE')
    original = catalog[span['raw_path']]
    for field, expected in [('raw_sha256', original['verified_raw_hash']),
                            ('source_url', original['source_url']),
                            ('source_revision', original['verified_revision']),
                            ('source_id', original['source_id']), ('source_path', original['source_path'])]:
        require(span.get(field) == expected, f'SPAN_SOURCE_PROVENANCE: {field}')
    raw = original['raw_bytes'].decode('utf-8')
    start = _integer(span.get('raw_start'), 'raw_start')
    end = _integer(span.get('raw_end'), 'raw_end')
    require(start < end <= len(raw), 'RAW_SPAN_BOUNDS')
    require(_integer(span.get('raw_byte_start'), 'raw_byte_start') == len(raw[:start].encode('utf-8')), 'RAW_BYTE_OFFSET')
    require(_integer(span.get('raw_byte_end'), 'raw_byte_end') == len(raw[:end].encode('utf-8')), 'RAW_BYTE_OFFSET')
    return raw[start:end]


def _validate_spans(spans, text, start, end, catalog, document):
    require(isinstance(spans, list) and (spans or start == end), 'SPANS_REQUIRED')
    cursor = start
    for span in spans:
        lo = _integer(span.get('normalized_start'), 'normalized_start')
        hi = _integer(span.get('normalized_end'), 'normalized_end')
        require(lo == cursor and lo < hi <= end, 'NORMALIZED_SPAN_COVERAGE')
        raw = _raw_span(span, catalog)
        transform = span.get('transform')
        require(transform in ('identity', 'newline'), 'UNKNOWN_SPAN_TRANSFORM')
        value = raw if transform == 'identity' else raw.replace('\r\n', '\n').replace('\r', '\n')
        require(value == text[lo:hi], 'SOURCE_TEXT_SPAN_MISMATCH')
        if span.get('role') == 'document':
            require(span['raw_path'] == document['raw_path'], 'FOREIGN_DOCUMENT_SPAN')
        else:
            require(span.get('role') == 'supporting_asset', 'SOURCE_ROLE')
            asset = catalog[span['raw_path']]
            require(document['source_path'] in asset.get('referenced_by_source_paths', []), 'UNREFERENCED_ASSET')
            require(asset['source_id'] == document['source_id'] and asset['verified_revision'] == document['source_revision'], 'FOREIGN_ASSET')
            origin = span.get('include_origin', {})
            require(origin.get('raw_path') == document['raw_path'], 'INCLUDE_ORIGIN')
            original = catalog[document['raw_path']]['raw_bytes'].decode('utf-8')
            a, b = _integer(origin.get('raw_start'), 'include_start'), _integer(origin.get('raw_end'), 'include_end')
            require(a < b <= len(original) and original[a:b] == origin.get('directive'), 'INCLUDE_ORIGIN_SPAN')
        cursor = hi
    require(cursor == end, 'NORMALIZED_SPAN_COVERAGE')


def _validate_applicability(row):
    require(row.get('decision') in ('allowed', 'excluded', 'unknown'), 'APPLICABILITY_DECISION')
    require(isinstance(row.get('reason'), str) and row['reason'].strip(), 'APPLICABILITY_REASON')
    require(row.get('review_state') == 'pending' and not row.get('reviewer') and not row.get('reviewed_at'), 'CANDIDATE_REVIEW_STATE')
    require(row.get('app_version') == 'unknown' and row.get('platform_version') == 'unknown', 'DEPLOYMENT_NOT_VERIFIED')
    require(row.get('evidence_ids') and row.get('owner'), 'APPLICABILITY_EVIDENCE')
    if row['decision'] == 'unknown':
        require(row.get('allowed_experiment_mode') and row.get('config_preconditions'), 'UNKNOWN_WITHOUT_POLICY')


def _validate_raw_coverage(document, catalog):
    """Every original codepoint is retained or removed by a documented rule."""
    original = catalog[document['raw_path']]['raw_bytes'].decode('utf-8')
    partitions = [(span['raw_start'], span['raw_end']) for span in document['source_spans'] if span['role'] == 'document']
    removal_groups = {}
    for span in document['removed_spans']:
        require(span['raw_path'] == document['raw_path'], 'REMOVED_FOREIGN_DOCUMENT')
        require(span['reason'] in ('utf8_bom', 'markdown_frontmatter', 'initial_license_comment_retained_in_raw', 'replaced_by_verified_local_asset'), 'REMOVAL_RULE')
        partitions.append((span['raw_start'], span['raw_end']))
        removal_groups.setdefault(span['reason'], []).append(span)
    position = 0
    for start, end in sorted(partitions):
        require(start == position and start < end <= len(original), 'RAW_DOCUMENT_COVERAGE')
        position = end
    require(position == len(original), 'RAW_DOCUMENT_COVERAGE')
    for reason, spans in removal_groups.items():
        spans.sort(key=lambda span: span['raw_start'])
        if reason == 'utf8_bom':
            require(len(spans) == 1 and spans[0]['raw_start'] == 0 and spans[0]['raw_end'] == 1 and original.startswith('\ufeff'), 'BOM_REMOVAL')
        elif reason == 'replaced_by_verified_local_asset':
            intervals = []
            for span in spans:
                if intervals and intervals[-1][1] == span['raw_start']:
                    intervals[-1][1] = span['raw_end']
                else:
                    intervals.append([span['raw_start'], span['raw_end']])
            for start, end in intervals:
                require(re.fullmatch(r'\{\{[<%]\s*(include|code_sample)\s+.+?\s*[>%]\}\}', original[start:end]), 'INCLUDE_REMOVAL_RULE')
                require(any(s.get('include_origin', {}).get('raw_start') == start and s.get('include_origin', {}).get('raw_end') == end
                            for s in document['source_spans']), 'REMOVED_INCLUDE_WITHOUT_EXPANSION')
        else:
            start, end = spans[0]['raw_start'], spans[-1]['raw_end']
            require(start == int(original.startswith('\ufeff')), 'INITIAL_REMOVAL_POSITION')
            value = original[start:end].replace('\r\n', '\n').replace('\r', '\n')
            if reason == 'markdown_frontmatter':
                require(document['parser_kind'] == 'markdown' and value.startswith('---\n')
                        and re.fullmatch(r'---\n.*?^---[ \t]*(?:\n|$)', value, re.S | re.M), 'FRONTMATTER_REMOVAL_RULE')
            else:
                require(document['parser_kind'] in ('yaml', 'proto') and re.match(r'^(#|//) Copyright\b', value), 'LICENSE_REMOVAL_RULE')
                require(re.fullmatch(r'(?:(?:#|//)[^\n]*\n)*(?:#|//)[^\n]*limitations under the License\.[ \t]*(?:\n|$)', value), 'LICENSE_REMOVAL_RULE')


def _validate_chunk_coverage(documents, chunks, omitted):
    require(isinstance(omitted, list), 'OMITTED_SPANS_SCHEMA')
    by_document = {}
    for chunk in chunks:
        by_document.setdefault(chunk['document_id'], []).append((chunk['start_offset'], chunk['end_offset']))
    doc_by_id = {doc['document_id']: doc for doc in documents}
    for span in omitted:
        require(isinstance(span, dict) and set(span) == {'document_id', 'start_offset', 'end_offset', 'reason'}, 'OMITTED_SPAN_SCHEMA')
        require(span['document_id'] in doc_by_id, 'OMITTED_FOREIGN_DOCUMENT')
        doc = doc_by_id[span['document_id']]
        require(doc['candidate_eligible'] is True, 'OMITTED_EXCLUDED_DOCUMENT')
        start, end = _integer(span['start_offset'], 'omitted_start'), _integer(span['end_offset'], 'omitted_end')
        require(start < end <= len(doc['normalized_text']), 'OMITTED_SPAN_BOUNDS')
        require(span['reason'] == 'whitespace_or_html_marker_only'
                and not re.sub(r'<!--.*?-->', '', doc['normalized_text'][start:end], flags=re.S).strip(), 'UNJUSTIFIED_CONTENT_OMISSION')
        by_document.setdefault(span['document_id'], []).append((start, end))
    for doc in documents:
        if doc['applicability']['decision'] == 'excluded':
            require(doc['candidate_eligible'] is False and not by_document.get(doc['document_id']), 'EXCLUDED_DOCUMENT_COVERAGE')
            continue
        require(doc['candidate_eligible'] is True, 'CANDIDATE_DOCUMENT_ELIGIBILITY')
        end = 0
        for a, b in sorted(by_document.get(doc['document_id'], [])):
            require(a <= end, 'MISSING_CHUNK_COVERAGE')
            end = max(end, b)
        require(end == len(doc['normalized_text']), 'MISSING_CHUNK_COVERAGE')


def _source_offset_map(raw):
    """Map original acquisition text offsets to raw Unicode coordinates."""
    intervals = []
    pos = int(raw.startswith('\ufeff'))
    while pos < len(raw):
        stop = pos + 2 if raw[pos:pos + 2] == '\r\n' else pos + 1
        intervals.append((pos, stop))
        pos = stop
    return intervals


def _expected_old_links(old, chunks, catalog, original):
    raw = catalog[original['raw_path']]['raw_bytes'].decode('utf-8')
    mapping = _source_offset_map(raw)
    start, end = old['start_offset'], old['end_offset']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(mapping), 'OLD_CHUNK_BOUNDS')
    require(old['text'] == original['text'][start:end] and text_hash(old['text']) == old['text_hash'], 'OLD_CHUNK_TEXT')
    raw_start, raw_end = mapping[start][0], mapping[end - 1][1]
    expected = []
    for chunk in chunks:
        if chunk['document_id'] != old['parent_document_id']:
            continue
        spans = []
        for span in chunk['source_spans']:
            origin = span if span['role'] == 'document' else span.get('include_origin', {})
            if (origin.get('raw_path') == original['raw_path']
                    and origin['raw_start'] < raw_end and origin['raw_end'] > raw_start):
                a, b = max(raw_start, origin['raw_start']), min(raw_end, origin['raw_end'])
                if span['role'] == 'document':
                    lo = span['normalized_start'] + a - span['raw_start'] if span['transform'] == 'identity' else span['normalized_start']
                    hi = lo + b - a if span['transform'] == 'identity' else span['normalized_end']
                    spans.append({'normalized_start': lo, 'normalized_end': hi, 'raw_start': a, 'raw_end': b, 'mapping': 'direct'})
                else:
                    spans.append({'normalized_start': span['normalized_start'], 'normalized_end': span['normalized_end'],
                                  'raw_start': a, 'raw_end': b, 'mapping': 'local_include_expansion', 'asset_raw_path': span['raw_path']})
        if spans:
            expected.append({'chunk_id': chunk['chunk_id'], 'spans': spans})
    return raw_start, raw_end, expected


def _heading_at(document, offset):
    """Read heading state directly, excluding fenced code and embedded YAML."""
    heading, fence, pos = document['title'], None, 0
    if document['parser_kind'] != 'markdown':
        return heading
    for line in document['normalized_text'].splitlines(keepends=True):
        if pos > offset:
            break
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            value = marker[1]
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence) and not line[marker.end():].strip():
                fence = None
        match = re.match(r'^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*\n?$', line) if fence is None else None
        heading_pos = pos + len(line) - len(line.lstrip(' ')) if match else pos
        source = next((span for span in document['source_spans'] if span['normalized_start'] <= heading_pos < span['normalized_end']), {})
        if match and not (source.get('role') == 'supporting_asset' and not source.get('source_path', '').endswith('.md')):
            heading = match[1]
        pos += len(line)
    return heading


def validate_corpus(corpus_root=DEFAULT_OUTPUT, config_path=DEFAULT_CONFIG, require_reviewed=False):
    """Return evidence or raise CorpusError. No writing, downloading or model calls."""
    from .build_corpus import build_digest_payload

    root = Path(corpus_root).resolve()
    config = load_config(config_path)
    source_root, originals, catalog = _source_catalog(config)
    tokenizer = CorpusTokenizer(config)
    manifest = read_json(root / 'corpus-manifest.json')
    docs = read_jsonl(root / 'documents.jsonl')
    chunks = read_jsonl(root / 'chunks.jsonl')
    citations = read_jsonl(root / 'citation-registry.jsonl')
    lineage = read_jsonl(root / 'chunk-lineage.jsonl')
    with (root / 'applicability.tsv').open(encoding='utf-8-sig', newline='') as stream:
        applicability = list(csv.DictReader(stream, delimiter='\t'))
    doc_by_id, chunk_by_id = _rows_by_id(docs, 'document_id'), _rows_by_id(chunks, 'chunk_id')
    citation_by_id = _rows_by_id(citations, 'chunk_id')
    app_by_id = _rows_by_id(applicability, 'document_id')
    require(set(doc_by_id) == set(originals) == set(app_by_id), 'DOCUMENT_POPULATION')
    require(set(citation_by_id) == set(chunk_by_id), 'CITATION_POPULATION')
    require(manifest.get('status') == 'candidate', 'CANDIDATE_STATUS')
    corpus_hash = manifest.get('corpus_hash')
    require(isinstance(corpus_hash, str) and len(corpus_hash) == 64, 'CORPUS_HASH')
    require(manifest.get('config_hash') == sha256(config_path), 'CONFIG_HASH')
    require(manifest.get('config_content_hash') == canonical_hash(config), 'CONFIG_CONTENT_HASH')
    require(manifest.get('config') == config, 'CONFIG_SNAPSHOT')
    required_files = {'documents.jsonl', 'chunks.jsonl', 'citation-registry.jsonl', 'chunk-lineage.jsonl', 'applicability.tsv', 'source-registry.jsonl', 'token-audit.json'}
    require(set(manifest.get('derived_file_hashes', {})) == required_files, 'DERIVATIVE_FILE_INVENTORY')
    require({path.name for path in root.iterdir()} == required_files | {'corpus-manifest.json'}, 'FOREIGN_CORPUS_FILE')
    require(all(path.is_file() and not path.is_symlink() for path in root.iterdir()), 'UNSAFE_CORPUS_FILE')
    require(manifest.get('index_whitelist') == [], 'UNREVIEWED_INDEX_WHITELIST')
    require(manifest.get('review_state') == 'pending', 'MANIFEST_REVIEW_STATE')
    for name, digest in manifest['derived_file_hashes'].items():
        require(sha256(safe_path(root, name)) == digest, f'DERIVATIVE_FILE_HASH: {name}')
    for path, digest in manifest['source_checksums'].items():
        require(sha256(safe_path(ROOT, path)) == digest, f'SOURCE_CHECKSUM: {path}')

    for doc in docs:
        original = originals[doc['document_id']]
        require(doc.get('corpus_hash') == corpus_hash, 'FOREIGN_CORPUS_ID')
        require(doc.get('original_document_id') == doc['document_id'], 'ORIGINAL_DOCUMENT_ID')
        require(doc.get('derived_from_incident_ids') == [] and doc.get('is_synthetic') is False, 'INCIDENT_DERIVED_CONTENT')
        require(doc.get('index_eligible') is False, 'UNREVIEWED_DOCUMENT_ELIGIBILITY')
        for field in ('source_id', 'source_path', 'source_url', 'raw_path', 'raw_sha256', 'license', 'attribution', 'available_at', 'availability_basis', 'retrieved_at'):
            require(doc.get(field) == original[field], f'DOCUMENT_PROVENANCE: {field}')
        require(doc.get('source_revision') == original['version_scope'], 'DOCUMENT_REVISION')
        require(doc.get('original_title') == original['title'], 'ORIGINAL_TITLE')
        if original['title'].startswith('Copyright '):
            expected_title = f"{Path(original['source_path']).stem} Kubernetes manifest" if doc['parser_kind'] == 'yaml' else original['source_path']
            require(doc.get('title') == expected_title, 'COPYRIGHT_TITLE')
        else:
            require(doc.get('title') == original['title'], 'UNEXPECTED_TITLE_CHANGE')
        text = doc['normalized_text']
        require(doc['normalized_text_hash'] == text_hash(text), 'NORMALIZED_TEXT_HASH')
        require(doc['normalization_version'] == config['normalization_version'], 'NORMALIZATION_VERSION')
        _validate_spans(doc['source_spans'], text, 0, len(text), catalog, doc)
        for removed in doc['removed_spans']:
            _raw_span(removed, catalog)
            require(removed.get('reason'), 'REMOVAL_REASON')
        _validate_raw_coverage(doc, catalog)
        _validate_applicability(doc['applicability'])
        require(doc['applicability'].get('decision_version') == config['applicability']['decision_version'], 'APPLICABILITY_DECISION_VERSION')
        # CSV encodes list/dict fields as canonical JSON; compare their values.
        for key, value in doc['applicability'].items():
            if key not in app_by_id[doc['document_id']]:
                continue
            expected = app_by_id[doc['document_id']][key]
            if isinstance(value, (list, dict)):
                require(json.loads(expected) == value, f'APPLICABILITY_JOIN: {key}')
            else:
                require(str(value if value is not None else '') == expected, f'APPLICABILITY_JOIN: {key}')

    for chunk in chunks:
        require(chunk.get('document_id') in doc_by_id, 'FOREIGN_DOCUMENT_ID')
        doc = doc_by_id[chunk['document_id']]
        require(chunk.get('corpus_hash') == corpus_hash, 'FOREIGN_CORPUS_ID')
        require(chunk.get('index_eligible') is False and chunk.get('candidate_eligible') is True, 'CANDIDATE_ELIGIBILITY')
        require(doc['applicability']['decision'] != 'excluded', 'EXCLUDED_CONTENT')
        require(chunk.get('applicability') == doc['applicability'], 'CHUNK_APPLICABILITY')
        for field in ('source_id', 'source_url', 'source_revision', 'license', 'attribution', 'available_at'):
            require(chunk.get(field) == doc.get(field), f'CHUNK_PROVENANCE: {field}')
        start, end = _integer(chunk.get('start_offset'), 'start'), _integer(chunk.get('end_offset'), 'end')
        require(start < end <= len(doc['normalized_text']), 'CHUNK_BOUNDS')
        require(chunk.get('offset_unit') == 'unicode_codepoint_in_normalized_text', 'OFFSET_UNIT')
        require(chunk['text'] == doc['normalized_text'][start:end], 'CHUNK_TEXT_SPAN')
        require(chunk['section_heading'] == _heading_at(doc, start), 'CHUNK_HEADING')
        require(chunk['text_hash'] == text_hash(chunk['text']), 'CHUNK_TEXT_HASH')
        require(chunk['content'] == tokenizer.content(chunk['section_heading'], chunk['text']), 'CONTENT_POLICY')
        require(chunk['content_hash'] == text_hash(chunk['content']), 'CONTENT_HASH')
        identity = {'document_id': doc['document_id'], 'normalized_text_hash': doc['normalized_text_hash'],
                    'config_hash': canonical_hash(config), 'start_offset': start, 'end_offset': end,
                    'section_heading': chunk['section_heading'], 'content': chunk['content']}
        require(chunk['chunk_id'] == f"KBC-{doc['source_id']}-{canonical_hash(identity)[:24]}", 'CHUNK_CONTENT_ID')
        require(type(chunk.get('token_count')) is int, 'REAL_TOKEN_COUNT_REQUIRED')
        require(chunk['token_count'] == tokenizer.count(chunk['content']) <= tokenizer.max_length, 'TOKEN_BUDGET')
        require(chunk['normalization_version'] == config['normalization_version'] and chunk['chunking_version'] == config['chunking_version'], 'CHUNK_VERSION')
        _validate_spans(chunk['source_spans'], doc['normalized_text'], start, end, catalog, doc)
        citation = citation_by_id[chunk['chunk_id']]
        require(citation.get('corpus_hash') == corpus_hash, 'FOREIGN_CITATION_CORPUS')
        require(citation.get('document_id') == chunk['document_id'], 'CITATION_DOCUMENT')
        require(citation.get('source_spans') == chunk['source_spans'], 'CITATION_SOURCE_SPANS')
        require(citation.get('normalized_span') == {'start': start, 'end': end}, 'CITATION_NORMALIZED_SPAN')
        for field in ('text_hash', 'content_hash', 'source_url', 'source_revision', 'source_id', 'license',
                      'attribution', 'applicability', 'offset_unit', 'review_state'):
            require(citation.get(field) == chunk.get(field), f'CITATION_METADATA: {field}')

    old_chunks = _rows_by_id(read_jsonl(source_root / 'chunks.jsonl'), 'chunk_id')
    old_to_new = _rows_by_id(lineage, 'old_chunk_id')
    require(set(old_to_new) == set(old_chunks), 'LINEAGE_POPULATION')
    for row in lineage:
        old = old_chunks[row['old_chunk_id']]
        require(row.get('parent_document_id') == old['parent_document_id'], 'LINEAGE_PARENT')
        require(row.get('corpus_hash') == corpus_hash, 'FOREIGN_LINEAGE_CORPUS')
        require(isinstance(row.get('new_chunk_ids'), list), 'LINEAGE_NEW_IDS')
        require(len(row['new_chunk_ids']) == len(set(row['new_chunk_ids'])), 'DUPLICATE_LINEAGE_NEW_ID')
        require(all(key in chunk_by_id and chunk_by_id[key]['document_id'] == old['parent_document_id'] for key in row['new_chunk_ids']), 'LINEAGE_FOREIGN_CHUNK')
        a, b, expected_spans = _expected_old_links(old, chunks, catalog, originals[old['parent_document_id']])
        require(row['new_chunk_ids'] == [match['chunk_id'] for match in expected_spans], 'LINEAGE_SPAN_LINKS')
        require(row.get('new_spans') == expected_spans, 'LINEAGE_NEW_SPANS')
        for field, value in [('old_start_offset', old['start_offset']), ('old_end_offset', old['end_offset']),
                             ('old_text_hash', old['text_hash']), ('old_raw_start', a), ('old_raw_end', b),
                             ('document_id', old['parent_document_id']), ('normalization_version', config['normalization_version']),
                             ('chunking_version', config['chunking_version']), ('qrel_transfer', 'prohibited_requires_rejudgment')]:
            require(row.get(field) == value, f'LINEAGE_METADATA: {field}')
        excluded = doc_by_id[old['parent_document_id']]['applicability']['decision'] == 'excluded'
        relation = ('one_to_many' if len(expected_spans) > 1 else 'overlap') if expected_spans else ('excluded' if excluded else 'removed')
        require(row.get('relation') == relation, 'LINEAGE_RELATION')
        require(not row.get('reason') if expected_spans else bool(row.get('reason')), 'LINEAGE_REASON')

    # The builder exposes only the serialization shape; semantic checks above
    # reconstruct source slices independently and do not use its normalizer.
    payload = build_digest_payload(config, manifest['source_checksums'], docs, chunks, citations, lineage, applicability)
    require(canonical_hash(payload) == corpus_hash, 'CORPUS_CONTENT_DIGEST')
    counts = {'source_documents': len(docs), 'candidate_documents': len({c['document_id'] for c in chunks}),
              'candidate_chunks': len(chunks), 'indexed_documents': 0, 'indexed_chunks': 0,
              'excluded_documents': sum(d['applicability']['decision'] == 'excluded' for d in docs),
              'unknown_documents': sum(d['applicability']['decision'] == 'unknown' for d in docs),
              'old_chunks': len(lineage), 'max_tokens': max((c['token_count'] for c in chunks), default=0)}
    require(manifest['counts'].get('documents') == len(docs), 'MANIFEST_COUNTS')
    for field in ('candidate_documents', 'candidate_chunks', 'indexed_documents', 'indexed_chunks', 'excluded_documents', 'unknown_documents'):
        require(type(manifest['counts'].get(field)) is int and manifest['counts'][field] == counts[field], f'MANIFEST_COUNTS: {field}')
    require(sorted(manifest.get('candidate_whitelist', [])) == sorted({c['document_id'] for c in chunks}), 'CANDIDATE_WHITELIST')
    require(sorted(manifest.get('chunk_whitelist', [])) == sorted(chunk_by_id), 'CHUNK_WHITELIST')
    require(manifest.get('release_ready') is False and manifest.get('coverage') == manifest.get('relevance') == 'unjudged', 'UNMEASURED_RELEASE_CLAIM')
    require(manifest.get('tokenizer') == config['tokenizer'] and manifest.get('selected_sources') == config['selected_sources'], 'MANIFEST_CONTRACT')
    require(manifest.get('versions') == {key: config[key] for key in ('corpus_version', 'normalization_version', 'chunking_version')}, 'MANIFEST_VERSIONS')
    for field, expected in [('allowed_documents', sum(row['decision'] == 'allowed' for row in applicability)),
                            ('source_chunks', len(lineage)), ('supporting_assets', 12)]:
        require(type(manifest['counts'].get(field)) is int and manifest['counts'][field] == expected, f'MANIFEST_COUNTS: {field}')
    expected_exclusions = [{'document_id': row['document_id'], 'reason': row['reason']} for row in applicability if row['decision'] == 'excluded']
    require(manifest.get('exclusions') == expected_exclusions, 'MANIFEST_EXCLUSIONS')
    audit = read_json(root / 'token-audit.json')
    require(audit.get('corpus_hash') == corpus_hash and audit.get('tokenizer_revision') == tokenizer.revision, 'TOKEN_AUDIT_CORPUS')
    require(audit.get('tokenizer_sha256') == config['tokenizer']['sha256'], 'TOKEN_AUDIT_ASSET')
    require(audit.get('token_count_includes_prefix_and_special_tokens') is True and audit.get('truncation') is False, 'TOKEN_AUDIT_POLICY')
    require(audit.get('max_tokens') == counts['max_tokens'] and audit.get('over_limit_count') == 0, 'TOKEN_AUDIT_BUDGET')
    expected_tokens = [{'chunk_id': c['chunk_id'], 'token_count': c['token_count'], 'characters': len(c['text']),
                        'overlap_tokens': c['overlap_tokens'], 'short_chunk': c['short_chunk']} for c in chunks]
    require(audit.get('chunks') == expected_tokens, 'TOKEN_AUDIT_ROWS')
    audit_expected = {'max_length': tokenizer.max_length, 'encoder_prefix': tokenizer.prefix, 'special_tokens': 2,
                      'library_version': config['tokenizer']['library_version'], 'candidate_chunk_count': len(chunks),
                      'short_chunk_count': sum(c['short_chunk'] for c in chunks),
                      'overlap_chunk_count': sum(c['overlap_characters'] > 0 for c in chunks),
                      'excluded_document_count': counts['excluded_documents'], 'content_policy': config['content_policy']}
    for field, expected in audit_expected.items():
        require(type(audit.get(field)) is type(expected) and audit[field] == expected, f'TOKEN_AUDIT_SUMMARY: {field}')
    require(audit.get('omitted_spans') == manifest.get('omitted_spans'), 'OMITTED_SPANS_AUDIT')
    _validate_chunk_coverage(docs, chunks, manifest.get('omitted_spans'))
    require(sha256(root / 'source-registry.jsonl') == sha256(safe_path(IMPL, config['preparation_root']) / 'source-registry.jsonl'), 'SOURCE_REGISTRY_PROPOSAL')
    require(sha256(root / 'applicability.tsv') == sha256(safe_path(IMPL, config['applicability_path'])), 'APPLICABILITY_PROPOSAL')
    if require_reviewed:
        raise CorpusError('RELEASE_PENDING: plan02 full acceptance and plan03 human applicability review required')
    return {'schema_version': 'cs221-corpus-validation-v1', 'status': 'pass', 'technical_valid': True,
            'release_ready': False, 'corpus_hash': corpus_hash, 'counts': counts,
            'validation_scope': 'all source and derivative hashes, spans, token counts, citations, lineage, candidate boundary',
            'coverage': 'unjudged', 'compatibility': 'unknown', 'human_review': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-root', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--require-reviewed', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = validate_corpus(args.corpus_root, args.config, args.require_reviewed)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'status': 'fail', 'technical_valid': False, 'error': str(error)}
    if args.output:
        output = args.output.resolve()
        require(output.is_relative_to(IMPL / 'reports') or output.is_relative_to(IMPL / '.test-work'), 'VALIDATION_OUTPUT_BOUNDARY')
        write_json(output, result)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
