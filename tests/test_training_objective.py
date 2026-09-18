"""Target-only labels, frozen base, real adapter updates."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.training.adapters import adapter_hash, base_hash, frozen_base_ok
from src.training.collator import ByteTokenizer, tokenize_example
from src.training.trainer import build_model, train_run

IMPL = Path(__file__).resolve().parents[1]


def toy_example(suffix='aaaaaaaaaaaaaaaa', service='cartservice'):
    return {
        'example_id': f'ex_{suffix}_g1_service_g0_r2',
        'incident_id': f'inc_{suffix}',
        'input_messages': [
            {'role': 'system', 'content': 'You are a local service-localization assistant.'},
            {'role': 'user', 'content': 'checkout latency 99 cpu cartservice'},
        ],
        'target_text': json.dumps({'candidate_causes': [{'service_id': service}]}, separators=(',', ':')),
        'safe_input_sha256': 'a' * 64,
        'g1_source_sha256': 'b' * 64,
        'split_sha256': 'c' * 64,
        'label_revision': 'test',
        'target_kind': 'g1_service',
    }


class TrainingObjectiveTests(unittest.TestCase):
    def test_prompt_tokens_are_masked_and_target_keeps_ids(self):
        tokenizer = ByteTokenizer()
        example = toy_example()
        row = tokenize_example(example, tokenizer, max_train_tokens=2048, prompt_cap=1024, target_reserve=256)
        self.assertTrue(all(label == -100 for label in row['labels'][:row['prompt_length']]))
        self.assertEqual(row['labels'][row['prompt_length']:], row['input_ids'][row['prompt_length']:])
        self.assertNotIn(-100, row['labels'][row['prompt_length']:])
        self.assertEqual(row['input_ids'][-1], tokenizer.eos_token_id)
        decoded_target = tokenizer.decode(row['input_ids'][row['prompt_length']:-1])
        self.assertIn('cartservice', decoded_target)
        self.assertNotIn('inc_', row['prompt_text'])

    def test_empty_target_is_rejected(self):
        example = toy_example()
        example['target_text'] = '   '
        with self.assertRaises(Exception) as caught:
            tokenize_example(example, ByteTokenizer())
        self.assertEqual(caught.exception.code, 'TARGET_EMPTY')

    def setUp(self):
        self.workdir = Path('runs-test-objective')
        if self.workdir.exists():
            import shutil
            shutil.rmtree(self.workdir)

    def tearDown(self):
        import shutil
        if self.workdir.exists():
            shutil.rmtree(self.workdir, ignore_errors=True)

    def test_adapter_changes_and_base_stays_frozen(self):
        example = toy_example()
        receipt = train_run(
            [example, toy_example('bbbbbbbbbbbbbbbb', 'checkoutservice')],
            run_id='objective-smoke',
            mode='smoke',
            max_steps=2,
            output_root=self.workdir,
        )
        self.assertTrue(receipt['tiny_training_mechanics_verified'])
        self.assertFalse(receipt['full_training_run_completed'])
        self.assertNotEqual(receipt['adapter_hash_before'], receipt['adapter_hash_after'])
        self.assertTrue(all(value == value for value in receipt['losses']))
        self.assertTrue(any(norm > 0 for norm in receipt['grad_norms']))
        model = build_model(258, {})
        self.assertTrue(frozen_base_ok(model))
        self.assertEqual(len(receipt['losses']), 2)
        self.assertEqual(receipt['model_kind'], 'tiny')

    def test_full_mode_without_qwen_assets_fails_closed(self):
        from src.data.common import DataContractError
        with self.assertRaises(DataContractError) as caught:
            train_run(
                [toy_example()],
                run_id='full-missing',
                mode='full',
                max_steps=1,
                output_root=self.workdir,
                require_qwen=True,
            )
        self.assertEqual(caught.exception.code, 'MISSING_INPUT')


if __name__ == '__main__':
    unittest.main()
