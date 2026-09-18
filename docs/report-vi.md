# Định vị dịch vụ sự cố với Hybrid RAG và LoRA G1 trên RCAEval RE2-Online Boutique

**Phiên bản source:** METH-LOCK-KAGGLE-20260918 overlay  
**Ngày:** 2026-09-18  
**Múi giờ:** Asia/Saigon  
**Hạn bàn giao:** 2026-09-30T12:00:00+07:00

## Trang bìa

- Nguyễn Văn Nam — 24521120
- Nguyễn Đình Phát — 23521144
- Lê Vũ Thiêm Hoàng — 25520584
- Bùi Đặng Nhật Nguyên — 23521037

Nghiên cứu này bàn giao source fine-tuning LoRA và hai báo cáo Word. Không bịa trường, khoa, hay giảng viên.

## Tóm tắt

Bài toán là **định vị dịch vụ** (service localization) trên benchmark RCAEval RE2-Online Boutique: 90 sự cố, 30 family, split family-isolated 54/18/18. Thiết kế giữ Hybrid RAG (BM25, E5 pretrained, RRF) và thêm một generator LoRA Qwen2.5-1.5B-Instruct huấn luyện G1 no-RAG (R2). E5 không được train. Thực nghiệm đầy đủ trên Kaggle là việc của người dùng sau khi nhận source; **Chưa thực hiện/điền kết quả thực nghiệm trong phiên bản này.**

## 1. Giới thiệu và câu hỏi nghiên cứu

Hệ microservice Online Boutique sinh telemetry logs/metrics/traces. Tác vụ không phải chứng minh nhân quả đầy đủ mà là xếp hạng dịch vụ gốc theo G1. Retrieval dùng corpus kiến thức; generation dùng quan sát R2, có hoặc không có đoạn kiến thức.

- RQ-IR: IR-H (RRF) so với retriever đơn mạnh hơn trên dev, cùng nDCG@5/MRR@10/coverage.
- RQ-LOC: localization Top-1/Top-3 và grounding (claim/citation) trên G0/GB/GD/GH.
- RQ-LORA: ảnh hưởng before/after LoRA G1 trên cùng prompt, context và decoding.

Ranh giới: tập test có thể đã lộ trong công việc trước (retrospective); cỡ mẫu nhỏ; corpus eligible có thể rỗng khi deployment version unknown.

## 2. Lý thuyết và công trình liên quan

BM25 [P-BM25] là baseline từ vựng. E5-small-v2 [P-E5] là encoder dense pretrained, pin `intfloat/e5-small-v2@ffb93f3bd4047442299a41ebb6fa998a38507c52`. Reciprocal Rank Fusion [P-RRF] trộn rank với c=60. RAG [P-RAG] gắn đoạn vào prompt. LoRA [P-LORA] thích nghi low-rank; recipe r=8, alpha=16, dropout=0.05, target `q_proj,v_proj`. Qwen2.5-1.5B-Instruct [P-QWEN25] revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. RCAEval [P-RCAEVAL] cung cấp RE2-OB. Định vị dịch vụ khác causal proof: G1 là nhãn dịch vụ, không phải chứng minh cơ chế.

## 3. Dữ liệu và tiền xử lý

Nguồn: RCAEval-RE2-OB, source revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. 90 incidents, 30 families, 54/18/18. Observation an toàn nằm `data/inference/`; G1 private partitions tách train/dev/test (gitignored; hash không công bố trên tip). Trainer join 54 train qua incident_id, không serialize `source_case`, family, `fault_description`, `injection_time`, gold wording. Tên service trong telemetry là evidence hợp lệ. Test 18 không vào prepare/train. Reconstruction vàng không nằm trên cây public; xem `docs/publication.md`.

## 4. Kiến trúc và huấn luyện

```
safe observations -> R2 render -> (optional) IR-B/D/H top-5
        |                              |
        +-----> local Qwen prompt <----+
        |
G1 sidecar (train only) -> completion loss / LoRA adapter
```

Mỗi incident train một example G0-style R2 no-RAG. Target JSON `{"candidate_causes":[{"service_id":"<G1>"}]}`. Loss: token CE trên target+EOS; prompt/pad = -100. Sequence train 3072, prompt cap 2944, target reserve 128, R2 observations 2048 Qwen tokens. Microbatch 1, accumulation 8, AdamW lr=1e-4, linear warmup 0.1, tối đa 3 epoch, seed 221. Checkpoint theo dev masked loss thấp nhất. Smoke 2 optimizer step namespace `runs/training/smoke`; research tách `runs/training/research`. Resume lưu optimizer, scheduler, RNG, trainer_state. Export adapter safetensors; smoke_only không dùng cho freeze nghiên cứu. Suy luận local, `local_files_only=True`, không API.

