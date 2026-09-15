---
phase: 1
title: "Khởi động, chốt phạm vi và phân công"
status: pending
priority: P1
effort: "12h"
dependencies: []
---

# Phase 01: Khởi động, chốt phạm vi và phân công

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 01](../260913-0057-cs221-01-scope-and-protocol/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Tuần 1, nhóm chốt phạm vi, tiêu chí chấm, phân công và các quyết định cần giảng viên xác nhận cho 8 tuần. C điều phối; A và B phản biện.

## Requirements

- Câu hỏi chính: hybrid retrieval có cải thiện truy hồi bằng chứng so với baseline mạnh hơn giữa BM25/dense được chọn trên dev, và cải thiện đó có chuyển thành chẩn đoán có căn cứ không?
- Giữ RE2–Online Boutique: 90 incidents, 30 families, split đề xuất 54/18/18. Duyệt split trước khi khóa; không chia các repetition cùng family sang nhiều tập.
- Ba người dùng Kaggle Free; DeepSeek V4.1 Flash là phương án generator chính có điều kiện giảng viên cho phép. Không mặc định API hay open weights được môn học chấp nhận.
- Ưu tiên thí nghiệm công bằng và kết luận trung thực; không đặt tiêu chí bắt buộc hybrid thắng, không cam kết giảm MTTR.

## Architecture

Phạm vi gồm observations → biểu diễn incident → BM25/dense/hybrid → reranker ablation → câu trả lời có dẫn chứng → đánh giá. A phụ trách dữ liệu/corpus; B phụ trách retrieval/thực nghiệm; C phụ trách RAG/tích hợp và biên tập. Cả ba cùng chấm dữ liệu theo phân công độc lập, bảo vệ phần mình và đọc chéo kết quả.

Nguồn: [START-HERE](../../START-HERE.md), [đề cương](../../00_plan/project_proposal.md), [thiết kế nghiên cứu](../../05_research/method-and-experiment-design.md).

## Related Code Files

Sản phẩm dự kiến khi triển khai:

- Tạo `06_implementation/docs/project-charter.md`: mục tiêu, đầu vào/đầu ra, tiêu chí môn học.
- Tạo `06_implementation/docs/decision-log.md`: quyết định, người chịu trách nhiệm, hạn chốt, bằng chứng.
- Tạo `06_implementation/docs/literature-matrix.tsv`: bài lõi, mức đọc, lựa chọn phương pháp được hỗ trợ.
- Tạo `06_implementation/docs/team-working-agreement.md`: phân công, lịch đồng bộ, quy tắc bàn giao.

## Implementation Steps

1. **Chốt đề cương — 2h:** đối chiếu rubric CS221, hạn nộp, yêu cầu báo cáo/demo và mức sử dụng mô hình có sẵn. Viết một đoạn nêu đóng góp NLP: biểu diễn log, retrieval và grounded generation; tách khỏi causal discovery.
2. **Phân công — 3h:** mỗi hạng mục có một owner và một người kiểm. Lập buổi đồng bộ ngắn hai lần mỗi tuần, kiểm sản phẩm cuối tuần; mọi đổi corpus, split, prompt và tiêu chí đánh giá phải có lý do ghi lại.
3. **Chọn tài liệu — 5h:** lấy 8–12 bài lõi từ danh mục đã có, phủ AIOps/benchmark, BM25–dense–RRF/reranking và đánh giá RAG. Mỗi người phụ trách một nhóm, đọc phần liên quan, ghi mức đọc thực tế cùng quyết định rút ra. Không lấy 1.009 bản ghi làm số bài đã đọc.
4. **Khóa nhánh mô hình — 2h:** chuẩn bị nội dung hỏi giảng viên trong tuần 1 về API, gửi observations đã khử định danh và việc dùng open weights. Nhóm chủ động xin phản hồi; hạn quyết định cuối tuần 2. Chưa được phép API thì chưa gửi dữ liệu.
5. Nếu API bị từ chối, chỉ chọn mô hình open weights nhỏ khoảng 1.5B–4B sau khi được phép và pilot xác nhận chạy vừa Kaggle. Nếu mọi LLM đều không được phép, thống nhất sửa tác vụ thành retrieval/extractive QA với giảng viên, cập nhật mục tiêu và rubric trước triển khai.

## Success Criteria

- [ ] Ba thành viên thống nhất phạm vi, owner và lịch 8 tuần.
- [ ] Có ma trận 8–12 bài lõi, mức đọc và liên hệ phương pháp.
- [ ] Yêu cầu môn học cùng quyết định mô hình có người theo dõi và hạn chốt.
- [ ] GraphRAG, fine-tuning, đa hệ thống và tự động khắc phục nằm ngoài MVP.

## Risk Assessment

Giảng viên phản hồi chậm: vẫn làm dữ liệu, corpus và retrieval trong tuần 1–2. Phân công rời rạc: yêu cầu người khác chạy lại sản phẩm bàn giao. Phạm vi quá lớn: hoàn thiện annotation và đối chứng trước mở rộng.
