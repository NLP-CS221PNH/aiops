"""Create a Plan 01 draft or explicitly authorized automated acceptance manifest.

Run after review edits. Existing same-version content cannot be silently replaced.
Only the explicit plan-01 file list is included; other concurrent plans are untouched.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION = ROOT / "06_implementation"
ARTIFACTS = [
    "README.md", "requirements-validation.txt",
    "configs/protocol.yaml", "configs/decisions.json",
    "docs/project-charter.md", "docs/research-protocol.md", "docs/decision-log.md",
    "docs/team-working-agreement.md", "docs/instructor-questions-draft.md",
    "docs/literature-matrix.tsv", "docs/literature-reading-notes.md",
    "docs/protocol-review.md", "scripts/validate_protocol.py",
    "scripts/build_g0_manifest.py", "tests/test_validate_protocol.py",
    "validation/source-inventory.py", "validation/source-inventory.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = yaml.safe_load((IMPLEMENTATION / "configs/protocol.yaml").read_text(encoding="utf-8"))
    decisions = json.loads((IMPLEMENTATION / "configs/decisions.json").read_text(encoding="utf-8"))
    automated = config.get("gate", {}).get("review_mode") == "automated"
    if not automated and (config["status"] != "draft" or config["gate"]["status"] != "awaiting_human_review"):
        raise SystemExit("This builder only creates draft review candidates; human gate acceptance requires explicit review records.")
    validator_module = None
    review = None
    if automated:
        spec = importlib.util.spec_from_file_location("g0_candidate_validator", Path(__file__).with_name("validate_protocol.py"))
        validator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator_module)
        # Load errors are reported before any archive or accepted manifest is written.
        preflight = validator_module.Validator(ROOT)
        preflight.load(validator_module.AUTH)
        review = preflight.load(validator_module.REVIEW)
        if preflight.errors:
            raise SystemExit(json.dumps({"result": "FAIL", "errors": preflight.errors}))
    inventory = json.loads((IMPLEMENTATION / "validation/source-inventory.json").read_text(encoding="utf-8"))
    sources = []
    for source in inventory["sources"]:
        path = ROOT / source["path"]
        if digest(path) != source["sha256"]:
            raise SystemExit(f"Source changed since inventory audit: {source['path']}; investigate before rebuilding.")
        sources.append({"path": source["path"], "sha256": source["sha256"]})
    version = config["version"]
    names = ARTIFACTS + (["configs/acceptance-authorization.json", "reports/plan01-autonomous-review.json", "docs/acceptance-amendment.md"] if automated else [])
    artifacts = [{"path": f"06_implementation/{name}", "sha256": digest(IMPLEMENTATION / name), "version": version} for name in names]
    manifest = {
        "schema_version": 1, "gate_id": "G0", "gate_kind": "project_start",
        "gate_status": "awaiting_human_review", "protocol_id": config["protocol_id"],
        "version": version, "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifacts": artifacts, "sources": sources, "reviewers": [],
        "pending_reviews": [
            {"role": "A", "person": None, "scope": "inventory and data boundary", "reviewed_at": None},
            {"role": "B", "person": None, "scope": "design, metrics and reproducibility", "reviewed_at": None},
            {"role": "C", "person": None, "scope": "scope, resources and handoff", "reviewed_at": None},
        ],
        "permissions": config["permissions"],
        "open_decisions": [row["decision_id"] for row in decisions["decisions"] if row["status"] == "pending"],
        "allowed_work": ["data", "corpus", "representation", "retrieval", "annotation_preparation"],
        "allowed_work_mode": "preparation_only_until_G0",
        "communication": config["communication"],
        "notes": "Local audit metadata only; not an inference payload, F1, F2, or evidence of human approval.",
    }
    if automated:
        manifest.update(
            gate_status="accepted", review_mode="automated", authorization_ref=validator_module.AUTH,
            pending_reviews=[], allowed_work_mode="accepted_under_explicit_user_authorization",
            automated_reviews=[{"reviewer": review.get("reviewer"), "scope": review.get("scope"),
                                "reviewed_at": review.get("reviewed_at_utc"), "evidence_ref": validator_module.REVIEW}],
        )
        checked = validator_module.Validator(ROOT).run(require_g0=True, manifest_override=manifest)
        if checked["result"] != "PASS":
            raise SystemExit(json.dumps(checked, ensure_ascii=False))
    out = IMPLEMENTATION / "freezes/G0/manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        old = json.loads(out.read_text(encoding="utf-8"))
        if old["version"] == version and "supersedes" in old:
            manifest["supersedes"] = old["supersedes"]
        comparable = lambda obj: {k: v for k, v in obj.items() if k != "created_at_utc"}
        if comparable(old) == comparable(manifest):
            print("Manifest unchanged; existing timestamp and bytes preserved.")
            return
        if old["version"] == version:
            raise SystemExit("Content changed under the same manifest version. Review changes and increment document/config version first.")
        archive = out.parent / f"manifest-{old['version']}-{digest(out)[:12]}.json"
        # No overwrite or deletion: retain exact historical manifest bytes.
        if not archive.exists():
            archive.write_bytes(out.read_bytes())
        manifest["supersedes"] = {"path": archive.relative_to(ROOT).as_posix(), "sha256": digest(archive)}
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {out.relative_to(ROOT).as_posix()} ({version}); G0 {manifest['gate_status']} ({'automated' if automated else 'human'} review mode).")


if __name__ == "__main__":
    main()
