# Kế hoạch thí nghiệm và đánh giá

**Tất cả cỡ mẫu, ngưỡng và lịch chạy dưới đây là đề xuất cần chốt sau pilot. Không có kết quả thực nghiệm trong file này.**

## Thiết kế theo giai đoạn

Pilot bắt đầu bằng 10–20 incident để kiểm tra parser/schema và annotation, không dùng số này làm tập test chính. Sau pilot, khóa split, corpus snapshot, nhãn và siêu tham số; chỉ chạy test khi các quyết định trên đã chốt.

Nếu chỉ dùng một tập RCAEval 90 ca, ưu tiên báo cáo hạn chế độ lớn và đánh giá theo nhóm lỗi. Có thể dùng group cross-validation trên train/dev nếu hợp lý, nhưng phải giữ một test độc lập với quá trình lựa chọn mô hình. Không gọi năm seed chạy trên cùng 90 ca là 450 incident độc lập.

## Ma trận tối thiểu

| Mã | Thành phần | Biến thay đổi | Yếu tố cố định |
|---|---|---|---|
| IR-1 | BM25 | lexical retrieval | corpus, qrels, incident queries |
| IR-2 | Dense | một bi-encoder | corpus, qrels, incident queries |
| IR-3 | Hybrid | rank fusion của IR-1/IR-2 | cùng candidate depth |
| IR-4 | Hybrid + reranker | cross-encoder trên candidate pool | cùng generator/context budget |
| GEN-0 | Không RAG | query + incident bundle | generator, decoding, bundle |
| GEN-1 | Naive RAG | một retriever | generator, decoding, token budget |
| GEN-2 | Hybrid RAG | bằng chứng từ IR-3 | generator, decoding, token budget |
| GEN-3 | Reranked RAG | bằng chứng từ IR-4 | generator, decoding, token budget |

GEN-0 vẫn được nhìn telemetry bundle vì nó là đầu vào task; “không RAG” không có nghĩa bị cắt mất chính dữ liệu sự cố. Nếu cho GEN-0 đọc toàn bộ tài liệu còn RAG chỉ đọc top-k, phải gọi đó là baseline long-context khác và báo rõ ngân sách.

## Ablation nên ưu tiên

**Biểu diễn query:** raw error lines; normalized logs giữ nguyên thực thể quan trọng; bundle theo thời gian/service; summary sinh bằng mô hình có ghi provenance. Bộ chuẩn hóa không được xóa error code, exception class hay service name là tín hiệu nhãn.

**Knowledge source:** runbook-only; historical-incident-only; kết hợp. Mọi nguồn phải có sẵn trước observation cutoff. Không có nguyên tắc rằng thêm corpus luôn cải thiện: một kho khác miền có thể chỉ tạo distractor.

**Fusion/reranking:** báo candidate pool size, k sau reranking và token budget. Thử một số ít cấu hình trên dev; không grid-search trên test. Chunking chọn theo cấu trúc tài liệu hoặc window có overlap; không trộn phần triệu chứng và phần kết luận gold từ test postmortem.

**Cấu hình mở rộng:** GraphRAG hoặc retrieval nhiều vòng chỉ sau khi baseline đạt trạng thái ổn định. Đặt budget số vòng và điều kiện dừng; các vòng không được đọc trường ground truth hay tài liệu bị embargo.

## Chỉ số IR và đơn vị tính

Với query q, Gq là tập evidence/document IDs liên quan đã annotation, Rq@k là top-k retrieval. Recall@k là tỷ lệ Gq được tìm thấy trong Rq@k. MRR@k lấy nghịch đảo hạng relevant đầu tiên, bằng 0 nếu không thấy trong k; trung bình trên queries. nDCG@k dùng nhãn graded relevance 0/1/2 và cùng công thức gain/discount trong mọi baseline.

Báo k=1,3,5,10 khi dữ liệu đủ; chốt một k chính trước test. Khi Gq rỗng, recall không xác định: tách nhóm *unanswerable*, không tự gán 0 hoặc 1 rồi trộn vào điểm chung. Hit rate và Recall không đồng nghĩa khi một query cần nhiều bằng chứng.

