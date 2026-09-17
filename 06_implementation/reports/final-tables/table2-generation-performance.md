# Table 2: Generation performance

> Qrels provenance is llm_judge_adjudicated (on-disk label llm_lexical_proxy). Not human gold. Headline IR metrics stay NOT_RUN until human-double-adjudicated G2 and frozen rankings exist. Primary RQ2 columns are IR-B / IR-D / IR-H only.

| condition | responses_n | top1_service_acc | top3_service_acc | citation_validity | claim_support_precision | abstention_rate | qrels_provenance | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0 (No-RAG) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| GB (BM25 RAG) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| GD (Dense RAG) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| GH (Hybrid RAG) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
