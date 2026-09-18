"""Completion-only collator. Prompt and padding labels are -100."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.data.common import DataContractError, require


PAD_ID = 0
EOS_ID = 1
BYTE_OFFSET = 2


class ByteTokenizer:
    """Deterministic tokenizer used when Qwen assets are absent."""

    name = 'byte-tokenizer-v1'
    pad_token_id = PAD_ID
    eos_token_id = EOS_ID
    vocab_size = 258

    def encode(self, text: str) -> list[int]:
        return [byte + BYTE_OFFSET for byte in text.encode('utf-8')]

    def decode(self, ids: Sequence[int]) -> str:
        raw = bytes(max(0, int(item) - BYTE_OFFSET) for item in ids if int(item) >= BYTE_OFFSET)
        return raw.decode('utf-8', errors='replace')

    def apply_chat_template(self, messages: Sequence[Mapping[str, str]], tokenize=False,
                            add_generation_prompt=True) -> str:
        parts = []
        for message in messages:
            parts.append(f"<|{message['role']}|>\n{message['content']}\n")
        if add_generation_prompt:
            parts.append("<|assistant|>\n")
        return ''.join(parts)


def render_prompt(messages: Sequence[Mapping[str, str]], tokenizer: Any) -> str:
    if hasattr(tokenizer, 'apply_chat_template'):
        return tokenizer.apply_chat_template(list(messages), tokenize=False, add_generation_prompt=True)
    return ByteTokenizer().apply_chat_template(messages)


def encode_ids(tokenizer: Any, text: str) -> list[int]:
    if hasattr(tokenizer, 'encode'):
        ids = list(tokenizer.encode(text))
    else:
        ids = list(tokenizer(text, add_special_tokens=False)['input_ids'])
    return [int(item) for item in ids]


def tokenize_example(
    example: Mapping[str, Any],
    tokenizer: Any,
    *,
    max_train_tokens: int = 3072,
    prompt_cap: int = 2944,
    target_reserve: int = 128,
) -> dict[str, Any]:
    target = str(example.get('target_text') or '')
    require(target.strip(), 'TARGET_EMPTY')
    prompt = render_prompt(example['input_messages'], tokenizer)
    prompt_ids = encode_ids(tokenizer, prompt)
    target_ids = encode_ids(tokenizer, target)
    eos = int(getattr(tokenizer, 'eos_token_id', EOS_ID) or EOS_ID)
    if not target_ids or target_ids[-1] != eos:
        target_ids = target_ids + [eos]
    require(prompt_ids, 'TARGET_EMPTY')
    require(len(prompt_ids) <= prompt_cap, 'PROMPT_TOO_LONG')
    require(len(target_ids) <= target_reserve or len(prompt_ids) + len(target_ids) <= max_train_tokens,
            'TARGET_TRUNCATED')
    require(len(prompt_ids) + len(target_ids) <= max_train_tokens, 'TARGET_TRUNCATED')
    input_ids = prompt_ids + target_ids
    labels = ([-100] * len(prompt_ids)) + list(target_ids)
    attention_mask = [1] * len(input_ids)
    require(any(label != -100 for label in labels), 'TARGET_EMPTY')
    return {
        'example_id': example.get('example_id'),
        'incident_id': example.get('incident_id'),
        'input_ids': input_ids,
        'labels': labels,
        'attention_mask': attention_mask,
        'prompt_length': len(prompt_ids),
        'target_length': len(target_ids),
        'prompt_text': prompt,
        'target_text': target,
    }


def pad_batch(rows: Sequence[Mapping[str, Any]], pad_id: int = PAD_ID) -> dict[str, list[list[int]]]:
    width = max(len(row['input_ids']) for row in rows)
    input_ids, labels, masks = [], [], []
    for row in rows:
        pad = width - len(row['input_ids'])
        input_ids.append(list(row['input_ids']) + [pad_id] * pad)
        labels.append(list(row['labels']) + [-100] * pad)
        masks.append(list(row['attention_mask']) + [0] * pad)
    return {'input_ids': input_ids, 'labels': labels, 'attention_mask': masks}
