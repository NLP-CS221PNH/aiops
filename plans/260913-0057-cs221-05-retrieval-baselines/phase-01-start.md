---
phase: 1
title: "Contract và fixtures retrieval"
status: pending
priority: P1
effort: "8h"
dependencies: []
---

# Phase 1 — Contract và fixtures retrieval

## Overview

Đóng input boundary và output schema trước khi xây dense/hybrid.
B/Codex 6h, A review 1h, C review 1h; mốc ra 05.contract.
Synthetic fixtures có thể làm sớm; run dữ liệu thật chờ 03.corpus/04.variants.

## Requirements

- Environment 02 import được dependencies; CPU là đường chạy tối thiểu.
- Query/corpus manifests có version và hash, kể cả khi còn pilot.
- Chỉ text quan sát/tri thức đã duyệt đi vào encoder/index.
- Scenario family, source_case, injection target và qrels không được inference đọc.
- Cùng content fields cho BM25/dense; metadata chỉ phục vụ provenance.
- Ties theo chunk ID, ranks bắt đầu 1, duplicate ID mỗi ranking bị reject.
- Empty/short ranking có record rõ, không bỏ incident hoặc tự thêm evidence.
- Không cần qrels thật để kiểm RRF, schema, cache và ID consistency.

## Architecture

Manifest allowlist → validate → query adapter → retriever → ranking schema.
Query adapter nhận common observation bundle của 04; task/window version xác định cùng bài toán.
Controller giữ split metadata riêng và chỉ truyền IDs cho runner.
Package retrieval không import evaluator hoặc modules đọc gold.
Pilot train/dev và frozen test là hai mode; 08 sở hữu mode test.
Frozen mode nhận input-manifest của test do 08 tạo sau F1, kiểm actual query hashes trước xếp hạng.
Chunk ID gắn corpus version; consumer verify hashes trước khi hợp pool.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/preview-retrieval.py` | Audit scorer/tokenizer/ties |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/experiment-proposal.json` | Model revisions đề xuất |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/source-snapshots/intfloat--e5-small-v2-sentence_bert_config.json` | Budget model |
| Input — chờ 03 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/chunks.jsonl` | Corpus derivative |
| Input — chờ 04 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/` | Query variants |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml` | Tham số chung |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/schemas/retrieval-run.schema.json` | Output schema |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/fixtures/retrieval/` | Synthetic fixture |

## Implementation Steps

### 05.01 — Audit contract · 2h

Input: preview script và upstream draft schemas; Codex đọc, B kiểm scoring, A review leakage.
Action: ghi fields sử dụng, forbidden fields, tie behavior và known gaps.
Output: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/retrieval-input-audit.md`.
Acceptance: mọi field có nguồn/owner; 400 BM25 pairs vẫn được gọi seed chưa chấm.
Failure: thiếu semantics/version → yêu cầu upstream artifact cụ thể, không đoán từ filename.

### 05.02 — Schema/config · 2h

Input: 05.01 và contract chung; Codex soạn, C review interface consumer.
Action: định nghĩa IR-B/IR-D/IR-H/IR-R; required/null fields; strict parsing.
Output: retrieval.yaml và ranking schema, ghi rõ text field policy.
Acceptance: run khác model/corpus/query không thể gộp vào cùng fingerprint.
Failure: invalid input dừng trước index, thông báo ID và field cần sửa.

### 05.03 — Fixture độc lập · 2h

Input: schema 05.02; Codex soạn corpus nhỏ và two-ranking fixture.
Action: B tính tay BM25 ordering/RRF scores; thêm ties, duplicate và empty ranking.
Output: expected values + numeric tolerance và explanation trong fixture README.
Acceptance: expected không được sinh bằng chính implementation sẽ kiểm.
Failure: tolerance không rõ thì chưa dùng output làm chứng cứ reproducibility.

### 05.04 — Review và nguồn lực · 2h

Input: contracts/fixtures; B/C chốt CPU path và ownership model weights với 02.
Action: xác định download revision, model cache, batch limit pilot và consumer needs.
Output: 05.contract review receipt, blocker list và gate nguồn lực.
Acceptance: A xác nhận input boundary;06/07 có schema preview đủ để chuẩn bị.
Failure: GPU thiếu không chặn CPU fixture; weights/revision thiếu giữ real run pending.

## Interface/schema dự kiến

```text
python -m src.retrieval index --config configs/retrieval.yaml
python -m src.retrieval run --mode pilot --incident-list <allowlist> --methods bm25,dense,hybrid --depth 50
```

Commands sẽ xây và chạy từ `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation`; chưa được thực thi khi lập plan.
Ranking row: run_id, condition, incident_id, chunk_id, document_id, rank, score.
Provenance: query_hash, task_version, window_hash, corpus_hash, config_hash; schema_version và timestamp.
Run manifest: candidate counts, errors, empty/short runs, environment/model/tokenizer hashes.
Model payload chỉ chứa query text; incident_id là metadata, không ghép vào natural language.
Corpus registry cung cấp source_url/heading/text và offsets cho downstream citations.
Không dùng hash filename làm content hash; serialization phải ổn định.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Corpus ID trùng/hash lệch | Reject trước indexing |
| Query chứa forbidden field | Boundary validation fail |
| BM25 zero overlap | hits=[] và manifest không thiếu incident |
| Scores ties | Chunk-ID ordering ổn định |
| Frozen test thiếu F1 | Reject với prerequisite cụ thể |
| Revision không tìm thấy | Không tự đổi sang latest |

## Success Criteria

- [ ] Có 05.contract và reviewers A/B/C ghi phạm vi review.
- [ ] Fixtures/schema mô tả đủ ba conditions bắt buộc.
- [ ] Paths proposed khác paths đã có được ghi rõ.
- [ ] Không có metric quality hoặc test access trong phase này.

## Risk Assessment

Thay field policy sau annotation làm qrels stale: hash/version phải xuyên suốt.
Technical tokenizer và model tokenizer khác nhau; budget/token counts ghi từng nhánh.
Fixtures có thể tiến hành khi upstream draft; pilot thật chỉ nhận manifest đã được duyệt.

## Execution evidence sync — 2026-09-13

Technical portions of 05.01–05.03 are delivered: [input audit](../../06_implementation/reports/retrieval-input-audit.md), strict config/run schema, independent hand-calculated BM25/RRF fixtures, synthetic dense checks, and actual pinned E5-tokenizer accounting. The final [test receipt](../../06_implementation/reports/retrieval-tests.md) reports 66 retrieval tests and 269 full-suite tests passing without failures/errors/skips. Current-versus-proposed input/model/pilot paths are documented, and no quality metric or real test materialization occurred.

05.04 remains partial: CPU/runtime ownership and missing-model feasibility are explicit, but A/B/C human review and corpus release are pending. Existing tokenizer assets are not model-weight evidence. No PyTorch/Transformers or pinned E5/BGE weights were provisioned. Original criterion 1 still requires actual reviewer scopes; criteria 2–4 are covered by the technical artifacts and preserved boundaries. No phase-wide check is valid yet. See [all-criteria mapping](../../06_implementation/reports/plan05-progress.md) for the full reconciliation and CLI bookkeeping limitation.
