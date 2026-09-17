---
phase: 1
title: "Đọc ràng buộc và lập sổ quyết định"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 01: Đọc ràng buộc và lập sổ quyết định

## Tổng quan

Biến đề cương đang có thành danh sách yêu cầu cần kiểm chứng; chưa khóa quyền API hoặc số liệu kết quả.
Công dự kiến **3 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Đề cương | `00_plan/project_proposal.md` | C đọc mục tiêu, A kiểm dữ liệu, B kiểm RQ |
| Thiết kế | `05_research/method-and-experiment-design.md` | B đối chiếu phép đo và leakage |
| Hiện trạng | `START-HERE.md` | A xác nhận nguồn là pack hiện tại |
| Annotation | `03_collection_plan/annotation-kit/status.json` | Ghi đúng 0 human judgments |

## Yêu cầu

- Giữ đề tài hỗ trợ phân tích incident offline trên Online Boutique, không mở sang tự động khắc phục.
- Mỗi quyết định chưa biết có owner, hạn chốt và trạng thái pending; không lấy thiếu phản hồi làm chấp thuận.
- Rubric/hạn nộp/tên thành viên chưa được cung cấp phải giữ placeholder rõ ràng.
- Ngân sách API $10–15 chỉ là đề xuất để nhóm quyết; không tạo payment hay gọi API ở phase này.

## Kiến trúc và ranh giới trách nhiệm

Nguồn hiện có → bảng ràng buộc → câu hỏi ưu tiên → decision log → charter nháp. C điều phối, A/B review chéo; chỉ nhóm gửi nội dung hỏi giảng viên.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `06_implementation/docs/project-charter.md` — Mục tiêu, input/output, phạm vi.
- **Tạo:** `06_implementation/docs/decision-log.md` — Bảng quyết định và bằng chứng.
- **Tạo:** `06_implementation/docs/instructor-questions-draft.md` — Thư nháp chờ nhóm gửi.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- decision_id:string; topic:string; options:string[]; chosen:string|null.
- status:pending|confirmed|rejected; owner:A|B|C; reviewer:A|B|C.
- due_relative_week:int; source_ref:string|null; decided_at_utc:string|null.
- Không ghi confirmed khi chưa có nguồn trả lời; ghi một quyết định cho mỗi quyền API/open weights/data sharing.
- Charter phân biệt observations lúc inference với root labels, injection time, qrels và reference chỉ evaluator thấy.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.1.1 | 0.75h | Codex + C / B | Đề cương và thiết kế | Trích 3 RQ, đóng góp NLP, giới hạn causal | Charter nháp có đường dẫn nguồn |
| 01.1.2 | 0.75h | Codex + A / C | START-HERE, status annotation | Lập bảng đã có/chưa có và kiểm count nguồn | 90 incidents, 54/18/18, 0 judgments ghi đúng |
| 01.1.3 | 0.75h | Codex + C / A | Giả định môn học và API | Soạn câu hỏi rubric, API, payload, local model, khai báo AI | Thư nháp; không gửi |
| 01.1.4 | 0.75h | C / A và B | Ràng buộc 8 tuần/3 người | Gán owner/hạn cho quyết định còn thiếu | Decision log có người xử lý |

## Trình tự thực hiện

1. Đọc đúng bản gốc trước khi chép giả định sang charter; đánh dấu dữ kiện đã có nguồn.
2. Mô tả một input incident hợp lệ và output nghi vấn service/fault có citations; chỉ dùng ví dụ schema.
3. Nhóm bổ sung rubric/hạn nộp/tên A/B/C khi nhận được; Codex không suy đoán.
4. Chia câu hỏi API thành quyền dùng model, quyền gửi payload và trần chi để tránh một câu đồng ý mơ hồ.
5. Đặt mốc cuối tuần 2 cho quyết định generator; phần retrieval không đợi phản hồi này.
6. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
7. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Rubric chưa có | Nguồn rubric trống | Đánh pending + owner + hạn; không bịa tiêu chí môn |
| API chưa trả lời | Permission record pending | Thư vẫn nháp, không gửi payload |
| Một family có ba incident repetitions | Family xuất hiện nhiều ca | Charter yêu cầu giữ family cùng split |
| Thành công quá mức | Câu nói giảm MTTR/causal chain | Sửa thành offline localization/support |
| Nhầm dữ liệu sẵn có | 90 incidents nhưng 0 human labels | Tách inventory khỏi ground truth judgments |

## Checklist thực hiện

- [ ] **01.1.1**: Charter nháp có đường dẫn nguồn; Codex + C / B xác nhận bằng chứng.
- [ ] **01.1.2**: 90 incidents, 54/18/18, 0 judgments ghi đúng; Codex + A / C xác nhận bằng chứng.
- [ ] **01.1.3**: Thư nháp; không gửi; Codex + C / A xác nhận bằng chứng.
- [ ] **01.1.4**: Decision log có người xử lý; C / A và B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 3h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Charter diễn đạt input/output và đóng góp NLP trong một đoạn cụ thể.
- [ ] 100% quyết định chưa biết có owner và hạn tuần tương đối.
- [ ] Thư nháp hỏi đúng quyền, không coi việc soạn thư là đã gửi/được chấp thuận.
- [ ] A/B đọc chéo bảng hiện trạng và ký mục review bằng tên thật khi triển khai.

## Gate nghiệm thu và điều kiện thất bại

G01-A: C chấp nhận inventory và các câu hỏi; không yêu cầu giảng viên đã trả lời để sang phase 2. Sai hiện trạng hoặc lẫn gold khiến gate fail.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Nguồn rubric đến muộn: giữ vùng TBD và tiếp tục protocol không phụ thuộc. Nhầm mức đọc literature: ghi curated records/read notes và full-text reviewed tách nhau.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 2 nhận charter nháp, decision log và thư nháp; các record pending giữ nguyên. Đây là bàn giao tài liệu, không cấp quyền chạy API.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

## Bằng chứng thực hiện — 2026-09-13

Phần kỹ thuật đã bắt đầu và có artifacts; **G01-A vẫn pending human review**. Acceptance gốc ở trên giữ nguyên vì từng task yêu cầu người xác nhận. Các câu “công việc tương lai” mô tả bản kế hoạch trước phiên thực hiện.

| Task | Bằng chứng kỹ thuật hiện có | Việc còn cần người |
|---|---|---|
| 01.1.1 | [Charter](../../06_implementation/docs/project-charter.md): 3 RQ, input/output offline, đóng góp NLP và giới hạn causal | C/B review và chấp nhận phạm vi |
| 01.1.2 | [Source inventory](../../06_implementation/validation/source-inventory.json): 16 checks, 90 incidents/30 families, split 54/18/18, 0 human judgments | A/C kiểm nguồn, chấp nhận inventory và boundary |
| 01.1.3 | [Thư nháp](../../06_implementation/docs/instructor-questions-draft.md): rubric, API, payload, local model, khai báo AI; chưa gửi | C/A review nội dung; nhóm tự gửi và cung cấp phản hồi có nguồn |
| 01.1.4 | [Decision log](../../06_implementation/docs/decision-log.md), [JSON](../../06_implementation/configs/decisions.json): 16 pending records, owner/reviewer/hạn tuần | A/B/C xác nhận danh tính, trách nhiệm, giờ và các quyết định chưa biết |

Chưa có bằng chứng G01-A accepted, không lấy dự toán 3 giờ-người làm số giờ đã thực hiện. [Tiến độ và công cụ](../../06_implementation/reports/plan01-progress.md) giữ checklist chưa được người nghiệm thu và việc theo dõi pending.

