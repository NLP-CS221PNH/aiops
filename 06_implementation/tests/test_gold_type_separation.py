"""G1 ≠ G2 ≠ G2-proxy ≠ G3 ≠ G4. Does not rewrite freeze bytes."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
import unittest

IMPL = Path(__file__).resolve().parents[1]
ROOT = IMPL.parent
RE2OB = re.compile(r"re2ob_[a-z0-9-]+_(cpu|mem|memory|disk|delay|loss|socket)_\d")


class GoldTypeSeparation(unittest.TestCase):
    def test_qrels_grades_are_012(self):
        for split in ("train", "dev", "test"):
            path = IMPL / "annotations" / "qrels" / split / "qrels.tsv"
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertTrue(rows, path)
            self.assertNotIn("reviewer_id", rows[0])
            for row in rows:
                grade = row["relevance_grade"]
                self.assertIn(grade, {"0", "1", "2"}, msg=path)
                for forbidden in (
                    "root_cause_service",
                    "source_case",
                    "fault",
                    "checkoutservice",
                ):
                    self.assertNotEqual(grade, forbidden)

    def test_f2_bytes_still_say_human_sidecar_overrides(self):
        f2 = json.loads((IMPL / "freezes" / "F2.json").read_text(encoding="utf-8"))
        self.assertTrue(any("human" in item.lower() for item in f2["limitations"]))
        sidecar = json.loads((IMPL / "freezes" / "F2.provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["qrels_provenance"], "llm_lexical_proxy")
        self.assertEqual(sidecar["f2_sha256"], f2_hash())
        self.assertEqual(sidecar["qrels_hash"], f2["qrels_hash"])

    def test_blinded_reviewer_is_llm_judge(self):
        path = IMPL / "annotations" / "blinded" / "test" / "annotator-A.tsv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertTrue(any(row.get("reviewer_id", "").startswith("LLM_Judge") for row in rows))

    def test_g1_equivalent_leak_is_documented_not_used_as_qrels(self):
        manifest = ROOT / "02_datasets" / "acquired" / "labels" / "acquisition-manifest.tsv"
        text = manifest.read_text(encoding="utf-8")
        self.assertRegex(text, RE2OB)
        contract = (IMPL / "docs" / "gold-type-contract.md").read_text(encoding="utf-8")
        self.assertIn("acquisition-manifest.tsv", contract)
        self.assertIn("not annotators", contract)

    def test_coverage_pilot_is_train_only(self):
        split_map = IMPL / "data" / "private" / "split-map.tsv"
        if not split_map.exists():
            split_map = ROOT / "02_datasets" / "processed" / "split-map.tsv"
        train_ids = set()
        with split_map.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["split"] == "train":
                    train_ids.add(row["incident_id"])
        path = IMPL / "annotations" / "coverage-pilot" / "candidate-ids.tsv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            ids = [row["incident_id"] for row in csv.DictReader(handle, delimiter="\t")]
        self.assertEqual(len(ids), 6)
        self.assertTrue(set(ids).issubset(train_ids))

    def test_candidate_tsv_has_no_grades(self):
        path = ROOT / "03_collection_plan" / "annotation-kit" / "incident-document-candidates.tsv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            header = reader.fieldnames or []
            rows = list(reader)
        self.assertIn("symptom_family", header)
        self.assertIn("service_scope", header)
        for row in rows:
            self.assertIn(row.get("is_qrel", "false").lower(), {"false", "0", ""})
            self.assertEqual((row.get("relevance_grade") or "").strip(), "")

    def test_kit_still_has_zero_human_qrels(self):
        status = json.loads(
            (ROOT / "03_collection_plan" / "annotation-kit" / "status.json").read_text(encoding="utf-8")
        )
        self.assertEqual(status["human_judgments_completed"], 0)
        self.assertFalse(status["gold_qrels_available"])

    def test_inference_observations_drop_g1_and_split(self):
        path = IMPL / "data" / "inference" / "observations.jsonl"
        self.assertTrue(path.is_file())
        forbidden = {
            "split",
            "scenario_family_id",
            "source_case",
            "root_cause_service",
            "fault",
            "gold",
        }
        with path.open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(rows), 90)
        for row in rows:
            self.assertTrue(forbidden.isdisjoint(row))
            blob = json.dumps(row, ensure_ascii=False)
            self.assertIsNone(RE2OB.search(blob))

    def test_inference_exporters_do_not_join_g1_leaks(self):
        for rel in (
            "src/data/export_inference_data.py",
            "src/data/validate_inputs.py",
            "src/data/package_inference.py",
        ):
            text = (IMPL / rel).read_text(encoding="utf-8")
            self.assertNotIn("acquisition-manifest", text, msg=rel)
            self.assertNotIn("cases-index.json", text, msg=rel)
            self.assertNotIn("re2ob_", text, msg=rel)

    def test_private_g1_copy_matches_canonical_hash(self):
        import hashlib

        config = json.loads((IMPL / "configs" / "data.yaml").read_text(encoding="utf-8"))
        expected = config["private_sources"]["ground_truth.jsonl"]["sha256"]
        canonical = ROOT / "02_datasets" / "processed" / "labels" / "ground_truth.jsonl"
        private = IMPL / "data" / "private" / "ground_truth.jsonl"
        if not canonical.is_file():
            self.skipTest("canonical G1 not present")
        self.assertEqual(hashlib.sha256(canonical.read_bytes()).hexdigest(), expected)
        if private.is_file():
            self.assertEqual(hashlib.sha256(private.read_bytes()).hexdigest(), expected)


def f2_hash() -> str:
    import hashlib

    return hashlib.sha256((IMPL / "freezes" / "F2.json").read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
