---
phase: 1
title: "Audit selection và chốt specification ba variants"
status: pending
priority: P1
effort: "4h"
dependencies: []
---

# Phase 1: Audit selection và chốt specification ba variants

## Overview

Đặc tả selection/normalization từ safe export và sáu train incidents.
B sở hữu thiết kế, A kiểm source lineage, C kiểm generator bundle; Codex audit và soạn config.
Dự toán 4 giờ-người chưa đo; không dùng test labels hoặc dev scores để chốt variant thắng.
Sản phẩm là specification triển khai, chưa phải representation đã kiểm benchmark.

## Requirements

- Chỉ đọc data/inference của plan 02 trong runtime.
- Dùng six train incidents phủ nhiều family do manager chọn, renderer không nhận family.
- R1/R2 giữ cùng selected evidence; R3 thay modality mix có chủ đích.
- Không dùng source-case/injection/fault gold để chọn dòng hoặc time window.
- Phân biệt upstream selection loss với representation truncation.
- LLM summary/translation nằm ngoài ba variants chính.

## Architecture

Private manager chọn opaque train IDs → safe evidence resolver → selection audit.
Source selector chỉ là evidence về hiện trạng, không là runtime dependency.
Candidate universe của renderer là safe exported evidence đã có.
Nếu cần rộng hơn, plan 02 tạo additional safe export version sau audit.
Selection ledger ghi included/dropped IDs trong universe ấy, không bịa discarded raw IDs.
Stable order dùng timestamp/service/evidence ID và quotas được ghi config.
R1/R2 dùng log ledger chung trước và sau token clipping; underlying source spans phải bằng nhau, giữ mapping normalization. R3 thêm metric/trace IDs từ cùng incident/window.
Template scaffolding English, literal source không tự dịch hoặc diễn giải.

## Related Code Files

- Existing/read for audit: [prepare-incidents.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-incidents.py:93).
- Existing/read for audit: [observations.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/observations.jsonl).
- Prerequisite/proposed from 02: [input-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/input-manifest.json).
- Prerequisite/proposed from 02: [observations.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/observations.jsonl).
- Proposed/create: [configs/representation.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/representation.yaml).
- Proposed/create: [reports/representation-source-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-source-audit.md).
- Proposed/create: [queries/representation-schema.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/representation-schema.json).
- Proposed/create: [reports/representation-decisions.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-decisions.md).

## Implementation Steps

### R04-01 — Audit sáu train incidents (1h)

- Input → plan 02 manifest và six opaque IDs do A chọn theo split admin.
- Action → Codex đối chiếu selected evidence IDs/window; A review provenance, B ghi modality/selection limits.
- Output → source audit không chứa gold, có counts và source selection restrictions.
- Prerequisite → full plan 02 pass; manager xác nhận IDs thuộc train.
- Acceptance → mọi evidence đúng incident/window; retrospective policy/unknown units được giữ.
- Failure path → resolve fail trả plan 02; không đọc case path hay injection để sửa query.

### R04-02 — Selection policy và loss ledger (1h)

- Input → safe exported log candidates và source query đầu 8 logs.
- Action → Codex thống kê service coverage/duplicate patterns, B chọn deterministic selection rule, A review sample.
- Output → config quotas/order/ties và ledger schema.
- Prerequisite → R04-01; safe candidate universe cố định.
- Acceptance → first-8 bias được ghi; R1/R2 cùng evidence IDs; upstream unavailable được ghi unknown.
- Failure path → thiếu symptom vì source selection thì đề xuất export mới cho 02, không tự bypass raw boundary.

### R04-03 — Normalization và modality contract (1h)

- Input → selected logs, metrics/traces và data unit policy.
- Action → B/C chốt R1/R2/R3 structure, Codex mô tả entity-preserving normalization; A review meanings.
- Output → representations schema và examples bằng train/fixture.
- Prerequisite → R04-02; aliases/time policy từ 02.
- Acceptance → service/error/exception/version/port không bị blanket numeric replacement; R3 giữ neutral status/duration.
- Failure path → rule có thể đổi meaning giữ literal gốc/unknown thay vì summary suy diễn.

### R04-04 — Token và downstream interface (1h)

- Input → candidate tokenizer revision, shared contracts và variant schema.
- Action → Codex đặc tả token budget/order/fallback, B review IR fairness, C review common observation bundle.
- Output → representation.yaml/token ledger spec và handoff boundary tới 05/07/08.
- Prerequisite → R04-03; model card/config đủ biết encoder budget.
- Acceptance → prefix/special tokens được tính; joint R1/R2 budget giữ cùng IDs/source spans sau cắt, R2 dư chỗ không thêm evidence; common cắt trước retrievers; dev selection/F1 thuộc 08.
- Failure path → tokenizer unavailable giữ verification pending; không lấy chars/4 làm kết quả thật.

## Interface và schema dự kiến

| Thành phần | Fields/quy tắc |
|---|---|
| Selector input | incident_id, observation window, evidence objects allowlisted |
| Selector output | selected_log_ids, dropped_log_ids, reasons, universe_hash |
| Query record | incident_id, query_id, representation_id/version, query_text/hash |
| Provenance | input_manifest_hash, evidence_ids, config/redaction/transform versions |
| Token ledger | tokenizer revision, before/after tokens, prefix budget, common retained/dropped IDs, source spans và normalization map |
| Observation bundle | Same per incident for all generation conditions, separate context budget |
| Synthetic flags | query_is_synthetic=true, source telemetry không đổi thành synthetic |
| Manager metadata | family/split outside renderer and query text |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| RC-01 | Service alphabetically cuối | Ledger cho biết có được chọn, không silent loss |
| RC-02 | HTTP 500 và 503 gần giống | Không normalize cả hai thành <N>; source dedup loss được ghi |
| RC-03 | Logs không match error pattern | Fallback rõ và trung thực, không bịa error |
| RC-04 | Trace status nonzero | Giữ numeric status+unknown semantics |
| RC-05 | All-null metric | Missing marker, không invent anomaly |
| RC-06 | Window dùng injection onset | Contract reject; dùng exported retrospective window |
| RC-07 | Raw candidate không có safe export | Yêu cầu 02 versioned export, không đọc trực tiếp |

## Bàn giao cho phase 2

Config mô tả từng transformation, selection rule và artifact consumer.
A cung cấp source audit/alias evidence, B sở hữu normalization, C sở hữu bundle review.
Test fixtures có thể tạo khi chờ tokenizer; token acceptance vẫn pending đến khi đo.
Không cần qrels để viết variants hoặc tests.

## Success Criteria

- [x] Source selection limits và six-train audit được ghi.
- [x] R1/R2 selection chung; R3 enrichment có contract riêng.
- [x] Entity/time/unknown policies cụ thể, không dùng gold.
- [x] Token/interface spec đủ viết renderer deterministic.
- [x] Dev selection/F1 responsibility không nằm trong phase này.

## Risk Assessment

Raw text đã redaction không đồng nghĩa raw telemetry chưa xử lý; đặt tên variant/README rõ.
Query scaffold tiếng Anh không làm literal log tiếng khác biến thành English evidence.
Tối ưu selector/normalizer quá nhiều trên vài cases có thể overfit; giới hạn config ban đầu và ghi decisions.
