---
title: "07 — Generator có dẫn chứng và pilot train/dev"
description: "Xây adapter, context packer, validator và runner dùng lại được; pilot train/dev công bằng cho G0, GB, GD, GH và GR nếu được chọn."
status: completed
priority: P1
effort: "28h"
tags: [research, docs, aiops, rag]
blockedBy: [260913-0057-cs221-05-retrieval-baselines]
blocks: [260913-0057-cs221-08-evaluation-and-freeze, 260913-0057-cs221-09-evidence-demo, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 07 — Generator có dẫn chứng và pilot train/dev

## Tổng quan

Xây adapter, context packer, validator và runner dùng lại được; pilot train/dev công bằng cho G0, GB, GD, GH và GR nếu được chọn.
Tuần 3–5; dừng tại adapter và pilot đã bàn giao cho F1. Đây là kế hoạch tương lai; chưa tạo `06_implementation/`, chưa chạy hay đánh dấu hoàn thành công việc.
Căn cứ: [master](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md), [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).

## Goal contract

| Thành phần | Hợp đồng |
|---|---|
| Kết quả cần đạt | Adapter chịu lỗi, output/usage đầy đủ, pilot train/dev có audit; 08 sở hữu toàn bộ execution cuối sau F1. |
| Bằng chứng hoàn tất | Các sản phẩm có đường dẫn, version/hash, người kiểm và checklist nghiệm thu trong phase 03 |
| Owner / reviewer | C điều phối; A kiểm dữ liệu/nguồn; B kiểm thiết kế, kết quả và tái lập |
| Công dự kiến | 28 giờ-người, cộng dự phòng trong master; không phải giờ Codex đã thực hiện |
| Ngoài phạm vi | Chạy final test, chọn cấu hình từ test, tự chữa production, fine-tuning, agent tools hoặc gọi lại theo chất lượng đáp án. |

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
| 1 | [Khóa contract và preflight](phase-01-start.md) | 6h | completed |
| 2 | [Xây adapter và pilot](phase-02-build.md) | 14h | completed |
| 3 | [Kiểm độ bền và bàn giao F1](phase-03-validate-and-handoff.md) | 8h | completed |

## Dependency và bàn giao

Nhận input/corpus/query/retrieval từ 02–05 và rubric/pilot 06A; quyền mô hình từ 01. Không chờ 06B test.
Dependency chi tiết được kiểm ở từng gate; đọc `blockedBy` như phụ thuộc hoàn tất, không mặc định cấm soạn khung sớm.
Đầu ra sai contract phải trả lại owner kèm lỗi có thể tái hiện; không sửa ngầm artifact đã freeze.

## Codex làm gì, nhóm làm gì

- **Codex:** Viết code/prompt/schema, test có ý nghĩa, chạy pilot trong tài nguyên đã được phép, lập ledger và báo cáo lỗi.
- **Con người:** C cấp secrets qua kênh phù hợp; A duyệt payload; B kiểm công bằng; người chấm đánh giá support. Không dùng Codex thay human judgments.
- Quyết định chưa có phản hồi giữ `pending` với owner và hạn; không tự suy thành đồng ý.
- Codex chỉ soạn nội dung liên lạc; mọi gửi thư/tin nhắn cần yêu cầu riêng rõ ràng.

## Kho sản phẩm dự kiến

Gốc tuyệt đối: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/`.
Danh sách con: `configs/generation.yaml; configs/prompts/grounded-diagnosis.txt; src/generation/context_builder.py; src/generation/provider.py; src/generation/validator.py; src/generation/runner.py; docs/generation-protocol.md; reports/generation-pilot.md`.
Từng phase bên dưới nêu đầy đủ đường dẫn, thao tác và bên nhận; các file này chưa được tạo trong lần lập kế hoạch.

## Nghiệm thu và rủi ro

- [x] Các task có đầu vào, hành động, đầu ra và người kiểm; ba phase đạt gate đã nêu.
- [x] Mọi kết quả thực được phân biệt với giả định, fixture và công việc chưa chạy.
- [x] Không rò gold/reference/qrels sang inference; ledger giữ ca lỗi và thiếu evidence.
- [x] Người nhận xác nhận version và tái hiện được bằng chứng bàn giao.
API chưa được phép: tiếp tục fixtures/adapter; pilot local chỉ sau quyết định cho phép và kiểm Kaggle thực.
