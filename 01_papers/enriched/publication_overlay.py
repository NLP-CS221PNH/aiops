"""Build publication-class overlays, gap exports, and type-safe BibTeX.

The 1,009-record catalog remains the identity registry.  This module emits only
rows supported by publication/preprint evidence and never treats a BibTeX entry
type as evidence of peer review or venue rank.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent

PUBLICATION_TYPES = {
    "journal-article",
    "proceedings-article",
    "preprint",
    "book-chapter",
    "dissertation",
    "posted-content",
    "other",
    "unknown",
}
OVERLAY_COLUMNS = [
    "paper_id_or_gap_id",
    "publication_type",
    "peer_review_status",
    "venue_exact",
    "issn",
    "venue_family",
    "venue_rank_scheme",
    "venue_rank_value",
    "venue_rank_year",
    "rank_evidence_id",
    "crossref_type",
    "notes",
]
GAP_COLUMNS = [
    "gap_id",
    "title",
    "authors",
    "doi",
    "arxiv_id",
    "publication_type",
    "peer_review_status",
    "venue_exact",
    "issued",
    "venue_rank_scheme",
    "venue_rank_value",
    "venue_rank_year",
    "rank_evidence_id",
    "why_in_scope",
    "core_candidate",
    "catalog_overlap",
    "source_url",
    "retrieved_at",
    "status",
    "evidence_ids",
]

CONFERENCE_SERIES_EXACT = {
    "Proceedings of the ACM on Software Engineering",
    "Proceedings of the ACM on Measurement and Analysis of Computing Systems",
    "Proceedings of the VLDB Endowment",
    "ACM SIGPLAN Notices",
    "ACM SIGOPS Operating Systems Review",
    "Proceedings of the AAAI Conference on Artificial Intelligence",
    "Proceedings of the AAAI Symposium Series",
}
CONFERENCE_SERIES_PREFIXES = (
    "proceedings of ",
    "proceedings - ",
    "proceedings of the aaai ",
    "aaai conference",
    "aaai symposium",
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def evidence_hash(excerpt: str) -> str:
    return hashlib.sha256(excerpt.encode("utf-8")).hexdigest()


def is_conference_series(venue: str | None) -> bool:
    value = html.unescape(venue or "").strip()
    if value in {html.unescape(item) for item in CONFERENCE_SERIES_EXACT}:
        return True
    folded = value.casefold()
    return folded.startswith(CONFERENCE_SERIES_PREFIXES)


def preferred_metadata(record: dict) -> dict:
    research = record.get("research", {})
    return research.get("publication_metadata") or research.get("metadata") or {}


def classify_record(record: dict, rank_by_venue: dict[str, dict] | None = None) -> dict | None:
    """Return an evidence-supported overlay row, or None for unknown records."""
    preferred = preferred_metadata(record)
    research = record.get("research", {})
    publication_type = preferred.get("publication_type")
    source_kind = preferred.get("source_kind", "")
    citation_tags = preferred.get("citation_tags") or {}
    arxiv_id = record.get("arxiv_id") or record.get("discovered_arxiv_id")
    year_basis = str(preferred.get("year_basis") or "")

    if source_kind == "primary_page_citation_tags" and citation_tags.get("citation_conference_title"):
        publication_type = "proceedings-article"
    elif not publication_type and arxiv_id and (
        "arxiv" in year_basis.casefold()
        or "arxiv" in str(preferred.get("metadata_source_url") or "").casefold()
        or not research.get("publication_metadata")
    ):
        publication_type = "preprint"

    mapped = {
        "journal": "journal-article",
        "proceedings": "proceedings-article",
        "book": "book-chapter",
        "dissertation": "dissertation",
    }.get(publication_type, publication_type)
    if mapped not in PUBLICATION_TYPES or mapped == "unknown":
        return None

    venue = preferred.get("venue") or record.get("venue") or ""
    venue_family = "conference_journal_series" if is_conference_series(venue) else ""
    year = preferred.get("publication_year") or record.get("publication_year") or record.get("reference_year")
    if mapped == "preprint":
        peer_review = "preprint"
    elif mapped in {"journal-article", "proceedings-article", "book-chapter"}:
        peer_review = "peer_reviewed" if venue and year else "unknown"
    elif mapped in {"posted-content", "dissertation"}:
        peer_review = "not_applicable"
    else:
        peer_review = "unknown"

    rank = None
    if rank_by_venue and mapped == "journal-article" and not venue_family:
        rank = rank_by_venue.get(venue)

    notes = ["catalog evidence"]
    if source_kind:
        notes.append(source_kind)
    if mapped == "preprint":
        notes.append("arXiv-only evidence; not peer review")
    if venue_family:
        notes.append("conference journal series; excluded from SJR Q1")
    if mapped == "journal-article" and not venue_family and not rank:
        notes.append("no tracked SJR 2024 row; rank unclaimed")
    return {
        "paper_id_or_gap_id": record["paper_id"],
        "publication_type": mapped,
        "peer_review_status": peer_review,
        "venue_exact": venue,
        "issn": rank.get("issn", "") if rank else "",
        "venue_family": venue_family,
        "venue_rank_scheme": "sjr" if rank else "",
        "venue_rank_value": rank.get("quartile", "") if rank else "",
        "venue_rank_year": str(rank.get("sjr_year", "")) if rank else "",
        "rank_evidence_id": rank.get("evidence_id", "") if rank else "",
        "crossref_type": preferred.get("publication_type", ""),
        "notes": "; ".join(notes),
    }


def gap_overlay_row(gap: dict, rank_by_id: dict[str, dict]) -> dict:
    rank = rank_by_id.get(gap.get("rank_evidence_id", ""))
    return {
        "paper_id_or_gap_id": gap["gap_id"],
        "publication_type": gap["publication_type"],
        "peer_review_status": gap["peer_review_status"],
        "venue_exact": gap["venue_exact"],
        "issn": rank.get("issn", "") if rank else "",
        "venue_family": "conference_journal_series" if is_conference_series(gap["venue_exact"]) else "",
        "venue_rank_scheme": gap.get("venue_rank_scheme", ""),
        "venue_rank_value": gap.get("venue_rank_value", ""),
        "venue_rank_year": str(gap.get("venue_rank_year", "")),
        "rank_evidence_id": gap.get("rank_evidence_id", ""),
        "crossref_type": gap["publication_type"],
        "notes": "gap overlay; " + ",".join(gap.get("evidence_ids", [])),
    }


def bib_type_for(classification: dict | None) -> str:
    if not classification:
        return "misc"
    publication_type = classification["publication_type"]
    if publication_type == "journal-article" and classification.get("venue_family") != "conference_journal_series":
        return "article"
    if publication_type == "proceedings-article" or classification.get("venue_family") == "conference_journal_series":
        return "inproceedings"
    if publication_type == "book-chapter":
        return "incollection"
    return "misc"


def bib_escape(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def bib_entry(record: dict, classification: dict | None) -> str | None:
    research = record.get("research", {})
    if research.get("identity_status") != "matched":
        return None
    preferred = preferred_metadata(record)
    authors = record.get("authors") or preferred.get("authors") or []
    year = record.get("reference_year") or preferred.get("publication_year")
    title = record.get("reference_title") or preferred.get("title") or record.get("title")
    if not authors or not year or not title:
        return None
    venue = record.get("venue") or preferred.get("venue") or ""
    doi = record.get("publication_doi")
    arxiv_id = record.get("arxiv_id") or record.get("discovered_arxiv_id")
    url = record.get("reference_url") or record.get("canonical_url")
    kind = bib_type_for(classification)
    fields: list[tuple[str, object]] = [
        ("title", "{" + bib_escape(title) + "}"),
        ("author", " and ".join(bib_escape(author) for author in authors)),
        ("year", year),
        ("url", url),
    ]
    if venue:
        if kind == "article":
            fields.append(("journal", bib_escape(venue)))
        elif kind in {"inproceedings", "incollection"}:
            fields.append(("booktitle", bib_escape(venue)))
        else:
            fields.append(("howpublished", bib_escape(venue)))
    if doi:
        fields.append(("doi", doi))
    if arxiv_id:
        fields.extend((("eprint", arxiv_id), ("archivePrefix", "arXiv")))
    publication_year = record.get("publication_year")
    basis = "publication year" if publication_year else "arXiv preprint year; publication venue not verified"
    fields.append(("note", f"Verified descriptive metadata; {basis}; accessed 2026-09-13"))
    source = preferred.get("metadata_source_url")
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
    return f"% Metadata source: {source}\n@{kind}{{{record['paper_id']},\n{body}\n}}\n"


def gap_bib_entry(gap: dict) -> str:
    fields: list[tuple[str, object]] = [
        ("title", "{" + bib_escape(gap["title"]) + "}"),
        ("author", " and ".join(bib_escape(author) for author in gap["authors"])),
        ("journal", bib_escape(gap["venue_exact"])),
        ("year", str(gap["issued"])[:4]),
        ("doi", gap["doi"]),
        ("url", "https://doi.org/" + gap["doi"]),
    ]
    if gap.get("arxiv_id"):
        fields.extend((("eprint", gap["arxiv_id"]), ("archivePrefix", "arXiv")))
    fields.append(("note", "Gap overlay; Crossref and rank evidence recorded in tracked sidecars"))
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
    return f"@article{{{gap['gap_id']},\n{body}\n}}\n"


def tsv_text(rows: list[dict], columns: list[str]) -> str:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        encoded = dict(row)
        for key, value in encoded.items():
            if isinstance(value, list):
                encoded[key] = "; ".join(str(item) for item in value)
        writer.writerow(encoded)
    return buffer.getvalue()


def validate_evidence(rows: list[dict], label: str) -> list[str]:
    errors = []
    ids = [row.get("evidence_id") for row in rows]
    if not rows or len(ids) != len(set(ids)) or any(not item for item in ids):
        errors.append(f"{label}: evidence IDs must be nonempty and unique")
    for row in rows:
        if row.get("sha256") != evidence_hash(row.get("evidence_excerpt", "")):
            errors.append(f"{label}: excerpt hash mismatch for {row.get('evidence_id')}")
        if not str(row.get("url", "")).startswith("https://"):
            errors.append(f"{label}: non-HTTPS source for {row.get('evidence_id')}")
    return errors


def build_outputs() -> tuple[dict[str, str], dict, list[str]]:
    errors: list[str] = []
    records = read_jsonl(BASE / "catalog-enriched.jsonl")
    rank_rows = read_jsonl(BASE / "rank-evidence.jsonl")
    gap_evidence = read_jsonl(BASE / "gap-candidates-evidence.jsonl")
    gaps = read_jsonl(BASE / "gap-candidates.jsonl")
    errors.extend(validate_evidence(rank_rows, "rank evidence"))
    errors.extend(validate_evidence(gap_evidence, "gap evidence"))
    rank_by_venue = {row["venue_exact"]: row for row in rank_rows}
    rank_by_id = {row["evidence_id"]: row for row in rank_rows}

    overlays = [row for record in records if (row := classify_record(record, rank_by_venue))]
    overlays.extend(gap_overlay_row(gap, rank_by_id) for gap in gaps)
    overlays.sort(key=lambda row: row["paper_id_or_gap_id"])

    catalog_bibs = []
    priority_bibs = []
    overlay_by_id = {row["paper_id_or_gap_id"]: row for row in overlays}
    for record in records:
        entry = bib_entry(record, overlay_by_id.get(record["paper_id"]))
        if entry:
            catalog_bibs.append(entry)
            if record.get("research", {}).get("priority_reading"):
                priority_bibs.append(entry)

    q1_rows = [
        row
        for row in overlays
        if row["publication_type"] == "journal-article"
        and row["venue_family"] != "conference_journal_series"
        and row["venue_rank_scheme"] == "sjr"
        and row["venue_rank_value"] == "Q1"
        and row["venue_rank_year"] == "2024"
        and row["rank_evidence_id"] in rank_by_id
    ]
    conf_rows = [row for row in overlays if row["venue_family"] == "conference_journal_series"]
    true_journals = [row for row in overlays if row["publication_type"] == "journal-article" and not row["venue_family"]]
    hist = Counter(row["publication_type"] for row in overlays)
    recount = {
        "n_overlay_rows": len(overlays),
        "n_catalog_overlay_rows": sum(row["paper_id_or_gap_id"].startswith("P") for row in overlays),
        "n_gap_overlay_rows": sum(row["paper_id_or_gap_id"].startswith("G") for row in overlays),
        "n_journal_article_true": len(true_journals),
        "n_conference_journal_series": len(conf_rows),
        "n_proceedings_article": hist["proceedings-article"],
        "n_preprint": hist["preprint"],
        "n_q1_sjr_2024": len(q1_rows),
        "n_q1_sjr_2024_catalog": sum(row["paper_id_or_gap_id"].startswith("P") for row in q1_rows),
        "n_q1_sjr_2024_gaps": sum(row["paper_id_or_gap_id"].startswith("G") for row in q1_rows),
        "n_article_bibtex": sum(entry.startswith("@article{") or "\n@article{" in entry for entry in catalog_bibs),
        "n_inproceedings_bibtex": sum(entry.startswith("@inproceedings{") or "\n@inproceedings{" in entry for entry in catalog_bibs),
        "n_bibliography_entries": len(catalog_bibs),
    }
    q1_lines = "\n".join(
        f"- `{row['paper_id_or_gap_id']}` — {html.unescape(row['venue_exact'])} (`{row['rank_evidence_id']}`)"
        for row in q1_rows
    )
    excluded = "\n".join(f"- {html.unescape(name)}" for name in sorted({row["venue_exact"] for row in conf_rows}))
    recount_md = f"""# SJR 2024 recount for the publication overlay

