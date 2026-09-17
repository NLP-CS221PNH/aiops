# MVP scientific controls

Primary RQ2 remains IR-B / IR-D / IR-H only. Rows below are extra labeled controls, not a second primary.

| Control | Status | Evidence |
|---|---|---|
| G0 (observations only) | Existing generation floor | F1 condition `G0` |
| G-oracle | Retrieval-side packed; generation `NOT_RUN` | `src/evaluation/controls.py` `pack_oracle`; gold-in-top-5 nDCG@5 = 1.0 by construction |
| G-random / wrong evidence | Seeded packer; generation `NOT_RUN` | `pack_random`; judged rel=0, else corpus sample |
| Answerability slice | `NOT_RUN` | Annotator TSVs are `needs_human_review` with empty labels; no invented unanswerable gold |
| Historical vs current leakage | Diagnostic overlap only | Historical 74 docs / 580 chunks vs current 73 docs / 598 chunks; shared document IDs = 0; shared source paths = 73; IR-H nDCG@5 delta `NOT_RUN` (current corpus is not mixed into the F1 index). See `results/leakage-diagnostic.json`. |

Generation for G-oracle / G-random stays `NOT_RUN` while API permission and `approved_cap_usd` are pending. `src/generation/provider.py` mock success is refused (`refusing_mock_as_result`), not recorded as a result.

## Deferred

IR-R, GraphRAG, multi-agent, iterative retrieval, R1/R2/R3 test grid, source-type corpus split, second generator. These are deferred, not missing failures of the frozen R2 + IR-B/D/H comparison.
