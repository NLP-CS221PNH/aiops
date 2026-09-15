# Tiến độ plan 01 và bàn giao phần Codex

Ngày thực hiện: 2026-09-13 (receipts dùng UTC). Protocol `cs221-aiops-rag-protocol-v1`, candidate `1.0.0-draft.2`.

**Plan 01 in-progress; G0 project_start awaiting_human_review.** Phần tài liệu/tooling đã được soạn và ánh xạ đủ 12 task. Chưa có task hỗn hợp Codex + người nào được nghiệm thu đầy đủ: 0/12 task accepted, 0/3 phase accepted. Không chuyển thiếu phản hồi thành chấp thuận.

## Sweep toàn plan và bằng chứng

Đã đọc/sync [plan.md](../../plans/260913-0057-cs221-01-scope-and-protocol/plan.md) và cả ba phase, bổ sung execution evidence cho mọi task, giữ nguyên acceptance gốc. `ak plan status` báo `in-progress`, 3 phases, 0 phases done, 30 checkbox items, 0 done, progress 0%. Đây là tỷ lệ acceptance nguyên bản; không diễn giải thành chưa có sản phẩm kỹ thuật, cũng không tự cộng phần tài liệu để nâng tỷ lệ nghiệm thu.

| Task | Phần kỹ thuật đã có | Phần chưa hoàn tất / owner-reviewer |
|---|---|---|
| 01.1.1 | [Charter](../docs/project-charter.md): 3 RQ, phạm vi offline, input/output và giới hạn causal | C/B chấp nhận phạm vi |
| 01.1.2 | [Source audit](../validation/source-inventory.json): đếm/join trực tiếp 90/30, split54/18/18, test6families, 0judgments; source hashes | A/C review inventory/boundary |
| 01.1.3 | [Instructor draft](../docs/instructor-questions-draft.md): rubric/API/payload/local/AI disclosure; chưa gửi | C/A review; nhóm tự gửi, thu phản hồi có nguồn |
| 01.1.4 | [Decision log](../docs/decision-log.md), [16records](../configs/decisions.json): owner/reviewer/hạn, status pending | C/A/B xác nhận danh tính và trách nhiệm; cung cấp quyết định thật |
| 01.2.1 | [Research protocol](../docs/research-protocol.md), [YAML](../configs/protocol.yaml): primary/secondary, denominator, failed runs, F1/F2 | B/A review thiết kế và chấp nhận |
| 01.2.2 | [Literature matrix](../docs/literature-matrix.tsv), [notes](../docs/literature-reading-notes.md): 10 bài, selected sections do Codex đọc, nguồn/hash/giới hạn | A/B/C đọc phần được giao; reviewer khác xác nhận; human statuses pending |
| 01.2.3 | [Working agreement](../docs/team-working-agreement.md): lịch tương đối, sync/review, chấm đôi/adjudicate, dự toán nguồn lực | C/A/B xác nhận tên, giờ và lịch làm việc |
| 01.2.4 | [Decisions](../configs/decisions.json), [YAML](../configs/protocol.yaml): API/local/extractive theo quyền riêng, deadline W2 | C/B chốt quyền, payload, budget và generator bằng chứng; không tự chạy |
| 01.3.1 | [Protocol review](../docs/protocol-review.md), validator và tests: issues/dispositions, checks và negative cases | B/A review kết quả kỹ thuật và disposition |
| 01.3.2 | Review-record schema, pending person/time/source_ref và scope A/B/C trong [review](../docs/protocol-review.md) | A/B/C thực hiện review và ký bằng chứng đúng artifact version/hash |
| 01.3.3 | [Builder](../scripts/build_g0_manifest.py), [candidate manifest](../freezes/G0/manifest.json): explicit allowlist artifacts, provenance, pending permissions/reviews | C/B kiểm candidate; chờ human acceptance; vị trí freezes/G0 không chứng minh accepted |
| 01.3.4 | [Handoff table02–10](../docs/protocol-review.md), báo cáo này và journal local | C tổ chức bàn giao; A/B và bên nhận acknowledge; chưa có communication gửi/nhận |

## Kiểm tra và các giới hạn kết quả

