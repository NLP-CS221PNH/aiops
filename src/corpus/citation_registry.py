"""Resolve only validated local corpus citations; stale/foreign identifiers fail closed."""
from __future__ import annotations

from pathlib import Path

from .common import DEFAULT_CONFIG, DEFAULT_OUTPUT, read_json, read_jsonl, require


def resolve_citation(chunk_id, corpus_root=DEFAULT_OUTPUT, corpus_hash=None, *, config_path=DEFAULT_CONFIG):
    corpus_root = Path(corpus_root)
    manifest = read_json(corpus_root / 'corpus-manifest.json')
    if corpus_hash is not None:
        require(corpus_hash == manifest['corpus_hash'], 'FOREIGN_CORPUS_HASH')
    matches = [row for row in read_jsonl(corpus_root / 'citation-registry.jsonl') if row['chunk_id'] == chunk_id]
    require(len(matches) == 1, 'UNKNOWN_OR_DUPLICATE_CITATION')
    from .validate_corpus import validate_corpus
    validate_corpus(corpus_root, config_path)
    require(matches[0]['corpus_hash'] == manifest['corpus_hash'], 'STALE_CITATION_REGISTRY')
    return matches[0]
