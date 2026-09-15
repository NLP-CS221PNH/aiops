# Annotation, chia dữ liệu và chống rò rỉ

## Đơn vị dữ liệu

Một `incident_id` gom tất cả query, telemetry window, fault injection run và response liên quan. `scenario_family_id` gom các lần lặp gần giống nhau của cùng service/fault/configuration. `document_id` là tài liệu gốc; `chunk_id` là lát cắt có offsets; không dùng chunk như tài liệu độc lập khi đo document recall.

Tách ít nhất ba lớp: observations người vận hành nhìn thấy; labels dùng để đánh giá; knowledge snapshot được phép truy hồi. Tên thư mục chứa service/fault, `inject_time.txt`, `record.csv`, nhãn reason và annotation root cause thường có thể tiết lộ đáp án. Chúng thuộc nhánh labels, không đi vào text index hay prompt.

## Chính sách split đề xuất

Chia theo incident hoặc scenario family, không theo dòng log. Một lần tiêm lỗi và các query paraphrase của nó phải ở cùng split. Trong đánh giá khác hệ thống, giữ nguyên một hệ thống ngoài train/dev; không chỉnh query template sau khi xem đáp án test.

Nếu sử dụng lịch sử incident, thêm temporal split: tài liệu chỉ được truy hồi nếu đã công bố trước `available_at <= observation_cutoff`. `published_at` và `updated_at` khác nhau; bản sửa sau sự cố có thể tiết lộ root cause dù ngày đăng cũ. Không lấy tài liệu tại thời điểm hiện tại rồi nói mô phỏng triage thời gian thực trong quá khứ.

Nếu KB gồm runbook tổng hợp do nhóm tự viết từ train incidents, phải ghi `derived_from_incident_ids`. Không được tổng hợp từ test postmortems rồi dùng tài liệu mới đó làm “runbook độc lập”. Dữ liệu tổng hợp bằng LLM cũng phải thừa kế lineage của đầu vào.

## Qrels

Một query có thể cần runbook về triệu chứng, một incident tương tự và một mảnh telemetry đặc trưng. Chấm ở hai tầng document và evidence span:

| Nhãn | Quy tắc đề xuất |
|---|---|
| 0 | Không liên quan hoặc dẫn sai miền/phiên bản/triệu chứng |
| 1 | Liên quan nhưng không đủ trực tiếp hỗ trợ chẩn đoán hoặc bước kiểm tra |
| 2 | Trực tiếp hỗ trợ ít nhất một claim hoặc một bước loại trừ cần thiết |

Pool candidates từ BM25, dense và hybrid, xáo thứ tự, ẩn tên retriever. Hai người chấm độc lập một phần chung để thống nhất rubric; bất đồng adjudication lưu lại. Không để LLM judge duy nhất tạo và chấm luôn gold của chính nó.

Gold RCA có thể giúp người xây nhãn kiểm tra evidence, nhưng bản thân gold không được đi vào query generator của test theo cách tiết lộ đáp án. Phân biệt query mô phỏng được tạo từ observations với query tạo từ kết luận; loại thứ hai có nguy cơ quá dễ và phải báo riêng.

## Ca thiếu thông tin và negative examples

Có thể tạo condition “không có runbook phù hợp” bằng cách embargo tài liệu đủ bằng chứng trong một subset đã định nghĩa trước. Không được gọi một câu hỏi là unanswerable chỉ vì BM25 chưa tìm ra tài liệu. Tính answerable phải do người chấm hoặc quy tắc evidence đầy đủ kiểm tra độc lập.

Hard negatives nên giống error token nhưng sai service/version; giống service nhưng khác fault; đúng loại exception nhưng là downstream symptom chứ không phải nguyên nhân. Trước khi dùng làm negative, kiểm tra nó không chứa một bằng chứng hợp lệ khác bị bỏ sót.

## Lineage và near duplicates

Dùng checksum để nhận dạng file trùng, sau đó so normalized text/MinHash hoặc công cụ tương đương khi triển khai. Hai website mirror, hai định dạng CSV/Parquet, bản gốc và bản dịch không phải nguồn test độc lập. Giữ nhóm trùng ở cùng split. Với metadata paper, cách khử trùng hiện tại chỉ dùng identifier/title; đối chiếu authors/venue sâu hơn là phần chưa hoàn tất của bibliography, không được quảng cáo đã đảm bảo mọi journal extension đều độc lập.

## Quyền riêng tư và an toàn dữ liệu

Trước khi đưa log vào mô hình, kiểm tra token, credential, email, IP và identifier có thể liên kết người dùng. Redaction phải nhất quán trong một incident để vẫn nối trace/service nhưng không tiết lộ secret. Đừng làm mẫu log tự bịa giống token thật; dữ liệu demo sau này phải ghi synthetic.

Không gửi telemetry chưa được phép lên dịch vụ bên ngoài. Không thực thi nội dung retrieved documents, pickle, notebook hay loader do nguồn cung cấp mà chưa kiểm tra. Không thử fault injection trên hạ tầng thật; đồ án mặc định chỉ đọc và gợi ý.

## Checklist chốt test

Kiểm tra từng split không giao `incident_id/scenario_family_id`; không lọt gold vào index/prompt; mọi tài liệu có mốc `available_at`; mọi bản dịch/summary có lineage; qrels và gold response không dùng cùng pipeline với mô hình được chấm; model revision và corpus hash được khóa; test metrics chưa được dùng chọn cấu hình; quyết định loại case có log lý do từ trước khi xem kết quả.
