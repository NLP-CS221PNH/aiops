---
title: "09 — Demo offline kiểm được evidence"
description: "Dựng demo Python cục bộ từ artifacts, giúp người xem đi từ incident tới claim và đoạn evidence thực sự đã được gửi generator."
status: complete
priority: P1
effort: "12h"
tags: [research, docs, aiops, rag]
blockedBy: [260913-0057-cs221-07-grounded-generation]
blocks: [260913-0057-cs221-10-report-and-release, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 09 — Demo offline kiểm được evidence

## Tổng quan

Dựng demo Python cục bộ từ artifacts, giúp người xem đi từ incident tới claim và đoạn evidence thực sự đã được gửi generator.
Đã hoàn thành toàn bộ 3 phases với các artifact: loader bảo mật, local web viewer 3 panels, bộ cấu hình 5 ca (thành công, chẩn đoán yếu, thiếu bằng chứng/abstain, lỗi trích dẫn, so sánh đối chứng GB vs GH), runbook, script thuyết trình 5-7 phút, case audit, rehearsal và demo manifest bàn giao cho Phase 10.
Căn cứ: [master](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md), [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).

## Goal contract

| Thành phần | Hợp đồng |
|---|---|
| Kết quả cần đạt | Demo 5–7 phút, cache có nhãn, ca sai/thiếu evidence, đường dẫn citation đúng và phương án mất mạng. |
| Bằng chứng hoàn tất | Các sản phẩm có đường dẫn, version/hash, người kiểm và checklist nghiệm thu trong phase 03 |
| Owner / reviewer | C điều phối; A kiểm dữ liệu/nguồn; B kiểm thiết kế, kết quả và tái lập |
| Công dự kiến | 12 giờ-người, cộng dự phòng trong master; không phải giờ Codex đã thực hiện |
| Ngoài phạm vi | Deploy cloud, tài khoản đăng nhập, telemetry production, dashboard lớn hoặc tự động chạy bước khắc phục. |

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
| 1 | [Chọn hợp đồng và kịch bản](phase-01-start.md) | 2h | complete |
| 2 | [Xây màn hình và nối artifacts](phase-02-build.md) | 6h | complete |
| 3 | [Tổng duyệt và bàn giao](phase-03-validate-and-handoff.md) | 4h | complete |

## Dependency và bàn giao

Khung cần contract 07 và corpus/input 02–04. Bộ case nghiên cứu cuối phải nhận runs và phân tích từ 08.
Dependency chi tiết được kiểm ở từng gate; đọc `blockedBy` như phụ thuộc hoàn tất, không mặc định cấm soạn khung sớm.
Đầu ra sai contract phải trả lại owner kèm lỗi có thể tái hiện; không sửa ngầm artifact đã freeze.

## Codex làm gì, nhóm làm gì

- **Codex:** Scaffold UI tối thiểu, loader manifest, selector case/config, hiển thị lỗi, kiểm citation và viết kịch bản.
- **Con người:** C chọn kịch bản và trình bày; A kiểm nguồn; B đối chiếu runs. Chỉ nhóm bật live khi đã được phép.
- Quyết định chưa có phản hồi giữ `pending` với owner và hạn; không tự suy thành đồng ý.
- Codex chỉ soạn nội dung liên lạc; mọi gửi thư/tin nhắn cần yêu cầu riêng rõ ràng.

## Kho sản phẩm dự kiến

Gốc tuyệt đối: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/`.
Danh sách con: `src/demo/app.py; src/demo/loaders.py; configs/demo-cases.yaml; docs/demo-script.md; docs/demo-runbook.md; reports/demo/case-audit.tsv; reports/demo/rehearsal.md; reports/demo/demo-manifest.json; reports/demo/backup/`.
Đã hoàn thành toàn bộ và kiểm thử độc lập thành công.

## Nghiệm thu và rủi ro

- [x] Các task có đầu vào, hành động, đầu ra và người kiểm; ba phase đạt gate đã nêu.
- [x] Mọi kết quả thực được phân biệt với giả định, fixture và công việc chưa chạy.
- [x] Không rò gold/reference/qrels sang inference; ledger giữ ca lỗi và thiếu evidence.
- [x] Người nhận xác nhận version và tái hiện được bằng chứng bàn giao.
Thiếu final runs thì dùng fixture gắn nhãn để xây giao diện; không tạo kết quả nghiên cứu giả.
