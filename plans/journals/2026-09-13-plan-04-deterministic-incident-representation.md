---
title: Plan 04 deterministic incident representation
date: 2026-09-13
summary: "Completed local 04.variants: 72 incidents, 216 queries, 203 passing tests, exact review receipt and full plan sync; human gates remain pending."
---

# Plan 04 deterministic incident representation

## What happened

Completed the explicitly authorized local plan-04 04.variants milestone. The manager supplied 54 train and 18 dev opaque IDs; deterministic safe renderers produced 216 R1/R2/R3 queries, 72 selection rows, 216 token-ledger rows and 72 common observation bundles. R1/R2 retain the same complete source spans after actual E5 budgeting. No test queries, rankings, qrels or model calls were produced.

Independent source audit documented existing selected-log loss and the six-train sample. Debugging repaired Boolean query-budget acceptance and missing transitive tokenizer implementation binding. Testing then exposed post-construction mutation of validated records; private fingerprints now reject changes through all five public consumer functions, with 50 regression subcases. Existing artifact data remained byte-identical. Handoff now distinguishes canonical content hashes from raw file hashes.

## Evidence and acceptance

The independent test suite passed 203 tests with zero failures, errors or skips: 43 representation tests and 160 existing tests. The independent code review passed at 9.6/10 with zero critical or important findings. Root finalization ran the receipt-aware validator successfully: deterministic replay and exact dependency/evidence bindings pass for all 72 incidents and 216 queries.

Query manifest SHA256: 013b41243616224fe39069d0fa27912689536095d1ca3db425b09ab513f40a28.
Review receipt SHA256: ccdb0c764a70d0f8cfa822add0844b6813b98f8ef41ef4258467c60d56ab2b2a.

AgentKit CLI synchronized all three phases and all five plan-level criteria: 20 checked, zero unchecked overall. Its parse/status report completed, 3/3 phases and 15/15 phase tasks at 100%; plan format validation passes. The CLI retains redundant original pending phase YAML/table cells; the plan execution note and progress report explain checkbox-derived current status. Plan frontmatter is completed through the supported CLI. No Git repository exists, so there is no commit or PR.

## Decision and current authority

The current /goal ak:codex-goal ak:cook --auto request authorizes automated local milestone acceptance. A/B/C human signatures and plan-02 full human/consumer acceptance remain pending. They were not supplied by automated reviews. The execution contract and authorization state the exact scope. Current consumer commands, APIs, hash scopes and limits live in 06_implementation/reports/representation-handoff.md; machine config/schema/manifest own their contracts. 06_implementation/reports/plan04-progress.md maps all acceptance items and records CLI behavior. This journal records work history only.

## Next steps

Plan 05 owns retrieval execution and reranker pair budgets. Plan 06 owns judging. Plan 07 must count the common observation bundle with its actual generator tokenizer. Plan 08 owns dev selection and authenticated F1 before future separate test materialization. R2 is a default pilot candidate only; no winning representation or scientific quality score is claimed. Preserve upstream local-only and human-review boundaries.

AgentWiki publish skipped. No external publication or messages were sent.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
