# Plan 04 local acceptance audit

Milestone: **04.variants**. Scope: train/dev representation tooling and integrity
checks under the user's explicit `--auto` execution instruction. No ranking,
generator run, qrel, quality score, selected winner or test freeze is included.
The [execution contract](representation-goal-contract.md) and
[authorization](../configs/representation-execution-authorization.json) explain
automated local acceptance and preserve plan 02's pending human-review status.

## Deliverable and invariants

- 72 opaque train/dev incidents produce 216 queries, 72 selection records, 216
  token-ledger records and 72 common observation bundles. Every variant retains
  the same incident and exported retrospective half-open window. Test IDs are
  excluded by the separately verified manager selection.
- R1/R2 retain the same 572 log occurrences with identical complete source
  spans. All remaining log candidates are accounted for by selector or joint
  budget reasons. R2 whitespace normalization maps preserve every other source
  character. R3 explicitly adds metrics/traces and records its further loss.
- Exact token counts include query prefix and special tokens, with no implicit
  truncation. Query maxima are 512; bundle maximum is 2,047 under the separate
  2,048-token E5 planning budget. [Token audit](representation-token-audit.md)
  provides measured ranges, counts and the 70/72 identical-R1/R2 limitation.
- Every retained source span resolves to the current safe evidence. Generator
  text includes observation evidence IDs. G0/GB/GD/GH consume a common bundle;
  plan 07 owns actual-generator tokenization and prompt/knowledge budgets.
- Source/config/code/schema/tokenizer/dependency/output hashes are bound in the
  manifest. Rebuilding the exact candidate reproduces all artifact bytes.
  A changed config, input manifest, code, span or review evidence invalidates
  verification; publishing over a changed same-version candidate is refused.

## Independent evidence

[Source audit](representation-source-audit.md) checks the safe export, six
manager-selected train incidents, source selector restrictions and first-eight
service loss. [Decisions](representation-decisions.md) records the deterministic
quotas, ordering, unknown policies and downstream division of responsibility.

[Tester report](representation-tests.md) records real commands, runtime setup,
test totals and exact tested file hashes. Synthetic tests independently cover
private/unknown fields, input reorder/ties, cross-incident joins, half-open
windows, injection-policy rejection, Unicode, HTTP codes, versions, ports,
exceptions, all-null metrics, neutral traces, missing/empty/oversized evidence,
actual prefix/special token boundaries, normalization segment reconstruction,
shared bundle reuse, F1 rejection, output/receipt tampering and version drift.
Existing data/corpus/protocol suites check the unchanged shared touchpoints.

[Debugger report](representation-debugger.md) records its actual focused
checks and repaired strict-integer budget validation. The
[independent code review](representation-code-review.md) maps acceptance and
inspects the full train/dev candidate. Review also identified a public-boundary
mutation issue: a caller could change a validated object's fields before
rendering. Private observation/evidence fingerprints now reject such mutation
at consumption; regression subcases exercise all five public entry points.
The repair preserves all 576 artifact rows byte for byte, while its new code
hash requires a fresh manifest.

The [review receipt](representation-review-receipt.json) binds the final
manifest and current test, debugger, reviewer, specification and handoff
evidence. Automated actors are explicitly named as Codex agents. No A/B/C
human signatures are invented. The CLI validates both artifacts and receipt.

## Existing behavior and limits

All production changes are new representation files/configuration/schema;
existing data and corpus code, original telemetry, labels and prior manifests
remain unchanged. The pack has no application build, configured linter or type
checker; all new Python files parse and the relevant unittest suites execute.
No Git repository exists, so no commit or PR is created.

Safe export is already selected and redacted, not full raw telemetry. The
source's numeric deduplication cannot be reversed locally, and bounded regex
privacy checks do not grant external-sharing approval. Nulls, units, trace
semantics and unresolved service aliases stay unknown. The input package is
validated as a whole but only train/dev incidents are materialized; this work
does not claim pristine holdout blinding for earlier data preparation.

Plan 05 receives an R2 pilot candidate and all variants; plan 08 owns dev
selection with plan 06 judgments and F1 before test materialization. Plan 07
owns the actual generator budget. These are downstream milestones, not missing
work in local milestone 04.variants. [Handoff](representation-handoff.md)
documents the APIs, hash scopes, commands and invalidation procedure.
