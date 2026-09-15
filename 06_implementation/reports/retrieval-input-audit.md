# Retrieval input contract audit

The detailed independent inventory is [retrieval-debugger-preflight.md](retrieval-debugger-preflight.md)
with byte evidence in [retrieval-preflight-inputs.json](retrieval-preflight-inputs.json).
All 216 query rows and 440 candidate chunk content hashes passed that read-only audit.
The user's subsequent instruction is to build/test runners and wait for a reviewed
corpus before the pilot; [execution contract](retrieval-goal-contract.md) governs this delivery.

| Input | Owner | Runtime use |
|---|---|---|
| Corpus manifest, released document whitelist | 03 / A+B | Verify pinned manifest and chunk bytes; reject candidate status before reading chunk text. A future released manifest must explicitly authorize indexed documents/chunks. This handshake still needs owner03 confirmation. |
| `section_heading + "\n" + text` / `content_hash` | 03 | The identical canonical content feeds BM25 and E5. No applicability, source path or citation metadata is concatenated into model text. |
| Query manifest and exact safe query schema | 04 | Verify artifact bytes, nested schema, text hash, source-input hash, representation config hash and actual tokenizer identity. |
| Query text | 04 | Same query text for every condition; E5 adds only the fixed `query: ` prefix. Shared actual E5 token count must fit 512 including prefix/special tokens. Overbudget input is rejected, not silently shortened for one branch. |
| `task_version`, `window_hash` | 05 adapter, based on 01/04 | Explicit retrieval task identity and canonical hash of the existing window object. These are new retrieval provenance fields, not invented fields in the upstream query artifacts. |
| Incident allowlist | 06 controller / later 08 | Exact JSON containing only schema version, mode, opaque IDs and query-manifest hash. The retrieval package never opens the split map. Current pilot eligibility is constrained by the pinned train/dev-only query artifact. |
| F1 and later immutable test-input receipt | 08 | Distinct artifacts: F1 freezes policy/code/environment/export/corpus/schema/tokenizer before test queries are materialized; later receipt binds actual query hashes to F1. Controller supplies trusted file hashes externally. No F1 is created or accepted for real execution here. |

Forbidden query fields include family, split, source_case, injection target/time,
gold, labels, qrels and relevance grades, including nested copies. Unknown fields
also fail the exact query schema. Allowed input roots exclude private datasets,
labels and annotations; traversal, links and external schema references are rejected
before I/O. This is a fail-closed application interface, not an OS sandbox claim.

BM25 preserves exact technical terms and component tokens from the preview scorer.
Unique query terms are now sorted before accumulation for repeatable floating-point
addition; this is explicitly versioned `technical-preview-v1-sorted-query-terms`.
Score ties use chunk ID, ranks start at one and duplicate IDs/ranks fail. Zero overlap
returns an empty successful record, while engine failures remain failed records.

The legacy 400 BM25 candidate pairs remain an unjudged annotation seed. Their old
chunk IDs and private observation format are not loaded or relabeled as new rankings.
No quality measure, test materialization or upstream release decision was made.

Technical review is performed by independent Codex agents. A/B/C human identities,
applicability review and consumer acceptance remain pending, without substituted signatures.
