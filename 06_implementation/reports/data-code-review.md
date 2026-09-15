# Independent technical code review — plan 02

Reviewed: 2026-09-13. Reviewer: Codex `/root/source_audit`, independent of the implementation and test authors. The same reviewer previously performed the source audit; this is not independent human review by A/B/C. The concurrent plan-01 report `reports/code-review.md` is preserved; this plan-02 report uses a distinct filename.

Technical assessment: **9/10**. **Critical findings: 0. Open implementation findings: 0.** The issues found in review have been addressed in source. The final data suite passed 48/48 tests, and the combined existing-protocol plus data suite passed 83/83, with zero failures, errors or skips. Human sign-off remains pending and is not supplied by this score.

## Scope and methods

Read every new module under `src/data`, `configs/data.yaml`, `configs/runtime.yaml`, `configs/requirements-lock.txt`, the smoke notebook and the two plan-02 test modules. Compared their public interfaces and failure behavior with all three plan-02 phases and the existing `scripts/prepare-incidents.py` conventions. The review made no implementation edits. It wrote only review documentation and ran passive local checks.

The implementation uses standard-library Python and the existing pinned PyArrow dependency. JSON-formatted YAML avoids a new configuration parser dependency. Existing source preparation, protocol implementation, unrelated tests and documentation are outside this change's modification scope. There is no frontend, service API, packaging build system or application type/lint setup to extend; adding such gates would not improve this isolated data implementation.

Manual content review used the six verified train IDs recorded in `data-contract-review.md`. Heldout processing in validators/tests is structural: IDs, counts, fields, joins, offsets, timestamps and hashes. The initial scouting exposure limitation remains documented in that source report and is not erased by subsequent correct practice.

## Findings and resolutions

| Finding | Initial impact | Resolution confirmed in code |
|---|---|---|
| Consumer gate accepted any self-consistent set of 90 opaque IDs | P1: frozen population could be replaced while count remained 90 | `validate_inference` now requires the exact configured ID set; configuration IDs are typed, unique and count-checked |
| Environment report accepted an arbitrary overwrite destination | P1: a caller could direct a report over immutable source data | Common writers use `writable_path`; report output is restricted to implementation reports, and aliases/redirected temporary outputs are rejected |
| Environment train selection trusted an unpinned private split map | P1: altered assignments could select heldout IDs while claiming train | Environment builder checks the private split map's frozen SHA256 before selecting two train IDs |
| Detached or empty evidence could satisfy partial join checks | P2: incomplete evidence could be presented as a complete observation | All modality reference lists must be nonempty; log/trace reference sets must exactly cover their evidence; additional metric summaries remain permitted because observations reference only a selected subset |
| Resolved paths could alias another in-root data role | P1 boundary risk | `safe_path` rejects lexical/resolved aliases as well as traversal, foreign absolute paths and role-root escapes; real Windows junction tests exercise this |
| Malformed structures could raise uncontrolled errors or exploit bool/int equality | P2: incomplete structured failure contract | Config/manifest/receipt type and UTF-8 guards, strict integer manifest counts and hash/path checks now produce controlled contract failures |

The debugger independently supplied 45 passing targeted checks with no skips, including real junction behavior, source-output protection, malformed inputs, changed transform source and receipt/config/payload tampering. See `debugger-report.md` and `debugger-results.json`. Tests use temporary train/synthetic fixtures; they do not mutate actual gold or source telemetry.

## Acceptance review

| Plan work item | Technical evidence / disposition |
|---|---|
| D02-01: census, provenance and checksums | Independent source audit recomputed all 360 inventory hashes/sizes, confirmed 90 IDs, 270 telemetry +90 label files, 922,484,805 bytes and frozen revision. Management validator reproduces hashes, role paths, schemas/counts and split-family checks. Source mapping remains private |
| D02-02: timestamp/null/alias policy | Six train cases establish seconds versus milliseconds and inclusive-summary versus exclusive-bundle endpoints. Derivative keeps source sample end and adds a versioned +1 second exclusive end. Nulls, unknown physical/duration units, unknown status semantics and unmerged raw service names are explicit |
| D02-03: allowlist and data roles | Exact source filenames and field projections precede serialization. Nested objects and unclassified fields fail. Family/split/gold/source-case/injection/private paths are absent from inference schemas and public configuration hashing. Human A/B/C review is not manufactured |
| D02-04: validator failure contract | Source integrity, canonical role paths, duplicate IDs/evidence, foreign joins, field types, null states, finite JSON, windows and exact frozen IDs are checked. Error output uses rule codes and opaque IDs rather than raw payloads |
| D02-05: deterministic export and sidecars | New staging directories are validated before atomic publication. Existing different releases cannot be overwritten. JSON ordering, Parquet options and manifest hashes are fixed. Private sidecars are copied byte-for-byte by a separate management module; inference export opens only the four pinned public-source candidates |
| D02-06: local CPU runtime | Runtime config disables API/network/GPU and records CPU data scope. Lock identifies the measured CPython/PyArrow/Windows ABI and actual wheel hash. Notebook cells run in two fresh isolated processes with an empty working directory; actual versions/resources and train IDs are captured by the environment report |
| D02-07: packaging/resume and Kaggle | ZIP snapshots exactly five derivative files plus their manifest after validation; no directory glob can include private/raw/notebook artifacts. Archive ordering, timestamps and permissions are deterministic. Resume verifies immutable bytes; changed output requires a new version. Kaggle is deferred with owner C and a reason |
| D02-08: leakage/path/provenance checks | Adversarial tests cover labels/nested private fields, path escapes/junctions, duplicate/foreign IDs, windows, null/NaN/Inf, missing files, altered hashes, partial staging and private archive contamination. Six-train source-row replay adds independent provenance evidence below |
| D02-09: replay, payload and review receipt | Notebook has no saved outputs; the worker rejects saved code-cell output rather than exporting it. Environment replay compares exact manifest/data/selected-content hashes. Receipt validation binds exact manifest and evidence bytes; changed artifacts invalidate it. Human review is explicitly pending |
| D02-10: consumer handoff/version policy | Public consumer gate reads only inference files/configuration/code. Private sidecars are distinct evaluator artifacts. Handoff must name exact final paths/manifest and retain unknown-unit, API-off, Kaggle-deferred and human-pending states; final human release acceptance is not implied by technical completion |

