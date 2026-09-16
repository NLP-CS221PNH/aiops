---
phase: 2
title: "Hiện thực hóa Dense Embeddings & Candidate Pools (Plan 05)"
status: complete
priority: P1
effort: "4h"
dependencies: [phase-01-unblock-data-and-corpus.md]
---

# Phase 2: Hiện thực hóa Dense Embeddings & Candidate Pools (Plan 05)

## Mục tiêu
1. Thực thi quyết định của người dùng cho Plan 05: Tải mô hình `intfloat/e5-small-v2` (~130 MB) và sinh vector embeddings thực tế cho toàn bộ 580 chunks.
2. Chạy công cụ tìm kiếm lai Hybrid RRF ($c=60$) trên dữ liệu thật cho 56 core incidents (20 train, 18 dev, 18 test) để kết xuất tập ứng viên Top-10 thực tế chuẩn bị cho việc chấm nhãn.

## Danh mục tệp liên quan
- `06_implementation/scripts/download_e5_assets.py` [NEW]
- `06_implementation/vendor/e5-small-v2/` [DOWNLOAD ASSETS]
- `06_implementation/scripts/build_embeddings.py` [NEW]
- `06_implementation/cache/retrieval/e5_embeddings.npy` [NEW CACHE]
- `06_implementation/configs/retrieval.yaml` [MODIFY]
- `06_implementation/annotations/pools/` [UPDATE REAL POOLS]

## Các bước triển khai
1. **R05-DL: Tải và xác minh tài sản mô hình**:
   - Viết script `download_e5_assets.py` tải `config.json` và `model.safetensors` từ HuggingFace repository `intfloat/e5-small-v2` đúng revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`.
   - Lưu trữ vào `06_implementation/vendor/e5-small-v2/`.
   - Tính toán và xác nhận mã băm SHA256 khớp với hàm `verify_model_assets` trong `dense.py`.
2. **R05-EMB: Sinh embeddings thật cho 580 chunks**:
   - Khởi tạo tokenizer và encoder `e5-small-v2` trên CPU/GPU.
   - Thêm tiền tố `passage: ` cho từng chunk.
   - Sinh ma trận vector $580 \times 384$, chuẩn hóa cosine vector $L_2$.
   - Lưu trữ an toàn vào `cache/retrieval/` có fingerprint kiểm toán.
3. **R05-POOL: Chạy Hybrid Retrieval thật**:
   - Sử dụng các truy vấn R2 đã được chuẩn hóa từ Plan 04.
   - Chạy BM25 và Dense Index, hợp nhất kết quả bằng RRF $c=60$.
   - Xuất danh sách Top-10 candidate chunks cho 56 core incidents để cập nhật tệp `manager-pool.tsv`.

## Tiêu chí Nghiệm thu
- [x] Hàm `verify_model_assets()` trong `dense.py` xác thực thành công bộ trọng số tải về.
- [x] Ma trận embeddings có kích thước $(580, 384)$, không chứa giá trị NaN hay Inf.
- [x] Tệp pool ứng viên cho 56 incidents được tạo với dữ liệu thật, không dùng fixture giả định.
