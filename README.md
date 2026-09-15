# CS221 · AIOps / RCA / Hybrid RAG — Research Pack

**Nguyễn Văn Nam · MSSV 24521120**  
**Ngày rà soát nguồn:** 12/09/2026  
**Trạng thái:** tài liệu nghiên cứu và kế hoạch, chưa thu thập dataset hay chạy thí nghiệm.

## Đọc trước

Gói gồm **1.009 mục tài liệu sau khử trùng**, **102 đăng ký nguồn/tập con/tài nguyên dữ liệu**, kế hoạch đồ án và nhật ký kiểm tra. Chỉ có Markdown, JSON/JSONL, TSV, TXT và BibTeX tối thiểu; không có PDF, model, dữ liệu gốc hoặc crawler.

**1.009 không có nghĩa 1.009 bài đã được xác minh đầy đủ.** Có 766 mục được đối chiếu **tiêu đề và định danh** trên nguồn gốc; 35 mục có PDF đọc được nhưng chưa xác nhận tiêu đề; 208 mục bị chặn/chưa đọc được qua công cụ. Tất cả mục đều đã có lần thử kiểm tra link chuẩn hóa. Tác giả, venue, năm xuất bản và tình trạng phản biện **chưa được kiểm chứng đồng loạt**, nên để trống thay vì suy đoán. Bộ 243 mục chưa xác nhận được tách riêng trong `01_papers/unresolved.tsv`.

| Chỉ tiêu | Số lượng / phạm vi |
|---|---:|
| Bản ghi đầu vào cũ | 858 |
| Bản ghi bổ sung | 163 |
| Tổng trước xử lý | 1.021 |
| Bản ghi gộp trùng bổ sung | 9 |
| Nhóm loại vì ngoài phạm vi | 3 |
| Danh mục còn lại | 1.009 |
| Tiêu đề + định danh đã xác nhận | 766 |
| PDF đọc được, tiêu đề còn chờ | 35 |
| Bị chặn/chưa đọc được | 208 |
| Nguồn dữ liệu/tài nguyên cấp đầu | 64 |
| Tập con hoặc phiên bản ghi riêng | 38 |
| Tổng đăng ký trong catalog dữ liệu | 102 |

**Không phải 102 dataset độc lập.** Mục cha, mục con, bản dịch, bản xử lý lại, benchmark sinh dữ liệu, code phương pháp và trang để cào được ghi riêng bằng `resource_type`, `parent_id`, `family`, `lineage_notes`. Đây là catalog có kiểm soát trạng thái, không phải cam kết rằng mọi nguồn đều có thể tải và tái phân phối ngay.

## Bắt đầu từ đâu?

Đọc [đề cương](00_plan/project_proposal.md), sau đó [shortlist dữ liệu](02_datasets/shortlist.md) và [kế hoạch đánh giá](00_plan/experiments_and_evaluation.md). Để chọn tài liệu đọc, mở [50 tài liệu ưu tiên](01_papers/priority_reading.md). Các ghi chú ưu tiên là câu hỏi cần rút ra khi đọc, không giả làm bản tóm tắt toàn văn đã hoàn tất.

## Cấu trúc

| Đường dẫn | Công dụng |
|---|---|
| `00_plan/` | Đề cương, tổng hợp hướng nghiên cứu, thí nghiệm, annotation, timeline |
| `01_papers/catalog.tsv` | Lọc/tìm tên bài, chủ đề, trạng thái và nguồn metadata |
| `01_papers/catalog.jsonl` | Một bản ghi đầy đủ mỗi dòng, thuận tiện xử lý riêng |
| `01_papers/confirmed_primary.jsonl` | Chỉ 766 mục xác nhận được tiêu đề/định danh |
| `01_papers/unresolved.tsv` | 243 mục cần đối chiếu tiếp; không bị giấu trong tổng số |
| `01_papers/topics/` | Danh mục chia 9 nhóm chủ đề |
| `01_papers/references_minimal.bib` | Import khung tài liệu; chưa phải BibTeX sẵn nộp |
| `02_datasets/catalog.tsv` | License dữ liệu/code, phạm vi xác nhận, trạng thái truy cập |
| `02_datasets/dataset_cards.md` | Mục lục 102 thẻ nguồn, mỗi thẻ có link và lưu ý |
| `03_collection_plan/` | Manifest thu thập tương lai, schema và truy vấn tìm tài liệu |
| `04_audit/` | Nhật ký kiểm chứng, mapping khử trùng, khác biệt tiêu đề, giới hạn |
| `MANIFEST_SHA256.txt` | Checksum các file trong gói |

## Phạm vi tài liệu

Theo nhãn sàng lọc, 363 mục gắn với AIOps/log/observability; 616 mục là phương pháp IR/RAG/QA; 30 mục là phương pháp lân cận để cân nhắc chuyển giao. Nhãn này dựa trên tiêu đề và taxonomy nguồn phát hiện, không phải phân loại sau khi đọc trọn mọi bài. Không có tuyên bố “1.009 bài trực tiếp giải quyết đúng RCA bằng RAG”.

Kho tài liệu nghiên cứu **không phải knowledge base mặc định của hệ thống RCA**. Knowledge base vận hành phải là runbook, tài liệu kỹ thuật và sự cố lịch sử phù hợp hệ thống, phiên bản và thời điểm; xem [tổng hợp nghiên cứu](00_plan/literature_synthesis.md).

## Giới hạn cần giữ khi sử dụng

HTTP thành công không chứng minh link đúng bài; lỗi công cụ không chứng minh link chết. “Trang công khai” không đồng nghĩa “dữ liệu có license mở”. Mục có xung đột license được giữ để thông tin đầy đủ, không được mặc nhiên bật cho crawler. Không có kết quả benchmark, số đo chất lượng hay tiết kiệm thời gian nào được tạo trong gói này.

Đây là đề xuất phạm vi môn học, **không phải đề cương hay tiêu chí chấm chính thức của UIT**. Trước khi nộp, đối chiếu yêu cầu giảng viên và bổ sung BibTeX chính thức cho các bài thực sự được trích dẫn.
