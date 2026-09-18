"""Data-only and GPU preflight. Trainer never stats the test root."""
from __future__ import annotations

from pathlib import Path

from src.data.common import IMPL, DEFAULT_CONFIG, require
from src.training.access import TrainingAccessGuard
from src.training.config import load_resolved_kaggle, load_training_config
from src.training.data import join_training_examples, load_partition
from src.training.tiny_model import TORCH_IMPORT_ERROR, torch


def _guard_for(resolved: dict) -> TrainingAccessGuard:
    allowed = [
        resolved['inference_root'],
        resolved['private_train_root'],
        IMPL / 'configs',
        IMPL / 'schemas',
        IMPL / 'data' / 'inference',
        Path(DEFAULT_CONFIG).resolve().parent,
    ]
    if resolved.get('private_dev_root'):
        allowed.append(resolved['private_dev_root'])
    if resolved.get('qwen_assets'):
        allowed.append(resolved['qwen_assets'])
    if resolved.get('output_root'):
        allowed.append(resolved['output_root'])
    return TrainingAccessGuard(allowed, ())


def preflight(resolved_config_path: str | Path, *, data_only: bool = True, require_gpu: bool = False) -> dict:
    resolved = load_resolved_kaggle(resolved_config_path)
    require(resolved.get('inference_root') and resolved.get('private_train_root'), 'MISSING_ROOT')
    guard = _guard_for(resolved)
    inference = Path(resolved['inference_root'])
    train_root = Path(resolved['private_train_root'])
    require(guard.is_file(inference / 'input-manifest.json'), 'MISSING_FILE')
    load_partition(train_root, 'train', guard)
    if resolved.get('private_dev_root'):
        load_partition(Path(resolved['private_dev_root']), 'dev', guard)
    recipe = load_training_config()
    gpu = False
    if torch is not None:
        gpu = bool(torch.cuda.is_available())
    if require_gpu and not gpu:
        raise RuntimeError('missing_runtime: CUDA GPU is required for this preflight')
    if not data_only:
        assets = resolved.get('qwen_assets')
        require(assets and Path(assets).is_dir(), 'MISSING_INPUT')
    return {
        'status': 'pass',
        'data_only': data_only,
        'gpu_available': gpu,
        'torch_available': torch is not None,
        'torch_import_error': None if torch is not None else str(TORCH_IMPORT_ERROR),
        'lora': recipe.get('lora'),
        'touched': guard.touched,
        'test_root_accessed': any(
            'private-test' in Path(path).as_posix() for _op, path in guard.touched
        ),
    }


def prepare_examples(resolved_config_path: str | Path, output_path: str | Path | None = None) -> dict:
    resolved = load_resolved_kaggle(resolved_config_path)
    forbidden = [resolved['private_test_root']] if resolved.get('private_test_root') else []
    receipt = join_training_examples(
        resolved['inference_root'],
        resolved['private_train_root'],
        private_dev_root=resolved.get('private_dev_root'),
        forbidden_roots=forbidden,
    )
    from src.training.data import write_examples
    dest = Path(output_path or (Path(resolved.get('output_root') or IMPL / 'artifacts') / 'train-examples.jsonl'))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sidecar = write_examples(receipt, dest)
    sidecar['test_root_accessed'] = False
    return sidecar
