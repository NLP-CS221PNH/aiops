# Thư nháp hỏi giảng viên — CHƯA GỬI

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2`.

Người gửi/người nhận/lớp: pending, nhóm điền. Người điều phối đề xuất C, A kiểm payload/nguồn, B kiểm nội dung thí nghiệm. Codex chỉ soạn; communication status=pending, sent_at_utc=null, response_ref=null.

**Tiêu đề đề xuất:** CS221 — xin xác nhận phạm vi và quyền dùng mô hình cho đồ án hỗ trợ phân tích sự cố bằng Hybrid RAG

Kính gửi Thầy/Cô,

Nhóm chúng em dự kiến làm đồ án hỗ trợ phân tích incident offline trên RCAEval RE2–Online Boutique trong tám tuần với ba thành viên. Đóng góp NLP dự kiến gồm biểu diễn log có bảo toàn thực thể, so sánh BM25/dense/hybrid retrieval trên cùng dữ liệu và đánh giá giải thích có dẫn chứng. Chúng em không tự sửa hệ thống hoặc tuyên bố phát hiện đầy đủ chuỗi nhân quả. Nhóm sẽ dùng human qrels để đánh giá retrieval; hiện biểu mẫu chưa có phán quyết người.

Để chốt protocol và tiến độ, nhóm xin xác nhận riêng các mục sau:

1. Rubric chính thức, hạn nộp, định dạng report/demo, yêu cầu thuật toán NLP và mức đóng góp cá nhân là gì? Có yêu cầu tự huấn luyện/fine-tune hoặc giới hạn thư viện/model có sẵn không?
2. Có được sử dụng hosted LLM API (ứng viên theo kế hoạch là DeepSeek) cho các conditions no-RAG/RAG không? Nhóm sẽ cố định cấu hình, lưu usage/output và khai báo nguồn; API chỉ là generator, không làm human ground truth.
3. Nếu được dùng API, loại payload nào được gửi? Nhóm đề xuất chỉ observations/evidence đã khử định danh, không raw telemetry, gold service/fault, injection time, qrels, reference hoặc đường dẫn case chứa nhãn. Quyền model không tự đồng nghĩa quyền gửi dữ liệu; nhóm có thể cung cấp mẫu export để Thầy/Cô xem ở giai đoạn dữ liệu.
4. Nếu API không được phép hoặc chưa có quyết định cuối tuần2, có được dùng model open-weight cục bộ/Kaggle với license phù hợp không? Nhóm sẽ xin xác nhận model/revision cụ thể sau pilot tài nguyên, không coi đây là chấp thuận mặc định.
5. Có được dùng Kaggle/private notebook và chia sẻ derivative dataset/corpus/output giữa nhóm hoặc trong gói nộp không? Những dữ liệu/artifacts nào phải giữ local/private?
6. Yêu cầu khai báo AI/Codex trong viết code, đọc tài liệu, soạn báo cáo và kiểm tra là gì? Nhóm chịu trách nhiệm hiểu/kiểm tra kết quả; không ghi AI reading hoặc AI labels thành công người.
7. Có yêu cầu ngôn ngữ output dùng để chấm/report/demo không? Nhóm muốn cố định một ngôn ngữ output đánh giá để tránh thay đổi nhiệm vụ giữa conditions.
8. Nếu tất cả generators không được phép, nhóm có thể trình amendment thành retrieval/extractive incident assistance, báo RQ3 chưa thực hiện, thay vì giả là thí nghiệm RAG hoàn chỉnh không?

Nhóm tự quyết định trần chi sau khi có quyền phù hợp; mức $10–15 mới là đề xuất nội bộ, chưa có khoản chi được duyệt. Trong lúc chờ, nhóm tiếp tục audit dữ liệu, corpus, retrieval và chuẩn bị annotation theo phạm vi môn học.

Nhóm cảm ơn Thầy/Cô.

[Tên nhóm/thành viên/lớp — pending]

## Cách lưu phản hồi

C lưu từng phản hồi với source_ref và UTC thực, tách API use, API payload, local model, data sharing, rubric/deadline và disclosure thành từng decision. Không đánh confirmed cho toàn bộ khi chỉ một phần được đồng ý. Review mẫu export thuộc plan02; thư này không đính kèm/gửi telemetry. Nhóm quyết ngân sách riêng bằng record có trần số cụ thể. Soạn hoặc mở bản nháp không tính là đã gửi/được phê duyệt.
