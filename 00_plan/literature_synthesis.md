# Bản đồ nghiên cứu và hàm ý thiết kế cho đồ án

Tài liệu này tổng hợp **hướng đọc và lập luận thiết kế**, không thay một systematic review đã đọc toàn văn từng paper. Các nhận định về lựa chọn cho CS221 là đề xuất; không có kết luận so sánh thực nghiệm mới.

## 1. RCA không chỉ là “hỏi log rồi để LLM giải thích”

Có ít nhất ba loại đầu ra dễ bị trộn: service gây lỗi, mô tả nguyên nhân bằng ngôn ngữ tự nhiên, và hành động khắc phục. [P0011 — Recommending Root-Cause and Mitigation Steps for Cloud Incidents using Large Language Models](https://arxiv.org/abs/2301.03797) và [P0005 — Automatic Root Cause Analysis via Large Language Models for Cloud Incidents](https://arxiv.org/abs/2305.15778) là điểm vào cho hướng sinh chẩn đoán cloud; [P0003 — Nissist: An Incident Mitigation Copilot based on Troubleshooting Guides](https://arxiv.org/abs/2402.17531) giúp đặt trọng tâm vào troubleshooting guides. Đối với đồ án, nên khai báo đầu ra nào có gold để chấm trước khi chọn kiến trúc.

Một hệ thống có thể truy hồi đúng một incident tương tự nhưng vẫn áp dụng nguyên nhân cũ sai vào service hiện tại. Ngược lại, nó có thể đoán đúng service từ một token lộ nhãn mà hoàn toàn không sử dụng evidence. Vì vậy, đề xuất tách retrieval quality, root-cause correctness và evidence grounding; demo câu trả lời mạch lạc không đủ là thí nghiệm RCA.

Hai nguồn khảo sát để định nghĩa terminology và ranh giới tác vụ là [P0052 — A Survey of AIOps for Failure Management in the Era of Large Language Models](https://arxiv.org/abs/2406.11213) và [P0773 — Failure Diagnosis in Microservice Systems: A Comprehensive Survey and Analysis](https://arxiv.org/abs/2407.01710). P0052 là preprint failure-management riêng; [G0005 — A Survey of AIOps in the Era of Large Language Models](https://doi.org/10.1145/3746635) là khảo sát CSUR successor cùng nhóm tác giả, không phải DOI/bản in của P0052. Khi đọc, cần lập ma trận “observed input → output label → evaluation unit”. Không gắn tên RCA cho mọi anomaly detection benchmark chỉ vì cùng có log.

## 2. Định vị đóng góp NLP rõ ràng

Có nhiều thuật toán RCA dựa trên metric, dependency graph hoặc trace. Đối với môn NLP, lời giải thích hợp lý là nghiên cứu biểu diễn thông điệp log, matching giữa triệu chứng và văn bản tri thức, và tạo câu trả lời có dẫn chứng. Một graph topology có thể là context, không buộc phải thành contribution chính mới.

[P0007 — Xpert: Empowering Incident Management with Query Recommendations via Large Language Models](https://arxiv.org/abs/2312.11988) gợi hướng đọc query recommendation; [P0009 — Assess and Summarize: Improve Outage Understanding with Large Language Models](https://arxiv.org/abs/2305.18084) gợi hướng outage summarization; [P0013 — Mining Root Cause Knowledge from Cloud Service Incident Investigations for AIOps](https://arxiv.org/abs/2204.11598) và [P0015 — SoftNER: Mining Knowledge Graphs From Cloud Incidents](https://arxiv.org/abs/2101.05961) là đầu mối knowledge extraction từ cloud incidents. Một cải tiến nhỏ nhưng có đối chứng, như entity-preserving incident bundle hoặc evidence-aware reranking, là phạm vi có thể kiểm nghiệm rõ hơn một multi-agent system với nhiều module nhưng thiếu nhãn.

Đề xuất contribution statement: “Đánh giá cách biểu diễn incident và hybrid retrieval ảnh hưởng thế nào đến evidence recall và grounded diagnosis dưới split theo incident/thời gian.” Không viết “xây hệ thống tự động tìm nguyên nhân mọi sự cố cloud” khi chỉ thử trên một tập fault-injection.

## 3. Log là văn bản bán cấu trúc, không phải câu tự nhiên thông thường

Tên service, error code, exception class, dấu đường dẫn và số phiên bản có thể mang thông tin phân biệt. Một bước cleaning xóa hết chữ số, dấu gạch hoặc placeholder quá mạnh có thể bỏ đúng tín hiệu để chọn nguyên nhân. Đây là lý do thiết kế nên giữ raw spans cùng với representation đã chuẩn hóa, để khi lỗi retrieval có thể truy lại điều gì đã bị mất.

Các hướng parsing để đọc gồm [P0410 — Drain: An Online Log Parsing Approach with Fixed Depth Tree](https://jiemingzhu.github.io/pub/pjhe_icws2017.pdf), [P0001 — LILAC: Log Parsing using LLMs with Adaptive Parsing Cache](https://arxiv.org/abs/2310.01796), [P0109 — LLMParser: An Exploratory Study on Using Large Language Models for Log Parsing](https://arxiv.org/abs/2404.18001) và [P0107 — A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?](https://arxiv.org/abs/2308.10828). Mục tiêu không phải tái lập hết mọi parser: chỉ cần một baseline rule/template và một phương án representation có lý do. Độ chính xác parsing tốt không tự chuyển thành Recall@k hay Hit@k cao; phải đo ở cả hai lớp nếu parsing là contribution.

[P0120 — RAGLog: Log Anomaly Detection using Retrieval Augmented Generation](https://arxiv.org/abs/2311.05261) nằm ở giao điểm RAG và log anomaly detection. Khi dùng làm related work, cần ghi rõ task anomaly khác causal diagnosis. [P0121 — LLM meets ML: Data-efficient Anomaly Detection on Unstable Logs](https://arxiv.org/abs/2406.07467) là đầu mối nghiên cứu log không ổn định; đồ án nên kiểm một holdout theo format/version nếu đủ dữ liệu, thay vì chỉ random split các log template gần như giống nhau.

## 4. Vì sao đặt BM25, dense và hybrid cạnh nhau?

Lập luận thiết kế: lexical match giữ exact error tokens; semantic matching có thể nối triệu chứng diễn đạt khác nhau. Đây là hai loại bằng chứng phù hợp để đối chứng, không phải chứng minh trước rằng hybrid chắc thắng. Cần giữ corpus, qrels và query bundle cố định mới đọc được phần đóng góp của retriever.

[P0245 — Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906) và [P0291 — Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://arxiv.org/abs/1908.10084) là nền tảng đọc cho dense representations; [P0230 — SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking](https://arxiv.org/abs/2107.05720) là phương án learned sparse; [P0199 — ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT](https://arxiv.org/abs/2004.12832) và [P0214 — ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction](https://arxiv.org/abs/2112.01488) mở hướng late interaction. Không cần triển khai tất cả: BM25 + một bi-encoder + rank fusion là baseline đủ để bắt đầu, rồi thêm reranker nếu thấy candidate pool có relevant evidence nhưng xếp thấp.

[P0325 — Passage Re-ranking With BERT](https://arxiv.org/abs/1901.04085) cung cấp đầu mối reranking; [P0338 — GPL: Generative Pseudo Labeling for Unsupervised Domain Adaptation of Dense Retrieval](https://arxiv.org/abs/2112.07577) và [P0345 — Promptagator: Few-shot Dense Retrieval From 8 Examples](https://arxiv.org/abs/2209.11755) phục vụ phần domain adaptation khi thiếu qrels. Pseudo labels có thể hỗ trợ train nhưng test cần nhãn độc lập; không dùng cùng LLM để sinh câu hỏi có đáp án rồi chấm “thành công” bằng chính cấu trúc câu đã tạo.

[P0331 — BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/abs/2104.08663) nhắc đến cross-domain evaluation. Hàm ý đề xuất: sau test trong Online Boutique, một thí nghiệm giữ lại Train Ticket có thể cho biết pipeline có phụ thuộc tên service/template của hệ thống đầu không. Đó là phép kiểm tra cần thực hiện, không là kết quả generalization đã có.

## 5. RAG cần kiểm soát nội dung, không chỉ nối vector database vào LLM

[P0376 — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) là điểm đọc nền tảng retrieval + generation. Khi triển khai, phải phân biệt external knowledge với observations của incident: log trong cửa sổ hiện tại là đầu vào, còn runbook và lịch sử incident là kho tri thức. Không cho baseline no-RAG thiếu observations trong khi RAG có đủ rồi kết luận retrieval đã cải thiện.

[P0634 — Query2doc: Query Expansion with Large Language Models](https://aclanthology.org/2023.emnlp-main.585/) và [P0740 — Query Rewriting for Retrieval-Augmented Large Language Models](https://arxiv.org/abs/2305.14283) giúp lập nhánh query expansion/rewriting. Trong miền kỹ thuật, một query viết lại không được bịa thêm tên service, triệu chứng hay error token. Ghi cả query gốc và query sau biến đổi; đánh giá no-rewrite như baseline.

[P0645 — Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) và [P0574 — RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation](https://arxiv.org/abs/2310.04408) liên quan context dài/compression. Đề xuất đo cùng token budget và theo dõi việc mất negation, condition hoặc version constraint khi summary. Một summary ngắn có thể dễ đọc nhưng sai bản chất; không đưa summary đó vào evaluator như ground truth.

[P0561 — Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511), [P0560 — Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) và [P0678 — Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity](https://arxiv.org/abs/2403.14403) mở các nhánh reflection/correction/adaptation. Trong giới hạn môn học, chúng là extension sau baseline; mỗi nhánh phải có điều kiện dừng, chi phí và ablation. Không lấy thêm vòng tự phản biện làm thay thế cho bằng chứng thật bị thiếu trong corpus.

## 6. GraphRAG là lựa chọn sau khi biết flat retrieval thiếu điều gì

Nếu câu hỏi cần nối nhiều thành phần, quan hệ service hoặc nhiều tài liệu, một graph/tree index có thể là giả thuyết đáng thử. Nhưng lỗi triage thường còn do scope mismatch, nhãn rò rỉ, corpus không có runbook hoặc timeline không đúng. Thêm graph không tự giải các lỗi này.

Các tài liệu đọc cho nhánh cấu trúc gồm [P0481 — RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval](https://arxiv.org/abs/2401.18059), [P0497 — From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) và [P0867 — HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models](https://arxiv.org/abs/2405.14831). Khi đưa vào đồ án, nên nói rõ graph chứa loại cạnh nào: liên kết trong tài liệu, quan hệ thực thể trích xuất, hay dependency từ telemetry. Cạnh co-occurrence/semantic similarity không được tự gọi là quan hệ nhân quả.

Đề xuất bước quyết định: kiểm tra các query hybrid thất bại; chỉ chọn graph extension nếu lỗi chính là thiếu liên kết nhiều mảnh evidence mà corpus thực sự có. Nếu evidence chưa tồn tại hoặc wrong-version, nên sửa corpus trước.

## 7. Benchmark quyết định câu kết luận được phép viết

[P0757 — RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data](https://arxiv.org/abs/2412.17015) mô tả benchmark RCA với telemetry và annotations. [P0075 — OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?](https://openreview.net/forum?id=M4qNIzQYpd) đưa vào bối cảnh query tự nhiên cần phân tích observations. [P0758 — OpenRCA 2.0: From Outcome Labels to Causal Process Supervision](https://arxiv.org/abs/2606.27154) chuyển sự chú ý sang causal-process supervision; trong danh mục này, trang paper OpenRCA gốc bị chặn còn release OpenRCA 2.0 chưa được xác nhận ở cấp tệp dữ liệu. Cần phân biệt bằng chứng mô tả bài với khả năng tải dataset.

Một benchmark có service label nhưng không có qrels chỉ đủ chấm service localization; muốn nói retrieval tốt hơn cần tạo nhãn evidence phù hợp. Một benchmark QA tổng quát có supporting facts không thay cho causal path. [P0905 — MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries](https://arxiv.org/abs/2401.15391) là đầu mối thiết kế multi-hop qrels, không phải nguồn gold nhân quả cho cloud.

Một plan có thể dùng [TechQA](https://huggingface.co/datasets/PrimeQA/TechQA) hay [MTRAG Cloud](https://github.com/IBM/mt-rag-benchmark) để giữ contribution NLP rõ khi dữ liệu RCA không đủ. Khi đó, chỉ tiêu và tên đề tài phải đổi cho phù hợp. Không giữ nhãn causal diagnosis rồi chỉ báo QA overlap score.

## 8. Độ bám sát nguồn và độ đúng không giống nhau

[P0761 — ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2311.09476), [P0762 — Evaluation of Retrieval-Augmented Generation: A Survey](https://arxiv.org/abs/2405.07437) và [P0763 — Retrieval Augmented Generation Evaluation in the Era of Large Language Models: A Comprehensive Survey](https://arxiv.org/abs/2504.14891) là lộ trình đọc evaluation. Với đồ án, cần giữ ba bảng kết quả: retrieval; root-cause task; generated answer. Một LLM judge có thể là phép đo phụ, nhưng annotator người và gold task phải độc lập với mô hình sinh.

[P0826 — Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/) là điểm đọc về citations. Đề xuất chấm từng claim quan trọng: nguồn có tồn tại; đoạn được dẫn có nói điều đó; claim có áp dụng cho incident hiện tại; các bằng chứng phản bác có bị bỏ qua không. Citation correctness chỉ trả lời một phần, không bao trùm mọi điều kiện.

[P0069 — PACE-LM: Prompting and Augmentation for Calibrated Confidence Estimation with GPT-4 in Cloud Incident Root Cause Analysis](https://arxiv.org/abs/2309.05833) đặt confidence thành một đề tài đánh giá riêng. Không chuyển câu “tôi khá chắc” của mô hình thành 90% xác suất đúng. Với ca thiếu bằng chứng, một câu trả lời nêu rõ unknown và bước kiểm tra có thể hữu ích hơn một nguyên nhân đoán chắc, nhưng điều này phải được rubric chấm, không chỉ mô tả trong demo.

## 9. Khoảng trống có thể kiểm nghiệm trong đồ án

Ba giả thuyết nên ưu tiên: **H1**, giữ error/service entities trong incident representation cải thiện lexical/semantic retrieval so với cleaning mạnh; **H2**, hybrid cải thiện evidence coverage trên query có cả exact tokens và paraphrase so với từng retriever; **H3**, kiểm soát evidence/citations cải thiện groundedness mà không tăng từ chối trả lời quá mức. Các giả thuyết có thể sai; báo cả negative results và phân tích nguyên nhân.

Không tuyên bố đây là khoảng trống khoa học chưa ai làm trên toàn thế giới. Danh mục hiện tại chưa được full-text systematic review; nó đủ tạo giả thuyết thực nghiệm cấp môn học, nhưng novelty ở cấp publication cần rà sâu từng nhánh và các paper gần nhất.

## 10. Cách biến danh mục thành related work

Universe related-work được khóa ở core 45 mục trong `01_papers/core-literature.tsv`; extraction matrix vẫn là tập nhỏ 8–12 công trình đã đọc đúng depth. Đọc sâu 15–25 bài từ core trước khi mở rộng matrix. Mỗi dòng extraction có task, observation, labels, knowledge source, split, baseline, metric, source availability, license và failure mode. Phần related work nên so sánh theo trục đóng góp, không liệt kê một nghìn tên bài. Chỉ khi kiểm tra full text mới chép số liệu bảng, mô tả implementation hoặc kết luận hơn/kém của paper.

Giữ một đoạn limitations: data công khai có thể khác production; fault injection không đại diện mọi sự cố; qrels hữu hạn có thể chưa phủ đủ bằng chứng; judge có bias; KB có ràng buộc version/time; phép đo trên một hệ thống chưa chứng minh generalization. Những giới hạn này giúp xác định phạm vi claim thay vì làm benchmark trông lớn hơn thực tế.
