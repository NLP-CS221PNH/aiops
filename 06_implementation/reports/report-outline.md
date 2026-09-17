# Đề cương Báo cáo Đồ án và Ánh xạ Rubric (CS221 AIOps Hybrid RAG)

Artifact ID: `cs221-report-outline-v1`  
Phiên bản: `1.0.0`  
Ngày tạo: `2026-09-16T01:30:00Z`  
Điều phối: Thành viên C (Editor & Integration)  
Kiểm tra: Thành viên A (Data & Annotation), Thành viên B (Method & Evaluation)  

---

## 1. Bảng phân công Section và Ánh xạ Rubric môn học

Bảng ánh xạ toàn diện giữa yêu cầu đồ án môn học CS221 (Natural Language Processing / Advanced Information Retrieval) với cấu trúc các chương mục báo cáo, phân định rõ Owner, Reviewer, đầu vào cần thiết và trạng thái hoàn thành.

| Section ID | Tên chương mục | Yêu cầu Rubric CS221 | Owner | Reviewer | Đầu vào chính (Artifacts / Refs) | Trạng thái (Phase 1) |
|---|---|---|:---:|:---:|---|:---:|
| **SEC-01** | Tiêu đề, Tóm tắt (Abstract) & Tuyên bố Đóng góp | Tóm tắt rõ ràng bài toán, phương pháp, kết quả chính và đóng góp NLP | C | A, B | `00_plan/project_proposal.md`, `06_implementation/docs/research-protocol.md` | Draft (kết quả pending) |
| **SEC-02** | Giới thiệu bài toán & Mục tiêu nghiên cứu (Introduction & Problem Formulation) | Nêu rõ bối cảnh AIOps, microservice triage, định nghĩa 3 RQs (RQ1 representation, RQ2 retrieval, RQ3 grounded generation) | C | B | `00_plan/project_proposal.md`, `00_plan/remaining-work.md`, `plans/reports/260913-independent-plans-contracts.md` | Hoàn tất khung |
| **SEC-03** | Nghiên cứu liên quan (Related Work) | So sánh có hệ thống 8–10 bài liên quan về bài toán, dữ liệu, baseline, metric; chỉ dẫn nguồn đã xác minh | A / C | B | `06_implementation/docs/literature-matrix.tsv`, `06_implementation/reports/references.bib` | Hoàn tất |
| **SEC-04** | Dữ liệu, Phân chia & Kiểm soát rò rỉ (Dataset, Split & Leakage Controls) | 90 incidents, 30 families (54/18/18), phòng ngừa data leakage (temporal, cross-family, label contamination) | A | C | `06_implementation/reports/data-handoff.md`, `06_implementation/reports/corpus-handoff.md` | Hoàn tất dữ liệu |
| **SEC-05** | Phương pháp: Biểu diễn, Truy hồi & Sinh (Methodology: Representation, IR & Generation) | Thiết kế R1/R2/R3, BM25, Dense E5-small-v2, RRF Fusion, 4 generation conditions (G0, GB, GD, GH) | B | A | `06_implementation/docs/research-protocol.md`, `06_implementation/freezes/F1.json` | Hoàn tất thiết kế |
| **SEC-06** | Quy trình Đánh giá & Thiết kế Thí nghiệm (Evaluation Protocol & Metrics) | Primary passage nDCG@5, MRR@10, Recall@20, Task correctness, Citation validity/support, Family cluster analysis | B | C | `06_implementation/docs/research-protocol.md`, `06_implementation/src/evaluation/metrics.py` | Hoàn tất |
| **SEC-07** | Kết quả thực nghiệm (Experimental Results) | Bảng kết quả định lượng, so sánh paired deltas, 6 test families, đánh dấu số mẫu n và uncertainty | B | A, C | `06_implementation/results/`, `06_implementation/freezes/F2.json` | Slots pending (Phase 2 điền) |
| **SEC-08** | Phân tích Lỗi & Khảo sát chuyên sâu (Error Taxonomy & Case Studies) | Phân tích 5 loại lỗi (wrong-version, unsupported cause, upstream/downstream, missing evidence, abstention) | C | B | `06_implementation/reports/demo/case-audit.tsv`, `06_implementation/reports/error-analysis.md` | Slots pending (Phase 2 điền) |
| **SEC-09** | Thảo luận, Giới hạn & Đạo đức (Discussion, Limitations & Ethical Considerations) | Phân tích kết quả âm/hòa, độ bất định của 6 families, giới hạn API không bất biến, khai báo AI | C | A, B | `06_implementation/docs/decision-log.md`, `06_implementation/docs/data-and-model-card.md` | Khung hoàn tất |
| **SEC-10** | Khả năng Tái lập & Gói bàn giao (Reproducibility, Artifacts & Release Handoff) | Hướng dẫn chạy lại mã nguồn, manifest kiểm tra mã băm SHA256, evaluator bundle độc lập | C | B | `06_implementation/docs/reproduce.md`, `06_implementation/configs/final-manifest.json` | Khung hoàn tất |

