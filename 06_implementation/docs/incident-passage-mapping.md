# Incident → passage mapping

Three layers. Do not promote layer 1 or 2 to G2.

| Layer | Key | `is_qrel` | Grade |
|---|---|---|---|
| `symptom_hint` | `document_id`, `service_scope`, `symptom_family` (historical 83 MAP-* rows) | false | null |
| `incident_candidate` | `incident_id`, `document_id`, optional `chunk_id` | false | null |
| `qrel` | `query_id` + incident + chunk (plan 06 humans) | true | 0/1/2 |

TSV columns: `mapping_id, incident_id, document_id, chunk_id, mapping_layer, mapping_basis, source_id, service_scope, symptom_family, version_compatibility, is_qrel, relevance_grade, evidence_role, review_state, annotation_version`.

Forbidden: join `ground_truth` or `acquisition-manifest.tsv` to set a grade. Alert-name heading match is a key, not a qrel. Unjudged ≠ 0.

Annotators must not be given `annotations/qrels/**` or `annotations/blinded/**`.

Candidate generation uses only observed service inventories and metric-name hints, plus historical mapping and document title metadata. It does not read G1 or existing proxy judgments. `scripts/write_readiness_sidecars.py` records a reproducible six-incident train sample and caps candidates at 40 unique documents per incident. The current 156 candidates are document-level; blank `chunk_id` does not assert passage support. All remain unjudged pending two humans. Historical 83 hints and current 82 hints remain byte-stable and separate.
