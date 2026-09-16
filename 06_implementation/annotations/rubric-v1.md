# Rubric v1 cho Phán quyết và Đánh giá (CS221)

Dựa trên rubric nền (annotation-kit), cập nhật các trường cụ thể:

## Mức độ Relevance (Grade)

| Grade | Ý nghĩa | Ví dụ |
|-------|---------|-------|
| 0 | **Không liên quan / Sai bối cảnh**: Không cung cấp thông tin giúp ích cho claim. | Bài viết về cấu hình network DNS cho một lỗi thanh toán, nơi nguyên nhân gốc rễ là API key. |
| 1 | **Liên quan nhưng gián tiếp**: Có liên quan đến service hoặc chủ đề nhưng không hỗ trợ trực tiếp. | README mô tả workflow chung của service, không có chi tiết chẩn đoán lỗi. |
| 2 | **Hỗ trợ trực tiếp / Nguyên nhân gốc rễ (Root Cause)**: Trực tiếp hỗ trợ đánh giá một claim, ca kiểm tra, hoặc chẩn đoán nguyên nhân gốc. | Log lỗi rõ ràng, giải thích cách kiểm tra resource limit liên quan đến CPU throttle. |

## Các Trường Yêu Cầu Cho Mỗi Phán Quyết

1. `reviewer_id`: ID của người chấm.
2. `grade`: Mức relevance 0, 1 hoặc 2. (Passage và Document có grade riêng).
3. `reviewed_at`: Thời gian hoàn thành đánh giá.
4. `evidence_role`: Loại bằng chứng (ví dụ: `symptom_interpretation`, `service_dependency`, `diagnostic_check`, `elimination_check`, `root_cause_support`, `counter_evidence`, `context_only`).
5. `supported_claim`: Tóm tắt claim mà bằng chứng này hỗ trợ.
6. `applicability`: Bằng chứng có áp dụng được trong bối cảnh hệ thống (phiên bản, môi trường) không (`compatible`, `incompatible`, `uncertain`).
7. `span_start` và `span_end`: Vị trí bắt đầu/kết thúc đoạn bằng chứng bằng Unicode codepoint trên văn bản document (chỉ cho passage).
8. `review_state`: Trạng thái đánh giá.

## Phân xử (Adjudication)
Trong trường hợp bất đồng giữa hai phiếu A/B:
Người thứ 3 (Adjudicator) sẽ ghi `final_grade` và `rationale`. Các phiếu gốc (A/B) được giữ nguyên, không thay đổi (immutable).

## Answerability (Khả năng trả lời)
- `answerable`: Đủ dữ liệu và bằng chứng trong corpus.
- `partially_answerable`: Có bằng chứng một phần, thiếu vài bước cụ thể.
- `unanswerable`: Thiếu bằng chứng hoàn toàn trong corpus hiện tại.
- `uncertain_pending_review`: Chờ kiểm tra thêm.

*Lưu ý: Document relevance và Passage relevance là hai trường hoàn toàn độc lập. Passage (chunk) có thể mang grade 0 trong khi Document là grade 2.*
