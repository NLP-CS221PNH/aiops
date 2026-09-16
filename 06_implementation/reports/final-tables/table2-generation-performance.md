# Bảng 2: Hiệu Năng Sinh Chẩn Đoán Dẫn Chứng Trên 18 Test Incidents (Grounded Generation)

| Điều Kiện (Condition) | Số Phản Hồi (N) | Độ Chính Xác Top-1 (Root Cause) | Độ Chính Xác Top-3 | Tính Hợp Lệ Dẫn Chứng (Citation Validity) | Độ Chuẩn Xác Chứng Cứ (Claim Precision) | Tỷ Lệ Từ Chối (Abstention) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **G0 (No-RAG)** | 18 | **33.3%** | 44.4% | null | 50.0% | 16.7% |
| **GB (BM25 RAG)** | 18 | **61.1%** | 66.7% | 100.0% | 38.9% | 5.6% |
| **GD (Dense RAG)** | 18 | **55.6%** | 66.7% | 100.0% | 33.3% | 5.6% |
| **GH (Hybrid RAG)** | 18 | **100.0%** | 100.0% | 100.0% | 36.1% | 0.0% |
