# Knowledge corpus và annotation cho CS221

Đã chuyển phần knowledge plan thành dữ liệu thật: corpus historical chính gồm **74 tài liệu / 580 chunks từ ba nguồn**, 12 tài nguyên bổ trợ; corpus current riêng có **73 tài liệu / 598 chunks**, 15 tài nguyên bổ trợ. Cả hai có giấy phép và receipt tải đầy đủ. Đã tạo phiếu chấm cho 90 incident IDs, 74 phiếu applicability historical và 73 phiếu current. **Chưa có phán quyết của người chấm, gold qrels, reference answers hoặc tỷ lệ evidence coverage đã đo.** Không cộng hai snapshots thành nguồn test độc lập.

## Tài nguyên được chọn và vai trò

| Thành phần | Đã có trên đĩa | Giá trị dùng được | Giới hạn |
|---|---|---|---|
| Online Boutique | 25 historical / 24 current docs/config/proto, sơ đồ kiến trúc | Danh mục service, dependency khai báo, RPC contract, cấu hình ports/probes/resources tham chiếu | Đây là upstream app snapshot; chưa chứng minh đúng deployment RCAEval. Không có incident gold. |
| Kubernetes | 14 trang troubleshooting/resource/lifecycle/logging và 14 fragment YAML/includes | Giải thích trạng thái Pod, CPU/memory limit, DNS/service connectivity và cách kiểm tra | Chỉ áp dụng khi cluster/version/feature tương thích. Trang nguồn chưa render Hugo; snippets lưu riêng. |
| Prometheus runbooks | 35 runbooks CPU, Pod, node, network, storage, metrics/alerting | Diễn giải alert và đề xuất kiểm tra có điều kiện | RCAEval chưa được xác nhận dùng đúng alert rules; tên alert khớp chưa là qrel. |

