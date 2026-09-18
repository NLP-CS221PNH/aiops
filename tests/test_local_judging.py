"""Local judging: no G1, blinded pool, unjudged is not grade 0."""
from __future__ import annotations

import unittest

from src.annotations.build_pool import build_pool
from src.annotations.local_judge import judge_answerability, judge_g2, judge_g3
from src.data.common import DataContractError


class FakeJudge:
    def __init__(self, raw: str, status='success'):
        self.raw = raw
        self.status = status

    def generate(self, messages, context, config):
        blob = ' '.join(item['content'] for item in messages)
        if 'root_cause_service' in blob or 'checkoutservice' in blob and 'Observation' not in blob:
            raise AssertionError('g1 leaked into judge prompt')
        return self.raw, {'status': self.status}


class LocalJudgingTests(unittest.TestCase):
    def test_g2_missing_model_is_unjudged_not_zero(self):
        result = judge_g2('cpu high', {'chunk_id': 'c1', 'text': 'throttle docs'})
        self.assertEqual(result['status'], 'unjudged')
        self.assertIsNone(result['grade'])
        self.assertEqual(result['provenance'], 'local-model-automated-v1')

    def test_g2_rejects_g1_fields(self):
        with self.assertRaises(DataContractError):
            judge_g2('obs', {'chunk_id': 'c1', 'text': 'x', 'root_cause_service': 'cartservice'})

    def test_g3_support_uses_packed_text_not_id_only(self):
        claims = [{'claim_id': 'cl1', 'text': 'cpu throttling on worker'}]
        result = judge_g3(claims, 'the packed context mentions cpu throttling on worker')
        self.assertEqual(result['judgments'][0]['label'], 'support')
        empty = judge_g3(claims, 'unrelated network loss')
        self.assertEqual(empty['judgments'][0]['label'], 'insufficient')

    def test_g3_wrong_text_same_id_is_not_support(self):
        claims = [{'claim_id': 'same', 'text': 'disk full'}]
        result = judge_g3(claims, 'cpu throttling evidence')
        self.assertNotEqual(result['judgments'][0]['label'], 'support')

    def test_answerability_does_not_use_empty_pool_as_unanswerable(self):
        result = judge_answerability('observations show cartservice 5xx')
        self.assertNotEqual(result['label'], 'unanswerable')

    def test_pool_shuffle_is_seeded_and_blind(self):
        runs = [
            {'incident_id': 'inc_aaaaaaaaaaaaaaaa', 'ranking': ['a', 'b', 'c'], 'retriever': 'IR-H', 'scores': [0.9, 0.8, 0.1]},
            {'incident_id': 'inc_aaaaaaaaaaaaaaaa', 'ranking': ['c', 'd'], 'retriever': 'IR-B', 'scores': [0.7, 0.2]},
        ]
        first = build_pool(runs, depth=10, seed=221)
        second = build_pool(runs, depth=10, seed=221)
        self.assertEqual(first['candidates'], second['candidates'])
        self.assertGreaterEqual(first['n'], 4)
        for row in first['candidates']:
            self.assertNotIn('rank', row)
            self.assertNotIn('score', row)
            self.assertNotIn('retriever', row)

    def test_provider_success_records_raw(self):
        result = judge_g2('obs', {'chunk_id': 'c1', 'text': 'docs'}, provider=FakeJudge('2'))
        self.assertEqual(result['grade'], 2)
        self.assertEqual(result['raw_response'], '2')


if __name__ == '__main__':
    unittest.main()
