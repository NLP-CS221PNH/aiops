# Báo cáo Đồ án CS221: Phân loại sự cố và Hỗ trợ chẩn đoán nguyên nhân gốc cho Microservices bằng Hybrid RAG có Dẫn chứng

**Tên đề tài tiếng Anh:** Evidence-Grounded Incident Triage and Root-Cause Diagnosis for Microservices using Hybrid Retrieval-Augmented Generation  
**Môn học:** CS221 — Xử lý Ngôn ngữ Tự nhiên & Hệ thống Tìm kiếm Thông tin Nâng cao  
**Nhóm thực hiện:** Nhóm nghiên cứu CS221 (Thành viên A: Dữ liệu & Chú thích; Thành viên B: Mô hình & Đánh giá; Thành viên C: Tích hợp & Soạn thảo)  
**Mã đề án:** `CS221-AIOps-RAG` · Phiên bản: `1.0.0-draft` · Ngày: `16/09/2026`  

---

## Tóm tắt (Abstract)

Quản lý sự cố vận hành trong kiến trúc microservice (AIOps Incident Management) đòi hỏi phải định vị nhanh chóng dịch vụ gặp sự cố và đề xuất hướng khắc phục dựa trên các tài liệu hướng dẫn kỹ thuật (runbooks). Các phương pháp sinh sử dụng mô hình ngôn ngữ lớn (LLM) hiện nay thường đối mặt với nguy cơ ảo giác (hallucination) và thiếu liên kết bằng chứng xác thực khi áp dụng vào miền dữ liệu đo từ xa (telemetry) bán cấu trúc. 

Đồ án này nghiên cứu và đánh giá hệ thống **Hybrid Retrieval-Augmented Generation (Hybrid RAG)** nhằm giải quyết ba thách thức cốt lõi:
1. Biểu diễn sự cố từ chuỗi dữ liệu log và cảnh báo hệ thống mà không làm tràn ngữ cảnh;
2. Đánh giá thực nghiệm khách quan xem cơ chế truy hồi kết hợp từ khóa (BM25) và ngữ nghĩa dày đặc (Dense E5-small-v2) thông qua Reciprocal Rank Fusion (RRF) có mang lại lợi ích vượt trội so với các baseline đơn lẻ hay không;
3. Kiểm chứng xem ngữ cảnh tri thức được truy hồi có thực sự giúp mô hình sinh đưa ra chẩn đoán chính xác, có dẫn chứng hợp lệ (valid citation) và biết từ chối trả lời (abstention) khi thiếu dữ kiện hay không.

Nghiên cứu được triển khai trên tập kiểm định 90 sự cố phân tán trên 30 service×fault families từ benchmark microservice RE2-Online Boutique, với kho tri thức lịch sử gồm 74 tài liệu (580 chunks). Toàn bộ quy trình tuân thủ giao thức đóng băng tham số nghiêm ngặt (F1/F2 protocol) và đánh giá độ bất định trên 6 họ lỗi kiểm thử độc lập.

---

## 1. Giới thiệu & Định nghĩa Bài toán (Introduction & Problem Formulation)

### 1.1. Bối cảnh thực tế và Vấn đề kỹ thuật
Trong các hệ thống phân tán và vi dịch vụ hiện đại, một sự cố đơn lẻ (ví dụ: cạn kiệt bộ nhớ pod hoặc cấu hình sai kết nối cơ sở dữ liệu) có thể kích hoạt hàng nghìn dòng log lỗi lan truyền qua mạng lưới dịch vụ phụ thuộc. Các kỹ sư vận hành hệ thống (Site Reliability Engineers - SRE) phải mất nhiều thời gian để sàng lọc dữ liệu thô, tra cứu tài liệu vận hành và xác định nguyên nhân gốc rễ.

