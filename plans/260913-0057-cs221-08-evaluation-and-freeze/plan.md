---
title: "08 — Lựa chọn trên dev, F1/F2 và đánh giá cuối"
description: "Khóa hệ thống trước test pool, chờ human qrels F2 rồi chạy final generation, scoring và phân tích."
status: pending
priority: P1
effort: "40h"
tags: [research, evaluation, experimental]
blockedBy: [260913-0057-cs221-05-retrieval-baselines, 260913-0057-cs221-07-grounded-generation]
blocks: [260913-0057-cs221-10-report-and-release, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 08 — Lựa chọn trên dev, F1/F2 và đánh giá cuối

Kế hoạch độc lập mục 08, sở hữu final selection và test execution bằng runners từ 05/07.
Chưa có benchmark results, evaluator triển khai hoặc freeze F1/F2 trên đĩa.

| Phase | Công việc | Công | Trạng thái |
|---|---|---:|---|
| 1 | [Evaluator, dev selection và F1](phase-01-start.md) | 10h | pending |
| 2 | [Frozen test pool, F2 và scoring](phase-02-build.md) | 12h | pending |
| 3 | [Human output review và analysis](phase-03-validate-and-handoff.md) | 18h | pending |

## Goal contract

- Outcome: comparison công bằng, nhãn người, không leakage, mọi số truy được về outputs/config.
- Artifact: evaluator, evaluation.yaml, F1/F2 chain, final runs, metrics, human review và analysis.
- Evidence hoàn tất: fixtures pass, hashes/gates đúng, đủ 18 test records mỗi condition.
- Codex viết evaluator, điều phối runners, kiểm manifests và tính statistics.
- B owner protocol/statistics; A kiểm nhãn; C điều phối generation và output review.
- Nhãn relevance/support/applicability do người chấm; Codex không giả human judgment.
- F1 cần 05.runners + 07.pilot + **06.dev**, không cần hoàn tất toàn plan 06.
- Sau F1 tạo test pool → 06 chấm và xuất F2 → final generation/scoring → human output review.
- Không tune bằng test; bug sau F1 có deviation và rerun mọi conditions bị ảnh hưởng.

## Nền có thật và khoảng thiếu

| Đã có | Dùng làm căn cứ | Không được hiểu là |
|---|---|---|
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/experiments_and_evaluation.md` | Nguyên tắc đánh giá | Evaluator đã chạy |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/experiment-results-template.tsv` | Tám rows NOT_RUN | Bảng schema cuối hoặc kết quả |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/validate-research-pack.py` | Integrity gói chuẩn bị | Gate benchmark/F1/F2 |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/freeze-research-pack.py` | Checksum gói nguồn | Freeze hệ thống và qrels |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/split-map.tsv` | 18 test/6 families | 18 mẫu độc lập theo family |

## Giao diện và artifact dự kiến

- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/evaluation.yaml` và `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/evaluation/`.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F1.json`; nhận F2 owner nhãn từ 06.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/{retrieval,generation}/test/` theo run_id.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/{per-incident,family-comparison}.tsv` và analysis reports.
- Controller/evaluator đọc private split/gold; inference runners chỉ nhận allowlists, không mount qrels.
- IR-B/IR-D/IR-H bắt buộc, IR-R tùy chọn; G0/GB/GD/GH và GR tương ứng.
- Primary: passage nDCG@5; hybrid so với baseline đơn tốt hơn trên dev, hòa chọn BM25.
- F1 khóa renderer/config và train/dev bundle hashes; test query/bundle được tạo riêng sau F1.
- Document metrics chỉ có khi judgments document riêng; thiếu thì ghi unavailable.
- Top-5 đã judged; MRR@10 chỉ khi top-10 đã judged; Recall20/50 là pooled diagnostic.

## Mẫu số và giới hạn

Test gồm 18 incidents/6 families; primary là macro trên cùng tập incidents đủ nhãn, family chỉ diagnostic.
Không có relevant qrels: nDCG/recall undefined; có relevant nhưng ranking rỗng: giá trị 0.
Service top-1/top-3 accuracy dùng toàn 18; failed/invalid/abstained không có prediction đúng.
Báo riêng failures, abstention, coverage và conditional accuracy; coverage 0 → selective risk undefined.
72 final responses, hoặc 90 khi thêm GR; mỗi attempt/failure vẫn có record.
Một lượt human review toàn bộ và lượt thứ hai cho sáu incidents chọn tại F1: thêm 24/30 reviews.
Không nhân n bằng claims, seeds hoặc retries; family bootstrap nếu có chỉ mang tính thăm dò.

## Công và nghiệm thu

40 giờ-người theo phases 10/12/18h; B 18h, A 10h, C 12h là phân vai dự kiến.
Human qrels thuộc 06; human output review thuộc 08, không tính công hai lần.

- [ ] F1 trước test pooling; F2 trước generation/scoring; validation receipts khớp hashes hiện tại.
- [ ] Contrast/representation/conditions/prompt/model được chọn trên train/dev và khóa tại F1.
- [ ] Counts, eligible denominators, six-family analysis và failures được báo đầy đủ.
- [ ] Human review có agreement trên subset thực chấm đôi, không tuyên bố tất cả outputs chấm đôi.
- [ ] 08.results bàn giao cho 09/10, kể cả khi hybrid không cải thiện.

Đọc [quy ước dùng chung](../reports/260913-independent-plans-contracts.md) cho quyền đọc dữ liệu và các mốc xen kẽ.
