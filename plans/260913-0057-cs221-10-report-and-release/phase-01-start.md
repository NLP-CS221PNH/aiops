---
phase: 1
title: "Dựng khung báo cáo và ma trận nguồn từ tuần 1"
status: done
priority: P1
effort: "6h"
dependencies: []
---

# Phase 01: Dựng khung báo cáo và ma trận nguồn từ tuần 1

## Tổng quan

Viết sớm bài toán, phương pháp và thiết kế nghiên cứu; mọi mục kết quả giữ trạng thái chưa đo để tránh viết kết luận trước thí nghiệm.
Công dự kiến **6 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Protocol | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/research-protocol.md` | 01.protocol hoặc bản draft có version |
| Bài lõi | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/literature-matrix.tsv` | 8–12 bài với mức đọc thật |
| Đề cương gốc | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/00_plan/project_proposal.md` | Tên bài toán, RQ và giới hạn |
| Phương pháp | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/05_research/method-and-experiment-design.md` | Thiết kế hiện có, chưa là kết quả |

## Yêu cầu

- Dùng mẫu/rubric môn học khi nhóm cung cấp; placeholder chỉ được giữ ở thông tin thật sự chưa biết.
- Mở báo cáo bằng bài toán và đóng góp NLP; tách retrieval, localization, support, citations và abstention.
- Không gọi1.009 records là1.009 bài đã đọc; related work chỉ dùng nguồn kiểm chứng và mức đọc ghi thật.
- Bảng kết quả chưa có giá trị phải ghi NOT_RUN hoặc pending, không điền số liệu minh họa trông như thật.
- Tài liệu chính viết tiếng Việt, thuật ngữ/ID metric giữ thống nhất; ngôn ngữ output model theo01decision.
- Tạo claim registry từ sớm để kiểm mỗi đóng góp/kết luận; mọi claim định lượng cần artifact, mẫu số và giới hạn.

## Kiến trúc và ranh giới trách nhiệm

Protocol + nguồn gốc → outline có slots bằng chứng → report draft → claim registry → checklist chờ08 results. A viết data/annotation, B method/evaluation, C integration/editor; Codex hỗ trợ bản thảo.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-report.md` — Bản thảo có kết quả pending.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/references.bib` — Chỉ mục nguồn sử dụng thật.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/claim-evidence.tsv` — Registry kết luận và bằng chứng.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/report-outline.md` — Rubric mapping, owner và mục còn thiếu.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/data-and-model-card.md` — Data/model limitations nháp.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Claim TSV:claim_id,section,claim_text,claim_type,artifact_ref,run_id,metric,denominator,reviewer,status,limitations.
- claim_type=method|data|result|limitation; status=draft|awaiting_evidence|verified|rejected.
- Source record:bib_key,title,authors,year,venue,doi_or_primary_url,read_depth,verified_at,used_for.
- Outline record:section_id,rubric_requirement,owner,reviewer,input_refs,completion_state; rubric chưa có ghi pending.
- Card:{dataset,system,incident_count,family_count,split,observation_window,corpus_scope,annotation_scope,model_identity,allowed_use,limitations}.
- Chưa có run_id thì để null; không tạo DOI, citation metadata hoặc số liệu mà nguồn không hỗ trợ.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 10.1.1 | 2h | Codex + C / A và B | Protocol và rubric nếu có | Lập outline/rubric mapping, phân owner section | report-outline.md |
| 10.1.2 | 2h | A/B/C + Codex / người khác | 8–12 bài lõi và notes | Viết related work có so sánh task/input/gold/evaluation | Bản thảo related work vàreferences |
| 10.1.3 | 1h | Codex + B / A | Protocol và dữ kiệnpack | Viết method/data/evaluation dự kiến, tách NOT_RUN | final-report.md nháp |
| 10.1.4 | 1h | Codex + C / B | Outline và claims ban đầu | Tạo claim registry/card, đặt evidence slots | claim-evidence.tsv vàcard |

## Trình tự thực hiện

1. Chia báo cáo: bài toán/RQ, related work, dữ liệu+leakage, phương pháp, protocol, kết quả, error analysis, giới hạn, tái lập.
2. Ánh xạ mỗi rubric requirement tới section và sản phẩm; yêu cầu chưa rõ theo dõi ở01decision.
3. Related work so tính tương đồng tác vụ/dữ liệu thay vì so số accuracy không cùng benchmark.
4. Mô tả RQ2 primary nDCG@5 và contrast hybrid vs stronger dev single; hòa chọn BM25 và F1 trước test.
5. Ghi90 incidents/30 families, split54/18/18, core 56 dự kiến và0 human judgments ở hiện trạng; số liệu này cần cập nhật đúng khi thực hiện.
6. Viết phương pháp ở dạng thiết kế dự kiến; chuyển sang đã thực hiện chỉ khi có artifact/receipt.
7. Giữ mọi số liệu output ở NOT_RUN; template chart chỉ để trống có nhãn hoặc chưa tạo.
8. Gán A/B/C sections, lịch review; C biên tập thuật ngữ, Codex không ký thay tác giả/người chấm.
9. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
10. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Chưa có kết quả | Không08 results | Section results ghi pending, không tạo số giả |
| Nguồn chỉ abstract | read_depth=abstract | Không viết đã đọc/toàn bài hỗ trợ kết luận sâu |
| DOI không có | Metadata thiếuDOI | Giữ URLprimary hoặc null, không đoán |
| So benchmark khác | Paper accuracy khác dataset | Chỉ so thiết kế/phạm vi, không kết luận hơn |
| Rubric chưa biết | Nguồn yêu cầu môn thiếu | Outline có pending owner; không bịa hạn/trang |
| Claim nhân quả | Đề xuất chứng minh causal chain | Sửa thành nghi vấn/localization offline |

## Checklist thực hiện

- [x] **10.1.1**: report-outline.md; Codex + C / A và B xác nhận bằng chứng.
- [x] **10.1.2**: Bản thảo related work vàreferences; A/B/C + Codex / người khác xác nhận bằng chứng.
- [x] **10.1.3**: final-report.md nháp; Codex + B / A xác nhận bằng chứng.
- [x] **10.1.4**: claim-evidence.tsv vàcard; Codex + C / B xác nhận bằng chứng.
- [x] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [x] Đối chiếu tổng công task với 6h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Khung báo cáo có owner/reviewer và slots bằng chứng từng section.
- [x] Related work chỉ chứa nguồn kiểm được và phân biệt mức đọc.
- [x] Claim registry có trạng thái rõ, không có result claim được verified khi chưa chạy.
- [x] Data/model card nêu phạm vi và giới hạn từ đầu.

## Gate nghiệm thu và điều kiện thất bại

G10-A: outline và method draft có review, không cần08 results để bắt đầu. Result claims giữ awaiting_evidence tới phase2.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Viết văn phong kết luận quá sớm: bắt buộc status registry. Chạy theo số bài: ưu tiên8–12 bài hỗ trợ lựa chọn cụ thể. Rubric đến muộn: outline mapping giúp điều chỉnh không sửa kết quả.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase2 nhận report draft/references/claim registry, chờ08 results và06 annotation audit để điền kết quả. Draft từ tuần1 không làm dependency vòng với demo.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.
