# Plan 05 execution contract

2026-09-13. Accepted input: `plans/260913-0057-cs221-05-retrieval-baselines/plan.md`
and all three phases, executed with `ak:codex-goal` and `ak:cook --auto`.

The user clarified: **Build and test runners now; wait for a reviewed corpus
before the pilot.** This is the stop condition for the current delivery. The
full 05.runners milestone stays pending until real pilot evidence and consumer
acceptance exist. Synthetic fixtures cannot discharge pilot requirements.

Outcome: implement local BM25, exact E5 cosine, RRF, conditional reranking,
strict inputs, fingerprinted caches/checkpoints, a validating consumer reader,
CLI/notebook wrapper, independent fixtures and technical test/review receipts.
Keep legacy sources, upstream manifests, queries, private data and tests intact.
Do not weaken, narrow, skip or delete existing tests to satisfy the goal.

Current scout: Python 3.11, standard-library modules and unittest; configuration
uses JSON as a YAML subset. Existing code is in `src/data`, `src/corpus`,
`src/representations.py`; the reference scorer is `../scripts/preview-retrieval.py`.
There is no Git repository. The 440 corpus chunks are conditional candidates,
with zero released/indexable chunks; 216 queries cover 72 train/dev incidents
and three variants. Tokenizer assets exist, model weights do not. No new public
upstream signatures or schema fields will be changed.

Reviewed implementation sequence:
1. Establish strict retrieval-only schemas/config and release/allowlist gates.
2. Implement engines independently from safe input loading, cache and orchestration.
3. Test formulas, IDs, nonfinite values, actual-tokenizer budgets, invalidation,
   interrupted resume, tampering, private paths and F1 prerequisite failures.
4. Independently review all acceptance criteria and run relevant plus existing tests.
5. Synchronize all plan phases honestly, document the blocked pilot and write a journal.

Acceptance for this user-authorized slice: technical tests pass; documented CLI
works on clearly synthetic fixtures; production preflight rejects the current
unreleased corpus before indexing; unavailable model/runtime is explicit; run
reader detects tampering, omission and provenance mismatch; no real pilot/test
rankings or quality metrics are produced. Model inference tests requiring absent
weights are identified as unperformed, not replaced with fabricated embeddings.

Validation: local Python with isolated dependency paths, `python -B -m unittest
discover -s tests -v`, synthetic CLI run/validate/resume, and read-only preflight.
No generator, qrels, real test materialization, dev winner selection, external
telemetry transfer, publication, commit or upstream release is in scope.

Human roles A/B/C remain pending; delegated agents provide technical review only.
Owner A/B must release the corpus; owner B/C must provision pinned E5 weights and
runtime before real dense execution; 06 selects the pilot allowlist; 08 owns F1,
authenticated freeze hashes, test input materialization and final evaluation.
