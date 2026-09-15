---
phase: 2
title: "Frozen test pool, F2, final generation và scoring"
status: pending
priority: P1
effort: "12h"
dependencies: [1]
---

# Phase 2 — Frozen test execution và scoring

## Overview

Điều phối test theo thứ tự F1 → pooling → 06.F2 → generation và scoring.
B/Codex giữ run registry, A kiểm qrels chain, C chạy generation bằng adapter 07.
12h công điều phối/kiểm/scoring; không gồm giờ human qrels của 06 hoặc thời gian máy chờ API.

## Requirements

- F1 hợp lệ trước mọi test retrieval/pooling; configs không đổi theo test.
- Runner 05 nhận incident allowlist và F1, không mount qrels/private gold.
- Tooling 06 tạo manager/blinded pool; 06 sở hữu judgments và F2.
- Final generation chỉ chạy sau F2, nhưng runtime không được đọc labels/references.
- Cùng common observation bundle do 04 xuất, generator, prompt, decoding và context allowance cho G0/GB/GD/GH.
- GR chỉ tồn tại nếu IR-R đã được chọn tại F1; không thêm condition sau xem test.
- G0 vẫn đọc observation evidence và có thể dẫn observation IDs.
- Cache outputs bất biến theo run_id; ghi mọi failures/retries thay vì bỏ incidents.
- Retry theo lỗi kỹ thuật đã khóa, không chọn response dựa correctness.
- API mutable dùng model/cohort receipts; thay model cần deviation và rerun đối chứng liên quan.

## Architecture

