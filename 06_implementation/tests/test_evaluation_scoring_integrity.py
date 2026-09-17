"""Scoring integrity: no metric literals in writers, bootstrap, undefined policy."""
from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from src.evaluation.bootstrap import family_clustered_mean_ci, paired_delta_ci
from src.evaluation.lock import load_lock
from src.evaluation.metrics import Status, calculate_ndcg
from src.evaluation.scoring import eligible_mean, score_ranking
from src.evaluation.tables import write_headline_tables
from src.evaluation.experimental_qrels import load_experimental_qrels

IMPL = Path(__file__).resolve().parents[1]
FORBIDDEN_LITERALS = ("0.642", "0.671", "[+0.009, +0.075]")
WRITERS = [
    IMPL / "scripts" / "execute_evaluation.py",
    IMPL / "src" / "evaluation" / "tables.py",
    IMPL / "src" / "evaluation" / "cli_ops.py",
]


class ScoringIntegrityTests(unittest.TestCase):
    def test_writers_have_no_pasted_metric_literals(self):
        for path in WRITERS:
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_LITERALS:
                self.assertNotIn(token, text, msg=path)

    def test_undefined_empty_and_unjudged(self):
        self.assertEqual(calculate_ndcg(["d1"], {"d2": 0}, k=5).status, Status.UNDEFINED)
        empty = calculate_ndcg([], {"d1": 1}, k=5)
        self.assertEqual(empty.status, Status.ELIGIBLE)
        self.assertEqual(empty.value, 0.0)
        unjudged = calculate_ndcg(["d1", "missing"], {"d1": 2}, k=5)
        self.assertEqual(unjudged.status, Status.UNDEFINED)

    def test_family_bootstrap_is_seeded_and_paired(self):
        lock = load_lock(IMPL)
        seed = lock["bootstrap"]["seed"]
        resamples = lock["bootstrap"]["resamples"]
        treatment = {"fam_a": [0.4, 0.6], "fam_b": [0.2]}
        baseline = {"fam_a": [0.3, 0.5], "fam_b": [0.1]}
        first = paired_delta_ci(treatment, baseline, seed=seed, resamples=resamples)
        second = paired_delta_ci(treatment, baseline, seed=seed, resamples=resamples)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first["mean"], 0.1, places=8)
        self.assertLess(first["low"], first["high"])

    def test_scorer_means_repeat_within_tolerance(self):
        ranking = ["doc1", "doc2"]
        qrels = {"doc1": 2, "doc2": 1, "doc3": 0}
        first = score_ranking(ranking, qrels)["passage_ndcg_5"].value
        second = score_ranking(ranking, qrels)["passage_ndcg_5"].value
        self.assertLessEqual(abs(first - second), 1e-8)
        mean = eligible_mean([score_ranking(ranking, qrels)["passage_ndcg_5"]] * 2)
        self.assertEqual(mean.status, Status.ELIGIBLE)
        self.assertTrue(math.isclose(mean.value, first))

    def test_experimental_qrels_keep_llm_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qrels.tsv"
            path.write_text(
                "incident_id\tchunk_id\trelevance_grade\tprovenance\tannotator_id\tadjudication_state\tannotation_version\n"
                "inc1\tdoc1\t1\tllm_lexical_proxy\tjudge-A\tadjudicated\ttest-only\n",
                encoding="utf-8",
            )
            tables, provenance = load_experimental_qrels(path)
            self.assertEqual(provenance, "llm_lexical_proxy")
            self.assertEqual(tables["inc1"]["doc1"], 1)

    def test_headline_tables_are_not_run_and_captioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            impl = Path(tmp)
            (impl / "configs").mkdir()
            (impl / "reports" / "final-tables").mkdir(parents=True)
            (impl / "configs" / "methodology-lock.yaml").write_bytes(
                (IMPL / "configs" / "methodology-lock.yaml").read_bytes()
            )
            write_headline_tables(impl)
            table = (impl / "reports" / "final-tables" / "table1-retrieval-performance.tsv").read_text(encoding="utf-8")
            self.assertIn("IR-B (BM25)", table)
            self.assertIn("NOT_RUN", table)
            self.assertNotIn("IR-R", table)
            markdown = (impl / "reports" / "final-tables" / "table1-retrieval-performance.md").read_text(encoding="utf-8")
            self.assertIn("llm_judge_adjudicated", markdown)
            self.assertIn("Not human gold", markdown)
            table3 = (impl / "reports" / "final-tables" / "table3-six-family-diagnostics.tsv").read_text(encoding="utf-8")
            table4 = (impl / "reports" / "final-tables" / "table4-resource-accounting.tsv").read_text(encoding="utf-8")
            self.assertIn("NOT_RUN", table3)
            self.assertIn("NOT_RUN", table4)
            self.assertNotIn("1.000", table3)
            self.assertNotIn("497138", table4)


if __name__ == "__main__":
    unittest.main()
