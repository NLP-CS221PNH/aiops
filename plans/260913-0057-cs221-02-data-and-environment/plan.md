---
title: "02 — Dữ liệu và môi trường chạy"
description: "Tạo đầu vào suy luận tách nhãn, hợp đồng telemetry và môi trường tái lập cho 90 incident RE2-OB."
status: in-progress
priority: P1
effort: "24h"
tags: [docs, infra, experimental]
blockedBy: []
blocks: [260913-0057-cs221-03-knowledge-corpus, 260913-0057-cs221-04-incident-representation, 260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 02 — Dữ liệu và môi trường chạy

## Overview

Kế hoạch độc lập này chuyển dữ liệu đã thu thành đầu vào có hợp đồng cho corpus, representation và thực nghiệm. Không tải thêm dataset, không chạy mô hình trong đợt lập kế hoạch. Mọi file dưới `06_implementation` bên dưới là **đề xuất tạo khi triển khai**, hiện chưa tồn tại.

A phụ trách dữ liệu, B kiểm ranh giới và tái lập, C kiểm payload/môi trường; Codex thực hiện tooling và ghi bằng chứng. Tổng 24 giờ-người (6 + 12 + 6), là dự toán chưa đo. Điều chỉnh theo smoke thực tế, không đổi split để tiết kiệm.

## Hiện trạng đã đọc

- [Profile nguồn](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/profile-summary.json): 90 incident/30 families; train/dev/test 54/18/18; 35.333 ô metric null.
- [Inventory](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/acquired/inventory.tsv): 360 tệp, trong đó 270 telemetry Parquet và 90 injection files; inventory không phải payload inference.
- [Validation đã lưu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/dataset-validation.json): IDs/offsets/window pass trong đợt chuẩn bị, chưa thay thế kiểm hợp đồng mới.
- [Observations](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/observations.jsonl) vẫn mang family và split; cần allowlist mới trước serializer.
- [Reader nguồn](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-incidents.py:67) dùng retrospective window; chưa xác nhận duration/status semantics.
- [Môi trường dữ liệu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/requirements-data.txt) ghi Python 3.11.9 Windows x64, PyArrow 21.0.0; chưa có lock cho model/Kaggle.

## Phạm vi và quyết định

| Việc | Quyết định |
|---|---|
| Nguồn | Giữ nguyên pack, revision và 90 IDs; không chạy lại acquisition mặc định |
| Inference | Chỉ export observation/evidence đã redaction; không family/split/gold/source-case |
| Quản lý | Split, gold, lineage và source paths nhạy nhãn chỉ ở vùng audit/evaluator riêng |
| Môi trường | CPU local là gate bắt buộc; Kaggle là nhánh đo thực tế, không mặc định có GPU |
| API | Mặc định tắt; plan 01/07 xử lý quyền dùng mô hình và chi phí |
| Null/unknown | Giữ trạng thái và lý do; không impute hoặc suy status nonzero là lỗi |

## Kiến trúc và giao diện bàn giao

Nguồn immutable → validator/path allowlist → exporter → `data/inference` + manifest → plan 03/04/05/07. Audit mapping ở `data/private` chỉ cho kiểm toán/evaluator.

Đề xuất `configs/data.yaml` chứa schema version, source hashes, allowed roots/fields, time policy, redaction version, seed và API off. Manifest ghi row counts, file hashes, source revision, transform/config hash; không chứa source-case.

`incident-index.parquet` chỉ có incident_id, observation_start, observation_end_exclusive, evidence file IDs. Family/split không serialize vào record đưa tới model. Các hàm dự kiến: `validate_inputs`, `export_inference_data`, `build_environment_report`.

## Phases

| # | Phase | Giờ-người | Đầu ra | Status |
|---|---|---:|---|---|
| 1 | [Audit và khóa hợp đồng](./phase-01-start.md) | 6 | Census, time policy, allowlist | Pending |
| 2 | [Tạo export và môi trường](./phase-02-build.md) | 12 | Safe export, lock, smoke notebook | Pending |
| 3 | [Kiểm ranh giới và bàn giao](./phase-03-validate-and-handoff.md) | 6 | Failure tests, receipt, handoff | Pending |

## File inventory đề xuất

- Create: [configs/data.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/data.yaml) — hợp đồng nguồn/đầu vào.
- Create: [src/data/validate_inputs.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/validate_inputs.py), [export_inference_data.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/export_inference_data.py).
- Create: [data/inference/input-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/input-manifest.json) và incident index/evidence derivatives.
- Create: [data/private/data-audit.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/data-audit.json) — mapping riêng, không đóng gói model.
- Create: [data/private/split-map.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/split-map.tsv), [ground_truth.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/ground_truth.jsonl) — sidecars evaluator giữ source IDs/hash, không vào inference/demo.
- Create: [src/data/export_private_sidecars.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/export_private_sidecars.py) — management-only export, tách hàm suy luận.
- Create: [notebooks/00-environment-smoke.ipynb](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/notebooks/00-environment-smoke.ipynb), [configs/requirements-lock.txt](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/requirements-lock.txt).
- Create: [tests/test_data_boundary.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/tests/test_data_boundary.py), [reports/data-handoff.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/data-handoff.md).
- Modify/Delete nguồn: không có; các file nguồn được đọc, không ghi đè.

## Gate và xử lý chưa rõ

Plan 02 hoàn thành khi local export, kiểm ranh giới và môi trường CPU tái lập đạt; Kaggle/API chưa sẵn có được ghi deferred cùng owner, không giả đã chạy. Plan 03/04 chỉ bắt đầu triển khai sau toàn bộ gate 02 này.

Metric summary end hiện là giây mẫu cuối, bundle end là giây cuối +1. Đây là **yêu cầu audit và hòa giải semantics**, chưa phải kết luận dữ liệu bị lỗi. Giữ source nguyên, ghi rõ conversion ở derivative.

## Success Criteria

- [ ] 90 IDs, split nguồn và hashes đúng; không có family overlap.
- [ ] Inference export chỉ chứa allowlisted data và mọi evidence truy được nguồn.
- [ ] Timestamp/null/unit/alias policy được review; unknown giữ đúng trạng thái.
- [ ] Chèn labels/path sai/hash sai bị từ chối; hai smoke sạch có cùng output hash.
- [ ] Receipt môi trường/payload và hướng dẫn handoff đủ cho plan 03/04.

## Rủi ro

Wheel Windows không chuyển sang Linux/Kaggle; tạo môi trường tương thích mới. Regex privacy chỉ là lớp lọc, cần review payload thật. Thiếu GPU không ngăn CPU/data gate; quyền chia sẻ ngoài máy và API do con người xác nhận khi dùng. Không gọi synthetic template query là câu hỏi operator thật.
