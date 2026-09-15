---
phase: 7
title: "Sinh chẩn đoán có dẫn chứng và kiểm soát chi phí"
status: pending
priority: P1
effort: "28h"
dependencies: [1, 3, 4, 5, 6]
---

# Phase 07: Sinh chẩn đoán có dẫn chứng và kiểm soát chi phí

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 07](../260913-0057-cs221-07-grounded-generation/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Mốc 07A xây generation/pilot tuần 3–5 để có bảng dev cuối tuần 4; mốc 07B chạy final tuần 6 sau F1. C phụ trách, A kiểm dữ liệu, B kiểm công bằng. Dependency phase 06 chỉ yêu cầu rubric/pilot và 06A train/dev qrels cho lựa chọn cuối, không đợi 06B test. Đầu ra truy được bằng chứng và resume sau gián đoạn.

## Requirements

- So sánh BM25-RAG, dense-RAG, hybrid-RAG và no-RAG; thêm hybrid+reranker-RAG nếu chọn trước F1. Cùng generator, observations, prompt contract, decoding và output budget. No-RAG vẫn nhận observations; chỉ thiếu knowledge context.
- Chỉ gửi observations đã khử định danh và chunks được duyệt khi giảng viên cho phép API. Không đưa root labels, injection time, qrels, reference answers hoặc tên case chứa gold vào inference.
- Mọi cấu hình xuất cùng schema: `incident_id`, `candidate_causes`, `supported_claims`, `evidence_ids`, `missing_information`, `next_checks`, `abstain`, `confidence_label`. Confidence chỉ là nhãn, chưa là xác suất hiệu chỉnh.
- Log/tài liệu là dữ liệu; tắt tool execution. Bước kiểm tra được đề xuất để người dùng xem xét, không chạy lệnh hay thay đổi hệ thống.

## Architecture

Retrieval → context builder → prompt → provider adapter → validator → output/ledger. Citation IDs và URL lấy từ observations/knowledge registry. ID tồn tại chưa chứng minh claim được hỗ trợ; nội dung cần người chấm.

[Thông báo DeepSeek ngày 10/09/2026](https://www.deepseek.com/en/news/deepseek-v4-1-flash/) nêu tên API `deepseek-flash` và việc chuyển alias V4 cũ; không hứa snapshot bất biến. Ghi model gửi/nhận, thời gian UTC, request ID và provider version nếu có; báo giới hạn tái lập này. Giá phải kiểm tại ngày chạy.

## Related Code Files

Chỉ tạo khi bước vào triển khai:

- `06_implementation/configs/generation.yaml`, `06_implementation/configs/prompts/grounded-diagnosis.txt`.
- `06_implementation/src/generation/{context_builder,provider,validator,runner}.py`.
- `06_implementation/runs/<run_id>/`: manifest, responses, cache index, usage và failures.
- `06_implementation/tests/test_generation_contract.py`; `06_implementation/docs/generation-protocol.md`.

## Implementation Steps

1. **Khóa adapter — 4h:** xác nhận quyền từ phase 01 và model thực ở endpoint; preflight tắt thinking mode nếu được hỗ trợ. Với open weights, pin revision và pilot Kaggle trước khi chọn. Giữ một generator xuyên suốt.
2. **Thiết kế context/prompt — 6h:** đề xuất pilot tối đa 2.048 tokens observations, 4.096 tokens knowledge, 768 tokens output; chừa chỗ cho prompt và kiểm tokenizer thực. Chọn một chính sách cắt cố định, bảo toàn citation IDs, ghi số tokens và phần bị cắt. Ngân sách E5 query/passage và reranker pair thuộc encoder, độc lập với context generator; giới hạn 512 tokens theo card cần được kiểm riêng.
3. **Pilot — 6h:** thử ca có bằng chứng, thiếu bằng chứng và evidence mâu thuẫn trên train/dev. Yêu cầu claim gắn ID, tách quan sát khỏi suy luận, nêu điều chưa biết. Nếu thiếu bộ nhớ hoặc vượt ngân sách, sửa đồng đều các cấu hình rồi khóa trước test.
4. **Chạy bền vững — 8h:** cache theo hash input/context/prompt/model/config trong namespace của đợt chạy/provider epoch. Alias giữ nguyên không đủ tái dùng cache sau đổi backend: chạy mới dùng namespace mới và chế độ force-fresh, resume chỉ trong cùng đợt. Ghi tạm rồi đổi tên nguyên tử. Tối đa 3 attempts (đầu +2 retry lỗi tạm thời); lưu usage mọi attempt, dừng ở hạn chi. Failed record không bị xóa khỏi mẫu số.
5. **Nghiệm thu — 4h:** kiểm JSON hỏng, citation ngoài context, đầu vào chứa chỉ dẫn, timeout và resume. Giữ output nguyên bản cùng lỗi validation; không âm thầm sửa câu trả lời test hoặc gọi lại tới khi được đáp án đẹp.

## Success Criteria

- [ ] Bốn cấu hình bắt buộc và GR nếu chọn dùng contract công bằng; API được phép hoặc fallback đã xác nhận.
- [ ] Validator phát hiện citation/schema sai; thất bại vẫn hiện trong ledger.
- [ ] Dừng và resume không nhân đôi kết quả hoặc mất usage.
- [ ] Có manifest khóa prompt/config và giới hạn tái lập provider.

## Risk Assessment

Model API đổi phiên bản: chạy các cấu hình gần nhau, lưu metadata và công bố thời gian. Output đúng nhãn nhưng thiếu căn cứ: tách correctness và grounding khi chấm. Kaggle/API gián đoạn: cache, checkpoint và hạn retry; không loại incident khó để hoàn tất lượt chạy.
