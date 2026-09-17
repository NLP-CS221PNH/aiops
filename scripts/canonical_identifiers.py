"""Normalize and validate canonical paper DOI/arXiv identity mappings."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "01_papers" / "enriched" / "catalog-enriched.jsonl"
ALIAS_MAP = ROOT / "01_papers" / "enriched" / "alias-version-map.tsv"
UNRESOLVED = ROOT / "01_papers" / "enriched" / "unresolved.tsv"
CANONICAL_INPUTS = (
    "01_papers/enriched/catalog-enriched.jsonl",
    "01_papers/enriched/rescue-metadata.jsonl",
    "01_papers/enriched/priority-source-index.jsonl",
    "01_papers/enriched/selective-pdf-source-index.jsonl",
    "01_papers/enriched/priority-publication-resolution.jsonl",
    "01_papers/enriched/reading-extractions.json",
    "01_papers/enriched/divlog-publication-metadata.json",
    "01_papers/enriched/alias-version-map.tsv",
)
DOI_PREFIX = re.compile(r"(?i)^(?:https?://(?:dx\.)?doi\.org/|doi:)?")
ARXIV_PREFIX = re.compile(r"(?i)^(?:https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/|arxiv:)")


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = DOI_PREFIX.sub("", str(value).strip()).strip().rstrip(".").lower()
    text = text.replace("doi:", "")
    return text or None


def normalize_arxiv(value: str | None) -> str | None:
    if not value:
        return None
    text = ARXIV_PREFIX.sub("", str(value).strip())
    text = re.sub(r"\.pdf$", "", text, flags=re.I)
    text = re.sub(r"v\d+$", "", text)
    text = text.strip().rstrip("/")
    return text.lower() or None


def collect_ids(record: dict) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    research = record.get("research") or {}
    metadata = research.get("metadata") or {}
    blobs = [record, research, metadata, research.get("publication_metadata") or {}]
    related = []
    for candidate in (
        record.get("related_identifiers"),
        research.get("related_identifiers"),
        metadata.get("related_identifiers"),
        (research.get("publication_metadata") or {}).get("related_identifiers"),
    ):
        if isinstance(candidate, list):
            related.extend(candidate)
    blobs.extend(item for item in related if isinstance(item, dict))
    for blob in blobs:
        if not isinstance(blob, dict):
            continue
        related_id = blob.get("relatedIdentifier") or blob.get("related_identifier")
        related_type = str(blob.get("relatedIdentifierType") or blob.get("related_identifier_type") or "").lower()
        if related_type == "doi":
            doi = normalize_doi(related_id)
            if doi:
                found.add(("doi", doi))
        elif related_type in {"arxiv", "eprint"}:
            arxiv = normalize_arxiv(related_id)
            if arxiv:
                found.add(("arxiv", arxiv))
        doi = normalize_doi(blob.get("doi") or blob.get("publication_doi") or (related_id if related_type == "doi" else None))
        if doi:
            found.add(("doi", doi))
        arxiv = normalize_arxiv(
            blob.get("arxiv_id") or blob.get("discovered_arxiv_id") or blob.get("eprint") or blob.get("arxiv_doi")
            or (related_id if "arxiv" in related_type else None)
        )
        if arxiv:
            found.add(("arxiv", arxiv))
        arxiv_doi = blob.get("arxiv_doi")
        if arxiv_doi:
            stripped = re.sub(r"(?i)^10\.48550/arxiv\.", "", str(arxiv_doi))
            normalized = normalize_arxiv(stripped)
            if normalized:
                found.add(("arxiv", normalized))
    return found


def load_alias_pairs(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            paper_id = (row.get("paper_id") or "").strip()
            if paper_id:
                rows.append(row)
    return rows


def _iter_records(path: Path):
    if path.suffix == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
        return
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield item
        elif isinstance(payload, dict):
            if payload.get("paper_id"):
                yield payload
            for value in payload.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and item.get("paper_id"):
                            yield item
                elif isinstance(value, dict) and value.get("paper_id"):
                    yield value
        return
    if path.suffix == ".tsv":
        for row in load_alias_pairs(path):
            yield {
                "paper_id": row.get("paper_id"),
                "doi": row.get("publication_doi"),
                "arxiv_id": row.get("arxiv_id"),
            }


def validate_catalog(catalog_path: Path = CATALOG) -> list[dict]:
    errors = []
    by_key = defaultdict(set)
    scanned = []
    inputs = [catalog_path] if catalog_path != CATALOG else [ROOT / rel for rel in CANONICAL_INPUTS]
    for path in inputs:
        if not path.is_file():
            errors.append({"code": "canonical_input_missing", "path": str(path)})
            continue
        scanned.append(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
        try:
            records = list(_iter_records(path))
        except json.JSONDecodeError as exc:
            errors.append({"code": "canonical_input_parse", "path": str(path), "error": str(exc)})
            continue
        ids = [row.get("paper_id") for row in records if row.get("paper_id")]
        if path.suffix == ".jsonl" and ids and len(ids) != len(set(ids)):
            dup = sorted({item for item in ids if ids.count(item) > 1})
            errors.append({"code": "duplicate_paper_id", "path": str(path), "ids": dup})
        for record in records:
            paper_id = record.get("paper_id")
            if not paper_id:
                continue
            for kind, value in collect_ids(record):
                by_key[(kind, value)].add(paper_id)
    collisions = []
    for key, papers in sorted(by_key.items()):
        if len(papers) > 1:
            collisions.append({"identifier": f"{key[0]}:{key[1]}", "paper_ids": sorted(papers)})
    if collisions:
        errors.append({"code": "identifier_collision", "collisions": collisions})
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args()
    errors = validate_catalog(args.catalog)
    print(json.dumps({"passed": not errors, "errors": errors, "canonical_inputs": list(CANONICAL_INPUTS)}))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
