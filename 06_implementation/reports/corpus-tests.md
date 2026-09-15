# Corpus candidate test evidence

The final local candidate passes **60/60 corpus tests**, with zero failures, errors, or skips. The corpus suite ran in 25.353 seconds on CPython 3.11.9. Existing data tests also pass **48/48**, and the current protocol suite passes **52/52**: **160 tests total**. The old plan02 report's protocol count is historical; this run used the current 52-test suite.

Reviewer: **Codex prerequisite_audit tester/debugger**, an automated agent. No human approval is claimed. [Machine receipt](corpus-tests.json) records every test name, exact tested code/configuration/test hashes, runtime, commands, failures, and final artifact hashes.

| Candidate evidence | Verified result |
|---|---|
| Corpus hash | `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3` |
| Final manifest SHA256 | `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7` |
| Documents | 74: 25 D057, 14 D058, 35 D059 |
| Candidate | 67 unknown-applicability documents, 440 chunks |
| Exclusions | 7 documents, retained in the document registry |
| Released index | 0 documents and 0 chunks; whitelist empty |
| Provenance inputs | 12 supporting assets, all 580 old chunk lineage records, 215 source/code/tokenizer checksums |
| Replay | Fresh baseline and independent isolated Python process produced identical bytes for all eight artifacts |
| Published local candidate | `data/knowledge` matches all eight tested baseline artifact hashes |

The suite checks actual E5 tokens including heading, passage prefix and special tokens, full budgets without truncation, long code blocks and overlap, deterministic IDs, BOM/CRLF/Unicode codepoint and UTF-8 byte spans, local include provenance, YAML/proto routing, Markdown fence boundaries, and preserving technical comments adjacent to a license footer. Every candidate chunk is checked against raw provenance and the citation registry.

Negative fixtures exercise foreign corpus/source IDs, corrupted token counts, citations and lineage, unsupported normalization settings, false applicability and human review claims, missing unknown-use conditions, stale review evidence, source/output boundaries and publication rollback. Semantic attacks refresh outer file hashes and the corpus digest. A dropped-chunk attack additionally rebuilds lineage, token audit, counts and whitelists; it still fails content coverage. A shifted valid source slice cannot retain the original chunk ID.

Sources were read only. Synthetic files and copied derivative mutations lived under `06_implementation/.test-work`. Fresh builds require the source audit to pass without findings; validators rehash pinned/raw sources and reconstruct complete source spans. Existing data/protocol implementation and receipts were not changed.

From the pack root, set `$env:PYTHONPATH = Join-Path (Get-Location) '06_implementation'`, then run:

```powershell
./06_implementation/.venv/Scripts/python.exe -B -m unittest discover -s 06_implementation/tests -p 'test_c*py' -v
./06_implementation/.venv/Scripts/python.exe -B -m unittest discover -s 06_implementation/tests -p 'test_data_*.py' -q
python -B -m unittest discover -s 06_implementation/tests -p 'test_validate_protocol.py' -q
```

The corpus receipt was produced through `unittest` discovery and `TextTestRunner` using the same discovery parameters as the first command. The data suite used the project venv; the protocol suite used Store Python with its existing PyYAML. No global environment was modified.

Technical success preserves the candidate boundary: plan02 human acceptance and plan03 human applicability review remain pending. Compatibility remains unknown; incident relevance and evidence coverage remain unjudged. No model inference or benchmark score was produced.
