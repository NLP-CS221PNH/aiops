---
phase: 1
title: "Đọc ràng buộc và lập sổ quyết định"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 01: Đọc ràng buộc và lập sổ quyết định

## Amendment theo yêu cầu người dùng — 2026-09-13

Người dùng chỉ thị trong task hiện tại: **“tự check mọi thứ, không cần human input”**. Chỉ thị này thay điều kiện review người thật của riêng plan01 bằng **Codex và reviewer agent độc lập**, có actor/type, scope, thời gian, artifact hashes và bằng chứng kiểm. Không ghi AI review thành chữ ký, người đọc hoặc giờ cam kết của con người.

Tên A/B/C, giờ thực có, rubric và hạn môn học chưa biết vẫn được ghi rõ pending/unknown; không cần hỏi thêm để hoàn tất scope01. Quyền API/payload/local model/sharing/ngân sách giữ trạng thái thực tế; nhãn qrels và annotation người thật ở các plan sau không được tạo hoặc miễn thay. RQ, counts/split/core, conditions và F1/F2 giữ nguyên. Bàn giao scope01 là static handoff có paths/version/hash được reviewer kiểm, communication thực tế vẫn chưa gửi.

Bản trước amendment được giữ nguyên bytes cùng hashes tại [archive](../../06_implementation/reports/plan01-pre-automated-review/archive-manifest.json). Chỉ check acceptance/complete qua CLI sau khi independent review và strict G0 validator cho phiên bản amendment đều đạt; amendment này chưa tự là bằng chứng PASS.

## Tổng quan

Biến đề cương đang có thành danh sách yêu cầu cần kiểm chứng; chưa khóa quyền API hoặc số liệu kết quả.
Công dự kiến **3 giờ-người**; các checkbox là acceptance theo amendment, chỉ check sau bằng chứng cuối.
Codex điều phối phần plan01; reviewer agent độc lập kiểm bằng chứng. A/B/C là vai trò đề xuất cho nghiên cứu; chưa biết người thật không chặn review01. Các quyền bên ngoài và annotation thật ở plan sau vẫn cần bằng chứng riêng.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` trỏ tới sản phẩm triển khai; kiểm nội dung/hash và trạng thái thực ở receipts thay vì suy từ tên file.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Đề cương | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/project_proposal.md` | C đọc mục tiêu, A kiểm dữ liệu, B kiểm RQ |
| Thiết kế | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/method-and-experiment-design.md` | B đối chiếu phép đo và leakage |
| Hiện trạng | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/START-HERE.md` | A xác nhận nguồn là pack hiện tại |
| Annotation | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/status.json` | Ghi đúng 0 human judgments |

## Yêu cầu

- Giữ đề tài hỗ trợ phân tích incident offline trên Online Boutique, không mở sang tự động khắc phục.
- Mỗi quyết định chưa biết có owner, hạn chốt và trạng thái pending; không lấy thiếu phản hồi làm chấp thuận.
- Rubric/hạn nộp/tên thành viên chưa được cung cấp phải giữ placeholder rõ ràng.
- Ngân sách API $10–15 chỉ là đề xuất để nhóm quyết; không tạo payment hay gọi API ở phase này.

## Kiến trúc và ranh giới trách nhiệm

Nguồn hiện có → bảng ràng buộc → câu hỏi ưu tiên → decision log → charter. Codex và reviewer agent độc lập kiểm; thư giảng viên chỉ là draft, không đòi gửi để hoàn tất01.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/project-charter.md` — Mục tiêu, input/output, phạm vi.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` — Bảng quyết định và bằng chứng.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/instructor-questions-draft.md` — Thư nháp chờ nhóm gửi.
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

Cột thực hiện/reviewer tách bằng dấu “/”; theo amendment, Codex thực hiện và reviewer agent độc lập kiểm. A/B/C trong các quyết định là role đề xuất, không là người đã ký.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.1.1 | 0.75h | Codex / reviewer agent độc lập | Đề cương và thiết kế | Trích 3 RQ, đóng góp NLP, giới hạn causal | Charter nháp có đường dẫn nguồn |
| 01.1.2 | 0.75h | Codex / reviewer agent độc lập | START-HERE, status annotation | Lập bảng đã có/chưa có và kiểm count nguồn | 90 incidents, 54/18/18, 0 judgments ghi đúng |
| 01.1.3 | 0.75h | Codex / reviewer agent độc lập | Giả định môn học và API | Soạn câu hỏi rubric, API, payload, local model, khai báo AI | Thư nháp; không gửi |
| 01.1.4 | 0.75h | Codex / reviewer agent độc lập | Ràng buộc 8 tuần/3 người | Gán owner/hạn cho quyết định còn thiếu | Decision log có role owner/reviewer và hạn theo dõi |

