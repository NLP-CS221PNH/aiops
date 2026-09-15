# Thỏa thuận làm việc nhóm — bản đề xuất để review

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2` · **chưa có chữ ký người thật**.

Tám tuần tương đối, ba thành viên; W1 bắt đầu khi nhóm xác nhận ngày khởi động. Ngày/hạn môn học, tên A/B/C, giờ cam kết và lịch giờ cụ thể đều pending. Codex soạn/kiểm tooling; không đại diện chữ ký hoặc đọc bài của thành viên.

| Vai trò | Tên / giờ mỗi tuần | Sở hữu artifacts | Reviewer khác owner |
|---|---|---|---|
| A — dữ liệu/tri thức | pending / null | Plan02 export,03 corpus,06 annotation management | B kiểm contract/design; C kiểm IDs/provenance |
| B — retrieval/thực nghiệm | pending / null | Plan04 variants,05 runners,08 evaluator/F1/results | A kiểm leakage/splits; C kiểm khả năng tái lập |
| C — generation/tích hợp | pending / null | Plan01 protocol,07 provider/context,09 demo,10 report | B kiểm design/context; A kiểm nguồn/payload |

Review không đổi người sở hữu nhãn: passage qrels có hai người chấm độc lập và người thứ ba adjudicate. Đề xuất xoay theo batch10–20 ca: batch1 A+B/C, batch2 B+C/A, batch3 C+A/B. Giữ identities thật trong annotation; không ghi role A của file biểu mẫu như đương nhiên là thành viên A. Không cho người phát triển nhận feedback tuning từ test; ghi hạn chế tính độc lập của nhóm ba người. Không dùng AI judgments làm human judgments.

## Nhịp làm việc và lịch dự kiến

Hai buổi đồng bộ ngắn mỗi tuần, đề xuất thứ Ba và thứ Sáu20phút; một artifact review45phút cuối tuần. Đây là slot đề xuất giờ địa phương Asia/Saigon, chưa phải lời mời đã gửi. UTC ISO-8601 lưu cho review/decision/run receipts. C gom agenda, owner mang artifact+hash+check; reviewer trả lại issue có bước tái hiện, không chỉ nhận xét miệng. Ghi những gì đã có, chưa chạy, failures và pending trong cùng handoff.

| Tuần | Công việc / checkpoint | Owner / reviewer |
|---|---|---|
| W1 | Charter/protocol, rubric, phân vai, review G0; thư hỏi giảng viên do nhóm gửi | C / A+B |
| W2 | Export/corpus/query pilot; calibration5ca, đo phút/judgment; quyết định API/local/budget cuối tuần | A+B / C; quyền do C theo dõi |
| W3 | Ba runners, pool đa phương pháp; chấm đôi20train và bắt đầu dev | B / A; cả nhóm chấm |
| W4 | Hoàn thành18dev qrels; generator có phép, no-RAG/RAG pilot | A+C / B |
| W5 | Dev selection; cắt/chọn GR; F1 khóa hệ thống | B / A+C |
| W6 | Test inputs/pool sau F1;18test chấm đôi/F2; final generation đúng quyền | B+A / C |
| W7 | Output review, sáu family deltas, lỗi, demo/report | B+C / A |
| W8 | Tái tính bảng từ archive, diễn tập, release/nộp do nhóm xác nhận | C / A+B |

## Công và khả năng thực hiện

| Plan | Giờ-người dự kiến | Owner |
|---|---:|---|
| 01 scope/protocol | 12 (3+6+3) | C |
| 02 data/environment | 24 | A |
| 03 corpus | 24 | A |
| 04 representations | 20 | B |
| 05 retrieval | 36 | B |
| 06 annotation | 84–150 | A điều phối; cả nhóm |
| 07 generation | 28 | C |
| 08 evaluation | 40 | B |
| 09 demo | 12 | C |
| 10 report/release | 28 | C |
| Tổng trực tiếp | 308–374 | Chưa phải cam kết |
| Cộng20% dự phòng | 370–449 (làm tròn) | Chưa phải giờ thực |

Đơn vị giờ-người: 15,4–18,7h/người/tuần trong tám tuần. Nếu mỗi người chỉ8h/tuần, tổng192h; thiếu116–182h trực tiếp,178–257h có dự phòng. C phải thu giờ thật và đề xuất đổi lịch/phạm vi; không tự hứa đủ chỉ nhờ Codex. Giữ qrels core56/test18, ba retrievers, no-RAG và failure accounting. Cắt lần lượt trang trí UI, encoder thứ hai, snapshot/cross-system ablation, reranker, representation ngoài dev và34train mở rộng; nếu vẫn thiếu thì amendment.

Plan06 dự toán56×30–40 candidates×2 =3.360–4.480 lượt chấm trước các khoản quản lý;45–75giây/lượt là giả định, không measured rate. Đo sau5ca calibration: số pairs sau dedup, phút đọc incident/evidence, phút/judgment, adjudication và missing-evidence rate. Không cap pool để bỏ final top-5. Annotation84–150h không tính human output review plan08 lần nữa. Human output review một lượt72/90responses, thêm24/30lượt của sáu incidents đã chọn trước F1.

## Bài lõi, thay đổi và tiếp nhận

[Literature matrix](literature-matrix.tsv) ghi nguồn, phương pháp dùng, giới hạn và mức đọc thật của Codex; human reviewer/reader assignment chỉ là đề xuất. A nhận benchmark/AIOps, B lexical/dense/fusion, C RAG/grounded evaluation; mỗi người ghi tên, phần đã đọc và xác nhận liên hệ artifact của mình. Không gọi các selected sections là full_text hoặc xem10 hàng matrix là10 bài nhóm đã đọc.

Khi source/hash lệch: dừng dùng artifact bị ảnh hưởng, ghi issue, owner tạo phiên bản+changelog rồi reviewer kiểm lại. Sau F1 ghi protocol deviation và đối xứng conditions. C tập hợp [pending decisions](decision-log.md) tại mỗi sync; quá hạn ghi overdue và ảnh hưởng, không tự chuyển confirmed.

| Người/role | Chấp nhận trách nhiệm/giờ | Đã đọc bài và review artifacts | UTC / bằng chứng |
|---|---|---|---|
| A / tên pending | pending | pending | null / null |
| B / tên pending | pending | pending | null / null |
| C / tên pending | pending | pending | null / null |

Biểu mẫu này chưa là sign-off. C gửi handoff tới các thành viên; communication status hiện pending. Giảng viên quyết định quyền model/rubric, nhóm quyết trần chi và trách nhiệm theo thẩm quyền; mỗi quyết định cần chứng cứ lưu được.
