---
phase: 3
title: "Tái lập, đóng gói và diễn tập bảo vệ"
status: done
priority: P1
effort: "10h"
dependencies: [2]
---

# Phase 03: Tái lập, đóng gói và diễn tập bảo vệ

## Tổng quan

Một thành viên khác tái tạo bảng chính từ artifacts trong môi trường mới, kiểm gói nguồn và diễn tập; tạo gói nộp local có manifest. Nhóm tự thực hiện việc gửi và nộp.
Công dự kiến **10 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Báo cáo và claims | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-report.md` | G10-B có audit đã review |
| Demo | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/demo-manifest.json` | 09.demo có run refs đã kiểm |
| Môi trường và code | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/` | Dependency locks, source versions, artifacts |
| Freeze và kết quả | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/freezes/` | F1/F2 chain và kết quả gốc |
| Rubric và quyền | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/decision-log.md` | Format nộp, quyền phân phối, khai báo AI |

## Yêu cầu

- Tính lại các metrics/bảng chính từ artifacts đã lưu là bắt buộc. Chạy lại IR từ raw/model và fresh generation là tùy chọn có receipt giới hạn; thiếu core metric inputs chặn scientific release hoặc cần scope amendment được nhóm duyệt rõ.
- Kaggle chạy Linux cần dependencies tương thích; không dùng Windows wheels của pack như môi trường có thể chuyển sang mọi máy.
- API không có revision bất biến: tái lập config và cache; fresh generation chỉ optional nếu được phép, không hứa output giống từng token.
- Mọi bảng phải khớp tolerance số chốt trước khi tái lập; rankings và ties theo F1 policy, không chọn tolerance sau khi thấy sai lệch.
- Gói local giữ licenses và attribution; nếu không được phân phối lại thì hướng dẫn tải hợp lệ. Không nhúng key hoặc private gold vào app.
- Report, slides, demo và hướng dẫn phải thống nhất version/số liệu; PDF cần kiểm font tiếng Việt, bảng bị cắt và links.
- Codex chuẩn bị gói và nội dung nháp; nhóm tự nộp theo quy định, không có email, publish hoặc upload tự động.

## Kiến trúc và ranh giới trách nhiệm

Manifest inputs → môi trường mới → receipts tái chạy/phát lại → xuất report/slides → audit license, secret, paths → gói local và checksum → nhóm review rồi nộp. Receipts tái lập tách khỏi artifacts thí nghiệm gốc.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/reproduce.md` — Hướng dẫn từng bước và đầu ra cần khớp.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/reproduction-receipts.md` — Môi trường, commands, hashes và sai khác.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/final-report.pdf` — Bản đọc theo format môn học.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/slides.pdf` — Bản trình bày nếu format yêu cầu.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/final-manifest.json` — Inventory, hash và version của gói.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/release-checklist.md` — Rubric, licenses, secrets, contributions.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/submission-package/evaluator-bundle/` — allowlist riêng: F2 qrels, service gold và split/family join, human support-review records, run rankings/manifests, responses/actual contexts và attempt/usage logs; hoặc access/acquisition recipe đã kiểm thật cho từng nguồn bị hạn chế. Bundle này tách khỏi inference/demo.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/submission-package/` — Gói local có checksum; chưa gửi.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- ReleaseManifest:{release_id,created_at_utc,protocol_id,F1_hash,F2_hash,code_revision,environment_ref,artifacts:[{path,sha256,kind,license_ref}]}.
- Receipt:{operator,environment,step,command_or_action,input_hashes,expected,observed,pass,output_refs,limitations}.
- Numerical receipt nêu tolerance đã chốt; đề xuất 1e-8 absolute khi cùng inputs/libraries, môi trường khác cần giải thích trước chấp nhận.
- Reproduction scope:retrieval_rerun|metric_rerun|generation_replay|generation_fresh_optional; cached outputs không gắn nhãn fresh.
- Paths trong gói dùng tương đối để chuyển máy; manifest nội bộ giữ root/version, sản phẩm công khai không có đường dẫn cá nhân.
- Contribution record:{person,role,artifacts,reviewed_artifacts,human_annotation_scope,AI_assistance_disclosure}; người thật xác nhận.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 10.3.1 | 4h | A hoặc C không viết runner / B | Runbook, data locks, artifacts | Tạo môi trường mới, tái tạo IR/metrics, kiểm cache generation | Reproduction receipts |
| 10.3.2 | 2h | Codex + C / A | Report, slides, rubric | Xuất bản đọc, kiểm font/bảng/links và nội dung | PDFs local đã review |
| 10.3.3 | 2h | Codex + A / C | Artifacts, licenses, permissions | Audit inventory/secrets/paths/hashes, đóng gói local | Manifest, checklist và package |
| 10.3.4 | 2h | A/B/C / kiểm chéo | Slides, demo, claim registry | Diễn tập, xác nhận contributions và rubric coverage | Bàn giao sẵn sàng để nhóm nộp |

## Trình tự thực hiện

1. Người khác làm theo reproduce.md, ghi máy/Kaggle thực, commands và hashes; đọc hướng dẫn chưa phải bằng chứng tái lập.
2. Tính lại bảng chính từ allowlisted evaluator bundle: F2 qrels, gold và split/family join, support-review labels, rankings/manifests, responses/actual contexts, attempt/usage logs và frozen evaluator. Nếu nguồn bị hạn chế thì kiểm access/acquisition recipe tới nguồn thật trước nghiệm thu; chạy lại IR từ raw/model chỉ khi đủ tài nguyên.
3. So ranked IDs, tie policy và tolerance đã chốt; khác biệt trả owner 08 phân tích, không sửa số báo cáo bằng tay.
4. Nếu đủ quyền/ngân sách có thể chạy fresh generation một vòng nhỏ; receipt riêng và không thay headline final runs.
5. Xuất PDF/slide theo format môn học, kiểm trực quan bảng không cắt, font tiếng Việt đúng và số khớp Markdown.
6. Đóng gói docs/code/configs/results cùng evaluator bundle đã duyệt để tính lại bảng; tách evaluator data khỏi inference/demo và không glob cả data/private. Loại key/caches không cần, giữ licenses; nguồn hạn chế có recipe truy cập hợp lệ đã kiểm thay bản sao.
7. Verify checksum sau khi giải nén sang thư mục mới; kiểm reproduce và demo đọc được relative paths.
8. Diễn tập câu hỏi về leakage, baseline, qrels, sáu families, unsupported claims, quyền API và kết quả âm.
9. Nhóm xác nhận đóng góp và khai báo AI; người nộp kiểm deadline/format thực trước tự gửi.
10. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
11. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Máy mới | Không có cache path cũ | Runbook đủ bước; thiếu nguồn được báo rõ |
| Windows wheel trên Kaggle | Wheel win_amd64 | Dùng resolver/lock Linux phù hợp |
| API replay | Cached output giống hoàn toàn | Ghi replay, không kết luận fresh deterministic |
| Hash sau giải nén | Package thiếu hoặc đổi một file | Fail inventory, không bàn giao bản lỗi |
| PDF font/bảng | Tiếng Việt hoặc bảng qua trang | Kiểm trực quan và sửa bố cục |
| Nguồn không được chia sẻ | License cấm redistribution | Manifest và hướng dẫn tải hợp lệ thay bản sao |
| Câu hỏi bảo vệ | Tại sao chỉ có sáu families | Nhóm giải thích repetitions phụ thuộc và uncertainty |
| Thiếu qrels/gold/support labels | Gói có bảng CSV nhưng không có đầu vào evaluator | Chặn core metric gate; bảng kết quả sẵn có không thay tính lại |
| Chưa gửi bài | Có package và checklist local | Trạng thái ready, không gọi đã nộp |

## Checklist thực hiện

- [x] **10.3.1**: Reproduction receipts; A hoặc C không viết runner / B xác nhận bằng chứng.
- [x] **10.3.2**: PDFs local đã review; Codex + C / A xác nhận bằng chứng.
- [x] **10.3.3**: Manifest, checklist và package; Codex + A / C xác nhận bằng chứng.
- [x] **10.3.4**: Bàn giao sẵn sàng để nhóm nộp; A/B/C / kiểm chéo xác nhận bằng chứng.
- [x] Lưu các lỗi/chưa biết và cách xử lý; không đánh dấu complete vì chỉ viết được tài liệu.
- [x] Đối chiếu tổng công task với 10h; vượt dự toán phải ghi ảnh hưởng và cắt optional trước.

## Tiêu chí thành công

- [x] Người khác tính lại được bảng/metrics chính từ evaluator artifacts đã lưu; receipt giới hạn chỉ thay cho optional raw/IR/model reruns, không thay core metric recomputation.
- [x] Report, slides và demo khớp versions/claims; gói đủ manifest, checksum và hướng dẫn.
- [x] Không còn secret, vấn đề license chưa xử lý hoặc claim vượt quá evidence.
- [x] Nhóm đã review đóng góp và rubric; gói local sẵn sàng, nộp thật là bước của người được phân công.

## Gate nghiệm thu và điều kiện thất bại

G10-C/10.release: bắt buộc core metric recomputation đạt từ evaluator bundle hoặc nguồn hợp lệ truy cập được, cùng claim audit, 09.demo và package audit. Không hạ gate vì đến hạn; giới hạn được chấp nhận phải ghi rõ và có nhóm review, không giả test pass.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Nộp sát hạn: ưu tiên bảng chính, hướng dẫn và demo backup trước đồ họa. Core metric recomputation thất bại: chặn scientific release hoặc mở scope amendment có review rõ. Optional raw/model rerun thất bại: ghi giới hạn cụ thể, không hứa tái lập đầy đủ. API alias đổi: giữ cached artifacts.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Nhóm nhận gói local, checklist, report/slides/demo và receipts để tự nộp. Phần Codex kết thúc khi gói đã review; trạng thái nộp thật do người phụ trách cập nhật theo bằng chứng.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.


