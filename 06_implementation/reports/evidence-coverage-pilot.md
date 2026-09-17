# Evidence coverage pilot

Coverage is **unmeasured_no_reviewer**. The sample has six incidents from 54 train incidents; there are zero human judgments. Coverage rate and answerability remain null, not zero. Even a measured k/6 would not be a population estimate or a project kill switch.

[Candidate IDs](../annotations/coverage-pilot/candidate-ids.tsv) are shuffled with seed 221. The coordinator samples uniformly from sorted train IDs and then shuffles using the same random generator. No G1 or family stratification is used. The [manifest](../annotations/coverage-pilot/manifest.json) records input hashes and candidate counts.

The [candidate table](../../03_collection_plan/annotation-kit/incident-document-candidates.tsv) contains 156 document candidates, 24–30 per incident (cap 40). These derive from observed service inventory and metric-name hints intersected with the historical 83 mappings, with title matches used only to order candidates. Inventories are broad, so lists can coincide; this is not evidence of relevance. Passage IDs and relevance grades remain blank. All rows are `is_qrel=false` and `needs_human_review`.

Future reviewers receive redacted inference evidence, the shuffled IDs, candidate documents, and blank judgment forms. They must not receive proxy qrels, blinded proxy forms, G1, acquisition manifests or case indexes. Two independent humans must record answerability, grade-2 document/chunk counts, missing-evidence notes and reviewer codes. No fault diversity analysis is published here.

Unanswerable is not a retrieval miss. Pilot judgments are never promoted automatically to G2; downstream plan 06 must re-judge under the frozen retriever union pool. This unmeasured outcome satisfies the current plan's permitted no-human branch.
