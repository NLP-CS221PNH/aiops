"""Exact public_git_files + denylist. No git inside a ZIP extract."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from src.data.common import IMPL

_SPEC = importlib.util.spec_from_file_location(
    "validate_public_source_tree",
    IMPL / "scripts" / "validate-public-source-tree.py",
)
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

_CONFIG = IMPL / "configs" / "kaggle.yaml"


class PublicSourceTreeTests(unittest.TestCase):
    def setUp(self):
        self.expected, self.denylist = _MOD.load_lists(_CONFIG)

    def test_exact_match_is_ok(self):
        result = _MOD.compare(sorted(self.expected), self.expected, self.denylist)
        self.assertTrue(result["ok"])
        self.assertEqual(result["extra"], [])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["denied"], [])

    def test_extra_file_fails(self):
        tracked = list(self.expected) + ["00_plan/secret.md"]
        result = _MOD.compare(tracked, self.expected, self.denylist)
        self.assertFalse(result["ok"])
        self.assertIn("00_plan/secret.md", result["extra"])

    def test_denylist_ground_truth_fails(self):
        leak = "data/training-inputs/v1/private-train/ground_truth.jsonl"
        tracked = list(self.expected) + [leak]
        result = _MOD.compare(tracked, self.expected | {leak}, self.denylist)
        self.assertFalse(result["ok"])
        self.assertIn(leak, result["denied"])

    def test_files_from_skips_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "files.txt"
            listing.write_text("\n".join(sorted(self.expected)) + "\n", encoding="utf-8")
            code = _MOD.main(["--files-from", str(listing)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
