# Rà soát mười kế hoạch độc lập

## Phạm vi

Rà soát ngày 13/09/2026 cho mười thư mục `260913-0057-cs221-*`. Kiểm tính thực thi của kế hoạch, đường dẫn và giao diện giữa các gói; không nghiệm thu code, mô hình, annotation hoặc chất lượng thí nghiệm chưa chạy.

Hai nguồn kiểm bổ sung nhau: audit source/artifacts của gói chuẩn bị và phản biện bản kế hoạch mới. Các vấn đề được xử lý trong phạm vi chi tiết hóa đã yêu cầu; quyết định cần nhóm/giảng viên tiếp tục là gate tương lai, không được đánh dấu đã duyệt.

## Các điều chỉnh từ audit nguồn

| Vấn đề có căn cứ | Vị trí bằng chứng | Xử lý trong plan |
|---|---|---|
| Bundles còn family/split | `scripts/prepare-incidents.py:132` | 02 tạo allowlist export, private join; 04/05/07 không serialize management fields |
| End inclusive và exclusive khác nhau | `scripts/prepare-incidents.py:81`, `:123` | 02 đặc tả conversion/units và boundary tests; không kết luận bug hoặc sửa raw thiếu bằng chứng |
| Query selection mất thông tin trước rendering | `scripts/prepare-incidents.py` | 04 giữ selection ledger chung, phân biệt upstream loss với normalization |
| Token count corpus chưa được tính, title/boilerplate cần audit | Historical documents/chunks JSONL | 03 có tokenizer audit, derivative IDs/offset lineage; số chunks mới được báo thật |
| Chỉ có BM25 seed pool | `05_research/retrieval-preview/pilot-pool-status.json` | 05 xây runner đầy đủ; 06 pool union và chấm đôi |
| Qrels template chưa tách passage/document | `03_collection_plan/annotation-kit/qrels-annotator-A.tsv` | 06 schema target riêng; document metric unavailable khi chưa có judgments |
| Validator cũ đòi zero judgments/NOT_RUN | `scripts/validate-research-pack.py:163`, `:176` | 08 tạo validator/freeze mới, giữ nguồn chuẩn bị nguyên |
| Master còn phase và ownership xen kẽ | Master/phase04–08 | Tạo 10 plan riêng; 04/05/07 dừng tooling/pilot, 08 sở hữu dev selection/final, 06 sở hữu F2 |
| API thinking/JSON behavior có điều kiện | DeepSeek official guides, research report | 07 cấu hình rõ, giữ malformed/empty responses, retry hữu hạn và no quality retry |

## Quyết định giữ nguyên

- Core 56 incidents; test 18/6 families; no-RAG và ba nhánh RAG bắt buộc; optional reranker có quyết định trước F1.
- Không tạo human labels bằng agent. Agreement được tính trước adjudication trên judgments thật.
- Primary passage nDCG@5; baseline đơn chọn trên dev, hòa BM25. Không thay metric/denominator để tìm kết quả tốt.
- Tuning train/dev → F1 → test pool → human test qrels/F2 → final generation/scoring → output review.
- Pooled recall/unknown/undefined/failure counts được mô tả rõ; không nói giảm MTTR hay causal chain đã được xác thực.
- Effort kế thừa 308–374 giờ-người; annotation 84–150 nằm ở 06, human output review ở 08.

## Các điều chỉnh qua đọc chéo

| Vấn đề được chỉ ra | Quyết định và vị trí áp dụng |
|---|---|
| Nhãn relevance gắn vào query wording có thể khiến mỗi variant thành một tác vụ khác | 04/06/08 dùng key incident/task/window/corpus/chunk; query hashes chỉ là pool provenance; candidates mới cần judgment |
| R1/R2 có thể giữ evidence khác nhau sau token budgeting | 04 chọn retained evidence IDs/source spans chung sao cho cả hai vừa giới hạn; không dùng token R2 tiết kiệm để bổ sung evidence trong ablation |
| Generator có thể tự chọn lại observations khác với 04 | 04 xuất common observation bundle; 07 dùng đúng bundle/hash cho mọi conditions; 08 khóa trong F1 |
| Split có thể bị diễn đạt như tham số tùy ý trước F1 | 01 giữ split hiện có; thay đổi cần amendment rõ, không mặc định được phép |
| Demo yêu cầu đủ loại ca dù kết quả thật có thể không có | 09 báo category absent; fixture minh họa phải dán nhãn và nằm ngoài kết quả đánh giá |
| Release chỉ có bảng/hashes chưa đủ để tính lại headline metrics | 08 bàn giao replay command; 10 bắt buộc evaluator bundle/access recipe được kiểm và tái tính bảng từ archived inputs |
| Mean theo family có thể lệch primary incident mean khi số ca đủ điều kiện khác nhau | 08 khóa cùng eligible incident set, paired incident mean; family là diagnostic; sensitivity/bootstrap tính lại cùng statistic |
| CLI của consumer thiếu entrypoint trong danh sách producer | 06 bổ sung coverage module dự kiến; 07 có generation CLI entrypoint khớp lệnh của 08 |
| Chưa có bước tạo test inputs giữa F1 và retrieval | 08 dùng frozen functions 04 sau F1, tạo query/bundle và manifest test riêng; F1 chỉ khóa rules cùng train/dev hashes, không yêu cầu test content tạo sớm |

