"""Publication ledger rules, glob matching and git inventory helpers."""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "04_audit" / "public-artifact-ledger.tsv"
POLICY_VERSION = "cs221-public-artifact-policy-v1"
SIZE_LIMIT_MIB = 5
LEDGER_FIELDS = [
    "path_glob",
    "artifact_class",
    "authority",
    "owner_source",
    "exact_revision",
    "license_expression",
    "evidence_snapshot",
    "grant_scope",
    "grant_exclusions",
    "redistribution_status",
    "sensitive_data_status",
    "disposition",
    "approval_scope",
    "approver",
    "decision_id",
    "expiry",
    "size_exception_mib",
    "notes",
]
RIGHTS_PUBLIC = {"approved"}
SENSITIVE_PUBLIC = {"none", "public_metadata_approved", "redacted_approved"}
DISPOSITION_PUBLIC = {"keep_public"}
FORBIDDEN_PUBLIC_GLOBS = (
    "01_papers/enriched/cache/**",
    "01_papers/enriched/rescue-cache/**",
    "01_papers/enriched/primary-text/**",
    "02_datasets/acquired/raw/**",
    "02_datasets/processed/labels/**",
    "06_implementation/data/private/**",
    "06_implementation/data/candidate-inference/**",
    "06_implementation/data/candidate-pre-review/**",
    "**/source-snapshots/**",
)
FORBIDDEN_PUBLIC_EXCEPTIONS = (
    "**/source-snapshots/**/LICENSE",
)
LOCAL_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]+(?:Users|Windows|Temp|Documents)[\\/]+|/+Users/[A-Za-z0-9._-]+|/home/[a-z0-9._-]+|/workspaces/)"
)
SECRET_RE = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:ghp|github_pat)_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})"
)
PII_SENTINEL_RE = re.compile(r"(?i)\b(?:ssn|passport_number|credit[_\s]?card_number)\b")
SKIP_SCAN_PREFIXES = (
    "03_collection_plan/knowledge-corpus",
    "06_implementation/data/",
    "06_implementation/vendor/",
    "02_datasets/processed/",
    "02_datasets/acquired/meta/",
    "05_research/retrieval-preview/",
    "06_implementation/queries/",
    "06_implementation/tests/",
    "01_papers/enriched/catalog-enriched",
    "01_papers/enriched/priority-source-index",
    "01_papers/enriched/rescue-metadata",
    "01_papers/enriched/selective-pdf-source-index",
    "01_papers/enriched/official-acl-bibtex/",
    "06_implementation/freezes/G0/",
)
SKIP_SCAN_EXACT = (
    "scripts/publication_policy.py",
    "plans/reports/260913-independent-plans-contracts.md",
)

OWNED = {
    "authority": "canonical",
    "owner_source": "project-owned",
    "exact_revision": "HEAD",
    "license_expression": "MIT",
    "evidence_snapshot": "LICENSE",
    "grant_scope": "software-and-hand-authored-docs",
    "grant_exclusions": "third-party-data-full-text-pdf-raw-vendor-weights",
    "redistribution_status": "approved",
    "sensitive_data_status": "none",
    "disposition": "keep_public",
    "approval_scope": "public-git-tip",
    "approver": "repository-policy",
    "decision_id": "PUB-2026-09-16-OWNED-WORK",
    "expiry": "",
    "size_exception_mib": "",
    "notes": "Root MIT covers project Software only.",
}
DENY = {
    "authority": "canonical",
    "owner_source": "third-party",
    "exact_revision": "see-acquisition-manifest",
    "license_expression": "NOASSERTION",
    "evidence_snapshot": "01_papers/enriched/README.md",
    "grant_scope": "none",
    "grant_exclusions": "all-bytes",
    "redistribution_status": "internal_only",
    "sensitive_data_status": "unknown",
    "disposition": "remove_public",
    "approval_scope": "local-workspace-only",
    "approver": "repository-policy",
    "decision_id": "PUB-2026-09-16-DEFAULT-DENY",
    "expiry": "",
    "size_exception_mib": "",
    "notes": "Fail-closed: public URL or root MIT does not grant redistribution.",
}


def rule(path_glob: str, artifact_class: str, base: dict | None = None, **overrides) -> dict:
    row = {"path_glob": path_glob, "artifact_class": artifact_class}
    row.update(OWNED if base is None else base)
    row.update(overrides)
    return row


