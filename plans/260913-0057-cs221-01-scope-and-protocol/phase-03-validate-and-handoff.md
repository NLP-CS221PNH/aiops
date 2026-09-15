---
phase: 3
title: "Review hợp đồng và bàn giao gate G0"
status: pending
priority: P1
effort: "3h"
dependencies: [2]
---

# Phase 03: Review hợp đồng và bàn giao gate G0

## Amendment theo yêu cầu người dùng — 2026-09-13

Người dùng chỉ thị trong task hiện tại: **“tự check mọi thứ, không cần human input”**. Chỉ thị này thay điều kiện review người thật của riêng plan01 bằng **Codex và reviewer agent độc lập**, có actor/type, scope, thời gian, artifact hashes và bằng chứng kiểm. Không ghi AI review thành chữ ký, người đọc hoặc giờ cam kết của con người.

Tên A/B/C, giờ thực có, rubric và hạn môn học chưa biết vẫn được ghi rõ pending/unknown; không cần hỏi thêm để hoàn tất scope01. Quyền API/payload/local model/sharing/ngân sách giữ trạng thái thực tế; nhãn qrels và annotation người thật ở các plan sau không được tạo hoặc miễn thay. RQ, counts/split/core, conditions và F1/F2 giữ nguyên. Bàn giao scope01 là static handoff có paths/version/hash được reviewer kiểm, communication thực tế vẫn chưa gửi.

Bản trước amendment được giữ nguyên bytes cùng hashes tại [archive](../../06_implementation/reports/plan01-pre-automated-review/archive-manifest.json). Chỉ check acceptance/complete qua CLI sau khi independent review và strict G0 validator cho phiên bản amendment đều đạt; amendment này chưa tự là bằng chứng PASS.

## Tổng quan

Kiểm một lượt toàn bộ quyết định và sự thống nhất giữa tài liệu, tạo mốc G0 đủ để các phần dữ liệu, retrieval và annotation bắt đầu.
Công dự kiến **3 giờ-người**; các checkbox là acceptance theo amendment, chỉ check sau bằng chứng cuối.
Codex điều phối phần plan01; reviewer agent độc lập kiểm bằng chứng. A/B/C là vai trò đề xuất cho nghiên cứu; chưa biết người thật không chặn review01. Các quyền bên ngoài và annotation thật ở plan sau vẫn cần bằng chứng riêng.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` trỏ tới sản phẩm triển khai; kiểm nội dung/hash và trạng thái thực ở receipts thay vì suy từ tên file.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Protocol | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/research-protocol.md` | B kiểm primary và chống test tuning |
| Config | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/protocol.yaml` | Codex so trường với văn bản |
| Phân công | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/team-working-agreement.md` | Reviewer agent kiểm role assignments/unknowns |
| Quyết định | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` | C đối chiếu chứng cứ phản hồi |

## Yêu cầu

- G0 gate khởi động khác G0 điều kiện no-RAG; tên record phải nêu gate hoặc condition.
- Không đóng pending quyền API/model/ngân sách chỉ để đạt gate.
- Version/hash của tài liệu phải được lưu; sửa sau G0 có changelog, ảnh hưởng và bên nhận.
- Tài liệu gốc không bị thay thế; G0 là bản derivative có provenance.

## Kiến trúc và ranh giới trách nhiệm

Codex + review agent độc lập → strict checks theo amendment → manifest version/hash → static handoff có thể kiểm. Không yêu cầu gửi thông báo/receiver human acknowledgment để complete01; các quyền model độc lập.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/project-charter.md` — Bản đã review.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/research-protocol.md` — Giải quyết mâu thuẫn.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` — Nguồn quyết định và pending.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/protocol-review.md` — Issue và disposition.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/G0/manifest.json` — Hashes cùng quyền chưa chốt.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- gate_id:G0; gate_kind:project_start; protocol_id:string; created_at_utc:string.
- artifacts:[{path:string,sha256:string,version:string}]; human reviewers không được bịa. Automated review lưu riêng actor/type, scope, reviewed_at, artifact hashes và user authorization theo schema triển khai hiện tại.
- permissions:{api:pending|approved|rejected,local_model:pending|approved|rejected,budget_usd:number|null}.
- open_decisions:[decision_id]; allowed_work:[data,corpus,representation,retrieval,annotation_preparation].
- Nếu API chưa approved thì allowed_work không có api_generation; record approval cần source_ref.
- review issue:issue_id,severity,location,problem,owner,disposition,evidence_ref.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; theo amendment, Codex thực hiện và reviewer agent độc lập kiểm. A/B/C trong các quyết định là role đề xuất, không là người đã ký.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 01.3.1 | 1h | Codex / reviewer agent độc lập | Toàn bộ docs/config | Quét mâu thuẫn counts, fields, freeze, metrics | Protocol review có issue xử lý |
| 01.3.2 | 1h | Codex / reviewer agent độc lập | Charter, literature, phân công | Review tính khả thi, assignments và unknowns bằng agent độc lập | Automated review records có actor/type, scope và evidence thật |
| 01.3.3 | 0.5h | Codex / reviewer agent độc lập | Docs đã review | Lập manifest hash và open decisions | G0 manifest |
| 01.3.4 | 0.5h | Codex / reviewer agent độc lập | G0 manifest | Bàn giao checklist 02–10, đặt lịch xử lý pending | Handoff record trong protocol review |

