---
title: Methodology freeze MVP cook complete
date: 2026-09-17
summary: Locked METH-LOCK-20260917; retracted 0.671 vs 0.342; headline tables stay NOT_RUN until human G2.
status: Resolved
---

# Methodology freeze MVP cook complete

**Date**: 2026-09-17
**Severity**: High (claim integrity, not pipeline breakage)
**Component**: `configs/methodology-lock.yaml`, `src/evaluation`, scientific controls
**Status**: Resolved

## What happened

Cooked the accepted plan `plans/260916-1707-cs221-methodology-freeze-mvp` under `/ak:cook --auto` with a durable goal. The pipeline was not rebuilt. BM25 / E5 / RRF stayed as-is. GraphRAG, multi-agent, iterative retrieval, and IR-R were not added. Corpus and chunks were not rematerialized. `F1.json` bytes did not change.

What actually shipped is a lock, a scoring clamp, and extra-labeled controls. That is the whole MVP. The embarrassing part is that we had already been citing numbers the scorer cannot produce.

## Technical details

Phase 1 wrote `configs/methodology-lock.yaml` as **METH-LOCK-20260917**, SHA-256 `f4453cdbf4388b131c9426efe368dbba8a9681c5e59e4b17dd963f0c96e12adb`. `protocol.yaml` now matches the lock: dense revision, generation `T=0.1`, bootstrap seed `221` / 1000 resamples, qrels `llm_judge_adjudicated`. Any report that still says BM25 `k1=1.5` or `T=0.0` is a defect. The lock wins: `k1=1.2`, `T=0.1`.

Phase 2 made `src/evaluation` the only headline scorer. `execute_evaluation.py` no longer pastes `0.642` / `0.671` / CI strings. `write_headline_tables` emits tables 1–4 as `NOT_RUN` with LLM-judge captions because qrels are `llm_lexical_proxy` and rankings plus human G2 are missing. `headline_ci()` calls `family_clustered_mean_ci({})` so empty families stay `NOT_RUN`. The **0.671 vs 0.342** IR-H contradiction is retracted.

Phase 3 kept G0; added G-oracle and G-random packers; generation stays `NOT_RUN` and `refusing_mock_as_result`; answerability stays `NOT_RUN` (empty labels). Leakage diagnostic: historical 74 vs current 73, `shared_document_ids=0`, `shared_source_paths=73`, IR-H delta `NOT_RUN`. Artifact: `results/leakage-diagnostic.json`. Controls are extra-labeled; primary RQ2 remains IR-B / IR-D / IR-H.

`generate_f1_freeze` now raises `SystemExit` `f1_overwrite_forbidden`. Tests: **363 passed / 0 failed** in `06_implementation` (`python -m pytest -q -o pythonpath=.`). Tester: [tester-full](4bf87e77-82a0-4ecc-9e0a-4e0ba753ac98). Reviewer cycle 2: 8/10, `critical_count=0`, auto-approved with warnings ([review](9720c177-ed91-45f0-b822-1ea7d05ff65e)). Cycle-1 critical was leftover numeric table 3/4. Non-blocking warnings: `execute_f1_freeze` overwrite check sits after the corpus gate; table 3/4 markdown asserts are thin; claim-audit leftover narrative; lock omits a `corpus_manifest_hash` knob.

## Decisions

Lock existing knobs; do not invent a second pipeline. Treat mismatched slides/reports as bugs, not as alternative configs. Refuse mock generation success as a result. Do not let extra controls become primary RQ2. Do not commit unless the user asks — that ask is still open.

Rejected: rematerializing the corpus to “fix” hashes; backfilling headline nDCG from proxy qrels; shipping IR-R / GraphRAG as if they were missing failures of this plan.

## Lessons

Hardcoded table cells outlive the experiment. Cycle 1 proved it: we clamped IR tables and still left numeric generation tables. Empty CI input is the only honest CI. Shared source paths with zero shared document IDs is leakage-adjacent, not an IR-H delta. A freeze that cannot overwrite F1 is worth more than another narrative claim-audit.

## Next steps

This plan is done. Remaining work is **human G2** under the retrieval-qrels protocol and a **corpus release** with applicability review — not another methodology-freeze cook. Keep tables `NOT_RUN` until frozen rankings and human-double-adjudicated G2 exist. Owner: evaluation / annotation track. Do not git-commit until asked.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
