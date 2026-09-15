# Bắt đầu làm việc với bộ nghiên cứu CS221

Mở [mục lục có tìm kiếm](START-HERE.html) để tra paper, incident và nội dung tài liệu. Đọc [báo cáo tổng hợp](05_research/research-report.md) trước khi dùng dữ liệu làm thí nghiệm.

## Đã có trên máy

| Sản phẩm | Trạng thái thực tế | Mở |
|---|---|---|
| RCAEval RE2–Online Boutique | 90/90 ca; 360 tệp; 922,484,805 bytes; 270 Parquet khớp hash upstream | [Inventory](02_datasets/acquired/inventory.tsv) |
| Observations và evidence | 90 bundles; 1,770 log excerpts; 6,603 metric summaries; 1,260 trace excerpts | [Observations](02_datasets/processed/observations.jsonl) |
| Gold và split | Gold service/fault/injection tách riêng; 30 families; 54/18/18 train/dev/test | [Labels](02_datasets/processed/labels/ground_truth.jsonl) · [Split](02_datasets/processed/split-map.tsv) |
| Kho tri thức chính | 74 tài liệu / 580 chunks, commit trước năm 2024 | [Historical corpus](03_collection_plan/knowledge-corpus-historical/README.md) |
| Snapshot hiện tại để so sánh | 73 tài liệu / 598 chunks; có overlap với bản lịch sử | [Current corpus](03_collection_plan/knowledge-corpus/README.md) |
| Bibliography | 1,009 record giữ ID; 1,005 khớp định danh; 1,003 mục BibTeX; 6 bibliography chưa đủ thông tin | [TSV](01_papers/enriched/catalog-enriched.tsv) · [BibTeX](01_papers/enriched/references-verified.bib) |
| Ghi chú đọc | 50 ghi chú ưu tiên, có mức đọc và hạn chế | [Paper report](05_research/paper-research.md) |
| Annotation | Biểu mẫu cho 90 ca; seed pool BM25 20 train incident / 400 candidates; chưa có phán quyết người | [Kit](03_collection_plan/annotation-kit/README.md) · [Seed pool](05_research/retrieval-preview/README.md) |
| Model/config tham khảo | E5, BGE và reranker có card/config/revision; chưa tải weights hay chạy generator | [Thiết kế](05_research/method-and-experiment-design.md) |
| Kiểm tra artifact | PASS | [Validation](04_audit/research-pack-validation.json) |

## Thứ tự sử dụng

1. Đọc [phân tích dataset](05_research/dataset-research.md) và [thiết kế thí nghiệm](05_research/method-and-experiment-design.md).
2. Mở 20 train incidents trong seed pool, xem observations cùng raw row references khi cần. Duyệt applicability của tài liệu lịch sử đối với deployment.
3. Bổ sung dense/hybrid vào pool, rồi hai người chấm độc lập theo rubric; adjudicate bất đồng. Seed pool BM25 hiện tại chưa là pool đánh giá hoàn chỉnh.
4. Khóa query representation, corpus, split được review, qrels, generator/context và evaluator trước test. Dùng [bảng kết quả trống](05_research/experiment-results-template.tsv).

## Tìm thử bằng chứng trên máy

Từ thư mục gốc, dùng Python 3 để chạy công cụ tra cứu nhẹ, không cần model hoặc mạng:

```powershell
python scripts/preview-retrieval.py --query "Kubernetes pod OOMKilled memory limit" --top-k 5
```

Kết quả có citation IDs, nguồn, corpus hash và đoạn văn. Score là BM25 để xem thử, không phải accuracy hay kết luận benchmark. Corpus mặc định là snapshot lịch sử. Xem [hướng dẫn tái lập](05_research/reproducibility-guide.md) để đọc Parquet và chạy các bước chuẩn bị.

## Những phần còn cần hoàn thiện trước thí nghiệm cuối

Chưa có human qrels/reference answers; chưa có agreement hoặc kết quả baseline. Deployment version và evidence coverage vẫn cần duyệt. Còn 6 bibliography chưa đủ thông tin, trong đó 4 record chưa khớp định danh. Khớp định danh không đồng nghĩa mọi trường xuất bản đã được xác minh; số mục có venue/year được xác minh là 366. RE2-TT mới có metadata, không tải telemetry vì là nhánh mở rộng; có một ca thiếu logs theo nguồn. Các dataset khác giữ quyết định nguồn, không được tính là đã tải.

Raw data giữ byte gốc và có email/IP patterns; chỉ bản trích xuất đã qua khử định danh theo quy tắc. Không đưa nhánh `labels` hoặc manifest có tên case chứa gold vào model/index. Không gửi raw lên dịch vụ mô hình khi chưa xử lý phù hợp.

`README.md` và `MANIFEST_SHA256.txt` ban đầu được giữ nguyên làm mốc kiểm toán của gói trước khi thu thập. Manifest mới `MANIFEST_RESEARCH_SHA256.txt` và `04_audit/research-file-inventory.tsv` được tạo sau các kiểm tra cuối; không gồm binary dependency trong `.runtime-python`. Môi trường dữ liệu đã dùng nằm trong `04_audit/data-runtime.json`. Trạng thái hiện tại ở tài liệu này. Hoàn thiện bàn giao: 2026-09-13T00:28:56+07:00 (Asia/Saigon); receipts nguồn dùng UTC.
