---
artifact_id: cs221-scope-literature-v1
status: draft
reader: Codex
verified_at: 2026-09-13T02:05:48Z
human_review_status: pending
---

# Bằng chứng đọc cho ma trận bài lõi

Ma trận chọn 10 bài để phục vụ protocol hiện tại: taxonomy/benchmark/TSG, BM25, dense, RRF, RAG, reranking optional, ARES và ALCE. Đây là ghi nhận đọc của **Codex**. Các cột A/B/C là phân công đề xuất; cả việc đọc và review của người thật đều `pending`. Chưa có chữ ký nhóm, human judgments mới hay kết quả thí nghiệm.

`read_depth=selected_sections` chỉ có nghĩa đã đọc các đoạn primary text ghi trong `read_sections`; không tuyên bố đọc toàn văn. Tệp có tên `fulltext.txt` không phải chứng cứ đã đọc hết. Các lựa chọn trong `method_decision` là liên hệ do Codex đề xuất với accepted plan, không phải phát biểu nguyên văn của tác giả hoặc quyết định đã được nhóm duyệt.

## Nguồn và cách kiểm

- Tám ID `P...` được đối chiếu tiêu đề/identifier với `01_papers/enriched/catalog-enriched.tsv`, reading notes trong `01_papers/enriched/reading-extraction-matrix.tsv`, và **đọc lại primary text thực có trên đĩa**. Đường dẫn trong TSV tính từ gốc research pack. SHA-256 là hash toàn bộ tệp nguồn local, không phải hash đoạn đọc.
- Hai ID `LIT-BM25-2009` và `LIT-RRF-2009` là bổ sung cho triển khai, không tự thêm/sửa catalog gốc. Primary PDF được đọc trực tuyến; `source_local_path=null` và `source_sha256=null` vì chưa lưu bản local. Không dùng việc file thiết kế có citation thay cho việc đọc bài.
- `verified_at` là thời điểm kiểm artifact/ghi nhận đọc lần này (UTC), không khẳng định metadata xuất bản mới nhất. Đối với bản local, SHA-256 và version ở primary text là căn cứ tái đọc; không gộp metadata của các version thành một bản đã đọc.
- Link landing của Now Publishers cho BM25 trả 403 khi mở; đã đọc bản PDF trên trang tác giả tại City University thay thế. DOI in trong PDF là `10.1561/1500000019`. Bản primary PDF ghi Vol.3, No.4 (2009), pp.333–389; ma trận không sao chép volume/pages đang mâu thuẫn ở một số landing metadata.

## Hai primary sources bổ sung

[Robertson và Zaragoza, BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf): đọc các đoạn về saturation, chuẩn hóa độ dài, biến thể và parameter optimization (§3.4.4–3.5.1; đầu §5). Điều rút ra cho protocol là phải ghi implementation cùng tham số và giới hạn việc chọn tham số ở train/dev. Bài không quyết định k1/b tối ưu cho corpus này.

[Cormack, Clarke và Büttcher, Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf): đọc công thức, mô tả pilot/validation và discussion (§1–2). RRF cộng đóng góp theo thứ hạng; tác giả khóa hằng số 60 sau pilot. Cách xử lý passage không có trong danh sách đã cắt và tie-break trong implementation vẫn cần ghi ở protocol; bài không bảo đảm hybrid thắng ở dự án này.

## Những phân biệt cần reviewer giữ

| Nhóm bài | Điều dùng trong protocol | Không suy ra từ việc đã đọc |
|---|---|---|
| P0052, P0757 | Task taxonomy; schema telemetry; nhãn RCA khác passage relevance | 735 ca benchmark là 90 ca local; có runbook qrels sẵn; paper results là project results |
| P0003 | Giữ điều kiện và liên kết giữa các bước TSG | User study Microsoft bảo đảm hiệu quả trên RE2-Online Boutique |
| BM25, P0245, RRF | Ba retrievers trên cùng corpus/query/qrels; tham số khóa trước test | Dense hay hybrid bắt buộc thắng; unjudged tự động bằng 0 |
| P0376, P0325 | Tách retrieval/generation; reranker chỉ là optional có chi phí | Context-prepending là tái lập RAG gốc; reranker tạo evidence ngoài pool |
| P0761, P0826 | Chấm evidence support/coverage, correctness và relevance riêng | LLM judge thay human gold; citation hiện hữu là claim đúng |

Các lựa chọn passage nDCG@5, contrast với single baseline mạnh hơn trên dev, hòa chọn BM25, core 20/18/18 và F1/F2 đến từ accepted plan; không gán chúng thành kết luận của các bài trên. Cấu hình/model cụ thể vẫn cần validation phù hợp ở các kế hoạch sau.

## Bàn giao người thật

Người được giao đọc ghi đoạn đã đọc, một nhận xét task-match và ít nhất một giới hạn; reviewer khác người đọc đối chiếu primary source cùng hash/version. Sau đó mới cập nhật trạng thái người thật, kèm timestamp và record review. Hiện mọi ô `human_read_status` và `human_review_status` đều `pending`.

Điều còn thiếu cho nghiệm thu toàn bộ task 01.2.2: A/B/C xác nhận phân công và thực hiện đọc/review; việc Codex hoàn thành ma trận chưa đáp ứng chữ ký của con người.
