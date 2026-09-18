"""Load pinned local Qwen + PEFT LoRA when assets exist. Tiny path stays separate."""
from __future__ import annotations

from pathlib import Path

from src.data.common import require
from src.training.collator import ByteTokenizer
from src.training.tiny_model import TinyCausalLM, require_torch
from src.training.adapters import frozen_base_ok, inject_lora, is_adapter_param


def load_qwen_lora(assets: Path, recipe: dict):
    require_torch()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(f'missing_runtime: transformers/peft required for Qwen LoRA ({exc})') from exc
    root = Path(assets)
    require(root.is_dir(), 'MISSING_INPUT')
    tokenizer = AutoTokenizer.from_pretrained(str(root), local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(root), local_files_only=True, trust_remote_code=False, use_cache=False,
    )
    lora = recipe.get('lora') or {}
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=int(lora.get('r', 8)),
        lora_alpha=int(lora.get('lora_alpha', 16)),
        lora_dropout=float(lora.get('lora_dropout', 0.05)),
        bias=str(lora.get('bias', 'none')),
        target_modules=list(lora.get('target_modules') or ['q_proj', 'v_proj']),
    )
    model = get_peft_model(model, config)
    for name, parameter in model.named_parameters():
        parameter.requires_grad = is_adapter_param(name)
    return model, tokenizer, {
        'id': 'Qwen/Qwen2.5-1.5B-Instruct',
        'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306',
        'kind': 'qwen',
        'local_files_only': True,
        'assets': str(root),
    }


def load_tiny_lora(recipe: dict, vocab_size: int = 258):
    require_torch()
    model = TinyCausalLM(vocab_size=vocab_size)
    lora = recipe.get('lora') or {}
    inject_lora(
        model,
        r=int(lora.get('r', 8)),
        alpha=int(lora.get('lora_alpha', 16)),
        dropout=float(lora.get('lora_dropout', 0.05)),
        targets=tuple(lora.get('target_modules') or ('q_proj', 'v_proj')),
    )
    require(frozen_base_ok(model), 'BASE_NOT_FROZEN')
    return model, ByteTokenizer(), {
        'id': 'tiny-causal-lm',
        'revision': None,
        'kind': 'tiny',
        'local_files_only': True,
    }


def resolve_model_and_tokenizer(recipe: dict, *, qwen_assets=None, tokenizer=None, model=None, mode: str = 'smoke', require_qwen: bool = False):
    assets = Path(qwen_assets) if qwen_assets else None
    if require_qwen:
        require(assets is not None and assets.is_dir(), 'MISSING_INPUT')
    if model is not None and tokenizer is not None:
        kind = 'qwen' if assets and assets.is_dir() else 'tiny'
        identity = {
            'id': 'Qwen/Qwen2.5-1.5B-Instruct' if kind == 'qwen' else 'tiny-causal-lm',
            'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306' if kind == 'qwen' else None,
            'kind': kind,
        }
        return model, tokenizer, identity
    if assets is not None and assets.is_dir():
        return load_qwen_lora(assets, recipe)
    return load_tiny_lora(recipe)
