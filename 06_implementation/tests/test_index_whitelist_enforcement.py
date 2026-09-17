"""Released index is empty; bypass scripts must stay named."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

IMPL = Path(__file__).resolve().parents[1]


class IndexWhitelistEnforcement(unittest.TestCase):
    def test_released_whitelist_empty(self):
        manifest = json.loads((IMPL / "data" / "knowledge" / "corpus-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("index_whitelist"), [])
        self.assertEqual(manifest["counts"]["allowed_documents"], 0)
        self.assertEqual(manifest["counts"]["indexed_documents"], 0)

    def test_legacy_entrypoints_fail_before_writing_or_indexing(self):
        import hashlib
        import subprocess
        import sys

        paths = [IMPL / "freezes/F1.json", IMPL / "freezes/F2.json", IMPL / "results/per-incident.tsv"]
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        for script in ("generate_test_pool_and_qrels.py", "execute_evaluation.py"):
            result = subprocess.run([sys.executable, str(IMPL / "scripts" / script)],
                                    cwd=IMPL, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CORPUS_RELEASE_PENDING", result.stderr)
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        self.assertEqual(before, after)

    def test_schema_lists_every_on_disk_key(self):
        schema = (IMPL / "docs" / "knowledge-corpus-schema.md").read_text(encoding="utf-8")
        doc_keys = set()
        chunk_keys = set()
        with (IMPL / "data" / "knowledge" / "documents.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    doc_keys.update(json.loads(line).keys())
        with (IMPL / "data" / "knowledge" / "chunks.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    chunk_keys.update(json.loads(line).keys())
        missing_docs = [key for key in sorted(doc_keys) if f"`{key}`" not in schema]
        missing_chunks = [key for key in sorted(chunk_keys) if f"`{key}`" not in schema]
        self.assertEqual(missing_docs, [])
        self.assertEqual(missing_chunks, [])


if __name__ == "__main__":
    unittest.main()
