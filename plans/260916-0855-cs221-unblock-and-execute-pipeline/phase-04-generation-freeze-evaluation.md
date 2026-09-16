---
phase: 4
title: "Chạy Sinh Thật, Đóng băng F1/F2 & Đánh giá (Plans 07 & 08)"
status: complete
priority: P1
effort: "6h"
dependencies: [phase-03-llm-judge-annotation-qrels.md]
---

# Phase 4: Chạy Sinh Thật, Đóng băng F1/F2 & Đánh giá (Plans 07 & 08)

## Mục tiêu
1. Thực hiện sinh chẩn đoán có dẫn chứng thực tế cho 18 test incidents dưới 4 điều kiện đối chứng (G0, GB, GD, GH) $\rightarrow$ 72 phản hồi sinh hoàn chỉnh.
2. Đóng băng hệ thống tại F1 và đóng băng nhãn tại F2 với mã băm SHA256 thực tế.
3. Chạy toàn diện module đánh giá `src/evaluation/metrics.py` để tính toán số liệu định lượng thực tế và lưu trữ kết quả.

## Danh mục tệp liên quan
- `06_implementation/runs/generation/test/` [REAL RUN OUTPUTS]
- `06_implementation/freezes/F1.json` [CRYPTOGRAPHIC F1 FREEZE]
- `06_implementation/freezes/F2.json` [CRYPTOGRAPHIC F2 FREEZE]
- `06_implementation/scripts/execute_evaluation.py` [NEW]
- `06_implementation/results/per-incident.tsv` [REAL QUANTITATIVE RESULTS]
- `06_implementation/results/family-comparison.tsv` [REAL FAMILY RESULTS]
- `06_implementation/reports/freeze-chain-audit.json` [UPDATED AUDIT]

## Các bước triển khai
1. **G07-RUN: Chạy thực tế Grounded Generation**:
   - Nạp context phù hợp cho từng điều kiện: G0 (chỉ telemetry), GB (telemetry + top BM25), GD (telemetry + top Dense), GH (telemetry + top Hybrid RRF).
   - Thiết lập nhiệt độ $T = 0.0$ để đảm bảo tính tất định.
   - Thu thập 72 phản hồi chẩn đoán JSON, kiểm tra cấu trúc và tính hợp lệ của citation bằng `src.generation.validator`.
2. **E08-FREEZE: Tạo mốc khóa F1 và F2**:
   - Sinh `F1.json` chứa mã băm của code retriever, code generator, prompt template, và config đã khóa trên tập Dev.
   - Sinh `F2.json` chứa mã băm của tập qrels Test đã phân xử từ Phase 3.
   - Đảm bảo F1 được đóng trước khi truy cập kết quả đánh giá Test.
3. **E08-EVAL: Tính toán các chỉ số thực tế**:
   - Tính toán `passage nDCG@5` cho IR-B, IR-D, IR-H trên tập test.
   - Tính toán `Top-1 và Top-3 Service Localization Accuracy`.
   - Tính toán `Citation Validity (%)` và `Claim Support Precision (%)`.
   - Tính toán `Abstention Rate (%)`.
   - Chạy phân tích độ nhạy cụm 6 families bằng kỹ thuật Leave-One-Family-Out (LOFO).
   - Ghi dữ liệu chi tiết từng incident vào `results/per-incident.tsv`.

## Tiêu chí Nghiệm thu
- [x] Đủ 72 bản ghi sinh chẩn đoán được lưu trữ trong `runs/generation/test/`.
- [x] Tệp `F1.json` và `F2.json` có mã băm SHA256 thật, không còn chuỗi placeholder.
- [x] Tệp `results/per-incident.tsv` có đầy đủ 72 dòng kết quả đánh giá thực tế.
- [x] `test_evaluation_contract.py` và `test_generation_contract.py` đạt 100% PASS.
