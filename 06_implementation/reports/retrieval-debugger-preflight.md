# Plan 05 retrieval debugger preflight

Date: 2026-09-13. Actor: Codex `/root/audit_inputs`, automated scout/debugger; no human A/B/C signature. Scope: read-only upstream audit, artifact integrity checks, and isolated tooling provisioning. No private labels, qrels, private sidecar contents, real corpus indexing, or model inference were read/run by this subtask.

The user selected **“Build and test runners now; wait for a reviewed corpus before the pilot.”** That decision supersedes the earlier suggestion of a locally authorized candidate pilot. Build synthetic fixtures and fail-closed runners now; retain the actual pilot as pending until the corpus review/release gate is satisfied.

## Existing system and safe touchpoints

This is a local Python 3.11 research implementation, with JSON-compatible YAML configs and deterministic JSON/JSONL artifacts. There is no application framework or database. Relevant existing modules are `src/corpus/{common,tokenizer,validate_corpus}.py`, `src/data/common.py`, `src/representations.py`, and `src/representation_pipeline.py`. `scripts/preview-retrieval.py` is source-era preview code only; its runtime also reads legacy observations/split metadata and must not be imported wholesale as the new inference runner.

Accepted work is in `plans/260913-0057-cs221-05-retrieval-baselines/`: phase 1 contract/fixtures, phase 2 runners/pilot, phase 3 validation/handoff. Shared protocol lives in `plans/reports/260913-independent-plans-contracts.md`; concrete later authority is in `06_implementation/docs/corpus-contract.md` and `reports/representation-handoff.md`. The shared planning appendix's statement that every implementation path is still proposed is historical: corpus, safe export and query artifacts now exist.

The new retrieval package must not import a manager/evaluator or a label reader. The source-free helper `src.data.common.validate_inference` validates the safe export without opening private metadata. `src.representation_pipeline.load_manager_selection` is management-only and **does read** `data/private/split-map.tsv`; do not call it from the retrieval runtime. Controller-supplied opaque ID allowlists are the intended boundary. Existing `configs/representation-manager.json` contains 72 train/dev opaque IDs and an upstream split hash; it is not query payload.

## Verified input population and identities

Read-only checks passed for 16 artifact hashes/byte sizes, all 216 query schemas and exact text hashes, and all 440 chunk content/text hashes. See [machine receipt](retrieval-preflight-inputs.json). These checks establish integrity, not corpus approval or retrieval quality.

| Artifact | Actual state / exact SHA-256 |
|---|---|
| Corpus manifest bytes | `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7` |
| Corpus identity | `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3` |
| `data/knowledge/chunks.jsonl` bytes | `b46aafdb29fa6f70d2b95a990ed496d407bd19779ae8d15255c80ff7400a86ba` |
| Query manifest bytes | `013b41243616224fe39069d0fa27912689536095d1ca3db425b09ab513f40a28` |
| `queries/variants.train-dev.jsonl` bytes | `995c12d9b37ae6dc8ca8943af3ad8d4740ba957d75fc53967d8d1bc72ba35073` |
| Safe input manifest bytes | `55e091a86081e7a9b46208364a1dc8c65658a2628908306f1ec076e693334ae4` |

The corpus contains 74 document records, 67 conditional candidate documents, 7 excluded documents and 440 candidate chunks. `candidate_whitelist` names the 67 documents; `chunk_whitelist` names the 440 chunks. **`index_whitelist` is empty; indexed document/chunk counts are zero.** Manifest `status` is `candidate`, `release_ready` is false, and `review_state` is `pending`. All 67 usable candidates have unknown deployment compatibility; all 74 document human applicability reviews remain pending. Source-era 580 chunks are a different population and identity.

The query manifest is `cs221-query-manifest-v1`, milestone `04.variants`, status `candidate`, representation version `candidate-v1`. It binds 72 incidents, 216 queries (R1/R2/R3), 72 common bundles, 72 selections and 216 token ledgers. R2 is the default pilot candidate, with no selected winner. `test_materialization` is `not_performed_requires_plan08_F1`. The safe inference export has 90 incidents, but query materialization is limited to the 72 train/dev IDs.

