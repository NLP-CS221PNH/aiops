---
phase: 3
title: "Tổng duyệt, backup và bàn giao demo"
status: complete
priority: P1
effort: "4h"
dependencies: [2]
---

# Phase 03: Tổng duyệt, backup và bàn giao demo

## Tổng quan

Một thành viên khác mở demo theo runbook, kiểm nguồn/chế độ/lỗi và diễn tập trong5–7 phút; xuất backup cục bộ từ dữ liệu đã khóa.
Công dự kiến **4 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Ứng dụng | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/demo/app.py` | G09-B đọc artifact và error states |
| Case audit | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/case-audit.tsv` | Final refs khớp08.results |
| Kịch bản | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-script.md` | Đủ case đúng/yếu/thiếu |
| Runbook | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-runbook.md` | Cách mở offline từ môi trường sạch |

## Yêu cầu

- Nghiệm thu cuối cần08.results có hashes và errors; demo không thay bằng fixture rồi gọi là final.
- Người chưa viết app làm theo runbook; các bước cần giải thích miệng phải bổ sung vào docs.
- Kiểm keyboard cơ bản, font dễ đọc, contrast và trạng thái không chỉ màu; phù hợp màn hình trình chiếu.
- Lưu ảnh hoặc bản ghi backup có ngày/run IDs; không công khai/upload nếu chưa được yêu cầu.
- Nội dung trình bày giữ giới hạn fault injection,6 families và evidence support; không claim causal chain/MTTR.
- Demo không sửa thí nghiệm; bug phát hiện được ghi cho owner08 đánh giá protocol deviation.

## Kiến trúc và ranh giới trách nhiệm

Final cases → độc lập mở replay → kiểm citation/compare/errors → diễn tập → screenshots/video local → handoff10. Live nếu có là phần phụ sau replay đã đạt.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-script.md` — Kịch bản cuối và câu trả lời dự kiến.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-runbook.md` — Hướng dẫn đã có người khác chạy.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/case-audit.tsv` — Kết quả citation/hash review.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/rehearsal.md` — Thời lượng, lỗi, reviewer và sửa.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/backup/` — Ảnh hoặc video cục bộ từ artifacts thật.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/demo-manifest.json` — Version/hash của case và backup.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Rehearsal:{date_utc,operator,reviewer,environment,mode,script_version,duration_seconds,issues,receipts}.
- DemoManifest:{app_hash,config_hash,run_refs,corpus_refs,case_audit_hash,backup_files:[{path,sha256}],reviewed_by}.
- Presentation claim map:{script_step,claim_or_message,artifact_ref,limitation}; kết luận định lượng trỏ08 results.
- Issue:{id,severity,case_id,repro_steps,expected,observed,owner,status}; unresolved critical làm gate fail.
- Backup metadata:{origin:replay|fixture|live,run_id,generated_at_utc,recorded_at_utc}; thời gian ghi màn hình khác thời gian model sinh.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 09.3.1 | 1.5h | B / C | Runbook và máy/môi trường khác | Mở offline, kiểm ít nhất1citation/case, các trạng thái lỗi | Reproduction/rehearsal receipt |
| 09.3.2 | 1h | C / A và B | Kịch bản cuối | Diễn tập5–7 phút, kiểm claim và timing | Script cuối và issue list |
| 09.3.3 | 1h | C + Codex / A | Demo đã đạt và fixtures lỗi có nhãn | Ghi ảnh/video backup, kiểm nguồn và secrets | Backup local có metadata |
| 09.3.4 | 0.5h | Codex + C / B | Case audit và receipts | Lập manifest bàn giao10, ghi live optional | Demo manifest |

## Trình tự thực hiện

1. Mở từ thư mục triển khai qua runbook trong một session sạch; thiếu bước thì cập nhật và làm lại phần đó.
2. Ngắt mạng để chứng minh replay vẫn mở; kiểm mode text không chuyển thành live.
3. Chọn claim hỗ trợ đủ, claim yếu và abstention từ runs nếu có; nhóm vắng mặt dùng fixture có nhãn “không quan sát thấy ca thật”; kiểm người xem hiểu sự khác biệt.
4. Kiểm invalid fixture luôn có badge; mọi case research dùng output gốc dù sai.
5. Đo kịch bản5–7 phút; rút nội dung trang trí trước phần evidence/failure.
6. Ghi backup sau khi version cuối ổn định, dùng absolute artifact ref trong manifest và relative path trong gói chia sẻ.
7. A kiểm không lộ key/payload ngoài danh sách; B đối chiếu mọi số liệu hiển thị với08.
8. Bàn giao10 screenshots, script, manifest và limitations; không upload hay nộp trong task demo.
9. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
10. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Người khác mở | Chỉ có runbook, không lời nhắc | Mở replay và kiểm citation thành công |
| Offline hoàn toàn | Không mạng/API | Case replay đủ; live có thông báo rõ |
| Lỗi citation fixture | Case purpose invalid_citation | Badge mô phỏng/validator đúng; không tính metric |
| Nhầm thời gian | Cached response cũ, màn hình ghi hôm nay | Hiện generated_at và mode đúng |
| Aggregate khác08 | Số liệu demo tự tính trên4case | Fail; lấy bảng08 hoặc bỏ aggregate |
| Thiếu case final | Chỉ có fixtures | Không đóng09.demo; chờ08results |
| Bug phát hiện | App đọc sai chunk revision | Chặn case, sửa loader; báo08 nếu artifact thật sai |

## Checklist thực hiện

- [x] **09.3.1**: Reproduction/rehearsal receipt; B / C xác nhận bằng chứng tại `reports/demo/rehearsal.md`.
- [x] **09.3.2**: Script cuối và issue list; C / A và B xác nhận bằng chứng tại `docs/demo-script.md` và `reports/demo/rehearsal.md`.
- [x] **09.3.3**: Backup local có metadata; C + Codex / A xác nhận bằng chứng tại `reports/demo/backup/`.
- [x] **09.3.4**: Demo manifest; Codex + C / B xác nhận bằng chứng tại `reports/demo/demo-manifest.json`.
- [x] Lưu các lỗi/chưa biết và cách xử lý; hoàn thành đầy đủ các artifacts của Phase 03.
- [x] Đối chiếu tổng công task với 4h; hoàn thành đúng dự toán và phạm vi.

## Tiêu chí thành công

- [x] B hoặc A mở được replay độc lập và đi từ claim tới source snapshot.
- [x] Kịch bản 5–7 phút phủ thành công, yếu/thiếu evidence và giới hạn; nhóm không xuất hiện ở runs thật dùng fixture có nhãn và ghi không quan sát thấy ca thật.
- [x] Backup có nhãn nguồn/thời điểm/run IDs, giữ secrets ngoài sản phẩm.
- [x] 09.demo manifest và case audit khớp 08.results khi có; 10 nhận đủ handoff.

## Gate nghiệm thu và điều kiện thất bại

G09-C/09.demo: final research cases có provenance, offline runbook được người khác thực hiện, citations đúng và demo không xuyên tạc failures. Live có thể bỏ mà vẫn đạt.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Mất mạng lúc bảo vệ: replay+backup. Người xem hiểu abstention là hỏng app: script giải thích thiếu evidence và coverage. Lỗi nguồn nghiêm trọng: dừng case, ghi issue, không dùng output thay thế đẹp hơn.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

10 nhận app/version, script, runbook, case audit, backup và manifest để đưa vào gói nộp local. Nhóm quyết định gửi/nộp đúng quy định môn học; Codex không tự gửi.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

