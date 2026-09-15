---
phase: 2
title: "Dữ liệu và môi trường chạy"
status: pending
priority: P1
effort: "24h"
dependencies: [1]
---

# Phase 02: Dữ liệu và môi trường chạy

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 02](../260913-0057-cs221-02-data-and-environment/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Tuần 1–2, người phụ trách dữ liệu tổ chức lại đầu vào cho thí nghiệm; một thành viên kiểm tra chéo. Ngân sách 24 giờ-người gồm 6 giờ kiểm dữ liệu, 8 giờ môi trường, 6 giờ hợp đồng đầu vào và 4 giờ kiểm thử. Toàn bộ sản phẩm dưới đây là việc sẽ triển khai.

## Requirements

Tái sử dụng đủ 90 incident RE2-OB đã tải; giữ nguyên research pack. Split hiện có là 54/18/18 incident, tương ứng 18/6/6 families. Không tải thêm dataset trong MVP. Notebook chạy được trên Kaggle miễn phí; tài nguyên thực tế phải đo, không giả định GPU hoặc quota luôn sẵn. API DeepSeek chỉ được bật sau khi giảng viên cho phép và xác minh tên model khả dụng.

## Architecture

Nguồn đóng băng → kiểm hash/schema → bảng incident theo ID mờ → bộ đầu vào được phép → notebook và pipeline. Gold chỉ nối vào evaluator bằng incident ID; không thuộc input của retrieval/generation. Các ví dụ kiểm thử dùng train; test chỉ kiểm cấu trúc và tính toàn vẹn.

## Related Code Files

Đọc `02_datasets/acquired/inventory.tsv`, `02_datasets/processed/{observations.jsonl,split-map.tsv,incident-profiles.jsonl,dataset-validation.json}` và ba file evidence. Tham khảo `scripts/prepare-incidents.py`, `scripts/validate-research-pack.py`; không sửa các file nguồn này.

Tạo dưới `06_implementation/`: `configs/{runtime.yaml,data-contract.yaml}`, `data/{incident-index.parquet,input-manifest.json,service-aliases.yaml}`, `notebooks/00-environment-smoke.ipynb`, `src/data/validate_inputs.py`, `tests/test_data_boundary.py`, `reports/environment-check.json`. Dependency lock lưu tại `configs/requirements-lock.txt`.

## Implementation Steps

1. **Lập inventory được phép.** Ghi SHA256, kích thước, source revision, schema và số bản ghi. Tạo incident-index cho inference chỉ chứa ID mờ, observation window và đường dẫn evidence được phép. Family/split nằm trong bảng quản lý evaluator riêng; family có thể mã hóa service×fault nên không serialize vào query/prompt. Không sao chép source-case, fault hoặc injection vào input. Source labels chỉ được khai báo trong cấu hình evaluator riêng.
2. **Chốt hợp đồng telemetry.** Giữ epoch giây cho logs/metrics và millisecond cho trace start; window nửa mở. Không impute 35.333 ô metric null mặc định. Duration/statusCode chưa xác nhận phải mang trạng thái unknown; không đổi nonzero thành error. Alias `frontend/frontendservice`, `redis/redis-cart` chỉ hợp nhất khi có bằng chứng, lưu cả tên gốc.
3. **Đóng gói môi trường nhẹ.** Ghim phiên bản Python và thư viện đã chạy smoke; ghi OS, CPU/GPU, RAM/VRAM, seed. Một notebook đọc 2 train incidents, kiểm schema, xuất kết quả rồi chạy lại từ phiên sạch. Chia notebook chuẩn bị dữ liệu khỏi notebook model để tránh đọc lại hàng chục triệu dòng khi GPU được cấp.
4. **Chuẩn bị Kaggle.** Chỉ đưa derivatives cần thiết đã kiểm redaction vào dataset riêng tư; giữ raw tại máy. Không nhúng key vào notebook/output. Cache embeddings và checkpoint theo corpus/model/config hash; xuất artifact sau mỗi batch. Nếu thiếu GPU, vẫn chạy CPU cho validation/BM25 và giảm batch dense; không tự đổi model sau freeze.
5. **Kiểm đường ra ngoài.** Duyệt payload thực tế cho email/IP, credential và identifier có thể liên kết; lưu redaction version. API mặc định tắt. Khi được phép, ghi model ID thật, ngày xác minh, giới hạn tiền/token và receipt cấu hình; không lưu secret. Giá và khả năng dùng được kiểm lại lúc chạy.
6. **Kiểm thử ranh giới.** Thử đưa `labels/`, source-case hoặc injection vào input: validator phải từ chối. Kiểm đủ 90 ID, zero family overlap, timestamp/offset hợp lệ, file thiếu và hash sai. Đối chiếu hai lần chạy smoke cho cùng tập ID và hash dữ liệu đầu ra.

## Success Criteria

- [ ] Notebook mới chạy thành công; môi trường và mức tài nguyên thực có biên bản.
- [ ] Đủ 90 incidents; giữ nguyên split; mọi evidence ID truy được nguồn.
- [ ] Các thử nghiệm cố đưa gold hoặc file sai hash đều thất bại rõ ràng.
- [ ] Payload được phép và policy API được ghi; không có key trong artifact.

## Risk Assessment

Hash sai hoặc timestamp không hợp lệ: dừng incident liên quan, đối chiếu raw và ghi quyết định; không tự loại sau xem điểm. Kaggle hết tài nguyên: tiếp tục CPU/cached artifacts, báo ảnh hưởng lịch. Version hoặc alias chưa biết: giữ unknown và hạn chế diễn giải; không suy từ tên gần giống. Chưa được phép API: dùng nhánh local đã chọn tại phase 01.
