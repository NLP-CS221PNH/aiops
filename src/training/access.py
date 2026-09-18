"""Fail-closed path access for trainer commands.

Trainer prepare/train/export may open inference plus the explicitly mounted
private train (and optional dev selector) roots. They must not stat, open, or
hash a test label root even when that directory exists and is readable.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from src.data.common import DataContractError, require, sha256 as file_sha256

EXIT_OK = 0
EXIT_CLI = 2
EXIT_MISSING = 3
EXIT_INTEGRITY = 4
EXIT_RUNTIME = 5

INTEGRITY_CODES = {
    'HASH_MISMATCH', 'TEST_ROOT_ACCESS', 'PRIVATE_FIELD', 'PRIVATE_VALUE',
    'FAMILY_OVERLAP', 'SPLIT_MISMATCH', 'SPLIT_COUNTS', 'GOLD_IDS',
    'DUPLICATE_ID', 'FOREIGN_INCIDENT', 'PROMPT_LEAK', 'PARTITION_SCHEMA',
    'TARGET_EMPTY', 'INCIDENT_ID', 'PRIVATE_ID_MISMATCH', 'PATH_FORBIDDEN',
    'PATH_ESCAPE', 'PATH_ALIAS', 'OUTPUT_VERSION_CHANGE_REQUIRED',
    'EXAMPLE_SCHEMA', 'SPLIT_VERSION', 'GOLD_LINEAGE', 'BIJECTION',
}


def exit_code_for(error: BaseException) -> int:
    code = getattr(error, 'code', '')
    if isinstance(error, (ValueError, TypeError)) and not isinstance(error, DataContractError):
        return EXIT_CLI
    if code in INTEGRITY_CODES:
        return EXIT_INTEGRITY
    if code in {'MISSING_FILE', 'MISSING_INPUT', 'MISSING_ROOT', 'MISSING_CONFIG'}:
        return EXIT_MISSING
    if code in {'CONFIG_SCHEMA', 'CLI_INVALID', 'CONFIG_IDS', 'CONFIG_COUNTS'}:
        return EXIT_CLI
    if isinstance(error, DataContractError):
        return EXIT_INTEGRITY
    if isinstance(error, FileNotFoundError):
        return EXIT_MISSING
    return EXIT_RUNTIME


class TrainingAccessGuard:
    """Record every filesystem touch and reject forbidden subtrees."""

    def __init__(self, allowed_roots, forbidden_roots=()):
        self.allowed = tuple(Path(root).resolve() for root in allowed_roots)
        self.forbidden = tuple(Path(root).resolve() for root in forbidden_roots if root)
        self.touched: list[tuple[str, str]] = []

    def _under(self, path: Path, root: Path) -> bool:
        return path == root or path.is_relative_to(root)

    def check(self, path, operation: str) -> Path:
        resolved = Path(path).resolve()
        self.touched.append((operation, str(resolved)))
        for forbidden in self.forbidden:
            if self._under(resolved, forbidden):
                raise DataContractError('TEST_ROOT_ACCESS')
        require(any(self._under(resolved, allowed) for allowed in self.allowed), 'PATH_FORBIDDEN')
        return resolved

    def open(self, path, mode='r', **kwargs):
        return self.check(path, 'open').open(mode, **kwargs)

    def stat(self, path):
        return self.check(path, 'stat').stat()

    def sha256(self, path):
        return file_sha256(self.check(path, 'hash'))

    def is_file(self, path):
        return self.check(path, 'stat').is_file()


def lexical_relative(root: Path, relative: str) -> Path:
    """Join a relative path without following a later open yet."""
    text = str(relative).replace('\\', '/')
    require(bool(text) and ':' not in text and not PureWindowsPath(text).is_absolute()
            and not PurePosixPath(text).is_absolute() and '..' not in PurePosixPath(text).parts,
            'PATH_FORBIDDEN')
    return Path(root) / text
