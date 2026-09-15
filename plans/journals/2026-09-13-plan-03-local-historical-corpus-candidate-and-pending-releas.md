---
title: Plan 03 local historical corpus candidate and pending release
date: 2026-09-13
summary: Validated 74-document, 440-chunk historical candidate with 160 passing tests; actual human acceptance remains pending.
---

# Plan 03 local historical corpus candidate and pending release

## What happened

The user explicitly authorized a local Plan 03 corpus candidate on Plan 02's passed technical contract while preserving all human/release gates. The implementation produced 74 historical document records, 67 unknown conditional candidate documents, 7 proposed exclusions and 440 token-aware chunks. All 580 original chunks have exact overlap/removal/exclusion lineage. Raw source bytes, source receipts, attribution and license evidence remain intact. Twelve copyright titles were corrected with originals retained; 14 local includes expanded across 6 documents; 43 short chunks and 175 unresolved Hugo warnings remain explicit review work.

## Decisions and verification

The corpus hash is `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3`; manifest SHA256 is `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7`. The source audit passed 5,666 checks. Sixty corpus/citation tests, 48 existing data tests and 52 existing protocol tests passed with no failures/errors/skips. Fresh and independent-process builds reproduced all 8 artifacts. Independent code review identified citation metadata, silent chunk loss, proposal-version and summary-validation gaps; these were fixed and reverified before final acceptance. Code review scored 9/10 with zero remaining critical/high/medium findings. The coordinator separately reviewed the source-audit code authored by the code reviewer.

Actual pinned E5 token counts include passage prefix, heading and special tokens, reaching a maximum 511/512 without truncation. No model inference, embedding, benchmark, remote include or downloaded source example was executed. Content review flags 4 near-duplicate pairs using a declared five-word-shingle Jaccard 0.8 threshold; no incident relevance or evidence independence is inferred.

## Remaining release work

All 74 human review identities/timestamps remain blank; released/indexed count is 0 and strict reviewed validation fails as intended. Plan 02 human acceptance and actual A/B applicability/content/citation review remain pending. The original Plan 03 remains in-progress while the amended local-candidate task is complete. All 3 phase files were reconciled; the CLI checked phases 1/2 only (10/15 durable boxes, 66%). Four of phase 3's 5 criteria have technical evidence, but its human criterion is unfulfilled and the CLI only toggles a whole phase. Exact partial progress is recorded in `06_implementation/reports/plan03-progress.md`.

A future change requires a new version, retrieval rebuild, re-pooling and affected-pair rejudgment; old/new overlaps never transfer qrel grades. Coverage and relevance remain unjudged, and deployment compatibility unknown. No Git repository was present, so no commit or PR was created.

AgentWiki publish skipped. This chronological record does not replace the corpus contract, handoff or review receipt.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
