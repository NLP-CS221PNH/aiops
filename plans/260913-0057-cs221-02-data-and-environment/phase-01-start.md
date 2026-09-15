---
phase: 1
title: "Audit nguồn và khóa hợp đồng đầu vào"
status: pending
priority: P1
effort: "6h"
dependencies: []
---

# Phase 1: Audit nguồn và khóa hợp đồng đầu vào

## Overview

Chuyển hiện trạng research pack thành hợp đồng có thể kiểm máy trước khi tạo derivative.
A chịu trách nhiệm nguồn; B review ranh giới; Codex lập census và cấu hình.
Dự toán 6 giờ-người chưa đo; đầu vào là protocol plan 01 và pack đã tải.
Phase này không xuất dữ liệu sang Kaggle/API và không chạy lại source pipeline.

## Requirements

- Giữ 90 incident IDs, revision và split 54/18/18; không bỏ ca thiếu giá trị.
- Có phân biệt immutable source, inference export và evaluator metadata.
- Schema allowlist là cơ chế chính; denylist chỉ bổ trợ bắt lỗi.
- Review nội dung bằng train; test chỉ census/schema/IDs/hash.
- Sai hash hoặc nguồn thiếu phải dừng gate, không tải revision khác để vượt kiểm.

## Architecture

Inventory nguồn → census/hash/schema → policy decision → `configs/data.yaml`.
Metadata label/split chỉ được validator offline/evaluator đọc trong vùng riêng.
Serializer model không nhận nguyên hàng observation hoặc acquisition inventory.
Public service names xuất hiện trong telemetry vẫn là observation hợp lệ.
Family ID tuy opaque vẫn mã hóa nhóm service×fault nên không serialize.
Source reader hiện giữ metric end và bundle end theo hai conventions cần reconcile.
Conversion derivative phải lưu rule/version, không đổi source timestamps.
UTC seconds/milliseconds được kiểm bằng giá trị thực và schema, không dựa tên cột đơn lẻ.

## Related Code Files

- Existing/read: [inventory.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/acquired/inventory.tsv) — chứa cả observation và label rows.
- Existing/read: [observations.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/observations.jsonl).
- Existing/read: [split-map.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/split-map.tsv) — chỉ quản lý/evaluator.
- Existing/read: [profile-summary.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/profile-summary.json).
- Existing/read: [prepare-incidents.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/scripts/prepare-incidents.py:67) — hiểu selection/window, không sửa.
- Proposed/create: [configs/data.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/data.yaml).
- Proposed/create: [data/private/source-census.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/source-census.json).
- Proposed/create: [reports/data-contract-review.md](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/data-contract-review.md).

## Implementation Steps

### D02-01 — Census nguồn và checksum (2h)

- Input → inventory, manifests, validation cũ và protocol.
- Action → Codex đọc metadata, đếm IDs/files/schema và kiểm hash nguồn chọn; A review provenance, B kiểm mẫu.
- Output → source-census.json có counts/revision/size/hash và bảng allowed versus private.
- Prerequisite → plan 01 xác nhận RE2-OB là nguồn MVP; nguồn local truy cập được.
- Acceptance → 90 IDs; 270 telemetry +90 label files; mỗi loại có vai trò rõ; không gọi inventory là safe export.
- Failure path → thiếu/sai file thì ghi incident/file ID và dừng export; kiểm bản gốc trước quyết định phục hồi.

### D02-02 — Hợp đồng timestamps, null và alias (2h)

- Input → schema/profile + sáu train incidents do split admin chọn.
- Action → Codex đối chiếu source row/window; A xác nhận convention, B review last-second boundary và unknown units.
- Output → phần time/null/alias trong data.yaml và decision table có evidence path.
- Prerequisite → D02-01 pass; sample IDs thuộc train đã xác nhận.
- Acceptance → metric/log epoch seconds; trace milliseconds; half-open window explicit; null giữ nguyên; alias cần bằng chứng.
- Failure path → semantics chưa rõ giữ unknown và source value; không convert duration hoặc sửa data source bằng suy đoán.

### D02-03 — Allowlist và phân quyền dữ liệu (2h)

- Input → census, observation/evidence schemas và execution contract.
- Action → Codex liệt kê fields/roots được phép; A duyệt data role, C review payload boundary.
- Output → schema inference, schema private audit, error codes và review receipt dự kiến.
- Prerequisite → D02-01 và D02-02 đã có decision.
- Acceptance → family/split/source-case/fault/injection/gold không có trong inference schema; root path chuẩn hóa được.
- Failure path → trường chưa phân loại mặc định không export; bổ sung lý do thay vì wildcard toàn record.

## Interface và schema dự kiến

| Record | Fields bắt buộc | Quy tắc |
|---|---|---|
| Incident index | incident_id, observation_start, observation_end_exclusive, evidence_file_ids | ID opaque, UTC, không split/family |
| Evidence | evidence_id, incident_id, modality, source_file_id, row/span, content | Join cùng incident, source IDs opaque |
| Time policy | source_unit, boundary_kind, conversion_version | Giữ source sample range riêng nếu inclusive |
| Source census | revision, counts, schema_hashes, file_hashes | Chỉ audit riêng; có thể tham chiếu labels |
| Private split-map | incident_id, scenario_family_id, split, split_version | Giữ đủ 90 source IDs và mapping; manager/evaluator-only |
| Private ground_truth | incident_id, source service/fault labels, label provenance | Copy source byte-preserving và hash; không thuộc inference export |
| Data config | schema_version, allowed_fields, allowed_roots, redaction_version | Không credential; api_enabled=false |
| Alias review | raw_name, canonical_name, evidence, state | state unknown không hợp nhất tự động |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| DC-01 | Inventory có injection path | Phân loại private, không xuất model manifest |
| DC-02 | Observation có family/split | Whitelist loại ở serializer; admin map giữ riêng |
| DC-03 | Metric summary end khác bundle +1s | Ghi convention/conversion; chưa kết luận lỗi nguồn |
| DC-04 | Trace ngay end_exclusive | Bị loại khỏi window; last valid millisecond vẫn nằm trong |
| DC-05 | Metric null/all-null series | Giữ null/missing; không tạo số 0 ngầm |
| DC-06 | frontend và frontendservice | Chỉ merge sau bằng chứng; giữ raw names |
| DC-07 | Nhãn fault đổi, telemetry không đổi | Contract inference không thay theo nhãn |

## Bàn giao cho phase 2

D02-03 cung cấp allowlist để viết exporter; D02-02 cung cấp unit/window contracts.
B ký review nghiệp vụ dữ liệu, Codex ghi status thật; không tự ký thay B.
C nhận lỗi policy/API còn mở và có thể chuẩn bị checklist offline.
Nếu hardware chưa rõ, phase 2 bắt đầu bằng local CPU.

## Success Criteria

- [ ] Census có 90 IDs và phân biệt observation/label files.
- [ ] Time semantics issue có decision hoặc unknown có hạn chế sử dụng.
- [ ] Inference schema không chứa quản lý family/split hoặc source-case.
- [ ] A/B đã review phần dữ liệu được gán cho con người.
- [ ] Phase 2 có input contract version rõ.

## Risk Assessment

Validation cũ không kiểm inference serialization nên không dùng nó thay gate mới.
Case path và private mapping có thể lọt qua nested JSON; schema phải kiểm recursive.
Tất cả estimate là công lập kế hoạch; sáu train cases là mẫu audit, không kết luận đủ coverage.
