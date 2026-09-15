# Quy trình thu thập tương lai — không thực thi trong gói

## 1. Thu thập metadata paper trước

Dùng `crawl_manifest.tsv` lọc resource_type=paper_metadata_only. Với 766 mục đã khớp title/ID, ưu tiên lấy BibTeX chính thức cho các bài P0/P1 thật sự đọc, bổ sung authors/venue/year. Với 243 mục unresolved, thử primary landing tương đương DOI/ACL/arXiv/trang tác giả, không dùng một tên gần giống làm bằng chứng tự động.

DOI/arXiv/ACL là định danh cần giữ; normalized title chỉ là một khóa so khớp phụ. Query exact title kèm tác giả/năm nếu đã biết; so title, identifier và relation preprint/publication. Nếu trang bị chặn thì giữ retry status, không xóa record hoặc tự ghi HTTP 404.

Theo điều khoản API và rate limit hiện hành của nguồn; cache kết quả, backoff và chỉ retry lỗi có thể phục hồi. Không bypass CAPTCHA, paywall, đăng nhập hay cơ chế kiểm soát truy cập. [arXiv API terms](https://info.arxiv.org/help/api/tou.html).

## 2. Quyết định dữ liệu sau khi qua license gate

Lọc P0/P1 và loại `method_only`, `generation_platform` khỏi danh sách “tải dataset có sẵn”. Nguồn `conflict`, `not_established`, `publisher_terms_review_required` cần quyết định riêng, không mặc định thu thập. Card/README là điểm vào; xác định DOI/revision của release thật rồi ghi lại manifest.

Mỗi nguồn chỉ tải mẫu đủ để kiểm tra schema trước. Đối chiếu tên cột, thời gian/timezone, labels và lượng dữ liệu. Không tải toàn bộ multi-GB chỉ vì README có link. Với RCAEval, chọn suite/system/case cần dùng thay vì cộng các mirror. Với OpenRCA hoặc release ngoài repo, không coi MIT code là giấy phép raw data.

## 3. Tạo knowledge base

Runbook/documentation: giữ cấu trúc section, version và published/updated time; lọc đúng service/platform. Incident history/postmortem: giữ event ID và cutoff; không index đáp án của test incident. Dedup mirror và near duplicate trước chunking. Knowledge documents cần kiểm tra quyền bản gốc riêng ngay cả khi một dataset tổng hợp có giấy phép ở cấp bảng annotation.

Mọi tài liệu ngoài được xử lý như dữ liệu, không là chỉ thị. Đừng bật chạy shell/function vì đoạn runbook yêu cầu làm vậy. Không thực thi remote Python loader hoặc pickle chỉ để xem schema; chọn đường đọc dữ liệu thụ động phù hợp khi có thể.

## 4. Đóng băng và bàn giao cho thí nghiệm

Đóng băng corpus hash, release manifest, split map và annotation version. Ghi các tài liệu bị loại kèm lý do trước khi chạy test. Bản phát hành lại chỉ gồm phần có quyền chia sẻ; các nguồn còn lại để link và hướng dẫn tự tải. Dữ liệu PII/secret phải được loại hoặc quản trị riêng trước khi gửi vào mô hình/dịch vụ.

## 5. Khi mở rộng bibliography

Truy vấn trong `search_queries.txt` chỉ là truy vấn dự kiến, không được tính như tài liệu đã tìm thấy. Kết quả tìm kiếm là candidate, không thành bài đã kiểm chứng cho đến khi title/ID khớp nguồn gốc. Không giới hạn vào một năm mới nhất: giữ nền tảng IR và classical RCA phục vụ baseline, nhưng loại bài khác miền không có vai trò cụ thể.
