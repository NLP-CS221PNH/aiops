---
phase: 2
title: "Chấm đôi train/dev và xuất 06.dev"
status: pending
priority: P1
effort: "48–96h"
dependencies: [1]
---

# Phase 2 — Chấm đôi train/dev và xuất 06.dev

## Overview

Hoàn thành 20 train core gồm năm calibration và 18 dev, mọi passage pairs được chấm đôi.
Mốc 06.dev cho 08 chọn representation/baselines và tạo F1; không chờ test.
Công 48–96h bổ sung phase 1; ghi riêng reannotation do rubric hoặc trial candidates mới.

## Requirements

- Có rubric/calibration gate và 05.runners.
- Chọn 20 train để phủ 18 train families khi khả thi; không cherry-pick ca dễ.
- Pools giữ query/corpus hashes của runs; grades căn cứ cùng full observation/task.
- 30/40 candidates trước dedup là dự toán; không cap bỏ final top-k.
- Original A/B immutable sau submit; adjudicator ghi rationale và evidence.
- Agreement tính trước adjudication, gồm weighted kappa, raw agreement và grade distribution.
- Không dùng ngưỡng kappa tùy ý làm chuẩn thành công của môn CS221.
- References/answerability do người kiểm, không suy từ gold service hoặc BM25 failure.
- Document metrics chỉ khả dụng khi có document judgments riêng đầy đủ.
- Labels/references không được mount vào retrieval hoặc generation runtime.

## Architecture

Train pool → double judgments → agreement → adjudication → train export.
Dev pool → double judgments → candidates bổ sung → versioned dev export.
08 dùng 06.dev để chọn cấu hình; dev hits mới quay lại round bổ sung theo cùng rubric.
Manifest 06.dev ghi hashes và coverage để 08 biết bản nào được dùng cho selection.
Base workload là một task mỗi incident; variants dùng chung judgments nếu task/evidence không đổi.
Variants chỉ làm tăng nhãn khi có candidates mới; intent/window/chunk đổi cần xét chấm lại.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/split-map.tsv` | Nguồn 54/18/18, manager-only |
| Input — owner 02 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/split-map.tsv` | Assignment join |
| Input — owner 05 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/pilot/` | Rankings/provenance |
| Modify — sau phase 1 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/rubric-v1.md` | History khi thay đổi |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/pools/{train,dev}/` | Manager pools |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/blinded/{train,dev}/` | Original A/B |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/qrels/{train,dev}/` | Passage/document exports |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/annotations/{agreement,coverage,export_gold}.py` | Agreement/coverage/export |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/dev-manifest.json` | 06.dev receipt |

## Implementation Steps

### 06.05 — Mở round và tooling · 8–12h

Input: calibrated schemas, pilot rankings, assignments; Codex xây import/export, A review.
Action: chọn 20 train core và giữ năm calibration; hợp dev pool, phân lịch hai reviewers.
Output: pools, forms, time ledger và import/export tests.
Acceptance: A/B pair sets bằng nhau, IDs đúng split, provenance tách khỏi blind forms.
Failure: task/window/corpus/rubric đổi thì tạo round mới; query wording đổi chỉ bổ sung provenance/candidates.

### 06.06 — Chấm đôi train/dev · 22–48h

Input: 15 train còn lại + 18 dev và calibration cần chấm lại, observations/corpus.
Action: hai người chấm độc lập grade/span/role/applicability, bổ sung evidence nếu tìm thấy.
Output: original A/B, actual time và human-found candidates có provenance.
Codex hỗ trợ viewer/validation; A/B/C xoay vai và không xem phiếu nhau trước submit.
Acceptance: mọi required pair có hai reviewer khác nhau, target và span hợp lệ.
Failure: thiếu nhãn giữ pending, không dùng LLM hoặc default 0 để lấp.

### 06.07 — Agreement, adjudication và references · 10–24h

Input: A/B đã submit; Codex tính agreement, người thứ ba adjudicate bằng evidence.
Action: giữ raw grades/distribution; viết reference ngắn có claims, citations và unknowns.
Output: adjudication, answerability/reference cho 38 train/dev core; document judgments nếu có.
Acceptance: evidence chỉ hỗ trợ diagnostic check không bị nâng thành causal proof.
Failure: ca thiếu evidence không bị bỏ; ghi uncertainty và missing evidence.

### 06.08 — Dev candidates bổ sung và 06.dev · 8–12h

Input: qrels/dev trials do 08 điều phối; Codex lập coverage audit.
Action: pool hits mới ở top-5/top-10, chấm đôi trước comparison, lưu version history.
Output: dev-manifest liên kết queries/corpus/runs/rubric/qrels và coverage.
Acceptance: 08 nhận qrels adjudicated với trial ledger đồng bộ và top-k đã judged.
Failure: thiếu labels thì trả danh sách pairs cần chấm, không xem test để quyết định.

## Schema và export contract

Mỗi qrels version có task/window/corpus/pool/rubric hashes và expected incident IDs.
Danh sách query hashes là provenance của pool, không là grade key của cùng task.
Passage TSV chứa incident_id, chunk_id, grade; sidecar giữ reviewers/spans/provenance.
Document TSV chứa incident_id, document_id, document_grade từ judgments riêng.
Thiếu document labels thì manifest ghi unavailable, không tự suy từ passage.
Answerability/reference join theo incident+task/window+corpus version, không theo query wording.
Bất đồng được lưu dù final grade bằng một trong hai reviewers.
Eligible metric denominator do 08 tính từ qrels, không từ số hàng forms.

## Interface dự kiến

```text
python -m src.annotations.agreement --round annotations/blinded/dev --before-adjudication
python -m src.annotations.export_gold --split dev --require-double --round <round_id>
python -m src.annotations.coverage --runs <dev_runs> --qrels <dev_qrels> --required-k 5,10
```

Các commands chưa triển khai; không chạy script chuẩn bị cũ để ghi đè forms.
Coverage dùng actual hits; empty/short rankings được báo riêng.
Top-10 union không bảo đảm toàn corpus đã judged; phải gọi pooled evaluation.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| ID sai split/family assignment | Manager guard reject |
| Trial mới có top-5 ngoài pool | Chặn comparison tương ứng đến khi chấm |
| A/B bất đồng, chưa adjudicate | Không xuất gold |
| Không có relevant judged evidence | Giữ ca và answerability review |
| Document labels thiếu | Document metric unavailable |
| Evidence người tìm ngoài pool | Thêm provenance/version và chấm đôi |
| Reference citation sai ID/span | Reference export fail |

## Success Criteria

- [ ] 20 train + 18 dev có human qrels chấm đôi và version.
- [ ] Agreement trước adjudication và distributions được báo.
- [ ] References/answerability có evidence, unknowns và reviewer.
- [ ] 06.dev đủ cho 08 selection/F1, không cần test labels.
- [ ] 34 train chưa chấm giữ unjudged rõ ràng.

## Risk Assessment

Trials nhiều hoặc overlap thấp tăng công: 08 giới hạn trials, 06 ghi actual/deepening.
Thiếu causal evidence thì thu hẹp claim bằng quyết định trước F1, không âm thầm loại ca.
Manager/adjudicator luân phiên khiến blinding nội bộ có giới hạn; công bố đúng thực tế.
