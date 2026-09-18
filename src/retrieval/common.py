"""Retrieval-local integrity primitives; no private-data/evaluation imports."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timezone

IMPL = Path(__file__).resolve().parents[2]
HASH = re.compile(r'[0-9a-f]{64}\Z')
PRIVATE_FIELDS = {'scenario_family_id', 'family', 'split', 'gold', 'ground_truth',
                  'source_case', 'source-case', 'fault', 'injection_time',
                  'injection_target', 'label', 'labels', 'qrels', 'root_cause_service',
                  'local_path', 'private', 'answer', 'relevance_grade'}
READ_ROOTS = ('configs', 'queries', 'data/knowledge', 'data/inference', 'freezes',
              'vendor', 'schemas', 'tests/fixtures/retrieval', '.test-work/retrieval')
WRITE_ROOTS = ('cache/retrieval', 'runs/retrieval', '.test-work/retrieval')
TOKENIZER_HASH = 'd241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66'


class RetrievalError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise RetrievalError(code)


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def _pairs(pairs):
    output = {}
    for key, value in pairs:
        require(key not in output, 'DUPLICATE_JSON_KEY:' + key)
        output[key] = value
    return output


def parse_json(text):
    return json.loads(text, object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(RetrievalError('NONFINITE_JSON')))


def read_json(path):
    return parse_json(Path(path).read_text(encoding='utf-8-sig'))


def read_jsonl(path):
    return [parse_json(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def safe_path(value, *, write=False, roots=None):
    """Reject traversal, private paths and links before opening a file."""
    path = Path(value)
    require('..' not in path.parts, 'PATH_TRAVERSAL')
    path = path if path.is_absolute() else IMPL / path
    absolute = path.absolute()
    resolved = absolute.resolve()
    require(absolute == resolved, 'PATH_ALIAS_OR_SYMLINK')
    choices = roots if roots is not None else (WRITE_ROOTS if write else READ_ROOTS)
    require(any(resolved.is_relative_to((IMPL / root).resolve()) for root in choices), 'PATH_NOT_ALLOWED')
    require(not any(part.lower() in {'private', 'qrels', 'labels', 'annotations'} for part in resolved.parts), 'PRIVATE_PATH')
    return resolved


def atomic_json(path, value):
    path = safe_path(path, write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(value) + b'\n'
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def reject_private(value):
    if isinstance(value, dict):
        require(not PRIVATE_FIELDS.intersection(value), 'PRIVATE_FIELD')
        for item in value.values():
            reject_private(item)
    elif isinstance(value, list):
        for item in value:
            reject_private(item)


def exact_fields(value, fields, code):
    require(isinstance(value, dict) and set(value) == set(fields), code)


def local_schema(schema):
    """JSON schemas are local contracts, never instructions to fetch a URI."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key in {'$ref', '$dynamicRef'}:
                require(isinstance(value, str) and value.startswith('#'), 'EXTERNAL_SCHEMA_REFERENCE')
            local_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            local_schema(value)
    return schema


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def utc_now():
    return datetime.now(timezone.utc).isoformat()
