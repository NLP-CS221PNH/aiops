# 50 tài liệu ưu tiên và câu hỏi cần rút ra khi đọc
Đây là lộ trình đọc đề xuất, không phải 50 bản tóm tắt toàn văn. Mỗi mục liên kết catalog và nêu sản phẩm nên tạo sau khi đọc. Không suy chất lượng khoa học từ số trích dẫn hay tên venue chưa kiểm chứng.

Danh sách CORE 45 mục, gồm các gap đã xác minh và phân bổ theo vai trò, sống riêng trong [`core-literature.md`](core-literature.md). File hiện tại vẫn là workflow đọc 50 mục ban đầu; các mục retrieval nâng cao không được dùng để đệm CORE nếu implementation không sử dụng chúng.

## 01 · Chốt bài toán và benchmark
### 01. [P0052 — A Survey of AIOps for Failure Management in the Era of Large Language Models](https://arxiv.org/abs/2406.11213)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Tách incident detection, triage, diagnosis và mitigation.

**Ứng dụng đề xuất:** Viết định nghĩa task; chỉ chọn một hoặc hai đầu ra đánh giá được.

### 02. [P0757 — RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data](https://arxiv.org/abs/2412.17015)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cấu trúc ca lỗi, nhãn root service/indicator và protocol.

**Ứng dụng đề xuất:** Chốt suite/system; lập danh sách trường gold tuyệt đối không đưa vào index.

### 03. [P0075 — OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?](https://openreview.net/forum?id=M4qNIzQYpd)

**Trạng thái metadata:** `blocked_or_unreadable`.

**Cần đọc để trả lời:** Đọc cách câu hỏi tự nhiên kết nối với telemetry và nhãn đầu ra.

**Ứng dụng đề xuất:** Dùng repo Microsoft làm đầu mối; primary paper landing chưa đọc được trong audit.

### 04. [P0758 — OpenRCA 2.0: From Outcome Labels to Causal Process Supervision](https://arxiv.org/abs/2606.27154)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Phân biệt outcome labels và process supervision.

**Ứng dụng đề xuất:** Tách Hit@k service với đánh giá đường lan truyền; không tuyên bố causal path nếu thiếu gold.

### 05. [P0005 — Automatic Root Cause Analysis via Large Language Models for Cloud Incidents](https://arxiv.org/abs/2305.15778)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem những bằng chứng được sử dụng trong RCA cloud và cách xây pipeline.

**Ứng dụng đề xuất:** Vẽ sơ đồ đầu vào được phép nhìn; đối chiếu với dữ liệu công khai mình có.

### 06. [P0011 — Recommending Root-Cause and Mitigation Steps for Cloud Incidents using Large Language Models](https://arxiv.org/abs/2301.03797)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Tách nhiệm vụ sinh nguyên nhân và gợi ý mitigation.

**Ứng dụng đề xuất:** Giữ rubric diagnosis và next-checks riêng; không tự động thực thi remediation.

### 07. [P0003 — Nissist: An Incident Mitigation Copilot based on Troubleshooting Guides](https://arxiv.org/abs/2402.17531)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách sử dụng troubleshooting guides.

**Ứng dụng đề xuất:** Xây schema runbook có điều kiện áp dụng, evidence và bước kiểm tra.

### 08. [P0007 — Xpert: Empowering Incident Management with Query Recommendations via Large Language Models](https://arxiv.org/abs/2312.11988)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem query recommendation phục vụ điều tra incident.

**Ứng dụng đề xuất:** Chỉ thêm query rewriting nếu có phép so sánh không sửa đổi generator/corpus.

### 09. [P0009 — Assess and Summarize: Improve Outage Understanding with Large Language Models](https://arxiv.org/abs/2305.18084)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc tóm tắt outage và mất mát thông tin khi tổng hợp.

**Ứng dụng đề xuất:** Đánh giá incident summary có giữ service/error/time và provenance không.

### 10. [P0013 — Mining Root Cause Knowledge from Cloud Service Incident Investigations for AIOps](https://arxiv.org/abs/2204.11598)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem knowledge extraction từ investigation records.

