"""Section-first windows whose actual encoder input fits a pinned tokenizer."""
from __future__ import annotations

import re

from .common import canonical_hash, require, text_hash
from .normalize import clip_spans


def sections(document):
    text = document['normalized_text']
    boundaries = [(0, document['title'])]
    if document['parser_kind'] == 'markdown':
        fence = None
        position = 0
        for line in text.splitlines(keepends=True):
            marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
            if marker:
                value = marker[1]
                if fence is None:
                    fence = value
                elif (value[0] == fence[0] and len(value) >= len(fence)
                      and not line[marker.end():].strip()):
                    fence = None
            heading = re.match(r'^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*\n?$', line) if fence is None else None
            heading_position = position + line.index('#') if heading else position
            source = next((span for span in document['source_spans']
                           if span['normalized_start'] <= heading_position < span['normalized_end']), None)
            if heading and not (source and source['role'] == 'supporting_asset'
                                and not source['source_path'].endswith('.md')):
                if position == 0:
                    boundaries[0] = (0, heading[1])
                else:
                    boundaries.append((position, heading[1]))
            position += len(line)
    return [(start, boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text), heading)
            for index, (start, heading) in enumerate(boundaries)]


def _boilerplate_only(text):
    return not re.sub(r'<!--.*?-->', '', text, flags=re.S).strip()


def chunk_document(document, tokenizer, config, *, root):
    chunks, omitted = [], []
    text = document['normalized_text']
    overlap_budget = config['chunking']['overlap_tokens']
    for section_index, (section_start, section_end, heading) in enumerate(sections(document)):
        if _boilerplate_only(text[section_start:section_end]):
            if section_end > section_start:
                omitted.append({'document_id': document['document_id'], 'start_offset': section_start,
                                'end_offset': section_end, 'reason': 'whitespace_or_html_marker_only'})
            continue
        require(tokenizer.count(tokenizer.content(heading, '')) < tokenizer.max_length,
                f"HEADING_EXCEEDS_TOKEN_BUDGET: {document['document_id']}")
        start, previous_end = section_start, section_start
        while start < section_end:
            remaining = text[start:section_end]
            content = tokenizer.content(heading, remaining)
            if tokenizer.count(content) <= tokenizer.max_length:
                stop = section_end
            else:
                encoding = tokenizer.encode(remaining, add_special_tokens=False)
                # Candidate boundaries use true token offsets, never chars/4.
                boundaries = sorted({end for begin, end in encoding.offsets if end > 0})
                low, high, best = 0, len(boundaries) - 1, None
                while low <= high:
                    middle = (low + high) // 2
                    proposed = boundaries[middle]
                    if tokenizer.count(tokenizer.content(heading, remaining[:proposed])) <= tokenizer.max_length:
                        best, low = proposed, middle + 1
                    else:
                        high = middle - 1
                require(best is not None and best > 0, 'NO_CONTENT_TOKEN_BUDGET')
                stop = start + best
                newline = text.rfind('\n', start + int(best * 0.65), stop)
                if newline >= 0:
                    stop = newline + 1
            require(stop > start, 'CHUNKER_NO_PROGRESS')
            chunk_text = text[start:stop]
            content = tokenizer.content(heading, chunk_text)
            count = tokenizer.count(content)
            require(count <= tokenizer.max_length, 'CHUNK_EXCEEDS_TOKEN_BUDGET')
            identity = {
                'document_id': document['document_id'], 'normalized_text_hash': document['normalized_text_hash'],
                'config_hash': canonical_hash(config), 'start_offset': start, 'end_offset': stop,
                'section_heading': heading, 'content': content,
            }
            chunks.append({
                'chunk_id': f"KBC-{document['source_id']}-{canonical_hash(identity)[:24]}",
                'document_id': document['document_id'], 'section_heading': heading, 'section_index': section_index,
                'text': chunk_text, 'text_hash': text_hash(chunk_text), 'content': content,
                'content_hash': text_hash(content), 'start_offset': start, 'end_offset': stop,
                'offset_unit': 'unicode_codepoint_in_normalized_text', 'token_count': count,
                'overlap_start': start, 'overlap_end': previous_end if start < previous_end else start,
                'overlap_characters': max(0, previous_end - start),
                'overlap_tokens': len(tokenizer.encode(text[start:previous_end], add_special_tokens=False).ids)
                                  if start < previous_end else 0,
                'short_chunk': len(chunk_text) <= config['chunking']['short_chunk_chars'],
                'source_spans': clip_spans(document['source_spans'], start, stop, root=root),
                'source_id': document['source_id'], 'source_url': document['source_url'],
                'source_revision': document['source_revision'], 'license': document['license'],
                'attribution': document['attribution'], 'available_at': document['available_at'],
                'normalization_version': config['normalization_version'], 'chunking_version': config['chunking_version'],
                'applicability': document['applicability'], 'candidate_eligible': True, 'index_eligible': False,
                'review_state': 'pending',
            })
            if stop == section_end:
                break
            previous_end = stop
            if overlap_budget:
                offsets = tokenizer.encode(chunk_text, add_special_tokens=False).offsets
                begin = offsets[max(0, len(offsets) - overlap_budget)][0]
                start = max(start + 1, start + begin)
            else:
                start = stop
    return chunks, omitted