RULES = [
    rule("01_papers/enriched/cache/**", "acquisition-cache", DENY, authority="generated",
         disposition="remove_public", notes="Regenerable HTTP cache."),
    rule("01_papers/enriched/rescue-cache/**", "acquisition-cache", DENY, authority="generated"),
    rule("01_papers/enriched/primary-text/**", "paper-full-text", DENY,
         sensitive_data_status="sensitive_internal",
         notes="Per-item paper copyright; no uniform redistribution grant."),
    rule("01_papers/enriched/**/*.pdf", "source-pdf", DENY,
         sensitive_data_status="sensitive_internal"),
    rule("02_datasets/acquired/raw/**", "raw-rca-eval", DENY,
         owner_source="RCAEval", exact_revision="see-02_datasets/acquired/labels/acquisition-manifest.jsonl",
         license_expression="MIT-author-data-with-embedded-baseline-exclusions",
         evidence_snapshot="02_datasets/licenses_and_lineage.md",
         disposition="archive_private", sensitive_data_status="sensitive_internal",
         notes="Pinned upstream re-acquisition only; owner grant required before public bytes."),
    rule("02_datasets/processed/labels/**", "gold-labels", DENY,
         sensitive_data_status="sensitive_internal",
         notes="Evaluator-only until release-stage approval."),
    rule("06_implementation/data/private/**", "private-sidecars", DENY,
         sensitive_data_status="sensitive_internal"),
    rule("06_implementation/data/candidate-inference/**", "inference-working-copy", DENY,
         authority="generated", disposition="remove_public"),
    rule("06_implementation/data/candidate-pre-review/**", "inference-working-copy", DENY,
         authority="generated", disposition="remove_public"),
    rule("**/source-snapshots/**/LICENSE", "license-snapshot",
         owner_source="upstream-with-attribution",
         license_expression="Apache-2.0 OR CC-BY-4.0",
         evidence_snapshot="03_collection_plan/knowledge-corpus/source-manifest.jsonl",
         grant_scope="license-text-only",
         grant_exclusions="snapshot-source-bytes",
         decision_id="PUB-2026-09-16-LICENSE-EVIDENCE",
         notes="License text required for offline PR reconstruction checks; raw snapshot bytes stay private."),
    rule("**/source-snapshots/**", "source-snapshot", DENY,
         disposition="archive_private",
         notes="Re-acquire from recorded git revision; keep manifests and processed chunks."),
    rule("06_implementation/reports/**/*.pdf", "generated-pdf", DENY,
         authority="generated", disposition="generate",
         notes="Build in release staging; do not track binaries."),
    rule("06_implementation/reports/data-test-results.json", "generated-local-receipt", DENY,
         authority="generated", disposition="generate",
         notes="Machine-local pytest receipt; contains host paths."),
    rule("06_implementation/reports/environment-check.json", "generated-local-receipt", DENY,
         authority="generated", disposition="generate",
         notes="Machine-local environment receipt; contains host paths."),
    rule("06_implementation/reports/submission-package/**", "release-copy", DENY,
         authority="generated", disposition="generate"),
    rule("06_implementation/configs/final-manifest.json", "generated-manifest", DENY,
         authority="generated", disposition="generate",
         notes="Written only into release staging by package_release."),
    rule("START-HERE.html", "generated-index", DENY, authority="generated", disposition="generate"),
    rule("06_implementation/data/inference/**", "inference-bundle",
         owner_source="project-derived-from-RCAEval",
         license_expression="MIT", evidence_snapshot="06_implementation/data/inference/input-manifest.json",
         grant_scope="de-identified-processed-inference-bundle",
         sensitive_data_status="redacted_approved",
         decision_id="SIZE-2026-09-16-INFERENCE-BUNDLE",
         size_exception_mib="8",
         expiry="2027-09-16",
         notes="Canonical inference bundle; candidate copies are not authority."),
    rule("06_implementation/data/imputed/**", "inference-working-copy", DENY,
         authority="generated", disposition="remove_public",
         notes="Working imputation copy; canonical bundle is data/inference."),
    rule("06_implementation/vendor/e5-small-v2/**", "vendor-tokenizer",
         owner_source="intfloat/e5-small-v2", exact_revision="configs/corpus.yaml",
         license_expression="MIT", evidence_snapshot="06_implementation/configs/corpus.yaml",
         grant_scope="tokenizer-config-vocab-only", grant_exclusions="model-weights",
         decision_id="PUB-2026-09-16-VENDOR-E5"),
    rule("02_datasets/processed/**", "processed-telemetry",
         owner_source="project-derived-from-RCAEval",
         license_expression="MIT", evidence_snapshot="02_datasets/licenses_and_lineage.md",
         grant_scope="de-identified-processed-extracts",
         grant_exclusions="raw-parquet-gold-labels",
         sensitive_data_status="redacted_approved",
         decision_id="PUB-2026-09-16-DERIVED-REDACTED"),
    rule("03_collection_plan/knowledge-corpus-historical/**", "knowledge-corpus",
         owner_source="upstream-with-attribution",
         license_expression="Apache-2.0 OR CC-BY-4.0",
         evidence_snapshot="03_collection_plan/knowledge-corpus-historical/source-manifest.jsonl",
         grant_scope="attributed-processed-chunks-and-manifests",
         grant_exclusions="raw-source-snapshots-trademarks-external-assets",
         decision_id="PUB-2026-09-16-CORPUS-ATTRIBUTED"),
    rule("03_collection_plan/knowledge-corpus/**", "knowledge-corpus",
         owner_source="upstream-with-attribution",
         license_expression="Apache-2.0 OR CC-BY-4.0",
         evidence_snapshot="03_collection_plan/knowledge-corpus/source-manifest.jsonl",
         grant_scope="attributed-processed-chunks-and-manifests",
         grant_exclusions="raw-source-snapshots-trademarks-external-assets",
         decision_id="PUB-2026-09-16-CORPUS-ATTRIBUTED"),
    rule("01_papers/**", "paper-metadata",
         owner_source="project-compiled-metadata",
         license_expression="CC0-1.0 AND MIT",
         evidence_snapshot="01_papers/enriched/README.md",
         grant_scope="descriptive-metadata-and-hand-authored-notes",
         grant_exclusions="full-text-pdf-cache",
         sensitive_data_status="public_metadata_approved",
         decision_id="PUB-2026-09-16-METADATA"),
    rule("02_datasets/**", "dataset-metadata",
         evidence_snapshot="02_datasets/licenses_and_lineage.md",
         grant_scope="catalog-cards-lineage-docs",
         grant_exclusions="raw-gold"),
    rule("03_collection_plan/**", "collection-plan", grant_scope="schemas-manifests-annotation-kit"),
    rule("04_audit/**", "audit-records", grant_scope="validation-receipts-and-ledgers"),
    rule("05_research/**", "research-docs", grant_scope="hand-authored-research-docs"),
    rule("00_plan/**", "project-plan", grant_scope="hand-authored-course-plan"),
    rule("06_implementation/**", "implementation", grant_scope="code-configs-schemas-docs-fixtures"),
    rule("scripts/**", "scripts", grant_scope="project-scripts"),
    rule("plans/reports/260913-independent-plans-contracts.md", "g0-contract-snapshot",
         grant_scope="frozen-g0-handoff-contract",
         decision_id="PUB-2026-09-17-G0-CONTRACT-SNAPSHOT",
         notes="G0 freeze source. Other AgentKit plans are local-only."),
    rule("plans/**", "internal-plans", DENY, authority="generated",
         disposition="remove_public",
         decision_id="PUB-2026-09-17-AGENT-PLANS-LOCAL",
         notes="AgentKit overlays stay gitignored; do not track timestamped cook plans."),
    rule("docs/**", "publication-policy", grant_scope="publication-and-release-docs"),
    rule(".github/**", "ci-config", grant_scope="offline-pr-and-heavy-workflows"),
    rule("README.md", "repo-root", grant_scope="root-docs-license-manifests"),
    rule("START-HERE.md", "repo-root", grant_scope="root-docs-license-manifests"),
    rule("LICENSE", "repo-root", grant_scope="root-docs-license-manifests"),
    rule("MANIFEST_SHA256.txt", "historical-snapshot", grant_scope="audit-snapshot-not-current-freeze"),
    rule("MANIFEST_RESEARCH_SHA256.txt", "historical-snapshot", grant_scope="audit-snapshot-not-current-freeze"),
    rule(".gitignore", "repo-root", grant_scope="root-docs-license-manifests"),
    rule(".gitattributes", "repo-root", grant_scope="root-docs-license-manifests"),
]


