# Plan 01 — protocol và gói review G0

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-reviewed.1`.

**Plan01 tự nghiệm thu bằng Codex theo yêu cầu “tự check mọi thứ, không cần human input”.** [Amendment](docs/acceptance-amendment.md) quy định review độc lập, hashes và strict G0 check. Không có API/model run, annotation hoặc benchmark được thực hiện bởi delivery này. Artifacts của những plan khác có thể xuất hiện đồng thời trong thư mục này; manifest01 chỉ hash danh sách rõ ràng thuộc scope01.

Đọc [charter](docs/project-charter.md) → [research protocol](docs/research-protocol.md) → [review và handoff](docs/protocol-review.md). [Decision log](docs/decision-log.md) có D16 confirmed cho review mode và 15 quyết định chưa xác minh với owner/reviewer/hạn; [team agreement](docs/team-working-agreement.md) chứa lịch/nguồn lực đề xuất; [literature matrix](docs/literature-matrix.tsv) có10bài với mức đọc thực của Codex; [thư hỏi giảng viên](docs/instructor-questions-draft.md) chưa gửi.

## Kiểm tra từ gốc research pack

Python3.11+ và PyYAML6.0.2 ([dependency](requirements-validation.txt)); môi trường hiện tại đã có, không cần cài lại để chạy các lệnh sau:

```powershell
python -B 06_implementation/validation/source-inventory.py
python -B -m unittest discover -s 06_implementation/tests -p test_validate_protocol.py -v
python -B 06_implementation/scripts/validate_protocol.py --output 06_implementation/reports/protocol-validation.json
python -B 06_implementation/scripts/validate_protocol.py --require-g0 --output 06_implementation/reports/g0-readiness.json
```

Lệnh cuối phải PASS khi authorization, review receipt và mọi hashes hiện tại hợp lệ trong automated mode. Thiếu authorization/receipt hoặc hash lệch phải exit1; human mode mặc định vẫn yêu cầu human review. Validator phân biệt `technical_valid` với `g0_ready`; cả hai cần đọc. Kiểm không tự sửa/hash lại files. [Progress](reports/plan01-progress.md) ghi kết quả thực theo acceptance đã amendment. Script inventory mặc định read-only; `--write-report` chỉ refresh derivative receipt khi cần, sau đó manifest cũ sẽ stale và phải review/version lại.

[G0 manifest](freezes/G0/manifest.json) chứa byte hashes, versions, nguồn, open decisions và automated_reviews có evidence; reviewers người thật để trống. G0 acceptance dựa trên [review receipt](reports/plan01-autonomous-review.json) và [authorization](configs/acceptance-authorization.json), không cấp quyền model. Không upload manifest/source-audit như inference payload vì provenance tham chiếu private source files. Contract handoff tới plans02–10 đã được Codex kiểm; trạng thái gửi thông điệp tới người thật vẫn chưa gửi.

Sau sửa nội dung: review affected artifacts, tăng version nhất quán, cập nhật review receipt từ kiểm tra thực rồi chạy `python -B 06_implementation/scripts/build_g0_manifest.py`; builder giữ manifest cũ và từ chối thay nội dung cùng version. Automated acceptance cần đúng authorization và review receipt gắn content hashes; kiểm bằng `--require-g0`. Không refresh manifest để che hash mismatch chưa điều tra. Contract plan/phase snapshot được hash riêng, live plan files dùng để theo dõi tiến độ.

Các bản gốc `00_plan`–`05_research` và source manifests được giữ nguyên. Source inventory đã kiểm16điều kiện, gồm90incidents/30families, split54/18/18 và0human judgments;270upstream hash-verification flags là provenance đã ghi, không phải raw bytes được rehash ở lượt này. Không chạy validator gói chuẩn bị để ghi đè `04_audit` hoặc biến NOT_RUN thành kết quả.
