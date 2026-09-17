"""Freeze public-tracked files from git + the publication ledger."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publication_policy import (  # noqa: E402
    LEDGER_PATH,
    POLICY_VERSION,
    classify_tracked,
    git_head,
    load_ledger,
    matching_rule,
    posix,
    sha256_file,
)

PUBLIC_MANIFEST = ROOT / "04_audit" / "public-tracked-manifest.tsv"
RECEIPT = ROOT / "04_audit" / "public-freeze-receipt.json"
LEGACY_MANIFEST = ROOT / "MANIFEST_RESEARCH_SHA256.txt"
LEGACY_INVENTORY = ROOT / "04_audit" / "research-file-inventory.tsv"
FREEZE_SELF = {
    "04_audit/public-tracked-manifest.tsv",
    "04_audit/public-freeze-receipt.json",
}


def public_rows(root: Path = ROOT) -> list[dict]:
    if not LEDGER_PATH.is_file():
        raise SystemExit("missing_ledger")
    rules = load_ledger(LEDGER_PATH)
    summary = classify_tracked(root, rules)
    rows = []
    for rel in summary["public"]:
        if rel in FREEZE_SELF:
            continue
        path = root / rel
        row = matching_rule(rel, rules)
        rows.append({
            "path": rel,
            "bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": sha256_file(path) if path.is_file() else "",
            "artifact_class": row.get("artifact_class", ""),
            "redistribution_status": row.get("redistribution_status", ""),
            "sensitive_data_status": row.get("sensitive_data_status", ""),
            "disposition": row.get("disposition", ""),
        })
    return sorted(rows, key=lambda item: item["path"])


def write_manifest(rows: list[dict], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".staging")
    with staging.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "bytes", "sha256", "artifact_class", "redistribution_status", "sensitive_data_status", "disposition"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    if path.exists():
        path.unlink()
    staging.replace(path)
    return sha256_file(path)


def receipt_payload(rows: list[dict], manifest_hash: str, revision: str) -> dict:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    created = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat() if epoch else datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "cs221-public-freeze-receipt-v1",
        "policy_version": POLICY_VERSION,
        "code_revision": revision,
        "created_at_utc": created,
        "file_count": len(rows),
        "payload_bytes": sum(int(row["bytes"]) for row in rows),
        "manifest_path": posix(PUBLIC_MANIFEST.relative_to(ROOT)),
        "manifest_sha256": manifest_hash,
        "legacy_snapshot_manifest": posix(LEGACY_MANIFEST.relative_to(ROOT)),
        "legacy_snapshot_inventory": posix(LEGACY_INVENTORY.relative_to(ROOT)),
        "note": "Legacy MANIFEST_RESEARCH_SHA256.txt is an audit snapshot, not the current public freeze. Freeze artifacts omit themselves from the path list so their hashes stay stable.",
    }


def verify_rows(rows: list[dict]) -> list[str]:
    errors = []
    seen = set()
    for row in rows:
        rel = row["path"]
        if rel in seen:
            errors.append(f"duplicate:{rel}")
        seen.add(rel)
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing:{rel}")
            continue
        if sha256_file(path) != row["sha256"] or str(path.stat().st_size) != str(row["bytes"]):
            errors.append(f"mismatch:{rel}")
    if PUBLIC_MANIFEST.is_file():
        on_disk = list(csv.DictReader(PUBLIC_MANIFEST.open(encoding="utf-8-sig", newline=""), delimiter="\t"))
        disk_paths = {item["path"] for item in on_disk}
        live_paths = {item["path"] for item in rows}
        for rel in sorted(live_paths - disk_paths):
            errors.append(f"missing_from_manifest:{rel}")
        for rel in sorted(disk_paths - live_paths):
            errors.append(f"unexpected_in_manifest:{rel}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only verification; never writes.")
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    args = parser.parse_args()
    revision = git_head(ROOT)
    rows = public_rows(ROOT)
    if args.check:
        if not PUBLIC_MANIFEST.is_file() or not RECEIPT.is_file():
            print(json.dumps({"passed": False, "error": "missing_freeze_artifacts"}))
            raise SystemExit(1)
        errors = verify_rows(rows)
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        live_hash = sha256_file(PUBLIC_MANIFEST)
        if receipt.get("manifest_sha256") != live_hash:
            errors.append("stale_receipt")
        if receipt.get("policy_version") != POLICY_VERSION:
            errors.append("stale_policy")
        print(json.dumps({"passed": not errors, "errors": errors, "files": len(rows), "revision": revision}))
        raise SystemExit(0 if not errors else 1)
    manifest_hash = write_manifest(rows, PUBLIC_MANIFEST)
    payload = receipt_payload(rows, manifest_hash, revision)
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "files": len(rows), "manifest": posix(PUBLIC_MANIFEST.relative_to(ROOT)), "revision": revision}))


if __name__ == "__main__":
    main()
