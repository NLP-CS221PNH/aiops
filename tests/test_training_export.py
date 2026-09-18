"""Adapter export/reload and smoke-only marking."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest

from src.training.export import export_adapter, verify_export
from src.training.trainer import train_run
from tests.test_training_objective import toy_example


class TrainingExportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('runs-test-export')
        if self.root.exists():
            shutil.rmtree(self.root)
        self.example = toy_example()

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    def test_export_reload_and_smoke_flag(self):
        receipt = train_run(
            [self.example, toy_example('bbbbbbbbbbbbbbbb')],
            run_id='export-smoke', mode='smoke', max_steps=2,
            output_root=self.root,
        )
        export_dir = self.root / 'export'
        manifest = export_adapter(Path(receipt['run_dir']), export_dir)
        self.assertTrue(manifest['smoke_only'])
        self.assertTrue((export_dir / manifest['weights']).is_file())
        verified = verify_export(export_dir, self.example)
        self.assertEqual(verified['status'], 'pass')
        self.assertTrue(verified['smoke_only'])
        self.assertEqual(verified['adapter_hash'], receipt['adapter_hash_after'])
        self.assertEqual(manifest['base_model']['kind'], 'tiny')
        self.assertNotEqual(manifest['base_model']['id'], 'Qwen/Qwen2.5-1.5B-Instruct')


if __name__ == '__main__':
    unittest.main()
