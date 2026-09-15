# Đề cương đề xuất

## 1. Tên và câu hỏi nghiên cứu

**Evidence-Grounded Incident Triage and Root-Cause Diagnosis for Microservices using Hybrid Retrieval-Augmented Generation.**

Tên tiếng Việt: **Phân loại sự cố và hỗ trợ chẩn đoán nguyên nhân gốc cho microservices bằng Hybrid RAG có dẫn chứng.**

Câu hỏi chính: với cùng dữ liệu đầu vào, cùng generator và cùng ngân sách context, cách truy hồi kết hợp tín hiệu từ khóa lỗi và ngữ nghĩa có giúp tìm được bằng chứng phù hợp, từ đó cải thiện chẩn đoán và giảm câu khẳng định không có căn cứ, so với BM25 hoặc dense retrieval riêng lẻ không?

Đây là giả thuyết để kiểm nghiệm, không phải kết quả đã được chứng minh trên dữ liệu của đồ án.

## 2. Phạm vi NLP nên bảo vệ

Đóng góp cốt lõi là biểu diễn sự cố từ log bán cấu trúc, truy hồi tài liệu/historical incidents, và sinh giải thích có liên kết bằng chứng. Metrics và traces là ngữ cảnh bổ trợ để hiểu quan hệ dịch vụ; đồ án không cần phát triển đồng thời một mô hình time-series mới và một thuật toán causal discovery mới.

Đầu vào dự kiến: mô tả sự cố hoặc câu hỏi, khoảng thời gian quan sát, danh sách log đáng chú ý, service/resource identifiers và vài tín hiệu observability đã tổng hợp. Đầu ra dự kiến: top-k service hoặc fault type nghi ngờ, các mảnh bằng chứng với ID, lời giải thích bị giới hạn bởi bằng chứng, thông tin còn thiếu và bước kiểm tra tiếp theo.

Nhãn `anomaly`, nhãn `root_cause_service`, qrels truy hồi và nhãn chất lượng lời giải thích là bốn sản phẩm khác nhau. Không dùng nhãn này thay nhãn kia. [RCAEval](https://github.com/phamquiluan/RCAEval) công bố service/indicator ground truth; [Loghub](https://github.com/logpai/loghub) là bộ sưu tập log cho nhiều tác vụ, không tự cung cấp qrels incident→runbook.

## 3. Ba câu hỏi đủ cho một đồ án

**RQ1 — Biểu diễn:** giữ log thô, chuẩn hóa có giữ thực thể, hay tóm tắt thành incident bundle tạo khác biệt thế nào với retrieval? Điều kiện cần giữ: cùng cửa sổ thời gian và không đọc gold khi tạo bundle.

**RQ2 — Truy hồi:** hybrid có cải thiện recall bằng chứng so với BM25 và dense hay không? Cross-encoder reranking có cải thiện ranking đủ để bù độ trễ không? Dùng cùng corpus, qrels, k và ngân sách context để so sánh.

**RQ3 — Sinh câu trả lời:** bằng chứng truy hồi tốt hơn có chuyển thành câu trả lời đúng và có trích dẫn tốt hơn không? Cần đánh giá cả trường hợp bằng chứng thiếu; không thưởng việc đoán chắc khi không có căn cứ.

## 4. Dữ liệu và phạm vi thực nghiệm đề xuất

MVP: khảo sát **RE2-Online Boutique của RCAEval** trước; giữ **RE2-Train Ticket** cho đánh giá khác hệ thống nếu đủ dữ liệu và thời gian annotation. Theo bảng nguồn, hai tập này có log, metric và trace; Sock Shop không có trace trong RE2/RE3. Các bản Parquet/Zenodo/TORAI có quan hệ xử lý lại, không được chia thành nguồn train/test độc lập. [Nguồn](https://github.com/phamquiluan/RCAEval#available-datasets).

Kho tri thức: chọn một lượng nhỏ runbook/tài liệu đúng hệ thống và lịch sử incident thuộc train/dev. Kubernetes troubleshooting và Prometheus runbooks là nguồn tài liệu ứng viên; **không mặc định tài liệu Kubernetes giải thích được mọi lỗi ứng dụng Online Boutique**. Một bước mapping thủ công xác định độ phù hợp là bắt buộc. [Kubernetes](https://kubernetes.io/docs/tasks/debug/) · [Prometheus runbooks](https://github.com/prometheus-operator/runbooks).

Phương án NLP dự phòng: **TechQA hoặc MTRAG Cloud** cho retrieval và grounded QA; **ITBench-Lite/SRE** cho tình huống vận hành offline. Nếu không có telemetry và gold RCA tương ứng, đổi phạm vi thành *incident/technical QA assistance*, không giữ tuyên bố đã giải được causal RCA. [TechQA](https://huggingface.co/datasets/PrimeQA/TechQA) · [MTRAG](https://github.com/IBM/mt-rag-benchmark) · [ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite).

## 5. Kiến trúc tối thiểu

```text
Incident query + observation window
  → lọc telemetry theo thời gian
  → chuẩn hóa log nhưng giữ service/error code/exception
  → incident bundle có provenance
  → BM25 và dense retrieval trên cùng knowledge snapshot
  → hợp nhất ranking; reranker là nhánh ablation
  → chọn context theo ngân sách token, không cắt mất citation ID
  → generator cố định, chỉ trả lời từ bằng chứng
  → đầu ra có root-cause candidates + citations + unknowns
```

Không đưa hàng triệu dòng log trực tiếp vào prompt. Chọn lọc và tổng hợp phải tái lập được, có thể truy ngược đến span log gốc. Một bản tóm tắt do LLM tạo là dữ liệu suy diễn, không được nâng thành quan sát thật hay nhãn chuẩn.

Đề xuất baseline hybrid bằng rank fusion thay vì cộng trực tiếp hai score không cùng thang. Chọn bi-encoder và reranker sau khi đọc model card/license; các tên như BGE/e5 là ứng viên, không phải lựa chọn tốt nhất đã đo trên đồ án. Ghim model revision, normalization, tokenizer và các query prefix trong cấu hình tương lai.

## 6. Đầu ra có cấu trúc

Một response record cần có `incident_id`, `candidate_causes`, `evidence_ids`, `supported_claims`, `missing_information`, `next_checks`, `abstain` và `confidence_label`. Confidence label không được quảng cáo là xác suất đã hiệu chỉnh nếu chưa có calibration experiment. Không hiện ra chuỗi suy nghĩ nội bộ; chỉ hiện căn cứ kiểm tra được và kết luận.

Bước khắc phục chỉ ở dạng khuyến nghị để người dùng xem xét. Không tự thực thi shell, thay đổi Kubernetes, khởi động lại dịch vụ hoặc xóa dữ liệu. Nội dung retrieved document được coi là dữ liệu không tin cậy; một câu hướng dẫn trong log không được trở thành chỉ thị điều khiển hệ thống.

## 7. Sản phẩm dự kiến khi triển khai sau này

Một corpus có provenance/version; bộ incident bundles; qrels và rubric; bảng baseline có confidence intervals; demo truy vấn có trích dẫn; phân tích lỗi trên các case thành công/thất bại. Đây là những đầu việc tương lai, **không phải các file dữ liệu hay kết quả đã có trong ZIP**.

Không cam kết phần trăm giảm MTTR, phần trăm giảm hallucination, hay chi phí GPU khi chưa chạy đo. Tiêu chí thành công đầu tiên là thí nghiệm công bằng, không rò rỉ, có nguồn và có thể tái lập.
