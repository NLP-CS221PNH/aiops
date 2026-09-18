"""Interrupted resume matches an uninterrupted run with the same horizon."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest

from src.training.checkpoint import latest_complete
from src.training.trainer import train_run
from tests.test_training_objective import toy_example


class TrainingResumeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('runs-test-resume')
        if self.root.exists():
            shutil.rmtree(self.root)
        self.examples = [
            toy_example('aaaaaaaaaaaaaaaa', 'cartservice'),
            toy_example('bbbbbbbbbbbbbbbb', 'checkoutservice'),
            toy_example('cccccccccccccccc', 'frontend'),
            toy_example('dddddddddddddddd', 'paymentservice'),
        ]

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    def test_resume_uses_same_total_horizon_not_a_new_plan(self):
        recipe = {
            'lora': {'r': 8, 'lora_alpha': 16, 'lora_dropout': 0.0, 'target_modules': ['q_proj', 'v_proj']},
            'optimizer': {'lr': 1e-3, 'betas': [0.9, 0.999], 'eps': 1e-8, 'weight_decay': 0.0, 'max_grad_norm': 1.0},
            'schedule': {'warmup_ratio': 0.0, 'seed': 221},
            'batching': {'accumulation': 1},
            'namespaces': {'smoke': 'training/smoke', 'research': 'training/research'},
        }
        prefix = train_run(
            self.examples, run_id='resume-shared', mode='full', max_steps=4,
            interrupt_after=2, recipe=recipe, output_root=self.root,
        )
        self.assertEqual(prefix['total_planned_steps'], 4)
        self.assertEqual(prefix['steps'], 2)
        ckpt = latest_complete(Path(prefix['run_dir']))
        self.assertIsNotNone(ckpt)
        resumed = train_run(
            self.examples, run_id='resume-shared', mode='full', max_steps=4,
            resume=str(ckpt), recipe=recipe, output_root=self.root,
        )
        self.assertEqual(resumed['total_planned_steps'], 4)
        self.assertEqual(resumed['steps'], 4)
        uninterrupted = train_run(
            self.examples, run_id='uninterrupted', mode='full', max_steps=4,
            recipe=recipe, output_root=self.root,
        )
        self.assertEqual(resumed['adapter_hash_after'], uninterrupted['adapter_hash_after'])
        self.assertEqual(resumed['base_hash'], uninterrupted['base_hash'])
        self.assertEqual(resumed['final_logits_sha256'], uninterrupted['final_logits_sha256'])

    def test_smoke_checkpoint_is_not_research_latest(self):
        smoke = train_run(
            self.examples, run_id='smoke-ns', mode='smoke', max_steps=2,
            output_root=self.root,
        )
        self.assertTrue(smoke['smoke_only'])
        self.assertIn('smoke', smoke['run_dir'].replace('\\', '/'))


if __name__ == '__main__':
    unittest.main()
