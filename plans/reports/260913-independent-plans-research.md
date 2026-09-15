# Phân tích khả năng triển khai đồ án AIOps Hybrid RAG

## Nhận định chính

Hướng hợp lý là hoàn thiện thí nghiệm từ gói đang có: lọc đầu vào, chuẩn hóa corpus và biểu diễn, xây ba retrievers, tạo nhãn người rồi đánh giá câu trả lời. Đổi dataset hoặc mở thêm GraphRAG lúc này sẽ tăng số quyết định chưa được kiểm, trong khi các khoảng trống quyết định tính hợp lệ của nghiên cứu vẫn là applicability, qrels và kiểm soát test.

Codex có thể đảm nhận phần lớn công việc lập trình và chuẩn bị tài liệu: xuất dữ liệu có schema, kiểm provenance, tạo index/runner, công cụ annotation, validator, phân tích và demo. Khả năng viết các thành phần ấy chưa chứng minh chúng hoạt động tốt trên RE2-OB. Nghiệm thu phải dựa trên lần chạy và phán quyết người thật; quyền môn học, ngân sách và kết luận chuyên môn của người chấm không thể suy ra từ việc code chạy thành công.

Tách thành mười plan độc lập giúp giao từng gói với tiêu chí hoàn tất riêng. Ba gói 04/05/07 kết thúc ở tooling cùng pilot để có thể bàn giao trước khi chọn cấu hình cuối; plan 08 điều phối dev selection và F1. Phần annotation test của 06 nối lại sau F1, tránh yêu cầu cả hai plan phải hoàn tất trước nhau.

## Mục lục

