# Retrieval qrels protocol

G1 root-service ≠ G2 retrieval qrels ≠ G3 explanation/claim gold ≠ G4 causal-path gold. G4 remains out of scope.

Current `annotations/qrels/{train,dev,test}/qrels.tsv` contain 200/180/180 historical lexical-proxy rows. Every row carries `provenance=llm_lexical_proxy`, `annotator_id=lexical-personas-A+B`, `adjudication_state=automated_proxy`, and an annotation version. These are frozen historical judgments, not reproducible human annotation. Do not score nDCG/MRR/Recall on them, including as an ablation. The lexical implementation calls no LLM; both personas share one base grade.

F1/F2 bytes are preserved. [F2.provenance.json](../freezes/F2.provenance.json) invalidates both for evaluation, retains the old F2 qrels hash, and binds the newly stamped TSVs. Future human exports require a new F2 and reviewed provenance receipt; a nonzero hash or provenance string alone does not establish human review.

## Human G2 process (downstream plan 06)

1. Review corpus applicability and release a nonempty approved whitelist before retrieval. Freeze a new F1 before test materialization or test judging; the historical empty-whitelist F1 is invalid.
2. Calibrate on five train incidents with two independent humans. Preserve original A/B forms, disagreements, a third adjudicator's rationale, timestamps and reviewer codes. The existing calibration report is retracted and supplies no human receipt.
3. For each incident, deduplicate the union of top-10 BM25, top-10 dense and top-10 hybrid passages. Shuffle candidates and hide retriever, rank and score. The six-incident coverage pilot is a separate capped hint pool, not this union pool.
4. Judge passage relevance independently as 0/1/2. Document-level relevance uses a separate form. Keep original A/B judgments and an adjudication record; LLM personas cannot fill human roles.
5. Record evidence roles from the kit: `symptom_interpretation`, `service_dependency`, `diagnostic_check`, `elimination_check`, `root_cause_support`, `counter_evidence`, `context_only`.
6. Keep unjudged rows blank, never grade zero. Judge answerability separately from retrieval success. Compute judged coverage over actual returned hits for short rankings, with explicit numerators/denominators.
7. Preserve the core allocation: 20 train + 18 dev + 18 test. The remaining 34 train incidents remain unjudged. Annotators must not receive proxy qrels, existing blinded proxy forms, G1 files, acquisition manifests or case indexes.
8. Export G2 only after independent review and adjudication with `provenance=human-double-adjudicated`, nonempty reviewer codes, adjudication state and annotation version. Bind current qrels, pool and F1 in the new F2 and the reviewed receipt. Pilot judgments are never automatically promoted to headline G2.

`verify-freezes` and `score` reject missing provenance and proxy rows. `score` also verifies freeze bindings before writing results. Blank grades stay unjudged. These checks enforce the data contract; scientific acceptance still requires inspection of original human receipts. G3 claim review remains separate and unfilled.
