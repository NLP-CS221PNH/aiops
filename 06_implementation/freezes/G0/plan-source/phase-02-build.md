---
phase: 2
title: "Soạn protocol, ma trận bài lõi và phân công"
status: pending
priority: P1
effort: "6h"
dependencies: [1]
---

# Phase 02: Soạn protocol, ma trận bài lõi và phân công

## Amendment theo yêu cầu người dùng — 2026-09-13

Người dùng chỉ thị trong task hiện tại: **“tự check mọi thứ, không cần human input”**. Chỉ thị này thay điều kiện review người thật của riêng plan01 bằng **Codex và reviewer agent độc lập**, có actor/type, scope, thời gian, artifact hashes và bằng chứng kiểm. Không ghi AI review thành chữ ký, người đọc hoặc giờ cam kết của con người.

Tên A/B/C, giờ thực có, rubric và hạn môn học chưa biết vẫn được ghi rõ pending/unknown; không cần hỏi thêm để hoàn tất scope01. Quyền API/payload/local model/sharing/ngân sách giữ trạng thái thực tế; nhãn qrels và annotation người thật ở các plan sau không được tạo hoặc miễn thay. RQ, counts/split/core, conditions và F1/F2 giữ nguyên. Bàn giao scope01 là static handoff có paths/version/hash được reviewer kiểm, communication thực tế vẫn chưa gửi.

Bản trước amendment được giữ nguyên bytes cùng hashes tại [archive](../../06_implementation/reports/plan01-pre-automated-review/archive-manifest.json). Chỉ check acceptance/complete qua CLI sau khi independent review và strict G0 validator cho phiên bản amendment đều đạt; amendment này chưa tự là bằng chứng PASS.

## Tổng quan

Khóa thiết kế đề xuất bằng protocol cụ thể và phân bổ công cho ba người; còn quyền mô hình thì giữ nhánh quyết định có điều kiện.
Công dự kiến **6 giờ-người**; các checkbox là acceptance theo amendment, chỉ check sau bằng chứng cuối.
Codex điều phối phần plan01; reviewer agent độc lập kiểm bằng chứng. A/B/C là vai trò đề xuất cho nghiên cứu; chưa biết người thật không chặn review01. Các quyền bên ngoài và annotation thật ở plan sau vẫn cần bằng chứng riêng.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` trỏ tới sản phẩm triển khai; kiểm nội dung/hash và trạng thái thực ở receipts thay vì suy từ tên file.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Charter | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/project-charter.md` | Reviewer agent kiểm phạm vi |
| Decision log | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` | Reviewer agent kiểm các pending |
| Tổng hợp học thuật | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/literature_synthesis.md` | Codex chọn/đọc bài liên quan và reviewer agent kiểm bằng chứng |
| Đánh giá gốc | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/experiments_and_evaluation.md` | Reviewer agent kiểm baseline/metrics |

## Yêu cầu

- Primary contrast hybrid với baseline đơn mạnh hơn trên dev; hòa chọn BM25; khóa trước xem test.
- Passage nDCG@5 là primary; tài liệu-level dùng relevance riêng và collapse theo thứ hạng chunk xuất hiện đầu.
- G0/GB/GD/GH bắt buộc, GR optional; cùng generator/context policy; RQ1 giới hạn train/dev.
- Core 56 incident:20 train/18 dev/18 test; chưa có judgment; mọi final top-5 phải được chấm.
- Annotation là công người độc lập, Codex hỗ trợ tooling; 6 test families yêu cầu báo family deltas.

## Kiến trúc và ranh giới trách nhiệm

Charter → protocol.yaml + research-protocol.md → working agreement → literature matrix. Một protocol_id nối metric, split, freeze và quyết định; sửa tạo version mới có lý do.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/research-protocol.md` — Thiết kế RQ, metric và điều kiện.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/protocol.yaml` — Các lựa chọn có cấu trúc.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/team-working-agreement.md` — Owner/reviewer và lịch nhóm.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/literature-matrix.tsv` — 8–12 bài thực sự dùng.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` — Ghi đề xuất và các quyết định mới.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- protocol_id:string; status:draft|reviewed|frozen; dataset_id:string; split_version:string.
- primary_metric:passage_ndcg_at_5; primary_selection:stronger_dev_single; tie_break:BM25.
- required_conditions:[G0,GB,GD,GH]; optional_conditions:[GR]; test_tuning:false.
- qrels_core:{train:20,dev:18,test:18}; unjudged_is_zero:false; no_relevant_policy:undefined_report_separately.
- Literature TSV:paper_id,title,primary_url,read_depth,reader,task_match,method_decision,limitations,verified_at.
- read_depth=metadata|abstract|selected_sections|full_text; không gắn full_text cho đọc tóm tắt.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; theo amendment, Codex thực hiện và reviewer agent độc lập kiểm. A/B/C trong các quyết định là role đề xuất, không là người đã ký.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.2.1 | 1.5h | Codex / reviewer agent độc lập | Charter, thiết kế gốc | Viết primary/secondary metrics, split và freeze | Protocol nháp thống nhất F1/F2 |
| 01.2.2 | 2.5h | Codex / reviewer agent độc lập | Danh mục bài và reading notes | Chọn 8–12 bài lõi, đọc phần cần dùng, ghi đối chiếu | Literature matrix với mức đọc thật |
| 01.2.3 | 1h | Codex / reviewer agent độc lập | Master 8 tuần và dự toán | Gán owner/reviewer, lịch chấm, lịch đồng bộ | Working agreement và tuần tương đối |
| 01.2.4 | 1h | Codex / reviewer agent độc lập | Permission pending và tài nguyên | Mô tả API/local/extractive fallback, chi phí, điểm cắt | Decision log và protocol YAML |

