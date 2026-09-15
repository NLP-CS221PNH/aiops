---
phase: 2
title: "Xây runners và pilot rankings"
status: pending
priority: P1
effort: "20h"
dependencies: [1]
---

# Phase 2 — Xây runners và pilot rankings

## Overview

Xây IR-B/IR-D/IR-H cùng inputs, cache và checkpoints; optional IR-R nếu pilot đáp ứng.
B/Codex 17h, A review 1h, C review/tích hợp 2h; tổng 20 giờ-người.
Mốc đầu ra là runners/pilot, không phải final dev selection hoặc benchmark test.

## Requirements

- Qua 05.contract; có environment, corpus derivative và query variants.
- E5 dùng prefixes, revision và normalized cosine theo proposal đã kiểm.
- Exact dense search phù hợp corpus khoảng 580 chunks; chưa cần vector database.
- E5 512 tokens gồm prefix/special tokens; log trước/sau truncation.
- Reranker 512 tokens cho query+passage cùng special tokens.
- Query budget chung do 04 quy định; không cho một retriever đọc dài hơn âm thầm.
- Retrieval depth=50; top-10 dùng annotation; top-5 là tối đa của context.
- Phiếu human do 06 quản lý; runner không được mount/read annotations.
- Timings phân biệt indexing/query encode/search/fusion/rerank và cache warm/cold.

## Architecture

BM25 postings và embedding matrix chung row→chunk registry.
RRF cộng reciprocal ranks, không cộng lexical score với cosine raw.
Rerank chỉ nhìn hybrid top-50; không đưa gold evidence thêm vào candidate pool.
Checkpoint khóa incident/condition/config; resume chỉ khi fingerprint khớp.
Các processes không ghi chung output file; run_id xác định thư mục độc lập.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/preview-retrieval.py` | BM25 semantics |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/source-snapshots/support-resources.json` | Revisions/receipts |
| Modify — sau phase 1 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml` | Pilot values |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/__main__.py` | CLI điều phối |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/{bm25,dense,fusion,rerank,cache}.py` | Engines và cache |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/notebooks/02_retrieval.ipynb` | Wrapper gọi module |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/pilot/` | Pilot outputs |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/cache/retrieval/` | Rebuildable cache |

## Implementation Steps

### 05.05 — BM25 runner · 4h

Input: scorer cũ, config, fixture; Codex port, B review equivalence.
Action: expose k1/b/depth; preserve technical tokens; guard empty data and ties.
Output: IR-B module và pilot sanity rankings kèm hashes.
Acceptance: cùng input/config thì ordering match expected fixture/preview.
Failure: lệch tokenizer/content policy phải giải thích và version, không sửa expected cho vừa code.

### 05.06 — E5/cache · 6h

Input: pinned weights/tokenizer, corpus; Codex xây batches, B kiểm normalization.
Action: tokenize prefixes, count lengths, exact cosine search, finite-vector/dimension checks.
Output: IR-D, embedding matrix, row registry và cache manifest.
Acceptance: đổi text/model/tokenizer/prefix/max_tokens làm cache miss hoặc reject.
Failure: OOM giảm batch/chuyển CPU; tải lỗi giữ missing-model status, không thay alias.

### 05.07 — Fusion và reranker · 4h

Input: IR-B/D cùng hashes; Codex implement RRF, B kiểm hand fixture.
Action: constant=60/weights=1:1; duplicate reject; rerank adapter chỉ nhận candidate set hiện có.
Output: IR-H và optional IR-R feasibility receipt.
Acceptance: scores/ties đúng; pair truncation/logging đúng; candidate IDs không tự mở rộng.
Failure: IR-R thiếu nguồn lực ghi unavailable cho 08 quyết định trước F1.

### 05.08 — Pilot/checkpoint · 4h

