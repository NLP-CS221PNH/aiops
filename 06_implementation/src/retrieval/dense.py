"""Pinned local E5 encoding and exact cosine search; importing needs no ML runtime.

Model recipe: https://huggingface.co/intfloat/e5-small-v2
Weights/tokenizer assets must be provisioned explicitly; this module never downloads.
"""

import hashlib
import json
from pathlib import Path
import re

from .bm25 import validate_chunks, validate_depth


E5_MODEL_ID = "intfloat/e5-small-v2"
E5_REVISION = "ffb93f3bd4047442299a41ebb6fa998a38507c52"


class ModelUnavailableError(ValueError):
    """Pinned local assets or optional model runtime are unavailable."""


def verify_model_assets(model_dir, expected_assets):
    """Hash every declared file and refuse untracked files the loader could consume."""
    if model_dir is None or not isinstance(model_dir, (str, Path)):
        raise ModelUnavailableError("missing local model directory; provision pinned assets explicitly")
    directory = Path(model_dir).resolve()
    if not directory.is_dir():
        raise ModelUnavailableError("missing local model directory; provision pinned assets explicitly")
    if not isinstance(expected_assets, dict) or not expected_assets:
        raise ModelUnavailableError("missing expected model asset SHA256 manifest")
    verified = {}
    for name, expected in expected_assets.items():
        if not isinstance(name, str) or not name or "\\" in name:
            raise ValueError("model asset names must be nonempty relative POSIX paths")
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or ":" in name:
            raise ValueError("model asset path must stay within the model directory")
        asset = (directory / relative).resolve()
        if not asset.is_relative_to(directory):
            raise ValueError("model asset path escapes the model directory")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ValueError("model asset SHA256 must be 64 hexadecimal characters")
        if not asset.is_file():
            raise ModelUnavailableError(f"missing pinned model asset: {name}")
        digest = hashlib.sha256()
        with asset.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected.lower():
            raise ValueError(f"model asset SHA256 mismatch: {name}")
        verified[name] = digest.hexdigest()
    required = {"config.json", "tokenizer_config.json", "tokenizer.json"}
    if not required.issubset(verified):
        raise ModelUnavailableError("model asset manifest must pin config.json, tokenizer_config.json and tokenizer.json")
    if "model.safetensors" not in verified and "pytorch_model.bin" not in verified:
        raise ModelUnavailableError("missing pinned model weights (model.safetensors or pytorch_model.bin)")
    # Both pinned models have a single weight file. Sharded/adapted alternatives are
    # deliberately not selected by the loader under the same revision identity.
    if (directory / "adapter_config.json").exists():
        raise ValueError("adapter models are outside the pinned retrieval contract")
    relevant = {"config.json", "tokenizer_config.json", "tokenizer.json", "special_tokens_map.json",
                "added_tokens.json", "vocab.txt", "vocab.json", "merges.txt", "sentencepiece.bpe.model",
                "spiece.model", "model.safetensors", "pytorch_model.bin"}
    for name in relevant:
        if (directory / name).exists() and name not in verified:
            raise ValueError(f"untracked model or tokenizer asset: {name}")
    return verified


def _validate_token_options(max_tokens, batch_size=None):
    if type(max_tokens) is not int or not 4 <= max_tokens <= 512:
        raise ValueError("max_tokens must be an integer between 4 and 512")
    if batch_size is not None and (type(batch_size) is not int or batch_size <= 0):
        raise ValueError("batch_size must be a positive integer")


def _rows(value):
    return value.tolist() if hasattr(value, "tolist") else value