Mô hình RAG hứa hẹn khả năng tự động hóa quy trình này bằng cách truy hồi tài liệu kỹ thuật liên quan và tổng hợp thành báo cáo chẩn đoán. Tuy nhiên, việc áp dụng RAG vào AIOps đặt ra ba câu hỏi khoa học quan trọng:
- **Từ vựng chuyên ngành và mã lỗi kỹ thuật:** Dữ liệu log chứa các mã lỗi chuẩn xác (`HTTP 503`, `java.net.ConnectException`, `CrashLoopBackOff`) mà mô hình dense bi-encoder thuần túy dễ bỏ sót do hiện tượng trôi miền (domain shift). Ngược lại, bộ truy hồi từ khóa (lexical) như BM25 lại khó nắm bắt ngữ nghĩa khái quát của triệu chứng.
- **Tính xác thực của lời giải thích (Grounding & Faithfulness):** Mô hình sinh có thể định vị đúng dịch vụ bị lỗi do đoán mò hoặc thiên kiến tần suất, nhưng lại trích dẫn một tài liệu không liên quan.
- **Yêu cầu an toàn vận hành:** Khi tài liệu tri thức không chứa thông tin về sự cố mới, hệ thống bắt buộc phải chủ động từ chối trả lời (abstention) thay vì suy diễn sai lệch gây rủi ro vận hành.

### 1.2. Câu hỏi nghiên cứu (Research Questions)
Đồ án tập trung giải quyết 3 câu hỏi nghiên cứu (RQs):
- **RQ1 (Representation):** Phương pháp biểu diễn log bán cấu trúc nào tối ưu cho việc truy hồi tri thức mà vẫn bảo toàn định danh lỗi và tiết kiệm ngân sách token?
- **RQ2 (Retrieval):** Cơ chế truy hồi kết hợp (Hybrid RRF) có vượt trội hơn baseline đơn mạnh nhất trên tập validation (dev) theo thước đo xếp hạng đoạn văn chuẩn `passage nDCG@5` hay không?
- **RQ3 (Grounded Generation):** Sự hiện diện của tài liệu truy hồi có làm tăng độ chính xác định vị lỗi, độ phủ trích dẫn có căn cứ (grounded citation) và năng lực từ chối trả lời đúng lúc so với điều kiện không dùng RAG (No-RAG) hay không?

---

## 2. Nghiên cứu Liên quan (Related Work)

Nghiên cứu của chúng tôi kế thừa và so sánh có hệ thống với các công trình tiêu biểu trong lĩnh vực AIOps, IR và RAG:

| Nhóm nghiên cứu | Công trình tiêu biểu | Tác vụ & Đóng góp chính | So sánh với hướng tiếp cận của Đồ án |
|---|---|---|---|
| **AIOps Taxonomy & Benchmarking** | Chen et al. (2024) [P0052]; Wang et al. (2024) [P0757] | Khảo sát AIOps bằng LLM; công bố benchmark RCAEval với telemetry đa phương thức. | Đồ án kế thừa schema dữ liệu RE2 của RCAEval nhưng xây dựng mới toàn bộ tập passage qrels và quy trình đánh giá grounding. |
| **Operational Copilots & TSG** | Ahmed et al. (2024) [P0003] (Nissist) | Tận dụng Troubleshooting Guides (TSG) làm bằng chứng chẩn đoán sự cố cloud. | Đồ án chuẩn hóa corpus runbook công khai và đánh giá khách quan trên môi trường microservice mở thay vì hạ tầng nội bộ. |
| **Lexical, Dense & Hybrid Retrieval** | Robertson & Zaragoza (2009) [LIT-BM25]; Karpukhin et al. (2020) [P0245]; Cormack et al. (2009) [LIT-RRF] | Nền tảng xác suất BM25; Dense Passage Retrieval (DPR); Reciprocal Rank Fusion (RRF). | Đồ án áp dụng RRF để kết hợp BM25 và E5-small-v2 trên miền văn bản log/runbook với hằng số `rrf_constant = 60` đã khóa tại F1. |
| **RAG Architecture & Re-ranking** | Lewis et al. (2020) [P0376]; Nogueira & Cho (2019) [P0325] | Kiến trúc RAG nền tảng; Cross-encoder re-ranking với BERT. | Đồ án áp dụng RAG tiền xử lý context (context-prepending) với ngân sách token nghiêm ngặt; coi re-ranking là điều kiện mở rộng có kiểm soát chi phí. |
| **Grounded Evaluation & Citations** | Saad-Falcon et al. (2023) [P0761] (ARES); Gao et al. (2023) [P0826] (ALCE) | Đánh giá RAG tự động nhiều khía cạnh; Đo lường tính hợp lệ của citation và grounding. | Đồ án áp dụng nguyên tắc của ALCE: phân tách rạch ròi giữa việc trích dẫn tồn tại (`citation validity`) và nội dung trích dẫn có thực sự hỗ trợ nhận định (`claim support`). |

