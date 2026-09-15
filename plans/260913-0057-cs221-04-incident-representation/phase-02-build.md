---
phase: 2
title: "Xây renderers, observation bundle và token ledger"
status: pending
priority: P1
effort: "10h"
dependencies: [1]
---

# Phase 2: Xây renderers, observation bundle và token ledger

## Overview

Hiện thực ba variants deterministic cùng input provenance và audit truncation.
Codex viết tooling; B review IR contract, A kiểm semantic preservation, C review generation bundle.
Dự toán 10 giờ-người chưa đo; outputs train/dev đủ cho pilot và dev trials downstream.
Không tạo test queries để tuning hoặc chạy retrieval/generator trong plan này.

## Requirements

- Runtime không mount/read labels hoặc private manager fields.
- Rendered text chỉ dùng observations, approved alias và literal technical terms.
- Determinism gồm candidate ordering, tie breaks, normalization và clipping.
- Truncation trước mọi retrievers có cùng policy; không cho BM25 thấy full text còn dense bị cắt ngầm.
- Tokenizer prefix/special tokens phải được tính trong encoder limit.
- Query và generator observation bundle có budgets khác, ghi rõ.
- No-RAG/RAG cùng observation bundle; knowledge context được plan 07 thêm riêng.

## Architecture

`select_evidence` → `render_representation` → `apply_query_budget` → query record.
Renderer functions nhận typed safe records, không toàn source table.
R1 giữ redacted literals; R2 chuẩn hóa whitespace/timestamps theo rules giữ entities.
R3 group service/time, thêm metric descriptive summaries/trace facts không cause inference.
Budget cắt theo block/evidence priority đã khóa, không random cut giữa identity/citation.
apply_query_budget nhận nhóm R1/R2 cùng source-span ledger, chọn retained IDs/spans để cả hai fit tokenizer; R2 freed budget không lấy thêm evidence. R3 dùng budget riêng với enrichment được ghi rõ.
Partial literal khi bất khả kháng phải đánh dấu truncated; R1/R2 giữ cùng source slice, normalization map nối source slice tới normalized output.
`build_observation_bundle` độc lập retrieval representation để giữ generation fairness.
Manifest content hashes dùng stable serialization, created_at receipt tách khỏi digest.

## Related Code Files

- Prerequisite/proposed from 02: [data/inference](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference) — nguồn safe records.
- Proposed/create: [src/representations.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/representations.py).
- Proposed/update: [configs/representation.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/representation.yaml).
- Proposed/create: [queries/variants.train-dev.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/variants.train-dev.jsonl).
- Proposed/create: [queries/selection-ledger.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/selection-ledger.jsonl).
- Proposed/create: [queries/token-ledger.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/token-ledger.jsonl).
- Proposed/create: [queries/observation-bundles.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/observation-bundles.jsonl).
- Proposed/create: [queries/query-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/query-manifest.json).
- Proposed/create: [reports/representation-token-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-token-audit.md).

## Implementation Steps

### R04-05 — Selector và R1/R2 renderer (3h)

- Input → safe records và phase 1 config.
- Action → Codex triển khai select_evidence/render_representation, B review stable order, A kiểm literals ở mẫu train.
- Output → R1/R2 strings và shared selection ledger.
- Prerequisite → R04-01..04 specs hoàn chỉnh; plan 02 manifest hash pass.
- Acceptance → R1/R2 cùng selected IDs/window; HTTP codes/exceptions/services/versions giữ; no source-case/family.
- Failure path → normalizer làm mất entity thì revert rule/version, thêm focused fixture; không chỉnh source logs.

### R04-06 — R3 và common observation bundle (3h)

- Input → selected logs, metrics/traces cùng incident/window và unknown policies.
- Action → Codex render R3 theo service/time, build_observation_bundle; A review data semantics, C kiểm generation reuse.
- Output → R3 queries và observation-bundles.jsonl có evidence links/missing markers.
- Prerequisite → R04-05 ledger stable; data aliases/units đã review.
- Acceptance → trace status neutral, metric change descriptive; bundle same hash qua G0/GB/GD/GH placeholders.
- Failure path → missing modality giữ missing_information; unit unknown không convert hoặc diễn giải error tự động.