- Source inventory audit đã kiểm 16 điều kiện từ dữ liệu cấu trúc; giữ đúng 0 human judgments. Chỉ kiểm raw paths/sizes và provenance flags, không tuyên bố đã rehash toàn bộ 922,484,805 bytes trong lượt này.
- [Technical validation](protocol-validation.json) thực chạy lúc 02:19:13 UTC: exit0, `technical_valid:true`, `g0_ready:false`, `errors:[]`. [Strict G0 readiness](g0-readiness.json) exit1 đúng yêu cầu, chỉ còn human A/B/C review, protocol draft và G0 chưa accepted; không có lỗi kỹ thuật.
- [Test report](plan01-tests.md) ghi 35/35 unit/mutation tests và 7/7 builder lifecycle checks PASS; các ca approval thành công là fixture synthetic, không phải chữ ký thật. [Independent code review](code-review.md) ghi phạm vi review và các sửa đã kiểm. `technical_valid` tách khỏi `g0_ready`.
- `ak plan validate` thực chạy, exit0, `valid:true`; `ak plan status` thực chạy và trả số acceptance ở trên. CLI reindex thành công, nhận diện đúng plan01 với ID `./260913-0204-2` và ba phases.
- Dự toán 12 giờ-người (3+6+3) là ước lượng trong plan, không phải thời gian làm việc con người hoặc Codex đã đo. Không có benchmark, API/model run, human annotation hay thư gửi trong delivery01.

Lệnh từ gốc research pack:

```powershell
python -B 06_implementation/validation/source-inventory.py
python -B -m unittest discover -s 06_implementation/tests -p test_validate_protocol.py -v
python -B 06_implementation/scripts/validate_protocol.py --output 06_implementation/reports/protocol-validation.json
python -B 06_implementation/scripts/validate_protocol.py --require-g0 --output 06_implementation/reports/g0-readiness.json
```

Lệnh strict cuối trả exit1 khi human review chưa đủ; đó là trạng thái nghiệm thu thực cần giải quyết, không phải lý do hạ điều kiện check. Manifest không tự refresh trong validator; candidate draft.2 đã tạo sau source-plan sync, SHA-256 `67d644d1ef8cc484636761ba4fe1863d9095a74810b06f7198d6ebc264d5f60c`, giữ candidate draft.1 qua supersedes.

## CLI sync và journal

Đã chuẩn hóa duy nhất CRLF cuối plan.md sang LF rồi dùng `ak plan update './260913-0204-2' --status in-progress --json`. Lỗi “no front-matter block to update” được tái hiện với bản byte gốc: frontmatter LF nhưng cuối file có CRLF. Uniform LF/CRLF đều chạy được; source không có BOM. [Fixture receipts](../.work/cli-frontmatter-fixtures/results.json) ghi bằng chứng và giữ nguyên source trong lúc debug.

`ak plan phase update ... --notes/--evidence` đã ghi cả ba phase, sau đó `ak plan reindex --path . --apply --json`. Live CLI help xác nhận phase status thuộc checkbox, không cho cập nhật status riêng. `ak plan check` sẽ check mọi item, nên không dùng: original phase frontmatter/table vẫn pending, index hiển thị `todo`, còn notes/evidence ghi kỹ thuật đã thực hiện và human acceptance còn thiếu. Đây là giới hạn hiển thị tiến độ của CLI, không phải claim phase complete.

Reindex chỉ đồng bộ index từ các plan files; chỉ bốn source files của plan01 được sửa nội dung trong phần sync-back này. Không sửa file plan02 hay artifacts task khác. Không có `.git`, nên current-plan pointer/commit không áp dụng; không Git init và không yêu cầu commit.

[Journal local](../../plans/journals/2026-09-13-cs221-plan01-protocol-review-handoff.md) được tạo bằng `ak journal create --stdin` và kiểm bằng `ak journal validate`; đường dẫn và receipt nằm trong [finalization receipt](plan01-finalization.json). **AgentWiki publish skipped.** Không publish hoặc gửi nội dung cho người khác.

## Việc cần nhóm cung cấp để tiếp tục nghiệm thu

1. **Cuối W1 — C điều phối:** rubric và ngày bắt đầu/hạn nộp (D01–D02); tên A/B/C, trách nhiệm và giờ thực có (D03–D04); ngôn ngữ output và khai báo AI (D11–D12).
2. **Review G0 — A/B/C:** đọc các phần literature được giao, kiểm charter/protocol/working agreement, ghi person/scope/time/source_ref gắn version/hash; C thu receiver acknowledgments (D16). Cung cấp tên đơn thuần không chứng minh đã review.
3. **Cuối W2 — C/A/B theo owner:** quyền hosted API, quyền payload, local/open weights, sharing/Kaggle/derivatives, trần chi, generator và quota/runtime (D05–D10,D13). Mỗi quyền có nguồn riêng; $10–15 chỉ là đề xuất.
4. **Downstream:** A/B đo annotation calibration/evidence coverage (D15,W2); B/C quyết định reranker optional trước F1 (D14,W5). Chưa có qrels hoặc output judgment người thật; các việc này không bị giả hoàn tất trong plan01.

Các tài liệu/tooling và mandatory sync-back/report/journal có thể bàn giao để review. Toàn bộ goal contract của plan01 vẫn còn human acceptance; thiếu giảng viên/API chỉ chặn phần mô hình tương ứng, không biến mọi chuẩn bị IR/data thành không thể làm.
