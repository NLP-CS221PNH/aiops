# Representation candidate decisions

Date: 2026-09-13. Scope: `04.variants`, local deterministic tooling and train/dev candidate artifacts. These decisions implement the accepted plan without using qrels, dev scores, test telemetry content, an LLM summary, or translation. Codex authored the implementation/specification; A/B/C human reviews remain pending.

The exact machine authority is `configs/representation.yaml`; the generated query manifest binds its hash and the implementation/tokenizer/input hashes. The source evidence and prerequisite distinction are recorded in `representation-source-audit.md`. Plan 02's local technical gate is validated; its full human/consumer gate remains pending. The current explicit `--auto` request authorizes this local work, as recorded in `configs/representation-execution-authorization.json`, without changing upstream receipts or authorizing external sharing/experiments.

## Candidate selection

Use only `data/inference` observations and exported evidence. The manager supplies 72 opaque train/dev IDs; family/split administration stays in its separate workflow. A typed `SafeIncident` validates allowlisted fields, the exact retrospective half-open window policy, incident joins, reference coverage, transform/redaction versions and evidence uniqueness. Unexpected private fields are rejected at that boundary; manager metadata is never a selection feature.

`service-round-robin-v1` groups logs by observed service, orders each group by ascending UTC timestamp and evidence ID, and visits services in lexical order one evidence at a time. Keep at most two logs per service and 24 per incident. Record empty-text, service-quota and incident-quota drops. Do not reapply an error filter or numeric dedup. These initial conservative quotas are fixed candidates, not an optimization result from the six audit cases. Round-robin selection addresses the observed legacy first-eight service ordering loss; it does not prove relevance or quality.

Metrics are ordered by descending descriptive change score, with null scores last and metric name/evidence ID as ties. Traces use service round-robin with ascending UTC timestamp/evidence ID inside each service. R3 initially considers at most two metrics and two traces. Every safe evidence record outside these enrichment quotas remains accounted for as `modality_quota`; upstream discarded raw rows have no recoverable ledger and stay unknown.

## Rendering and source spans

| Variant | Text | Preserved contract |
|---|---|---|
| R1 | Selected exported redacted log literals with English service/time scaffold | Full retained source strings, exact window, evidence provenance |
| R2 | R1 logs with each whitespace run replaced by one space | Every non-whitespace Unicode code point, same retained IDs and full source spans as R1 |
| R3 | Normalized retained logs plus descriptive metrics and neutral trace facts | Same incident/window; intentional, separately recorded modality enrichment |

R2 is `whitespace-only-v1`: it does not strip timestamps, replace numbers, translate, infer aliases, or rewrite exceptions. Whitespace normalization includes leading/trailing runs and records segment maps from source to normalized offsets. Offsets use Unicode code points in the **safe redacted export**, not offsets in unredacted telemetry. Technical literals such as service names, HTTP 500/503, versions, ports and Unicode exceptions remain unchanged.

Every query is explicitly synthetic while the source telemetry synthetic flag is preserved. Preserve unknown metric/duration units and raw nullable numeric trace status. Nonzero status does not imply an error; change score is not a causal score. Missing or omitted modalities have explicit markers distinguishing absent safe evidence from selection/budget loss. `frontend` and `frontendservice` remain separate observed names.

## Actual tokenizer and clipping

Use the locally pinned `intfloat/e5-small-v2` tokenizer, revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`, with the four asset hashes in the config and `tokenizers` 0.21.4. Query counting includes `query: ` and two special tokens. The limit is 512 actual tokens; implicit truncation and padding are disabled. Character estimates are not acceptance evidence.

`whole-block-joint-v1` considers logs in the shared selector order. A log is retained only when **both R1 and R2** fit the limit with it. When a block fails, record a joint token-budget drop and continue trying later blocks. No partial source slice is produced. This deliberately chooses the accepted plan's explicit insufficient-evidence fallback instead of partial clipping: a single oversized log can be dropped, its reason remains visible, and an empty result has `insufficient_evidence` status. A scaffold that cannot fit raises an explicit budget failure.

R2's freed space stays unused for adding evidence. R1/R2 always share retained IDs and complete underlying source spans after budgeting. Their normalization maps explain only text normalization. A dense encoder adds its required prefix, while the same pre-budgeted `query_text` is given to every retriever; consumers must not pass a fuller BM25 query or silently retokenize/truncate the dense query.

R3 budgets the first metric, first trace, common retained logs, then the remaining metric/trace candidates. A candidate that does not fit gets `r3_token_budget`; all counts include its current missing-information scaffold. R3 can retain fewer common logs because enrichment intentionally consumes its own 512-token budget. This is documented modality variation, not a claim that R3 preserves the R1/R2 log ablation.

## Common generator observations

The observation bundle is generated once per incident independently of retrieval representation/condition. It considers the selector's logs, up to six descriptive metrics, and four trace facts, interleaving candidate modalities in log/metric/trace order before whole-block budgeting. It renders evidence IDs for citations and records complete spans, missing information, all quota/budget drops, and a content hash.

The candidate bundle has a separate 2,048-token **E5 planning budget**, with special tokens but no query prefix. This is not proof of fit for an actual generator tokenizer or its knowledge-context/prompt budget. Plan 07 must retokenize the same bundle using its actual generator and, if clipping is required, apply one common policy across G0/GB/GD/GH (and any supported extra condition), recording a new common context version. It must not vary observations with retriever success or independently choose raw telemetry.

## Downstream and change boundaries

`R2` is the default pilot candidate only; `selected_winner=null`. Plan 05 can consume validated candidate interfaces for its future runner work. Plan 08 compares R1/R2/R3 on the 18 dev incidents with a common reference retriever/corpus and plan-06 judged union candidates; unjudged candidates are not automatic grade zero. Plan 04 reports no retrieval/generation score and no winner.

Plan 08 owns F1 and later test materialization using the same frozen functions. Current train/dev outputs exclude all 18 test IDs. An F1 hash string alone is not a permission to generate test queries; a consumer must validate the full applicable freeze contract. Keep test artifacts in a separate versioned location and never append to F1-bound train/dev files.

Changing selector, normalization, budget, schema, tokenizer, code, or safe input invalidates the bound candidate receipt and affected rankings/pool receipts. Rebuild versioned artifacts and notify consumers. Query-only rendering changes do not automatically invalidate incident-centered relevance judgments if task/window/evidence/applicability are unchanged, but newly pooled candidates need judgment. Changed task/window/evidence/applicability requires review of affected labels. Human payload/sharing approval, scientific-quality claims, final generator budget proof, and dev/F1 decisions remain outside this automated local completion.
