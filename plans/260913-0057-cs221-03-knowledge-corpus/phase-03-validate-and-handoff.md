---
phase: 3
title: "Kiểm corpus, review applicability và bàn giao"
status: pending
priority: P1
effort: "6h"
dependencies: [2]
---

# Phase 3: Kiểm corpus, review applicability và bàn giao

## Overview

Nghiệm thu derivative corpus bằng integrity checks, source review và rebuild determinism.
A quyết định applicability, B review offsets/token/citations; Codex chạy kiểm và tổng hợp.
Dự toán 6 giờ-người chưa đo; corpus release không khẳng định incident coverage.
Refinement từ train/dev sau bàn giao thuộc quy trình versioned trước F1.

## Requirements

- Toàn bộ chunks được kiểm máy; human source review có tên/thời điểm/scope thật.
- Unknown applicability được phép tồn tại nếu usage/exclusion được review rõ.
- Không dùng metric kết quả test để sửa corpus.
- Rebuild cùng nguồn/config/tokenizer phải giữ IDs/text/content hash.
- Thay đổi corpus cần rebuild all retrieval branches và re-pool/rejudge affected candidates.
- Source snapshot cũ được giữ để reproducing provenance.

## Architecture

Candidate manifest → integrity suite → human decision review → deterministic rebuild → corpus receipt.
Receipt gắn exact corpus/config/tokenizer/source hashes.
Retrieval consumer chỉ đọc indexed whitelist và cùng content field.
Generation nhận citation registry và applicability, không chỉ URL.
Pool manager nhận lineage/version để phát hiện stale qrels; không tự chuyển grade theo mapping.
Plan 06 chịu evidence coverage, answerability và relevance judgments.
Plan 08 nhận final candidate qua dev trials rồi khóa F1.
Không có việc phase 03 chờ toàn bộ dev/test để được hoàn tất.

## Related Code Files

- Existing/read: [knowledge-corpus-historical/README.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/README.md).
- Proposed/create: [test_corpus_integrity.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_corpus_integrity.py).
- Proposed/create: [test_citation_registry.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_citation_registry.py).
- Proposed/update: [applicability.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/applicability.tsv).
- Proposed/update: [corpus-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/corpus-manifest.json).
- Proposed/create: [corpus-review-receipt.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-review-receipt.json).
- Proposed/create: [corpus-audit.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-audit.md).
- Proposed/create: [corpus-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/corpus-handoff.md).

## Implementation Steps

### K03-08 — Full integrity và negative checks (2h)

- Input → candidate corpus, tokenizer and registries.
- Action → Codex validate all spans/hashes/IDs/token counts; B review checks và một mẫu Unicode/short/long docs.
- Output → tests + corpus-audit với exact input hashes và issue list.
- Prerequisite → K03-04..07 candidate có đủ artifact.
- Acceptance → 100% indexed chunks resolve citation/offset/hash/token; bad lineage/missing source/foreign corpus IDs bị reject.
- Failure path → quarantine derivative lỗi và fix transform/config; không xóa nguyên doc nguồn để che failure.

### K03-09 — Applicability và content review (2h)

- Input → 74-row registry, title/boilerplate/duplicate reports và source evidence.
- Action → A/người được phân review quyết định, B review consistency; Codex nhập đúng phán quyết đã nhận.
- Output → applicability.tsv và review receipt có reviewer/status/reason cho 74 sources.
- Prerequisite → K03-08 đủ technical evidence; reviewer thực tham gia.
- Acceptance → all 74 dispositions rõ; indexed unknown chỉ allowed conditional usage; coverage/relevance chưa chấm vẫn unjudged.
- Failure path → thiếu review giữ gate pending và tooling sẵn; không điền tương thích giả hoặc giả hai người đã chấm.

### K03-10 — Rebuild và handoff versioned (2h)

- Input → reviewed corpus config/manifest và source hash set.
- Action → Codex rebuild sạch, B so sánh content hashes, A ký release scope; viết consumer/change guide.
- Output → corpus-handoff.md, final receipt và corpus-manifest status reviewed.
- Prerequisite → K03-08/09 pass; không còn citation/token integrity blocker.
- Acceptance → same IDs/text/hash; plan 05/07 đọc được chunks/citation/applicability; plan 06 nhận version+lineage.
- Failure path → nondeterminism hoặc schema mismatch thì giữ candidate, sửa/review vùng ảnh hưởng; downstream không index partial.

## Interface và receipt bàn giao

