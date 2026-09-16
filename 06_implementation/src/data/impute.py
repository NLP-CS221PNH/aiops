"""Mean imputation module for telemetry metric summaries.

Imputes missing/null values (e.g. change_score, first_quarter_mean, last_quarter_mean)
to the computed mean of the corresponding metric_name across the dataset,
as authorized by user directive (Plan 02).
"""
import json
from pathlib import Path
from typing import Dict, Any, List


def calculate_metric_means(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculates means for numerical fields grouped by metric_name."""
    sums: Dict[str, Dict[str, float]] = {}
    counts: Dict[str, Dict[str, int]] = {}
    
    numerical_fields = ["change_score", "first_quarter_mean", "last_quarter_mean", "mean", "minimum", "maximum"]
    
    for r in records:
        metric = r.get("metric_name", "unknown")
        if metric not in sums:
            sums[metric] = {f: 0.0 for f in numerical_fields}
            counts[metric] = {f: 0 for f in numerical_fields}
            
        for f in numerical_fields:
            val = r.get(f)
            if val is not None and isinstance(val, (int, float)):
                sums[metric][f] += float(val)
                counts[metric][f] += 1
                
    means: Dict[str, Dict[str, float]] = {}
    for metric in sums:
        means[metric] = {}
        for f in numerical_fields:
            c = counts[metric][f]
            means[metric][f] = (sums[metric][f] / c) if c > 0 else 0.0
            
    return means


def impute_records(records: List[Dict[str, Any]], means: Dict[str, Dict[str, float]]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Imputes null values in records using precalculated metric means."""
    imputed_records = []
    audit_log: Dict[str, int] = {
        "total_records": len(records),
        "imputed_change_score": 0,
        "imputed_first_quarter_mean": 0,
        "imputed_last_quarter_mean": 0,
        "imputed_mean": 0,
    }
    
    for r in records:
        rec = dict(r)
        metric = rec.get("metric_name", "unknown")
        metric_means = means.get(metric, {})
        
        for field in ["change_score", "first_quarter_mean", "last_quarter_mean", "mean"]:
            if rec.get(field) is None:
                default_val = metric_means.get(field, 0.0)
                rec[field] = default_val
                audit_key = f"imputed_{field}"
                audit_log[audit_key] = audit_log.get(audit_key, 0) + 1
                
        rec["imputation_policy"] = "mean_imputation_v1"
        imputed_records.append(rec)
        
    return imputed_records, audit_log


def apply_mean_imputation(input_path: Path, output_path: Path, audit_path: Path) -> Dict[str, Any]:
    """Reads JSONL, applies mean imputation, writes output and audit."""
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    means = calculate_metric_means(records)
    imputed_records, audit = impute_records(records, means)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in imputed_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
        
    return audit


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    inp = base / "data" / "inference" / "metric-summaries.jsonl"
    out = base / "data" / "imputed" / "metric-summaries-imputed.jsonl"
    audit_file = base / "reports" / "imputation-audit.json"
    
    print(f"Applying mean imputation from {inp} -> {out}...")
    res = apply_mean_imputation(inp, out, audit_file)
    print("Imputation completed successfully:", res)
