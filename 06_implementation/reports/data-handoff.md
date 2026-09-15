# Plan 02 data candidate handoff

Date: 2026-09-13. Local technical gate: **pass**. Human A/B/C reviews and actual plan 03/04 acceptance: **pending**. The implementation is ready for those reviews; plan 02 remains in progress and does not authorize downstream experiments, external sharing, Kaggle upload or API calls.

The candidate is `re2-ob-inference-v1`, schema `cs221-inference-v1`, derived from source revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`.

| Frozen artifact | SHA256 |
|---|---|
| `data/inference/input-manifest.json` | `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4` |
| `artifacts/inference-package.zip` | `332717caa25e78ff62cc29a53e675189e598f1e4d98c3e6887e87cb112327527` |

These paths are relative to [06_implementation](../). The exact inference root is `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference`. Its source-free consumer API is `src.data.common.validate_inference(root)`. It loads the pinned configuration and implementation code but does not open raw telemetry, acquisition metadata, labels or private sidecars.

## Contents and boundaries

The ZIP contains exactly these six files; per-file bytes, rows and hashes are owned by [input-manifest.json](../data/inference/input-manifest.json).

| File | Rows | Consumer purpose |
|---|---:|---|
| `incident-index.parquet` | 90 | Opaque incident ID, start, exclusive end and evidence file IDs |
| `observations.jsonl` | 90 | Observation window, public service inventory and evidence references |
| `logs-evidence.jsonl` | 1,770 | Redacted selected logs and opaque row provenance |
| `metric-summaries.jsonl` | 6,603 | Descriptive statistics, null states and source sample endpoint |
| `trace-evidence.jsonl` | 1,260 | Selected spans, raw duration, nullable status and opaque row provenance |
| `input-manifest.json` | — | Exact file inventory, source/config/transform/content hashes |

Schema fields are owned by [configs/data.yaml](../configs/data.yaml). The package has 90 incidents and 9,633 evidence records. There is no family, split, gold, source-case, injection metadata or original synthetic `symptom_query` in the inference records. Plan 04 owns future query construction from retained observations/evidence; source template questions are not real operator questions. The index and observations must be joined by opaque incident ID, never by file ordering. An observation references a selected subset of metric summaries; all 6,603 summaries remain available.

[data/private](../data/private/) is management/evaluator-only. It holds byte-preserving copies of `split-map.tsv` and `ground_truth.jsonl`, `data-audit.json`, and `source-census.json`. The audit records source hashes, physical paths and row maps; a source provenance resolver belongs in this private workflow. Do not give private sidecars or the audit report to a model/demo loader. The source split remains 54/18/18 with 30 disjoint families and exactly the original 90 IDs. The package excludes `.venv`, `.wheelhouse`, notebooks, configuration, scripts, reports, keys, raw files and private sidecars. Runtime/code/configuration are supplied separately as local tooling.

## Verified semantics and usage limits

| Item | Contract and allowed use | Owner for additional evidence |
|---|---|---|
| Metric/log clocks | UTC Unix seconds; no modification of source timestamps | A, reviewed by B |
| Trace clock | `startTimeMillis` supplies UTC Unix milliseconds; ambiguous source clock strings are not event clocks | A, reviewed by B |
| Window endpoint | Half-open `[start, last_metric_second + 1s)`; metric summaries retain `source_sample_end_inclusive`, with conversion `seconds-half-open-v1`; an event exactly at exclusive end is rejected | A/B |
| Duration | Keep `duration_raw` and `duration_unit=unknown`; no conversion to seconds or physical latency claims | A |
| Trace status | Keep integer or null and `status_code_semantics=unknown`; nonzero is not established as an error and null is not zero | A/B |
| Metric unit | Keep descriptive values with `unit=unknown`; suffixes do not establish scale or physical units | A |
| Missing metrics | Preserve null values/counts, `complete`/`partial`/`all_missing` and their reasons; no imputation or automatic zero | A/B |
| Service aliases | Preserve `frontend` and `frontendservice` as distinct raw names; identity/merge state is unknown | A |
| Query construction | Deliberately deferred to plan 04; preserve synthetic provenance and derive only from permitted evidence | Plan 04 owner/B |
| External sharing | Pending A/C review of this exact package; local checks are not an upload approval | A/C |
| Kaggle | Deferred, owner C; no upload/account/quota/Linux/GPU run claimed | C |
| API/models | Disabled; model execution, permissions and costs belong to plans 01/07 | C and plan 01/07 owners |

[Data contract review](data-contract-review.md) records a method limitation: initial unfiltered scouting exposed the existing `pilot-schema.json` example before checking its split, and the coordinator displayed an initial source-observation example that belonged to test. No diagnosis, retrieval tuning, model evaluation or performance decision used those examples. The later content audit used six verified train IDs. This session must not be described as having pristine holdout blinding.

## Commands from the pack root

Use PowerShell in `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack`. The tested interpreter is the explicit local venv below. Set its module search path for this shell:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) '06_implementation'
```

The full management source gate rehashes all 360 inventory files plus pinned metadata/scripts, checks the 90 IDs, split/families, schemas, row bounds, windows and joins. Run its read-only API before rebuilding a candidate; exporter-only validation checks its four pinned source inputs and is not a substitute for this full gate.

```powershell
./06_implementation/.venv/Scripts/python.exe -B -c "from src.data.validate_inputs import validate_inputs; r=validate_inputs(); print(r['status'], r['counts']['incidents'], r['counts']['files'])"
```

Export inference first, then management sidecars, then persist the management validation report. On a fresh destination, private export must precede any separate command that writes `source-census.json` into that same destination: it atomically publishes all four private files together. On this already complete candidate, the commands below are idempotent when bytes are unchanged.