**Ứng dụng đề xuất:** Phân biệt knowledge sinh từ train investigations với gold test phải embargo.

### 11. [P0035 — Incident-aware Duplicate Ticket Aggregation for Cloud Systems](https://arxiv.org/abs/2302.09520)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách xác định ticket trùng sự cố.

**Ứng dụng đề xuất:** Gom cùng incident trước split; không để ticket duplicate rơi ở hai phía.

### 12. [P0069 — PACE-LM: Prompting and Augmentation for Calibrated Confidence Estimation with GPT-4 in Cloud Incident Root Cause Analysis](https://arxiv.org/abs/2309.05833)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc định nghĩa confidence và cách kiểm tra calibration.

**Ứng dụng đề xuất:** Không trình bày confidence của LLM như xác suất chuẩn nếu chưa hiệu chỉnh.

### 13. [P0071 — RCAgent: Cloud Root Cause Analysis by Autonomous Agents with Tool-Augmented Large Language Models](https://arxiv.org/abs/2310.16340)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Tìm cách giới hạn công cụ và bằng chứng trong tác nhân RCA.

**Ứng dụng đề xuất:** MVP chỉ đọc; ghi tool/output provenance và điều kiện dừng trước khi mở agent loop.

### 14. [P0054 — AIOpsLab: A Holistic Framework to Evaluate AI Agents for Enabling Autonomous Clouds](https://arxiv.org/abs/2501.06706)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc phần môi trường, fault injection và evaluation.

**Ứng dụng đề xuất:** Tách generator benchmark khỏi static dataset; chỉ dùng sandbox trong phần mở rộng.

### 15. [P0055 — ITBench: Evaluating AI Agents across Diverse Real-World IT Automation Tasks](https://arxiv.org/abs/2502.05352)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem taxonomy tác vụ IT và loại ground truth.

**Ứng dụng đề xuất:** Chọn SRE thay vì trộn FinOps/CISO vào con số ca RCA.

## 02 · Biểu diễn và phân tích log
### 16. [P0410 — Drain: An Online Log Parsing Approach with Fixed Depth Tree](https://jiemingzhu.github.io/pub/pjhe_icws2017.pdf)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách trích log template và giới hạn của parsing.

**Ứng dụng đề xuất:** Giữ đồng thời raw span và parsed template để kiểm tra mất thông tin.

### 17. [P0107 — A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?](https://arxiv.org/abs/2308.10828)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc protocol đánh giá parsing và dữ liệu benchmark.

**Ứng dụng đề xuất:** Chốt parsing metric khác retrieval metric; tránh coi parsing tốt là RCA tốt.

### 18. [P0001 — LILAC: Log Parsing using LLMs with Adaptive Parsing Cache](https://arxiv.org/abs/2310.01796)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Tìm cách sử dụng LLM và cache cho parsing.

**Ứng dụng đề xuất:** Cân nhắc cache ở phần tiền xử lý, đo lại lợi ích sau chuẩn hóa log.

### 19. [P0108 — Prompting for Automatic Log Template Extraction](https://arxiv.org/abs/2307.09950)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đối chiếu tiêu đề primary với alias DivLog trong danh mục phát hiện.

**Ứng dụng đề xuất:** Khi trích dẫn, lấy BibTeX chính thức đúng version; không giữ alias thành một paper mới.

### 20. [P0109 — LLMParser: An Exploratory Study on Using Large Language Models for Log Parsing](https://arxiv.org/abs/2404.18001)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc các thiết lập dùng LLM để parsing.

**Ứng dụng đề xuất:** Xây một baseline đơn giản trước khi fine-tune toàn pipeline.

### 21. [P0111 — Stronger, Cheaper and Demonstration-Free Log Parsing with LLMs](https://arxiv.org/abs/2406.06156)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem thiết lập parsing không cần demonstrations.

**Ứng dụng đề xuất:** So sánh chi phí/quality ở cùng tập log mẫu, không dùng lời quảng bá trong tiêu đề làm kết quả.

### 22. [P0114 — LibreLog: Accurate and Efficient Unsupervised Log Parsing Using Open-Source Large Language Models](https://arxiv.org/abs/2408.01585)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc lựa chọn mô hình open-source trong log parsing.

