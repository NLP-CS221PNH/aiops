# Generation Protocol

## Quyền và Ngân sách (Permissions & Budgets)
- Mô hình mặc định là DeepSeek V4.1 Flash (`deepseek-flash`).
- Chế độ Thinking bị vô hiệu hóa (`extra_body: {thinking: {type: disabled}}`).
- API và Local fallback cần được cấp quyền trong `decision-log.md` trước khi gọi thực tế.
- Ngân sách (Budget): Phân bổ `observations: 2048`, `knowledge: 4096`, `output: 768`.

## Mô hình mối đe dọa (Threat Model)
- **Prompt Injection:** Rủi ro từ observations hoặc knowledge context chứa mã độc hoặc chỉ thị giả mạo yêu cầu mô hình thực thi mã hoặc bỏ qua constraints. Hệ thống không thực thi công cụ hoặc URL, nội dung sinh ra chỉ được xem là dẫn chứng (evidence).
- **Data Leakage:** Đảm bảo không tiêm nhãn root/gold/qrels vào inference request. Cần xóa thông tin định danh private nếu có.

## Tính công bằng (Fairness)
- Cấu hình (decoding, temperature) là cố định và áp dụng đồng đều trên tất cả các điều kiện (G0, GB, GD, GH).
- Điều kiện G0 (No-RAG) sẽ nhận empty knowledge context (chỉ truyền metadata/conditions) mà không độn thêm thông tin.

## Nguồn gốc dữ liệu (Provenance)
- Mọi kết quả từ mô hình phải được lưu trữ kèm theo toàn bộ raw response.
- `bundle_hash`, `prompt_hash`, `config_hash` và actual evidence offsets phải được ghi nhận đầy đủ vào ledger.
- Mỗi claim phải chứa ít nhất một citation trỏ về ID hợp lệ trong phần observations hoặc knowledge context thực tế đã được gửi cho mô hình.
