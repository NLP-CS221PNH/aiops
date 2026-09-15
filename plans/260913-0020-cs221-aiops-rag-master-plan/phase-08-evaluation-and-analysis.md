---
phase: 8
title: "Khóa test, đánh giá và phân tích lỗi"
status: pending
priority: P1
effort: "40h"
dependencies: [5, 6, 7]
---

# Phase 8: Khóa test, đánh giá và phân tích lỗi

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 08](../260913-0057-cs221-08-evaluation-and-freeze/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

B điều phối protocol/thống kê, A kiểm nhãn, C quản lý output review. Dự kiến 40 giờ công tuần 5–7: B 18h, A 10h, C 12h; annotation qrels thuộc phase 6. Phần F1 chỉ chờ 06A train/dev và 07A pilot; phần scoring chờ F2 của 06B. Test 18 incidents chỉ có 6 family độc lập, nên thống kê là thăm dò.

## Requirements

- Primary: passage nDCG@5, hybrid so với BM25/dense mạnh hơn trên dev; gain=2^rel−1, relevance≥1 cho binary metrics. IDCG từ pooled qrels đã adjudicate. Document secondary collapse chunk theo document, lấy thứ hạng xuất hiện đầu tiên và judgment document riêng.
- Secondary: pooled Recall@20, MRR@10, candidate Recall@50; báo judged@k và tách document/passage. Query không có relevant evidence được đánh giá answerability riêng.
- Bốn nhánh no-RAG/BM25/dense/hybrid trên cùng 18 incidents tạo 72 responses; có rerank thì năm nhánh/90 responses. Khóa quyết định trước F1; giữ generator/bundle/decoding/context allowance chung.

## Architecture

Freeze retrievers/query/corpus/prompt → chạy test pooling riêng → blind annotation/adjudication → freeze qrels → score test. Phase 6 có mốc train/dev trước; phần test được hoàn tất trong luồng này, không tạo vòng phụ thuộc buộc qrels tồn tại trước pooling.

Top-10 union 3/4 retrievers tối đa 30/40 candidates trước dedup. Cả 56 core incidents chấm qrels đôi theo phase 6. Không dùng metric test để tuning; phiếu che phương pháp/rank. B+C tạo F1 từ 06A/07A; A điều phối 06B tạo F2 rồi mới scoring.

## Related Code Files

Đọc [protocol đánh giá](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/experiments_and_evaluation.md:1). Tạo khi triển khai:

- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/evaluate.py` — metrics/aggregation.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/evaluation.yaml` — endpoint/contrast/seed.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/response-judgments.tsv` — chấm claims/citations.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/family-comparison.tsv` — paired differences.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/error-analysis.md` — case analysis.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_evaluation_contract.py` — metric fixtures.

## Implementation Steps

1. C kiểm freeze manifest; ghi model request/response, thời điểm API, prompt hash, retry và outputs gốc. Nếu dùng `deepseek-flash`, không khẳng định alias là version bất biến; thay đổi model giữa đợt phải đánh giá ảnh hưởng và chạy lại các đối chứng liên quan.
2. A quản lý test pooling/chấm mù, giữ judgments ban đầu và adjudication. Gate: mọi top-5 được đánh giá; tính MRR@10 khi top-10 đã chấm. Nếu thiếu, hoàn tất annotation trước scoring.
3. B tính metrics theo incident rồi family. Pooled recall không phải exhaustive recall hay mặc định là cận dưới của true recall; chỉ số evidence đã xác nhận là cận dưới cho số evidence relevant thực có. Báo judged@20/50, đào sâu pool khi diagnostic cần kết luận mạnh hơn.
4. C/A chấm một lượt toàn bộ 72–90 outputs và chấm đôi thêm 6 incidents (một mỗi family, đủ 4/5 cấu hình: 24–30 outputs). Chọn IDs/seed tại F1, che hệ thống; người thứ ba adjudicate, báo agreement trên subset. 96–120 lượt ×5 phút ≈8–10h, cộng 4h calibration/adjudication trong 40h; đo lại pilot. Chấm correctness, support/citation, unknowns/abstention; báo Hit@1/3 (5 tùy chọn), coverage và mẫu số, không causal path.
5. Báo point estimates, bảng paired difference của 6 family và leave-one-family-out. Nếu bootstrap, resample family cùng mọi repetitions/predictions; CI chỉ thăm dò. Không nhân mẫu bằng seeds, claims hay log rows.
6. Phân tích cả thành công/thất bại: evidence thiếu, wrong-version, upstream/downstream nhầm, citation không support cause, evidence có nhưng reranker bỏ, abstain sai. Đo p50/p95 từng bước, tokens và chi phí thực; biến thể embargo giữ riêng original test.

## Validation Scenarios

| Tình huống | Kết quả cần kiểm |
|---|---|
| Gq rỗng hoặc top-k chưa chấm | Không relevant: metric undefined; top-5 thiếu chặn primary, top-10 thiếu chặn MRR; pooledRecall20/50 kèm judged coverage |
| Nhiều chunks cùng document; ba repetitions | Dedup document; resample theo family |
| Đoán đúng service nhưng citation sai; abstain tất cả | Tách correctness/grounding; coverage phơi bày câu trả lời rỗng |

## Success Criteria

- [ ] Freeze trước pooling; qrels freeze trước scoring.
- [ ] Primary contrast được chọn trên dev; test không chỉnh cấu hình.
- [ ] Kết quả có counts, judged coverage, sáu family và sensitivity.
- [ ] Mọi claim báo cáo truy về run/evidence, kể cả kết quả âm.

## Risk Assessment

Sáu clusters không đủ cho tuyên bố khái quát rộng; breakdown fault chỉ mô tả. API mutable, annotations thiếu và corpus applicability là giới hạn phải công bố. Khi tìm lỗi test, ghi deviation và chạy lại toàn bộ baseline bị ảnh hưởng; không sửa riêng nhánh đang thua.
