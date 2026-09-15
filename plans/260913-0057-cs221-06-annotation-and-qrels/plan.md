---
title: "06 — Annotation, qrels và reference có người chấm"
description: "Chấm đôi 56 incidents, giữ judgments gốc và khóa test qrels sau F1."
status: pending
priority: P1
effort: "84–150h"
tags: [research, annotation, experimental]
blockedBy: [260913-0057-cs221-05-retrieval-baselines]
blocks: [260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 06 — Annotation, qrels và reference có người chấm

Kế hoạch độc lập cho mục 06: tạo tooling và tổ chức phán quyết của người thật.

| Phase | Công việc | Công | Trạng thái |
|---|---|---:|---|
| 1 | [Rubric, schema và calibration](phase-01-start.md) | 12h | pending |
| 2 | [Chấm đôi train/dev và xuất 06.dev](phase-02-build.md) | 48–96h | pending |
| 3 | [Chấm đôi test và F2 sau F1](phase-03-validate-and-handoff.md) | 24–42h | pending |

## Goal contract

- Outcome: 56 core incidents có passage qrels chấm đôi, adjudication, answerability và references.
- Core gồm 20 train + 18 dev + 18 test; 34 train còn lại giữ unjudged, không tính IR metrics.
- Artifact: rubric, assignments, pools, original A/B, qrels, references, agreement và F2.
- Evidence hoàn tất: reviewer thật, IDs/spans/hashes đúng, original judgments và quyết định cuối riêng.
- Codex làm schemas, pool tooling, validation, agreement và export; không thay người phán quyết.
- Hai người chấm độc lập; người thứ ba adjudicate; xoay vai theo assignment của từng incident.
- Hai agent hoặc hai lần LLM không thay thế hai người chấm.
- Mốc 06.dev bàn giao trước khi hoàn tất plan; test chỉ bắt đầu sau 08.F1/test-pool.
- Thiếu người hoặc nhãn thì giữ gate pending với phiếu dùng được; không bịa completion.

## Hiện trạng kiểm trên đĩa

| Đã có | Nội dung | Khoảng thiếu |
|---|---|---|
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/status.json` | 90 tasks; 0 judgments | Chưa gold hoặc pool cuối |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/README.md` | Rubric 0/1/2 và span codepoints | Bản triển khai chấm đôi toàn 56 |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-annotation-kit.py` | Bảo vệ partial human work | Chưa import/export theo version |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/retrieval-preview/` | 400 BM25 pairs/20 train | Thiếu dense/hybrid union |
| `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/03_collection_plan/annotation-kit/qrels-annotator-A.tsv` | Một relevance_grade | Document judgment cần schema riêng |

## Đầu vào và bàn giao

- Nhận corpus/query versions và 05.runners; manager giữ private assignment metadata riêng.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/`; không ghi nhãn mới vào source annotation-kit.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/annotations/` cho pool, import, validate, agreement và export.
- Tạo `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F2.json` sau test judgments, liên kết F1 của 08.
- Qrels key gồm incident + task/window + corpus + target; query hashes chỉ là pool provenance.
- Passage/document judgments riêng; document metrics unavailable nếu chưa chấm riêng.
- Union top-10 mỗi retriever có tối đa 30/40 candidates trước dedup; không cap bỏ final top-k.
- Dev trials có candidates mới cần chấm bổ sung trước so sánh; 08 điều phối lựa chọn dev.
- Top-5 thực trả phải judged cho primary; top-10 thực trả phải judged cho MRR.
- Short/empty rankings báo riêng; mẫu số coverage dùng số hits thực, không giả đủ 5/10.
- Answerability dựa corpus review; retriever thất bại chưa chứng minh ca unanswerable.

## Công và phân vai

Tổng 84–150 giờ-người: 12h calibration/tooling, 48–96h train/dev, 24–42h test/F2.
56 × 30–40 × 2 = 3.360–4.480 judgments là dự toán trước dedup cho một task mỗi incident.
Thử thêm query variants có thể tăng pool vượt dự toán; ghi actual pairs và công bổ sung.
45–75 giây/judgment chưa được đo; năm ca calibration phải cập nhật throughput và lịch.
Năm calibration thuộc 20 train core; human output review thuộc 08, không tính công hai lần.

## Success Criteria

- [ ] 20 train + 18 dev có 06.dev; 18 test chấm sau F1 và xuất F2.
- [ ] Original A/B, agreement trước adjudication và rationale được giữ.
- [ ] Unjudged khác 0; sai snapshot/span hoặc thiếu reviewer bị export reject.
- [ ] F2 liên kết đúng F1/pool và đủ coverage của final top-5/top-10.
- [ ] Không chấm document thì không báo document metrics.
- [ ] Không dùng test feedback để tune hệ thống.

## Rủi ro và liên kết

Thiếu evidence không phải lý do bỏ ca âm thầm; ghi answerability và giới hạn pooled evaluation.
Công vượt dự toán: giảm optional branch hoặc độ dài reference trước F1, giữ chuẩn chấm đôi.
Đọc [quy ước dùng chung](../reports/260913-independent-plans-contracts.md) để phối hợp 06.dev/08.F1/06.F2.
