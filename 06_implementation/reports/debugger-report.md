# Independent debugger report — plan 02

Date: 2026-09-13. Technical debugger: Codex subagent. Final result: **45/45 targeted checks pass**, with no skipped or blocked check. Python 3.11.9 and PyArrow 21.0.0 from `06_implementation/.venv/Scripts/python.exe` were used. Individual outcomes and tested implementation hashes are in `debugger-results.json`.

## Scope

This pass supplements the separate tester suite. It exercised failure paths in the inference consumer, shared parsers, output guards and review receipt. A temporary release fixture retained only the first sorted train incident (`inc_08457c0fbff4700e`); its fixture config explicitly declared one incident. Other payload fixtures were synthetic. Receipt tests used temporary evidence and overrode only the receipt module's implementation root and consumer call to validate this one-incident fixture with its explicit config. No human approval was asserted.

Source telemetry and source scripts were not modified. Temporary files stayed beneath `06_implementation/reports/.debugger-fixtures-*`; the actual Windows junction was unlinked before the verified fixture root was removed. No raw messages, source-case labels, faults or private paths were reproduced in results. The existing candidate ZIP was inspected only for its archive envelope; this report does not certify a later frozen release or replace its full 90-incident validation.

## Verified failures and boundaries

| Area | Evidence |
|---|---|
| Windows paths | A real junction from the fixture public directory into a synthetic private sibling failed `PATH_ALIAS`. An output beneath the junction parent failed `PATH_NOT_ALLOWED`. Parent traversal, ADS and UNC paths failed `PATH_FORBIDDEN`. An ordinary allowlisted file succeeded. |
| Source write protection | Read-only calls to `writable_path` targeting the immutable processed observation file, source preparation script, or a parent traversal toward sources failed `OUTPUT_PATH`; no source write was attempted. |
| JSON/type contract | Top-level array/null/boolean/string configs and receipts failed structured schema codes. Duplicate keys, NaN, malformed JSON and invalid UTF-8 failed structured parser codes. Manifest list/dict paths and boolean incident counts failed `MANIFEST_SCHEMA`. A boolean row count also failed `MANIFEST_SCHEMA` after the attacker recomputed the manifest content hash. |
| CLI failure | An export subprocess given a file containing byte `0xff` exited 1, printed `{"status": "failed", "code": "INVALID_JSON"}`, and emitted no traceback or stderr. |
| Frozen artifact integrity | Public config modification failed `CONFIG_HASH`; changed payload bytes failed `HASH_MISMATCH`; altered manifest/receipt/evidence failed the relevant receipt or transform hash code. A fresh subprocess importing a temporary copy of the transform package with an appended comment in `common.py` rejected the previously valid fixture with `TRANSFORM_HASH`. |
| Human review boundary | Empty reviews, null review rows and a review object instead of a list failed `HUMAN_REVIEW_PENDING`. This technical run never approved A/B/C reviews. |
| Runtime/package diagnostics | In-memory compilation passed for all 8 data modules and 3 current test files (11 files total). `python -m pip check` reported no broken requirements. Notebook saved outputs/counts are empty and its code has no raw/private/network path. Candidate ZIP contains exactly five inference derivatives and their manifest, with a passing ZIP integrity check. |

## Findings resolved during the pass

The initial run exposed five concrete failures, which were reported to the coordinating agent and repaired before the final run:

1. A config containing the single byte `0xff` raised `UnicodeDecodeError`. Final config, JSONL, receipt and manifest readers return `INVALID_JSON`.
2. Changing the one-incident fixture manifest to `incident_count: true` passed because Python equates `True` and `1`. The manifest now rejects it with `MANIFEST_SCHEMA`.
3. Replacing a receipt evidence entry path with `[]` raised an unhashable `TypeError`. It now returns `RECEIPT_EVIDENCE`.
4. Setting `human_reviews` to `[null, null, null]` raised `AttributeError`. It now returns `HUMAN_REVIEW_PENDING`.
5. Setting `human_reviews` to `{"A":"approved"}` raised `AttributeError`. It now returns `HUMAN_REVIEW_PENDING`.

Minimal repro inputs above are applied to disposable copies of a valid receipt/manifest. For receipt cases, `local_gate` remains `pass`, the fixture manifest hash remains correct and the evidence hash remains valid so the specific malformed type reaches its intended gate. The final pass reran each original failure rather than weakening its expected result.

## Limits

These checks prove the exercised technical conditions; they do not certify that every possible sensitive string can be identified by regular expressions. Full source-integrity accounting, the complete automated test suite and two clean smoke runs belong to their separate receipts. Candidate staleness after transform changes is expected integrity invalidation, not an exemption for the final release. Human source/payload/sharing reviews, Kaggle execution and external API authorization remain outside this debugger pass.

## Tested implementation hashes

- `common.py`: `76c5555e45e5df69275d722c53e8d829b73ce487a565cbf4b6b50d9a9dd75771`
- `export_inference_data.py`: `edb33a08c2ae726d9419bd8ca87f7c4d22ce7542b2dc399170913beb5777efc1`
- `package_inference.py`: `2edcc05a59f5056a6a9585a2cfaa863cbbdfbe73053507e0dc02c32a6a82573d`
- `review_receipt.py`: `b643b9dbc66a7c08101927bb6b405efd4632ed8374439c9b087c9f58dfb9daab`