| Field | Nội dung bắt buộc |
|---|---|
| corpus_hash | Stable digest của content/config/source versions |
| source_document_count | 74 source records; indexed count báo riêng |
| indexed/excluded/unknown counts | Theo quyết định đã review, không ép 74/580 |
| tokenizer/config hash | Trùng token audit và corpus.yaml |
| applicability_review | Người thật, UTC, scope, pending/complete |
| citation_registry_hash | Registry cùng version corpus |
| limitations | Deployment unverified/conditional rules/coverage unjudged |
| lineage/change policy | Rebuild baselines và rejudge affected pools khi đổi |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| KV-01 | Offset dùng UTF-8 bytes | Test Unicode fail, phải dùng codepoints |
| KV-02 | source_url đúng nhưng text span sai | Citation validity fail |
| KV-03 | Rebuild có timestamps mới | Content digest giữ, receipt metadata thời gian được tách |
| KV-04 | Chỉnh một title/content field | Hash/version thay, stale pool được nhận diện |
| KV-05 | Chunk có parent từ current corpus | Historical manifest reject foreign source |
| KV-06 | Unknown applicability không có policy | Review gate fail |
| KV-07 | Artifact còn proposed-mappings text | Whitelist/index check fail |
| KV-08 | Human coverage chưa chấm | Report unjudged, không tạo tỷ lệ coverage |

## Bàn giao và refinement sau plan

- Plan 05 nhận chunks/content policy/tokenizer/corpus hash.
- Plan 07/09 nhận citation registry và applicability để trình bày điều kiện sử dụng.
- Plan 06 nhận source metadata/lineage và warnings, không nhận relevance gán sẵn.
- Train pilot thiếu evidence: mở change proposal theo claim gap có nguồn, A review.
- Corpus thay trước F1: tạo version, rebuild mọi baseline, re-pool và chấm lại pairs affected.
- Không chuyển qrel cũ sang chunk mới chỉ vì cùng title hoặc overlapping span.
- Thay sau F1 theo deviation policy plan 08, giữ original outputs và ghi ảnh hưởng unseen test.
- Current snapshot ablation chỉ sau explicit optional decision, có manifest riêng.

## Success Criteria

- [ ] Toàn indexed corpus đạt integrity/token/citation checks.
- [ ] 74 dispositions có human review thật; unknown được giữ với policy.
- [ ] Same-config rebuild deterministic, source hashes nguyên.
- [ ] Downstream nhận đủ schema/path/hash và biết qrels nào stale.
- [ ] Completion không tuyên bố coverage, compatibility hay benchmark chưa đo.

## Risk Assessment

Đếm đúng chunks không là semantic coverage; phase 06 có quyền phát hiện corpus thiếu evidence.
Human reviewer trong nhóm không là external independent reviewer; ghi đúng tổ chức đánh giá.
Nếu unknown docs chỉ đủ hỗ trợ bước kiểm tra, giữ phạm vi claim ấy đến khi có bằng chứng thêm.

## Partial execution evidence — 2026-09-13

K03-08 technical validation is complete: 60 corpus/citation tests and the 48 data +52 protocol regression tests passed without failures/errors/skips. Independent code review accepts this local candidate with score 9/10 and zero remaining critical/high/medium findings. The [technical receipt](../../06_implementation/reports/corpus-review-receipt.json) binds actual automated evidence and preserves an empty `human_reviews` list.

K03-09 remains pending: no actual human A/B applicability/content decision has been received. All 74 proposals have reasons/evidence and explicit owners, but no reviewer or review timestamp is invented. K03-10's clean rebuild and schema/change-guide portions are complete; its reviewed-release/signed-scope portion is pending. The manifest stays `candidate`, and strict reviewed validation returns `RELEASE_PENDING`.

| Original success criterion | Verified state |
|---|---|
| Integrity/token/citation | Technical pass for all 440 candidate chunks; released indexed population is zero. |
| 74 actual human-reviewed dispositions | Pending A/B; Plan 02 human acceptance is also pending. |
| Same-config deterministic rebuild/source hashes | Pass; independent builds reproduce all eight files and retain raw hashes. |
| Downstream schema/path/hash/stale-qrels guide | Complete in [handoff](../../06_implementation/reports/corpus-handoff.md). |
| No unmeasured coverage/compatibility/benchmark claim | Preserved: unjudged/unknown, no model run. |

Four of five criteria have technical evidence, but the available `ak plan check` toggles every checkbox in a phase. No blanket check was applied; the five boxes above remain pending to avoid falsely completing the actual human criterion. This exact partial state is recorded in [progress](../../06_implementation/reports/plan03-progress.md); the original plan remains `in-progress` while the explicitly authorized local-candidate task is complete.
