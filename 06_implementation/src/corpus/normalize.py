"""Loss-aware normalization with separate Unicode and UTF-8 provenance spans."""
from __future__ import annotations

import re
from pathlib import Path

from .common import ROOT, require, safe_path, sha256, text_hash


def raw_units(raw_text):
    """Return normalized characters and exact original codepoint intervals."""
    units = []
    position = 1 if raw_text.startswith('\ufeff') else 0
    while position < len(raw_text):
        end = position + 1
        char = raw_text[position]
        if char == '\r':
            if end < len(raw_text) and raw_text[end] == '\n':
                end += 1
            char = '\n'
        units.append((char, position, end))
        position = end
    return units


def _reference(record, role):
    return {
        'raw_path': record['raw_path'],
        'raw_sha256': record.get('raw_sha256', record.get('sha256')),
        'source_url': record['source_url'],
        'source_revision': record.get('version_scope', record.get('release_revision')),
        'source_id': record['source_id'], 'source_path': record['source_path'],
        'role': role,
    }


def _load(record, role, root):
    ref = _reference(record, role)
    path = safe_path(root, ref['raw_path'])
    require(sha256(path) == ref['raw_sha256'], f"RAW_HASH: {ref['raw_path']}")
    raw = path.read_bytes().decode('utf-8')
    byte_offsets = [0]
    for char in raw:
        byte_offsets.append(byte_offsets[-1] + len(char.encode('utf-8')))
    units = [{'char': char, 'raw_start': start, 'raw_end': end,
              'raw_byte_start': byte_offsets[start], 'raw_byte_end': byte_offsets[end],
              **ref, 'transform': 'newline' if raw[start:end] != char else 'identity'}
             for char, start, end in raw_units(raw)]
    return raw, units


def _spans(units):
    result = []
    for position, unit in enumerate(units):
        current = {key: value for key, value in unit.items() if key != 'char'}
        current.update(normalized_start=position, normalized_end=position + 1)
        previous = result[-1] if result else None
        # Newline transformations remain individual non-linear spans.
        if (previous and current['transform'] == previous['transform'] == 'identity'
                and previous['raw_end'] == current['raw_start']
                and all(previous.get(key) == current.get(key) for key in
                        ('raw_path', 'role', 'include_origin'))):
            previous['raw_end'] = current['raw_end']
            previous['raw_byte_end'] = current['raw_byte_end']
            previous['normalized_end'] = position + 1
        else:
            result.append(current)
    return result


def _removal(units, reason):
    spans = _spans(units)
    for span in spans:
        span.pop('normalized_start')
        span.pop('normalized_end')
        span['reason'] = reason
    return spans


