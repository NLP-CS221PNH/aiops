# Methodology lock (authoritative knob table)

Lock id: `METH-LOCK-20260917`  
SHA-256: `f4453cdbf4388b131c9426efe368dbba8a9681c5e59e4b17dd963f0c96e12adb`  
Source file: `configs/methodology-lock.yaml`

Every retrieval/generation comparison uses these copied values. Changing a value requires a new lock id. F1 hashes are not overwritten.

## Frozen knobs

| Knob | Value | Source |
|---|---|---|
| Dense model | `intfloat/e5-small-v2` @ `ffb93f3bd4047442299a41ebb6fa998a38507c52` | `configs/retrieval.yaml` |
| Tokenizer | `vendor/e5-small-v2/tokenizer.json` sha256 `d241a60d…`; tokenizers `0.21.4` | `configs/representation.yaml` |
| Embedding | L2 normalize, prefixes `query: ` / `passage: ` | `configs/retrieval.yaml` |
| BM25 | k1=**1.2**, b=0.75 | `configs/retrieval.yaml` |
| Depth / RRF | 50; c=60; weights 1:1 | `configs/retrieval.yaml` |
| Rerank | disabled | `configs/retrieval.yaml` |
| Context | top-5 chunks; obs 2048 / knowledge 4096 / output 768 | `protocol.yaml`, `generation.yaml` |
| Generator | `deepseek` / `deepseek-flash`; thinking disabled; `json_object` | `configs/generation.yaml` |
| Decoding | temperature **0.1** | `configs/generation.yaml` |
| Representation | R2 | `configs/retrieval.yaml` |
| Primary IR | `passage_ndcg_5`; tie-break BM25 | `evaluation.yaml`, `F1.json` |
| Conditions | IR-B, IR-D, IR-H, G0, GB, GD, GH | `F1.json` |
| Qrels | `llm_judge_adjudicated` (on-disk `llm_lexical_proxy`); **not human gold** | lock + protocol |
| Device | CPU float32 | `configs/retrieval.yaml` |
| Bootstrap | family cluster, seed 221, 1000 resamples | `protocol.yaml` |

Reports that cite k1=1.5 or T=0.0 without calling those figures defects are wrong. Winning source is this lock.

## Deferred (not missing failures)

- IR-R / BGE reranker
- GraphRAG
- multi-agent
- iterative retrieval
- R1/R2/R3 test-set selection
- runbook-only vs history-only corpus grid
- second generator
- Train Ticket
- full human re-annotation
