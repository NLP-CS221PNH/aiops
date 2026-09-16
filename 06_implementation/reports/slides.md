# Trình chiếu Báo cáo Đồ án CS221 (Slide Storyboard)

**Đề tài:** Phân loại sự cố và Hỗ trợ chẩn đoán nguyên nhân gốc cho Microservices bằng Hybrid RAG có Dẫn chứng  
*(Evidence-Grounded Incident Triage and Root-Cause Diagnosis for Microservices using Hybrid Retrieval-Augmented Generation)*  
**Nhóm thực hiện:** Nhóm CS221 AIOps (Thành viên A, B, C)  
**Thời lượng trình bày:** 10–12 phút · **Mốc nghiệm thu:** `G10-B`  

---

<!-- slide -->
## Slide 1: Giới thiệu Đề tài & Mục tiêu Nghiên cứu

### Phân loại Sự cố & Hỗ trợ Chẩn đoán Microservices bằng Hybrid RAG có Dẫn chứng
- **Khóa học:** CS221 — Natural Language Processing & Advanced Information Retrieval
- **Thành viên nhóm:**
  - **Thành viên A:** Dữ liệu, Chú thích & Khảo sát kho tri thức
  - **Thành viên B:** Mô hình, Thí nghiệm Truy hồi & Đánh giá Định lượng
  - **Thành viên C:** Tích hợp Hệ thống, Báo cáo & Đóng gói Bàn giao
- **Trọng tâm đề tài:** Xây dựng quy trình RAG đáng tin cậy cho dữ liệu vận hành hệ thống (AIOps), kết hợp từ khóa chính xác và ngữ nghĩa dày đặc, bảo đảm mọi kết luận đều có trích dẫn kiểm chứng được.

---

<!-- slide -->
## Slide 2: Vấn đề Thực tiễn & Ba Câu hỏi Nghiên cứu (RQs)

### Thách thức trong Vận hành Microservices (AIOps Triage)
- Một lỗi phần mềm (ví dụ: tràn bộ nhớ pod) có thể sinh ra hàng nghìn dòng log lỗi lan truyền qua mạng lưới microservice.
- LLM thông thường dễ bị **ảo giác (hallucination)** và đưa ra kết luận chẩn đoán sai lệch nhưng với giọng văn rất tự tin.
- Từ vựng trong log chứa nhiều mã lỗi kỹ thuật chuẩn xác (`HTTP 503`, `CrashLoopBackOff`) mà mô hình ngữ nghĩa dễ bỏ sót.

### Ba Câu hỏi Nghiên cứu (Research Questions)
1. **RQ1 (Representation):** Biểu diễn log bán cấu trúc thế nào để bảo toàn mã lỗi và tiết kiệm token?
2. **RQ2 (Retrieval):** Cơ chế Hybrid RRF có thực sự vượt trội hơn baseline đơn mạnh nhất trên tập dev theo chuẩn `passage nDCG@5` hay không?
3. **RQ3 (Grounded Generation):** Ngữ cảnh RAG có cải thiện độ chính xác chẩn đoán, độ hợp lệ trích dẫn và khả năng từ chối trả lời (abstention) hay không?

---

<!-- slide -->
## Slide 3: Tổng quan Nghiên cứu Liên quan (Related Work)

### Kế thừa và Khác biệt Khoa học
- **Benchmark AIOps (RCAEval - Wang et al., 2024):** Cung cấp dữ liệu đo từ xa RE2-Online Boutique; chúng tôi xây dựng mới toàn bộ tập passage qrels và giao thức đánh giá RAG có dẫn chứng.
- **Troubleshooting Copilot (Nissist - Ahmed et al., 2024):** Khai thác hướng dẫn vận hành (TSG) làm bằng chứng; chúng tôi chuẩn hóa trên kho tri thức mở và độc lập.
- **Truy hồi Kết hợp (BM25 + DPR + RRF):** Tận dụng thế mạnh kép: BM25 khớp chính xác định danh kỹ thuật, E5-small-v2 bao quát ngữ nghĩa khái niệm.
- **Đánh giá Trích dẫn & Grounding (ALCE - Gao et al., 2023):** Phân tách nghiêm ngặt giữa việc trích dẫn tồn tại (`citation validity`) và nội dung có thực sự hỗ trợ nhận định (`claim support`).

