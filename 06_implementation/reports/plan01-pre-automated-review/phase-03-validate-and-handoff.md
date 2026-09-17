---
phase: 3
title: "Review hợp đồng và bàn giao gate G0"
status: pending
priority: P1
effort: "3h"
dependencies: [2]
---

# Phase 03: Review hợp đồng và bàn giao gate G0

## Tổng quan

Kiểm một lượt toàn bộ quyết định và sự thống nhất giữa tài liệu, tạo mốc G0 đủ để các phần dữ liệu, retrieval và annotation bắt đầu.
Công dự kiến **3 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Protocol | `06_implementation/docs/research-protocol.md` | B kiểm primary và chống test tuning |
| Config | `06_implementation/configs/protocol.yaml` | Codex so trường với văn bản |
| Phân công | `06_implementation/docs/team-working-agreement.md` | Nhóm xác nhận trách nhiệm |
| Quyết định | `06_implementation/docs/decision-log.md` | C đối chiếu chứng cứ phản hồi |

## Yêu cầu

- G0 gate khởi động khác G0 điều kiện no-RAG; tên record phải nêu gate hoặc condition.
- Không đóng pending quyền API/model/ngân sách chỉ để đạt gate.
- Version/hash của tài liệu phải được lưu; sửa sau G0 có changelog, ảnh hưởng và bên nhận.
- Tài liệu gốc không bị thay thế; G0 là bản derivative có provenance.

## Kiến trúc và ranh giới trách nhiệm

Review chéo → checklist G0 → manifest version/hash → thông báo bàn giao nội bộ do nhóm thực hiện. Các plan sau đọc mốc này và quyền mô hình độc lập.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Sửa:** `06_implementation/docs/project-charter.md` — Bản đã review.
- **Sửa:** `06_implementation/docs/research-protocol.md` — Giải quyết mâu thuẫn.
- **Sửa:** `06_implementation/docs/decision-log.md` — Nguồn quyết định và pending.
- **Tạo:** `06_implementation/docs/protocol-review.md` — Issue và disposition.
- **Tạo:** `06_implementation/freezes/G0/manifest.json` — Hashes cùng quyền chưa chốt.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- gate_id:G0; gate_kind:project_start; protocol_id:string; created_at_utc:string.
- artifacts:[{path:string,sha256:string,version:string}]; reviewers:[{person,scope,reviewed_at}].
- permissions:{api:pending|approved|rejected,local_model:pending|approved|rejected,budget_usd:number|null}.
- open_decisions:[decision_id]; allowed_work:[data,corpus,representation,retrieval,annotation_preparation].
- Nếu API chưa approved thì allowed_work không có api_generation; record approval cần source_ref.
- review issue:issue_id,severity,location,problem,owner,disposition,evidence_ref.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.3.1 | 1h | Codex + B / A | Toàn bộ docs/config | Quét mâu thuẫn counts, fields, freeze, metrics | Protocol review có issue xử lý |
| 01.3.2 | 1h | A/B/C / C điều phối | Charter, literature, phân công | Review tính khả thi và xác nhận trách nhiệm | Review records người thật |
| 01.3.3 | 0.5h | Codex + C / B | Docs đã review | Lập manifest hash và open decisions | G0 manifest |
| 01.3.4 | 0.5h | C / A và B | G0 manifest | Bàn giao checklist 02–10, đặt lịch xử lý pending | Handoff record trong protocol review |

## Trình tự thực hiện

