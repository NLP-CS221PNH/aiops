# Nghiên cứu và chuẩn bị dữ liệu AIOps với Hybrid RAG

## Kết quả chính

Phạm vi dữ liệu trọng tâm của kế hoạch đã được chuyển thành artifact có thể dùng: toàn bộ **90 ca RCAEval RE2–Online Boutique**, telemetry gốc có kiểm checksum, observations và gold riêng, kho tài liệu có phiên bản, metadata paper bổ sung và bộ hồ sơ annotation. Bộ này cho phép bắt đầu kiểm dữ liệu, mapping bằng chứng và triển khai baseline. Nó chưa phải một benchmark đã có human qrels và kết quả mô hình.

Lựa chọn khoa học giữ đúng đề cương: so sánh BM25, dense, hybrid và reranking trên cùng corpus/query, rồi kiểm tra việc cải thiện evidence retrieval có chuyển thành câu trả lời đúng và có dẫn chứng không. Không có kết luận hybrid thắng được đưa ra trước thí nghiệm. Thiết kế cần phân biệt nhãn service/fault của nguồn, qrels bằng chứng và correctness/grounding của câu trả lời.

Một rủi ro lớn đã được xử lý ở cấp thời gian: snapshot tài liệu hiện tại mới hơn telemetry 2024. Đã bổ sung corpus ghim commit trước năm 2024 và kiểm timestamp với 90 cửa sổ quan sát. Corpus cũ trở thành lựa chọn chính trong cấu hình đề xuất; việc tương thích với phiên bản ứng dụng/cluster thực tế và mức đủ bằng chứng vẫn cần được duyệt. [Corpus và annotation](knowledge-and-annotation.md).

## Mục lục

