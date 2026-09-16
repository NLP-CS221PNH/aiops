# Báo cáo Kiểm toán Lập luận Khoa học và Bằng chứng (Claim–Evidence Audit)

Artifact ID: `cs221-claim-audit-v1`  
Phiên bản: `1.0.0`  
Thời gian thực hiện: `2026-09-16T01:30:00Z`  
Người kiểm toán: Thành viên C (Lead Auditor)  
Người đối chiếu: Thành viên A (Data Audit), Thành viên B (Method & Metrics Audit)  

---

## 1. Mục tiêu và Nguyên tắc Kiểm toán
Báo cáo này thẩm định tính trung thực, sự nhất quán và mức độ gắn kết chặt chẽ giữa các luận điểm (scientific claims) trong Báo cáo cuối cùng (`reports/final-report.md`), Bảng số liệu (`reports/final-tables/`) và Bằng chứng từ artifacts đã khóa (`claim-evidence.tsv`).

Quy tắc bất biến:
1. **Không phóng đại năng lực (No Overclaiming):** Không khẳng định hệ thống đã giải quyết hoàn toàn chuỗi nhân quả (causal chain) hoặc rút ngắn thời gian khắc phục sự cố (MTTR) trong môi trường sản xuất thực tế.
2. **Bảo tồn kết quả âm và trường hợp khó (Preserving Difficult Cases & Neutral Results):** Giữ nguyên các ca định vị kém (như họ lỗi `frontend` HTTP 500 do cascading RPC) và sự chênh lệch vừa phải của Hybrid RRF ($+4.3\%$), không cắt xén hoặc chọn lọc ca đẹp (cherry-picking).
3. **Chính xác về mẫu số thống kê (Strict Denominators):** Báo cáo rõ ràng $n = 18$ test incidents thuộc 6 clusters, không nhân khống kích thước mẫu bằng số dòng log hay số lượt gọi API.
4. **Tách biệt Trích dẫn và Hỗ trợ ngữ nghĩa (Citation Validity vs. Semantic Support):** Một trích dẫn tồn tại trong context không tự động đồng nghĩa với việc nó hỗ trợ đầy đủ cho kết luận của mô hình.

---

## 2. Bảng Thẩm định Chi tiết Từng Luận điểm (Claim-by-Claim Disposition)

| Mã Luận điểm | Luận điểm khoa học | Bằng chứng đối chiếu (Artifacts & Hashes) | Mẫu số ($n$) | Kết quả Thẩm định | Đánh giá & Ranh giới |
|---|---|---|:---:|:---:|---|
| **CLM-DATA-001** | Quy mô 90 sự cố, 30 families, 3 repetitions/family. | `reports/data-handoff.md` (`manifest-v1`) | 90 | **PASS** | Đã kiểm toán qua test suite `test_data_provenance.py` (31 tests passed). Giới hạn ở tập RE2-Online Boutique. |
| **CLM-DATA-002** | Phân chia cụm 54 train / 18 dev / 18 test theo family. | `reports/data-handoff.md` (`split-map.tsv`) | 30 families | **PASS** | Đã xác minh không có hiện tượng rò rỉ phân phối giữa các repetitions cùng họ lỗi. |
| **CLM-DATA-003** | Kho tri thức lịch sử: 74 tài liệu, 580 chunks. | `reports/corpus-handoff.md` (`chunks.jsonl`) | 580 chunks | **PASS** | Đã kiểm tra qua `test_corpus_integrity.py`. Giới hạn ở tài liệu công khai tiền 2024. |
| **CLM-ANNO-001** | Tập core 56 incidents được chấm đôi và phân xử độc lập. | `annotations/rubric-v1.md`, `assignments.tsv` | 56 incidents | **PASS** | Đã kiểm toán độ bao phủ qua `test_annotation_integrity.py`. 34 train còn lại không có qrels core. |
| **CLM-METH-001** | Khóa toàn bộ tham số tại F1 trước khi truy cập test. | `freezes/F1.json` | 1 config lock | **PASS** | Khóa BM25 $k_1=1.5, b=0.75$, RRF $c=60$, Dense E5-small-v2. Không có hành vi test tuning. |
| **CLM-METH-002** | 4 điều kiện đối chứng bắt buộc: G0, GB, GD, GH. | `freezes/F1.json` | 4 conditions | **PASS** | Đảm bảo mọi điều kiện nhận cùng common observation bundle và decoding temperature $T = 0.0$. |
| **CLM-RES-001** | IR-H vượt BM25 trên test: nDCG@5 = 0.671 vs 0.628 ($\Delta = +0.043$). | `reports/final-tables/table1-retrieval-performance.tsv` | 18 test incidents | **PASS** | Paired delta dương nhất quán; khoảng tin cậy 95% bootstrap: $[+0.008, +0.078]$. |
| **CLM-RES-002** | Top-1 service accuracy đạt 72.2% ở GH vs 38.9% ở G0. | `reports/final-tables/table2-generation-performance.tsv` | 18 test incidents | **PASS** | Định vị dịch vụ bị tiêm lỗi chính xác; không suy diễn thành chữa lỗi tự động. |
| **CLM-RES-003** | 97.2% citation validity và 85.2% claim support ở GH. | `reports/final-tables/table2-generation-performance.tsv` | 72 responses | **PASS** | Đã kiểm toán phân tách rạch ròi giữa việc trích dẫn hợp lệ và nội dung có hỗ trợ claim. |
| **CLM-RES-004** | Tỉ lệ từ chối trả lời (abstention) đạt 22.2% ở G0 và 5.6% ở GH. | `reports/demo/case-audit.tsv` | 18 test incidents | **PASS** | Đã thẩm định hành vi an toàn qua ca kiểm thử `case_03_missing_evidence`. |
| **CLM-LIM-001** | Độ bất định hạch toán theo 6 cụm family qua LOFO. | `reports/final-tables/table3-six-family-diagnostics.tsv` | 6 families | **PASS** | LOFO macro delta dao động hẹp $[+0.040, +0.046]$; thừa nhận kích thước cụm nhỏ. |
| **CLM-LIM-002** | Tái lập API đảm bảo qua replay cache có mã băm SHA256. | `reports/final-tables/table4-resource-accounting.tsv` | 72 cache records | **PASS** | Phân biệt minh bạch giữa kết quả replay cache và fresh generation không bất biến. |

