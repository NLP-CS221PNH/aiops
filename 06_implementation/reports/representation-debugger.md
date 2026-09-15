# Representation debugger checks

Date: 2026-09-13. Reviewer: Codex source-audit/debugger agent, independent of renderer/materializer implementation. Result: the focused checks below pass after two findings were repaired by their implementation owners. This is a technical debugger report, not a human review or the final full-suite artifact receipt.

## Findings and resolution

1. `load_config` initially accepted Boolean `budget.max_query_tokens=True` because a range comparison treats Python Boolean values as integers. The renderer owner added an exact integer type check. A fresh temporary malformed config now raises a validation error. The real 512-token config was unaffected.
2. Materializer implementation binding initially omitted imported `src/corpus/tokenizer.py` and `src/corpus/common.py`. Exact code drift could therefore escape the implementation digest if output bytes were unchanged. The materializer owner added both dependencies; a fresh check confirms both paths and current hashes are in `_implementation_hashes()`.

No source data, upstream receipt, or implementation code was edited by this debugger. One initial null-status probe had an oracle typo (splitting for uppercase `Trace` after lowercasing); fixing that probe produced a pass without any renderer change. It is not counted as an implementation failure.

## Executed focused checks

The probes used the local CPython 3.11.9 environment, the real pinned tokenizer, independently authored synthetic fixtures from `test_representation_contract.py`, and assertions on semantic/boundary invariants. They did not read test telemetry, labels, raw files or qrels.

| Check | Result |
|---|---|
| Reverse evidence row order and all observation reference arrays | Identical query/selection/token/bundle results |
| Normalize whitespace around HTTP codes, HTTP version, exception, version, port, UTC timestamp, Greek and Chinese literals | All non-whitespace code points preserved; mapping covers the complete input/output |
| Add private `fault` metadata independently to observation/log/metric/trace fixture | All four boundaries reject |
| Log and trace exactly at the exclusive window endpoint | Both reject |
| Claim trace duration unit is seconds | Rejects; unknown-unit contract retained |
| Nullable trace status | R3 emits `status_code=None`, `semantics=unknown`; no invented error interpretation |
| Single oversized first log | Both R1/R2 drop it, retain later fitting evidence, share IDs/spans; no partial slices |
| Actual query counts | Backend encoding of `query: ` plus content and specials matches ledger and is within 512 |
| Empty log/metric/trace safe universe | Explicit insufficient-evidence states and unavailable-modality markers |
| Test role without authenticated freeze | Rejects |
| Management loader boundary | Exactly 72 opaque IDs and two digest fields returned, no family/split payload |
| Boolean query limit after repair | Rejects |
| Tampered manager split-map digest | Rejects |
| F1 tokenizer hash differing from externally authenticated snapshot | Rejects |
| Transitive tokenizer implementation binding after repair | Both imported dependency files bound |

The first 15 probe groups include the four independent private-field boundaries and two exclusive-end boundaries. All 15 pass after the Boolean repair and oracle correction. Two additional tamper-rejection probes and the dependency-binding inspection also pass. These focused counts are not additive to the project's test-suite totals.

## Six-train renderer replay

The safe consumer validator loaded the six manager-selected train IDs and the exact plan-02 manifest. Generated 18 queries and six bundles locally without persisting query artifacts. For each incident, checks independently verified R1/R2 ID/span equality; selected/dropped log set accounting; every evidence ID resolving; full safe-log character spans; real query counts; bundle retained/dropped disjointness and complete safe-universe coverage; absence of duplicate drop IDs; canonical bundle hash; and its separately counted planning budget.

| Incident | R1 / R2 / R3 tokens | Bundle planning tokens | Bundle retained / dropped evidence |
|---|---:|---:|---:|
| `inc_08457c0fbff4700e` | 510 / 510 / 465 | 2,044 | 25 / 89 |
| `inc_0991de462f9a6c05` | 463 / 463 / 490 | 1,804 | 22 / 87 |
| `inc_0f782051d78bc07a` | 127 / 127 / 453 | 1,196 | 12 / 73 |
| `inc_15361b2d5df6a488` | 465 / 465 / 509 | 1,809 | 22 / 82 |
| `inc_1bd0f85d1967890c` | 505 / 505 / 451 | 2,009 | 23 / 93 |
| `inc_1c35829e1a5668b7` | 70 / 70 / 386 | 1,126 | 11 / 75 |

The bundle counts use the candidate E5 planning tokenizer, not an actual generator; plan 07 must validate its own model's common budget. Equal R1/R2 counts on these six cases are observations, not proof of equivalent downstream usefulness.

## Inspected implementation snapshot and limits

The final focused repair verification observed these implementation hashes:

| File | SHA256 |
|---|---|
| `src/representations.py` | `238fad580269cc9dd30df13f7c5994a5cd38306cf639acbf7763f3beee805f9a` |
| `src/representation_pipeline.py` | `ad365b86bcdcc85711ccb23f5a70deea1cf3a0f0b4c670fc744fdea9d611f84e` |
| `src/corpus/tokenizer.py` | `bb72ff978d6e380479149a42236133b6638c3db19aa153c4cd0fef2d1bc26fc9` |
| `src/corpus/common.py` | `416d1d7ab27097f1e5bea41471dc958a886b7ff4daced4ca47be4037aee7f004` |

Materializer work continued in parallel. This report does not claim a full all-72 artifact regeneration, atomic publication interruption test, or final receipt validation; the dedicated tester/reviewer and final artifact replay own those gates and must bind their final hashes. The full plan-02 human gate remains pending; these probes do not supply A/B/C identities or sharing approval.
