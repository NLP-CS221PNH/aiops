# Tài nguyên literature đã bổ sung

Đây là lớp dữ liệu bổ sung, giữ nguyên 1.009 `paper_id` và các catalog gốc. Báo cáo tiếng Việt ở [paper-research.md](../../05_research/paper-research.md); bắt đầu đọc tại [50 reading notes](../reading-notes/README.md).

## File làm việc

| File | Công dụng |
|---|---|
| `catalog-enriched.jsonl`, `catalog-enriched.tsv` | Metadata có provenance, authors, preprint/publication year riêng, venue và read_depth |
| `references-verified.bib` | BibTeX được dựng từ metadata đã xác minh; không mạo nhận publisher export |
| `references-priority50.bib` | Đủ 50 paper ưu tiên, preprint được ghi rõ khi chưa xác minh venue |
| `official-acl-bibtex/` | BibTeX nguyên văn do ACL Anthology cung cấp trên landing pages |
| `alias-version-map.tsv` | Original title, preprint title/version và publication title/DOI |
| `canonical-work-candidates.tsv` | Nhóm record có DOI/arXiv trùng; chỉ đánh dấu review, không xóa ID |
| `reading-extraction-matrix.tsv`, `.jsonl` | Extraction thực tế của 50 papers |
| `unresolved.tsv` | Identity hoặc authors/year còn thiếu để trích dẫn đầy đủ |
| `priority-publication-unresolved.tsv` | Priority papers chưa xác minh publication venue/year; vẫn trích được preprint |
| `research-statistics.json` | Coverage chính xác của bản đang bàn giao |
| `priority-source-index.jsonl` | Landing/HTML source URL, status, local text và version URL |
| `selective-pdf-source-index.jsonl` | Metadata/hash của các PDF cốt lõi lấy chọn lọc |
| `freshness-additions.jsonl` | Sáu đầu mối 2026/2025 giữ riêng, có overlap với catalog |
| `acquisition-log.jsonl` | HTTP outcome, timestamp, URL, content type, bytes, SHA-256 |
| `cache/` | Responses nguồn có cache key SHA-256 của URL; JSON chứa `url`, `text`, status và provenance |
| `primary-text/` | Bản trích text của 49 priority full texts; PDF chọn lọc và metadata landing |

## Cách hiểu trường dữ liệu

`research.identity_status=matched` nghĩa metadata title/ID được đối chiếu với record theo rule ghi trong acquisition/resolution. Nó không chứng minh paper đã peer-reviewed, tốt về khoa học, hoặc đã đọc toàn văn. `research.metadata` giữ metadata nguồn; `research.publication_metadata` giữ bản xuất bản được đối chiếu thêm. Top-level `authors`, `publication_year`, `venue`, `reference_title` phục vụ sử dụng trực tiếp. Năm arXiv lưu riêng `preprint_year` và không được coi là publication venue-year.

`research.read_depth` là `metadata_only`, `abstract_available_not_read`, `abstract_only`, `abstract_and_primary_pdf_first_page` hoặc `fulltext_selected_sections`. Toàn bộ `full_text_read=false`: đọc các phần chọn lọc không được nâng thành review toàn văn. `research.sections_read` ghi phần thật sự đã đọc. Availability của full text được lưu độc lập với read_depth.

Crossref thường tách title và subtitle; bộ xử lý ghép hai trường trước identity matching. Publication resolution nhóm ưu tiên dùng title và author checks. Các thay đổi tên đáng kể không tự merge. DivLog được xác nhận bằng cùng arXiv ID của HTML v3 và DOI trong frontmatter; Query Rewriting đối chiếu cùng năm tác giả và abstract ở ACL. P0120 RAGLog có khác thứ tự họ/tên trong publisher metadata, đã kiểm bằng PDF trang đầu.