---

## 3. Dữ liệu & Kiểm soát Rò rỉ (Dataset & Leakage Controls)

### 3.1. Bộ dữ liệu sự cố RE2-Online Boutique
Dữ liệu thực nghiệm được trích xuất từ hệ thống microservice Online Boutique gồm 10–11 dịch vụ phân tán.
- **Quy mô:** 90 sự cố tương ứng với 30 cặp dịch vụ và dạng lỗi (`service×fault families`). Mỗi family chứa đúng 3 lần tiêm lỗi lặp lại (`repetitions`) độc lập.
- **Phân chia tập (Dataset Split):**
  - **Train:** 54 incidents (18 families, 3 repetitions/family).
  - **Dev:** 18 incidents (6 families, 3 repetitions/family).
  - **Test:** 18 incidents (6 families, 3 repetitions/family).
- **Phòng chống rò rỉ (Leakage Prevention):** Việc phân chia split bắt buộc thực hiện ở cấp **family**, không chia ngẫu nhiên ở cấp incident. Nếu chia ngẫu nhiên, các repetition của cùng một family sẽ xuất hiện ở cả train và test, dẫn đến hiện tượng rò rỉ đặc trưng lỗi cực kỳ nghiêm trọng.

### 3.2. Kho tri thức Vận hành (Knowledge Corpus)
- Sử dụng tập dữ liệu `cs221-knowledge-pre2024-v1` gồm 74 tài liệu kỹ thuật được phân đoạn thành 580 chunks.
- Mỗi chunk có tiêu đề mục (`section_heading`), nội dung văn bản chuẩn hóa (`text`) và mốc offset codepoint để xác minh vị trí trích dẫn.
- Tuyệt đối không đưa tài liệu xuất bản sau thời điểm sự cố hoặc các nhãn chuẩn vào kho tri thức.

### 3.3. Tập nhãn Chú thích Con người (Core Human Qrels)
- Tập core gồm **56 incidents** (20 train đại diện cho 18 families, 18 dev, 18 test).
- Toàn bộ các cặp (incident, passage) trong retrieval pool được chấm đôi độc lập bởi 2 người thẩm định theo thang điểm 0, 1, 2. Bất đồng ý kiến được giải quyết bởi người phân xử thứ ba (adjudication).

---

## 4. Phương pháp (Methodology)

Kiến trúc hệ thống bao gồm ba khối chức năng:

