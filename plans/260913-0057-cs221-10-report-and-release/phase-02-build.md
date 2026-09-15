---
phase: 2
title: "Tổng hợp kết quả, kiểm lập luận và viết giới hạn"
status: pending
priority: P1
effort: "12h"
dependencies: [1]
---

# Phase 02: Tổng hợp kết quả, kiểm lập luận và viết giới hạn

## Tổng quan

Nối kết quả đã khóa vào báo cáo và claim registry, giữ mẫu số/lỗi/kết quả âm; kiểm lập luận theo incident và sáu test families.
Công dự kiến **12 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Kết quả | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/` | 08.results đã khóa có denominators/failures |
| Freeze chain | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/` | F1/F2 và receipts khớp artifacts |
| Annotation audit | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/annotations/` | 06 original A/B/adjudication/coverage |
| Pilot/models | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/generation-pilot.md` | Alias/settings/usage limitations |
| Draft | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-report.md` | G10-A và slots bằng chứng |

## Yêu cầu

- Mỗi bảng/hình dẫn run/config/qrels/corpus versions; không nhập tay sửa số để hợp narrative.
- IR primary passage nDCG@5; baseline đơn chọn trên dev/hòa chọn BM25 trước test; không dùng test chọn contrast.
- Báo service accuracy đúng/tổng trên 18 test; invalid/failed/abstain không là localization đúng, báo thêm coverage/conditional accuracy.
- nDCG/recall undefined khi không có relevant qrels; pooled recall không exhaustive hoặc guaranteed lower bound; ghi eligible denominator.
- Test có 6 families × 3 repetitions; trình bày cả 6 family deltas, leave-one-family-out; bootstrap nếu có là family-resampled thăm dò.
- Báo 56 incidents core có passage judgments và scope thực, agreement trước adjudication; output review toàn bộ 72/90 và subset chấm đôi 24/30 lượt theo thực tế.
- Trình bày latency/API usage/cost/error riêng; giá/tokens theo ngày chạy, mọi unknown billing phải ghi.

## Kiến trúc và ranh giới trách nhiệm

Kết quả 08 + audit 06 + F1/F2 → bảng/hình tự tạo từ artifacts → claim-evidence trace → nội dung kết quả/thảo luận → kiểm chéo A/B/C. 10 không tự thay evaluator hoặc chạy lại test để cải thiện kết quả.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-report.md` — Kết quả, error analysis, giới hạn.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/claim-evidence.tsv` — Artifact refs/mẫu số/review.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-tables/` — Bảng/hình tạo từ results đã khóa.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/claim-audit.md` — Mâu thuẫn và disposition.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/data-and-model-card.md` — Model/run metadata và limitations thật.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/slides.md` — Storyboard từ kết quả đã kiểm.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- Table provenance:{table_id,source_artifacts,source_hashes,query_or_transform,metric,conditions,denominators,undefined_counts,generated_at}.
- Result claim:{claim_id,direction,effect_size,unit,eligible_n,families_n,paired_method,uncertainty_scope,artifact_ref,limitations}.
- Claim dùng family_bootstrap phải ghi resampling unit=family,n_families=6; không gọi claim rows là n độc lập.
- Annotation summary:{core_planned,core_completed,pairs_actual,double_judged_pairs,agreement_pre_adjudication,unjudged_at_k,no_relevant_cases}.
- Output-review summary:{conditions,planned_responses,actual_records,failures,single_reviewed,double_reviewed_subset,agreement_subset}.
- Cost summary:{provider,model_requested,model_returned,UTC_window,price_source_at_run,input/output_usage,known_cost,unknown_billing,cache_replay_count}.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 10.2.1 | 5h | Codex + B / A | 08 results + F1/F2 | Tạo bảng/hình và viết kết quả đúng mẫu số | Final tables và phần kết quả |
| 10.2.2 | 3h | A/B/C + Codex / người khác | Bảng/claims/annotation audit | Trace từng con số, kiểm 6 families/failures/grounding | claim-evidence.tsv reviewed |
| 10.2.3 | 2h | C + Codex / A và B | Error taxonomy và limitations | Viết thảo luận/kết quả âm/giới hạn API và dataset | Discussion/limitations cuối |
| 10.2.4 | 2h | Codex + C / B | Báo cáo đã audit và kịch bản 09 nếu có | Soạn slides bằng claims verified, trace số liệu | slides.md và claim audit |

## Trình tự thực hiện

1. Kiểm hash chain F1/F2 và manifest results trước đọc số liệu; mismatch trả 08, không sửa config tại 10.
2. Lập bảng bắt buộc IR-B/D/H và G0/GB/GD/GH; GR chỉ nếu được chốt trước F1 và có đủ records.
3. Đặt planned/actual/failed/stopped cạnh metrics để người đọc không hiểu nhầm thiếu ca.
4. Báo định vị và support/citation khác nhau; câu đúng nhãn nhưng unsupported không bị gọi fully grounded.
5. Trình bày 6 family deltas và case errors, giữ kết quả âm; không chỉ chọn ca tốt cho báo cáo.
6. Chèn chú thích pooled/unjudged/undefined; denominator của mỗi metric xuất hiện trong bảng hoặc caption.
7. Kiểm mỗi claim với source table; giảm mức kết luận nếu CI rộng/n nhỏ/evidence thiếu.
8. Ghi API alias có thể đổi và replay cache là mức tái lập khác fresh generation; công bố model/time thực.
9. Soạn slides sau khi claims verified; demo 09 case selection không thay aggregate từ 18 test.
10. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
11. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Hybrid thua | Primary delta âm | Báo đúng, thảo luận lỗi; không đổi contrast |
| Không relevant | IDCG = 0 trong vài ca | Undefined + eligible_n; không điền 0 để đủ 18 |
| Failed generation | 1/72 records provider_error | Giữ denominator và failure count |
| Sai đơn vị độc lập | Bootstrap claims hoặc 18 repetitions như mẫu độc lập | Fail claim; dùng 6 families theo protocol 08 |
| Citation valid nhưng yếu | ID đúng/support=no | Báo validity riêng support |
| Chi phí unknown | Timeout không usage | Không điền 0; báo known+unknown |
| Bảng khác artifact | Ô nhập tay sửa làm đẹp | Fail; sinh lại từ source đã khóa |

## Checklist thực hiện

- [ ] **10.2.1**: Final tables và phần kết quả; Codex + B / A xác nhận bằng chứng.
- [ ] **10.2.2**: claim-evidence.tsv reviewed; A/B/C + Codex / người khác xác nhận bằng chứng.
- [ ] **10.2.3**: Discussion/limitations cuối; C + Codex / A và B xác nhận bằng chứng.
- [ ] **10.2.4**: slides.md và claim audit; Codex + C / B xác nhận bằng chứng.
- [ ] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [ ] Đối chiếu tổng công task với 12h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [ ] Mọi số liệu chính có đường trace đến artifacts/version/mẫu số.
- [ ] Toàn bộ 18 test được hạch toán ở diagnosis và failures; Mẫu số IR hợp lệ được giải thích.
- [ ] Báo cáo và slides giữ sáu families, uncertainty, kết quả âm và giới hạn.
- [ ] Claim registry không còn result claim verified thiếu evidence.

## Gate nghiệm thu và điều kiện thất bại

G10-B: A kiểm dữ liệu/nhãn, B kiểm metric/provenance, C kiểm câu kết luận; thiếu kết quả 08 hoặc chain sai thì section liên quan pending, không viết bù.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Narrative lệch kết quả: registry bắt buộc trước slides. Error analysis gây test tuning: chỉ mô tả, thay đổi hệ thống chuyển thành deviation do 08 điều phối, giữ original runs.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 3 nhận report/slides/tables/claim audit đã review, cộng 09.demo khi có; chỉ hoàn tất gói nộp sau kiểm tái lập.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.