---

<!-- slide -->
## Slide 4: Kiến trúc Dữ liệu & Phòng chống Rò rỉ (Leakage Prevention)

### Dữ liệu Sự cố & Nguyên tắc Phân chia
- **90 sự cố** phân bố trên **30 service×fault families**, mỗi family đúng 3 lần lặp (repetitions).
- **Phân chia Split:** 54 train (18 families) / 18 dev (6 families) / 18 test (6 families).
- **Chống rò rỉ phân phối (No Leakage):** Phân chia chặt chẽ ở cấp **family**, tuyệt đối không chia ngẫu nhiên ở cấp incident để tránh các lần lặp của cùng họ lỗi xuất hiện ở cả train và test.

### Kho Tri thức & Nhãn Chú thích Con người
- **Corpus lịch sử:** 74 tài liệu, 580 chunks chuẩn hóa codepoint offsets tiền 2024.
- **Core 56 Incidents:** 20 train, 18 dev, 18 test được chấm đôi độc lập bởi 2 người và phân xử bởi người thứ 3 (adjudication) theo `rubric-v1.md`.

---

<!-- slide -->
## Slide 5: Phương pháp: Biểu diễn, Truy hồi & Sinh có Dẫn chứng

### Kiến trúc Đường ống (Pipeline Architecture)
1. **Biểu diễn sự cố:** Chuẩn hóa log, giữ nguyên service names, exceptions và HTTP codes.
2. **Truy hồi Kết hợp (Hybrid Retrieval):**
   - Nhánh từ khóa: BM25 ($k_1 = 1.5, b = 0.75$)
   - Nhánh ngữ nghĩa: Dense `intfloat/e5-small-v2` (cosine similarity)
   - Hợp nhất: Reciprocal Rank Fusion ($c = 60$, candidate depth = 50 mỗi nhánh)
3. **Mô hình Sinh có Kiểm soát Ngân sách (Grounded Generator):**
   - Ngân sách context: Observations $\le 2048$ tokens, Knowledge $\le 4096$ tokens, Output $\le 768$ tokens.
   - 4 điều kiện đối chứng: **G0** (No-RAG), **GB** (BM25), **GD** (Dense), **GH** (Hybrid RRF). Giải mã deterministic ($T = 0.0$).

---

<!-- slide -->
## Slide 6: Giao thức Đóng băng & Thiết kế Đánh giá (F1/F2 Protocol)

### Trình tự Đóng băng Nghiêm ngặt
- **Mốc F1 (Plan 08):** Đóng băng toàn bộ cấu hình tiền xử lý, retriever, tokenizer, prompt template và evaluator trước khi chạm vào tập test.
- **Mốc F2 (Plan 06):** Đóng băng qrels test sau khi hoàn tất chấm đôi và phân xử con người.
- **Lựa chọn Baseline trên Dev:** Trên tập dev, BM25 đạt 0.642 so với Dense 0.618 $\rightarrow$ BM25 được khóa làm **Stronger Dev Single Comparator**.
- **Chỉ số Đánh giá:**
  - Truy hồi: `passage nDCG@5` (chính), `MRR@10`, `Pooled Recall@20`.
  - Sinh: Top-1/Top-3 Service Accuracy, Citation Validity, Claim Support Precision, Abstention Rate.

---

<!-- slide -->
## Slide 7: Kết quả Thực nghiệm 1: Hiệu năng Truy hồi Thông tin (RQ2)

### Bảng 1: Hiệu năng Truy hồi trên tập Dev và Test (Eligible $n = 18$)

