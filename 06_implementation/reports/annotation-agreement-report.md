# RETRACTED as human agreement

**RETRACTED 2026-09-17.** Kappa below is an arithmetic property of a lexical proxy with seeded A/B noise. It does not unlock Plan 06 and is not human inter-rater agreement.

# Báo Cáo Đo Lường Độ Đồng Thuận Chấm Nhãn (Plan 06 Hướng B)

## 1. Phương pháp & Giao thức Thực hiện

- **Phương pháp:** lexical proxy (`llm_judge.py`), not an LLM and not two human reviewers. Grades are 0/1/2 with seeded A/B noise over one `base_grade`.
- **Người chấm:**
  - `Annotator A`: Persona SRE khắt khe, ưu tiên định danh chính xác mã dịch vụ và hành vi lỗi.
  - `Annotator B`: Persona SRE mở rộng ngữ cảnh, đánh giá cao sự liên đới kiến trúc và phụ thuộc giữa các microservices.
- **Phân xử bất đồng (Adjudication):** Áp dụng bộ phân xử tự động theo quy tắc hòa giải có bảo chứng.

## 2. Bảng Thống Kê Độ Đồng Thuận Theo Từng Tập

| Phân Vùng (Split) | Số Cặp Đánh Giá (N) | Tỷ Lệ Nhất Trí Tuyệt Đối | Cohen's Kappa (Unweighted) | Cohen's Kappa (Quadratic Weighted) | Đánh Giá Ngưỡng |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `train` | 200 | 86.50% | 0.7754 | **0.8542** | Đạt chuẩn xuất sắc (\(\kappa \ge 0.70\)) |
| `dev` | 180 | 87.22% | 0.7813 | **0.8524** | Đạt chuẩn xuất sắc (\(\kappa \ge 0.70\)) |
| `test` | 180 | 95.00% | 0.9174 | **0.9459** | Đạt chuẩn xuất sắc (\(\kappa \ge 0.70\)) |

## 3. Ma Trận Nhầm Lẫn (Confusion Matrices)

### Phân vùng `train`

| Annotator A \ B | Điểm 0 | Điểm 1 | Điểm 2 |
| :---: | :---: | :---: | :---: |
| **Điểm 0** | 80 | 17 | 0 |
| **Điểm 1** | 0 | 74 | 10 |
| **Điểm 2** | 0 | 0 | 19 |

### Phân vùng `dev`

| Annotator A \ B | Điểm 0 | Điểm 1 | Điểm 2 |
| :---: | :---: | :---: | :---: |
| **Điểm 0** | 79 | 12 | 0 |
| **Điểm 1** | 0 | 66 | 11 |
| **Điểm 2** | 0 | 0 | 12 |

### Phân vùng `test`

| Annotator A \ B | Điểm 0 | Điểm 1 | Điểm 2 |
| :---: | :---: | :---: | :---: |
| **Điểm 0** | 69 | 2 | 0 |
| **Điểm 1** | 0 | 81 | 7 |
| **Điểm 2** | 0 | 0 | 21 |

## 4. Kết luận

Do not treat this kappa as human agreement. It does not unlock Plan 06. Headline nDCG on these proxy files is invalid. See `freezes/F2.provenance.json`.
