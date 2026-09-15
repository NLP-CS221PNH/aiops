# Retrieval technical verification

The final independent tester run passed **66 retrieval tests** and **269 tests
across the repository**, with no failures, errors, or skips. Source, configuration,
schema, and retrieval test hashes were unchanged during the final full run.
The tester edited no production source or pre-existing tests.

| Run | Tests | Result | Measured time |
|---|---:|---|---:|
| Retrieval engines and contracts | 66 | pass | 3.054 s |
| Full repository discovery and execution | 269 | pass | 42.032 s |

The full runner's execution-only time was 41.855 seconds; the larger value
includes discovery. The machine-readable [test receipt](retrieval-tests.json)
records UTC start/end, all 269 test outcomes, dependency versions, source and
artifact hashes, and exact commands. This is an automated technical review by
`/root/retrieval_tests`, not a human corpus approval.

## Evidence exercised

- Independent BM25 and RRF arithmetic, documented in
  [the fixture derivations](../tests/fixtures/retrieval/README.md), plus technical
  tokens, repeated query terms, ties, empty results, identity checks, and invalid
  ranks/parameters. BM25 tolerance is `1e-12`; RRF tolerance is `1e-14`.
- Exact cosine search against invented unit vectors, including negative/zero
  scores, stable ties, normalization, overflow/underflow resistance, dimensions,
  finite values, zero vectors, and duplicate IDs. Tolerance is `1e-6`.
- The real pinned E5 tokenizer: 600 single-token `alpha` terms plus two prefix
  tokens and two special tokens produce 604 input tokens. The 512-token cut
  retains 508 body tokens and removes 92; batch padding is excluded from counts.
  The helper rejects cuts that remove the entire body.
- Generic pair-budget accounting with the real local E5 BERT tokenizer:
  both 600-token sides and three special tokens total 1203, then cut to 512
  while retaining both sides. This checks the pair helper, **not the unavailable
  BGE tokenizer or reranker model**. Candidate guards run before model access.
- Fifteen independent cache-key changes, payload integrity, immutable entries,
  and a shared-key writer lock. Pinned model asset checks use deliberately
  non-loadable synthetic bytes; no synthetic file is loaded as a model.
- Strict configuration, corpus/query body hashes, allowlists, private and nested
  forbidden fields, local schema references, fixture path/ID separation, and
  early corpus-release/F1 rejection before downstream text reads.
- An interrupted synthetic runner resumes only its pending record. Completed
  record bytes remain unchanged, and a completely resumed run performs no new
  search. An interrupted retry preserves its previously committed failed attempt.
- Missing real model assets create explicit failed IR-D/IR-H records for every
  synthetic incident. Readers validate empty/short results, record completeness,
  provenance, immutable filenames, and checksums. Forged document identity is
  rejected even after its filename and every enclosing checksum are recomputed.

## Reproduce

From `06_implementation`, retain the project runtime and existing dependency
roots. The focused command is:

```powershell
.\.venv\Scripts\python.exe -B -c "import sys; sys.path.insert(0,'.retrieval-deps'); import unittest; result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests',pattern='test_retrieval*.py')); raise SystemExit(not result.wasSuccessful())"
```

The complete regression command preserves the prior protocol suite's existing
user-site PyYAML resolution:

```powershell
.\.venv\Scripts\python.exe -B -c "import sys,site,unittest; sys.path.insert(0,'.retrieval-deps'); sys.path.insert(0,'.corpus-deps'); sys.path.append(site.getusersitepackages()); result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not result.wasSuccessful())"
```

No installation was performed by the tester. Temporary retrieval artifacts stay
under `.test-work/retrieval` and are cleaned by each fixture. CLI/notebook delivery
checks are recorded separately in
[the reproducibility receipt](retrieval-reproducibility.json); this test receipt
also binds the verification script and notebook hashes.

## Scope limits

No real E5 embeddings, BGE reranking, incident pilot, private retrieval input,
gold/qrels access, human judgments, frozen test execution, quality scores, or
winner selection were performed by these retrieval tests. Real model inference
and the reviewed-corpus pilot remain separate prerequisites. The tests verify
the available implementation and failure behavior without treating synthetic
results as pilot evidence.
