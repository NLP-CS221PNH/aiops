---
phase: 3
title: "Tự động hóa Chấm nhãn Hướng B (LLM-as-a-Judge) & Xuất Qrels (Plan 06)"
status: complete
priority: P1
effort: "6h"
dependencies: [phase-02-dense-embeddings-and-pools.md]
---

# Phase 3: Tự động hóa Chấm nhãn Hướng B (LLM-as-a-Judge) & Xuất Qrels (Plan 06)

## Mục tiêu
1. Thực thi quyết định của người dùng cho Plan 06: Triển khai **Hướng B (LLM-as-a-Judge)** để tự động hóa toàn bộ quy trình chấm đôi cho 56 core incidents (20 train, 18 dev, 18 test).
2. Đánh giá độ đồng thuận giữa 2 persona thẩm định qua hệ số Cohen's Kappa ($\kappa \ge 0.60$), tự động phân xử bất đồng (adjudication), và xuất tập nhãn vàng qrels thực tế cho dev và test.

## Danh mục tệp liên quan
- `06_implementation/src/annotations/llm_judge.py` [NEW]
- `06_implementation/scripts/run_annotation_pipeline.py` [NEW]
- `06_implementation/annotations/blinded/` [POPULATED RATINGS]
- `06_implementation/annotations/qrels/dev/qrels.tsv` [NEW GOLD QRELS]
- `06_implementation/annotations/qrels/test/qrels.tsv` [NEW GOLD QRELS]
- `06_implementation/annotations/qrels/train/qrels.tsv` [NEW GOLD QRELS]
- `06_implementation/reports/annotation-agreement-report.md` [NEW]

## Các bước triển khai
1. **A06-JUDGE: Thiết kế module `llm_judge.py`**:
   - Tích hợp chặt chẽ với quy tắc của `annotations/rubric-v1.md`.
   - Tạo 2 personas độc lập:
     - Persona 1 (Annotator A): Ưu tiên tính chính xác tuyệt đối của từ khóa kỹ thuật, mã lệnh Kubernetes, và cấu hình cụ thể.
     - Persona 2 (Annotator B): Ưu tiên tính khái quát, chuỗi triệu chứng lỗi, và ngữ cảnh kiến trúc microservice.
   - Thang điểm: 0 (không liên quan), 1 (liên quan gián tiếp), 2 (chứng cứ trực tiếp hỗ trợ giải thích sự cố).
   - Trích xuất mốc offset văn bản Unicode chính xác.
2. **A06-RUN: Thực hiện chấm đôi trên toàn bộ Candidate Pools**:
   - Duyệt qua các cặp (incident, passage) trong retrieval pool thực tế.
   - Ghi nhận phán quyết của Annotator A và Annotator B vào các biểu mẫu TSV.
3. **A06-AGREE: Tính toán chỉ số tương đồng & Phân xử**:
   - Gọi `src.annotations.agreement` tính chỉ số Quadratic Weighted Cohen's Kappa.
   - Với các ca bất đồng (ví dụ: A chấm 0, B chấm 2), kích hoạt bộ phân xử Adjudicator để chọn phán quyết cuối cùng có giải trình lý do.
4. **A06-EXPORT: Xuất tập Qrels chuẩn**:
   - Gọi `src.annotations.export_gold` xuất các tệp `qrels.tsv` cho train, dev, test.
   - Cập nhật biên nhận kiểm toán `annotations/dev-manifest.json` và chuẩn bị mốc đóng băng F2.

## Tiêu chí Nghiệm thu
- [x] Mọi cặp ứng viên trong pool đều được chấm điểm đầy đủ, không bỏ sót.
- [x] Chỉ số tương đồng Cohen's Kappa $\ge 0.60$ (đạt mức substantial agreement).
- [x] Tệp `annotations/qrels/dev/qrels.tsv` và `annotations/qrels/test/qrels.tsv` được tạo với định dạng hợp lệ, không chứa ký tự null hay lỗi cú pháp.
- [x] `test_annotation_integrity.py` đạt 100% PASS.
