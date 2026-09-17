# Dataset readiness matrix — Hybrid RAG + RCA

Audit date: 2026-09-17. Human remaining work: `00_plan/remaining-work.md`.

Invariant: **G1 root-service ≠ G2 retrieval qrels ≠ G3 explanation/claim gold ≠ G4 causal-path gold.**

| Source | Artifact | Modalities | Native gold | License | Leakage | Split | Native qrels | Annotation still needed | Fit |
|---|---|---|---|---|---|---|---|---|---|
| RCAEval RE2-OB | 90/90 local; 270 Parquet gitignored; revision `afeacb11` (`02_datasets/acquired/meta/acquisition-status.json`) | metrics, logs, traces | G1 service/fault/inject in gitignored `processed/labels/ground_truth.jsonl`. No G2/G3/G4 | MIT | **G1-equivalent join** in tracked `acquired/labels/acquisition-manifest.tsv` and `cases-index.json` (`incident_id` → `re2ob_{service}_{fault}_{rep}`). Also `inject_time.txt`. Processed observations carry `split`/`family`. Inference bundle does not. | 54/18/18 families | none | Human G2; G3; applicability. Do not join the manifest when annotating | RCA scoring READY if G1 stays evaluator-only. RAG eval CONDITIONAL |
| RCAEval RE2-TT | metadata only (`acquired/labels/RE2-TT-metadata.json`) | would be metrics/traces/logs (89/90) | G1 in metadata | MIT | same path-name pattern | not split | none | download deferred | RCA reserve |
| OpenRCA | not in pack; Drive telemetry | NL query + telemetry | diagnostic QA labels | code MIT; data license unestablished | query.csv can leak answers | none | none | license first | NOT READY |
| ITBench-Lite/SRE | HF public; not downloaded | scenario snapshots | resolution artifacts, not G1 | Apache-2.0 | reference artifacts are answers | none | none | remap if ever used | SRE task, not RCA RAG |
| TechQA | not acquired | questions, spans, TechNotes | extractive QA + 50-candidate lists | Apache-2.0 card | LLM contamination of TechNotes | 600/310/490 | semi-qrels for QA | none for fallback QA | technical QA fallback only |
| MTRAG Cloud | not acquired | multi-turn QA + cloud docs | turn-level passage qrels | Apache-2.0 repo; upstream TOS caveat | crawl date unknown | conversations | conversational IR only | crawl-date + TOS | NLP fallback, not RCA KB |
| Loghub | not acquired | raw logs | anomaly labels on some subsets | custom research/academic | PII; unsanitized | community AD | none | PII scan if used | log AD, not RCA |
| Loghub-2.0 | not acquired | logs + parse templates | parsing gold | same custom terms | inherits Loghub PII | parsing eval | none | cite parent | parsing only |
| Kubernetes docs | in historical corpus: 14 docs, commit `7e631d03` 2023-12-31 | markdown | none | CC-BY-4.0 | pin avoids current-docs leak; cluster version unverified | n/a KB | none | applicability + G2 | KB CONDITIONAL |
| Prometheus runbooks | in historical corpus: 35 docs, commit `f8061f3e` 2023-09-07 | alert runbooks | alert-name keys ≠ qrels | Apache-2.0 | alert match ≠ root cause | n/a KB | none | per-incident relevance | KB CONDITIONAL |

**Headline:** Hybrid RAG + RCA is CONDITIONAL. Do not download OpenRCA, TechQA, MTRAG, Loghub, or RE2-TT telemetry under this plan.

See `06_implementation/docs/gold-type-contract.md`.