Controller verify F1 → materialize test inputs bằng frozen renderer 04 → retrieve → pool → gate 06.F2.
Controller verify F1/F2 chain → run generation bằng inference-only mount → raw/parsed records.
Evaluator mới join qrels/private gold để tính metrics.
Missing required labels chặn scoring; synthetic validation vẫn chạy độc lập.
Giữ test original outputs khi có technical deviation; run sửa có version và limitation riêng.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Input — owner 04 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/representations.py` | Frozen render/budget/bundle functions |
| Create — sau F1 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/test/{queries,observation-bundles}.jsonl` | Test inputs riêng, không sửa train/dev |
| Create — sau F1 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/test/test-input-manifest.json` | Actual test hashes liên kết F1 |
| Input — sau phase 1 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F1.json` | Frozen config |
| Input — owner 06 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F2.json` | Frozen qrels |
| Read — owner 05 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/` | Runner tái sử dụng |
| Read — owner 07 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/` | Adapter tái sử dụng |
| Read — evaluator only | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/` | Split/family/gold join |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/test/` | Frozen rankings |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/generation/test/` | Raw/parsed outputs |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/per-incident.tsv` | Metrics/status mỗi incident |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/freeze-chain-audit.json` | F1/F2 validation |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/test-deviations.md` | Change/failure ledger |

## Implementation Steps

### 08.04 — Frozen retrieval và test pool · 3h

Input: F1, 18 opaque test IDs, approved inference export/corpus và renderer 04; B/Codex điều phối.
Action: sau verify F1, gọi select_evidence/render_representation/apply_query_budget/build_observation_bundle đã khóa.
Ghi test inputs riêng và test-input-manifest liên kết F1/config/code/tokenizer/schema cùng actual hashes trước retrieval.
Sau đó chạy IR-B/D/H (+IR-R nếu khóa) bằng runner 05; tool 06 union top-10 và blinding.
Output: frozen rankings, pool receipt liên kết F1 và handoff 08.test-pool cho 06.
A kiểm IDs/versions, đảm bảo thông tin method/rank/score chỉ manager thấy.
Acceptance: mọi actual top-5/top-10 có trong pool, không cap làm rơi final hits.
Failure: missing/short/empty runs ghi status; hash drift dừng trước khi annotation bắt đầu.

### 08.05 — Chờ F2 và final generation · 4h

Input: F2 từ 06, F1, test-input-manifest, frozen retrieval outputs và adapter 07.
Action: recompute hash chain, kiểm required judged coverage rồi chạy G0/GB/GD/GH (+GR).
Output: 72 hoặc 90 generation records, raw/parsed payload, context IDs/hash, attempts và usage.
C owner provider; runner resolve test bundle qua test-input-manifest, chỉ mount inference/knowledge/config.
Acceptance: một final record cho mỗi incident×condition, kể cả failed/invalid/abstained.
Failure: F2 thiếu thì giữ final run pending; model drift/rate limit theo retry/deviation policy.

### 08.06 — Scoring và audit denominator · 5h

Input: F1/F2, runs, private join và evaluator đã kiểm.
Action: score retrieval/service metrics theo incident, joined counts/status, coverage và pooled diagnostics.
Output: per-incident metrics, validation audit, pairwise comparison inputs cho phase 3.
B review công thức/counts; A kiểm gold joins, C kiểm invalid responses/citation ID status.
Acceptance: cùng incident registry cho mọi condition; undefined có reason; failed không bị bỏ.
Failure: thiếu required qrels/config mismatch chặn metric tương ứng và ghi remediation cụ thể.

## Frozen interfaces dự kiến

```text
python -m src.retrieval run --mode frozen --freeze freezes/F1.json --input-manifest queries/test/test-input-manifest.json --purpose annotation-pool --incident-list <test_ids>
python -m src.evaluation verify-freezes --system freezes/F1.json --qrels freezes/F2.json
python -m src.generation run --freeze freezes/F1.json --input-manifest queries/test/test-input-manifest.json --incident-list <test_ids> --run-id generation/test/<cohort>
python -m src.evaluation score --system freezes/F1.json --qrels freezes/F2.json --runs <final_runs>
```

F2 là prerequisite của controller; generation command không nhận qrels path.
F2 chain kiểm thêm test_input_manifest_hash; manifest test không chứa labels hoặc references.
Run ID generation/test/<cohort> ánh xạ runs/generation/test/<cohort>/; mỗi cohort ghi riêng, không dùng chung file.
Commands được hiện thực trong package chủ sở hữu; module evaluation không viết lại retriever/provider.
Test scoring không dùng script validate-research-pack.py vì script cũ đòi 0 judgments/NOT_RUN.
Final response schema phải lưu actual context IDs để kiểm citation, không chỉ full corpus registry.

## Result schema và mẫu số

Metric row: metric, condition, incident_id, split, run_id, qrels_version, eligible, value, undefined_reason.
Thêm status/failure counts, corpus/config hashes và scenario_family_id chỉ trong results evaluator.
Service top-1/top-3 dùng denominator 18; no prediction do invalid/failed/abstained tính incorrect.
Conditional accuracy báo denominator số có trả lời; coverage=0 thì selective risk undefined.
Citation ID tồn tại nhưng không trong actual context bị invalid; support cần human review phase 3.
Recall20/50 là pooled diagnostic, kèm judged@k và số relevant đã chấm.
Primary pairs dùng cùng eligibility qrels theo task/window; không loại ca theo condition thắng/thua.
Macro-average và mean paired delta dùng đúng cùng tập eligible incidents; báo cả incident/family counts.
Family không có eligible IR incident giữ undefined; service metrics vẫn dùng toàn 18 incidents.
Trước generation kiểm bundle_hash khớp test-input-manifest và manifest liên kết đúng F1; không thay theo condition.
Không append test vào train/dev observation-bundles.jsonl đã được F1 hash.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Materialize/pooling trước F1 | Controller reject |
| Test manifest thiếu hoặc actual hash lệch | Không retrieval/generation, không sửa F1 cho khớp |
| F2 thiếu hoặc link F1 sai | Không generation/scoring final |
| Labels mount trong runner | Boundary gate fail |
| Một condition thiếu incident | Record failure, không silently drop denominator |
| Top-5 chưa judged | Primary scoring blocked |
| Có relevant nhưng empty ranking | Retrieval score 0 |
| Không relevant qrels | Retrieval undefined, service vẫn đủ 18 |
| API cohort đổi giữa batch | Deviation và rerun conditions liên quan |
| Cached run khác prompt/hash | Reject cache reuse |

## Success Criteria

- [ ] 08.test-pool sau F1, 06.F2 có chain/coverage hợp lệ.
- [ ] Final generation sau F2 và runtime không đọc nhãn.
- [ ] 72/90 records đầy đủ statuses, retries, context và usage.
- [ ] Metrics có counts/denominators/undefined reasons, không bias do missing rows.
- [ ] Raw outputs và deviations giữ để phase 3/10 kiểm lại.

## Risk Assessment

API failures không làm test set nhỏ đi; báo primary accuracy và failure rate song song.
Bug sau F1 giữ bản gốc, rerun đủ affected conditions; không sửa riêng nhánh đang thua.
Mọi test feedback đã xem khiến run thay đổi không còn hoàn toàn unseen, phải công bố.