def normalize_document(source, assets=(), *, root=ROOT):
    """Normalize a verified document; never fetch or execute referenced content."""
    root = Path(root)
    raw, units = _load(source, 'document', root)
    warnings, changes, removed = [], [], []
    suffix = Path(source['source_path']).suffix.lower()
    parser_kind = 'yaml' if suffix in ('.yaml', '.yml') else 'proto' if suffix == '.proto' else 'markdown'
    if raw.startswith('\ufeff'):
        removed.append({**_reference(source, 'document'), 'raw_start': 0, 'raw_end': 1,
                        'raw_byte_start': 0, 'raw_byte_end': 3, 'transform': 'removed', 'reason': 'utf8_bom'})
        changes.append('utf8_bom_removed')
    source_text = ''.join(unit['char'] for unit in units)
    require(source_text == source['text'], f"SOURCE_TEXT_RAW_MISMATCH: {source['document_id']}")
    if any(unit['transform'] == 'newline' for unit in units):
        changes.append('newlines_normalized')

    if parser_kind == 'markdown' and source_text.startswith('---\n'):
        closing = re.search(r'^---[ \t]*(?:\n|$)', source_text[4:], re.M)
        if closing:
            stop = 4 + closing.end()
            removed.extend(_removal(units[:stop], 'markdown_frontmatter'))
            units = units[stop:]
            changes.append('markdown_frontmatter_removed')
        else:
            warnings.append({'kind': 'unterminated_frontmatter', 'action': 'preserved_verbatim'})

    text = ''.join(unit['char'] for unit in units)
    if parser_kind in ('yaml', 'proto') and re.match(r'^(?:#|//) Copyright\b', text):
        boilerplate = re.match(r'(?:(?:#|//)[^\n]*(?:\n|$))+', text)
        if boilerplate and 'limitations under the License.' in boilerplate.group():
            closing = re.search(r'^(?:#|//)[^\n]*limitations under the License\.[^\n]*(?:\n|$)',
                                boilerplate.group(), re.M)
            stop = closing.end()
            removed.extend(_removal(units[:stop], 'initial_license_comment_retained_in_raw'))
            units = units[stop:]
            changes.append('initial_license_comment_removed_from_derivative')

    title = source['title']
    if title.startswith('Copyright '):
        title = f"{Path(source['source_path']).stem} Kubernetes manifest" if parser_kind == 'yaml' else source['source_path']
        changes.append('copyright_title_replaced_from_source_path')

    if parser_kind == 'markdown':
        text = ''.join(unit['char'] for unit in units)
        replacements = []
        verified_assets = {(asset['source_id'], asset['source_path']): asset for asset in assets}
        pattern = re.compile(r'\{\{[<%]\s*(include|code_sample)\s+(.+?)\s*[>%]\}\}')
        for match in pattern.finditer(text):
            name, args = match.groups()
            argument = (re.fullmatch(r'"([^"\n]+)"', args) if name == 'include'
                        else re.fullmatch(r'file="([^"\n]+)"', args))
            candidate = ('content/en/includes/' if name == 'include' else 'content/en/examples/') + argument[1] if argument else None
            asset = verified_assets.get((source['source_id'], candidate))
            if (asset is None or source['source_path'] not in asset.get('referenced_by_source_paths', [])
                    or asset['release_revision'] != source['version_scope']):
                warnings.append({'kind': 'unresolved_local_directive', 'directive': match.group(),
                                 'raw_path': source['raw_path'], 'raw_start': units[match.start()]['raw_start'],
                                 'raw_end': units[match.end() - 1]['raw_end'],
                                 'action': 'preserved_verbatim'})
                continue
            _, expansion = _load(asset, 'supporting_asset', root)
            origin_units = units[match.start():match.end()]
            origin = {'raw_path': source['raw_path'], 'raw_start': origin_units[0]['raw_start'],
                      'raw_end': origin_units[-1]['raw_end'], 'directive': match.group()}
            for unit in expansion:
                unit['include_origin'] = origin
            replacements.append((match.start(), match.end(), expansion))
            removed.extend(_removal(origin_units, 'replaced_by_verified_local_asset'))
            changes.append(f"resolved_{name}:{asset['source_path']}")
        for start, end, expansion in reversed(replacements):
            units[start:end] = expansion
        rendered = ''.join(unit['char'] for unit in units)
        for directive in re.finditer(r'\{\{[<%].*?[>%]\}\}', rendered, re.S):
            warnings.append({'kind': 'hugo_directive_not_rendered', 'directive': directive.group(),
                             'normalized_start': directive.start(), 'normalized_end': directive.end(),
                             'action': 'preserved_verbatim'})

    normalized = ''.join(unit['char'] for unit in units)
    return {
        'title': title, 'original_title': source['title'], 'parser_kind': parser_kind,
        'normalized_text': normalized, 'normalized_text_hash': text_hash(normalized),
        'source_spans': _spans(units), 'removed_spans': removed,
        'normalization_changes': changes, 'rendering_warnings': warnings,
    }


def clip_spans(spans, start, end, *, root=ROOT):
    """Clip normalized intervals while retaining exact codepoint and byte offsets."""
    clipped = []
    for original in spans:
        lo, hi = max(start, original['normalized_start']), min(end, original['normalized_end'])
        if lo >= hi:
            continue
        span = dict(original)
        if span['transform'] == 'identity':
            raw = safe_path(root, span['raw_path']).read_bytes().decode('utf-8')
            span['raw_start'] += lo - original['normalized_start']
            span['raw_end'] = span['raw_start'] + hi - lo
            span['raw_byte_start'] = len(raw[:span['raw_start']].encode('utf-8'))
            span['raw_byte_end'] = len(raw[:span['raw_end']].encode('utf-8'))
        else:
            require(lo == span['normalized_start'] and hi == span['normalized_end'], 'NONLINEAR_SPAN_SPLIT')
        span.update(normalized_start=lo, normalized_end=hi)
        clipped.append(span)
    require(sum(span['normalized_end'] - span['normalized_start'] for span in clipped) == end - start,
            'UNCOVERED_NORMALIZED_SPAN')
    return clipped