Generated by `publication_overlay.py`. The 1,009-record catalog is a discovery registry; this recount covers only evidence-supported overlay rows and the five explicit gap rows.

| Measure | Count |
|---|---:|
""" + "\n".join(f"| `{key}` | {value} |" for key, value in recount.items()) + f"""

`n_q1_sjr_2024` counts only true journal rows with `venue_rank_scheme=sjr`, `venue_rank_value=Q1`, `venue_rank_year=2024`, and a tracked `rank_evidence_id`. It is not the BibTeX `@article` count.

## Q1 rows

{q1_lines}

## Conference-journal-series excluded from SJR Q1

{excluded}

`Journal of Software: Evolution and Process` has no tracked rank row in this audit, so its rank remains unclaimed. `Applied Sciences` has tracked SJR 2024 Q2 evidence and is not counted as Q1.
"""

    gap_tsv_rows = []
    for gap in gaps:
        row = dict(gap)
        row["authors"] = "; ".join(gap["authors"])
        row["evidence_ids"] = "; ".join(gap["evidence_ids"])
        gap_tsv_rows.append(row)

    outputs = {
        "publication-class.tsv": tsv_text(overlays, OVERLAY_COLUMNS),
        "q1-recount.md": recount_md,
        "references-verified.bib": "% Generated from verified primary/depositor metadata, not an official publisher export.\n\n" + "\n".join(catalog_bibs),
        "references-priority50.bib": "% Priority reading references. Preprint year and venue status are explicit.\n\n" + "\n".join(priority_bibs),
        "gap-candidates.tsv": tsv_text(gap_tsv_rows, GAP_COLUMNS),
        "gap-candidates.bib": "% Five explicit bibliography gaps; not members of the 1,009-record catalog.\n\n" + "\n".join(gap_bib_entry(gap) for gap in gaps),
    }
    handoff_path = BASE / "handoff-checksums.json"
    if handoff_path.exists():
        handoff_rows = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
        refreshed = []
        for item in handoff_rows:
            rel = item["path"]
            name = Path(rel).name
            payload = outputs[name].encode("utf-8") if name in outputs and rel.startswith("01_papers/enriched/") else (ROOT / rel).read_bytes()
            refreshed.append({"path": rel, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        outputs["handoff-checksums.json"] = json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n"
    return outputs, recount, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated outputs without writing files.")
    parser.add_argument("--output-dir", type=Path, default=BASE, help="Write generated files to this directory.")
    args = parser.parse_args()
    outputs, recount, errors = build_outputs()
    target = args.output_dir.resolve()
    if args.check:
        for name, expected in outputs.items():
            path = target / name
            if not path.exists() or path.read_text(encoding="utf-8-sig") != expected:
                errors.append(f"generated output differs: {path}")
    else:
        target.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            (target / name).write_text(content, encoding="utf-8", newline="")
    print(json.dumps({"passed": not errors, "output_dir": str(target), "recount": recount, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
