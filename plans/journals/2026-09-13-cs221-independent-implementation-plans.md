---
title: CS221 independent implementation plans
date: 2026-09-13
summary: "Tách mười hạng mục master thành mười kế hoạch độc lập, giữ gates và human boundaries."
---

# CS221 independent implementation plans

## Context

Đọc master CS221 gồm mười hạng mục và yêu cầu tách mỗi mục thành plan độc lập. Scope giữ tám tuần, ba người; đây là đợt lập kế hoạch, không chạy implementation.

## What happened

Audit đọc nguồn/artifacts phát hiện inference cần allowlist, corpus token counts chưa có và query selection có nguy cơ thiên lệch theo service. Các validators cũ thuộc gói chuẩn bị, không dùng chứng nhận thí nghiệm. Tạo mười thư mục plan qua AgentKit, mỗi plan ba phase; thêm nghiên cứu và contracts dùng chung. Master/legacy phases được nối sang plan mới.

## Decision

04 bàn giao variants, 05 bàn giao runners, 07 bàn giao adapter/pilot; 08 sở hữu dev selection/F1/final runs; 06 sở hữu human labels/F2. Test query/bundle được materialize riêng sau F1, không sửa train/dev files đã khóa. Không tự chấm thay người hoặc coi API đã được giảng viên cho phép. Index AgentKit lưu trong workspace do index toàn cục không ghi được; Markdown là nguồn chính.

## Next

Đã đọc chéo và kiểm links/dependencies/efforts; đủ 10 plan/30 phase, mọi implementation checkbox giữ pending. AgentKit validate cả 10 plan mới và master đạt. Báo cáo nghiệm thu kế hoạch tại plans/reports/260913-independent-plans-review.md. Triển khai sau này bắt đầu bằng một plan hoặc milestone đủ đầu vào, ưu tiên 01 và local audit của 02.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
