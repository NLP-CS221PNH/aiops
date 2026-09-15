# Research protocol v1 — CS221 AIOps Hybrid RAG

Protocol `cs221-aiops-rag-protocol-v1` · version `1.0.0-draft.2` · **draft, chưa được nhóm review/freeze**.

## Thẩm quyền và câu hỏi

Bản derivative thực hiện [plan 01](../../plans/260913-0057-cs221-01-scope-and-protocol/plan.md), [master](../../plans/260913-0020-cs221-aiops-rag-master-plan/plan.md) và [contracts](../../plans/reports/260913-independent-plans-contracts.md). Khi tài liệu cũ khác master/contracts mới, bản này dùng thiết kế mới: passage nDCG@5 chính, bốn generation conditions, chấm đôi toàn core 56 và F1 trước test pooling. Giữ bản gốc để kiểm toán. Bản này chưa thay thế quyền giảng viên hay quyết định có chữ ký; [protocol.yaml](../configs/protocol.yaml) là cấu hình có cấu trúc cùng phiên bản, không đủ để chạy test.

RQ2 chính: so sánh hybrid với baseline đơn mạnh hơn trên dev. RQ1 chỉ trên train/dev, chọn một representation trước test. RQ3 kiểm service localization, citations/support và abstention với một generator đã được phép. Các giả thuyết không là kết quả; hiệu số âm vẫn đáp ứng RQ2.

<!-- protocol-summary:start -->
```yaml
primary_metric: passage_ndcg_at_5
primary_selection: stronger_dev_single
tie_break: BM25
required_conditions: [G0, GB, GD, GH]
optional_conditions: [GR]
qrels_core: {train: 20, dev: 18, test: 18}
test_tuning: false
freeze_sequence: [F1, test_input, test_pool, F2, test_scoring]
```
<!-- protocol-summary:end -->

## Dữ liệu, đơn vị và corpus

90 incidents/30 service×fault families, ba repetitions/family. Split nguồn `cs221-family-split-20260912-v1`: 54/18/18 incidents và 18/6/6 families train/dev/test. Giữ family cùng split; không sinh lại seed/split hay dùng test tune. Chỉ evaluator join private gold/family/split; renderer/query/index/provider/demo live dùng allowlist được plan 02 kiểm. Tất cả variants thừa kế incident/task-window identity; labels, injection time, qrels, reference và original case path không vào inference.

Historical `cs221-knowledge-pre2024-v1` (74 documents/580 chunks) là **nguồn đề xuất** cho corpus chính; plan 03 tạo derivative có IDs, offsets codepoint trên normalized text, revision, license và applicability. Current 73/598 là snapshot so sánh có overlap; không cộng thành corpus độc lập. Tài liệu trước thời điểm không đủ chứng minh phù hợp deployment. Unknown applicability giữ unknown. Corpus vận hành gồm tài liệu/runbook hợp lệ và lịch sử chỉ từ train có lineage/cutoff phù hợp; không lấy qrels hay bibliography làm evidence.

## Đối chứng và công bằng

| Retriever | Generation condition | Nội dung |
|---|---|---|
| Không có external retrieval | G0 | No-RAG, vẫn nhận common observation bundle và được cite observation IDs |
| IR-B | GB | BM25 |
| IR-D | GD | Một dense encoder |
| IR-H | GH | RRF của IR-B và IR-D |
| IR-R (optional) | GR (optional) | Rerank cùng candidates; quyết định và chi phí phải khóa trước F1 |

`G0` condition no-RAG khác `gate_id:G0, gate_kind:project_start`. G0 project-start không cấp quyền model.

Cùng corpus/content field `section_heading + text`, query content, common observation bundle, tokenizer/budget policy và một generator/prompt contract/decoding cho mọi conditions. Prefix model được ghi riêng, không tự thêm evidence. R1 selected logs và R2 normalized logs giữ cùng retained evidence IDs/source spans sau token budgeting: cắt đồng thời cho cả hai vừa; phần token tiết kiệm của R2 để trống. Giữ service names, HTTP codes, exceptions và identifiers có ý nghĩa. R3 thêm metrics/traces có chủ đích và ledger. Không ép no-RAG đủ tokens bằng context giả.

Pilot kế thừa: RRF constant 60, candidate depth 50/nhánh, tối đa top-5 knowledge chunks, observations ≤2.048 / knowledge ≤4.096 / output ≤768 tokens; system/prompt tính riêng. Đây là đề xuất chưa đo; tokenizer và actual usage phải kiểm trước F1. E5-small-v2 là ứng viên từ [snapshot model cards](../../05_research/source-snapshots/support-resources.json), chưa là model được duyệt hay đã chạy. Revision, tokenizer, prompt và generator thực giữ null tới pilot/quyết định; cấu hình draft không giả pin model. Ranking short/empty giữ thật, không padding.