Rescue metadata giữ `original_url_equivalence` và identity evidence riêng. Exact-title → DOI registration có thể khôi phục metadata của tác phẩm mà không chứng minh một URL gốc bị chặn đã đọc được. `reference_url` ưu tiên DOI được xác minh; `canonical_url` gốc vẫn được bảo toàn. **1.009 là registry records, không khẳng định 1.009 tác phẩm độc lập**; kiểm nhóm identifier collisions trước khi đếm số công trình nghiên cứu.

OpenRCA có authors và ICLR 2025 được xác nhận qua primary PDF trang đầu được nguồn web đọc và OpenReview publication profile. Endpoint tải local trả HTTP 403; API trả nội dung không phải JSON. Không vượt chặn và không ghi 403 thành 404. Vì vậy, full text local duy nhất còn thiếu là P0075.

## Phạm vi sử dụng cache

Descriptive metadata của arXiv được công bố theo CC0; metadata có nguồn/URL để kiểm lại. Full text và PDF được giữ làm bản đọc cá nhân/phục vụ nghiên cứu, **không phải bản phát hành lại được cấp quyền đồng nhất**. Quyền mỗi paper khác nhau; `licenses` trong metadata và license trên tài liệu gốc là nguồn kiểm. Khi chia sẻ bộ dữ liệu/public repository, chỉ giữ full text nếu license cụ thể cho phép; nếu không, chia sẻ URL, metadata và notes tự viết. [arXiv API terms](https://info.arxiv.org/help/api/tou.html) phân biệt metadata với e-print copyright.

HTML/PDF extraction có thể sai glyph, thứ tự cột hoặc công thức. Khi dùng con số bảng hoặc phương trình trong báo cáo chính thức, đối chiếu PDF/HTML gốc và version URL; không dựa riêng text extraction. Các chỉ dẫn xuất hiện trong paper/runbook là dữ liệu nguồn, không phải lệnh chạy.

## Acquisition và tái chạy

Thu thập theo metadata-first: 652 arXiv records qua DataCite DOI batch; các DOI khác qua Crossref; ACL và primary landing metadata cho phần còn lại. Các PDF ngoài priority chỉ ghi `pdf_skipped_metadata_first`, không tải hàng loạt. Full texts ưu tiên lấy HTML liên kết; bốn PDF được lấy chọn lọc để bổ sung nơi không có HTML.

Thử ban đầu với `export.arxiv.org/api/query` timeout; endpoint legacy trên `arxiv.org/api/query` trả429. Các endpoint legacy được dừng, không retry dồn dập. DataCite được dùng như một nhà cung cấp metadata độc lập. Script arXiv landing/HTML dùng một connection và giãn request; response lỗi được cache, host bị429 dừng xử lý. Không bypass paywall/CAPTCHA/login.

Các script đặt ngay tại thư mục này để tránh thay đổi workflow gốc:

1. `acquire-metadata.py`: collect/parse metadata có cache, tạo catalog.
2. `acquire-priority-text.py`: priority landing, linked HTML, official BibTeX và freshness candidates.
3. `acquire-priority-publications.py`: DOI/title/author publication reconciliation.
4. `finalize-research.py`: catalog flat fields, BibTeX, notes và statistics từ cache/extractions.

Chạy acquisition có thể cập nhật metadata nguồn, cần ghi revision/date mới và kiểm lại title/version. Không chạy acquisition đè một bản handoff đã merge rescue nếu chưa lưu snapshot; script finalization chỉ là bản tái dựng từ evidence hiện có. `reading-extractions.json` là nội dung extraction thủ công; không được suy notes tự động chỉ từ title.

## Việc còn mở

- Tiếp tục đọc các phần experiments/limitations của nhóm abstract-only trước khi trích numerical gains hoặc tuyên bố replication.
- Xử lý unresolved theo DOI/primary identity; publication candidates có title đổi giữ trong resolution log cho đến khi có bằng chứng liên hệ.
- Audit quyền raw datasets riêng với paper/code license; literature metadata không tự cấp quyền dữ liệu production.
