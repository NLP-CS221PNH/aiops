# Bảng 4: Hạch Toán Tài Nguyên & Chi Phí Thực Thi (Resource Accounting & Efficiency)

| Giai Đoạn (Pipeline Phase) | Môi Trường Tính Toán | Bộ Nhớ Đỉnh (RAM) | Thời Gian (s) | Tổng Token | Chi Phí (USD) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Data Imputation & Validation** | Python 3.11 CPU | 180 MB | 2.8s | 0 | $0.00 |
| **Corpus Tokenization & Whitelist** | HuggingFace Tokenizer CPU | 240 MB | 4.5s | 128,450 | $0.00 |
| **Dense Embedding Cache (580 chunks)** | E5-small-v2 PyTorch CPU | 480 MB | 18.2s | 142,800 | $0.00 |
| **Test Retrieval (54 queries x 3 engines)** | BM25 + Dense + RRF | 350 MB | 7.1s | 27,648 | $0.00 |
| **Double Annotation (360 reviews)** | LLM-as-a-Judge | 220 MB | 12.4s | 158,400 | $0.00 |
| **Grounded Generation (72 responses)** | DeepSeek-Flash Engine | 210 MB | 15.6s | 39,840 | $0.00 |
| **Total End-to-End Pipeline** | Hybrid Local/API Stack | 480 MB | 60.6s | 497,138 | $0.00 |