## Annotation và mẫu số

Core **56 incidents: 20 train + 18 dev + 18 test**; hiện có **0 human judgments**. 34 train còn lại là mở rộng, không được gọi có qrels. Chọn 20 train đại diện families trước chấm; seed pool BM25 20/400 chỉ là điểm bắt đầu. Union top-10 của mọi methods/configurations được đánh giá, dedup theo incident/task-window/corpus/chunk; bổ sung candidates khi thử dev variants. Tất cả passage pairs core chấm bởi hai người độc lập; người thứ ba adjudicate. Giữ bản A/B gốc, agreement trước adjudication, phân bố grade, evidence role/applicability/answerability. Người chấm thấy cùng full observations/task/window; che method/rank, shuffle bằng seed được lưu. Hai agents không thay hai người.

Relevance 0/1/2; unjudged khác 0. Query-only change không ghi đè judgment cùng evidence/task/window; lưu query hashes trong pool provenance và chấm candidates mới. Thay task/window/evidence phải review/rejudge phần ảnh hưởng. Document-level relevance chấm riêng, không lấy max passage grade.

Primary passage nDCG@5: `DCG@5 = sum((2^rel_r - 1) / log2(r+1), r=1..5)`; IDCG@5 từ qrels đã adjudicate cùng incident. Mọi final top-5 thực trả phải judged; chưa đủ coverage chặn headline scoring, không loại incident để qua gate. Top-k thiếu do ranking short không đòi padding. Có relevant qrels mà ranking rỗng: nDCG/recall = 0. Không có relevant judged evidence: nDCG/recall undefined, báo riêng count; điều này không tự chứng minh corpus hoàn toàn không có evidence. Unjudged không thành 0.

Macro-average trên **cùng tập incident đủ điều kiện** cho các conditions. Baseline đơn chọn theo dev passage nDCG@5; BM25 và dense cùng denominator, score bằng nhau chọn BM25. Chọn bằng score chưa làm tròn; nếu không có incident dev đủ điều kiện thì giữ selection pending, không áp dụng tie-break cho undefined. Primary test contrast = mean của paired incident deltas `IR-H - selected_single`. Không đổi headline khi thấy test. Document secondary collapse theo document đầu tiên xuất hiện trong ranking; dùng relevance riêng, thiếu document judgments thì unavailable.

MRR@10 chỉ tính khi top-10 thực trả đã judged và có relevant judged evidence (grade≥1); không relevant trong top-10 với relevant qrels thì 0, không relevant judged trong toàn qrels thì undefined. Pooled Recall@20/50 chỉ diagnostic: numerator là relevant judged retrieved, denominator là relevant judged trong pool; báo judged@k = judged returned / actual returned; empty ranking coverage undefined và empty_run=true. Không gọi pooled Recall exhaustive hoặc guaranteed lower bound.

## Localization, grounding, failures và thống kê

Service top-1/top-3 accuracy dùng toàn **18 test incidents** cho mỗi condition. Invalid, failed và abstained không có localization đúng trong primary; báo riêng những trạng thái ấy, coverage và conditional accuracy; coverage=0 làm conditional accuracy undefined. Fault category chỉ secondary khi có mapping rubric rõ. Injection-target service accuracy không chứng minh causal path hoặc giảm MTTR.

Claims chấm supported/contradicted/insufficient evidence, tách observation/inference và applicability. Citation hợp lệ phải có ID trong **actual context** của response, span đúng và hỗ trợ nội dung; ID tồn tại đâu đó trong corpus chưa đủ. Unsupported rate dùng claims cần evidence làm mẫu số; report count claims, responses không claims, invalid responses, abstention và missing evidence. Citation coverage dùng evidence-requiring claims; citation precision dùng citations đã kiểm. Không claims/citations thì metric tương ứng undefined, không thưởng 1. Không lấy LLM judge làm gold người.

Final 18×4=72 response records; optional GR thì 90. Một lượt người review mọi outputs; chấm đôi thêm một incident/family đã chọn bằng seed trước F1, đủ conditions: thêm 24 hoặc 30 lượt. Agreement chỉ trên subset thực chấm đôi. Future seed/subset phải khóa trước outputs, hiện pending. Không bỏ failed/empty outputs khỏi ledger, không retry tới khi đáp án đúng. Ghi attempts, error/status, usage, model/cohort/config/context hashes và giữ raw/parsed output.

