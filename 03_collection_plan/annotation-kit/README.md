# Bộ chấm thủ công cho pilot

Các TSV ở đây là **phiếu trống**, chưa có gold qrels, reference answer, mức answerability hay phán quyết của người chấm. Trường rỗng nghĩa là *unjudged*, không phải relevance 0. `status.json` ghi số công việc và số nhãn thực sự hoàn thành; không suy chất lượng retrieval từ số hàng phiếu.

## Dùng các file

1. Đọc observations theo `task-index.tsv`; chỉ mở telemetry nằm trong observation window. Giai đoạn viết query không đọc nhánh labels, tên folder gốc, injection target, reason hoặc `inject_time.txt`.
2. Làm pilot 10–20 incident theo plan; các query/paraphrase của một incident nằm cùng nhóm. Chưa dùng pilot làm test độc lập. Chốt scenario-family split trước khi viết train history.
3. Người xây pool chạy BM25, dense và hybrid trên cùng corpus và queries. Hợp nhất candidates bằng ID, giữ provenance retriever trong `candidate-pool-template.tsv` dành cho người quản lý. Chọn depth trước, xáo thứ tự bằng seed đã lưu, bỏ retriever/rank/score khỏi phiếu đưa cho người chấm. Thêm candidates do người chấm phát hiện và ghi rõ nguồn bổ sung. Pool hiện chưa hoàn tất.
4. Điền một hàng cho mỗi query–document hoặc query–chunk cần chấm vào cả `qrels-annotator-A.tsv` và `qrels-annotator-B.tsv`. Hai người chấm độc lập toàn bộ pilot. Sau khi sửa rubric, chốt trước tỷ lệ phần chung cho tập còn lại; phần được chấm đơn phải được báo rõ. Không gửi phiếu A đã điền cho B trước khi B chốt.
5. Hai phiếu answerability A/B đánh giá riêng độ đủ bằng chứng của cả corpus đã cho phép. Sau đó lưu bất đồng và quyết định cuối trong hai phiếu adjudication. Không ghi đè phiếu ban đầu.
6. Chỉ xuất gold qrels từ hàng đã adjudicate; chỉ xuất reference answer sau khi người chấm kiểm tra claim và citations. Nếu còn unjudged ngoài pool, báo pooled evaluation. Không đổi ô rỗng thành 0.

Chạy lại `scripts/prepare-annotation-kit.py` có thể thêm incident IDs sau acquisition. Script kiểm tra toàn bộ phiếu đích trước khi ghi bất kỳ phiếu nào: nếu có judgment, answer, adjudication, span/claim đang nhập, review state đã đổi hoặc cột không nhận diện, cả batch dừng và giữ nguyên file. Đây là bảo vệ annotation đã làm, không phải công cụ merge phiếu. Nếu có phiếu đã làm, giữ nguyên và quản lý một annotation version mới.

## Rubric relevance 0/1/2

| Grade | Điều kiện | Ví dụ về cách phân biệt |
|---|---|---|
| 0 | Không liên quan, sai miền hoặc điều kiện áp dụng dẫn sai cho claim đang xét | Tài liệu DNS không giúp kiểm tra lỗi thanh toán có quan sát chỉ ra exception xử lý nghiệp vụ; không gán 0 nếu tài liệu còn một evidence hợp lệ khác. |
| 1 | Có liên quan chủ đề/service nhưng chưa trực tiếp hỗ trợ claim hay bước loại trừ cần thiết | README nêu checkout gọi payment, trong khi câu hỏi cần bằng chứng nguyên nhân payment chậm. |
| 2 | Trực tiếp hỗ trợ ít nhất một claim hoặc bước kiểm tra/loại trừ cần thiết trong điều kiện áp dụng | Đoạn giải thích cách kiểm tra resource limit có thể hỗ trợ bước xác nhận throttling khi observations có tín hiệu CPU; nó chưa tự chứng minh root cause. |

Ở tầng document, đánh giá giá trị của toàn tài liệu. Ở tầng chunk/span, chỉ chấm text thật nằm trong offsets. Một tài liệu có thể grade 2 nhưng chunk chứa phần không liên quan là grade 0. Giữ `document_id` và `chunk_id` riêng; không cộng nhiều chunk của một tài liệu thành nhiều tài liệu relevant.