## Trình tự thực hiện

1. Giữ dataset gốc 90 ca/30 families và split 54/18/18 đã có; không tự đổi split. Chỉ sửa khi yêu cầu môn học/người dùng đòi hỏi, có protocol amendment, lý do, review có bằng chứng theo protocol và cập nhật mọi bên nhận trước triển khai bị ảnh hưởng.
2. Mô tả F1 khóa corpus/query/model/prompt/evaluator trước test pooling; F2 khóa qrels test trước scoring.
3. Giữ pooled Recall là thước đo trên pool, không gọi exhaustive hoặc cận dưới bảo đảm.
4. Chọn bài phủ AIOps benchmark, dense/RRF và grounded evaluation; không đọc toàn 1.009 records.
5. Định hai buổi đồng bộ ngắn/tuần và một review artifact; xoay hai người chấm, người ba adjudicate.
6. Tính dự toán master308–374h trực tiếp,370–449h gồm20%; đo lại annotation sau5ca calibration.
7. Ghi mốc cắt reranker/ablation nếu thiếu giờ; giữ ba retrievers, no-RAG, qrels và failure accounting.
8. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
9. Khi bàn giao, reviewer agent độc lập kiểm đầu ra cùng lỗi/chưa biết; thiếu điều kiện amendment bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là acceptance; kết quả thực phải lấy từ receipts hiện tại, không suy PASS chỉ từ mô tả kịch bản.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Dev hòa | BM25=dense trên primary | Chọn BM25 theo tie-break đã ghi |
| Không có relevant qrels | Mẫu số IDCG bằng0 | Báo undefined + count; không tự đặt0/1 |
| Hybrid thua | Hiệu số âm | Vẫn là kết quả nghiên cứu hợp lệ |
| API bị từ chối | Permission=rejected | Local cần cho phép riêng; không tự chuyển |
| Mọi LLM không được phép | Hai nhánh model rejected | Đề xuất retrieval/extractive và xin sửa scope |
| Chỉ8h/người/tuần | Tổng công vượt24h/tuần | Ghi thiếu công; cắt optional hoặc điều chỉnh lịch |

## Checklist thực hiện

- [ ] **01.2.1**: Protocol nháp thống nhất F1/F2; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [ ] **01.2.2**: Literature matrix với mức đọc thật; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [ ] **01.2.3**: Working agreement và tuần tương đối; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [ ] **01.2.4**: Decision log và protocol YAML; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [ ] Lưu lỗi/chưa biết, disposition và review evidence; chỉ complete khi các checks theo amendment đạt, không chỉ vì file tồn tại.
- [ ] Đối chiếu tổng công task với 6h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Protocol mô tả công bằng, mẫu số, failed records và primary contrast trước test.
- [ ] 8–12 bài có nguồn, mức đọc Codex thật và reviewer agent độc lập đối chiếu provenance; không giả human reading.
- [ ] Mỗi hạng mục có role owner/reviewer khác, lịch/nguồn lực là đề xuất và giờ thực có vẫn unknown; kế hoạch annotation chấm đôi thật ở plan sau giữ nguyên.
- [ ] Quyền API/local và trần chi vẫn pending nếu chưa có chứng cứ đồng ý.

## Gate nghiệm thu và điều kiện thất bại

G01-B: Codex và reviewer agent độc lập kiểm boundary/design/nguồn lực, literature provenance và amendment; tên/giờ/human signatures không là gate01. API decision chưa có không chặn protocol IR nhưng vẫn chặn model tương ứng.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Protocol phình: giữ một corpus/query chính và một generator. Nhóm không đủ giờ: đo calibration rồi giảm optional trước khi giảm chất lượng qrels.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase3 nhận protocol/ma trận/working agreement; reviewer agent chỉ rõ điều chưa khóa. Reviewer tự kiểm theo user override, không biến lịch/giờ/model đề xuất thành quyết định thực đã có.
Reviewer agent độc lập kiểm static handoff bằng paths/version/hash; không đòi receiver chữ ký người thật cho scope01. Các trạng thái nguồn chưa biết và communication chưa gửi vẫn giữ đúng sự thật.

## Bằng chứng thực hiện theo amendment — 2026-09-13

| Task | Bằng chứng observable cần reviewer độc lập kiểm |
|---|---|
| 01.2.1 | [Protocol](../../06_implementation/docs/research-protocol.md), [YAML](../../06_implementation/configs/protocol.yaml): nDCG@5/denominators/conditions/F1→test_input→pool→F2→scoring |
| 01.2.2 | [Matrix](../../06_implementation/docs/literature-matrix.tsv), [notes](../../06_implementation/docs/literature-reading-notes.md):10bài, actual Codex read-depth, primary sources/hash, independent agent review |
| 01.2.3 | [Working agreement](../../06_implementation/docs/team-working-agreement.md): role assignments, lịch và giờ đề xuất/unknown rõ, annotation duties thật không bị miễn |
| 01.2.4 | [Decisions](../../06_implementation/configs/decisions.json): API/payload/local/sharing/budget riêng, fallback conditional và deadlineW2 |

Review agent không giả human reading hoặc giờ cam kết. Dự toán6giờ-người giữ đúng tính đề xuất; không API/model/annotation ở01. Final review/strict receipts quyết định acceptance.