def posix(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def glob_match(path: str, pattern: str) -> bool:
    path = posix(path)
    pattern = posix(pattern)
    if pattern.startswith("**/") and pattern.endswith("/**"):
        mid = pattern[3:-3]
        if not mid:
            return True
        return (
            path == mid
            or path.startswith(mid + "/")
            or path.endswith("/" + mid)
            or f"/{mid}/" in f"/{path}/"
        )
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    if pattern.startswith("**/"):
        tail = pattern[3:]
        if any(char in tail for char in "*?[]"):
            return bool(fnmatch.fnmatch(path, pattern))
        return path.endswith("/" + tail) or path == tail
    if any(char in pattern for char in "*?[]"):
        return fnmatch.fnmatch(path, pattern)
    return path == pattern


def matching_rule(path: str, rules: list[dict] | None = None) -> dict | None:
    rel = posix(path)
    for row in rules or RULES:
        if glob_match(rel, row["path_glob"]):
            return row
    return None


def is_public_allowlisted(row: dict) -> bool:
    return (
        row.get("redistribution_status") in RIGHTS_PUBLIC
        and row.get("sensitive_data_status") in SENSITIVE_PUBLIC
        and row.get("disposition") in DISPOSITION_PUBLIC
    )


def git_ls_files(root: Path = ROOT) -> list[str]:
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    return [posix(item.decode()) for item in output.split(b"\x00") if item]


def git_head(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def git_dirty(root: Path = ROOT) -> bool:
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    return bool(status.strip())


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def load_ledger(path: Path = LEDGER_PATH) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_ledger(path: Path = LEDGER_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(RULES)
    return path


def inventory_bytes(root: Path, rels: list[str]) -> tuple[int, int]:
    total = 0
    missing = 0
    for rel in rels:
        path = root / rel
        if path.is_file():
            total += path.stat().st_size
        else:
            missing += 1
    return total, missing


def classify_tracked(root: Path = ROOT, rules: list[dict] | None = None) -> dict:
    files = git_ls_files(root)
    uncovered = []
    overlapping_check = []
    public = []
    denied = []
    for rel in files:
        row = matching_rule(rel, rules)
        if row is None:
            uncovered.append(rel)
            continue
        overlapping_check.append(rel)
        if is_public_allowlisted(row):
            public.append(rel)
        else:
            denied.append(rel)
    return {
        "tracked": files,
        "public": public,
        "denied": denied,
        "uncovered": uncovered,
        "count": len(files),
        "bytes": inventory_bytes(root, files)[0],
    }


def scan_text_for_policy(path: Path, rel: str) -> list[str]:
    posix_rel = posix(rel)
    if posix_rel in SKIP_SCAN_EXACT:
        return []
    if any(posix_rel.startswith(prefix) for prefix in SKIP_SCAN_PREFIXES):
        return []
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".parquet", ".whl", ".bin", ".pt", ".safetensors"}:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    hits = []
    if LOCAL_PATH_RE.search(text) and not rel.startswith("04_audit/"):
        hits.append("local_absolute_path")
    if SECRET_RE.search(text):
        hits.append("secret_pattern")
    if PII_SENTINEL_RE.search(text):
        hits.append("pii_sentinel")
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["write-ledger", "inventory"])
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    args = parser.parse_args()
    if args.command == "write-ledger":
        write_ledger(args.ledger)
        print(json.dumps({"ledger": posix(args.ledger.relative_to(ROOT)), "rules": len(RULES)}))
        return
    summary = classify_tracked()
    print(json.dumps({
        "policy_version": POLICY_VERSION,
        "tracked": summary["count"],
        "bytes": summary["bytes"],
        "public": len(summary["public"]),
        "denied": len(summary["denied"]),
        "uncovered": summary["uncovered"][:20],
        "archive_target": "pinned-upstream-reacquisition",
        "history_action": "no-rewrite",
        "history_decision_id": "HIST-2026-09-16-NO-REWRITE",
        "archive_decision_id": "ARCH-2026-09-16-UPSTREAM-PIN",
    }, indent=2))


if __name__ == "__main__":
    main()
