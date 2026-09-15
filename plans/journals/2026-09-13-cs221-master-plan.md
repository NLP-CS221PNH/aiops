---
title: cs221-master-plan
date: 2026-09-13
summary: Master plan 8 tuần và 10 phase cho nhóm 3 người
---

# cs221-master-plan

# Nhật ký lập master plan CS221

## Diễn biến
Đọc bộ nghiên cứu hiện có, xác nhận 90 incidents và chưa có human qrels. Nhóm xác nhận 8 tuần, 3 người, Kaggle free và DeepSeek V4.1 Flash nếu giảng viên cho phép. Tạo master plan, 10 phase, danh mục và căn cứ nghiên cứu có nguồn; review chéo dữ liệu, thí nghiệm và tài nguyên.

## Quyết định
Giữ ba retrievers bắt buộc, rerank tùy chọn, 56 core qrels chấm đôi và đủ 18 test. Passage nDCG@5 là primary; F1 khóa hệ thống trước test pooling, F2 khóa qrels trước scoring. Test chỉ sáu family. Cache API tách đợt vì alias có thể đổi model.

## Bước tiếp
Nhóm đọc master và phase01/02, chốt rubric/quyền model, audit train và đo pilot annotation. Chưa triển khai, chưa gọi API trả phí, chưa tạo nhãn người.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
