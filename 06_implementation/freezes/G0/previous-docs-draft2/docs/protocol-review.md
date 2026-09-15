# Protocol review và bàn giao G0

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2`.

**G0 project_start: awaiting_human_review.** Các tài liệu đã được soạn để review. Không có chữ ký người thật, communication vẫn pending. Manifest ở thư mục `freezes/G0` là candidate có hashes; vị trí thư mục không chứng minh gate đã accepted. API/payload/local/sharing/budget vẫn pending độc lập với G0.

Draft.2 ghi các sửa sau automated review: ràng buộc outcome/amount của permission decisions, kiểm literature provenance và coverage review-log, đối chiếu trạng thái gate YAML/manifest, và giữ tính idempotent khi builder có manifest kế thừa. Đồng thời sync tiến độ plan và làm mới source inventory receipt sau thay đổi metadata của plan01. Draft.1 được giữ trong manifest archive; không có experimental setting hay human permission nào được thay đổi.

## Issues và disposition

Schema: issue_id, severity, location, problem, owner, disposition, evidence_ref. `resolved_in_draft` là sửa/giải thích kỹ thuật của Codex, không là chấp thuận của nhóm.

| issue_id | severity | location | problem | owner | disposition | evidence_ref |
|---|---|---|---|---|---|---|
| REV01 | major | README.md vs START-HERE.md | README cũ nói chưa có dữ liệu, trái inventory hiện tại | A | resolved_in_draft: giữ README lịch sử, charter dẫn structured inventory | [audit16checks](../validation/source-inventory.json) |
| REV02 | major | source observations.jsonl | Có scenario_family_id và split; chưa được dùng như inference export | A | resolved_in_draft: allowlist ở plan02, private labels chỉ evaluator | [charter](project-charter.md), [source audit](../validation/source-inventory.json) |
| REV03 | major | method-and-experiment-design.md, phần annotation | Hướng dẫn cũ chỉ chấm đôi pilot rồi chọn tỷ lệ | A | resolved_in_draft: contract mới chấm đôi mọi core passage pair của56incidents | [contracts](../../plans/reports/260913-independent-plans-contracts.md), [protocol](research-protocol.md) |
| REV04 | major | experiment-proposal và experiments_and_evaluation cũ | IR-1/GEN-* không tách đủ BM25-RAG và dense-RAG | B | resolved_in_draft: IR-B/IR-D/IR-H; G0/GB/GD/GH; GR optional | [YAML](../configs/protocol.yaml) |
| REV05 | major | timeline_and_scope.md cũ | Cắt incidents có thể làm đổi core/test | C | resolved_in_draft: giữ90/split/core56/test18; đổi phải amendment có review | [working agreement](team-working-agreement.md) |
| REV06 | major | freeze workflow | Đòi test qrels trước retrieval pooling tạo vòng chờ | B | resolved_in_draft: F1→test_input→test_pool→F2→test_scoring | [protocol](research-protocol.md) |
| REV07 | major | metric denominator | Không relevant và empty ranking dễ bị gán cùng0 | B | resolved_in_draft: no relevant=undefined+count; relevant nhưng empty=0; thiếu top5 judgments chặn headline | [protocol](research-protocol.md) |
| REV08 | major | gate và condition G0 | G0 bị đọc thành no-RAG/approval model | C | resolved_in_draft: gate_kind=project_start, condition=G0; permissions độc lập | [manifest](../freezes/G0/manifest.json) |
| REV09 | major | human reviews | Chưa có A/B/C tên thật, giờ hoặc review signatures | C | open_human_required: D03/D04/D16; không auto-sign | [decisions](decision-log.md) |
| REV10 | major | permissions/course | Rubric/deadline/API/payload/local/sharing/budget chưa có nguồn quyết định | C | open_tracked: owner/hạn riêng, chỉ chặn phần tương ứng | [decisions](../configs/decisions.json) |
| REV11 | major | literature acceptance | Codex đọc selected sections không là nhóm đã đọc/review | C | open_human_required: assignments và human statuses pending | [matrix](literature-matrix.tsv), [notes](literature-reading-notes.md) |
| REV12 | minor | window units | Sample end inclusive khác observation end exclusive | A | resolved_in_draft: chuyển đổi có kiểm ở boundary plan02, không sửa raw để ép bằng nhau | [contract boundary](../../plans/reports/260913-independent-plans-contracts.md) |
| REV13 | major | corpus applicability | Timestamp cũ không chứng minh đúng deployment/answerability | A | open_downstream: plan03/06 kiểm evidence, unknown giữ nguyên | [protocol](research-protocol.md) |
| REV14 | minor | plan status tooling | ak plan file update cần tương thích newline Windows | C | tracked_in_progress_report: không đánh all checkboxes khi thiếu human review | [progress](../reports/plan01-progress.md) |

## Walkthrough nghiệm thu

| Trigger | Kết quả bắt buộc / evidence |
|---|---|
| Rubric thiếu | D01 pending, C/B, cuối W1; không bịa tiêu chí môn |
| API pending/rejected | Không api_generation; tiếp tục chuẩn bị IR/data; local phải có quyền riêng |
| Tất cả model bị từ chối | D10 đề xuất amendment retrieval/extractive; RQ3 not_run, không âm thầm đổi scope |
| Family có ba repetitions | Cùng split; test18incidents chỉ6clusters độc lập |
| Dev BM25=dense | Tie-break BM25 khi scores defined; không có eligible dev giữ selection pending |
| Không relevant/thiếu judgments | Undefined+count khi không relevant; unjudged khác0; không loại ca để vượt gate |
| Hybrid thua | Giữ primary contrast và báo hiệu số âm |
| Corpus/qrels chưa xong | G0 không đòi qrels thật; không gọi F1/F2/scoring đã sẵn sàng |
| Giờ chỉ8/người/tuần |192h <308–374h trực tiếp; ghi thiếu công, cắt optional rồi xem lại lịch/phạm vi |
| Sửa byte artifact sau manifest | Validator fail hash, không tự cập nhật trong check; tăng version/giữ manifest cũ trước bàn giao lại |
| Test qrels trước F1 | Validator fail freeze sequence |
| Chỉ Codex review | Draft technical validation có thể PASS; strict G0 readiness phải FAIL |
| Thư mới soạn | Communication pending; sent_at_utc=null |

Đọc kết quả thực từ [technical validation](../reports/protocol-validation.json), [strict gate check](../reports/g0-readiness.json), [independent review](../reports/code-review.md). Các walkthrough ở trên mô tả acceptance, không tự là kết quả chạy model hoặc xác nhận con người. Chỉ report có command/time/input evidence mới chứng minh kiểm kỹ thuật đã chạy.

## Review records cần người thật

| Role | Person | Scope | reviewed_at UTC | Decision / source_ref |
|---|---|---|---|---|
| A | null | Inventory, leakage boundary, source/applicability limitations | null | pending / null |
| B | null | RQ, metrics/denominators, F1/F2, test integrity/reproduction | null | pending / null |
| C | null | Scope/resources, assignments/reading, decisions and handoff | null | pending / null |

Không ghi các dòng pending này vào `reviewers` như review đã hoàn tất. Manifest dùng reviewers=[] và pending_reviews riêng. G01-A cần C chấp nhận inventory/câu hỏi; G01-B cần A/B/C kiểm boundary/design/nguồn lực; G0 cần review người khác và nhận bàn giao. Cung cấp tên/giờ chưa tự chứng minh đã review artifact; phải nêu cùng version/hash.

## Handoff được chuẩn bị, chưa được xác nhận

| Bên nhận | Nội dung chuyển | Owner / reviewer | Receiver acknowledgment |
|---|---|---|---|
| 02 data/environment | Allowlist inference vs private, source counts/split, sharing constraints | A / C | pending |
| 03 corpus | Historical scope, IDs/offsets/applicability, paper không vào index | A / B | pending |
| 04 representations | RQ1 train/dev, shared retained evidence và test renderer sau F1 | B / A | pending |
| 05 retrieval | IR-B/D/H, GR optional, primary metric, short rankings/pool contracts | B / C | pending |
| 06 annotation | Core20/18/18, hai người chấm, unjudged, document relevance riêng, F2 | A / B | pending |
| 07 generation | G0/GB/GD/GH, common bundle/context, permissions và chi phí chưa duyệt | C / B | pending |
| 08 evaluation | Stronger dev single/tie BM25, F1/F2 chain, denominators, sáu family deltas | B / A | pending |
| 09 demo | Offline support/citations/unknowns, private gold không vào live | C / A | pending |
| 10 report/release | Claim limits, provenance, replay/tái tính và pending review | C / B | pending |

Các bên nhận kiểm version/hash trước dùng. Allowed work trong manifest chỉ cho biết những phần có thể chuẩn bị theo contract; không thực thi plans02–10 từ delivery01 và không ghi đè artifacts của task khác. C tổ chức review/hand-off nội bộ và tự gửi thư khi đã kiểm nội dung. Communication chưa gửi không chuyển thành received.

## Điều kiện nâng G0

Hoàn tất tên/vai trò/khả năng thực hiện, human reading/review và acknowledgments thật; lưu issue dispositions và source_refs. Đổi protocol draft→reviewed và manifest candidate→accepted chỉ sau review; tạo version mới, cập nhật hashes và giữ candidate cũ. API có thể vẫn pending mà G0 accepted có điều kiện, nhưng allowed_work không có api_generation. Chạy validator thường và `--require-g0`; technical PASS riêng không thay gate readiness.
