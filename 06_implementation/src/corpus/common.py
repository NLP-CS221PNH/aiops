"""Small, offline primitives for the versioned historical corpus."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

IMPL = Path(__file__).resolve().parents[2]
ROOT = IMPL.parent
DEFAULT_CONFIG = IMPL / 'configs/corpus.yaml'
DEFAULT_OUTPUT = IMPL / 'data/knowledge'


class CorpusError(ValueError):
    """A source or derivative violates the corpus contract."""


def require(condition, message):
    if not condition:
        raise CorpusError(message)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'DUPLICATE_JSON_KEY: {key}')
        result[key] = value
    return result


def parse_json(text):
    def invalid(value):
        raise CorpusError(f'NONFINITE_JSON: {value}')
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=invalid)


def read_json(path):
    return parse_json(Path(path).read_text(encoding='utf-8'))


def read_jsonl(path):
    return [parse_json(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n' for row in rows).encode('utf-8'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_hash(value):
    return text_hash(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False))


def safe_path(root, relative):
    root = Path(root).resolve()
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'RELATIVE_PATH_REQUIRED')
    path = (root / relative).resolve()
    require(path.is_relative_to(root), f'PATH_ESCAPE: {relative}')
    return path


def load_config(path=DEFAULT_CONFIG):
    # JSON is a YAML subset; no parser/dependency variation in replay.
    config = read_json(path)
    require(config.get('schema_version') == 'cs221-corpus-config-v1', 'CONFIG_SCHEMA')
    require(config.get('selected_sources') == ['D057', 'D058', 'D059'], 'SOURCE_WHITELIST')
    require(config.get('source_root') == '03_collection_plan/knowledge-corpus-historical', 'HISTORICAL_ONLY')
    require(config.get('normalization_version') and config.get('chunking_version') and config.get('corpus_version'), 'VERSIONS_REQUIRED')
    tokenizer = config.get('tokenizer', {})
    require(tokenizer.get('model_id') == 'intfloat/e5-small-v2', 'TOKENIZER_MODEL')
    require(tokenizer.get('revision') == 'ffb93f3bd4047442299a41ebb6fa998a38507c52', 'TOKENIZER_REVISION')
    require(type(tokenizer.get('max_length')) is int and 8 <= tokenizer['max_length'] <= 512, 'TOKEN_LIMIT')
    require(tokenizer.get('prefix') == 'passage: ', 'TOKEN_PREFIX')
    require(tokenizer.get('special_tokens') == 2 and tokenizer.get('truncation') is False and tokenizer.get('padding') is False, 'TOKENIZER_POLICY')
    overlap = config.get('chunking', {}).get('overlap_tokens')
    require(type(overlap) is int and 0 <= overlap < tokenizer['max_length'] // 2, 'OVERLAP_BUDGET')
    short = config.get('chunking', {}).get('short_chunk_chars')
    require(type(short) is int and short >= 0, 'SHORT_CHUNK_THRESHOLD')
    require(config.get('content_policy') == 'section_heading + newline + text', 'CONTENT_POLICY_CONFIG')
    supported = {'preserve_technical_literals': True, 'newline': 'LF', 'unicode_normalization': 'none',
                 'remove_frontmatter': True, 'remove_initial_license_boilerplate_from_index_only': True,
                 'replace_copyright_titles': True, 'hugo_include_policy': 'verified_local_assets_only',
                 'unknown_hugo_policy': 'preserve_with_warning', 'offset_unit': 'unicode_codepoint'}
    require(config.get('normalization') == supported, 'UNSUPPORTED_NORMALIZATION_POLICY')
    release = config.get('release_policy', {})
    require(release.get('status') == 'candidate' and release.get('index_eligible') is False
            and release.get('requires_plan02_full_acceptance') is True
            and release.get('requires_human_applicability_review') is True, 'RELEASE_POLICY_CONFIG')
    require(config.get('applicability', {}).get('human_review_required_for_release') is True, 'APPLICABILITY_REVIEW_POLICY')
    require(config['applicability'].get('decision_version') == 'applicability-proposal-v1', 'APPLICABILITY_DECISION_VERSION')
    return config
