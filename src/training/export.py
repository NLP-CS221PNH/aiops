"""Export and reload adapter weights. Smoke exports are never research adapters."""
from __future__ import annotations

import json
from pathlib import Path

from src.data.common import canonical_hash, require, sha256, write_json
from src.training.adapters import adapter_hash, adapter_state_dict
from src.training.collator import pad_batch, tokenize_example
from src.training.config import load_training_config
from src.training.qwen_loader import load_qwen_lora, load_tiny_lora
from src.training.tiny_model import require_torch

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

try:
    from safetensors.torch import save_file, load_file
except ImportError:  # pragma: no cover
    save_file = None
    load_file = None


def export_adapter(run_dir: Path, output_dir: Path, *, checkpoint: str = 'best-dev') -> dict:
    require_torch()
    run_dir = Path(run_dir)
    output_dir = Path(output_dir)
    receipt = json.loads((run_dir / 'receipt.json').read_text(encoding='utf-8'))
    adapter_last = run_dir / 'adapter_last.pt'
    adapter_best = run_dir / 'adapter_best.pt'
    if checkpoint == 'best-dev' and adapter_best.is_file():
        adapter_path = adapter_best
        selected = 'best-dev'
    else:
        adapter_path = adapter_last
        selected = 'adapter_last' if checkpoint == 'best-dev' else checkpoint
    require(adapter_path.is_file(), 'MISSING_INPUT')
    output_dir.mkdir(parents=True, exist_ok=True)
    state = torch.load(adapter_path, map_location='cpu', weights_only=True)
    if save_file is not None:
        save_file({key: value.contiguous() for key, value in state.items()}, str(output_dir / 'adapter_model.safetensors'))
        weights = output_dir / 'adapter_model.safetensors'
    else:
        torch.save(state, output_dir / 'adapter_model.pt')
        weights = output_dir / 'adapter_model.pt'
    identity = dict(receipt.get('base_model') or {})
    if not identity:
        identity = {
            'id': 'tiny-causal-lm' if receipt.get('model_kind') == 'tiny' else 'Qwen/Qwen2.5-1.5B-Instruct',
            'kind': receipt.get('model_kind') or 'tiny',
        }
    manifest = {
        'schema_version': 'cs221-adapter-export-v1',
        'checkpoint': selected,
        'requested_checkpoint': checkpoint,
        'smoke_only': bool(receipt.get('smoke_only')),
        'run_kind': receipt.get('run_kind'),
        'run_id': receipt.get('run_id'),
        'adapter_hash': receipt.get('adapter_hash_after'),
        'base_hash': receipt.get('base_hash'),
        'weights': weights.name,
        'weights_sha256': sha256(weights),
        'base_model': identity,
    }
    write_json(output_dir / 'adapter-manifest.json', manifest)
    return manifest


def _load_weights(path: Path) -> dict:
    if path.suffix == '.safetensors' and load_file is not None:
        return load_file(str(path))
    return torch.load(path, map_location='cpu', weights_only=True)


def verify_export(export_dir: Path, example: dict, recipe: dict | None = None, atol: float = 1e-5) -> dict:
    require_torch()
    export_dir = Path(export_dir)
    manifest = json.loads((export_dir / 'adapter-manifest.json').read_text(encoding='utf-8'))
    recipe = recipe or load_training_config()
    identity = dict(manifest.get('base_model') or {})
    if identity.get('kind') == 'qwen':
        assets = identity.get('assets')
        require(assets and Path(assets).is_dir(), 'MISSING_INPUT')
        model, tokenizer, _loaded = load_qwen_lora(Path(assets), recipe)
    else:
        model, tokenizer, _loaded = load_tiny_lora(recipe)
    weights = _load_weights(export_dir / manifest['weights'])
    missing, unexpected = model.load_state_dict(weights, strict=False)
    require(not unexpected, 'HASH_MISMATCH')
    model.eval()
    row = tokenize_example(example, tokenizer)
    batch = pad_batch([row], pad_id=tokenizer.pad_token_id)
    with torch.no_grad():
        logits = model(
            input_ids=torch.tensor(batch['input_ids'], dtype=torch.long),
            attention_mask=torch.tensor(batch['attention_mask'], dtype=torch.long),
        ).logits
    return {
        'status': 'pass',
        'smoke_only': manifest.get('smoke_only'),
        'adapter_hash': adapter_hash(model),
        'logits_sha256': canonical_hash(logits.cpu().tolist()),
        'atol': atol,
        'missing_keys': list(missing),
    }
