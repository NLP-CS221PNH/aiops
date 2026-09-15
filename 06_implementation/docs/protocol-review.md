# Protocol review và bàn giao G0 — Codex tự nghiệm thu

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-reviewed.1`.

Người dùng yêu cầu **“tự check mọi thứ, không cần human input”**. [Amendment](acceptance-amendment.md) chuyển gate nghiệm thu plan01 sang automated review có authorization và receipt gắn đúng content hashes. Trạng thái G0 cuối cùng lấy từ [strict validation](../reports/g0-readiness.json) và [manifest](../freezes/G0/manifest.json); tự viết chữ accepted không đủ qua validator.

## Issues và disposition

Schema: issue_id, severity, location, problem, owner, disposition, evidence_ref. Review này do Codex thực hiện; human reviews để trống. Các unknown đã có owner/hạn được bàn giao như constraints thay vì giữ goal chờ người.

| issue_id | severity | location | problem | owner | disposition | evidence_ref |
|---|---|---|---|---|---|---|
| REV01 | major | README gốc | Trạng thái trước thu thập khác inventory hiện tại | A | Resolved: giữ README lịch sử, dùng structured inventory trong charter | [source audit](../validation/source-inventory.json) |
| REV02 | major | observations nguồn | Còn scenario_family_id/split, không phải inference-ready export | A | Resolved: biên allowlist/private được ghi rõ; export thuộc plan02 | [charter](project-charter.md) |
| REV03 | major | Hướng dẫn annotation cũ | Chấm đôi pilot không đủ contract mới | A | Resolved: mọi core passage pair chấm đôi; 56 là mục tiêu, hiện 0 judgments | [protocol](research-protocol.md) |
| REV04 | major | Condition names cũ | GEN-* chưa tách BM25/dense RAG | B | Resolved: IR-B/D/H, G0/GB/GD/GH; GR optional | [YAML](../configs/protocol.yaml) |
| REV05 | major | Cắt scope | Giảm test/core để tiết kiệm gây đổi thí nghiệm | C | Resolved: giữ90/split/core56/test18, cắt optional trước | [agreement](team-working-agreement.md) |
| REV06 | major | Freeze | Test qrels trước test pooling tạo vòng chờ | B | Resolved: F1→test_input→test_pool→F2→test_scoring | [protocol](research-protocol.md) |
| REV07 | major | Mẫu số | No relevant/empty/unjudged bị gộp sai | B | Resolved: undefined và0 có điều kiện riêng; thiếu top-5 judgments chặn scoring | [protocol](research-protocol.md) |
| REV08 | major | G0 | Nhầm gate project_start với no-RAG hoặc model approval | C | Resolved: gate_kind và condition riêng; permissions không đổi | [manifest](../freezes/G0/manifest.json) |
| REV09 | major | Human-only acceptance | Thiếu signatures giữ goal chờ dù user yêu cầu tự kiểm | C | Resolved by explicit amendment: review Codex độc lập, không tạo signatures người | [authorization](../configs/acceptance-authorization.json) |
| REV10 | major | Course/resources | Rubric/hạn/API/payload/local/sharing/budget chưa xác minh | C | Tracked constraint:15pending records có owner/hạn; G0 không cấp quyền model | [decision log](decision-log.md) |
| REV11 | major | Literature | Đọc selected sections của Codex không là người đã đọc full text | C | Resolved: provenance/mức đọc/reader thật và agent review, human status vẫn pending | [matrix](literature-matrix.tsv), [notes](literature-reading-notes.md) |
| REV12 | minor | Window units | Sample end inclusive khác observation end exclusive | A | Resolved: boundary chuyển đổi có kiểm, giữ source | [contracts](../../plans/reports/260913-independent-plans-contracts.md) |
| REV13 | major | Applicability | Timestamp lịch sử không đủ chứng minh đúng deployment | A | Tracked downstream:03/06 đánh giá applicability/evidence, unknown giữ nguyên | [protocol](research-protocol.md) |
| REV14 | minor | Plan CLI | Mixed newline gây lỗi status writer; phase status theo checkboxes | C | Resolved/tracked: newline fix có fixture; sync bằng CLI, report semantics | [progress](../reports/plan01-progress.md) |

## Nghiệm thu theo từng task

| Task | Điều Codex phải kiểm để chấp nhận | Artifact |
|---|---|---|
| 01.1.1 | Ba RQ, đóng góp NLP, input/output, giới hạn causal/offline | [charter](project-charter.md) |
| 01.1.2 | Đếm trực tiếp90/30, split54/18/18,0human judgments; không inference gold | [source audit](../validation/source-inventory.json) |
| 01.1.3 | Thư nháp hỏi rubric/model/payload/local/sharing/AI rõ; không gửi | [instructor draft](instructor-questions-draft.md) |
| 01.1.4 | Mọi pending có owner khác reviewer, hạn W1/W2/W5, source null thật | [decisions](../configs/decisions.json) |
| 01.2.1 | Primary/secondary, denominator, failed runs, freeze sequence và config khớp | [protocol](research-protocol.md), [YAML](../configs/protocol.yaml) |
| 01.2.2 | 10 bài có primary source, mức đọc thật, task-match và giới hạn | [matrix](literature-matrix.tsv), [notes](literature-reading-notes.md) |
| 01.2.3 | Phân vai đủ3role, review chéo, lịch 8 tuần, tính công và kịch bản thiếu giờ | [agreement](team-working-agreement.md) |
| 01.2.4 | API/local/extractive có điều kiện, budgetnull và cutoffW2; không tự cấp quyền | [decision log](decision-log.md), [YAML](../configs/protocol.yaml) |
| 01.3.1 | Mọi issue kỹ thuật xử lý; unknown được giữ/định tuyến, không bị giấu | Tài liệu review này và [code review](../reports/code-review.md) |
| 01.3.2 | Agent độc lập kiểm đủ data/design/resources/literature, gắn exact hashes | [autonomous receipt](../reports/plan01-autonomous-review.json) |
| 01.3.3 | Manifest version/bytehash/source/permissions/authorization hợp lệ | [G0 manifest](../freezes/G0/manifest.json), [strict check](../reports/g0-readiness.json) |
| 01.3.4 | Đối chiếu producer/consumer từng plan02–10 và lưu handoff đọc được | Bảng handoff bên dưới, [progress](../reports/plan01-progress.md) |

## Walkthrough và evidence kiểm thực

Dev hòa chọn BM25 trên score defined; không eligible dev giữselection pending. Không relevant judged evidence thì nDCG/recall undefined+count; relevant nhưng ranking rỗng=0. Unjudged khác 0; thiếu finaltop-5 judgments chặn scoring. Hybrid thua vẫn hợp lệ. Test 18 incidents chỉ 6 families; giữ pairing. Các quy tắc này được code/config review, không bị biến thành kết quả thí nghiệm.

API pending/rejected không có api_generation; local cần quyền riêng. Tất cả generator bị từ chối dẫn tới đề xuất amendment retrieval/extractive và RQ3 not_run ở plan07, không đổi scope khoa học tại đây. Corpus/qrels chưa xong không là điều kiện G0 nhưng ngăn F1/F2/scoring tương ứng. Giờ 8/người/tuần chỉ 192h, thiếu116–182h trực tiếp; workingagreement nêu giới hạn thay vì cam kết khả thi giả.

Test suite giữ human mode cũ và thêm mode automated. Sửa byte artifact/receipt, thiếu authorization, scope sai, tênCodex giả vào humanreview, permission mismatch hoặc testpool trước F1 phải fail. Automated mode đủ scopedauthorization+receiptPASS+hashes thì strictG0pass. [Test report](../reports/plan01-tests.md) ghi command/counts/receipts thực; [technical validation](../reports/protocol-validation.json) và [strict gate](../reports/g0-readiness.json) dùng artifact hiện tại.

## Review attribution

`review_mode=automated`; reviewer độc lập là Codex agent, khai trong receipt với UTC và phạm vi. `reviewers=[]` và `pending_reviews=[]` biểu thị không sử dụng human review gate theo amendment, không biểu thị có human review đã xong. Actual human literature statuses, tên/giờ nhóm và instructor decisions vẫn chưa xác minh. Các labels hoặc signature người thật không được tạo bởi reviewmode này.

## Handoff artifacts đã được tự kiểm

| Bên nhận | Input/contract được kiểm | Owner / reviewer role | Kết quả kiểm của Codex |
|---|---|---|---|
| 02 data/environment | Allowlist/private, counts/split, units và sharing constraints | A / C | Contract rõ; export phải qua validator của02 |
| 03 corpus | Historical scope, IDs/offsets/applicability, paper không vào index | A / B | Contract rõ; unknown applicability giữ nguyên |
| 04 representation | RQ1train/dev, shared retained evidence, test renderer sau F1 | B / A | Producer/consumer và thời điểm tạo test inputs khớp |
| 05 retrieval | IR-B/D/H, GR optional, metrics, short rankings/pooling | B / C | Ba baseline và failure accounting được giữ |
| 06 annotation | Core20/18/18, hai người chấm, unjudged, documentgrade riêng,F2 | A / B | Qrels vẫn công việc tương lai; không thay bằng agentlabels |
| 07 generation | G0/GB/GD/GH, common bundle/context, permissions và cutoff | C / B | Chưa được chạy model chỉ từ G0; mock/tooling theo plan07 |
| 08 evaluation | Devprimary/tie, F1/F2 chain, denominators,sáu family deltas | B / A | Không có vòng chờ test qrels trước test pool; scoring sau F2 |
| 09 demo | Offline support,citations,unknowns; privategold không vào live | C / A | Giới hạn claims và biên dữ liệu khớp |
| 10 report/release | Claim limits, provenance, archived-input reproduction | C / B | G0 không là kết quả khoa học hay permission nộp bài |

Đây là kiểm việc bàn giao artifact, không là acknowledgment của người thật hoặc thông báo đã gửi. Communication status vẫn pending/unsent. Phạm vi goal này dừng ở plan01; không thực thi02–10. Bên nhận dùng version/hash và điều kiện cụ thể trước chạy phần được giao.

## Lịch sử và hoàn tất

Draft.1/.2 cần human review theo contract cũ và đã được báo chưa đạt. Chỉ dẫn mới được ghi thành D16 confirmed, tạo reviewed.1, giữ manifests và documents trước. Contract snapshot trước ghi checkboxcompletion ở freezes/G0/plan-source; live plan là sổ tracking. Nghiệm thu cuối phải có review PASS, tests PASS và strict G0 PASS; sau đó sync cả 3 phase/12 task và journal bằng evidence thật.