Tách passage-level và document-level qrels. Một retriever trả năm chunk của cùng runbook không được tính thành năm tài liệu độc lập; hợp nhất theo parent_document_id cho phép đo document-level. Với pool qrels chưa exhaustively judged, báo pooled evaluation và số mục chưa được chấm, không khẳng định mọi ngoài-pool đều không liên quan.

## Chỉ số RCA

RCA Hit@1/3/5 dựa trên service/fault labels được công bố hoặc annotation độc lập. Với nhiều nguyên nhân, ghi rõ phép đo any-hit và coverage toàn bộ tập nguyên nhân. Reason category và occurrence time chỉ đo nếu nguồn thực sự có nhãn đúng loại; tolerances thời gian phải định nghĩa trước.

Tỷ lệ đoán đúng service không chứng minh đúng đường lan truyền nguyên nhân. [OpenRCA 2.0](https://arxiv.org/abs/2606.27154) là nguồn đọc về phân biệt outcome labels và causal-process supervision. Chỉ đánh giá causal path khi có gold path tin cậy; nếu chỉ có nhãn injection target, dùng mô tả “định vị mục tiêu lỗi được tiêm”.

## Chất lượng câu trả lời

Tách bốn chiều: **đúng về tác vụ**, **được nguồn hỗ trợ**, **trích dẫn đúng**, **đủ bằng chứng quan trọng**. Một câu trích dẫn chính xác tài liệu cũ nhưng chẩn đoán sai ca hiện tại có thể faithful mà không correct. Một câu đoán đúng nguyên nhân nhưng dẫn chứng không liên quan có thể correct mà không grounded.

Rubric người chấm: mỗi claim nguyên tử được đánh dấu supported, contradicted hoặc insufficient evidence; citation link có tồn tại, chỉ đúng đoạn và hỗ trợ claim hay không. Báo tỷ lệ unsupported claims với mẫu số là các claims cần bằng chứng, và báo cả số response không có claim để tránh thắng bằng trả lời rỗng.

Đánh giá abstention bằng coverage (tỷ lệ trả lời), selective risk (lỗi trên phần có trả lời), và tỷ lệ từ chối đúng trên ca thiếu bằng chứng. Không tối ưu “an toàn” bằng từ chối tất cả query. RAGAS/ARES có thể là bộ chấm phụ, nhưng phiên bản judge/model/prompt phải khóa và một phần mẫu phải được người kiểm tra. [ARES](https://arxiv.org/abs/2311.09476) · [Tổng quan đánh giá RAG](https://arxiv.org/abs/2504.14891).

ROUGE/BLEU chỉ dùng phụ nếu có reference text: không lấy việc giống câu chữ làm bằng chứng chính cho RCA. Đo root-cause label, citation và tính đầy đủ bằng chứng bằng nhãn tương ứng.

## Sai số, chi phí và báo cáo

Bootstrap hoặc phân tích khoảng tin cậy theo **incident/group**, không resample từng dòng log như quan sát độc lập. Khi nhiều query của một incident dùng chung telemetry, phải cluster chúng trong thống kê. Báo trung bình kèm phân bố theo fault type, hệ thống và answerability.

Đo thời gian riêng cho preprocessing, retrieval, reranking và generation; báo p50/p95, token input/output, số lần gọi mô hình, RAM/VRAM quan sát thực. Nếu dùng API trả phí, chi phí phải tính từ bill/token và bảng giá tại ngày chạy, không đưa số ước đoán trong gói kế hoạch này.

Bảng kết quả để trống trước thực nghiệm:

| Baseline | Recall@5 | MRR@5 | RCA Hit@1 | Citation precision | Unsupported rate | Coverage | p95 latency |
|---|---|---|---|---|---|---|---|
| BM25 + fixed LLM | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| Dense + fixed LLM | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| Hybrid + fixed LLM | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| Hybrid + reranker | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
