# Giới hạn còn lại — không che bằng tổng số

## Bibliography

Mục tiêu khoảng 1.000 tài liệu đã đạt ở cấp discovery registry: 1.009 `paper_id` được giữ nguyên. Con số này không chứng minh 1.009 công trình độc lập sau work-level dedup, không chứng minh peer review, và tuyệt đối không phải số Q1. Metadata chưa đầy đủ đồng đều; record không có hàng trong publication overlay được giữ là unknown thay vì suy đoán.

Publication overlay hiện phân loại các record có Crossref/citation-tag/arXiv evidence và tách conference-journal-series khỏi journal thật. Recount SJR 2024 chỉ đếm hàng có sidecar rank tracked; nó vẫn là audit metadata, không phải đánh giá chất lượng nội dung. Work-level relation audit chỉ bao phủ priority-50. Năm gap G0001–G0005 sống ngoài registry và đã qua collision gate DOI/arXiv, nhưng không làm tăng số catalog.

Nhãn core/method/adjacent được gán để người đọc chọn lọc, không là mức độ liên quan sau review đầy đủ. Một số nguồn là preprint, short paper, tool paper hoặc survey; không khẳng định tất cả là bài conference/journal đã peer review. Phạm vi gồm IR và RAG nền tảng vì đồ án cần baseline, không chỉ các bài giao điểm RCA+RAG.

Dedup không dựa full author/venue/citation graph; các phiên bản đổi tên nhiều hoặc journal extension vẫn cần đối chiếu trước systematic review. P0052 và G0005 được ghi là hai work khác nhau có cùng nhóm tác giả, quan hệ successor. Sidecar lưu excerpt metadata, URL, ngày và checksum; không lưu toàn bộ response body của mỗi nguồn.

## Dữ liệu và quyền

102 mục là nguồn, tập con, phiên bản, framework và corpus ứng viên; không là 102 dataset độc lập và sẵn tải. Trang public/file listing không bảo đảm download binary; những link kho ngoài Drive/Zenodo khác chưa đều được tải hoặc đăng nhập thử.

Giấy phép unknown/conflict được giữ nguyên. Chưa có xác nhận từ tác giả để giải quyết các xung đột; không được dùng ưu tiên P0/P1 như một quyết định pháp lý. Giấy phép repo không tự chuyển sang mọi tài liệu raw/upstream. The 12/09/2026 snapshot had no local raw binaries. HEAD later acquired RCAEval Parquet and knowledge snapshots; those bytes are now archive-private / gitignored. Public processed extracts still do not prove overlap, PII absence, or label quality for every upstream corpus.

## Đồ án

Chưa xem đề cương/tiêu chí chấm chính thức CS221 của lớp người dùng; lịch và phạm vi là đề xuất. Chưa biết tài nguyên máy, nhóm và deadline. Chưa cào data, huấn luyện, embedding/index, benchmark, deploy hay đo latency/cost. Không có kết quả số, kết luận cải thiện hay tiết kiệm MTTR nào được xác lập.

Những giới hạn này không ngăn bắt đầu pilot bằng nguồn có bằng chứng rõ. Chúng xác định đâu là quyết định dựa trên quan sát và đâu là công việc cần thực hiện khi triển khai riêng.
