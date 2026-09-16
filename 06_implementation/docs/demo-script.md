# Kịch Bản Thuyết Trình Demo Offline Kiểm Bằng Chứng (5–7 Phút)

**Đề tài:** Đánh giá độ tin cậy và căn cứ bằng chứng của mô hình RAG trong chẩn đoán sự cố AIOps  
**Thời lượng mục tiêu:** 5 đến 7 phút  
**Chế độ trình bày:** Hoàn toàn Offline (Replay / Fixture) trên máy trạm cục bộ  

---

## 1. Tuyên bố giới hạn và nguyên tắc nghiên cứu (Disclaimers - 30 giây)

> "Kính thưa Hội đồng và Thầy Cô, trước khi đi vào các ca cụ thể, nhóm xin khẳng định 4 nguyên tắc phạm vi của buổi demo:
> 1. **Mục đích của Demo:** Minh họa cơ chế kiểm chứng liên kết bằng chứng: đi từ triệu chứng viễn trắc (incident observations) → đoạn tri thức thực sự được gửi vào prompt (`actual_context_text`) → các tuyên bố chẩn đoán (`claims`) của mô hình.
> 2. **Không đại diện cho tổng thể thống kê:** 4 ca được chọn trình diễn ở đây là các trường hợp điển hình nhằm kiểm tra các khía cạnh khác nhau của hệ thống; kết luận khoa học định lượng (Passage nDCG@5, Precision/Recall, Citation Groundedness) phải đối chiếu từ báo cáo thống kê chính thức (`08.results`), không tự suy từ 4 ca demo này.
> 3. **Phân định rõ nguồn dữ liệu:** Do hệ thống hiện đang trong quá trình chuẩn bị kết quả mô hình cuối, các ca demo hôm nay được gắn nhãn minh bạch là **[DỮ LIỆU MÔ PHỎNG (FIXTURE)]** với tiền tố `fixture:`. Tuyệt đối không giả mạo số liệu nghiên cứu.
> 4. **Giới hạn phạm vi bài toán:** Đề tài giới hạn trên môi trường thực nghiệm mô phỏng lỗi (fault injection) với 6 họ microservices (Online Boutique); nghiên cứu không đưa ra khẳng định suy diễn nhân quả tổng quát (causal chain) hay giảm thiểu thời gian MTTR thực tế trong sản xuất."

---

## 2. Diễn tiến kịch bản 5–7 phút

### Phút 1:00 – Ca 1: Ca thành công tiêu biểu (`fixture:case_01_success`)
- **Hành động của người trình bày:**
  - Chọn case `fixture:case_01_success` trên thanh điều hướng.
  - Chỉ vào **Cột trái**: Chỉ ra sự cố `inc_0f782051d78bc07a` trên service `redis` với socket latency tăng vọt lên p90 và disk IO bất thường.
  - Chỉ vào **Cột giữa**: Chỉ ra Rank 1 là trích đoạn manifest Kubernetes của Redis (`KBH-D057-0ad6299a6f1d`), hiển thị cấu hình tài nguyên `limits: memory 256Mi` và volume `redis-data`.
  - Chỉ vào **Cột phải**: Click vào trích dẫn `[know_redis_manifest_01]` trong Claim 1.
  - **Điểm nhấn trực quan:** Cột giữa tự động highlight đoạn text Kubernetes manifest chính xác mà generator đã nhận được.
- **Lời thuyết minh:**
  > "Ở điều kiện Hybrid RAG (GH), hệ thống truy xuất được cấu hình cụ thể của service Redis. Người đánh giá có thể click trực tiếp vào từng citation của claim để kiểm tra đoạn văn bản chính xác với source revision và codepoint offsets. Mô hình kết luận nguyên nhân với nhãn `confidence: high` dựa trên bằng chứng có thể kiểm chứng độc lập."

### Phút 2:30 – Ca 2: Chẩn đoán yếu do hạn chế truy xuất (`fixture:case_02_weak_diagnosis`)
- **Hành động của người trình bày:**
  - Chọn case `fixture:case_02_weak_diagnosis`.
  - Chỉ vào **Cột giữa**: Lưu ý rằng với điều kiện BM25 đơn thuần (GB), tài liệu lấy về chỉ là mô tả chung về emailservice, không có thông số hàng đợi (spool queue/thread pool).
  - Chỉ vào **Cột phải**: Mô hình chỉ đưa ra nghi vấn (`cpu_spike_suspect`) và hạ nhãn xuống `confidence: low`.
- **Lời thuyết minh:**
  > "Ở Ca 2, chúng tôi kiểm tra khả năng nhận thức giới hạn của mô hình khi truy xuất chỉ trả về tài liệu chung chung. Thay vì tự bịa ra thông số cấu hình, mô hình gắn cờ `confidence: low`, đồng thời liệt kê rõ thông tin còn thiếu (`missing_information`) là cấu hình thread pool và đề xuất kiểm tra log hàng đợi spool trong `next_checks`."

