# Qrels provenance

The train/dev/test TSVs are historical `llm_lexical_proxy` dumps, retained for forensics. All 560 rows carry provenance, annotator identity, adjudication state and annotation version; grades and original fields were preserved.

[F2.provenance.json](../../freezes/F2.provenance.json) retains `qrels_hash` from historical F2, records each `historical_sha256`, and binds the updated files through `qrels_files.*.sha256` and `current_qrels_hash`. Historical F1/F2 bytes stay unchanged and are invalid for evaluation. Neither proxy metrics nor an ablation on these labels is admissible.

A later human export needs independently reviewed A/B and adjudicator records plus a new F2. See [the protocol](../../docs/retrieval-qrels-protocol.md).
