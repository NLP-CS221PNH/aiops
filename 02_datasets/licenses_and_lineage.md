# Giấy phép, truy cập và quan hệ dữ liệu

## Hai phép kiểm tra độc lập

**Access:** trang/card/README có đọc được không, có chỉ ra file/release không, link nằm trong repository hay kho ngoài? **Permission:** có điều khoản cho dữ liệu đó không, hay chỉ có license code, hoặc các trang công bố mâu thuẫn? Một nguồn có thể public nhưng quyền tái phân phối chưa rõ; một nguồn có license rõ vẫn có thể lỗi truy cập tạm thời.

Không có binary dataset nào được tải trong đợt này. Do đó catalog không khẳng định checksum asset, schema thực tế hay quyền đăng nhập đã thử. “Files listed” chỉ là quan sát danh sách/đường dẫn công bố.

## Trạng thái license

`explicit_data_and_code` hoặc `explicit_dataset_card` ghi một công bố cụ thể của nguồn, vẫn cần giữ đúng version/phạm vi. `repo_only_external_data_unclear` có license repository nhưng chưa xác nhận raw data kho ngoài. `repo_only_upstream_terms` và `repo_assets_with_upstream_caveat` yêu cầu kiểm tra các corpus gốc. `custom_research_terms` không phải giấy phép mở phổ quát. `not_established` nghĩa chưa tìm được bằng chứng đủ rõ trong trang đã kiểm tra, **không** có nghĩa khẳng định không tồn tại giấy phép ở bất kỳ đâu.

`conflict` là cờ không tự chọn một giấy phép để dùng. `publisher_terms_review_required` áp dụng các trang bài viết/status chưa có data-specific grant được thiết lập. `code_only` là code hoặc nền tảng, không tạo ra quyền với một dataset chưa được phát hành.

## Những xung đột đã thấy

| Nguồn | Quan sát | Quyết định kế hoạch |
|---|---|---|
| LEMMA-RCA | [Website](https://lemma-rca.github.io/) ghi CC-BY-ND-4.0; [repo](https://github.com/KnowledgeDiscovery/rca_baselines) và [HF card](https://huggingface.co/datasets/Lemma-RCA-NEC/Product_Review_Original) có cả NC và ND | Chờ xác định điều khoản đúng cho từng release, nhất là dữ liệu biến đổi |
| GAIA | [README](https://github.com/CloudWise-OpenSource/GAIA-DataSet) ghi Apache-2.0, [LICENSE](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/LICENSE) là GPL-v2 | Không tự coi raw data đã Apache; cần làm rõ ranh giới file/phạm vi |
| DeathStarBench | [README](https://github.com/delimitrou/DeathStarBench) nhắc GPL-v2, [LICENSE](https://github.com/delimitrou/DeathStarBench/blob/master/LICENSE) là Apache-2.0 | Giữ cờ xung đột code trước khi chọn nền tảng; chưa phải dataset |

Đây là bản ghi khác biệt giữa các nguồn công bố, không phải kết luận pháp lý bên nào có hiệu lực cao hơn.

## Những nguồn phải tách dữ liệu và code

[RCAEval](https://github.com/phamquiluan/RCAEval#licensing) nêu MIT cho dữ liệu và code do tác giả thực hiện; các baseline nhúng có điều khoản riêng. [AzurePublicDataset](https://github.com/Azure/AzurePublicDataset) tách CC-BY-4.0 data và MIT code. [Loghub](https://github.com/logpai/loghub) dùng điều khoản research/academic; [MS MARCO](https://microsoft.github.io/msmarco/) có điều khoản non-commercial research và không trao quyền sở hữu tài liệu web bên thứ ba.

[BEIR](https://github.com/beir-cellar/beir) không cung cấp giấy phép bao trùm mọi dataset chỉ từ license của code. Một dataset card HF ghi Apache/CC là công bố cần lưu, không tự chứng minh mọi văn bản được dẫn vào đều thuộc cùng một chủ thể quyền. Không xóa attribution, notices hay source URLs khi tạo corpus cho môn học.

## Bản đồ lineage cần kiểm soát

RCAEval → RE1/RE2/RE3 → OB/SS/TT; HF/Zenodo/Parquet là cách phân phối/biểu diễn. TORAI dùng bản xử lý RE2, không là 270 ca hoàn toàn mới để đem vào test nếu RE2 đã train.

Loghub → 19 tập con/phiên bản; Loghub-2.0 chứa annotation parsing có quan hệ nguồn gốc. mMARCO → dịch từ MS MARCO. MTRAG → human/synthetic/Cloud view; MTRAG-UN là phiên bản cần kiểm tra overlap. ITBench và ITBench-Lite là hệ sinh thái liên quan; đừng cộng cùng scenario hai lần.

Một ứng dụng Train Ticket/Online Boutique/DeathStarBench có thể được nhiều nhóm dùng để sinh nhiều bộ dữ liệu. Cùng tên ứng dụng không chứng minh trùng ca; khác tên repo cũng không chứng minh độc lập. Chỉ sau khi có manifest và dữ liệu mới kiểm tra được run/scenario/hash overlap.

## Cổng thu thập

Trước mọi batch lớn, lưu snapshot điều khoản và ngày kiểm tra; xác nhận scope file, dữ liệu dẫn xuất, mục đích học thuật và quyền công bố. Nguồn conflict/unknown không tự bật crawler. Tải mẫu sau khi quyền phù hợp; kiểm tra định dạng, PII và gold fields; sau đó mới quyết định thu thập phần cần cho thí nghiệm.

Quy trình này không yêu cầu public lại raw data. Báo cáo môn học có thể phát hành manifest, schema, hướng dẫn và code xử lý của nhóm trong phạm vi cho phép, còn người tái lập lấy dữ liệu từ nguồn gốc theo điều khoản của họ.