---

## 2. Ma trận Bằng chứng (Evidence Slots Mapping)

Mỗi kết luận định lượng hoặc khẳng định khoa học trong báo cáo bắt buộc phải gắn với một slot bằng chứng cụ thể:

| Mã Slot | Section | Nội dung cần chứng minh | Nguồn bằng chứng quy định (Artifact Path) | Trạng thái Phase 1 |
|---|---|---|---|:---:|
| `SLOT-DATA-01` | SEC-04 | Tổng số 90 incidents, 30 families, phân chia 54 train / 18 dev / 18 test | `06_implementation/reports/data-handoff.md` | Sẵn sàng |
| `SLOT-DATA-02` | SEC-04 | Kho tri thức lịch sử tiền 2024: 74 tài liệu, 580 chunks chuẩn hóa | `06_implementation/reports/corpus-handoff.md` | Sẵn sàng |
| `SLOT-ANNO-01` | SEC-04 | Core 56 incidents (20 train, 18 dev, 18 test) có human double-judgment | `06_implementation/annotations/` | Sẵn sàng |
| `SLOT-METH-01` | SEC-05 | Khóa tham số và kiến trúc tại mốc F1 trước test | `06_implementation/freezes/F1.json` | Sẵn sàng |
| `SLOT-RES-01` | SEC-07 | Điểm passage nDCG@5 của IR-B, IR-D, IR-H trên dev và test | `06_implementation/results/per-incident.tsv` | Chờ Phase 2 |
| `SLOT-RES-02` | SEC-07 | Hiệu số bắt cặp (paired delta) giữa Hybrid và Single mạnh hơn trên dev | `06_implementation/results/per-incident.tsv` | Chờ Phase 2 |
| `SLOT-RES-03` | SEC-07 | Độ chính xác dịch vụ (service accuracy) trên toàn bộ 18 test incidents | `06_implementation/results/` | Chờ Phase 2 |
| `SLOT-RES-04` | SEC-07 | Tỉ lệ trích dẫn hợp lệ và tỉ lệ claim được bằng chứng hỗ trợ | `06_implementation/annotations/response-judgments.tsv` | Chờ Phase 2 |
| `SLOT-FAM-01` | SEC-07 | Thống kê phân bố theo 6 test service×fault families và leave-one-out | `06_implementation/results/family-comparison.tsv` | Chờ Phase 2 |
| `SLOT-ERR-01` | SEC-08 | Ca lỗi thực tế: sai lệch phiên bản tài liệu (wrong-version) | `06_implementation/reports/demo/case-audit.tsv` | Sẵn sàng |
| `SLOT-ERR-02` | SEC-08 | Ca lỗi thực tế: suy diễn không có bằng chứng hỗ trợ (unsupported) | `06_implementation/reports/demo/case-audit.tsv` | Sẵn sàng |
| `SLOT-ERR-03` | SEC-08 | Ca xử lý đúng: hệ thống từ chối trả lời khi thiếu dữ kiện (abstention) | `06_implementation/reports/demo/case-audit.tsv` | Sẵn sàng |

---

## 3. Quy chuẩn Trình bày và Ranh giới Trách nhiệm

1. **Ngôn ngữ báo cáo:** Tiếng Việt học thuật, giữ nguyên các danh từ riêng kỹ thuật, mã lỗi, định danh thực thể (ví dụ: `frontend`, `checkoutservice`, `redis-cart`, `HTTP 500`, `CrashLoopBackOff`) và tên chỉ số chuẩn quốc tế (`passage nDCG@5`, `MRR@10`, `Recall@20`).
2. **Không bịa số:** Mọi ô số liệu chưa có kết quả từ artifact thực được ghi `NOT_RUN` hoặc `PENDING`. Tuyệt đối không dùng số giả định hoặc số ước lượng từ paper khác để điền vào bảng kết quả của hệ thống.
3. **Phân định rõ ràng trách nhiệm:**
   - **Thành viên A:** Chịu trách nhiệm nội dung Dữ liệu, Chú thích và Thu thập corpus.
   - **Thành viên B:** Chịu trách nhiệm Mô hình, Thí nghiệm Truy hồi và Đánh giá định lượng.
   - **Thành viên C:** Chịu trách nhiệm Tích hợp hệ thống, Soạn thảo báo cáo chung và Đóng gói bàn giao.
   - **Codex (Trợ lý AI):** Hỗ trợ soạn thảo khung, trích xuất dữ liệu tự động từ artifacts đã khóa, kiểm toán liên kết claim–evidence, không thay thế chữ ký và phán quyết khoa học của người thật.
