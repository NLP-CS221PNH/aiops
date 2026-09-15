---
title: "05 — Các bộ truy hồi và rankings pilot"
description: "Xây BM25, E5, hybrid RRF và optional reranker với cùng input, provenance và cache."
status: in-progress
priority: P1
effort: "36h"
tags: [research, retrieval, experimental]
blockedBy: [260913-0057-cs221-03-knowledge-corpus, 260913-0057-cs221-04-incident-representation]
blocks: [260913-0057-cs221-06-annotation-and-qrels, 260913-0057-cs221-07-grounded-generation, 260913-0057-cs221-08-evaluation-and-freeze, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 05 — Các bộ truy hồi và rankings pilot

Kế hoạch độc lập của mục 05; hoàn thành khi runners và pilot đủ để bàn giao cho 06/07/08.

| Phase | Công việc | Công | Trạng thái |
|---|---|---:|---|
| 1 | [Contract và fixtures](phase-01-start.md) | 8h | pending |
| 2 | [Runner và pilot](phase-02-build.md) | 20h | pending |
| 3 | [Kiểm tra và bàn giao](phase-03-validate-and-handoff.md) | 8h | pending |

## Goal contract

- Outcome: IR-B/IR-D/IR-H cùng queries/corpus, output tái đọc được và resume đúng fingerprint.
- Artifact: package retrieval, config, pilot rankings, tests, manifests và hướng dẫn chạy.
- Evidence hoàn tất: scoring fixtures đúng, cache guard hoạt động, pilot rerun có receipt.
- Codex làm implementation/tests/instrumentation, phân tích kỹ thuật và tài liệu.
- B owner IR; A review leakage/corpus; C review context interface và runtime.
- Giờ dự kiến B 28h/A 4h/C 4h; đây là giờ-người, không phải thời gian máy hay cam kết.
- 05 kết thúc tại mốc 05.runners; **08 sở hữu dev selection, F1 và final test execution**.
- Không tạo human gold, chạy generator hoặc bổ sung GraphRAG/vector database/fine-tuning.
- Input sai/thiếu phải ghi blocker có owner; không chuyển test thành pilot để đạt goal.

## Hiện trạng và khoảng thiếu

| File đã có | Dùng lại | Cần bổ sung |
|---|---|---|
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/preview-retrieval.py` | BM25, tokenizer technical, tie theo chunk ID | Tham số/config, dense, fusion, cache |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/retrieval-preview/pilot-pool-status.json` | 20 train/400 candidates | Pool chỉ BM25, 0 judgments |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/experiment-proposal.json` | Pinned revisions đề xuất | Weights chưa tải; config chưa thực thi |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/knowledge-corpus-historical/chunks.jsonl` | 580 chunks lịch sử | Derivative/applicability do 03 |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/observations.jsonl` | Bundles có thật | Queries sạch/variants do 04 |

## Đầu vào và đầu ra dự kiến

- Nhận environment từ 02, corpus 03.corpus, query variants 04.variants.
- Corpus: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunks.jsonl`.
- Queries: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/`; inference allowlist tại `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/`.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/retrieval/` và `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml`.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/retrieval/pilot/`, tests và cache có fingerprint.
- Bảng private split/gold ở `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/`; runner chỉ nhận incident allowlist.
- Runner không mount/read gold/qrels; controller chỉ truyền IDs và mode.
- 06 nhận rankings/provenance; 07 nhận hits schema; 08 nhận CLI để trial/freeze/final.
- Source pack cũ giữ nguyên; bảng results cũ NOT_RUN không được dùng làm schema kết quả mới.

## Thiết kế ban đầu

BM25 k1=1,2/b=0,75; E5 normalized cosine; exact dense search; depth=50; RRF constant=60/weights=1:1.
Content chung `section_heading + text`; E5 thêm query:/passage: prefixes theo model contract.
512 tokens cho E5; reranker 512 cho cả pair; log truncation bằng tokenizer thật.
Top-5 context là tối đa; short/empty rankings được ghi thật, không padding evidence giả.
Reranker là mở rộng có điều kiện; 08 quyết định giữ/bỏ trước F1.
Thông số này chưa phải cấu hình thắng và pilot không chứng minh retrieval quality.

## Success Criteria

- [ ] IR-B/D/H có hashes/IDs/ranks hợp lệ và đủ manifests lỗi/candidate counts.
- [ ] Fixtures RRF/BM25, cache invalidation, truncation và leakage guard pass.
- [ ] Pilot train/dev bàn giao được, không có test scores hoặc lựa chọn winner tại 05.
- [ ] Optional IR-R có trạng thái feasibility rõ, không che thiếu model/compute.
- [ ] 06/07/08 xác nhận schema và receipt 05.runners.

## Rủi ro và liên kết

Corpus thiếu evidence hoặc sai applicability không được giải quyết chỉ bằng thêm reranker.
Kaggle gián đoạn xử lý bằng cache/resume và CPU path; performance phải đo trên runtime thực.
Đổi task/window hoặc nội dung chunk cần xét chấm lại; đổi query wording cùng task chỉ bổ sung pool/provenance.
Đọc [quy ước dùng chung](../reports/260913-independent-plans-contracts.md) trước khi hiện thực hóa interface.

## Execution sync — 2026-09-13

User-approved delivery scope: **build and test the runners now; wait for a reviewed corpus before the real pilot**. The available technical slice is implemented and verified: 66 retrieval tests and 269 full-suite tests pass with zero failures/errors/skips, plus synthetic CLI/notebook reproducibility. The complete Plan05 and `05.runners` milestone remain in progress/pending real pilot and owner acceptance. No real E5/BGE forward pass, embedding-cache warm/cold measurement, human approval, quality metric, or test execution is claimed.

All three phase files were swept. [Detailed progress and criterion mapping](../../06_implementation/reports/plan05-progress.md) records completed technical portions and every remaining original requirement; [runbook](../../06_implementation/docs/retrieval-runbook.md) provides setup, CLI, error-state, resume and consumer guidance. Test and reproducibility receipts are linked from the progress report. A/B must release the corpus; B/C must provision verified pinned neural assets/runtime; 06 supplies pilot allowlists; the real pilot and consumer approvals remain outstanding.

Installed `ak plan check` checks an entire phase, with no per-item checkbox operation. No original phase is fully accepted, so all 14 original phase boxes remain unchecked; this coarse checklist count does not measure the completed engineering slice. The overall `in-progress` status is updated through `ak plan update`; no original success criterion is weakened or relabeled as synthetic acceptance. Agent technical reviews do not constitute A/B/C signatures or 06/07/08 acceptance.
