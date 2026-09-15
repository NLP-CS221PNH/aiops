# Plan 04 — local variants handoff

The deliverable is **04.variants**: deterministic train/dev representations and
local verification. The current `--auto` instruction authorizes automated local
acceptance, recorded in [execution authorization](../configs/representation-execution-authorization.json).
Plan 02's original human-review state stays pending. Reviews here are Codex
reviews, not A/B/C signatures, experiment approval or external sharing approval.

## Run from the research-pack root

```powershell
06_implementation/.venv/Scripts/python.exe -B 06_implementation/scripts/build_representations.py validate --receipt 06_implementation/reports/representation-review-receipt.json
```

The builder and validator use the pinned E5 tokenizer assets already on disk
(`intfloat/e5-small-v2`, revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`,
tokenizers 0.21.4). No model weights or inference are used. All queries count the
`query: ` prefix and two special tokens within 512 tokens. Tokenizer truncation
and padding are disabled. [Query manifest](../queries/query-manifest.json) pins
input, configuration, schema, implementation, environment and artifact hashes.
The validator regenerates the outputs, compares exact bytes and verifies the
final review receipt against the current manifest and review evidence.

### Hash comparison scopes

Compare hashes only when their byte/content scope agrees. Canonical JSON uses
the implementation's stable serializer; a file hash includes the exact file
bytes and therefore can differ from a canonical content hash.

| Field | Hashed scope | Correct comparison |
|---|---|---|
| Query row `config_hash` | Canonical configuration JSON content | Manifest `config_content_hash` |
| Manifest `config_hash` | Exact bytes of `configs/representation.yaml` | SHA256 of that file |
| Query/token row `tokenizer_hash` | Exact bytes of the pinned `tokenizer.json` asset | Tokenizer asset SHA256 in the pinned specification |
| Manifest `tokenizer_hash` | Canonical complete tokenizer specification | Canonical hash of that specification, including its asset hashes |
| `input_manifest_hash` | Exact bytes of the input manifest | Same raw-file SHA256 across rows, manifest and receipt |
| Query row `query_hash` | Exact UTF-8 `query_text`, excluding `query: ` | SHA256 of the unchanged stored text |
| Bundle `bundle_hash` | Canonical bundle JSON excluding `bundle_hash` itself | Canonical hash after removing only the self-hash field |

## Retrieval interface: plans 05 and 08

- Read [variants.train-dev.jsonl](../queries/variants.train-dev.jsonl). There are
  three query records per opaque incident ID, keyed by `query_id` and
  `representation_id`. Use `query_text` unchanged for every retrieval branch.
  `query_hash` is SHA256 of its exact UTF-8 text. Dense encoding adds `query: `
  once; the stored text excludes the prefix. BM25 must not receive additional
  unbudgeted logs. Any reranker pair budget belongs to plan 05.
- **R2 is the default pilot candidate, not a selected winner.** R1 contains the
  literal already redacted, already selected safe-export log text. R2 collapses
  whitespace runs only. It preserves every other character, including service
  names, error codes, exceptions, ports, versions and source language. Identical
  text/token results are legitimate when source whitespace already agrees.
- R1/R2 share prebudget selection and postbudget retained evidence IDs and whole
  source spans. R2 cannot refill saved space. Entire blocks that do not fit are
  dropped with a reason; later smaller blocks can fit. No partial literals or
  fabricated evidence are emitted. `insufficient_evidence` remains an explicit
  record if nothing usable fits.
- R3 intentionally changes modality mix: first metric and first trace, common
  retained logs, then remaining configured metric/trace candidates. Its log
  subset, enrichment IDs and all budget loss remain auditable. Grouping is by
  service/time within modalities. Metric scores are descriptive; unknown metric
  units, raw trace durations and neutral numeric statuses remain unknown.
- [Selection ledger](../queries/selection-ledger.jsonl) distinguishes selector
  quotas, joint budget loss, modality quotas and the safe candidate universe.
  [Token ledger](../queries/token-ledger.jsonl) adds real before/after counts,
  tokenizer revision, retained/dropped IDs, full source spans and normalization
  maps. Offsets are half-open Unicode code points in the **safe exported log**.
  They do not locate unredacted raw text. Source IDs/row positions link onward
  through plan 02's private provenance audit without exposing private paths.

## Generator interface: plan 07

Read [observation-bundles.jsonl](../queries/observation-bundles.jsonl) by
`incident_id`. `observation_text` contains explicit evidence IDs for observation
citations. Use exactly the same bundle in G0, GB, GD and GH, independent of
retrieval representation. Knowledge context is added separately. `bundle_hash`
is the canonical JSON hash of the bundle excluding the hash field itself.

The bundle has an independent 2,048-token **E5 planning budget** with no query
prefix and with special tokens counted. This is a real count under the named
tokenizer, not proof of fit under a future generator tokenizer. Plan 07 must pin
and count its actual generator tokenizer and apply any necessary common bundle
revision symmetrically across all conditions before F1. System/prompt, knowledge
and output budgets are separate. No generator has run in plan 04.

## Runtime and manager separation

`src.representations.SafeIncident` accepts exact safe schemas, checks incident
joins and the exported retrospective half-open window, and rejects private or
unknown fields. The pure public functions are `select_evidence`,
`render_representation`, `apply_query_budget`, `build_observation_bundle` and
`generate_incident`. They receive no split, family, gold, qrels or manager table.

`src.representation_pipeline` isolates management selection from runtime loading.
The manager checks the split sidecar and passes 72 opaque train/dev IDs; the
runtime loader validates only the safe export. Safe package hash/schema checks
cover all 90 input IDs, but only 72 train/dev IDs are materialized. The six train
audit samples cover six families chosen by the manager; family metadata stays
outside renderer payloads. The input manifest contains the existing full export;
test telemetry is neither transformed into query outputs nor used for tuning.

## Dev selection, freeze and invalidation

Plan 08 compares the candidates on the 18 dev incidents using one reference
retriever/corpus and plan 06 dev judgments. New retrieved candidates require
judging; unjudged is not grade zero. Record negative and unchanged trials too.
There is no winner, quality metric, ranking, annotation or test freeze here.

The current CLI has no test-materialization command. The small
`assert_test_f1_gate` interface rejects test mode without an externally
authenticated F1 hash contract. Plan 08 owns that authentication and future test
materialization using these same pure functions. Synthetic unit fixtures need
no real-data freeze. Do not append test outputs to train/dev artifacts.

Changes to config, source export, renderer, token assets or schema invalidate the
manifest/receipt. Preserve the old release and build a versioned directory with
a new version; verify and review before downstream consumption. Query-only
changes stale rankings and pool receipts, not automatically incident-centered
relevance judgments when task/window/evidence text/applicability are unchanged.
Rejudge new candidates and review affected labels when those underlying task
properties change. Bugs after F1 require plan 08's deviation procedure and the
original outputs must remain preserved.

## Known limits

Upstream selection already discarded most raw logs and deduplicated numeric
patterns. Local ledgers measure loss only within the safe export; they cannot
reconstruct discarded raw IDs or distinguish every original HTTP code removed
upstream. Privacy regex coverage is bounded; the existing local-only payload
restriction remains relevant. `frontend` and `frontendservice` stay separate,
and no alias, duration conversion, causal diagnosis or translation is invented.
