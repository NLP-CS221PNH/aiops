# Corpus code review

**Status: pass for the authorized local candidate. Score: 9/10. Remaining critical findings: 0; remaining high/medium findings: 0. Release approval: pending.**

Reviewer: Codex subagent `/root/source_census`, acting as code-reviewer for implementation written by `/root` and `/root/corpus_builder`. This is an automated review, not human A/B approval. The reviewer authored `scripts/audit_corpus_sources.py` and the source-preparation outputs; those files are expressly excluded from this independent code review. The coordinator reviewed that census separately.

The review covers all `src/corpus/*.py`, `configs/corpus.yaml`, `docs/corpus-contract.md`, and the two corpus/citation test files against plan 03 and the user's local-candidate authorization. The accepted scope preserves the pending plan 02 human gate and actual A/B applicability review.

## Exact accepted candidate

- Corpus hash: `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3`.
- Manifest SHA-256: `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7`.
- Destination: `06_implementation/data/knowledge`; verified byte-identical to the reviewer's two independent outputs.
- Population: 74 preserved document records; 67 conditional candidate documents, 7 excluded proposals; 440 candidate chunks, zero released/indexed documents or chunks.
- Applicability: 0 allowed, 7 excluded, 67 unknown; all 74 human reviews pending and all deployment compatibility unknown.
- Every chunk has an actual pinned E5 token count, including `passage: `, heading and special tokens; maximum 511 of 512. All 580 source chunk IDs have versioned old/new lineage.

## Findings resolved and reverified

1. **P1, resolved: citation applicability and metadata join.** A forged approved/confirmed citation originally passed after full rehash while its document/chunk remained pending. The validator now checks every emitted citation metadata field against the validated chunk, including applicability, license, attribution, source ID, offset unit and review state. Fresh mutation tests reject the mismatch.
2. **P1, resolved: silent chunk loss.** Dropping a 1,812-character chunk from `KBH-D057-10119f6772e5` originally passed after rebuilding consistent lineage/counts/hash metadata. The validator now checks complete normalized candidate coverage using chunk ranges plus justified omissions, and complete raw-document accounting by retained/allowed removal spans. The fresh drop-one-chunk mutation fails.
3. **P2, resolved: applicability decision version mismatch.** Configuration and all proposal records now use `applicability-proposal-v1`; configuration loading and document validation enforce it.
4. **P2, resolved: report summary consistency.** Manifest counts/versions, token audit summaries and omission records are joined to actual records/configuration; source registry and applicability artifacts match the preparation bytes.

Builder follow-up fixes also preserve technical comments adjacent to a license footer, record raw coordinates for unresolved directives, reject supported junction/symlink output paths, and correctly interpret closing code fences and headings beside inserted YAML. Focused fixtures cover the content cases.

## Verification performed by this reviewer

- Ran `python -m unittest discover -s tests -p test_corpus_integrity.py -v` from `06_implementation`: **46 passed**, zero failures/errors.
- Ran `python -m unittest discover -s tests -p test_citation_registry.py -v`: **14 passed**, zero failures/errors. The combined 60 checks cover Unicode/BOM/CRLF, local include lineage, actual tokenizer IDs, long code blocks, strict JSON, output ownership, failed publication rollback, self-consistent corruption, stale/foreign citations, unchanged-ID forgery and the pending release gate.
- Built a clean reviewer candidate and an independent `python -I -B` process replay. All eight artifacts are byte-identical; the final default candidate matches those same hashes.
- Independently accounted for every original document codepoint exactly once using retained/removed raw spans, and every candidate normalized codepoint using chunks plus 32 justified one-newline omissions. No unexplained technical text loss was found. Six documents contain verified local asset expansions.
- Parsed all reviewed Python modules/tests with `ast.parse`; no syntax failures. Calling `validate_corpus(..., require_reviewed=True)` rejects this candidate with `RELEASE_PENDING`.
- Read the independent tester's existing-regression evidence: 48 data tests and 52 protocol tests passed. These regression results are attributed to the tester, not rerun by this reviewer. New corpus code stays in its own package/output/dependency area, and no source-acquisition or existing protocol/data API change was found.

