---
title: "03 — Kho tri thức có phiên bản và điều kiện áp dụng"
description: "Chuẩn hóa historical corpus thành nguồn retrieval có tokenizer, citation lineage và quyết định applicability được review."
status: in-progress
priority: P1
effort: "24h"
tags: [docs, database, experimental]
blockedBy: [260913-0057-cs221-02-data-and-environment]
blocks: [260913-0057-cs221-05-retrieval-baselines, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 03 — Kho tri thức có phiên bản và điều kiện áp dụng

## Overview

Kế hoạch độc lập này tạo corpus derivative có thể index và trích dẫn từ 74 historical documents. Codex xây tooling/census/lineage; A chịu trách nhiệm nguồn và applicability, B kiểm tokenizer/citation. Tổng dự toán 24 giờ-người (6 +12 +6), chưa đo.

Kế hoạch gốc kết thúc khi corpus derivative được human review và handoff; chưa khẳng định coverage theo incident hoặc lựa chọn thí nghiệm cuối. Refinement từ train/dev trước F1 phải version và re-pool theo plan 06/08. Các artifact `06_implementation` đã được triển khai và kiểm kỹ thuật trong phạm vi local candidate được người dùng cho phép ngày 2026-09-13; human review và release của kế hoạch gốc vẫn pending.

## Hiện trạng đã đọc

### Candidate đã bàn giao — 2026-09-13

User amendment: “Proceed with local candidate; keep release pending (Recommended)”; [authorization](../../06_implementation/configs/corpus-execution-authorization.json). Corpus `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3` có 74 document records, 67 unknown conditional candidates, 7 proposed exclusions, 440 chunks; released/indexed count = 0. Census 5,666 checks và 160 corpus/data/protocol tests đều pass. Automated review không thay thế chữ ký A/B.

[Handoff](../../06_implementation/reports/corpus-handoff.md), [technical receipt](../../06_implementation/reports/corpus-review-receipt.json), [audit](../../06_implementation/reports/corpus-audit.md) và [full-phase progress](../../06_implementation/reports/plan03-progress.md) ghi exact hashes, replay, schema và ranh giới release. Phase 1/2 technical checklists đã được check qua CLI; phase 3 có 4/5 tiêu chí kỹ thuật có evidence nhưng actual human review còn thiếu. CLI chỉ toggle toàn phase, nên không check blanket phase 3. Tổng checkbox bền vững: 10/15, CLI progress 66%, plan `in-progress`. Các status `Pending` trong bảng/frontmatter phase bên dưới là giá trị gốc mà CLI checkbox-only không rewrite; trạng thái tiến độ được lấy từ checkbox và báo cáo này.

Các số liệu dưới đây mô tả baseline nguồn immutable, không phải derivative hiện tại.

- [Historical snapshot](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/snapshot.json): 74 docs/580 chunks/12 supporting assets/83 mappings chưa chấm.
- [Source manifest](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl): URL/commit/license/hash và attribution đã lưu.
- [Comparison](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/comparison-with-current.json): 41 paths cùng text, 32 đổi text; historical có thêm redis manifest.
- [Applicability forms](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/document-applicability-historical.tsv): 74 phiếu đang cần human review.
- [Documents](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/documents.jsonl): 12 titles mở đầu Copyright 2018 Google LLC.
- [Chunks](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/chunks.jsonl): 580 token_count null; 61 chunks ≤40 ký tự; chars/4 chỉ ước lượng.
- [Chunker nguồn](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/acquire-knowledge.py:113) chia heading/2400 chars, chưa theo tokenizer; không sửa script nguồn.

## Phạm vi và quyết định

| Thành phần | Quyết định |
|---|---|
| Corpus chính | Historical; thời gian trước incident đã kiểm nhưng deployment compatibility còn unknown |
| Corpus current | Optional ablation riêng, không nối hai snapshots thành nguồn độc lập |
| Nguồn index | Operational docs/config/proto đã duyệt; không paper library, labels hoặc annotation answers |
| Applicability | Quyết định có reason/evidence; unknown có conditional-use policy, không giả compatible |
| Chunking | Section trước, token budget thật sau; số derivative chunks có thể khác 580 |
| Mappings | 83 proposed mappings không là qrels và không đưa vào index/context |

## Kiến trúc và giao diện

Raw immutable → document/applicability registry → normalized text → tokenizer-aware chunks → citation registry → manifest. Index content thống nhất `section_heading + text`; tokenizer prefix/special tokens nằm trong audit budget.

Chunk schema dùng `document_id` để thống nhất consumer; giữ `parent_document_id` nguồn trong lineage mapping. Offsets là Unicode codepoint trên normalized text, có raw/normalized provenance. Các hàm dự kiến: `build_corpus`, `validate_corpus`, `resolve_citation`.

Manifest gồm corpus hash, source whitelist, exclusions, versions, tokenizer revision, counts và validation receipt. Source IDs/title/commit không bị mất khi tạo chunk mới.

## Phases

| # | Phase | Giờ-người | Đầu ra | Status |
|---|---|---:|---|---|
| 1 | [Census và applicability contract](./phase-01-start.md) | 6 | Source registry, policy và review backlog | Pending |
| 2 | [Chuẩn hóa, chunking và citations](./phase-02-build.md) | 12 | Derivative corpus, token/lineage audit | Pending |
| 3 | [Kiểm corpus và handoff](./phase-03-validate-and-handoff.md) | 6 | Review receipt, manifest và change policy | Pending |

## File inventory đề xuất

- Create: [configs/corpus.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/corpus.yaml).
- Create: [src/corpus/build_corpus.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/corpus/build_corpus.py), [validate_corpus.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/corpus/validate_corpus.py).
- Create: [data/knowledge/documents.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/documents.jsonl), [chunks.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunks.jsonl).
- Create: [applicability.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/applicability.tsv), [citation-registry.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/citation-registry.jsonl).
- Create: [corpus-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/corpus-manifest.json), [chunk-lineage.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunk-lineage.jsonl).
- Create: [tests/test_corpus_integrity.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_corpus_integrity.py), [reports/corpus-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-handoff.md).
- Existing/read only: toàn bộ knowledge-corpus-historical và annotation-kit nguồn; không modify/delete nguồn.

## Gate và ranh giới người

Plan 02 phải hoàn thành export/data contract trước triển khai corpus; đọc nguồn/soạn schema có thể chuẩn bị sớm. A/người review quyết định applicability dựa evidence; Codex chỉ hỗ trợ, không tự tạo review của con người.

Corpus có unknown applicability vẫn có thể hoàn thành nếu policy conditional/exclusion rõ và được review. Không cần bịa deployment version để đạt gate. Phase 06 đo coverage và relevance riêng; phase 08 khóa corpus cuối tại F1.

## Success Criteria

- [ ] Cả 74 source documents có quyết định và lý do; số indexed/excluded/unknown báo thật.
- [ ] Tất cả derivative chunks đạt token budget/offset/hash/citation checks.
- [ ] Raw/normalized lineage đầy đủ và source hashes giữ nguyên.
- [ ] Rebuild cho cùng config tạo cùng IDs/text/hash.
- [ ] Corpus handoff gắn review receipt; refinement có version và qrels invalidation policy.

## Rủi ro

Temporal eligibility không chứng minh deployment hoặc causal relevance. Platform runbooks có thể chỉ hỗ trợ bước kiểm tra, không định danh cause. YAML copyright headings và Hugo fragments cần review để tránh index boilerplate; corpus hash đổi kéo theo rerun mọi baseline/pool liên quan.
