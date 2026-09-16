---
phase: 1
title: "Mở khóa Dữ liệu & Phê duyệt Kho tri thức (Plans 02 & 03)"
status: complete
priority: P1
effort: "4h"
dependencies: []
---

# Phase 1: Mở khóa Dữ liệu & Phê duyệt Kho tri thức (Plans 02 & 03)

## Mục tiêu
1. Thực thi quyết định của người dùng cho Plan 02: Điền giá trị trung bình (mean imputation) cho 35.333 ô metrics null trong telemetry và tạo script/notebook hỗ trợ môi trường Kaggle GPU.
2. Thực thi quyết định của người dùng cho Plan 03: Chính thức phê duyệt 74 tài liệu của Corpus (chấp thuận 67 tài liệu hợp lệ và 7 tài liệu loại trừ), phát hành manifest `reviewed` để mở khóa cổng giải phóng (release gate) cho retrieval.

## Danh mục tệp liên quan
- `06_implementation/src/data/impute.py` [NEW]
- `06_implementation/configs/data.yaml` [MODIFY]
- `06_implementation/scripts/kaggle_gpu_runner.py` [NEW]
- `06_implementation/configs/corpus.yaml` [MODIFY]
- `06_implementation/reports/corpus_approval_receipt.json` [NEW]

## Các bước triển khai
1. **D02-IMP: Xây dựng module `impute.py`**:
   - Nhận diện các giá trị `null` trong `metric-summaries.jsonl`.
   - Tính toán giá trị trung bình theo từng loại `metric_name` và `service`.
   - Tạo bộ dữ liệu xuất khẩu `re2-ob-inference-v2-imputed`.
   - Xuất nhật ký kiểm toán `imputation-audit.json` ghi nhận chính xác các vị trí đã điền.
2. **D02-KAG: Soạn thảo script `kaggle_gpu_runner.py`**:
   - Thiết lập cấu hình môi trường Linux CUDA / PyTorch tương thích với Windows local venv.
3. **K03-APP: Phê duyệt Corpus 74 tài liệu**:
   - Cập nhật `06_implementation/configs/corpus.yaml` sang `status: reviewed`.
   - Tạo `corpus_approval_receipt.json` xác nhận 67 tài liệu hợp lệ và 7 tài liệu loại trừ (tài liệu không thuộc stack Online Boutique).
   - Xác nhận cổng kiểm soát G1/Release của Plan 03 chính thức đạt yêu cầu kỹ thuật.

## Tiêu chí Nghiệm thu
- [x] Hàm `impute.py` điền đúng giá trị mean, không còn ô null không mong muốn, bảo toàn 90 incident IDs.
- [x] Script Kaggle GPU chạy được cú pháp và kiểm tra CUDA device.
- [x] `corpus_approval_receipt.json` được tạo thành công, `test_corpus_integrity.py` đạt 100% PASS.
