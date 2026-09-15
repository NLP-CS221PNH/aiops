# Hợp đồng thực hiện nghiên cứu

## Kết quả cần bàn giao

Thực hiện phần nghiên cứu và chuẩn bị dữ liệu của kế hoạch có sẵn: bibliography được bổ sung bằng nguồn gốc; ghi chú đọc có mức bằng chứng; một tập RCAEval RE2–Online Boutique thực tải về và kiểm tra; kho tài liệu có phiên bản, nguồn và giấy phép; bộ hồ sơ để bắt đầu annotation và thí nghiệm.

## Phạm vi và ràng buộc

Lấy `00_plan/project_proposal.md`, `00_plan/experiments_and_evaluation.md`, `00_plan/annotation_and_leakage_policy.md`, `02_datasets/shortlist.md`, `03_collection_plan/collection_workflow.md` làm căn cứ. Danh mục 102 mục là tập lựa chọn, không phải lệnh tải mọi dataset. Ưu tiên hoàn thiện RE2-OB sau khi kiểm mẫu. RE2-TT là nhánh mở rộng; TechQA/MTRAG/ITBench là dự phòng, không trộn nhãn của chúng vào RCA.

Giữ nguyên gói nguồn làm mốc; bổ sung phiên bản nghiên cứu ở thư mục con. Tách observations, labels và knowledge. Không tạo qrels giả, không giả hai người đã chấm, không gọi nhãn injection là causal-path gold. Không suy license raw data từ license code. Không chạy mã dataset hoặc gửi telemetry đến mô hình bên ngoài.

## Công việc ngoài đợt chuẩn bị

Huấn luyện, chạy generator, kết luận benchmark, demo ứng dụng và triển khai hệ thống thuộc giai đoạn thí nghiệm tiếp theo. Việc chuẩn bị công cụ kiểm tra hoặc mẫu cấu hình không được báo thành đã hoàn tất các thí nghiệm này.

## Bằng chứng nghiệm thu

1. Mỗi paper giữ ID ban đầu, metadata mới có nguồn/cache và trạng thái; không lấp trường thiếu bằng suy đoán. Ghi rõ phần đọc toàn văn, đọc đoạn và chỉ metadata.
2. Raw dataset có revision, danh sách tệp, kích thước và SHA-256; kiểm schema trên tệp tải thật; subset chính đầy đủ theo manifest đã chọn hoặc ghi chính xác tệp bị chặn.
3. Observations và labels nằm riêng; ID liên kết hợp lệ; split được ghi là đề xuất/pilot tới khi annotation khóa.
4. Corpus có source URL, license snapshot, commit/revision, text hash; chunk truy ngược được về offsets trong document. Mốc thu thập hôm nay không giả thành mốc có sẵn trước incident lịch sử.
5. Qrels để trạng thái chưa chấm; có rubric, bảng chấm và cách adjudication. Không có metric chất lượng được bịa.
6. Có báo cáo tiếng Việt, bản đồ tài nguyên, hướng dẫn sử dụng và kết quả kiểm tra gói; các điểm chưa hoàn tất được kê riêng có bước xử lý cụ thể.

## Nhật ký tiến độ

- 2026-09-12: Đọc cấu trúc, 5 tài liệu kế hoạch, shortlist, workflow/schema và giới hạn hiện có. Xác nhận chưa có raw dataset. Bắt đầu ba nhánh: paper metadata/reading; dataset acquisition; knowledge/annotation. Phần tích hợp kiểm tra giữ ở nhánh chính.
- 2026-09-13: Hoàn tất thu nhận 90/90 ca RE2-OB (360 tệp), tạo observations và evidence tách nhãn; chuẩn bị corpus lịch sử 74 tài liệu/580 chunks và corpus hiện tại để so sánh. Hoàn tất 1.003 mục BibTeX trong 1.009 ID gốc, 50 reading notes, 49 toàn văn lưu local; 6 bibliography chưa đủ bằng chứng được giữ mở. Bộ annotation và pool BM25 pilot 20 ca/400 ứng viên sẵn sàng để người chấm. Kiểm tra nghiệm thu và checksum cuối được ghi ở `04_audit/` và `MANIFEST_RESEARCH_SHA256.txt`.

## Quy tắc chốt

Chỉ đánh dấu hoàn tất phần chuẩn bị khi các artifact bắt buộc đã được kiểm tra. Những hạng mục cần người chấm hoặc nguồn chưa cho truy cập phải giữ trạng thái thực tế; không thu hẹp kế hoạch hay thay nhãn để làm đẹp kiểm tra.
