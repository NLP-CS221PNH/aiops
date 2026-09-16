# Báo Cáo Đo Lường Độ Đồng Thuận Chấm Nhãn (Plan 06 Hướng B)

## 1. Phương pháp & Giao thức Thực hiện

- **Phương pháp:** LLM-as-a-Judge với quy trình chấm đôi độc lập (Double Annotation) theo Rubric 3 mức (0: Không liên quan, 1: Liên quan một phần, 2: Xác đáng hỗ trợ chẩn đoán).
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

Hệ thống chấm đôi tự động LLM-as-a-Judge đạt hệ số tương quan liên người chấm vững chắc (Quadratic Weighted Kappa > 0.70 trên cả 3 tập train, dev, test), đủ điều kiện giải phóng cổng kiểm soát Plan 06 và chuyển giao sang bước đóng băng F2.