| Bộ truy hồi | Tập | passage nDCG@5 | MRR@10 | Recall@20 | Paired Delta vs. BM25 | 95% Bootstrap CI |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **IR-B (BM25)** | Dev | 0.642 | 0.725 | 0.820 | *Baseline* | — |
| **IR-D (Dense E5)** | Dev | 0.618 | 0.684 | 0.785 | -0.024 | [-0.052, +0.004] |
| **IR-H (Hybrid RRF)** | Dev | 0.684 | 0.769 | 0.871 | +0.042 | [+0.011, +0.073] |
| **IR-B (BM25)** | Test | 0.628 | 0.714 | 0.812 | *Baseline* | — |
| **IR-D (Dense E5)** | Test | 0.594 | 0.667 | 0.765 | -0.034 | [-0.068, +0.001] |
| **IR-H (Hybrid RRF)** | Test | **0.671** | **0.758** | **0.864** | **+0.043** | **[+0.008, +0.078]** |

- **Kết luận RQ2:** Hybrid RRF vượt trội hơn baseline đơn mạnh nhất một khoảng statistically positive $\Delta = +0.043$ ($+4.3\%$), với khoảng tin cậy 95% bootstrap theo cụm luôn dương.

---

<!-- slide -->
## Slide 8: Kết quả Thực nghiệm 2: Định vị Lỗi & Dẫn chứng (RQ3)

### Bảng 2: Chất lượng Sinh và Định vị trên 18 Test Incidents (72 Responses)

| Điều kiện Sinh | Top-1 Service Accuracy | Top-3 Service Accuracy | Citation Validity (%) | Claim Support Precision (%) | Tỉ lệ Từ chối (Abstain %) |
|---|:---:|:---:|:---:|:---:|:---:|
| **G0 (No-RAG)** | 38.9% (7/18) | 61.1% (11/18) | *N/A* | 41.2% (14/34) | 22.2% (4/18) |
| **GB (BM25 RAG)** | 61.1% (11/18) | 77.8% (14/18) | 94.4% (34/36) | 78.6% (33/42) | 11.1% (2/18) |
| **GD (Dense RAG)** | 55.6% (10/18) | 72.2% (13/18) | 91.7% (33/36) | 73.5% (25/34) | 11.1% (2/18) |
| **GH (Hybrid RAG)** | **72.2% (13/18)** | **88.9% (16/18)** | **97.2% (35/36)** | **85.2% (46/54)** | 5.6% (1/18) |

- **Kết luận RQ3:**
  - Hybrid RAG tăng vọt độ chính xác định vị service từ **38.9%** lên **72.2%** (+33.3% absolute gain).
  - Tỉ lệ mệnh đề chẩn đoán có căn cứ hỗ trợ tăng hơn gấp đôi (từ 41.2% lên **85.2%**).
  - Ảo giác trích dẫn bị triệt tiêu gần như hoàn toàn (97.2% citation validity).

---

<!-- slide -->
## Slide 9: Chẩn đoán 6 Họ Lỗi & Phân tích Độ nhạy (LOFO)

### Bảng 3: Hiệu năng trên 6 Họ lỗi Kiểm thử và Leave-One-Family-Out Sensitivity

| Family ID | Dịch vụ mục tiêu | Dạng lỗi tiêm | IR-H nDCG | Paired Delta ($\Delta$) | GH Top-1 Accuracy | LOFO Macro Delta |
|---|---|---|:---:|:---:|:---:|:---:|
| `FAM-TEST-01` | `cartservice` | CPU Throttle | 0.724 | +0.057 | 100% (3/3) | +0.040 |
| `FAM-TEST-02` | `paymentservice` | Network Latency | 0.631 | +0.042 | 66.7% (2/3) | +0.043 |
| `FAM-TEST-03` | `checkoutservice` | Pod Failure / Crash | 0.748 | +0.046 | 100% (3/3) | +0.042 |
| `FAM-TEST-04` | `frontend` | HTTP 500 Error | 0.569 | +0.026 | 33.3% (1/3) | +0.046 |
| `FAM-TEST-05` | `emailservice` | Memory Pressure | 0.655 | +0.040 | 66.7% (2/3) | +0.044 |
| `FAM-TEST-06` | `redis-cart` | Connection Timeout | 0.699 | +0.048 | 66.7% (2/3) | +0.042 |

- **Tính ổn định của LOFO:** Loại trừ bất kỳ họ lỗi nào, $\Delta$ vĩ mô vẫn dao động hẹp trong khoảng $[+0.040, +0.046]$.
- **Thách thức tại `frontend` (`FAM-TEST-04`):** Lỗi lan truyền qua RPC khiến mô hình dễ nhầm lẫn giữa dịch vụ gọi và dịch vụ bị lỗi gốc (Top-1 chỉ đạt 33.3%).

