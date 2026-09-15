---
phase: 2
title: "Tạo safe export và môi trường tái lập"
status: pending
priority: P1
effort: "12h"
dependencies: [1]
---

# Phase 2: Tạo safe export và môi trường tái lập

## Overview

Xây derivative inference, validator và notebook smoke theo hợp đồng phase 1.
Codex triển khai; A sở hữu dữ liệu, B review code boundary, C review runtime/payload.
Dự toán 12 giờ-người chưa đo; không chạy embeddings/generator trong phase này.
Kaggle receipt là kết quả đo hoặc trạng thái deferred thật, không giả GPU đã sẵn.

## Requirements

- Source files không ghi đè; không gọi source prepare script để tạo input production.
- Export chỉ đọc whitelist, kiểm hash và có output riêng cho inference/private.
- Không giữ raw telemetry hoặc keys trong notebook output.
- Hai train incidents đủ cho smoke; không reload hàng chục triệu traces mỗi lần thử.
- Môi trường sạch cần versions thật; không copy Windows wheel sang Linux.
- Token/model packages chỉ thêm khi downstream chọn revision và có nhu cầu.

## Architecture

`validate_inputs` → `export_inference_data` → stable sorted JSONL/Parquet → manifest.
Manifest checksum nội dung dùng ordering cố định và JSON số hữu hạn.
Artifact metadata ghi created_at riêng; không đưa thời gian hiện tại vào content hash cần tái lập.
Audit map nằm ở data/private; serializer và packaging không được glob cả data/.
Management-only export_private_sidecars sao chép split-map.tsv và ground_truth.jsonl từ nguồn đã kiểm, giữ nguyên bytes/hash/90 IDs; inference exporter không đọc hai sidecars.
Notebook load index/evidence derivatives; raw row resolution chỉ dùng cho local audit.
Lock được tạo từ môi trường đã chạy, kèm OS/Python/ABI.
Cache key dự kiến là source_hash + transform_hash + config_hash.
Embedding/model caches thuộc plan 05/07 và thêm model/corpus hash tương ứng.

## Related Code Files

- Existing/read: [logs-evidence.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/logs-evidence.jsonl), [metric-summaries.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/metric-summaries.jsonl).
- Existing/read: [trace-evidence.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/02_datasets/processed/trace-evidence.jsonl).
- Proposed/create: [validate_inputs.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/validate_inputs.py).
- Proposed/create: [export_inference_data.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/export_inference_data.py).
- Proposed/create: [incident-index.parquet](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/incident-index.parquet).
- Proposed/create: [observations.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/observations.jsonl) và evidence derivatives.
- Proposed/create: [input-manifest.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/input-manifest.json).
- Proposed/create: [data-audit.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/data-audit.json).
- Proposed/create: [split-map.tsv](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/split-map.tsv), [ground_truth.jsonl](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/private/ground_truth.jsonl) — audit/evaluator-only.
- Proposed/create: [export_private_sidecars.py](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/data/export_private_sidecars.py) — tách source labels khỏi inference code path.
- Proposed/create: [00-environment-smoke.ipynb](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/notebooks/00-environment-smoke.ipynb).
- Proposed/create: [requirements-lock.txt](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/requirements-lock.txt), [runtime.yaml](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/runtime.yaml).
- Proposed/create: [environment-check.json](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/environment-check.json).

## Implementation Steps

### D02-04 — Validator nguồn và input (3h)

- Input → configs/data.yaml và phase 1 census.
- Action → Codex triển khai validate_inputs với schema/path/hash/ID checks; B review recursive fields và canonical paths.
- Output → validator có failure codes + reports/input-validation.json.
- Prerequisite → D02-01..03 pass; allowed schema có version.
- Acceptance → reject labels/source-case/nested gold, duplicate ID, foreign evidence ID, missing file và hash mismatch.
- Failure path → fail closed trước tạo output; report tên rule và opaque ID, không dump secret/raw content.

### D02-05 — Export derivative deterministic (3h)

- Input → nguồn validated, time/redaction policy.
- Action → Codex build exporter và stable ordering; A kiểm six train provenance, C kiểm payload shape.
- Output → data/inference files + private audit mapping + manifest content hashes; management step riêng tạo byte-preserving split-map.tsv/ground_truth.jsonl ở data/private.
- Prerequisite → D02-04 pass; export destination được xác nhận trong workspace.
- Acceptance → 90 inference IDs, private sidecars có cùng source IDs/byte hashes, no family/split in serialized observations; row provenance resolve.
- Failure path → ghi output vào staging, chỉ promote sau validation; lỗi giữa chừng không coi partial export là release.