Các sửa đổi giữ nguyên mục tiêu so sánh công bằng và phạm vi mười hạng mục. Không thêm baseline bắt buộc, thu nhỏ test set hoặc giảm số người chấm để khớp lịch. Bản nháp được tác giả đọc lại, sau đó đọc chéo giữa nhóm dữ liệu/corpus, retrieval/evaluation và generation/delivery; kết quả tích hợp được kiểm lại bằng công cụ tài liệu.

## Kết quả kiểm kỹ thuật

**Bộ kế hoạch đạt kiểm tra tài liệu.** Đã xử lý các mâu thuẫn được phát hiện trong đọc chéo; không còn vấn đề nghiêm trọng đã biết về ownership, F1/F2, test input producer, mẫu số hoặc gói tái lập.

- Đủ 10 plan độc lập và 30 phase; tổng 44 Markdown được kiểm gồm mục lục và ba báo cáo hỗ trợ.
- Tất cả 40 plan/phase giữ `pending`, không có checkbox hoàn tất hoặc scaffold bỏ trống.
- Dependency hai chiều khớp, không có vòng; master là mốc hoàn tất toàn chương trình, không chặn các plan con.
- Liên kết local và các đường dẫn nguồn được kiểm tồn tại; các đường dẫn sản phẩm tương lai được phân biệt riêng.
- Tổng giờ của từng phase khớp từng plan; tổng bộ kế hoạch là 308–374 giờ-người.
- AgentKit `plan validate` trả exit 0 cho cả 10 plan mới và master.

[Kết quả kiểm tài liệu và hashes](260913-independent-plans-validation.json) lưu counts chính xác cùng snapshot các file. [Kết quả AgentKit](260913-independent-plans-cli-validation.json) lưu kiểm convention; phép kiểm này không thay đọc nội dung. Không dùng các kết quả đó làm bằng chứng gates triển khai đã pass.

Lệnh kiểm tài liệu có thể chạy lại từ workspace:

```powershell
node plans/reports/260913-verify-independent-plans.cjs
```

Script chỉ kiểm bộ tài liệu, không gọi API hay chạy pipeline nghiên cứu. Các liên kết tới sản phẩm tương lai trong `06_implementation` được ghi riêng, không báo rằng file đã có.

AgentKit tạo đủ thư mục/phase qua CLI. Chỉ mục global không ghi được trong sandbox; index tạm tái dựng được đặt ở `plans/.agentkit-runtime` bằng biến môi trường của tiến trình. Không đổi cấu hình hoặc quyền toàn máy. Markdown vẫn là nguồn chính, không cần database để đọc/chạy từng plan.

## Giới hạn và quyết định mở

Không có benchmark, model weights hoặc human labels mới trong đợt này. Không kiểm lại toàn bộ raw hashes; số liệu nguồn dùng manifests kết hợp các phép đọc cấu trúc có mục tiêu. Runtime/model compatibility, Kaggle quota, applicability và tốc độ chấm còn phải đo khi triển khai.

Rubric/hạn nộp, giờ thành viên, quyền API/local model, trần tiền và ngôn ngữ output có owner tại01. Reviewer human chưa thực hiện các gate tương lai. Những điểm này không phải lỗi cấu trúc của kế hoạch, nhưng chặn các milestone tương ứng cho đến khi có evidence.

## Đối chiếu yêu cầu người dùng

| Yêu cầu | Sản phẩm để kiểm |
|---|---|
| Đọc plan đang có | Master và mười phase gốc được đối chiếu với source/artifacts; master có liên kết sang backlog mới |
| Nghiên cứu và cân nhắc Codex có thể làm gì | [Báo cáo nghiên cứu](260913-independent-plans-research.md): hiện trạng, nguồn sơ cấp, phương án, capability matrix và giới hạn |
| Mỗi mục là một plan riêng | [Mục lục](../260913-independent-plans-index.md) trỏ tới mười thư mục, mỗi thư mục một plan và ba phase |
| Kế hoạch chi tiết có thể thực hiện | Mỗi phase có task ID, effort, input/action/output, owner/reviewer, file inventory, nghiệm thu và xử lý lỗi |
| Không báo hoàn thành công việc chưa chạy | Cả 40 plan/phase giữ pending và checkbox chưa đánh dấu; sản phẩm triển khai tương lai được ghi rõ |

Đây là nghiệm thu bộ kế hoạch. Khi bắt đầu triển khai, các gate về nguồn lực, quyền sử dụng và nhãn người vẫn phải được đáp ứng bằng bằng chứng thật.
