---
phase: 1
title: "Census nguồn và hợp đồng applicability"
status: pending
priority: P1
effort: "6h"
dependencies: []
---

# Phase 1: Census nguồn và hợp đồng applicability

## Overview

Lập danh sách 74 nguồn và điều kiện được dùng trước khi thay đổi văn bản.
A review applicability; B kiểm tính sử dụng được cho IR; Codex trích metadata và bằng chứng.
Đầu vào kỹ thuật là full gate plan 02, historical sources và protocol.
Dự toán 6 giờ-người chưa đo; chưa có incident→document relevance gold.

## Requirements

- Giữ commit/license/attribution, available_at, retrieved_at và source hash riêng.
- available_at là snapshot commit time, không giả thành publication date mỗi trang.
- Snapshot trước incident chỉ là temporal eligibility.
- Deployment/config version unknown không suy từ upstream README hoặc tên service gần giống.
- 74 rows có quyết định hoặc review pending với owner, không để khoảng trống mơ hồ.
- Proposed mappings chỉ phục vụ preparation review, không biến thành truth cho index.

## Architecture

Source manifests + document metadata + deployment evidence đã có → applicability registry.
A đọc source span; Codex đề xuất scope/state có evidence; B kiểm conditional-use rule.
Review quyết định dùng `allowed/excluded/unknown`; `review_state` độc lập với decision.
Unknown không đồng nghĩa irrelevant; applicability khác qrel relevance.
Generic diagnostic steps được gắn precondition; platform feature instructions cần config proof.
Registry giữ exclusion reason nhưng không làm biến mất original document.
Tokenizer/model revision tham chiếu card/protocol; lựa chọn cuối được downstream freeze.
Evidence coverage chỉ được đánh giá với incident pool ở plan 06.

## Related Code Files

- Existing/read: [source-manifest.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl).
- Existing/read: [documents.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/documents.jsonl).
- Existing/read: [snapshot.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/snapshot.json).
- Existing/read: [comparison-with-current.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/comparison-with-current.json).
- Existing/read: [document-applicability-historical.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/document-applicability-historical.tsv).
- Existing/read: [knowledge-and-annotation.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/knowledge-and-annotation.md).
- Proposed/create: [configs/corpus.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/corpus.yaml).
- Proposed/create: [data/knowledge/applicability.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/applicability.tsv).
- Proposed/create: [reports/corpus-source-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-source-audit.md).

## Implementation Steps

### K03-01 — Source census và license lineage (2h)

- Input → historical manifest/documents/raw receipts và plan 02 contract.
- Action → Codex xác nhận counts/IDs/hash, A review license attribution, B kiểm snapshot separation.
- Output → census 74 docs/3 sources, source revision/license table và audit report.
- Prerequisite → plan 02 completed; nguồn local đọc được.
- Acceptance → 25 D057 +14 D058 +35 D059; URL/commit/license/source hash resolve; current không trộn vào.
- Failure path → receipt/hash thiếu thì quarantine doc khỏi candidate index và ghi lý do; không tự suy quyền từ code khác.

### K03-02 — Applicability evidence và review contract (2h)

- Input → source metadata, benchmark/deployment evidence có provenance và 74 blank forms.
- Action → Codex đề xuất condition/state, A đọc evidence và review, B kiểm unknown/conditional language.
- Output → applicability.tsv versioned với evidence, reviewer/status và allowed experiment mode.
- Prerequisite → K03-01; source scope đã rõ.
- Acceptance → mỗi doc có reason; compatibility chỉ confirmed khi có deployed evidence; unknown không bị lấp bằng ngày commit.
- Failure path → thiếu deployment evidence giữ unknown + permitted conditional use/exclusion; giữ human review pending khi chưa chấm.

### K03-03 — Chuẩn hóa/token/citation specification (2h)