def prepare_e5_batch(tokenizer, texts, kind="query", max_tokens=512,
                     query_prefix="query: ", passage_prefix="passage: ", return_tensors=None):
    """Tokenize once for the model and report true prefix/special/truncation counts.

    The tokenizer must implement Hugging Face's fast tokenizer call protocol.
    This helper does not load model weights, so real-tokenizer fixtures can use it.
    """
    _validate_token_options(max_tokens)
    if kind not in ("query", "passage"):
        raise ValueError("encoding kind must be query or passage")
    if not isinstance(texts, (list, tuple)) or any(not isinstance(text, str) for text in texts):
        raise ValueError("texts must be a list or tuple of strings")
    if not isinstance(query_prefix, str) or not isinstance(passage_prefix, str):
        raise ValueError("E5 prefixes must be strings")
    if not texts:
        return {}, []
    prefix = query_prefix if kind == "query" else passage_prefix
    inputs = [prefix + text for text in texts]
    before = tokenizer(inputs, add_special_tokens=True, padding=False, truncation=False,
                       return_special_tokens_mask=True, return_offsets_mapping=True)
    encoded = tokenizer(inputs, add_special_tokens=True, padding=True, truncation=True,
                        max_length=max_tokens, return_tensors=return_tensors,
                        return_special_tokens_mask=True, return_offsets_mapping=True)
    ids_rows = _rows(encoded["input_ids"])
    masks = _rows(encoded["attention_mask"])
    special_rows = _rows(encoded.pop("special_tokens_mask"))
    offset_rows = _rows(encoded.pop("offset_mapping"))
    audits = []
    for index, model_ids in enumerate(ids_rows):
        active = [position for position, mask in enumerate(masks[index]) if mask]
        before_ids = before["input_ids"][index]
        after_ids = [model_ids[position] for position in active]
        input_tokens, output_tokens = len(before_ids), len(after_ids)
        if not 0 < output_tokens <= max_tokens or output_tokens > input_tokens:
            raise ValueError("tokenizer produced an invalid E5 token budget")
        before_special = before["special_tokens_mask"][index]
        before_offsets = before["offset_mapping"][index]
        prefix_tokens = sum(not special and end > start and start < len(prefix)
                            for special, (start, end) in zip(before_special, before_offsets))
        body_before = sum(not special and end > len(prefix)
                          for special, (start, end) in zip(before_special, before_offsets))
        body_after = sum(not special_rows[index][position] and offset_rows[index][position][1] > len(prefix)
                         for position in active)
        if body_before and not body_after:
            raise ValueError("E5 truncation removed the entire text after the prefix")
        audits.append({
            "kind": kind, "input_tokens": input_tokens, "output_tokens": output_tokens,
            "removed_tokens": input_tokens - output_tokens, "truncated": input_tokens > output_tokens,
            "prefix_tokens": prefix_tokens, "special_tokens": sum(special_rows[index][position] for position in active),
            "body_tokens_before": body_before, "body_tokens_after": body_after,
            "max_tokens": max_tokens, "token_count_kind": "actual_model_tokenizer",
            "input_sha256": hashlib.sha256(inputs[index].encode("utf-8")).hexdigest(),
            "token_ids_sha256": hashlib.sha256(json.dumps(after_ids, separators=(",", ":")).encode()).hexdigest(),
        })
    return encoded, audits


def _load_runtime():
    try:
        import site
        import sys
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.append(user_site)
        import numpy as np
        import torch
        from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
    except (ImportError, OSError) as exc:
        raise ModelUnavailableError(f"optional local model runtime unavailable: {exc}") from exc
    return np, torch, AutoModel, AutoModelForSequenceClassification, AutoTokenizer


