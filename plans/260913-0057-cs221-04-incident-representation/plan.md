---
title: "04 — Biểu diễn incident và kiểm soát đầu vào"
description: "Tạo ba query variants có evidence lineage, selection/token ledger và giao diện cố định để so sánh trên dev."
status: completed
priority: P1
effort: "20h"
tags: [docs, backend, experimental]
blockedBy: [260913-0057-cs221-02-data-and-environment]
blocks: [260913-0057-cs221-05-retrieval-baselines, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 04 — Biểu diễn incident và kiểm soát đầu vào

## Overview

Kế hoạch độc lập này bàn giao R1/R2/R3, selection ledger, token audit và observation bundle chung. B chịu trách nhiệm representation, A review provenance, C review generator interface; Codex triển khai deterministic tooling. Dự toán 20 giờ-người (4 +10 +6), chưa đo.

**Hoàn tất plan 04 tại mốc variants/tooling/tests**, không đợi chọn biểu diễn thắng. Plan 08 dùng runners 05 và dev qrels 06 để chọn representation, khóa F1 rồi tạo test queries bằng rules đã khóa. Mọi đường dẫn `06_implementation` là proposed.

## Current execution acceptance

The current explicit `/goal ak:codex-goal ak:cook --auto` execution applies to
the local `04.variants` milestone under the
[execution contract](../../06_implementation/reports/representation-goal-contract.md)
and [authorization](../../06_implementation/configs/representation-execution-authorization.json).
The acceptance mapping for every phase and the five plan success criteria is
maintained in [plan04-progress.md](../../06_implementation/reports/plan04-progress.md).
Completed review checkboxes in this execution mean documented independent
automated local review; A/B/C human identities, upstream plan-02 full acceptance
and downstream sharing approval remain pending. The original human assignment
wording below records ownership and is not evidence those people signed.
Plan 07 owns actual generator-tokenizer fit; plan 08 owns dev selection and F1.
These downstream events do not delay the local variants/tooling/tests milestone.

AgentKit's current CLI derives phase execution status from the phase success
checkboxes. Its supported mutations do not rewrite the original phase-table
status cells or phase YAML status fields when checkboxes exist. Read
`ak plan status ./plans/260913-0057-cs221-04-incident-representation` and the
linked progress report for execution progress; the static original cells below
are not the current acceptance record.

## Hiện trạng đã đọc

- [prepare-incidents.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-incidents.py:67) tạo template query từ observations, chưa có R1/R2/R3 runners.
- [logs-evidence.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/logs-evidence.jsonl): 1.770 selected excerpts; không phải toàn 15 triệu raw logs.
- Source selector ưu tiên error patterns, tối đa 4/service và 48/incident, dedup theo text thay số bằng <N>.
- Source query lấy 8 excerpts đầu sau sort service/time, mỗi excerpt tối đa 300 chars; có nguy cơ bỏ service ở cuối.
- Query hiện nêu tên 6 metric có descriptive change score lớn; chưa đưa trace content vào query.
- [profile-summary.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/profile-summary.json): duration/status semantics chưa xác minh; retrospective window.
- [observations.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/observations.jsonl) chứa family/split; runtime chỉ đọc safe export từ plan 02.

## Phạm vi và lựa chọn

| Variant | Nội dung | Điều cố định |
|---|---|---|
| R1 | Selected log text đã redaction, giữ literal gốc | Cùng selected log ledger với R2 |
| R2 | Normalized selected logs giữ service/error/exception/version | Selection, incident và window như R1 |
| R3 | Service/time bundle thêm descriptive metrics và neutral traces | Logs từ ledger chung, modality enrichment có chủ đích |

Query scaffold tiếng Anh cho E5; giữ nguyên technical literal/ngôn ngữ log nguồn, không dịch máy hoặc LLM summary. Không thêm diagnosis/cause từ gold hay đặt injection time vào window. Không gửi toàn raw telemetry.
R1/R2 phải giữ cùng evidence IDs và underlying source spans **sau** clipping: chọn joint budget để cả hai fit tokenizer, R2 dư chỗ không lấy thêm evidence. R3 enrichment là thay đổi có chủ đích và được báo riêng.

## Kiến trúc và giao diện

Safe observations/evidence → fixed selector → shared log ledger → R1/R2/R3 renderers → shared token-budget policy → query manifest. Observation bundle chung đi tới plan 07, không thay theo retriever.

Query record: incident_id, query_id, representation_id/version, query_text/hash, evidence IDs, selected/dropped ledger, tokenizer/config/input manifest hashes. Family/split chỉ ở manager riêng; renderer không nhận metadata ấy.

Các hàm dự kiến: `select_evidence`, `render_representation`, `apply_query_budget`, `build_observation_bundle`. Giai đoạn này tạo train/dev outputs; test materialization do plan 08 gọi cùng functions sau F1.

## Phases

| # | Phase | Giờ-người | Đầu ra | Status |
|---|---|---:|---|---|
| 1 | [Audit selection và specification](./phase-01-start.md) | 4 | Train audit, common selector và variant contract | Pending |
| 2 | [Xây variants và token ledger](./phase-02-build.md) | 10 | Renderers, query/bundle artifacts | Pending |
| 3 | [Kiểm bất biến và handoff](./phase-03-validate-and-handoff.md) | 6 | Metamorphic tests, receipt, dev-selection guide | Pending |

## File inventory đề xuất

- Create: [configs/representation.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/representation.yaml).
- Create: [src/representations.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/representations.py).
- Create: [queries/variants.train-dev.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/variants.train-dev.jsonl).
- Create: [queries/selection-ledger.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/selection-ledger.jsonl), [token-ledger.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/token-ledger.jsonl).
- Create: [queries/observation-bundles.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/observation-bundles.jsonl), [query-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/query-manifest.json).
- Create: [tests/test_representation_contract.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_representation_contract.py).
- Create: [reports/representation-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-audit.md), [representation-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/representation-handoff.md).
- Existing/read only: source observations/selector for audit; inference runner đọc data/inference từ plan 02, không source labels.

## Dependencies và gate

Plan 02 completed là prerequisite triển khai. Plan 04 không đọc qrels để xây variants và không tự chạy test ranking. Plan 05 nhận một default candidate config để pilot, chưa gọi đó là lựa chọn thắng.

Nếu muốn lấy logs ngoài selected evidence đã export, mở yêu cầu versioned cho plan 02; không tự đọc raw/labels xuyên ranh giới. Candidate variants có thể sửa bằng train feedback trước F1, với manifest mới và thông báo pool manager.
Qrels là incident-centered với full observation task/window cố định. Chỉ đổi query rendering làm stale rankings/pool receipts, không tự vô hiệu labels của evidence text không đổi; candidates mới vẫn phải chấm. Task/window/evidence text/applicability thay thì review lại nhãn chịu ảnh hưởng.

## Success Criteria

- [x] R1/R2 cùng selected log ledger; R3 enrichment có evidence IDs và missing markers.
- [x] Mọi variants cùng incident/window; không nhãn, synthetic inference hoặc mất provenance.
- [x] Token audit thật, cắt thống nhất trước các retrievers, evidence bị bỏ có reason.
- [x] Leakage/entity/determinism tests pass; generator bundle chung được C review.
- [x] 05/08 nhận variants và hash/interface đủ để chạy dev selection; chưa tuyên bố biểu diễn thắng.

## Rủi ro

Selection nguồn đã dedup theo số nên downstream không khôi phục được mọi log khác code. Bỏ triệu chứng do clipping phải đo bằng ledger, không suy chất lượng chỉ từ query ngắn. Metric/trace chỉ mô tả quan sát; status nonzero không tự là error và change score không phải causal score.
