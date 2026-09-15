---
phase: 3
title: "Kiểm leakage, provenance và bàn giao variants"
status: pending
priority: P1
effort: "6h"
dependencies: [2]
---

# Phase 3: Kiểm leakage, provenance và bàn giao variants

## Overview

Chứng minh variants giữ boundary/entity/provenance và consumer dùng được.
A/B/C review các mảng tương ứng; Codex chạy tests, tổng hợp audit và handoff.
Dự toán 6 giờ-người chưa đo; completion là mốc 04.variants.
Dev selection và final query freeze do plan 08 điều phối sau qrels plan 06.

## Requirements

- Thay metadata gold trong fixture không được đổi output query/bundle.
- Giữ source files nguyên; không sửa actual labels để chạy test.
- Mỗi evidence xuất hiện có provenance, mỗi evidence dropped có reason trong phạm vi candidate universe.
- Tests bao gồm token limits/missing modalities/Unicode/tie ordering.
- Handoff không tự tuyên bố R3 hoặc hybrid tốt hơn.
- Test materialization có F1 gate do consumer 08 enforce.

## Architecture

Candidate query manifest → positive/negative/metamorphic suite → A/B/C review → variants receipt.
Test fixtures chứa synthetic short data, không dùng test gold.
Manager can select IDs nhưng renderer function chỉ nhận allowlisted safe records.
Query ledger/data manifests được hash liên kết để phát hiện upstream drift.
05 dùng candidate default để runner smoke, chưa chọn thắng bằng intuition.
06 chấm union candidates từ những variants thực được thử trên dev.
08 chọn representation trên dev, log all trials, khóa config/query/tokenizer tại F1.
08 gọi renderer frozen cho test; không thay rules sau xem test responses.

## Related Code Files

- Proposed/create: [test_representation_contract.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_representation_contract.py).
- Proposed/create: [test_representation_tokens.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_representation_tokens.py).
- Proposed/update: [query-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/query-manifest.json).
- Proposed/create: [representation-review-receipt.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-review-receipt.json).
- Proposed/create: [representation-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-audit.md).
- Proposed/create: [representation-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-handoff.md).
- Existing/read contract: [independent-plans-contracts.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md).
- Proposed/read consumer: [configs/retrieval.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml) — plan 05 owns.

## Implementation Steps

### R04-09 — Metamorphic leakage và entity tests (2h)

- Input → renderers/config/fixtures và candidate outputs.
- Action → Codex thay gold/source-case/family metadata trong fixtures, đảo input rows và kiểm entities; A/B review oracle.
- Output → contract tests + representation-audit có pass/fail và scope.
- Prerequisite → R04-05..08; exact query/data hashes available.
- Acceptance → same telemetry produces same output despite private metadata; IDs/windows/entities preserved.
- Failure path → reject unsafe interface hoặc sửa transform rồi version; không update expected output để hợp thức hóa gold leak.

### R04-10 — Token/provenance và consumer smoke (2h)

- Input → ledgers, all train/dev variants, query/bundle schema.
- Action → Codex check IDs/token budget/records, B kiểm IR content field, C kiểm bundle reuse, A resolve train samples.
- Output → token tests và review receipt gắn manifest/data/config/tokenizer hashes.
- Prerequisite → R04-09 pass; actual tokenizer available.
- Acceptance → every record traceable and within limit; R1/R2 cùng retained IDs/source spans sau clipping, normalization map resolve; same generation bundle across conditions.
- Failure path → mismatch/token overflow dừng receipt; thiếu modality explicit, không silently drop incident.

### R04-11 — Handoff cho pilot/dev selection/F1 (2h)

- Input → validated variants và review receipt.
- Action → Codex viết guide; B/C xác nhận consumer contracts, A review limitation wording.
- Output → representation-handoff.md có API/path/hash, default candidate, test gate và change procedure.
- Prerequisite → R04-09/10 pass; unresolved integrity issues đã xử lý.
- Acceptance → 05 chạy được pilot từ variants; 08 biết dev selection cần 06 qrels và F1 trước test materialization.
- Failure path → chưa có qrels vẫn hoàn tất tooling gate; không báo dev winner hoặc giữ plan 04 chờ test để tạo vòng dependency.

## Interface và receipt bàn giao

| Field | Nội dung |
|---|---|
| milestone | 04.variants, không phải F1 |
| query_manifest_hash | Exact variants và ledgers được review |
| input_manifest_hash | Liên kết safe export plan 02 |
| representation/config versions | R1/R2/R3 và selector/budget rules |
| tokenizer_revision | Đếm tokens và preprocessing actual |
| evidence_loss_report | Upstream unavailable versus local dropped/partial |
| human_review | A provenance, B representation, C common bundle; người thật/status |
| test_materialization | Consumer requires F1; no current test-quality claim |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| RV-01 | Fault/gold đổi, observations giữ | Query/bundle hashes bất biến |
| RV-02 | scenario_family_id gửi vào renderer | Type/schema reject hoặc strip trước function boundary |
| RV-03 | Service ID giống source label text | Chỉ giữ khi có evidence thật, không denylist mù |
| RV-04 | Evidence ID trỏ incident khác | Contract fail |
| RV-05 | Unicode exception + code block | Entities giữ, token count thật và stable |
| RV-06 | Raw ordering/ties đổi | Deterministic query hash |
| RV-07 | Zero usable evidence | Explicit insufficient/missing state, không bịa observations |
| RV-08 | Data manifest đổi sau receipt | Receipt invalid; rebuild variants và downstream pool |
| RV-09 | Chạy test trước F1 qua consumer | Run refused, local synthetic tests vẫn cho phép |
| RV-10 | R1 vượt limit, R2 còn chỗ | Joint budget bỏ cùng evidence/source spans, không âm thầm tăng evidence cho R2 |

## Dev selection và thay đổi sau handoff

- 05 tạo rankings cho default candidate để xây runner/pilot; không coi candidate là dev winner.
- 08 chọn R1/R2/R3 trên 18 dev incidents với reference retriever/corpus chung.
- 06 mở rộng pool/chấm candidates mới từ dev trials trước so điểm; unjudged không grade 0.
- 08 ghi cả negative/no-improvement trials và chọn theo protocol định trước.
- Representation/config thay trước F1 cần new version, manifests và invalidation rankings/pool receipts; query-only rendering không tự hủy relevance labels incident-centered nếu task/window/evidence text/applicability không đổi.
- Pool manager giữ query hashes như provenance; union candidates mới phải chấm. Task/window/evidence text/applicability đổi cần đánh giá lại phạm vi nhãn bị ảnh hưởng.
- Test queries được materialize từ config F1 bằng chính renderer đã kiểm.
- Bug sau F1 theo deviation policy 08; giữ original outputs và không sửa theo test answer.
- Generator observation bundle vẫn chung cho mọi mandatory conditions.

## Success Criteria

- [x] Leakage/entity/provenance/metamorphic tests pass có evidence.
- [x] Token budgets thực và dropped/missing states đầy đủ.
- [x] Receipt gắn exact hashes và reviews thực.
- [x] 05/07/08 nhận interfaces ổn định; không vòng chờ qrels/test.
- [x] Không có tuyên bố winner, quality metric hoặc test freeze chưa thực hiện.

## Risk Assessment

Source selector đã bỏ raw rows; local ledger chỉ chứng minh loss trong safe universe.
Cùng window không bảo đảm equal usefulness; dev ablation mới trả lời hiệu quả.
Valid evidence IDs không chứng minh supported explanation; human evidence/output review thuộc 06/08.
