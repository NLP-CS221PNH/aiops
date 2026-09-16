---
phase: 2
title: "Xây context, adapter, runner và pilot train/dev"
status: completed
priority: P1
effort: "14h"
dependencies: [1]
---

# Phase 02: Xây context, adapter, runner và pilot train/dev

## Tổng quan

Triển khai đường sinh dùng lại được, giới hạn lỗi/chi phí và chạy pilot trên train/dev để 08 có đầu vào lựa chọn trước F1.
Công dự kiến **14 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Contract | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/schemas.py` | G07-A review schema |
| Prompt/config | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/generation.yaml` | Quyền và cap cho gọi thật |
| Runners | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/` | IR-B/D/H dùng chung query/corpus |
| Bundle từ 04 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/observation-bundles.jsonl` | Chọn đúng incident_id; kiểm bundle_hash và cùng bundle cho G0/GB/GD/GH |
| Train/dev export | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/` | Coordinator chọn IDs qua private join; runner không mount gold |

## Yêu cầu

- Observations lấy từ bundle do 04 tạo, không dựng lại từ raw inference; ghi source bundle_hash cùng actual observations hash nếu cắt theo policy 2.048 tokens. Packer giữ thứ hạng, tối đa5 chunks sau dedup đúng chunk ID; ranking rỗng/ngắn ghi thật, không bù evidence từ hệ khác.
- Cùng content field section_heading+text; cắt có thể giảm support, phải lưu EXACT text/offset gửi thực tế và dropped/truncated ledger.
- Chỉ retry lỗi tạm thời429/5xx/network theo protocol, tối đa3 attempts gồm ban đầu; malformed/quality/citation failure không là lý do retry.
- Mỗi attempt có UTC,status,usage/cost; timeout chưa biết usage ghi unknown và dự phòng chi bảo thủ; không bỏ phí attempt lỗi.
- Budget cap kiểm trước request với worst-case dự toán; stop khi phần còn lại không đủ; no paid call khi cap chưa approved.
- Cache theo input/context/prompt/model/config+provider_epoch; resume chỉ cùng cohort, force-fresh cho cohort mới khi backend có thể đổi.
- Pilot chỉ train/dev; cuối cùng 08 mới chọn representation/primary baseline và thực thi final sau F1/F2.

## Kiến trúc và ranh giới trách nhiệm

Packer deterministic theo config → adapter → runner tuần tự/checkpoint → validation → ledger immutable. G0 dùng knowledge rỗng có nhãn điều kiện, không thêm filler để ép token bằng RAG.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/context_builder.py` — Token packing, context snapshot/ledger.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/provider.py` — API/local adapter và metadata.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/validator.py` — Schema/citation integrity.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/runner.py` — Attempts, checkpoint, resume, cost cap.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/__main__.py` — Entry point cho `python -m src.generation`; parse arguments và chuyển cho runner, không nhân đôi logic provider/gates.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<pilot_run_id>/manifest.json` — Cohort, config/hash, selected IDs.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<pilot_run_id>/responses.jsonl` — Một record cho mỗi incident×condition.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<pilot_run_id>/attempts.jsonl` — Usage và lỗi mọi attempt.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/generation-pilot.md` — Pilot train/dev và vấn đề cần xử lý.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Context snapshot:{incident_id,condition,bundle_hash,observation_items,knowledge_items,actual_context_ids,context_hash,token_counts,truncation_ledger}.
- Token_counts:{observations,knowledge,system_prompt,output_limit,tokenizer_id,method:exact|estimated}; usage thật bổ sung sau gọi.
- Attempt:{attempt_id,request_key,attempt_index:1..3,started_at,ended_at,status,retry_reason,usage?,cost_estimate_usd,billing_unknown}.
- Cache key=hash(canonical(input+actual_context+prompt+model_requested+config+provider_epoch)); cache_hit không được giả thành live.
- Record status=success|invalid_response|invalid_citation|provider_error|budget_stopped|blocked_permission; parsed_payload=null nếu parse thất bại.
- Write tạm+atomic rename theo record; cache index nối artifact hash, không chỉ incident ID; một tiến trình sở hữu run directory.
- Pilot manifest nêu số planned/attempted/failed/stopped và split scope; test ID bị coordinator chặn trước runner.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.
- CLI dự kiến, chạy từ `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation`: `python -m src.generation run --freeze freezes/F1.json --input-manifest queries/test/test-input-manifest.json --incident-list <test_ids> --run-id <final_run>`. Đây là giao diện để plan 08 gọi sau khi kiểm F1/F2; plan 07 không thực thi final test.
- CLI pilot dùng `run --config configs/generation.yaml --incident-list <train_dev_ids> --run-id <pilot_run>`; `--config` và `--freeze` loại trừ nhau. `--incident-list` đọc file opaque IDs, không mount gold/qrels; final config và conditions lấy từ F1, test queries/bundle lấy từ input manifest liên kết F1. Kiểm actual hashes trước dùng; không cho override bằng tham số tuning.
- Test manifest do 08 tạo sau F1 bằng frozen functions 04, trỏ tới `queries/test/observation-bundles.jsonl`; không đọc file train/dev mặc định trong frozen test mode. Manifest này chỉ chứa metadata đầu vào được duyệt, không chứa qrels/private labels.
- CLI chuyển nguyên request tới runner; kiểm freeze/hash/permission/cap trước provider, ghi records vào `runs/<run_id>/`. Exit code 0 khi toàn bộ records bắt buộc thành công, 1 khi run có failed/invalid/stopped records đã ghi ledger, 2 khi arguments hoặc preflight không hợp lệ; lỗi không kích hoạt quality retry.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 07.2.1 | 4h | Codex + C / B | Schema, bundle04, query/rankings, tokenizer | Xây packer và validator actual context, lưu truncation | Context snapshots tái lập |
| 07.2.2 | 3h | Codex + C / A | Provider docs và quyền đã duyệt | Xây adapter non-thinking/JSON, metadata, raw capture | Provider adapter có mock tests |
| 07.2.3 | 4h | Codex + C / B | Contract attempts/cache/cap và CLI consumer 08 | Xây entry point chuyển tới runner, checkpoint, budget guard, finite retry, resume | Runner và CLI có ledger đầy đủ |
| 07.2.4 | 3h | C + Codex / A và B | Train/dev cases, G07-A đủ quyền | Pilot đủ các điều kiện bắt buộc; đọc lỗi/support theo rubric | Pilot report và artifacts cho08 |