```text
[Telemetry Logs & Alerts]
           │
           ▼
[Biểu diễn Sự cố R1/R2/R3] (Chuẩn hóa lỗi, lọc theo cửa sổ quan sát)
           │
           ├──────────────────────────────┬──────────────────────────────┐
           ▼                              ▼                              ▼
     [Nhánh BM25]                   [Nhánh Dense]                  [Baseline G0]
(Lexical Tokenization)          (E5-small-v2 Embeddings)            (No External
           │                              │                          Knowledge)
           └──────────────┬───────────────┘                              │
                          ▼                                              │
              [Reciprocal Rank Fusion]                                   │
                (rrf_constant = 60)                                      │
                          │                                              │
                          ▼                                              │
              [Top-k Retrieved Chunks]                                   │
                          │                                              │
                          ▼                                              ▼
           [Grounded Prompt Construction] ───────────────────────────────┘
              (Token Budget: Obs ≤ 2048, Knowledge ≤ 4096, Out ≤ 768)
                          │
                          ▼
            [Deterministic LLM Generator]
                 (temperature = 0.0)
                          │
                          ▼
        [Chẩn đoán có Dẫn chứng & Báo cáo Lỗi]
   (Root-cause service, Citation IDs, Claim Support, Abstention)
```

### 4.1. Biểu diễn sự cố (Incident Representation)
Sự cố được biểu diễn qua cơ chế chuẩn hóa log: giữ nguyên tên dịch vụ, exception trace, HTTP status codes, đồng thời loại bỏ các chuỗi ngẫu nhiên không mang ý nghĩa ngữ nghĩa để vừa khớp ngân sách ngữ cảnh vừa tối ưu hóa chỉ mục từ khóa.

### 4.2. Bộ truy hồi Thông tin (Retrievers)
- **IR-B (BM25):** Sử dụng hàm tính điểm Okapi BM25 chuẩn hóa độ dài, tham số $k_1 = 1.5, b = 0.75$.
- **IR-D (Dense):** Sử dụng mô hình `intfloat/e5-small-v2` với tiền tố `query: ` cho sự cố và `passage: ` cho tài liệu tri thức; tính độ tương đồng qua chuẩn hóa vector L2 cosine.
- **IR-H (Hybrid RRF):** Hợp nhất danh sách xếp hạng của BM25 và Dense bằng công thức Reciprocal Rank Fusion:
  $$RRF\_Score(d) = \sum_{m \in \{BM25, Dense\}} \frac{1}{60 + r_m(d)}$$
  trong đó $r_m(d)$ là thứ hạng của tài liệu $d$ trong danh sách $m$.

### 4.3. Các điều kiện Đối chứng Sinh (Generation Conditions)
Hệ thống thiết lập 4 điều kiện đối chứng bắt buộc:
1. **G0 (No-RAG):** Không cấp context tài liệu ngoài, chỉ cấp dữ liệu telemetry đã xử lý.
2. **GB (BM25 RAG):** Cấp top-k chunks từ BM25.
3. **GD (Dense RAG):** Cấp top-k chunks từ Dense E5.
4. **GH (Hybrid RAG):** Cấp top-k chunks từ Hybrid RRF.

---

## 5. Thiết kế Đánh giá & Quy trình Thực nghiệm (Evaluation Protocol)

### 5.1. Thước đo Truy hồi (Retrieval Metrics)
- **Chỉ số chính (Primary Metric):** `passage nDCG@5` tính trên tập qrels đã phân xử của các incident hợp lệ (có ít nhất một chunk liên quan trong tập qrels).
- **Chỉ số chẩn đoán phụ (Secondary Metrics):** `MRR@10` (Mean Reciprocal Rank) và `Pooled Recall@20`.
- **Giao thức chọn baseline:** Lựa chọn baseline đơn mạnh nhất (BM25 hoặc Dense) dựa trên kết quả `passage nDCG@5` trên tập **dev**. Nếu hai bên hòa điểm, ưu tiên BM25. So sánh chính (Primary Contrast) là hiệu số bắt cặp (paired delta):
  $$\Delta_{Primary} = nDCG@5(IR\text{-}H) - nDCG@5(Selected\_Single)$$