## Trình tự thực hiện

1. Đọc đúng bản gốc trước khi chép giả định sang charter; đánh dấu dữ kiện đã có nguồn.
2. Mô tả một input incident hợp lệ và output nghi vấn service/fault có citations; chỉ dùng ví dụ schema.
3. Ghi rubric/hạn nộp/tên A/B/C chưa biết thành pending/unknown với role owner và hạn; không hỏi lại hoặc suy đoán để hoàn tất01.
4. Chia câu hỏi API thành quyền dùng model, quyền gửi payload và trần chi để tránh một câu đồng ý mơ hồ.
5. Đặt mốc cuối tuần 2 cho quyết định generator; phần retrieval không đợi phản hồi này.
6. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
7. Khi bàn giao, reviewer agent độc lập kiểm đầu ra cùng lỗi/chưa biết; thiếu điều kiện amendment bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là acceptance; kết quả thực phải lấy từ receipts hiện tại, không suy PASS chỉ từ mô tả kịch bản.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Rubric chưa có | Nguồn rubric trống | Đánh pending + owner + hạn; không bịa tiêu chí môn |
| API chưa trả lời | Permission record pending | Thư vẫn nháp, không gửi payload |
| Một family có ba incident repetitions | Family xuất hiện nhiều ca | Charter yêu cầu giữ family cùng split |
| Thành công quá mức | Câu nói giảm MTTR/causal chain | Sửa thành offline localization/support |
| Nhầm dữ liệu sẵn có | 90 incidents nhưng 0 human labels | Tách inventory khỏi ground truth judgments |

## Checklist thực hiện

- [x] **01.1.1**: Charter nháp có đường dẫn nguồn; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.1.2**: 90 incidents, 54/18/18, 0 judgments ghi đúng; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.1.3**: Thư nháp; không gửi; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.1.4**: Decision log có role owner/reviewer và hạn theo dõi; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] Lưu lỗi/chưa biết, disposition và review evidence; chỉ complete khi các checks theo amendment đạt, không chỉ vì file tồn tại.
- [x] Đối chiếu tổng công task với 3h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Charter diễn đạt input/output và đóng góp NLP trong một đoạn cụ thể.
- [x] 100% quyết định chưa biết có owner và hạn tuần tương đối.
- [x] Thư nháp hỏi đúng quyền, không coi việc soạn thư là đã gửi/được chấp thuận.
- [x] Reviewer agent độc lập kiểm bảng hiện trạng/source hashes và lưu review đúng actor_type; không cần chữ ký người thật theo amendment.

## Gate nghiệm thu và điều kiện thất bại

G01-A: Codex và reviewer agent độc lập xác nhận inventory/câu hỏi bằng source checks; không cần human input hoặc giảng viên phản hồi để sang phase2. Sai hiện trạng hoặc lẫn gold khiến gate fail.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Nguồn rubric đến muộn: giữ vùng TBD và tiếp tục protocol không phụ thuộc. Nhầm mức đọc literature: ghi curated records/read notes và full-text reviewed tách nhau.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 2 nhận charter nháp, decision log và thư nháp; các record pending giữ nguyên. Đây là bàn giao tài liệu, không cấp quyền chạy API.
Reviewer agent độc lập kiểm static handoff bằng paths/version/hash; không đòi receiver chữ ký người thật cho scope01. Các trạng thái nguồn chưa biết và communication chưa gửi vẫn giữ đúng sự thật.

## Bằng chứng thực hiện theo amendment — 2026-09-13

| Task | Bằng chứng observable cần reviewer độc lập kiểm |
|---|---|
| 01.1.1 | [Charter](../../06_implementation/docs/project-charter.md): RQ/input/output/offline/causal limits, links nguồn |
| 01.1.2 | [Source inventory](../../06_implementation/validation/source-inventory.json):90incidents/30families/split54/18/18/test6families/0judgments và hashes |
| 01.1.3 | [Instructor draft](../../06_implementation/docs/instructor-questions-draft.md): câu hỏi quyền tách riêng, communication unsent đúng sự thật |
| 01.1.4 | [Decision log](../../06_implementation/docs/decision-log.md), [JSON](../../06_implementation/configs/decisions.json): role owner/reviewer/hạn và nguồn; không tự chốt unknowns |

[Review](../../06_implementation/docs/protocol-review.md) và final receipts chứng minh check thực. Dự toán3giờ-người không là giờ actual; tên/giờ/rubric pending không chặn scope01 theo user override. Không check task chỉ vì tồn tại file.