---

<!-- slide -->
## Slide 10: Phân tích Ca Lỗi Thực tế (Case Studies từ Demo Viewer)

### Kiểm toán 5 Ca Sự cố Điển hình (`case-audit.tsv`)
1. **Grounded Success (`run_gh_redis`):** Nhánh BM25 tìm đúng cấu hình `redis.conf`, nhánh Dense tìm runbook nghẽn mạng $\rightarrow$ chẩn đoán chuẩn xác 100%.
2. **Low-Confidence Grounded (`run_gb_email`):** Chỉ tìm thấy tài liệu chung chung $\rightarrow$ mô hình định vị đúng nhưng tự động hạ cờ `confidence: low`.
3. **Safe Abstention (`run_g0_recommendation`):** Thiếu dữ liệu log và tài liệu $\rightarrow$ mô hình chủ động từ chối (`abstain: true`) thay vì bịa đặt nguyên nhân.
4. **Trapped Invalid Citation (`run_gd_invalid_citation`):** Mô hình bịa trích dẫn ngoài context $\rightarrow$ Validator tự động phát hiện vi phạm và chặn cảnh báo.
5. **So sánh Đối chứng (`run_gb_redis` vs. `run_gh_redis`):** GH khắc phục hoàn toàn thiếu sót về mối liên hệ bộ đệm I/O mà GB đơn lẻ bỏ quên.

---

<!-- slide -->
## Slide 11: Hạch toán Tài nguyên, Khả năng Tái lập & Kiểm thử

### Bảng 4: Chi phí, Độ trễ và Tài nguyên Hệ thống
- **Độ trễ trung bình:** 1.12s (G0) $\rightarrow$ 2.15s (GH). Mức tăng 1.03s hoàn toàn nằm trong SLA vận hành (< 5s).
- **Tổng chi phí API:** \$0.114 cho toàn bộ 72 lượt chạy kiểm thử test set.
- **Tỉ lệ lỗi hệ thống:** 0 ca crash chết luồng.

### Khả năng Tái lập Tuyệt đối (Reproducibility)
- Toàn bộ 302/302 automated unit & contract tests đã chạy và vượt qua 100%.
- Bảng số liệu được sinh trực tiếp bằng code từ các artifacts đã băm SHA256.
- Hướng dẫn chạy lại từng bước chi tiết tại `docs/reproduce.md`.

---

<!-- slide -->
## Slide 12: Kết luận & Giới hạn Nghiên cứu (Conclusions & Limitations)

### Kết luận Khoa học Cốt lõi
1. **Hybrid RRF mang lại ưu thế thực chất:** Đạt hiệu số $+4.3\%$ so với BM25 trên tập test, kết hợp hiệu quả giữa mã lỗi kỹ thuật và ngữ nghĩa chẩn đoán.
2. **RAG giải quyết bài toán ảo giác:** Nâng độ chính xác định vị lên **72.2%**, đạt **97.2%** trích dẫn hợp lệ và **85.2%** nhận định có căn cứ.
3. **Tính an toàn vận hành:** Cơ chế phát hiện trích dẫn giả mạo và từ chối trả lời (abstention) bảo vệ an toàn cho kỹ sư SRE.

### Giới hạn & Hướng Phát triển
- Tập kiểm thử giới hạn ở 6 họ lỗi microservice; cần mở rộng sang các kiến trúc phân tán đa ngôn ngữ khác.
- Kết quả phản ánh việc định vị dịch vụ tiêm lỗi, chưa thay thế hoàn toàn chuỗi can thiệp nhân quả tự động trong production.
- **Khai báo:** Công cụ AI hỗ trợ lập trình khung và kiểm toán mã băm; toàn bộ quyết định khoa học do nhóm chịu trách nhiệm.

---

### *Xin trân trọng cảm ơn Thầy Cô và Hội đồng!*
*Q&A Session — Sẵn sàng trả lời các câu hỏi bảo vệ đồ án.*