Test gồm **6 families**, mỗi family ba repetitions; incident là đơn vị tính metric, family là đơn vị cluster độc lập. Báo sáu family means/deltas và eligible incidents/families; family không có eligible IR incident là undefined. Leave-one-family-out: bỏ từng family, tính lại cùng paired incident mean trên phần còn lại. Nếu bootstrap: resample family cùng toàn repetitions và conditions, giữ pairing, tính lại cùng statistic; chỉ thăm dò với sáu clusters, báo seed/resample count. Không tăng n bằng claims/log rows/API calls. Service metrics vẫn dùng toàn 18, kể cả incident không relevant qrels.

## Freeze và đổi phiên bản

1. **F1 (plan 08, sau 06.dev + 05.runners + 07.pilot):** khóa split/IDs/hash; approved export; train/dev query/common bundle; corpus/model/tokenizer revisions; renderer/budget/schema/config/code/environment; prompt/context/decoding; conditions/primary baseline/aggregation; evaluator/rubric; seed/subset review. Test inputs chưa materialize, nên F1 khóa rules để tạo chúng, không đòi hash file chưa có.
2. **test_input (08 dùng functions 04):** tạo test query/bundle riêng; manifest liên kết F1 và frozen functions/config, input hashes. Không append test vào file train/dev đã hash.
3. **test_pool:** retrieval bằng F1/test-input manifest; union candidates cho plan 06. Test qrels không phải prerequisite của retrieval tạo pool.
4. **F2 (06):** chấm test độc lập/adjudication; khóa qrels với F1, test-input, pool, annotation versions và coverage.
5. **test_scoring (08):** kiểm chain hiện tại, chạy final generation bằng F1 sau F2 với inference không mount labels, review support và tính metrics. Không dùng test feedback tune.

G0 chỉ là hợp đồng khởi động; không phải F1/F2 hoặc scientific release. Manifest hash exact bytes, đường dẫn tương đối workspace, version, provenance và pending permissions. Sửa draft sau manifest làm bản cũ invalid; tạo version mới và review ảnh hưởng, giữ manifest trước. Sửa thí nghiệm sau F1 phải deviation record, giữ original outputs, chạy lại đối xứng mọi conditions ảnh hưởng và khai báo nếu test không còn unseen. Không hạ/xóa/bỏ tests, đổi test IDs, bịa nhãn hoặc loại ca khó để hoàn tất goal. Tái tính headline tables từ archived evaluator inputs là gate release; replay API cache khác fresh generation.

## Quyền, nguồn lực và điểm cắt

API use, gửi payload, local/open-weight model, data sharing và trần chi là năm quyết định riêng. API generation cần api=approved, api_payload=approved và budget_usd được xác nhận bằng source_ref; local generation cần local_model=approved, revision/license/resources/payload phù hợp. Không coi G0 hoặc `--auto` là phản hồi giảng viên. Không gửi gì từ lượt này.

Trần $10–15 là đề xuất chờ nhóm; approved budget=null. Không giữ giá hiện hành chưa kiểm lại: dự toán `requests × (input_tokens × input_rate + output_tokens × output_rate) / 1_000_000`, cộng retry/thinking actual usage khi có. Giá và model revision phải xác minh ngay trước pilot có phép. Kaggle free/quota/GPU là tài nguyên chưa kiểm trên tài khoản; không cộng ba quota thành bảo đảm.

Cuối tuần 2: nếu API chưa được phép, tiếp tục IR/annotation; local fallback chỉ khi quyền riêng đã approved và pilot khả thi. Nếu mọi generator bị từ chối, soạn amendment thành retrieval/extractive assistance và xin thay đổi scope; RQ3 remains not_run, không tự đổi tên kết quả. Chưa có trần tiền thì không paid run. Reranker/GR quyết trước F1, mặc định chưa chọn; cắt optional trước qrels/test/integrity.

Tổng master 308–374 giờ-người trực tiếp; 20% dự phòng =369,6–448,8 (làm tròn370–449), tương đương15,4–18,7 giờ/người/tuần trong tám tuần. Nếu chỉ8h/người/tuần thì tổng192h, thiếu116–182h trực tiếp hoặc178–257h có dự phòng: cắt optional chưa chắc đủ, phải thống nhất lịch/phạm vi bằng amendment. Annotation84–150h phải đo lại sau5ca calibration cuối tuần2. Không ghi dự toán như giờ đã làm. [Working agreement](team-working-agreement.md) ghi owner/reviewer và lịch; [decision log](decision-log.md) giữ phần cần người.
