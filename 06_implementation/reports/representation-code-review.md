# Independent representation code review

Date: 2026-09-13. Reviewer: `/root/code_reviewer`, Codex agent, independent of the renderer, materializer and test authors. Skill: `ak:code-review`, specification pass followed by implementation/edge-case review and fresh verification. No implementation files were edited by this reviewer.

**Result: PASS for the local `04.variants` technical milestone. Score: 9.6/10. Unresolved critical findings: 0; unresolved important findings: 0.** The score assesses implementation correctness, traceability and maintainability within this milestone; it is not a scientific quality score or a human signature.

The accepted plan and all three phase files, shared independent-plan contracts, execution contract, source audit, decisions, renderer, pipeline, CLI, configuration, manager contract, artifact schema, tests and downstream handoff were reviewed. The explicit current `--auto` instruction authorizes automated local acceptance as recorded in `configs/representation-execution-authorization.json`. Plan 02's full human/consumer gate remains pending. No upstream approval was inferred, fabricated or changed.

## Exact reviewed candidate

The final reviewed staging directory is `.representation-check/review-v2`. Its four JSONL artifacts are byte-identical to the earlier `review-v1` data that underwent the independent all-72 audit. The final manifest incorporates the public-boundary integrity repair. The reviewer also independently verified that the four published `queries/` artifacts and manifest are byte-identical to this final reviewed stage.

| Binding | SHA256 |
|---|---|
| Query manifest | `013b41243616224fe39069d0fa27912689536095d1ca3db425b09ab513f40a28` |
| Implementation aggregate | `06d480c54cfffb6201b4f2d208b47d5df8d71977f30367fb62c9cc0426f1fdb3` |
| Safe input manifest | `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4` |
| Representation config file | `0e0c347c20f7a025013c3e7134a83c73356f5fc00dafed666f099c8395ffd34d` |
| Representation schema | `c86745c9dec0b067b7744951a3f974bf5615978cb0eb266097ed917cf8c3c365` |
| `src/representations.py` | `3b1a107ac7bca39e5123772c33e89840951c857857319f9b8d09852fa5da90a6` |
| `src/representation_pipeline.py` | `7ed8f2b186f3592dbaa4337af0d79ee1bc0acf7ea6e51472f27e03b31197f2cb` |

The manifest additionally binds tokenizer policy/assets, dependency versions/locks, transitive imported implementation files, manager selection/config and every artifact. Config/content and tokenizer/policy hash scopes differ intentionally and are now explicitly mapped in the handoff and schema.

## Findings and retest

1. **Resolved important boundary gap — `src/representations.py:63`, `:101`, `:177`, `:244`.** The tester demonstrated that mutating an already validated log text into a nested private mapping could reach the low-level renderer. The implementation owner added canonical observation/evidence snapshots and checks at public consumption boundaries. The reviewer inspected the repair and independently tested 20 mutations: private text, private observation field, interpreted trace semantics and changed window, each through selector, renderer, budgeter, bundle builder and aggregate generator. All reject with `SAFE_INCIDENT_MUTATED`. The independent committed regression covers 50 mutation subcases. Final real-data artifact bytes remain unchanged.
2. **Resolved documentation ambiguity — `reports/representation-handoff.md:23`.** Per-query `config_hash` means canonical config content, while manifest `config_hash` means file bytes; per-record tokenizer hashes identify the asset, while the manifest hash identifies the complete tokenizer policy. The requested comparison table now names the correct joins. No producer schema or output change was necessary.

The earlier debugger's Boolean-budget and omitted-transitive-tokenizer-binding repairs were inspected in current code and exercised by the final tests/replay. No new actionable defect remained after retest.

## Acceptance mapping

