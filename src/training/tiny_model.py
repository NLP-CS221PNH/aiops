"""Tiny causal LM with q_proj/v_proj so LoRA tests share the trainer path."""
from __future__ import annotations

import math
from typing import Any

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover
    torch = None
    nn = None
    TORCH_IMPORT_ERROR = exc
else:
    TORCH_IMPORT_ERROR = None


def require_torch() -> None:
    if torch is None:
        raise RuntimeError(f'missing_runtime: torch unavailable: {TORCH_IMPORT_ERROR}')


if torch is not None:
    class TinySelfAttention(nn.Module):
        def __init__(self, hidden: int):
            super().__init__()
            self.q_proj = nn.Linear(hidden, hidden)
            self.k_proj = nn.Linear(hidden, hidden)
            self.v_proj = nn.Linear(hidden, hidden)
            self.o_proj = nn.Linear(hidden, hidden)

        def forward(self, hidden_states):
            query = self.q_proj(hidden_states)
            key = self.k_proj(hidden_states)
            value = self.v_proj(hidden_states)
            scale = 1.0 / math.sqrt(hidden_states.size(-1))
            scores = torch.matmul(query, key.transpose(-2, -1)) * scale
            seq = hidden_states.size(1)
            causal = torch.triu(torch.ones(seq, seq, device=hidden_states.device), diagonal=1).bool()
            scores = scores.masked_fill(causal, torch.finfo(scores.dtype).min)
            weights = torch.softmax(scores, dim=-1)
            return self.o_proj(torch.matmul(weights, value))


    class TinyBlock(nn.Module):
        def __init__(self, hidden: int):
            super().__init__()
            self.attn = TinySelfAttention(hidden)
            self.norm = nn.LayerNorm(hidden)
            self.ff = nn.Sequential(
                nn.Linear(hidden, hidden * 2),
                nn.GELU(),
                nn.Linear(hidden * 2, hidden),
            )

        def forward(self, hidden_states):
            hidden_states = hidden_states + self.attn(self.norm(hidden_states))
            return hidden_states + self.ff(self.norm(hidden_states))


    class TinyCausalLM(nn.Module):
        def __init__(self, vocab_size: int = 258, hidden: int = 32, n_layers: int = 2):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, hidden)
            self.blocks = nn.ModuleList([TinyBlock(hidden) for _ in range(n_layers)])
            self.norm = nn.LayerNorm(hidden)
            self.lm_head = nn.Linear(hidden, vocab_size, bias=False)
            self.config = type('Cfg', (), {'vocab_size': vocab_size, 'hidden_size': hidden})()

        def forward(self, input_ids, attention_mask=None, labels=None):
            hidden_states = self.embed(input_ids)
            for block in self.blocks:
                hidden_states = block(hidden_states)
            logits = self.lm_head(self.norm(hidden_states))
            loss = None
            if labels is not None:
                shift_logits = logits[:, :-1].contiguous()
                shift_labels = labels[:, 1:].contiguous()
                loss = nn.functional.cross_entropy(
                    shift_logits.view(-1, shift_logits.size(-1)),
                    shift_labels.view(-1),
                    ignore_index=-100,
                )
            return type('Output', (), {'logits': logits, 'loss': loss})()
else:
    TinyCausalLM = None  # type: ignore
    TinySelfAttention = None  # type: ignore
    TinyBlock = None  # type: ignore
