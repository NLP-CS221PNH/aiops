# Historical knowledge corpus contract

Plan 03 builds a local candidate from the immutable historical snapshot. The user authorized candidate implementation while retaining the pending release gate in [execution authorization](../configs/corpus-execution-authorization.json). Plan 02's technical data contract has passed; its human acceptance has not. This document does not authorize inference, uploading, deployment actions, relevance labeling, or changing the frozen protocol.

The outcome is reproducible, token-budgeted operational reference content with exact source citations. The input population is 74 documents: 25 D057, 14 D058, 35 D059, with 12 supporting assets and 580 old source chunks. The 83 proposed incident mappings are preparation material, not corpus text or qrels. No incident content, labels, proposed mapping text, papers, or current-snapshot document text is read to choose corpus content.

## Candidate and release

Disposition (`allowed`, `excluded`, `unknown`) is separate from `review_state`. Proposals carry a document-specific reason, evidence, owner, permitted use, and version/config preconditions. Human reviewer and review time remain blank until an actual review is received. Deployment compatibility remains `unknown`; a 2023 commit proves an upstream snapshot time, not the deployed version or causal relevance.

Conditional candidates may be built and tested locally. The candidate manifest has `status: candidate`, a candidate document/chunk whitelist, and an empty released index whitelist. Its released indexed count is zero. Downstream production/experiment loaders must require the reviewed release gate and must not treat a candidate whitelist as release approval. Unknown documents require verification of their stated preconditions; use is limited to possible diagnostic checks/reference facts, never asserted diagnosis or proof of configuration. Excluded documents remain in the document registry with explicit reasons. Historical and current snapshots must never be pooled as independent evidence.

## Content and tokenizer

All retrieval branches consume exactly `section_heading + "\n" + text`, stored as `content`. Encoder input is `"passage: " + content`. Both the prefix and `[CLS]`/`[SEP]` special tokens count toward the 512-token ceiling. Counts use the actual `intfloat/e5-small-v2` tokenizer at revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`, whose candidate status is inherited from the research proposal. Model execution and the final model choice remain downstream decisions. No characters-per-token estimate or encoder truncation is accepted as validation.

Tokenizer JSON, configuration, special tokens and vocabulary are saved with hashes. The isolated tokenizer package has its own version and wheel lock; it does not change the plan 02 environment or lock. Building and validation use local assets and disable tokenizer truncation and padding. Rerankers and generators have separate tokenizers and limits; a passing E5 count does not establish those budgets.

Normalization routes Markdown, YAML and proto separately. Initial metadata/license boilerplate may be removed from candidate content only with removal spans and preserved attribution/license/original text hashes. Copyright titles receive descriptive path-based metadata, retaining `original_title`. Technical literals, case, commands, error codes and versions are preserved. Markdown headings inside fenced code are not section boundaries. Local Hugo includes/code samples are resolved only from the supporting-asset registry at the matching source revision. Unknown directives remain visible with warnings; no remote include is fetched. Near-duplicate/short fragments are surfaced for review rather than treated as independent evidence.

## Records and offsets

| Record | Required contract |
|---|---|
| Document | `document_id`, `original_document_id`, `title`, `original_title`, `normalized_text`, normalized hash, raw hash/path, URL/revision/license/attribution, time provenance, normalization version, source spans, removals, rendering warnings, disposition |
| Chunk | `corpus_hash`, `chunk_id`, `document_id`, heading/text/content and their hashes, `start_offset`, `end_offset`, full token count, applicability, source spans |
| Citation | Same corpus/chunk/document IDs, normalized span, matching hashes, source URL/revision, exact source spans including expanded assets |
| Old/new lineage | Every original chunk ID, `parent_document_id`, overlapping new chunk IDs, relation and transform version, removal/exclusion reason when no match; never inherited qrel grades |
| Manifest | Corpus/config/source/tokenizer/code versions and hashes, exact artifact hashes/counts, candidate/released whitelists, exclusions, review state and validation receipt |

All spans are half-open. Normalized offsets are Python Unicode codepoint positions in `normalized_text`. Raw character offsets are codepoint positions in decoded raw UTF-8 text, including a BOM when present; raw byte positions are labeled separately. CRLF conversion preserves an explicit mapping. An include's inserted text points to its own raw asset; the directive location is retained as include provenance. No normalized offset is passed off as a raw byte position. Each citation span must reconstruct the actual chunk slice.

## Identity, replay and validation

Content identity uses canonical sorted JSON and SHA256. Build timestamps are excluded from identity. The digest payload includes source hashes, config/transform/tokenizer versions, document/chunk/citation/lineage records before adding their `corpus_hash` stamps, and applicability proposals. Post-stamp artifact hashes are kept outside the digest payload to avoid circular hashing. Changes to technical content, title, relevant metadata, policies, tokenizer or transformation invalidate the corresponding IDs/hash; old IDs are not reused for changed content.

The validator checks exact IDs/population, source whitelist and hashes, normalized/source spans, token counts and full budget, citation integrity, old/new lineage, foreign corpus/source IDs, artifact/config hashes and review state. Negative fixtures must reject missing/tampered sources, byte-based Unicode offsets, forged citations, excess prefix budgets, malformed decisions, missing unknown-use policy and stale corpus IDs. A clean build in an independent output directory must reproduce all canonical files byte-for-byte. Existing data/protocol checks must continue to pass; source acquisition scripts and snapshots remain unchanged.

## Change policy and consumers

Plan 05 receives the validated candidate schema, content policy and hashes for local contract preparation. Plans 07/09 receive citations with applicability conditions. Plan 06 receives old/new lineage and warnings; relevance, answerability and evidence coverage remain unjudged. Release is pending actual applicability review and the upstream acceptance gate. A technical review receipt must say who performed automated checks and must not substitute agent names for human signatures.

Any corpus refinement before F1 requires a new version, complete rebuild of every affected retrieval branch, new candidate pooling and rejudgment of affected pairs. Do not transfer grades using old/new overlap or matching titles. After F1, follow plan 08's deviation procedure and retain original outputs, hashes and the record of exposure to test data. Current-snapshot ablation requires a separate optional decision and manifest.
