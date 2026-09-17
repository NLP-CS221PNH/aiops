"""Annotation integrity: proxy qrels are not human gold."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import unittest

IMPL = Path(__file__).resolve().parents[1]


class TestAnnotationIntegrity(unittest.TestCase):
    def test_blind_forms_no_rank_score(self):
        path = IMPL / "annotations" / "blinded" / "train" / "annotator-A.tsv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle, delimiter="\t"))
        lowered = {name.lower() for name in header}
        self.assertNotIn("rank", lowered)
        self.assertNotIn("score", lowered)

    def test_double_annotation_requirement_not_met_by_llm_personas(self):
        path = IMPL / "annotations" / "blinded" / "dev" / "annotator-A.tsv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertTrue(rows)
        self.assertTrue(rows[0]["reviewer_id"].startswith("LLM_Judge"))

    def test_qrels_require_proxy_provenance_on_every_row(self):
        import hashlib

        sidecar = json.loads((IMPL / "freezes/F2.provenance.json").read_text(encoding="utf-8"))
        for split in ("train", "dev", "test"):
            path = IMPL / f"annotations/qrels/{split}/qrels.tsv"
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                self.assertTrue({"provenance", "annotator_id", "adjudication_state", "annotation_version"}.issubset(reader.fieldnames))
                rows = list(reader)
            self.assertTrue(rows)
            self.assertTrue(all(row["provenance"] == "llm_lexical_proxy" for row in rows))
            self.assertEqual(sidecar["qrels_files"][split]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotEqual(sidecar["current_qrels_hash"], sidecar["qrels_hash"])
        self.assertFalse(sidecar["f1_evaluation_eligible"])
        self.assertFalse(sidecar["f2_evaluation_eligible"])

    def test_f2_generator_refuses_human_default(self):
        source = (IMPL / "src" / "annotations" / "freeze_f2.py").read_text(encoding="utf-8")
        self.assertNotIn(
            '"F2 freezes adjudicated human test qrels linked to F1 freeze."',
            source,
        )
        self.assertIn("llm_lexical_proxy", source)
        self.assertIn("coverage_info is required", source)

    def test_calibration_report_is_retracted(self):
        text = (IMPL / "annotations" / "calibration" / "calibration-report.md").read_text(encoding="utf-8")
        self.assertIn("RETRACTED", text)

    def test_reports_do_not_treat_proxy_as_human_gold(self):
        forbidden = (
            "đủ điều kiện giải phóng cổng kiểm soát Plan 06",
            "được chấm đôi độc lập bởi 2 người và phân xử bởi người thứ 3",
        )
        for rel in (
            "reports/slides.md",
            "reports/annotation-agreement-report.md",
            "reports/final-report.md",
            "reports/claim-audit.md",
        ):
            text = (IMPL / rel).read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, msg=rel)


if __name__ == "__main__":
    unittest.main()
