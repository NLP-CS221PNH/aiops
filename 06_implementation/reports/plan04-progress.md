# Plan 04 progress and acceptance mapping

Date: 2026-09-13. Scope: local `04.variants` milestone under the user's explicit
`/goal ak:codex-goal ak:cook --auto` request. The
[execution contract](representation-goal-contract.md) and
[authorization](../configs/representation-execution-authorization.json) separate
automated technical acceptance from pending A/B/C human review and plan 02's
pending full administrative gate. No human signature is claimed.

Finalization state: **completed for the authorized local `04.variants`
milestone**. All three phases and all five plan criteria are reconciled below.
The independent test suite, independent code review and final receipt-aware
artifact replay pass. Upstream and A/B/C human gates remain pending as stated
in the execution authorization.

## Verification evidence

The final independent [tester report](representation-tests.md) and
[machine test receipt](representation-tests.json) record **203/203 tests passing,
0 failures, 0 errors and 0 skips** in 46.300 seconds: 43 representation tests
plus 160 existing protocol, data, provenance, corpus and citation tests. The
representation-only replay passed 43/43 in 2.643 seconds. These totals include
50 mutation subcases across the five public entry points; subcases are not
added again to the test count.

Tests use CPython 3.11.9 from the local venv, pinned `tokenizers` 0.21.4 and the
existing user-site PyYAML 6.0.2 needed by protocol tests. An initial venv-only
PyYAML import failure was corrected through the existing module path; no
installation, skip or weakened test was used. Exact commands and tested file
hashes are in the tester evidence.

The [acceptance audit](representation-audit.md) traces artifacts and reviewed
invariants. The source/debugger review found a strict-integer budget gap and
missing transitive tokenizer implementation binding; both were repaired.
Independent testing also exposed mutation of validated records before use.
Private fingerprints now reject changed safe records at every public consumer,
with the original candidate artifact rows preserved byte for byte.

The independent [code review](representation-code-review.md) passes at 9.6/10
with zero unresolved critical or important findings. The reviewer checked 20
additional mutation probes and independently verified all 72 published incident
artifacts against the reviewed candidate. These probes are separate review
evidence and are not added to the 203-test suite total.

The final [review receipt](representation-review-receipt.json) binds 15 current
evidence files and exact input/config/schema/tokenizer/dependency/implementation
hashes. The root executor ran the handoff's `validate --receipt` command after
creating it: exit 0, `technical_gate=pass`, `deterministic_replay=true`, all 72
incidents and 216 queries accepted. Receipt evidence deliberately excludes live
plan files, this progress report and the journal so progress sync cannot change
the accepted technical evidence.

| Final binding | SHA256 |
|---|---|
| Query manifest | `013b41243616224fe39069d0fa27912689536095d1ca3db425b09ab513f40a28` |
| Review receipt | `ccdb0c764a70d0f8cfa822add0844b6813b98f8ef41ef4258467c60d56ab2b2a` |

## Phase 1 acceptance: specification and source audit

| Checklist criterion | Local acceptance evidence |
|---|---|
| Source selection limits and six-train audit recorded | [Source audit](representation-source-audit.md) validates six train incidents spanning six manager-selected families: 97 logs, 433 metrics and 84 traces; identifies upstream numeric dedup, selection quotas and first-eight service loss. Runtime receives only opaque IDs and safe records. |
| R1/R2 common selection; R3 separate enrichment contract | [Configuration](../configs/representation.yaml) and [decisions](representation-decisions.md) fix service round-robin, quotas, whole-block joint R1/R2 clipping and explicit R3 modality quotas and priorities. |
| Concrete entity/time/unknown policies, without gold | [Safe renderer](../src/representations.py) rejects private fields and invalid joins/windows; R2 changes only whitespace; source spans and normalization maps preserve non-whitespace code points; units/status semantics stay unknown. [Contract fixtures](../tests/test_representation_contract.py) cover technical literals and forbidden inputs. |
| Token/interface specification sufficient for deterministic rendering | [Schema](../queries/representation-schema.json), configuration and [handoff](representation-handoff.md) define actual E5 tokenizer revision, 512-token limit including prefix/specials, shared retained IDs/spans, missing states, manifests and separate common-bundle planning budget. |
| Dev selection/F1 responsibility outside this phase | Decisions and handoff assign plan 08 dev selection/F1 and plan 06 judging. R2 is a default pilot candidate only. |

