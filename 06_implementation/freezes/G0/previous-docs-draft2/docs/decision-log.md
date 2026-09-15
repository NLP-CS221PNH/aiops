# Sổ quyết định — nguồn phản hồi còn pending

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2`.

[decisions.json](../configs/decisions.json) giữ toàn schema: decision_id, topic, options, chosen, status, owner, reviewer, due_relative_week, source_ref, decided_at_utc; permission_key liên kết quyền. Bảng dưới là bản xem cùng dữ liệu. Tất cả16quyết định đang pending, chosen/source_ref/decided_at_utc=null. A/B/C là vai trò đề xuất chưa thay tên người thật; owner khác reviewer. Mốc là cuối tuần tương đối, không là hạn môn học đã được xác nhận.

| ID | Quyết định / options | Owner / reviewer | Hạn | chosen / status | Việc tiếp theo |
|---|---|---|---|---|---|
| D01 | Rubric chính thức: Nhận rubric có nguồn của giảng viên; Ghi thiếu và theo dõi | C / B | W1 | null / pending | Nguồn rubric và tiêu chí NLP; ảnh hưởng scope/report. |
| D02 | Ngày bắt đầu và hạn nộp: Xác nhận ngày/hạn thật; Tiếp tục lịch tuần tương đối | C / A | W1 | null / pending | Không tự đặt deadline lịch; nhóm cung cấp nguồn. |
| D03 | Tên A/B/C và trách nhiệm: Nhóm xác nhận phân vai đề xuất; Nhóm đổi phân vai và review | C / A | W1 | null / pending | Tên người và trách nhiệm được từng người xác nhận; B review bổ sung. |
| D04 | Giờ cam kết mỗi người: Cam kết theo dự toán; Đổi lịch/cắt optional có review | C / B | W1 | null / pending | 15,4–18,7 giờ/người/tuần là nhu cầu tính toán, không cam kết. |
| D05 | Quyền sử dụng hosted API: approved; rejected; pending | C / B | W2 | null / pending | C lưu phản hồi giảng viên; thiếu phản hồi không là đồng ý. |
| D06 | Quyền gửi API payload: approved; rejected; pending | A / C | W2 | null / pending | Phản hồi theo phạm vi payload; mẫu export sẽ được plan02 kiểm, không gửi raw/gold. |
| D07 | Quyền dùng local/open-weight model: approved; rejected; pending | C / A | W2 | null / pending | Giảng viên xác nhận riêng; từ chối API không tự cấp quyền local. |
| D08 | Quyền data sharing/Kaggle/derivatives: approved; rejected; pending | A / C | W2 | null / pending | Xác định recipients/artifact/license/phạm vi; chưa upload gì. |
| D09 | Trần chi API thực tế: Nhóm xác nhận trần USD cụ thể; Không cấp ngân sách | C / B | W2 | null / pending | $10–15 là đề xuất; approved budget=null. Người có quyền chi cung cấp chứng cứ. |
| D10 | Generator và nhánh fallback: API đủ quyền/payload/budget; Local đủ quyền và pilot khả thi; Xin amendment retrieval/extractive | C / B | W2 | null / pending | Chọn trước pilot thực; nếu mọi model bị cấm thì RQ3 chưa chạy, xin đổi scope. |
| D11 | Ngôn ngữ output đánh giá: English; Vietnamese | B / C | W1 | null / pending | Khóa một ngôn ngữ cho các conditions; báo cáo/demo có thể khác nhưng phải ghi. |
| D12 | Khai báo sử dụng AI: Theo quy định được giảng viên cung cấp; Chờ phản hồi và lưu AI contribution log | C / B | W1 | null / pending | Không gọi AI readings/judgments là công đọc/chấm người. |
| D13 | Kaggle quota/GPU và runtime: Đo quota/CPU/GPU thật được phép; Dùng CPU/cached workflow phù hợp | C / A | W2 | null / pending | Không bảo đảm quota ba tài khoản; model/data upload theo quyền riêng. |
| D14 | GR/reranker optional trước F1: Bỏ GR để bảo vệ MVP; Giữ GR khi dev evidence và công đủ | B / C | W5 | null / pending | Mặc định chưa chọn; khóa trước test, không quyết theo điểm test. |
| D15 | Năng suất annotation và phạm vi evidence: Giữ lịch sau calibration5ca; Cắt optional hoặc amendment có review | A / B | W2 | null / pending | Đo phút/pair, đọc ca và adjudication; không giảm core56/test18 mặc định. |
| D16 | Human review G0 và xác nhận handoff: Nhóm review/ký cùng phiên bản; Trả issues về owner rồi review lại | C / B | W1 | null / pending | A/B/C ký phạm vi tương ứng; không dùng automated PASS làm chữ ký người. |

## Quy tắc xác nhận

Với record có `permission_key`, khi xác nhận/từ chối phải bổ sung `permission_value`: chuỗi `approved` hoặc `rejected` cho quyền; số USD không âm cho ngân sách đã xác nhận. Giá trị phải khớp YAML/manifest. `chosen` là phương án được chọn trong `options`; với quyền enum nó phải bằng `permission_value`, còn ngân sách chọn phương án trong options và lưu số tiền ở `permission_value` (không suy số tiền từ câu văn). Lý do bổ sung ở `follow_up` hoặc `rationale`. Approval cần `status=confirmed`, source_ref và UTC thật; rejection cần `status=rejected` với cùng bằng chứng. Pending giữ permission_value thiếu hoặc null. Không chấp nhận confirmed với chosen=null hoặc quyền/amount mâu thuẫn.

Chỉ chuyển confirmed khi có chosen rõ, source_ref truy được và UTC phản hồi thật. Ghi một record riêng cho API use, API payload, local model, sharing và budget; một câu đồng ý chung không tự xác nhận các quyền còn lại. Quyết định từ chối giữ rejected và lý do/nguồn. Bản nháp thư không là source_ref của một approval. Không tự tạo thời điểm đã quyết khi thiếu dữ kiện.

C điều phối theo dõi mỗi buổi sync, ghi quá hạn/ảnh hưởng nếu thiếu phản hồi. Cuối W2 API còn pending/rejected thì IR/annotation tiếp tục; local cần quyền riêng; nếu mọi model bị cấm, đề xuất amendment retrieval/extractive và RQ3 not_run. Nếu8h/người/tuần chỉ192h cho8tuần, thiếu116–182h trực tiếp so308–374h; cắt optional chưa chắc đủ, phải thống nhất lịch/phạm vi.

## Các bất biến kế thừa từ plan

90incidents/30families; split54/18/18; core qrels dự kiến20/18/18 và hiện0human judgments; RQ2 passage nDCG@5, hybrid so stronger_dev_single, tie BM25; G0/GB/GD/GH bắt buộc; không test tuning. Đây là ràng buộc của plan người dùng yêu cầu, không phải quyết định quyền mới hoặc chữ ký nhóm. Source: [plan01](../../plans/260913-0057-cs221-01-scope-and-protocol/plan.md) và [contracts](../../plans/reports/260913-independent-plans-contracts.md).

## Nhật ký amendment

Bản draft.1 tạo artifacts và ghi mâu thuẫn nguồn cũ trong [protocol-review](protocol-review.md). Chưa có human decision nào được đóng. Khi thay đổi: tăng version, ghi lý do/ảnh hưởng/producer-consumer, giữ manifest cũ; sync JSON, YAML và các tài liệu trước hashing lại. Sau F1 thêm protocol deviation và không dùng test để chọn thay đổi.