class E5Encoder:
    def __init__(self, model_dir, expected_assets, revision=E5_REVISION,
                 max_tokens=512, batch_size=2, device="cpu",
                 query_prefix="query: ", passage_prefix="passage: "):
        if revision != E5_REVISION:
            raise ValueError("E5 revision must match the pinned intfloat/e5-small-v2 revision")
        _validate_token_options(max_tokens, batch_size)
        if not isinstance(query_prefix, str) or not isinstance(passage_prefix, str):
            raise ValueError("E5 prefixes must be strings")
        if device != "cpu":
            raise ValueError("this baseline implements the measured CPU path; device must be cpu")
        self.asset_hashes = verify_model_assets(model_dir, expected_assets)
        self.model_dir, self.revision = str(Path(model_dir).resolve()), revision
        self.max_tokens, self.batch_size, self.device = max_tokens, batch_size, device
        self.query_prefix, self.passage_prefix = query_prefix, passage_prefix
        self.np, self.torch, auto_model, _, auto_tokenizer = _load_runtime()
        try:
            self.tokenizer = auto_tokenizer.from_pretrained(self.model_dir, local_files_only=True,
                                                          trust_remote_code=False, use_fast=True)
            self.model = auto_model.from_pretrained(
                self.model_dir, local_files_only=True, trust_remote_code=False,
                use_safetensors="model.safetensors" in self.asset_hashes,
            ).to(device="cpu", dtype=self.torch.float32).eval()
        except (ImportError, OSError, RuntimeError) as exc:
            raise ModelUnavailableError(f"cannot load pinned E5 model locally: {exc}") from exc
        if not self.tokenizer.is_fast or self.model.config.hidden_size != 384:
            raise ValueError("pinned E5 requires a fast tokenizer and 384-dimensional embeddings")
        self.dimension = 384

    def encode(self, texts, kind="query"):
        if kind not in ("query", "passage") or not isinstance(texts, (list, tuple)) or any(not isinstance(text, str) for text in texts):
            raise ValueError("encode expects string texts and kind query or passage")
        if not texts:
            return self.np.empty((0, self.dimension), dtype=self.np.float32), []
        vectors, audits = [], []
        for start in range(0, len(texts), self.batch_size):
            encoded, batch_audits = prepare_e5_batch(
                self.tokenizer, texts[start:start + self.batch_size], kind, self.max_tokens,
                self.query_prefix, self.passage_prefix, return_tensors="pt",
            )
            with self.torch.inference_mode():
                output = self.model(**encoded)
                mask = encoded["attention_mask"].bool().unsqueeze(-1)
                hidden = output.last_hidden_state.masked_fill(~mask, 0.0)
                means = hidden.sum(dim=1) / mask.sum(dim=1)
            matrix = normalized_matrix(means.float().cpu().numpy(), expected_rows=len(batch_audits))
            if matrix.shape[1] != self.dimension:
                raise ValueError("E5 produced an unexpected embedding dimension")
            vectors.append(matrix)
            audits.extend(batch_audits)
        return self.np.concatenate(vectors, axis=0), audits


def normalized_matrix(values, expected_rows=None):
    """Validate numeric, finite, nonzero rows and normalize without overflow."""
    try:
        import numpy as np
    except ImportError as exc:
        raise ModelUnavailableError("dense search requires numpy") from exc
    try:
        matrix = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError("embeddings must be a rectangular numeric matrix") from exc
    if matrix.ndim != 2 or matrix.shape[1] < 1 or matrix.dtype.kind not in "iuf":
        raise ValueError("embeddings must be a two-dimensional numeric matrix with positive dimension")
    if expected_rows is not None and matrix.shape[0] != expected_rows:
        raise ValueError("embedding row count does not match chunk registry")
    matrix = matrix.astype(np.float64)
    if not np.isfinite(matrix).all():
        raise ValueError("embedding values must be finite")
    if not len(matrix):
        return matrix.astype(np.float32)
    scale = np.max(np.abs(matrix), axis=1, keepdims=True)
    if (scale == 0).any():
        raise ValueError("embedding vectors must have nonzero norm")
    matrix /= scale
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix.astype(np.float32)


class DenseIndex:
    def __init__(self, chunks, embeddings):
        self.chunks = validate_chunks(chunks, require_content=False)
        # An empty plain list has no dimension to infer. Keep that state explicit;
        # an empty matrix with a declared second dimension is validated normally.
        if not self.chunks and isinstance(embeddings, (list, tuple)) and not embeddings:
            self.embeddings, self.dimension = None, None
            return
        self.embeddings = normalized_matrix(embeddings, expected_rows=len(self.chunks))
        self.dimension = self.embeddings.shape[1]

    def search(self, query_vector, depth=50):
        import numpy as np
        validate_depth(depth)
        try:
            vector = np.asarray(query_vector)
        except (TypeError, ValueError) as exc:
            raise ValueError("query vector must contain numeric values") from exc
        if vector.ndim != 1 or not vector.shape[0] or (self.dimension is not None and vector.shape[0] != self.dimension):
            raise ValueError("query vector dimension does not match the dense index")
        normalized = normalized_matrix(vector.reshape(1, -1))[0]
        if self.embeddings is None:
            return []
        scores = self.embeddings @ normalized
        if not np.isfinite(scores).all():
            raise ValueError("dense search produced nonfinite scores")
        ordered = sorted(range(len(self.chunks)), key=lambda index: (-float(scores[index]), self.chunks[index]["chunk_id"]))[:depth]
        return [{"chunk_id": self.chunks[index]["chunk_id"], "document_id": self.chunks[index]["document_id"],
                 "rank": rank, "score": float(scores[index])} for rank, index in enumerate(ordered, 1)]
