# Knowledge corpus đã thu thập

Snapshot `cs221-knowledge-2026-09-12-v1` gồm **73 tài liệu, 598 chunks, 15 supporting assets**, và **82 mapping candidates chưa được người chấm xác nhận**. Đây là tập tài liệu có phạm vi đã chọn từ ba nguồn, không phải bản mirror toàn bộ website/repository.

| Nguồn | Tài liệu | Commit | Thời điểm commit snapshot UTC | Giấy phép lưu kèm |
|---|---:|---|---|---|
| Online Boutique | 24 | `b9a978db9e01f4ad3dca9494a22cb9edc17548fe` | 2026-09-03T21:10:06Z | Apache-2.0 |
| Kubernetes website | 14 | `76a0e90f253e924a7b55f01f92a37555bd89be68` | 2026-09-12T03:59:12Z | CC-BY-4.0 |
| Prometheus Operator runbooks | 35 | `a685d14cf5128bb30e2bf935c3983decd772d885` | 2024-10-03T13:27:07Z | Apache-2.0 |

`documents.jsonl` chứa text nguồn đã chuẩn hóa newline, source URL ghim commit, license, hash và metadata. `chunks.jsonl` giữ text cùng offsets [start,end) theo Unicode codepoint của document. `token_count=null`; `token_estimate_chars_div_4` chỉ là ước lượng, cần tính lại bằng tokenizer thật khi chốt context budget. Chunks tách theo heading rồi window tối đa 2.400 ký tự, overlap 240 ký tự khi phải chia section dài.

`raw/source-snapshots/<source_id>/files/` giữ nguyên bytes tải về. Root của mỗi nguồn giữ LICENSE, commit API metadata, repository-tree và receipt URL/timestamp/SHA-256. `supporting-assets.jsonl` ghi 14 fragment/include YAML của Kubernetes và sơ đồ kiến trúc Online Boutique. Các fragment được lưu riêng, chưa render thay thế vào Markdown; không thực thi lệnh, YAML hay code nguồn. Liên kết website bên ngoài và các trang ngoài phạm vi chọn không được mirror tự động.

`source-manifest.jsonl` ghi giấy phép và phạm vi. `snapshot.json` ghi counts/hash, kiểm tra offsets và trạng thái chưa chấm. `proposed-mappings.tsv/jsonl` chỉ gợi ý theo service/path/title, không chứa gold. Không đưa các bảng annotation/mapping vào text index như chứng cứ.

**Chính sách thời gian:** snapshot này dùng cho offline assistance. `available_at` là thời điểm tồn tại bảo thủ của commit snapshot; `published_at` và `updated_at` của riêng tài liệu chưa biết nên để null. `retrieved_at` chỉ ghi lúc acquisition. Tài liệu 2024–2026 không được dùng để tuyên bố mô phỏng triage incident xảy ra trước đó. Historical evaluation cần dùng corpus historical riêng, so cutoff từng incident, và xác nhận deployment/version.

**Attribution và thay đổi:** Online Boutique thuộc Google LLC và các contributors; Kubernetes documentation thuộc The Kubernetes Authors và contributors; Prometheus Operator runbooks thuộc các contributors tương ứng. Giữ source URL, commit, attribution, LICENSE và change notice khi sử dụng/phân phối các bản sao và chunks. Raw giữ nguyên; document text chỉ decode UTF-8, bỏ BOM nếu có, chuẩn hóa newline; chunks là lát cắt dẫn xuất. Không suy quyền đối với nhãn hiệu hoặc nội dung ở website ngoài chỉ vì nó được link trong tài liệu.

Giấy phép gốc: [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo/blob/b9a978db9e01f4ad3dca9494a22cb9edc17548fe/LICENSE), [Kubernetes website](https://github.com/kubernetes/website/blob/76a0e90f253e924a7b55f01f92a37555bd89be68/LICENSE), [Prometheus runbooks](https://github.com/prometheus-operator/runbooks/blob/a685d14cf5128bb30e2bf935c3983decd772d885/LICENSE).
