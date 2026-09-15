# Historical corpus candidate handoff

The authorized local candidate is technically validated. The corpus hash is `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3`; manifest SHA-256 is `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7`. Plan 02's human acceptance and Plan 03's actual A/B review remain pending. The [execution authorization](../configs/corpus-execution-authorization.json) permits this local candidate; it does not authorize release or model execution.

The [manifest](../data/knowledge/corpus-manifest.json) preserves 74 documents from the historical snapshot: 25 D057, 14 D058 and 35 D059. Applicability proposals are 0 allowed, 7 excluded and 67 unknown. The 67 conditional candidate documents produce 440 chunks; **released/indexed documents and chunks are both zero**. All 74 human reviewer/time fields remain blank. Source timestamps establish upstream snapshot time; they do not establish deployed versions or incident relevance.

## Evidence and content review

The [validator](corpus-validation.json) passed every candidate's source/span/hash/token/citation checks. The [test evidence](corpus-tests.json) records 60 corpus/citation tests, 48 existing data tests and 52 existing protocol tests, with no failures, errors or skips. Fresh in-process and independent-process builds reproduced all eight artifacts byte-for-byte. The [code review](corpus-code-review.md) accepts the local candidate with zero remaining critical/high/medium findings. The coordinator separately reviewed the census in [source preparation review](corpus-source-review.md). These are automated technical reviews, not human signatures; see the [review receipt](corpus-review-receipt.json).

The [content review backlog](corpus-content-review.json) contains 12 corrected copyright titles, 43 retained short chunks, 32 documented whitespace omissions, 175 preserved Hugo warnings and 14 verified local expansions across six documents. It reports zero exact normalized-document duplicate groups and four document pairs at a fixed 0.8 Jaccard threshold over five-word shingles. This lexical comparison supports content review only. It does not establish evidence independence, relevance or coverage. The short chunks include heading-only/empty sections; they remain flagged for A/B review.

## Reproduce locally

Run the following from `06_implementation` using the existing Python environment. Tokenization uses the pinned Windows AMD64 `tokenizers==0.21.4` wheel and bundled E5 tokenizer assets; no model weights, embeddings, retrieval benchmark or model inference are involved. The plan 02 dependency lock remains separate.

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .corpus-wheelhouse --require-hashes --no-deps --target .corpus-deps -r configs/corpus-requirements-lock.txt
.\.venv\Scripts\python.exe scripts/audit_corpus_sources.py
.\.venv\Scripts\python.exe scripts/audit_corpus_sources.py --output-dir 06_implementation/data/knowledge-preparation --report-dir 06_implementation/reports
.\.venv\Scripts\python.exe -m src.corpus.build_corpus
.\.venv\Scripts\python.exe -m src.corpus.validate_corpus
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_c*py' -v
.\.venv\Scripts\python.exe -m src.corpus.build_corpus --output .test-work/handoff-rebuild
.\.venv\Scripts\python.exe -m src.corpus.validate_corpus --corpus-root .test-work/handoff-rebuild
```

The first census command is read-only. The second explicitly materializes preparation outputs and refuses to overwrite existing human review fields. Reinstall the isolated tokenizer only when absent or intentionally restoring that environment. Neither build nor validation downloads dependencies. The build checks all source receipts/hashes before normalizing and publishes the complete validated directory with rollback on failure. Existing same-version candidates with different content are rejected unless an explicit new version/output or `--replace-candidate` decision is supplied. Treat replacement as a deliberate local-candidate action; retain any frozen/reviewed outputs.

The strict release check must currently fail with exit status 1 and `RELEASE_PENDING`:

```powershell
.\.venv\Scripts\python.exe -m src.corpus.validate_corpus --require-reviewed
```

Resolve citations using a chunk ID from this exact corpus. Unknown IDs, stale artifacts and foreign corpus hashes fail closed:

```python
from pathlib import Path
from src.corpus.common import read_jsonl
from src.corpus.citation_registry import resolve_citation

chunk = read_jsonl(Path('data/knowledge/chunks.jsonl'))[0]
citation = resolve_citation(chunk['chunk_id'], corpus_hash=chunk['corpus_hash'])
# For a separately built configuration, pass its matching config explicitly:
# resolve_citation(chunk_id, corpus_root=Path('.test-work/next-candidate'),
#                  corpus_hash=expected_hash, config_path=Path('.test-work/corpus-next.json'))
```

## Consumer contract

The detailed authority is [corpus-contract.md](../docs/corpus-contract.md); [corpus.yaml](../configs/corpus.yaml) owns supported configuration and version values.

| Artifact | Consumer boundary |
|---|---|
| `documents.jsonl` | All 74 original identities, source metadata/license/attribution, original and corrected title, normalized text/hash, applicability, retained/removed raw spans. Exclusion does not erase the original. |
| `chunks.jsonl` | Exactly `section_heading + "\n" + text` is stored as `content` for BM25 and dense consumers. `document_id` is the shared key. `candidate_eligible` does not imply release. |
| `citation-registry.jsonl` | Exact chunk/document/corpus IDs, matching metadata and applicability, normalized intervals and raw source/asset spans. A URL alone is insufficient. |
| `chunk-lineage.jsonl` | Every one of 580 old chunks maps to overlaps, explicit removal or exclusion: 368 overlap, 55 one-to-many, 140 removed, 17 excluded. Original `parent_document_id` is retained. No qrel grades transfer. |
| `applicability.tsv` | Versioned proposals with reason, evidence, unknown deployment/config preconditions, owner and independent pending human review fields. |
| `source-registry.jsonl` | Original non-text source metadata and source manifest/receipt provenance; no incident labels or mapping text become retrieval content. |
| `token-audit.json` | Counts actual `passage: ` + content plus two special tokens; maximum 511 against a 512-token limit, no truncation. Reranker/generator limits are separate. |
| `corpus-manifest.json` | Exact hashes/config/code/source inventory, candidate and chunk whitelists, empty released `index_whitelist`, true counts and pending release blockers. |

All spans are half-open Unicode codepoint intervals; raw UTF-8 byte coordinates are separately named. Normalized offsets never stand in for raw bytes. BOM/newline/frontmatter/license transformations retain exact accounting; local includes point to their asset and original directive location. YAML/proto comments and fenced code are not treated as Markdown headings.

Plan 05 receives the candidate schema, canonical content and tokenizer hash for local preparation. Plans 07/09 receive complete citations plus applicability conditions. Plan 06 receives lineage/warnings; coverage, answerability and relevance remain unjudged. Consumers requiring released input must enforce the reviewed gate and empty released whitelist rather than loading candidate IDs as approval.

## Release and refinement

A must review the 74 source/applicability proposals and content backlog; B must check tokenizer, offsets, citations and conditional-use consistency. Plan 02's actual acceptance remains a separate prerequisite. The tooling intentionally rejects fabricated reviewer fields; recording real future reviews requires an explicit reviewed-release implementation and versioned evidence rather than editing the candidate into an apparent approval. No corpus coverage or deployment compatibility claim follows from these technical checks.

Any content, source, transform, tokenizer or policy refinement requires a new version, complete affected retrieval rebuild, re-pooling and rejudgment of affected pairs. Matching titles/overlapping lineage do not preserve old grades. Before F1, use the train/dev change procedure; after F1 follow plan 08's deviation policy, preserve the original outputs and record any test exposure. Current-snapshot ablation needs a separate decision and manifest; do not pool it with historical documents as independent evidence.