The existing 20-incident/400-pair BM25 pool remains an unjudged source-era annotation seed with zero human judgments. It is not pilot acceptance for the new 440-chunk corpus and query variants. No quality score is available.

## Exact text, schema and hash semantics

Every branch consumes the same stored chunk `content`, which equals `section_heading + "\n" + text`. `content_hash` hashes that exact UTF-8 string; `text_hash` hashes only `text`. Do not add source URL, applicability, document ID, incident ID, family or other metadata to retrieval text. `document_id` is the derivative identifier; the old preview's `parent_document_id` is not the new schema.

Chunk records also bind `corpus_hash`, `chunk_id`, `document_id`, `start_offset`, `end_offset`, `source_revision`, source spans, `token_count`, applicability, `candidate_eligible`, `index_eligible` and review state. Offsets are half-open Unicode code points, not byte offsets. Citation registry records bind the same IDs/content hashes and normalized span. Source URL/revision/applicability may be emitted as provenance, independently from encoder/index text.

`queries/representation-schema.json` `$defs.query` has an exact-property schema. Query fields are:

```text
incident_id, query_id, representation_id, representation_version,
query_text, query_hash, window, evidence_ids, log_evidence_ids,
source_spans, missing_information, query_is_synthetic,
telemetry_is_synthetic, status, input_manifest_hash, config_hash,
tokenizer_hash, normalization_version, redaction_version, transform_version
```

The window fields are `observation_start`, `observation_end_exclusive`, `window_policy`. The query status is `ok` or `insufficient_evidence`; an insufficient record must not disappear. `query_is_synthetic: true` means a generated query representation; actual current records have `telemetry_is_synthetic: false`. Do not mistake that flag for permission to treat real telemetry as a synthetic engine fixture.

| Field | Hash scope / correct comparison |
|---|---|
| Query `query_hash` | Exact UTF-8 `query_text`, excluding dense `query: ` prefix |
| Query `config_hash` | Canonical representation config JSON; compare manifest `config_content_hash` |
| Query/token row `tokenizer_hash` | Raw `tokenizer.json` file SHA256 |
| Query manifest `tokenizer_hash` | Canonical full tokenizer specification, including policies/assets |
| Manifest `config_hash` | Exact config file bytes; differs from canonical content hash |
| Query/input `input_manifest_hash` | Exact safe input manifest file bytes |
| Bundle `bundle_hash` | Canonical complete bundle excluding only `bundle_hash` |
| Corpus `corpus_hash` | Canonical pre-stamp digest payload; not any single artifact's file hash |

Canonical JSON uses UTF-8, `ensure_ascii=False`, sorted keys, compact separators `(',', ':')`, `allow_nan=False`. The existing readers reject duplicate JSON keys and nonfinite constants. Use explicit UTF-8 reads on Windows. Source-file hashes and post-stamp artifact hashes are outside the corpus digest payload to avoid circular identity.

There is **no explicit `task_version` or `window_hash` in the current query row**. Plan 05 must define its ranking adaptation transparently: preserve the full upstream window, compute a canonical hash of that window, and bind the retrieval task policy/config/version rather than pretending an upstream `task_version` already existed. Representation version is not automatically task version. Any choice must be documented for 06/07/08 and covered by the config/fingerprint.

Private-key rejection in existing query/data code includes family/split/gold/ground-truth/source-case/fault/injection/label/root-cause/path fields. Query schemas should also reject extra nested manager fields and qrels/reference fields explicitly. Corpus provenance legitimately contains source URLs and raw source spans; query and corpus field policies should be distinct, with only the text projection passed to the encoder.

## Scoring and model contracts

BM25 preview lowercases technical tokens using `[\w]+(?:[-.:/][\w]+)*`, retains the full token, and adds split components longer than one character. It removes the fixed English stop list, deduplicates query terms, uses Robertson positive IDF `log(1 + (N-df+0.5)/(df+0.5))`, k1 1.2 and b 0.75, and sorts by descending score then chunk ID. It returns no hits for zero lexical overlap. Preserve semantics, but iterate deduplicated query terms in sorted order to eliminate cross-process set summation order variation. Independently calculated fixtures must verify scores and ordering with a declared tolerance.