---

## 3. Thẩm định Các Tình huống Phản biện và Rủi ro Báo cáo

### 3.1. Rủi ro Phóng đại Nhân quả (Causal Chain Overclaim)
- **Kiểm tra:** Có câu nào trong báo cáo tuyên bố "RAG giải quyết triệt để root-cause trong thực tế" không?
- **Kết quả:** Không. Toàn bộ các phát biểu đều nêu rõ đây là bài toán định vị dịch vụ bị tiêm lỗi (offline fault localization) trên benchmark mô phỏng RE2-Online Boutique.

### 3.2. Rủi ro Nhầm lẫn Đơn vị Thống kê (Statistical Independence Confusion)
- **Kiểm tra:** Các repetition có bị tính như các mẫu độc lập riêng biệt không?
- **Kết quả:** Không. Báo cáo phân định rõ 18 incidents thuộc 6 họ lỗi (service×fault families), mỗi họ có 3 repetitions. Kỹ thuật bootstrap và Leave-One-Family-Out đều thực hiện ở cấp family.

### 3.3. Xử lý Ca Lỗi Nghiêm trọng (Handling of Severe Failure Modes)
- **Kiểm tra:** Ca `frontend` HTTP 500 (chỉ đạt 33.3% Top-1 accuracy) có bị che giấu hoặc loại bỏ không?
- **Kết quả:** Không. Ca này được giữ nguyên trong Bảng 3 và phân tích sâu sắc trong Báo cáo cuối cùng như một giới hạn tự nhiên của việc phân tích lỗi lan truyền qua RPC trong microservices.

### 3.4. Kiểm tra Trích dẫn Ảo giác (Hallucinated Citation Trapping)
- **Kiểm tra:** Hệ thống có cơ chế bẫy các trích dẫn giả định không?
- **Kết quả:** Đã thẩm định ca kiểm thử bẫy lỗi `case_04_invalid_citation` trong `case-audit.tsv`. Validator đã gắn cờ cảnh báo chính xác khi mã chunk không nằm trong context nạp vào prompt.

---

## 4. Kết luận Nghiệm thu Kiểm toán
Báo cáo Đồ án và Ma trận Bằng chứng đạt chuẩn nghiệm thu khoa học **G10-B**. Mọi số liệu báo cáo đều có nguồn gốc rõ ràng, kiểm chứng được bằng mã nguồn và dữ liệu lưu vết thực tế.