### Phút 4:00 – Ca 3: Từ chối chẩn đoán khi thiếu bằng chứng (`fixture:case_03_missing_evidence`)
- **Hành động của người trình bày:**
  - Chọn case `fixture:case_03_missing_evidence`.
  - Chỉ vào **Cột giữa**: Hoàn toàn trống vì đây là điều kiện No-RAG (G0).
  - Chỉ vào **Cột phải**: Cờ `abstain: true` được bật màu đỏ/cam nổi bật, danh sách nguyên nhân đề xuất là rỗng.
- **Lời thuyết minh:**
  > "Trong AIOps, 'biết rằng mình không biết' là tiêu chuẩn an toàn tối quan trọng. Ở Ca 3, khi không được cung cấp tài liệu kiến trúc, hệ thống kích hoạt cơ chế `abstain`, chủ động từ chối chẩn đoán sai lệch và hướng dẫn kỹ sư những tài liệu cần nạp thêm trước khi phân tích tiếp."

### Phút 5:00 – Ca 4: Bắt lỗi trích dẫn giả mạo (`fixture:case_04_invalid_citation`)
- **Hành động của người trình bày:**
  - Chọn case `fixture:case_04_invalid_citation`.
  - Chỉ vào màn hình: Giao diện hiển thị badge màu đỏ `[LỖI VALIDATOR: INVALID_CITATION]`.
  - Hiển thị raw response của mô hình chứa citation `hallucinated_evidence_external_99` (một URL hoặc ID không có trong context đã gửi).
- **Lời thuyết minh:**
  > "Ca 4 mô phỏng trường hợp mô hình sinh ra trích dẫn ảo (hallucinated citation) hoặc trích dẫn đường link bên ngoài. Lớp Validator độc lập của chúng tôi phát hiện `hallucinated_evidence_external_99` không tồn tại trong `actual_context_ids`, lập tức đánh dấu lỗi `invalid_citation`, chặn đưa claim không căn cứ vào báo cáo vận hành."

### Phút 6:00 – Ca 5: So sánh đối chứng BM25 vs Hybrid (`fixture:case_05_compare_gb_gh`)
- **Hành động của người trình bày:**
  - Chọn case `fixture:case_05_compare_gb_gh` và bật chế độ Compare View.
  - Hai cột kết quả GB và GH hiển thị song song cho cùng incident `inc_0f782051d78bc07a`.
- **Lời thuyết minh:**
  > "Để trả lời câu hỏi nghiên cứu RQ chính: liệu Hybrid RAG có tốt hơn baseline đơn lẻ hay không, tính năng Compare View cho phép đặt song song cùng một incident viễn trắc với cùng hash. Ta thấy rõ ràng GH đưa tài liệu manifest chứa volume mount vào Rank 1, giúp chẩn đoán rõ hơn hẳn tài liệu tổng quan của GB."

### Phút 6:45 – Tổng kết và chuyển giao (Handoff - 15 giây)
> "Tóm lại, ứng dụng demo offline chứng minh tính khả kiểm chứng (auditability) hoàn chỉnh của kiến trúc: mọi khẳng định đều truy nguyên được về từng byte dữ liệu gốc, hoạt động 100% offline và bảo vệ an toàn trước hiện tượng hallucination. Xin cảm ơn Thầy Cô và mời Hội đồng đặt câu hỏi."

---

## 3. Câu hỏi và câu trả lời dự kiến (Q&A Defense)

**Q1: Làm sao tôi biết được văn bản hiển thị ở giữa đúng là cái mô hình đã nhìn thấy chứ không phải lấy lại từ file gốc dài ngoằng?**  
*Trả lời:* Giao diện demo sử dụng trường `actual_context_text` và danh sách `actual_context_ids` được trích xuất trực tiếp từ bản ghi `RunRecord` lúc chạy generator. Mã băm `actual_context_hash` được kiểm tra khớp với manifest. Văn bản gốc trong corpus registry chỉ được mở khi người dùng chủ động chọn 'Xem tài liệu gốc'.

**Q2: Nếu mất mạng hoặc hội đồng yêu cầu tắt wifi khi bảo vệ thì demo có chạy được không?**  
*Trả lời:* Hoàn toàn bình thường. Ứng dụng chạy trên Python web server tích hợp lắng nghe tại `127.0.0.1`, toàn bộ dữ liệu đọc từ ổ đĩa cục bộ, không gửi bất kỳ request nào ra ngoài.

**Q3: Tại sao trên màn hình có chữ 'DỮ LIỆU MÔ PHỎNG (FIXTURE)'?**  
*Trả lời:* Đây là nguyên tắc liêm chính học thuật bắt buộc trong Hợp đồng nghiên cứu của đề tài (Contract 09). Do các mẻ chạy mô hình cuối cùng (Final runs của Phase 08) chưa hoàn thành, nhóm dùng fixture có cấu trúc chuẩn để dựng và kiểm thử UI trước. Khi có `08.results`, ta chỉ cần cập nhật `configs/demo-cases.yaml` sang các file chạy thật mà không phải sửa đổi mã nguồn app.
