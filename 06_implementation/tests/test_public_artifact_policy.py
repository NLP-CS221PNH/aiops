"""Public artifact ledger, identifier and forbidden-path gates."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.data.common import IMPL, ROOT

SCRIPTS = ROOT / "scripts"


def run_script(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class PublicArtifactPolicyTests(unittest.TestCase):
    def test_ledger_covers_every_tracked_path(self):
        result = run_script(
            str(SCRIPTS / "validate-public-artifacts.py"),
            "--ledger",
            "04_audit/public-artifact-ledger.tsv",
            "--tracked-only",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"], payload.get("failed"))
        self.assertEqual(result.returncode, 0)

    def test_forbidden_globs_are_not_tracked(self):
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        forbidden = (
            "/cache/",
            "/rescue-cache/",
            "/primary-text/",
            "02_datasets/acquired/raw/",
            "processed/labels/",
            "data/private/",
            "candidate-inference/",
            "candidate-pre-review/",
            "/source-snapshots/",
        )
        leaked = [
            path.replace("\\", "/")
            for path in tracked
            if any(token in path.replace("\\", "/") for token in forbidden)
            and not path.replace("\\", "/").endswith("/LICENSE")
        ]
        self.assertEqual(leaked, [])

    def test_canonical_identifiers_pass_on_enriched_catalog(self):
        result = run_script(str(SCRIPTS / "canonical_identifiers.py"))
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"], payload.get("errors"))
        self.assertEqual(result.returncode, 0)

    def test_duplicate_nested_doi_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "catalog.jsonl"
            catalog.write_text(
                json.dumps({"paper_id": "P0001", "doi": "10.1/ABC", "research": {"metadata": {}}})
                + "\n"
                + json.dumps({
                    "paper_id": "P0002",
                    "research": {
                        "metadata": {
                            "related_identifiers": [{
                                "relatedIdentifier": "https://doi.org/10.1/ABC",
                                "relatedIdentifierType": "DOI",
                                "relationType": "IsVersionOf",
                            }]
                        }
                    },
                })
                + "\n",
                encoding="utf-8",
            )
            result = run_script(str(SCRIPTS / "canonical_identifiers.py"), "--catalog", str(catalog))
            payload = json.loads(result.stdout)
            self.assertFalse(payload["passed"])
            self.assertEqual(result.returncode, 1)

    def test_source_snapshot_license_exception(self):
        sys.path.insert(0, str(SCRIPTS))
        from publication_policy import (
            FORBIDDEN_PUBLIC_EXCEPTIONS,
            glob_match,
            matching_rule,
        )
        license_path = "03_collection_plan/knowledge-corpus/raw/source-snapshots/D057/LICENSE"
        other = "03_collection_plan/knowledge-corpus/raw/source-snapshots/D057/files/README.md"
        self.assertTrue(glob_match(license_path, "**/source-snapshots/**"))
        self.assertTrue(glob_match(other, "**/source-snapshots/**"))
        self.assertTrue(any(glob_match(license_path, pattern) for pattern in FORBIDDEN_PUBLIC_EXCEPTIONS))
        self.assertFalse(any(glob_match(other, pattern) for pattern in FORBIDDEN_PUBLIC_EXCEPTIONS))
        self.assertEqual(matching_rule(license_path)["disposition"], "keep_public")
        self.assertEqual(matching_rule(other)["disposition"], "archive_private")

    def test_escaped_windows_home_path_is_detected(self):
        sys.path.insert(0, str(SCRIPTS))
        from publication_policy import LOCAL_PATH_RE, scan_text_for_policy
        self.assertIsNotNone(LOCAL_PATH_RE.search(r'C:\\Users\\someone\\Downloads\\pack'))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leak.json"
            path.write_text('{"cwd": "C:\\\\Users\\\\someone\\\\Downloads\\\\pack"}', encoding="utf-8")
            self.assertIn("local_absolute_path", scan_text_for_policy(path, "reports/leak.json"))
        result = run_script(str(ROOT / "01_papers/enriched/finalize-research.py"), "--check")
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"], payload.get("errors"))

    def test_freeze_manifest_omits_self_paths(self):
        result = run_script(str(SCRIPTS / "freeze-research-pack.py"), "--check")
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"], payload.get("errors"))
        import csv
        manifest = ROOT / "04_audit" / "public-tracked-manifest.tsv"
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            paths = {row["path"] for row in csv.DictReader(handle, delimiter="\t")}
        self.assertNotIn("04_audit/public-tracked-manifest.tsv", paths)
        self.assertNotIn("04_audit/public-freeze-receipt.json", paths)


if __name__ == "__main__":
    unittest.main()
