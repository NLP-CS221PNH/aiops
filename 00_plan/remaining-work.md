# Việc còn lại (human plan)

Đây là kế hoạch còn lại **dành cho người**. Overlay AgentKit nằm ở `plans/` trên máy làm việc, không phải bề mặt Git công khai. Snapshot G0 vẫn giữ `plans/reports/260913-independent-plans-contracts.md`.

Ngày khóa: 2026-09-17. Không phải rubric chấm điểm chính thức của UIT.

## Việc đã khóa — không nấu lại

| Hạng mục | Trạng thái trung thực |
|---|---|
| Đề cương, RQ, MVP RE2-OB | Giữ. GraphRAG / multi-agent / IR-R / Train Ticket nằm ngoài MVP. |
| Tooling 02–05, 07, 09 | Có runners, export suy luận, biến thể R1/R2/R3, demo cục bộ. Chữ ký A/B/C người vẫn pending. |
| Hợp đồng vàng G1≠G2≠G3≠G4 | Đã đóng. Proxy `llm_lexical_proxy` không phải human gold. G4 ngoài phạm vi. |
| Khóa phương pháp `METH-LOCK-20260917` | k1=1.2, T=0.1, R2, IR-B/D/H, G0–GH. Bảng 1–4 là `NOT_RUN`. |
| Bibliography overlay | Catalog 1.009 là discovery registry. Core literature tách riêng. Không suy Q1 từ `@article`. |
| History rewrite | Không. `HIST-2026-09-16-NO-REWRITE`. |

Các số nDCG 0.671 / 0.342 và Top-1 72.2% đã rút. Không phục hồi chúng.

## Đường găng khoa học còn lại

1. **Duyệt applicability corpus** — 74 tài liệu; `index_whitelist` hiện `[]`. Unblock “67 hợp lệ” không phải release.
2. **F1 mới** — F1/F2 hiện tại bị sidecar vô hiệu (whitelist rỗng + proxy qrels). Giữ bytes cũ.
3. **Calibration** — 5 ca train, hai người độc lập. Báo cáo calibration cũ không dùng.
4. **Human G2** — 20 train + 18 dev + 18 test; chấm đôi passage 0/1/2; unjudged ≠ 0. Protocol: `06_implementation/docs/retrieval-qrels-protocol.md`.
5. **Rankings đóng băng** rồi mới chấm nDCG@5. Hybrid hòa trên dev thì chọn BM25.
6. **G3** (hỗ trợ claim) là form riêng. Không báo citation/support headline khi chưa chấm.
7. **Viết lại báo cáo** sau khi có số từ evaluator. Plan 10 cũ đã đóng sớm.

Không chấm nDCG trên qrels proxy, kể cả ablation.

## Hợp đồng dữ liệu cần một câu trả lời

Plan 02 gốc: giữ null, không impute. Một overlay agent từng yêu cầu mean-impute. `configs/data.yaml` vẫn “preserve null”. Trước thí nghiệm cuối, nhóm chọn **một** hợp đồng và ghi vào decision log.

## Cổng môn học / hạ tầng

Còn mở: hạn nộp, rubric, giờ cam kết, quyền API/local model, trần tiền, ngôn ngữ output. Plan 01 đóng bằng automated acceptance; không suy thành chữ ký giảng viên.

Publication: untrack không xóa blob cũ. Required GitHub checks, heavy runner và archive SHA là việc owner, không phải gate khoa học.

## Việc không làm trong MVP

Reranker, GraphRAG, multi-agent, iterative retrieval, generator thứ hai, tải OpenRCA/Loghub/TechQA/RE2-TT telemetry, rewrite Git history.
