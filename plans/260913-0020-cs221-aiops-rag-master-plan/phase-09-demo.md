---
phase: 9
title: "Demo hỗ trợ điều tra với bằng chứng kiểm tra được"
status: pending
priority: P2
effort: "12h"
dependencies: [7, 8]
---

# Phase 09: Demo hỗ trợ điều tra với bằng chứng kiểm tra được

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 09](../260913-0057-cs221-09-evidence-demo/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

C dựng khung demo cục bộ tuần 4–5 khi 07A ổn định, chốt nội dung tuần 7 sau 08. A kiểm bằng chứng, B đối chiếu bảng thí nghiệm. Dependency 08 chỉ chặn bộ kết quả demo cuối; không chặn xây khung. Tổng effort vẫn 12h.

## Requirements

- Chọn incident bằng ID opaque, xem observations và cấu hình retrieval, nhận danh sách nghi vấn cùng căn cứ. Không hiện gold trước câu trả lời.
- Hai chế độ được ghi rõ: “Kết quả đã lưu” lấy đúng run đã khóa; “Chạy trực tiếp” gọi pipeline khi môi trường và quyền API cho phép. Không trình bày cache như kết quả vừa sinh.
- Có ví dụ thành công, chẩn đoán yếu/sai, thiếu bằng chứng và citation không hợp lệ. Demo không thay thế kết quả toàn bộ 18 test incidents.
- Mỗi citation mở đúng đoạn trong snapshot corpus hoặc observations; hiển thị nguồn, phiên bản và phần hỗ trợ. Không để mô hình tự tạo URL.
- Chạy trên máy nhóm; ưu tiên trang đơn giản hoặc notebook rõ ràng. Không cần tài khoản người dùng, triển khai cloud hay hệ thống production trong MVP.

## Architecture

Ba vùng: hồ sơ sự cố; evidence truy hồi; chẩn đoán và điều còn thiếu. Chọn claim làm nổi đoạn được dẫn. Hiện trạng thái trả lời/từ chối/lỗi, thời điểm, chế độ cache/live và độ trễ.

Demo đọc manifest và outputs của phase 08 bằng cùng loader với báo cáo. Chế độ live dùng adapter của phase 07 và giữ khóa API ngoài phía trình duyệt. Dữ liệu minh họa là bản đã khử định danh; raw giữ trong khu vực nghiên cứu.

## Related Code Files

Sản phẩm dự kiến:

- `06_implementation/src/demo/app.py`: giao diện cục bộ tối thiểu.
- `06_implementation/configs/demo-cases.yaml`: incident IDs, mục đích chọn, run IDs.
- `06_implementation/docs/demo-script.md`: kịch bản trình bày và phương án mất mạng.
- `06_implementation/reports/demo/`: ảnh/chứng cứ trình diễn và mẫu lỗi có nhãn rõ.

## Implementation Steps

1. **Chọn kịch bản — 2h:** dùng taxonomy lỗi đã định trước ở phase 08 để chọn các ca minh họa. Ghi lý do chọn; chọn ca yếu và thiếu evidence bên cạnh ca thành công. Nếu không có lỗi citation trong runs thật, dùng fixture kiểm validator có nhãn “mẫu kiểm thử”, không nhập vào số liệu.
2. **Làm luồng xem — 4h:** nối selector incident, cấu hình và evidence tới output đã lưu. Giữ câu trả lời gốc; hiển thị phản hồi không hợp lệ bằng trạng thái lỗi. Thêm bảng đối chiếu hai cấu hình trên cùng incident, cùng observations khi cần giải thích khác biệt retrieval.
3. **Thêm live — 2h:** chỉ nối khi API/mô hình sẵn sàng; hiện chờ, timeout và lỗi. Sau thất bại, người trình bày có thể chủ động chuyển sang cache có nhãn. Không tự thay bằng một output đẹp từ cấu hình khác.
4. **Tổng duyệt — 4h:** người khác mở từ hướng dẫn, kiểm citation tới đúng span, mất mạng, từ chối và citation sai. Tập trình bày 5–7 phút, giải thích bằng chứng và giới hạn. Lưu ảnh/bản ghi dự phòng.

## Success Criteria

- [ ] Thành viên khác mở được demo và kiểm một claim tới nguồn.
- [ ] Có đủ nhóm ví dụ; fixture và kết quả nghiên cứu phân biệt rõ.
- [ ] Cache/live, failure và abstention hiển thị đúng thực tế.
- [ ] Các số liệu demo khớp outputs đã khóa; không bổ sung metric từ ca chọn tay.

## Risk Assessment

Thiếu mạng/GPU: chuẩn bị cache và hướng dẫn offline. Giao diện tốn thời gian: giới hạn incident, evidence và output trong 12h. Tránh ngộ nhận quan hệ nhân quả: dùng nhãn “nghi vấn cần kiểm tra”, nêu hạn chế injection labels và dữ liệu hồi cứu.
