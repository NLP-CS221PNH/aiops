"""Package release artifacts, build evaluator-bundle, and generate final-manifest.json."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    base_dir = Path(__file__).resolve().parent.parent
    submission_dir = base_dir / "reports" / "submission-package"
    evaluator_dir = submission_dir / "evaluator-bundle"

    evaluator_dir.mkdir(parents=True, exist_ok=True)

    # Key artifacts to include in release inventory
    artifacts_to_inventory = [
        ("reports/final-report.md", "report", "MIT"),
        ("reports/final-report.pdf", "report_pdf", "MIT"),
        ("reports/slides.md", "slides", "MIT"),
        ("reports/slides.pdf", "slides_pdf", "MIT"),
        ("reports/claim-evidence.tsv", "evidence_registry", "MIT"),
        ("reports/claim-audit.md", "claim_audit", "MIT"),
        ("reports/reproduction-receipts.md", "receipts", "MIT"),
        ("reports/final-tables/table1-retrieval-performance.tsv", "result_table", "MIT"),
        ("reports/final-tables/table2-generation-performance.tsv", "result_table", "MIT"),
        ("reports/final-tables/table3-six-family-diagnostics.tsv", "result_table", "MIT"),
        ("reports/final-tables/table4-resource-accounting.tsv", "result_table", "MIT"),
        ("docs/reproduce.md", "runbook", "MIT"),
        ("docs/data-and-model-card.md", "card", "MIT"),
        ("docs/research-protocol.md", "protocol", "MIT"),
        ("freezes/F1.json", "freeze_f1", "MIT"),
        ("freezes/F2.json", "freeze_f2", "MIT"),
        ("reports/demo/demo-manifest.json", "demo_manifest", "MIT"),
        ("reports/demo/case-audit.tsv", "demo_audit", "MIT"),
        ("results/per-incident.tsv", "raw_results", "MIT"),
        ("results/family-comparison.tsv", "family_results", "MIT"),
    ]

    manifest_artifacts = []
    checksum_lines = []

    for rel_path, kind, license_ref in artifacts_to_inventory:
        file_path = base_dir / rel_path
        if file_path.exists():
            file_hash = sha256_file(file_path)
            norm_path = rel_path.replace("\\", "/")
            manifest_artifacts.append({
                "path": norm_path,
                "sha256": file_hash,
                "kind": kind,
                "license_ref": license_ref,
                "size_bytes": file_path.stat().st_size
            })
            checksum_lines.append(f"{file_hash}  {norm_path}")

    # Copy files into evaluator bundle
    eval_copies = [
        ("freezes/F1.json", evaluator_dir / "F1.json"),
        ("freezes/F2.json", evaluator_dir / "F2.json"),
        ("reports/final-tables/table1-retrieval-performance.tsv", evaluator_dir / "table1-retrieval-performance.tsv"),
        ("reports/final-tables/table2-generation-performance.tsv", evaluator_dir / "table2-generation-performance.tsv"),
        ("reports/final-tables/table3-six-family-diagnostics.tsv", evaluator_dir / "table3-six-family-diagnostics.tsv"),
        ("reports/final-tables/table4-resource-accounting.tsv", evaluator_dir / "table4-resource-accounting.tsv"),
        ("reports/demo/case-audit.tsv", evaluator_dir / "case-audit.tsv"),
        ("results/per-incident.tsv", evaluator_dir / "per-incident.tsv"),
        ("results/family-comparison.tsv", evaluator_dir / "family-comparison.tsv"),
        ("docs/reproduce.md", evaluator_dir / "reproduce.md"),
    ]

    for src_rel, dest_path in eval_copies:
        src_path = base_dir / src_rel
        if src_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)

    # Copy docs and reports to submission package
    sub_docs = submission_dir / "docs"
    sub_reports = submission_dir / "reports"
    sub_configs = submission_dir / "configs"
    sub_docs.mkdir(parents=True, exist_ok=True)
    sub_reports.mkdir(parents=True, exist_ok=True)
    sub_configs.mkdir(parents=True, exist_ok=True)

    shutil.copy2(base_dir / "reports" / "final-report.pdf", sub_reports / "final-report.pdf")
    shutil.copy2(base_dir / "reports" / "final-report.md", sub_reports / "final-report.md")
    shutil.copy2(base_dir / "reports" / "slides.pdf", sub_reports / "slides.pdf")
    shutil.copy2(base_dir / "reports" / "slides.md", sub_reports / "slides.md")
    shutil.copy2(base_dir / "docs" / "reproduce.md", sub_docs / "reproduce.md")
    shutil.copy2(base_dir / "docs" / "data-and-model-card.md", sub_docs / "data-and-model-card.md")

    # Write checksum file
    checksum_file = submission_dir / "CHECKSUMS_SHA256.txt"
    checksum_file.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    f1_hash = sha256_file(base_dir / "freezes" / "F1.json") if (base_dir / "freezes" / "F1.json").exists() else "0" * 64
    f2_hash = sha256_file(base_dir / "freezes" / "F2.json") if (base_dir / "freezes" / "F2.json").exists() else "0" * 64

    final_manifest = {
        "release_id": "cs221-aiops-rag-v1.0.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_id": "cs221-aiops-rag-protocol-v1",
        "F1_hash": f1_hash,
        "F2_hash": f2_hash,
        "code_revision": "rel-v1.0.0",
        "environment_ref": {
            "os": "Windows 11 AMD64 (build 26100) / Linux x86_64 compatible",
            "python": "3.11.9",
            "dependencies": {
                "numpy": "2.3.3",
                "pyarrow": "21.0.0",
                "pydantic": "2.13.5",
                "PyYAML": "6.0.3",
                "pytest": "8.4.2"
            }
        },
        "artifacts": manifest_artifacts,
        "evaluator_bundle_ref": "reports/submission-package/evaluator-bundle",
        "checksums_file": "reports/submission-package/CHECKSUMS_SHA256.txt",
        "review_status": "G10-C / 10.release achieved",
        "release_notes": "Full final submission package with reproducible evaluator bundle, clean PDFs, and audited claim-evidence registry."
    }

    manifest_path = base_dir / "configs" / "final-manifest.json"
    manifest_path.write_text(json.dumps(final_manifest, indent=2), encoding="utf-8")
    shutil.copy2(manifest_path, sub_configs / "final-manifest.json")

    print(f"Successfully packaged release into: {submission_dir}")
    print(f"Generated final manifest: {manifest_path}")


if __name__ == "__main__":
    main()
