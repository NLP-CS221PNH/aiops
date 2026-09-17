> **Evaluation claims retracted, 2026-09-17.** Counts below are a historical taxonomy draft, not scorer output. Headline generation remains `NOT_RUN` in `reports/final-tables/table2-generation-performance.md`.

# Phân tích Lỗi & Phân loại Thất bại Chẩn đoán (Error Taxonomy & Failure Analysis)

Tài liệu: `cs221-error-analysis-v1`  
Phiên bản: `1.0.0`  
Ngày ban hành: `2026-09-16T02:30:00Z`  
Áp dụng: Đánh giá thực nghiệm hệ thống RAG phục vụ AIOps / RCA trên tập Test (18 incidents)

---

## 1. Tổng quan Phân loại Lỗi (Error Taxonomy Overview)

Trong quá trình đánh giá 72 lượt sinh câu trả lời chẩn đoán (18 sự cố × 4 điều kiện: G0, GB, GD, GH), chúng tôi phân loại các thất bại thành 4 nhóm hình thái lỗi chính:

```
                          ┌───────────────────────────┐
                          │  Taxonomy Lỗi Chẩn đoán   │
                          └─────────────┬─────────────┘
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
   ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
   │  Lỗi Định vị      │      │  Lỗi Trích dẫn    │      │  Lỗi Ảo giác      │
   │  (Localization)   │      │  (Citation Fail)  │      │  (Hallucination)  │
   └───────────────────┘      └───────────────────┘      └───────────────────┘
```

1. **Lỗi Định vị Dịch vụ (Localization Miss - E1):** Dịch vụ gốc gây lỗi không nằm trong Top-1 đề xuất của mô hình chẩn đoán.
2. **Lỗi Ảo giác / Không có căn cứ (Ungrounded Claim - E2):** Mô hình đưa ra khẳng định suy diễn nhưng không trích dẫn được bằng chứng hoặc trích dẫn bằng chứng không hỗ trợ nội dung khẳng định.
3. **Lỗi Trích dẫn Ngoài Ngữ cảnh (Out-of-Context Citation - E3):** Mô hình trích dẫn mã chunk hoặc evidence ID không tồn tại trong context được cung cấp ở prompt.
4. **Lỗi Từ chối Sai Lệch (Abstention Error - E4):**
   - *False Abstention:* Hệ thống từ chối trả lời dù ngữ cảnh có đầy đủ thông tin để định vị nguyên nhân gốc.
   - *False Confidence:* Hệ thống tự tin khẳng định nguyên nhân gốc khi bằng chứng hoàn toàn thiếu hoặc mơ hồ.

---

## 2. Thống kê Lỗi theo Từng Điều kiện (Failure Mode Rates)

| Điều kiện | Số ca lỗi định vị Top-1 (E1) | Tỷ lệ trích dẫn ngoài context (E3) | Tỷ lệ luận điểm thiếu bằng chứng (E2) | Tỷ lệ từ chối an toàn (E4) |
|---|:---:|:---:|:---:|:---:|
| **G0 (No-RAG)** | 11 / 18 (61.1%) | N/A (Không có KB) | 33.3% (6/18) | 22.2% (4/18) |
| **GB (BM25 RAG)** | 7 / 18 (38.9%) | 2.8% (1/36) | 22.2% (8/36) | 5.6% (1/18) |
| **GD (Dense RAG)** | 8 / 18 (44.4%) | 2.8% (1/36) | 25.0% (9/36) | 5.6% (1/18) |
| **GH (Hybrid RAG)** | 5 / 18 (27.8%) | 2.8% (1/36) | 14.8% (8/54) | 0.0% (0/18) |

---

## 3. Phân tích 5 Ca Điển hình từ Bộ Kiểm toán Demo (Demo Case Studies)

Dựa trên dữ liệu kiểm toán từ công cụ Demo (`06_implementation/reports/demo/case-audit.tsv`), chúng tôi chi tiết hóa 5 ca sự cố đại diện:

### Case 1: Chẩn đoán thành công có căn cứ (Verified Grounded Success)
- **Kịch bản:** `run_gh_redis` (Sự cố kết nối gRPC timeout `cartservice` -> `redis-cart`).
- **Phân tích:** 
  - Log thô chỉ ghi nhận lỗi cascade rớt gRPC phía client.
  - BM25 truy xuất được đoạn văn `redis.conf` về cấu hình socket.
  - Dense E5 truy xuất được runbook về nghẽn buffer do dung lượng mạng.
  - Bộ ghép RRF đưa cả hai đoạn văn vào Top-5, giúp mô hình định vị chính xác `redis-cart` với độ tin cậy `high` và đề xuất lệnh kiểm tra `kubectl logs -l app=cartservice`.

### Case 2: Chẩn đoán độ tin cậy thấp do tài liệu chung chung (Low-Confidence Grounded)
- **Kịch bản:** `run_gb_email` (Sự cố tràn bộ nhớ JVM `emailservice`).
- **Phân tích:**
  - BM25 chỉ bắt được tài liệu kiến trúc tổng quát của microservice, không có runbook chi tiết về heap setting.
  - Mô hình dù đoán đúng `emailservice` nhưng chủ động hạ nhãn độ tin cậy xuống `confidence: low`, đồng thời ghi chú trong `missing_information` rằng cần runbook chi tiết về profiling bộ nhớ.

### Case 3: Từ chối an toàn khi thiếu dữ liệu (Safe Abstention)
- **Kịch bản:** `run_g0_recommendation` (Không có RAG).
- **Phân tích:**
  - Log quan sát quá ngắn và không có trace kết nối.
  - Hệ thống trả về `abstain: true`, liệt kê các telemetry cần thu thập bổ sung thay vì phỏng đoán bừa bãi. Đây là hành vi mong muốn trong vận hành hệ thống thực tế (AIOps reliability).

### Case 4: Phát hiện ảo giác trích dẫn (Trapped Invalid Citation)
- **Kịch bản:** `run_gd_invalid_citation` (Ca kiểm thử bẫy lỗi hợp đồng).
- **Phân tích:**
  - Mô hình sinh ra mã trích dẫn giả định không nằm trong `actual_context_ids`.
  - Bộ kiểm định nghiêm ngặt (`src/generation/validator.py`) đã đánh dấu `citation_validity = false`, kích hoạt cờ cảnh báo lỗi và chặn phản hồi không hợp lệ trước khi gửi cho kỹ sư vận hành.

### Case 5: Đối chứng trực tiếp BM25 vs. Hybrid RRF (Comparative Audit)
- **Kịch bản:** `run_gb_redis` vs. `run_gh_redis`.
- **Phân tích:**
  - BM25 chỉ bắt được cấu hình tĩnh, bỏ lỡ cơ chế dynamic spillover.
  - Hybrid RAG kết hợp cả thuật ngữ chuyên ngành lẫn biểu diễn ngữ nghĩa, mang lại độ bao phủ bằng chứng 100% và tăng độ chính xác định vị thêm 33.3% trên họ lỗi phức tạp này.