**Ứng dụng đề xuất:** Ghim model card/revision; đo giới hạn thực trên máy có sẵn.

### 23. [P0115 — LUNAR: Unsupervised LLM-based Log Parsing](https://arxiv.org/abs/2406.07174)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách đặt mục tiêu parsing không nhãn.

**Ứng dụng đề xuất:** Tách pseudo-label khỏi annotation người; giữ nguồn gốc các template.

### 24. [P0120 — RAGLog: Log Anomaly Detection using Retrieval Augmented Generation](https://arxiv.org/abs/2311.05261)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc điểm giao RAG và log anomaly detection.

**Ứng dụng đề xuất:** Phân biệt anomaly detection với root-cause diagnosis trong phạm vi báo cáo.

### 25. [P0121 — LLM meets ML: Data-efficient Anomaly Detection on Unstable Logs](https://arxiv.org/abs/2406.07467)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc vấn đề log không ổn định và hiệu quả sử dụng nhãn.

**Ứng dụng đề xuất:** Tạo holdout theo phiên bản/thay đổi log, không chỉ random split cùng template.

## 03 · Retriever và reranker
### 26. [P0291 — Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://arxiv.org/abs/1908.10084)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách xây sentence representation và similarity.

**Ứng dụng đề xuất:** Định nghĩa query/document encoding, normalization và cách giữ token lỗi.

### 27. [P0245 — Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc dense passage retrieval và supervision.

**Ứng dụng đề xuất:** Làm baseline bi-encoder trên qrels riêng, không dùng QA answer string thay qrels.

### 28. [P0199 — ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT](https://arxiv.org/abs/2004.12832)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc late interaction trong retrieval.

**Ứng dụng đề xuất:** Cân nhắc như ablation nếu exact error tokens bị embeddings gộp mất.

### 29. [P0214 — ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction](https://arxiv.org/abs/2112.01488)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Xem đánh đổi hiệu quả và chi phí của late interaction.

**Ứng dụng đề xuất:** So sánh cả footprint/latency với retriever đơn giản, không chỉ Recall.

### 30. [P0230 — SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking](https://arxiv.org/abs/2107.05720)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc learned sparse retrieval.

**Ứng dụng đề xuất:** Để làm phương án mở rộng của lexical branch, không bắt buộc cho MVP.

### 31. [P0342 — Unsupervised Dense Information Retrieval with Contrastive Learning](https://arxiv.org/abs/2112.09118)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc dense retrieval không nhãn với contrastive learning.

**Ứng dụng đề xuất:** Không gọi pretraining general corpus là đã thích nghi miền incident.

### 32. [P0338 — GPL: Generative Pseudo Labeling for Unsupervised Domain Adaptation of Dense Retrieval](https://arxiv.org/abs/2112.07577)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc pseudo labeling để domain adaptation.

**Ứng dụng đề xuất:** Chỉ sinh/tune trên train corpus, có tập qrels người độc lập.

### 33. [P0331 — BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/abs/2104.08663)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cross-domain retrieval evaluation.

**Ứng dụng đề xuất:** Thiết kế test khác hệ thống, kiểm tra quyền từng corpus benchmark.

### 34. [P0325 — Passage Re-ranking With BERT](https://arxiv.org/abs/1901.04085)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc cách rerank passage bằng mô hình tương tác query-document.

**Ứng dụng đề xuất:** Đo reranker trên cùng candidate pool và cùng context budget.

### 35. [P0647 — M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation](https://arxiv.org/abs/2402.03216)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc đặc tính multi-lingual/multi-granular embeddings.

**Ứng dụng đề xuất:** Chọn model bằng pilot trên log/technical docs; không suy luôn tốt hơn BM25.

## 04 · RAG và quản lý bằng chứng
### 36. [P0376 — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc tách retriever và generator trong knowledge-intensive NLP.

**Ứng dụng đề xuất:** Giữ hai lớp evaluation; tracing evidence từ query đến response.

### 37. [P0561 — Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc retrieve/generate/critique có self-reflection.

**Ứng dụng đề xuất:** Không dùng self-critique thay cho gold label; đặt nhánh này sau baseline cố định.

