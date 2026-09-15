# Representation token and selection audit

Candidate `candidate-v1`, milestone `04.variants`. Counts below are measured
from all 72 train/dev incidents with the pinned local E5 tokenizer, not a
character estimate or model inference. The final manifest and review receipt
bind the generated artifacts.

| Representation | Queries | Min tokens | Max tokens | Retained evidence occurrences | Budget drops |
|---|---:|---:|---:|---:|---:|
| R1 | 72 | 68 | 512 | 572 logs | 268 |
| R2 | 72 | 68 | 512 | 572 logs | 268 |
| R3 | 72 | 373 | 512 | 584 | 544 |

Query counts include `query: ` and two special tokens. Every rendered text is
prebudgeted once for all retrievers. Counts are actual WordPiece token counts
with implicit truncation disabled. No query is empty or insufficient on this
train/dev export; the synthetic suite checks those states separately.

R1/R2 share exactly the same full log source spans and evidence IDs after
clipping. R1/R2 have equal token counts on this export and identical text for
70/72 incidents. The remaining two differ in whitespace only. This is measured
limited variation, not evidence that normalization improves retrieval. A
synthetic U+0085/NEL fixture exercises a real tokenizer case where R1 is larger
than R2 and proves that R2 still cannot refill the joint evidence budget.

## Selection loss

The train/dev safe universe contains 1,403 exported log records. Service quotas
drop 563, leaving 840 prebudget selected logs; the joint budget drops another
268 and retains 572. All exclusions have evidence IDs and reasons in the
selection/token ledgers. No partial source slice is used. Offsets address full
redacted safe-export text in Unicode code points; normalization segment maps
reconstruct retained text without deleting technical literals.

R3 retains 405 logs, 91 metrics and 88 trace spans. Every incident retains at
least one metric and one trace. Its 544 budget-drop occurrences include the
268 joint log drops plus 276 further R3 exclusions. Metric/trace candidates
outside the configured enrichment quotas are recorded separately in the
selection ledger. The modalities deliberately consume different parts of the
512-token query budget.

The common generator bundles retain 1,482 evidence occurrences in total.
Their independent E5 counts range from 1,080 to 2,047, within the configured
2,048-token planning budget. Bundle ledgers account for 563 service-quota drops,
5,557 modality-quota drops and 78 budget drops. The bundle includes literal
evidence IDs for observation citations; these IDs are included in its token
count. Plan 07 still needs the actual generator tokenizer and separate
system/prompt, knowledge and output budgets.

## Limits and interpretation

Before/after counts live on every token-ledger record and each bundle budget.
No lost raw telemetry count is fabricated. The source selector already
restricted and number-deduplicated logs before safe export; local counts cover
only the exported universe. Token fit and complete provenance are integrity
checks, not usefulness or causal-support scores. No dev winner, ranking or
retrieval/generation quality metric was computed.