R04-01 through R04-04 map, in order, to the source audit, selection policy,
normalization/modality contract and tokenizer/consumer interface above.

## Phase 2 acceptance: renderers and train/dev artifacts

| Checklist criterion | Local acceptance evidence |
|---|---|
| Deterministic R1/R2/R3 from safe evidence | [Pure functions](../src/representations.py) implement `select_evidence`, `render_representation`, `apply_query_budget`, `build_observation_bundle` and `generate_incident`. [Pipeline](../src/representation_pipeline.py) keeps manager selection separate. Reordering/tie fixtures and regeneration compare exact output bytes. |
| Common log selection and common generator bundle verified | Contract fixtures require identical R1/R2 retained IDs and source spans, complete normalization mapping, and one bundle hash across G0/GB/GD/GH placeholders. Bundles contain literal evidence IDs for citations. |
| Complete real token counts and clipping ledger | [Token audit](representation-token-audit.md) records all-72 query ranges: R1/R2 68–512 tokens, R3 373–512; each query uses actual pinned E5 counts. Joint selection retains 572 log occurrences and records 268 budget drops. Bundle planning counts range 1,080–2,047 within 2,048. |
| Honest train/dev counts/errors; no test materialization | [Manager configuration](../configs/representation-manager.json) supplies 54 train + 18 dev opaque IDs. [Manifest](../queries/query-manifest.json) binds 216 queries and 72 bundles; all 18 test IDs are excluded. Final artifact replay confirms exact counts, zero manifest errors and no silent incident drops. |
| Downstream schema/hash fields match shared contracts | Schema, manifest and handoff define per-record hashes, evidence lineage, token/selection ledgers and independent bundle interface. The handoff hash-scope table distinguishes raw file hashes from canonical content hashes. |

R04-05 through R04-08 map to the pure R1/R2 implementation, R3/common bundle,
actual tokenizer/ledgers and manager-scoped train/dev materialization respectively.

## Phase 3 acceptance: integrity and consumer handoff

| Checklist criterion | Local acceptance evidence |
|---|---|
| Leakage/entity/provenance/metamorphic tests pass with evidence | [Contract suite](../tests/test_representation_contract.py), [pipeline suite](../tests/test_representation_pipeline.py) and [independent debugger](representation-debugger.md) cover private-field rejection, fixture metadata invariance, ordering, Unicode, technical literals, joins/windows, source span resolution and tampering. Final [tester](representation-tests.md) and [reviewer](representation-code-review.md) evidence passes. |
| Real token budgets and full dropped/missing states | Token audit and per-record ledgers cover real prefix/special counts, exact boundary, R1 overflow while R2 fits without refill, oversized blocks, zero evidence, missing modalities and raw neutral status. |
| Receipt binds exact hashes and reviews actually performed | Final [review receipt](representation-review-receipt.json) binds the current manifest, input, configuration, tokenizer, implementation and independent evidence. Automated reviewers are recorded as Codex; human reviewers remain pending. The receipt-aware validator passes. |
| Stable interfaces to 05/07/08 without circular qrels/test wait | Handoff provides paths, APIs, exact hash scopes, unchanged common query text, generation bundle, candidate version and invalidation procedure. The pilot consumer interface is locally checked; downstream ranking/generator execution is outside plan 04. |
| No unperformed winner, quality score or test freeze claim | R2 remains only the pilot candidate. No retrieval/generation experiment, qrels, dev winner, actual generator budget proof or F1/test materialization is claimed. |

R04-09 through R04-11 map to the metamorphic/integrity suite, token/provenance
consumer checks and receipt, then downstream handoff respectively.

## Plan success criteria: complete cross-phase mapping

