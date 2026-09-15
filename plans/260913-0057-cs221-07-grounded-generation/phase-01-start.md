---
phase: 1
title: "Khóa contract output và preflight generator"
status: pending
priority: P1
effort: "6h"
dependencies: []
---

# Phase 01: Khóa contract output và preflight generator

## Tổng quan

Chốt schema dùng chung, model branch, token budgets và quyền xử lý payload trước khi có bất kỳ API pilot thật nào.
Công dự kiến **6 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Quyền và protocol | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` | API/local/budget cần bằng chứng approved |
| Observation bundle từ 04 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/observation-bundles.jsonl` | Bundle schema và bundle_hash cố định dùng chung các conditions |
| Inference export | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/` | 02.export có allowlist và redaction |
| Chunk registry | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/` | 03.corpus có revision, offsets, applicability |
| Retrieval runner | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/` | 05.runners cho rankings train/dev |
| Rubric pilot | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/` | 06A rubric cho support/answerability; không đọc qrels trong prompt |

## Yêu cầu

- Model chính có điều kiện: DeepSeek V4.1 Flash, API name deepseek-flash; không coi alias là immutable revision.
- Thinking mặc định bật; OpenAI SDK dùng extra_body={thinking:{type:disabled}} để pilot non-thinking rõ ràng.
- JSON mode dùng response_format={type:json_object}, prompt có từ json và ví dụ; vẫn xử lý rỗng/truncated/invalid schema.
- Token limits tách observations2048, knowledge4096, output768; prompt/system tính riêng; encoder512 không thay generator budget.
- Dùng observations và bundle_hash từ 04, không tự tái dựng khác từ raw export; adapter nếu cần phải bảo toàn nội dung/chính sách và kiểm hash. Một output language, generator và decoding policy chung; top_p non-thinking bị cố định/ignored, không diễn giải thành núm tune hiệu quả.
- G0 no-RAG được dẫn observation IDs; GB/GD/GH nhận cùng observations và knowledge từ đúng retriever.

## Kiến trúc và ranh giới trách nhiệm

Bundle 04 đã dùng export 02 được duyệt + ranked chunks → context packer → prompt có schema → provider adapter → raw response → schema/citation validator. Đây là thư viện Python cục bộ, không tool execution.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/generation.yaml` — Provider, budgets, retries, approved cap.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/prompts/grounded-diagnosis.txt` — Prompt cố định với json example.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/schemas.py` — Request, response và ledger schema.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/generation-protocol.md` — Quyền, threat model, fairness và provenance.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Request:incident_id,condition,run_id,observations,bundle_hash,knowledge_context,context_hash,prompt_hash,config_hash; observations lấy bundle của 04, cấm split/family/gold.
- Payload:candidate_causes:[{service_id,fault_type,reason}], supported_claims:[{claim_id,text,type,evidence_ids}].
- Payload thêm incident_id,missing_information:string[],next_checks:string[],abstain:boolean,confidence_label:string.
- Claim type=observation|inference; evidence_ids phải thuộc actual context record của request, không chỉ tồn tại global corpus.
- Context item:evidence_id,source_kind,document_id?,chunk_id?,text,start_codepoint,end_codepoint,source_revision; offsets trên normalized text.
- Run record:raw_response,parsed_payload|null,actual_context_ids,actual_context_hash,model_requested,model_returned|null,provider_epoch.
- Record thêm status,error,attempts,usage,UTC/request_id; unknown metadata dùng null, không đoán model revision.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 07.1.1 | 1h | Codex + C / A | Decision log và payload sample train | Kiểm quyền/API cap/redaction; chọn nhánh được phép | Preflight record hoặc blocker rõ |
| 07.1.2 | 2h | Codex + C / B | Rubric và shared contracts | Viết JSON schema, ID policy, fixture ví dụ | schemas.py và contract review |
| 07.1.3 | 2h | Codex + C / A và B | Export, chunks, token allowances | Thiết kế prompt/context policy, kiểm malformed/missing evidence | Prompt/config draft có hash |
| 07.1.4 | 1h | C + Codex / B | Docs provider hiện hành | Xác minh model/settings/giá tại ngày chạy, ghi metadata | Generation protocol và preflight receipt |

## Trình tự thực hiện

1. Đọc [pricing DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/) tại ngày pilot; giá kiểm13/09/2026 input cache miss$0.30/output$1.20 mỗi triệu tokens chỉ làm mốc.
2. Đọc [thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) và [JSON mode](https://api-docs.deepseek.com/guides/json_mode/); ghi setting gửi thực tế.
3. Chặn API nếu permission hoặc approved_cap_usd chưa có; fixtures/contract vẫn làm được.
4. Nếu dùng local fallback, xác minh license/revision, quyền môn học và GPU Kaggle thực; model phải pilot vừa tài nguyên trước chọn.
5. Mô tả field allowlist; parse incident opaque IDs thay raw case names; chỉ serialize trường đã duyệt.
6. Đặt temperature/settings rõ theo docs; không hứa seed hoặc temperature0 tạo bitwise determinism.
7. Dùng status blocked_permission để ghi preflight; không gọi smoke API nhằm thử xem có bị cấm không.
8. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
9. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| API pending | Không có source_ref approve | Không gọi provider; vẫn kiểm fixtures |
| Thinking mặc định | Config bỏ trường thinking | Fail preflight; yêu cầu disabled explicit |
| Context ID giả | ID có trong corpus ngoài request | Validator contract phải reject citation |
| Gold trong request | Export chứa injected service label | Fail allowlist trước provider |
| JSON mode rỗng | Provider trả empty content | Raw giữ nguyên; status invalid_response |
| Quyền local chưa rõ | API rejected/local pending | Không tự tải/chạy local model |

## Checklist thực hiện

- [ ] **07.1.1**: Preflight record hoặc blocker rõ; Codex + C / A xác nhận bằng chứng.
- [ ] **07.1.2**: schemas.py và contract review; Codex + C / B xác nhận bằng chứng.
- [ ] **07.1.3**: Prompt/config draft có hash; Codex + C / A và B xác nhận bằng chứng.
- [ ] **07.1.4**: Generation protocol và preflight receipt; C + Codex / B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 6h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Schema có citations gắn từng claim, actual-context lookup và output lỗi đầy đủ.
- [ ] Config nêu rõ non-thinking, budget và quyền đã kiểm hoặc blocker thật.
- [ ] Preflight tách model requested/returned, provider epoch và hạn chế alias bất biến.
- [ ] A duyệt payload, B duyệt công bằng; không dùng gold/reference trong prompt.

## Gate nghiệm thu và điều kiện thất bại

G07-A: contract/fixtures review đạt; gọi thật cần permission, tài nguyên và trần chi đã duyệt. Nếu chưa đủ, phase build offline tiếp tục nhưng pilot thật còn pending.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Docs/API đổi: kiểm lại trước chạy, lưu thời điểm. JSON mode không bảo đảm schema: luôn giữ raw và errors. Output tự tin không là confidence đã hiệu chỉnh.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase2 nhận schema/prompt/config đã review. 09 có thể dùng fixture contract để scaffold; fixture không là kết quả nghiên cứu.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

