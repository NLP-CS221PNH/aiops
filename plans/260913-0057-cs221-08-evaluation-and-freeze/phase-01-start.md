---
phase: 1
title: "Evaluator, dev selection và freeze F1"
status: pending
priority: P1
effort: "10h"
dependencies: []
---

# Phase 1 — Evaluator, dev selection và F1

## Overview

Xây evaluator bằng fixtures, dùng train/dev để chọn cấu hình rồi khóa trước mọi test pool.
B chủ trì cùng Codex; A review eligibility/nhãn, C review generation parity.
Tổng 10h: evaluator 4h, dev selection 3h, freeze/review 3h.

## Requirements

- Fixture work bắt đầu sớm; F1 cần 05.runners, 07.pilot và 06.dev.
- Chỉ selection bằng train/dev; 06 full completion không là dependency của phase này.
- Giữ trial ledger gồm mọi cấu hình đã thử và nguồn judgment tương ứng.
- Mặc định workload core là một task/window mỗi incident; variants cùng task chia sẻ judgments.
- Nếu thử thêm variants, chỉ candidates mới cần thêm judgments; pool provenance giữ mọi query hashes.
- Không chạy tích mọi representation × retriever × corpus × generator.
- Chốt primary endpoint, comparator tie-break, undefined policy và eligible denominators.
- Chốt conditions, context/prompt/decoding, API permission và immutable/mutable model limitations.
- Chọn human double-review subset tại F1: một incident mỗi test family, đủ mọi conditions.
- Chọn subset bằng seed/private IDs, không đọc test content hoặc output để lựa chọn.

## Architecture

Synthetic fixtures → evaluator contract → dev runs/qrels → selection ledger → F1.
Controller được join private split/gold; runner không mount qrels hoặc private metadata.
Dùng common observation bundle theo renderer 04 cho mọi conditions; gold nguồn chỉ evaluator đọc.
F1 hash mọi input/config/code/evaluator dependencies, không chỉ giữ tên tệp.
Validation receipt phải khớp dependency hash hiện tại; cờ passed cũ không đủ.
F1 là preregistration cấu hình nội bộ, không phải kết quả test.

## Related Code Files

