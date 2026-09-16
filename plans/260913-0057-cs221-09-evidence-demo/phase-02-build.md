---
phase: 2
title: "Xây viewer cục bộ và nối kết quả"
status: complete
priority: P1
effort: "6h"
dependencies: [1]
---

# Phase 02: Xây viewer cục bộ và nối kết quả

## Tổng quan

Dựng ứng dụng Python tối thiểu đọc manifest, observations, exact contexts và responses; hiển thị đầy đủ trạng thái và nguồn evidence.
Công dự kiến **6 giờ-người**; các checkbox là công việc tương lai.
Owner điều phối C; task ghi người thực hiện và reviewer. Codex soạn/xây/kiểm tooling, con người quyết định và chấm nhãn.

## Bối cảnh và đầu vào

Đọc [plan cha](plan.md), [hợp đồng chung](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-contracts.md) và [nghiên cứu](C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/plans/reports/260913-independent-plans-research.md).
Các đường dẫn trong `06_implementation` bên dưới là sản phẩm dự kiến; chưa tồn tại chỉ vì tài liệu kế hoạch đã viết.

| Đầu vào | Đường dẫn tuyệt đối | Điều phải kiểm |
|---|---|---|
| Case config | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/demo-cases.yaml` | Origin và result refs |
| Generation artifacts | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/runs/<run_id>/` | 07pilot hoặc08final có raw/parsed/context |
| Khung và kịch bản | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-runbook.md` | Ba vùng và nhãn trạng thái |
| Kết quả khóa | `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/results/` | Chỉ nối final khi08.results sẵn sàng |

## Yêu cầu

- Mặc định local127.0.0.1, route chỉ đọc và đường dẫn allowlist dưới artifact root; không mở public network.
- Chọn stack nhỏ nhất: app.py dùng Python/HTML cục bộ; ưu tiên thư viện chuẩn, không cần framework/dashboard.
- Escape toàn bộ raw text/log/model output trước render; không thực thi HTML/JS hoặc commands chứa trong evidence.
- Hiển thị run_id,condition,UTC,model,corpus/query hash,mode,status; lỗi có nội dung nguyên bản và lý do validator.
- Nhãn confidence chỉ là output model, không hiển thị như xác suất đã hiệu chỉnh.
- Live optional phải gọi adapter07 phía server trong quyền/cap đã có; không nhúng key vào HTML/frontend.
- Timeout live hiển thị lỗi; chuyển replay phải là thao tác rõ và có nhãn, không tự lấy response đẹp thay.

## Kiến trúc và ranh giới trách nhiệm

Local HTTP viewer read-only → loader resolve allowlisted artifact paths → manifest/hash check → view model → escaped HTML. Citation panel dùng actual context snapshot làm mặc định; registry chỉ giải thích nguồn.
Không gửi thư/tin nhắn bằng công cụ; nếu cần liên lạc thì Codex soạn nháp, nhóm thực hiện.
Không đưa root labels, qrels hay reference claims vào inference hoặc giao diện live.

## Các file liên quan

- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/demo/app.py` — Local entrypoint và render/route tối thiểu.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/src/demo/loaders.py` — Manifest/context/response validation.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/configs/demo-cases.yaml` — Nối artifacts thật khi có.
- **Sửa:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/docs/demo-runbook.md` — Cách mở, chuyển chế độ, troubleshooting.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/case-audit.tsv` — Case refs và hash checks.
- **Tạo:** `C:/Users/Siinn/Downloads/CS221_AIOps_RAG_Research_Pack/06_implementation/reports/demo/sample-screen.png` — Ảnh minh họa từ demo khi triển khai.
- **Xóa:** không có; giữ bộ nghiên cứu gốc và artifacts đã khóa để đối chiếu.

## Schema và giao diện bàn giao

- ViewModel:{case_id,origin,display_mode,incident_id,condition,status,raw_output,parsed_output?,metadata,observations,evidence_items}.
- EvidenceView:{evidence_id,actual_context_text,source_kind,document_id?,chunk_id?,rank?,source_revision,offsets,used_by_claim_ids}.
- Metadata:{run_id,generated_at_utc,model_requested,model_returned,context_hash,corpus_hash,latency_ms?,usage?}; thiếu dùng unavailable.
- Compare requires same incident_id+observations_hash+protocol/F1 version; condition khác là chủ đích.
- UIState:loading|ready|abstained|invalid_response|invalid_citation|provider_error|artifact_mismatch; fixture là origin độc lập với state.
- Audit TSV:case_id,run_id,condition,artifact_hash,context_hash,origin,citation_check,reviewer,note.
- Mọi timestamp là UTC ISO-8601; thiếu dữ kiện dùng null hoặc trạng thái pending theo schema, không tự điền số giả.
- Bên nhận đối chiếu version/hash trước dùng; lệch phiên bản phải fail rõ và trả lại owner.

## Các task triển khai

Cột thực hiện/reviewer tách bằng dấu “/”; Codex không đại diện cho chữ ký review người thật.

