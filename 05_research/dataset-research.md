# Nghiên cứu và bàn giao dữ liệu RCAEval

Đã thu đủ **90/90 ca RE2-Online Boutique**, 360 file gốc (270 Parquet telemetry và 90 file injection được tách vào labels), **922,484,805 bytes**. Ba modality đều hiện diện trong cả 90 ca. Đây là toàn bộ subset MVP mà plan chọn, không phải chỉ một sample; 102 mục catalog là registry nhiều vai trò, không phải yêu cầu tải 102 dataset.

## Bằng chứng và phiên bản

- [HF dataset revision](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e) được ghim; index gồm 735 ca toàn benchmark, không cộng mirror thành mẫu độc lập.
- [README và phạm vi license của tác giả](https://github.com/phamquiluan/RCAEval/blob/bb48c5aa9a24f1d5fcc716bdd479ea2d63145c90/README.md#licensing) xác nhận MIT cho dữ liệu tác giả. Bản license và SHA256 lưu tại `02_datasets/acquired/meta/`.
- 270 Parquet tải có SHA256 khớp LFS của revision; `cases.parquet` khớp SHA256 `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb`. File injection nhỏ có checksum local và URL ghim revision.
- Đã tải một ca trước, đọc schema thụ động, rồi mới tải đủ 90 ca. Không chạy loader, notebook, fault injection hay pickle từ nguồn.

## Dữ liệu thực đã kiểm

| Đại lượng | Giá trị |
|---|---:|
| Incident / scenario families | 90 / 30 |
| Train / dev / test | 54 / 18 / 18 |
| Metric timesteps | 128,742 |
| Log rows | 15,053,223 |
| Trace spans | 34,461,235 |
| Log evidence / metric summaries / trace evidence | 1770 / 6603 / 1260 |

Khoảng telemetry thực từ 2024-01-15T17:30:22+00:00 tới 2024-02-21T04:31:01+00:00. Log `timestamp` và metric `time` là epoch giây; trace dùng `startTimeMillis`. Không dùng chuỗi `HH:MM` thiếu ngày/timezone. Đơn vị duration được ghi rõ là microsecond suy từ schema kiểu Jaeger, chưa được xác nhận độc lập.

Số metric timesteps mỗi ca từ 930 tới 1441; metric columns từ 69 tới 77. Có 35,333 ô metric null, được giữ nguyên trong raw, thống kê mô tả bỏ qua null và không tự impute. Cả 90 chuỗi metric đơn điệu theo thời gian, không có timestamp trùng. Observation window là khoảng nửa mở từ giây metric đầu đến giây metric cuối cộng 1 giây, để giữ trọn giây cuối khi nối trace millisecond. `statusCode` trace được giữ nguyên, chưa đồng nhất nonzero với lỗi.

Split đóng băng theo service×fault family; mỗi fault có 3 family train, 1 dev, 1 test, các repetition giữ cùng split. Root-service/fault/injection chỉ dùng tạo labels và group split. Hàm sinh observations chỉ nhận opaque ID cùng telemetry, không đọc gold hoặc tên case gốc.

## Cách sử dụng

- Input được phép: `processed/observations.jsonl`, `logs-evidence.jsonl`, `metric-summaries.jsonl`, `trace-evidence.jsonl`. Citation ID dẫn đến row offset trong file telemetry gốc có opaque ID.
- Gold riêng: `processed/labels/ground_truth.jsonl`. Lineage chứa case name gốc ở `processed/labels/lineage.jsonl`; manifest nguồn có đường dẫn gold ở `acquired/labels/`. Không đưa các nhánh này vào prompt/index.
- Raw telemetry đầy đủ ở `acquired/raw/inc_*/`. Giữ nguyên byte gốc để tái lập. Chỉ bản trích xuất đưa vào model đã khử email/IP và các pattern credential; không gửi raw lên dịch vụ bên ngoài chưa qua xử lý.
- `split-map.tsv`, `incident-profiles.jsonl`, `profile-summary.json`, `acquired/inventory.tsv` cung cấp khóa, thống kê, checksum và vị trí dữ liệu.

Query là template suy từ quan sát đã ghi `is_synthetic=true`, không giả làm query do operator viết. Window dùng toàn bộ metric timeframe từng ca, không lấy injection làm tín hiệu đầu vào. Đây là đánh giá offline hồi cứu; KB hiện tại không chứng minh mô phỏng triage trực tuyến năm 2024.

## Reserve và registry

RE2-TT giữ metadata của 90 ca, chưa tải 1,965,747,924 bytes telemetry. Một ca không có logs; [known-data notes của tác giả](https://huggingface.co/datasets/phamquiluan/RCAEval/blob/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e/README.md#known-data-notes) xác nhận 89/90 có logs. Trước test khác hệ thống, chọn rõ missing-modality policy; không âm thầm loại ca.

`02_datasets/catalog-review.tsv` và JSONL audit cả 102 dòng: existence card, parent link, role, license gate, collection decision. Không tuyên bố 102 nguồn được reverify live. RCAEval release và P1 OpenRCA, Loghub, Loghub-2.0, MultiHop-RAG, RAGTruth có primary snapshots; LEMMA website được đọc lại, mâu thuẫn quyền vẫn giữ. Các nguồn thay thế và KB có nghiên cứu riêng của gói.

[Loghub](https://github.com/logpai/loghub) và [Loghub-2.0](https://github.com/logpai/loghub-2.0) dành cho research/academic với nghĩa vụ ghi nguồn; giữ làm lựa chọn parsing. [OpenRCA](https://github.com/microsoft/OpenRCA) có MIT repository nhưng chưa đủ bằng chứng quyền raw trên Drive. [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) ghi ODC-BY ở README, dùng tham khảo qrels khác miền; [RAGTruth](https://github.com/ParticleMedia/RAGTruth) dùng tham khảo rubric hallucination, không quy đổi score thành RCA.

## Phần chưa thể coi là hoàn thành

Qrels incident→runbook, độ phủ bằng chứng và human review còn `unjudged`; không có annotation của người hay kết quả benchmark bị bịa. Selected HF index có service/fault/injection gold, không chứa root-cause-indicator riêng cho RE2-OB. Chưa có deployment version của các ca để xác nhận runbook hiện tại tương thích. Regex privacy là kiểm tra có giới hạn, không chứng nhận raw logs sạch mọi PII/secret. Các hạn chế này quyết định những claim thí nghiệm được phép nêu.
