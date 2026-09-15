---
phase: 4
title: "Biểu diễn incident và kiểm soát đầu vào"
status: pending
priority: P1
effort: "20h"
dependencies: [2]
---

# Phase 4: Biểu diễn incident và kiểm soát đầu vào

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 04](../260913-0057-cs221-04-incident-representation/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

B phụ trách biểu diễn; A kiểm dữ liệu, C kiểm generator. Dự kiến 20 giờ công: B 14h, A 4h, C 2h. Mốc 04A tạo query draft tuần 2 đủ để 05 xây runner/pool; mốc 04B chọn biểu diễn trên dev ở tuần 5 sau 06A. Không buộc phase 05 đợi toàn bộ ablation/chốt phase 04.

## Requirements

- Giữ service, error code, exception, timestamp và evidence ID; truy ngược được mỗi đoạn về observations.
- Cùng incident/window cho mọi biểu diễn; không đọc gold, injection time, case name hoặc đường dẫn chứa nhãn.
- Query tiếng Anh cho E5; không thêm dịch máy hoặc LLM summary vào ba ablation chính.
- Paraphrase/repetition kế thừa family/split. Metadata quản lý family/split không serialize vào prompt.

## Architecture

Observations đã redaction → chọn đoạn cố định → ba query → tokenizer audit → retrieval. Generator nhận cùng bundle quan sát ở phase 7.

R1 là raw selected error lines sau redaction; R2 là normalized lines giữ thực thể; R3 là bundle theo service/thời gian cùng mô tả metric/trace. Không gửi toàn bộ raw telemetry. Chỉ thay representation trên dev; giữ retriever/corpus và giới hạn query chung.

## Related Code Files

Đọc [pipeline observations](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-incidents.py:67). Các tệp sau tạo khi triển khai:

- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/representations.py` — quy tắc query.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/representations.yaml` — whitelist, window, tokenizer.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/queries.jsonl` — queries có version.
- Create: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_representation_contract.py` — rò rỉ/provenance.

## Implementation Steps

1. A kiểm 6 train incidents phủ nhiều family, đối chiếu evidence IDs với telemetry. Xác nhận timestamp/unit và missing values. Window hiện dùng toàn khoảng metric hồi cứu, không phải detection onset.
2. Audit query hiện tại lấy 8 log đầu sau sắp xếp service/time. Kiểm việc một service chiếm hết chỗ; thử phân bổ đoạn theo service và tần suất trên train/dev, không đọc gold test.
3. Tạo whitelist và ba representation. Lưu input IDs, transformation version, window, redaction version; không đưa summary suy diễn thành observation thật.
4. B đếm tokens bằng tokenizer thật, kể cả prefix. Ghi tỷ lệ truncation và evidence bị loại; dùng cùng quy tắc giới hạn cho mọi retriever.
5. Chạy R1/R2/R3 trên dev với retriever tham chiếu. Phase 6 chấm thêm candidates mới trước so sánh; không tính unjudged như grade 0. Ghi cả ablation không cải thiện.
6. Chọn dạng chính trên dev, khóa version/hash rồi tạo query test bằng quy tắc ấy. C xác nhận bundle chung cho bốn nhánh generation bắt buộc và GR nếu chọn; dữ liệu đủ điều kiện đưa lên Kaggle/API theo phase 2.

## Validation Scenarios

| Tình huống | Kết quả cần kiểm |
|---|---|
| Thay gold/case metadata, giữ telemetry | Query không đổi; whitelist không chứa trường nhãn |
| Log có HTTP 503, exception, service có dấu gạch | Chuẩn hóa giữ tín hiệu và evidence ID |
| Query vượt token limit hoặc thiếu modality | Có truncation/missing marker; không bịa observations |

## Success Criteria

- [ ] Ba representation cùng incident/window, đủ lineage.
- [ ] Kiểm leakage, redaction và entity preservation đạt.
- [ ] Có truncation report và quyết định chọn trên dev.
- [ ] Một query version khóa trước test pooling; ablation chỉ trên dev.

## Risk Assessment

Duration/status semantics chưa xác minh phải giữ chú thích; metric/trace chỉ bổ trợ ngữ cảnh. Query template không đại diện hoàn toàn câu hỏi operator tự nhiên. Nếu clipping mất triệu chứng, sửa trên dev và version lại trước freeze. Raw và labels giữ riêng; chỉ chuyển bản đã review sang môi trường ngoài máy.