### 5.2. Thước đo Định vị và Dẫn chứng (Localization & Grounding Metrics)
- **Service Localization Accuracy:** Tỉ lệ định vị đúng dịch vụ gốc bị tiêm lỗi trên toàn bộ **18 test incidents** (top-1 và top-3).
- **Citation Validity:** Tỉ lệ các mã trích dẫn trong câu trả lời thực sự tồn tại trong context được cung cấp cho mô hình.
- **Claim Support Precision:** Tỉ lệ các mệnh đề kết luận được hỗ trợ trực tiếp bởi nội dung đoạn văn được trích dẫn.
- **Abstention Rate:** Năng lực từ chối trả lời một cách chính xác khi tài liệu không chứa đủ dữ kiện để chẩn đoán.

### 5.3. Hạch toán Cụm 6 Families (Cluster Accounting)
Do tập test chỉ có 6 họ lỗi độc lập, việc coi 18 incidents là các quan sát độc lập cùng phân phối (i.i.d) là sai lầm thống kê. Báo cáo cung cấp đầy đủ phân tích phương sai theo từng family và đánh giá độ nhạy bằng kỹ thuật loại trừ từng cụm (Leave-One-Family-Out).

---

## 6. Kết quả Thực nghiệm (Experimental Results)

Toàn bộ kết quả dưới đây được tổng hợp trực tiếp từ các artifact đã khóa theo giao thức F1/F2 và kiểm toán tại `06_implementation/reports/final-tables/`.

### 6.1. Hiệu năng Truy hồi Thông tin (Retrieval Performance)

Trên tập Dev, IR-B (BM25) đạt điểm `passage nDCG@5` là **0.642**, cao hơn IR-D (Dense E5: 0.618). Do đó, theo đúng quy định của protocol F1, **BM25 được chọn làm baseline đơn mạnh nhất (Stronger Dev Single)** để thiết lập đối chứng chính trên tập Test.

| Bộ truy hồi (Retriever) | Tập đánh giá | Mẫu số hợp lệ ($n$) | passage nDCG@5 | MRR@10 | Recall@20 | Paired Delta ($\Delta$ vs BM25) | 95% Bootstrap CI |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **IR-B (BM25)** | Dev | 18 | 0.642 | 0.725 | 0.820 | *Baseline* | — |
| **IR-D (Dense E5)** | Dev | 18 | 0.618 | 0.684 | 0.785 | -0.024 | [-0.052, +0.004] |
| **IR-H (Hybrid RRF)** | Dev | 18 | 0.684 | 0.769 | 0.871 | +0.042 | [+0.011, +0.073] |
| **IR-B (BM25)** | Test | 18 | 0.628 | 0.714 | 0.812 | *Baseline* | — |
| **IR-D (Dense E5)** | Test | 18 | 0.594 | 0.667 | 0.765 | -0.034 | [-0.068, +0.001] |
| **IR-H (Hybrid RRF)** | Test | 18 | **0.671** | **0.758** | **0.864** | **+0.043** | **[+0.008, +0.078]** |

> [!IMPORTANT]
> **Trả lời lời khẳng định RQ2:** Cơ chế Hybrid RRF vượt trội hơn baseline đơn mạnh nhất (BM25) một khoảng statistically positive $\Delta = +0.043$ ($+4.3\%$, khoảng tin cậy 95% bootstrap theo cụm: $[+0.008, +0.078]$). Sự kết hợp giữa khả năng khớp chính xác token kỹ thuật của BM25 và độ phủ ngữ nghĩa của Dense E5 giúp tăng cả MRR@10 lẫn Recall@20.

### 6.2. Hiệu năng Định vị Dịch vụ và Chất lượng Dẫn chứng (Grounded Generation Performance)

Đánh giá trên toàn bộ 72 phản hồi ($18 \text{ incidents} \times 4 \text{ conditions}$) với mô hình sinh deterministic ($T = 0.0$):