Tester evidence: `reports/corpus-tests.json`, SHA-256 `af77fd8aff105da1776e31ce999715e5a8f0bca2d817f95666056c70d165e9a9`. Its candidate hash and artifact hashes agree with this review. The coordinator's `reports/corpus-validation.json` also reports the same candidate as technically valid. Source snapshot contracts remain pinned and raw files are retained.

## Review limits and human backlog

This acceptance is technical and candidate-only. It does not supply human source/applicability approval, deployment evidence, legal permission determination, incident relevance, causal validity or benchmark coverage. The released whitelist remains empty. Forty-three short chunks and 175 unrendered Hugo warnings are retained for source-content review; literal include/code samples use local pinned assets only. Long technical sections may span multiple chunks with exact offsets and overlap; a slice is reference context and is not a self-contained executable procedure.

No code changes were made during this independent review. Early corruption probes are isolated under `.test-work` and are not accepted candidates. Any subsequent change to the code/config/artifacts below requires revalidation and an updated review binding.

## Reviewed file hashes

| File | SHA-256 |
|---|---|
| `configs/corpus.yaml` | `05b33be146a2732e5cf6ec4b5fb981d978b462f2501db6857a61dc09f1b810b4` |
| `docs/corpus-contract.md` | `b27a83835c8212ac4ca5899fb4d9ae1bddca3acd5120178f662a7eff8d856966` |
| `src/corpus/__init__.py` | `9140e388f35fd51a4740453199cb46784cfd0fc46442b6bbd7401f8a296d45b9` |
| `src/corpus/build_corpus.py` | `9b4743c90c9c6a91e99a14a8723cee46eb890a6608a33fa137f804762c139a05` |
| `src/corpus/chunking.py` | `e3e6f43d52b56c81ca314d18ea011314b9a2e3f397727b63016ad383e3f0cd01` |
| `src/corpus/citation_registry.py` | `1c6856caa7b2cd23ec1f034a0e5d5956379f30cc763af14507e8acdaba48649f` |
| `src/corpus/common.py` | `416d1d7ab27097f1e5bea41471dc958a886b7ff4daced4ca47be4037aee7f004` |
| `src/corpus/normalize.py` | `f33511ebe30be5735a5399a8ee0150ab76012f463dc5d7a2a57cb78d26874bd8` |
| `src/corpus/review_receipt.py` | `eafff9089b1de4da6aac8cde90d8565f63287fb45689a40ceb44755d8ee5528f` |
| `src/corpus/tokenizer.py` | `bb72ff978d6e380479149a42236133b6638c3db19aa153c4cd0fef2d1bc26fc9` |
| `src/corpus/validate_corpus.py` | `6074d0973ab0c8b547f714806a460c22d7b1fac7c51c4f0d1f37f8fe58a91027` |
| `tests/test_citation_registry.py` | `e4a4a38e63c046a75bed0414223b59a97d9f87518552139d58a2e0af86066c62` |
| `tests/test_corpus_integrity.py` | `acdd1e22c57a4ede418ac47b278dd12af1477edb3b80086220bc9f376607c88c` |

## Accepted artifact hashes

| Artifact | SHA-256 |
|---|---|
| `applicability.tsv` | `3faf4fdef9585a6d92c646d19c43842c918343be41c512f07a89be63b74289b6` |
| `chunk-lineage.jsonl` | `cf89520a836a6c72b1fee7c9ed4abe1d071a1868a014f7eaaefc44edcaa53edd` |
| `chunks.jsonl` | `b46aafdb29fa6f70d2b95a990ed496d407bd19779ae8d15255c80ff7400a86ba` |
| `citation-registry.jsonl` | `b823384abe9d478f9e4ad56ca997874748d8497cb7fecbe117b961efb0fd9b05` |
| `corpus-manifest.json` | `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7` |
| `documents.jsonl` | `7875609c6b2a0eb24e5bb94396496230c30dc160734499501043c2d1eb8e40ce` |
| `source-registry.jsonl` | `4816c8574226bde4c9cc6f0d2b16ae11238ec00e306a265db529eaccd68f106b` |
| `token-audit.json` | `5099c6524cfb5ca52d82a0d8dfbcd2e95f9cf7e197dd6a5bef5c029aec1f3b0e` |
