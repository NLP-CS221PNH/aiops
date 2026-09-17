# Data and Model Card — CS221 AIOps Hybrid RAG

Artifact ID: `cs221-data-model-card-v1`  
Phiên bản: `1.0.0-verified`  
Ngày cập nhật: `2026-09-16T01:30:00Z`  
Người phụ trách: Thành viên A (Data), Thành viên B (Model), Thành viên C (Integration)  

---

## 1. Dataset Card

### Thông tin tổng quan (Dataset Summary)
- **Dataset Name:** RE2-Online Boutique Incident Telemetry Benchmark (Derivative for CS221)
- **System Under Test:** Google Cloud Microservices Demo (Online Boutique 10-11 services: `frontend`, `cartservice`, `productcatalogservice`, `currencyservice`, `paymentservice`, `shippingservice`, `emailservice`, `checkoutservice`, `recommendationservice`, `adservice`, `redis-cart`).
- **Nguồn gốc dữ liệu gốc:** Benchmark [RCAEval](https://github.com/phamquiluan/RCAEval) (Wang et al., 2024), tập RE2 với đầy đủ 3 loại dữ liệu đo từ xa: logs bán cấu trúc, metrics hệ thống và distributed traces.

### Quy mô và Phân bố mẫu (Dataset Scale & Split)
- **Tổng số incidents:** `90` incidents phân bố đồng đều trên `30` service×fault families.
- **Cấu trúc lặp (Repetitions):** Mỗi family có chính xác `3` lần tiêm lỗi độc lập (`repetition_1`, `repetition_2`, `repetition_3`).
- **Phân chia tập (Dataset Split):**
  - **Train:** 54 incidents (18 families, 3 repetitions/family).
  - **Dev:** 18 incidents (6 families, 3 repetitions/family).
  - **Test:** 18 incidents (6 families, 3 repetitions/family).
- **Nguyên tắc phân chia:** Split theo cụm `service×fault family`. Tuyệt đối không phân chia ngẫu nhiên theo incident đơn lẻ để ngăn chặn triệt để hiện tượng rò rỉ phân phối lỗi (distribution leakage) giữa các repetitions.
- **Cửa sổ quan sát (Observation Window):** Giới hạn chặt chẽ theo cửa sổ thời gian tiêm lỗi đã được chuẩn hóa trong schema `04_representation`.

### Phạm vi Kho tri thức (Knowledge Corpus Scope)
- **Tập dữ liệu:** `cs221-knowledge-pre2024-v1`.
- **Quy mô:** 74 tài liệu, 580 chunks.
- **Phân đoạn (Chunking Policy):** Chuẩn hóa Unicode, tiêu đề mục (`section_heading`) kèm văn bản (`text`), đánh chỉ mục codepoint offsets chính xác.
- **Nguồn tài liệu:** Kubernetes Troubleshooting Guides, Prometheus Operator Runbooks, kiến trúc chuẩn của Online Boutique công khai trước năm 2024.
- **Kiểm soát tính thời điểm:** Không đưa tài liệu xuất bản sau mốc thời gian sự cố hoặc qrels vào corpus.

### Phạm vi và Quy trình gán nhãn (Annotation Scope & Protocols)
- **Tập Core:** 56 incidents gồm 20 train (đại diện 18 families), 18 dev, 18 test.
- **Quy chuẩn chấm đôi:** Planned human process (plan 06). Current on-disk qrels are `llm_lexical_proxy`, not two human reviewers.
- **Thang điểm Relevance:** 0 (không liên quan), 1 (liên quan gián tiếp), 2 (hỗ trợ trực tiếp / nguyên nhân gốc rễ).
- **Tập mở rộng:** 34 train incidents còn lại không có human qrels core.

---

## 2. Model Card

### Định danh mô hình (Model Identity)
- **Bộ mã hóa Truy hồi Dày đặc (Dense Retriever):**
  - Mô hình: `intfloat/e5-small-v2`
  - Cơ chế biểu diễn: Bi-encoder, mean pooling, L2-normalization, cosine similarity.
  - Tiền tố truy vấn quy định: `query: ` cho truy vấn incident; `passage: ` cho tài liệu tri thức.
- **Bộ hợp nhất Thứ hạng (Rank Fusion):**
  - Thuật toán: Reciprocal Rank Fusion (RRF).
  - Tham số: `rrf_constant = 60`, `candidate_depth = 50` mỗi nhánh (lexical BM25 và dense E5).
- **Mô hình Sinh có Dẫn chứng (Generator):**
  - Kiến trúc: Khung tích hợp adapter LLM hỗ trợ kiểm soát ngân sách context (observations ≤ 2.048 tokens, knowledge ≤ 4.096 tokens, generation output ≤ 768 tokens).
  - Nhiệt độ giải mã: `temperature = 0.0` (deterministic decoding).

### Điều kiện Sinh thực nghiệm (Generation Conditions)
1. **G0 (No-RAG Baseline):** Chỉ nhận common observation bundle, không có context tài liệu ngoài.
2. **GB (BM25 + Generator):** Nhận top-k chunks từ bộ truy hồi từ khóa BM25.
3. **GD (Dense + Generator):** Nhận top-k chunks từ bộ truy hồi ngữ nghĩa E5-small-v2.
4. **GH (Hybrid RRF + Generator):** Nhận top-k chunks hợp nhất từ BM25 và E5-small-v2.

---

## 3. Quyền hạn sử dụng và Giới hạn đã biết (Allowed Use & Known Limitations)

### Quyền hạn và Đạo đức (Allowed Use & Ethics)
- Dữ liệu và mô hình chỉ phục vụ mục đích nghiên cứu học thuật trong khuôn khổ môn học CS221.
- Không tự động thực thi các hành động can thiệp hệ thống (remediation commands, restart, delete) trong môi trường production.
- Không tiết lộ private gold labels hoặc root-cause mappings trong các giao diện người dùng live / demo.

### Giới hạn kỹ thuật (Known Limitations)
1. **Quy mô cụm kiểm thử nhỏ:** Tập test có 18 incidents nhưng chỉ thuộc 6 service×fault families độc lập. Do đó, các kết luận khoa học phải hạch toán sự tương quan giữa các lần lặp (repetitions) cùng cụm và báo cáo phân bố phương sai theo family.
2. **Tính bất biến của API bên ngoài:** Các API cloud LLM có thể thay đổi trọng số ngầm theo thời gian mà không thay đổi định danh model string. Tính tái lập tuyệt đối (exact bit-reproducibility) chỉ được đảm bảo qua cơ chế replay cache đã băm SHA256.
3. **Bản chất của nhãn Ground Truth:** Nhãn dịch vụ bị lỗi (`root_cause_service`) phản ánh mục tiêu tiêm lỗi nhân tạo của benchmark RCAEval, chưa đại diện cho toàn bộ chuỗi nhân quả phức tạp trong các hệ thống phân tán thực tế quy mô lớn.
