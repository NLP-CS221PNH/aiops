"""Pinned tokenizer assets only; no model execution or implicit network access."""
from __future__ import annotations

import sys
from importlib import metadata

from .common import IMPL, require, safe_path, sha256


class CorpusTokenizer:
    def __init__(self, config):
        spec = config['tokenizer']
        dependency_root = IMPL / '.corpus-deps'
        if dependency_root.exists() and str(dependency_root) not in sys.path:
            sys.path.insert(0, str(dependency_root))
        from tokenizers import Tokenizer
        require(metadata.version('tokenizers') == spec['library_version'], 'TOKENIZER_LIBRARY_VERSION')
        tokenizer_path = safe_path(IMPL, spec['path'])
        require(sha256(tokenizer_path) == spec['sha256'], 'TOKENIZER_ASSET_HASH')
        for entry in spec.get('assets', []):
            require(sha256(safe_path(IMPL, entry['path'])) == entry['sha256'], 'TOKENIZER_ASSET_HASH')
        self.backend = Tokenizer.from_file(str(tokenizer_path))
        self.backend.no_truncation()
        self.backend.no_padding()
        self.prefix = spec['prefix']
        self.max_length = spec['max_length']
        self.revision = spec['revision']
        require(self.backend.num_special_tokens_to_add(False) == 2, 'TOKENIZER_SPECIALS')

    def encode(self, text, add_special_tokens=True):
        return self.backend.encode(text, add_special_tokens=add_special_tokens)

    @staticmethod
    def content(heading, text):
        return heading + '\n' + text

    def count(self, content):
        return len(self.encode(self.prefix + content, add_special_tokens=True).ids)