1. So tất cả occurrence90/54/18/56/6 families và cách diễn giải mẫu số.
2. Đối chiếu RQ, required conditions và freeze sequence trong YAML/văn bản; một lỗi phải sửa ở mọi nơi.
3. Chạy walkthrough: API pending, corpus chưa xong, qrels0; ghi chính xác phần nào vẫn bắt đầu được.
4. Xác nhận owner/reviewer bằng tên nhóm lúc triển khai; không tự ký thay bằng Codex.
5. Tạo hash sau khi review; một thay đổi tiếp theo tạo manifest version mới.
6. Người điều phối tự gửi/yêu cầu phản hồi cần thiết; Codex cung cấp nội dung nháp trong repo.
7. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
8. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Hash không khớp | Sửa protocol sau manifest | Gate invalid; tạo bản mới và review ảnh hưởng |
| Sai số lượng core | Nhầm90 incidents có qrels | Fail; sửa thành56 dự kiến và0 hiện tại |
| Test qrels trước F1 | Workflow tạo vòng phụ thuộc | Fail; F1→pooltest→06B/F2→08score |
| Thông báo chưa gửi | Chỉ có thư nháp | Giữ communication pending |
| Reviewer thiếu | Chỉ owner tự xác nhận | Chưa đạt G0; bổ sung review người khác |
| API pending | Mọi docs khác đạt | G0 có điều kiện; IR được làm, API chưa chạy |

## Checklist thực hiện

- [ ] **01.3.1**: Protocol review có issue xử lý; Codex + B / A xác nhận bằng chứng.
- [ ] **01.3.2**: Review records người thật; A/B/C / C điều phối xác nhận bằng chứng.
- [ ] **01.3.3**: G0 manifest; Codex + C / B xác nhận bằng chứng.
- [ ] **01.3.4**: Handoff record trong protocol review; C / A và B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 3h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Không còn mâu thuẫn chưa xử lý giữa charter, protocol và config.
- [ ] Manifest chứa đúng hash/version và phạm vi review.
- [ ] A/B/C biết đầu ra/đầu vào từng phần và hạn quyết định còn pending.
- [ ] Các phần sau phân biệt gate đã đủ với permission chưa đủ.

## Gate nghiệm thu và điều kiện thất bại

G0 được chấp nhận khi phạm vi và contract nhất quán, owner/reviewer rõ, pending quyết định có người theo dõi. Giảng viên/API chưa trả lời là blocker phần model, không tự giả hoàn tất.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Coi freeze là bất biến tuyệt đối: sửa lỗi vẫn được nhưng cần version và đánh giá tác động. Điều chỉnh sau thấy test là protocol deviation, phải ghi và không thay headline tùy tiện.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

02 nhận data boundary;03 nhận corpus scope;04–05 nhận RQ/metrics;06 nhận qrels design;07 nhận permissions;08 nhận F1/F2;09–10 nhận chuẩn claim và lịch. Không chạy các plan trong lượt viết này.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

## Bằng chứng thực hiện — 2026-09-13

Đã chuẩn bị review kỹ thuật và bàn giao có thể kiểm; **G0 project_start vẫn awaiting_human_review**. Manifest candidate không là human acceptance hoặc quyền gọi model. Các acceptance gốc không được tự check.

| Task | Bằng chứng kỹ thuật hiện có | Việc còn cần người |
|---|---|---|
| 01.3.1 | [Protocol review](../../06_implementation/docs/protocol-review.md), [validator](../../06_implementation/scripts/validate_protocol.py), [tests](../../06_implementation/tests/test_validate_protocol.py): issue/disposition và checks; kết quả thực ở progress report | B/A review nội dung và xác nhận disposition |
| 01.3.2 | [Review records và pending scopes](../../06_implementation/docs/protocol-review.md): A/B/C person/time/source_ref còn null | A/B/C thực hiện review khả thi, đọc bài và ký bằng chứng đúng version/hash |
| 01.3.3 | [Builder](../../06_implementation/scripts/build_g0_manifest.py) và [candidate manifest](../../06_implementation/freezes/G0/manifest.json): hash/version/open decisions; receipt tạo/kiểm ở progress report | C/B kiểm candidate, human acceptance và version mới khi đổi trạng thái |
| 01.3.4 | [Handoff table 02–10](../../06_implementation/docs/protocol-review.md), [progress](../../06_implementation/reports/plan01-progress.md): inputs/owners/reviewers và acknowledgments pending | C bàn giao nội bộ, A/B và bên nhận xác nhận; communication chưa gửi |

`technical_valid` và `g0_ready` là hai kết quả riêng. Strict G0 check phải từ chối khi thiếu human review, kể cả các kiểm kỹ thuật đều pass. Không giả thời gian nghiệm thu, không commit/Git init và không publish/send để vượt gate.
