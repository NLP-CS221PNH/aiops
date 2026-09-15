---
phase: 3
title: "Human output review, thống kê và bàn giao"
status: pending
priority: P1
effort: "18h"
dependencies: [2]
---

# Phase 3 — Human output review và analysis

## Overview

Chấm chất lượng output thật, phân tích theo sáu families và bàn giao kết quả có provenance.
C điều phối human review, A/B/C chia người chấm/adjudicate; B/Codex tính thống kê.
18h gồm review 12h, family analysis 3h, error/resource analysis 2h, handoff 1h.

## Requirements

- Có final runs và F1/F2 chain đúng; outputs có status kể cả failed/invalid.
- Review một lượt toàn bộ 72/90 responses, lượt thứ hai thêm 24/30 responses.
- Double-review subset là sáu incidents đã chọn tại F1, một mỗi family, đủ mọi conditions.
- Che tên system/condition; reviewer đọc actual observations/context, không được đoán support từ đúng service.
- Chấm riêng task correctness, citation validity, evidence support, unknowns và abstention.
- Agreement chỉ báo trên subset thật sự chấm đôi, trước adjudication.
- Không coi claims, log rows hoặc retries là mẫu thống kê độc lập.
- 18 incidents có sáu family clusters; uncertainty phải được công bố.
- Document secondary giữ unavailable nếu thiếu document judgments.
- Kết quả âm hoặc hybrid không thắng vẫn là output nghiên cứu hợp lệ.

## Architecture

