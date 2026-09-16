# Bảng 3: Đánh Giá Phân Tách Theo 6 Họ Sự Cố Kiểm Thử (Family-level Diagnostics & Leave-One-Out)

| Họ Sự Cố (Family ID) | Dịch Vụ Gốc | Loại Lỗi (Fault) | Số Ca (N) | BM25 nDCG@5 | Dense nDCG@5 | Hybrid nDCG@5 | Chênh Lệch Ghép Cặp | GH Top-1 Acc | Độ Lệch Rút Bỏ (LOO Delta) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `FAM-TEST-01 (fam_2a57)` | `productcatalogservice` | `loss` | 3 | 0.232 | 0.653 | **0.314** | **+0.083** | **100%** | -0.006 |
| `FAM-TEST-02 (fam_4f5e)` | `currencyservice` | `cpu` | 3 | 0.242 | 0.124 | **0.207** | **-0.035** | **100%** | -0.027 |
| `FAM-TEST-03 (fam_60b0)` | `checkoutservice` | `mem` | 3 | 0.437 | 0.352 | **0.425** | **-0.012** | **100%** | +0.017 |
| `FAM-TEST-04 (fam_71e9)` | `currencyservice` | `socket` | 3 | 0.387 | 0.457 | **0.365** | **-0.022** | **100%** | +0.004 |
| `FAM-TEST-05 (fam_7309)` | `recommendationservice` | `delay` | 3 | 0.466 | 0.473 | **0.486** | **+0.020** | **100%** | +0.029 |
| `FAM-TEST-06 (fam_d01f)` | `currencyservice` | `disk` | 3 | 0.359 | 0.197 | **0.256** | **-0.102** | **100%** | -0.017 |
