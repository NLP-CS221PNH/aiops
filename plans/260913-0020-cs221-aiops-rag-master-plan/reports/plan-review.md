# Rà soát master plan

## Kết quả

Review ngày 13/09/2026 đối chiếu master, 10 phase và hiện trạng research pack. Ba lượt phản biện độc lập tập trung vào dữ liệu/annotation, phương pháp thí nghiệm và phạm vi/tài nguyên. Các điểm trùng được gộp; bản cuối đã xử lý các mâu thuẫn dưới đây. Đây là kiểm kế hoạch, không phải kiểm thực nghiệm đã chạy.

## Các điều chỉnh đã áp dụng

| Vấn đề | File liên quan | Điều chỉnh |
|---|---|---|
| Rerank tùy chọn nhưng gate bắt đủ mọi nhánh | Master, phase 04–08 | 3 IR/4 generation bắt buộc; thêm rerank thành 4/5; 72 hoặc 90 test outputs |
| Generation quá muộn cho bảng dev tuần 4 | Phase 07, 09 | 07A xây/pilot tuần 3–5, final tuần 6; demo có khung sớm và nội dung cuối tuần 7 |
| Vòng chờ representation/pool/qrels | Phase 04–08 | Mốc 04A/05A/06A/07A; B+C tạo F1, 06B tạo F2, scoring chờ F2 |
| Top-k gate ngầm yêu cầu chấm hết depth 50 | Phase 06, 08 | Top-5 primary/top-10 MRR; Recall20/50 pooled diagnostic và judged coverage |
| Primary metric chưa chọn document/passage | Master, phase 05/08, research | Passage nDCG@5; document secondary collapse theo thứ hạng đầu và qrel riêng |
| Chưa xác định human output review | Master, phase 08 | Review tất cả 72–90, double thêm sáu incident đủ cấu hình chọn trước F1 |
| Alias model giữ nguyên có thể replay cache cũ | Phase 07/08 | Cache namespace theo cohort/provider epoch; force-fresh cho đợt mới |
| Giảm ca mâu thuẫn core56/test18 | Master | Giữ core; cắt 34 train mở rộng và ablation trước; thay test là protocol amendment riêng |
| Metadata family có thể mã hóa nhãn | Phase 02/04 | Inference index không family/split; metadata ấy ở evaluator riêng |

## Tính nhất quán và phép tính

- Tổng effort: 224 giờ cố định +84–150 giờ annotation =308–374; dự phòng 20% làm tròn 370–449.
- Nhóm 3 người/8 tuần: trung bình 15,4–18,7 giờ/người/tuần, cần xác nhận năng lực thực.
- Core56=20train+18dev+18test; 34train chưa có qrels không biến thành negative.
- Test18=6family×3repetitions; không nhân cỡ mẫu bằng logs/claims/seeds.
- 18×4/5=72/90 test responses. Review thêm sáu ca×4/5=24/30 lượt chấm thứ hai.
- Ví dụ API 280×7.000 input và 280×768 output tại giá peak chưa cache: $0,846048; là dự toán, chưa tiêu tiền.

## Giới hạn kiểm tra

Đã kiểm cấu trúc bằng AgentKit và kiểm các liên kết tệp cục bộ trong tài liệu. Các đường dẫn ghi Create/tạo mới là sản phẩm tương lai; không báo tồn tại. Plan phases giữ pending. Bộ dữ liệu nguồn/manifest nghiên cứu không bị sửa; chưa tải weights, gọi API mô hình hoặc chấm dữ liệu thay người.

CLI đã tạo đúng thư mục và phase; chỉ mục toàn cục không ghi được do quyền thư mục ngoài workspace. Các Markdown là nguồn kế hoạch đầy đủ, không phụ thuộc chỉ mục đó. Workspace không là Git repository nên không có worktree pointer để kích hoạt. Không cần thay quyền hoặc cấu hình máy để đọc và dùng kế hoạch.

## Việc mở có chủ đích

Rubric/hạn nộp, quyền API/local model, mức giờ thực tế, ngân sách và ngôn ngữ output cần chốt trong phase 01. Applicability, evidence coverage và vận tốc annotation cần pilot. Những việc này có đầu việc/gate rõ; không được hiểu là đã được xác minh.

## Kiểm nhất quán cuối

Đã đọc lại master và đủ 10 phase sau các sửa đổi; 9 nhóm quyết định trong bảng trên đã được đối chiếu. Không còn mâu thuẫn chưa xử lý trong phạm vi review. Kiểm artifact: 14 Markdown, 10 phase, 44 liên kết tệp tồn tại, không còn placeholder và tất cả phase pending; AgentKit validate PASS. Kết quả máy đọc tại `artifact-validation.json`. Chưa nghiệm thu các gates triển khai/human annotation.
