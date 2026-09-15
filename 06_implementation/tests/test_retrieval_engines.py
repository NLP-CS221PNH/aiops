"""Independent synthetic scoring checks; no real incidents, qrels, or E5 output."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

from src.retrieval.bm25 import BM25
from src.retrieval.dense import DenseIndex, E5Encoder, prepare_e5_batch
from src.retrieval.fusion import rrf
from src.retrieval.rerank import BGEReranker, prepare_reranker_batch


FIXTURES = Path(__file__).parent / 'fixtures' / 'retrieval'


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def chunk(identifier, content='alpha'):
    return {'chunk_id': identifier, 'document_id': 'doc-' + identifier,
            'content': content}


def hit(identifier, rank=1, score=1.0):
    return {'chunk_id': identifier, 'document_id': 'doc-' + identifier,
            'rank': rank, 'score': score}


class BM25Tests(unittest.TestCase):
    def setUp(self):
        self.example = fixture('bm25-hand.json')
        self.index = BM25(self.example['chunks'], **self.example['parameters'])

    def test_hand_calculated_scores_ranks_and_document_ids(self):
        rows = self.index.search(self.example['query'])
        self.assertEqual(len(rows), len(self.example['expected']))
        for actual, expected in zip(rows, self.example['expected']):
            self.assertEqual(actual['chunk_id'], expected['chunk_id'])
            self.assertEqual(actual['document_id'], 'doc-' + expected['chunk_id'])
            self.assertEqual(actual['rank'], expected['rank'])
            self.assertAlmostEqual(actual['score'], expected['score'],
                                   delta=self.example['absolute_tolerance'])

    def test_nondefault_parameters_have_independent_expected_score(self):
        rows = BM25(self.example['chunks'], k1=2, b=0).search('alpha')
        self.assertEqual([r['chunk_id'] for r in rows], ['A', 'B'])
        self.assertAlmostEqual(rows[0]['score'], math.log(2) * 6 / 4, delta=1e-12)
        self.assertAlmostEqual(rows[1]['score'], math.log(2), delta=1e-12)

    def test_repeated_query_terms_do_not_multiply_scores(self):
        self.assertEqual(self.index.search('alpha beta'),
                         self.index.search('ALPHA alpha beta beta'))

    def test_empty_corpus_empty_query_stopwords_and_zero_overlap(self):
        self.assertEqual(BM25([]).search('alpha'), [])
        for query in ('', '  ', 'the and is', 'notinthecorpus'):
            with self.subTest(query=query):
                self.assertEqual(self.index.search(query), [])
        self.assertEqual(BM25([chunk('A', '')]).search('alpha'), [])

    def test_equal_scores_order_by_chunk_id_and_depth_does_not_pad(self):
        index = BM25([chunk('z'), chunk('a'), chunk('m')])
        rows = index.search('alpha', depth=50)
        self.assertEqual([r['chunk_id'] for r in rows], ['a', 'm', 'z'])
        self.assertEqual([r['rank'] for r in rows], [1, 2, 3])
        self.assertEqual(index.search('alpha', depth=1), rows[:1])

    def test_technical_exact_token_and_components_preserved(self):
        # Full java.net.ConnectException adds a match beyond the three components.
        index = BM25([chunk('A', 'java.net.ConnectException'),
                      chunk('B', 'java net ConnectException')])
        self.assertEqual(index.search('JAVA.NET.CONNECTEXCEPTION')[0]['chunk_id'], 'A')
        for term in ('java', 'net', 'connectexception'):
            with self.subTest(term=term):
                self.assertEqual({r['chunk_id'] for r in index.search(term)}, {'A', 'B'})
        tokens = BM25([chunk('tech', 'HTTP/503 v1.2.3 checkout-service api:8080')])
        for term in ('HTTP/503', '503', 'v1.2.3', 'checkout-service', 'checkout', 'api:8080', '8080'):
            with self.subTest(term=term):
                self.assertEqual([r['chunk_id'] for r in tokens.search(term)], ['tech'])

    def test_duplicate_chunk_ids_rejected_before_scoring(self):
        with self.assertRaises(ValueError):
            BM25([chunk('same'), chunk('same', 'beta')])

    def test_content_policy_rejects_mismatch_and_does_not_index_metadata(self):
        row = dict(chunk('A', 'heading\nalpha'), section_heading='heading', text='alpha',
                   source_url='https://synthetic.invalid/metadata-only-token')
        self.assertEqual(BM25([row]).search('metadata-only-token'), [])
        self.assertEqual(BM25([row]).search('heading')[0]['chunk_id'], 'A')
        row['content'] = 'different body'
        with self.assertRaisesRegex(ValueError, 'content disagrees'):
            BM25([row])

    def test_invalid_parameters_rejected(self):
        for parameters in ({'k1': -1}, {'k1': float('nan')}, {'k1': float('inf')},
                           {'b': -0.01}, {'b': 1.01}, {'b': float('nan')}):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                BM25(self.example['chunks'], **parameters)

    def test_invalid_depth_rejected(self):
        self.assertEqual(self.index.search('alpha', depth=0), [])
        for depth in (-1, 1.5, True):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                self.index.search('alpha', depth=depth)


class RRFTests(unittest.TestCase):
    def setUp(self):
        self.example = fixture('rrf-hand.json')

    def test_hand_calculated_scores_missing_branch_and_document_ids(self):
        rows = rrf(self.example['rankings'], constant=self.example['constant'])
        self.assertEqual(len(rows), len(self.example['expected']))
        for actual, expected in zip(rows, self.example['expected']):
            self.assertEqual(actual['chunk_id'], expected['chunk_id'])
            self.assertEqual(actual['document_id'], 'doc-' + expected['chunk_id'])
            self.assertEqual(actual['rank'], expected['rank'])
            self.assertAlmostEqual(actual['score'], expected['score'],
                                   delta=self.example['absolute_tolerance'])

    def test_raw_scores_never_contribute_to_rrf(self):
        rankings = copy.deepcopy(self.example['rankings'])
        for branch in rankings:
            for item in branch:
                item['score'] = -123456789.0
        self.assertEqual(rrf(rankings), rrf(self.example['rankings']))

    def test_weighted_rrf_uses_each_declared_rank(self):
        rows = rrf(self.example['rankings'], weights=[2, 1])
        expected = {'A': 2 / 61 + 1 / 63, 'B': 3 / 62, 'C': 2 / 63, 'D': 1 / 61}
        self.assertEqual([r['chunk_id'] for r in rows], ['A', 'B', 'C', 'D'])
        for row in rows:
            self.assertAlmostEqual(row['score'], expected[row['chunk_id']], delta=1e-14)

    def test_empty_short_and_tied_rankings(self):
        self.assertEqual(rrf([[], []]), [])
        rows = rrf([[hit('z')], [hit('a')]], depth=50)
        self.assertEqual([r['chunk_id'] for r in rows], ['a', 'z'])
        self.assertEqual([r['rank'] for r in rows], [1, 2])
        self.assertEqual(rrf([[hit('z')], [hit('a')]], depth=1), rows[:1])
        self.assertAlmostEqual(rrf([[], [hit('a')]])[0]['score'], 1 / 61, delta=1e-14)

    def test_duplicate_ids_and_duplicate_ranks_within_branch_rejected(self):
        invalid = ([[hit('a'), hit('a', 2)]],
                   [[hit('a'), hit('b', 1)]])
        for rankings in invalid:
            with self.subTest(rankings=rankings), self.assertRaises(ValueError):
                rrf(rankings)

    def test_same_chunk_cannot_have_conflicting_document_identity(self):
        changed = hit('a')
        changed['document_id'] = 'different-document'
        with self.assertRaises(ValueError):
            rrf([[hit('a')], [changed]])

    def test_invalid_rank_constant_weights_and_depth_rejected(self):
        for rank in (0, -1, 1.5, True):
            with self.subTest(rank=rank), self.assertRaises(ValueError):
                rrf([[hit('a', rank=rank)]])
        for kwargs in ({'constant': -1}, {'constant': float('nan')},
                       {'constant': float('inf')}, {'weights': [1]},
                       {'weights': [1, -1]}, {'weights': [1, float('nan')]},
                       {'depth': -1}, {'depth': 1.5}, {'depth': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rrf(self.example['rankings'], **kwargs)
        self.assertEqual(rrf(self.example['rankings'], depth=0), [])


class DenseIndexTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [chunk('A'), chunk('B'), chunk('C'), chunk('D')]
        self.embeddings = [[1, 0], [0, 1], [-1, 0], [0.6, 0.8]]
        self.index = DenseIndex(self.chunks, self.embeddings)

    def test_exact_cosines_include_zero_and_negative_hits(self):
        rows = self.index.search([1, 0], depth=50)
        self.assertEqual([r['chunk_id'] for r in rows], ['A', 'D', 'B', 'C'])
        self.assertEqual([r['rank'] for r in rows], [1, 2, 3, 4])
        for row, score in zip(rows, [1, 0.6, 0, -1]):
            self.assertEqual(row['document_id'], 'doc-' + row['chunk_id'])
            self.assertAlmostEqual(row['score'], score, delta=1e-6)
        self.assertEqual(self.index.search([1, 0], depth=2), rows[:2])

    def test_ties_resolve_by_chunk_id(self):
        rows = DenseIndex([chunk('z'), chunk('a')], [[1, 0], [1, 0]]).search([1, 0])
        self.assertEqual([r['chunk_id'] for r in rows], ['a', 'z'])

    def test_cosines_are_scale_invariant_without_overflow_or_underflow(self):
        rows = self.index.search([3, 4])
        self.assertEqual([r['chunk_id'] for r in rows], ['D', 'B', 'A', 'C'])
        for row, score in zip(rows, [1, 0.8, 0.6, -0.6]):
            self.assertAlmostEqual(row['score'], score, delta=1e-6)
        huge = DenseIndex([chunk('A')], [[1e308, 1e308]])
        tiny = DenseIndex([chunk('A')], [[1e-308, 1e-308]])
        self.assertAlmostEqual(huge.search([1e308, 1e308])[0]['score'], 1, delta=1e-6)
        self.assertAlmostEqual(tiny.search([1e-308, 1e-308])[0]['score'], 1, delta=1e-6)

    def test_empty_index_returns_no_synthetic_evidence(self):
        import numpy as np
        # Keep the encoder's known dimension even when no corpus rows exist.
        self.assertEqual(DenseIndex([], np.empty((0, 2))).search([1, 0]), [])

    def test_nonfinite_zero_ragged_and_wrong_row_count_embeddings_rejected(self):
        invalid = ([[1, 0]], [[1, 0], [0, 1], [1, 0], [float('nan'), 0]],
                   [[1, 0], [0, 1], [1, 0], [0, float('inf')]],
                   [[1, 0], [0, 1], [1, 0], [0, 0]],
                   [[1, 0], [0, 1], [1, 0], [1, 0, 0]])
        for embeddings in invalid:
            with self.subTest(embeddings=embeddings), self.assertRaises(ValueError):
                DenseIndex(self.chunks, embeddings)

    def test_invalid_query_dimensions_and_nonfinite_values_rejected(self):
        for query in ([], [1], [1, 0, 0], [0, 0], [float('nan'), 0],
                      [0, float('inf')], [[1, 0]]):
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.index.search(query)

    def test_duplicate_chunk_ids_rejected(self):
        with self.assertRaises(ValueError):
            DenseIndex([chunk('same'), chunk('same')], [[1, 0], [0, 1]])

    def test_invalid_depth_rejected(self):
        self.assertEqual(self.index.search([1, 0], depth=0), [])
        for depth in (-1, 1.5, True):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                self.index.search([1, 0], depth=depth)


class RealBatch(dict):
    def __init__(self, fields, rows):
        super().__init__(fields)
        self.rows = rows

    def sequence_ids(self, index):
        return self.rows[index].sequence_ids


class RealTokenizerAdapter:
    """HF-shaped calls backed by the real pinned Rust tokenizer, without weights.

    This tests budget accounting, not Transformers integration or neural output.
    Each call clones the tokenizer to isolate padding and truncation state.
    """
    def __init__(self):
        implementation = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(implementation / '.corpus-deps'))
        from tokenizers import Tokenizer
        self.tokenizer_type = Tokenizer
        self.serialized = Tokenizer.from_file(
            str(implementation / 'vendor/e5-small-v2/tokenizer.json')).to_str()

    def __call__(self, texts, text_pair=None, *, add_special_tokens=True,
                 padding=False, truncation=False, max_length=None,
                 return_tensors=None, return_special_tokens_mask=False,
                 return_offsets_mapping=False):
        if return_tensors is not None:
            raise ValueError('test adapter does not create tensors or model output')
        tokenizer = self.tokenizer_type.from_str(self.serialized)
        tokenizer.no_truncation()
        tokenizer.no_padding()
        if truncation:
            tokenizer.enable_truncation(max_length, strategy='longest_first')
        if padding:
            tokenizer.enable_padding(pad_id=0, pad_token='[PAD]')
        inputs = texts if text_pair is None else list(zip(texts, text_pair))
        rows = tokenizer.encode_batch(inputs, add_special_tokens=add_special_tokens)
        result = {'input_ids': [r.ids for r in rows],
                  'attention_mask': [r.attention_mask for r in rows],
                  'token_type_ids': [r.type_ids for r in rows]}
        if return_special_tokens_mask:
            result['special_tokens_mask'] = [r.special_tokens_mask for r in rows]
        if return_offsets_mapping:
            result['offset_mapping'] = [r.offsets for r in rows]
        return RealBatch(result, rows)


class E5TokenBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = RealTokenizerAdapter()

    def test_true_tokenizer_prefix_and_special_ids(self):
        for kind, prefix_id in (('query', 23032), ('passage', 6019)):
            encoded, audits = prepare_e5_batch(self.tokenizer, ['alpha'], kind=kind)
            with self.subTest(kind=kind):
                self.assertEqual(encoded['input_ids'], [[101, prefix_id, 1024, 6541, 102]])
                self.assertEqual(audits[0]['input_tokens'], 5)
                self.assertEqual(audits[0]['output_tokens'], 5)
                self.assertEqual(audits[0]['prefix_tokens'], 2)
                self.assertEqual(audits[0]['special_tokens'], 2)
                self.assertEqual(audits[0]['body_tokens_before'], 1)
                self.assertEqual(audits[0]['removed_tokens'], 0)
                self.assertFalse(audits[0]['truncated'])
                self.assertEqual(audits[0]['input_sha256'], hashlib.sha256(
                    (kind + ': alpha').encode()).hexdigest())

    def test_actual_512_limit_includes_prefix_specials_and_excludes_padding(self):
        encoded, audits = prepare_e5_batch(self.tokenizer, ['alpha ' * 600, 'alpha'])
        # One alpha token repeated 600 times, two prefix tokens, two specials.
        self.assertEqual(audits[0]['input_tokens'], 604)
        self.assertEqual(audits[0]['output_tokens'], 512)
        self.assertEqual(audits[0]['removed_tokens'], 92)
        self.assertEqual(audits[0]['body_tokens_before'], 600)
        self.assertEqual(audits[0]['body_tokens_after'], 508)
        self.assertTrue(audits[0]['truncated'])
        self.assertEqual(encoded['input_ids'][0], [101, 23032, 1024] + [6541] * 508 + [102])
        self.assertEqual(len(encoded['input_ids'][1]), 512)
        self.assertEqual(sum(encoded['attention_mask'][1]), 5)
        self.assertEqual(audits[1]['output_tokens'], 5)
        self.assertEqual(audits[1]['removed_tokens'], 0)
        self.assertEqual(audits[1]['special_tokens'], 2)
        self.assertEqual(audits[0]['token_count_kind'], 'actual_model_tokenizer')

    def test_repeated_truncation_is_deterministic(self):
        text = 'Đường dẫn java.net.ConnectException v1.2.3 ' * 100
        self.assertEqual(prepare_e5_batch(self.tokenizer, [text], max_tokens=32),
                         prepare_e5_batch(self.tokenizer, [text], max_tokens=32))

    def test_entire_body_must_not_disappear_after_prefix_truncation(self):
        with self.assertRaisesRegex(ValueError, 'entire text'):
            prepare_e5_batch(self.tokenizer, ['alpha'], max_tokens=4)

    def test_empty_batch_and_invalid_kind_limits_fail_without_models(self):
        self.assertEqual(prepare_e5_batch(self.tokenizer, []), ({}, []))
        for options in ({'max_tokens': 513}, {'max_tokens': 3}, {'max_tokens': True},
                        {'kind': 'incident_id'}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                prepare_e5_batch(self.tokenizer, ['alpha'], **options)

    def test_unpinned_revision_and_missing_assets_do_not_select_latest(self):
        with self.assertRaisesRegex(ValueError, 'revision'):
            E5Encoder(None, {}, revision='main')
        with self.assertRaisesRegex(ValueError, 'missing local model'):
            E5Encoder(None, {})


class PairBudgetAndCandidateTests(unittest.TestCase):
    """Generic pair accounting uses real E5 tokens, not unavailable BGE tokens."""
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = RealTokenizerAdapter()

    def test_pair_budget_counts_both_sides_and_three_bert_specials(self):
        encoded, audits = prepare_reranker_batch(
            self.tokenizer, 'alpha ' * 600, ['beta ' * 600], max_tokens=512)
        row = audits[0]
        self.assertEqual(row['input_tokens'], 1203)
        self.assertEqual(row['output_tokens'], 512)
        self.assertEqual(row['removed_tokens'], 691)
        self.assertEqual(row['special_tokens'], 3)
        self.assertEqual(row['query_tokens_before'], 600)
        self.assertEqual(row['passage_tokens_before'], 600)
        self.assertGreater(row['query_tokens_after'], 0)
        self.assertGreater(row['passage_tokens_after'], 0)
        self.assertEqual(row['query_tokens_after'] + row['passage_tokens_after'], 509)
        self.assertEqual(sum(encoded['attention_mask'][0]), 512)

    def test_pair_padding_is_excluded_and_empty_sides_rejected(self):
        _, audits = prepare_reranker_batch(self.tokenizer, 'alpha', ['beta ' * 600, 'beta'])
        self.assertEqual(audits[1]['output_tokens'], 5)
        self.assertEqual(audits[1]['special_tokens'], 3)
        for query, passage in (('', 'beta'), ('alpha', ''), ('  ', 'beta')):
            with self.subTest(query=query, passage=passage), self.assertRaisesRegex(ValueError, 'nonempty'):
                prepare_reranker_batch(self.tokenizer, query, [passage])

    def test_candidate_guards_execute_before_optional_model_access(self):
        # Construct only the adapter object; never substitute a model or scores.
        reranker = BGEReranker.__new__(BGEReranker)
        self.assertEqual(reranker.rerank('alpha', [], [chunk('A')]), ([], []))
        invalid = ([hit('foreign')], [hit('A'), hit('A', 2)],
                   [dict(hit('A'), document_id='foreign-document')])
        for candidates in invalid:
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                reranker.rerank('alpha', candidates, [chunk('A')])
        candidates = [hit(str(i), i + 1) for i in range(51)]
        with self.assertRaisesRegex(ValueError, 'top-50'):
            reranker.rerank('alpha', candidates, [chunk(str(i)) for i in range(51)])


if __name__ == '__main__':
    unittest.main()
