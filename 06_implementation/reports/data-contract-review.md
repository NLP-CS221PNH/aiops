# Data contract review — plan 02

Audit date: 2026-09-13. Reviewer: Codex source-audit agent. This is a technical review receipt, not a signature from the plan's human owners A, B or C.

The source pack supports an immutable, allowlisted derivative. The audit found no missing, modified or size-mismatched inventory files. Time boundaries need an explicit derivative conversion; duration units, status-code meanings and service aliases remain unverified. Source preparation code must not be imported or run as the new exporter.

## Scope and evidence method

- Read the three phase files and `scripts/prepare-incidents.py`; no local `AGENTS.md` was found by a workspace file search.
- Read source metadata and existing Python patterns; no acquisition, network request, source pipeline, model, embedding, notebook or remote loader was executed. Source files were not edited by this audit. Its only output is this report.
- Recomputed SHA256 and size for all 360 inventory paths; read Arrow schema and Parquet row counts for all 270 telemetry files. Dev/test checks were restricted to structural schemas, counts, IDs and hashes after the initial scouting exception below.
- Chose six train IDs deterministically as the first six sorted train `incident_id` values from the management-only `02_datasets/processed/split-map.tsv`; no source-case or fault labels were needed to choose them.
- Inspected raw metric rows and the timestamp/service/duration/status columns of those six incidents. Raw log message strings and raw trace identifiers were not reproduced in the report.
- Runtime for these passive reads: local Android NDK CPython 3.11.4 with pack-local PyArrow 21.0.0. This audit runtime is evidence of a working reader, not the final clean-environment lock. The saved historical source-preparation receipt names CPython 3.11.9.

Method limitation: initial unfiltered scouting displayed the existing `pilot-schema.json` example snapshot before its split had been checked. The coordinating agent also reported that an initial source-observation example belonged to test. No diagnosis, retrieval tuning, model evaluation or performance decision used those examples. The dedicated content audit below is confined to the six verified train IDs. Do not describe the overall session as having pristine holdout blinding.

## Census and provenance

