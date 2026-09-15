# Plan05 progress: retrieval tooling and deferred pilot

Date: 2026-09-13. Scope follows the user's clarification: **build and test the runners now; wait for a reviewed corpus before the real pilot**. The current technical delivery is separate from full `05.runners` acceptance. Plan05 remains in progress; no human role or pilot requirement is fulfilled by an agent signature or synthetic output.

The authorized technical slice is complete. The final independent tester passed **269 full-suite tests, including 66 retrieval tests**, with zero failures, errors, or skips; source/config/schema/retrieval-test hashes stayed unchanged during the run. See [test report](retrieval-tests.md) and its [machine receipt](retrieval-tests.json). Synthetic reproducibility independently passed 15 CLI command expectations, 28 current artifact hashes, four manifest reader validations, and notebook execution through the same CLI; see [reproducibility receipt](retrieval-reproducibility.json) and [pilot audit](retrieval-pilot-audit.md). These are technical checks of the available implementation and explicit failure behavior, not real E5/BGE forward passes or embedding-cache performance.

The [execution contract](retrieval-goal-contract.md), [input audit](retrieval-input-audit.md), [detailed debugger audit](retrieval-debugger-preflight.md), [dependency receipt](retrieval-dependency-provisioning.json), and [runbook](../docs/retrieval-runbook.md) define the scope and limitations. The [independent code review](retrieval-code-review.md) passes the technical scope at 9.3/10 with zero remaining material findings; its deferred model/pilot/owner limits are retained. The [machine handoff](retrieval-handoff.json) records `technical_delivery_complete_pilot_pending` and `milestone_accepted: false`. No agent review substitutes for human A/B/C or consumer approval.

## All-phase mapping

| Plan item | Implemented or prepared | Remaining condition for the original plan item |
|---|---|---|
| 05.01 Input audit | Read-only hash/schema/field audit; explicit text projection, upstream identity distinctions, release and private-data boundaries. | Human owner review remains pending. |
| 05.02 Schema/config | Strict retrieval config, ranking/manifest schema, explicit error/count/provenance fields and validating consumer reader. | Consumer owners must accept the contract for actual pilot handoff. |
| 05.03 Independent fixtures | Hand-calculated BM25/RRF values and explanations; synthetic exact-vector, tie, empty, duplicate, finite-value and real E5 tokenizer budget checks pass. | Human B may review the fixture assertions; no real neural inference is claimed. |
| 05.04 Contract/resource review | CPU path specified; local dependency lock and explicit missing-model feasibility. | A/B/C human acceptance, reviewed corpus release, pinned PyTorch/Transformers and weights. |
| 05.05 BM25 runner | Canonical-content BM25, technical tokenizer, deterministic accumulation/order, configurable k1/b/depth, empty rankings. | Actual reviewed-corpus pilot sanity rankings and B acceptance. |
| 05.06 E5/cache | Pinned local E5 adapter, true tokenizer audits, exact normalized-cosine index, asset verification, fingerprinted cache. | Real E5 weight/backend provisioning and measured encoding/cache runs; synthetic vectors are not E5 evidence. |
| 05.07 Fusion/reranker | RRF and bounded optional BGE adapter; missing-model state is explicit. | Real hybrid pilot; actual BGE tokenizer/model feasibility if requested. Plan08 owns final inclusion. |
| 05.08 Pilot/checkpoint | Atomic records/index/manifest, every incident-condition represented, strict resume fingerprint, isolated run directories. | 5-train smoke, selected 20-train pilot and dev rankings after release; no actual pilot started. |
| 05.09 Manager bundle | Provenance/count/schema interfaces and top-10/top-5 designations are implemented. | Actual rankings and runtime/resource summary for 06 pooling. |
| 05.10 Technical tests | Final independent receipt: 66 retrieval checks and 269 full-suite checks pass, zero failures/errors/skips; current artifact hashes recorded. | Actual model forward passes remain unperformed; human B acceptance remains separate. |
| 05.11 Input/split boundary | Fail-closed released-corpus requirement, allowed paths, private-field rejection, authenticated F1/test-input gates; technical rejection tests pass. | A human review and any later pilot-specific audit; Plan08 acceptance of the proposed frozen handshake. |
| 05.12 Rerun/resume/consumer | Synthetic interruption/resume/tamper cases and validating readers. | Real train-pilot warm/cold/restart evidence plus 06/07 confirmation. |
| 05.13 Handoff | CLI/notebook interfaces, runbook and technical handoff artifacts. | Actual pilot rankings/provenance and B/A/C plus 06/07/08 acceptance. Full `05.runners` remains pending. |

