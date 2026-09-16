# Báo Cáo Tổng Duyệt & Diễn Tập Demo Offline (Plan 09 - Rehearsal)

**Thời điểm thực hiện:** 2026-09-15T23:55:00Z  
**Người vận hành (Operator):** C (Điều phối)  
**Người kiểm tra độc lập (Reviewer):** B (Thiết kế & Tái lập) / A (Nguồn & Dữ liệu)  
**Môi trường thử nghiệm:** Windows 11 x64, Python 3.11.9 Virtualenv, Ngắt kết nối mạng hoàn toàn (Air-gapped simulation)  
**Chế độ chạy:** `display_mode: fixture` (Replay trên offline artifacts)  
**Phiên bản kịch bản:** `docs/demo-script.md` (v1.0.0)  
**Thời lượng diễn tập thực tế:** 350 giây (~5 phút 50 giây — đạt mục tiêu 5–7 phút)  

---

## 1. Bản ghi các bước diễn tập (Rehearsal Timeline & Receipts)

| Mốc thời gian | Thao tác trên giao diện | Trạng thái hiển thị | Kết quả kiểm tra | Người ký nhận |
|---|---|---|---|---|
| **00:00 – 00:35** | Mở trang chủ `http://127.0.0.1:8080/`, đọc disclaimer | Header hiển thị banner cảnh báo nghiên cứu, badge [DỮ LIỆU MÔ PHỎNG] | ĐẠT: Không phát sinh request ngoại vi | B |
| **00:35 – 02:15** | Chọn Ca 1 (`fixture:case_01_success`), kiểm tra Cột 1, Cột 2 và click citation `[know_redis_manifest_01]` | Cột giữa tự động scroll và highlight đoạn manifest Kubernetes `limits: memory 256Mi` viền vàng | ĐẠT: Đi từ claim tới đúng exact context text và offsets `[0:380]` | A & B |
| **02:15 – 03:45** | Chọn Ca 2 (`fixture:case_02_weak_diagnosis`), kiểm tra chẩn đoán yếu | Cột 3 hiển thị `confidence: low`, cảnh báo thiếu thông tin cấu hình hàng đợi email | ĐẠT: Nhận thức giới hạn đúng, không hallucinate | B |
| **03:45 – 04:50** | Chọn Ca 3 (`fixture:case_03_missing_evidence`), kiểm tra điều kiện G0 (No-RAG) | Cột giữa trống, Cột 3 hiển thị `ABSTAIN: TRUE`, danh sách nguyên nhân rỗng | ĐẠT: Từ chối chẩn đoán an toàn | B |
| **04:50 – 05:25** | Chọn Ca 4 (`fixture:case_04_invalid_citation`), kiểm tra bẫy lỗi | Hiển thị hộp thông báo đỏ `INVALID_CITATION`, bắt đúng ID giả mạo `hallucinated_evidence_external_99` | ĐẠT: Lớp validator chặn đứng citation ảo | A |
| **05:25 – 05:50** | Chọn Ca 5 / bấm menu `So sánh đối chứng (GB vs GH)` | Màn hình 2 cột so sánh side-by-side; xác nhận cùng incident `inc_0f782051d78bc07a` và cùng hash viễn trắc | ĐẠT: Preconditions compare chuẩn xác | B |

---

## 2. Bảng đối chiếu Tuyên bố thuyết trình & Bằng chứng (Claim Map)

| Bước kịch bản | Tuyên bố thuyết trình | Artifact tham chiếu | Giới hạn & Ghi chú |
|---|---|---|---|
| 1. Disclaimers | Demo chạy offline, không đại diện aggregate 18 test | `docs/demo-runbook.md` | Mọi số liệu định lượng phải lấy từ `08.results` |
| 2. Ca 1 (GH) | Redis disk IO saturation gây nghẽn socket | `tests/fixtures/demo/run_gh_redis/` | Có exact context từ manifest thật |
| 3. Ca 2 (GB) | BM25 chỉ lấy được tài liệu chung, hạ confidence | `tests/fixtures/demo/run_gb_email/` | Thể hiện điểm yếu của lexical search thuần |
| 4. Ca 3 (G0) | Không có RAG thì từ chối chẩn đoán (abstain) | `tests/fixtures/demo/run_g0_recommendation/` | Không bịa ra nguyên nhân khi thiếu tri thức |
| 5. Ca 4 (GD) | Trích dẫn không có trong context bị validator bắt | `tests/fixtures/demo/run_gd_invalid_citation/` | Hiển thị raw escaped text, không crash app |
| 6. Ca 5 (Compare) | Hybrid GH xếp hạng tài liệu manifest cao hơn GB | `tests/fixtures/demo/run_gb_redis/` | Đảm bảo cùng incident ID và hash viễn trắc |

---

## 3. Nhật ký sự cố phát hiện và biện pháp xử lý (Issue Log)

| ID | Mức độ | Case ID | Hiện tượng quan sát | Nguyên nhân gốc | Biện pháp đã khắc phục | Trạng thái |
|---|---|---|---|---|---|---|
| **ISS-01** | Minor | CLI Export | Windows cp1252 console ném `UnicodeEncodeError` khi in chuỗi tiếng Việt | Mặc định PowerShell Windows không dùng UTF-8 cho stdout | Đổi thông báo print sang tiếng Anh chuẩn trong CLI entrypoint | **ĐÃ GIẢI QUYẾT** |
| **ISS-02** | Trivial | UI | Cần phím tắt nhanh để chuyển sang chế độ Compare | Tiện ích khi thuyết trình trực tiếp | Thêm listener phím `C` trong JavaScript để mở nhanh `/compare` | **ĐÃ GIẢI QUYẾT** |

---

## 4. Kết luận nghiệm thu (Gate G09-C / 09.demo)

- Toàn bộ 5 case hoạt động mượt mà trong chế độ Replay/Fixture không cần internet.
- Thời lượng diễn tập đạt 5 phút 50 giây (nằm chuẩn trong khung 5–7 phút).
- Bằng chứng trích dẫn được làm nổi bật trực tiếp tới từng đoạn text đã gửi generator.
- Bàn giao đầy đủ manifest, backup tĩnh HTML và runbook cho Phase 10 (`260913-0057-cs221-10-report-and-release`).
- **Đánh giá chung:** ĐẠT GATE G09-C (Chấp thuận bàn giao).
