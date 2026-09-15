# Tái lập bộ dữ liệu và tài nguyên nghiên cứu

## Dùng ngay các tệp đã chuẩn bị

Mở [START-HERE.html](../START-HERE.html) trực tiếp để tìm trong danh mục và xem incident/query/log excerpts. JSONL/TSV/BibTeX được lưu riêng để dùng với công cụ nghiên cứu. Không cần tải lại gần 1 GB raw data khi các kiểm tra checksum hiện vẫn đạt.

Các lệnh dưới đây chạy từ thư mục gốc của gói. Trên máy hiện tại, `python` là **Python 3.11.9**. Công cụ preview và kiểm tra toàn gói dùng thư viện chuẩn; đọc/chuẩn bị Parquet dùng **PyArrow 21.0.0** cài cục bộ trong `.runtime-python`.

```powershell
python --version
python scripts/preview-retrieval.py --query "Kubernetes pod OOMKilled memory limit" --top-k 5
python scripts/validate-research-pack.py
```

Preview chỉ là BM25 browsing trên corpus lịch sử mặc định. Kết quả giữ ID, source và corpus hash; không phải điểm đánh giá chất lượng. Muốn xem corpus hiện tại để so sánh:

```powershell
python scripts/preview-retrieval.py --query "Kubernetes pod OOMKilled memory limit" --corpus 03_collection_plan/knowledge-corpus/chunks.jsonl --top-k 5
```

## Đọc Parquet hoặc tái tạo observations

Thư mục `.runtime-python` hiện chứa wheel cho **CPython 3.11, Windows x64**. Không dùng nó với Python 3.12 của runtime tài liệu Codex: sai ABI sẽ báo thiếu `pyarrow.lib`. Khi mang gói sang máy khác, dùng Python 3.11 trên Windows x64 hoặc cài PyArrow tương thích với Python/máy đích trong một môi trường mới; giữ lại version của lần chạy để tái lập.

Trên máy này có thể đọc dữ liệu thụ động như sau:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.runtime-python').resolve()))
import pyarrow.parquet as pq

case = next(Path('02_datasets/acquired/raw').glob('inc_*'))
pf = pq.ParquetFile(case / 'logs.parquet')
print(pf.metadata.num_rows, pf.schema_arrow.names)
# Đọc từng batch để hạn chế bộ nhớ; không gọi remote dataset loader.
batch = next(pf.iter_batches(batch_size=100))
```

Tạo lại observations/labels/profile từ raw đang có:

```powershell
python scripts/prepare-incidents.py
python scripts/validate-research-pack.py
```

Lệnh prepare ghi lại derivatives từ raw với quy tắc đã định nghĩa. Giữ phiên bản nếu đã dùng derivatives trong thí nghiệm. Nó không đọc human qrels để sinh query, không chạy model, không sửa raw. Labels và tên case gốc vẫn ở nhánh riêng; không serialize chúng vào prompt.

## Tải lại dữ liệu khi thật sự cần

Release đã được ghim trong script và source registry. Chuỗi bước dành cho khôi phục/tiếp tục acquisition là:

```powershell
python scripts/acquire-datasets.py metadata
python scripts/acquire-datasets.py pilot
python scripts/acquire-datasets.py full
python scripts/prepare-incidents.py
python scripts/validate-research-pack.py
```

Đọc `acquired/meta/pilot-schema.json` trước bước full nếu tái lập trên bản gói mới. Mạng cần truy cập Hugging Face và nguồn metadata công khai. File hợp lệ được kiểm bằng revision/size/hash; không đổi revision chỉ để tránh lỗi tải. Không cần làm chuỗi này cho gói hiện tại đã thu đủ 90 ca.

## Corpus và annotation

Hai corpus đã có license, raw sources, manifests, documents và chunks. Historical là bản chính; current là snapshot so sánh. Đừng trộn chúng hoặc thay một file chunk khi đã có qrels tham chiếu ID cũ.

```powershell
python scripts/prepare-annotation-kit.py
python scripts/preview-retrieval.py --prepare-pilot
```

Các lệnh này chỉ chuẩn bị phiếu và pool nháp. Chúng từ chối ghi đè khi phát hiện phần chấm đã điền; giữ bản chấm trong phiên bản riêng trước khi mở vòng mới. Không biến các ô trống thành grade 0. Pool BM25 hiện chưa có dense/hybrid; phải mở rộng trước chấm final retrieval evaluation.

## Bibliography và báo cáo

Dùng `01_papers/enriched/catalog-enriched.tsv` để lọc trong bảng tính, `references-priority50.bib` cho nhóm đọc chính và `references-verified.bib` cho những record đủ trường đã xác minh. Trong JSONL, `research` giữ metadata nguồn và evidence; các trường trích dẫn và year basis phân biệt preprint/publication. Đọc README của nhánh paper trước khi chạy lại các script acquisition vì metadata API có rate limits.

Sau khi cập nhật artifact có chủ đích:

```powershell
python scripts/validate-research-pack.py
python scripts/build-handoff.py
python scripts/build-resource-index.py
python scripts/check-handoff-files.py
```

Kiểm tra handoff cần Node.js để kiểm cú pháp JavaScript của mục lục. Nó dùng một fixture tạm để kiểm việc giữ phiếu chấm; không thay các phiếu thật. Trong môi trường Codex hạn chế, fixture có thể cần quyền chạy ngoài sandbox vì ACL của thư mục tạm; chạy trực tiếp bằng tài khoản hiện tại là cách đã kiểm chứng. Không có kiểm UI browser tự động vì chính sách browser chặn local-file URL.

## Giới hạn tái lập

Pipeline chuẩn bị đã được chạy và kiểm; dense embeddings, reranker và generator chưa cài/chạy. Model cards và revisions đã có nhưng không phải model weights. Chưa có bộ dependency khóa cho các thí nghiệm mô hình; cần chọn generator/hardware trước khi tạo môi trường đó. Gói không chứa kết quả retrieval/diagnosis giả để làm mẫu báo cáo.
