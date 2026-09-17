# Schema dự kiến cho dữ liệu do bạn tự thu thập

Không có dữ liệu thật hay crawler trong file này. Đây là đặc tả để thiết kế pipeline sau này.

## Paper metadata

`paper_id`: ID nội bộ ổn định; `title`: tiêu đề nguồn ưu tiên; `original_titles`: tiêu đề tại nguồn phát hiện; `canonical_url`: landing/evidence URL; `arxiv_id/doi/acl_id`: định danh khi trích được; `authors/venue/publication_year`: để null nếu chưa kiểm chứng; `arxiv_id_year`: năm suy từ ID arXiv, **không phải năm conference/journal**; `verification_status/verified_fields`: trường nào thực sự đã đối chiếu; `source_rows`: mapping về đầu vào.

Trong gói hiện tại, null không phải lỗi parser. Nó biểu thị chưa thu thập hoặc chưa đủ bằng chứng. Không dùng `year_hint` hay năm nằm trong một danh mục awesome để lấp publication_year. Một preprint có thể được cập nhật tiêu đề hoặc có bản xuất bản khác; cần canonical-work ID khi nhập Zotero/BibTeX sau này.

### Publication-quality overlay

Catalog identity không mang nhãn chất lượng. Overlay `01_papers/enriched/publication-class.tsv` chỉ có hàng khi có bằng chứng type/preprint và gồm: `paper_id_or_gap_id`, `publication_type`, `peer_review_status`, `venue_exact`, optional `issn`, `venue_family`, `venue_rank_scheme`, `venue_rank_value`, `venue_rank_year`, `rank_evidence_id`, `crossref_type`, `notes`.

`publication_type` ∈ `journal-article | proceedings-article | preprint | book-chapter | dissertation | posted-content | other | unknown`. `peer_review_status` ∈ `peer_reviewed | preprint | not_applicable | unknown`. `peer_reviewed` chỉ hợp lệ cho journal/proceedings/book chapter có venue và năm đã xác minh. arXiv-only luôn là `preprint`.

SJR được join theo `venue_exact` và optional ISSN vào sidecar tracked. Q1 chỉ hợp lệ cho journal thật, năm rank 2024, quartile Q1 và evidence ID tồn tại. Conference cùng conference-journal-series không nhận SJR Q1 dù Crossref type là `journal-article`. Gap dùng registry G riêng; chúng không được thêm vào 1.009 `paper_id` hay canonical identifier inputs.

## Source registry

Mỗi nguồn có `source_id`, `official_url`, `canonical_release_url`, `retrieved_at`, `license_data`, `license_code`, `license_evidence_url`, `license_snapshot_hash`, `scope_notes`, `access_state`, `upstream_source_ids`, `allowed_processing`. Scope uncertainty phải là trạng thái có thể lọc, không chỉ một câu nằm cuối README.

## Incident observations

| Trường | Ý nghĩa |
|---|---|
| incident_id | Khóa cho incident thực nghiệm |
| scenario_family_id | Nhóm các ca lặp/gần giống nhau |
| system_id / service_inventory | Hệ thống và tập service hợp lệ |
| observation_start / observation_end | Cửa sổ model được nhìn |
| symptom_query | Câu hỏi hoặc mô tả chỉ từ quan sát |
| log_span_ids | Các đoạn log có nguồn và offsets |
| metric_summary_ids / trace_span_ids | Context bổ trợ |
| redaction_version | Quy tắc khử định danh |
| provenance_source / release_revision | Nguồn và phiên bản |
| split | Train/dev/test đã đóng băng |

`ground_truth` phải đặt trong bảng riêng gồm root-service, fault/reason, injection/run metadata và label provenance. Không join gold vào observations rồi serialize cả hàng cho LLM.

## Knowledge document và chunk

Mỗi tài liệu: `document_id`, `source_url`, `title`, `text_hash`, `published_at`, `updated_at`, `available_at`, `system/version_scope`, `license/source_id`, `document_kind`, `derived_from_incident_ids`. Mỗi chunk: `chunk_id`, `parent_document_id`, `start_offset`, `end_offset`, `section_heading`, `token_count`, `transform_version`. Derivative candidate uses `document_id` instead of `parent_document_id` and `chunking_version` instead of `transform_version`; see `06_implementation/docs/knowledge-corpus-schema.md`.

Giữ nguyên citation IDs qua pipeline; generator không tự tạo URL. Retrieval result gồm rank, retriever, raw score, fusion rank, rerank score và evidence span. Raw scores của retriever khác nhau không so trực tiếp nếu không hiệu chỉnh.

## Qrels và response evaluation

Qrel: `query_id`, `document_id/chunk_id`, `relevance_grade`, `evidence_role`, `annotator_id`, `adjudication_state`, `annotation_version`. Ghi unjudged khác non-relevant.

Response: `response_id`, `incident_id`, `candidate_causes`, `claims`, `evidence_ids`, `abstain`, `missing_information`, `model_revision`, `prompt_hash`, `knowledge_snapshot_hash`, `latency_breakdown`, `token_usage`. Claim annotation: supported/contradicted/insufficient-evidence, linked citation, correctness và reviewer notes.

## Provenance cho dữ liệu tổng hợp

Mọi query paraphrase, bản dịch, summary, synthetic incident cần `is_synthetic`, `generator_revision`, `input_source_ids`, `generation_date`, `human_review_state`. Một item synthetic của train incident không được rơi vào test chỉ vì có câu chữ khác.