1. [Căn cứ và độ chắc chắn](#căn-cứ-và-độ-chắc-chắn)
2. [Khoảng trống đã kiểm](#khoảng-trống-đã-kiểm)
3. [Lựa chọn phương án](#lựa-chọn-phương-án)
4. [Khả năng của Codex](#khả-năng-của-codex-theo-hạng-mục)
5. [Thiết kế thực nghiệm](#thiết-kế-thực-nghiệm-và-giới-hạn)
6. [Nguồn lực](#nguồn-lực-và-thứ-tự-ưu-tiên)
7. [Nguồn](#nguồn-sơ-cấp)
8. [Câu hỏi mở](#bước-tiếp-theo-và-câu-hỏi-mở)

## Căn cứ và độ chắc chắn

Đối chiếu ngày **13/09/2026**, cập nhật bắt đầu lúc khoảng **08:00 Asia/Saigon**. Phạm vi là các lựa chọn làm thay đổi mười gói của master, không phải tổng quan hệ thống toàn bộ lĩnh vực. Tài liệu nền: nghiên cứu RRF 2009, E5 2022, ALCE 2023, RCAEval 2024/2025; tài liệu API/model hiện hành được kiểm lại trong ngày.

Nguồn local gồm START-HERE, master và mười phase, contracts/reports của gói chuẩn bị, JSON/TSV/JSONL và source Python. Nguồn ngoài ưu tiên paper gốc, model card và tài liệu nhà cung cấp. Tra cứu tập trung các nhóm: RCAEval task/data format; E5 và RRF; citation evaluation; DeepSeek thinking/JSON/pricing; Kaggle resources. Các nghiên cứu mới xuất hiện khi tìm kiếm được xem là đầu mối, chưa tự động thêm vào MVP.

| Loại kết luận | Căn cứ | Mức diễn giải |
|---|---|---|
| Dữ liệu/artifact đã có | File inventory, JSON/TSV/JSONL và code local | Đọc cấu trúc và source; không đồng nghĩa chạy lại toàn pipeline/hash 0,92 GB |
| Hành vi thư viện/API | Tài liệu sơ cấp bên dưới | Contract tại ngày đọc; xác nhận lại khi pin runtime/chạy API |
| Số giờ, chọn architecture, gate | Phân tích thiết kế theo phạm vi master | Dự toán/khuyến nghị; chưa đo trên tài khoản của nhóm |
| Applicability/relevance/correctness | Cần evidence và human judgment | Hiện còn mở; không suy từ tính hợp lệ của schema |

Trang Kaggle GPU guidance được truy cập nhưng không trả nội dung có thể trích xuất trong lượt này. Vì vậy không xác nhận con số quota hiện hành hoặc phần cứng tài khoản. Kế hoạch chỉ yêu cầu kiểm trực tiếp lúc pilot và có nhánh CPU/cache; không dựa vào mức quota được nhớ hoặc tổng ba tài khoản.[^9]

## Khoảng trống đã kiểm

### 1. Nguồn dữ liệu nhiều nhưng đầu vào mô hình chưa được khóa

[START-HERE](../../START-HERE.md) và [profile](../../02_datasets/processed/profile-summary.json) mô tả 90 incidents, 30 families và split 54/18/18. Inventory gồm 270 telemetry Parquet cộng 90 injection files. Những bản ghi nguồn chứa tên case và thông tin nhãn không được chuyển nguyên hàng sang inference.

Audit cho thấy cả 90 observation bundles còn trường family và split. Đây là metadata phục vụ quản lý, không phải bằng chứng quan sát cần cho mô hình. Plan 02 phải tạo export dùng allowlist; provenance gốc và join tới nhãn giữ riêng. Gọi thư mục hiện tại là observations chưa đủ để bảo đảm không lộ gold. Nguồn: [observations](../../02_datasets/processed/observations.jsonl), [inventory](../../02_datasets/acquired/inventory.tsv), [prepare-incidents.py](../../scripts/prepare-incidents.py).

Một khác biệt cần đặc tả, chưa đủ để kết luận là bug: metric summaries lưu end tại giây cuối sample, còn bundle dùng end cộng một giây cho cửa sổ nửa mở. Cả 6.603 summaries có khác biệt ấy. Test boundary nên kiểm chuyển đổi inclusive/exclusive và units của từng modality; không sửa raw để ép mọi trường end bằng nhau.

### 2. Corpus lịch sử có provenance, nhưng chưa có chứng cứ áp dụng đầy đủ

Historical corpus chứa 74 documents/580 chunks; current corpus 73/598. Hai snapshot có nhiều đường dẫn chung nên không thể coi là hai nguồn độc lập hoặc trộn vào index chính mà không xử lý trùng. Có 12 title bắt đầu bằng copyright, 61 chunks dài không quá 40 ký tự và cả 580 token counts đang null trong lần đọc cấu trúc này. Các con số ấy chỉ chứng minh cần audit; chưa đo được tác hại tới retrieval. Nguồn: [historical snapshot](../../03_collection_plan/knowledge-corpus-historical/snapshot.json), [documents](../../03_collection_plan/knowledge-corpus-historical/documents.jsonl), [chunks](../../03_collection_plan/knowledge-corpus-historical/chunks.jsonl).

Commit trước thời điểm incident chứng minh điều kiện thời gian, không chứng minh đúng phiên bản deployment. Plan 03 cần giữ trạng thái unknown khi thiếu evidence, ghi applicability theo loại khuyến nghị và đưa cảnh báo vào answerability. Chuẩn hóa title/chunking có thể làm số chunks khác 580; đó là derivative mới với mapping và lineage, không phải lý do ép count cũ hoặc tái dùng qrels sai ID.

### 3. Query hiện tại có nguy cơ mất tín hiệu theo thứ tự service

Code chuẩn bị chọn và giới hạn logs theo service, rồi query chỉ lấy tám logs đầu sau sắp xếp, mỗi đoạn cắt theo ký tự. Vì vậy cả selection lẫn rendering cần audit. Nếu mỗi representation tự chọn một tập log khác nhau, kết quả sẽ trộn ảnh hưởng lựa chọn evidence với ảnh hưởng chuẩn hóa ngôn ngữ. Nguồn: [prepare-incidents.py](../../scripts/prepare-incidents.py).

Khuyến nghị của phân tích: giữ selection ledger chung cho R1/R2 và ghi chính xác phần enrich của R3. R1/R2 phải giữ cùng evidence IDs/source spans cả sau token budgeting; chọn phần chung vừa giới hạn của cả hai, không dùng số token R2 tiết kiệm để thêm evidence trong ablation chuẩn hóa. Chuẩn hóa bảo toàn HTTP codes, exception, service names và identifiers có ý nghĩa; thay đổi policy khử định danh phải có test. Chọn representation trên dev thuộc plan 08, trong khi plan 04 cung cấp variants và công cụ.

### 4. BM25 preview là tài nguyên tái dùng, chưa là bộ baseline hoàn chỉnh

[preview-retrieval.py](../../scripts/preview-retrieval.py) có BM25 thuần Python và tie-break ID; seed pool có 400 candidates cho 20 train incidents. Chưa có dense/hybrid hoặc human judgments. Ranking BM25 có thể ngắn/rỗng khi không có lexical match, nên runner mới phải ghi candidate count và trạng thái thật, không padding bằng chứng giả. Nguồn: [pilot status](../../05_research/retrieval-preview/pilot-pool-status.json), [annotation status](../../03_collection_plan/annotation-kit/status.json).

E5-small-v2 là ứng viên cho retrieval tiếng Anh, embedding 384 chiều, prefix query/passage và giới hạn 512 tokens theo card. Những thông số này đặt yêu cầu tokenizer/prefix/cache, không chứng minh chất lượng trên logs.[^3] Với vài trăm chunks, exact search là lựa chọn thiết kế đơn giản; chỉ thêm index service khi pilot chứng minh cần thiết.

RRF cộng đóng góp theo thứ hạng, phù hợp khi BM25 và cosine khác thang. Constant 60 được dùng trong nghiên cứu gốc; dùng nó làm điểm khởi đầu giúp hạn chế tuning, không tạo cam kết hybrid thắng.[^4] Reranker nhận cặp query–passage và chỉ sắp xếp lại candidates đã có; kiểm chi phí/truncation rồi quyết định trước F1.[^5]

### 5. Annotation là công việc mới, không phải chuyển định dạng từ gold injection

RCAEval mô tả benchmark RCA dựa trên telemetry; repository xác nhận RE2-OB có 90 ca cùng metrics/logs/traces.[^1][^2] Nhãn fault/service không cung cấp sẵn relevance incident→runbook, mức support hay reference explanation. Hiện [qrels template A](../../03_collection_plan/annotation-kit/qrels-annotator-A.tsv) chưa có grade người điền.

Template cũ có một relevance grade, trong khi master muốn passage primary/document secondary. Plan 06 cần schema target rõ ràng hoặc hai export, giữ phán quyết document riêng. Chấm đôi 56 core incidents là quyết định master mới; hướng dẫn cũ chỉ chấm đôi pilot không được dùng để âm thầm giảm phạm vi.

Relevance được định nghĩa theo cùng incident/task/window và corpus evidence, để R1/R2/R3 dùng chung phán quyết khi chỉ đổi cách biểu diễn. Query hashes thuộc provenance của pool. Candidates mới cần nhãn; đổi task hoặc nội dung evidence cần review lại phần ảnh hưởng. Quy tắc này tránh vừa ghi đè nhãn giữa variants vừa chấm lại không cần thiết những evidence không đổi.

### 6. Gói chuẩn bị và thí nghiệm cần hai loại validator khác nhau

[validate-research-pack.py](../../scripts/validate-research-pack.py) kiểm 0 judgments/NOT_RUN để bảo đảm gói chuẩn bị chưa giả kết quả. [freeze-research-pack.py](../../scripts/freeze-research-pack.py) tạo checksum gói, không kiểm quy trình F1/F2 hoặc độ mới của mọi receipt. Không sửa các điều kiện ấy để biến gói chuẩn bị thành benchmark hoàn tất.

Plan 08 phải có evaluator và freeze mới, kiểm chain cấu hình/data/qrels theo nội dung. [experiment-proposal.json](../../05_research/experiment-proposal.json) và bảng kết quả cũ cũng chưa khớp condition names/metrics của master; xây schema mới trong implementation, lưu nguồn cũ làm lịch sử.

## Lựa chọn phương án

| Phương án | Ưu điểm | Chi phí/rủi ro | Kết luận thiết kế |
|---|---|---|---|
| Giữ RE2-OB, hoàn thiện IR + grounded diagnosis | Tái dùng dữ liệu/provenance, bám mục tiêu NLP/AIOps | Cần human qrels và giới hạn applicability | Chọn làm MVP |
| Chuyển sang technical QA có nhãn | Có thể giảm công nối telemetry với knowledge | Đổi nhiệm vụ, dữ liệu và câu hỏi nghiên cứu | Dự phòng nếu pilot cho thấy evidence coverage không đủ và giảng viên chấp thuận |
| Thêm graph, agents hoặc fine-tuning | Có thể mở câu hỏi nghiên cứu mới | Nhiều thành phần/đối chứng, dữ liệu nhãn hạn chế | Để sau MVP; mở plan mới từ lỗi thực nghiệm cụ thể |

Đối với tổ chức tài liệu, một master dài dễ đọc overview nhưng khó giao quyền sở hữu. Một plan cho từng task rất nhỏ tạo quá nhiều giao diện. Mười plan ứng với đúng mười mục, mỗi plan ba phase nội bộ, là mức tách phù hợp: giữ phạm vi gốc và vẫn có điều kiện bàn giao độc lập.

Không đề xuất backend/frontend/services riêng cho demo. Một ứng dụng Python cục bộ đọc artifacts phù hợp mục tiêu trình bày; phần live chỉ được nối khi đủ quyền và tài nguyên. Đây là lựa chọn giảm công tích hợp, không phải kết luận hiệu năng đã đo.

## Khả năng của Codex theo hạng mục

| Plan | Codex có thể làm khi triển khai được yêu cầu | Con người hoặc điều kiện ngoài code | Đầu ra cần nghiệm thu |
|---|---|---|---|
| 01 Phạm vi | Draft charter, literature matrix, decision log, thư xin phép để nhóm xem | Rubric thật, phân người/giờ, giảng viên trả lời | Protocol có owner và các quyết định chưa đóng được đánh dấu |
| 02 Dữ liệu | Export allowlist, schema/units, privacy checks, notebook smoke, manifests | Quyền chia sẻ, tài khoản Kaggle và review payload | 90 IDs hợp lệ, gold riêng, runtime receipt |
| 03 Corpus | Audit metadata, tokenizer/chunking, dedup, registry/offset validation | Applicability và evidence thiếu cần người duyệt | Corpus derivative có provenance và unknown minh bạch |
| 04 Biểu diễn | Selection ledger, R1/R2/R3, clipping/entity tests | Review tín hiệu chuyên môn trên train | Variants tái lập, sẵn sàng cho ablation dev |
| 05 Retrieval | BM25/dense/RRF, cache, runner, candidate export, tests | GPU/weights nếu optional rerank được chọn | Ba runner, pilot rankings và failure ledger |
| 06 Annotation | Pooling, blinded forms, merge không ghi đè, agreement/export | Hai người chấm độc lập và adjudicator | Qrels/reference thật; F2 chỉ sau F1 |
| 07 Generation | Provider/mock, context/validator, retry/budget/cache, tests | API/local-model được phép, key và trần chi | Adapter cùng pilot thực nếu được phép |
| 08 Đánh giá | Fixtures, F1/F2 checks, runs, metrics/statistics/figures | Human support review, xử lý protocol deviation | Kết quả đủ mẫu số và sáu family deltas |
| 09 Demo | UI cục bộ, citation navigation, cache/live labels, backup | Tổng duyệt và giải thích trước lớp | Demo truy từng claim về đoạn nguồn |
| 10 Bàn giao | Draft report/slides, tables, reproduction scripts/checklist | Xác nhận nội dung/đóng góp/nộp bài | Gói nộp có nguồn, hashes và limitations |

Không ước lượng phần trăm tự động hóa hoặc số giờ tiết kiệm trước khi có pilot. Một phần code được Codex tạo nhanh vẫn đòi thời gian review, chạy trên môi trường thật và hiểu để bảo vệ đồ án.

## Thiết kế thực nghiệm và giới hạn

Hai lớp đánh giá phải tách: retrieval có tìm được evidence thích hợp không, và generator có đưa ra chẩn đoán đúng với lời giải thích được hỗ trợ không. ALCE phân biệt correctness với citation quality; nhóm cần rubric incident riêng, không lấy thẳng metric QA làm gold cho RCA.[^6] Citation ID tồn tại chỉ là kiểm tra cấu trúc, khác với support về nội dung.

Primary comparison được chọn trên dev rồi khóa; test có 18 incidents nhưng chỉ sáu families. nDCG chính lấy trung bình trên cùng tập incidents đủ điều kiện; contrast lấy trung bình paired incident deltas. Family deltas là diagnostic, family không có incident đủ điều kiện nhận undefined. Leave-one-family-out và cluster bootstrap phải tính lại cùng primary statistic sau khi bỏ/lấy mẫu families, giữ pairing. Không trình bày telemetry rows như cỡ mẫu độc lập. Nếu khoảng bất định rộng hoặc hybrid không thắng, đó vẫn là kết quả đáp ứng câu hỏi nghiên cứu.

Qrels dựa trên pool nên recall phải được mô tả là pooled. Khi không có relevant evidence được chấm, nDCG/recall không xác định theo protocol của đồ án; vẫn giữ incident ấy trong đánh giá localization/abstention. Ranking rỗng trên ca có relevant qrels thì bằng 0, khác với ca không có relevant judgments. Quy tắc mẫu số và missingness phải được code hóa trước xem test.

Tuning trên train/dev có thể làm xuất hiện candidates mới: cần bổ sung pool/qrels trước dùng score để chọn cấu hình. Khóa hệ thống F1 trước tạo test pool, rồi F2 khóa qrels test. Sau F1 không đổi representation/prompt vì một test case xấu. Bug thực phải có deviation record, giữ bản gốc và chạy lại đối xứng các conditions bị ảnh hưởng.

No-RAG vẫn nhận observations và được dẫn observation IDs; phần bị loại là knowledge ngoài incident. Dùng cùng generator, prompt contract, decoding và ngân sách; không ép token bằng cách nhét context rỗng. Thiếu corpus evidence phải có abstention/unknowns, đồng thời báo coverage để tránh hệ thống có vẻ tốt chỉ vì không trả lời.

## Nguồn lực và thứ tự ưu tiên

Master ước tính 308–374 giờ-người; có dự phòng khoảng 370–449, tức 15,4–18,7 giờ/người/tuần trong 8 tuần. Đây là dự toán chưa đo. Annotation 84–150 giờ là đường găng: calibration năm ca cần đo tốc độ, số cặp sau dedup và công đọc evidence trước khi nhóm cam kết lịch.

DeepSeek pricing hiện xác nhận `deepseek-flash` tương ứng V4.1 Flash; mức peak cache-miss input/output là $0,30/$1,20 mỗi triệu tokens.[^7] Chi phí chỉ là biến đầu vào của công thức, cần kiểm lại lúc chạy. Với giả định 280 requests ×7.000 input ×768 output, một lượt khoảng $0,846 chưa retry; đây không phải hóa đơn hoặc mức chi được duyệt.

Thinking mặc định bật; cần cấu hình tắt rõ cho pilot non-thinking, không trông chờ tham số sampling có tác dụng giống nhau giữa các chế độ.[^8] JSON mode cần thiết lập output và prompt tương ứng, nhưng tài liệu vẫn ghi nhận khả năng empty content; validator và ledger phải giữ lỗi, không gọi lại cho đến khi chẩn đoán đúng.[^10]

Model API không có snapshot bất biến trong contract hiện dùng, nên tái lập bằng request/config + cached outputs là cam kết thực tế hơn tái sinh đúng từng token. Tách replay, resume cùng cohort và chạy đợt mới; tên alias không đủ làm cache key xuyên thời gian.

Ưu tiên công việc: audit/export và corpus/query → runners/pool → human qrels → generation/dev selection → F1/F2 và test → demo/report. Khi thiếu thời gian, cắt trang trí và ablation mở rộng trước, giữ core56/test18, đối chứng và integrity. Không giảm test theo điểm số, không lấy reference tự sinh làm human ground truth.

## Nguồn sơ cấp

1. Pham, L. và cộng sự. [RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data](https://arxiv.org/abs/2412.17015), preprint 2024, phiên bản công trình WWW 2025. Đọc abstract/metadata, không tuyên bố đọc lại toàn văn trong đợt này.
2. Nhóm RCAEval. [Repository chính thức](https://github.com/phamquiluan/RCAEval), README, truy cập 13/09/2026. Dùng mô tả dataset/format; dữ liệu local theo revision đã lưu, không tự cập nhật sang main.
3. intfloat. [E5-small-v2 model card](https://huggingface.co/intfloat/e5-small-v2), truy cập 13/09/2026. Dùng contract input/vector/token limit; không dùng điểm benchmark của card làm điểm đồ án.
4. Cormack, G. V., Clarke, C. L. A., Büttcher, S. [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), SIGIR 2009, pp.758–759. Đọc công thức, pilot và giới hạn suy rộng.
5. BAAI. [BGE-reranker-base model card](https://huggingface.co/BAAI/bge-reranker-base), truy cập 13/09/2026; bổ sung [snapshot local](../../05_research/source-snapshots/baai--bge-reranker-base-readme.md). Contract query–passage; optional workload chưa đo.
6. Gao, T., Yen, H., Yu, J., Chen, D. [Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/), EMNLP 2023, pp.6465–6488. Dùng định nghĩa các trục evaluation qua abstract/metadata.
7. DeepSeek. [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/), đọc trực tiếp 13/09/2026. Dùng model name và mức peak cho dự toán minh họa.
8. DeepSeek. [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/), đọc 13/09/2026. Dùng toggle/default và giới hạn sampling.
9. Kaggle. [Efficient GPU Usage Tips](https://www.kaggle.com/docs/efficient-gpu-usage), truy cập 13/09/2026 nhưng không đọc được nội dung qua công cụ. Không dùng làm bằng chứng quota hiện hành.
10. DeepSeek. [JSON Output](https://api-docs.deepseek.com/guides/json_mode/), đọc 13/09/2026. Dùng điều kiện JSON và khả năng empty/truncated output.

[^1]: Pham và cộng sự, [RCAEval](https://arxiv.org/abs/2412.17015), 2024/2025.
[^2]: Nhóm RCAEval, [README chính thức](https://github.com/phamquiluan/RCAEval), truy cập 13/09/2026.
[^3]: intfloat, [E5-small-v2](https://huggingface.co/intfloat/e5-small-v2), truy cập 13/09/2026.
[^4]: Cormack và cộng sự, [RRF](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), SIGIR 2009.
[^5]: BAAI, [BGE-reranker-base](https://huggingface.co/BAAI/bge-reranker-base), model card và snapshot local.
[^6]: Gao và cộng sự, [ALCE](https://aclanthology.org/2023.emnlp-main.398/), EMNLP 2023.
[^7]: DeepSeek, [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/), 13/09/2026.
[^8]: DeepSeek, [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/), 13/09/2026.
[^9]: Kaggle, [GPU guidance](https://www.kaggle.com/docs/efficient-gpu-usage); chỉ xác nhận đường dẫn, chưa xác minh quota.
[^10]: DeepSeek, [JSON Output](https://api-docs.deepseek.com/guides/json_mode/), 13/09/2026.

## Bước tiếp theo và câu hỏi mở

Bắt đầu plan 01 và audit local trong plan 02. Sau export contract, triển khai 03/04 song song; tạo pilot pool từ 05 và tổ chức calibration trong 06. Các hạng mục độc lập được liên kết ở [mục lục](../260913-independent-plans-index.md), với [quy ước bàn giao](260913-independent-plans-contracts.md).

Chưa rõ rubric/hạn nộp chính thức, giờ thật mỗi thành viên, quyền API/local model, ngân sách và ngôn ngữ chấm; plan 01 có đầu việc để đóng. Deployment compatibility, corpus answerability, annotation speed và tài nguyên Kaggle phải được kiểm bằng evidence/pilot. Các khoảng trống ấy không được chuyển thành giả định đã được xác nhận.
