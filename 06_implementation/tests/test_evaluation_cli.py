"""Evaluation CLI is fail-closed and validate-handoff is read-only."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.data.common import IMPL, ROOT
from src.evaluation.cli_ops import sha256_file, validate_handoff


def run_eval(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.evaluation", *args],
        cwd=IMPL,
        text=True,
        capture_output=True,
        check=False,
    )


class EvaluationCliTests(unittest.TestCase):
    def test_placeholder_handoff_fails_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "final-manifest.json"
            manifest.write_text(json.dumps({"handoff": "ready"}), encoding="utf-8")
            before = (manifest.stat().st_mtime_ns, sha256_file(manifest))
            result = run_eval("validate-handoff", "--manifest", str(manifest))
            after = (manifest.stat().st_mtime_ns, sha256_file(manifest))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, after)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), {"handoff": "ready"})

    def test_unsupported_review_import_exits_nonzero_without_output(self):
        result = run_eval("review-import", "--judgments", "missing.tsv")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported", result.stderr.lower() + result.stdout.lower())

    def test_score_missing_inputs_does_not_write_sample_rows(self):
        target = IMPL / "results" / "per-incident.tsv"
        before = target.read_bytes() if target.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            result = run_eval(
                "score",
                "--system", "missing.json",
                "--qrels", "missing.tsv",
                "--runs", "missing.jsonl",
                "--output", str(Path(tmp) / "per-incident.tsv"),
            )
        self.assertNotEqual(result.returncode, 0)
        after = target.read_bytes() if target.exists() else None
        self.assertEqual(before, after)

    def test_score_and_analyze_with_declared_human_contract_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            qrels = Path(tmp) / "qrels.tsv"
            runs = Path(tmp) / "runs.jsonl"
            system = Path(tmp) / "F1.json"
            scored_out = Path(tmp) / "per-incident.tsv"
            analyzed_out = Path(tmp) / "family-comparison.tsv"
            qrels.write_text("incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\ninc1\tdoc1\t1\thuman-double-adjudicated\tfixture-A+B\tadjudicated\ttest-only\n", encoding="utf-8")
            runs.write_text(json.dumps({"incident_id": "inc1", "ranking": ["doc1"]}) + "\n", encoding="utf-8")
            system.write_text(json.dumps({"schema_version": "cs221-freeze-f1-v1", "status": "frozen", "qrels_hash": sha256_file(qrels)}), encoding="utf-8")
            scored = run_eval(
                "score",
                "--system", str(system),
                "--qrels", str(qrels),
                "--runs", str(runs),
                "--output", str(scored_out),
            )
            self.assertEqual(scored.returncode, 0, scored.stderr)
            self.assertTrue(scored_out.is_file())
            with scored_out.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertGreater(len(rows), 0)
            analyzed = run_eval(
                "analyze",
                "--results", str(scored_out),
                "--group", "metric",
                "--output", str(analyzed_out),
            )
            self.assertEqual(analyzed.returncode, 0, analyzed.stderr)
            canonical = IMPL / "results" / "per-incident.tsv"
            self.assertNotEqual(canonical.read_bytes(), scored_out.read_bytes())

    def test_score_refuses_canonical_results_path(self):
        canonical = IMPL / "results" / "per-incident.tsv"
        before = canonical.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            qrels = Path(tmp) / "qrels.tsv"
            runs = Path(tmp) / "runs.jsonl"
            system = Path(tmp) / "F1.json"
            qrels.write_text("incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\ninc1\tdoc1\t1\thuman-double-adjudicated\tfixture-A+B\tadjudicated\ttest-only\n", encoding="utf-8")
            runs.write_text(json.dumps({"incident_id": "inc1", "ranking": ["doc1"]}) + "\n", encoding="utf-8")
            system.write_text(json.dumps({"schema_version": "cs221-freeze-f1-v1", "status": "frozen", "qrels_hash": sha256_file(qrels)}), encoding="utf-8")
            result = run_eval(
                "score",
                "--system", str(system),
                "--qrels", str(qrels),
                "--runs", str(runs),
                "--output", str(canonical),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing_to_overwrite_canonical_results", result.stderr + result.stdout)
        self.assertEqual(before, canonical.read_bytes())

    def test_validate_handoff_accepts_real_revision_and_hashes(self):
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        sample = IMPL / "docs" / "reproduce.md"
        payload = {
            "code_revision": revision,
            "artifacts": [{
                "path": "docs/reproduce.md",
                "sha256": sha256_file(sample),
                "license_ref": "MIT",
                "size_bytes": sample.stat().st_size,
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            before = sha256_file(manifest)
            with mock.patch("src.evaluation.cli_ops.git_dirty", return_value=False):
                validate_handoff(str(manifest))
            self.assertEqual(before, sha256_file(manifest))

    def test_historical_freezes_and_proxy_qrels_are_rejected(self):
        for freeze in ("F1.json", "F2.json"):
            result = run_eval("verify-freezes", "--system", str(IMPL / "freezes" / freeze),
                              "--qrels", str(IMPL / "annotations/qrels/test/qrels.tsv"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("qrels_not_human_gold", result.stderr)

    def test_verify_freezes_rejects_wrong_qrels_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            qrels = Path(tmp) / "qrels.tsv"
            freeze = Path(tmp) / "F2.json"
            qrels.write_text("incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\ninc1\tdoc1\t1\thuman-double-adjudicated\tfixture-A+B\tadjudicated\ttest-only\n", encoding="utf-8")
            freeze.write_text(json.dumps({
                "schema_version": "cs221-annotation-freeze-f2-v1",
                "qrels_hash": "1" * 64,
                "hashes": {"retriever": "live"},
            }), encoding="utf-8")
            result = run_eval("verify-freezes", "--system", str(freeze), "--qrels", str(qrels))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("freeze_hash_mismatch", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
