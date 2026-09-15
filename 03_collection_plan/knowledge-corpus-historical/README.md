# Historical knowledge snapshot trước 2024

Snapshot `cs221-knowledge-pre2024-v1` gồm **74 tài liệu, 580 chunks, 12 supporting assets, 83 proposed mappings chưa được người chấm xác nhận**. Đây là ứng viên corpus chính cho RE2-OB theo chính sách thời gian của plan. Đã kiểm toàn bộ 90 observation windows: mọi ngày snapshot đều trước observation start; mốc sớm nhất là 2024-01-15T17:30:22Z. Chưa xác nhận deployment version hoặc evidence coverage; trước đánh giá phải chấm applicability. Nếu đổi dữ liệu/cutoff, phải kiểm lại thời gian.

| Nguồn | Tài liệu | Commit | Thời điểm snapshot UTC | Giấy phép |
|---|---:|---|---|---|
| Online Boutique | 25 | `80bea9bfd97bec107361d4663e207aa8d3f312c6` | 2023-12-28T18:03:44Z | Apache-2.0 |
| Kubernetes website | 14 | `7e631d0318dc279cb2d31231d8823360e61e9304` | 2023-12-31T15:40:05Z | CC-BY-4.0 |
| Prometheus runbooks | 35 | `f8061f3e9b3337d90107aa2f10a0111f3f6dc86f` | 2023-09-07T14:21:57Z | Apache-2.0 |

Toàn bộ file được tải trực tiếp tại commit lịch sử; không dùng file 2026 lấp vào snapshot. So với corpus current: 73 paths chung, trong đó 41 text không đổi và 32 text đã đổi; historical có thêm `kubernetes-manifests/redis.yaml`. Không có selected path của current bị thiếu trong các historical trees. Diff và policy lưu trong `comparison-with-current.json`.

Document/chunk schema giống corpus current. Prefix `KBH` giúp phân biệt citation IDs với `KB` current; không trộn hai snapshot trong một index như hai nguồn độc lập. `available_at` là ngày commit toàn snapshot, `published_at`/`updated_at` riêng trang chưa biết, `retrieved_at` là ngày acquisition. Hash và số lượng chính thức ở `snapshot.json`.

Raw source, LICENSE, commit metadata, repository-tree và receipts nằm trong `raw/source-snapshots/`. Nguồn Markdown giữ Hugo directives; 11 fragment/include của Kubernetes và sơ đồ OB được lưu riêng, không render hoặc thực thi. Token count thực chưa tính; chars/4 chỉ là ước lượng.

Attribution: Google LLC và Online Boutique contributors; The Kubernetes Authors và website contributors; Prometheus Operator runbooks contributors. Raw giữ nguyên; document text decode UTF-8/BOM, chuẩn hóa newline; chunks là derivatives dạng lát cắt. Giữ source URL, commit, attribution, LICENSE và change notice khi chia sẻ. Không suy quyền với tài liệu bên ngoài hoặc trademarks.

Nguồn ghim: [OB README](https://github.com/GoogleCloudPlatform/microservices-demo/blob/80bea9bfd97bec107361d4663e207aa8d3f312c6/README.md), [OB LICENSE](https://github.com/GoogleCloudPlatform/microservices-demo/blob/80bea9bfd97bec107361d4663e207aa8d3f312c6/LICENSE), [K8s resource management](https://github.com/kubernetes/website/blob/7e631d0318dc279cb2d31231d8823360e61e9304/content/en/docs/concepts/configuration/manage-resources-containers.md), [K8s LICENSE](https://github.com/kubernetes/website/blob/7e631d0318dc279cb2d31231d8823360e61e9304/LICENSE), [CPUThrottlingHigh](https://github.com/prometheus-operator/runbooks/blob/f8061f3e9b3337d90107aa2f10a0111f3f6dc86f/content/runbooks/kubernetes/CPUThrottlingHigh.md), [Runbooks LICENSE](https://github.com/prometheus-operator/runbooks/blob/f8061f3e9b3337d90107aa2f10a0111f3f6dc86f/LICENSE).
