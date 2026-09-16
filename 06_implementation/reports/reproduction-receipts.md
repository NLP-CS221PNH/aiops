# Báo cáo Biên nhận Tái lập Thực nghiệm (Reproduction Receipts)

Artifact ID: `cs221-reproduction-receipts-v1`  
Phiên bản: `1.0.0`  
Thời điểm đo lường: `2026-09-16T01:30:00Z`  
Người thực hiện kiểm toán: Thành viên C (Độc lập đối chiếu)  
Người xác nhận: Thành viên B (Tác giả code đánh giá)  

---

## 1. Hồ sơ Môi trường Đo lường (Environment Specifications)

- **Hệ điều hành:** Windows 11 AMD64 (build 26100)
- **CPython:** `3.11.9` (tags: `cp311-cp311-win_amd64`)
- **Package Versions:**
  - `numpy`: `2.3.3`
  - `pyarrow`: `21.0.0`
  - `pydantic`: `2.13.5`
  - `pytest`: `8.4.2`
  - `PyYAML`: `6.0.3`
- **Mã băm F1 Freeze:** `4d7a8e2b...` (khóa cấu hình và pipeline)
- **Mã băm F2 Freeze:** `9c1f0b7e...` (khóa tập nhãn qrels test)
- **Phạm vi tái lập (Scope):** `metric_rerun` + `retrieval_rerun` + `generation_replay`

---

## 2. Nhật ký Biên nhận Từng Bước Thực nghiệm (Receipt Ledger)

### Receipt 1: Chạy Toàn bộ 302 Automated Contract & Integrity Tests
- **Command:** `python -m pytest -o pythonpath=.`
- **Thời gian thực thi:** 48.88 giây
- **Số lượng kiểm thử:** 302 items collected
- **Kết quả quan sát:**
  - `test_annotation_integrity.py`: 4 passed
  - `test_citation_registry.py`: 14 passed
  - `test_corpus_integrity.py`: 50 passed
  - `test_data_boundary.py`: 31 passed
  - `test_data_provenance.py`: 17 passed
  - `test_demo_app.py`: 6 passed
  - `test_demo_loaders.py`: 8 passed
  - `test_evaluation_contract.py`: 9 passed
  - `test_generation_contract.py`: 3 passed
  - `test_generation_reliability.py`: 3 passed
  - `test_representation_contract.py`: 32 passed
  - `test_representation_pipeline.py`: 11 passed
  - `test_retrieval_contract.py`: 32 passed
  - `test_retrieval_engines.py`: 34 passed
  - `test_validate_protocol.py`: 48 passed
- **Đánh giá:** **PASSED (302/302 tests passed, 0 failures, 0 errors)**

---

### Receipt 2: Tái tính Chỉ số Truy hồi (Retrieval Metric Recomputation)
- **Command:** `python -m src.evaluation score --system freezes/F1.json --qrels annotations/qrels/test/ --runs runs/retrieval/`
- **Đầu vào kiểm tra:** `results/per-incident.tsv`
- **Dung sai quy định (Tolerance):** $\pm 10^{-8}$ (absolute)
- **Kết quả đối chiếu:**
  - `IR-B (BM25) passage nDCG@5`: Kỳ vọng = 0.62800000; Quan sát = 0.62800000; Sai lệch = 0.00e+00 (**PASS**)
  - `IR-D (Dense E5) passage nDCG@5`: Kỳ vọng = 0.59400000; Quan sát = 0.59400000; Sai lệch = 0.00e+00 (**PASS**)
  - `IR-H (Hybrid RRF) passage nDCG@5`: Kỳ vọng = 0.67100000; Quan sát = 0.67100000; Sai lệch = 0.00e+00 (**PASS**)
  - `Paired Delta (IR-H vs. BM25)`: Kỳ vọng = +0.04300000; Quan sát = +0.04300000; Sai lệch = 0.00e+00 (**PASS**)
- **Đánh giá:** **MATCHED EXACTLY (Dung sai $< 10^{-8}$)**

---

### Receipt 3: Tái tính Hiệu năng Sinh và Định vị (Generation Metric Recomputation)
- **Đầu vào kiểm tra:** `reports/final-tables/table2-generation-performance.tsv`
- **Kết quả đối chiếu:**
  - Top-1 Service Accuracy (G0): 7/18 = 38.888889% (**PASS**)
  - Top-1 Service Accuracy (GH): 13/18 = 72.222222% (**PASS**)
  - Citation Validity (GH): 35/36 = 97.222222% (**PASS**)
  - Claim Support Precision (GH): 46/54 = 85.185185% (**PASS**)
  - Abstention Rate (G0): 4/18 = 22.222222% (**PASS**)
- **Đánh giá:** **MATCHED EXACTLY**

---

### Receipt 4: Kiểm toán Phân tích Cụm 6 Families và Độ nhạy LOFO
- **Command:** `python -m src.evaluation analyze --results results/per-incident.tsv --group scenario_family_id`
- **Đầu vào kiểm tra:** `reports/final-tables/table3-six-family-diagnostics.tsv`
- **Kết quả đối chiếu:**
  - Số lượng cụm kiểm thử: đúng 6 families, mỗi family 3 incidents.
  - Biên độ dao động LOFO macro delta: min = +0.040, max = +0.046.
  - Paired delta dương trên cả 6 families độc lập.
- **Đánh giá:** **CONSISTENT & VERIFIED**

---

### Receipt 5: Kiểm tra Replay Offline và Không Rò rỉ Nhãn của Ứng dụng Demo
- **Command:** `python -m pytest tests/test_demo_loaders.py tests/test_demo_app.py`
- **Đầu vào kiểm tra:** `reports/demo/demo-manifest.json`, `reports/demo/case-audit.tsv`
- **Kết quả quan sát:**
  - 14/14 demo tests passed.
  - Mọi đường dẫn dữ liệu tuân thủ relative paths an toàn (`safe_resolve_path`), không truy cập ra ngoài thư mục hoặc mount private gold labels.
  - Khả năng phát hiện và bẫy trích dẫn ảo giác (`case_04_invalid_citation`) hoạt động chính xác 100%.
- **Đánh giá:** **VERIFIED SECURE & REPRODUCIBLE**

---

## 3. Tuyên bố Nghiệm thu Tái lập
Nhóm nghiên cứu xác nhận:
1. Mọi con số trình bày trong Báo cáo cuối cùng (`reports/final-report.md`) và Bản trình chiếu (`reports/slides.md`) đều có thể tái tạo lại nguyên vẹn từ các artifacts trong gói mã nguồn.
2. Không sử dụng bất kỳ số liệu ước lượng, số liệu giả lập chưa chạy hoặc trích dẫn không được hỗ trợ bởi bằng chứng.
