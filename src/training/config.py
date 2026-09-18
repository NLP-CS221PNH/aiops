"""Load training and resolved Kaggle configs without touching a test root."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.common import IMPL, DataContractError, require

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_mapping(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    require(path.is_file(), 'MISSING_CONFIG')
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix in {'.yaml', '.yml'}:
        if yaml is None:
            raise DataContractError('MISSING_RUNTIME')
        payload = yaml.safe_load(text) or {}
    else:
        payload = json.loads(text)
    require(isinstance(payload, dict), 'CONFIG_SCHEMA')
    return payload


def resolve_under(root: Path, value: str | None) -> Path | None:
    if value in (None, '', 'null'):
        return None
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_training_config(path: str | Path | None = None) -> dict[str, Any]:
    return load_mapping(path or (IMPL / 'configs' / 'training.yaml'))


def load_resolved_kaggle(path: str | Path, impl: Path | None = None) -> dict[str, Any]:
    impl = impl or IMPL
    payload = load_mapping(path)
    require(payload.get('schema_version') == 'cs221-kaggle-resolved-v1', 'CONFIG_SCHEMA')
    resolved = dict(payload)
    resolved.pop('private_test_root', None)
    for key in (
        'inference_root', 'private_train_root', 'private_dev_root',
        'knowledge_root', 'qwen_assets', 'e5_assets', 'output_root', 'source_root',
    ):
        if key in payload:
            resolved[key] = resolve_under(impl, payload.get(key))
    resolved['config_path'] = str(Path(path).resolve())
    return resolved
