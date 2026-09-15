# Plan 01 — hoàn tất theo nghiệm thu tự động được cho phép

Protocol `cs221-aiops-rag-protocol-v1`, version **1.0.0-reviewed.1**. **Plan completed; G0 project_start accepted** ở `review_mode: automated`.

Người dùng chỉ thị: **“tự check mọi thứ, không cần human input”**. [Authorization](../configs/acceptance-authorization.json) và [amendment](../docs/acceptance-amendment.md) thay điều kiện human sign-off của riêng scope01 bằng kiểm tra Codex và reviewer agent độc lập. Không ghi agent thành người thật, không tự xác nhận dữ kiện chưa biết hoặc quyền mô hình/ngân sách.

## Kết quả kiểm và hoàn tất

- [Independent review](plan01-autonomous-review.json): **PASS, 9/10, 0 critical findings, 0 blockers**; gắn reviewer, thời gian, scope và hashes đúng version. Receipt này là bằng chứng nghiệm thu automated hiện tại.
- [Tests](plan01-tests.md): **52/52 PASS**, gồm 35 tests trước và 17 tests cho automated mode, authorization, receipt, permission boundaries và builder. Bảy lifecycle checks trước amendment được giữ làm lịch sử; không cộng chúng thành số unit tests hiện tại.
- [Technical validation](protocol-validation.json) và [strict G0](g0-readiness.json) đều **PASS, exit0, technical_valid:true, g0_ready:true**, errors/blockers/warnings đều rỗng. Integration lúc 2026-09-13T02:54:57Z; finalization receipt ghi kiểm strict sau cập nhật tracking.
- CLI đã check **34/34 acceptance boxes**: 4 trong plan và 30 ở ba phases; `ak plan status` báo **completed, 3/3 phases, 30/30 phase items, 100%**. Phase notes/evidence và index đã đồng bộ; plan format validation PASS.

[Finalization receipt](plan01-finalization.json) lưu lệnh/kết quả, live tracking hashes, snapshot integrity và journal. Chỉ đóng plan sau độc lập review và strict checks đạt; không đánh dấu các downstream experiments hoàn tất.

## Ánh xạ 12 task đã nghiệm thu

| Task | Sản phẩm / bằng chứng được reviewer kiểm |
|---|---|
| 01.1.1 | [Charter](../docs/project-charter.md): 3RQ, đóng góp NLP, input/output offline và giới hạn causal |
| 01.1.2 | [Source audit](../validation/source-inventory.json): 90incidents/30families, split54/18/18, test6families, 0human judgments; nguồn/hashes và inference boundary |
| 01.1.3 | [Instructor draft](../docs/instructor-questions-draft.md): rubric/model/payload/sharing/disclosure tách riêng, trạng thái unsent đúng thực tế |
| 01.1.4 | [Decision log](../docs/decision-log.md), [JSON](../configs/decisions.json): 15quyết định còn mở có role owner/reviewer/hạn; D16 ghi actual user override |
| 01.2.1 | [Protocol](../docs/research-protocol.md), [YAML](../configs/protocol.yaml): nDCG@5, dev stronger single/tie BM25, conditions, denominators, failures, F1/F2 |
| 01.2.2 | [Matrix](../docs/literature-matrix.tsv), [reading notes](../docs/literature-reading-notes.md): 10bài, primary-source provenance và mức đọc Codex thật; không giả human reading |
| 01.2.3 | [Working agreement](../docs/team-working-agreement.md): role assignments, lịch8tuần, 308–374giờ trực tiếp/370–449có dự phòng; giờ người thật chưa biết ghi rõ |
| 01.2.4 | [Decisions](../configs/decisions.json): API/payload/local/sharing/budget độc lập, generator fallback có điều kiện, cutoffW2 |
| 01.3.1 | [Review/issues](../docs/protocol-review.md), validator/tests và current review receipt: disposition và negative cases được kiểm |
| 01.3.2 | [Automated review](plan01-autonomous-review.json): actor/type/scope/time/hash và user authorization; không có human signatures |
| 01.3.3 | [Manifest](../freezes/G0/manifest.json): accepted automated, version/hash chain, 20artifacts và32sources, prior manifests giữ qua supersedes |
| 01.3.4 | [Static handoff02–10](../docs/protocol-review.md): inputs/outputs/roles/hạn/version/hash kiểm được; hoàn tất bàn giao tài liệu cục bộ, communication vẫn chưa gửi |

## Snapshot hợp đồng và tracking hiện tại

Bốn [plan-source snapshots](../freezes/G0/plan-source/plan.md) là bytes acceptance contract đã amendment, chụp trước dấu check hoàn tất. Manifest/source inventory ràng buộc các snapshots bất biến đó. Bốn live files trong [plan01](../../plans/260913-0057-cs221-01-scope-and-protocol/plan.md) giữ tracking và được CLI đánh hoàn tất sau strict PASS; chúng chỉ khác snapshots ở checkboxes và overall status, không đổi hợp đồng khoa học. Snapshot unchecked không phải trạng thái công việc hiện tại.

CLI `ak plan check` cập nhật checkboxes; trạng thái phase trong index là `done`. CLI không sửa trường `status: pending` cũ trong phase frontmatter hoặc table trạng thái viết tay; các trường đó là metadata của bản acceptance trước hoàn tất, không phải authority tracking hiện tại. Không sửa status thủ công; kết quả chuẩn là `ak plan status`, checkboxes và receipt. Lỗi writer mixed-LF/CRLF trước đây đã được tái hiện bằng fixture và xử lý EOL-only.

Manifest reviewed.1 SHA-256: `fc411c69c5e6cdc8883a8a458eb33502e7b7c50aaabab68b2387c905be943c29`. Không sửa frozen artifacts, source datasets hoặc plan khác trong finalization01. Reindex đọc các plans để đồng bộ index, không viết source files của plan02.

## Lịch sử và phạm vi còn mở

[Bản plan trước user override](plan01-pre-automated-review/archive-manifest.json), các báo cáo tracking trước amendment trong cùng archive và journal cũ được giữ. Strict FAIL của draft.2 phản ánh quy tắc human gate tại thời điểm đó; reviewed.1 áp dụng authorization mới có nguồn, không xóa hay giả kết quả cũ. [Journal nghiệm thu tự động](../../plans/journals/2026-09-13-cs221-plan01-automated-acceptance-amendment.md) được tạo/validate bằng CLI. **AgentWiki publish skipped.** Workspace không có Git repository; không Git init, commit, send hoặc publish.

Tên người thật, giờ cam kết, lịch môn/rubric và những quyết định bên ngoài chưa biết vẫn pending/unknown có role/hạn. Chúng **không chặn hoàn tất plan01 theo amendment**, và báo cáo này không yêu cầu thêm human input để đóng scope01. Quyền API/payload/local/sharing vẫn pending, approved budget=null; $10–15 chỉ là đề xuất. Không gọi model hoặc tiêu tiền từ việc G0 accepted.

Human passage judgments vẫn **0**, core qrels20/18/18 vẫn là thiết kế; annotation người thật, F1/F2 và kết quả thí nghiệm ở các plan sau giữ nguyên nhiệm vụ. Không chạy retrieval/generation benchmark, tạo nhãn hoặc thay counts/RQ để hoàn tất01. Dự toán12giờ-người không phải thời gian thực đã đo.
