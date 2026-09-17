"""Behavioral checks for provenance, pilot blinding, and forensic preservation."""
import csv
import importlib.util
import json
import random
import tempfile
import unittest
from pathlib import Path

from src.annotations.common import CoverageError
from src.annotations.freeze_f2 import build_f2_freeze
from src.evaluation.cli_ops import load_qrels, score_runs, verify_freezes

IMPL = Path(__file__).resolve().parents[1]
ROOT = IMPL.parent


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class ReadinessContractTests(unittest.TestCase):
    def test_invalidated_freeze_cannot_be_reused_with_relabelled_qrels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qrels.tsv"
            path.write_text("incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\n"
                            "i\tc\t2\thuman-double-adjudicated\tfixture-A+B\tadjudicated\ttest-only\n", encoding="utf-8")
            for freeze in ("F1.json", "F2.json"):
                with self.assertRaisesRegex(SystemExit, "historical_freeze_invalidated"):
                    verify_freezes(str(IMPL / "freezes" / freeze), str(path))

    def test_proxy_exports_cannot_overwrite_historical_dump(self):
        from src.annotations.llm_judge import export_adjudicated_qrels

        for split in ("train", "dev", "test"):
            path = IMPL / f"annotations/qrels/{split}/qrels.tsv"
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "HISTORICAL_PROXY_IMMUTABLE"):
                export_adjudicated_qrels([], [], path)
            self.assertEqual(before, path.read_bytes())

    def test_missing_or_proxy_provenance_rejected_before_output(self):
        for body, expected in (
            ("incident_id\tchunk_id\trelevance_grade\ni\tc\t2\n", "qrels_provenance_missing"),
            ((IMPL / "annotations/qrels/test/qrels.tsv").read_text(encoding="utf-8"), "qrels_not_human_gold"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "qrels.tsv"
                path.write_text(body, encoding="utf-8")
                out = Path(tmp) / "scored.tsv"
                for operation in (
                    lambda: load_qrels(path),
                    lambda: verify_freezes("missing.json", str(path)),
                    lambda: score_runs("missing.json", str(path), "missing.jsonl", str(out)),
                ):
                    with self.assertRaisesRegex(SystemExit, expected):
                        operation()
                self.assertFalse(out.exists())

    def test_blank_grade_is_unjudged_and_invalid_grades_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qrels.tsv"
            header = "incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\n"
            suffix = "\thuman-double-adjudicated\tfixture-A+B\tadjudicated\ttest-only\n"
            path.write_text(header + "i\tjudged\t2" + suffix + "i\tunjudged\t" + suffix, encoding="utf-8")
            self.assertEqual(load_qrels(path), {"i": {"judged": 2}})
            for grade in ("checkoutservice", "3", "1.5", "nan"):
                path.write_text(header + "i\tc\t" + grade + suffix, encoding="utf-8")
                with self.assertRaisesRegex(SystemExit, "qrels_invalid_grade"):
                    load_qrels(path)

    def test_f2_rejects_absent_coverage_and_mislabelled_proxy_receipt(self):
        args = dict(f1_path=IMPL / "freezes/F1.json",
                    test_pool_manifest_path=IMPL / "annotations/pools/test/pool-manifest.json",
                    test_qrels_path=IMPL / "annotations/qrels/test/qrels.tsv",
                    provenance_sidecar_path=IMPL / "freezes/F2.provenance.json")
        with self.assertRaisesRegex(CoverageError, "coverage_info is required"):
            build_f2_freeze(**args)
        with self.assertRaisesRegex(CoverageError, "provenance receipt mismatch"):
            build_f2_freeze(**args, coverage_info={}, provenance="human-double-adjudicated")
        with self.assertRaisesRegex(CoverageError, "proxy qrels cannot"):
            build_f2_freeze(**args, coverage_info={})

    def test_pilot_sample_and_candidates_are_reproducible_without_gold(self):
        spec = importlib.util.spec_from_file_location("readiness_writer", IMPL / "scripts/write_readiness_sidecars.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        train = sorted(row["incident_id"] for row in rows(ROOT / "02_datasets/processed/split-map.tsv") if row["split"] == "train")
        rng = random.Random(221)
        expected = rng.sample(train, 6)
        rng.shuffle(expected)
        actual = [row["incident_id"] for row in rows(IMPL / "annotations/coverage-pilot/candidate-ids.tsv")]
        self.assertEqual(expected, actual)
        observations = {row["incident_id"]: row for row in module.read_jsonl(IMPL / "data/inference/observations.jsonl")}
        candidates = module.pilot_candidates(actual, observations,
            module.read_jsonl(IMPL / "data/knowledge/documents.jsonl"),
            module.read_jsonl(ROOT / "03_collection_plan/knowledge-corpus-historical/proposed-mappings.jsonl"))
        self.assertEqual(candidates, rows(ROOT / "03_collection_plan/annotation-kit/incident-document-candidates.tsv"))
        for incident in actual:
            selected = [row for row in candidates if row["incident_id"] == incident]
            self.assertTrue(0 < len(selected) <= 40)
            self.assertEqual(len(selected), len({row["document_id"] for row in selected}))
        for row in candidates:
            self.assertEqual(row["relevance_grade"], "")
            self.assertEqual(row["is_qrel"], "false")
            self.assertEqual(row["review_state"], "needs_human_review")
        self.assertEqual(rows(IMPL / "annotations/coverage-pilot/judgments.tsv"), [])

    def test_forensic_results_are_ineligible(self):
        results = rows(IMPL / "results/per-incident.tsv")
        self.assertTrue(results)
        for row in results:
            self.assertEqual(row["qrels_provenance"], "llm_lexical_proxy")
            self.assertEqual(row["eligible"], "false")


if __name__ == "__main__":
    unittest.main()
