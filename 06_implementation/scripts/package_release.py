"""Release packaging into clean staging with a real git revision."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT = BASE_DIR.parent
sys.path.insert(0, str(ROOT / "scripts"))
from publication_policy import git_dirty, git_head, sha256_file  # noqa: E402

PLACEHOLDER_MARKERS = ("handoff", "ready", "placeholder", "dummy")
SUPPORTED_PLATFORMS = ("win_amd64",)


def sha256_text(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(code)


def load_lock_ref() -> dict:
    lock = BASE_DIR / "configs" / "requirements-lock.txt"
    require(lock.is_file(), "missing_dependency_lock")
    return {
        "os": "Windows AMD64",
        "python": "3.11.9",
        "supported_platforms": list(SUPPORTED_PLATFORMS),
        "lock_file": "configs/requirements-lock.txt",
        "lock_sha256": sha256_file(lock),
        "install": "python -m pip install --require-hashes -r configs/requirements-lock.txt",
        "linux_lock": None,
        "note": "Windows hash lock only; this release does not claim Linux support.",
    }


def artifact_list() -> list[tuple[str, str, str]]:
    return [
        ("reports/final-report.md", "report", "MIT"),
        ("reports/slides.md", "slides", "MIT"),
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


def reject_placeholder(path: Path) -> None:
    if path.suffix.lower() in {".json", ".jsonl", ".tsv", ".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if path.name == "final-manifest.json" and '"handoff"' in text and "ready" in text and "artifacts" not in text:
            raise SystemExit("placeholder_manifest")
        if text.strip() in {"dummy_judgments", '{"status":"exported"}', '{"handoff": "ready"}', '{"handoff":"ready"}'}:
            raise SystemExit(f"placeholder:{path}")


def _safe_replace_output(final_dir: Path) -> None:
    if not final_dir.exists():
        return
    marker = final_dir / "CHECKSUMS_SHA256.txt"
    if final_dir.name != "submission-package" or not marker.is_file():
        raise SystemExit("refuse_overwrite_output")
    shutil.rmtree(final_dir)


def package_release(output_dir: Path | None = None) -> dict:
    require(not git_dirty(ROOT), "dirty_worktree")
    revision = git_head(ROOT)
    tag = subprocess.check_output(["git", "tag", "--points-at", "HEAD"], cwd=ROOT, text=True).strip().splitlines()
    artifacts = []
    checksum_lines = []
    for rel_path, kind, license_ref in artifact_list():
        file_path = BASE_DIR / rel_path
        require(file_path.is_file(), f"missing:{rel_path}")
        reject_placeholder(file_path)
        digest = sha256_file(file_path)
        artifacts.append({
            "path": rel_path.replace("\\", "/"),
            "sha256": digest,
            "kind": kind,
            "license_ref": license_ref,
            "size_bytes": file_path.stat().st_size,
            "provenance": "implementation-working-tree",
        })
        checksum_lines.append(f"{digest}  {rel_path.replace(chr(92), '/')}")
    f1 = BASE_DIR / "freezes" / "F1.json"
    f2 = BASE_DIR / "freezes" / "F2.json"
    env = load_lock_ref()
    manifest = {
        "release_id": "cs221-aiops-rag",
        "protocol_id": "cs221-aiops-rag-protocol-v1",
        "F1_hash": sha256_file(f1),
        "F2_hash": sha256_file(f2),
        "code_revision": revision,
        "git_tags_at_head": tag,
        "environment_ref": env,
        "artifacts": artifacts,
        "evaluator_bundle_ref": "reports/submission-package/evaluator-bundle",
        "checksums_file": "reports/submission-package/CHECKSUMS_SHA256.txt",
        "policy_version": "cs221-public-artifact-policy-v1",
        "review_status": "packaged-from-clean-head",
    }
    staging_parent = BASE_DIR / "reports"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".release-staging-", dir=staging_parent) as tmp:
        staging = Path(tmp)
        dest_root = staging / "submission-package"
        evaluator = dest_root / "evaluator-bundle"
        evaluator.mkdir(parents=True)
        (dest_root / "docs").mkdir()
        (dest_root / "reports").mkdir()
        (dest_root / "configs").mkdir()
        for item in artifacts:
            src = BASE_DIR / item["path"]
            copied = dest_root / item["path"]
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, copied)
            require(sha256_file(copied) == item["sha256"], f"dest_hash_mismatch:{item['path']}")
        copies = [
            "freezes/F1.json",
            "freezes/F2.json",
            "reports/final-tables/table1-retrieval-performance.tsv",
            "reports/final-tables/table2-generation-performance.tsv",
            "reports/final-tables/table3-six-family-diagnostics.tsv",
            "reports/final-tables/table4-resource-accounting.tsv",
            "reports/demo/case-audit.tsv",
            "results/per-incident.tsv",
            "results/family-comparison.tsv",
            "docs/reproduce.md",
        ]
        for rel in copies:
            shutil.copy2(BASE_DIR / rel, evaluator / Path(rel).name)
            require(sha256_file(evaluator / Path(rel).name) == sha256_file(BASE_DIR / rel), f"bundle_mismatch:{rel}")
        (dest_root / "CHECKSUMS_SHA256.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        (dest_root / "configs" / "final-manifest.json").write_bytes(manifest_bytes)
        (staging / "final-manifest.json").write_bytes(manifest_bytes)
        final_dir = output_dir or (BASE_DIR / "reports" / "submission-package")
        _safe_replace_output(final_dir)
        shutil.copytree(dest_root, final_dir)
    return {"submission": str(final_dir), "code_revision": revision, "artifacts": len(artifacts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = package_release(args.output)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
