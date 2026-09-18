"""Blank-result bilingual reports: exact team strings and empty metric cells."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
import unittest

from src.data.common import IMPL

CONTRACT = IMPL / "configs" / "report-contract.json"


class ReportContractTests(unittest.TestCase):
    def test_contract_team_and_pins(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        names = [(row["name"], row["student_id"]) for row in contract["team"]]
        self.assertEqual(names, [
            ("Nguyễn Văn Nam", "24521120"),
            ("Nguyễn Đình Phát", "23521144"),
            ("Lê Vũ Thiêm Hoàng", "25520584"),
            ("Bùi Đặng Nhật Nguyên", "23521037"),
        ])
        self.assertTrue(contract["blank_results"])
        self.assertEqual(contract["model"]["generator_revision"], "989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
        self.assertTrue(contract["model"]["e5_pretrained"])

    def test_markdown_result_cells_are_empty(self):
        forbidden = {"0", "-", "100%", "NOT_RUN"}
        for lang in ("vi", "en"):
            text = (IMPL / "docs" / f"report-{lang}.md").read_text(encoding="utf-8")
            self.assertIn("Nguyễn Văn Nam", text)
            in_table = False
            for line in text.splitlines():
                if line.startswith("| method") or line.startswith("| row") or line.startswith("| metric"):
                    in_table = True
                    continue
                if in_table and line.startswith("|"):
                    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                    if set("".join(cells)) <= set("-: "):
                        continue
                    for cell in cells[1:]:
                        self.assertNotIn(cell, forbidden)
                        self.assertEqual(cell, "")
                elif in_table and not line.startswith("|"):
                    in_table = False

    def test_built_docx_xml(self):
        import shutil
        import subprocess
        import sys
        out = IMPL / "artifacts" / "kaggle-delivery" / "test-docx"
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                [sys.executable, str(IMPL / "scripts" / "build-bilingual-reports.py"),
                 "--contract", str(CONTRACT), "--blank-results", "--output", str(out)],
                cwd=IMPL, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((out / "docx-layout-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["n_docx"], 2)
            self.assertTrue(receipt["results_intentionally_blank"])
            for name in ("aiops-report-vi.docx", "aiops-report-en.docx"):
                path = out / name
                self.assertTrue(path.is_file())
                with zipfile.ZipFile(path) as archive:
                    xml = archive.read("word/document.xml").decode("utf-8")
                contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
                for member in contract["team"]:
                    self.assertIn(member["name"], xml)
                    self.assertIn(member["student_id"], xml)
                self.assertIn("TOC", xml)
                self.assertNotIn(">NOT_RUN</w:t>", xml)
                self.assertNotIn(">100%</w:t>", xml)
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
