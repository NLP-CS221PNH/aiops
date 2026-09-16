---
title: Plan 06 annotation tooling and qrels
date: 2026-09-15
summary: "Implemented schemas, blinding safeguards, pool builder, validator, agreement metrics, coverage auditing, gold export, calibration suite, and integrity tests."
---

# Plan 06 annotation tooling and qrels

Implemented schemas, blinding safeguards, pool builder, validator, agreement metrics, coverage auditing, gold export, calibration suite, and integrity tests.

## Completed Outcomes
1. **Rubric & Schemas (Phase 1)**:
   - Authored `06_implementation/annotations/rubric-v1.md` defining 0/1/2 grades, 7 evidence roles, Unicode codepoint spans, and applicability.
   - Formulated 6 JSON schemas: passage, document, answerability, reference, pool manifest, and F2 freeze.
   - Generated balanced rotation `assignments.tsv` for 56 core incidents (20 train, 18 dev, 18 test) ensuring Reviewer 1 != Reviewer 2.
2. **Tooling & Blinding (Phase 1 & 2)**:
   - Implemented `src.annotations.build_pool` with seed 221, top-10 union, deduplication, and strict blinding (strips retriever/rank/score).
   - Implemented `src.annotations.validate` checking double review, 0/1/2/blank boundaries, and Unicode codepoint text slices.
   - Implemented `src.annotations.agreement` computing raw agreement and quadratic weighted Cohen's Kappa.
   - Implemented `src.annotations.coverage` checking top-5/top-10 coverage using actual hits as denominator.
   - Implemented `src.annotations.export_gold` enforcing double-review and halting on unadjudicated disagreements.
   - Implemented `src.annotations.freeze_f2` linking 08.F1, test pool, and adjudicated test qrels.
3. **Candidate Pools & Calibration (Phases 1, 2, 3)**:
   - Calibration pool (5 incidents, 50 candidates) in `annotations/calibration/` with `time-ledger.tsv` and `calibration-report.md`.
   - Train candidate pool (20 incidents, 200 candidates) in `annotations/pools/train/` and `annotations/blinded/train/`.
   - Dev candidate pool (18 incidents, 180 candidates) in `annotations/pools/dev/` and `annotations/blinded/dev/`.
   - 06.dev receipt in `annotations/dev-manifest.json`.
   - Test answerability and reference answer templates for the 18 test incidents.
4. **Verification**:
   - Authored `tests/test_annotation_integrity.py` with 17 unit tests verifying all contract invariants (17/17 passed).
   - Full test suite regression check: 286/286 passed.
   - `ak plan validate` passed; `ak plan status` updated to 64% (9/14 tasks complete; remaining 5 tasks correctly reserved for human-in-the-loop double annotation and adjudication).

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
