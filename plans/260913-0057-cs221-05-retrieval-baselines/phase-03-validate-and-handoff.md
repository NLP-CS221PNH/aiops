---
phase: 3
title: "Kiểm runner và bàn giao"
status: pending
priority: P1
effort: "8h"
dependencies: [2]
---

# Phase 3 — Kiểm runner và bàn giao

## Overview

Nghiệm thu kỹ thuật để 06 dùng rankings, 07 dùng hits và 08 dùng frozen runner sau này.
B/Codex 5h, A review 2h, C review 1h; tổng 8 giờ-người.
05 hoàn tất tại 05.runners, không chờ qrels test hay F1.

## Requirements

- Có runners, pilot manifests và expected fixtures độc lập.
- Tests phải bắt sai scoring/hash/IDs; không chỉ lặp implementation.
- Không chạy test metrics hoặc đọc test judgments ở phase này.
- 08 sở hữu final dev selection, optional reranker decision và test execution.
- Validator source preparation vẫn đòi 0 judgments/NOT_RUN, không dùng cho implementation.
- Notebook và CLI gọi cùng code path; hardware/tolerance ghi rõ.
- Report tách đo runtime thật và quality chưa được đo.
- Source artifacts không bị viết lại để phù hợp kết quả mới.

## Architecture

Fixtures → contract tests → pilot rerun → boundary review → handoff receipt.
Consumers verify run/query/corpus/config hashes trước sử dụng.
Một mismatch làm run/pool stale, không tự sửa references của artifact cũ.
08 chỉ gọi runner bằng allowlist/config/F1; qrels private chỉ evaluator đọc.
Lỗi code sau bàn giao được theo dõi như bug/deviation riêng.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/validate-research-pack.py` | Preparation gate khác implementation |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/retrieval-preview/README.md` | Pool preview chưa gold |
| Read — sau phase 2 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/` | Runner cần nghiệm thu |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_retrieval_contract.py` | Integrity/scoring tests |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/retrieval-pilot-audit.md` | Kết quả kiểm thực |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/retrieval-handoff.json` | 05.runners receipt |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/retrieval-runbook.md` | CLI/Kaggle/resume |
| Future input — owner 08 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F1.json` | Test gate sau dev |

## Implementation Steps

### 05.10 — Scoring/cache tests · 3h

Input: fixtures và implementations; Codex viết/run tests, B review assertions.
Action: kiểm BM25/RRF, ties, duplicate IDs, cache invalidation và truncation.
Output: receipt command, env hash, expected/observed và failures.
Acceptance: hand-calculated case bắt được sai công thức; tất cả required checks pass.
Failure: sửa logic và chạy checks bị ảnh hưởng, không xóa fixture để đạt goal.

### 05.11 — Input/split boundary · 2h

Input: allowlist/read graph và pilot outputs; A review cùng Codex.
Action: kiểm runner không mount labels/qrels; serialized query không có manager fields.
Output: boundary report với file/field references và test-mode guard results.
Acceptance: forbidden private paths không được inference đọc; fake/stale F1 bị từ chối.
Failure: leak chặn handoff, rerun mọi pilot ảnh hưởng sau khi sửa.

### 05.12 — Rerun/resume/consumer · 2h

Input: một train pilot và checkpoint; B/C thử same CLI/consumer parsers.
Action: warm/cold rerun, simulate interruption, kiểm reads của 06/07.
Output: reproducibility receipt, schema confirmation và hardware/tolerance.
Acceptance: stable ID/order theo policy; mọi float lệch được giải thích trong tolerance.
Failure: mismatch config/cache phải sửa trước khi consumer nhận dữ liệu.

### 05.13 — 05.runners handoff · 1h

Input: checks trước; Codex viết runbook/receipt, B owner nghiệm thu, A/C ghi review.
Action: liệt kê commands, limitations, optional IR-R và invalidation policy.
Output: retrieval-handoff.json có paths/hashes/check timestamps.
Acceptance: 06 có rankings/provenance;07 có hits;08 có runner/config để tiếp tục.
Failure: thiếu một artifact bắt buộc giữ task pending, không tuyên bố benchmark complete.

## Commands nghiệm thu dự kiến

```text
python -m pytest tests/test_retrieval_contract.py -q
python -m src.retrieval validate-run --manifest runs/retrieval/pilot/run-manifest.json
python -m src.retrieval run --mode pilot --incident-list <one_train_id> --resume --config configs/retrieval.yaml
```

Commands chạy từ `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation` sau implementation.
Receipt lưu expected/observed, command/env/config hashes, reviewer và UTC.
Frozen test runner sẽ cần F1; 08 quyết định thời điểm, không execute ở đây.
Không đổi tên old BM25 seed output thành chuẩn final để tránh phải chạy lại.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Duplicate IDs/ranks | Reject |
| Tie trong merged rankings | Deterministic ordering |
| Thiếu incident record | Validation fail; không silently drop |
| Methods khác query/corpus | Không hợp pool/cặp comparison |
| Resume config khác | Reject, ghi run mới |
| Annotation có người đang nhập | Runner không ghi hoặc overwrite |
| Không GPU | CPU smoke hoặc measured blocker rõ |
| Quality scores chưa có | Đúng trạng thái, không fabricate |

## Success Criteria

- [ ] Required technical tests pass, receipts khớp artifact hiện tại.
- [ ] Pilot rerun và restart được minh chứng.
- [ ] Consumer owners nhận contract 05.runners.
- [ ] 05 hoàn tất không phụ thuộc toàn plan 06 hoặc08.
- [ ] Winner/config final/test metrics chưa được quyết định tại 05.

## Handoff và Risk Assessment

06 sở hữu union/blinding/adjudication; 05 chỉ cung cấp rankings có provenance.
07 pack cùng IDs và budgets; không tự thêm outside-context evidence.
08 dùng 06.dev để chọn representation/contrast, tạo F1 và điều phối final.
Các query variants cùng task/window dùng chung judgments; chỉ new candidates cần thêm nhãn.
Bug sau F1 phải ghi deviation và rerun đủ conditions ảnh hưởng dưới 08.
Corpus thiếu evidence không phải lỗi runner;report giới hạn và chuyển 06 applicability/coverage.

## Execution evidence sync — 2026-09-13

Technical portions of 05.10–05.13 are delivered: [66 retrieval / 269 full-suite checks](../../06_implementation/reports/retrieval-tests.md) pass with no failures/errors/skips, and [synthetic delivery verification](../../06_implementation/reports/retrieval-reproducibility.json) binds CLI/notebook expectations, current code/environment and output hashes. Integrity checks cover corrupted/omitted records, finite scores, identity/provenance mismatches, forbidden paths/fields, release/F1 rejection, immutable retry attempts and compatible-run readers. [Runbook](../../06_implementation/docs/retrieval-runbook.md) documents commands, invalidation, failure states and future consumer gates.

Actual E5/BGE forward passes and embedding-cache performance remain unverified; the generic pair-budget fixture uses the E5 tokenizer and does not validate the absent BGE tokenizer. Original criterion 1 is technically met for the authorized build/test slice, and criterion 5 is preserved. Criteria 2–4 remain pending real pilot rerun/restart evidence, actual consumer-owner acceptance and full Plan05 completion. `05.runners` is not accepted merely because the technical slice passes; the smaller delivery follows the user's explicit deferral. See [all-criteria mapping](../../06_implementation/reports/plan05-progress.md); no phase-wide check is valid yet.