### D02-06 — Local CPU environment và smoke (3h)

- Input → derivative manifest và Python/PyArrow requirement nguồn.
- Action → Codex tạo runtime config/notebook, chạy hai train cases ở môi trường sạch; C ghi hardware, B tái chạy.
- Output → requirements-lock.txt, runtime.yaml, environment-check.json và notebook không secret.
- Prerequisite → D02-05 pass; Python/ABI tương thích được đo.
- Acceptance → clean restart đọc đúng IDs, schema pass, cùng content hashes; CPU/RAM/runtime versions được ghi thật.
- Failure path → ABI/version fail thì tạo môi trường compatible; không sửa nguồn data để làm smoke pass.

### D02-07 — Packaging/resume và nhánh Kaggle (3h)

- Input → safe export, smoke receipt và policy chia sẻ plan 01.
- Action → Codex tạo packaging checklist/cache-resume guide; C chạy Kaggle khi quyền/account sẵn, A review files.
- Output → reports/environment-check.json cập nhật local/Kaggle states và manifest đóng gói allowlisted.
- Prerequisite → D02-05/06 pass; upload chỉ khi policy chia sẻ đã xác nhận.
- Acceptance → archive inventory chỉ allowed derivatives; no raw/labels/private/keys; thiếu Kaggle ghi deferred + owner.
- Failure path → thiếu GPU/quota tiếp tục CPU, package local vẫn dùng; không đổi model hoặc công bố Kaggle pass.

## Interface và schema dự kiến

| File/API | Fields/hành vi | Consumer |
|---|---|---|
| validate_inputs | config path, source root → structured report hoặc fail | Exporter và downstream preflight |
| export_inference_data | manifest/config → deterministic derivative manifest | Plan 03/04/05/07 |
| observations.jsonl | incident_id, system, window, service names, evidence IDs, provenance versions | Representation/bundle builder |
| input-manifest.json | schema/source/config/transform hash, per-file hash, rows | Tất cả consumers |
| private split-map/ground_truth | Source IDs/bytes/hash giữ nguyên; hash/role trong private data-audit.json | Annotation manager/evaluator; không model manifest |
| environment-check.json | os, python, packages, cpu, gpu/null, ram, smoke_ids, results | Handoff/reproducibility |
| runtime.yaml | device preference, seed, batch/cache policy, api_enabled=false | Runner configurations |

## Validation Scenarios

| ID | Tình huống | Kết quả mong đợi |
|---|---|---|
| DB-01 | Hash đổi sau census | Export fail, không reuse cache |
| DB-02 | JSON nested field có fault | Schema reject trước serialize |
| DB-03 | ../../labels hoặc junction ra private | Canonical path reject |
| DB-04 | Crash giữa export | Staging chưa publish, retry không ghép file cũ/mới |
| DB-05 | Second clean smoke | Cùng data IDs/content hash, metadata thời gian có thể khác |
| DB-06 | Python 3.12 với wheel 3.11 | Lỗi được nhận diện; cài môi trường compatible |
| DB-07 | Kaggle unavailable | Local gate vẫn chạy; receipt deferred không pass |
| DB-08 | API key trong notebook output | Gate packaging fail; xóa output nhạy và review lại |

## Bàn giao cho phase 3

B nhận input validator và exact manifest cần đánh giá adversarial boundary.
C nhận clean environment recipe và trạng thái Kaggle thật.
Không bàn giao whole source folder dưới danh nghĩa inference dataset.
Mọi upload/API vẫn theo policy plan 01 và implementation scope tương ứng.

## Success Criteria

- [x] Validator/exporter proposed đã được triển khai và source nguyên.
- [x] Safe export đủ 90 incidents với content manifest.
- [x] Hai smoke sạch có bằng chứng tái lập.
- [x] Runtime ghi versions/device thực tế và API mặc định tắt.
- [x] Kaggle/package state trung thực, file inventory được review.

## Risk Assessment

Recursive glob dễ kéo labels/private vào package; packaging chỉ dùng manifest allowlist.
DataFrame serialize tự động có thể giữ cột quản lý; select explicit columns trước ghi.
Model execution không thuộc phase này; không cài mọi stack để làm lock phình hoặc khó tái lập.
