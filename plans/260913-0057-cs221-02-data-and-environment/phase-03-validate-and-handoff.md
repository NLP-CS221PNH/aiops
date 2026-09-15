---
phase: 3
title: "Kiểm ranh giới, tái lập và bàn giao dữ liệu"
status: pending
priority: P1
effort: "6h"
dependencies: [2]
---

# Phase 3: Kiểm ranh giới, tái lập và bàn giao dữ liệu

## Overview

Chốt gate dữ liệu bằng thử nghiệm âm, đối chiếu nguồn và bàn giao manifest cụ thể.
B review độc lập với người tạo export; A chịu trách nhiệm source claims, C nhận runtime.
Codex thực hiện kiểm và tổng hợp receipt; không tự tạo human approval.
Dự toán 6 giờ-người chưa đo; chỉ hoàn tất khi mandatory local gates pass.

## Requirements

- Source checksum phải giữ nguyên sau toàn bộ pipeline mới.
- Mỗi evidence ID unique/resolvable và thuộc đúng incident/window.
- Tất cả 90 IDs kiểm cấu trúc; đọc nội dung để debug bằng train.
- Failures được lưu có lỗi cụ thể, không silent skip incident.
- Kaggle/API unavailable không biến thành thành công giả.
- Downstream nhận inference path riêng và private boundary rõ.

## Architecture

Frozen candidate manifest → positive/negative tests → replay smoke → human review → release receipt.
Tests dùng temporary fixtures trong workspace; không mutate actual labels/gold.
Fixture đổi nhãn giữ telemetry để chứng minh serialized input bất biến.
Validator permission test kiểm path thực đã resolve trước mở file.
Review checklist gắn manifest hash; hash thay đổi làm receipt cũ invalid.
Runtime recipe và sample IDs được lưu, raw privacy content không in report.
Data gate 02 là full dependency của corpus/representation triển khai.
Refinement sau handoff tạo version mới và thông báo consumers bị ảnh hưởng.

## Related Code Files

- Existing/read: [MANIFEST_RESEARCH_SHA256.txt](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/MANIFEST_RESEARCH_SHA256.txt) — đối chiếu source.
- Existing/read: [validate-research-pack.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/validate-research-pack.py) — tham khảo scope cũ, không sửa.
- Proposed/create: [test_data_boundary.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_data_boundary.py).
- Proposed/create: [test_data_provenance.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_data_provenance.py).
- Proposed/update: [input-validation.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/input-validation.json).
- Proposed/update: [environment-check.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/environment-check.json).
- Proposed/create: [data-review-receipt.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/data-review-receipt.json).
- Proposed/create: [data-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/data-handoff.md).

## Implementation Steps

### D02-08 — Kiểm leakage/path/provenance (2h)

- Input → candidate manifest và validator/exporter phase 2.
- Action → Codex chạy fixtures âm, B review test oracle; A resolve mẫu train về raw rows.
- Output → tests + reports/input-validation.json đầy đủ result/count/error code.
- Prerequisite → D02-04/05 pass; candidate hashes cố định.
- Acceptance → all 90 IDs/joins/window hợp lệ, mọi cố đưa labels/gold/private/path sai bị reject.
- Failure path → dừng handoff; sửa exporter/config trong derivative rồi chạy lại tests bị ảnh hưởng.

### D02-09 — Tái lập và payload review (2h)

- Input → runtime lock, notebook, package manifest.
- Action → C/B chạy clean replay; Codex diff hashes và scan export/notebook outputs, A review sample payload.
- Output → environment receipt và data-review-receipt.json có người review, hash, scope, limits.
- Prerequisite → D02-08 pass; reviewer thực sẵn có.
- Acceptance → content hashes/IDs trùng; no secret/raw/private file trong package; resource numbers có bằng chứng.
- Failure path → nondeterminism/version drift được truy nguyên; thiếu reviewer giữ pending, không tự ký human review.

### D02-10 — Bàn giao và version policy (2h)

- Input → tests pass, review receipt và list unresolved issues.
- Action → Codex viết guide; A ký source/data state, B/C xác nhận đọc package bằng consumer smoke không model.
- Output → data-handoff.md với paths, schema versions, commands khi triển khai và rollback/change policy.
- Prerequisite → D02-08/09 mandatory local gates pass.
- Acceptance → plan 03/04 có cùng inference manifest; blocked branches và owner rõ; API off giữ nguyên.
- Failure path → consumer không đọc được schema thì sửa interface/adapter trước handoff; không sửa nguồn để tương thích.

## Interface và gate receipt

| Field | Nội dung |
|---|---|
| data_version | Version derivative và source revision |
| manifest_hash | Exact input-manifest hash người review đã đọc |
| schema_version | Cùng version configs/data.yaml |
| local_gate | pass/fail với tests và clean replay evidence |
| kaggle_state | pass/deferred/failed, device/null, owner và lý do |
| sharing_review | actual reviewer/status/scope; không đồng nghĩa API permitted |
| unresolved | Time/unit/alias unknown cùng allowed usage |
| consumers | Plan 03, 04 và downstream inference runners |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| DV-01 | Gold/source-case đổi trong fixture | Query/input export hash không đổi |
| DV-02 | Evidence của incident B nối incident A | Validator reject join |
| DV-03 | Duplicate evidence ID | Fail uniqueness, không overwrite dictionary im lặng |
| DV-04 | File nguyên tên nhưng hash khác | Reject và cache miss |
| DV-05 | Trace đúng boundary cuối | Rule half-open được áp dụng nhất quán |
| DV-06 | Missing metric hoặc NaN/Inf | Missing state hoặc schema fail, không giả giá trị |
| DV-07 | Private source mapping nằm trong archive | Packaging gate fail |
| DV-08 | Artifact đổi sau receipt | Receipt invalid, cần review lại phần bị ảnh hưởng |

## Handoff checklist

- Bàn giao input-manifest, schema config, inference-only index/evidence và runtime lock.
- Bàn giao data-handoff với exact root paths; không yêu cầu consumers tự tìm file bằng glob.
- Liệt kê source provenance resolver là audit-only.
- Bàn giao data/private/split-map.tsv và ground_truth.jsonl riêng cho annotation manager/evaluator; kiểm bytes/hash và 90 IDs khớp nguồn, không vào model/demo package.
- Nêu metric summary/end semantics đã xử lý thế nào và unknown units còn lại.
- Ghi sample train IDs cho reproduction, không chọn test theo labels.
- Kaggle upload, API model và chi phí vẫn theo plan 01/07.
- Mọi schema/text change tạo version mới; giữ bản cũ đã dùng cho experiments.

## Success Criteria

- [ ] Tests âm chứng minh boundary, positive checks đủ 90 IDs.
- [ ] Source hashes nguyên và derivative replay deterministic.
- [ ] Review receipt gắn exact manifest, không có chữ ký giả.
- [ ] Plan 03/04 nhận được interface hoàn chỉnh, không cần đọc labels.
- [ ] Unknown/deferred items có owner và không bị báo đã giải quyết.

## Risk Assessment

Một lần regex scan không bảo đảm sạch mọi PII; kết luận chỉ giới hạn payload/fields được review.
Evidence offset pass không chứng minh relevance hoặc truth của diagnosis.
Nếu bản nguồn thay đổi, giữ gate fail cho đến khi protocol/version được xử lý, không tự cập nhật split.
