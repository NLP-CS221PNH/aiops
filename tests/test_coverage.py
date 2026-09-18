"""Coverage CLI fails closed when top-k returned hits are unjudged."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.annotations.coverage import check_coverage, main as coverage_main


class CoverageCliTests(unittest.TestCase):
    def test_complete_judged_top_k_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qrels = root / "qrels.tsv"
            runs = root / "runs.jsonl"
            qrels.write_text(
                "incident_id\tchunk_id\trelevance_grade\ninc1\tdoc1\t2\ninc1\tdoc2\t0\n",
                encoding="utf-8",
            )
            runs.write_text(json.dumps({"incident_id": "inc1", "ranking": ["doc1", "doc2"]}) + "\n", encoding="utf-8")
            report = check_coverage([runs], qrels, [2])
        self.assertTrue(report["complete"])
        self.assertEqual(report["top2_coverage_ratio"], 1.0)

    def test_unjudged_hit_is_incomplete_not_grade_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qrels = root / "qrels.tsv"
            runs = root / "runs.jsonl"
            qrels.write_text(
                "incident_id\tchunk_id\trelevance_grade\ninc1\tdoc1\t1\n",
                encoding="utf-8",
            )
            runs.write_text(json.dumps({"incident_id": "inc1", "ranking": ["doc1", "missing"]}) + "\n", encoding="utf-8")
            code = coverage_main(["--runs", str(runs), "--qrels", str(qrels), "--required-k", "2"])
        self.assertEqual(code, 4)


if __name__ == "__main__":
    unittest.main()
