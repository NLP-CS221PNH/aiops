# Plan 01 — protocol và gói review G0

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2`.

**Các sản phẩm plan01 đã được soạn; G0 vẫn chờ review người thật.** Không có API/model run, annotation hoặc benchmark được thực hiện bởi delivery này. Artifacts của những plan khác có thể xuất hiện đồng thời trong thư mục này; manifest01 chỉ hash danh sách rõ ràng thuộc scope01.

Đọc [charter](docs/project-charter.md) → [research protocol](docs/research-protocol.md) → [review và handoff](docs/protocol-review.md). [Decision log](docs/decision-log.md) có16quyết định pending với owner/reviewer/hạn; [team agreement](docs/team-working-agreement.md) chứa lịch/nguồn lực đề xuất; [literature matrix](docs/literature-matrix.tsv) có10bài với mức đọc thật; [thư hỏi giảng viên](docs/instructor-questions-draft.md) chưa gửi.

## Kiểm tra từ gốc research pack

Python3.11+ và PyYAML6.0.2 ([dependency](requirements-validation.txt)); môi trường hiện tại đã có, không cần cài lại để chạy các lệnh sau:

```powershell
python -B 06_implementation/validation/source-inventory.py
python -B -m unittest discover -s 06_implementation/tests -p test_validate_protocol.py -v
python -B 06_implementation/scripts/validate_protocol.py --output 06_implementation/reports/protocol-validation.json
python -B 06_implementation/scripts/validate_protocol.py --require-g0 --output 06_implementation/reports/g0-readiness.json
```

Lệnh cuối **phải exit1 khi thiếu human review**; đây là kiểm gate thực, không lỗi bị bỏ qua. Validator thường phân biệt `technical_valid` với `g0_ready`; cả hai cần đọc. Kiểm không tự sửa/hash lại files. [Reports](reports/plan01-progress.md) ghi kết quả thực và công còn cần người. Script inventory mặc định read-only; `--write-report` chỉ refresh derivative receipt khi cần, sau đó manifest cũ sẽ stale và phải review/version lại.

[G0 manifest](freezes/G0/manifest.json) chứa byte hashes, versions, nguồn, open decisions, reviewers=[] và pending_reviews. Không upload manifest/source-audit như inference payload vì provenance tham chiếu private source files. Có hashes không cấp quyền model hay xác nhận G0. Plans02–10 nhận contract theo bảng handoff sau khi người thật xác nhận version.

Sau sửa nội dung: review affected artifacts, tăng version nhất quán, rồi chạy `python -B 06_implementation/scripts/build_g0_manifest.py`; builder giữ manifest cũ và từ chối thay nội dung cùng version. Builder chỉ tạo draft candidates; acceptance người thật phải có record riêng và kiểm `--require-g0`. Không refresh manifest để che hash mismatch chưa điều tra.

Các bản gốc `00_plan`–`05_research` và source manifests được giữ nguyên. Source inventory đã kiểm16điều kiện, gồm90incidents/30families, split54/18/18 và0human judgments;270upstream hash-verification flags là provenance đã ghi, không phải raw bytes được rehash ở lượt này. Không chạy validator gói chuẩn bị để ghi đè `04_audit` hoặc biến NOT_RUN thành kết quả.
