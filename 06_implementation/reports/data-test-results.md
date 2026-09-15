# Plan 02 data test results

Status: **PASS**. Final inference manifest SHA-256: `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4`.

| Run | Tests | Failures | Errors | Skipped | Seconds |
|---|---:|---:|---:|---:|---:|
| Clean CPU data venv | 48 | 0 | 0 | 0 | 8.997 |
| Existing protocol + data, combined | 83 | 0 | 0 | 0 | 12.096 |

The combined run contains the same 48 data tests plus 35 existing protocol tests. Python 3.11.9 and PyArrow 21.0.0 were measured in both runs. The combined run used existing PyYAML 6.0.2; the isolated data environment and its dependency lock remain unchanged.

## Covered gates

- Exact source/public schemas reject nested gold, fault and source-case values; configured IDs, duplicate evidence, foreign joins and orphan logs fail closed.
- The Windows junction test created an actual workspace junction and proved resolved paths cannot escape the approved root. Traversal, absolute paths, alternate data streams, missing files and changed hashes are rejected.
- The last valid trace millisecond survives; the exclusive end fails. All-null metrics preserve nulls and missing reasons, nullable trace status remains unknown, and NaN/Infinity fail.
- Administrative split/family and private gold/source-case changes leave every public file, including the public manifest, byte-identical.
- Private sidecars preserve source bytes and hashes. Mid-export crashes publish nothing; retries are clean; a changed release cannot overwrite an existing release.
- Packaging includes only the six public files and produces repeatable ZIP bytes. Extra private/raw/unlisted files fail.
- The actual release has all 90 configured IDs. Private sidecars retain identical source bytes, 54/18/18 splits and 30 disjoint families. Pinned processed/source metadata hashes still match.
- A train log row, trace row and metric summary resolve to raw Parquet timestamps, service/duration/status or metric statistics/null counts/window. The independent source review provides broader six-train checks.
- Receipt tests reject changed manifest bytes and changed evidence artifacts; pending human review cannot pass the human gate.

Every mutable data fixture stays in workspace temporary directories and retains content only from the first train incident selected using private split administration. Real source files are never changed. All-90 checks are structural and administrative; they do not review test payload content.

## Reproduction

Run from `06_implementation`:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -p test_data_*.py -v
```

The existing protocol suite also needs PyYAML, which is already installed in Store Python. The combined run prepended the existing workspace Arrow runtime and used the same unittest discovery:

```powershell
@'
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent / '.runtime-python'))
unittest.main(module=None, argv=['unittest', 'discover', '-s', 'tests', '-v'])
'@ | python -
```

Captured execution used `unittest.defaultTestLoader.discover` and `TextTestRunner(verbosity=2)` to retain structured results with the equivalent discovery parameters above. Exact test names, measured runtimes, test file hashes and manifest binding are recorded in `data-test-results.json`.

Human A/B/C review is not asserted by these tests. GPU, Kaggle upload, model/API execution and external sharing are outside this test run.