## Original success criteria

The original checkboxes intentionally cover the full plan, including release, real pilot, and human acceptance. They will not be bulk-checked for the smaller technical delivery.

| Phase / criterion | Technical slice status | Full-plan status |
|---|---|---|
| 1.1 Contract receipt with A/B/C scopes | Automated technical review can record its own scope. | Pending actual A/B/C review. |
| 1.2 Fixtures/schema cover three required conditions | BM25/RRF/synthetic dense fixtures and schema pass technical checks. | Fulfilled for fixture/schema scope. |
| 1.3 Proposed versus existing paths explicit | Input audit and runbook distinguish current files from absent model/pilot artifacts. | Fulfilled in the technical documentation. |
| 1.4 No quality metrics or test access | Current scope excludes them; source/guard checks confirm the boundary. | Preserved. |
| 2.1 BM25/dense/hybrid run same inputs with complete manifests | Tooling and failure manifests are available. | Pending real dense/hybrid pilot. |
| 2.2 Cache/resume/truncation checked on pilot | Synthetic checks only. | Pending actual pilot and model runtime. |
| 2.3 06 rankings and 07 hits schema | Reader/schema prepared. | Pending actual rankings and owner receipt. |
| 2.4 IR-R feasibility explicit; Plan08 final inclusion | Missing weights/tokenizer/backend documented. | Feasibility state is explicit; inclusion remains with Plan08. |
| 2.5 No quality scores before human qrels | No quality evaluation is performed. | Preserved. |
| 3.1 Required technical tests/receipts current | 66 retrieval and 269 full-suite tests pass; receipts bind current artifacts. | Fulfilled for the authorized technical slice; real neural/pilot verification remains separate. |
| 3.2 Pilot rerun/restart proven | Synthetic restart is a tooling check. | Pending real pilot. |
| 3.3 Consumers accept 05.runners | Contract prepared for review. | Pending actual owners. |
| 3.4 Plan05 complete independent of full 06/08 | Plan05 does not require their full completion. | Plan05 itself remains incomplete. |
| 3.5 No winner/final config/test metrics selected here | Configuration is a pinned candidate baseline. | Preserved. |

## Blockers and owners

| Blocker / deferred work | Owner and next evidence |
|---|---|
| Corpus release | A/B: reviewed applicability/release receipt and nonempty eligible whitelist. The current 440 candidate chunks are not released. |
| Neural execution | B/C: verified pinned E5 weights, tokenizer asset manifest, pinned PyTorch/Transformers environment, then measured CPU smoke. No backend or weight download occurred for this slice. |
| Pilot membership | Controller/06: opaque train/dev allowlists bound to the current query manifest, after the release gate. Runner must not read private split metadata. |
| Real pilot/handoff | B/C and 06/07: real rankings, warm/cold/restart receipts, provenance and reader acceptance. |
| Frozen handshake / test | Plan08: accept the proposed contract, supply independently trusted F1 and post-F1 test-input receipts, select final configuration, and own test execution. |

## Plan synchronization method

The explicit indexed target is `CS221_AIOps_RAG_Research_Pack/260913-0206-6`, corresponding to `plans/260913-0057-cs221-05-retrieval-baselines`. `ak plan use` cannot set a worktree pointer because this workspace has no Git repository. Project-level `ak plan resolve` matches multiple plans, so it is not used to select a mutation target.

Live `ak plan check` can only check all boxes in a phase. `ak plan phase update --status` is rejected as file-owned, and the installed CLI has no per-item checkbox mutation. No phase meets all original criteria, so no bulk check is valid. Completed sync preserved all 14 phase checkboxes, appended durable evidence notes across all three phase files and the main plan, reindexed with `ak plan reindex --apply`, updated all three index notes/evidence through `ak plan phase update`, and set only the overall plan to `in-progress` through `ak plan update`. `ak plan validate` returned valid; `ak plan status` confirmed `in-progress`, 0/3 complete phases, and 0/14 checked items. Raw CLI checklist progress describes its coarse full-phase bookkeeping, not zero implementation progress. No phase or full `05.runners` milestone is declared complete.

Docs impact is affirmative: new setup, config, CLI, consumer, cache/resume, and frozen-boundary contracts need the dedicated retrieval runbook. Upstream corpus/representation/source-pack documentation and artifacts are not rewritten merely to claim completion. Journal publication, if any, is local only; AgentWiki publishing is skipped.
