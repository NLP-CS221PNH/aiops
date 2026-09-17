# Kiểm tra chất lượng gói bàn giao

**Historical snapshot (12/09/2026), not the current public HEAD.** Current publication checks are `scripts/validate-public-artifacts.py` and `04_audit/public-artifact-ledger.tsv`.

Kiểm tra cấu trúc ngày 12/09/2026. Đây là QA file của gói catalogs ban đầu, không là một lượt xác minh web bổ sung và không mô tả repository sau khi thu thập raw/full text.

| Kiểm tra | Kết quả |
|---|---|
| 1.009 paper IDs duy nhất, không trùng title nguyên dạng sau casefold | PASS |
| Mỗi paper có trạng thái, URL và mapping đến nhật ký | PASS |
| 1.021 input rows đều map đến paper ID hoặc EXCLUDED | PASS |
| 1.017 URL chuẩn hóa có bản ghi lần kiểm tra đã lưu | PASS |
| 766 confirmed + 35 PDF pending + 208 blocked = 1.009 | PASS |
| 102 dataset/resource IDs; 64 cấp đầu + 38 con/phiên bản | PASS |
| Mọi dataset card có license/access/evidence fields | PASS |
| 102 thẻ Markdown đều tồn tại, parent ID hợp lệ | PASS |
| Lộ trình có đúng 50 mục đọc ưu tiên | PASS |
| Liên kết Markdown nội bộ có đích tồn tại | PASS |
| Tất cả file là UTF-8 text trong danh sách định dạng cho phép | PASS |
| Không có PDF/raw dataset/model/crawler/script thực thi | PASS |
| Có SHA-256 manifest cho mọi payload file | PASS |

## Ý nghĩa

PASS chỉ xác nhận tính nhất quán và khả năng đọc gói. Nó không nâng 243 paper unresolved thành verified, không giải quyết license conflicts, không kiểm chứng binary dataset và không tạo kết quả benchmark. Xem `limitations.md` và `methodology.md` để hiểu ranh giới.