```powershell
./06_implementation/.venv/Scripts/python.exe -B -m src.data.export_inference_data
./06_implementation/.venv/Scripts/python.exe -B -m src.data.export_private_sidecars
./06_implementation/.venv/Scripts/python.exe -B -m src.data.validate_inputs
```

The strict consumer check below reads the safe derivatives and their manifest without opening source/private data. It verifies exact fields/population, hashes, joins, windows and the matching config/transform contract.

```powershell
./06_implementation/.venv/Scripts/python.exe -B -c "from pathlib import Path; from src.data.common import validate_inference; print(validate_inference(Path('06_implementation/data/inference')))"
```

Run local replay, package generation and the plan-02 test suite:

```powershell
./06_implementation/.venv/Scripts/python.exe -I -B 06_implementation/src/data/build_environment_report.py
./06_implementation/.venv/Scripts/python.exe -B -m src.data.package_inference
./06_implementation/.venv/Scripts/python.exe -B -m unittest discover -s 06_implementation/tests -p 'test_data_*.py' -v
```

Validate the review evidence binding and then explicitly require named human reviews when accepting the full gate:

```powershell
./06_implementation/.venv/Scripts/python.exe -B -c "from src.data.review_receipt import validate_review_receipt; print(validate_review_receipt('06_implementation/reports/data-review-receipt.json','06_implementation/data/inference'))"
./06_implementation/.venv/Scripts/python.exe -B -c "from src.data.review_receipt import validate_review_receipt; print(validate_review_receipt('06_implementation/reports/data-review-receipt.json','06_implementation/data/inference',require_human=True))"
```

The second command currently fails with `HUMAN_REVIEW_PENDING`, as intended. Rerunning commands that replace evidence reports (especially the environment report with new timestamps/resources) invalidates the old review receipt's evidence hashes; regenerate and review the changed evidence before claiming the receipt still passes. Do not weaken the validator or edit hashes to conceal a change.

## Evidence and runtime

- [Input validation](input-validation.json): 90 IDs; 360/360 inventory files match; 270 telemetry and 90 label files; 922,484,805 inventory bytes. Source scripts and data were not rewritten.
- [Final test results](data-test-results.md): 48/48 data tests pass; 83/83 combined data/protocol tests pass, with no failures, errors or skips. The Windows junction case ran. [JSON receipt](data-test-results.json) binds the tested artifacts.
- [Code review](data-code-review.md): 9/10 technical assessment, zero critical or open implementation findings. Independent train provenance replay matched 97 log rows, 84 trace rows and 433 metric summaries with zero mismatches.
- [Debugger report](debugger-report.md): 45/45 targeted checks pass on its recorded intermediate implementation hashes; the final suite/review cover the later frozen candidate. Findings included invalid UTF-8, bool/int schema ambiguity and malformed receipt containers and were repaired.
- [Full data replay](data-replay.json): a fresh isolated process regenerated all 90 incidents from the four pinned observation inputs and reproduced all six inference files byte-for-byte.
- [Environment receipt](environment-check.json): two fresh isolated CPython processes replayed notebook code cells on the first two sorted train IDs, `inc_08457c0fbff4700e` and `inc_0991de462f9a6c05`, with identical content and IDs. This was direct code-cell execution, not a Jupyter kernel run.

The measured environment is CPython 3.11.9, PyArrow 21.0.0, Windows 64-bit, 16 logical CPUs and 34,142,842,880 bytes physical RAM. Unavailable processor/ABI fields remain null; GPU was unused and unprobed. The notebook keeps outputs and execution counts empty. Hardware availability and elapsed times are observations, not reproducibility hashes. The [environment recipe](environment-recipe.md) and [hash lock](../configs/requirements-lock.txt) explain fresh Windows setup. The Windows wheel cannot serve as a Linux/Kaggle lock; C must obtain and record a compatible Linux wheel when that branch is authorized. API/network/GPU are disabled in [runtime.yaml](../configs/runtime.yaml).

Regex redaction and technical tests cover specified fields/patterns; they do not certify every possible sensitive string. Evidence offsets and summary equality do not establish relevance, diagnosis accuracy or model quality.

## Acceptance, versioning and recovery

[data-review-receipt.json](data-review-receipt.json) binds this candidate to exact evidence hashes and explicitly lists A/B/C as pending, with no names or dates invented. A reviews source/time/null/alias and selected payloads; B reviews the boundary, test oracle and independent replay; C reviews runtime/package and the separate sharing decision. Record a real reviewer's identity, time, scope and the exact manifest only after review. Consumers 03/04 have an interface ready for review; actual acceptance and implementation remain pending the complete plan-02 gate and applicable protocol gate.

Treat this release directory and ZIP as immutable. Export and packaging use validated staging, fixed ordering and atomic publication; rerunning identical inputs is allowed, while different bytes at an existing destination fail `OUTPUT_VERSION_CHANGE_REQUIRED`. Never merge a partial staging directory with a release. On failure, keep the original candidate intact, fix the cause and publish to a new versioned destination inside `06_implementation` using the CLI `--output` options. Do not rerun acquisition or source preparation to force a pass.

A change to source/config/schema/redaction/text/transform code creates a new candidate version, output directory and manifest; preserve the prior exact bytes. Rebuild package, tests, replay and review evidence for the affected contract, notify/coordinate the 03/04 owners before consumption, and record actual acknowledgments. Receipt validation rejects changed manifest or evidence. Cache reuse requires matching source/config/transform hashes and every file hash. Roll back by selecting the complete previous version with its matching code/config/receipt, never mixing files across versions. Model/corpus-specific cache keys remain downstream work.

The workspace has no Git repository, so no commit, push or PR was created. Local completion records are in [pm-data-progress.md](pm-data-progress.md) and the local journal; they are not human approvals or published research results.
