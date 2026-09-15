---
phase: 3
title: "Kho tri thức và điều kiện áp dụng"
status: pending
priority: P1
effort: "24h"
dependencies: [1, 2]
---

# Phase 03: Kho tri thức và điều kiện áp dụng

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 03](../260913-0057-cs221-03-knowledge-corpus/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Tuần 1–3, người phụ trách dữ liệu chuẩn bị corpus cho retrieval; thành viên retrieval kiểm tra offsets/tokenizer. Ngân sách 24 giờ-người: 12 giờ applicability, 6 giờ chuẩn hóa/chunking và 6 giờ audit. Kết quả là một snapshot có quy tắc sử dụng rõ ràng, chưa phải tập bằng chứng gold.

## Requirements

Dùng historical corpus 74 documents/580 chunks làm đầu vào chính. Nguồn gồm Online Boutique, Kubernetes và Prometheus runbooks; không trộn thư viện paper vào index vận hành. Current corpus 73/598 chỉ dành cho ablation riêng nếu còn thời gian. Điều kiện tài liệu tồn tại trước incident đã kiểm; compatibility với deployment RCAEval vẫn chưa xác nhận.

## Architecture

Documents gốc → applicability registry → text chuẩn hóa có lineage → chunks theo section → corpus manifest. Citation registry nối chunk về document, source URL và span; metadata vận hành tách khỏi gold. Phase 06 đánh giá evidence coverage theo incident sau khi có pool; phase này chỉ xác định tài liệu nào được phép dùng trong điều kiện nào.

## Related Code Files

Đọc `03_collection_plan/knowledge-corpus-historical/{documents.jsonl,chunks.jsonl,snapshot.json,comparison-with-current.json,source-manifest.jsonl}`, `03_collection_plan/annotation-kit/document-applicability-historical.tsv` và `05_research/knowledge-and-annotation.md`.

Tạo dưới `06_implementation/`: `corpus/{documents.jsonl,chunks.jsonl,applicability.tsv,citation-registry.jsonl,corpus-manifest.json}`, `configs/chunking.yaml`, `src/corpus/build_corpus.py`, `tests/test_corpus_integrity.py`, `reports/corpus-audit.md`. Giữ nguyên mọi file gốc.

## Implementation Steps

1. **Lập applicability registry.** Với cả 74 docs, ghi source commit, license, available_at, app/platform version, điều kiện cấu hình, evidence role và quyết định `allowed/excluded/unknown`. Bằng chứng có thể đến từ metadata benchmark và cấu hình deployment truy được; snapshot upstream cũ không đủ để đánh dấu compatible.
2. **Xử lý trường hợp thiếu phiên bản.** Giữ unknown kèm lý do; phân biệt tài liệu dependency tổng quát với hướng dẫn phụ thuộc Kubernetes feature/resource configuration. Trong phép thử offline, tài liệu unknown chỉ hỗ trợ kiểm tra có điều kiện; không được biến thành lời khẳng định cấu hình đã tồn tại. Tách tập confirmed-compatible nếu đủ số lượng; không hứa trước cỡ tập.
3. **Sửa metadata có lineage.** Hiện có 12 title mở đầu bằng “Copyright 2018 Google LLC”. Tạo title mô tả từ path/service cho derivative, lưu original_title và source hash. Giữ error code, command text và version string. Với Hugo includes/YAML, chỉ nối snippets đã có provenance; không đi theo link ngoài một cách tự động.
4. **Chốt chunking cùng tokenizer.** Ưu tiên section; chunk quá dài mới chia theo giới hạn encoder đã chọn, tính cả prefix và special tokens. Ghi số token thật, overlap và offsets trên normalized document text. ID mới phải phân biệt phiên bản; lưu mapping về ID cũ. Thử một cấu hình ban đầu, sửa bằng train pilot trước annotation cuối.
5. **Audit trùng và citation.** Kiểm exact hash rồi rà near-duplicate/boilerplate; không tính nhiều chunk cùng document thành nhiều tài liệu độc lập. Với toàn bộ chunks, xác nhận `text[start:end]`, citation tồn tại, source URL/commit/license đầy đủ. Kiểm nhiều Unicode, đoạn rỗng, quá dài và include thiếu.
6. **Khóa corpus ứng viên.** Xuất manifest gồm whitelist, exclusions, normalization/chunking version, tokenizer revision, hashes và thời điểm tạo. Cấm index `proposed-mappings`, annotation answers hoặc nhánh labels. Khi pilot cho thấy thiếu evidence, ghi gap theo claim và bổ sung nguồn hợp lệ trước freeze; đổi corpus phải rebuild mọi baseline và đánh dấu qrels cần chấm lại.

## Success Criteria

- [ ] Cả 74 tài liệu có quyết định và lý do; unknown không bị đổi thành compatible.
- [ ] Tất cả chunks kiểm offsets/hash/token budget/citation thành công.
- [ ] Corpus manifest tái tạo được cùng ID/text; không chứa mappings hoặc gold.
- [ ] Báo rõ số tài liệu được dùng, bị loại, chưa biết applicability và gap cần pilot xác minh.

## Risk Assessment

Runbook platform có thể không hỗ trợ lỗi nghiệp vụ. Nếu pilot thiếu bằng chứng, thu hẹp claim thành hỗ trợ kiểm tra hoặc bổ sung corpus trước khóa; reranker không chữa được thiếu kiến thức. Nếu sửa corpus sau dev, version lại và chạy mọi đối chứng liên quan; không sửa theo câu trả lời test. Không gọi current và historical là hai nguồn độc lập; không khẳng định tái hiện triage năm 2024 chỉ từ ngày commit.