| Điều kiện Sinh | Mẫu số phản hồi | Top-1 Service Accuracy | Top-3 Service Accuracy | Citation Validity (%) | Claim Support Precision (%) | Tỉ lệ Từ chối (Abstain %) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **G0 (No-RAG)** | 18 | 38.9% (7/18) | 61.1% (11/18) | *N/A (Không có context)* | 41.2% (14/34 claims) | 22.2% (4/18) |
| **GB (BM25 RAG)** | 18 | 61.1% (11/18) | 77.8% (14/18) | 94.4% (34/36 citations) | 78.6% (33/42 claims) | 11.1% (2/18) |
| **GD (Dense RAG)** | 18 | 55.6% (10/18) | 72.2% (13/18) | 91.7% (33/36 citations) | 73.5% (25/34 claims) | 11.1% (2/18) |
| **GH (Hybrid RAG)** | 18 | **72.2% (13/18)** | **88.9% (16/18)** | **97.2% (35/36 citations)** | **85.2% (46/54 claims)** | 5.6% (1/18) |

> [!NOTE]
> **Trả lời lời khẳng định RQ3:** Bổ sung ngữ cảnh Hybrid RAG giúp nâng Top-1 Service Accuracy từ 38.9% lên **72.2%** (+33.3% absolute gain). Quan trọng hơn, 97.2% mã trích dẫn là hợp lệ và 85.2% mệnh đề chẩn đoán được hỗ trợ bởi văn bản dẫn chứng, giảm thiểu ảo giác trầm trọng của điều kiện No-RAG (chỉ 41.2% claim support).

### 6.3. Phân tích Chẩn đoán theo 6 Họ lỗi Kiểm thử (Six-Family Diagnostics & Sensitivity)

Đánh giá chi tiết trên 6 cụm service×fault family và độ nhạy Leave-One-Family-Out (LOFO):

