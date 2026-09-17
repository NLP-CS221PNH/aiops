---
phase: 2
title: "Soạn protocol, ma trận bài lõi và phân công"
status: pending
priority: P1
effort: "6h"
dependencies: [1]
---

# Phase 02: Soạn protocol, ma trận bài lõi và phân công

## Tổng quan

Khóa thiết kế đề xuất bằng protocol cụ thể và phân bổ công cho ba người; còn quyền mô hình thì giữ nhánh quyết định có điều kiện.
Công dự kiến **6 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Charter nháp | `06_implementation/docs/project-charter.md` | C xác nhận phạm vi |
| Decision log | `06_implementation/docs/decision-log.md` | A/B kiểm các pending |
| Tổng hợp học thuật | `00_plan/literature_synthesis.md` | Mỗi người chọn bài liên quan phần mình |
| Đánh giá gốc | `00_plan/experiments_and_evaluation.md` | B kiểm baseline/metrics |

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

- **Tạo:** `06_implementation/docs/research-protocol.md` — Thiết kế RQ, metric và điều kiện.
- **Tạo:** `06_implementation/configs/protocol.yaml` — Các lựa chọn có cấu trúc.
- **Tạo:** `06_implementation/docs/team-working-agreement.md` — Owner/reviewer và lịch nhóm.
- **Tạo:** `06_implementation/docs/literature-matrix.tsv` — 8–12 bài thực sự dùng.
- **Sửa:** `06_implementation/docs/decision-log.md` — Ghi đề xuất và các quyết định mới.
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

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.2.1 | 1.5h | Codex + B / A | Charter, thiết kế gốc | Viết primary/secondary metrics, split và freeze | Protocol nháp thống nhất F1/F2 |
| 01.2.2 | 2.5h | A/B/C + Codex / người khác | Danh mục bài và reading notes | Chọn 8–12 bài lõi, đọc phần cần dùng, ghi đối chiếu | Literature matrix với mức đọc thật |
| 01.2.3 | 1h | C + Codex / A và B | Master 8 tuần và dự toán | Gán owner/reviewer, lịch chấm, lịch đồng bộ | Working agreement và tuần tương đối |
| 01.2.4 | 1h | Codex + C / B | Permission pending và tài nguyên | Mô tả API/local/extractive fallback, chi phí, điểm cắt | Decision log và protocol YAML |

## Trình tự thực hiện

1. Giữ dataset gốc 90 ca/30 families và split 54/18/18 đã có; không tự đổi split. Chỉ sửa khi yêu cầu môn học/người dùng đòi hỏi, có protocol amendment, lý do, review nhóm và cập nhật mọi bên nhận trước triển khai bị ảnh hưởng.
2. Mô tả F1 khóa corpus/query/model/prompt/evaluator trước test pooling; F2 khóa qrels test trước scoring.
3. Giữ pooled Recall là thước đo trên pool, không gọi exhaustive hoặc cận dưới bảo đảm.
4. Chọn bài phủ AIOps benchmark, dense/RRF và grounded evaluation; không đọc toàn 1.009 records.
5. Định hai buổi đồng bộ ngắn/tuần và một review artifact; xoay hai người chấm, người ba adjudicate.
6. Tính dự toán master308–374h trực tiếp,370–449h gồm20%; đo lại annotation sau5ca calibration.
7. Ghi mốc cắt reranker/ablation nếu thiếu giờ; giữ ba retrievers, no-RAG, qrels và failure accounting.
8. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
9. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Dev hòa | BM25=dense trên primary | Chọn BM25 theo tie-break đã ghi |
| Không có relevant qrels | Mẫu số IDCG bằng0 | Báo undefined + count; không tự đặt0/1 |
| Hybrid thua | Hiệu số âm | Vẫn là kết quả nghiên cứu hợp lệ |
| API bị từ chối | Permission=rejected | Local cần cho phép riêng; không tự chuyển |
| Mọi LLM không được phép | Hai nhánh model rejected | Đề xuất retrieval/extractive và xin sửa scope |
| Chỉ8h/người/tuần | Tổng công vượt24h/tuần | Ghi thiếu công; cắt optional hoặc điều chỉnh lịch |

## Checklist thực hiện

- [ ] **01.2.1**: Protocol nháp thống nhất F1/F2; Codex + B / A xác nhận bằng chứng.
- [ ] **01.2.2**: Literature matrix với mức đọc thật; A/B/C + Codex / người khác xác nhận bằng chứng.
- [ ] **01.2.3**: Working agreement và tuần tương đối; C + Codex / A và B xác nhận bằng chứng.
- [ ] **01.2.4**: Decision log và protocol YAML; Codex + C / B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 6h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Protocol mô tả công bằng, mẫu số, failed records và primary contrast trước test.
- [ ] 8–12 bài có nguồn và mức đọc; người thật chịu trách nhiệm phần đã đọc.
- [ ] Mỗi hạng mục có owner và reviewer khác; công annotation được phân bổ cả nhóm.
- [ ] Quyền API/local và trần chi vẫn pending nếu chưa có chứng cứ đồng ý.

## Gate nghiệm thu và điều kiện thất bại

G01-B: A kiểm boundary dữ liệu, B kiểm design, C kiểm nguồn lực; thiếu API decision không chặn protocol cho IR nhưng chặn chạy model tương ứng.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Protocol phình: giữ một corpus/query chính và một generator. Nhóm không đủ giờ: đo calibration rồi giảm optional trước khi giảm chất lượng qrels.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 3 nhận protocol/ma trận/working agreement; reviewer phải chỉ ra điều chưa khóa, không biến đề xuất thành quyết định nhóm đã chấp nhận.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

## Bằng chứng thực hiện — 2026-09-13

Đã soạn các đầu ra kỹ thuật để review; **G01-B vẫn pending human review**. Giữ tất cả acceptance gốc; việc Codex đọc phần bài và soạn phân công không chứng minh nhóm đã chấp nhận.

| Task | Bằng chứng kỹ thuật hiện có | Việc còn cần người |
|---|---|---|
| 01.2.1 | [Protocol](../../06_implementation/docs/research-protocol.md), [YAML](../../06_implementation/configs/protocol.yaml): primary nDCG@5, dev selection/tie-break, F1→test input/pool→F2→scoring | B/A review thiết kế, boundary và phép đo |
| 01.2.2 | [Matrix](../../06_implementation/docs/literature-matrix.tsv), [reading notes](../../06_implementation/docs/literature-reading-notes.md): 10 bài, nguồn/hash, selected sections do Codex đọc | A/B/C đọc phần được phân công và reviewer khác xác nhận; human statuses pending |
| 01.2.3 | [Working agreement](../../06_implementation/docs/team-working-agreement.md): lịch tuần tương đối, hai sync/tuần, review artifact, luân phiên chấm/adjudicate, dự toán và thiếu giờ | C/A/B xác nhận tên, giờ thực có, lịch và trách nhiệm |
| 01.2.4 | [Decisions](../../06_implementation/configs/decisions.json), [protocol](../../06_implementation/configs/protocol.yaml): API/local/extractive theo quyền riêng, trần chi chưa duyệt, mốc cuối W2 | C/B xử lý bằng chứng quyền mô hình/payload/budget; không mặc định local được phép |

Không chạy API/model hoặc annotation; hybrid không cần thắng để đạt kết quả nghiên cứu hợp lệ. Dự toán 6 giờ-người vẫn là kế hoạch; [progress report](../../06_implementation/reports/plan01-progress.md) phân biệt công kỹ thuật và acceptance chưa hoàn tất.

