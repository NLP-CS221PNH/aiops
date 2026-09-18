"""Optional local BGE cross-encoder restricted to supplied hybrid candidates.

Model recipe: https://huggingface.co/BAAI/bge-reranker-base#usage-for-reranker
Scores are raw relevance logits, not probabilities or retrieval-quality metrics.
"""

import hashlib
import json
from pathlib import Path

from .bm25 import validate_chunks, validate_depth
from .dense import ModelUnavailableError, _load_runtime, _rows, _validate_token_options, verify_model_assets
from .fusion import validate_ranking


BGE_MODEL_ID = "BAAI/bge-reranker-base"
BGE_REVISION = "2cfc18c9415c912f9d8155881c133215df768a70"


def prepare_reranker_batch(tokenizer, query, passages, max_tokens=512, return_tensors=None):
    """Audit actual pair tokenization, including both sides and special tokens."""
    _validate_token_options(max_tokens)
    if not isinstance(query, str) or not isinstance(passages, (list, tuple)) or any(not isinstance(text, str) for text in passages):
        raise ValueError("reranker expects query text and a list or tuple of passages")
    if not passages:
        return {}, []
    queries = [query] * len(passages)
    before = tokenizer(queries, list(passages), add_special_tokens=True, padding=False,
                       truncation=False, return_special_tokens_mask=True)
    encoded = tokenizer(queries, list(passages), add_special_tokens=True, padding=True,
                        truncation="longest_first", max_length=max_tokens,
                        return_tensors=return_tensors, return_special_tokens_mask=True)
    ids_rows, masks = _rows(encoded["input_ids"]), _rows(encoded["attention_mask"])
    special_rows = _rows(encoded.pop("special_tokens_mask"))
    audits = []
    for index, model_ids in enumerate(ids_rows):
        active = [position for position, mask in enumerate(masks[index]) if mask]
        before_sequences, after_sequences = before.sequence_ids(index), encoded.sequence_ids(index)
        query_before, passage_before = before_sequences.count(0), before_sequences.count(1)
        query_after = sum(after_sequences[position] == 0 for position in active)
        passage_after = sum(after_sequences[position] == 1 for position in active)
        input_tokens, output_tokens = len(before["input_ids"][index]), len(active)
        if not 0 < output_tokens <= max_tokens or output_tokens > input_tokens:
            raise ValueError("tokenizer produced an invalid reranker pair budget")
        if not query_before or not passage_before or not query_after or not passage_after:
            raise ValueError("reranker requires nonempty query and passage tokens after pair truncation")
        after_ids = [model_ids[position] for position in active]
        audits.append({
            "kind": "query_passage_pair", "input_tokens": input_tokens, "output_tokens": output_tokens,
            "removed_tokens": input_tokens - output_tokens, "truncated": input_tokens > output_tokens,
            "query_tokens_before": query_before, "query_tokens_after": query_after,
            "passage_tokens_before": passage_before, "passage_tokens_after": passage_after,
            "special_tokens": sum(special_rows[index][position] for position in active),
            "max_tokens": max_tokens, "truncation_strategy": "longest_first",
            "token_count_kind": "actual_model_tokenizer",
            "pair_sha256": hashlib.sha256(json.dumps([query, passages[index]], ensure_ascii=False,
                                                       separators=(",", ":")).encode("utf-8")).hexdigest(),
            "token_ids_sha256": hashlib.sha256(json.dumps(after_ids, separators=(",", ":")).encode()).hexdigest(),
        })
    return encoded, audits


class BGEReranker:
    def __init__(self, model_dir, expected_assets, revision=BGE_REVISION,
                 max_tokens=512, batch_size=2, device="cpu"):
        if revision != BGE_REVISION:
            raise ValueError("BGE revision must match the pinned BAAI/bge-reranker-base revision")
        _validate_token_options(max_tokens, batch_size)
        if device != "cpu":
            raise ValueError("this baseline implements the measured CPU path; device must be cpu")
        self.asset_hashes = verify_model_assets(model_dir, expected_assets)
        self.model_dir, self.revision = str(Path(model_dir).resolve()), revision
        self.max_tokens, self.batch_size, self.device = max_tokens, batch_size, device
        self.np, self.torch, _, auto_model, auto_tokenizer = _load_runtime()
        try:
            self.tokenizer = auto_tokenizer.from_pretrained(self.model_dir, local_files_only=True,
                                                          trust_remote_code=False, use_fast=True)
            self.model = auto_model.from_pretrained(
                self.model_dir, local_files_only=True, trust_remote_code=False,
                use_safetensors="model.safetensors" in self.asset_hashes,
            ).to(device="cpu", dtype=self.torch.float32).eval()
        except (ImportError, OSError, RuntimeError) as exc:
            raise ModelUnavailableError(f"cannot load pinned BGE reranker locally: {exc}") from exc
        if not self.tokenizer.is_fast or self.model.config.num_labels != 1:
            raise ValueError("pinned BGE requires a fast tokenizer and one relevance logit per pair")

    def rerank(self, query, candidates, chunks, depth=50):
        validate_depth(depth)
        if not isinstance(query, str):
            raise ValueError("reranker query must be text")
        validate_ranking(candidates)
        if len(candidates) > 50:
            raise ValueError("reranker candidate set must be hybrid top-50 or shorter")
        registry = {chunk["chunk_id"]: chunk for chunk in validate_chunks(chunks)}
        for hit in candidates:
            if hit["chunk_id"] not in registry:
                raise ValueError("reranker candidate is missing from chunk registry")
            if registry[hit["chunk_id"]]["document_id"] != hit["document_id"]:
                raise ValueError("reranker candidate document_id disagrees with chunk registry")
        if not candidates or depth == 0:
            return [], []
        scores, audits = [], []
        for start in range(0, len(candidates), self.batch_size):
            batch = candidates[start:start + self.batch_size]
            passages = [registry[hit["chunk_id"]]["content"] for hit in batch]
            encoded, batch_audits = prepare_reranker_batch(
                self.tokenizer, query, passages, self.max_tokens, return_tensors="pt",
            )
            with self.torch.inference_mode():
                logits = self.model(**encoded, return_dict=True).logits
            if tuple(logits.shape) != (len(batch), 1):
                raise ValueError("reranker must produce exactly one relevance logit per candidate")
            values = logits[:, 0].float().cpu().numpy()
            if not self.np.isfinite(values).all():
                raise ValueError("reranker produced nonfinite scores")
            scores.extend(float(value) for value in values)
            for hit, audit in zip(batch, batch_audits):
                audits.append({"chunk_id": hit["chunk_id"], **audit})
        ordered = sorted(range(len(candidates)), key=lambda index: (-scores[index], candidates[index]["chunk_id"]))[:depth]
        hits = [{"chunk_id": candidates[index]["chunk_id"], "document_id": candidates[index]["document_id"],
                 "rank": rank, "score": scores[index]} for rank, index in enumerate(ordered, 1)]
        return hits, audits
