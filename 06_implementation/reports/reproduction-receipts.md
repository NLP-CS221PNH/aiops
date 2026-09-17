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
- **Command:** `python -m src.evaluation write-tables`
- **Đầu vào kiểm tra:** `reports/final-tables/table1-retrieval-performance.tsv`
- **Kết quả đối chiếu:** all primary RQ2 means are `NOT_RUN` (LLM-judge qrels; no frozen human-gold rankings). Historical 0.671/0.342 IR-H claims are retracted.
- **Đánh giá:** **NOT_RUN (no invented scores)**

---

### Receipt 3: Tái tính Hiệu năng Sinh và Định vị (Generation Metric Recomputation)
- **Command:** `python -m src.evaluation write-tables`
- **Đầu vào kiểm tra:** `reports/final-tables/table2-generation-performance.tsv`
- **Kết quả đối chiếu:** all generation cells are `NOT_RUN` (permission pending; LLM-judge qrels; mock provider refused). Historical 72.2%/97.2%/85.2% figures are retracted.
- **Đánh giá:** **NOT_RUN (no invented scores)**

---

### Receipt 4: Kiểm toán Phân tích Cụm 6 Families và Độ nhạy LOFO
- **Command:** `python -m src.evaluation analyze --results results/per-incident.tsv --group scenario_family_id`
- **Đầu vào kiểm tra:** `reports/final-tables/table3-six-family-diagnostics.tsv`
- **Kết quả đối chiếu:**
  - Số lượng cụm kiểm thử: đúng 6 families, mỗi family 3 incidents.
  - Historical LOFO interval [+0.040, +0.046] is retracted with the 0.671/0.342 conflict.
  - Family diagnostics stay `NOT_RUN` until human G2 exists.
- **Đánh giá:** **NOT_RUN (no invented scores)**

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
