# Historical corpus source census

Status: **pass** across 5666 offline integrity checks. This is source preparation and an unreviewed proposal, not corpus release approval.

Rehashed 74 documents, 12 supporting assets and 3 licenses; verified acquisition receipts, pinned revisions and Git blob identities against local repository trees. Source counts: D057=25, D058=14, D059=35. The existing 580 chunks were inspected only to prepare normalization.

| Source | Documents | Revision | Recorded documentation license |
|---|---:|---|---|
| D057 | 25 | `80bea9bfd97bec107361d4663e207aa8d3f312c6` | Apache-2.0 |
| D058 | 14 | `7e631d0318dc279cb2d31231d8823360e61e9304` | CC-BY-4.0 |
| D059 | 35 | `f8061f3e9b3337d90107aa2f10a0111f3f6dc86f` | Apache-2.0 |

License metadata and file hashes were verified; this is not a legal determination. Preserve source attribution, LICENSE, original notices and derivative change notices. No rights are inferred for externally linked material.

Applicability proposals: **0 allowed, 7 excluded, 67 unknown**. All 74 require A review and B check; reviewer identities and review timestamps are blank. Deployment compatibility stays unknown for all 74. The excluded records remain in the source registry.

Unknown sources may support an explicitly authorized local candidate as conditional reference hypotheses subject to the per-document preconditions. The proposals do not establish compatible deployment, incident relevance, causal evidence or human approval. Release remains gated by the project review contracts.

## Normalization preparation

- 12 original titles are copyright headings; retain them as original metadata and use a source-path/configuration title for future normalized metadata.
- 189 Hugo directives appear in 14 documents. 14 include/code_sample occurrences resolve to pinned local assets; missing literal includes: 0.
- Dynamic shortcodes and external figure/ref/glossary links remain source text. Handle them explicitly without current-value inference, web fetching or execution.
- 61 source chunks contain at most 40 characters; all 580 source token counts are null. Character estimates are not tokenizer validation.
- Exact document duplicate groups: 0; exact source chunk duplicate groups: 22. Repeated boilerplate is reported without deleting source evidence.

## Content review backlog

The proposal excludes project-purpose/product-requirement material, dependency-only frontend/checkout README files, a navigation-only troubleshooting introduction, an external-link-only out-of-order-timestamps stub and a TODO-only ingestion runbook. A/B may revise these decisions with evidence. Prometheus label/target-limit runbooks have empty diagnosis sections; the kubelet startup-latency runbook has an unresolved threshold placeholder.

CPUThrottlingHigh explicitly describes an informative alert inhibited by default; it must not establish a cause from the title alone. Google Cloud Operations is explicitly disabled by default. Network policies, HPA, persistent volumes, OpenShift-specific commands and optional platform features require deployed configuration evidence.

## Time and source separation

All source available_at values match verified repository commit metadata and precede 2024-01-01 UTC. This run does not open incident data or perform per-incident cutoff checks. Per-page published_at/updated_at remain unknown; acquisition timestamps are retained separately. Current corpus text, incident labels and proposed mapping content were not opened. No downloads or raw-source changes were performed.

## Reproduction and evidence

Run `python 06_implementation/scripts/audit_corpus_sources.py` for read-only validation. Add `--output-dir 06_implementation/data/knowledge-preparation --report-dir 06_implementation/reports` to materialize only the designated derivative files. Output is deterministic, with no timestamp claiming a human review. An existing reviewed applicability file is never overwritten.

The JSON report contains every exact input path, byte count and SHA-256, plus all document IDs, shortcode references, short chunks, duplicates and errors. The source registry retains all original non-text document metadata and complete source manifest/license metadata. Applicability rows cite the raw path, receipt and hashed source-text span.

| Contract input | SHA-256 |
|---|---|
| `03_collection_plan/knowledge-corpus-historical/snapshot.json` | `4859942b21898a0fd70ca85ebc12639b717299c1c18a19aa5f6b33dfd2351103` |
| `03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl` | `f8f768a8ee87b25d414a954fd0b0998d167bb91c5c3f5483cdff1c23ede07391` |
| `03_collection_plan/knowledge-corpus-historical/documents.jsonl` | `b8373b3087de3933b6dfee2ab0aa28db6df14485f7bda913360be3a19d409ab3` |
| `03_collection_plan/knowledge-corpus-historical/chunks.jsonl` | `1f6c1c28f5f7bcab926509595dda5d5400600c0ea773fdb23eb09d1849a6d8ca` |
| `03_collection_plan/knowledge-corpus-historical/supporting-assets.jsonl` | `4a277721a0c5bc3db40cc8456e194d00b40025e941b193e71b1043cd66a68f78` |
