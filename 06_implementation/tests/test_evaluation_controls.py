"""Oracle/random packers, leakage overlap, and mock-generation refusal."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.data.common import ROOT
from src.evaluation.controls import answerability_slice, leakage_overlap, pack_oracle, pack_random
from src.generation.control_driver import run_control_generation

IMPL = Path(__file__).resolve().parents[1]


class EvaluationControlTests(unittest.TestCase):
    def test_oracle_ranks_gold_and_scores_one(self):
        packed = pack_oracle({"c2": 1, "c1": 2, "c0": 0}, k=5)
        self.assertEqual(packed["condition"], "G-oracle")
        self.assertEqual(packed["chunk_ids"], ["c1", "c2"])
        self.assertEqual(packed["retrieval_ndcg5"], 1.0)
        self.assertEqual(packed["generation_status"], "NOT_RUN")

    def test_random_is_seeded_and_avoids_relevant(self):
        qrels = {"gold": 2, "neg1": 0, "neg2": 0, "neg3": 0}
        first = pack_random(qrels, ["gold", "neg1", "neg2", "neg3"], seed=221, k=2)
        second = pack_random(qrels, ["gold", "neg1", "neg2", "neg3"], seed=221, k=2)
        self.assertEqual(first["chunk_ids"], second["chunk_ids"])
        self.assertTrue(first["chunk_ids"])
        self.assertNotIn("gold", first["chunk_ids"])

    def test_leakage_table_does_not_replace_historical_corpus(self):
        hist = ROOT / "03_collection_plan" / "knowledge-corpus-historical" / "documents.jsonl"
        curr = ROOT / "03_collection_plan" / "knowledge-corpus" / "documents.jsonl"
        result = leakage_overlap(hist, curr)
        self.assertEqual(result["historical_documents"], 74)
        self.assertEqual(result["current_documents"], 73)
        self.assertEqual(result["ir_h_ndcg5_delta"], "NOT_RUN")
        self.assertEqual(result["status"], "diagnostic_only")

    def test_answerability_without_labels_is_not_run(self):
        self.assertEqual(answerability_slice(["inc_a"], {})["status"], "NOT_RUN")

    def test_pending_generation_is_not_run(self):
        packed = pack_oracle({"c1": 2})
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "generation.yaml"
            config.write_text("permissions:\n  api: pending\napproved_cap_usd: null\n", encoding="utf-8")
            result = run_control_generation(packed, "inc_a", str(config))
        self.assertEqual(result["generation_status"], "NOT_RUN")

    def test_mock_success_is_refused(self):
        packed = pack_oracle({"c1": 2})
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "generation.yaml"
            config.write_text(
                "permissions:\n  api: approved\n  local: pending\napproved_cap_usd: 10\nprovider:\n  model: deepseek-flash\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "refusing_mock_as_result"):
                run_control_generation(packed, "inc_a", str(config))

    def test_primary_rq2_excludes_controls(self):
        evaluation = Path(IMPL / "configs" / "evaluation.yaml").read_text(encoding="utf-8")
        self.assertIn("G-oracle", evaluation)
        self.assertIn("primary_rq2", evaluation)
        f1 = json.loads((IMPL / "freezes" / "F1.json").read_text(encoding="utf-8"))
        self.assertEqual(f1["selected_conditions"], ["IR-B", "IR-D", "IR-H", "G0", "GB", "GD", "GH"])
        self.assertNotIn("G-oracle", f1["selected_conditions"])
        self.assertNotIn("IR-R", f1["selected_conditions"])


if __name__ == "__main__":
    unittest.main()