Dense proposal: `intfloat/e5-small-v2` revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`, query prefix `query: `, passage prefix `passage: `, normalized embeddings and exact cosine search. The existing tokenizer assets are verified, but the proposed model weights are absent. RRF is rank-based with constant 60 and weights 1:1, using each branch's actual candidates and rejecting duplicate IDs. Optional reranker is `BAAI/bge-reranker-base` revision `2cfc18c9415c912f9d8155881c133215df768a70`; its model/tokenizer assets are absent and its final inclusion belongs to plan 08.

The E5 512-token ceiling includes prefix plus two special tokens. Current upstream builders use real tokenizer counts with padding/truncation disabled; query text is already budgeted identically for every branch. Dense adds its prefix once. A reranker has an independent total pair budget, including both query and passage plus specials. Synthetic long-input tests can verify truncation determinism/logging without indexing actual data. Do not silently let one branch see more source query text, nor treat E5 counts as proof of fit for a reranker tokenizer.

Cache identity must bind exact corpus/content/ordered row identities, query identities as relevant, model and tokenizer revisions/assets, text policy, prefixes, max tokens, normalization and implementation/config hashes. Rerank caching additionally binds ordered candidate text hashes. Resume must reject fingerprint mismatch and corrupted/partial checkpoints. Failed/empty/short records and measured versus estimated timings must remain explicit.

## Runtime and provisioned tooling

Measured interpreter: `06_implementation/.venv/Scripts/python.exe`, CPython 3.11.9, Windows AMD64. Before this subtask, the venv held PyArrow 21.0.0 plus bootstrap packages. The E5 Rust tokenizer 0.21.4 lives in isolated `.corpus-deps`; `CorpusTokenizer` inserts that directory and verifies all local asset hashes. No model weight files exist in `vendor/e5-small-v2`, and the normal Hugging Face cache has no E5 or proposed reranker entry. No GPU was probed.

Public wheels were downloaded and ZIP-checked, then installed offline with `--target .retrieval-deps --no-index --no-deps --require-hashes`. Direct packages are NumPy 2.3.3, JSON Schema 4.25.1 and pytest 8.4.2, with 10 pinned transitive packages. The original `.venv`, data lock and corpus lock were unchanged. Exact wheel hashes and measured import/synthetic-array smoke are in [dependency receipt](retrieval-dependency-provisioning.json) and [retrieval tooling lock](../configs/retrieval-requirements-lock.txt). No weights were downloaded and no actual text was encoded.

Import the isolated tooling explicitly:

```python
sys.path.insert(0, str(implementation_root / '.retrieval-deps'))
sys.path.insert(0, str(implementation_root / '.corpus-deps'))
```

No PyTorch, Transformers, sentence-transformers or ONNX Runtime backend was installed by this subtask. A future real E5 run needs its pinned backend and weights, or must emit an honest missing-model/runtime state. Synthetic vectors are appropriate for explicitly synthetic exact-search/cache tests only. Model provenance cannot claim an E5 encode merely because vector fixtures passed.

## Current gates and recommendations

| Gate | Owner / evidence required |
|---|---|
| Actual pilot/indexing | A/B: reviewed corpus release manifest and current review receipt; eligible whitelist must be nonempty and content/version hashes verified. Current manifest fails this gate. |
| Model execution | B/C: pinned weights/tokenizer/backend and measured local CPU smoke after the release prerequisite; do not download weights in the current subtask. |
| Pilot incident membership | Controller/06: opaque 20-train and 18-dev allowlists tied to upstream input/query hashes; retrieval runtime never reads split/gold. |
| Test mode | Plan 08: externally authenticated F1 plus immutable post-F1 test-input manifest and actual query/bundle hashes. Caller-supplied `status: frozen` is insufficient. |
| Human acceptance | Actual A/B/C reviews remain pending. Agent reviews may accept technical tooling, never create human signatures or qrels. |

Complete schema, hand-calculated scoring fixtures, synthetic engine tests, strict release/test boundary tests, checkpoint/cache validation, runbook and honest pending-pilot receipt now. Do not call a synthetic run a real pilot or mark `05.runners` fully accepted while mandatory real rankings and consumer receipt are missing. Do not alter upstream release flags or source-era NOT_RUN artifacts to satisfy the goal.