Final outputs → blind response IDs → human claims/citations review → adjudication.
Primary: mean điểm và paired deltas trên cùng tập eligible incidents cho mọi conditions.
Family means/deltas là diagnostics; giữ đủ sáu rows và undefined nếu family không có eligible IR incident.
Result tables → error cases có provenance → 08.results cho demo/report.
Citation existence do tooling kiểm; semantic support/applicability do người phán quyết.
Không dùng LLM judge thay human subset để giảm công mà vẫn báo chấm đôi.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/claim-evaluation.tsv` | Blank template tham khảo |
| Input — sau phase 2 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/per-incident.tsv` | Scores/status đầu vào |
| Input — sau phase 2 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/generation/test/` | Raw/parsed actual outputs |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/response-judgments.tsv` | Human review |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/response-review-manifest.json` | Subset/blinding/reviewers |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/family-comparison.tsv` | Sáu family deltas |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/evaluation/analysis.py` | Aggregation/sensitivity |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/error-analysis.md` | Case analysis |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/evaluation-handoff.json` | 08.results receipt |

## Implementation Steps

### 08.07 — Human output review · 12h

Input: 72/90 outputs, actual contexts, F1 subset và frozen rubric; C quản lý, người chấm thực hiện.
Action: blind IDs; một lượt toàn bộ, thêm lượt hai cho 24/30 outputs; adjudicate disagreements.
Output: human judgments, raw agreement trên subset, claim/support/abstention summary.
Codex tạo forms/ID checks/aggregation; không gán semantic support thay reviewer.
Acceptance: 96/120 total review lượt, đúng subset; count/status/empty responses được báo.
Failure: chưa đủ human review giữ gate pending; đo lại tốc độ nếu vượt 5 phút/lượt dự toán.

### 08.08 — Phân tích paired theo family · 3h

Input: per-incident results và private family mapping; Codex tính, B review.
Action: tính primary macro/paired delta trên eligible incidents, bảng family diagnostics và leave-one-family-out.
Output: family-comparison.tsv, sensitivity table và optional exploratory cluster bootstrap.
Acceptance: resample/drop family giữ mọi repetitions/conditions, tính lại cùng primary statistic trên eligible incidents.
Failure: code resample từng claim/row/incident rời family thì reject và sửa trước báo cáo.

### 08.09 — Error cases và tài nguyên · 2h

Input: metrics, human labels, attempts/usage/timings; B/C cùng Codex phân tích.
Action: chọn 6–10 thành công/thất bại theo taxonomy đã ghi; truy input/config/evidence.
Output: error-analysis, resource summary và limitations có counts.
Acceptance: có wrong-version, unsupported cause, upstream/downstream, missing evidence hoặc abstain cases khi xảy ra.
Failure: không đủ loại lỗi thực thì báo absent, không dựng ví dụ giả hoặc chỉ chọn ca đẹp.

### 08.10 — Handoff 08.results · 1h

Input: results/analysis/review receipts; Codex lập registry, A/B/C kiểm claim–evidence.
Action: kiểm mọi số có run/config/qrels provenance, reviewers và denominator.
Output: evaluation-handoff.json cho 09/10, limitations/deviations và reproduction commands.
Bàn giao cho 10 dữ liệu và command replay bắt buộc của core metrics từ frozen outputs, không gọi API mới.
Acceptance: demo/report dùng đúng frozen results, không lấy pilot số đẹp thay test.
Failure: thiếu provenance hoặc nhãn quan trọng giữ claim chưa đủ evidence, không làm tròn để che mismatch.

## Human review schema và chỉ số

Record: response_id, incident_id, blinded_condition_id, reviewer_id, claim_id, claim_text.
Bổ sung citation_ids, actual_context_hash, support_label, applicability, task_correctness, reviewed_at.
Support label: supported/contradicted/insufficient_evidence; citation validity là trường riêng.
Claim đúng service nhưng source không support vẫn có support_label không được hỗ trợ.
Support precision dùng claims cần evidence làm denominator; coverage dùng required/reference claims theo rubric.
Abstain/empty responses báo rõ; không dùng mẫu số rỗng để gán precision hoặc selective accuracy bằng 1.
Tooling ghi exact counts bên cạnh percentages và lý do undefined.
96/120 lượt × 5 phút ≈ 8–10h, thêm calibration/adjudication trong budget 12h; đo lại pilot.

## Thống kê và commands dự kiến

Primary contrast khóa tại F1, không đổi đối thủ vì test score khác dev.
Family table có n_incidents, eligible_count, condition scores và paired delta; zero eligible → undefined.
Báo tổng eligible incidents/families; service metrics vẫn dùng đủ 18, không theo IR eligibility.
Leave-one-family-out bỏ từng family rồi tính lại mean incident deltas, không mean family means.
Bootstrap resample family, giữ pairing/repetitions, tính lại primary macro trên sampled eligible incidents.
Sample không còn eligible incidents → undefined, báo số lần này; ít hơn hai eligible families không báo CI.
Bootstrap seed/resamples do F1 định nghĩa; CI ghi exploratory vì chỉ sáu clusters.
Các repeated API attempts không làm tăng n khoa học.

```text
python -m src.evaluation review-import --judgments annotations/response-judgments.tsv
python -m src.evaluation analyze --results results/per-incident.tsv --group scenario_family_id
python -m src.evaluation validate-handoff --manifest reports/evaluation-handoff.json
```

Commands dự kiến; analysis package chỉ đọc frozen results và private evaluator mapping.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Service đúng, citation không support | Accuracy/support khác nhau được giữ |
| Citation ID chỉ có trong corpus, không actual context | Invalid citation |
| Abstain tất cả | Coverage 0, primary accuracy 0, selective risk undefined |
| Double-review subset khác F1 | Review manifest fail |
| Sáu families, ba repetitions | Family resampling giữ cả group và paired conditions |
| Một family có zero eligible; counts các family khác không đều | Family undefined; primary/LOFO/bootstrap vẫn dùng macro incidents |
| Missing/failed outputs | Giữ đủ 18 denominator, báo status riêng |
| Model/rubric changed outputs | Separate cohort/deviation, không silent merge |
| Negative hybrid delta | Giữ và phân tích như kết quả hợp lệ |

## Success Criteria

- [ ] Human review đủ lượt, agreement đúng subset và adjudication có rationale.
- [ ] Six-family table, paired differences và sensitivity có counts/provenance.
- [ ] Error/resource analysis dựa cases thật, không suy causal-path hoặc production MTTR.
- [ ] 08.results đủ cho 09/10 replay core metrics và công bố cả kết quả âm.
- [ ] Limitations gồm pooled qrels, ít families, applicability và mutable API nếu áp dụng.

## Risk Assessment

Human review chậm hơn dự toán phải cập nhật lịch, không giảm nhãn đã cam kết sau xem kết quả.
Sáu clusters không hỗ trợ khái quát rộng; fault breakdown chỉ mang tính mô tả.
Automated citation validity không thay semantic support; báo hai lớp rõ ràng.
