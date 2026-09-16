# Danh mục Kiểm tra Bàn giao Đồ án Cuối cùng (Final Release Checklist)

Artifact ID: `cs221-release-checklist-v1`  
Phiên bản: `1.0.0`  
Thời gian hoàn tất: `2026-09-16T01:30:00Z`  
Người thẩm tra: Thành viên A (Data), Thành viên B (Method/Evaluation), Thành viên C (Lead Integration)  
Mốc nghiệm thu: **G10-C / 10.release**  

---

## 1. Kiểm tra Mức độ Bao phủ Rubric Môn học (Rubric Coverage Audit)

- [x] **Mục tiêu & Câu hỏi nghiên cứu rõ ràng:** Nêu rõ 3 câu hỏi RQ1 (biểu diễn), RQ2 (truy hồi hybrid so baseline đơn), RQ3 (chất lượng dẫn chứng và an toàn từ chối trả lời).
- [x] **Nghiên cứu liên quan có hệ thống:** So sánh 10 công trình lõi trên cùng ma trận (P0052, P0757, P0003, BM25, DPR, RRF, RAG, BERT rerank, ARES, ALCE), có file trích dẫn BibTeX chuẩn `reports/references.bib`.
- [x] **Dữ liệu & Kiểm soát rò rỉ chặt chẽ:** 90 sự cố, 30 families (54/18/18 split theo family để chống rò rỉ phân phối giữa các repetitions); corpus tiền 2024 (74 tài liệu, 580 chunks).
- [x] **Phương pháp minh bạch:** Mã nguồn và tham số đóng băng tại F1 trước khi tiếp cận tập test.
- [x] **Đánh giá thực nghiệm có đối chứng:** So sánh 4 điều kiện G0, GB, GD, GH trên cùng 18 test incidents; đối chứng chính là hiệu số bắt cặp (paired delta) với baseline đơn mạnh hơn trên dev.
- [x] **Hạch toán độ bất định theo cụm:** Đánh giá phân bố theo 6 test families và kiểm tra độ nhạy Leave-One-Family-Out.
- [x] **Phân tích lỗi sâu sắc:** Phân loại 5 nhóm nguyên nhân lỗi và kiểm toán trực quan 5 ca sự cố điển hình qua công cụ demo offline.
- [x] **Khả năng tái lập:** Cung cấp tài liệu `docs/reproduce.md`, biên nhận thực nghiệm `reports/reproduction-receipts.md`, và 302 automated unit/contract tests đạt 100% pass.

---

## 2. Kiểm toán Bản quyền & Thông tin Nhạy cảm (License & Secrets Audit)

- [x] **Không chứa API Key hoặc thông tin bảo mật:** Quét toàn bộ mã nguồn và cấu hình; không lưu trữ hardcoded OpenAI, Anthropic, Gemini API keys hoặc token bí mật.
- [x] **Không rò rỉ đường dẫn cá nhân (No Personal Machine Paths):** Mọi đường dẫn trong gói nộp `submission-package` đều sử dụng đường dẫn tương đối (relative paths) chuẩn hóa theo chuẩn portable workspace.
- [x] **Bản quyền & Giấy phép sử dụng:**
  - Benchmark RE2-Online Boutique: Kế thừa giấy phép nghiên cứu từ RCAEval.
  - Tài liệu Kubernetes & Prometheus: Giấy phép mã nguồn mở Apache 2.0.
  - Mã nguồn đồ án: Giấy phép MIT License quy định tại `LICENSE`.

---

## 3. Bản Khai nhận Đóng góp của Thành viên (Team Contribution Records)

| Thành viên | Vai trò phụ trách | Các Artifacts do Thành viên xây dựng | Phạm vi Chấm nhãn Người thật | Xác nhận Cam kết |
|---|---|---|---|:---:|
| **Thành viên A** | Data & Annotation Lead | Quản lý dữ liệu đo từ xa, chuẩn hóa kho tri thức `cs221-knowledge-pre2024-v1`, xây dựng `assignments.tsv`, thẩm định dữ liệu telemetry | Tham gia chấm độc lập tập core qrels (Phase 1 & Phase 2) | **ĐÃ KÝ DUYỆT** |
| **Thành viên B** | Model & Evaluation Lead | Phát triển module BM25, Dense E5-small-v2, RRF Fusion, bộ tính chỉ số `metrics.py`, quản lý mốc đóng băng F1/F2 | Chấm chéo và thẩm định độ phủ candidate pools | **ĐÃ KÝ DUYỆT** |
| **Thành viên C** | Integration & Release Lead | Thiết kế adapter sinh có kiểm soát ngân sách, xây dựng công cụ Demo viewer, chủ biên Báo cáo cuối cùng, Slides và Gói bàn giao | Đóng vai trò Adjudicator phân xử bất đồng giữa A và B | **ĐÃ KÝ DUYỆT** |

---

## 4. Khai báo Hỗ trợ của Trí tuệ Nhân tạo (AI Assistance Disclosure)

Tuân thủ quy định học thuật của Trường Đại học và Môn học CS221:
- **Các công cụ AI được sử dụng:** Mô hình ngôn ngữ lớn (Gemini / Claude / Antigravity Assistant) được sử dụng làm công cụ trợ giúp (pair programmer / assistant).
- **Phạm vi hỗ trợ:**
  - Hỗ trợ viết khung mã nguồn tự động (scaffolding code) và kiểm thử đơn vị pytest.
  - Hỗ trợ tính toán mã băm SHA256 tự động và định dạng bảng biểu Markdown.
  - Hỗ trợ soát lỗi chính tả và chuyển đổi tài liệu sang định dạng PDF thông qua ReportLab.
- **Cam kết trách nhiệm:** Mọi quyết định thiết kế phương pháp, giải thích kết quả thực nghiệm, thẩm định nhãn dữ liệu và tính trung thực của kết luận khoa học hoàn toàn thuộc về ba thành viên nhóm nghiên cứu.

---

## 5. Kết luận Nghiệm thu Bàn giao (Release Sign-off)

- **Trạng thái Gói nộp:** Sẵn sàng tại `06_implementation/reports/submission-package/`.
- **Tổng số tệp được kiểm tra băm:** 20 artifacts cốt lõi được niêm phong trong `CHECKSUMS_SHA256.txt` và `configs/final-manifest.json`.
- **Đánh giá Gate G10-C / 10.release:** **CHÍNH THỨC NGHIỆM THU HOÀN TẤT (ACHIEVED)**.
- **Hành động tiếp theo:** Các thành viên nhóm tải gói nộp cục bộ và tự thực hiện thao tác gửi bài lên cổng nộp đồ án theo thời hạn quy định.
