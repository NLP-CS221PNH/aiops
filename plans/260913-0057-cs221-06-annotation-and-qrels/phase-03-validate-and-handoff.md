---
phase: 3
title: "Chấm đôi test sau F1 và khóa F2"
status: in-progress
priority: P1
effort: "24–42h"
dependencies: [2]
---

# Phase 3 — Chấm đôi test sau F1 và khóa F2

## Overview

Chấm 18 test incidents thuộc 6 families sau 08.F1; 08 tạo test pool bằng runner 05.
Hai người chấm độc lập, người thứ ba adjudicate; Codex kiểm và export, không phán quyết.
Công 24–42h; 06.dev đã bàn giao nên 08 không phải chờ hoàn tất toàn plan 06.

## Requirements

- Có F1 hợp lệ, test-pool receipt liên kết F1 và rubric/version đã khóa.
- Không tạo test pool trước F1 chỉ để tiết kiệm thời gian.
- Không đổi query/corpus/model/prompt dựa trên feedback test.
- Test labels chỉ manager/người được phân công/evaluator đọc; runner không mount qrels.
- Mọi required test passage pairs chấm đôi, đủ top-5/top-10 coverage trước F2.
- Human discovery/deepening theo quy tắc trước scoring và có provenance.
- Giữ original A/B, agreement trước adjudication, references và answerability.
- 18 test = 6 families × 3 repetitions; không tăng n bằng claims hoặc judgments.
- Thiếu document judgments thì secondary metric unavailable.
- 08 chạy final generation/scoring sau F2; nhãn không đi vào generation runtime.

## Architecture

08.F1 → frozen test pool → human A/B → agreement → adjudication → 06.F2.
F2 liên kết F1 hash, pool hash, rubric, qrels versions và judged coverage.
08 kiểm chain trước scoring, không chỉ đọc cờ passed trong validation cũ.
Test annotations không trở thành knowledge và không copy vào inference workspace.
Đổi content/candidates sau F1 phải tuân deviation policy của 08.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Input — owner 08 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F1.json` | Khóa hệ thống |
| Input — owner 08 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/test/test-input-manifest.json` | Actual test query/bundle hashes sau F1 |
| Input — owner 08 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/test/` | Frozen rankings |
| Input — owner 08/06 tooling | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/pools/test/` | Pool/provenance |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/blinded/test/` | Original A/B |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/qrels/test/` | Passage/document qrels |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/test-reference-answers.jsonl` | Human references |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/test-answerability.tsv` | Human answerability |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F2.json` | Qrels freeze |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_annotation_integrity.py` | Gate/export tests |

## Implementation Steps

### 06.09 — Nhận pool và kiểm F1 · 3–4h

Input: F1, frozen rankings, corpus registry; Codex validate, A kiểm receipt.
Action: recompute hashes, kiểm conditions/18 IDs, xuất blind forms và assignments.
Output: test manager receipt, reviewer assignment và form hashes.
Acceptance: pool sau F1, candidates đúng snapshot, method/rank/score được ẩn.
Failure: stale F1 hoặc config mismatch gửi 08 xử lý chain; không tune từ nhãn test.

### 06.10 — Chấm đôi test · 14–26h

Input: test forms, observations, corpus và rubric khóa.
Action: human A/B chấm độc lập grade/span/applicability, ghi human additions có provenance.
Output: original judgments, time ledger, answerability/reference được review.
Codex chỉ hỗ trợ schema/viewer; không gửi feedback test để chỉnh model/prompt.
Acceptance: giữ đủ 18 ca; mọi required pair có hai reviewer khác nhau.
Failure: thiếu người/grade/span thì gate chưa đạt, không default 0 hoặc giảm test set.

### 06.11 — Agreement và adjudication · 4–6h

Input: A/B đã submit; Codex tính agreement, người thứ ba phân xử bằng evidence.
Action: giữ raw grades/distributions, final rationale, applicability và references.
Output: qrels draft, answerability/reference final và agreement report.
Acceptance: ca không relevant evidence vẫn ở dataset, không bị xóa để tăng metric.
Failure: uncertainty giữ đúng trạng thái, không gán compatible/cause để đóng gate.

### 06.12 — Coverage và F2 · 3–6h

Input: adjudication, qrels và mọi frozen runs; Codex kiểm, A xác nhận nhãn, B review chain.
Action: kiểm final top-5/top-10 đã judged; hoàn tất deepening và version nếu cần.
Output: F2 JSON, human-label receipt, pair/incident counts và limitations.
Acceptance: F2 khớp F1/pool/qrels hiện tại, không còn required judgments chưa adjudicate.
Failure: cần thay hệ thống thì chuyển 08 deviation, giữ original test/version.

## F2 schema và interface

F2 có schema_version, created_at_utc, F1_hash, pool_hash, qrels_hash và rubric_version.
F2 giữ test_input_manifest_hash; kiểm manifest này liên kết F1 và actual query/bundle hashes đúng với pool.
Thêm annotation_version, task/window versions, incident_ids, reviewerreceipt_hash và coverage.
Pool sidecar giữ query hashes; qrels key theo incident/task/window/corpus/target, không theo wording.
Passage/document availability ghi riêng; references và answerability cũng có hashes.
Không mount các nhãn này cho final generation, dù evaluator được quyền đọc.
Coverage dùng actual hits; empty ranking có trạng thái riêng.
F2 không chứng minh exhaustive relevance hoặc causal-path gold.

```text
python -m src.annotations.validate --split test --require-double --freeze freezes/F1.json
python -m src.annotations.coverage --runs <frozen_runs> --qrels <test_qrels> --required-k 5,10
python -m src.annotations.export_gold --split test --freeze freezes/F1.json --out freezes/F2.json
```

Commands dự kiến trong `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation`, chỉ chạy khi có nhãn người.
Export preflight toàn batch trước ghi; không overwrite original A/B hoặc F2 khác version.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Test pool thiếu F1 | Reject |
| Corpus/query hash khác F1 | Reject; 08 xử lý |
| Top-5 unjudged | F2 primary gate fail |
| Top-10 unjudged | Chặn MRR, hoàn tất annotation trước scoring |
| Qrels không có relevant | Trạng thái hợp lệ; 08 ghi metric undefined |
| A/B cùng người | Double-annotation gate fail |
| F2 đã có, nội dung khác | Version mới theo change protocol |
| Document labels thiếu | Secondary unavailable, không auto-derive |

## Success Criteria

- [ ] 18 test/6 families có passage qrels chấm đôi sau F1.
- [ ] Originals, agreement, adjudication và references có provenance.
- [x] F2 hash chain đúng và đủ coverage của mọi final required top-k.
- [x] Không tune từ test, không bịa nhãn hoặc giảm denominator.
- [x] 08 nhận handoff để chạy generation/scoring riêng biệt.

## Risk Assessment

Thiếu nhân sự làm F2 pending; Codex vẫn bàn giao tooling và missing-pair list.
Coverage thấp giới hạn claim, không cho phép đổi corpus sau F1 âm thầm.
Nếu đã xem test rồi sửa hệ thống, 08 phải công bố deviation và mất tính unseen.