Input: methods đã build, 20 train IDs được 06 chọn và dev allowlist.
Action: 5 train smoke rồi train pilot/dev rankings; interruption và resume theo fingerprint.
Output: complete/failed record cho từng incident×condition, times/errors/candidate counts.
A review allowlist; C kiểm hits reader của 07.
Acceptance: không test IDs; không bỏ rows lỗi hoặc trộn config vào cùng run.
Failure: giữ checkpoint, retry phần chưa hoàn tất và không chọn retry theo correctness.

### 05.09 — Manager bundle · 2h

Input: pilot runs/manifest; Codex chuẩn bị bundle, 06 sở hữu union và blinding.
Action: cung cấp top-50/provenance; ghi top-10 candidate designation.
Output: manager receipt với corpus/query versions và timing/resource summary.
Acceptance: 06 đọc được IDs và biết số hits thực; reviewer sheet không nhận rank/score.
Failure: hash đổi thì run version mới, downstream pool cũ được đánh dấu stale.

## Interface/cache contract

```text
python -m src.retrieval run --mode pilot --incident-list <train_ids> --config configs/retrieval.yaml
python -m src.retrieval run --mode pilot --incident-list <dev_ids> --config configs/retrieval.yaml --resume
```

Cache key: corpus text hash, content policy, model/tokenizer revision, prefixes, normalization, max_tokens.
Rerank key thêm query hash và ordered candidate text hashes; tên file không đủ định danh.
Manifest lưu dtype/hardware/batch/warmup/env versions; estimated bytes/tokens phải có nhãn estimate.
Atomic checkpoint hoặc append có index/checksum bảo vệ partial runs.
Mọi text/truncation thay đổi phải làm key thay đổi; không dùng cache từ variant khác.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Đổi prefix/revision | Invalidated cache |
| Long passage | Deterministic cut và logged removed tokens |
| Long pair | Budget cả pair, không cắt passage thành rỗng im lặng |
| Missing hit một branch | RRF contribution nhánh còn lại đúng |
| Interrupted batch | Resume không duplicate hoặc overwrite config khác |
| Relevant ngoài candidates | Báo candidate limitation, không kết luận quality reranker |

## Success Criteria

- [ ] IR-B/D/H chạy cùng corpus/query với complete manifests.
- [ ] Cache/resume/truncation được kiểm trên pilot.
- [ ] 06 có rankings để pool;07 có hits schema để context.
- [ ] IR-R feasibility rõ; final inclusion thuộc 08.
- [ ] Chưa có scores quality khi chưa có qrels người.

## Risk Assessment

Empty BM25 là khả năng hợp lệ, không padding; consumer phải xử lý.
GPU quota không chắc chắn: CPU/cache/batch nhỏ là fallback đo được.
Query/corpus thay sau pilot làm lại manifest; không tái dùng judgments khi text target đã đổi.

## Execution evidence sync — 2026-09-13

The user deferred actual pilot work until reviewed corpus input exists. Technical portions of 05.05–05.09 are implemented: canonical BM25, exact normalized-cosine search, local-only pinned E5 adapter, RRF, bounded optional BGE adapter, strict inputs, fingerprinted immutable caches, exclusive cache/run locks, and atomic checkpoint/manifest publication. Reranker is disabled by default. Missing models create explicit failed records; synthetic vectors never stand in for E5 rankings.

[Synthetic reproducibility](../../06_implementation/reports/retrieval-reproducibility.json) verifies the CLI and notebook, deterministic BM25 repeats, empty-hit handling, interruption/resume and reader behavior. A retry uses a separate immutable attempt file so the previously committed attempt survives interruption before the index switch. These checks do not establish actual neural execution, embedding-cache warm/cold timing, or real pilot performance.

Original criteria 1–3 remain pending actual reviewed-corpus BM25/dense/hybrid pilot, real cache/runtime evidence, and rankings/consumer handoff. Criterion 4 has explicit unavailable/disabled feasibility; Plan08 owns final inclusion. Criterion 5 is preserved: no quality score or winner is claimed. [Pilot audit](../../06_implementation/reports/retrieval-pilot-audit.md) and [progress mapping](../../06_implementation/reports/plan05-progress.md) retain all owners and remaining acceptance conditions; no phase-wide check is valid.
