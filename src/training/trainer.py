"""LoRA causal LM trainer. Smoke and research namespaces stay isolated."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Sequence

from src.data.common import IMPL, canonical_hash, require, write_json
from src.training.adapters import adapter_hash, adapter_state_dict, base_hash
from src.training.checkpoint import latest_complete, load_checkpoint, save_checkpoint
from src.training.collator import pad_batch, tokenize_example
from src.training.config import load_training_config
from src.training.qwen_loader import resolve_model_and_tokenizer
from src.training.tiny_model import require_torch

try:
    import torch
    from torch.optim import AdamW
    from torch.optim.lr_scheduler import LambdaLR
except ImportError:  # pragma: no cover
    torch = None
    AdamW = None
    LambdaLR = None


def seed_everything(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    if torch is not None:
        torch.manual_seed(seed)


def _linear_warmup(step: int, total: int, warmup_ratio: float) -> float:
    warmup = max(1, int(total * warmup_ratio))
    if step < warmup:
        return float(step + 1) / float(warmup)
    remain = max(1, total - warmup)
    return max(0.0, float(total - step) / float(remain))


def build_model(vocab_size: int, recipe: dict):
    model, _tokenizer, _identity = resolve_model_and_tokenizer(recipe, tokenizer=None, model=None, mode='smoke')
    return model


def collate_examples(examples: Sequence[dict], tokenizer, recipe: dict) -> list[dict]:
    sequence = recipe.get('sequence') or {}
    rows = []
    for example in examples:
        rows.append(tokenize_example(
            example, tokenizer,
            max_train_tokens=int(sequence.get('max_train_tokens', 3072)),
            prompt_cap=int(sequence.get('prompt_cap', 2944)),
            target_reserve=int(sequence.get('target_reserve', 128)),
        ))
    return rows


def train_run(
    examples: Sequence[dict],
    *,
    run_id: str,
    mode: str = 'smoke',
    max_steps: int | None = None,
    resume: str | None = None,
    interrupt_after: int | None = None,
    recipe: dict | None = None,
    output_root: Path | None = None,
    tokenizer=None,
    model=None,
    qwen_assets=None,
    require_qwen: bool = False,
) -> dict[str, Any]:
    require(mode in {'smoke', 'full'}, 'CLI_INVALID')
    require(examples, 'MISSING_INPUT')
    recipe = recipe or load_training_config()
    seed = int((recipe.get('schedule') or {}).get('seed', 221))
    seed_everything(seed)
    ordered = list(examples)
    require(mode != 'full' or max_steps is None or max_steps >= 1, 'CLI_INVALID')
    namespaces = recipe.get('namespaces') or {}
    kind = 'smoke' if mode == 'smoke' else 'research'
    root = Path(output_root or IMPL) / namespaces.get(kind, f'runs/training/{kind}') / run_id
    if mode == 'smoke':
        planned = int(max_steps or recipe.get('smoke', {}).get('max_steps', 2))
        require(kind == 'smoke', 'CLI_INVALID')
    else:
        epochs = int((recipe.get('schedule') or {}).get('max_epochs', 3))
        planned = int(max_steps or (epochs * len(ordered)))
    if resume == 'latest-complete':
        require(kind == 'research', 'CLI_INVALID')
        ckpt = latest_complete(root)
        require(ckpt is not None, 'MISSING_INPUT')
        resume = str(ckpt)
    model, tokenizer, identity = resolve_model_and_tokenizer(
        recipe, qwen_assets=qwen_assets, tokenizer=tokenizer, model=model, mode=mode,
        require_qwen=require_qwen,
    )
    opt_cfg = recipe.get('optimizer') or {}
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = AdamW(
        trainable,
        lr=float(opt_cfg.get('lr', 1e-4)),
        betas=tuple(opt_cfg.get('betas') or (0.9, 0.999)),
        eps=float(opt_cfg.get('eps', 1e-8)),
        weight_decay=float(opt_cfg.get('weight_decay', 0.01)),
    )
    scheduler = LambdaLR(optimizer, lambda step: _linear_warmup(step, planned, float((recipe.get('schedule') or {}).get('warmup_ratio', 0.1))))
    start = 0
    if resume:
        state = load_checkpoint(Path(resume), model, optimizer, scheduler)
        require(int(state['total_planned_steps']) == planned, 'RESUME_HORIZON_MISMATCH')
        start = int(state['global_step'])
    before_adapter = adapter_hash(model)
    before_base = base_hash(model)
    rows = collate_examples(ordered, tokenizer, recipe)
    pad_id = int(getattr(tokenizer, 'pad_token_id', 0) or 0)
    model.train()
    losses = []
    grads = []
    step = start
    accumulation = int((recipe.get('batching') or {}).get('accumulation', 1))
    optimizer.zero_grad()
    while step < planned:
        example = rows[step % len(rows)]
        batch = pad_batch([example], pad_id=pad_id)
        input_ids = torch.tensor(batch['input_ids'], dtype=torch.long)
        labels = torch.tensor(batch['labels'], dtype=torch.long)
        mask = torch.tensor(batch['attention_mask'], dtype=torch.long)
        out = model(input_ids=input_ids, attention_mask=mask, labels=labels)
        loss = out.loss
        require(loss is not None and torch.isfinite(loss), 'TRAIN_NAN')
        (loss / accumulation).backward()
        if (step + 1) % accumulation == 0 or (step + 1) == planned:
            grad_norm = torch.nn.utils.clip_grad_norm_(trainable, float(opt_cfg.get('max_grad_norm', 1.0)))
            grads.append(float(grad_norm))
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        losses.append(float(loss.detach()))
        step += 1
        trainer_state = {
            'run_id': run_id,
            'run_kind': kind,
            'global_step': step,
            'total_planned_steps': planned,
            'example_order_sha256': canonical_hash([item.get('example_id') for item in ordered]),
            'mode': mode,
            'smoke_only': kind == 'smoke',
        }
        save_checkpoint(root, model=model, optimizer=optimizer, scheduler=scheduler,
                        trainer_state=trainer_state, complete=True)
        if interrupt_after is not None and step >= int(interrupt_after):
            break
    after_adapter = adapter_hash(model)
    after_base = base_hash(model)
    require(after_base == before_base, 'BASE_NOT_FROZEN')
    require(after_adapter != before_adapter, 'ADAPTER_UNCHANGED')
    require(any(value > 0 for value in grads), 'ZERO_GRAD')
    logits = model(input_ids=input_ids, attention_mask=mask).logits.detach()
    receipt = {
        'schema_version': 'cs221-training-run-v1',
        'run_id': run_id,
        'run_kind': kind,
        'mode': mode,
        'steps': step,
        'total_planned_steps': planned,
        'losses': losses,
        'grad_norms': grads,
        'adapter_hash_before': before_adapter,
        'adapter_hash_after': after_adapter,
        'base_hash': after_base,
        'smoke_only': kind == 'smoke',
        'run_dir': str(root),
        'final_logits_sha256': canonical_hash(logits.cpu().tolist()),
        'tiny_training_mechanics_verified': identity.get('kind') == 'tiny',
        'target_model_smoke_verified': identity.get('kind') == 'qwen' and kind == 'smoke',
        'full_training_run_completed': False,
        'model_kind': identity.get('kind'),
        'base_model': identity,
    }
    write_json(root / 'receipt.json', receipt)
    torch.save(adapter_state_dict(model), root / 'adapter_last.pt')
    return receipt
