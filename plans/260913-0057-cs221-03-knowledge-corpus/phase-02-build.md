---
phase: 2
title: "Chuẩn hóa tài liệu, chunking và citation registry"
status: pending
priority: P1
effort: "12h"
dependencies: [1]
---

# Phase 2: Chuẩn hóa tài liệu, chunking và citation registry

## Overview

Tạo pipeline corpus derivative giữ lineage, thực đếm tokens và truy hồi citation.
Codex triển khai; A review ngữ nghĩa/source changes, B review tokenizer/offset.
Dự toán 12 giờ-người chưa đo; sử dụng local CPU, chưa chạy retrieval benchmark.
Số chunks đầu ra do rules quyết định; 580 là baseline nguồn, không là target cố định.

## Requirements

- Source Markdown/YAML/proto giữ nguyên; derivative có transform version.
- Sửa title metadata không tự đổi technical content hoặc mất attribution.
- Hugo includes chỉ resolve tài nguyên local đã có provenance.
- Cùng content field cho BM25/dense; prefix encoder được tính budget.
- ID thay khi text/normalization/chunking thay; mapping về source/old IDs vẫn tồn tại.
- Không coi normalized offset là raw byte offset.

## Architecture

`build_corpus` đọc source allowlist → normalize → section split → token-safe split → emit registries.
Normalization giữ error codes, commands, version strings và exact technical literals.
YAML comments không mặc định là Markdown headings; parser route theo document kind.
Title sửa từ path/service để metadata rõ; original_title và change notice giữ riêng.
Chunk overlaps có vị trí xác định; short boilerplate được review, không xóa license source.
Citation resolver nối normalized spans về raw source spans và source URL/commit.
Corpus content hash tính từ canonical ordered content/config/source references.
Chunk record mang corpus_hash sau manifest content digest, tránh hash vòng tự tham chiếu.

## Related Code Files

- Existing/read: [acquire-knowledge.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/acquire-knowledge.py:105) — title/chunking nguồn để audit.
- Existing/read: [supporting-assets.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/supporting-assets.jsonl).
- Proposed/create: [build_corpus.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/corpus/build_corpus.py).
- Proposed/create: [validate_corpus.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/corpus/validate_corpus.py).
- Proposed/create: [citation_registry.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/corpus/citation_registry.py).
- Proposed/create: [documents.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/documents.jsonl).
- Proposed/create: [chunks.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunks.jsonl).
- Proposed/create: [citation-registry.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/citation-registry.jsonl).
- Proposed/create: [chunk-lineage.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunk-lineage.jsonl).
- Proposed/create: [corpus-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/corpus-manifest.json).
- Proposed/create: [corpus-token-audit.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-token-audit.json).

## Implementation Steps

### K03-04 — Normalizer có lineage (3h)

- Input → source docs/assets và corpus.yaml.
- Action → Codex route Markdown/YAML/proto, normalize newline/frontmatter/title theo rules; A review diff technical literals.
- Output → derivative documents.jsonl và source-normalized span map.
- Prerequisite → K03-03 config và K03-01 source hashes pass.
- Acceptance → 12 copyright titles có replacement mô tả hoặc reason giữ; original title/hash/license còn; snippets chỉ từ known assets.
- Failure path → include thiếu hoặc parse ambiguous giữ raw source text + rendering warning; không lấy link ngoài tự động.

### K03-05 — Chunking theo tokenizer thật (3h)

- Input → normalized docs, encoder tokenizer revision và content policy.
- Action → Codex section split rồi split quá dài, B đếm token thực kể prefix/specials, A review technical fragments.
- Output → chunks.jsonl + token audit gồm short/long/overlap/excluded counts.
- Prerequisite → K03-04; tokenizer files/revision available.
- Acceptance → mỗi indexed chunk fit encoder limit với content thực; no token_count null; overlap/offset stable.
- Failure path → technical block quá dài chia có lineage hoặc exclude có reason; không cắt im lặng ở encoder.

### K03-06 — Citation và old/new ID mapping (3h)

- Input → normalized spans/chunks + source document IDs/URLs.
- Action → Codex build resolve_citation và chunk-lineage; B kiểm ID/version collision, A resolve mẫu về source.
- Output → citation-registry.jsonl và mapping old source chunk → new spans/chunks, có one-to-many.
- Prerequisite → K03-04/05 stable candidate.
- Acceptance → chunk_id/document_id/source revision/source spans resolve; đổi text không reuse ID cũ; Unicode offsets đúng.
- Failure path → cannot map span thì chunk chưa được phép index; mapping mơ hồ ghi split/merged state, không giả one-to-one.

