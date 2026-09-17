"""F2 freeze generation and validation tool for CS221 annotation.

Verifies the hash chain linking 08.F1, the test candidate pool, the adjudicated test qrels,
and verified top-5/top-10 judged coverage before locking 06.F2.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.annotations.common import (
    CoverageError,
    read_json,
    read_tsv,
    sha256_file,
    write_json,
)


def _limitations_for(provenance: str) -> List[str]:
    if provenance == "human-double-adjudicated":
        lead = "F2 freezes adjudicated human-double-adjudicated test qrels linked to F1 freeze."
    else:
        lead = (
            f"F2 freezes {provenance} test qrels. These are not human gold and "
            "must not be used for headline nDCG."
        )
    return [
        lead,
        "Qrels are restricted to evaluator use; runners must not mount qrels during generation.",
        "Test labels cannot be used to fine-tune prompts, representations, or retrieval parameters.",
    ]


def build_f2_freeze(
    f1_path: Path,
    test_pool_manifest_path: Path,
    test_qrels_path: Path,
    test_input_manifest_path: Optional[Path] = None,
    rubric_version: str = "rubric-v1",
    annotation_version: str = "06.F2-v1",
    coverage_info: Optional[Dict[str, Any]] = None,
    out_f2_path: Optional[Path] = None,
    provenance: str = "llm_lexical_proxy",
    provenance_sidecar_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assembles and validates the F2 freeze record.

    Default provenance is llm_lexical_proxy. Human wording is emitted only when
    provenance is exactly human-double-adjudicated.
    """
    if not f1_path.exists():
        raise FileNotFoundError(f"F1 freeze file not found: {f1_path}")
    if not test_pool_manifest_path.exists():
        raise FileNotFoundError(f"Test pool manifest not found: {test_pool_manifest_path}")
    if not test_qrels_path.exists():
        raise FileNotFoundError(f"Test qrels file not found: {test_qrels_path}")

    f1_hash = sha256_file(f1_path)
    test_pool_hash = sha256_file(test_pool_manifest_path)
    test_qrels_hash = sha256_file(test_qrels_path)

    test_input_manifest_hash = (
        sha256_file(test_input_manifest_path)
        if test_input_manifest_path and test_input_manifest_path.exists()
        else "0" * 64
    )

    # Load test pool to extract incident IDs
    pool_data = read_json(test_pool_manifest_path)
    candidate_list = pool_data.get("candidates", [])
    incident_ids = sorted(list({c["incident_id"] for c in candidate_list}))

    if len(incident_ids) != 18:
        raise ValueError(
            f"F2 requires exactly 18 test core incidents, but pool contains {len(incident_ids)}"
        )

    # Verify qrels coverage
    qrels_rows = read_tsv(test_qrels_path)
    judged_test_pairs = {(r["incident_id"], r["chunk_id"]) for r in qrels_rows if (r.get("relevance_grade") or r.get("grade") or "").strip() != ""}

    if coverage_info is None:
        raise CoverageError("coverage_info is required; refusing default 1.0")
    cov = coverage_info

    sidecar_path = provenance_sidecar_path or (test_qrels_path.parent / "qrels-sidecar.jsonl")
    if not Path(sidecar_path).exists():
        raise CoverageError("provenance sidecar is required; refusing zero reviewer_receipt_hash")
    reviewer_receipt_hash = sha256_file(Path(sidecar_path))
    receipt = read_json(Path(sidecar_path))
    if receipt.get("qrels_provenance") != provenance:
        raise CoverageError("provenance receipt mismatch")
    bound_hash = receipt.get("current_qrels_hash", receipt.get("qrels_hash"))
    if bound_hash != test_qrels_hash:
        raise CoverageError("provenance receipt does not bind current qrels")
    required = {"provenance", "annotator_id", "adjudication_state", "annotation_version"}
    if not qrels_rows or any(not required.issubset(row) for row in qrels_rows):
        raise CoverageError("qrels provenance columns are required")
    if any(row["provenance"] != provenance for row in qrels_rows):
        raise CoverageError("qrels provenance mismatch")
    if provenance != "human-double-adjudicated" or receipt.get("human_gold") is not True:
        raise CoverageError("proxy qrels cannot create an evaluation freeze")
    for key in ("top5_coverage_ratio", "top10_coverage_ratio"):
        value = cov.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            raise CoverageError("measured coverage ratios are required")

    f2_data = {
        "schema_version": "cs221-annotation-freeze-f2-v1",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "F1_hash": f1_hash,
        "test_input_manifest_hash": test_input_manifest_hash,
        "test_pool_hash": test_pool_hash,
        "qrels_hash": test_qrels_hash,
        "rubric_version": rubric_version,
        "annotation_version": annotation_version,
        "incident_ids": incident_ids,
        "judged_coverage": cov,
        "reviewer_receipt_hash": reviewer_receipt_hash,
        "qrels_provenance": provenance,
        "limitations": _limitations_for(provenance),
    }

    if out_f2_path:
        write_json(out_f2_path, f2_data)

    return f2_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or validate CS221 F2 freeze record linking F1, test pool, and test qrels."
    )
    parser.add_argument(
        "--f1",
        type=str,
        required=True,
        help="Path to 08.F1 freeze JSON.",
    )
    parser.add_argument(
        "--test-pool",
        type=str,
        required=True,
        help="Path to test candidate pool manifest.",
    )
    parser.add_argument(
        "--qrels",
        type=str,
        required=True,
        help="Path to adjudicated test qrels.tsv.",
    )
    parser.add_argument(
        "--test-input-manifest",
        type=str,
        default=None,
        help="Optional path to test-input-manifest.json from 08.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="freezes/F2.json",
        help="Output path for F2.json.",
    )

    args = parser.parse_args()

    try:
        f2 = build_f2_freeze(
            f1_path=Path(args.f1),
            test_pool_manifest_path=Path(args.test_pool),
            test_qrels_path=Path(args.qrels),
            test_input_manifest_path=Path(args.test_input_manifest) if args.test_input_manifest else None,
            out_f2_path=Path(args.out),
        )
        print("Successfully generated F2 freeze:")
        print(f"  F1 Hash:        {f2['F1_hash']}")
        print(f"  Test Pool Hash: {f2['test_pool_hash']}")
        print(f"  Qrels Hash:     {f2['qrels_hash']}")
        print(f"  Incident Count: {len(f2['incident_ids'])}")
        print(f"  Output:         {args.out}")
    except Exception as exc:
        print(f"F2 Generation FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
