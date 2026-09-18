"""LoRA adapters on q_proj/v_proj. Base weights stay frozen."""
from __future__ import annotations

import hashlib
from typing import Iterable

from src.training.tiny_model import require_torch

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover
    torch = None
    nn = None


def is_adapter_param(name: str) -> bool:
    leaf = name.split('.')[-1]
    if leaf in {'A', 'B'}:
        return True
    return 'lora_A' in name or 'lora_B' in name


class LoRALinear(nn.Module if nn is not None else object):
    def __init__(self, base: nn.Module, r: int, alpha: int, dropout: float):
        super().__init__()
        self.base = base
        for parameter in self.base.parameters():
            parameter.requires_grad = False
        in_features = base.in_features
        out_features = base.out_features
        self.A = nn.Parameter(torch.empty(r, in_features))
        self.B = nn.Parameter(torch.zeros(out_features, r))
        nn.init.kaiming_uniform_(self.A, a=5 ** 0.5)
        self.scaling = alpha / r
        self.dropout = nn.Dropout(dropout) if dropout else nn.Identity()

    def forward(self, inputs):
        base = self.base(inputs)
        update = self.dropout(inputs) @ self.A.transpose(0, 1)
        update = update @ self.B.transpose(0, 1)
        return base + update * self.scaling


def inject_lora(model, *, r=8, alpha=16, dropout=0.05, targets=('q_proj', 'v_proj')):
    require_torch()
    replaced = 0
    for module_name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if child_name in targets and isinstance(child, nn.Linear):
                setattr(module, child_name, LoRALinear(child, r, alpha, dropout))
                replaced += 1
    if replaced == 0:
        raise RuntimeError('missing_runtime: no q_proj/v_proj Linear modules for LoRA')
    for name, parameter in model.named_parameters():
        parameter.requires_grad = is_adapter_param(name)
    return model, replaced


def adapter_parameters(model) -> Iterable:
    for name, parameter in model.named_parameters():
        if is_adapter_param(name):
            yield name, parameter


def frozen_base_ok(model) -> bool:
    for name, parameter in model.named_parameters():
        adapter = is_adapter_param(name)
        if adapter and not parameter.requires_grad:
            return False
        if not adapter and parameter.requires_grad:
            return False
    return True


def tensor_hash(tensors) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def adapter_hash(model) -> str:
    values = [parameter.detach() for _, parameter in adapter_parameters(model)]
    return tensor_hash(values)


def base_hash(model) -> str:
    values = [parameter.detach() for name, parameter in model.named_parameters()
              if not is_adapter_param(name)]
    return tensor_hash(values)


def adapter_state_dict(model) -> dict:
    return {name: parameter.detach().cpu().clone()
            for name, parameter in adapter_parameters(model)}
