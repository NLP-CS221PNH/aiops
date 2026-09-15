---
phase: 6
title: "Annotation, qrels và answerability"
status: pending
priority: P1
effort: "84–150h"
dependencies: [3, 4, 5]
---

# Phase 06: Annotation, qrels và answerability

> Mô tả phạm vi ban đầu. Checklist và bước triển khai hiện hành nằm trong [plan độc lập 06](../260913-0057-cs221-06-annotation-and-qrels/plan.md). Các nội dung dưới đây giữ làm lịch sử; ownership và mốc bàn giao mới theo plan độc lập.

## Overview

Chấm 56 incident cốt lõi: 20 train pilot, 18 dev, 18 test; 34 train còn lại có thể giữ unjudged. Hai thành viên chấm độc lập; người thứ ba quản lý pool và adjudication. Công việc trải tuần 2–6, phần test chỉ bắt đầu sau khóa hệ thống; không buộc chờ toàn phase để triển khai generation.

## Requirements

Hiện chưa có human gold. Pool top-10 BM25, dense, hybrid và hybrid+reranker nếu được chọn: tối đa 30/40 cặp query–chunk trước dedup. Với giả định 30–40 cặp/incident, hai lượt chấm tạo 3.360–4.480 judgments. Giả định 45–75 giây/lượt relevance: 42–93 giờ; tổng 84–150 giờ-người gồm chuẩn bị, đọc sâu, answerability/reference và adjudication. Đo lại sau năm ca; đây là dự toán, không phải tốc độ đã kiểm chứng.

## Architecture

Runs có provenance → hợp pool/xáo thứ tự → phiếu A/B độc lập → agreement → adjudication → qrels và references. Người xây hệ thống không nhận feedback test trước khi đóng băng model/config/prompt; chỉ mở điểm sau khi qrels test đã khóa. Gold injection service dùng chấm localization riêng, không tự thành relevance.

## Related Code Files

Đọc `03_collection_plan/annotation-kit/README.md`, các phiếu trống và `05_research/retrieval-preview/`. Seed cũ chỉ BM25, cần tạo lại khi query/corpus đổi.

Tạo dưới `06_implementation/annotations/`: `rubric-v1.md`, `assignments.tsv`, `pools/{train,dev,test}.jsonl`, `blinded/{split}-{A,B}.tsv`, `adjudication.tsv`, `qrels/{split}.tsv`, `answerability.tsv`, `reference-answers.jsonl`, `annotation-manifest.json`. Tạo `src/annotations/{build_pool.py,export_gold.py}` và `tests/test_annotation_integrity.py`.

## Implementation Steps

1. **Chốt rubric.** Grade 0/1/2, evidence role, supported_claim và span document; document relevance và passage relevance là hai trường riêng. Định nghĩa answerable/partially_answerable/unanswerable/uncertain và applicability. Empty là unjudged; LLM draft nếu có chỉ hỗ trợ, phải ghi provenance và được người kiểm.
2. **Pool pilot.** Chọn 20 train incidents đại diện families; seed pool cũ có thể điều chỉnh nếu thiếu đại diện. Hợp top-10 của 3/4 hệ thống được đánh giá theo query+chunk, lưu retriever/rank/score trong bản quản lý. Phiếu chấm che các trường này, xáo bằng seed. Khoảng 30–40 là ước lượng; không cắt im lặng candidates bổ sung. Chấm đủ top-5 primary và top-10 nếu tính MRR; mở rộng depth ghi lý do và công chấm.
3. **Chấm độc lập và hiệu chỉnh.** A/B đọc cùng observations, tài liệu và điều kiện áp dụng; không xem phiếu nhau. Sau năm ca đo thời gian, sau 20 ca tính raw agreement, weighted kappa và phân bố grades trước adjudication. Bất đồng do rubric phải sửa phiên bản và chấm lại phần ảnh hưởng; không đặt ngưỡng agreement thành bằng chứng corpus đầy đủ.
4. **Chấm dev và viết references.** Hai người chấm 18 dev ca; người thứ ba giải quyết bất đồng bằng evidence. Kiểm answerability từ corpus được phép, không suy từ BM25 thất bại. Reference gồm claim bắt buộc, citations, unknowns và next checks. Phân biệt evidence hỗ trợ bước kiểm tra với chứng minh nguyên nhân.
5. **Khóa rồi mới pool test.** Mốc 06A là train/dev qrels, đủ để B+C tạo manifest F1 cùng pilot 07A; không chờ 06B. Sau F1, 06B chạy hệ thống cố định tạo pool 18 test, hai người chấm không trả feedback để chỉnh hệ thống. 06B xuất F2 (qrels freeze), rồi phần scoring 08 mới bắt đầu. Deepening ghi trước scoring; mọi baseline dùng cùng gold cuối.
6. **Xuất gold.** Giữ phiếu A/B, adjudication và lịch sử. Validator từ chối nhãn thiếu reviewer, ID/span sai, sai snapshot hoặc hàng chưa adjudicate. Top-5 còn unjudged chặn primary scoring; top-10 chưa chấm chặn MRR. Recall@20/50 chỉ là pooled diagnostic kèm judged coverage, không đòi toàn depth được chấm và không coi ngoài pool là 0.

## Success Criteria

- [ ] 56 ca được chấm đôi; qrels/reference và manifest có version, provenance.
- [ ] Agreement trước adjudication được báo; mọi bất đồng có quyết định lưu.
- [ ] Test không dùng chọn cấu hình; top-5 primary/top-10 MRR được chấm đủ; high-depth diagnostic báo judged coverage.
- [ ] 34 train unjudged vẫn phân biệt rõ; không nhân repetitions thành mẫu độc lập.

## Risk Assessment

Pool thiếu evidence: cho người chấm bổ sung và báo incompleteness. Công vượt 150 giờ: giảm nhánh mở rộng/độ dài reference, bàn lại scope trước test; không bỏ top-k hoặc giả nhãn. Thiếu người chấm thứ hai: đây là gate nhân lực chưa đạt, không thay bằng hai lượt cùng LLM. Test chỉ sáu families nên phase 08 phải báo độ bất định và count cụ thể.
