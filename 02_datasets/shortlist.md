# Shortlist: chọn ít nguồn đúng vai trò trước

Catalog lớn để có lựa chọn, không để thu thập tất cả. Nhãn P0/P1 là **ưu tiên đề xuất của gói**, không phải bảo đảm license đã được tác giả xác nhận ở mọi cấp hoặc dữ liệu tải được thành công.

| Nguồn | Vai trò ưu tiên | Điều kiện phải giải quyết |
|---|---|---|
| [D001 RCAEval](cards/D001.md) / RE2-OB | Gold service/fault và telemetry để đánh giá RCA | Xây qrels riêng; không cho model thấy tên thư mục/nhãn injection |
| RCAEval RE2-TT | Test khác hệ thống | Không chỉnh pipeline sau khi nhìn test labels |
| [D051 ITBench-Lite](cards/D051.md) / SRE | Tình huống vận hành offline | Kiểm tra schema và nhãn của 35 scenario SRE trước khi chốt task |
| [D032 TechQA](cards/D032.md) | Technical QA/retrieval có corpus | Dùng đúng PrimeQA/TechQA; kiểm tra splits và quyền TechNotes |
| [D027 MTRAG](cards/D027.md) / Cloud | Hỏi đáp nhiều lượt về tài liệu kỹ thuật | Phân biệt quyền repo và từng corpus; không coi đây là telemetry RCA |
| [D058 Kubernetes docs](cards/D058.md) | Kho tri thức vận hành | Version/date pin và relevance mapping theo hệ thống |
| [D059 Prometheus runbooks](cards/D059.md) | Alert→runbook evidence | Mapping alert chưa phải gold đúng root cause |
| [D005 Loghub](cards/D005.md), [D006 Loghub-2.0](cards/D006.md) | Parsing/representation/AD hỗ trợ | Điều khoản research/academic; không suy có gold RCA |
| [D002 OpenRCA](cards/D002.md) | Mở rộng query+telemetry | License raw data trên Drive chưa đủ rõ |
| [D024 MultiHop-RAG](cards/D024.md), [D043 RAGTruth](cards/D043.md) | Tham khảo qrels và hallucination labels | Khác miền vận hành; không nhập điểm benchmark phụ vào RCA score |

## Bộ ghép đề xuất A — RCA thật sự có gold tương ứng

RCAEval RE2-OB + một kho runbook đã mapping + train-incident history; test trên held-out incident families và nếu đủ nguồn lực thì RE2-TT. Không có bảo đảm rằng runbook công khai sẽ phủ đủ lỗi ứng dụng: pilot phải đo tỷ lệ câu hỏi có bằng chứng trước.

## Bộ ghép đề xuất B — NLP rõ, hạ tầng nhẹ hơn

TechQA hoặc MTRAG Cloud + hybrid retrieval + generator có citation/abstention; ITBench-Lite/SRE là nhánh vận hành bổ sung. Gọi đầu ra là technical/incident assistance. Chỉ thêm claim RCA khi gold chẩn đoán tồn tại và được tách đúng khỏi đầu vào.

## Bộ ghép đề xuất C — Log representation

Loghub/Loghub-2.0 + qrels do nhóm chấm cho log/incident similarity + baseline IR; thêm RAG chỉ khi có tri thức và answer references thật sự phù hợp. Đừng ghép ngẫu nhiên mọi log BGL với runbook Kubernetes rồi đánh giá như production RCA.

## Chưa chọn làm phụ thuộc bắt buộc

LEMMA-RCA: có xung đột NC/ND. GAIA: README Apache nhưng LICENSE GPL-v2. DeathStarBench: README GPL-v2 nhưng LICENSE Apache. OpenRCA 2.0: bài mô tả benchmark đọc được nhưng release/license chưa xác nhận. Yahoo S5 và SRE workbook: trang bị chặn trong đợt rà soát. Các nguồn này được giữ trong catalog cùng cờ, không bị ngụy trang thành sẵn sàng dùng.

## Cách quyết định sau khi tự tải mẫu

Ghi lại năm câu trả lời: quan sát nào model nhìn thấy; gold nào đánh giá được; corpus nào có bằng chứng phù hợp; license nào bao phủ đúng các file; chi phí xử lý thực tế của một incident là bao nhiêu. Nếu chưa trả lời được một trong ba câu đầu, ưu tiên thay task hoặc dữ liệu hơn là tăng độ phức tạp mô hình.
