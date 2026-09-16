---
phase: 5
title: "Tái tổng hợp Số liệu, Biên dịch Báo cáo PDF & Đóng gói (Plan 10)"
status: complete
priority: P1
effort: "4h"
dependencies: [phase-04-generation-freeze-evaluation.md]
---

# Phase 5: Tái tổng hợp Số liệu, Biên dịch Báo cáo PDF & Đóng gói (Plan 10)

## Mục tiêu
1. Cập nhật 4 bảng kết quả định lượng tại `reports/final-tables/` từ dữ liệu thực tế thu được trong `results/per-incident.tsv`.
2. Đồng bộ các con số thực nghiệm vào Báo cáo nghiên cứu `reports/final-report.md` và Slide thuyết trình `reports/slides.md`.
3. Biên dịch lại publication-ready `final-report.pdf` và `slides.pdf`.
4. Cập nhật mã băm SHA256 và niêm phong gói nộp bài `reports/submission-package/`.

## Danh mục tệp liên quan
- `06_implementation/reports/final-tables/` [UPDATED TABLES]
- `06_implementation/reports/final-report.md` [UPDATED WITH REAL STATS]
- `06_implementation/reports/slides.md` [UPDATED SLIDES]
- `06_implementation/reports/final-report.pdf` [RECOMPILED PDF]
- `06_implementation/reports/slides.pdf` [RECOMPILED PDF]
- `06_implementation/configs/final-manifest.json` [UPDATED MANIFEST]
- `06_implementation/reports/submission-package/` [RESEALED BUNDLE]
- `06_implementation/reports/submission-package/CHECKSUMS_SHA256.txt` [FINAL CHECKSUMS]

## Các bước triển khai
1. **R10-TAB: Tạo lại 4 bảng số liệu**:
   - Chạy script tổng hợp để cập nhật:
     - Table 1: Retrieval Performance (passage nDCG@5, MRR@10, Recall@20, Paired Delta).
     - Table 2: Grounded Generation Performance (Top-1/Top-3 Service Accuracy, Citation Validity, Claim Support, Abstention).
     - Table 3: Six-Family Diagnostics & LOFO Sensitivity.
     - Table 4: Resource & Latency Accounting.
2. **R10-DOC: Đồng bộ văn bản báo cáo và slide**:
   - Cập nhật số liệu vào Mục 6 của `final-report.md` và các trang slide tương ứng trong `slides.md`.
   - Cập nhật mục Khai báo sử dụng AI phản ánh trung thực việc sử dụng LLM-as-a-Judge theo Hướng B.
3. **R10-PDF: Biên dịch lại PDF**:
   - Chạy `python 06_implementation/scripts/build_pdfs.py` sử dụng ReportLab để tạo lại 2 tệp PDF có font tiếng Việt chuẩn xác.
4. **R10-PKG: Đóng gói niêm phong bàn giao**:
   - Chạy `python 06_implementation/scripts/package_release.py` để cập nhật `final-manifest.json` và tạo gói nộp bài hoàn chỉnh trong `submission-package/`.
   - Chạy toàn bộ regression test suite (`pytest 06_implementation/tests`) để xác nhận không có bất kỳ regression nào.

## Tiêu chí Nghiệm thu
- [x] 4 bảng trong `final-tables/` khớp từng con số với `per-incident.tsv`.
- [x] `final-report.pdf` và `slides.pdf` được tạo mới với dung lượng hợp lệ (>100 KB), mở xem được.
- [x] Tệp `CHECKSUMS_SHA256.txt` trong `submission-package/` khớp 100% mã băm của các tệp nộp.
- [x] Toàn bộ 302+ bài test tự động PASS 100%.
