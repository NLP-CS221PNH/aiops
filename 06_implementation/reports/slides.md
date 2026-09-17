> **Evaluation claims retracted, 2026-09-17.** All reported nDCG/MRR/Recall values, comparisons and winner claims below are historical proxy outputs, not accepted experimental results. Historical F1/F2 are invalid for evaluation; see `freezes/F2.provenance.json`. The plan completes readiness contracts only. Human G2 and evidence coverage remain unavailable.

# RETRACTED human-qrels claims

**RETRACTED 2026-09-17.** Any slide text below that says two humans judged 56 incidents is false. Current qrels are `llm_lexical_proxy`. See `docs/gold-type-contract.md`.

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
- **Core 56 Incidents:** planned human G2 (20/18/18). Current `annotations/qrels` files are `llm_lexical_proxy`, not two humans. See `freezes/F2.provenance.json`.

---

<!-- slide -->
## Slide 5: Phương pháp: Biểu diễn, Truy hồi & Sinh có Dẫn chứng

### Kiến trúc Đường ống (Pipeline Architecture)
1. **Biểu diễn sự cố:** Chuẩn hóa log, giữ nguyên service names, exceptions và HTTP codes.
2. **Truy hồi Kết hợp (Hybrid Retrieval):**
   - Nhánh từ khóa: BM25 ($k_1 = 1.2, b = 0.75$) — older $k_1=1.5$ citations are defects
   - Nhánh ngữ nghĩa: Dense `intfloat/e5-small-v2` (cosine similarity)
   - Hợp nhất: Reciprocal Rank Fusion ($c = 60$, candidate depth = 50 mỗi nhánh)
3. **Mô hình Sinh có Kiểm soát Ngân sách (Grounded Generator):**
   - Ngân sách context: Observations $\le 2048$ tokens, Knowledge $\le 4096$ tokens, Output $\le 768$ tokens.
   - 4 điều kiện đối chứng: **G0** (No-RAG), **GB** (BM25), **GD** (Dense), **GH** (Hybrid RRF). Decoding temperature $T = 0.1$ (lock). $T = 0.0$ in older drafts is a defect.

---

<!-- slide -->
## Slide 6: Giao thức Đóng băng & Thiết kế Đánh giá (F1/F2 Protocol)

### Trình tự Đóng băng Nghiêm ngặt
- **Mốc F1 (Plan 08):** Đóng băng toàn bộ cấu hình tiền xử lý, retriever, tokenizer, prompt template và evaluator trước khi chạm vào tập test.
- **Mốc F2:** existing `F2.json` bytes are historical and still say human. Authoritative record is `F2.provenance.json` (`llm_lexical_proxy`). A new human F2 is future plan 06 work.
- **Lựa chọn Baseline trên Dev:** Dev nDCG figures 0.642/0.618 were pasted, not scorer output. Headline IR is `NOT_RUN`. BM25 remains the protocol tie-break.
- **Chỉ số Đánh giá:**
  - Truy hồi: `passage nDCG@5` (chính), `MRR@10`, `Pooled Recall@20`.
  - Sinh: Top-1/Top-3 Service Accuracy, Citation Validity, Claim Support Precision, Abstention Rate.

---

<!-- slide -->
## Slide 7: Kết quả Thực nghiệm 1: Hiệu năng Truy hồi Thông tin (RQ2)

### Bảng 1: Hiệu năng Truy hồi trên tập Dev và Test (Eligible $n = 18$)

Headline IR is `NOT_RUN`. LLM-judge qrels; missing frozen rankings. Do not cite test IR-H nDCG as both 0.342 and 0.671.

See `reports/final-tables/table1-retrieval-performance.md`.

- **Kết luận RQ2:** Headline IR remains `NOT_RUN`. The older $\Delta = +0.043$ claim is a defect, not a finding. See `reports/final-tables/table1-retrieval-performance.md`.

---

<!-- slide -->
## Slide 8: Kết quả Thực nghiệm 2: Định vị Lỗi & Dẫn chứng (RQ3)

### Bảng 2: Chất lượng Sinh và Định vị trên 18 Test Incidents (72 Responses)

Headline generation is `NOT_RUN`. See `reports/final-tables/table2-generation-performance.md`. Past 72.2% / 97.2% / 85.2% cells are defects, not scorer output.

- **Kết luận RQ3:** Generator permission is pending. Mock provider success is not a result. Do not cite GH top-1, citation validity, or claim-support percentages as live findings.

---

<!-- slide -->
## Slide 9: Chẩn đoán 6 Họ Lỗi & Phân tích Độ nhạy (LOFO)

### Bảng 3: Hiệu năng trên 6 Họ lỗi Kiểm thử và Leave-One-Family-Out Sensitivity

Family diagnostics remain `NOT_RUN` until human G2 and frozen rankings exist. Historical LOFO cells (including $[+0.040, +0.046]$) are retracted with the 0.671/0.342 conflict.

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
- Cost/latency cells are `NOT_RUN`. No GPU hours or API spend are invented while generator permission is pending.

### Khả năng Tái lập (Reproducibility)
- Headline tables come from `python -m src.evaluation write-tables` (`src/evaluation`), not pasted literals.
- Hướng dẫn chạy lại: `docs/reproduce.md`.
- Current pytest count is not a frozen 302/302 claim; re-run `python -m pytest -q -o pythonpath=.` in `06_implementation`.

---

<!-- slide -->
## Slide 12: Kết luận & Giới hạn Nghiên cứu (Conclusions & Limitations)

### Kết luận Khoa học Cốt lõi
1. Methodology is locked at R2 + IR-B/IR-D/IR-H; knobs live in `configs/methodology-lock.yaml`. Headline IR/generation remain `NOT_RUN`.
2. Past $+4.3\%$, 72.2%, 97.2%, and 85.2% claims are retracted defects, not findings.
3. Labeled controls (G0, G-oracle, G-random, answerability, leakage) are documented in `reports/controls-mvp.md`. GraphRAG / multi-agent / IR-R / iterative retrieval stay deferred.

### Giới hạn & Hướng Phát triển
- Tập kiểm thử giới hạn ở 6 họ lỗi microservice; cần mở rộng sang các kiến trúc phân tán đa ngôn ngữ khác.
- Kết quả phản ánh việc định vị dịch vụ tiêm lỗi, chưa thay thế hoàn toàn chuỗi can thiệp nhân quả tự động trong production.
- **Khai báo:** Công cụ AI hỗ trợ lập trình khung và kiểm toán mã băm; toàn bộ quyết định khoa học do nhóm chịu trách nhiệm.

---

### *Xin trân trọng cảm ơn Thầy Cô và Hội đồng!*
*Q&A Session — Sẵn sàng trả lời các câu hỏi bảo vệ đồ án.*
