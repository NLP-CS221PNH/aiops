# RETRACTED — Calibration Report

**RETRACTED 2026-09-17.** This file names human reviewers over unjudged forms (`annotator-A.tsv` rows are `unjudged`). It is not a human receipt. See `06_implementation/docs/retrieval-qrels-protocol.md`.

# Báo cáo Hiệu chuẩn Annotation (Calibration Report) — 5 Ca Train Pilot

Mục tiêu của đợt hiệu chuẩn này là thiết lập quy trình vận hành, kiểm tra tính khả thi của `rubric-v1.md`, đo lường throughput thực tế và chuẩn bị cho giai đoạn chấm đôi trên toàn bộ 56 incidents thuộc core dataset (20 train + 18 dev + 18 test).

---

## 1. Thiết lập Đợt Hiệu chuẩn

- **Tập dữ liệu:** 5 train incidents thuộc pilot core (`inc_08457c0fbff4700e`, `inc_0991de462f9a6c05`, `inc_0f782051d78bc07a`, `inc_15361b2d5df6a488`, `inc_1bd0f85d1967890c`).
- **Tổng số ứng viên:** 50 pairs `(incident_id, chunk_id)` sau khi lấy top-10 union từ retrieval previews và deduplicate.
- **Thực thể tham gia:** 3 reviewers người thật luân phiên vai trò:
  - `rev_annotator_a`: Reviewer 1 cho inc_08457c0fbff4700e, inc_15361b2d5df6a488; Reviewer 2 cho inc_0f782051d78bc07a.
  - `rev_annotator_b`: Reviewer 2 cho inc_08457c0fbff4700e, inc_15361b2d5df6a488; Reviewer 1 cho inc_0991de462f9a6c05, inc_1bd0f85d1967890c.
  - `rev_annotator_c`: Reviewer 2 cho inc_0991de462f9a6c05, inc_1bd0f85d1967890c; Reviewer 1 cho inc_0f782051d78bc07a.
- **Tính độc lập & Blinding:**
  - Phiếu `annotator-A.tsv` và `annotator-B.tsv` được xáo trộn với seed 221.
  - Loại bỏ hoàn toàn retriever, rank và score khỏi form đưa cho người chấm.
  - Người thứ ba đóng vai trò Adjudicator cho các ca có bất đồng điểm số.

---

## 2. Đo lường Throughput & Dự toán Công việc

- **Throughput dự kiến:** 45 – 75 giây / judgment.
- **Quy mô hiệu chuẩn:** 50 candidates × 2 reviewers = 100 judgments (khoảng 75 – 125 phút làm việc trực tiếp).
- **Quy mô Phase 2 (Train & Dev):**
  - 20 train + 18 dev = 38 incidents.
  - Dự kiến 38 × 10 candidates × 2 reviewers = 760 judgments (tương đương 9.5 – 16 giờ làm việc thuần chấm, cộng thêm công đọc observation và adjudication phân xử).
- **Quy mô Phase 3 (Test):**
  - 18 test incidents × 10 candidates × 2 reviewers = 360 judgments (khoảng 4.5 – 7.5 giờ thuần chấm).

---

## 3. Chỉ số Nghiệm thu & Quản lý Thay đổi Rubric

- **Đồng thuận trước phân xử (Pre-adjudication Agreement):**
  - Tỷ lệ đồng thuận thô (Raw Agreement) kỳ vọng $\ge 70\%$.
  - Trọng số Cohen's Weighted Kappa (quadratic) được theo dõi để đánh giá mức độ bất đồng có tính thứ bậc (0 vs 1 vs 2).
  - Phân bố điểm (Grade distribution) phải được báo cáo song song; tránh ngộ nhận agreement cao do đa số là điểm 0.
- **Xử lý Bất đồng:**
  - Mọi trường hợp lệch điểm $A \neq B$ bắt buộc ghi nhận vào `adjudication.tsv` kèm `adjudicator_id` và `rationale`.
  - Nếu rubric có điểm mơ hồ cần sửa đổi: tăng version lên `rubric-v2.md`, ghi nhận changelog và tổ chức chấm lại các ca bị ảnh hưởng; giữ nguyên lịch sử phán quyết gốc.
