# Core literature for the AIOps/RCA study

The core is the 45-row, metadata-backed selection in [`core-literature.tsv`](core-literature.tsv). It is deliberately smaller than the 1,009-record discovery registry and distinct from the 50-item reading workflow. Inclusion means “important to the study design or related-work argument”; it does not claim every work has been read in full.

| Band | Role | Rows |
|---|---|---:|
| A | Surveys and task taxonomy | 5 |
| B | LLM incident/AIOps methods | 9 |
| C | Classic RCA and causal localization | 10 |
| D | Log representation and parsing | 6 |
| E | Benchmarks and evaluation corpora | 5 |
| F | IR/RAG methods used by the implementation | 10 |
| **Total** |  | **45** |

The five explicit gap candidates are all included. CARE is included as trace/profiling context for the existing observation variants, not as a claim that trace RCA is a new contribution of this project.

P0052 and G0005 remain separate rows. The former is the failure-management preprint; the latter is the later ACM Computing Surveys work. Their relationship is `successor_same_authors`, not a publication-version merge.

## Reading and claim boundaries

- `q1_sjr_2024=yes` is copied only from the tracked publication overlay and therefore requires a true journal classification plus a valid SJR 2024 evidence row.
- A `no` Q1 value means “not counted under this audit rule”; it does not necessarily assert that the venue is low quality. It covers preprints, proceedings, conference-journal-series, SJR Q2, and journals without a tracked rank row.
- The report matrix remains the smaller set of works actually read at the recorded depth. Promoting a work to this core does not change the matrix or fabricate reading depth.
- Advanced retrieval variants that the implementation does not run remain method-support reading, not CORE padding. They stay in the priority-reading workflow where already present.