| Plan criterion | Evidence and acceptance scope |
|---|---|
| R1/R2 shared selected-log ledger; R3 enrichment IDs and missing markers | Phase 1 common-selection contract + phase 2 implementation and all-72 token/selection audit + phase 3 invariants. |
| Same incident/window; no labels, synthetic inference or provenance loss | Exact safe-schema boundary, original windows, source spans, entity preservation, descriptive metric/neutral trace rendering and phase 3 leakage/join tests. Query scaffolds are explicitly synthetic; source telemetry flags are preserved. |
| Real token audit; common pre-retriever clipping and reasons for dropped evidence | Pinned tokenizer assets/revision, actual counts including prefix/specials, joint R1/R2 whole-block ledger and exact artifact replay. |
| Leakage/entity/determinism pass; common generator bundle reviewed | Independent automated contract/debugger/reviewer evidence establishes local acceptance under the execution authorization. C's human signature is still pending; plan 07 must count its actual generator tokenizer. |
| 05/08 receive variants plus hashes/interfaces for dev selection without winner claim | Local hash-bound artifacts and handoff are available to the downstream owners. No external message, human consumer acknowledgment, retrieval run or selected winner is represented as completed. |

## Documentation impact and authority

Documentation impact exists because plan 04 adds executable commands, safe
runtime interfaces, machine-readable schemas and consumer hash contracts.
[Representation handoff](representation-handoff.md) is the smallest current
consumer guide and now includes explicit hash comparison scopes. Configuration,
schema, source code and generated manifest remain their respective machine
authorities; this report records progress and traceability rather than copying
their full contract inventories.

The root README describes the original research-pack snapshot and the
implementation README owns the existing plan-01 protocol delivery. Neither is
rewritten merely to record this plan's completion. Existing upstream source
files, human receipts and protocol acceptance remain unchanged. The plan's
execution note links this report and clarifies the automated local review scope.

## Plan-store synchronization

The live AgentKit CLI is available. Its help defines phase status from
checkboxes: `ak plan check` changes checklist items; `ak plan phase update`
cannot set file-owned phase status. `ak plan update --status` owns the plan
frontmatter. The local `AGENTKIT_HOME` is
`06_implementation/.agentkit-state`, allowing the existing local plan registry
to operate without the inaccessible global cache. The repository has no Git
directory, so the Git current-plan pointer is unavailable.

After all independent gates passed, `ak plan phase close` checked all five
criteria in each of the three phase files; `ak plan check` checked the five
plan-level success criteria. `ak plan update --status completed --current-phase
3` updated plan frontmatter and the current phase. Each phase received
index-owned evidence, acceptance and notes through `ak plan phase update`, then
`ak plan reindex --path . --apply` synchronized the local store.

Final `ak plan status` and `ak plan parse` both return **completed, 3/3 phases
done, 15/15 phase tasks, 100%**. All three parsed phases are `done` at 5/5.
A direct file sweep additionally confirms the plan's own 5/5 criteria, giving
**20 checked, zero unchecked criteria overall**. `ak plan validate` exits 0
with `valid=true` and no errors. There are no unresolved acceptance mappings.

CLI limitation verified on a disposable fixture and the final files:
`phase close`/`check` change checkboxes but retain literal `status: pending` in
phase frontmatter and the original `Pending` phase-table cells. The initial
`phase close` response even returned a stale `todo` view; subsequent phase
updates, reindex, parse and status return `done`/100%. Supported CLI mutations
do not rewrite those redundant static cells for phases with checkboxes. Their
meaning is explicitly clarified in the plan's execution note; no phase/status
table was hand-edited. The plan-level YAML status is accurately `completed`.

No external task-management surface with phase/checklist operations was
discovered; durable plan files and the local AgentKit plan store provide the
progress record. Only this workspace was registered in the local AgentKit
home for journal routing; no global registry write was needed.

## Remaining owner work

A/B/C human review, upstream full acceptance and any external payload approval
remain pending. Plan 05 owns retrieval/pair-budget execution, plan 06 judging,
plan 07 actual generator-tokenizer fit, and plan 08 dev trials/F1 followed by
separate test materialization. Original upstream selection loss and bounded
redaction are documented limits, not reconstructed or certified by local tests.

Unresolved local integrity findings: none. All local stop conditions are met.
AgentWiki publish skipped; the technical journal is persisted locally through
the first-class `ak journal create --stdin` command:
[Plan 04 deterministic incident representation](../../plans/journals/2026-09-13-plan-04-deterministic-incident-representation.md).
Journal validation by filename stem with the explicit registered project exits
0 (`ok=true`); this CLI did not resolve the earlier relative-path invocation.
Final link checks found zero broken targets across the plan, handoff and this
report. All 15 receipt-bound evidence hashes still match after finalization.
