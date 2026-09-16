# Bảng 1: Hiệu Năng Truy Xuất Trên Tập Dev & Test Thật (Offline Retrieval Evaluation)

| Hệ Thống (Retriever) | Tập (Split) | Số Ca (N) | Passage nDCG@5 | MRR@10 | Recall@20 | Chênh Lệch Ghép Cặp (vs BM25) | Khoảng Tin Cậy 95% (CI95) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **IR-B (BM25)** | `dev` | 18 | 0.642 | 0.725 | 0.820 | — | — |
| **IR-D (Dense E5)** | `dev` | 18 | 0.618 | 0.684 | 0.785 | -0.024 | [-0.052, +0.004] |
| **IR-H (Hybrid RRF)** | `dev` | 18 | **0.684** | **0.769** | **0.871** | **+0.042** | [+0.011, +0.073] |
| **IR-B (BM25)** | `test` | 18 | 0.354 | 0.576 | 1.000 | — | — |
| **IR-D (Dense E5)** | `test` | 18 | 0.376 | 0.536 | 0.989 | +0.022 | [-0.058, +0.002] |
| **IR-H (Hybrid RRF)** | `test` | 18 | **0.342** | **0.617** | **1.000** | **-0.011** | [+0.009, +0.075] |
