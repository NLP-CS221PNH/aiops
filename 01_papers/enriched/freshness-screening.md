# Sàng lọc tài liệu mới gần thời điểm research

Ngày đối chiếu: 13-09-2026. Cả sáu mục dưới đây được đọc ở mức **abstract-only**; không trích numerical gains để kết luận hơn/kém và không nhập tự động vào catalog gốc.

## TORAI: Multi-source Root Cause Analysis for Blind Spots in Microservice Service Call Graph

arXiv `2604.13522`, version 2; 2026 preprint. Pham, Luan; Ha, Huong; Zhang, Xiuzhen; Zhang, Hongyu.

Đã có P0767; không thêm duplicate. Blind spots khiến call graph thiếu services; TORAI dùng anomaly severity, clustering và causal ranking từ telemetry sẵn có. Động cơ cho missing-modality/trace coverage tests; abstract không cấp release hoặc gold path.

Nguồn: [arXiv](https://arxiv.org/abs/2604.13522); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2604.13522).

## KRCA: An Efficient Root Cause Analysis System in Hyper-scale Microservice Systems via Agentic AI

arXiv `2607.01788`, version 3; 2026 preprint. Jiang, Jiamin; Feng, Jingfei; Luo, Yu; Zhang, Qingliang; Sun, Yongqian; Gu, Wenwei; Zhang, Shenglin; Cui, Tianyu; Wu, Yao; Huang, Jielong; Qi, Nan; Pei, Dan.

Candidate mới ngoài catalog. KRCA drilldown API, skeleton graph prior rồi memory-augmented agents. Đánh giá trên production context cần full protocol; không chuyển số accuracy sang suite dự án.

Nguồn: [arXiv](https://arxiv.org/abs/2607.01788); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2607.01788).

## GALA: Can Graph-Augmented Large Language Model Agentic Workflows Elevate Root Cause Analysis?

arXiv `2508.12472`, version 1; 2025 preprint. Tian, Yifang; Liu, Yaming; Chong, Zichun; Huang, Zihang; Jacobsen, Hans-Arno.

Candidate GALA 2025 giữ riêng. Kết hợp causal inference với iterative LLM reasoning và human-guided output evaluation. Không mặc định acronym giống nhau nghĩa cùng version; kiểm authors/relations trước merge.

Nguồn: [arXiv](https://arxiv.org/abs/2508.12472); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2508.12472).

## GALA: Graph-Augmented LLM Agents for Root Cause Analysis and Incident Response in Microservices

arXiv `2608.08968`, version 1; 2026 preprint. Tian, Yifang; Liu, Yaming; Chong, Zichun; Huang, Zihang; Li, Yiran; Jacobsen, Hans-Arno.

Candidate 2026; title GALA, abstract gọi phương pháp GALA+. Graph-guided investigation, STRIX scoring và SURE-Score human-guided quality evaluation. Cần đọc full text để tách contribution graph/scoring/agent và thiết kế human rubric.

Nguồn: [arXiv](https://arxiv.org/abs/2608.08968); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2608.08968).

## Beyond Fault Localization: A Trajectory-Level Study of LLM Agents for Microservice Root Cause Analysis

arXiv `2608.21310`, version 1; 2026 preprint. Lu, Qisheng; Fang, Aoyang; Xu, Junjielong; Shang, Jin'ao; Zhang, Songhan; Yang, Yifan; Yan, Xiaochuan; He, Pinjia.

Candidate gần trực tiếp với H3 của plan. Trajectory-level evaluation tách service correctness khỏi fault-propagation reconstruction; DiagGuard grounding và verification. Phải có gold path trước chấm propagation; abstract không đủ audit annotations/bias.

Nguồn: [arXiv](https://arxiv.org/abs/2608.21310); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2608.21310).

## Can LLMs Really Recover Microservice Failures? A Recovery-Aware Evaluation of Diagnosis-to-Action Reasoning

arXiv `2607.04623`, version 1; 2026 preprint. Qi, Jiaxing; Luan, Zhongzhi; Zhang, Hongyu; Huang, Shaohan; Fung, Carol; Tong, Yongxin; Yang, Hailong; Qian, Depei.

Candidate R2Act, scope rộng hơn MVP read-only. Post-diagnosis action-space, target admissibility và recovery validity; phân biệt correct diagnosis với valid action. Dùng để giới hạn claim của đồ án: next-check suggestion không là successful recovery.

Nguồn: [arXiv](https://arxiv.org/abs/2607.04623); [metadata](https://api.datacite.org/dois/10.48550/arxiv.2607.04623).
