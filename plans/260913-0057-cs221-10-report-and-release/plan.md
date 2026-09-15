---
title: "10 — Báo cáo, tái lập và gói bàn giao"
description: "Viết báo cáo từ tuần 1, liên kết mọi kết luận tới bằng chứng và đóng gói kết quả, demo, nguồn cùng hướng dẫn tái lập."
status: pending
priority: P1
effort: "28h"
tags: [research, docs, aiops, rag]
blockedBy: [260913-0057-cs221-08-evaluation-and-freeze, 260913-0057-cs221-09-evidence-demo]
blocks: [260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 10 — Báo cáo, tái lập và gói bàn giao

## Tổng quan

Viết báo cáo từ tuần 1, liên kết mọi kết luận tới bằng chứng và đóng gói kết quả, demo, nguồn cùng hướng dẫn tái lập.
Khung tuần 1; tổng hợp tuần 7; tái lập và bảo vệ tuần 8. Đây là kế hoạch tương lai; chưa tạo `06_implementation/`, chưa chạy hay đánh dấu hoàn thành công việc.
Căn cứ: [master](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md), [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).

## Goal contract

| Thành phần | Hợp đồng |
|---|---|
| Kết quả cần đạt | Báo cáo/slides và gói local truy được số liệu; thành viên khác tính lại được bảng chính từ evaluator artifacts; giới hạn chỉ áp dụng cho optional raw/model reruns. |
| Bằng chứng hoàn tất | Các sản phẩm có đường dẫn, version/hash, người kiểm và checklist nghiệm thu trong phase 03 |
| Owner / reviewer | C điều phối; A kiểm dữ liệu/nguồn; B kiểm thiết kế, kết quả và tái lập |
| Công dự kiến | 28 giờ-người, cộng dự phòng trong master; không phải giờ Codex đã thực hiện |
| Ngoài phạm vi | Nộp/gửi/publish thay nhóm, tuyên bố production hoặc causal chain, sinh số liệu còn thiếu, hứa tái lập token từ alias API. |

## Hiện trạng và bất biến

- Bộ có 90 incidents, 30 service×fault families; split 54 train / 18 dev / 18 test.
- Core qrels dự kiến 20 train + 18 dev + 18 test; hiện có **0 human judgments**.
- Test có 6 families; không coi repetitions, claims hoặc log rows là mẫu độc lập.
- RQ chính: passage nDCG@5; hybrid so baseline đơn mạnh hơn trên dev, hòa chọn BM25 trước test.
- G0/GB/GD/GH bắt buộc; GR chỉ khi quyết định trước F1 và đủ nguồn lực.
- `G0` trong protocol là gate khởi động; `G0` trong runs là điều kiện no-RAG, ghi rõ loại để tránh nhầm.
- Không dùng test để tune; không đặt yêu cầu hybrid phải thắng.
- Kaggle Free và API là nguồn lực có điều kiện; không coi quyền dùng model/chi tiền đã được duyệt.

## Các phase

| Phase | Nội dung | Công | Trạng thái |
|---|---|---:|---|
| 1 | [Khung báo cáo và nguồn](phase-01-start.md) | 6h | pending |
| 2 | [Kết quả và lập luận](phase-02-build.md) | 12h | pending |
| 3 | [Tái lập, đóng gói, bảo vệ](phase-03-validate-and-handoff.md) | 10h | pending |

## Dependency và bàn giao

Bản thảo dùng 01 và nguồn nghiên cứu. Kết luận cuối cần 06/08 khóa nhãn/kết quả; nghiệm thu cần 09.
Dependency chi tiết được kiểm ở từng gate; đọc `blockedBy` như phụ thuộc hoàn tất, không mặc định cấm soạn khung sớm.
Đầu ra sai contract phải trả lại owner kèm lỗi có thể tái hiện; không sửa ngầm artifact đã freeze.

## Codex làm gì, nhóm làm gì

- **Codex:** Soạn cấu trúc, tổng hợp nguồn, sinh bảng từ artifacts, audit claim–evidence, đóng gói và hỗ trợ diễn tập.
- **Con người:** A/B/C viết và chịu trách nhiệm phần mình, đọc bài thực, xác nhận đóng góp và nộp đúng yêu cầu môn học.
- Quyết định chưa có phản hồi giữ `pending` với owner và hạn; không tự suy thành đồng ý.
- Codex chỉ soạn nội dung liên lạc; mọi gửi thư/tin nhắn cần yêu cầu riêng rõ ràng.

## Kho sản phẩm dự kiến

Gốc tuyệt đối: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/`.
Danh sách con: `reports/final-report.md; reports/final-report.pdf; reports/slides.md; reports/claim-evidence.tsv; docs/reproduce.md; docs/data-and-model-card.md; configs/final-manifest.json; reports/release-checklist.md`.
Từng phase bên dưới nêu đầy đủ đường dẫn, thao tác và bên nhận; các file này chưa được tạo trong lần lập kế hoạch.

## Nghiệm thu và rủi ro

- [ ] Các task có đầu vào, hành động, đầu ra và người kiểm; ba phase đạt gate đã nêu.
- [ ] Mọi kết quả thực được phân biệt với giả định, fixture và công việc chưa chạy.
- [ ] Không rò gold/reference/qrels sang inference; ledger giữ ca lỗi và thiếu evidence.
- [ ] Người nhận xác nhận version và tái hiện được bằng chứng bàn giao.
Kết quả âm, CI rộng và thiếu evidence phải được giữ; deadline chưa chốt nên dùng lịch tuần tương đối.

