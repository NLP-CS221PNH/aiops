"""Delivery ZIP, checksums, and trainer isolation from the packaged test root."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
import subprocess
import sys
import unittest

from src.data.common import IMPL


class KagglePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = IMPL / "artifacts" / "kaggle-delivery" / "test-package"
        if cls.out.exists():
            shutil.rmtree(cls.out)
        cls.out.mkdir(parents=True, exist_ok=True)

        build = subprocess.run(
            [sys.executable, str(IMPL / 'scripts' / 'build-bilingual-reports.py'),
             '--contract', str(IMPL / 'configs' / 'report-contract.json'),
             '--blank-results', '--output', str(cls.out)],
            cwd=IMPL, capture_output=True, text=True,
        )
        if build.returncode != 0:
            raise AssertionError(build.stderr or build.stdout)
        packed = subprocess.run(
            [sys.executable, str(IMPL / 'scripts' / 'package-kaggle-source.py'),
             '--config', str(IMPL / 'configs' / 'kaggle.yaml'),
             '--output', str(cls.out)],
            cwd=IMPL, capture_output=True, text=True,
        )
        if packed.returncode != 0:
            raise AssertionError(packed.stderr or packed.stdout)

    def test_two_docx_and_zip_exist(self):
        self.assertTrue((self.out / 'aiops-kaggle-source.zip').is_file())
        self.assertTrue((self.out / 'aiops-report-vi.docx').is_file())
        self.assertTrue((self.out / 'aiops-report-en.docx').is_file())
        self.assertTrue((self.out / 'delivery-manifest.json').is_file())
        manifest = json.loads((self.out / 'delivery-manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(manifest['self_manifest_sha256_excluded'])
        self.assertNotIn('self_sha256', manifest)
        self.assertTrue(manifest['code_revision'])
        self.assertEqual(len(manifest['source_tree_sha256']), 64)
        self.assertEqual(manifest['plan_ref'], 'plans/260917-1948-kaggle-source-bilingual-reports')
        self.assertFalse(manifest['checks']['full_training_run_completed'])
        self.assertFalse(manifest['checks']['kaggle_execution_verified'])
        self.assertTrue(manifest['checks']['results_intentionally_blank'])

    def test_zip_has_no_git_or_venv(self):
        with zipfile.ZipFile(self.out / 'aiops-kaggle-source.zip') as archive:
            names = archive.namelist()
        self.assertTrue(any(name.startswith('src/training/') for name in names))
        self.assertTrue(any(name.endswith('03_kaggle_train.ipynb') for name in names))
        self.assertFalse(any('.git/' in name or name.startswith('.venv/') for name in names))
        self.assertFalse(any(name.endswith('.env') for name in names))
        self.assertFalse(any(name.startswith('00_plan/') for name in names))
        self.assertFalse(any(name.startswith('data/training-inputs/') for name in names))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_validate_checksums(self):
        receipt_path = self.out / 'validation-receipt.json'
        manifest_before = json.loads((self.out / 'delivery-manifest.json').read_text(encoding='utf-8'))
        receipt_before = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.is_file() else None
        result = subprocess.run(
            [sys.executable, str(IMPL / 'scripts' / 'validate-kaggle-delivery.py'),
             '--manifest', str(self.out / 'delivery-manifest.json')],
            cwd=IMPL, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload.get('clean_extract'))
        manifest_after = json.loads((self.out / 'delivery-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(
            manifest_before['checks']['source_validated'],
            manifest_after['checks']['source_validated'],
        )
        if receipt_before is not None:
            receipt_after = json.loads(receipt_path.read_text(encoding='utf-8'))
            self.assertEqual(receipt_before.get('source_validated'), receipt_after.get('source_validated'))
            self.assertEqual(receipt_before.get('clean_extract'), receipt_after.get('clean_extract'))

    def test_clean_extract_sets_source_validated(self):
        result = subprocess.run(
            [sys.executable, str(IMPL / 'scripts' / 'validate-kaggle-delivery.py'),
             '--manifest', str(self.out / 'delivery-manifest.json'),
             '--clean-extract'],
            cwd=IMPL, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads((self.out / 'validation-receipt.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['source_validated'])
        manifest = json.loads((self.out / 'delivery-manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(manifest['checks']['source_validated'])
        self.assertFalse(manifest['checks']['kaggle_execution_verified'])
        self.assertFalse(manifest['checks']['full_training_run_completed'])

    def test_trainer_help_in_package_contract(self):
        result = subprocess.run(
            [sys.executable, '-m', 'src.training', '--help'],
            cwd=IMPL, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('preflight', result.stdout)
        self.assertIn('train', result.stdout)


if __name__ == '__main__':
    unittest.main()