| Check | Actual result |
|---|---|
| Dataset revision | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` |
| Source registry path | `02_datasets/acquired/meta/source-registry.json` |
| Inventory rows | 360 unique paths: 270 observation files and 90 label files |
| Inventory bytes | 922,484,805 |
| Hash and size recomputation | 360/360 match inventory; no failure |
| Incident population | 90 source IDs |
| Raw metric row count | 128,742 from Parquet metadata |
| Raw log row count | 15,053,223 from Parquet metadata |
| Raw trace row count | 34,461,235 from Parquet metadata |
| Processed observation records | 90, covering 90 IDs |
| Processed log evidence records | 1,770, covering 90 IDs |
| Processed metric summaries | 6,603, covering 90 IDs |
| Processed trace evidence records | 1,260, covering 90 IDs |
| Independently checked split map | 90 unique IDs, 30 families; train/dev/test 54/18/18; zero families crossing splits |

The inventory uses `data_kind=observation` for each raw modality and `data_kind=label` for injection files. An injection path is administrative provenance and must never enter the inference manifest. An opaque incident ID does not make an entire inventory record safe. Family IDs also remain private despite their hashed spelling.

The eight processed artifacts below were independently rehashed and all match their entries in `MANIFEST_RESEARCH_SHA256.txt`:

| Path under `02_datasets/processed/` | SHA256 |
|---|---|
| `observations.jsonl` | `10f858579442a17ffbb254f10439be310276a114b780bc4049bf2b003dbfd641` |
| `logs-evidence.jsonl` | `526af35758e028686a62b14b776732d61e717999c062f9aac5ebacfb57ab2813` |
| `metric-summaries.jsonl` | `21a6a1f2dbd37d45566b3de669f520c0069a220ebc2d4a2f0034778e026cd8a1` |
| `trace-evidence.jsonl` | `f3416868364dcf116b76eb2e74602635b6ba2fce3934e48b3ef7e2c2238eaf91` |
| `incident-profiles.jsonl` | `a2e875e0e26cd39dd139a457825108af511ac5d26849b9bcbaee9859b5493fc4` |
| `profile-summary.json` | `4762db4395671d9972f3b217ff44ecb3e853ffd6081217e2ac790c380032e2dd` |
| `split-map.tsv` | `d7941d1487d4ec7e3943692b2911ea422bf6b14d620fd8e150324161fc17b8c7` |
| `labels/ground_truth.jsonl` | `bd02f4e8393e9ccfab3dd8b9bb1e016abee79bacb58aa9a8888c05240b8ee893` |

Additional independently measured hashes:

| Path | SHA256 |
|---|---|
| `02_datasets/acquired/inventory.tsv` | `7af2a2829ca2c62f0da743b88b9c80f6655475d414807e8eb39e1dae74d8129a` |
| `02_datasets/acquired/meta/source-registry.json` | `437efc6e889ed384a3c9c336a8fa2c1e418ad01ed2a7d953074722aa127bd74a` |
| `scripts/prepare-incidents.py` | `2767d57a1e9639015d68fdccc582bee8fb8a04e53f34937384b8cf0383adc26c` |

Hashes are integrity evidence against the frozen local pack; they are not a fresh remote provenance or license verification. Source registry and revision snapshots remain the local provenance basis.

## Exact structural findings

Raw schemas below describe Arrow field names and types with Pandas metadata removed. All raw schema reads include heldout files only as structural inspection.

| Modality | Arrow schema |
|---|---|
| Logs | `timestamp: int64`, `container_name: large_string`, `message: large_string` |
| Traces, string fields | `time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`: all `large_string` |
| Traces, integer fields | `startTimeMillis`, `startTime`, `duration`, `statusCode`: all `int64` |
| Metrics | `time: int64`; every observed measurement column has type `double`; field names vary by incident |

There are 34 distinct metadata-free metric schemas, one log schema and one trace schema across the 90 cases. The saved source profile reports 69–77 measurement columns per incident, excluding `time`. Optional error, disk-I/O and workload fields differ. Some workload column names describe proxy clusters, not application services. A contract must preserve each file's exact field set or permit its verified schema; it must not assume the pilot's metric fields exist in every incident. A metadata-free schema fingerprint and the source's `str(pq.read_schema(...))` fingerprint have different definitions and must not be compared interchangeably.

Observed processed top-level schemas follow. These are source schemas, not a recommendation to export every listed field.

| Record | Fields and observed Python types |
|---|---|
| Observation | Strings: `incident_id`, `system_id`, `observation_start`, `observation_end`, `window_policy`, `symptom_query`, `query_origin`, `generator_revision`, `human_review_state`, `redaction_version`, `provenance_source`, `release_revision`, `knowledge_evidence_coverage`, `deployment_version`, `scenario_family_id`, `split`, `generation_date`; lists: `service_inventory`, `input_source_ids`, `log_span_ids`, `metric_summary_ids`, `trace_span_ids`; booleans: `is_synthetic`, `query_is_synthetic`, `telemetry_is_synthetic` |
| Log evidence | Strings: `evidence_id`, `incident_id`, `timestamp`, `service`, `text`, `source_file_id`, `redaction_version`, `transform_version`; integer: `source_row_index` |
| Metric summary | Strings: `evidence_id`, `incident_id`, `metric_name`, `observation_start`, `observation_end`, `change_score_rule`, `source_file_id`, `transform_version`; integers: `row_count`, `null_count`, `source_row_start`, `source_row_end_exclusive`; floats: `minimum`, `maximum`, `mean`; float or null: `first_quarter_mean`, `last_quarter_mean`, `change_score` |
| Trace evidence | Strings: `evidence_id`, `incident_id`, `timestamp`, `duration_unit`, `status_code_semantics`, `serviceName`, `methodName`, `operationName`, `traceID`, `spanID`, `parentSpanID`, `source_file_id`, `selection`, `redaction_version`; integers: `duration_raw`, `source_row_index`; integer or null: `status_code` |

Nullability is semantic, not merely the set of types present today. A metric summary from an all-null series can legitimately have null `minimum`, `maximum` and `mean`, even though the existing 6,603 full-window summaries have numerical values there. Arrow `statusCode: int64` does not imply non-null values.

`incident-profiles.jsonl` is an administrative audit artifact with timing/count/schema and privacy summaries, including nested trace service/status aggregates. It is unnecessary for inference. Its 90 IDs and record structure were checked without using heldout summary values for content decisions.

## Six train samples and time reconciliation

Selection was made from the source management split map; all six entries are explicitly `train`. Each listed raw sample path is `02_datasets/acquired/raw/<incident_id>/<modality>.parquet`, and the first-row examples below use zero-based source row 0. The rows reproduce only structural numeric/time evidence and public service strings.

| Train incident ID | Metric first / last epoch seconds | Metric rows / columns | Metric null cells | Raw trace row 0: startTimeMillis / duration / statusCode |
|---|---|---|---|---|
| `inc_08457c0fbff4700e` | 1705369375 / 1705370815 | 1,441 / 73 | 8 | 1705369375062 / 131 / 0 |
| `inc_0991de462f9a6c05` | 1705663371 / 1705664811 | 1,441 / 75 | 5 | 1705663371041 / 39164 / null |
| `inc_0f782051d78bc07a` | 1705756612 / 1705758052 | 1,441 / 69 | 1,785 | 1705756612028 / 185 / 0 |
| `inc_15361b2d5df6a488` | 1705488502 / 1705489942 | 1,441 / 70 | 2 | 1705488502000 / 4728 / 0 |
| `inc_1bd0f85d1967890c` | 1705668201 / 1705669641 | 1,441 / 75 | 0 | 1705668201000 / 14 / 0 |
| `inc_1c35829e1a5668b7` | 1705493188 / 1705494628 | 1,441 / 71 | 6 | 1705493188003 / 34084 / null |

Each sample's minimum/maximum raw log `timestamp` equals its first/last metric epoch second. Example raw row 0 from `inc_08457c0fbff4700e`: metric `time=1705369375`, `frontend_cpu=6.897680955727379`; log `timestamp=1705369375`, `container_name=currencyservice`; trace `startTimeMillis=1705369375062`, `startTime=1705369375062000`, `time="01:42"`. The epoch second converts to `2024-01-16T01:42:55+00:00`, consistent with the trace millisecond field and the processed observation. The bare clock string contains neither date nor timezone and is unsuitable as an absolute event clock.

For all six incidents, every processed metric summary's `observation_end` is exactly one second earlier than the observation record's `observation_end`. This matches source implementation rather than showing a corrupted timestamp: source summary ranges describe the last sampled second inclusively; source observation bundles use the next second as an exclusive endpoint.

Concrete last-second evidence: `inc_15361b2d5df6a488` has one raw trace at `1705489942000` ms, exactly its last metric second. It belongs in the bundle interval `[1705488502000, 1705489943000)` ms. Using the metric summary's unadjusted end as exclusive would drop that trace. No sampled trace falls in the corresponding forbidden next second; an exact `end_exclusive` exclusion should also be tested with a synthetic boundary fixture.

| Concern | Contract decision | Evidence / limitation |
|---|---|---|
| Metric time | Interpret raw `time` as UTC Unix seconds | Numeric ranges and all six train cross-modality comparisons |
| Log time | Interpret raw `timestamp` as UTC Unix seconds | Same sampled endpoint range as metrics; existing source filter uses inclusive integer seconds |
| Trace event time | Use `startTimeMillis` as Unix milliseconds | 13-digit sampled values align with metric/log epochs; retain original row provenance |
| Trace `startTime` | Retain raw value only when needed for audit | Sample values resemble microseconds, but inference time policy should use the documented selected millisecond field |
| Trace `time` | Ignore as an absolute event timestamp | Only an ambiguous clock string |
| Bundle end | Explicit `observation_end_exclusive = last_metric_second + 1` | Existing source observation update and six matching examples |
| Metric summary end | Record inclusive source sample endpoint separately; derive exclusive endpoint with a versioned +1 second conversion | Do not overwrite source or silently relabel the inclusive field |
| Trace filter | `start_ms <= timestamp_ms < end_exclusive_ms` | Preserve the sampled last-second trace; reject exact exclusive endpoint |
| Window meaning | Retrospective offline observation window | Source selection is based on provided metric range, with no injection time input |
| Duration | Preserve `duration_raw`, mark unit unknown/unverified | Source says microseconds are inferred; this is not independent evidence. No duration conversion justified |
| Status code | Preserve integer or null, mark semantics unknown/unverified | Six-sample observed values include 0, 4, 14 and null; nonzero is not validated as an error |
| Null metrics | Preserve null counts and missing values; no automatic zero or imputation | Source mean reducers skip nulls; all-null subwindows can yield null summaries |
| Metric physical units | Unknown unless backed by a verified source contract | Suffixes such as `_cpu`, `_mem`, `_latency-50` alone do not establish units/scales |

Across the six sampled raw trace files, null `statusCode` counts are 18,135; 19,200; 17,780; 19,011; 18,798; and 12,868 respectively. Missing status is common and must not be coerced to zero. The source trace selector privileges nonzero status before duration when available; its existing `selection` description should remain transparent, without claiming this selects verified errors.

The 1,785 null cells in `inc_0f782051d78bc07a` include 1,139 nulls in `productcatalogservice_error` and 216 in `redis_diskio`. Its processed summaries include one null `last_quarter_mean`; the other five sampled incidents have no null quarter means. The saved full-pack profile reports 35,333 null metric cells; that full-pack value was not recomputed by reading heldout metric contents in this audit.

## Alias policy

All six train samples expose log service `frontend` and trace service `frontendservice`. Their co-occurrence establishes that both spellings are present, not that the same deployment resource has been independently identified. Keep `raw_name` unchanged, `canonical_name` null and review state `unknown`; do not merge them automatically. Preserve case and distinguish proxy metric names from service identities. Any future merge needs source/deployment evidence and a versioned mapping. Service names derived from telemetry remain valid observations and should not be mistaken for gold just because they could also occur in labels.

## Export and path boundary recommendations

1. Treat only the four explicitly enumerated processed evidence/observation files as inference exporter inputs after pinned hash validation. Project exact allowed fields into new records; never serialize `dict(source_row)`, an inventory row, a profile record or a whole nested object unchecked.
2. Keep source split map, ground truth, family IDs, source-case names, label lineage, injection paths and acquisition manifests inside administrative/evaluator paths. The inference exporter must not read the split/ground-truth sidecars. Management-only copying can preserve source bytes and hashes independently.
3. Build evidence IDs and opaque `source_file_id` joins from validated incident/modality pairs. Validate row indices/ranges against the corresponding raw file's count and validate that evidence belongs to the same incident. Keep absolute paths and private lineage only in the audit mapping.
4. Validate nested arrays/objects recursively; ensure unknown keys fail or are omitted by a documented input projection. Sanitizing top-level keys alone is insufficient. Preserve synthetic-query markers and unverified semantic states.
5. Resolve every candidate path and enforce containment by path components in the intended root, with a specific allowed filename/modality. Reject parent traversal, foreign drive/UNC paths, alternate data stream syntax and resolved symlink/junction escape. A string prefix or a global `glob(data/**)` is not an adequate containment/packaging rule.
6. Pin expected source hashes independently of the incoming candidate file. Recomputing both expected and actual hashes from a tampered candidate provides no gate. Separate source-content integrity hashes, schema fingerprints, transform/config hashes and nondeterministic receipt timestamps.
7. Use strict JSON with finite numbers, stable ordering and explicit nulls. Exclude current time from deterministic content hashes. Keep redaction version and source-row traceability in derivative metadata.

Existing project patterns are simple `pathlib`-based Python scripts, `csv.DictReader` for tabular management metadata, standard-library SHA256/JSON, and passive PyArrow Parquet reads. Reuse conventions by implementing new code under `06_implementation`; do not import `prepare-incidents.py`: even its module top level creates `processed/labels`, and its `main()` regenerates labels, split map, summaries and inventory. There is no reason to invoke it to validate immutable inputs.

## Review disposition

Source census/integrity and the six-train time/null audit provide adequate technical evidence to implement the new local contract. The report does not certify payload privacy, pass runtime/failure tests, or approve a completed exporter; those require the implementation and its validation receipts. Duration/status/alias unknowns are explicit usage restrictions, not unresolved reasons to guess values. Human A/B/C ownership and any human review remain unsigned unless those people actually review the work. Kaggle execution and API transfer were not attempted by this audit.
