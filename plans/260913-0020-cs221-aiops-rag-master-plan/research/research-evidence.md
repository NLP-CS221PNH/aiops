# Căn cứ nghiên cứu cho master plan CS221

## Tổng hợp

Khuyến nghị tiếp tục với RE2–Online Boutique và Hybrid RAG, vì gói nghiên cứu đã có telemetry, gold tách riêng và corpus có provenance. Công việc thiếu để hình thành một nghiên cứu có thể bảo vệ là applicability review, qrels người chấm, baseline so sánh công bằng, và đánh giá output. Sự khác nhau giữa số lượng dữ liệu thô và số incident độc lập phải được thể hiện trong thiết kế.

Phân biệt ba loại nội dung trong tài liệu này: **hiện trạng local** được đối chiếu artifact; **thông tin nguồn sơ cấp** có trích dẫn; **đề xuất thiết kế** do phân tích cho bài toán 8 tuần/3 người. Các tham số, số giờ và chi phí giả định không phải kết quả thí nghiệm.

## Mục lục

1. [Hiện trạng](#hiện-trạng-được-đối-chiếu)
2. [Bằng chứng kỹ thuật](#bằng-chứng-kỹ-thuật-và-giới-hạn)
3. [Quyết định](#quyết-định-thiết-kế)
4. [Nguồn](#nguồn)
5. [Bước tiếp theo](#bước-tiếp-theo-và-câu-hỏi-còn-mở)

## Hiện trạng được đối chiếu

| Claim | Bằng chứng local | Giới hạn |
|---|---|---|
| 90 incidents, train/dev/test 54/18/18 | [Profile](../../../02_datasets/processed/profile-summary.json), [split map](../../../02_datasets/processed/split-map.tsv) | 30 service×fault families; test chỉ 6 family |
| Historical 74 docs/580 chunks | [Snapshot](../../../03_collection_plan/knowledge-corpus-historical/snapshot.json) | Commit trước incident chưa chứng minh tương thích deployment |
| Chưa có nhãn người | [Annotation status](../../../03_collection_plan/annotation-kit/status.json) | Forms là placeholders, không phải qrels đã chấm |
| Seed pool chỉ BM25 | [Preview README](../../../05_research/retrieval-preview/README.md) | 400 candidates/20 train ca; chưa pool đủ phương pháp |
| Weights/generator/baseline chưa chạy | [Completion summary](../../../05_research/completion-summary.json), [method design](../../../05_research/method-and-experiment-design.md) | Có card/config khác có model hoạt động |

Audit code phát hiện query được dựng từ tám log đầu sau sắp service/time, cần kiểm service-order clipping. Corpus có metadata title copyright ở 12 tài liệu YAML/config; thay title cần tạo derivative có lineage. Hai điểm này là nguy cơ phương pháp, không phải bằng chứng đã đo retrieval kém. [Chuẩn bị incidents](../../../scripts/prepare-incidents.py), [documents historical](../../../03_collection_plan/knowledge-corpus-historical/documents.jsonl).

## Bằng chứng kỹ thuật và giới hạn

RCAEval cung cấp benchmark và môi trường đánh giá root-cause localization từ telemetry; nguồn công bố có nhãn root service/indicator. Điều đó không tự tạo qrels incident→runbook hay một bộ reference explanations. Subset 90 incident là artifact được chọn của nhóm, không phải toàn bộ benchmark. [^1][^2]

E5-small-v2 có input contract phù hợp để bắt đầu dense retrieval tiếng Anh. Prefix, normalization và truncation cần ghim trong cấu hình; card không chứng minh hiệu quả trên log của bộ hiện tại. [^3] RRF là phương pháp hợp thứ hạng của nhiều hệ thống; lựa chọn nó tránh phải hiệu chỉnh hai loại score khác thang. Hiệu quả báo trong bài gốc không phải kết quả cho RE2-OB. [^4]

BGE-reranker là ứng viên cross-encoder cho cặp query–passage; phải kiểm pair truncation và thời gian chạy thực trên Kaggle. Nếu evidence chưa vào candidates hoặc không có trong corpus thì reranking không thể bổ sung tri thức còn thiếu. [^5] ALCE tách correctness và citation quality trong đánh giá generation; đây là căn cứ để không đồng nhất một URL/ID hợp lệ với một câu giải thích được hỗ trợ. Rubric cho incident vẫn là sản phẩm nhóm phải chấm và kiểm riêng. [^6]

Kaggle có quota GPU theo tuần và tài nguyên thay đổi. Kế hoạch dùng checkpoint/caching và ưu tiên CPU cho công đoạn không dùng neural inference; không giả định GPU luôn sẵn hoặc nhân quota theo ba thành viên. Nguồn được kiểm ngày 13/09/2026; giới hạn tài khoản phải xem lúc chạy. [^7]

DeepSeek thông báo V4.1 Flash ngày 10/09/2026; nguồn API trực tiếp ngày 13/09/2026 xác nhận model name `deepseek-flash`. Kết quả tìm kiếm lưu đệm ban đầu vẫn hiện bảng V4 cũ; đối chiếu trực tiếp đã giải quyết sự khác biệt về model Flash và giá. Chỉ dùng bảng hiện hành, không lấy cached snippet làm giá cuối. Nguồn thông báo và trang pricing còn khác nhau về kế hoạch V4-Pro; master không phụ thuộc V4-Pro. [^8][^9]

API là dịch vụ có thể đổi model, nên lưu timestamp/config/request metadata và outputs thực. Tên model không tự bảo đảm immutable revision. Kế hoạch không cần context cực dài hay tính năng multimodal của dịch vụ để kiểm giả thuyết retrieval.

## Quyết định thiết kế

| Quyết định | Lý do | Bằng chứng nghiệm thu |
|---|---|---|
| Một corpus chính, ba IR baseline bắt buộc | Đủ kiểm contribution retrieval, hạn chế biến số | Cùng query/content/corpus, batch outputs và config hash |
| Exact dense search khởi đầu | Corpus nhỏ, chưa cần approximate/vector service | Pilot latency/memory thực và ranking có provenance |
| 56 ca có qrels cốt lõi | Không fine-tune nên chưa cần chấm hết train | 20 train/18 dev/18 test; A/B và final judgments |
| Pool top-10 union tối đa bốn hệ thống | Giới hạn tải mà vẫn phủ primary top-5 | Dedup count, judged@5=100% cho output cuối, deepen log |
| Passage nDCG@5 và một primary contrast | Tránh chọn metric/comparison sau test | Dev decision record, frozen protocol trước test |
| Family là cụm thống kê | Repetitions cùng scenario phụ thuộc nhau | Sáu test-family deltas, counts, uncertainty thăm dò |
| API conditional; local small-model fallback | Phù hợp nguồn lực và quyền môn học chưa chốt | Quyết định giảng viên, pilot tài nguyên, model/license record |

Qrels pooled là không đầy đủ: báo IDCG từ các nhãn đã có, pooled recall và judged coverage. Không biết relevance ngoài pool thì không suy chúng bằng 0 hoặc tuyên bố pooled recall là cận dưới của recall thật. Trường hợp không có evidence liên quan phải báo riêng cùng mẫu số.

Khóa hệ thống F1 trước test pooling; tạo pool bằng retriever đã khóa, chấm mù và khóa qrels F2, rồi scoring. Quy trình này tách nhu cầu dùng retriever để tạo nhãn khỏi việc lấy test feedback để tune. Nếu có thay đổi sau F1, phải ghi protocol amendment và xác định test không còn là phép đo chưa thấy trước.

## Phạm vi xác minh

Đối chiếu thực hiện ngày **13/09/2026, Asia/Saigon**. Nguồn nền gồm các công trình 2009–2025; thông tin tài nguyên/model dùng tài liệu dịch vụ đang có ở ngày kiểm. Phạm vi tập trung vào nguồn đã có và quyết định ảnh hưởng trực tiếp kế hoạch, không tự nhận là systematic literature review toàn bộ lĩnh vực hay đọc toàn văn 1.009 bài.

Các số hiệu chú thích trong phần thân nối với nguồn bên dưới. Các đề xuất pooling, cỡ mẫu, lịch và gate là phân tích cho đề tài, không gán cho tác giả các bài nghiên cứu.

## Nguồn

1. Pham, L. và cộng sự. [RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data](https://arxiv.org/abs/2412.17015). Preprint 2024; dùng để hiểu tác vụ/benchmark, không chuyển năm preprint thành năm venue.
2. Nhóm RCAEval. [Official repository](https://github.com/phamquiluan/RCAEval), mục Available Datasets/README. Truy cập 13/09/2026. Dùng nguồn dataset; local subset theo manifest đã ghim.
3. Wang, L. và nhóm intfloat. [E5-small-v2 model card](https://huggingface.co/intfloat/e5-small-v2). Truy cập 13/09/2026. Dùng input contract và giới hạn model.
4. Cormack, G. V., Clarke, C. L. A., Büttcher, S. [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf). SIGIR 2009. Dùng nguyên lý rank fusion.
5. BAAI. [BGE-reranker-base model card](https://huggingface.co/BAAI/bge-reranker-base). Truy cập 13/09/2026. Dùng contract pair scoring, không nhận benchmark của card là điểm đồ án.
6. Gao, T., Yen, H., Yu, J., Chen, D. [Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/). EMNLP 2023. Dùng phân biệt correctness/citation quality.
7. Kaggle. [Efficient GPU Usage Tips](https://www.kaggle.com/docs/efficient-gpu-usage) và [Notebooks documentation](https://www.kaggle.com/docs/notebooks). Truy cập 13/09/2026. Quota/availability cần xác nhận lại trên tài khoản.
8. DeepSeek. [Introducing DeepSeek-V4.1-Flash](https://www.deepseek.com/en/news/deepseek-v4-1-flash/). 10/09/2026. Dùng tên model/giai đoạn chuyển alias.
9. DeepSeek. [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/). Đọc trực tiếp 13/09/2026. Dùng bảng Flash hiện hành và công thức tính chi phí trong master.

## Bước tiếp theo và câu hỏi còn mở

Bắt đầu phase 01/02, đọc 5 train incidents và đo annotation calibration. Chốt quyền API, rubric chính thức và số giờ mỗi người trước cuối tuần 2. Deployment compatibility, evidence coverage và tốc độ chấm phải được chứng minh qua pilot; kế hoạch hiện giữ chúng là điều kiện cần kiểm, không kết luận sẵn đã đạt.

[^1]: Pham và cộng sự, [RCAEval paper](https://arxiv.org/abs/2412.17015), 2024.
[^2]: Nhóm RCAEval, [Official repository](https://github.com/phamquiluan/RCAEval), truy cập 13/09/2026.
[^3]: intfloat, [E5-small-v2 model card](https://huggingface.co/intfloat/e5-small-v2), truy cập 13/09/2026.
[^4]: Cormack và cộng sự, [RRF](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), SIGIR 2009.
[^5]: BAAI, [BGE-reranker-base](https://huggingface.co/BAAI/bge-reranker-base), truy cập 13/09/2026.
[^6]: Gao và cộng sự, [ALCE](https://aclanthology.org/2023.emnlp-main.398/), EMNLP 2023.
[^7]: Kaggle, [GPU usage guidance](https://www.kaggle.com/docs/efficient-gpu-usage), truy cập 13/09/2026.
[^8]: DeepSeek, [V4.1 Flash announcement](https://www.deepseek.com/en/news/deepseek-v4-1-flash/), 10/09/2026.
[^9]: DeepSeek, [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/), truy cập 13/09/2026.
