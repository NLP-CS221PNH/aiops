"""Generate the research handoff from measured artifact counts, preserving all limits."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
def jl(name):
    return [json.loads(x) for x in (ROOT / name).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def js(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
def write(name, text):
    (ROOT / name).write_text(text, encoding='utf-8')
papers = jl('01_papers/enriched/catalog-enriched.jsonl')
paper_stats = js('01_papers/enriched/research-statistics.json')
identity = Counter(p.get('research', {}).get('identity_status', 'unknown') for p in papers)
read_depth = Counter(p.get('research', {}).get('read_depth', 'not_read') for p in papers)
notes = list((ROOT / '01_papers/reading-notes').glob('P*.md'))
profile = js('02_datasets/processed/profile-summary.json')
acquired = js('02_datasets/acquired/meta/acquisition-status.json')
historical = js('03_collection_plan/knowledge-corpus-historical/snapshot.json')
current = js('03_collection_plan/knowledge-corpus/snapshot.json')
pool = js('05_research/retrieval-preview/pilot-pool-status.json')
pool_label = 'snapshot tài liệu trước năm 2024' if 'knowledge-corpus-historical/' in pool['corpus_path'] else 'snapshot tài liệu hiện tại (không dùng cho historical triage)'
validation = js('04_audit/research-pack-validation.json')
timestamp = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
matched = identity.get('matched', 0)
identity_pending = len(papers) - matched
bib_count = paper_stats['bibliography_entries']
bib_pending = paper_stats['unresolved_bibliography_rows']
status = 'PASS' if validation['passed'] else 'PENDING — xem các check chưa đạt'

write('START-HERE.md', f'''# Bắt đầu làm việc với bộ nghiên cứu CS221

Mở [mục lục có tìm kiếm](START-HERE.html) để tra paper, incident và nội dung tài liệu. Đọc [báo cáo tổng hợp](05_research/research-report.md) trước khi dùng dữ liệu làm thí nghiệm.

## Đã có trên máy

| Sản phẩm | Trạng thái thực tế | Mở |
|---|---|---|
| RCAEval RE2–Online Boutique | 90/90 ca; 360 tệp; {acquired['bytes']:,} bytes; 270 Parquet khớp hash upstream | [Inventory](02_datasets/acquired/inventory.tsv) |
| Observations và evidence | 90 bundles; {profile['log_evidence_records']:,} log excerpts; {profile['metric_summary_records']:,} metric summaries; {profile['trace_evidence_records']:,} trace excerpts | [Observations](02_datasets/processed/observations.jsonl) |
| Gold và split | Gold service/fault/injection tách riêng; 30 families; 54/18/18 train/dev/test | [Labels](02_datasets/processed/labels/ground_truth.jsonl) · [Split](02_datasets/processed/split-map.tsv) |
| Kho tri thức chính | {historical['document_count']} tài liệu / {historical['chunk_count']} chunks, commit trước năm 2024 | [Historical corpus](03_collection_plan/knowledge-corpus-historical/README.md) |
| Snapshot hiện tại để so sánh | {current['document_count']} tài liệu / {current['chunk_count']} chunks; có overlap với bản lịch sử | [Current corpus](03_collection_plan/knowledge-corpus/README.md) |
| Bibliography | {len(papers):,} record giữ ID; {matched:,} khớp định danh; {bib_count:,} mục BibTeX; {bib_pending} bibliography chưa đủ thông tin | [TSV](01_papers/enriched/catalog-enriched.tsv) · [BibTeX](01_papers/enriched/references-verified.bib) |
| Ghi chú đọc | {len(notes)} ghi chú ưu tiên, có mức đọc và hạn chế | [Paper report](05_research/paper-research.md) |
| Annotation | Biểu mẫu cho 90 ca; seed pool BM25 {pool['n_incidents']} train incident / {pool['n_candidates']} candidates; chưa có phán quyết người | [Kit](03_collection_plan/annotation-kit/README.md) · [Seed pool](05_research/retrieval-preview/README.md) |
| Model/config tham khảo | E5, BGE và reranker có card/config/revision; chưa tải weights hay chạy generator | [Thiết kế](05_research/method-and-experiment-design.md) |
| Kiểm tra artifact | {status} | [Validation](04_audit/research-pack-validation.json) |

## Thứ tự sử dụng

1. Đọc [phân tích dataset](05_research/dataset-research.md) và [thiết kế thí nghiệm](05_research/method-and-experiment-design.md).
2. Mở 20 train incidents trong seed pool, xem observations cùng raw row references khi cần. Duyệt applicability của tài liệu lịch sử đối với deployment.
3. Bổ sung dense/hybrid vào pool, rồi hai người chấm độc lập theo rubric; adjudicate bất đồng. Seed pool BM25 hiện tại chưa là pool đánh giá hoàn chỉnh.
4. Khóa query representation, corpus, split được review, qrels, generator/context và evaluator trước test. Dùng [bảng kết quả trống](05_research/experiment-results-template.tsv).

## Tìm thử bằng chứng trên máy

Từ thư mục gốc, dùng Python 3 để chạy công cụ tra cứu nhẹ, không cần model hoặc mạng:

```powershell
python scripts/preview-retrieval.py --query "Kubernetes pod OOMKilled memory limit" --top-k 5
```

Kết quả có citation IDs, nguồn, corpus hash và đoạn văn. Score là BM25 để xem thử, không phải accuracy hay kết luận benchmark. Corpus mặc định là snapshot lịch sử. Xem [hướng dẫn tái lập](05_research/reproducibility-guide.md) để đọc Parquet và chạy các bước chuẩn bị.

## Những phần còn cần hoàn thiện trước thí nghiệm cuối

Chưa có human qrels/reference answers; chưa có agreement hoặc kết quả baseline. Deployment version và evidence coverage vẫn cần duyệt. Còn {bib_pending} bibliography chưa đủ thông tin, trong đó {identity_pending} record chưa khớp định danh. Khớp định danh không đồng nghĩa mọi trường xuất bản đã được xác minh; số mục có venue/year được xác minh là {paper_stats['publication_venue_year_verified']}. RE2-TT mới có metadata, không tải telemetry vì là nhánh mở rộng; có một ca thiếu logs theo nguồn. Các dataset khác giữ quyết định nguồn, không được tính là đã tải.

Raw data giữ byte gốc và có email/IP patterns; chỉ bản trích xuất đã qua khử định danh theo quy tắc. Không đưa nhánh `labels` hoặc manifest có tên case chứa gold vào model/index. Không gửi raw lên dịch vụ mô hình khi chưa xử lý phù hợp.

`README.md` và `MANIFEST_SHA256.txt` ban đầu được giữ nguyên làm mốc kiểm toán của gói trước khi thu thập. Manifest mới `MANIFEST_RESEARCH_SHA256.txt` và `04_audit/research-file-inventory.tsv` được tạo sau các kiểm tra cuối; không gồm binary dependency trong `.runtime-python`. Môi trường dữ liệu đã dùng nằm trong `04_audit/data-runtime.json`. Trạng thái hiện tại ở tài liệu này. Hoàn thiện bàn giao: {timestamp} (Asia/Saigon); receipts nguồn dùng UTC.
''')

write('05_research/retrieval-preview/README.md', f'''# Pool gợi ý ban đầu cho annotation

Đã chạy BM25 trên **{pool_label}**, với {pool['n_incidents']} train incidents và {pool['n_candidates']} query–chunk candidates. Corpus: `{pool['corpus_path']}`; SHA-256: `{pool['corpus_hash']}`. Mỗi incident lấy tối đa 20 hits. Chọn một ca mỗi family trước rồi thêm ca lặp để đủ pilot; không lấy dev/test. Đây là bước chuẩn bị để đọc/chấm, không phải phép đo retrieval quality.

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
''')

write('05_research/research-report.md', f'''# Nghiên cứu và chuẩn bị dữ liệu AIOps với Hybrid RAG

## Kết quả chính

Phạm vi dữ liệu trọng tâm của kế hoạch đã được chuyển thành artifact có thể dùng: toàn bộ **90 ca RCAEval RE2–Online Boutique**, telemetry gốc có kiểm checksum, observations và gold riêng, kho tài liệu có phiên bản, metadata paper bổ sung và bộ hồ sơ annotation. Bộ này cho phép bắt đầu kiểm dữ liệu, mapping bằng chứng và triển khai baseline. Nó chưa phải một benchmark đã có human qrels và kết quả mô hình.

Lựa chọn khoa học giữ đúng đề cương: so sánh BM25, dense, hybrid và reranking trên cùng corpus/query, rồi kiểm tra việc cải thiện evidence retrieval có chuyển thành câu trả lời đúng và có dẫn chứng không. Không có kết luận hybrid thắng được đưa ra trước thí nghiệm. Thiết kế cần phân biệt nhãn service/fault của nguồn, qrels bằng chứng và correctness/grounding của câu trả lời.

Một rủi ro lớn đã được xử lý ở cấp thời gian: snapshot tài liệu hiện tại mới hơn telemetry 2024. Đã bổ sung corpus ghim commit trước năm 2024 và kiểm timestamp với 90 cửa sổ quan sát. Corpus cũ trở thành lựa chọn chính trong cấu hình đề xuất; việc tương thích với phiên bản ứng dụng/cluster thực tế và mức đủ bằng chứng vẫn cần được duyệt. [Corpus và annotation](knowledge-and-annotation.md).

## Mục lục

1. [Mức hoàn thiện và bằng chứng](#mức-hoàn-thiện-và-bằng-chứng)
2. [Phát hiện từ dữ liệu](#phát-hiện-từ-dữ-liệu)
3. [Nghiên cứu tài liệu và thiết kế](#nghiên-cứu-tài-liệu-và-thiết-kế)
4. [Nguồn tri thức và chống rò rỉ](#nguồn-tri-thức-và-chống-rò-rỉ)
5. [Thực nghiệm tiếp theo](#thực-nghiệm-tiếp-theo)
6. [Nguồn, phương pháp và giới hạn](#nguồn-phương-pháp-và-giới-hạn)

## Mức hoàn thiện và bằng chứng

| Hạng mục của plan | Kết quả hiện tại | Bằng chứng trên đĩa |
|---|---|---|
| Chọn nguồn có gold đúng loại | RE2-OB; MIT theo phạm vi công bố của tác giả | [Source registry](../02_datasets/acquired/meta/source-registry.json) |
| Tải mẫu trước rồi đủ subset | 90 ca, 360 tệp, {acquired['bytes']:,} bytes; 270 Parquet khớp hash upstream | [Acquisition status](../02_datasets/acquired/meta/acquisition-status.json) |
| Kiểm schema, thời gian, labels | Đã đọc toàn bộ selected telemetry, lập profiles | [Profile](../02_datasets/processed/profile-summary.json) |
| Observations và labels tách riêng | 90 observation bundles; gold nằm nhánh labels | [Observations](../02_datasets/processed/observations.jsonl) |
| Knowledge snapshot có provenance | Historical {historical['document_count']}/{historical['chunk_count']} docs/chunks; current {current['document_count']}/{current['chunk_count']} riêng | [Historical manifest](../03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl) |
| Bibliography bổ sung metadata | {len(papers):,} record; {matched:,} khớp định danh; {bib_count:,} mục BibTeX; {bib_pending} bibliography chưa đủ thông tin | [Enriched catalog](../01_papers/enriched/catalog-enriched.tsv) |
| Đọc nhóm ưu tiên | {len(notes)} ghi chú có read-depth, task, phương pháp và giới hạn | [Paper research](paper-research.md) |
| Qrels và rubric | Forms cho 90 ca; seed pool {pool['n_incidents']} train incidents/{pool['n_candidates']} candidates; chưa chấm | [Annotation kit](../03_collection_plan/annotation-kit/README.md) |
| Baseline quality và confidence intervals | Chưa chạy; bảng kết quả còn trống | [Results template](experiment-results-template.tsv) |

Các cột hoàn thiện nói về artifact đã có, không nâng thành kết luận chất lượng. Registry 102 nguồn/tập con đã được kiểm tính nhất quán và quyết định vai trò; chỉ nguồn cần cho MVP được tải theo kế hoạch. Số 102 không phải số dataset độc lập, và số 1.009 không phải số paper đã đọc toàn văn.

## Phát hiện từ dữ liệu

Raw subset có **{profile['log_rows']:,} dòng log**, **{profile['trace_rows']:,} trace spans** và **{profile['metric_rows']:,} metric timesteps**. Số này được tính từ tệp đã tải, không suy từ tên bộ dữ liệu hoặc từ mirror. Mỗi case có đủ metrics/logs/traces. Khác modality có timestamp unit khác nhau; pipeline dùng Unix seconds cho metrics/logs và Unix milliseconds cho trace start, bỏ trường giờ không có đủ ngày/timezone. [Phân tích dữ liệu](dataset-research.md).

Observation windows là toàn cửa sổ metric cung cấp, được mô tả half-open để xử lý trace timestamps nhất quán. Đây là thiết kế hồi cứu offline, không dùng injection time để tìm onset và không giả rằng hệ thống đã có detector online. Metric summaries mô tả thay đổi đầu/cuối cửa sổ, không là chứng minh bất thường hay quan hệ nhân quả. Trace duration còn unit assumption được ghi rõ; nonzero status không mặc nhiên được gọi là lỗi nếu chưa xác nhận semantics của nguồn.

Tập nhỏ có nhiều dòng telemetry nhưng chỉ **90 đơn vị incident**, thuộc **30 service×fault families**. Đề xuất split 54/18/18 giữ các repetition cùng family và cân theo fault. Đây là split artifact được ghim để pilot; cần duyệt điều kiện tổng quát hóa trước khi đóng băng final test. Không chia ngẫu nhiên các dòng log thành train/test hoặc gọi nhiều seed là nhiều incident độc lập.

Các log/trace excerpts có source file IDs và row offsets; raw giữ tên thư mục opaque để không lộ service/fault từ đường dẫn. Labels, tên case gốc và injection files nằm nhánh riêng. Query được tạo bằng quy tắc từ observations, có cờ synthetic; telemetry tải về là dữ liệu benchmark gốc. Cờ query synthetic không có nghĩa toàn bộ telemetry được mô hình sinh trong đợt này.

Kiểm pattern trong cửa sổ log phát hiện email và IPv4, vì vậy bản trích xuất đã khử định danh nhất quán theo incident. Raw được giữ nguyên để tái lập. Không thấy một số credential patterns đã định nghĩa không đủ để chứng nhận mọi file sạch secret/PII; phạm vi regex và số đếm nằm trong profile. Không gửi raw lên mô hình bên ngoài khi chưa xử lý phù hợp.

RE2-TT được giữ như nguồn mở rộng theo plan: đã pin metadata, chưa tải gần 1,97 GB telemetry. Có một case thiếu logs theo index và known-data notes. Trước cross-system test phải khóa policy xử lý missing modality; không loại ca sau khi thấy kết quả. TechQA, MTRAG và ITBench-Lite giữ vai trò dự phòng task, không nhập điểm QA của chúng vào kết quả RCA.

## Nghiên cứu tài liệu và thiết kế

Bibliography được cập nhật từ metadata của nơi xuất bản/đăng ký định danh và trang nguồn: DataCite cho arXiv, Crossref cho DOI và các trang ACL/OpenReview/primary tương ứng. Bản gốc 1.009 IDs và audit cũ được bảo toàn. Dữ liệu bổ sung có source/cache, trạng thái khớp định danh và year basis; năm preprint không tự thành năm conference. Các mục không truy cập hoặc chưa khớp đủ vẫn để pending. [Tổng hợp và bibliographic limits](paper-research.md).

Nhóm tài liệu ưu tiên cần được đọc theo trục **task → observations → labels → knowledge → split → evaluation**, thay vì theo kích thước mô hình hoặc một score riêng trong abstract. Tài liệu cloud production có thể chứng minh một kiến trúc khả thi nhưng không cung cấp raw incident để tái lập. Bài log anomaly detection không cung cấp causal RCA gold; bài retrieval tổng quát có qrels tốt nhưng khác miền incident. Các ghi chú đọc giữ những khác biệt này để viết related work chính xác.

Thiết kế đề xuất chọn một bi-encoder tiếng Anh nhỏ có input contract rõ, BM25 và rank fusion làm bước đầu. E5-small-v2, BGE-small-en-v1.5 và BGE-reranker-base có cards/config/revisions lưu cục bộ. Các model weights chưa được tải, chưa chọn generator, chưa đo latency/VRAM. Thông số proposal là điểm bắt đầu pilot, không phải hyperparameters thắng trên test. [Thiết kế chi tiết](method-and-experiment-design.md) · [Pinned model resources](source-snapshots/support-resources.json).

Một kết luận thiết kế quan trọng là reranker cần relevant evidence trong candidate pool. Nếu corpus sai version hoặc thiếu runbook, reranking không tạo được tri thức còn thiếu. Đọc failure cases và đo candidate recall trước sẽ quyết định hợp lý giữa cải thiện retrieval, bổ sung corpus hoặc mở nhánh graph. Graph/multi-agent/fine-tuning vẫn là mở rộng, đúng giới hạn đề cương.

## Nguồn tri thức và chống rò rỉ

Kho tri thức chính ghim ba repositories trước năm 2024: Online Boutique cho kiến trúc/service contract/config, Kubernetes cho troubleshooting nền tảng và Prometheus Operator cho alert runbooks. Mỗi document có raw source, commit, license snapshot, hash và text; mỗi chunk có offsets kiểm được. Supporting includes/YAML/diagram được giữ cùng license, không chạy các lệnh hay triển khai YAML.

Hai snapshot có nhiều nội dung trùng hoặc khác phiên bản. Chúng phục vụ so sánh version policy, không phải hai tập độc lập để chia train/test. Tất cả mappings theo path/title hiện là candidates chưa chấm. Tên alert khớp triệu chứng không chứng minh đúng root cause; ứng dụng hiện tại chưa chứng minh đúng deployment trong RCAEval. [Comparison và source manifests](knowledge-and-annotation.md).

Historical commit time bảo thủ là bằng chứng snapshot tồn tại trước incident; không giả là published_at của từng trang. Chưa có commit ứng dụng/cluster gốc của các ca nên tính áp dụng vẫn cần review. Một experiment có thể trung thực dùng tài liệu frozen hiện tại để hỗ trợ phân tích offline, hoặc dùng snapshot cũ với scope được kiểm; không được đổi nhãn giữa hai condition mà giấu policy.

Evidence evaluation phải tách document/chunk và phải giữ unjudged khác grade 0. Bộ biểu mẫu hiện có hai người chấm độc lập, answerability riêng, adjudication và reference-answer blanks. Chưa có người thực sự chấm nên không có agreement hay gold qrels. Seed pool BM25 {pool['n_incidents']} incident/{pool['n_candidates']} candidates dùng {pool_label} chỉ giảm công tìm dữ liệu ban đầu; vẫn cần thêm dense/hybrid vào pool theo plan.

## Thực nghiệm tiếp theo

Tuần dữ liệu của kế hoạch có thể tiếp tục bằng pilot annotation trên tập train. Duyệt khoảng 10–20 incident đại diện, xác nhận liệu người chấm có tìm thấy evidence hợp lệ và có hiểu nhãn nhất quán. Nếu tài liệu chỉ hỗ trợ bước kiểm tra chứ không hỗ trợ cause, ghi đúng evidence role; không nâng grade để tạo ground truth có vẻ đầy đủ.

Sau pilot, khóa split được review, corpus hash, qrels/adjudication, biểu diễn query và model/config. Baseline không RAG vẫn được đọc observations; các nhánh RAG dùng cùng generator và context budget. Báo IR, service localization, supported claims/citations và abstention thành các nhóm riêng. Tính uncertainty theo incident/family, không resample từng dòng log. [Protocol gốc](../00_plan/experiments_and_evaluation.md).

Kết quả có thể cho thấy hybrid không hơn BM25, hoặc retrieval tốt hơn nhưng diagnosis không tốt hơn. Những trường hợp này trả lời câu hỏi nghiên cứu nếu đối chứng công bằng. Không có cơ sở hứa phần trăm giảm hallucination, MTTR hoặc chi phí từ các artifact chuẩn bị. Độ đầy đủ và độ trung thực của protocol là tiêu chí đầu tiên.

## Nguồn, phương pháp và giới hạn

Đối chiếu nguồn và thu thập bắt đầu ngày 12/09/2026; thời điểm tổng hợp {timestamp}. File receipts lưu UTC. Kế hoạch gốc là tài liệu nội bộ được cung cấp; nguồn công khai được dùng để xác minh dữ liệu, metadata và input contract. Nội dung retrieved được đọc như dữ liệu, không làm chỉ dẫn thực thi.

Các nguồn chính: [RCAEval pinned release](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/{acquired['revision']}), [RCAEval official repository](https://github.com/phamquiluan/RCAEval), [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo), [Kubernetes website](https://github.com/kubernetes/website), [Prometheus Operator runbooks](https://github.com/prometheus-operator/runbooks), [DataCite](https://api.datacite.org), [Crossref REST API](https://api.crossref.org), [E5 card](https://huggingface.co/intfloat/e5-small-v2), [MTRAG](https://github.com/IBM/mt-rag-benchmark), [ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite). Các trang/commit cụ thể và mục đã sử dụng nằm ngay trong các báo cáo nhánh và manifests, không chỉ ở danh sách domain.

Kiểm tra tích hợp hiện tại: **{status}**; [validation JSON](../04_audit/research-pack-validation.json) ghi từng điều kiện. Kiểm hash/offset/split chứng minh tính nhất quán artifact, không chứng minh nhãn chấm đúng, nguồn phủ đủ hoặc mô hình tốt. Trang HTML được tạo như mục lục offline; môi trường duyệt tự động chặn local-file URL, nên chỉ kiểm tra cấu trúc và cú pháp, không báo đã kiểm UI bằng browser.

Những việc còn mở: {bib_pending} bibliography chưa đủ thông tin, trong đó {identity_pending} record chưa khớp định danh; human qrels và reference answers; compatibility theo deployment; evidence coverage; generator/phần cứng và model evaluation; yêu cầu chính thức của lớp CS221. Khớp định danh không có nghĩa mọi trường xuất bản đã được xác minh: hiện {paper_stats['publication_venue_year_verified']} mục có venue/year được xác minh. Danh sách này được giữ rõ để tiếp tục nghiên cứu, không được lấp bằng metadata suy đoán, nhãn giả hoặc kết quả thí nghiệm chưa chạy.
''')

summary = {'generated_at': timestamp, 'paper_records': len(papers), 'paper_identity_statuses': dict(identity), 'paper_read_depths': dict(read_depth), 'priority_notes': len(notes), 'raw_selected_bytes': acquired['bytes'], 'incidents': profile['incident_count'], 'historical_documents': historical['document_count'], 'historical_chunks': historical['chunk_count'], 'current_documents': current['document_count'], 'current_chunks': current['chunk_count'], 'human_qrels_completed': 0, 'experiments_run': 0, 'artifact_validation_passed': validation['passed']}
summary.update({'bibliography_entries': bib_count, 'unresolved_bibliography_rows': bib_pending, 'publication_venue_year_verified': paper_stats['publication_venue_year_verified'], 'priority_fulltext_local': paper_stats['priority_fulltext_local']})
write('05_research/completion-summary.json', json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False))
