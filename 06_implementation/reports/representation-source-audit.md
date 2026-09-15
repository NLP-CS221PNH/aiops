# Representation source audit

Date: 2026-09-13. Reviewer: Codex source-audit agent, independent of renderer implementation. Scope: local technical inspection of the existing safe export and six train incidents. This report is not an A/B/C human review or permission to share telemetry.

## Prerequisite result and execution scope

The plan-02 **local technical prerequisite passes** against the current safe package. Its full plan gate is still `pending_human_reviews_and_consumer_acceptance`; the upstream in-progress status is accurate. All three human review records have `status=pending`, `reviewer=null`, and `reviewed_at=null`. The implementation must preserve that distinction.

The current user's explicit plan-04 `--auto` request authorizes local representation tooling, artifact generation, and tests. This local work proceeds under that request, with the narrower technical gate recorded in `configs/representation-execution-authorization.json`. It does not turn pending upstream human reviews into approvals, authorize external transfer, launch downstream experiments, choose a dev winner, or satisfy F1. No upstream receipt or source file was changed.

| Evidence | Current check |
|---|---|
| Safe consumer `src.data.common.validate_inference` | Pass: 90 incidents, 9,633 evidence rows, exact fields/files/hashes, joins and half-open windows |
| Input manifest SHA256 | `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4` |
| Safe content hash | `f97a19dbbd3a9aebf3f4846e7b2bd62b736bf35938be0a5a8690a805d98aca30` |
| Frozen source revision | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` |
| Receipt evidence hashes | 26 non-private/split-map entries independently rehashed, all match |
| Explicitly unopened private files | `data-audit.json`, `ground_truth.jsonl`, `source-census.json`; their hashes are not independently reverified by this audit |
| Existing input-validation report | Recorded pass: 360 files, 90 incidents, 54/18/18 split, 30 disjoint families; its file hash matches the receipt |
| Existing environment evidence | Recorded local CPU pass in CPython 3.11.9/PyArrow 21.0.0: two fresh isolated processes, same two train IDs and content; report hash matches receipt |
| Human gate implementation | `src/data/review_receipt.py` requires A/B/C approved identities, dates, and exact manifest when `require_human=True`; the current records cannot pass |

The full source validator was not rerun here: it opens raw/private source artifacts outside this audit's boundary. The environment replay was not rerun or rewritten because its timestamp/resource evidence is already bound by the existing receipt. The recorded 48 data tests and 83 combined data/protocol tests are upstream evidence, not newly executed tests in this audit. The environment evidence is direct code-cell execution, not a Jupyter-kernel run, and supplies no tokenizer validation.

Reproduce the safe check from the pack root after setting `PYTHONPATH` to `06_implementation`:

```powershell
./06_implementation/.venv/Scripts/python.exe -B -c "from pathlib import Path; from src.data.common import validate_inference; print(validate_inference(Path('06_implementation/data/inference')))"
```

## Manager selection and content boundary

`configs/representation-manager.json` contains 72 sorted train/dev opaque IDs and six audit IDs. The manager read only `data/private/split-map.tsv` for partition/family administration. It selected the first lexicographically ordered train incident for each newly encountered opaque family, stopping at six distinct families. No ground truth, source-case mapping, injection time, qrels, dev scores, or test telemetry content was used to select the sample.

The split-map SHA256 is `d7941d1487d4ec7e3943692b2911ea422bf6b14d620fd8e150324161fc17b8c7`. It contains 54 train and 18 dev IDs in the candidate allowlist; all 18 test IDs are excluded. Per-ID family and split values are absent from the manager output and must never be supplied to the renderer. Pass only opaque ID lists across that boundary. The manager's automated selection is not a claim that human A selected or reviewed these incidents.

Only the safe package's six selected train records were inspected for telemetry content. All-90 validation was structural. The upstream data handoff documents earlier holdout-exposure limitations; this audit does not erase that history or claim pristine overall holdout blinding.

## Source selector restrictions

`scripts/prepare-incidents.py` was read as source evidence, never imported or executed. Its SHA256 is `2767d57a1e9639015d68fdccc582bee8fb8a04e53f34937384b8cf0383adc26c`.

1. The observation function accepts an opaque incident ID and reads telemetry. It derives the window from the first/last metric timestamps, not injection onset. The separate label builder owns family/split and fault metadata.
2. Log eligibility is the metric window, with timestamps bounded by the first and last metric seconds. The output window is the half-open interval `[first metric second, last metric second + 1s)`.
3. The source log candidate filter matches `error|exception|fail|timeout|timed out|refused|unavailable|deadline|panic|denied`, case-insensitively. If no candidate matches, it uses the last 200 in-window rows in existing input order, then sorts candidates by descending timestamp and descending source row. “Last 200” is not independently proven to mean the most recent 200 by event clock.
4. It redacts candidate text and deduplicates by `(service, text with number-shaped tokens replaced by <N>)`. This upstream rule can merge distinct numeric codes, ports or versions. It keeps at most four selected logs per service and 48 per incident, then sorts selected logs by service, timestamp, and evidence ID.
5. The legacy template query includes only the first eight selected logs, sliced to 300 characters each, and six metric names ranked by the descriptive change score. It contains no trace content. The safe export removes this legacy synthetic query; the audit replays its ordering/slicing on allowed safe excerpts, never consumes `symptom_query` from a source observation.
6. Metrics summarize all samples/columns; the source observation references the first 12 ranked metrics. All 6,603 safe metric summaries are available to the representation candidate universe. Change scores compare first/last-quarter summary values and are descriptive, not causal.
7. The trace selector chooses up to two spans per service: nonzero-status candidates if any, otherwise the service's spans, sorted by descending raw duration and ascending row. Null status comparisons do not mean zero. The safe export keeps duration and status semantics unknown; selection bias does not establish an error interpretation.

These restrictions are upstream loss. Plan 04 can measure retained/dropped/partial evidence only within the safe universe; the identities and semantic importance of discarded raw rows remain unknown. Adding raw logs requires a new versioned plan-02 export.

## Six-train audit

All six windows and all 97 log, 433 metric, and 84 trace records resolve to the correct incident and exported window. Observation references resolve; the log and trace lists match the exported evidence for each inspected incident. Each incident references 12 of its available metric summaries. No source file or evidence text was modified.

| Incident | Logs / services | Services in legacy first 8 | Omitted service count | Metric summaries (partial) | Traces / services |
|---|---:|---|---:|---:|---:|
| `inc_08457c0fbff4700e` | 27 / 9 | adservice, cartservice | 7 | 73 (4) | 14 / 7 |
| `inc_0991de462f9a6c05` | 20 / 6 | adservice, cartservice | 4 | 75 (3) | 14 / 7 |
| `inc_0f782051d78bc07a` | 2 / 2 | frontend, recommendationservice | 0 | 69 (15) | 14 / 7 |
| `inc_15361b2d5df6a488` | 20 / 6 | adservice, cartservice | 4 | 70 (2) | 14 / 7 |
| `inc_1bd0f85d1967890c` | 27 / 9 | adservice, cartservice | 7 | 75 (0) | 14 / 7 |
| `inc_1c35829e1a5668b7` | 1 / 1 | frontend | 0 | 71 (4) | 14 / 7 |

The four larger log sets lose every selected service after cartservice in the legacy first-eight rendering. The six-service sets omit currencyservice, frontend, recommendationservice, and shippingservice. The nine-service sets also omit checkoutservice, emailservice, and paymentservice. This demonstrates ordering bias, not a measured retrieval-quality difference.

All samples satisfy four logs/service and 48 logs/incident. No surviving duplicates remain under the source's service-plus-number-normalization rule when applied to safe strings; that does not quantify already discarded raw duplicates. The two small log sets have all 2/2 and 1/1 logs matching the error regex; the four larger sets have zero matches, consistent with the source fallback path. The raw candidate sets were not reopened, so this consistency check is not an independent raw-selection replay. No legacy 300-character slicing loss occurs in these particular first-eight excerpts; the risk remains for other/fixture data.

Across the selected traces there are 74 status-0, six null-status, two status-14, and two status-4 records. These are numeric observations only. All 433 metric summaries retain unknown units; 28 are partial and 405 complete, with no all-missing metric in this sample. All-missing behavior must be checked with a synthetic fixture.

## Semantics and remaining limits

Use UTC clocks, the exact exported retrospective window, unknown duration/metric units, nullable raw trace status, and explicit missing metric states. Preserve `frontend` and `frontendservice` separately; there is no approved alias merge. Preserve source technical literals, including HTTP codes, exceptions, versions and ports; no blanket numeric replacement or translation is justified downstream.

R1 means selected, exported, redacted log text. It does not mean unprocessed raw telemetry. The upstream bounded regex redaction does not cover every sensitive-looking field: the inspected safe logs include payment request field values. Their authenticity or privacy status is not established here; this report does not reproduce them. Keep the work local and preserve the existing separate payload/sharing review gate. Renderer integrity tests cannot certify universal privacy, source completeness, explanation support, or retrieval quality.

The source/manager audit is technically complete. Actual A/B/C provenance, representation, and common-bundle human reviews remain pending; downstream dev selection and F1 belong to plan 08.
