# Gold-type contract

Frozen 2026-09-17. Validation: contract+tests for G1 leaks; F1/F2 bytes kept; sidecar invalidates human wording.

Public tip paths below are post-flatten. Evaluator gold and trainer partitions are **gitignored** and are not in the public tree.

| Layer | Meaning | Canonical path | Who may read | Headline metric? |
|---|---|---|---|---|
| G1 | Injected root-service / fault / inject time | gitignored local gold (not in this tree) | evaluator only | service localization only |
| G1 copy | Must match G1 SHA-256 | gitignored `data/private/` | evaluator only | same |
| G1-equivalent leak | `incident_id` → `re2ob_{service}_{fault}_{rep}` | historical git blobs only (`acquisition-manifest.tsv`, `cases-index.json`); **not on the public tip** | **not annotators, not mapping generators** | never |
| G2 | Human passage/document relevance 0/1/2 | local `annotations/qrels/{train,dev,test}/qrels.tsv` after human export | evaluator after freeze | nDCG@5 only if `provenance=human-double-adjudicated` |
| G2-proxy | Lexical judge, pool-circular | same qrels paths today | forensics only | **no** nDCG/MRR/Recall |
| G3 | Claim / explanation support | local annotation-kit claim table | evaluator | citation support; currently empty |
| G4 | Causal path | does not exist | n/a | out of scope; never synthesize |

Forbidden joins:

- G1 or G1-equivalent into queries, indexes, candidate generation, or annotator-facing files.
- Scoring nDCG from G1 or from G2-proxy.
- Calling G2-proxy human.
- Inventing G4 from topology.

Model-visible input is only `data/inference/`.

G1-equivalent leak **file hashes are not published on the public tip**. Cloning with git history still contains those blobs and `inject_time.txt`. Untrack is not a leak control. See `docs/publication.md`.

Existing `freezes/F2.json` limitations still say "human"; `F2.provenance.json` is authoritative for this working tree when present locally.

## Trainer-only G1 overlay (2026-09-18)

Fine-tuning opens a **train-only** G1 reader. It does not change the inference loader.

| Layer | Who may read | Path |
|---|---|---|
| G1 train partition (54) | LoRA trainer loss only | gitignored `data/training-inputs/v1/private-train/` |
| G1 dev partition (18) | checkpoint selection / evaluator | gitignored `data/training-inputs/v1/private-dev/` |
| G1 test partition (18) | evaluator after freeze | gitignored `data/training-inputs/v1/private-test/` |
| Safe observations | inference and trainer prompts | `data/inference/` |

Trainer commands must not `stat`/`open`/`hash` the test partition. `source_case`, gold wording, fault metadata and family ids stay out of serialized prompts. Service names inside telemetry remain evidence.
