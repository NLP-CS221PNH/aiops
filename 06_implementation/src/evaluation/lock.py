"""Load the methodology lock and compare knobs to pinned source files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.evaluation.cli_ops import IMPL

LOCK_REL = Path("configs") / "methodology-lock.yaml"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lock_path(root: Path | None = None) -> Path:
    return (root or IMPL) / LOCK_REL


def load_lock(root: Path | None = None) -> dict[str, Any]:
    path = lock_path(root)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("methodology_lock_invalid")
    return payload


def lock_file_sha256(root: Path | None = None) -> str:
    return sha256_bytes(lock_path(root).read_bytes())


def _lookup(record: Any, dotted: str) -> Any:
    current = record
    for part in dotted.split("."):
        if isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(dotted)
    return current


def load_source(root: Path, relative: str) -> Any:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            return json.loads(text)
    return json.loads(text)


def compare_lock_to_sources(root: Path | None = None) -> list[dict[str, Any]]:
    base = root or IMPL
    lock = load_lock(base)
    mismatches = []
    for knob in lock.get("knobs") or []:
        source = load_source(base, knob["source_path"])
        actual = _lookup(source, knob["source_key"])
        expected = knob["value"]
        if actual != expected:
            mismatches.append({
                "name": knob["name"],
                "expected": expected,
                "actual": actual,
                "source_path": knob["source_path"],
            })
    return mismatches
