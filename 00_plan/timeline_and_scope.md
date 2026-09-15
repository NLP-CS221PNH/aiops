# Lộ trình đề xuất 8 tuần và điểm dừng

Đây là lịch giả định để lập kế hoạch, không phải lịch chính thức CS221. Quy mô nhóm, phần cứng và thời hạn thực tế chưa được xác nhận.

| Tuần | Việc chính | Đầu ra dự kiến | Điều kiện qua giai đoạn |
|---|---|---|---|
| 1 | Đọc nhóm P0, chọn một task và nguồn dữ liệu | Research question; data decision record | Có gold đúng loại và quyền sử dụng rõ |
| 2 | Kiểm tra mẫu, schema, sự kiện và leakage | Incident bundle schema; corpus scope | Tách observation và labels; không giả qrels |
| 3 | Annotation pilot và split | Rubric; qrels pilot; frozen grouping | Hai người hiểu nhãn nhất quán trên mẫu chung |
| 4 | BM25 và dense trên cùng corpus | Baseline IR, test script dự kiến | Có thể truy ngược từng hit đến document gốc |
| 5 | Hybrid và một generator cố định | Baseline RAG có citations | Prompt không đọc gold; citation ID hợp lệ |
| 6 | Rerank/representation ablations | Bảng thí nghiệm công bằng | Cấu hình chọn trên dev, không trên test |
| 7 | Test, human evaluation, error analysis | Metrics; uncertainty; failure cases | Đo theo incident và báo cả ca thiếu bằng chứng |
| 8 | Báo cáo, demo, tài liệu tái lập | Report, poster/slides nếu môn yêu cầu | Mọi claim kết quả có dữ liệu và nguồn |

## MVP bắt buộc

Một tập incident phù hợp, một knowledge snapshot có nguồn; BM25/dense/hybrid; một generator; qrels và gold RCA tách rời; đánh giá trích dẫn bằng người trên subset; failure analysis. Các phần này quan trọng hơn UI phức tạp.

## Phần mở rộng có thể bỏ

GraphRAG, multi-agent, fine-tuning LLM, tự động remediate, triển khai cloud thật và multilingual generation không nằm trên đường bắt buộc. Không làm đồng thời mọi phần chỉ vì có nhiều paper. Một ablation hoàn chỉnh thường đáng giá hơn một module mới nhưng thiếu đối chứng.

## Điểm dừng dữ liệu

Nếu source license chưa rõ: chuyển sang một source đã có điều khoản hoặc giữ nó ở danh sách pending; không tự coi quyền nghiên cứu là quyền công bố lại raw data.

Nếu dữ liệu chỉ có anomaly labels: giới hạn task ở anomaly/log retrieval hoặc tìm dataset RCA khác. Nếu chỉ có QA documents: đổi phạm vi sang technical/incident QA assistance. Không giữ tên causal root-cause analysis khi thiếu gold và evidence phù hợp.

Nếu không đủ công annotation qrels: giảm số incident/loại lỗi nhưng chấm tốt, báo cỡ mẫu; không dùng nhãn synthetic không kiểm tra để tạo ra một test set lớn có vẻ thuyết phục.

## Phân công theo vai trò

Vai trò dữ liệu chịu trách nhiệm provenance, license và split; vai trò IR chịu trách nhiệm embeddings/index và thí nghiệm retrieval; vai trò generation/evaluation chịu trách nhiệm prompt, citation, rubric và báo cáo. Một người có thể kiêm vai trò, nhưng cần một lượt kiểm tra chéo qrels/leakage không do chính người tạo nhãn tự duyệt.

## Hồ sơ quyết định tối thiểu

Mỗi quyết định nguồn/model/split có: ngày, lựa chọn, phương án đã loại, lý do, bằng chứng, rủi ro còn lại. Không sửa scope hoặc loại case sau test mà không ghi thay đổi và chạy lại mọi baseline ảnh hưởng.
