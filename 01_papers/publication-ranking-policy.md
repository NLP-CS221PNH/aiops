# Publication type, peer review, and venue-rank policy

The 1,009 catalog rows are a discovery registry. They are not 1,009 independently deduplicated, peer-reviewed, or Q1 papers. Publication status and venue rank live in the additive `enriched/publication-class.tsv` overlay; absence from that overlay means the audit has no evidence-backed classification to publish.

## Q1 rule

`n_q1_sjr_2024` is the number of overlay rows where `publication_type=journal-article`, `venue_family` is not `conference_journal_series`, `venue_rank_scheme=sjr`, `venue_rank_value=Q1`, `venue_rank_year=2024`, and `rank_evidence_id` resolves to a tracked row in `enriched/rank-evidence.jsonl`.

This audit uses SJR 2024 only. It does not claim JCR/ISI quartiles. The join key is exact venue title, with ISSN recorded when available; ISSN is optional because the catalog did not previously contain it.

## Negative rules

- BibTeX `@article` is a formatting choice, not evidence that a work is a journal article, peer reviewed, or Q1. An arXiv-only work must be `preprint` and is emitted as `@misc`, without a `journal` field.
- HTTP availability, a matched identifier, or a Crossref record does not by itself prove peer review. `peer_reviewed` requires a journal/proceedings/book-chapter type plus verified venue and year.
- Conferences do not receive SJR Q1 labels. Conference-journal-series are also excluded even when Crossref deposits them as `journal-article`.
- The initial conference-series denylist covers `Proceedings of …`, AAAI Conference, AAAI Symposium Series, ACM SIGPLAN Notices, Proceedings of the ACM on Software Engineering (PACMSE), Proceedings of the ACM on Measurement and Analysis of Computing Systems (POMACS), Proceedings of the VLDB Endowment, and ACM SIGOPS Operating Systems Review.
- Files under `enriched/cache/`, `enriched/rescue-cache/`, and `enriched/primary-text/` are not public ranking evidence. Rank and gap claims must point to tracked sidecars.

## P0052 counterexample

P0052 is arXiv `2406.11213`, *A Survey of AIOps for Failure Management in the Era of Large Language Models*. It remains a preprint record and must not receive DOI `10.1145/3746635`. The ACM Computing Surveys work at that DOI is G0005, *A Survey of AIOps in the Era of Large Language Models*, with arXiv `2507.12472`. The manual relation is `successor_same_authors`, not a publication-version merge.

## Evidence files

- `enriched/rank-evidence.jsonl` stores one tracked SCImago excerpt per exact venue, the retrieval date, SJR year/category/quartile/value, URL, optional ISSN, and SHA-256 of `evidence_excerpt`.
- `enriched/gap-candidates-evidence.jsonl` stores the Crossref and arXiv identity snapshots used for the five gap rows.
- `enriched/publication-class.tsv` has `paper_id_or_gap_id`, `publication_type`, `peer_review_status`, `venue_exact`, optional `issn`, `venue_family`, `venue_rank_scheme`, `venue_rank_value`, `venue_rank_year`, `rank_evidence_id`, `crossref_type`, and notes.
- `enriched/work-relations.tsv` records manual version/successor decisions. Generated alias maps are not edited by hand.
