"""Release packaging rejects placeholders, dirty trees and checksum drift."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.data.common import IMPL, ROOT


class ReleaseIntegrityTests(unittest.TestCase):
    def test_handoff_hash_matches_release_hasher_on_crlf_text(self):
        from src.evaluation.cli_ops import sha256_file as handoff_hash
        sys.path.insert(0, str(ROOT / "scripts"))
        from publication_policy import sha256_file as release_hash
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.tsv"
            path.write_bytes(b"a\r\nb\r\n")
            self.assertEqual(handoff_hash(path), release_hash(path))
            self.assertEqual(handoff_hash(path), hashlib.sha256(b"a\nb\n").hexdigest())
        from src.evaluation.cli_ops import validate_handoff
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "final-manifest.json"
            path.write_text(json.dumps({"handoff": "ready"}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate_handoff(str(path))

    def test_tampered_artifact_hash_is_rejected(self):
        from src.evaluation.cli_ops import sha256_file, validate_handoff
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        sample = IMPL / "docs" / "reproduce.md"
        payload = {
            "code_revision": revision,
            "artifacts": [{
                "path": "docs/reproduce.md",
                "sha256": "0" * 64,
                "license_ref": "MIT",
                "size_bytes": sample.stat().st_size,
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with mock.patch("src.evaluation.cli_ops.git_dirty", return_value=False):
                with self.assertRaises(SystemExit) as caught:
                    validate_handoff(str(path))
            self.assertIn("artifact_mismatch", str(caught.exception))
            self.assertNotEqual(sha256_file(sample), "0" * 64)

    def test_package_release_fails_on_dirty_tree(self):
        import importlib.util
        path = IMPL / "scripts" / "package_release.py"
        spec = importlib.util.spec_from_file_location("package_release", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module, "git_dirty", return_value=True):
            with self.assertRaises(SystemExit) as caught:
                module.package_release()
        self.assertEqual(str(caught.exception), "dirty_worktree")

    def test_package_release_refuses_unrelated_output_directory(self):
        import importlib.util
        path = IMPL / "scripts" / "package_release.py"
        spec = importlib.util.spec_from_file_location("package_release", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "not-a-package"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            with mock.patch.object(module, "git_dirty", return_value=True):
                with self.assertRaises(SystemExit) as dirty:
                    module.package_release(target)
            self.assertEqual(str(dirty.exception), "dirty_worktree")
            with self.assertRaises(SystemExit) as caught:
                module._safe_replace_output(target)
            self.assertEqual(str(caught.exception), "refuse_overwrite_output")
            self.assertTrue((target / "keep.txt").is_file())

    def test_dependency_lock_is_windows_hashed_and_does_not_claim_linux(self):
        lock = (IMPL / "configs/requirements-lock.txt").read_text(encoding="utf-8")
        self.assertIn("--hash=sha256:", lock)
        self.assertIn("Windows", lock)
        self.assertNotIn("linux support", lock.lower())
        recipe = (IMPL / "reports/environment-recipe.md").read_text(encoding="utf-8")
        self.assertIn("Linux", recipe)


if __name__ == "__main__":
    unittest.main()
