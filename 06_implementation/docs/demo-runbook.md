# Runbook Vận Hành Demo Offline Kiểm Bằng Chứng (Plan 09)

Tài liệu hướng dẫn triển khai, vận hành và kiểm tra ứng dụng Demo Offline kiểm tra bằng chứng (Evidence Demo) thuộc đề tài CS221 AIOps RAG.

---

## 1. Nguyên tắc thiết kế và bảo mật

1. **Hoạt động Offline 100% (Local-first):**
   - Ứng dụng chỉ lắng nghe trên `127.0.0.1` (localhost).
   - Tuyệt đối không thực hiện bất kỳ cuộc gọi HTTP ra ngoài internet hoặc cloud API.
   - Không yêu cầu tài khoản, API key hay quyền truy cập mạng.

2. **Chế độ Chỉ Đọc (Read-only) và Kiểm Soát Đường Dẫn (Allowlist):**
   - Mọi truy xuất file bị giới hạn nghiêm ngặt trong phạm vi thư mục gốc `06_implementation`.
   - Trình tải (Loader) từ chối tuyệt đối các đường dẫn chứa ký tự path traversal `..` hoặc đường dẫn tuyệt đối trỏ ra ngoài gốc hệ thống.

3. **An toàn hiển thị (Sanitization & Escaping):**
   - Toàn bộ nội dung log, trace, raw JSON, văn bản tài liệu và output của mô hình đều được HTML-escaped trước khi render.
   - Không thực thi mã JavaScript hoặc HTML nhúng bên trong dữ liệu viễn trắc (telemetry) hay tri thức.

4. **Phân định minh bạch nguồn dữ liệu bằng Text Badge:**
   - `[DỮ LIỆU MÔ PHỎNG (FIXTURE)]`: Dùng cho các fixture kiểm thử cấu trúc (khi chưa có `08.results`).
   - `[PHÁT LẠI KẾT QUẢ ĐÃ LƯU (REPLAY)]`: Kết quả sinh thực tế đã được freeze và tính hash.
   - `[GỌI TRỰC TIẾP (LIVE)]`: Chế độ gọi suy luận trực tiếp (chỉ mở khi có cờ ủy quyền rõ ràng và có kết nối được cấp phép).

5. **Xác thực toàn vẹn Hash (Hash Integrity Gate):**
   - Loader tự động kiểm tra mã băm SHA-256 của `manifest.json` và `context.jsonl`.
   - Nếu phát hiện sai lệch băm (hash mismatch), hệ thống chuyển sang trạng thái `artifact_mismatch` và hiển thị cảnh báo, không âm thầm tiếp tục.

---

## 2. Yêu cầu môi trường

- **Hệ điều hành:** Windows 10/11, Linux, hoặc macOS.
- **Python:** Python 3.10 trở lên (khuyến nghị Python 3.11).
- **Thư viện phụ thuộc:**
  - Standard library (`http.server`, `urllib`, `json`, `hashlib`, `html`, `pathlib`, `argparse`).
  - PyYAML (`yaml`) để đọc cấu hình demo cases.
  - Không cần cài đặt framework web nặng (Django/Flask/FastAPI).

---

## 3. Hướng dẫn khởi chạy

### Bước 1: Kích hoạt môi trường ảo
Từ thư mục `06_implementation/`:
```powershell
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1

# Hoặc chạy trực tiếp bằng python của venv:
.venv\Scripts\python.exe -m src.demo.app --port 8080
```

### Bước 2: Chọn cổng và tham số khởi động
Cú pháp lệnh:
```bash
python -m src.demo.app [--port <PORT>] [--config <CONFIG_PATH>] [--host <HOST>]
```
- `--port`: Cổng lắng nghe HTTP (mặc định: `8080`, nếu bận có thể chọn `8081`, `8765`,...).
- `--host`: Mặc định `127.0.0.1` (bảo vệ an toàn cục bộ).
- `--config`: Đường dẫn file cấu hình cases (mặc định: `configs/demo-cases.yaml`).

### Bước 3: Truy cập trên trình duyệt
Mở trình duyệt web bất kỳ tại địa chỉ:
```text
http://127.0.0.1:8080
```

---

## 4. Hướng dẫn điều hướng và thao tác

### Bố cục 3 vùng (Three-Panel Layout)
- **Cột trái (Observations & Telemetry):**
  - Hiển thị thông tin incident: `incident_id`, hệ thống (`online_boutique`), khoảng thời gian quan sát.
  - Bảng tổng hợp các metric bất thường (CPU, Memory, Disk I/O, Socket, Latency p50/p90).
  - Danh sách log spans và trace spans liên quan.
