# Tổng quan bằng chứng cho đồ án AIOps–RAG

## Kết luận nghiên cứu

Hướng nghiên cứu có cơ sở nhất cho CS221 là đánh giá **biểu diễn incident, truy hồi bằng chứng và chẩn đoán có dẫn nguồn** trong một phạm vi telemetry đã đóng băng. Các nghiên cứu cloud công nghiệp cho thấy giá trị của việc dùng lịch sử incident và troubleshooting guides, nhưng thường sử dụng dữ liệu nội bộ, tập nhãn được chuẩn bị riêng và quy trình thu thập diagnostics đặc thù. Vì vậy, nên dùng chúng để thiết kế phương pháp và đối chứng; không mặc định các tập production này là dữ liệu có thể tải để tái lập.[^1][^2][^3]

Ba câu hỏi trong plan vẫn phù hợp: giữ nguyên error/service entities có giúp retrieval; lexical và semantic retrieval bổ sung nhau trong những trường hợp nào; và kiểm soát bằng chứng có cải thiện độ đúng/bám nguồn của chẩn đoán hay không. Điều chỉnh quan trọng là **không đồng nhất tìm đúng service, citation entailment và tái dựng causal propagation path**. RCAEval, OpenRCA 2.0 và ALCE đo những đối tượng khác nhau; từng kết luận phải gắn với gold và protocol tương ứng.[^4][^5][^6]

## Mục lục

