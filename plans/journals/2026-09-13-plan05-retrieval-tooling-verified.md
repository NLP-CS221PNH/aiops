---
title: Plan05 retrieval tooling verified
date: 2026-09-13
summary: 269 tests pass; technical runners delivered while real pilot awaits reviewed corpus and neural resources.
---

# Plan05 retrieval tooling verified

## What happened

The user clarified Plan05 scope: build and test retrieval runners now, then wait for a reviewed corpus before any real pilot. Implemented canonical BM25, exact normalized-cosine search, pinned local E5 and optional BGE adapters, RRF, strict input/release/frozen gates, fingerprints, immutable cache/checkpoint publication, validating consumers, CLI and notebook.

Independent final verification passed 269 full-suite tests including 66 retrieval tests, with zero failures, errors or skips. Synthetic delivery evidence passed 15 CLI expectations, 28 artifact hashes, four manifest reader checks and the notebook path. Automated review passed at 9.3/10 with zero remaining material findings. Review fixes protected shared cache publication, interrupted retry attempts, external schema references and freeze identity bindings; existing upstream contracts and tests were not weakened.

## Decision and limits

The user-authorized technical delivery is complete; full 05.runners is not accepted. No real corpus indexing/pilot, E5/BGE forward pass, actual BGE-tokenizer verification, embedding-cache performance measurement, human signature, quality score, winner selection or frozen test execution is claimed. Generic pair-budget tests use the real E5 tokenizer only. PyTorch/Transformers and pinned model weights remain absent; optional reranker stays disabled.

All Plan05 phase files were swept and received durable evidence notes. Status/index changes used supported ak plan commands. The plan validates and remains in-progress with 0/3 complete phases and 0/14 checked original items: the installed CLI supports only whole-phase checking, and no phase's real-pilot/human criteria are wholly met. Detailed partial completion is recorded rather than bulk-checking unfulfilled requirements.

## Evidence and next steps

See [progress](../../06_implementation/reports/plan05-progress.md), [runbook](../../06_implementation/docs/retrieval-runbook.md), [tests](../../06_implementation/reports/retrieval-tests.md), [review](../../06_implementation/reports/retrieval-code-review.md), and [technical handoff](../../06_implementation/reports/retrieval-handoff.json).

A/B must release the reviewed corpus. B/C must provision and verify pinned neural runtime/assets. Controller/06 provides train/dev allowlists; then record actual pilot, warm/cold/restart evidence and consumer acceptance. Plan08 owns final selection, authenticated F1 and post-F1 test inputs. No commit/publication was performed in this non-Git workspace. AgentWiki publish skipped.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