1. [Mức hoàn thiện và bằng chứng](#mức-hoàn-thiện-và-bằng-chứng)
2. [Phát hiện từ dữ liệu](#phát-hiện-từ-dữ-liệu)
3. [Nghiên cứu tài liệu và thiết kế](#nghiên-cứu-tài-liệu-và-thiết-kế)
4. [Nguồn tri thức và chống rò rỉ](#nguồn-tri-thức-và-chống-rò-rỉ)
5. [Thực nghiệm tiếp theo](#thực-nghiệm-tiếp-theo)
6. [Nguồn, phương pháp và giới hạn](#nguồn-phương-pháp-và-giới-hạn)

## Mức hoàn thiện và bằng chứng

| Hạng mục của plan | Kết quả hiện tại | Bằng chứng trên đĩa |
|---|---|---|
| Chọn nguồn có gold đúng loại | RE2-OB; MIT theo phạm vi công bố của tác giả | [Source registry](../02_datasets/acquired/meta/source-registry.json) |
| Tải mẫu trước rồi đủ subset | 90 ca, 360 tệp, 922,484,805 bytes; 270 Parquet khớp hash upstream | [Acquisition status](../02_datasets/acquired/meta/acquisition-status.json) |
| Kiểm schema, thời gian, labels | Đã đọc toàn bộ selected telemetry, lập profiles | [Profile](../02_datasets/processed/profile-summary.json) |
| Observations và labels tách riêng | 90 observation bundles; gold nằm nhánh labels | [Observations](../02_datasets/processed/observations.jsonl) |
| Knowledge snapshot có provenance | Historical 74/580 docs/chunks; current 73/598 riêng | [Historical manifest](../03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl) |
| Bibliography bổ sung metadata | 1,009 record; 1,005 khớp định danh; 1,003 mục BibTeX; 6 bibliography chưa đủ thông tin | [Enriched catalog](../01_papers/enriched/catalog-enriched.tsv) |
| Đọc nhóm ưu tiên | 50 ghi chú có read-depth, task, phương pháp và giới hạn | [Paper research](paper-research.md) |
| Qrels và rubric | Forms cho 90 ca; seed pool 20 train incidents/400 candidates; chưa chấm | [Annotation kit](../03_collection_plan/annotation-kit/README.md) |
| Baseline quality và confidence intervals | Chưa chạy; bảng kết quả còn trống | [Results template](experiment-results-template.tsv) |

Các cột hoàn thiện nói về artifact đã có, không nâng thành kết luận chất lượng. Registry 102 nguồn/tập con đã được kiểm tính nhất quán và quyết định vai trò; chỉ nguồn cần cho MVP được tải theo kế hoạch. Số 102 không phải số dataset độc lập, và số 1.009 không phải số paper đã đọc toàn văn.

## Phát hiện từ dữ liệu

Raw subset có **15,053,223 dòng log**, **34,461,235 trace spans** và **128,742 metric timesteps**. Số này được tính từ tệp đã tải, không suy từ tên bộ dữ liệu hoặc từ mirror. Mỗi case có đủ metrics/logs/traces. Khác modality có timestamp unit khác nhau; pipeline dùng Unix seconds cho metrics/logs và Unix milliseconds cho trace start, bỏ trường giờ không có đủ ngày/timezone. [Phân tích dữ liệu](dataset-research.md).

Observation windows là toàn cửa sổ metric cung cấp, được mô tả half-open để xử lý trace timestamps nhất quán. Đây là thiết kế hồi cứu offline, không dùng injection time để tìm onset và không giả rằng hệ thống đã có detector online. Metric summaries mô tả thay đổi đầu/cuối cửa sổ, không là chứng minh bất thường hay quan hệ nhân quả. Trace duration còn unit assumption được ghi rõ; nonzero status không mặc nhiên được gọi là lỗi nếu chưa xác nhận semantics của nguồn.

Tập nhỏ có nhiều dòng telemetry nhưng chỉ **90 đơn vị incident**, thuộc **30 service×fault families**. Đề xuất split 54/18/18 giữ các repetition cùng family và cân theo fault. Đây là split artifact được ghim để pilot; cần duyệt điều kiện tổng quát hóa trước khi đóng băng final test. Không chia ngẫu nhiên các dòng log thành train/test hoặc gọi nhiều seed là nhiều incident độc lập.

Các log/trace excerpts có source file IDs và row offsets; raw giữ tên thư mục opaque để không lộ service/fault từ đường dẫn. Labels, tên case gốc và injection files nằm nhánh riêng. Query được tạo bằng quy tắc từ observations, có cờ synthetic; telemetry tải về là dữ liệu benchmark gốc. Cờ query synthetic không có nghĩa toàn bộ telemetry được mô hình sinh trong đợt này.

Kiểm pattern trong cửa sổ log phát hiện email và IPv4, vì vậy bản trích xuất đã khử định danh nhất quán theo incident. Raw được giữ nguyên để tái lập. Không thấy một số credential patterns đã định nghĩa không đủ để chứng nhận mọi file sạch secret/PII; phạm vi regex và số đếm nằm trong profile. Không gửi raw lên mô hình bên ngoài khi chưa xử lý phù hợp.

RE2-TT được giữ như nguồn mở rộng theo plan: đã pin metadata, chưa tải gần 1,97 GB telemetry. Có một case thiếu logs theo index và known-data notes. Trước cross-system test phải khóa policy xử lý missing modality; không loại ca sau khi thấy kết quả. TechQA, MTRAG và ITBench-Lite giữ vai trò dự phòng task, không nhập điểm QA của chúng vào kết quả RCA.

## Nghiên cứu tài liệu và thiết kế

Bibliography được cập nhật từ metadata của nơi xuất bản/đăng ký định danh và trang nguồn: DataCite cho arXiv, Crossref cho DOI và các trang ACL/OpenReview/primary tương ứng. Bản gốc 1.009 IDs được bảo toàn; năm gap DOI sống ở overlay riêng. Dữ liệu bổ sung có source/cache, trạng thái khớp định danh và year basis; năm preprint không tự thành năm conference. Publication overlay tách preprint, proceedings, journal thật và conference-journal-series; SJR 2024 Q1 chỉ được đếm khi có sidecar tracked, không suy từ `@article`. Core related-work có 45 mục, còn priority-reading giữ nguyên 50 mục. [Tổng hợp và bibliographic limits](paper-research.md).

Nhóm tài liệu ưu tiên cần được đọc theo trục **task → observations → labels → knowledge → split → evaluation**, thay vì theo kích thước mô hình hoặc một score riêng trong abstract. Tài liệu cloud production có thể chứng minh một kiến trúc khả thi nhưng không cung cấp raw incident để tái lập. Bài log anomaly detection không cung cấp causal RCA gold; bài retrieval tổng quát có qrels tốt nhưng khác miền incident. Các ghi chú đọc giữ những khác biệt này để viết related work chính xác.

Thiết kế đề xuất chọn một bi-encoder tiếng Anh nhỏ có input contract rõ, BM25 và rank fusion làm bước đầu. E5-small-v2, BGE-small-en-v1.5 và BGE-reranker-base có cards/config/revisions lưu cục bộ. Các model weights chưa được tải, chưa chọn generator, chưa đo latency/VRAM. Thông số proposal là điểm bắt đầu pilot, không phải hyperparameters thắng trên test. [Thiết kế chi tiết](method-and-experiment-design.md) · [Pinned model resources](source-snapshots/support-resources.json).

Một kết luận thiết kế quan trọng là reranker cần relevant evidence trong candidate pool. Nếu corpus sai version hoặc thiếu runbook, reranking không tạo được tri thức còn thiếu. Đọc failure cases và đo candidate recall trước sẽ quyết định hợp lý giữa cải thiện retrieval, bổ sung corpus hoặc mở nhánh graph. Graph/multi-agent/fine-tuning vẫn là mở rộng, đúng giới hạn đề cương.

## Nguồn tri thức và chống rò rỉ

Kho tri thức chính ghim ba repositories trước năm 2024: Online Boutique cho kiến trúc/service contract/config, Kubernetes cho troubleshooting nền tảng và Prometheus Operator cho alert runbooks. Mỗi document có raw source, commit, license snapshot, hash và text; mỗi chunk có offsets kiểm được. Supporting includes/YAML/diagram được giữ cùng license, không chạy các lệnh hay triển khai YAML.

Hai snapshot có nhiều nội dung trùng hoặc khác phiên bản. Chúng phục vụ so sánh version policy, không phải hai tập độc lập để chia train/test. Tất cả mappings theo path/title hiện là candidates chưa chấm. Tên alert khớp triệu chứng không chứng minh đúng root cause; ứng dụng hiện tại chưa chứng minh đúng deployment trong RCAEval. [Comparison và source manifests](knowledge-and-annotation.md).

Historical commit time bảo thủ là bằng chứng snapshot tồn tại trước incident; không giả là published_at của từng trang. Chưa có commit ứng dụng/cluster gốc của các ca nên tính áp dụng vẫn cần review. Một experiment có thể trung thực dùng tài liệu frozen hiện tại để hỗ trợ phân tích offline, hoặc dùng snapshot cũ với scope được kiểm; không được đổi nhãn giữa hai condition mà giấu policy.

Evidence evaluation phải tách document/chunk và phải giữ unjudged khác grade 0. Bộ biểu mẫu hiện có hai người chấm độc lập, answerability riêng, adjudication và reference-answer blanks. Chưa có người thực sự chấm nên không có agreement hay gold qrels. Seed pool BM25 20 incident/400 candidates dùng snapshot tài liệu trước năm 2024 chỉ giảm công tìm dữ liệu ban đầu; vẫn cần thêm dense/hybrid vào pool theo plan.

## Thực nghiệm tiếp theo

Tuần dữ liệu của kế hoạch có thể tiếp tục bằng pilot annotation trên tập train. Duyệt khoảng 10–20 incident đại diện, xác nhận liệu người chấm có tìm thấy evidence hợp lệ và có hiểu nhãn nhất quán. Nếu tài liệu chỉ hỗ trợ bước kiểm tra chứ không hỗ trợ cause, ghi đúng evidence role; không nâng grade để tạo ground truth có vẻ đầy đủ.

Sau pilot, khóa split được review, corpus hash, qrels/adjudication, biểu diễn query và model/config. Baseline không RAG vẫn được đọc observations; các nhánh RAG dùng cùng generator và context budget. Báo IR, service localization, supported claims/citations và abstention thành các nhóm riêng. Tính uncertainty theo incident/family, không resample từng dòng log. [Protocol gốc](../00_plan/experiments_and_evaluation.md).

Kết quả có thể cho thấy hybrid không hơn BM25, hoặc retrieval tốt hơn nhưng diagnosis không tốt hơn. Những trường hợp này trả lời câu hỏi nghiên cứu nếu đối chứng công bằng. Không có cơ sở hứa phần trăm giảm hallucination, MTTR hoặc chi phí từ các artifact chuẩn bị. Độ đầy đủ và độ trung thực của protocol là tiêu chí đầu tiên.

## Nguồn, phương pháp và giới hạn

Đối chiếu nguồn và thu thập bắt đầu ngày 12/09/2026; thời điểm tổng hợp 2026-09-13T00:28:56+07:00. File receipts lưu UTC. Kế hoạch gốc là tài liệu nội bộ được cung cấp; nguồn công khai được dùng để xác minh dữ liệu, metadata và input contract. Nội dung retrieved được đọc như dữ liệu, không làm chỉ dẫn thực thi.

Các nguồn chính: [RCAEval pinned release](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e), [RCAEval official repository](https://github.com/phamquiluan/RCAEval), [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo), [Kubernetes website](https://github.com/kubernetes/website), [Prometheus Operator runbooks](https://github.com/prometheus-operator/runbooks), [DataCite](https://api.datacite.org), [Crossref REST API](https://api.crossref.org), [E5 card](https://huggingface.co/intfloat/e5-small-v2), [MTRAG](https://github.com/IBM/mt-rag-benchmark), [ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite). Các trang/commit cụ thể và mục đã sử dụng nằm ngay trong các báo cáo nhánh và manifests, không chỉ ở danh sách domain.

Kiểm tra tích hợp hiện tại: **PASS**; [validation JSON](../04_audit/research-pack-validation.json) ghi từng điều kiện. Kiểm hash/offset/split chứng minh tính nhất quán artifact, không chứng minh nhãn chấm đúng, nguồn phủ đủ hoặc mô hình tốt. Trang HTML được tạo như mục lục offline; môi trường duyệt tự động chặn local-file URL, nên chỉ kiểm tra cấu trúc và cú pháp, không báo đã kiểm UI bằng browser.

Những việc còn mở: 6 bibliography chưa đủ thông tin, trong đó 4 record chưa khớp định danh; human qrels và reference answers; compatibility theo deployment; evidence coverage; generator/phần cứng và model evaluation; yêu cầu chính thức của lớp CS221. Khớp định danh không có nghĩa mọi trường xuất bản đã được xác minh: hiện 366 mục có venue/year được xác minh. Danh sách này được giữ rõ để tiếp tục nghiên cứu, không được lấp bằng metadata suy đoán, nhãn giả hoặc kết quả thí nghiệm chưa chạy.