Online Boutique upstream mô tả ứng dụng với 11 microservices giao tiếp qua gRPC; cart dùng Redis, checkout phối hợp cart/payment/shipping/email. Danh sách ứng dụng bao gồm loadgenerator, còn Redis là dependency lưu trữ; không đồng nhất con số này với inventory telemetry có alias `frontendservice`/`frontend` hay `redis`/`redis-cart`. [README ghim commit](https://github.com/GoogleCloudPlatform/microservices-demo/blob/b9a978db9e01f4ad3dca9494a22cb9edc17548fe/README.md), [cartservice manifest](https://github.com/GoogleCloudPlatform/microservices-demo/blob/b9a978db9e01f4ad3dca9494a22cb9edc17548fe/kubernetes-manifests/cartservice.yaml), [RPC contract](https://github.com/GoogleCloudPlatform/microservices-demo/blob/b9a978db9e01f4ad3dca9494a22cb9edc17548fe/protos/demo.proto).

Không mặc định CPU throttling alert chứng minh root cause: runbook của nguồn gọi đây là tín hiệu thông tin và yêu cầu kiểm tra ứng dụng có hành vi bất thường hay tín hiệu khác hay không. Cần đọc đúng evidence span trước khi nâng thành khuyến nghị hoặc claim. [CPUThrottlingHigh](https://github.com/prometheus-operator/runbooks/blob/a685d14cf5128bb30e2bf935c3983decd772d885/content/runbooks/kubernetes/CPUThrottlingHigh.md).

## Mapping đề xuất, chưa qua người chấm

| Nhóm triệu chứng | Nguồn ứng viên | Điều cần xác nhận từ observations |
|---|---|---|
| CPU pressure/throttling | K8s resource management; CPUThrottlingHigh | Có metric/limit thích hợp; chậm do CPU hay downstream; phiên bản/cgroup áp dụng |
| Memory/OOM/restart | Resource management, Pod lifecycle, failure reason, KubePodCrashLooping | OOM/termination reason thật, thời gian restart, limit và service bị ảnh hưởng |
| Network/DNS/service unreachable | DNS debugging, debug-service, TargetDown, node network | Loại lỗi network thực tế, DNS versus delay/loss; application fault không tự thành DNS fault |
| Dependency và gRPC | OB README/proto/config | Alias service, deployed version, trace path trong observation window |
| Disk/PV/filesystem | PV và filesystem runbooks | Dữ liệu có storage mount/node tương ứng; tránh chẩn đoán PV nếu workload không dùng PV |
| Metrics/alert collection lỗi | Prometheus ingestion/rule/target runbooks | Lỗi collector hay lỗi ứng dụng; các rules có thực sự được cài hay không |

82 hàng `proposed-mappings.*` được sinh bằng quy tắc path/title, có `review_state=needs_human_review`, `is_gold_qrel=false`, `relevance_grade=null`. Chúng dùng để định hướng người chuẩn bị pool, không dùng tính Recall/MRR/nDCG. Coverage của lỗi ứng dụng là câu hỏi pilot còn mở; không có bằng chứng để nói các runbook platform phủ toàn bộ lỗi được tiêm.

## Giấy phép, provenance và thời gian

Đã đọc LICENSE tại đúng commit rồi mới acquisition nội dung: Apache-2.0 cho Online Boutique và Prometheus runbooks; CC-BY-4.0 cho Kubernetes website documentation. Raw file, source URL, license snapshots, checksum và change notice đi cùng derivatives. Không nhập nội dung từ external links hoặc cho rằng public page mặc nhiên được tái phân phối. [OB LICENSE](https://github.com/GoogleCloudPlatform/microservices-demo/blob/b9a978db9e01f4ad3dca9494a22cb9edc17548fe/LICENSE), [K8s LICENSE](https://github.com/kubernetes/website/blob/76a0e90f253e924a7b55f01f92a37555bd89be68/LICENSE), [Runbooks LICENSE](https://github.com/prometheus-operator/runbooks/blob/a685d14cf5128bb30e2bf935c3983decd772d885/LICENSE).

Current snapshots: OB 2026-09-03, K8s 2026-09-12, runbooks 2024-10-03. Ngày commit là mốc bảo thủ khi toàn snapshot tồn tại, không được ghi thành ngày publish/update riêng trang. `published_at`/`updated_at=null`; `retrieved_at` ghi thời gian tải riêng. Pilot RE2-OB quan sát năm 2024 nên current corpus phục vụ **offline assistance**, bị loại khỏi historical evaluation cho tới khi có snapshot <= cutoff và mapping phiên bản được xác nhận. Không dùng date HTTP Last-Modified để suy ngày tài liệu ra đời.

Thu thập thụ động qua GitHub API/raw URL ghim commit. Không chạy repository loader, fault injection, kubectl, lệnh trong runbook hoặc YAML examples. docs-seeker detect/fetch đã chạy, Context7 không tìm được bộ tài liệu này, nên chuyển sang đọc repository nguồn trực tiếp.

## Annotation kit đã chuẩn bị

`03_collection_plan/annotation-kit/` có task-index, phiếu A/B relevance độc lập, phiếu A/B answerability độc lập, adjudication riêng cho hai loại, reference-answer blanks, claim-evaluation template, candidate-pool template, document-applicability và rubric tiếng Việt. 90 IDs lấy từ split-map có ID mờ, không đọc gold labels để tạo query hay phán quyết.

Đã cập nhật task-index từ đủ 90 observations bằng script prepare-annotation-kit. Script kiểm toàn bộ batch trước khi ghi, từ chối ghi đè nếu có annotation đang làm, phán quyết hoặc cột mới chưa nhận diện. Người xây pool dùng cùng query/corpus, pool BM25+dense+hybrid, xáo thứ tự và ẩn retriever/rank/score trước khi hai người chấm. BM25-only smoke pool nếu có chỉ là bản nháp chưa hoàn tất pool đánh giá. Hai người chấm toàn pilot 10–20 incident theo rubric 0/1/2, ghi bất đồng và adjudication; sau đó chốt protocol cho phần còn lại. Reference answer và answerability không tự suy từ việc retriever có tìm thấy tài liệu.

Không có human labels nên chưa tính agreement, không báo gold hoàn thành, không đổi ô trống thành 0. Khi có labels, chấm document và evidence span riêng; chunk offsets đã được kiểm tra khớp text document. `token_count` chưa tính theo tokenizer thật; ước lượng chars/4 chỉ để nhìn kích thước, không dùng làm context-budget measurement.

## Kiểm tra đã thực hiện và việc còn lại

Đã xác nhận 73 IDs document và 598 chunk IDs, toàn bộ offsets khớp, raw hash/text hash và nguồn ghim revision; chưa phát hiện file text trùng hash trong phạm vi chọn. Chưa có đánh giá near-duplicate bằng người, compatibility theo deployment, đủ bằng chứng trên từng incident hoặc gold qrels. Những phần này được lưu ở trạng thái pending, không được quảng bá là đã kiểm nghiệm.

## Historical snapshot đã bổ sung

`03_collection_plan/knowledge-corpus-historical/` đã có 74 docs/580 chunks/12 supporting assets. Ghim OB `80bea9bfd97bec107361d4663e207aa8d3f312c6` ngày 2023-12-28; K8s `7e631d0318dc279cb2d31231d8823360e61e9304` ngày 2023-12-31; runbooks `f8061f3e9b3337d90107aa2f10a0111f3f6dc86f` ngày 2023-09-07. LICENSE được tải và kiểm tra lại ở đúng các commit này, không kế thừa giả định từ current. [OB snapshot](https://github.com/GoogleCloudPlatform/microservices-demo/tree/80bea9bfd97bec107361d4663e207aa8d3f312c6), [K8s snapshot](https://github.com/kubernetes/website/tree/7e631d0318dc279cb2d31231d8823360e61e9304), [Runbooks snapshot](https://github.com/prometheus-operator/runbooks/tree/f8061f3e9b3337d90107aa2f10a0111f3f6dc86f).

Không forward-fill nội dung từ 2026. Các path chọn ở current đều có ở historical; historical thêm `kubernetes-manifests/redis.yaml`. Có 41 paths text giống hệt và 32 paths text đổi. Điều này cho thấy dùng tài liệu mới nhất thay tài liệu cũ có thể đổi evidence thực sự dù URL path giống nhau; không coi ngày publish ban đầu là đủ. Diff lưu `comparison-with-current.json`.

Historical IDs dùng `KBH`, current dùng `KB`; mọi kết quả/nhãn vẫn phải kèm snapshot hash. `proposed-mappings` historical gồm 83 candidates, tất cả chưa qua người chấm. Đã so toàn bộ historical documents với 90 observation windows: mọi `available_at` đều trước observation start; mốc observation sớm nhất là 2024-01-15T17:30:22Z. Kết quả ở `comparison-with-current.json` chỉ xác nhận điều kiện thời gian. Deployment app/cluster version vẫn chưa được nguồn xác nhận; temporal eligibility và applicability là hai kiểm tra riêng. Chọn historical làm ứng viên chính theo plan. Current corpus vẫn dùng được cho offline assistance hoặc ablation độ mới, nhưng không thay historical corpus âm thầm trong cùng benchmark.
