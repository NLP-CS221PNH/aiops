# Thiết kế nghiên cứu Hybrid RAG cho hỗ trợ chẩn đoán sự cố

## Kết luận lựa chọn

Giữ câu hỏi nghiên cứu trong đề cương: khi observations, corpus, generator và context budget không đổi, phối hợp lexical retrieval và dense retrieval có tìm được nhiều bằng chứng hữu ích hơn không, và phần tăng đó có chuyển thành câu trả lời đúng, có căn cứ không? Kết quả cần thiết là một so sánh có thể kiểm tra, bao gồm cả trường hợp hybrid không cải thiện. Cỡ danh mục paper hoặc lượng log tải về không thay cho đối chứng này.

Chọn RE2–Online Boutique làm nguồn chính theo kế hoạch. Xử lý ba sản phẩm riêng: observations từ telemetry; gold fault/service của benchmark; và qrels incident→evidence do người chấm. Nếu chỉ hoàn thiện hai sản phẩm đầu, đã có dữ liệu để thử pipeline và service localization, nhưng chưa có tập chuẩn để kết luận chất lượng evidence retrieval. [Đề cương](../00_plan/project_proposal.md) · [RCAEval](https://github.com/phamquiluan/RCAEval).

Đây là thiết kế thí nghiệm và tài nguyên triển khai đề xuất, không phải kết quả benchmark. Những cấu hình dưới đây cần được khóa sau pilot trước khi chạy test. Báo cáo dữ liệu, bibliography và corpus đi cùng cung cấp bằng chứng thu thập thực tế; không đọc các giả thuyết trong tài liệu này như quan sát đã đo.

## Mục lục

1. [Tác vụ và ranh giới kết luận](#tác-vụ-và-ranh-giới-kết-luận)
2. [So sánh các hướng](#so-sánh-các-hướng)
3. [Biểu diễn incident](#biểu-diễn-incident)
4. [Kho tri thức và thời gian](#kho-tri-thức-và-thời-gian)
5. [Truy hồi và model](#truy-hồi-và-model)
6. [Nhãn và chia dữ liệu](#nhãn-và-chia-dữ-liệu)
7. [Generation và đánh giá](#generation-và-đánh-giá)
8. [Phương án dữ liệu dự phòng](#phương-án-dữ-liệu-dự-phòng)
9. [Cấu hình cần khóa](#cấu-hình-cần-khóa)
10. [Nguồn và câu hỏi còn mở](#nguồn-và-câu-hỏi-còn-mở)

## Tác vụ và ranh giới kết luận

Đối tượng đánh giá là một incident, không phải từng dòng log. Một incident có nhiều dòng lỗi, trace spans và metric points, nhưng đó là những phép đo phụ thuộc trong cùng một lần chạy. Nếu biến mỗi dòng thành một mẫu test độc lập, số mẫu và độ chắc chắn thống kê sẽ bị phóng đại.

Với fault injection, nhãn service thường chỉ mục tiêu lỗi được tiêm. Một giải thích có causal chain nhiều bước cần chứng cứ mạnh hơn việc đoán đúng service. Không đánh đồng root-cause localization, causal-process reconstruction, mitigation recommendation và recovery success. Kế hoạch đã giới hạn xử lý offline, vì vậy không thể báo giảm MTTR hoặc hiệu quả khôi phục production từ thí nghiệm này. [Chính sách annotation](../00_plan/annotation_and_leakage_policy.md).

Ba phép kiểm phải độc lập: retrieval có tìm ra tài liệu được chấm liên quan; chẩn đoán có khớp gold; giải thích có được các đoạn được dẫn hỗ trợ. Câu trả lời có thể faithful với một runbook nhưng áp dụng sai vào incident, hoặc đoán đúng gold mà không có bằng chứng. Thiết kế đánh giá phải cho thấy được cả hai loại lỗi.

## So sánh các hướng

| Hướng | Điều kiện dữ liệu | Giá trị cho đồ án | Rủi ro chính | Quyết định |
|---|---|---|---|---|
| RE2-OB + tài liệu + qrels mới | Telemetry, nhãn fault/service, mapping evidence | Gắn NLP với vận hành; kiểm được IR và diagnosis | Qrels và version mapping cần công người | Hướng chính |
| Technical QA trên MTRAG/TechQA | Corpus và nhãn QA/retrieval đúng phiên bản | Tách rõ đóng góp retrieval/generation | Không đủ để tuyên bố causal RCA | Dự phòng nếu corpus RE2-OB không đủ |
| Log representation trên Loghub | Log và nhãn tác vụ tương ứng | Phân tích bảo toàn entity/error patterns | Anomaly labels không thành RCA gold | Nhánh thu hẹp có tên tác vụ riêng |
| Graph/multi-agent RCA | Cần topology, budget nhiều vòng, đối chứng | Mở rộng quan hệ nhiều bước | Tăng module và chi phí trước khi có evidence | Hoãn đến sau baseline |

Chọn hướng chính vì phù hợp đúng đề cương, không vì đã chứng minh tốt nhất. Quyết định chuyển hướng phải dựa trên pilot: nếu người chấm không tìm thấy tài liệu hỗ trợ các câu hỏi đại diện, thêm một retriever phức tạp sẽ không tạo ra bằng chứng còn thiếu. Khi đó cần bổ sung tài liệu đúng miền từ nguồn hợp lệ hoặc đổi task rõ ràng.

## Biểu diễn incident

Giữ một bản observations có thể truy ngược đến raw files và một dạng ngắn dùng để truy hồi. Một bundle hữu ích gồm cửa sổ quan sát, service inventory, các log patterns nổi bật, tần suất/timing và những trace/metric indicators đã tổng hợp. Những đoạn được chọn phải mang ID ổn định và offsets hoặc row indices để người kiểm tra quay lại dữ liệu gốc.

Không xóa hàng loạt số, punctuation hoặc tên service. HTTP status, exception class, port, error code và version string có thể là tín hiệu phân biệt. Thay các giá trị cần khử định danh một cách nhất quán, đồng thời giữ lineage của phép biến đổi. Chuỗi có thể là secret cần được xử lý trước mọi lần gửi đến API mô hình; việc giữ raw trên máy không phải xác nhận dữ liệu đủ sạch để chia sẻ.

RQ1 nên dùng ba biểu diễn trên cùng incident/window: raw selected error lines; normalized lines bảo toàn entity; bundle có cấu trúc. Nếu thêm summary bằng LLM, ghi riêng mô hình, prompt, input IDs và trạng thái kiểm tra. Summary là suy diễn từ observations; không trở thành raw observation hay reference answer.

Một nguy cơ đặc biệt là cắt cửa sổ theo injection time rồi gọi đó là tình huống triage không biết trước lỗi. Dùng gold injection time để dựng cửa sổ là một benchmark condition có thông tin oracle; nếu làm, phải công khai và cho tất cả baseline cùng điều kiện. Chọn cửa sổ quan sát từ dữ liệu có sẵn hoặc một detector cố định sẽ gần hơn với tình huống không biết onset, nhưng phải ghi cách chọn và độ trễ phát hiện.

## Kho tri thức và thời gian

Kho paper là bibliography phục vụ nghiên cứu. Kho truy hồi vận hành là tài liệu ứng dụng, runbook và lịch sử sự cố phù hợp. Trộn paper phương pháp RAG vào knowledge base rồi đánh giá như tài liệu sửa lỗi Online Boutique làm thay đổi nhiệm vụ và tạo những kết quả khó diễn giải.

Đối với nguồn công khai, cần giữ document ID, source URL, source commit, license, title, text hash, version scope và thời điểm có sẵn. Một file tải vào ngày nghiên cứu chỉ chứng minh nó có trong snapshot ngày đó; không chứng minh phiên bản ấy tồn tại trước một incident lịch sử. Khi dùng snapshot hiện tại với telemetry cũ, mô tả phép thử là **offline assistance với tài liệu đóng băng hiện tại**. Chỉ dùng tên historical triage khi đã kiểm tra temporal eligibility đúng phiên bản.

Đợt thu thập đã bổ sung [snapshot trước năm 2024](../03_collection_plan/knowledge-corpus-historical/snapshot.json), gồm 74 tài liệu và 580 chunks. Cấu hình đề xuất dùng snapshot này làm corpus chính; bản hiện tại 73 tài liệu/598 chunks là tài nguyên so sánh riêng. Mốc commit cũ giải quyết điều kiện tài liệu tồn tại trước cửa sổ quan sát khi kiểm tra ngày đạt, nhưng chưa giải quyết việc phiên bản ứng dụng/cluster có tương thích với deployment RCAEval hay không. Không cộng hai snapshot thành hai kho độc lập khi chia dữ liệu hoặc báo số nguồn.

Mapping service/symptom→document ở lượt chuẩn bị là gợi ý cho người chấm. Tài liệu Kubernetes về memory pressure có thể hướng dẫn bước kiểm tra OOM; nó không chứng minh application service nào là nguyên nhân ở một ca cụ thể. Tài liệu kiến trúc Online Boutique hỗ trợ hiểu quan hệ dịch vụ; runbook Prometheus hỗ trợ diễn giải alert. Mỗi nguồn có vai trò và giới hạn riêng.

Chunk theo section trước, sau đó chia khi quá dài. Lưu offsets theo ký tự trong chính text đã normalize, đồng thời giữ raw source riêng. Token count dùng tokenizer nào phải được nêu rõ; số từ hoặc số ký tự không được quảng cáo là exact model tokens. Khi đổi tokenizer hay chunking, tạo version/hash mới và chạy lại các baseline ảnh hưởng.

## Truy hồi và model

BM25 là baseline bắt buộc để kiểm exact lexical evidence. Dense retrieval là baseline để kiểm những cách diễn đạt khác nhau. Fusion dùng thứ hạng tránh cộng trực tiếp score BM25 và cosine không cùng thang. Reciprocal Rank Fusion cộng các nghịch đảo thứ hạng đã làm trơn; tham số fusion cần tách tên khỏi số kết quả top-k. Công trình gốc là [Cormack, Clarke và Büttcher, SIGIR 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf).

Đề xuất một cấu hình pilot đơn giản: candidate depth 50 cho mỗi retriever, RRF constant 60, top-5 context, cùng chunk corpus. Đây là giá trị bắt đầu do thiết kế chọn, chưa được tối ưu cho RE2-OB. Trên dev chỉ thử một số ít thay đổi có lý do; ghi lại toàn bộ lần thử để không chọn theo test.

| Thành phần | Ứng viên | Bằng chứng kỹ thuật | Cách dùng trong đợt tới |
|---|---|---|---|
| Dense chính | `intfloat/e5-small-v2` | 384 dimensions, tiếng Anh, input tối đa 512 tokens; query và passage cần prefix riêng | Gọn để bắt đầu; không dùng trực tiếp cho query tiếng Việt mà không đánh giá |
| Dense đối chứng tùy chọn | `BAAI/bge-small-en-v1.5` | 384 dimensions, 512-token sequence; query instruction theo card | Thay đúng một bi-encoder, giữ corpus và protocol |
| Reranker | `BAAI/bge-reranker-base` | Cross-encoder nhận cặp query/passage, card có ví dụ giới hạn 512 tokens | Chỉ rerank cùng candidate pool; đo thời gian riêng |
| IR toolkit tham khảo | Pyserini | Sparse/dense reproducible retrieval; README hiện tại nêu Python 3.12, Java 21 | Cân nhắc môi trường phụ thuộc trước khi chọn triển khai |

Thông số trong bảng được đọc từ model cards và README gốc, không phải benchmark chạy tại đây. Ba model cards ghi MIT; Pyserini README hiển thị Apache và có hướng dẫn dependency riêng. Đã giữ snapshot, revision và config trong [source-snapshots](source-snapshots/). [E5 card](https://huggingface.co/intfloat/e5-small-v2) · [BGE embedding card](https://huggingface.co/BAAI/bge-small-en-v1.5) · [BGE reranker card](https://huggingface.co/BAAI/bge-reranker-base) · [Pyserini](https://github.com/castorini/pyserini).

Khuyến nghị E5 ở đây là một lựa chọn thực dụng cho corpus/query tiếng Anh, không phải khẳng định tốt nhất trong miền log. Giữ query prefix `query: `, passage prefix `passage: ` và normalize embeddings theo card. Các bản weights chưa được tải hay chạy; không ghi model-ready hoặc latency dự kiến như kết quả. Việc chọn generator cần khóa model revision, context size và decoding trong giai đoạn thực nghiệm.

Reranking chỉ giúp khi relevant evidence đã vào candidate pool. Nếu Recall@50 thấp vì wrong-version hoặc corpus thiếu runbook, đổi thứ hạng top-50 không sửa được nguyên nhân này. Ngược lại, nếu relevant passage nằm trong pool nhưng ít khi lên top-5, reranker là ablation có lý do. Báo cả candidate recall và ranking metrics để phân biệt hai tình huống.

## Nhãn và chia dữ liệu

Qrels cần graded relevance 0/1/2 ở document và passage, với vai trò evidence và lý do ngắn. Trạng thái chưa chấm phải khác nhãn 0. Chấm một pool hợp nhất từ BM25, dense và hybrid, ẩn retriever/rank, xáo thứ tự ổn định. Người chấm có thể bổ sung evidence ngoài pool; nếu pool không đầy đủ thì báo pooled evaluation, không coi mọi ngoài-pool là không liên quan.

Pilot 10–20 incident chỉ giúp phát hiện lỗi schema và hiểu rubric. Hai người chấm độc lập toàn bộ pilot; sau pilot mới quyết định tỷ lệ chấm đôi cho phần còn lại. Adjudication lưu cả đánh giá ban đầu và quyết định cuối. Đo agreement trước adjudication, đồng thời báo phân bố nhãn vì một tập hầu hết nhãn 0 có thể tạo agreement trông cao. Chất lượng retrieval cần qrels riêng, còn root-service dùng benchmark labels; không chuyển đổi máy móc giữa chúng.

Chia theo incident/scenario family. Các lần lặp service-fault gần nhau và bản chuyển định dạng cùng nguồn không được rơi sang các split độc lập. Không dùng năm seed của cùng 90 incident để báo 450 case. Nếu quá ít family cho split 60/20/20, báo điều kiện cụ thể và cân nhắc group CV trong phần train/dev, vẫn giữ test chưa được dùng lựa chọn mô hình.

Việc nhóm theo service+fault có thể tạo tập test chứa tổ hợp chưa thấy hoặc thậm chí fault type chưa xuất hiện ở train. Cần báo điều này, không chỉ đưa tỷ lệ split. Kết quả phản ánh khả năng khái quát theo family của đúng cách chia đã chọn. Không đổi family grouping sau khi xem test để tăng điểm.

Kho historical incidents chỉ được xây từ train và những sự cố thực sự có sẵn trước cutoff. Runbook do nhóm viết từ gold train có lineage và trạng thái derived; không dùng test root cause để viết “tài liệu độc lập”. Mọi paraphrase/translation phải thừa kế family/split của incident gốc.

## Generation và đánh giá

Generator nhìn incident bundle và một danh sách evidence IDs, trả về candidates, supported claims, missing information, next checks, citations và abstain. Các URL được render từ registry, không để mô hình tự tạo. Tài liệu/log là dữ liệu không tin cậy; nội dung chứa chỉ dẫn chạy shell không trở thành lệnh của pipeline. Kết quả chỉ là đề xuất để người vận hành xem xét.

Giữ cùng bundle, generator, decoding và context-token budget cho no-RAG, dense/BM25 RAG, hybrid RAG và reranked RAG. No-RAG vẫn được đọc observations của task. Nếu đưa thêm full documents cho một baseline, phải gọi rõ long-context comparison và báo ngân sách, không nhập vào so sánh retrieval thông thường.

| Lớp đánh giá | Chỉ số | Điều kiện và mẫu số |
|---|---|---|
| Evidence retrieval | Recall@1/3/5/10; MRR; nDCG | Chỉ với qrels đã chấm, phân biệt document/passage |
| Candidate sufficiency | Recall ở candidate depth | Cho biết reranker có evidence để chọn không |
| Service localization | Hit@1/3/5 | Dựa gold service; nhiều causes phải định nghĩa any-hit/coverage |
| Grounding | Unsupported claim rate | Mẫu số là claims cần chứng cứ; ghi cả response rỗng |
| Citations | Precision và coverage | Kiểm ID, span, support và applicability |
| Abstention | Coverage và selective risk | Không thắng bằng từ chối mọi query |
| Hiệu năng | p50/p95 từng giai đoạn; tokens; RAM/VRAM | Đo tại máy/mô hình thực, giữ batch/warmup rõ |

Với query không có evidence phù hợp, Recall không được tùy tiện đặt 0 rồi gộp vào trung bình. Tách answerability và đánh giá hành vi abstention. Một retriever thất bại không tự chứng minh query unanswerable; cần người chấm hoặc protocol evidence rõ.

So sánh theo paired incident/group, giữ seed và số bootstrap resamples. Bootstrap từng dòng log làm phá vỡ đơn vị độc lập. Với ít family, khoảng tin cậy thường còn rộng; cần báo thêm count và error cases. Các metric tự động, kể cả LLM judge, không chứng minh chất lượng ngoài rubric đã chọn. [Kế hoạch đánh giá](../00_plan/experiments_and_evaluation.md).

Chọn failure cases theo tiêu chí công khai: exact error bị bỏ khi cleaning; upstream/downstream bị đảo; tài liệu đúng chủ đề nhưng sai version; citations hỗ trợ bước kiểm tra nhưng không hỗ trợ cause; gold đúng do leakage; evidence đủ mà reranker loại; abstention sai. Đưa cả ca tốt và ca xấu vào báo cáo, giữ input/config/evidence có thể kiểm tra.

## Phương án dữ liệu dự phòng

MTRAG có nhãn hội thoại và retrieval/generation riêng, vì thế phù hợp khi mục tiêu chuyển sang technical QA. README chính thức mô tả 110 hội thoại và 842 evaluation tasks trên bốn miền; Cloud corpus có 57.638 documents và 61.022 passages. Đây là số của tác giả ở snapshot, chưa phải lượng đã tải trong gói này. Quyền từng corpus và quan hệ document/passage cần kiểm riêng. [MTRAG](https://github.com/IBM/mt-rag-benchmark).

TechQA trên namespace PrimeQA hiện liệt kê một `TechQA.tar.gz` và card rất ngắn, chỉ ghi Apache-2.0. Metadata không đủ cho kiểm schema hoặc phạm vi các TechNotes bên trong. Vì vậy không thay thế RE2-OB bằng nguồn này chỉ vì nó mang tên QA; cần tải mẫu hợp lệ, kiểm labels/splits và điều khoản upstream trước. [PrimeQA/TechQA](https://huggingface.co/datasets/PrimeQA/TechQA).

ITBench-Lite card mô tả 65 scenarios, gồm 35 SRE, 15 FinOps, 15 CISO, và ghi Apache-2.0. SRE là snapshots môi trường, có telemetry và `ground_truth.yaml`; dùng để diagnosis offline, không đo được hành vi sửa hệ thống đang chạy. Card cũng còn mô tả một số phần đang phát triển, nên phải dựa file listing và schema thực trước khi tuyên bố đủ mọi domain. [ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite).

Không tải đồng thời ba bộ dự phòng khi nguồn chính đã khả dụng. Điều kiện chuyển là thiếu evidence/gold phù hợp hoặc chi phí annotation không đáp ứng, không phải vì thêm dataset sẽ làm nghiên cứu trông lớn hơn. Duy trì trạng thái từng nguồn trong dataset decision register để có thể tiếp tục mà không dò lại từ đầu.

## Cấu hình cần khóa

Trước final evaluation, khóa release/hash dataset, split/family policy, corpus hash, chunking version, redaction version, query representation, model revisions, prefix/normalization, candidate depth, fusion constant, reranking depth, context budget, prompt hash, decoding và evaluator version. Lưu manifest của từng lần chạy để một con số trong báo cáo nối được tới config và output.

Các file `experiment-proposal.json` và `experiment-results-template.tsv` là cấu hình đề xuất và bảng trống. Chưa có generator đã khóa, chưa có qrels được người chấm và chưa có test run. Khi chuyển sang giai đoạn 3 của lộ trình, điền annotation và quyết định pilot trước; không tự động chạy test chỉ vì JSON đã có đủ nhiều trường.

## Nguồn và câu hỏi còn mở

Nguồn sơ cấp được truy cập ngày 12/09/2026; các model/repository revisions nằm trong [support-resources.json](source-snapshots/support-resources.json). Tài liệu kế hoạch là nguồn cho các ràng buộc nội bộ; tham số pilot và ưu tiên triển khai ở đây là đề xuất phân tích, không gán cho tác giả paper.

1. Pham và cộng sự. [RCAEval repository](https://github.com/phamquiluan/RCAEval). Benchmark và đường vào dataset.
2. Cormack, Clarke và Büttcher. [Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf). SIGIR, 2009.
3. intfloat. [E5-small-v2 model card](https://huggingface.co/intfloat/e5-small-v2). Input contract và giới hạn.
4. BAAI. [BGE-small-en-v1.5 model card](https://huggingface.co/BAAI/bge-small-en-v1.5). Embedding candidate.
5. BAAI. [BGE-reranker-base model card](https://huggingface.co/BAAI/bge-reranker-base). Cross-encoder candidate.
6. Castorini. [Pyserini repository](https://github.com/castorini/pyserini). IR toolkit và dependencies.
7. IBM. [MTRAG repository](https://github.com/IBM/mt-rag-benchmark). Benchmark technical/multi-turn QA.
8. PrimeQA. [TechQA dataset entry](https://huggingface.co/datasets/PrimeQA/TechQA). Source metadata.
9. IBM Research. [ITBench-Lite dataset card](https://huggingface.co/datasets/ibm-research/ITBench-Lite). Offline SRE scenarios.

Câu hỏi còn mở: tỷ lệ incident có evidence phù hợp sau chấm; ứng dụng/version gốc của telemetry so với tài liệu; protocol split có đủ family; generator và phần cứng chạy thí nghiệm; thời gian hai người chấm; rubric chính thức CS221 của lớp. Các câu hỏi này không cản thu thập và kiểm tra nguồn, nhưng phải được giải quyết trước kết luận benchmark hoặc nộp báo cáo theo tiêu chí môn học.
