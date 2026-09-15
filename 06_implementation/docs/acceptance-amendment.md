# Amendment G0 — tự nghiệm thu theo yêu cầu người dùng

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-reviewed.1`.

Người dùng chỉ dẫn trực tiếp: **“tự check mọi thứ, không cần human input”**. [Authorization record](../configs/acceptance-authorization.json) lưu nguyên văn, phạm vi và thời điểm ghi nhận UTC. Chỉ dẫn mới thay yêu cầu human review/sign-off trong nghiệm thu **plan01** bằng Codex tự kiểm và agent độc lập review. Đây là thay đổi được người dùng yêu cầu, không phải suy ra từ việc im lặng hoặc từ `--auto` trước đó.

## Phạm vi được thay

| Điều kiện cũ của plan01 | Điều kiện áp dụng sau amendment | Bằng chứng cần có |
|---|---|---|
| A/B/C ký charter, inventory và protocol | Codex kiểm đầy đủ, agent độc lập review phạm vi dữ liệu/design/nguồn lực | Receipt có reviewer, scope, UTC, kết luận và hashes |
| Người thật đọc/review literature trước nghiệm thu | Codex đọc mức thực tế và reviewer kiểm primary-source/giới hạn | 10 hàng matrix, sections đã đọc, nguồn local/web, hashes local |
| Chờ tên và giờ thực tế của nhóm | Kiểm phân vai A/B/C, owner khác reviewer, lịch và kịch bản đủ/thiếu giờ; giữ tên/giờ chưa biết | Working agreement và phép tính nguồn lực; không bịa cam kết |
| Bên nhận ký handoff | Codex kiểm contract đầu vào/đầu ra của từng plan02–10 và version/hash | Bảng handoff cùng receipt review; không gọi đó là phản hồi con người |
| G0 phải có human reviewers | `review_mode=automated`, authorization hợp lệ và review PASS gắn đúng bytes | `--require-g0` PASS; human `reviewers=[]` và `pending_reviews=[]` trong mode này |

Các deliverables và 12 task giữ nguyên nội dung khoa học: charter, protocol MD/YAML, decision log, 8–12 bài lõi, working agreement, thư nháp, review issues, manifest và handoff. Tất cả acceptance của plan01 được đối chiếu theo bảng trên. Thu thập dữ kiện chưa biết được hoàn tất ở mức sổ pending có owner/hạn, đúng quyền tự quyết hiện có; không tạo dữ kiện giả để đóng chúng.

## Những dữ kiện và ràng buộc giữ nguyên

90 incidents/30 families, split54/18/18, core qrels dự kiến20/18/18, 0 human judgments; passage nDCG@5; stronger dev single/tie BM25; G0/GB/GD/GH và GR optional; không tune test; F1→test_input→test_pool→F2→test_scoring. Nghiên cứu vẫn là hỗ trợ incident offline, không tuyên bố causal chain hay MTTR.

Human labels/reference/support judgments trong các plan thí nghiệm sau vẫn là công việc khác với review tài liệu của plan01. Matrix giữ human_read_status và human_review_status pending; reader thực tế là Codex. A/B/C là role thiết kế, tên thật/giờ thật vẫn null. Rubric/hạn môn học, quota và permission chưa có nguồn vẫn pending.

Yêu cầu tự kiểm không cấp quyền API/payload/local/data sharing hoặc một ngân sách mới. Quyền model vẫn pending và approved budget=null; allowed_work chỉ gồm data, corpus, representation, retrieval và annotation_preparation. Không gửi thư, upload dữ liệu, gọi model hoặc chạy thí nghiệm từ lượt nghiệm thu01. D16 là quyết định đổi review mode đã confirmed; 15 decision khác có owner/hạn và được bàn giao với trạng thái thật.

## Bằng chứng và thay đổi phiên bản

[Autonomous review receipt](../reports/plan01-autonomous-review.json) phải có result PASS, không blocking findings, đủ scopes và exact-byte hashes của documents/config được kiểm; reviewer khác người sửa tài liệu trong đợt amendment này. [Validator](../scripts/validate_protocol.py) tiếp tục giữ human mode mặc định và các test cũ. Automated mode chỉ hợp lệ khi có đúng authorization, receipt và nội dung hiện tại khớp hashes; thiếu hoặc sửa chúng phải fail.

Manifest reviewed.1 giữ draft.2 qua `supersedes`; docs draft.2 ở `freezes/G0/previous-docs-draft2/`. Contract plan/phase đã amendment được lưu nguyên bytes ở `freezes/G0/plan-source/` trước ghi trạng thái hoàn tất. Manifest hash các snapshot contract đó; live plan files tiếp tục là sổ tiến độ. Thay checkbox/trạng thái sau nghiệm thu không làm thay scientific contract snapshot. Sửa nội dung khoa học hoặc acceptance sau này cần amendment/version mới và review lại, không tự refresh hash để che drift.

Plan01 chỉ được đánh completed sau review, tests và strict G0 validation thật sự pass. Evidence về human approval không được tạo; kết luận nghiệm thu được ghi rõ là Codex dưới ủy quyền người dùng.
