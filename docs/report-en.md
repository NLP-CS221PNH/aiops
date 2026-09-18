# Service localization with Hybrid RAG and G1 LoRA on RCAEval RE2-Online Boutique

**Source version:** METH-LOCK-KAGGLE-20260918 overlay  
**Date:** 2026-09-18  
**Timezone:** Asia/Saigon  
**Deadline:** 2026-09-30T12:00:00+07:00

## Cover

- Nguyễn Văn Nam — 24521120
- Nguyễn Đình Phát — 23521144
- Lê Vũ Thiêm Hoàng — 25520584
- Bùi Đặng Nhật Nguyên — 23521037

This delivery is a LoRA fine-tuning source pack and two Word reports. No university, faculty, or advisor names are invented.

## Abstract

The task is **service localization** on RCAEval RE2-Online Boutique: 90 incidents, 30 families, a family-isolated 54/18/18 split. The design keeps Hybrid RAG (BM25, pretrained E5, RRF) and adds one LoRA generator, Qwen2.5-1.5B-Instruct, trained on G1 with R2 and no RAG. E5 is not trained. A full Kaggle experiment is left to the user after delivery. Empirical results are not filled in this version.

## 1. Introduction and research questions

Online Boutique microservices emit logs, metrics, and traces. The task ranks the originating service under G1; it is not full causal proof. Retrieval uses a knowledge corpus. Generation uses R2 observations with or without knowledge passages.

- RQ-IR: IR-H (RRF) versus the stronger single retriever on dev, using nDCG@5, MRR@10, and coverage.
- RQ-LOC: localization Top-1/Top-3 and grounding (claims/citations) under G0/GB/GD/GH.
- RQ-LORA: before/after G1 LoRA on the same prompts, contexts, and decoding.

Boundaries: the test set may have prior exposure (retrospective); sample size is small; the eligible corpus may be empty while deployment versions stay unknown.

## 2. Background and related work

BM25 [P-BM25] is the lexical baseline. E5-small-v2 [P-E5] is the pretrained dense encoder pinned at `intfloat/e5-small-v2@ffb93f3bd4047442299a41ebb6fa998a38507c52`. Reciprocal Rank Fusion [P-RRF] uses c=60. RAG [P-RAG] inserts passages into the prompt. LoRA [P-LORA] is the adaptation method; the recipe is r=8, alpha=16, dropout=0.05, targets `q_proj,v_proj`. Qwen2.5-1.5B-Instruct [P-QWEN25] is pinned at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. RCAEval [P-RCAEVAL] supplies RE2-OB. Service localization is not causal proof: G1 is a service label, not a mechanism certificate.

## 3. Dataset and preprocessing

Source: RCAEval-RE2-OB, revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. Counts: 90 incidents, 30 families, 54/18/18. Safe observations live in `data/inference/`. G1 private partitions are disjoint gitignored train/dev/test roots (hashes not published on the public tip). The trainer joins 54 train incidents by id and does not serialize `source_case`, family, `fault_description`, `injection_time`, or gold wording. Service names inside telemetry remain valid evidence. The 18 test incidents never enter prepare/train. Local reconstruction of gold stays off the public tree; see `docs/publication.md`.

## 4. Architecture and training

```
safe observations -> R2 render -> (optional) IR-B/D/H top-5
        |                              |
        +-----> local Qwen prompt <----+
        |
G1 sidecar (train only) -> completion loss / LoRA adapter
```

Each train incident yields one G0-style R2 no-RAG example. The target JSON is `{"candidate_causes":[{"service_id":"<G1>"}]}`. Loss is token cross-entropy on target+EOS with prompt/pad labels -100. Train sequence 3072, prompt cap 2944, target reserve 128, R2 observations 2048 Qwen tokens. Microbatch 1, accumulation 8, AdamW lr=1e-4, linear warmup 0.1, at most 3 epochs, seed 221. Checkpoints select lowest dev masked loss. Smoke uses 2 optimizer steps under `runs/training/smoke`; research runs use `runs/training/research`. Resume stores optimizer, scheduler, RNG, and trainer_state. Export writes adapter safetensors; smoke_only adapters are not research freezes. Inference is local with `local_files_only=True` and no model API.

