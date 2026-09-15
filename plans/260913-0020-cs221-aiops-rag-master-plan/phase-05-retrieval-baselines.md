---
phase: 5
title: "Ba baseline retrieval và reranker tùy chọn"
status: pending
priority: P1
effort: "36h"
dependencies: [2, 3, 4]
---

# Phase 5: Ba baseline retrieval và reranker tùy chọn

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 05](../260913-0057-cs221-05-retrieval-baselines/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

B phụ trách IR; A kiểm dữ liệu, C kiểm context. Dự kiến 36 giờ công tuần 2–5: B 28h, A 4h, C 4h. Chuyển BM25 preview thành runner tái lập, bổ sung dense/hybrid và reranker tùy pilot. Mốc 05A nhận query draft 04A để tạo pool; 05B khóa cấu hình sau dev qrels 06A, không đợi toàn phase 06/test.

## Requirements

- Cùng query, snapshot, chunk IDs và content fields; lưu metadata của từng ranking.
- RQ2 chính: hybrid so với BM25/dense mạnh hơn, chọn bằng passage nDCG@5 trên dev; không chọn đối thủ bằng test.
- Khóa model revision, prefix/normalization và môi trường; model cards chưa đồng nghĩa weights đã chạy.
- Kaggle miễn phí cần cache/checkpoint và CPU fallback; không bảo đảm quota/GPU hay latency.

## Architecture

Corpus → BM25 và embeddings → hai ranking → RRF → hybrid top-50 → cross-encoder. Corpus khoảng 580 chunks cho phép exact dense search, chưa cần vector database.

| Điều kiện | Cấu hình khởi đầu, chốt trên dev |
|---|---|
| BM25 | k1=1,2; b=0,75; depth 50 |
| Dense | E5-small-v2; normalized cosine; depth 50 |
| Hybrid | RRF hai ranking; constant 60; trọng số bằng nhau |
| Hybrid + rerank | BGE-reranker-base trên hybrid top-50 |

Top-5 phục vụ context; lưu top-50 để chẩn đoán. Reranker không được tìm thêm evidence bằng gold.

## Related Code Files

Đọc [BM25 preview](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/preview-retrieval.py:34) và [proposal](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/experiment-proposal.json:1). Tạo khi triển khai:

- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval.py` — bốn nhánh.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml` — cấu hình.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/notebooks/02_retrieval.ipynb` — Kaggle entry point.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/` — rankings/manifests.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_retrieval_contract.py` — kiểm fusion/IDs.

## Implementation Steps

1. Đóng gói BM25 hiện có, tie-break theo chunk ID. Dense nhận cùng policy `section_heading + text`; chốt tokenizer bảo toàn technical tokens.
2. Audit truncation: E5 tối đa 512 tokens; reranker tối đa 512 cho query+passage. Chốt chunking trước annotation; đổi chunks phải version lại qrels liên quan.
3. Tạo embeddings và cache theo corpus hash/model revision. Chạy lại mẫu để kiểm ranking trong tolerance đã ghi; không dùng cache khác cấu hình.
4. Tạo RRF; pilot reranker trên cùng candidate pool nếu đủ tài nguyên. Đo riêng preprocessing, retrieval và rerank khi chạy, RAM/VRAM thực; ghi batch/warmup và hardware.
5. Xuất union top-10 của ba hệ thống bắt buộc, thêm reranker nếu được đánh giá: tối đa 30/40 candidates/incident trước dedup. Core 56 gồm 20 train, 18 dev, 18 test; 34 train còn lại tùy chọn. Phase 6 chấm mù; test pool chỉ xuất sau F1 ở phase 8.
6. Thử ít cấu hình trên dev, lưu mọi trial. Chọn representation và baseline đối chứng; nếu nDCG@5 bằng nhau, chọn BM25. Candidates mới cần chấm trước so sánh.
7. Khóa query/corpus/retrievers cùng prompt phase 7. Xuất IDs cho bốn nhánh generation bắt buộc và GR nếu có rerank. Nếu reranker chậm, giảm batch hoặc dùng cache/CPU; quyết định bỏ nhánh phải trước F1 và cập nhật mọi pool/ma trận.

## Validation Scenarios

| Tình huống | Kết quả cần kiểm |
|---|---|
| Hai ranking nhỏ có ties/duplicate IDs | RRF đúng fixture; IDs duy nhất, thứ hạng ổn định |
| Đổi corpus hash hoặc model revision | Cache cũ bị từ chối |
| Relevant evidence ngoài top-50; hoặc passage bị cắt | Báo giới hạn candidate/truncation; không quy lỗi chỉ cho reranker |

## Success Criteria

- [ ] Ba ranking bắt buộc và rerank nếu chọn dùng cùng inputs, IDs/hash hợp lệ.
- [ ] Có pool mù và provenance tách riêng.
- [ ] Cấu hình/đối thủ được chọn trên dev trước test.
- [ ] Có judged coverage, truncation và chi phí đo thật.

## Risk Assessment

Corpus thiếu evidence hoặc sai version không thể sửa bằng reranker. Recall@20/50 với qrels chưa đầy đủ chỉ là pooled diagnostic; báo judged coverage, đào sâu khi cần. Không coi outside-pool là negative. Gián đoạn Kaggle cần resume theo manifest; không trộn output khác model/config vào cùng run.
