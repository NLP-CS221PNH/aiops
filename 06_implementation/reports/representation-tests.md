# Plan 04 independent test report

Result: **PASS — 203 tests, 0 failures, 0 errors, 0 skips**, in 46.300 seconds on 2026-09-13. This includes 43 new representation tests and 160 existing protocol, data-boundary, provenance, corpus and citation tests. The final representation-only run passed all 43 tests in 2.643 seconds.

The tester agent wrote the representation tests independently, using manually authored synthetic records with the exact safe-export schemas. Production files were not edited by the tester. Pipeline fixtures replace only manager selection and safe input loading; real renderers, schema checks, local tokenizer, hashing, publication and replay execute unchanged. No real test telemetry, test labels, qrels, model APIs, retrieval, or generated answers were used to construct these tests. Existing data-boundary tests select train fixtures through their established management path.

## Commands and environment

Working directory: `06_implementation` under the research-pack root. Runtime: local `.venv/Scripts/python.exe`, Python 3.11.9, with the pinned local `tokenizers` 0.21.4 assets. The existing protocol tests need PyYAML 6.0.2 from the already installed user site; the venv supplies pyarrow. No dependency installation was performed.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_representation*.py' -q
.\.venv\Scripts\python.exe -B -c "import sys,site,unittest; sys.path.append(site.getusersitepackages()); result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not result.wasSuccessful())"
```

An initial venv-only baseline reported an import error for absent PyYAML; this was an environment-path issue. Existing protocol tests separately passed all 52 tests under the system Python, and the final combined command above passed all 203 tests. Tests were not skipped, narrowed or weakened to obtain the final pass.

## Acceptance evidence

| Contract | Independent evidence |
|---|---|
| Safe boundary | Extra/private fields, nested private values, missing required fields, cross-incident references, cross-modality references, duplicate and unreferenced evidence fail closed. |
| Mutation after validation | Fifty subcases across select/render/budget/bundle/generate reject changed private fields, nested gold text, window/policy, metric imputation, trace semantics, duplicate/missing/non-record rows with `SAFE_INCIDENT_MUTATED`. |
| Window and semantics | Half-open boundaries reject the exclusive end; the last millisecond survives. Injection-based window policy, interpreted trace units/status and all-null imputation are rejected. |
| Determinism and entities | Twelve input permutations include equal timestamps and shuffled reference sets. HTTP 500/503, exceptions, versions, ports, Unicode and legitimate service names matching fault vocabulary survive. R1 preserves literals; R2 changes whitespace only. |
| Selector accounting | Service round robin covers the alphabetically last service. Ordinary logs remain usable. Selected and dropped IDs cover the safe candidate universe, with explicit reasons. |
| Provenance | R1/R2 source spans match. Normalization segments cover every retained source code point contiguously; reconstructed text hashes and source hashes match independently. |
| Actual tokenizer | Prefix plus two special tokens are counted. Long input is not silently truncated. Exact-limit and one-token-less cases test whole-block clipping. |
| R1/R2 fairness | A real E5 fixture containing repeated `zulu` + U+0085 + `database` measures R1=307 and R2=187 tokens. At a 187-token limit, both variants drop that same whole log, so R2 cannot refill its freed space. No mock tokenizer is used for this case. |
| Missing/long evidence | Missing traces, all-null metrics, null/nonzero neutral trace status, empty text, zero evidence and a single oversized log retain explicit missing/insufficient/drop states. |
| Generator fairness | G0/GB/GD/GH placeholders receive identical complete bundle objects and hashes. Changing query budget or the default representation leaves the bundle unchanged. Bundle tokens use a separate budget and omit the retrieval prefix. |
| Replay and stale artifacts | Synthetic build/rebuild/replay is byte-identical. Changed query bytes, forged spans with refreshed outer hashes, upstream/config drift, overwrite under the same version and reuse of an old output directory for a new version are rejected. |
| F1 and review receipts | Test role needs an externally authenticated matching F1 digest mapping. Every required hash is tested. Receipt hashes, evidence freshness, reviewer roles/status and allowed evidence paths are checked with synthetic receipts. |

## Scope and follow-up

These tests establish tooling contracts, not representation quality or a winning variant. The bundle's E5 planning count does not replace the actual generator tokenizer check owned by plan 07. Plan 08 owns F1 authentication and future test materialization.

Testing identified a direct-API gap: replacing a validated log's `text` with a nested private mapping after construction could previously stringify that mapping. The parent fixed the production boundary using canonical snapshots checked at public consumption points. The independent regression now covers 50 mutation subcases and passes; the full 203-test run was performed after this fix. No unresolved test failures remain.

Exact tested source/config/schema/test hashes and run counts are recorded in `representation-tests.json`. Any production change after this report requires affected checks and report hashes to be refreshed before receipt acceptance.
