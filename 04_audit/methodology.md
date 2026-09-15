# Phương pháp rà soát và định nghĩa kiểm chứng

## Đầu vào và phép đếm

Đầu vào là 858 bản ghi của lượt trước. Bổ sung 163 bản ghi từ các danh mục nghiên cứu liên quan, rồi thử truy cập trang gốc theo từng URL. Tổng 1.021 hàng được liên kết theo định danh và tiêu đề; 9 hàng gộp thêm và 3 nhóm ngoài phạm vi bị loại, còn 1.009 mục.

Một mục không đồng nghĩa với một PDF, một lượt tìm kiếm hay một version arXiv. `dedup_mapping.tsv` nối mọi hàng gốc đến ID cuối hoặc EXCLUDED; `dedup_merges.tsv` ghi khóa tạo phép gộp. Nhật ký có 1.017 URL chuẩn hóa riêng biệt đã thử, vì một số hàng chia sẻ URL và một work có thể có nhiều đường dẫn.

## Phát hiện tài liệu và nguồn kiểm chứng

Awesome lists và repo survey dùng để phát hiện candidate và gán taxonomy ban đầu. Chúng không tự chứng minh link đúng tiêu đề, hội nghị hay năm. Trường `discovery_sources` ghi nguồn phát hiện, còn `metadata_source_url` ghi nơi ưu tiên đối chiếu. Dùng nguồn sơ cấp như arXiv, ACL Anthology, publisher/conference hoặc trang tác giả.

Link chuẩn hóa chuyển HTTP sang HTTPS, arXiv PDF/abs/DOI/versions sang landing ID, ACL PDF sang landing khi áp dụng. Vì vậy phép kiểm tra là link metadata chuẩn hóa, **không** là chứng nhận rằng nguyên chuỗi URL PDF cũ còn tải được. Không gán HTTP status khi công cụ không trả về mã thực.

## Khử trùng

Các khóa: URL chuẩn hóa; DOI, kể cả đường ACM DOI; ACL ID tương đương DOI 10.18653/v1; normalized title của bản phát hiện và tiêu đề quan sát. Title normalization bỏ khác biệt hoa/thường, dấu và punctuation. Sau gộp, ưu tiên record có primary title confirmation; lưu aliases và mọi URL.

Rà title gần giống giúp phát hiện trường hợp cần xem, không tự gộp tất cả dựa ngưỡng fuzzy. PROP/B-PROP và các phương pháp RAG tên gần nhau có thể là bài khác. Không có kiểm tra đồng loạt bằng authors/venue/citation graph, nên chưa thể bảo đảm loại hết mọi preprint đổi tên sâu hoặc journal extension. Kết quả là **1.009 mục không trùng theo các khóa đã áp dụng**, không là tuyên bố tuyệt đối mọi cặp đều khác sau đọc toàn văn.

## Ba mức trạng thái

| Giá trị | Ý nghĩa | Không được suy ra |
|---|---|---|
| primary_title_identifier_confirmed | Tiêu đề và ID/đường dẫn bài được đối chiếu trên nguồn gốc | Đã đọc full text, đã tái lập, đã kiểm mọi tác giả/venue |
| pdf_readable_title_pending | Công cụ đọc được PDF nhưng đối chiếu tiêu đề chưa được chốt | PDF đó chắc chắn đúng bài |
| blocked_or_unreadable | Trang bị chặn/không đọc được qua công cụ | Link chết, paper không tồn tại, hoặc có thể bypass kiểm soát |

766 mục thuộc mức đầu; 35 mức thứ hai; 208 mức thứ ba. `verification_log.jsonl` giữ outcome, error note và source URL theo từng lần kiểm tra được lưu. Nó **không lưu đầy đủ response body** hay screenshot của mọi trang; do đó không phải bản lưu trữ ngoại tuyến để chứng thực lại độc lập toàn bộ kết quả.

## Metadata không bịa

`authors`, `venue`, `publication_year` để null trong catalog hiện tại vì chưa thu thập/đối chiếu đồng loạt. `arxiv_id_year` được suy cơ học từ ID và gắn tên riêng, không thay publication_year. Mục arXiv có thể là preprint hoặc version tác giả; không suy acceptance chỉ từ nhãn một repo survey.

69 khác biệt normalized-title được ghi trong `metadata_corrections.tsv`. Chúng có thể là đổi tiêu đề giữa versions, cách viết khác, rút gọn, hoặc sai link thật; không gọi toàn bộ 69 trường hợp là paper giả. Ba nhóm ngoài phạm vi được ghi riêng ở `excluded.tsv`, trong đó có link được gắn nhãn SLA/RAG nhưng tiêu đề gốc là SurgRAW về video phẫu thuật.

## Dataset audit

64 nguồn cấp đầu được truy xuất ở mức landing/card/README và điều khoản đọc được; 38 thẻ con kế thừa nguồn bằng chứng của cha. Không giả 38 thẻ này có 38 lần tải binary thành công. Mỗi thẻ ghi license data, license code, evidence URL, access status và scope.

Không tải dataset để kiểm file count/checksum/schema hoặc xác thực gold. Nguồn công khai chỉ là một observation; quyền sử dụng phải dựa đúng điều khoản. Xung đột license và quyền upstream được ghi rõ. Các thẻ platform/method/corpus không được cộng như dataset RCA có sẵn.

## Ranh giới báo cáo

Đây là một curated research inventory kèm kế hoạch, **không phải systematic literature review đã đọc và chấm 1.009 toàn văn**. Không có extraction bảng kết quả, risk-of-bias của từng paper, đánh giá chất lượng peer review, hay chứng nhận một phương pháp tốt nhất. Chọn các paper thực sự trích dẫn trong báo cáo, đọc nguồn gốc và bổ sung metadata chính thức trước khi nộp.