## Trình tự thực hiện

1. So tất cả occurrence90/54/18/56/6 families và cách diễn giải mẫu số.
2. Đối chiếu RQ, required conditions và freeze sequence trong YAML/văn bản; một lỗi phải sửa ở mọi nơi.
3. Chạy walkthrough: API pending, corpus chưa xong, qrels0; ghi chính xác phần nào vẫn bắt đầu được.
4. Lưu danh tính agent reviewer thật và scope/hash được kiểm; tên người thật/giờ chưa biết không chặn01, không giả chữ ký con người.
5. Tạo hash sau khi review; một thay đổi tiếp theo tạo manifest version mới.
6. Hoàn thiện static handoff/draft trong repo, ghi communication unsent; không cần gửi hoặc chờ phản hồi để complete01.
7. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
8. Khi bàn giao, reviewer agent độc lập kiểm đầu ra cùng lỗi/chưa biết; thiếu điều kiện amendment bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là acceptance; kết quả thực phải lấy từ receipts hiện tại, không suy PASS chỉ từ mô tả kịch bản.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Hash không khớp | Sửa protocol sau manifest | Gate invalid; tạo bản mới và review ảnh hưởng |
| Sai số lượng core | Nhầm90 incidents có qrels | Fail; sửa thành56 dự kiến và0 hiện tại |
| Test qrels trước F1 | Workflow tạo vòng phụ thuộc | Fail; F1→pooltest→06B/F2→08score |
| Thông báo chưa gửi | Chỉ có thư nháp | Giữ communication pending |
| Reviewer độc lập thiếu | Chỉ author tự xác nhận | Chưa đạt G0; cần agent review độc lập và strict receipts theo user override |
| API pending | Mọi docs khác đạt | G0 có điều kiện; IR được làm, API chưa chạy |

## Checklist thực hiện

- [x] **01.3.1**: Protocol review có issue xử lý; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.3.2**: Automated review records có actor/type, scope và evidence thật; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.3.3**: G0 manifest; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] **01.3.4**: Handoff record trong protocol review; Codex / reviewer agent độc lập xác nhận bằng chứng.
- [x] Lưu lỗi/chưa biết, disposition và review evidence; chỉ complete khi các checks theo amendment đạt, không chỉ vì file tồn tại.
- [x] Đối chiếu tổng công task với 3h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Không còn mâu thuẫn chưa xử lý giữa charter, protocol và config.
- [x] Manifest chứa đúng hash/version và phạm vi review.
- [x] Static handoff nêu inputs/outputs/role owner/reviewer/hạn và pending; reviewer agent kiểm paths/version/hash, không đòi human acknowledgment.
- [x] Các phần sau phân biệt gate đã đủ với permission chưa đủ.

## Gate nghiệm thu và điều kiện thất bại

G0 được chấp nhận theo explicit user override khi scope/contract nhất quán, independent automated review có bằng chứng và strict validator đạt trên cùng version/hash, pending có role owner/hạn. Không cần human signatures/names/availability để complete01. Giảng viên/API chưa trả lời vẫn chặn phần model, không được suy thành approval.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Coi freeze là bất biến tuyệt đối: sửa lỗi vẫn được nhưng cần version và đánh giá tác động. Điều chỉnh sau thấy test là protocol deviation, phải ghi và không thay headline tùy tiện.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

02 nhận data boundary;03 nhận corpus scope;04–05 nhận RQ/metrics;06 nhận qrels design;07 nhận permissions;08 nhận F1/F2;09–10 nhận chuẩn claim và lịch. Không chạy các plan trong lượt viết này.
Reviewer agent độc lập kiểm static handoff bằng paths/version/hash; không đòi receiver chữ ký người thật cho scope01. Các trạng thái nguồn chưa biết và communication chưa gửi vẫn giữ đúng sự thật.

## Bằng chứng thực hiện theo amendment — 2026-09-13

| Task | Bằng chứng observable cần reviewer độc lập kiểm |
|---|---|
| 01.3.1 | [Protocol review](../../06_implementation/docs/protocol-review.md), [validator](../../06_implementation/scripts/validate_protocol.py), tests/receipts: issues, dispositions, negative checks |
| 01.3.2 | Automated review record đúng actor/type/scope/time/artifact hashes và explicit user authorization; không chữ ký human giả |
| 01.3.3 | [Manifest](../../06_implementation/freezes/G0/manifest.json): version/hash, archive/supersedes, open decisions, independent review/strictcheck cùng phiên bản |
| 01.3.4 | [Static handoff02–10](../../06_implementation/docs/protocol-review.md): inputs/outputs/role owner/reviewer/hạn/version/hash được kiểm; communication unsent |

`technical_valid` và `g0_ready` là hai checks riêng. Automated G0 cần cả strict check và independent review đạt theo user override. Không miễn quyềnmodel hoặc annotation thật; không chạy downstream từscope01. Dự toán3giờ-người không là giờactual. Chỉ CLI check/complete khi có receipts cuối.
