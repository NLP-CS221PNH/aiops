---
title: "01 — Phạm vi, protocol và thỏa thuận nhóm"
description: "Chốt hợp đồng nghiên cứu cho 8 tuần và ba thành viên; biến giả định môn học, tài nguyên và đánh giá thành quyết định có người chịu trách nhiệm."
status: in-progress
priority: P1
effort: "12h"
tags: [research, docs, aiops, rag]
blockedBy: []
blocks: [260913-0020-cs221-aiops-rag-master-plan]
created: 2026-09-13
---

# 01 — Phạm vi, protocol và thỏa thuận nhóm

## Amendment theo yêu cầu người dùng — 2026-09-13

Người dùng chỉ thị trong task hiện tại: **“tự check mọi thứ, không cần human input”**. Chỉ thị này thay điều kiện review người thật của riêng plan01 bằng **Codex và reviewer agent độc lập**, có actor/type, scope, thời gian, artifact hashes và bằng chứng kiểm. Không ghi AI review thành chữ ký, người đọc hoặc giờ cam kết của con người.

Tên A/B/C, giờ thực có, rubric và hạn môn học chưa biết vẫn được ghi rõ pending/unknown; không cần hỏi thêm để hoàn tất scope01. Quyền API/payload/local model/sharing/ngân sách giữ trạng thái thực tế; nhãn qrels và annotation người thật ở các plan sau không được tạo hoặc miễn thay. RQ, counts/split/core, conditions và F1/F2 giữ nguyên. Bàn giao scope01 là static handoff có paths/version/hash được reviewer kiểm, communication thực tế vẫn chưa gửi.

Bản trước amendment được giữ nguyên bytes cùng hashes tại [archive](../../06_implementation/reports/plan01-pre-automated-review/archive-manifest.json). Chỉ check acceptance/complete qua CLI sau khi independent review và strict G0 validator cho phiên bản amendment đều đạt; amendment này chưa tự là bằng chứng PASS.

## Tổng quan

Chốt hợp đồng nghiên cứu cho 8 tuần và ba thành viên; biến giả định môn học, tài nguyên và đánh giá thành quyết định có người chịu trách nhiệm.
Tuần 1; quyết định API/fallback theo dõi tới cuối tuần 2. Sản phẩm plan01 đã có trong `06_implementation`; đang review theo amendment của người dùng, chưa được check complete trước receipt cuối.
Căn cứ: [master](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/260913-0020-cs221-aiops-rag-master-plan/plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md), [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).

## Goal contract

| Thành phần | Hợp đồng |
|---|---|
| Kết quả cần đạt | Protocol v1, ma trận bài lõi, quyết định có bằng chứng và phân công vai trò A/B/C được Codex + reviewer agent độc lập kiểm theo chỉ thị người dùng. |
| Bằng chứng hoàn tất | Các sản phẩm có đường dẫn, version/hash, người kiểm và checklist nghiệm thu trong phase 03 |
| Owner / reviewer | Codex điều phối, reviewer agent độc lập kiểm nguồn/thiết kế/tái lập; A/B/C là vai trò nghiên cứu đề xuất |
| Công dự kiến | 12 giờ-người, cộng dự phòng trong master; không phải giờ Codex đã thực hiện |
| Ngoài phạm vi | Đổi đề tài, chạy API, tạo annotation, chạy thí nghiệm hoặc gửi thông điệp thay nhóm. |

## Hiện trạng và bất biến

- Bộ có 90 incidents, 30 service×fault families; split 54 train / 18 dev / 18 test.
- Core qrels dự kiến 20 train + 18 dev + 18 test; hiện có **0 human judgments**.
- Test có 6 families; không coi repetitions, claims hoặc log rows là mẫu độc lập.
- RQ chính: passage nDCG@5; hybrid so baseline đơn mạnh hơn trên dev, hòa chọn BM25 trước test.
- G0/GB/GD/GH bắt buộc; GR chỉ khi quyết định trước F1 và đủ nguồn lực.
- `G0` trong protocol là gate khởi động; `G0` trong runs là điều kiện no-RAG, ghi rõ loại để tránh nhầm.
- Không dùng test để tune; không đặt yêu cầu hybrid phải thắng.
- Kaggle Free và API là nguồn lực có điều kiện; không coi quyền dùng model/chi tiền đã được duyệt.

