# Knowledge corpus schema (candidate)

Subject hash: `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3`.

Population: 74 documents (D057=25 Apache-2.0, D058=14 CC-BY-4.0, D059=35 Apache-2.0). Source chunks 580 → candidate chunks 440. Applicability: 0 allowed / 67 unknown / 7 excluded. `index_whitelist: []`. `index_eligible` is false on all candidate docs. D058/D059 are in-corpus, not `corpus_to_collect`.

Historical `proposed-mappings.jsonl` (83 rows) is canonical for mapping hints. Current snapshot has 82. Neither is qrels.

`published_at` / `updated_at` are null. Time eligibility ≠ deployment compatibility. Derivative chunk key is `document_id`, not planned `parent_document_id`. See `03_collection_plan/data_schema.md`.

Nissist-style `prerequisites` / diagnostic checks are absent. Do not rewrite `documents.jsonl` to add them.

Hardcoded hash in `demo/loaders.py` is a follow-on; do not change it here.

## Document keys (`data/knowledge/documents.jsonl`, 48)

| Key | Disposition |
|---|---|
| `document_id` | frozen |
| `original_document_id` | frozen |
| `source_id` | frozen |
| `title` | frozen |
| `original_title` | frozen |
| `normalized_text` | frozen |
| `normalized_text_hash` | frozen |
| `text_hash` | frozen |
| `original_text_hash` | frozen |
| `raw_sha256` | frozen |
| `corpus_hash` | frozen |
| `license` | frozen |
| `license_evidence_url` | frozen |
| `attribution` | frozen |
| `change_notice` | frozen |
| `available_at` | frozen |
| `availability_basis` | frozen |
| `published_at` | frozen (null) |
| `updated_at` | frozen (null) |
| `version_scope` | frozen |
| `version_compatibility` | frozen |
| `upstream_application_release` | frozen (null) |
| `system_scope` | frozen |
| `index_eligible` | frozen (false) |
| `candidate_eligible` | frozen |
| `is_synthetic` | frozen |
| `derived_from_incident_ids` | frozen (must stay empty) |
| `document_kind` | frozen |
| `source_url` | frozen |
| `download_url` | frozen |
| `source_path` | frozen |
| `source_revision` | frozen |
| `raw_path` | frozen |
| `source_manifest` | frozen |
| `source_spans` | frozen |
| `removed_spans` | frozen |
| `normalization_changes` | frozen |
| `normalization_version` | frozen |
| `transform_version` | frozen |
| `parser_kind` | frozen |
| `rendering_state` | frozen |
| `review_state` | frozen |
| `applicability` | frozen sidecar-in-record |
| `bytes` | derived |
| `characters` | derived |
| `hugo_directive_count` | derived |
| `retrieved_at` | derived |
| `rendering_warnings` | derived |

## Chunk keys (`data/knowledge/chunks.jsonl`, 31)

| Key | Disposition |
|---|---|
| `chunk_id` | frozen |
| `document_id` | frozen (not `parent_document_id`) |
| `source_id` | frozen |
| `content` | frozen |
| `text` | frozen (same span as `content`) |
| `content_hash` | frozen |
| `text_hash` | frozen |
| `corpus_hash` | frozen |
| `license` | frozen |
| `attribution` | frozen |
| `available_at` | frozen |
| `source_url` | frozen |
| `source_revision` | frozen |
| `source_spans` | frozen |
| `section_heading` | frozen |
| `section_index` | frozen |
| `start_offset` | frozen |
| `end_offset` | frozen |
| `offset_unit` | frozen |
| `overlap_start` | frozen |
| `overlap_end` | frozen |
| `overlap_characters` | frozen |
| `overlap_tokens` | frozen |
| `chunking_version` | frozen |
| `normalization_version` | frozen |
| `index_eligible` | frozen (false) |
| `candidate_eligible` | frozen |
| `review_state` | frozen |
| `applicability` | frozen sidecar-in-record |
| `token_count` | derived |
| `short_chunk` | derived |

## Release enforcement

Both legacy scripts (`scripts/generate_test_pool_and_qrels.py` and `scripts/execute_evaluation.py`) now load chunks through `src.retrieval.inputs.load_corpus`. The current candidate fails with `CORPUS_RELEASE_PENDING` before text indexing or output writes. Even after a future release, their obsolete proxy/synthetic execution entrypoints remain disabled; use the reviewed retrieval runners and human annotation protocol.

Historical/current snapshots must never be pooled. Papers, G1 labels, qrels, and proposed mappings must never enter the knowledge index. Citation and chunk-lineage registries retain source revision, license, spans, and attribution; mappings are hints only.

The current applicability version is `decision_version=codex_proposal`. A human decision must be stored as a new versioned TSV; preserve proposals rather than overwriting them. Unknown documents can support candidate review, but cannot be described as deployment-compatible or released evidence.