- **Cột giữa (Retrieved Evidence & Knowledge Ranks):**
  - Các đoạn trích dẫn tri thức (evidence items) được truy xuất theo rank.
  - Hiển thị chính xác đoạn văn bản `actual_context_text` đã gửi cho mô hình.
  - Thông tin xuất xứ: Document ID, Chunk ID, Source Path, Revision git, Codepoint offsets `[start, end]`.
- **Cột phải (Model Claims, Unknowns & Citations):**
  - Nguyên nhân đề xuất (`candidate_causes`) kèm lý do giải thích.
  - Các tuyên bố được chứng minh (`supported_claims`): loại claim (`observation` vs `inference`) và danh sách `evidence_ids`.
  - **Tương tác click citation:** Khi click vào mã citation (ví dụ `[know_redis_manifest_01]`), ứng dụng tự động scroll và làm nổi bật (highlight màu vàng viền xanh) đoạn evidence tương ứng ở cột giữa.
  - Các thông tin còn thiếu (`missing_information`) và các bước kiểm tra tiếp theo (`next_checks`).
  - Huy hiệu trạng thái độ tin cậy (`confidence_label`) và trạng thái từ chối (`abstain`).

### Chuyển đổi Case và Chế độ So sánh (Compare View)
- **Menu chọn Case:** Nằm ở thanh điều hướng trên cùng, cho phép chuyển đổi giữa 4 nhóm kịch bản:
  1. `fixture:case_01_success` (Thành công - Hybrid GH)
  2. `fixture:case_02_weak_diagnosis` (Chẩn đoán yếu - BM25 GB)
  3. `fixture:case_03_missing_evidence` (Thiếu bằng chứng - G0 Abstain)
  4. `fixture:case_04_invalid_citation` (Lỗi citation - GD Invalid)
  5. `fixture:case_05_compare_gb_gh` (So sánh đối chứng GB vs GH trên cùng incident)
- **So sánh đối chứng:**
  - Nhấp nút **"So sánh với GH"** để hiển thị song song 2 cột kết quả của BM25 (GB) và Hybrid (GH).
  - Hệ thống kiểm tra điều kiện tiên quyết: Cùng `incident_id` và cùng `observation_hash`. Nếu khác hash viễn trắc, hệ thống sẽ từ chối so sánh và thông báo mismatch.

---

## 5. Xử lý sự cố (Troubleshooting)

| Vấn đề | Nguyên nhân | Biện pháp xử lý |
|---|---|---|
| `Address already in use` (Lỗi cổng) | Port 8080 đang bị chiếm dụng bởi tiến trình khác | Chạy lệnh với `--port 8081` hoặc `--port 8765`. |
| `artifact_mismatch` | File manifest hoặc context bị sửa đổi sau khi tạo | Chạy `.venv\Scripts\python scripts/generate_demo_fixtures.py` để tái lập fixtures chuẩn. |
| `Path traversal rejected` | Đường dẫn `result_ref` cố ý trỏ ra ngoài `06_implementation` | Kiểm tra lại `configs/demo-cases.yaml`, đường dẫn phải nằm trong allowlist. |
| Giao diện không nổi bật citation khi click | Trình duyệt tắt JavaScript | Bật JavaScript cục bộ trên trình duyệt. Script tương tác chỉ thuần DOM thao tác client-side, không tải thư viện ngoài. |
| Mô hình trả về JSON hỏng | Case 04 cố tình mô phỏng lỗi citation | Đây là hành vi đúng của Case 04; màn hình hiển thị raw escaped text kèm lỗi validator. |

---

## 6. Checklist nghiệm thu bàn giao (Phase 03)

- [x] Khởi động ứng dụng độc lập không cần internet.
- [x] Kiểm tra thành công ít nhất 1 citation highlight ở Case 01.
- [x] Hiển thị rõ ràng trạng thái chẩn đoán yếu (Low confidence) ở Case 02.
- [x] Hiển thị cờ `abstain=true` và `missing_information` ở Case 03.
- [x] Hiển thị raw error an toàn (không crash) ở Case 04.
- [x] So sánh đối chứng thành công giữa GB và GH ở Case 05.
- [x] Không tìm thấy bất kỳ cuộc gọi mạng ngoại vi nào trong network panel trình duyệt.
