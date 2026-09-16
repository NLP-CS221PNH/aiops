---
phase: 1
title: "Rubric, schema và calibration năm ca"
status: in-progress
priority: P1
effort: "12h"
dependencies: []
---

# Phase 1 — Rubric, schema và calibration

## Overview

Chuẩn bị quy trình nhân sự và kiểm rubric trên năm train incidents thuộc 20 pilot core.
Công 12h gồm tooling, review và calibration; ghi actual time để cập nhật hai phases sau.
A quản lý pool; hai người chấm độc lập, người còn lại adjudicate theo assignment.

## Requirements

- Schema có thể soạn sớm; calibration thật chờ corpus/query và 05.runners.
- Chỉ dùng train; không chọn calibration từ test hoặc từ output thuận lợi.
- Reviewer là người thật, có ID và thời điểm review.
- Grade 0/1/2 khác unjudged; relevance không đồng nghĩa root-cause correctness.
- Evidence role, applicability và answerability là các trường riêng.
- Document relevance cần judgment riêng; không lấy max passage grade.
- Span [start,end) dùng Unicode codepoint trên normalized document text.
- Original A/B và adjudication ở các artifact riêng; bảo vệ partial human work.
- Blind forms không lộ method/rank/score; vẫn cho đọc observations và evidence đầy đủ.
- Manager pool không nằm trong inference allowlist hoặc knowledge index.

## Architecture

Rankings → manager union → shuffle có seed → blinded A/B → agreement → adjudication.
Assignment liên kết reviewer, role, incident và round nhưng không lộ retriever.
Rubric version, task/window version và corpus hash đi cùng mọi judgment.
Query hashes là danh sách pool provenance; không tạo grade riêng chỉ vì R1/R2/R3 đổi wording.
Năm calibration được giữ trong core nếu rubric không đổi; chấm lại phần chịu ảnh hưởng khi đổi.
LLM draft nếu có phải ghi provenance và người kiểm; không tự xuất gold.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/README.md` | Rubric nền |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-annotation-kit.py` | Overwrite safeguards |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/qrels-annotator-A.tsv` | Template hiện tại |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/retrieval-preview/candidate-diagnostics.jsonl` | Seed chưa gold |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/rubric-v1.md` | Rubric triển khai |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/assignments.tsv` | Reviewer roles |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/annotations/{build_pool,validate}.py` | Tooling |
| Create — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/calibration/` | Phiếu, timing, receipts |

## Implementation Steps

### 06.01 — Rubric và schema · 3h

Input: rubric cũ và contract chung; Codex soạn, A/B/C review ví dụ biên.
Action: phân biệt topical/direct support, diagnostic check/cause và wrong version/unjudged.
Output: rubric-v1 và schemas passage/document/answerability/reference riêng.
Acceptance: biểu diễn được document grade 2 nhưng chunk grade 0.
Failure: role hoặc grade mơ hồ thì bổ sung ví dụ trước khi chấm hàng loạt.

### 06.02 — Pool, blinding và assignment · 3h

Input: train rankings và source hashes; Codex xây tooling, A review.
Action: union top-10, dedup theo incident+task/window+corpus+chunk, shuffle seed 221, che method/rank/score.
Output: manager pool, A/B forms, assignments và overwrite test.
Acceptance: hai phiếu có cùng pair set; A không xem phiếu B trước khi submit.
Failure: mismatch, stale hash hoặc partial work làm cả batch dừng, giữ nguyên files.

### 06.03 — Calibration năm ca · 4h

Input: năm train IDs được chọn trước, observations, corpus và rubric.
Action: hai người chấm độc lập; ghi phút thực, pair overlap, unknowns và disagreements.
Output: original A/B, time ledger, pre-adjudication agreement và resolution notes.
Codex chỉ hiển thị, kiểm schema và tính agreement; không điền phán quyết thay người.
Acceptance: người chấm đọc span/applicability thật và không xem ranking để chọn grade.
Failure: thiếu second reviewer thì gate chưa đạt dù tooling đã hoàn chỉnh.

### 06.04 — Chốt rubric và công · 2h

Input: calibration receipts; A/B/C review, Codex tổng hợp công.
Action: cập nhật rubric version nếu cần và liệt kê labels phải chấm lại.
Output: calibration report, throughput range và quyết định scope trước dev/test.
Acceptance: năm ca vẫn thuộc 20 train core; rework tăng giờ, không tăng sample size.
Failure: vượt nguồn lực thì ghi tradeoff giảm optional branch trước F1, không hạ chuẩn nhãn.

## Schema tối thiểu

Passage key: incident_id, task_version, window_hash, corpus_hash, chunk_id.
Judgment fields: reviewer_id, grade, reviewed_at; pool sidecar giữ danh sách query_hashes.
Bổ sung rubric_version, evidence_role, supported_claim, applicability, span và review_state.
Document row có document_id/document_grade riêng, không dùng chung cột với passage grade.
Answerability: answerable, partially_answerable, unanswerable hoặc uncertain_pending_review.
Reference: required_claims, evidence_ids, unknowns, next_checks, reviewer và version.
Adjudication giữ A_grade/B_grade/final_grade/adjudicator/rationale; không sửa original.
Candidate ID gồm incident+task/window version+corpus+chunk; text target đổi làm version đổi.
Cùng task và evidence giữ judgments khi query wording đổi; intent/window/chunk đổi cần xét chấm lại.

## Interface dự kiến

```text
python -m src.annotations.build_pool --runs <train_manifests> --depth 10 --seed 221
python -m src.annotations.validate --round annotations/calibration --require-double
```

Commands chạy tại `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation` sau khi tooling được xây.
Import kiểm toàn batch trước ghi; chỉ nhận schema version hợp lệ.
Blank là unjudged; không cast empty string thành 0 hoặc bỏ hàng thiếu grade.
Root-service gold ở private evaluator, không dùng để tự gán qrels.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Blind sheet lộ retriever/rank | Export fail |
| Phiếu có partial span hoặc cột mới | Không overwrite |
| Nhầm byte/codepoint offsets | Validation fail bằng text slice |
| Grade thiếu hoặc ngoài 0/1/2 | Giữ unjudged hoặc reject, không xuất gold |
| Document 2/chunk 0 | Hợp lệ, là hai judgments riêng |
| Hai reviewer cùng ID | Double-review gate fail |
| Wrong snapshot | Reject, chỉ rõ target cần chấm lại |

## Success Criteria

- [x] Rubric, schemas và assignments có version/reviewer.
- [ ] Năm calibration có original A/B và actual time.
- [x] Tool bảo vệ partial work và blinding được kiểm.
- [x] Effort hai phases sau được review bằng throughput thực.

## Risk Assessment

Raw agreement cao do đa số grade 0 cần được đọc cùng grade distribution.
Kappa không chứng minh corpus đủ evidence; thiếu deployment info phải giữ uncertain.
Rubric thay trước dev phải ghi history và scope chấm lại để giải thích rework.
