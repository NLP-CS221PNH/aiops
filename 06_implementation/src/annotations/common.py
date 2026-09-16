"""Common constants, exceptions, and serialization helpers for annotations."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

ROOT = Path(__file__).resolve().parents[3]
IMPL = ROOT / "06_implementation"
ANNOTATIONS_DIR = IMPL / "annotations"
DATA_DIR = IMPL / "data"

VALID_GRADES: Set[int] = {0, 1, 2}

EVIDENCE_ROLES: Set[str] = {
    "symptom_interpretation",
    "service_dependency",
    "diagnostic_check",
    "elimination_check",
    "root_cause_support",
    "counter_evidence",
    "context_only",
}

APPLICABILITY_STATES: Set[str] = {
    "compatible",
    "incompatible",
    "uncertain_pending_review",
}

ANSWERABILITY_STATES: Set[str] = {
    "answerable",
    "partially_answerable",
    "unanswerable",
    "uncertain_pending_review",
}


class AnnotationError(Exception):
    """Base exception for annotation contract failures."""


class BlindingViolationError(AnnotationError):
    """Raised when blinding is compromised (e.g. rank, score, or retriever present)."""


class OverwriteProtectionError(AnnotationError):
    """Raised when an operation would overwrite non-empty or partial human work."""


class DoubleReviewViolationError(AnnotationError):
    """Raised when double-annotation rules are violated."""


class SpanOffsetError(AnnotationError):
    """Raised when Unicode codepoint span offsets are invalid or mismatch document text."""


class CoverageError(AnnotationError):
    """Raised when required candidate coverage is unmet."""


class AdjudicationMissingError(AnnotationError):
    """Raised when A/B disagreement exists without adjudication."""


def sha256_file(path: Path | str) -> str:
    """Computes SHA-256 hex digest of a file in streaming 1MB blocks."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(val: Any) -> bytes:
    """Serializes value to canonical compact sorted UTF-8 JSON bytes."""
    return json.dumps(
        val,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash(val: Any) -> str:
    """Computes SHA-256 of canonical JSON bytes."""
    return hashlib.sha256(canonical_bytes(val)).hexdigest()


def read_json(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path | str, data: Any, indent: int = 2) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write("\n")


def read_tsv(path: Path | str) -> List[Dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def write_tsv(
    path: Path | str, rows: Iterable[Dict[str, Any]], fieldnames: List[str]
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def check_overwrite_safe(path: Path | str, allow_empty: bool = True) -> None:
    """Safeguard: Refuses to overwrite files that contain existing non-empty human work."""
    p = Path(path)
    if not p.exists():
        return
    # If file exists, check if it has content
    if p.stat().st_size == 0 and allow_empty:
        return
    # Check if TSV or JSON has completed judgments or entries
    try:
        if p.suffix.lower() == ".tsv":
            rows = read_tsv(p)
            for r in rows:
                grade = r.get("grade", "").strip()
                rev = r.get("reviewer_id", "").strip()
                if grade != "" or rev != "":
                    raise OverwriteProtectionError(
                        f"Target file '{p}' contains active human judgments (e.g. grade={grade}, reviewer={rev}). "
                        "Overwriting is blocked to protect human annotation work."
                    )
        elif p.suffix.lower() == ".json":
            data = read_json(p)
            if isinstance(data, dict) and data.get("human_judgments_completed", 0) > 0:
                raise OverwriteProtectionError(
                    f"Target file '{p}' records completed human judgments. Overwriting blocked."
                )
    except OverwriteProtectionError:
        raise
    except Exception:
        # If unknown format or error reading, block overwrite if non-empty
        if p.stat().st_size > 0:
            raise OverwriteProtectionError(
                f"Target file '{p}' already exists and is non-empty ({p.stat().st_size} bytes). "
                "Overwriting blocked by safeguard."
            )


def verify_span_offsets(
    doc_text: str,
    span_start: Optional[int],
    span_end: Optional[int],
    expected_slice: Optional[str] = None,
) -> bool:
    """Verifies that span_start/span_end are valid Unicode codepoint offsets in doc_text."""
    if span_start is None and span_end is None:
        return True
    if span_start is None or span_end is None:
        raise SpanOffsetError("Both span_start and span_end must be provided or both None.")
    if span_start < 0 or span_end < 0:
        raise SpanOffsetError(f"Span offsets cannot be negative: [{span_start}, {span_end})")
    if span_start > span_end:
        raise SpanOffsetError(
            f"span_start ({span_start}) cannot exceed span_end ({span_end})"
        )
    text_len = len(doc_text)
    if span_end > text_len:
        raise SpanOffsetError(
            f"span_end ({span_end}) exceeds document text length ({text_len})"
        )
    if expected_slice is not None:
        actual_slice = doc_text[span_start:span_end]
        if actual_slice != expected_slice:
            raise SpanOffsetError(
                f"Span slice mismatch: expected '{expected_slice[:30]}...', got '{actual_slice[:30]}...'"
            )
    return True