## 5. Evaluation

Matrix: IR-B/D/H; generation base×LoRA × G0/GB/GD/GH (8×18 by design). Controls G-oracle/G-random are excluded from training and selection. G1 is localization; G2 is passage relevance; G3 scores claim support against packed text. Local judging uses provenance `local-model-automated-v1` with raw receipts; `llm_lexical_proxy` is not a headline gold. Invalid/error/abstain count as incorrect on the full 18-incident denominator. nDCG uses gain `2^rel-1` and discount `log2(rank+1)`. Family bootstrap uses 1000 resamples, seed 221, and 6 test families. New F1/F2 files go to an explicit output root; historical `freezes/F1.json` and `F2.json` stay immutable.

## 6. Reproducibility

Notebook `notebooks/03_kaggle_train.ipynb` runs setup → roots → deps → data-only preflight → GPU receipt → 2-step smoke when assets exist → full train disabled → resume/export. Commands: `python -m src.training preflight --data-only`; `python -m src.training train --mode smoke --max-steps 2`. Linux install, Kaggle execution, and full training are separate status flags. Windows clean extraction must still pass data-only preflight.

## 7. Limitations and AI disclosure

54 training incidents, missing classes, 6 test families, no G3 supervision, unknown deployment subset, retrospective test exposure, and same-family Qwen judging (self-preference). AI tools helped write source code. Method decisions and the choice to leave metrics blank belong to the team.

## 8. Empirical results

Empirical results are not filled in this version.

### Table T1. Retrieval

| method | nDCG@5 | MRR@10 | coverage |
|---|---|---|---|
| IR-B |  |  |  |
| IR-D |  |  |  |
| IR-H |  |  |  |

### Table T2. Generation Top-k

| row | Top-1 | Top-3 | invalid | error | abstain | coverage |
|---|---|---|---|---|---|---|
| base×G0 |  |  |  |  |  |  |
| base×GB |  |  |  |  |  |  |
| base×GD |  |  |  |  |  |  |
| base×GH |  |  |  |  |  |  |
| lora×G0 |  |  |  |  |  |  |
| lora×GB |  |  |  |  |  |  |
| lora×GD |  |  |  |  |  |  |
| lora×GH |  |  |  |  |  |  |

### Table T3. Claim support

| metric | value |
|---|---|
| claim-support |  |
| citation |  |
| zero-claim-coverage |  |

### Table T4. Controls and family uncertainty

| metric | value |
|---|---|
| control |  |
| paired-family-delta |  |
| uncertainty |  |

### Table T5. Runtime

| metric | value |
|---|---|
| latency |  |
| tokens |  |
| peak-memory |  |

Error analysis stays blank with the numeric cells.

## 9. Design conclusion

The source pack includes a LoRA trainer, data/split boundaries, a local provider, v2 judging, and two reports with blank results. Empirical questions wait for a user Kaggle train/eval. No percentage improvement is claimed.

## References

- [P-RAG] Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. https://arxiv.org/abs/2005.11401
- [P-LORA] Hu et al. (2022). LoRA. https://arxiv.org/abs/2106.09685
- [P-E5] Wang et al. (2022). Text Embeddings by Weakly-Supervised Contrastive Pre-training. https://arxiv.org/abs/2212.03533
- [P-BM25] Robertson & Zaragoza (2009). The Probabilistic Relevance Framework. https://doi.org/10.1561/1500000019
- [P-RRF] Cormack et al. (2009). Reciprocal Rank Fusion. https://doi.org/10.1145/1571941.1572114
- [P-RCAEVAL] Pham et al. (2025). RCAEval. https://arxiv.org/html/2501.11735v3
- [P-QWEN25] Qwen Team (2025). Qwen2.5 Technical Report. https://arxiv.org/abs/2412.15115
- [P-PEFT] Mangrulkar et al. (2022). PEFT. https://github.com/huggingface/peft
