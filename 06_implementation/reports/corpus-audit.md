# Corpus technical audit

The local candidate passes the authorized technical gate and remains unreleased. Corpus hash: `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3`. Manifest SHA-256: `ffbe1715e4bd5387843d083fb0daf27f12dd3b2eea1a8c1f9619c4725c6153f7`; configuration SHA-256: `05b33be146a2732e5cf6ec4b5fb981d978b462f2501db6857a61dc09f1b810b4`; citation registry SHA-256: `b823384abe9d478f9e4ad56ca997874748d8497cb7fecbe117b961efb0fd9b05`.

The [source audit](corpus-source-audit.json) passed 5,666 offline checks covering the 74 historical documents, 12 supporting assets, three licenses, pinned revisions/Git blobs and acquisition receipts. All original source hashes remain unchanged. Source dates and retrieval dates are distinct; deployment compatibility remains unknown. The [manifest](../data/knowledge/corpus-manifest.json) records 215 source/configuration-asset/implementation checksum entries; [content-review input hashes](corpus-content-review.json) bind the exact inspected derivatives.

| Check | Observed result |
|---|---|
| Population/disposition | 74 retained document records; 67 unknown conditional candidates; 7 proposed exclusions; zero allowed or released/indexed documents. |
| Encoder input | 440 real token counts; maximum 511/512 including `passage: `, section heading and two special tokens; no truncation or character estimate. |
| Complete provenance | Raw Unicode/UTF-8 byte spans, normalized text spans, removals and local-asset expansions account for content. All 440 citations resolve within the exact candidate. |
| Original lineage | 580 rows: 368 overlap, 55 one-to-many, 140 removed, 17 excluded; no fabricated one-to-one or qrel transfer. |
| Literal-preserving normalization | 12 copyright metadata titles corrected, 13 initial license comments removed only from derivatives with retained raw attribution/license; Markdown/YAML/proto routed separately. |
| Content review | 43 retained short chunks, 32 explicit whitespace omissions, 175 preserved Hugo warnings, 14 local expansions across six documents. |
| Duplicate review | Zero exact normalized-document groups; four pairs at fixed five-word-shingle Jaccard >=0.8 across all 74 documents. This is a lexical review flag, not relevance. |
| Test/regression evidence | [60 corpus/citation + 48 existing data + 52 existing protocol tests passed](corpus-tests.json), zero failures/errors/skips. |
| Rebuild | Fresh test and reviewer builds plus independent processes reproduced all eight artifacts byte-for-byte; default candidate hashes match. |
| Release boundary | Strict reviewed validation rejects with `RELEASE_PENDING`; all human review identities/times remain blank, released whitelist empty. |

Negative tests reject malformed/foreign source metadata, byte coordinates used as Unicode offsets, source or tokenizer drift, silent token truncation, changed content with stale IDs, wrong citation applicability/license metadata, and chunk deletion even when hashes/counts/lineage are recomputed. Complete raw and normalized coverage are checked independently. Tests also cover adjacent technical comments after license headers, indented YAML expansions, fence delimiters, output-path ownership and publication rollback.

The implementation review was performed by Codex `/root/source_census` against code written by `/root` and `/root/corpus_builder`; it reports a 9/10 local-candidate score with zero remaining critical/high/medium findings in [code review](corpus-code-review.md). That reviewer authored the census, so the coordinator separately read and reviewed the source audit and proposals in [source review](corpus-source-review.md). The tester/debugger independently recorded execution in [test evidence](corpus-tests.json). No agent name substitutes for a human A/B reviewer. The [technical review receipt](corpus-review-receipt.json) binds these evidence artifacts while preserving pending release.

Applicability remains a reasoned proposal, not a diagnosis, deployment match or relevance judgment. License evidence was checked for identity/integrity, not signed legal approval. Short/empty sections and unrendered dynamic Hugo directives remain explicit review work. Semantic coverage, answerability, per-incident cutoff checks and benchmark quality belong downstream. No model, embedding, retrieval benchmark, remote include or source example was executed. The original acquisition scripts, source snapshots and existing data/protocol contracts were not modified.

Reproduction, consumer schemas, conditional-use requirements and version/re-pool/rejudge policy are in [the handoff](corpus-handoff.md).
