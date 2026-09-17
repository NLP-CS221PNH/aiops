# Hướng dẫn Tái lập Kết quả Thực nghiệm (Reproduction Guide)

Tài liệu: `cs221-reproduce-guide-v1`  
Phiên bản: `1.0.0`  
Ngày ban hành: `2026-09-16T01:30:00Z`  
Áp dụng cho: Hội đồng chấm, Giảng viên và Nhóm nghiên cứu CS221  

---

## 1. Yêu cầu Môi trường (System & Environment Requirements)

- **Hệ điều hành:** Windows 10/11 AMD64 is the supported hash-locked platform. Linux is not claimed until a Linux `--require-hashes` lock exists.
- **Python:** CPython `3.11.9` (`3.11.x`).
- **Cài đặt:** `python -m pip install --require-hashes -r configs/requirements-lock.txt`

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
pip install --require-hashes -r configs/requirements-lock.txt
python -m pip install pytest pyyaml numpy pydantic tokenizers==0.21.4
```

`tokenizers==0.21.4` is the pinned tokenizer library for PR tests. Model weights are not required. The Windows `--require-hashes` lock above is runtime-only and does not cover Linux.

### Bước 2: Named test suites

Do not treat a historical pass count as a contract. Required files include `tests/test_evaluation_cli.py`, `tests/test_release_integrity.py`, `tests/test_evaluation_contract.py` and `tests/test_public_artifact_policy.py`.

```powershell
python -m pytest -o pythonpath=. tests/test_evaluation_cli.py tests/test_release_integrity.py tests/test_evaluation_contract.py tests/test_public_artifact_policy.py
python -m pytest -q -o pythonpath=.
```

---

### Bước 3: Tính toán lại Bộ Chỉ số Chính từ Evaluator Bundle (Core Metric Recomputation)

Để tái tính các bảng số liệu trong báo cáo từ dữ liệu đã khóa mà không cần gọi lại API sinh tốn phí:

```powershell
# 1. Tính toán lại bảng xếp hạng truy hồi (Retrieval Performance)
python -m src.evaluation score --system freezes/F1.json --qrels annotations/qrels/test/ --runs runs/retrieval/ --output results/scored-from-replay.tsv

# 2. Phân tích thống kê theo cụm 6 families và Leave-One-Family-Out
python -m src.evaluation analyze --results results/per-incident.tsv --group scenario_family_id --output results/family-comparison-from-replay.tsv

# 3. Kiểm tra tính toàn vẹn của gói bàn giao
python -m src.evaluation validate-handoff --manifest reports/submission-package/configs/final-manifest.json
```

---

## 3. Bảng Đối chiếu Kết quả và Dung sai Số học (Tolerance Matrix)

Headline IR/generation values are `NOT_RUN`. A second scorer pass must match TSV means within $10^{-8}$ when rankings and human G2 exist. Until then, do not claim test IR-H nDCG is 0.342 or 0.671.

| Chỉ số (Metric) | Điều kiện / Bộ truy hồi | Giá trị Kỳ vọng (Expected) | Dung sai cho phép (Tolerance) | Nguồn lưu vết |
|---|---|:---:|:---:|---|
| **passage nDCG@5** | IR-B / IR-D / IR-H on Test | `NOT_RUN` | $\pm 10^{-8}$ when scored | `reports/final-tables/table1-retrieval-performance.tsv` |
| **Paired Delta ($\Delta$)** | IR-H vs. BM25 on Test | `NOT_RUN` | $\pm 10^{-8}$ when scored | `reports/final-tables/table1-retrieval-performance.tsv` |
| **Top-1 Accuracy** | G0 / GH | `NOT_RUN` | Exact ratio when scored | `reports/final-tables/table2-generation-performance.tsv` |
| **Qrels provenance** | all headline IR | `llm_judge_adjudicated` | exact label | `configs/methodology-lock.yaml` |

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
2. **Linux is unsupported until a Linux hash lock exists.** Do not copy Windows `win_amd64` wheels.
3. **Sự khác biệt khi gọi lại API sinh mới (Fresh Generation):**  
   Mô hình thương mại bên ngoài có thể thay đổi trọng số ngầm. Để đối chiếu bit-exact, luôn sử dụng replay cache đã băm trong `runs/generation/test/`.