## Trình tự thực hiện

1. Tạo fixture đủ evidence/thiếu/mâu thuẫn; dùng train để debug schema trước tiêu ngân sách.
2. Kiểm chunk trùng và offsets; citation chỉ trỏ ID/text thực được gửi, không trỏ nguyên chunk chưa gửi đầy đủ.
3. Chuẩn bị cả G0/GB/GD/GH trong cùng manifest, GR chỉ nếu05 có runner và đã chọn optional cho pilot.
4. Ghi mọi giá trị config trước gọi; đảo thứ tự condition có seed nếu protocol chọn để giảm hiệu ứng thời gian, không dùng seed giả determinism.
5. Chạy pilot nhỏ, kiểm usage thực so ước lượng; C dừng nếu có payload sai hoặc chi phí bất thường.
6. Mở rộng train/dev trong allowance đã duyệt; B so cùng input/context budget, A kiểm evidence support.
7. Giữ output invalid nguyên bản; sửa prompt chỉ trên train/dev bằng version mới áp dụng đều cấu hình.
8. Tổng hợp những lựa chọn còn mở cho08; không tự chọn baseline chính bằng scores test.
9. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
10. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Top5 quá dài | 5 chunks vượt4096tokens | Cắt theo policy chung, lưu actual spans/tokens |
| Ranking ngắn/rỗng | 2 chunks/0 chunks | Trả đúng2/0, ghi short/empty; không padding |
| 429 rồi thành công | Attempt1=429,2=success | 2ledger rows, tổng usage/cost, một response |
| Lỗi liên tục | 3 lần timeout/5xx | Dừng sau3, failed record giữ trong mẫu số |
| Hết cap | Dự toán request vượt phần còn lại | Không gọi, budget_stopped cho record |
| Resume | Kill sau raw write trước index | Khôi phục nhất quán, không nhân đôi response |
| JSON/citation sai | Raw không parse/ID ngoài context | Lưu raw, invalid status, không quality retry |
| CLI consumer 08 | Lệnh frozen với fixture provider; F1 đúng rồi thử hash sai | Entry point chuyển đúng arguments tới runner; records/exit code khớp; hash sai chặn provider trước gọi thật |

## Checklist thực hiện

- [x] **07.2.1**: Context snapshots tái lập; Codex + C / B xác nhận bằng chứng.
- [x] **07.2.2**: Provider adapter có mock tests; Codex + C / A xác nhận bằng chứng.
- [x] **07.2.3**: Runner và `python -m src.generation run` có ledger/exit codes đúng contract; Codex + C / B xác nhận bằng chứng.
- [x] **07.2.4**: Pilot report và artifacts cho08; C + Codex / A và B xác nhận bằng chứng.
- [x] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [x] Đối chiếu tổng công task với 14h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Packer/validator/adapter/runner dùng chung schema; bốn điều kiện mandatory hoạt động trên fixture.
- [x] Pilot thật chỉ train/dev khi có quyền; request/response/usage/errors lưu đầy đủ.
- [x] Context limits và truncation kiểm được, token ước lượng ghi rõ khác usage thật.
- [x] Resume không bỏ trạng thái lỗi, duplicate output hoặc làm mất chi phí.

## Gate nghiệm thu và điều kiện thất bại

G07-B: fixtures về contract/lỗi đạt và pilot train/dev có receipts; nếu permission chưa có thì adapter hoàn tất được nhưng milestone07.pilot thật còn pending.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Alias thay backend giữa pilot: cohort metadata và thời điểm bắt buộc; nghi thay đổi tạo cohort mới. Nhiều retries vượt tiền: dự toán worst-case gồm unknown billing, cap hữu hạn.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 3 nhận artifacts pilot và issue list;08 chỉ nhận pilot thành dữ kiện sau audit. 09 nhận loader/interface, chưa nhận final test results.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

