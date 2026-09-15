---
phase: 10
title: "Báo cáo, tái lập và bàn giao đồ án"
status: pending
priority: P1
effort: "28h"
dependencies: [8, 9]
---

# Phase 10: Báo cáo, tái lập và bàn giao đồ án

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 10](../260913-0057-cs221-10-report-and-release/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Tuần 7–8, nhóm hoàn thiện báo cáo/slides/tái lập: C biên tập, A viết dữ liệu/annotation, B viết phương pháp/kết quả. Dựng khung từ tuần 1, kết luận sau phase 08–09.

## Requirements

- Trả lời câu hỏi nghiên cứu bằng kết quả thực: so hybrid với baseline BM25/dense được chọn trên dev; giữ reranker và biểu diễn incident là ablation đúng phạm vi.
- Tách retrieval, định vị service/fault, grounded claims, citation, abstention và chi phí. Không dùng nhãn injection để khẳng định causal path hoặc hiệu quả production.
- Báo 90 incidents/30 families; test gồm 18 incidents/6 families. Số dòng log hay số lượt gọi không làm tăng cỡ mẫu độc lập.
- Nêu pool annotation thực tế: 20 train + 18 dev + 18 test = 56 incidents lõi; trạng thái qrels, tỷ lệ chấm đôi, agreement trước adjudication và evidence không đủ.
- Mọi bảng/hình có run/config/qrels/corpus version; ghi lỗi, mẫu số và kết quả âm. Không tuyên bố giảm MTTR thiếu bằng chứng vận hành.

## Architecture

Outputs/evaluation/annotation audit → bảng/hình → báo cáo → slides/demo → bàn giao. Claim registry nối kết luận tới bằng chứng, người kiểm và giới hạn. Bibliography chọn nguồn thực sự dùng, giữ mức xác minh metadata.

## Related Code Files

Các file dự kiến khi triển khai:

- `06_implementation/reports/final-report.md`, bản PDF và slides theo mẫu môn học.
- `06_implementation/reports/claim-evidence.tsv`, `06_implementation/reports/final-tables/`.
- `06_implementation/docs/reproduce.md`, `06_implementation/docs/data-and-model-card.md`.
- `06_implementation/configs/final-manifest.json`, `06_implementation/reports/release-checklist.md`.

Giữ gói nguồn; bàn giao version/hash và hướng dẫn tải hợp lệ khi không thể phân phối lại.

## Implementation Steps

1. **Viết báo cáo — 8h:** nêu bài toán/đóng góp, dữ liệu/lineage, corpus applicability, chống rò rỉ, phương pháp, protocol và kết quả. So sánh 8–12 bài lõi theo tác vụ, input/gold và điều kiện đánh giá; không đồng nhất kết quả paper khác với đồ án.
2. **Kiểm lập luận — 5h:** B nối từng bảng về run, A kiểm counts và gold/qrels, C kiểm câu kết luận. Báo chênh lệch paired, uncertainty theo family, phân tích sáu test families và các ca thất bại. Khoảng tin cậy rộng hoặc hybrid không thắng vẫn là kết quả hợp lệ.
3. **Viết giới hạn — 3h:** nêu dữ liệu fault injection, một hệ thống, cửa sổ hồi cứu, coverage/tính áp dụng corpus, pooling chưa đầy đủ, cỡ mẫu nhỏ và human judgment. Với API, ghi tên model và thời gian thực chạy; alias không bất biến nên không hứa tái lập từng token. Giá/tokens lấy từ logs và thông tin tại ngày chạy.
4. **Tái lập — 6h:** một thành viên khác làm theo hướng dẫn trong môi trường mới, kiểm hashes/split, tải đúng model revision và tái tạo retrieval/metrics từ artifacts. Trên Kaggle cài dependencies tương thích, không sao chép wheels Windows của gói nguồn. Kiểm một vòng generation nhỏ nếu quyền/chi phí cho phép; phân biệt replay cache với gọi model mới.
5. **Đóng gói và bảo vệ — 6h:** chuẩn bị slides, demo, contributions và câu trả lời về leakage, baseline, qrels, missing evidence. Loại secrets, giữ license/attribution, kiểm đường dẫn và checksum. Nhóm kiểm chéo toàn bộ 18 test records kể cả failure; không bỏ ca để khớp narrative. Nộp theo rubric và ghi phiên bản bàn giao.

## Success Criteria

- [ ] Mọi con số chính truy được đến cấu hình và kết quả đã khóa.
- [ ] Báo cáo trả lời RQ, giữ kết quả âm và giới hạn sáu test families.
- [ ] Người khác tái tạo được bảng chính hoặc đọc được giới hạn tái lập cụ thể.
- [ ] Báo cáo, slides, demo, hướng dẫn và phân công đóng góp đầy đủ.
- [ ] Không còn claim causal/production/MTTR vượt quá dữ liệu thực nghiệm.

## Risk Assessment

Viết dồn: dựng khung sớm. Báo cáo lệch runs: lấy bảng từ artifacts, kiểm claim registry. Thiếu thời gian: cắt trang trí/mở rộng, giữ kiểm rò rỉ, test coverage và giới hạn.
