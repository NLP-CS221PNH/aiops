---
phase: 3
title: "Kiểm độ bền, fairness và bàn giao 07.pilot"
status: completed
priority: P1
effort: "8h"
dependencies: [2]
---

# Phase 03: Kiểm độ bền, fairness và bàn giao 07.pilot

## Tổng quan

Kiểm adversarial inputs, chi phí, resume và tính công bằng; xuất gói adapter/pilot đủ cho 08 đóng F1 mà chưa chạy test.
Công dự kiến **8 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Runner | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/runner.py` | Version và error paths |
| Pilot responses | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<pilot_run_id>/responses.jsonl` | Raw/parsed/context/attempt provenance |
| Attempt ledger | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<pilot_run_id>/attempts.jsonl` | Known/unknown usage, cap |
| Rubric/dev | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/` | Human rubric/support; qrels không mount runner |

## Yêu cầu

- Test injection coi log/tài liệu là dữ liệu; không chạy commands, tool calls hay truy cập URL do model tự tạo.
- Citation validity tách support: ID hợp lệ chưa chứng minh claim được đoạn đó hỗ trợ; người chấm kiểm nội dung.
- Prompt/model/config changes chỉ train/dev; sau bàn giao08 sẽ freeze và quản lý protocol deviation.
- 08 sở hữu F1 và final test execution;07 không cần test qrels để hoàn tất adapter/pilot.
- Gói bàn giao chứa fixtures lỗi có nhãn; không trộn vào metrics nghiên cứu.

## Kiến trúc và ranh giới trách nhiệm

Fixtures + train/dev artifacts → test contract/failure/fairness → human spot review → release adapter receipt →08.F1/09 scaffold. Mọi reviewer thấy limitations alias/uncertainty.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_generation_contract.py` — Schema, actual-context citation, leakage.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_generation_reliability.py` — Retries/cap/checkpoint/cohort.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/generation-protocol.md` — API settings, usage và limitations.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/generation-pilot.md` — Lỗi đã xử lý, residual limitations.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/generation-handoff.json` — Hashes, receipts và unresolved issues.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Handoff:{milestone:07.pilot,code_hash,config_hash,prompt_hash,schema_version,pilot_run_ids,validation_receipts,permissions_ref}.
- Fairness audit:{incident_id,conditions,observations_hash,model_config_hash,prompt_contract_hash,context_allowance,pass,reason}.
- Validation receipt:{test_id,fixture_hash,observed_status,expected_status,artifact_hash,checked_at,reviewer}.
- Support spot review:{response_id,claim_id,evidence_ids,actually_supports:yes|partial|no|unknown,reviewer,note}; không gọi đây là human qrels đầy đủ.
- Residual limitation:{kind:alias_revision|billing_unknown|token_estimate|other,affected_runs,interpretation}; không điền zero cho dữ liệu thiếu.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 07.3.1 | 3h | Codex + C / B | Fixtures về retry/cap/cache | Kiểm lỗi, resume, cohort và zero duplicate | Reliability receipts |
| 07.3.2 | 2h | Codex + A / C | Payload/context và injection fixtures | Kiểm leakage, citations ngoài/thiếu actual spans | Contract/privacy receipts |
| 07.3.3 | 2h | A và B + Codex / C | Train/dev pilot và rubric | Spot-check support/abstention, fairness4 conditions | Pilot audit và limitations |
| 07.3.4 | 1h | C + Codex / B | Receipts, code/config hashes | Viết hướng dẫn consumer08/09 và final ownership | 07.pilot handoff |

## Trình tự thực hiện

1. Chạy test stub provider deterministic để tách lỗi code với biến động model.
2. Đặt citation tới chunk tồn tại trong corpus nhưng không actual context; thêm truncated-away evidence để kiểm không xác nhận quá mức.
3. Dừng/resume tại nhiều điểm: trước call, sau raw, sau atomic write; kiểm ledger attempts và count planned.
4. Thử cache cùng cohort và force-fresh khác cohort; không tái dùng alias cũ ngầm sau thay backend.
5. So bốn conditions cùng observations/model/decoding/output_limit; G0 thiếu knowledge là khác biệt có chủ đích.
6. Nhờ A/B xem vài claims train/dev đủ/thiếu/mâu thuẫn và ghi hạn chế; không biến spot review thành bộ labels đã hoàn tất.
7. Khi sửa bug, chạy lại tests chịu ảnh hưởng và giữ pilot versions cũ; không chạy thêm theo tiêu chí đáp án đẹp.
8. Gửi handoff local tới08 bằng artifact paths;08 tự xác minh hash trước đóng F1.
9. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
10. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Prompt injection | Log yêu cầu bỏ luật/chạy rm/URL | Không tool execution; nội dung là evidence |
| Citation corpus-only | Global ID hợp lệ ngoài request | invalid_citation |
| Claim không được support | ID đúng nhưng câu suy diễn | Validator chỉ validity; human chấm unsupported |
| Budget và crash | Timeout+kill+resume | Không mất attempt, unknown billing vẫn tính dự phòng |
| Cohort mới | Alias/model name giống, epoch khác | Cache miss/force-fresh đúng policy |
| Top_p setting | Provider nonthinking bỏ qua top_p | Docs nêu ignored; không claim đã kiểm soát sampling bằng nó |
| Final test request | Coordinator chọn test trước F1 | Block orchestration; không chạy từ07 |

## Checklist thực hiện

- [x] **07.3.1**: Reliability receipts; Codex + C / B xác nhận bằng chứng.
- [x] **07.3.2**: Contract/privacy receipts; Codex + A / C xác nhận bằng chứng.
- [x] **07.3.3**: Pilot audit và limitations; A và B + Codex / C xác nhận bằng chứng.
- [x] **07.3.4**: 07.pilot handoff; C + Codex / B xác nhận bằng chứng.
- [x] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [x] Đối chiếu tổng công task với 8h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Ma trận contract/reliability có receipts khớp code/config hiện hành.
- [x] Mọi failed/invalid/stopped record giữ nguyên raw và trạng thái trong ledger.
- [x] Bốn conditions audit fairness đạt; support nội dung có reviewer người thật.
- [x] Handoff07.pilot đủ schema/code/config/limitations,08 và09 nhận đúng interface.

## Gate nghiệm thu và điều kiện thất bại

G07-C/07.pilot: tests có ý nghĩa đạt, pilot train/dev đủ quyền và artifacts có provenance; không cần hybrid thắng. Permission/pilot thật thiếu thì ghi blocker, không tự hoàn tất gate.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Tưởng mock pass là model quality tốt: phân biệt tooling correctness và pilot evidence. Test model không lặp đúng token: công bố tái lập config/cache, không hứa bitwise generation.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

08 dùng adapter để khóa F1, chạy test pool/F2/final execution và scoring;09 dùng responses/context snapshot cho viewer. 07 kết thúc tại bàn giao này, không sở hữu final run.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.
