# Charter CS221 — hỗ trợ phân tích incident offline

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-reviewed.1` · **nghiệm thu bằng review Codex theo ủy quyền người dùng**.

## Kết quả và phạm vi

Trong tám tuần tương đối, nhóm ba người xây dựng và đánh giá một hệ thống hỗ trợ phân tích sự cố offline cho RCAEval RE2–Online Boutique. Đầu vào là incident ID opaque, cửa sổ quan sát có units, log chọn lọc và observations metrics/traces đã kiểm; đầu ra là các service/fault nghi ngờ, giải thích ngắn liên kết evidence IDs, phần chưa biết và bước kiểm tra đề xuất. Đóng góp NLP gồm biểu diễn log bảo toàn thực thể, so sánh lexical/dense/hybrid retrieval trên cùng tri thức, và kiểm chất lượng giải thích có dẫn chứng. Thành công là thí nghiệm công bằng, có nhãn người, failures và khả năng tái tính; hybrid thua vẫn là kết quả hợp lệ.

Nguồn phạm vi: [đề cương](../../00_plan/project_proposal.md), [master](../../plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [contract mới](../../plans/reports/260913-independent-plans-contracts.md). Phạm vi được kế thừa từ plan người dùng yêu cầu; không phải rubric chính thức hay chữ ký của nhóm.

## Ba câu hỏi nghiên cứu

| RQ | Câu hỏi và vai trò | Ranh giới |
|---|---|---|
| RQ1 | Biểu diễn selected logs, normalized logs và multimodal bundle ảnh hưởng retrieval thế nào? Phân tích phụ. | Chỉ train/dev; R1/R2 giữ cùng evidence IDs/spans sau budgeting; chọn một representation trước F1. |
| RQ2 | Hybrid BM25+dense khác baseline đơn mạnh hơn trên dev thế nào? Câu hỏi chính. | Passage nDCG@5; dev hòa chọn BM25; khóa trước test; không yêu cầu hiệu số dương. |
| RQ3 | Khi generator và context policy cố định, retrieval ảnh hưởng service localization, support/citations và abstention thế nào? | Chạy generator chỉ khi quyền tương ứng đủ; chưa có kết quả hoặc phán quyết người. |

## Inventory có bằng chứng

| Sản phẩm | Đã có trong pack | Chưa có/giới hạn | Nguồn |
|---|---|---|---|
| Dữ liệu và split | 90 incidents, 30 service×fault families; 54 train / 18 dev / 18 test; 18/6/6 families, ba repetitions/family | Bản export inference mới và boundary audit thuộc plan 02 | [split-map](../../02_datasets/processed/split-map.tsv) |
| Observations | 90 bundles trong gói chuẩn bị | Không dùng nguyên script chuẩn bị làm inference runtime; nó còn xử lý gold | [START-HERE](../../START-HERE.md), [observations](../../02_datasets/processed/observations.jsonl) |
| Tri thức | Historical 74 documents/580 chunks; current 73/598 | Hai snapshot có overlap; historical timestamp chưa chứng minh deployment compatibility; corpus derivative chưa freeze | [historical](../../03_collection_plan/knowledge-corpus-historical/README.md) |
| Annotation | Forms; BM25 seed pool 20 train incidents/400 candidates | **0 human judgments**; core 56 = 20 train + 18 dev + 18 test là kế hoạch chấm, không phải qrels đã có | [status](../../03_collection_plan/annotation-kit/status.json) |
| Literature | 1.009 catalog records, 50 reading notes | Không đồng nghĩa đã đọc toàn văn; ma trận lõi ghi reader/depth riêng | [paper research](../../05_research/paper-research.md), [matrix](literature-matrix.tsv) |
| Generation/quality | Model cards và cấu hình tham khảo | Chưa có baseline quality, human support judgments hoặc benchmark trong lượt này | [thiết kế](../../05_research/method-and-experiment-design.md) |

Kiểm đếm độc lập và SHA-256 được lưu tại [source inventory](../validation/source-inventory.json). `README.md` gốc mô tả gói trước thu thập và được giữ làm lịch sử; hiện trạng lấy từ structured files và `START-HERE.md`.

## Biên dữ liệu và ví dụ giao diện

Đây là ví dụ **schema**, không phải incident thật hay kết quả chạy:

```json
{"incident_id":"opaque-example-id","window":{"start":0,"end":60,"unit":"seconds","end_semantics":"exclusive"},"observations":[{"evidence_id":"obs-example-1","service":"service-from-observation","text":"redacted observed error"}]}
```

```json
{"incident_id":"opaque-example-id","candidate_causes":[],"supported_claims":[],"missing_information":["Chưa đủ bằng chứng"],"next_checks":[],"abstain":true}
```

Chỉ allowlist observations/evidence đã duyệt vào query, index, context và live demo. File observations nguồn hiện còn `scenario_family_id` và `split`, nên không phải inference export sẵn dùng; plan02 phải lọc tường minh. `scenario_family_id`, split, gold service/fault, injection time, original case path, qrels và reference claims ở private/evaluator; tuyệt đối không serialize chúng vào inference. Service xuất hiện thực trong observation là tín hiệu hợp lệ, khác gold service. Source pack dựng cửa sổ hồi cứu bằng thông tin chuẩn bị: phải kiểm/document window provenance; nếu dùng oracle onset, khai báo điều kiện benchmark thay vì gọi online detection. Labels và raw paths trong manifest nguồn chỉ phục vụ audit cục bộ.

## Ngoài phạm vi và nghiệm thu

Không đổi đề tài, chạy API/model, tải weights, tạo annotation, chạy thí nghiệm, upload/gửi thư hoặc triển khai plans 02–10 trong lượt plan 01. Không tự khắc phục hệ thống, graph/multi-agent RCA, fine-tuning, Train Ticket hay cam kết causal chain/giảm MTTR. Bibliography không phải corpus vận hành. Confidence label không là xác suất hiệu chỉnh nếu chưa calibration.

Gói review cần đủ charter, protocol MD/YAML, decision log có owner/hạn, 8–12 bài với mức đọc thật, working agreement, thư nháp, issue log và manifest kiểm hash được. Theo [amendment tự nghiệm thu](acceptance-amendment.md), G0 đạt bằng kiểm tra thực và review độc lập của Codex có receipt gắn hashes. Tên/giờ thật của nhóm vẫn chưa biết; chúng không là prerequisite nghiệm thu plan01 theo yêu cầu mới. Quyền API/payload/local/sharing/budget tách riêng và không tự được cấp khi G0 đạt. Các bất biến, thống kê và freeze sequence nằm trong [research protocol](research-protocol.md).

| Vai trò nhóm đề xuất | Tên thật | Phạm vi đã giao Codex kiểm | Xác nhận danh tính người thật |
|---|---|---|---|
| A | pending | Data boundary, nguồn và inventory | pending |
| B | pending | RQ, đối chứng, metrics và khả năng tái lập | pending |
| C | pending | Phạm vi, nguồn lực, điều phối và bàn giao | pending |

Ngày bắt đầu, hạn nộp/rubric, giờ cam kết và ngôn ngữ chấm giữ pending với mốc tương đối trong [decision log](decision-log.md). Tám tuần/ba người là ràng buộc kế hoạch, không phải 12 giờ Codex đã làm hoặc thời gian nhóm đã cam kết.
