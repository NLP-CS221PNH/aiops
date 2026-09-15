# Plan 01 — Kiểm thử và kiểm tra bàn giao

Kết quả kỹ thuật và strict G0 **PASS** cho `cs221-aiops-rag-protocol-v1`, phiên bản `1.0.0-reviewed.1`. Đây là nghiệm thu tự động theo chỉ thị rõ ràng của người dùng: “tự check mọi thứ, không cần human input”. Integration chạy ngày 2026-09-13 lúc 02:54:57 UTC; `technical_valid:true`, `g0_ready:true`, không errors/blockers/warnings.

Manifest ghi `review_mode:automated`, review receipt của Codex và authorization có hash; không tạo chữ ký người thật. Quyền API, payload, local model, chia sẻ dữ liệu vẫn pending; budget vẫn null.

## Lệnh và bằng chứng

Chạy từ gốc research pack với Python 3.11.9, PyYAML 6.0.2:

| Lệnh | Kết quả |
|---|---|
| `python -B -m unittest discover -s 06_implementation/tests -p test_validate_protocol.py -v` | 52/52 tests PASS, 3,142 giây; giữ nguyên 35 tests cũ và thêm 17 tests; tất cả fixtures trong thư mục tạm |
| `python -B 06_implementation/scripts/validate_protocol.py --output 06_implementation/reports/protocol-validation.json` | Exit 0; `technical_valid:true`, `g0_ready:true`; không errors/blockers/warnings |
| `python -B 06_implementation/scripts/validate_protocol.py --require-g0 --output 06_implementation/reports/g0-readiness.json` | Exit 0; `technical_valid:true`, `g0_ready:true`; không errors/blockers/warnings |

Receipts: [protocol-validation.json](protocol-validation.json), [g0-readiness.json](g0-readiness.json).

Mutation tests kiểm stale byte hashes, sai counts/split và family leakage, sai F1→test_input→test_pool→F2→test_scoring, thiếu unjudged policy, judgments giả, drift giữa YAML và Markdown, quyền API/budget sai hoặc thiếu evidence, chosen mâu thuẫn, owner/reviewer/deadline thiếu, literature provenance/human claims, thiếu review artifact, version sai, unsafe paths và khả năng CLI chỉ đọc khi không truyền `--output`. Ca human-G0 thành công trong unit tests chỉ dùng tên synthetic trong thư mục tạm; không ghi chữ ký người thật vào gói nghiên cứu.

17 tests mới kiểm mode tự động hợp lệ; thiếu authorization/receipt; authorization sai scope; receipt sai protocol/version hoặc thiếu phạm vi review; bytes khác bản đã review dù manifest được hash lại; receipt rỗng, có blocking finding hoặc không PASS; chữ ký người giả; quyền API không được tự cấp; review mode mâu thuẫn; `--output` không ghi đè receipt đã freeze. Tests builder xác minh candidate tự động hợp lệ/idempotent và từ chối thiếu authorization hoặc stale review trước khi thay manifest. Mode human mặc định vẫn yêu cầu review người và giữ toàn bộ tests cũ.

## Builder lifecycle

Trước amendment, đã import builder trong `python -B -`, chuyển ROOT/IMPLEMENTATION sang temporary synthetic pack và kiểm 7/7 kịch bản PASS:

1. Lần build đầu chỉ tạo draft, `reviewers:[]`.
2. Chạy lại version đầu khi nội dung không đổi giữ nguyên bytes và timestamp.
3. Thay artifact nhưng giữ version bị từ chối; receipt cũ còn nguyên.
4. Tăng version lưu đúng bytes manifest cũ và hash liên kết `supersedes`.
5. Chạy lại bản có `supersedes` khi nội dung không đổi giữ nguyên bytes.
6. Source khác inventory bị từ chối, không thay receipt.
7. Config đã reviewed ở mode human bị builder từ chối; không tự tạo chữ ký người.

Đây là kiểm tra lifecycle bằng fixture tạm trong phiên làm việc. Ba tests builder cho mode tự động đã được bổ sung vào suite 52 ca và tái chạy được bằng lệnh đã ghi. Builder chỉ xuất manifest accepted sau khi kiểm strict candidate trong bộ nhớ: authorization hợp lệ, review PASS không có blocker, coverage đủ và exact hashes khớp.

## Bằng chứng lịch sử trước amendment

Ngày 2026-09-13 lúc 02:19:13 UTC, bản `1.0.0-draft.2` qua kiểm kỹ thuật nhưng strict G0 trả exit 1 đúng yêu cầu lúc ấy: chưa có review A/B/C, protocol draft và gate chưa accepted. Kết quả đó thuộc trước chỉ thị đổi mode nghiệm thu của người dùng; không phải trạng thái hiện tại. Manifest draft.2 được giữ nguyên bytes trong archive và liên kết `supersedes` của bản reviewed.1.

## Định danh và giới hạn

- Manifest reviewed.1 SHA-256: `fc411c69c5e6cdc8883a8a458eb33502e7b7c50aaabab68b2387c905be943c29`.
- Validator SHA-256: `f836220e14b4a2f22085ad338f07ea9ee742a600b4efe63454b9f56b95ca3e29`.
- Unit tests SHA-256: `c107c4ea772f1ea8b1fcc703c2689a36b8eb9b2e9cc11b956d8b009619714cf2`.
- Automated review receipt SHA-256: `dff177b8618f23aec5e7976d7fa20dad38168a534f994d0fc74a44931d69063d`.
- Đã capture manifest bytes, chạy lại strict validator chỉ đọc và so sánh bytes sau lệnh: **không đổi**, strict vẫn PASS.
- Manifest kiểm exact bytes của các artifact Plan 01 và nguồn có provenance. Không gọi validator legacy vốn ghi lại `04_audit`; không quét/chạy tests của plan khác đang triển khai đồng thời.
- Không chạy retrieval/generation experiments, API, human annotation, gửi thư hay xác minh quyền bằng lời đáp chưa có. Nghiệm thu tự động chỉ áp dụng G0 Plan 01 theo authorization; không biến Codex thành người chấm nhãn hoặc người cấp quyền mô hình/ngân sách.
- Tài liệu nguồn, protocol và manifest không bị sửa bởi integration; chỉ hai JSON receipts và báo cáo này được ghi dưới `reports/`.
