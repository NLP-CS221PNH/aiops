"""Fail-closed public-artifact gate: ledger coverage, size, forbidden paths, secrets."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publication_policy import (  # noqa: E402
    FORBIDDEN_PUBLIC_EXCEPTIONS,
    FORBIDDEN_PUBLIC_GLOBS,
    LEDGER_PATH,
    POLICY_VERSION,
    SIZE_LIMIT_MIB,
    git_ls_files,
    glob_match,
    is_public_allowlisted,
    load_ledger,
    matching_rule,
    scan_text_for_policy,
)


def fail(name: str, details) -> dict:
    return {"check": name, "passed": False, "details": details}


def ok(name: str, details=None) -> dict:
    return {"check": name, "passed": True, "details": details}


def run_checks(ledger_path: Path, tracked_only: bool) -> list[dict]:
    checks = []
    if not ledger_path.is_file():
        return [fail("ledger_missing", str(ledger_path))]
    rules = load_ledger(ledger_path)
    if not rules:
        return [fail("ledger_not_empty", str(ledger_path))]
    seen = []
    for row in rules:
        glob = row.get("path_glob")
        if not glob:
            checks.append(fail("ledger_row_missing_glob", row))
            continue
        if glob in seen:
            checks.append(fail("duplicate_ledger_glob", glob))
        seen.append(glob)
        for field in ("redistribution_status", "sensitive_data_status", "disposition", "approver", "decision_id"):
            if not row.get(field):
                checks.append(fail("ledger_missing_field", {"glob": glob, "field": field}))
    files = git_ls_files(ROOT)
    uncovered = []
    public_denied = []
    size_violations = []
    size_exception_incomplete = []
    forbidden = []
    scan_hits = []
    expired = []
    now = datetime.now(timezone.utc).date().isoformat()
    for rel in files:
        row = matching_rule(rel, rules)
        if row is None:
            uncovered.append(rel)
            continue
        expiry = (row.get("expiry") or "").strip()
        if expiry and expiry < now and is_public_allowlisted(row):
            expired.append({"path": rel, "expiry": expiry})
        public = is_public_allowlisted(row)
        if not public:
            public_denied.append(rel)
        for pattern in FORBIDDEN_PUBLIC_GLOBS:
            if glob_match(rel, pattern) and public:
                forbidden.append(rel)
        path = ROOT / rel
        if path.is_file():
            size_mib = path.stat().st_size / (1024 * 1024)
            exception = row.get("size_exception_mib") or ""
            if exception and public:
                if not (row.get("expiry") and row.get("approver") and row.get("decision_id")):
                    size_exception_incomplete.append({
                        "path": rel,
                        "glob": row.get("path_glob"),
                        "missing": [field for field in ("expiry", "approver", "decision_id") if not row.get(field)],
                    })
            limit = float(exception) if exception else SIZE_LIMIT_MIB
            if public and size_mib > limit:
                size_violations.append({"path": rel, "mib": round(size_mib, 3), "limit": limit})
            if public:
                hits = scan_text_for_policy(path, rel)
                if hits:
                    scan_hits.append({"path": rel, "hits": hits})
    checks.append(ok("ledger_loaded", {"rules": len(rules), "policy_version": POLICY_VERSION})
                  if rules else fail("ledger_loaded", "empty"))
    checks.append(ok("tracked_coverage", len(files)) if not uncovered else fail("tracked_coverage", uncovered[:50]))
    checks.append(ok("public_allowlist_excludes_denied", len(public_denied))
                  if tracked_only else ok("denied_inventory", len(public_denied)))
    if tracked_only:
        leaked = [rel for rel in files if matching_rule(rel, rules) and not is_public_allowlisted(matching_rule(rel, rules))]
        checks.append(ok("tracked_only_public", len(files)) if not leaked else fail("tracked_only_public", leaked[:50]))
        leaked_forbidden = [
            rel for rel in files
            if any(glob_match(rel, pattern) for pattern in FORBIDDEN_PUBLIC_GLOBS)
            and not any(glob_match(rel, pattern) for pattern in FORBIDDEN_PUBLIC_EXCEPTIONS)
        ]
        checks.append(ok("forbidden_globs_untracked", 0) if not leaked_forbidden else fail("forbidden_globs_untracked", leaked_forbidden[:50]))
    else:
        checks.append(ok("forbidden_globs_documented", len(forbidden)))
    checks.append(ok("size_limit", SIZE_LIMIT_MIB) if not size_violations else fail("size_limit", size_violations[:20]))
    checks.append(ok("size_exception_fields", 0) if not size_exception_incomplete else fail("size_exception_fields", size_exception_incomplete[:20]))
    checks.append(ok("no_expired_public_exceptions", 0) if not expired else fail("expired_exceptions", expired))
    checks.append(ok("no_local_path_or_secret_in_public", 0) if not scan_hits else fail("public_text_scan", scan_hits[:20]))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    parser.add_argument("--tracked-only", action="store_true",
                        help="Fail if any tracked path is outside the public allowlist.")
    args = parser.parse_args()
    checks = run_checks(args.ledger, args.tracked_only)
    failed = [item for item in checks if not item["passed"]]
    report = {
        "passed": not failed,
        "policy_version": POLICY_VERSION,
        "failed": failed,
        "checks": checks,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
