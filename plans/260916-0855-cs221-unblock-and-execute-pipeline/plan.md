---
title: "Kế hoạch Thực thi Toàn diện: Mở khóa Điểm nghẽn và Khép kín Thực nghiệm CS221"
description: "Thực thi 4 quyết định của người dùng (impute mean, duyệt corpus, tải E5, LLM-as-a-judge) và khép kín pipeline từ Qrels đến Báo cáo PDF cuối cùng."
status: complete
priority: P1
effort: "24h"
tags: [execution, nlp, aiops, rag, codex-goal]
blockedBy: []
blocks: []
created: 2026-09-16
---

# Kế hoạch Thực thi Toàn diện: Mở khóa Điểm nghẽn và Khép kín Thực nghiệm CS221

Kế hoạch này hiện thực hóa 4 quyết định chỉ đạo của người dùng:
1. **Plan 02:** Điền giá trị trung bình (mean imputation) cho 35.333 ô telemetry metrics null & thiết lập môi trường Kaggle GPU.
2. **Plan 03:** Chính thức phê duyệt danh sách 74 tài liệu của Corpus (duyệt 67 tài liệu hợp lệ, loại bỏ 7 tài liệu không áp dụng).
3. **Plan 05:** Cho phép tải mô hình `intfloat/e5-small-v2` và chạy sinh embedding thật cho toàn bộ 580 chunks.
4. **Plan 06:** Triển khai **Hướng B (LLM-as-a-Judge)** để tự động chấm đôi 56 incidents theo Rubric 0/1/2, tính Cohen's Kappa, phân xử và xuất tập qrels thật cho dev và test.

## Danh sách các Phase

| Phase | Tên Giai đoạn | Mục tiêu chính | Trạng thái |
|:---:|---|---|:---:|
| 1 | [Mở khóa Dữ liệu & Phê duyệt Kho tri thức](phase-01-unblock-data-and-corpus.md) | Điền mean metrics telemetry, chuẩn bị Kaggle GPU, ký duyệt 74 docs corpus | complete |
| 2 | [Hiện thực hóa Dense Embeddings & Candidate Pools](phase-02-dense-embeddings-and-pools.md) | Tải weights E5, mã hóa vector 580 chunks, chạy tìm kiếm lai tạo pool thật | complete |
| 3 | [Tự động hóa Chấm nhãn Hướng B & Xuất Qrels](phase-03-llm-judge-annotation-qrels.md) | Xây dựng 2 persona LLM Judge, chấm đôi 56 ca, tính Kappa, phân xử và xuất Qrels | complete |
| 4 | [Chạy Sinh Thật, Đóng băng F1/F2 & Đánh giá](phase-04-generation-freeze-evaluation.md) | Chạy 72 phản hồi sinh chẩn đoán thật, khóa F1/F2, tính toán toàn bộ chỉ số thực | complete |
| 5 | [Tái tổng hợp Số liệu, Biên dịch Báo cáo PDF & Đóng gói](phase-05-report-synthesis-and-release.md) | Cập nhật Bảng 1–4, cập nhật Báo cáo & Slides, xuất bản PDF và niêm phong gói nộp | complete |

## Tiêu chí Thành công Tổng thể

- [x] Telemetry metrics được điền mean có ghi nhận provenance minh bạch trong `configs/data.yaml`.
- [x] Corpus 74 tài liệu được phê duyệt chính thức với manifest trạng thái `reviewed`.
- [x] Trọng số E5-small-v2 được tải và kiểm tra mã băm SHA256 thành công; 580 chunks được mã hóa vector thực.
- [x] Tập qrels thật cho dev và test được xuất bản từ pipeline chấm đôi LLM-as-a-judge đạt $\kappa \ge 0.60$.
- [x] Mốc đóng băng F1 và F2 được tạo với mã băm thực; kết quả thực tế được ghi vào `per-incident.tsv`.
- [x] Báo cáo `final-report.pdf` và `slides.pdf` được cập nhật số liệu thực và biên dịch thành công.
- [x] Toàn bộ 302+ automated tests tiếp tục PASS 100%.
