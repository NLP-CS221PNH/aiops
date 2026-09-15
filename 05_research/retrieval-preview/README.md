# Pool gợi ý ban đầu cho annotation

Đã chạy BM25 trên **snapshot tài liệu trước năm 2024**, với 20 train incidents và 400 query–chunk candidates. Corpus: `03_collection_plan/knowledge-corpus-historical/chunks.jsonl`; SHA-256: `1f6c1c28f5f7bcab926509595dda5d5400600c0ea773fdb23eb09d1849a6d8ca`. Mỗi incident lấy tối đa 20 hits. Chọn một ca mỗi family trước rồi thêm ca lặp để đủ pilot; không lấy dev/test. Đây là bước chuẩn bị để đọc/chấm, không phải phép đo retrieval quality.

## Các tệp

- `candidate-diagnostics.jsonl`: query, đoạn evidence, citation, nguồn, rank và score. Dành cho người xây pool, không đưa rank/retriever cho người chấm.
- `annotator-a.tsv`, `annotator-b.tsv`: thứ tự đã xáo bằng seed 221, ẩn rank/score/retriever; relevance và rationale đang trống. Phiếu có `unjudged`, không phải nhãn 0.
- `pilot-pool-status.json`: danh sách incident, corpus path/hash, phương pháp chọn và trạng thái.

## Cách dùng đúng

1. Dùng cùng incident queries/corpus để thêm dense và hybrid candidates, dedup theo query+chunk trước chấm.
2. Xáo và ẩn thông tin phương pháp trên pool hợp nhất. Chấm passage và document level riêng theo [rubric](../../03_collection_plan/annotation-kit/README.md).
3. Hai người chấm độc lập, sau đó adjudicate; giữ bản gốc từng phiếu. Thêm evidence ngoài pool nếu tìm thấy.
4. Chỉ lúc có qrels đã được chấp nhận mới tính Recall/MRR/nDCG; báo mức độ pool coverage và unjudged.

Tệp này chưa có dense/hybrid, chưa có human judgment và chưa được dùng chạy test. BM25-only pool không được đổi tên thành gold qrels. Công cụ từ chối ghi đè phiếu đã có nội dung chấm; cần giữ phiên bản cũ khi mở vòng annotation mới.
