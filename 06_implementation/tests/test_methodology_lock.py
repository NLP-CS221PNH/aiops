"""Methodology lock matches pinned configs and F1 conditions."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.evaluation.lock import compare_lock_to_sources, load_lock, lock_file_sha256

IMPL = Path(__file__).resolve().parents[1]


class MethodologyLockTests(unittest.TestCase):
    def test_lock_matches_retrieval_generation_and_f1(self):
        mismatches = compare_lock_to_sources(IMPL)
        self.assertEqual(mismatches, [])

    def test_lock_hash_is_recorded(self):
        digest = lock_file_sha256(IMPL)
        self.assertEqual(len(digest), 64)
        text = (IMPL / "reports" / "methodology-lock.md").read_text(encoding="utf-8")
        self.assertIn(digest, text)

    def test_f1_conditions_are_the_lock_union(self):
        lock = load_lock(IMPL)
        f1 = json.loads((IMPL / "freezes" / "F1.json").read_text(encoding="utf-8"))
        expected = lock["conditions"]["primary_rq2"] + lock["conditions"]["generation"]
        self.assertEqual(f1["selected_conditions"], expected)
        self.assertNotIn("IR-R", f1["selected_conditions"])

    def test_existing_f1_cannot_be_overwritten(self):
        from src.evaluation.freeze import generate_f1_freeze

        with self.assertRaisesRegex(SystemExit, "f1_overwrite_forbidden"):
            generate_f1_freeze(str(IMPL / "configs" / "evaluation.yaml"), str(IMPL / "freezes" / "F1.json"))

    def test_qrels_are_labeled_llm_judge_not_human(self):
        lock = load_lock(IMPL)
        self.assertEqual(lock["qrels_provenance"], "llm_judge_adjudicated")
        self.assertTrue(lock["qrels_not_human_gold"])
        self.assertEqual(lock["qrels_on_disk_label"], "llm_lexical_proxy")


if __name__ == "__main__":
    unittest.main()