| ID | Công | Thực hiện / reviewer | Đầu vào | Hành động | Đầu ra |
|---|---:|---|---|---|---|
| 09.2.1 | 2h | Codex + C / B | Manifest/schema/case config | Xây loader chỉ đọc, validate hashes và origin | loaders.py |
| 09.2.2 | 2.5h | Codex + C / A | ViewModel và3vùng | Xây UI, selectors, citation panel, raw/error states | app.py và màn hình mẫu |
| 09.2.3 | 1h | C + Codex / B | 08final hoặc fixtures gắn nhãn | Nối cases/compare và kiểm exact context offsets | Case audit |
| 09.2.4 | 0.5h | C + Codex / A | Quyền/live adapter nếu sẵn | Thêm live chỉ khi có thể; nếu không dùng công kiểm replay | Runbook và mode check |

## Trình tự thực hiện

1. Chọn port cục bộ khả dụng lúc triển khai, ghi trong runbook; không giả server đã chạy trong kế hoạch.
2. Resolve result_ref từ config qua pathlib chuẩn hóa; reject .., absolute ngoài root hoặc missing path.
3. Lưu source_context riêng với corpus_full_text; panel mặc định cho thấy đúng phần generator đã nhận.
4. Render badges text đủ rõ: dữ liệu mô phỏng, phát lại kết quả đã lưu, gọi trực tiếp; không chỉ phân biệt bằng màu.
5. Khi claim có nhiều citations, cho mở từng evidence; unknown ID chỉ hiện invalid không link bừa.
6. Với invalid JSON, hiện raw escaped và lỗi; không tự sửa thành một câu trả lời sạch.
7. Khóa input của live theo allowlist và bắt buộc gesture; nếu0.5h không đủ thì bỏ live, nghiệm thu replay.
8. Khi08.results có, C đổi case config có review B; không thay artifact gốc để demo đẹp hơn.
9. Sau mỗi thay đổi, ghi quyết định và bằng chứng; không thay artifact gốc hoặc trạng thái gate âm thầm.
10. Khi bàn giao, người nhận đọc đầu ra cùng lỗi/chưa biết; nếu thiếu một điều kiện bắt buộc thì giữ task chưa hoàn tất.

## Ma trận kiểm tra có ý nghĩa

Những ca dưới đây là kịch bản nghiệm thu dự kiến; chưa có kết quả pass trong lần lập kế hoạch.

| Kịch bản | Đầu vào hoặc trigger | Kết quả bắt buộc |
|---|---|---|
| Evidence chứa script | <script> trong log/chunk | Hiện text, không thực thi |
| Path traversal | result_ref=../../private/gold | Loader reject ngoài allowlist |
| Manifest mismatch | Hash response/corpus lệch | artifact_mismatch; không im lặng dùng |
| Citation bị cắt | ID hợp lệ nhưng full text dài hơn context | Mặc định chỉ exact sent text; full source gắn nhãn |
| Output invalid | RawJSON truncated | Hiện lỗi/raw; không giả parsed hợp lệ |
| Mất mạng | Live timeout | Thông báo lỗi; replay chỉ sau chọn chủ động |
| Hai conditions | Cùngincident/obs hash, khác evidence | Compare hiển thị khác biệt retrieval đúng nguồn |

## Checklist thực hiện

- [x] **09.2.1**: loaders.py; Codex + C / B xác nhận bằng chứng tại `src/demo/loaders.py` và `tests/test_demo_loaders.py`.
- [x] **09.2.2**: app.py và màn hình mẫu; Codex + C / A xác nhận bằng chứng tại `src/demo/app.py` và `tests/test_demo_app.py`.
- [x] **09.2.3**: Case audit; C + Codex / B xác nhận bằng chứng tại `reports/demo/case-audit.tsv`.
- [x] **09.2.4**: Runbook và mode check; C + Codex / A xác nhận bằng chứng tại `docs/demo-runbook.md`.
- [x] Lưu các lỗi/chưa biết và cách xử lý; hoàn thành đầy đủ các artifacts của Phase 02.
- [x] Đối chiếu tổng công task với 6h; hoàn thành đúng dự toán và phạm vi.

## Tiêu chí thành công

- [x] Người xem đi từ claim tới exact context evidence trong vài thao tác rõ.
- [x] Replay dùng được không internet; paths và hashes không khớp báo lỗi.
- [x] UI không chạy instructions/HTML trong data và không lộ secrets.
- [x] Fixtures, final results và optional live phân biệt trực quan bằng text.

## Gate nghiệm thu và điều kiện thất bại

G09-B: loader/UI và replay đạt; live không bắt buộc. Case final chưa có thì ghi partial scaffold, chưa gọi09.demo hoàn tất.
Nếu fail, ghi issue có đầu vào tái hiện, owner, hành động và bằng chứng cần có; chạy lại phần liên quan sau sửa.
Không được bỏ ca khó, chọn output đẹp hoặc tự xác nhận quyền chưa có để vượt gate.

## Rủi ro và xử lý

Package khác máy thiếu dependency: ưu tiên standard library và runbook nhỏ. Corpus snapshot khác: fail hash có giải thích, không tự tải bản mới từ URL.
Giữ khối lượng MVP; phần mở rộng chỉ được lấy từ dự phòng khi không làm trễ annotation, đối chứng và bàn giao.

## Bàn giao và dừng

Phase 3 nhận app/runbook/config và case-audit; khi08.results chưa tới, chỉ tổng duyệt fixture, giữ nghiệm thu khoa học pending.
Người nhận ký vào record review khi triển khai; `pending` trong kế hoạch này không phản ánh việc đã nghiệm thu.