| Planned item | Review evidence and disposition |
|---|---|
| R04-01: six-train source/window audit | PASS. Source audit records the safe export and exact lineage/selection limits. Independently checked the six manager IDs against split administration: six train incidents, six distinct opaque families. All-72 checks resolve evidence/window joins without opening raw telemetry or gold. Human A review remains pending explicitly. |
| R04-02: deterministic selector/loss ledger | PASS. Service round robin, UTC timestamp/evidence-ID ties, two logs/service and 24/incident are explicit. Source first-eight ordering bias is documented. Independent set accounting verifies every candidate is retained or dropped exactly once with a reason, within the safe universe. Unavailable raw IDs remain unknown. |
| R04-03: normalization/modality contract | PASS. R1 retains complete exported literals; R2 replaces whitespace only. Entity fixtures preserve 500/503, exception, service, version, port and Unicode literals. R3 carries evidence IDs, descriptive metric values and neutral raw nullable trace status/duration with unknown semantics. No translation, alias merge or diagnosis is added. |
| R04-04: tokenizer/downstream specification | PASS. Pinned real E5 assets and library version, 512-token query budget, query prefix and two special tokens, whole-block policy and separate generator planning budget are explicit. Dev selection/F1 stays with plan 08. |
| R04-05: R1/R2 implementation | PASS. All 72 incident pairs have identical post-budget retained log IDs and source spans. Full source strings and R2 normalized strings independently resolve inside query text. Typed record schemas reject private/unknown fields and foreign incidents/windows; post-validation mutation is also rejected. |
| R04-06: R3/common bundle | PASS. R3's separately budgeted enrichment and reduced log subset are declared. All R3 IDs resolve; raw trace facts are present without error interpretation. G0/GB/GD/GH fixture objects and hashes are identical. Query-budget/default-candidate changes leave the common bundle unchanged. All 72 bundles contain cited evidence IDs and complete retained/dropped accounting. This is the automated local bundle review; no human C identity is asserted. |
| R04-07: actual token/clipping ledger | PASS. Direct backend encoding independently matches all stored post-budget counts. R1/R2 range 68–512 tokens; R3 373–512; bundles 1,080–2,047 under the named 2,048-token planning budget. The real U+0085 counterexample makes R1 longer than R2 and proves joint dropping without R2 refill. Full-span policy emits no partial literal. Oversized/empty evidence has explicit drops or insufficient states. |
| R04-08: train/dev artifacts | PASS. Exactly 72 incidents, 216 queries, 72 selection rows, 216 token rows and 72 bundles; zero manifest errors. Independently joined manager split administration to confirm all 54 train/18 dev IDs and exclude all 18 test IDs. Payload schemas exclude family/split/private fields. Invalid input aborts with explicit failure instead of silently omitting an incident. |
| R04-09: leakage/entity/metamorphic tests | PASS. Fresh 43-test representation run verifies constructor and public-boundary rejection, twelve order/tie permutations, entity preservation, missing modalities, null semantics, half-open windows, explicit insufficient states and non-mutating source behavior. |
| R04-10: provenance/consumer/receipt checks | PASS for reviewed artifacts and receipt tooling. Exact regeneration verifies schema, hashes, counts, token limits and provenance. Normalization maps reconstruct contiguous source/output code points. Synthetic receipt tests reject drift in each required dependency, stale evidence, missing reviewer roles, pending reviews and private evidence paths. Final release receipt must bind these current reviewed bytes and reports and then pass the receipt-aware validator. |
| R04-11: downstream handoff | PASS. Handoff specifies paths, public functions, hash meanings, unchanged common retriever query text, common generator bundle, R2 pilot candidate only, plan-06 judging and plan-08 dev/F1 ownership, versioning/invalidation and test refusal. It contains no selected winner, retrieval/generation metric or test freeze claim. |

The phase scenarios are covered by the mapping and tests: RC-01–03 selector/ordinary/entity cases, RC-04–05 neutral trace/null metric cases, RC-06–07 window and safe-source refusal; RB-01–09 ordering/entities/limits/oversized logs/missing traces/neutral status/common bundle/stale config/joint clipping; RV-01–10 private-field and metadata invariance, legitimate service literals, foreign joins, Unicode, ordering, insufficient evidence, stale receipts, F1 refusal and joint clipping. Source-boundary rules are not replaced by blanket denial of valid service words.

## Fresh verification actually inspected

The reviewer ran these from `06_implementation` with local Python 3.11.9 and the pinned `tokenizers` 0.21.4 assets:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_representation*.py' -v
.\.venv\Scripts\python.exe -B scripts\build_representations.py validate --output-dir .representation-check\review-v2
```

Results: **43 tests, zero failures/errors, 2.628 seconds**; exact all-artifact regeneration **PASS**, exit 0, final manifest hash shown above, `deterministic_replay=true`, no test materialization. The reviewer also directly ran the all-72 set-accounting/literal/window/backend-token audit, six-train membership check, 20 post-construction mutation probes, equality of the four v1/v2 artifact files, and source compilation for the three implementation/CLI and two test modules.

The tester's final `representation-tests.md` and `.json` were read, and all seven recorded source/config/schema/test file hashes were independently matched to current files. That separately executed full run passed **203 tests, zero failures/errors/skips, 46.300 seconds**, comprising 43 representation tests and 160 existing protocol/data/corpus/citation tests. This full-suite result is inspected tester evidence, not a claim that the reviewer personally reran that command. The tester documents the existing PyYAML user-site path needed alongside the data venv; no dependency installation or test suppression was used.

Current `configs/data.yaml`, `src/data/common.py` and `src/data/export_inference_data.py` hashes still match the existing upstream data receipt. No existing public contract was intentionally changed. This research pack has no separate application build or configured application linter; successful source compilation, materialization, exact replay and the regression suite provide the applicable execution evidence.

## Limits and release integration

This automated review establishes the local tooling milestone. It does not establish raw-data completeness, universal redaction coverage, human evidence interpretation, actual generator-model budget fit, retrieval/generation quality, a winning representation, F1/F2 or permission to transfer telemetry. Safe-package validation is structural across the existing export; generated content is confined to train/dev. Raw telemetry, ground truth and qrels were not opened by this reviewer.

Plan 02's pending human/consumer gate and A/B/C human reviews remain explicit. Plan 07 must verify its actual generator tokenizer and common context budget; plan 08 must authenticate its freeze before future test materialization. There is no test-materialization CLI today, and the guard does not purport to authenticate caller JSON itself.

The finalizer must create a receipt with this review and the current tester evidence, then run the validator with `--receipt`. This report cannot hash or validate a future receipt that includes this report's own hash; final receipt-aware replay is the separate finalization check. Any later code/config/schema/input/artifact change invalidates this review's exact candidate binding and requires appropriate re-review/retest.
