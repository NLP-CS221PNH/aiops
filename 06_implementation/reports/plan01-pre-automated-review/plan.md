---
title: "01 — Phạm vi, protocol và thỏa thuận nhóm"
description: "Chốt hợp đồng nghiên cứu cho 8 tuần và ba thành viên; biến giả định môn học, tài nguyên và đánh giá thành quyết định có người chịu trách nhiệm."
status: in-progress
priority: P1
effort: "12h"
tags: [research, docs, aiops, rag]
blockedBy: []
blocks: [260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 01 — Phạm vi, protocol và thỏa thuận nhóm

## Tổng quan

Chốt hợp đồng nghiên cứu cho 8 tuần và ba thành viên; biến giả định môn học, tài nguyên và đánh giá thành quyết định có người chịu trách nhiệm.
Tuần 1; quyết định API/fallback theo dõi tới cuối tuần 2. Đây là kế hoạch tương lai; chưa tạo `06_implementation/`, chưa chạy hay đánh dấu hoàn thành công việc.
Căn cứ: [master](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md), [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).

## Goal contract

| Thành phần | Hợp đồng |
|---|---|
| Kết quả cần đạt | Protocol v1, ma trận bài lõi, quyết định có bằng chứng và phân công A/B/C được nhóm review. |
| Bằng chứng hoàn tất | Các sản phẩm có đường dẫn, version/hash, người kiểm và checklist nghiệm thu trong phase 03 |
| Owner / reviewer | C điều phối; A kiểm dữ liệu/nguồn; B kiểm thiết kế, kết quả và tái lập |
| Công dự kiến | 12 giờ-người, cộng dự phòng trong master; không phải giờ Codex đã thực hiện |
| Ngoài phạm vi | Đổi đề tài, chạy API, tạo annotation, chạy thí nghiệm hoặc gửi thông điệp thay nhóm. |

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
| 1 | [Thu thập ràng buộc](phase-01-start.md) | 3h | pending |
| 2 | [Soạn protocol và phân công](phase-02-build.md) | 6h | pending |
| 3 | [Review và bàn giao G0](phase-03-validate-and-handoff.md) | 3h | pending |

## Dependency và bàn giao

Không có dependency triển khai. Đọc bộ nghiên cứu và master hiện có; bàn giao G0 cho 02–10.
Dependency chi tiết được kiểm ở từng gate; đọc `blockedBy` như phụ thuộc hoàn tất, không mặc định cấm soạn khung sớm.
Đầu ra sai contract phải trả lại owner kèm lỗi có thể tái hiện; không sửa ngầm artifact đã freeze.

## Codex làm gì, nhóm làm gì

- **Codex:** Viết charter, protocol, thư nháp hỏi giảng viên, ma trận nghiên cứu, checklist và kiểm nhất quán.
- **Con người:** Nhóm xác nhận rubric/hạn nộp, đọc bài lõi, phân công; giảng viên quyết định API/open weights. Codex không gửi thư.
- Quyết định chưa có phản hồi giữ `pending` với owner và hạn; không tự suy thành đồng ý.
- Codex chỉ soạn nội dung liên lạc; mọi gửi thư/tin nhắn cần yêu cầu riêng rõ ràng.

## Kho sản phẩm dự kiến

Gốc tuyệt đối: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/`.
Danh sách con: `docs/project-charter.md; docs/research-protocol.md; docs/decision-log.md; docs/literature-matrix.tsv; docs/team-working-agreement.md; docs/instructor-questions-draft.md; configs/protocol.yaml; freezes/G0/manifest.json`.
Từng phase bên dưới nêu đầy đủ đường dẫn, thao tác và bên nhận; các file này chưa được tạo trong lần lập kế hoạch.

## Nghiệm thu và rủi ro

- [ ] Các task có đầu vào, hành động, đầu ra và người kiểm; ba phase đạt gate đã nêu.
- [ ] Mọi kết quả thực được phân biệt với giả định, fixture và công việc chưa chạy.
- [ ] Không rò gold/reference/qrels sang inference; ledger giữ ca lỗi và thiếu evidence.
- [ ] Người nhận xác nhận version và tái hiện được bằng chứng bàn giao.
Thiếu rubric hoặc phản hồi API chỉ chặn phần tương ứng; dữ liệu, IR và annotation vẫn chuẩn bị được.

## Bằng chứng thực hiện — 2026-09-13

Đã triển khai phần Codex của plan 01 trong `06_implementation`; các câu mô tả “chưa tạo” phía trên là trạng thái khi lập kế hoạch. Trạng thái hiện tại là **in-progress, G0 awaiting_human_review**. Không có phase nào đã được nhóm nghiệm thu; các checkbox acceptance gốc giữ nguyên. Mục này bổ sung tiến độ, không thay điều kiện gate hoặc ký thay A/B/C.

| Phase | Phần kỹ thuật đã thực hiện | Phần nghiệm thu còn thiếu |
|---|---|---|
| 1 | Charter, inventory audit, decision log 16 quyết định có owner/reviewer/hạn, thư nháp | C chấp nhận inventory/câu hỏi; A/B review; tên, rubric, lịch và nguồn quyết định thật |
| 2 | Protocol MD/YAML, literature matrix 10 bài với mức đọc Codex, working agreement và nhánh fallback | Người thật đọc/review bài, xác nhận phân công/giờ và kiểm thiết kế/nguồn lực |
| 3 | Review issues, validator/tests, builder candidate manifest và checklist bàn giao | Chữ ký người thật đúng version/hash, human G0 review và receiver acknowledgments |

[Báo cáo tiến độ](../../06_implementation/reports/plan01-progress.md) ánh xạ đủ 12 task, receipt kiểm tra và hạn chế công cụ. [Protocol review](../../06_implementation/docs/protocol-review.md) phân biệt technical validation với G0 readiness. Phần hoàn tất kỹ thuật không biến 0 human judgments, permission pending hoặc communication pending thành approved/completed.

Đã sweep cả ba phase để backfill bằng chứng. Không dùng `ak plan check` vì lệnh sẽ hoàn tất cả các điều kiện cần người; ghi notes/evidence qua CLI và reindex. Plan overall chuyển `in-progress` bằng CLI, các phase giữ trạng thái acceptance pending. Không commit/Git init vì workspace không là Git repository; không chạy kế hoạch 02–10 từ lượt này.
