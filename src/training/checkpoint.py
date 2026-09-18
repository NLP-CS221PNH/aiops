"""Full-state checkpoints with atomic complete markers."""
from __future__ import annotations

import json
import random
from pathlib import Path

from src.data.common import canonical_bytes, require, sha256, write_json
from src.training.tiny_model import require_torch

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

INVENTORY = (
    'model.pt', 'optimizer.pt', 'scheduler.pt', 'rng.pt',
    'trainer_state.json', 'complete.marker',
)


def rng_state() -> dict:
    payload = {'python': random.getstate()}
    if np is not None:
        payload['numpy'] = np.random.get_state()
    if torch is not None:
        payload['torch_cpu'] = torch.get_rng_state()
        if torch.cuda.is_available():
            payload['torch_cuda'] = torch.cuda.get_rng_state_all()
    return payload


def restore_rng(payload: dict) -> None:
    random.setstate(payload['python'])
    if np is not None and 'numpy' in payload:
        np.random.set_state(payload['numpy'])
    if torch is not None and 'torch_cpu' in payload:
        torch.set_rng_state(payload['torch_cpu'])
        if torch.cuda.is_available() and payload.get('torch_cuda') is not None:
            torch.cuda.set_rng_state_all(payload['torch_cuda'])


def save_checkpoint(
    run_dir: Path,
    *,
    model,
    optimizer,
    scheduler,
    trainer_state: dict,
    complete: bool,
) -> Path:
    require_torch()
    run_dir = Path(run_dir)
    step = int(trainer_state['global_step'])
    target = run_dir / f'checkpoint-{step:06d}'
    require(not target.exists(), 'CHECKPOINT_OVERWRITE')
    target.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), target / 'model.pt')
    torch.save(optimizer.state_dict(), target / 'optimizer.pt')
    torch.save(scheduler.state_dict() if scheduler is not None else {}, target / 'scheduler.pt')
    torch.save(rng_state(), target / 'rng.pt')
    write_json(target / 'trainer_state.json', trainer_state)
    files = {
        'model.pt': sha256(target / 'model.pt'),
        'optimizer.pt': sha256(target / 'optimizer.pt'),
        'scheduler.pt': sha256(target / 'scheduler.pt'),
        'rng.pt': sha256(target / 'rng.pt'),
        'trainer_state.json': sha256(target / 'trainer_state.json'),
    }
    write_json(target / 'inventory.json', {'files': files, 'complete': complete})
    if complete:
        (target / 'complete.marker').write_text('complete\n', encoding='utf-8')
    return target


def load_checkpoint(path: Path, model, optimizer, scheduler):
    require_torch()
    path = Path(path)
    inventory = json.loads((path / 'inventory.json').read_text(encoding='utf-8'))
    require(inventory.get('complete') is True, 'CHECKPOINT_INCOMPLETE')
    require((path / 'complete.marker').is_file(), 'CHECKPOINT_INCOMPLETE')
    for name, digest in inventory['files'].items():
        require(sha256(path / name) == digest, 'HASH_MISMATCH')
    model.load_state_dict(torch.load(path / 'model.pt', map_location='cpu', weights_only=True))
    optimizer.load_state_dict(torch.load(path / 'optimizer.pt', map_location='cpu', weights_only=True))
    sched = torch.load(path / 'scheduler.pt', map_location='cpu', weights_only=True)
    if scheduler is not None and sched:
        scheduler.load_state_dict(sched)
    restore_rng(torch.load(path / 'rng.pt', map_location='cpu', weights_only=False))
    state = json.loads((path / 'trainer_state.json').read_text(encoding='utf-8'))
    return state


def latest_complete(run_dir: Path) -> Path | None:
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        return None
    candidates = []
    for child in run_dir.iterdir():
        if child.is_dir() and child.name.startswith('checkpoint-') and (child / 'complete.marker').is_file():
            candidates.append(child)
    if not candidates:
        return None
    return sorted(candidates)[-1]