### 38. [P0560 — Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc kiểm soát chất lượng bằng chứng trong corrective retrieval.

**Ứng dụng đề xuất:** Thiết kế context-noise/irrelevance tests trước khi thêm retrieval fallback.

### 39. [P0678 — Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity](https://arxiv.org/abs/2403.14403)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc adaptive retrieval theo độ phức tạp câu hỏi.

**Ứng dụng đề xuất:** Cân nhắc budget routing nhưng báo latency và các ca chọn sai mức retrieval.

### 40. [P0578 — Active Retrieval Augmented Generation](https://arxiv.org/abs/2305.06983)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc retrieval theo nhu cầu trong generation.

**Ứng dụng đề xuất:** Đặt giới hạn số vòng và công khai evidence qua từng vòng.

### 41. [P0574 — RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation](https://arxiv.org/abs/2310.04408)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc compression và selective augmentation.

**Ứng dụng đề xuất:** Kiểm tra summary context không bỏ câu phủ định, phiên bản và exception token.

### 42. [P0645 — Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc ảnh hưởng vị trí thông tin trong context dài.

**Ứng dụng đề xuất:** Ablation sắp thứ tự evidence và context budget; không cho baseline context khác nhau.

### 43. [P0634 — Query2doc: Query Expansion with Large Language Models](https://aclanthology.org/2023.emnlp-main.585/)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc query expansion với LLM.

**Ứng dụng đề xuất:** Bảo vệ tên service/error; một expanded query bịa triệu chứng có thể làm sai retrieval.

### 44. [P0740 — Query Rewriting for Retrieval-Augmented Large Language Models](https://arxiv.org/abs/2305.14283)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc query rewriting cho RAG.

**Ứng dụng đề xuất:** Thử no-rewrite đối chứng; không dùng test answers huấn luyện rewriter.

### 45. [P0481 — RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval](https://arxiv.org/abs/2401.18059)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc tổ chức tài liệu phân cấp bằng tóm tắt.

**Ứng dụng đề xuất:** Graph/tree KB chỉ mở rộng khi flat hybrid chưa đủ, và vẫn truy ngược evidence gốc.

## 05 · Đánh giá và ground truth
### 46. [P0761 — ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2311.09476)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc tách context relevance, answer relevance và faithfulness.

**Ứng dụng đề xuất:** Dùng judge phụ với human calibration; không đồng nhất faithfulness và RCA correctness.

### 47. [P0762 — Evaluation of Retrieval-Augmented Generation: A Survey](https://arxiv.org/abs/2405.07437)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc taxonomy đánh giá retrieval và generation.

**Ứng dụng đề xuất:** Lập metrics theo task và dữ liệu gold thực sự có.

### 48. [P0763 — Retrieval Augmented Generation Evaluation in the Era of Large Language Models: A Comprehensive Survey](https://arxiv.org/abs/2504.14891)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc giới hạn, phạm vi các metric/framework RAG.

**Ứng dụng đề xuất:** Ghi model/prompt/version của evaluator; kiểm tra bias cùng model sinh/chấm.

### 49. [P0826 — Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc đánh giá văn bản có citations.

**Ứng dụng đề xuất:** Chấm citation correctness, coverage và supported claims riêng.

### 50. [P0905 — MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries](https://arxiv.org/abs/2401.15391)

**Trạng thái metadata:** `primary_title_identifier_confirmed`.

**Cần đọc để trả lời:** Đọc nhãn multi-hop evidence retrieval.

**Ứng dụng đề xuất:** Xây qrels nhiều tài liệu; retrieval được một đoạn chưa chắc đủ cả lời giải thích.

## Từ đọc sang viết related work

Mỗi bài thực sự sử dụng cần một extraction note: task, observations, labels, method, baseline, dataset/publicity, license link, protocol split, evaluation và giới hạn. Các con số kết quả chỉ ghi sau đọc bảng nguồn gốc; không suy từ abstract/title. Sau đó bổ sung author/venue/year chính thức vào bibliography, giữ alias/version map. Không cần trích đủ 1.009 mục trong báo cáo môn học.
