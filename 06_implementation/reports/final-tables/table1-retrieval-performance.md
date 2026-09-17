# Table 1: Retrieval performance (primary RQ2)

> Qrels provenance is llm_judge_adjudicated (on-disk label llm_lexical_proxy). Not human gold. Headline IR metrics stay NOT_RUN until human-double-adjudicated G2 and frozen rankings exist. Primary RQ2 columns are IR-B / IR-D / IR-H only.

| retriever | split | eligible_n | passage_ndcg_5 | mrr_10 | recall_20 | paired_delta_vs_single | uncertainty_ci95 | qrels_provenance | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IR-B (BM25) | dev | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | - | - | llm_judge_adjudicated | NOT_RUN |
| IR-D (Dense E5) | dev | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| IR-H (Hybrid RRF) | dev | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| IR-B (BM25) | test | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | - | - | llm_judge_adjudicated | NOT_RUN |
| IR-D (Dense E5) | test | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
| IR-H (Hybrid RRF) | test | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | llm_judge_adjudicated | NOT_RUN |