1. [Phạm vi bằng chứng](#phạm-vi-bằng-chứng)
2. [Định nghĩa tác vụ và benchmark](#định-nghĩa-tác-vụ-và-benchmark)
3. [Biểu diễn log và knowledge base](#biểu-diễn-log-và-knowledge-base)
4. [Lựa chọn retriever và RAG](#lựa-chọn-retriever-và-rag)
5. [Đánh giá và kiểm soát rò rỉ](#đánh-giá-và-kiểm-soát-rò-rỉ)
6. [Cập nhật và quan hệ phiên bản](#cập-nhật-và-quan-hệ-phiên-bản)
7. [Nguồn và việc còn mở](#nguồn-và-việc-còn-mở)

## Phạm vi bằng chứng

Mốc đối chiếu: **13-09-2026, Asia/Saigon**. Danh mục đầu vào có 1.009 record; đây là tập phát hiện tài liệu, không phải 1.009 nghiên cứu đã đọc. Báo cáo phân biệt ba lớp tài nguyên: metadata để trích dẫn; full text được lưu để tra cứu; và những phần thực sự đã được đọc và extraction. Tải được full text không tạo thành bằng chứng đã review toàn bộ bài.

<!-- coverage-start -->
| Hạng mục | Số lượng tại bản bàn giao |
|---|---:|
| Records bảo toàn trong catalog | 1.009 |
| Khớp metadata/identity nguồn chính thức hoặc depositor | 1.005 |
| Identity còn unresolved/candidate | 4 |
| Có tác giả/năm đủ tạo BibTeX | 1.003 |
| Bibliography chưa đủ authors/year hoặc identity | 6 |
| Có publication venue và năm được xác minh | 366 |
| Priority papers có bibliography | 50/50 |
| Priority papers có publication venue/year | 33/50 |
| Priority papers có full text local | 49/50 |
| Đã đọc một số sections trong full text | 25 |
| Mức abstract-only | 24 |
| Abstract và trang đầu primary PDF | 1 |
| Publication overlay có evidence | 991 catalog rows + 5 gap rows |
| SJR 2024 Q1 theo sidecar tracked | 24 catalog rows + 5 gap rows |
| Core related-work đã chọn | 45 |
<!-- coverage-end -->

Các con số này được ghi máy đọc được trong [research-statistics.json](../01_papers/enriched/research-statistics.json). [Reading matrix](../01_papers/enriched/reading-extraction-matrix.tsv) và [50 notes](../01_papers/reading-notes/README.md) lưu task, observations/labels, phương pháp, evaluation, giới hạn và phần đã đọc cho từng paper. `full_text_read=false` được giữ vì không bài nào được tuyên bố là đã thực hiện systematic full-text review hoàn chỉnh.

Lớp phục hồi metadata bổ sung bằng chứng cho 151 records, giữ nguyên URL gốc và ghi DOI/reference URL mới riêng. Sáu mục chưa đủ bibliography là P0089, P0189, P0422, P0437, P0537 và P0810: P0089 có ứng viên dissertation trùng tên với record IEEE nên bị loại; P0422 có tác giả/DOI nhưng chưa xác minh năm; các mục còn lại thiếu identity hoặc có title mismatch. Không tìm thấy collision trong các DOI/arXiv đã biết sau merge; đây vẫn là kiểm tra identifier, không chứng minh 1.009 records tương ứng 1.009 tác phẩm độc lập.

Nguồn metadata ưu tiên là arXiv-deposited DataCite, publisher-deposited Crossref, ACL Anthology và trang/paper gốc. Năm xuất hiện trên arXiv được lưu thành `preprint_year`; năm xuất bản và venue là các trường khác. Không suy peer review từ việc một bản thảo có DOI arXiv. Metadata chưa đủ hoặc title có nghi vấn được giữ trong hàng đợi unresolved, không điền tác giả/venue bằng trí nhớ.

Audit publication quality dùng overlay thay vì sửa 1.009 catalog rows. Q1 ở đây chỉ là journal thật có SJR 2024 Q1 và evidence ID tracked; BibTeX `@article` không phải tín hiệu Q1. Conference-journal-series dù được Crossref deposit như journal article vẫn bị loại khỏi Q1. Core 45 mục và priority-reading 50 mục là hai tập phục vụ hai mục tiêu khác nhau; việc vào core không nâng read depth.

## Định nghĩa tác vụ và benchmark

### Bốn loại đầu ra cần phân biệt

Survey AIOps chia pipeline thành preprocessing, failure perception, RCA và remediation. Trong RCA, localization, category classification và root-cause report generation cũng có yêu cầu nhãn khác nhau. Từ taxonomy này, đầu ra đề nghị cho đồ án là service ranking và một chẩn đoán có các claim liên kết với evidence; remediation chỉ ở mức next-check có điều kiện.[^7]

| Đầu ra | Đơn vị gold cần có | Kết luận có thể rút ra |
|---|---|---|
| Evidence retrieval | Query–document/span qrels | Bằng chứng cần thiết đã vào top-k hay chưa |
| Root service | Incident → service hoặc tập service | Khả năng localization trong suite đã chọn |
| Cause/fault category | Incident → taxonomy category | Classification theo taxonomy được khai báo |
| Explanation/citations | Claim → supporting/refuting spans | Mức bám nguồn, coverage và scope applicability |
| Causal path | Directed gold graph/path gắn propagation | Mức tái dựng cơ chế lan truyền theo benchmark |
| Mitigation | Environment recovery hoặc expert rubric | Khả năng phục hồi/đề xuất hành động trong điều kiện được chấm |

Đây là ma trận thiết kế, không phải tuyên bố các nhãn trên đều sẵn có trong một dataset. Nhãn service không cấp quyền gọi explanation là causal proof; corpus có supporting facts cũng không tự cung cấp causal edges.

### RCAEval phải chọn đúng suite

RCAEval v5 mô tả 735 ca: RE1 có 375 ca metrics-only, RE2 có 270 ca và RE3 có 90 ca code-level. RE2/RE3 là suite đa nguồn nhưng modality tùy system, chẳng hạn Sock Shop không có traces. Paper whole-benchmark mô tả service/indicator annotations và AC@k/Avg@k; release RE2-Online Boutique được chọn trong bộ dữ liệu dự án có root-service label trong index, chưa thấy gold indicator riêng. Vì dự án cần NLP từ log, RE2 phù hợp làm điểm vào hơn việc lấy toàn bộ số 735 làm quy mô corpus log. Các thí nghiệm sơ bộ của paper chủ yếu dùng RE2 Train Ticket; không nên đọc một bảng này như kết quả trên mọi suite/system.[^4]

Hàm ý: artifact nhập dữ liệu phải ghi suite, system, case, fault family, telemetry available và gold visibility. Việc chia train/test theo incident, embargo test postmortem và tạo qrels riêng vẫn là công việc của dự án. Paper count cũng không thay cho kiểm tra số tệp, hash và license của release thực tế.

### OpenRCA và causal-process supervision

OpenRCA gốc được xác minh là ICLR 2025. Abstract và trang đầu paper mô tả 335 failures trên ba enterprise systems với telemetry đa nguồn. Đợt này xác minh được metadata và nội dung trang đầu từ nguồn primary; bản PDF local trả 403, nên note không được ghi là đọc toàn văn. Các bảng/protocol ngoài phần này chưa được dùng làm bằng chứng chi tiết.[^8]

OpenRCA 2.0 phân biệt rõ outcome và process. PAVE dùng intervention đã biết, graph dependency và baseline telemetry để kiểm tra từ nguyên nhân tới symptom. AnySvc chỉ đòi ít nhất một service đúng; Path Reachability đòi liên kết tới một alarm node, còn Node/Edge F1 đánh giá graph. Paper nêu các điều kiện đầu vào và giới hạn transfer từ testbed. Đây là lý do mạnh để giữ grounding thành một trục riêng; nó không chứng minh dự án đã có process gold hoặc đã tải được release 500 instances.[^5]

### Production studies cung cấp thiết kế, không cấp dữ liệu mặc định

RCACopilot dùng incident handlers thu diagnostics rồi dự đoán root-cause category. Phần retriever dùng FastText được train trên lịch sử nội bộ và similarity có thành phần time-decay; tập prediction gồm 653 incidents của Transport với split 75/25. Đoạn setup đã đọc chưa xác lập đây là chronological split. Sự triển khai lâu năm của diagnostics collection không đồng nghĩa mọi phần LLM prediction đã có cùng quy mô đánh giá.[^1]

Xpert lại nêu test incidents xảy ra sau train và index cố định trong offline evaluation. Nó còn tuyên bố dữ liệu production không công khai. Oasis dùng chronological 7:1:2 và cùng context cho các baseline. Hai protocol này hỗ trợ trực tiếp việc đóng băng corpus và giữ information parity trong plan.[^2][^9]

ICA là đối chứng cần đọc thận trọng: nó dùng symptom của một PRB để truy trong các PRB còn lại, đồng thời nêu không có gold standard search-result set. Overlap với PRB và extraction outputs hữu ích cho nghiên cứu ban đầu, nhưng không nên được chuyển nguyên thành evidence-retrieval gold của dự án.[^10]

## Biểu diễn log và knowledge base

### Giữ raw spans cùng structured representation

Drain định tuyến bằng độ dài message và preceding tokens trong cây cố định; bước preprocessing có thể bỏ những token khớp domain regex. Điều này phù hợp với mục tiêu template extraction, nhưng error code, block ID hoặc service name bị biến thành variable có thể vẫn quan trọng với query. Vì vậy, một incident bundle nên giữ cả raw log, template, service, timestamp và provenance; normalization chỉ tạo thêm representation.[^11]

Loghub-2.0 chỉ ra nguy cơ message-level metrics bị các template phổ biến chi phối. Thí nghiệm representation nên có breakdown cho rare events và parameter-intensive logs. LILAC giải quyết chi phí/nhất quán bằng ICL và adaptive cache; DivLog dùng demonstrations đã gán nhãn. Các nhãn “training-free” hoặc “unsupervised” phải được đọc theo đúng thành phần phương pháp, không đồng nhất mọi phương pháp là không cần annotation.[^12][^13][^14]

Đề nghị tối thiểu cho H1: so raw spans, normalization mạnh và entity-preserving normalization trên cùng incident queries/qrels. Báo recall theo query có exact error token và query paraphrase; ghi tỷ lệ mất entities trước khi kết luận parser/cleaner hữu ích. Đừng dùng parsing accuracy thay cho retrieval hoặc RCA score.

### Runbook cần bảo toàn điều kiện và chuỗi hành động

Nissist mô tả knowledge node có type, intent, action và linker; intent dùng để index, linker nối outcome với intent bước sau. Động cơ chính là việc cắt TSG thành chunks có thể phá thứ tự hành động. User study chỉ gồm 20 OCE và 5 incidents, nên đây là nguồn thiết kế schema tốt hơn là bằng chứng đại diện cho mọi sự cố production.[^3]

Schema knowledge đề nghị: document/version, service/platform, section, prerequisites, symptoms, required observations, diagnostic checks, outcomes, next-step links và source span. Những trường này phục vụ quyết định applicability; không nên biến một đoạn hướng dẫn chung thành đáp án chắc chắn cho incident đang xét. Tài liệu lịch sử phải có published/updated/cutoff time để kiểm tránh tri thức tương lai.

## Lựa chọn retriever và RAG

### Baseline cần phản ánh trade-off thực

SBERT/DPR tạo cơ sở cho bi-encoder, ColBERT giữ tương tác ở token level, SPLADE học sparse lexical expansion. Các kỹ thuật này khác nhau về representation, training signal và footprint. BEIR cho thấy domain transfer không thể suy chỉ từ in-domain performance, đồng thời nêu missing judgments và lexical annotation bias. Vì vậy, BM25, một dense model và hybrid rank fusion là bộ đối chứng đủ có ý nghĩa cho giai đoạn đầu; không giả định hybrid luôn thắng.[^15]

Reranker chỉ có thể sắp lại candidates đã lấy được. Trước thêm module, hãy phân loại lỗi: relevant evidence không có trong KB; không vào candidate pool; vào pool nhưng xếp thấp; hoặc generator bỏ qua evidence đúng. Chỉ trường hợp thứ ba trực tiếp tạo động cơ cho reranking. Nếu dùng GPL/synthetic queries để thích nghi miền, qrels test phải độc lập với generator/teacher tạo pseudo labels.[^16]

### Mỗi RAG extension phải giữ một phép so sánh rõ

RAG gốc train retriever–generator và marginalize documents theo sequence/token; pipeline prepend context vào frozen API model là một cấu hình khác. Cần ghi cấu hình thực tế thay vì gọi mọi pipeline “tái lập RAG paper”. Self-RAG còn đòi training với reflection tokens và critic-generated annotations; một prompt “hãy tự kiểm tra” không tương đương phương pháp này.[^17][^18]

Query2doc giữ query gốc và bổ sung pseudo-document. Trong paper, sparse branch tăng trọng số query bằng lặp lại query, còn dense branch nối query với pseudo-document. Đây là nguồn cho ablation query expansion, đồng thời nhắc phải phân biệt văn bản do model sinh với observation thực. Pseudo-document không được làm nguồn evidence trong answer.[^19]

Lost in the Middle hỗ trợ việc kiểm thứ tự evidence và context budget, nhưng kết quả trên model trong paper không được gán nguyên cho mọi checkpoint hiện tại. RECOMP, CRAG, Adaptive-RAG và RAPTOR là các extension hợp lý sau khi biết failure mode; notes đi kèm ghi rõ ở các bài này mức extraction còn chủ yếu abstract. Chưa dùng chúng để tuyên bố một cấu hình có latency/accuracy tốt nhất cho corpus hiện tại.

## Đánh giá và kiểm soát rò rỉ

### Ba bảng kết quả chính

| Lớp | Metric đề nghị | Gold / điều kiện |
|---|---|---|
| Retrieval | Recall@k, nDCG@k, MRR; evidence-set completeness | Qrels theo incident, span/document IDs; pooled candidates nhiều retrievers |
| RCA | Hit/AC@k theo service; category F1 nếu có label | Khai báo single/multi-root, taxonomy và unit incident |
| Generated answer | Supported-claim rate, citation precision/coverage, contradiction, abstention/coverage | Human rubric, evidence có provenance và scope/time phù hợp |

Các metric là đề xuất thực nghiệm. Không trộn Recall@100 của một retriever với câu trả lời chỉ nhận top5 evidence; không gọi NLI entailment là causal correctness. Nếu có multi-root, ghi chính xác định nghĩa AC@k/recall và denominator trước khi so với paper.

ALCE chấm citation recall ở mức statement với tập passages được dẫn, còn citation precision tìm những citation không góp phần hỗ trợ. NLI chỉ là evaluator proxy; scope/version applicability của runbook đối với incident cần rubric bổ sung. ARES dùng human annotations để hiệu chỉnh judge error và tạo confidence intervals qua PPI; bỏ phần human calibration rồi vẫn gọi kết quả là tương đương ARES sẽ thay đổi phương pháp.[^6][^20]

PACE-LM sử dụng correctness pseudo-labels do GPT-4 sinh và threshold được kiểm trên human validation. Vì vậy, khi áp dụng calibration vào dự án, nên dùng gold người độc lập, reliability diagram, ECE và coverage/abstention. Đoạn dataset của paper nêu tổng 121.308 incidents nhưng các phần 98.308 + 2.000 + 3.000 cộng 103.308; phần chênh lệch chưa được giải thích trong đoạn đã đọc. Không tự chỉnh con số hoặc dùng chúng để cộng quy mô dữ liệu.[^21]

### Các kiểm soát cụ thể cần giữ

1. Group các ticket/log windows của cùng incident trước split; dedup text không đủ nếu ticket khác từ vựng nhưng cùng sự cố, như động cơ của iPACK.[^22]
2. Chỉ index investigations thuộc train và trước cutoff. RCAgent quy định log/database observations trước detection time; giữ raw snapshots bằng ID giúp trace nội dung dù context đã rút gọn.[^23]
3. Đóng băng query, corpus, qrels, k và context budget khi so retrievers; no-RAG vẫn có observations ngang nhau.
4. Annotator ghi supporting, refuting, irrelevant và insufficient-evidence; không ép mỗi query phải có đáp án chắc chắn.
5. Khi mở rộng live agents, ghi số lần lặp và environment state. AIOpsLab/ITBench đánh giá tương tác môi trường; variability ở đây khác một static QA dataset.[^24][^25]

## Cập nhật và quan hệ phiên bản

Không thêm ứng viên mới vào 1.009 record gốc. [Freshness additions](../01_papers/enriched/freshness-additions.jsonl) lưu sáu arXiv IDs cùng overlap: TORAI `2604.13522` đã có P0767; KRCA `2607.01788`, hai GALA IDs `2508.12472`/`2608.08968`, trajectory-level RCA `2608.21310` và recovery-aware evaluation `2607.04623` được giữ riêng. Hai bài cùng dùng acronym GALA chưa được tự coi là cùng version.

Năm gap DOI đã xác minh sống trong registry G0001–G0005 riêng và không tăng catalog. P0052 (`2406.11213`) vẫn là survey failure-management; G0005 (`10.1145/3746635`, arXiv `2507.12472`) là CSUR successor cùng nhóm tác giả. `2508.12472` là GALA khác work. Quan hệ P0052→G0005 được ghi `successor_same_authors`, không merge identifier.

KRCA mô tả pipeline drilldown, graph prior và memory-augmented agents; trajectory-level RCA nhấn mạnh sự tách rời giữa endpoint correctness và diagnostic process; recovery-aware evaluation mở thêm trục diagnosis-to-action. Đây là các nguồn gần thời điểm hiện tại để rà novelty, chưa là cơ sở thay benchmark vì các kết quả mới chỉ được screening ở mức abstract/metadata.[^26][^27][^28]

Hai quan hệ phiên bản đã được kiểm riêng: P0108 có title cũ trên metadata arXiv nhưng linked HTML v3 và DOI xuất bản xác nhận **DivLog: Log Parsing with Prompt Enhanced In-Context Learning**; P0740 đổi từ “for” thành “in” ở bản ACL, với cùng năm tác giả và abstract. Bibliography ưu tiên publication title, nhưng original title và arXiv ID vẫn giữ trong [alias-version-map.tsv](../01_papers/enriched/alias-version-map.tsv). Các candidates khác như survey title rút gọn, LogBatcher publication title hoặc ExaRanker cần bằng chứng quan hệ trước khi hợp nhất.

## Nguồn và việc còn mở

### Tài nguyên bàn giao

- [Catalog JSONL](../01_papers/enriched/catalog-enriched.jsonl) và [TSV](../01_papers/enriched/catalog-enriched.tsv): bảo toàn 1.009 IDs, metadata, provenance và mức xác minh.
- [Publication overlay](../01_papers/enriched/publication-class.tsv), [SJR recount](../01_papers/enriched/q1-recount.md), [rank evidence](../01_papers/enriched/rank-evidence.jsonl) và [ranking policy](../01_papers/publication-ranking-policy.md).
- [Core 45](../01_papers/core-literature.md), [năm gap](../01_papers/enriched/gap-candidates.tsv) và [manual work relations](../01_papers/enriched/work-relations.tsv).
- [Bibliography đã xác minh](../01_papers/enriched/references-verified.bib) và [bibliography riêng 50 priority](../01_papers/enriched/references-priority50.bib).
- [50 reading notes](../01_papers/reading-notes/README.md), [extraction matrix](../01_papers/enriched/reading-extraction-matrix.tsv), [mức coverage](../01_papers/enriched/research-statistics.json).
- [Unresolved bibliography](../01_papers/enriched/unresolved.tsv) và [priority publication metadata còn thiếu](../01_papers/enriched/priority-publication-unresolved.tsv).
- [Rescue evidence](../01_papers/enriched/rescue-metadata.jsonl) và [canonical-work candidates](../01_papers/enriched/canonical-work-candidates.tsv): phục hồi metadata và kiểm tra identifier collisions, bảo toàn mọi ID.
- [Hướng dẫn cache/provenance](../01_papers/enriched/README.md), bao gồm official ACL BibTeX và full-text resources local.

### Nguồn trích dẫn

[^1]: Chen và cộng sự. [Automatic Root Cause Analysis via Large Language Models for Cloud Incidents](https://arxiv.org/abs/2305.15778), 2023 preprint; phần §4–6. Metadata xuất bản trong bibliography.
[^2]: [Xpert: Empowering Incident Management with Query Recommendations via Large Language Models](https://arxiv.org/abs/2312.11988), 2023 preprint; §5, §6.1.1, §11.
[^3]: [Nissist: An Incident Mitigation Copilot based on Troubleshooting Guides](https://arxiv.org/abs/2402.17531), 2024; §2.1, §3.
[^4]: Pham, Zhang, Ha, Salim và Zhang. [RCAEval](https://arxiv.org/html/2412.17015v5), 2024 preprint/2025 publication; §3–5.
[^5]: [OpenRCA 2.0: From Outcome Labels to Causal Process Supervision](https://arxiv.org/abs/2606.27154), 2026; §3, §5.
[^6]: Gao và cộng sự. [Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/), EMNLP 2023; §3.3.
[^7]: Zhang và cộng sự. [A Survey of AIOps for Failure Management in the Era of Large Language Models](https://arxiv.org/abs/2406.11213), 2024; §2.3, §7.
[^8]: Xu và cộng sự. [OpenRCA](https://openreview.net/pdf?id=M4qNIzQYpd), ICLR 2025; trang1. [Primary publication profile](https://openreview.net/profile?id=~Zhiqing_Zhong2).
[^9]: [Assess and Summarize: Improve Outage Understanding with Large Language Models](https://arxiv.org/abs/2305.18084), 2023; §5.1–5.3.
[^10]: [Mining Root Cause Knowledge from Cloud Service Incident Investigations for AIOps](https://arxiv.org/abs/2204.11598), 2022; §3.4, §4.3.
[^11]: He, Zhu, Zheng và Lyu. [Drain](https://jiemingzhu.github.io/pub/pjhe_icws2017.pdf), ICWS 2017; §III.
[^12]: [A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?](https://arxiv.org/abs/2308.10828), 2023 preprint; introduction và §3.
[^13]: [LILAC](https://arxiv.org/abs/2310.01796), 2023 preprint; abstract/introduction.
[^14]: Xu và cộng sự. [DivLog: Log Parsing with Prompt Enhanced In-Context Learning](https://doi.org/10.1145/3597503.3639155), ICSE 2024; [arXiv version](https://arxiv.org/abs/2307.09950).
[^15]: Thakur và cộng sự. [BEIR](https://arxiv.org/abs/2104.08663), 2021; introduction, metrics và §4.
[^16]: [GPL: Generative Pseudo Labeling for Unsupervised Domain Adaptation of Dense Retrieval](https://arxiv.org/abs/2112.07577), 2021 preprint; abstract.
[^17]: Lewis và cộng sự. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401), 2020; §2.
[^18]: Asai và cộng sự. [Self-RAG](https://arxiv.org/abs/2310.11511), 2023 preprint; §3.1.
[^19]: Wang, Yang và Wei. [Query2doc](https://aclanthology.org/2023.emnlp-main.585/), EMNLP 2023; §2.
[^20]: [ARES](https://arxiv.org/abs/2311.09476), 2023 preprint; §3.3.
[^21]: [PACE-LM](https://arxiv.org/abs/2309.05833), 2023; §5.1.
[^22]: [Incident-aware Duplicate Ticket Aggregation for Cloud Systems](https://arxiv.org/abs/2302.09520), 2023; §III-D, §IV-A1.
[^23]: [RCAgent](https://arxiv.org/abs/2310.16340), 2023 preprint; §3.1, §4.2.
[^24]: [AIOpsLab](https://arxiv.org/abs/2501.06706), 2025; §3.1–3.3.
[^25]: [ITBench](https://arxiv.org/abs/2502.05352), 2025; §3.1, §4.4.
[^26]: Jiang và cộng sự. [KRCA](https://arxiv.org/abs/2607.01788), 2026; abstract.
[^27]: Lu và cộng sự. [Beyond Fault Localization: A Trajectory-Level Study of LLM Agents for Microservice Root Cause Analysis](https://arxiv.org/abs/2608.21310), 2026; abstract.
[^28]: [Can LLMs Really Recover Microservice Failures? A Recovery-Aware Evaluation of Diagnosis-to-Action Reasoning](https://arxiv.org/abs/2607.04623), 2026; metadata/abstract screening.

Full authors, publication venue/year, DOI và preprint mapping của nhóm ưu tiên có trong bibliography và từng note. Các số liệu chỉ mô tả phạm vi nguồn; không có thí nghiệm RCA/RAG mới được chạy trong báo cáo literature này.

### Các câu hỏi còn mở và bước thực hiện

1. Dùng cohort RE2-Online Boutique đã thu đủ 90 ca làm điểm bắt đầu; review label visibility và corpus applicability trước khi khóa final test. Nếu không có causal-path gold, giữ claim ở service localization và grounded answer.
2. Đọc evaluation/ablation đầy đủ của 24 bài còn abstract-only trước khi tái lập kết quả hoặc viện dẫn số benchmark; full text local giúp tiếp tục mà không tìm lại tài liệu.
3. Hoàn thiện những publication relations chưa chứng minh; không sửa title/venue theo ứng viên gần giống. OpenRCA PDF local cần một đường truy cập hợp lệ khác hoặc mở thủ công khi nguồn cho phép.
4. Gán qrels cho pilot incidents, pool candidates từ lexical/dense/hybrid và xử lý disagreements; từ đó quyết định experiment scale và chi phí annotation.
5. Chạy H1 trước, rồi H2, H3 với corpus/version/split cố định. Chỉ thêm graph, agent loop hoặc query rewriting sau error analysis chỉ rõ nhu cầu.