### R04-07 — Token budget và clipping ledger (2h)

- Input → rendered variants và encoder tokenizer revision.
- Action → Codex count actual tokens/apply_query_budget theo joint R1/R2 selection, B review prefix/specials và cắt chung retrievers.
- Output → token-ledger.jsonl với before/after counts, evidence dropped/partial, tokenizer hash.
- Prerequisite → R04-05/06; tokenizer tải/cài khi triển khai với revision đã chọn.
- Acceptance → cả R1/R2 fit limit với cùng retained IDs/underlying source spans sau budget, R2 dư chỗ để trống; repeat identical; no hidden dense-only truncation.
- Failure path → không fit ngay cả một evidence block thì emit explicit insufficient/truncated query state; không bịa evidence.

### R04-08 — Materialize train/dev và manifest (2h)

- Input → allowlisted train/dev IDs từ manager, frozen candidate config và data manifest.
- Action → Codex render variants/bundles, B kiểm counts, C kiểm consumer schema; manager giữ split riêng.
- Output → variants.train-dev.jsonl, ledgers, query-manifest có condition/version/input hashes.
- Prerequisite → R04-05..07 pass; IDs train/dev được manager xác nhận.
- Acceptance → nếu materialize toàn train/dev: 72 incidents ×3 =216 variant records; no test IDs, no split fields trong payload.
- Failure path → invalid incident có explicit error record/count, gate fail đến khi xử lý; không silent drop để đúng 216.

## Interface và schema dự kiến

| Artifact | Fields cốt lõi | Consumer |
|---|---|---|
| Query | query_id, incident_id, representation_id/version, query_text, query_hash | Plan 05/08 |
| Selection ledger | universe_hash, selected IDs, dropped IDs/reasons, ordering version | Audit và diagnosis selection loss |
| Token ledger | tokenizer_revision, limit, actual tokens, dropped/partial evidence IDs | IR preflight |
| Bundle | incident_id, observations, evidence_ids, window, bundle_hash | Plan 07 |
| Query manifest | input/config/tokenizer hashes, variant versions, counts/errors | All runners |
| Error state | incident_id, variant, rule, status, retryability | Runner/error reporting |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| RB-01 | Input rows đảo thứ tự | Same selected IDs và query hashes |
| RB-02 | Service-hyphen, v1.2.3, HTTP 503 | Entities giữ nguyên theo policy |
| RB-03 | Query đúng/gần token limit | Prefix/specials tính đủ, không overflow ngầm |
| RB-04 | One long log chiếm budget | Drop/partial marker + ledger, không mất evidence ID |
| RB-05 | R3 thiếu traces | Missing marker, không suy service path |
| RB-06 | Invalid unknown status | Neutral raw field hoặc validation error, không đổi thành exception |
| RB-07 | G0/GB/GD/GH scaffold | Same observation bundle_hash |
| RB-08 | New config cùng output filename | Manifest version/hash phát hiện stale outputs |
| RB-09 | R1 vượt limit nhưng R2 vừa | Joint clipping giữ cùng retained IDs/source spans; R2 không dùng chỗ dư lấy thêm evidence |

## Bàn giao cho phase 3

B nhận generated train/dev variants và token/selection ledgers.
A/C review sample payload trước mọi external use; local fixtures không cần API permission.
Phase 3 chạy metamorphic tests và consumer schema smoke.
Chưa có dev winner hoặc inference quality score trong report.

## Success Criteria

- [x] Renderers tạo R1/R2/R3 deterministic từ safe evidence.
- [x] Common log selection và common generation bundle được kiểm.
- [x] Actual token counts/clipping ledger đầy đủ.
- [x] Train/dev manifest counts/errors trung thực, test chưa materialize.
- [x] Downstream schema/hash fields khớp shared contracts.

## Risk Assessment

Normalize số quá mạnh có thể phá mã lỗi; ưu tiên preserve entities trước giảm length.
Text bị cut giữa evidence có thể gây claim mất context; ledger và truncation marker phải tới reviewer.
Tokenizer reranker có pair limit riêng plan 05 kiểm; common query policy không đảm bảo mọi future reranker fit.