## Independent provenance replay

Using passive PyArrow 21.0.0 reads, the reviewer resolved all selected evidence for the six train IDs back to original raw Parquet rows and recomputed metric statistics. The aggregate results are:

| Check | Compared | Mismatches |
|---|---:|---:|
| Log row offset resolves to recorded timestamp and service | 97 rows | 0 |
| Trace row offset resolves to timestamp, service, raw duration and nullable status | 84 rows | 0 |
| Metric column min/max/mean/null count/row count matches source summary | 433 summaries | 0 |

This supplements the all-90 row-bound/window/join checks. It does not certify raw log privacy, interpret status codes, prove diagnosis relevance, or validate every source value. No raw log messages or raw trace identifiers were printed by this replay.

## Public interface and operational limits

The incident index exposes opaque ID, start, exclusive end and evidence file IDs. The observation derivative deliberately omits the old synthetic `symptom_query` and its query metadata; plan 04 must derive its query from the retained evidence. No query in this package is represented as a real operator question. All 6,603 metric summaries can remain available while an observation points to its selected metric subset.

The source-free notebook provides a loading/hash/count/join smoke; its own text accurately distinguishes this from full management schema validation. It does not claim a Jupyter-kernel or model run. The Windows wheel lock is not a Linux/Kaggle lock. Regex-based privacy detection is a bounded defense; pending payload review must not be renamed comprehensive privacy certification.

The release manifest's transform hash intentionally changes when validator/exporter code changes. Final export, archive, environment and review receipts therefore need regeneration after the last guard change; stale candidate artifacts must not be relabeled as current. Final source hash validation and execution receipts belong to the coordinating release process.

Human A/B/C approval, actual downstream acceptance, Kaggle execution and API/sharing authorization remain separate unresolved gates. The local technical review does not sign them. Duration/status/alias unknowns are documented usage restrictions, not inferred facts.

## Final execution evidence and reviewed bytes

The independent tester reported 48/48 plan-02 data tests in 8.997 seconds and 83/83 combined protocol/data tests in 12.096 seconds, with no skipped tests, failures or errors. The actual Windows junction test ran. See the plan-02 scoped `data-test-results.json` and `data-test-results.md`; the concurrent plan-01 generic reports are preserved. Final inference manifest SHA256: `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4`. The coordinating receipt must bind this report and the final execution evidence.

| Reviewed implementation artifact | SHA256 |
|---|---|
| `src/data/__init__.py` | `080c6825667d244cd20be0dbfd59c5af9f0f06d63393a11c206f8452cd9e1ecc` |
| `src/data/build_environment_report.py` | `9fa8db927d1a86b445847e1741387febda87b7ea35c423c9cb45f7c4ee5a069a` |
| `src/data/common.py` | `0a03b244f2b5067e65612850214002314ba6c27adb570485dbd16d83816285b7` |
| `src/data/export_inference_data.py` | `edb33a08c2ae726d9419bd8ca87f7c4d22ce7542b2dc399170913beb5777efc1` |
| `src/data/export_private_sidecars.py` | `3726566570d95e37389ea3bf8c907444ffd2058fa3ab7f2e619b71ba2ea82000` |
| `src/data/package_inference.py` | `2edcc05a59f5056a6a9585a2cfaa863cbbdfbe73053507e0dc02c32a6a82573d` |
| `src/data/review_receipt.py` | `b643b9dbc66a7c08101927bb6b405efd4632ed8374439c9b087c9f58dfb9daab` |
| `src/data/validate_inputs.py` | `742900ef700782bbfd021e5f26a1b6f7edf42efc0009798278b804a12c1c0784` |
| `configs/data.yaml` | `9e394e23a8080f728371c35bbf7ceb785c5de68122601324c81e652b7bb01dbb` |
| `configs/runtime.yaml` | `ead5ea2a49511962b07e7809e0909234786bc9f33912c16f35b5c1c57cbc0244` |
| `configs/requirements-lock.txt` | `94e3a9d8aaa380c7c2ea90cb227614cb4435455a8fdc5176d2fefa50deb9bd9c` |
| `notebooks/00-environment-smoke.ipynb` | `f2571b48098b1f7f9943f85a1c44ef3a0630d0a64781e0b79d542b0a6cc52c0b` |