`evidence_role` dùng một trong: `symptom_interpretation`, `service_dependency`, `diagnostic_check`, `elimination_check`, `root_cause_support`, `counter_evidence`, `context_only`. Ghi claim được hỗ trợ trong `supported_claim`. Với lời khẳng định causal RCA, yêu cầu observations/gold đánh giá độc lập; runbook mô tả triệu chứng chung chưa đủ.

`span_start/span_end` là khoảng [start,end) theo Unicode codepoint trên trường `text` của document; không phải byte offset trong raw file. Kiểm tra `doc.text[start:end]` trước khi xuất evidence span. `chunks.jsonl` đã có offsets cùng hệ quy chiếu.

## Phiên bản và thời gian

Có hai corpus độc lập: `knowledge-corpus/` ghim commit 2024–2026 cho **offline assistance**; `knowledge-corpus-historical/` ghim commit trước 2024 làm ứng viên chính theo plan. Phiếu task mặc định chọn historical khi thư mục này đã có. Phải kiểm tra `available_at <= observation_cutoff` từng incident và deployment version; snapshot cũ chưa tự chứng minh compatibility. Ngày tải tài liệu không làm tài liệu trở thành bằng chứng từng có sẵn lúc incident. Chưa tuyên bố historical evaluation đã hợp lệ khi applicability chưa được chấm.

Ở `document-applicability.tsv` (primary historical) và hai phiếu có hậu tố current/historical, kiểm tra platform/app version, cấu hình bắt buộc, quyền truy cập observability và triệu chứng. Chỉ điền `reviewed_compatibility=compatible` khi có bằng chứng. `available_at` hiện là thời điểm commit toàn repository, không phải ngày xuất bản hoặc ngày sửa riêng trang. Chưa biết `published_at`/`updated_at` nên để null. Không trộn hai corpus trong cùng index; historical có ID prefix `KBH`, current có `KB`, và mỗi tập phải đi cùng snapshot hash riêng.

Không index `proposed-mappings.*` làm evidence; đây là gợi ý theo tên path/title, trạng thái `needs_human_review`, không phải incident qrels. Tài liệu hiện tại có tính năng Kubernetes mới hơn deployment cũ nên các đoạn version-sensitive có thể không áp dụng.

## Answerability và reference answer

Chọn `answerable`, `partially_answerable`, `unanswerable`, hoặc `uncertain_pending_review`. Ghi các claim bắt buộc, evidence đủ và thông tin còn thiếu. BM25 không tìm thấy tài liệu chưa đủ để gọi ca đó unanswerable. Nếu làm condition embargo, chốt danh sách document IDs và lý do trước khi chạy test; người chấm độc lập xác nhận mức answerability của từng condition.

Reference answer ngắn, chứa claim có evidence IDs, giới hạn điều đã biết, unknowns và next checks. Không yêu cầu người chấm viết chuỗi suy nghĩ nội bộ. Một LLM draft nếu có phải có provenance và người chấm kiểm tra; LLM không đồng thời tự tạo rồi chấm gold duy nhất của nó.

## Claim evaluation và bất đồng

Mỗi claim nguyên tử được chấm `supported`, `contradicted`, hoặc `insufficient_evidence`; chấm riêng task correctness và citation correctness. Claim đúng đáp án nhưng nguồn không hỗ trợ vẫn là insufficient evidence. Báo cả response rỗng/abstain để tránh tăng điểm bằng không đưa claim.

Tính agreement trên phần chung trước adjudication; với relevance thứ bậc có thể báo weighted Cohen kappa kèm raw agreement và phân bố grade. Không có nhãn thì không tính kappa. Nếu bất đồng do rubric, ghi phiên bản mới và chấm lại phần chịu ảnh hưởng; giữ lịch sử quyết định. Người adjudicate ghi lý do ngắn và ID đoạn chứng cứ. Không tự chọn kết quả có lợi cho hệ thống đang đánh giá.

## Điều kiện khóa gold

- Có phán quyết thật của người chấm và adjudication, không phải phiếu tạo sẵn.
- Corpus hash, query version, pool depth/seed, annotation version và split đã khóa.
- Unjudged, non-relevant, unanswerable và version-incompatible được giữ riêng.
- Nhãn RCA của nguồn vẫn ở nhánh labels; mọi incident-derived document ghi lineage và tuân split/cutoff.
- Root-cause target được tiêm, evidence relevance và chất lượng giải thích là ba loại nhãn khác nhau.
