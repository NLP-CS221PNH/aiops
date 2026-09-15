"""Hash-verified immutable caches and per-run atomic checkpoints."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re

from .common import (RetrievalError, atomic_json, digest, exact_fields, read_json,
                     require, safe_path, sha256, utc_now)


def cache_key(*, corpus_hash, chunks, model, content_policy):
    """The full model policy includes asset hashes, prefixes and token limits."""
    return digest({'schema_version': 'retrieval-cache-key-v1', 'corpus_hash': corpus_hash,
                   'rows': [{'chunk_id': c['chunk_id'], 'document_id': c['document_id'],
                             'content_hash': c['content_hash']} for c in chunks],
                   'model': model, 'content_policy': content_policy})


class ArtifactCache:
    def __init__(self, root):
        self.root = safe_path(root, write=True)

    def load(self, key):
        from .common import HASH
        require(isinstance(key, str) and HASH.fullmatch(key), 'CACHE_KEY')
        path = safe_path(self.root / (key + '.json'), write=True)
        if not path.exists():
            return None
        row = read_json(path)
        exact_fields(row, {'schema_version', 'key', 'payload_hash', 'payload'}, 'CACHE_SCHEMA')
        require(row['schema_version'] == 'retrieval-cache-v1' and row['key'] == key, 'CACHE_FINGERPRINT')
        require(row['payload_hash'] == digest(row['payload']), 'CACHE_CHECKSUM')
        return row['payload']

    def store(self, key, payload):
        from .common import HASH
        require(isinstance(key, str) and HASH.fullmatch(key), 'CACHE_KEY')
        # Runs have separate directories but share caches. Serialize publication
        # per key too, so a concurrent writer cannot replace an immutable entry.
        with run_lock(self.root / ('lock-' + key)):
            existing = self.load(key)
            if existing is not None:
                require(digest(existing) == digest(payload), 'CACHE_IMMUTABILITY')
                return
            atomic_json(self.root / (key + '.json'), {'schema_version': 'retrieval-cache-v1',
                        'key': key, 'payload_hash': digest(payload), 'payload': payload})


@contextmanager
def run_lock(directory):
    """Exclusive writer; stale lock requires deliberate recovery after process death."""
    directory = safe_path(directory, write=True)
    directory.mkdir(parents=True, exist_ok=True)
    lock = safe_path(directory / '.writer.lock', write=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RetrievalError('RUN_LOCKED: verify no active writer before recovering the lock') from exc
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


class Checkpoints:
    def __init__(self, directory, fingerprint, specification, *, resume=False):
        self.directory = safe_path(directory, write=True)
        self.fingerprint = fingerprint
        self.specification = specification
        self.path = self.directory / 'checkpoint-index.json'
        if self.path.exists():
            require(resume, 'RUN_EXISTS_USE_RESUME_OR_NEW_ID')
            self.index = read_json(safe_path(self.path, write=True))
            exact_fields(self.index, {'schema_version', 'fingerprint', 'specification', 'records'}, 'CHECKPOINT_SCHEMA')
            require(self.index['schema_version'] == 'retrieval-checkpoints-v1', 'CHECKPOINT_SCHEMA')
            require(self.index['fingerprint'] == fingerprint
                    and self.index['specification'] == specification, 'RESUME_FINGERPRINT_MISMATCH')
            require(isinstance(self.index['records'], dict), 'CHECKPOINT_SCHEMA')
            # Verify every committed record before any encoder/index work.
            for key in self.index['records']:
                self.get(key)
        else:
            require(not resume, 'RESUME_NOT_FOUND')
            require(not self.directory.exists() or not any(p.name != '.writer.lock' for p in self.directory.iterdir()),
                    'OUTPUT_DIRECTORY_NOT_EMPTY')
            self.index = {'schema_version': 'retrieval-checkpoints-v1',
                          'fingerprint': fingerprint, 'specification': specification, 'records': {}}
            atomic_json(self.path, self.index)

    def get(self, key):
        entry = self.index['records'].get(key)
        if entry is None:
            return None
        exact_fields(entry, {'path', 'sha256'}, 'CHECKPOINT_ENTRY')
        require(re.fullmatch(digest(key) + r'-[0-9a-f]{64}\.json', entry['path']) is not None, 'CHECKPOINT_PATH')
        path = safe_path(self.directory / 'records' / entry['path'], write=True)
        require(path.is_file() and sha256(path) == entry['sha256'], 'CHECKPOINT_CHECKSUM')
        row = read_json(path)
        require(entry['path'] == digest(key) + '-' + digest(row) + '.json', 'CHECKPOINT_CONTENT_ID')
        require(row.get('fingerprint') == self.fingerprint and row.get('record_key') == key, 'CHECKPOINT_BINDING')
        return row

    def put(self, key, row):
        require(row.get('fingerprint') == self.fingerprint and row.get('record_key') == key, 'CHECKPOINT_BINDING')
        # Each attempt has immutable bytes. A process dying before the index
        # switch leaves the previous committed attempt readable and retryable.
        name = digest(key) + '-' + digest(row) + '.json'
        path = self.directory / 'records' / name
        atomic_json(path, row)
        self.index['records'][key] = {'path': name, 'sha256': sha256(path)}
        atomic_json(self.path, self.index)
