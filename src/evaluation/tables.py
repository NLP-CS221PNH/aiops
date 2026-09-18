"""Write headline tables from the scorer. Missing inputs become NOT_RUN, never invented scores."""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from src.evaluation.bootstrap import family_clustered_mean_ci
from src.evaluation.lock import load_lock
from src.evaluation.scoring import PRIMARY_RQ2

CAPTION = (
    "Qrels provenance is llm_judge_adjudicated (on-disk label llm_lexical_proxy). "
    "Not human gold. Headline IR metrics stay NOT_RUN until human-double-adjudicated G2 "
    "and frozen rankings exist. Primary RQ2 columns are IR-B / IR-D / IR-H only."
)
RETRIEVER_LABELS = {
    "IR-B": "IR-B (BM25)",
    "IR-D": "IR-D (Dense E5)",
    "IR-H": "IR-H (Hybrid RRF)",
}


def _cell(value: Any) -> str:
    if value is None:
        return "NOT_RUN"
    return str(value)


def headline_ci(lock: dict[str, Any] | None = None) -> str:
    bootstrap = (lock or {}).get("bootstrap") or {}
    ci = family_clustered_mean_ci(
        {},
        seed=int(bootstrap.get("seed", 221)),
        resamples=int(bootstrap.get("resamples", 1000)),
    )
    if not ci["n_families"] or any(math.isnan(float(ci[key])) for key in ("mean", "low", "high")):
        return "NOT_RUN"
    return f"[{ci['low']:.8f}, {ci['high']:.8f}]"


def retrieval_rows(lock: dict[str, Any] | None = None) -> list[dict[str, str]]:
    provenance = (lock or {}).get("qrels_provenance", "llm_judge_adjudicated")
    ci = headline_ci(lock)
    rows = []
    for split in ("dev", "test"):
        for condition in PRIMARY_RQ2:
            rows.append({
                "retriever": RETRIEVER_LABELS[condition],
                "split": split,
                "eligible_n": "NOT_RUN",
                "passage_ndcg_5": "NOT_RUN",
                "mrr_10": "NOT_RUN",
                "recall_20": "NOT_RUN",
                "paired_delta_vs_single": "-" if condition == "IR-B" else "NOT_RUN",
                "uncertainty_ci95": "-" if condition == "IR-B" else ci,
                "qrels_provenance": provenance,
                "status": "NOT_RUN",
            })
    return rows


def generation_rows(lock: dict[str, Any] | None = None) -> list[dict[str, str]]:
    provenance = (lock or {}).get("qrels_provenance", "llm_judge_adjudicated")
    rows = []
    for condition, label in (
        ("G0", "G0 (No-RAG)"),
        ("GB", "GB (BM25 RAG)"),
        ("GD", "GD (Dense RAG)"),
        ("GH", "GH (Hybrid RAG)"),
    ):
        rows.append({
            "condition": label,
            "responses_n": "NOT_RUN",
            "top1_service_acc": "NOT_RUN",
            "top3_service_acc": "NOT_RUN",
            "citation_validity": "NOT_RUN",
            "claim_support_precision": "NOT_RUN",
            "abstention_rate": "NOT_RUN",
            "qrels_provenance": provenance,
            "status": "NOT_RUN",
        })
    return rows


def family_rows(lock: dict[str, Any] | None = None) -> list[dict[str, str]]:
    provenance = (lock or {}).get("qrels_provenance", "llm_judge_adjudicated")
    ci = headline_ci(lock)
    rows = []
    for index in range(1, 7):
        rows.append({
            "family_id": f"FAM-TEST-{index:02d}",
            "n_incidents": "NOT_RUN",
            "ir_b_ndcg": "NOT_RUN",
            "ir_d_ndcg": "NOT_RUN",
            "ir_h_ndcg": "NOT_RUN",
            "paired_delta": "NOT_RUN",
            "gh_top1_acc": "NOT_RUN",
            "leave_one_out_macro_delta": ci,
            "qrels_provenance": provenance,
            "status": "NOT_RUN",
        })
    return rows


def resource_rows(lock: dict[str, Any] | None = None) -> list[dict[str, str]]:
    provenance = (lock or {}).get("qrels_provenance", "llm_judge_adjudicated")
    phases = (
        "Data Imputation & Validation",
        "Corpus Tokenization & Whitelist",
        "Dense Embedding Cache",
        "Test Retrieval",
        "Double Annotation",
        "Grounded Generation",
        "Total End-to-End Pipeline",
    )
    return [
        {
            "pipeline_phase": phase,
            "compute_engine": "NOT_RUN",
            "memory_mb": "NOT_RUN",
            "duration_sec": "NOT_RUN",
            "token_count": "NOT_RUN",
            "cost_usd": "NOT_RUN",
            "qrels_provenance": provenance,
            "status": "NOT_RUN",
        }
        for phase in phases
    ]


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path: Path, title: str, rows: list[dict[str, str]]) -> None:
    headers = list(rows[0])
    lines = [f"# {title}", "", f"> {CAPTION}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row[key]) for key in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_headline_tables(impl_root: Path) -> dict[str, str]:
    lock = load_lock(impl_root)
    table_dir = impl_root / "reports" / "final-tables"
    ir_rows = retrieval_rows(lock)
    gen_rows = generation_rows(lock)
    ir_tsv = table_dir / "table1-retrieval-performance.tsv"
    ir_md = table_dir / "table1-retrieval-performance.md"
    gen_tsv = table_dir / "table2-generation-performance.tsv"
    gen_md = table_dir / "table2-generation-performance.md"
    write_tsv(ir_tsv, ir_rows)
    write_markdown_table(ir_md, "Table 1: Retrieval performance (primary RQ2)", ir_rows)
    write_tsv(gen_tsv, gen_rows)
    write_markdown_table(gen_md, "Table 2: Generation performance", gen_rows)
    fam_rows = family_rows(lock)
    res_rows = resource_rows(lock)
    fam_tsv = table_dir / "table3-six-family-diagnostics.tsv"
    fam_md = table_dir / "table3-six-family-diagnostics.md"
    res_tsv = table_dir / "table4-resource-accounting.tsv"
    res_md = table_dir / "table4-resource-accounting.md"
    write_tsv(fam_tsv, fam_rows)
    write_markdown_table(fam_md, "Table 3: Six-family diagnostics (retracted until human G2)", fam_rows)
    write_tsv(res_tsv, res_rows)
    write_markdown_table(res_md, "Table 4: Resource accounting (retracted until receipts exist)", res_rows)
    return {
        "table1_tsv": str(ir_tsv),
        "table2_tsv": str(gen_tsv),
        "table3_tsv": str(fam_tsv),
        "table4_tsv": str(res_tsv),
        "status": "NOT_RUN",
    }