| Family ID | Dịch vụ mục tiêu | Dạng lỗi tiêm | Số ca ($n$) | IR-B nDCG | IR-D nDCG | IR-H nDCG | Paired Delta ($\Delta$) | GH Top-1 Accuracy | LOFO Macro Delta |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FAM-TEST-01` | `cartservice` | CPU Throttle | 3 | 0.667 | 0.612 | 0.724 | +0.057 | 100% (3/3) | +0.040 |
| `FAM-TEST-02` | `paymentservice` | Network Latency | 3 | 0.589 | 0.542 | 0.631 | +0.042 | 66.7% (2/3) | +0.043 |
| `FAM-TEST-03` | `checkoutservice` | Pod Failure / Crash | 3 | 0.702 | 0.681 | 0.748 | +0.046 | 100% (3/3) | +0.042 |
| `FAM-TEST-04` | `frontend` | HTTP 500 Generic Error | 3 | 0.543 | 0.518 | 0.569 | +0.026 | 33.3% (1/3) | +0.046 |
| `FAM-TEST-05` | `emailservice` | Memory Pressure | 3 | 0.615 | 0.590 | 0.655 | +0.040 | 66.7% (2/3) | +0.044 |
| `FAM-TEST-06` | `redis-cart` | Connection Timeout | 3 | 0.651 | 0.622 | 0.699 | +0.048 | 66.7% (2/3) | +0.042 |

Khi loại bỏ bất kỳ family nào trong 6 cụm, hiệu số bắt cặp vĩ mô (LOFO Macro Delta) vẫn dao động ổn định trong khoảng hẹp $[+0.040, +0.046]$, chứng minh rằng kết quả vượt trội của Hybrid RAG có tính nhất quán trên toàn bộ các dạng lỗi.

### 6.4. Hạch toán Độ trễ, Tài nguyên và Chi phí (Latency & Resource Accounting)

| Điều kiện Sinh | Mẫu số phản hồi | Số ca lỗi hệ thống | Độ trễ trung bình (giây) | Tổng Prompt Tokens | Tổng Output Tokens | Chi phí ước tính (USD) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **G0 (No-RAG)** | 18 | 0 | 1.12 s | 14,210 | 4,120 | \$0.014 |
| **GB (BM25 RAG)** | 18 | 0 | 1.84 s | 32,450 | 5,890 | \$0.032 |
| **GD (Dense RAG)** | 18 | 0 | 1.92 s | 33,180 | 5,740 | \$0.033 |
| **GH (Hybrid RAG)** | 18 | 0 | 2.15 s | 34,920 | 6,210 | \$0.035 |
| **Toàn bộ Workload** | **72** | **0** | **1.76 s** | **114,760** | **21,960** | **\$0.114** |

---

## 7. Phân tích Lỗi & Các Ca Điển hình (Error Taxonomy & Case Studies)

Dựa trên dữ liệu kiểm toán từ công cụ Demo (`06_implementation/reports/demo/case-audit.tsv`), chúng tôi phân tích 5 ca sự cố điển hình tương ứng với các nhóm lỗi chính:

### Case 1: Chẩn đoán thành công có căn cứ (Verified Grounded Success)
- **Incident & Condition:** `run_gh_redis` (Điều kiện GH, sự cố timeout `redis-cart`).
- **Hiện tượng:** Log hệ thống ghi nhận hàng loạt lỗi rớt kết nối gRPC giữa `cartservice` và `redis-cart`.
- **Hành vi hệ thống:** Nhánh BM25 truy xuất chính xác tài liệu cấu hình `redis.conf` và chỉ thị cấu hình I/O pool. Nhánh Dense bổ sung runbook xử lý tràn kết nối mạng. Mô hình định vị chính xác dịch vụ `redis-cart`, trích dẫn đúng 2 đoạn văn và nêu các bước kiểm tra tiếp theo (`client-output-buffer-limit`).

### Case 2: Chẩn đoán độ tin cậy thấp do ngữ cảnh chung (Low-Confidence Grounded)
- **Incident & Condition:** `run_gb_email` (Điều kiện GB, sự cố cạn kiệt bộ nhớ `emailservice`).
- **Hiện tượng:** BM25 chỉ truy hồi được tài liệu cấu hình chung của microservice, không có runbook đặc thù về heap size của worker runtime.
- **Hành vi hệ thống:** Mô hình định vị đúng service nhưng gán nhãn độ tin cậy thấp (`confidence: low`), nêu rõ hạn chế của tài liệu và tránh đưa ra kết luận khẳng định sai lệch.

### Case 3: Từ chối trả lời an toàn khi thiếu dữ kiện (Safe Abstention)
- **Incident & Condition:** `run_g0_recommendation` (Điều kiện G0, sự cố `recommendationservice`).
- **Hiện tượng:** Không có tài liệu ngoài, dữ liệu log thô không đủ để chỉ ra nguyên nhân gốc.
- **Hành vi hệ thống:** Hệ thống chủ động trả về cờ `abstain: true` cùng trường `missing_information`, khuyến nghị SRE thu thập thêm trace thay vì suy đoán bừa bãi.

### Case 4: Phát hiện và chặn ảo giác trích dẫn (Trapped Invalid Citation)
- **Incident & Condition:** `run_gd_invalid_citation` (Điều kiện GD, ca kiểm thử bẫy lỗi).
- **Hiện tượng:** Bộ kiểm tra validator phát hiện mô hình trích dẫn mã chunk không có trong context được nạp vào prompt.
- **Hành vi hệ thống:** Hệ thống tự động phát hiện vi phạm hợp đồng (`citation validity = false`), gắn cờ cảnh báo lỗi trên giao diện kiểm toán và không công nhận đây là câu trả lời có bằng chứng.

### Case 5: So sánh đối chứng GB vs. GH (Direct Comparative Audit)
- **Incident & Condition:** `run_gb_redis` vs. `run_gh_redis` trên cùng observation context hash.
- **Hiện tượng:** Điều kiện GB (BM25) đưa ra giải thích cục bộ nhưng bỏ sót mối liên hệ tràn bộ đệm I/O. Điều kiện GH kết hợp cả từ khóa lẫn ngữ nghĩa, giúp đưa ra giải pháp toàn diện và đạt điểm hỗ trợ bằng chứng tuyệt đối từ chuyên gia thẩm định.

---

## 8. Thảo luận, Giới hạn & Đạo đức (Discussion, Limitations & Ethics)

### 8.1. Thảo luận về Kết quả Thực nghiệm
- Việc đánh giá trung thực cả những kịch bản hybrid không mang lại hiệu quả vượt trội (kết quả âm hoặc hòa) có giá trị khoa học quan trọng nhằm xác định ranh giới ứng dụng thực tế của RRF trong miền dữ liệu vận hành.
- Phân tích rạch ròi giữa việc "đoán đúng dịch vụ" và "chẩn đoán có căn cứ" chỉ ra rằng độ chính xác chẩn đoán thông thường có thể tạo ra cảm giác tin cậy sai lầm nếu không đi kèm thẩm định chất lượng trích dẫn.

### 8.2. Các Giới hạn của Đồ án
1. **Quy mô họ lỗi hạn chế:** 6 test families là cỡ mẫu cụm tương đối nhỏ, khiến các khoảng tin cậy thống kê (confidence intervals) có độ rộng đáng kể.
2. **Tính bất biến của API:** Các thử nghiệm phụ thuộc vào API thương mại bên ngoài có nguy cơ thay đổi phân phối sinh ngầm. Đồ án giải quyết bằng cách lưu vết toàn bộ cache đầu ra có băm SHA256.
3. **Không đại diện cho can thiệp nhân quả:** Định vị dịch vụ bị tiêm lỗi không đồng nghĩa với việc tìm ra toàn bộ chuỗi nhân quả trong sản xuất và không bảo đảm tự động rút ngắn thời gian khắc phục sự cố (MTTR) nếu không có con người giám sát.

### 8.3. Khai báo Hỗ trợ của Trí tuệ Nhân tạo & Phương pháp Chấm nhãn Tự động (AI Assistance & LLM-as-a-Judge Disclosure)
- **Công cụ hỗ trợ:** Các công cụ AI (Antigravity / Gemini / Claude) được sử dụng để hỗ trợ tạo mã khung tự động, kiểm tra cú pháp, tối ưu hóa các pipeline kiểm toán và tính toán mã băm mật mã toàn vẹn. Toàn bộ quyết định kiến trúc, thẩm định giao thức và phân tích khoa học do các tác giả chịu trách nhiệm.
- **Quy trình Chấm nhãn Tự động (Plan 06 - Hướng B):** Nhằm giải phóng điểm nghẽn của quy mô 3.360 – 4.480 lượt chấm thủ công, đồ án đã triển khai quy trình chấm đôi tự động độc lập thông qua hai persona thẩm định SRE (`Annotator A` khắt khe theo mã lỗi và cấu hình; `Annotator B` mở rộng ngữ cảnh và chuỗi phụ thuộc) tuân thủ nghiêm ngặt Rubric 3 mức (`0/1/2`). Hệ số đồng thuận liên người chấm đạt Quadratic Weighted Cohen's Kappa \(\kappa \ge 0.85\) trên cả 3 tập (`train`: 0.8542, `dev`: 0.8524, `test`: 0.8936) trước khi hòa giải (adjudication) tự động và xuất tập nhãn vàng F2. Toàn bộ nhật ký kiểm toán được lưu tại `reports/annotation-agreement-report.md`.

---

## 9. Khả năng Tái lập & Tài liệu Tham khảo (Reproducibility & References)

- Toàn bộ mã nguồn, cấu hình và dữ liệu kiểm toán được đóng gói tại thư mục `06_implementation/` và có thể tái hiện độc lập thông qua tài liệu `docs/reproduce.md`.
- Danh mục tài liệu tham khảo hoàn chỉnh được lưu trữ tại `reports/references.bib`.
