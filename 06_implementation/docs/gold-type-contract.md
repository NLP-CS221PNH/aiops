# Gold-type contract

Frozen 2026-09-17. Validation: contract+tests for G1 leaks; F1/F2 bytes kept; sidecar invalidates human wording.

| Layer | Meaning | Canonical path | Who may read | Headline metric? |
|---|---|---|---|---|
| G1 | Injected root-service / fault / inject time | `02_datasets/processed/labels/ground_truth.jsonl` (gitignored) | evaluator only | service localization only |
| G1 copy | Must match G1 SHA-256 | `06_implementation/data/private/ground_truth.jsonl` | evaluator only | same |
| G1-equivalent leak | `incident_id` → `re2ob_{service}_{fault}_{rep}` | `02_datasets/acquired/labels/acquisition-manifest.tsv`, `cases-index.json` (tracked) | **not annotators, not mapping generators** | never |
| G2 | Human passage/document relevance 0/1/2 | `06_implementation/annotations/qrels/{train,dev,test}/qrels.tsv` after human export | evaluator after freeze | nDCG@5 only if `provenance=human-double-adjudicated` |
| G2-proxy | Lexical judge, pool-circular | same qrels paths today; see `freezes/F2.provenance.json` | forensics only | **no** nDCG/MRR/Recall |
| G3 | Claim / explanation support | `03_collection_plan/annotation-kit/claim-evaluation.tsv` | evaluator | citation support; currently empty |
| G4 | Causal path | does not exist | n/a | out of scope; never synthesize |

Forbidden joins:

- G1 or G1-equivalent into queries, indexes, candidate generation, or annotator-facing files.
- Scoring nDCG from G1 or from G2-proxy.
- Calling G2-proxy human.
- Inventing G4 from topology.

Model-visible input is only `06_implementation/data/inference/`.

G1-equivalent leak hashes (tracked; not inference inputs):

| File | SHA-256 |
|---|---|
| `02_datasets/acquired/labels/acquisition-manifest.tsv` | `47af346e2c166fb1df4d7fff58c26c9a27f60bfb72a6b11c257dafa912319c9f` |
| `02_datasets/acquired/labels/cases-index.json` | `8115c9dff87296d4dccca2014220c8e84c252b2f024fb07b41a1e7cb09c8a3aa` |

Existing `freezes/F2.json` limitations still say "human"; `F2.provenance.json` is authoritative for this working tree.