- Input → source census, các title copyright/short chunks và downstream content contract.
- Action → Codex đề xuất rules, A xác nhận technical meaning, B review tokenizer budget/offset/IDs.
- Output → corpus.yaml và schema các document/chunk/citation/lineage records.
- Prerequisite → K03-01/02 có quyết định scope.
- Acceptance → heading+text+prefix+special tokens cùng budget; codepoint offsets; title metadata có original_title.
- Failure path → tokenizer chưa sẵn vẫn hoàn thành spec; token verification giữ pending trước phase 2 gate, không dùng chars/4 thay.

## Interface và schema dự kiến

| Record | Fields chính | Ý nghĩa |
|---|---|---|
| Applicability | document_id, decision, reason, review_state, reviewer, evidence_ids | Quyết định có provenance |
| Scope | app_version, platform_version, config_preconditions, evidence_role | Giá trị unknown hợp lệ |
| Time | available_at, availability_basis, retrieved_at | Không đồng nhất các mốc |
| Corpus config | selected_sources, normalization_version, chunking_version, tokenizer_revision | Input tạo derivative |
| Source entry | source_url, source_revision, license, attribution, raw_hash | Giữ theo doc/repo evidence |
| Citation spec | document_id, normalized start/end, raw spans, source URL | Resolve được citation |
| Exclusion | document_id, reason, decision_version | Không xóa raw doc |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| KC-01 | Upstream commit trước 2024 | Time eligible, deployment vẫn unknown nếu chưa evidence |
| KC-02 | K8s feature cần version không có | Conditional/excluded theo policy; không khẳng định hiện diện |
| KC-03 | CPUThrottlingHigh title khớp metric | Không tự thành relevant qrel hoặc causal claim |
| KC-04 | Current và historical cùng text | Không coi hai nguồn độc lập |
| KC-05 | License/source URL thiếu | Chưa publish index entry đến khi resolve |
| KC-06 | Proposed mapping có service/fault | Không index; review role tách annotation |
| KC-07 | Human reviewer chưa đọc | review_state pending; Codex không ký thay |

## Bàn giao cho phase 2

K03-01 cung cấp exact source list và immutable hashes.
K03-02 cung cấp policy dùng unknown và list cần người review cuối.
K03-03 cung cấp schema/key names; consumer dùng document_id, nguồn parent_document_id giữ trong lineage.
Các câu hỏi unresolved được gắn owner A/B và ảnh hưởng cụ thể.
Không chặn việc viết parser bằng việc giảng viên chưa duyệt API; corpus work chạy local.

## Success Criteria

- [x] Census 74 docs và lineage/license đầy đủ.
- [x] Applicability schema tách decision khỏi human review state.
- [x] Unknown deployment không bị đổi thành compatible.
- [x] Corpus config/offset/token/citation specification thống nhất.
- [x] Phase 2 nhận nguồn và rules đủ cụ thể.

## Risk Assessment

Nguồn có ngày cũ nhưng nội dung không áp dụng là rủi ro khoa học còn mở.
License permission khác applicability; cả hai cần được ghi nhưng không thay thế nhau.
Không dùng fault gold để “chọn tài liệu hợp lý”; relevance do annotation phase 06 xác định.

## Execution evidence — 2026-09-13

Local-candidate execution was explicitly authorized while Plan 02 human acceptance remains pending. K03-01 technical census passed 5,666 source/receipt/revision/license integrity checks with 25 D057 +14 D058 +35 D059 documents and 12 supporting assets. K03-02 produced all 74 reasoned proposals: 67 unknown with conditional-use preconditions, 7 excluded, 0 allowed; human reviewer/time fields remain blank. K03-03 delivered the fixed content/tokenizer/normalization/offset contract and config.

All five phase success criteria are technically evidenced and were marked through `ak plan check`; this does not claim that A/B performed the review actions in the original implementation steps. See [source audit](../../06_implementation/reports/corpus-source-audit.md), [source preparation review](../../06_implementation/reports/corpus-source-review.md), [corpus contract](../../06_implementation/docs/corpus-contract.md) and [progress mapping](../../06_implementation/reports/plan03-progress.md). The phase's original frontmatter status is retained because the available CLI mutates checkboxes only; parsed phase progress is complete.