### K03-07 — Applicability merge và candidate manifest (3h)

- Input → registries, reviewed applicability state và corpus configuration.
- Action → Codex join metadata explicit, chạy integrity checks, A/B review indexed/excluded/unknown counts.
- Output → corpus-manifest.json có source/config/tokenizer hashes, whitelist/exclusions và status candidate.
- Prerequisite → K03-05/06; mandatory source checks pass.
- Acceptance → không mappings/gold/papers trong index; content policy đồng nhất; manifest không tự hash vòng.
- Failure path → metadata thiếu hoặc review chưa xong giữ candidate/pending; raw corpus vẫn nguyên.

## Interface và schema dự kiến

| File | Fields bắt buộc | Consumer |
|---|---|---|
| documents | document_id, original_document_id, title, original_title, normalized_text/hash, source revision | Chunker/citations |
| chunks | corpus_hash, chunk_id, document_id, section_heading, text, offsets, token_count, applicability | Retrieval/context |
| citation registry | chunk_id, document_id, source_url, revision, normalized_span, source_spans | Generator/demo |
| lineage | old_chunk_id, new_chunk_ids, relation, normalization_version | Pool/qrels migration review |
| manifest | content digest, source/config/tokenizer hashes, counts, exclusions, versions | All consumers |
| token audit | tokenizer_revision, per-content tokens, prefix/special budget, max/overlap | B/reproducibility |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| KB-01 | Unicode/BOM/CRLF | Text normalized; codepoint offsets resolve, raw hash giữ |
| KB-02 | YAML copyright comment | Không tạo misleading Markdown section tự động |
| KB-03 | Hugo include thiếu | Warning/conditional content, không tự tải thêm |
| KB-04 | Code block dài hơn limit | Chia an toàn có lineage hoặc exclude có reason |
| KB-05 | Prefix+heading làm vượt 512 | Budget tính tổng; chia lại trước index |
| KB-06 | Hai docs giống exact text | Duplicate report, không xóa attribution/provenance |
| KB-07 | Same path đổi text | New corpus/chunk version, không reuse qrels silently |
| KB-08 | Hơn một new chunk từ old chunk | Mapping one-to-many, downstream biết cần rejudge |

## Bàn giao cho phase 3

Corpus candidate chưa phải benchmark-ready chỉ vì offsets pass.
A nhận near-duplicate/short-chunk/title diff list để review có mục tiêu.
B nhận token/citation audit và manifest exact hash để replay.
Phase 3 quyết định release corpus reviewed; coverage remains unjudged.

## Success Criteria

- [x] Documents/chunks/citation registries được tạo tại derivative root.
- [x] Token counts thật và toàn indexed content fit budget.
- [x] Original sources/attribution giữ nguyên; old/new lineage có version.
- [x] Manifest counts/exclusions/unknown được ghi thật.
- [x] Không có gold/mappings/annotation answers trong index content.

## Risk Assessment

Near duplicates có thể hữu ích nhưng không là evidence độc lập; ghi document identity.
Copy source title vào mọi chunk có thể làm boilerplate chiếm token; review content policy trên train.
Reranker có tokenizer/pair limit riêng ở plan 05; phase này không khẳng định chunk fit mọi model tương lai.

## Execution evidence — 2026-09-13

K03-04..07 are implemented for the authorized local candidate. All 74 normalized document records preserve source identities/hashes/license/attribution; 12 copyright titles are corrected with originals retained. Fourteen pinned local includes across six documents expand with separate raw asset provenance; 175 dynamic Hugo warnings remain explicit. Sixty-seven candidate documents produce 440 chunks with actual E5 encoder counts, maximum 511/512 including heading/prefix/special tokens, and no truncation. All 580 old source chunks have overlap/removal/exclusion lineage, including 55 one-to-many rows.

All five technical success criteria were marked through `ak plan check`. Every citation/source span and complete raw/normalized accounting passes independent checks; all eight artifacts rebuild byte-identically. Corpus `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3` remains `candidate`, with an empty released whitelist and actual human reviews pending. See [audit](../../06_implementation/reports/corpus-audit.md), [content backlog](../../06_implementation/reports/corpus-content-review.json), [token audit](../../06_implementation/reports/corpus-token-audit.json) and [handoff](../../06_implementation/reports/corpus-handoff.md). The original frontmatter status is retained by the CLI's checkbox-only behavior; parsed phase progress is complete.