## Các phase

| Phase | Nội dung | Công | Trạng thái |
|---|---|---:|---|
| 1 | [Thu thập ràng buộc](phase-01-start.md) | 3h | pending |
| 2 | [Soạn protocol và phân công](phase-02-build.md) | 6h | pending |
| 3 | [Review và bàn giao G0](phase-03-validate-and-handoff.md) | 3h | pending |

## Dependency và bàn giao

Không có dependency triển khai. Đọc bộ nghiên cứu và master hiện có; bàn giao G0 cho 02–10.
Dependency chi tiết được kiểm ở từng gate; đọc `blockedBy` như phụ thuộc hoàn tất, không mặc định cấm soạn khung sớm.
Đầu ra sai contract phải trả lại owner kèm lỗi có thể tái hiện; không sửa ngầm artifact đã freeze.

## Trách nhiệm và ranh giới review

- **Codex + reviewer agent độc lập:** Soạn/kiểm charter, protocol, thư nháp, literature, phân công, manifest và static handoff; lưu automated review đúng loại actor.
- **Dữ kiện/quyền bên ngoài:** Rubric/hạn nộp/tên/giờ chưa biết vẫn pending, không cần human input để đóng scope01. Giảng viên/quyền model vẫn chưa được suy thành đồng ý; không gửi thư hay tạo human qrels.
- Quyết định chưa có phản hồi giữ `pending` với owner và hạn; không tự suy thành đồng ý.
- Codex chỉ soạn nội dung liên lạc; mọi gửi thư/tin nhắn cần yêu cầu riêng rõ ràng.

## Kho sản phẩm dự kiến

Gốc tuyệt đối: `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/`.
Danh sách con: `docs/project-charter.md; docs/research-protocol.md; docs/decision-log.md; docs/literature-matrix.tsv; docs/team-working-agreement.md; docs/instructor-questions-draft.md; configs/protocol.yaml; freezes/G0/manifest.json`.
Từng phase bên dưới nêu đường dẫn, thao tác và bên nhận; final receipts/manifest chứng minh nội dung và phiên bản thực.

## Nghiệm thu và rủi ro

- [ ] Các task có đầu vào, hành động, đầu ra và người kiểm; ba phase đạt gate đã nêu.
- [ ] Mọi kết quả thực được phân biệt với giả định, fixture và công việc chưa chạy.
- [ ] Không rò gold/reference/qrels sang inference; ledger giữ ca lỗi và thiếu evidence.
- [ ] Reviewer agent độc lập kiểm version/hash và khả năng tái hiện static handoff; communication chưa gửi được ghi đúng.
Thiếu rubric hoặc phản hồi API chỉ chặn phần tương ứng; dữ liệu, IR và annotation vẫn chuẩn bị được.

## Bằng chứng thực hiện theo amendment — 2026-09-13

Sản phẩm kỹ thuật hiện có được ánh xạ đủ12task tại từng phase và [progress report](../../06_implementation/reports/plan01-progress.md). Trạng thái trong frontmatter/CLI chỉ đổi sau kiểm cuối; danh sách acceptance hiện vẫn chưa check. Human-only gate của bản trước đã được supersede bằng chỉ thị người dùng, không bị xóa khỏi lịch sử.

| Phase | Bằng chứng cần kiểm để nghiệm thu amendment |
|---|---|
| 1 | Charter, source counts/hashes, question draft, decision log và independent source review |
| 2 | Protocol MD/YAML,10paper provenance/read-depth, role agreement, resource/fallback constraints và independent review |
| 3 | Review/dispositions, strict validation/tests, manifest chain và static handoff theo version/hash |

Số0human judgments và permission pending vẫn là dữ kiện thật sau khi G0 automated được accepted. Hoàn tất01 không hoàn tất annotation/model/results của plans02–10. Không Git init/commit/send/publish để đóng plan.
