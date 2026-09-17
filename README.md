# CS221 · AIOps / RCA / Hybrid RAG — Research Pack

**Nguyễn Văn Nam · MSSV 24521120**  
**Current HEAD:** implementation and research-pack working tree (see `START-HERE.md`).  
**Initial research snapshot (12/09/2026):** Markdown/JSON catalogs only; that snapshot is audit history, not the current public surface.

## Read this first

Current publication rules: [docs/repository-publication-policy.md](docs/repository-publication-policy.md).  
Archive and history limitations: [docs/public-release-runbook.md](docs/public-release-runbook.md).  
Ledger: [04_audit/public-artifact-ledger.tsv](04_audit/public-artifact-ledger.tsv).

The public Git tip tracks project-owned code, schemas, descriptive metadata, de-identified processed extracts, the canonical inference bundle, attributed knowledge manifests/chunks, and snapshot `LICENSE` files needed for offline reconstruction checks. Raw RCAEval Parquet, paper caches/full text/PDFs, gold labels, private sidecars, candidate copies and knowledge snapshot *source bytes* are gitignored and reconstructed from pinned upstream revisions.

Root `LICENSE` is MIT for project Software. It does not relicense third-party data, PDFs, full text or snapshots.

## Start here

Read the [proposal](00_plan/project_proposal.md), then [dataset shortlist](02_datasets/shortlist.md), [evaluation plan](00_plan/experiments_and_evaluation.md), and [remaining work](00_plan/remaining-work.md). For reading order, open [50 priority papers](01_papers/priority_reading.md).

Offline PR checks from a clean checkout:

```powershell
python scripts/validate-public-artifacts.py --ledger 04_audit/public-artifact-ledger.tsv --tracked-only
python scripts/canonical_identifiers.py
python scripts/validate-research-pack.py --check --mode pr
python scripts/freeze-research-pack.py --check
cd 06_implementation
python -m pytest -q -o pythonpath=.
```

Windows AMD64 + CPython 3.11.9 is the supported install (`06_implementation/configs/requirements-lock.txt` with `pip --require-hashes`). This repository does not currently ship a Linux hash lock.

Historical catalog counts from the 12/09/2026 snapshot remain in `04_audit/package_qa.md` (labelled as that snapshot) and in `MANIFEST_SHA256.txt`.

## Catalog snapshot (12/09/2026, historical)


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

Đọc [đề cương](00_plan/project_proposal.md), sau đó [shortlist dữ liệu](02_datasets/shortlist.md), [kế hoạch đánh giá](00_plan/experiments_and_evaluation.md) và [việc còn lại](00_plan/remaining-work.md). Để chọn tài liệu đọc, mở [50 tài liệu ưu tiên](01_papers/priority_reading.md). Các ghi chú ưu tiên là câu hỏi cần rút ra khi đọc, không giả làm bản tóm tắt toàn văn đã hoàn tất.

## Cấu trúc

| Đường dẫn | Công dụng |
|---|---|
| `00_plan/` | Đề cương, tổng hợp hướng nghiên cứu, thí nghiệm, annotation, timeline, việc còn lại |
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
