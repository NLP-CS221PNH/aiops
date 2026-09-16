# Nhật ký Khác biệt Thực nghiệm & Dung sai (Test Deviations & Tolerance Ledger)

Tài liệu: `cs221-test-deviations-v1`  
Phiên bản: `1.0.0`  
Ngày ban hành: `2026-09-16T02:30:00Z`  
Giai đoạn áp dụng: Kế hoạch 08 (Đánh giá & Khóa F1/F2) và Kế hoạch 10 (Bàn giao)

---

## 1. Bối cảnh & Mục đích (Context & Purpose)

Nhật ký này ghi lại mọi điểm khác biệt (deviations), sự điều chỉnh môi trường phần cứng, dung sai tính toán và các giải pháp tương thích so với kế hoạch ban đầu, nhằm đảm bảo tính tái lập 100% không suy hao (lossless bit-exact reproduction).

---

## 2. Bảng Theo dõi Khác biệt Thực nghiệm (Deviation Ledger)

| ID | Thành phần | Kế hoạch ban đầu | Thực tế triển khai | Lý do & Ảnh hưởng | Biện pháp bảo toàn |
|---|---|---|---|---|---|
| **DEV-01** | Phần cứng nhúng (Encoder Device) | GPU Nvidia T4 trên Kaggle | CPU Execution (AMD64) trên môi trường cục bộ | Chạy kiểm định cục bộ tự hành không cần phụ thuộc quota Kaggle GPU; kích thước ma trận corpus nhỏ (580 chunks) hoàn thành trong 1.5 giây trên CPU | Vector chuẩn hóa L2 với sai số số học $\le 10^{-7}$, nDCG@5 khớp tuyệt đối |
| **DEV-02** | Replay Inferences | Gọi lại API sinh trực tiếp mỗi lần chạy | Lưu vết Replay Cache có băm SHA256 (`runs/generation/test/`) | Tránh trôi dạt phân phối ngầm (silent drift) của API thương mại và chi phí mạng | Lưu vết 72 bản ghi sinh hoàn chỉnh với băm context và payload |
| **DEV-03** | Khung chuẩn hóa E5 | Tokenizer HuggingFace online | Tokenizer & Config cục bộ ghim cố định SHA256 | Đảm bảo tính bất biến của không gian biểu diễn từ vựng khi offline | Toàn bộ 4 file tokenizer/vocab đã lưu trong `vendor/e5-small-v2/` |
| **DEV-04** | Chuẩn hóa xuống dòng Git | Windows default CRLF | Bắt buộc LF qua cấu hình `.gitattributes` | Tránh làm sai lệch mã băm SHA256 của các tệp tài liệu và manifest | Thêm quy tắc `* text=auto eol=lf` trong `.gitattributes` |

---

## 3. Dung sai Số học & Ngưỡng Chấp nhận (Numerical Tolerance)

1. **Cosine Similarity & Dense Indexing:**
   - Sử dụng chuẩn `np.float32`.
   - Dung sai đối chiếu giá trị nDCG: $\pm 10^{-8}$.
2. **Xác thực Trích dẫn (Citation Verification):**
   - Không có dung sai: mã chunk và evidence ID phải khớp chính xác 100% với danh sách context đã nạp.
3. **Mã băm Khóa (Cryptographic Hash Gates):**
   - Sai số cho phép: 0 (bất kỳ sự thay đổi dù chỉ 1 byte sẽ làm vô hiệu hóa F1 và F2).