| Trạng thái | Đường dẫn tuyệt đối | Vai trò |
|---|---|---|
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/experiments_and_evaluation.md` | Protocol nền |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/experiment-results-template.tsv` | Bảng cũ có MRR@5/naive RAG |
| Read — đã có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/freeze-research-pack.py` | Không tái dùng làm F1 |
| Input — owner 04 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/queries/observation-bundles.jsonl` | Train/dev common bundle và bundle_hash |
| Input — owner 06 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/dev-manifest.json` | 06.dev |
| Input — owner 05 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/retrieval.yaml` | Runner config |
| Input — owner 07 | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/generation.yaml` | Generator config |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/evaluation/{metrics,freeze,__main__}.py` | Evaluator/F1 CLI |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/evaluation.yaml` | Endpoint/contrast/seed |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_evaluation_contract.py` | Hand-worked fixtures |
| Create — chưa có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/F1.json` | Frozen system manifest |

## Implementation Steps

### 08.01 — Evaluator và metric fixtures · 4h

Input: protocol, schemas và synthetic rankings/qrels; Codex viết, B kiểm công thức bằng tay.
Action: implement passage nDCG, MRR, pooled recall, document collapse và denominator status.
Output: metrics package, fixtures, strict result schema và test report.
A review no-relevant/unjudged policy; C review invalid/failed/abstained generation status.
Acceptance: fixtures phân biệt missing judgments, zero score và undefined.
Failure: metric/toolkit default cast unjudged thành 0 phải bị wrapper chặn hoặc thay logic.

### 08.02 — Chọn cấu hình trên dev · 3h

Input: 04 variants, 05 runners, 07 pilot và 06.dev; B điều phối, Codex chạy/trích bảng.
Action: dùng trial list nhỏ ghi trước; xét RQ1 trên train/dev đã có judgments và workload phù hợp.
Output: ledger chốt representation, parameters, optional IR-R và generator/prompt chung.
Primary comparator là baseline đơn nDCG@5 dev cao hơn; hòa chọn BM25.
Acceptance: mọi candidates mới phải được 06 chấm trước khi dùng điểm để chọn.
Failure: thiếu labels/permission/resources giữ F1 pending, vẫn hoàn tất fixture/tooling độc lập.

### 08.03 — Freeze F1 và kiểm chéo · 3h

Input: selected config, current hashes, approved pilot và dev receipts.
Action: chốt 18 test IDs/split hash, six-family review seed/subset, conditions và evaluator version.
Output: F1 JSON, decision record và validation receipt B/A/C review.
Codex recompute hashes; C kiểm model request identity, API permission và cohort policy.
Acceptance: không còn unresolved required decisions; mọi dependency khớp nội dung thực.
Failure: stale receipt/model alias thay giữa pilot thì đánh giá lại trước F1, không dùng cờ pass cũ.

## Metric contract phải khóa

Qrels key là incident+task/window version+corpus+chunk; query wording variants không tạo grade mới.
nDCG@5: gain = 2^rel−1, discount = log2(rank+1), IDCG từ pooled adjudicated qrels.
Primary là macro-average trên cùng tập incidents đủ relevant qrels cho mọi conditions.
Primary paired delta là mean của incident deltas trên đúng tập đó; không lấy mean của family means.
Binary relevance dùng grade ≥1; MRR@10 chỉ khi top-10 thực trả đã judged và Gq có relevant.
Gq không relevant: nDCG/recall/MRR undefined theo protocol, ghi reason và eligible count.
Gq có relevant, ranking rỗng: nDCG/recall/MRR = 0; empty run vẫn có incident row.
Top-5 unjudged chặn primary; top-10 unjudged chặn MRR, không tự thay nhãn 0.
Document ranking collapse theo lần xuất hiện đầu; document qrels riêng, thiếu thì unavailable.
Pooled Recall20/50 có judged@k, không gọi exhaustive recall hoặc guaranteed lower bound.
Accuracy top-1/top-3 báo trên đủ 18 test; failed/invalid/abstained tính không đúng, báo status riêng.

## F1 schema và interface dự kiến

F1: approved inference export, split/corpus hashes, model/tokenizer revisions, code/environment hashes.
Khóa renderer/config/schema/budget của 04, train/dev query hashes và queries/observation-bundles.jsonl hash.
Không đòi test content trước F1; sau F1 tạo test query/bundle manifest riêng có actual hashes và F1_hash.
Thêm prompt/context/decoding, conditions, comparator, metric version/rubric, review seed/subset.
Mutable API model ghi requested/returned IDs, planned cohort window và rerun policy.
Không copy gold vào F1 payload cho runner; manager giữ private join riêng.

```text
python -m pytest tests/test_evaluation_contract.py -q
python -m src.evaluation select-dev --config configs/evaluation.yaml --qrels <dev_qrels>
python -m src.evaluation freeze --stage F1 --config configs/evaluation.yaml
```

Commands dự kiến, chạy tại `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation` sau khi modules được triển khai.

## Validation Scenarios

| Scenario | Expected result |
|---|---|
| Known graded ranking | nDCG khớp tính tay |
| No relevant vs empty ranking | Undefined khác 0 |
| Một family không có eligible IR incidents; các family khác có counts khác nhau | Primary vẫn macro incidents; family rỗng undefined |
| Document labels thiếu | Secondary unavailable |
| Dev comparator hòa | BM25 được chọn |
| New dev hit chưa judged | Selection gate fail cho trial đó |
| Test subset chọn từ outputs | Reject, tạo seed selection trước outputs |
| Config đổi sau receipt | F1 gate fail vì stale hash |

## Success Criteria

- [ ] Evaluator fixtures pass và result schema có denominator/reason.
- [ ] Dev selection ledger có đủ trials và judgments hợp lệ.
- [ ] Review subset, conditions và primary comparator khóa trước test.
- [ ] F1 đúng hashes, không đòi qrels test trước pooling.

## Risk Assessment

Ít dev families làm selection nhiễu; giới hạn trials và công bố uncertainty.
Nhiều variants có thể vượt 84–150h annotation; 06 đo công, 08 thu hẹp trials trước F1.
Không có real generator được phép thì F1 giữ pending; IR/annotation tooling vẫn tiến hành được.
