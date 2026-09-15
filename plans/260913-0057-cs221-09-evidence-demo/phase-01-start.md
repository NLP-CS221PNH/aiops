---
phase: 1
title: "Chốt kịch bản và hợp đồng demo"
status: pending
priority: P1
effort: "2h"
dependencies: []
---

# Phase 01: Chốt kịch bản và hợp đồng demo

## Tổng quan

Chọn đúng việc cần minh họa: incident → evidence → claim → thiếu thông tin; lập bộ case có lý do chọn và quy tắc fixture/cache/live.
Công dự kiến **2 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Output contract | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/generation/schemas.py` | 07 schema và actual-context citations |
| Corpus registry | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/knowledge/` | Source revision và normalized offsets |
| Inference export | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/data/inference/` | Chỉ fields đã duyệt |
| Phân tích cuối khi có | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/` | 08.results mới là nguồn số liệu nghiên cứu |

## Yêu cầu

- Ưu tiên demo Python cục bộ, chỉ đọc artifacts; không deploy hoặc yêu cầu tài khoản cloud.
- Scaffold sớm bằng fixture gắn nhãn; chưa có08.results không được điền số liệu model giả.
- Kịch bản gồm thành công, chẩn đoán sai/yếu, evidence thiếu và lỗi citation/schema.
- Nếu không có case thật cho bất kỳ nhóm success/weak/missing/invalid nào, ghi rõ “không quan sát thấy case thật thuộc nhóm này” và dùng fixture gắn nhãn để minh họa; không tính fixture vào số liệu.
- Case chọn tay chỉ minh họa, không đại diện hiệu năng toàn18 test; mọi aggregate lấy đúng08results.
- Mỗi citation mở exact context text/offset đã gửi, kèm registry/source revision; không dùng URL mô hình bịa.

## Kiến trúc và ranh giới trách nhiệm

Manifest cho phép → bộ chọn incident/condition → ba vùng observations, retrieved evidence, diagnosis/unknowns. Click claim/citation làm nổi đoạn đã gửi; bản gốc corpus có thể mở riêng có nhãn.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/demo-cases.yaml` — Case selection, nguồn dữ liệu, thứ tự diễn.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-script.md` — Kịch bản5–7 phút và câu giới hạn.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-runbook.md` — Quyền đọc và chế độ hoạt động.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- case_id:string; incident_id:string; run_id:string|null; condition:G0|GB|GD|GH|GR.
- purpose:success|weak_diagnosis|missing_evidence|invalid_citation; origin:research_run|fixture.
- selection_reason:string; result_ref:string; manifest_hash:string; expected_status:string; display_order:int.
- display_mode:replay|live|fixture; source_snapshot_hash:string; approved_payload_ref:string|null.
- Fixture IDs có namespace fixture:; mọi fixture tách khỏi incident IDs và metric loaders nghiên cứu.
- Live chỉ mở bằng thao tác rõ của người trình bày sau kiểm quyền/cap; mặc định replay.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 09.1.1 | 0.75h | C + Codex / B | 07 schema và08taxonomy nếu có | Chọn4nhóm case, ghi lý do; dùng fixture nếu chưa có runs | demo-cases.yaml nháp |
| 09.1.2 | 0.75h | Codex + C / A | Context registry và output fields | Vẽ luồng3vùng, định click citation và nhãn trạng thái | Contract trong runbook |
| 09.1.3 | 0.5h | C / A và B | Mục tiêu bảo vệ và giới hạn | Viết kịch bản5–7 phút, câu kết luận đúng phạm vi | demo-script.md nháp |

## Trình tự thực hiện

1. Đọc contract07.pilot trước dựng UI; không giả schema của parsed output từ câu trả lời mẫu.
2. Định nghĩa vùng trái incident/observations; vùng giữa evidence/rank; vùng phải claims/abstain/unknowns.
3. Ghi từng bước trình bày: mở case, nhìn triệu chứng, so GB/GH, kiểm claim, chỉ phần chưa biết.
4. Trước08results, điền result_ref tới fixture đã gắn nhãn; sau08 chọn case thật theo taxonomy, giữ lý do chọn.
5. Nếu có đối chiếu hai conditions, bắt buộc cùng incident/observation hash và version khóa.
6. Tách ảnh/bản ghi backup khỏi final metrics; backup trình bày không tự trở thành kết quả chạy mới.
7. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
8. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Không có final runs | results chưa tồn tại | Scaffold fixture có nhãn, case research còn pending |
| Chọn toàn ca đúng | 4case đều success | Bổ sung weak/missing thật nếu có; nếu không có dùng fixture với ghi chú không quan sát thấy ca thật |
| Không có invalid thật | Final validator không lỗi | Fixture invalid có nhãn, không ghi vào metrics |
| Khác observations | So hai condition cùngID nhưng hash khác | Chặn compare, hiển thị mismatch |
| Citation bịa URL | Output tự nêu external link | Chỉ mở source registry được duyệt |

## Checklist thực hiện

- [ ] **09.1.1**: demo-cases.yaml nháp; C + Codex / B xác nhận bằng chứng.
- [ ] **09.1.2**: Contract trong runbook; Codex + C / A xác nhận bằng chứng.
- [ ] **09.1.3**: demo-script.md nháp; C / A và B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 2h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Case config mô tả origin, run và lý do chọn đầy đủ.
- [ ] Luồng demo kiểm được ít nhất một claim tới đoạn exact context.
- [ ] Kịch bản nói rõ hỗ trợ phân tích offline; nhóm yếu/thiếu evidence dùng ca thật khi có, còn không dùng fixture có nhãn và lý do.
- [ ] Replay/live/fixture và failure/abstention được định nghĩa riêng.

## Gate nghiệm thu và điều kiện thất bại

G09-A: C duyệt kịch bản và contract; A kiểm dữ liệu hiển thị; B kiểm lựa chọn case không bị trình bày như aggregate. Chưa08results không chặn scaffold.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Chọn ca đẹp gây hiểu nhầm: bắt buộc weak/missing case và câu giới hạn. UI quá lớn: khóa ba vùng và một đường click citation, bỏ trang trí không giúp bảo vệ.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase2 nhận contract/demo-cases và fixtures; bộ nghiên cứu cuối vẫn chờ08.results. Không gọi model chỉ để tạo một case đẹp cho demo.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