## 5. Đánh giá

Ma trận: IR-B/D/H; generation base×LoRA × G0/GB/GD/GH (8×18 thiết kế). Controls G-oracle/G-random không train/selection. G1 localization; G2 passage relevance; G3 claim support trên packed text. Judge local-model-automated-v1 có raw provenance; `llm_lexical_proxy` không phải headline. Invalid/error/abstain tính incorrect trên mẫu số 18. nDCG gain `2^rel-1`, discount `log2(rank+1)`. Family bootstrap 1000, seed 221, 6 test families. F1/F2 mới ghi output root riêng; không ghi đè `freezes/F1.json` và `F2.json`.

## 6. Tái lập

Notebook `notebooks/03_kaggle_train.ipynb`: setup → roots → deps → data-only preflight → GPU receipt → smoke 2 bước nếu có assets → full train disabled → resume/export. Lệnh: `python -m src.training preflight --data-only`; `python -m src.training train --mode smoke --max-steps 2`. Linux/Kaggle/full-train là cờ riêng. Windows clean extraction phải chạy data-only.

## 7. Hạn chế và công bố AI

54 train, class vắng, 6 family test, không supervise G3, corpus deployment unknown, test retrospective, judge cùng họ Qwen (self-preference). Công cụ AI hỗ trợ lập trình source; quyết định phương pháp và việc không điền số liệu thuộc nhóm.

## 8. Kết quả thực nghiệm

Chưa thực hiện/điền kết quả thực nghiệm trong phiên bản này.

### Bảng T1. Retrieval

| method | nDCG@5 | MRR@10 | coverage |
|---|---|---|---|
| IR-B |  |  |  |
| IR-D |  |  |  |
| IR-H |  |  |  |

### Bảng T2. Generation Top-k

| row | Top-1 | Top-3 | invalid | error | abstain | coverage |
|---|---|---|---|---|---|---|
| base×G0 |  |  |  |  |  |  |
| base×GB |  |  |  |  |  |  |
| base×GD |  |  |  |  |  |  |
| base×GH |  |  |  |  |  |  |
| lora×G0 |  |  |  |  |  |  |
| lora×GB |  |  |  |  |  |  |
| lora×GD |  |  |  |  |  |  |
| lora×GH |  |  |  |  |  |  |

### Bảng T3. Claim support

| metric | value |
|---|---|
| claim-support |  |
| citation |  |
| zero-claim-coverage |  |

### Bảng T4. Controls và family uncertainty

| metric | value |
|---|---|
| control |  |
| paired-family-delta |  |
| uncertainty |  |

### Bảng T5. Runtime

| metric | value |
|---|---|
| latency |  |
| tokens |  |
| peak-memory |  |

Phân tích lỗi thực nghiệm để trống cùng các ô số.

## 9. Kết luận thiết kế

Source đã có trainer LoRA, ranh giới dữ liệu, local provider, judging v2 và hai báo cáo trống kết quả. Câu hỏi thực nghiệm chờ user train/eval trên Kaggle. Không kết luận cải thiện phần trăm.

## Tài liệu tham khảo

- [P-RAG] Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. https://arxiv.org/abs/2005.11401
- [P-LORA] Hu et al. (2022). LoRA. https://arxiv.org/abs/2106.09685
- [P-E5] Wang et al. (2022). Text Embeddings by Weakly-Supervised Contrastive Pre-training. https://arxiv.org/abs/2212.03533
- [P-BM25] Robertson & Zaragoza (2009). The Probabilistic Relevance Framework. https://doi.org/10.1561/1500000019
- [P-RRF] Cormack et al. (2009). Reciprocal Rank Fusion. https://doi.org/10.1145/1571941.1572114
- [P-RCAEVAL] Pham et al. (2025). RCAEval. https://arxiv.org/html/2501.11735v3
- [P-QWEN25] Qwen Team (2025). Qwen2.5 Technical Report. https://arxiv.org/abs/2412.15115
- [P-PEFT] Mangrulkar et al. (2022). PEFT. https://github.com/huggingface/peft
