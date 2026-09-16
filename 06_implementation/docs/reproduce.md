# Hướng dẫn Tái lập Kết quả Thực nghiệm (Reproduction Guide)

Tài liệu: `cs221-reproduce-guide-v1`  
Phiên bản: `1.0.0`  
Ngày ban hành: `2026-09-16T01:30:00Z`  
Áp dụng cho: Hội đồng chấm, Giảng viên và Nhóm nghiên cứu CS221  

---

## 1. Yêu cầu Môi trường (System & Environment Requirements)

- **Hệ điều hành:** Hỗ trợ Windows 10/11 (AMD64) hoặc Linux (Ubuntu 22.04 LTS / Debian 12 / Kaggle CPU/GPU).
- **Python:** Phiên bản chuẩn CPython `3.11.9` (hỗ trợ `3.11.x`).
- **Phụ thuộc cốt lõi:**
  - `numpy >= 1.24.0` (xử lý ma trận cosine và L2-normalization)
  - `pyarrow >= 21.0.0` (đọc telemetry data định dạng Parquet)
  - `pydantic >= 2.0.0` (xác thực schema đầu ra của mô hình sinh)
  - `PyYAML >= 6.0` (phân tích cấu hình hệ thống)
  - `pytest >= 8.0` (chạy bộ kiểm thử tự động)

---

## 2. Các bước Tái lập từ Đầu (Step-by-Step Reproduction)

### Bước 1: Khởi tạo Môi trường ảo (Virtual Environment Setup)

```powershell
# Di chuyển vào thư mục triển khai
cd 06_implementation

# Tạo môi trường ảo riêng biệt
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# (Trên Linux / macOS: source .venv/bin/activate)

# Cài đặt các gói phụ thuộc
pip install numpy pyarrow pydantic PyYAML pytest
```

### Bước 2: Chạy Toàn bộ Kiểm thử Hợp đồng và Tính toàn vẹn (302 Automated Tests)

Bộ kiểm thử tự động xác minh tính bất biến của dữ liệu, không rò rỉ nhãn (data leakage) và độ chính xác của các thuật toán xếp hạng:

```powershell
# Chạy pytest từ thư mục 06_implementation
python -m pytest -o pythonpath=.
```

**Kỳ vọng đầu ra (Expected Output):**
```text
============================ 302 passed in ~45s =============================
```
Mọi test case liên quan đến phân tách split, chuẩn hóa token, BM25, Dense cosine, RRF fusion, validator trích dẫn và demo loaders đều phải đạt `PASSED`.

---

### Bước 3: Tính toán lại Bộ Chỉ số Chính từ Evaluator Bundle (Core Metric Recomputation)

Để tái tính các bảng số liệu trong báo cáo từ dữ liệu đã khóa mà không cần gọi lại API sinh tốn phí:

```powershell
# 1. Tính toán lại bảng xếp hạng truy hồi (Retrieval Performance)
python -m src.evaluation score --system freezes/F1.json --qrels annotations/qrels/test/ --runs runs/retrieval/

# 2. Phân tích thống kê theo cụm 6 families và Leave-One-Family-Out
python -m src.evaluation analyze --results results/per-incident.tsv --group scenario_family_id

# 3. Kiểm tra tính toàn vẹn của gói bàn giao
python -m src.evaluation validate-handoff --manifest configs/final-manifest.json
```

---

## 3. Bảng Đối chiếu Kết quả và Dung sai Số học (Tolerance Matrix)

| Chỉ số (Metric) | Điều kiện / Bộ truy hồi | Giá trị Kỳ vọng (Expected) | Dung sai cho phép (Tolerance) | Nguồn lưu vết |
|---|---|:---:|:---:|---|
| **passage nDCG@5** | IR-B (BM25) on Test | `0.628` | $\pm 10^{-8}$ | `reports/final-tables/table1-retrieval-performance.tsv` |
| **passage nDCG@5** | IR-D (Dense E5) on Test | `0.594` | $\pm 10^{-8}$ | `reports/final-tables/table1-retrieval-performance.tsv` |
| **passage nDCG@5** | IR-H (Hybrid RRF) on Test | `0.671` | $\pm 10^{-8}$ | `reports/final-tables/table1-retrieval-performance.tsv` |
| **Paired Delta ($\Delta$)** | IR-H vs. BM25 on Test | `+0.043` | $\pm 10^{-8}$ | `reports/final-tables/table1-retrieval-performance.tsv` |
| **Top-1 Accuracy** | G0 (No-RAG) | `38.9% (7/18)` | Exact ratio | `reports/final-tables/table2-generation-performance.tsv` |
| **Top-1 Accuracy** | GH (Hybrid RAG) | `72.2% (13/18)` | Exact ratio | `reports/final-tables/table2-generation-performance.tsv` |
| **Citation Validity** | GH (Hybrid RAG) | `97.2% (35/36)` | Exact ratio | `reports/final-tables/table2-generation-performance.tsv` |
| **Claim Support** | GH (Hybrid RAG) | `85.2% (46/54)` | Exact ratio | `reports/final-tables/table2-generation-performance.tsv` |
| **Abstention Rate** | G0 (No-RAG) | `22.2% (4/18)` | Exact ratio | `reports/final-tables/table2-generation-performance.tsv` |

---

## 4. Chạy Ứng dụng Demo Kiểm toán Trực quan (Local Interactive Demo)

Để trực tiếp quan sát và đối chiếu từng câu trả lời với đoạn văn bản trích dẫn thực tế mà không cần kết nối Internet:

```powershell
# Khởi chạy demo viewer trên trình duyệt
python -m src.demo.app --port 8080
```
Mở trình duyệt tại `http://127.0.0.1:8080` để duyệt 5 ca sự cố điển hình (thành công, cảnh báo độ tin cậy thấp, từ chối trả lời an toàn, bẫy trích dẫn ảo giác, và so sánh đối chứng GB vs. GH).

---

## 5. Xử lý Sự cố Thường gặp (Troubleshooting)

1. **Lỗi `ModuleNotFoundError: No module named 'src'`:**  
   Chạy lệnh với tùy chọn `python -m ...` hoặc thiết lập biến môi trường `$env:PYTHONPATH="."`.
2. **Lỗi phiên bản bánh xe PyArrow trên Linux:**  
   Nếu chạy trên môi trường Linux/Kaggle, cài đặt gói pyarrow tương ứng với Linux x86_64 qua `pip install pyarrow==21.0.0`. Không sao chép các file `.whl` định dạng Windows `win_amd64`.
3. **Sự khác biệt khi gọi lại API sinh mới (Fresh Generation):**  
   Mô hình thương mại bên ngoài có thể thay đổi trọng số ngầm. Để đối chiếu bit-exact, luôn sử dụng replay cache đã băm trong `runs/generation/test/`.
