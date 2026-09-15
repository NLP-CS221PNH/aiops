"""Semantic provenance tests independent of outer artifact/content hashes."""
from __future__ import annotations

import copy
import unittest
from unittest import mock

from src.corpus.common import CorpusError, sha256, write_json
from src.corpus.normalize import normalize_document, clip_spans
from src.corpus.validate_corpus import _validate_spans, _validate_applicability
from test_corpus_integrity import CorpusFixture


class CitationSpanTests(CorpusFixture):
    def setUp(self):
        super().setUp()
        self.raw = '\ufeffKiểm tra 🚀\r\nHTTP 503\n'
        self.original = self.source(self.raw)
        self.document = {**self.original, **normalize_document(self.original, root=self.work),
                         'source_revision': 'synthetic-revision'}
        self.text = self.document['normalized_text']
        self.catalog = {'guide.md': {**self.original,
                                    'verified_raw_hash': self.original['raw_sha256'],
                                    'verified_revision': 'synthetic-revision',
                                    'raw_bytes': self.raw.encode('utf-8')}}

    def validate(self, spans, text=None, start=0, end=None):
        text = self.text if text is None else text
        return _validate_spans(spans, text, start, len(text) if end is None else end,
                               self.catalog, self.document)

    def test_real_unicode_crlf_provenance_reconstructs_full_text_and_chunk_slice(self):
        self.validate(self.document['source_spans'])
        start = self.text.index('🚀')
        end = self.text.index('HTTP') + len('HTTP 503')
        clipped = clip_spans(self.document['source_spans'], start, end, root=self.work)
        self.validate(clipped, start=start, end=end)

    def test_valid_source_url_with_wrong_normalized_text_span_fails(self):
        changed = self.text.replace('HTTP 503', 'HTTP 200')
        with self.assertRaisesRegex(CorpusError, 'SOURCE_TEXT_SPAN_MISMATCH'):
            self.validate(self.document['source_spans'], text=changed)

    def test_utf8_byte_offset_cannot_be_used_as_unicode_codepoint_offset(self):
        start = self.text.index('🚀')
        spans = clip_spans(self.document['source_spans'], start, start + 1, root=self.work)
        spans[0]['raw_start'] = spans[0]['raw_byte_start']
        spans[0]['raw_end'] = spans[0]['raw_byte_end']
        with self.assertRaisesRegex(CorpusError, 'RAW_SPAN_BOUNDS|RAW_BYTE_OFFSET'):
            self.validate(spans, start=start, end=start + 1)

    def test_incorrect_raw_byte_coordinate_fails_despite_correct_codepoints(self):
        spans = copy.deepcopy(self.document['source_spans'])
        spans[0]['raw_byte_start'] += 1
        with self.assertRaisesRegex(CorpusError, 'RAW_BYTE_OFFSET'):
            self.validate(spans)

    def test_missing_span_and_noninteger_offsets_are_rejected(self):
        with self.assertRaisesRegex(CorpusError, 'NORMALIZED_SPAN_COVERAGE'):
            self.validate(self.document['source_spans'][:-1])
        for value in (True, -1, 0.5, '0'):
            spans = copy.deepcopy(self.document['source_spans'])
            spans[0]['normalized_start'] = value
            with self.subTest(value=value), self.assertRaisesRegex(CorpusError, 'OFFSET_INTEGER'):
                self.validate(spans)

    def test_foreign_source_revision_hash_and_path_cannot_supply_citation(self):
        for field, value, message in (
            ('raw_sha256', '0' * 64, 'SPAN_SOURCE_PROVENANCE'),
            ('source_revision', 'current-revision', 'SPAN_SOURCE_PROVENANCE'),
            ('raw_path', 'current-snapshot.md', 'FOREIGN_RAW_SOURCE'),
            ('source_id', 'D000', 'SPAN_SOURCE_PROVENANCE'),
        ):
            spans = copy.deepcopy(self.document['source_spans'])
            spans[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(CorpusError, message):
                self.validate(spans)


class ApplicabilityGateTests(unittest.TestCase):
    def row(self):
        return {'decision': 'unknown', 'reason': 'Fixture deployment was not verified.',
                'review_state': 'pending', 'reviewer': '', 'reviewed_at': '',
                'app_version': 'unknown', 'platform_version': 'unknown',
                'evidence_ids': ['synthetic-source'], 'owner': 'A',
                'allowed_experiment_mode': 'local_candidate',
                'config_preconditions': 'Verify deployment and document conditions before reference use.'}

    def test_unknown_with_conditional_policy_is_valid_candidate(self):
        _validate_applicability(self.row())

    def test_unknown_without_explicit_policy_fails(self):
        for missing in ('allowed_experiment_mode', 'config_preconditions'):
            row = self.row()
            row.pop(missing)
            with self.subTest(field=missing), self.assertRaisesRegex(CorpusError, 'UNKNOWN_WITHOUT_POLICY'):
                _validate_applicability(row)

    def test_blank_reason_or_missing_evidence_fails(self):
        for field, value, message in (('reason', ' ', 'APPLICABILITY_REASON'),
                                      ('evidence_ids', [], 'APPLICABILITY_EVIDENCE'),
                                      ('owner', '', 'APPLICABILITY_EVIDENCE')):
            row = self.row()
            row[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(CorpusError, message):
                _validate_applicability(row)

    def test_human_approval_and_deployment_compatibility_cannot_be_invented(self):
        for field, value, message in (('review_state', 'approved', 'CANDIDATE_REVIEW_STATE'),
                                      ('reviewer', 'Codex acting as human A', 'CANDIDATE_REVIEW_STATE'),
                                      ('app_version', 'confirmed', 'DEPLOYMENT_NOT_VERIFIED'),
                                      ('platform_version', '1.29', 'DEPLOYMENT_NOT_VERIFIED')):
            row = self.row()
            row[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(CorpusError, message):
                _validate_applicability(row)


class ReviewReceiptTests(CorpusFixture):
    """Synthetic receipts exercise technical binding without inventing reviews."""
    def setUp(self):
        super().setUp()
        from src.corpus import review_receipt
        self.module = review_receipt
        self.config_path = self.work / 'configs/fixture.json'
        write_json(self.config_path, {'synthetic': True})
        self.candidate = self.work / 'candidate'
        write_json(self.candidate / 'corpus-manifest.json', {'synthetic': True})
        evidence = []
        for relative in ('reports/corpus-validation.json', 'reports/corpus-tests.json',
                         'reports/corpus-code-review.md', 'configs/corpus-execution-authorization.json'):
            path = self.work / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Explicitly synthetic fixture evidence only.\n', encoding='utf-8')
            evidence.append({'path': relative, 'sha256': sha256(path)})
        self.receipt_path = self.work / 'fixture-receipt.json'
        self.receipt = {
            'schema_version': 'cs221-corpus-review-v1', 'corpus_hash': 'a' * 64,
            'manifest_hash': sha256(self.candidate / 'corpus-manifest.json'),
            'config_hash': sha256(self.config_path), 'technical_gate': 'pass',
            'release_ready': False, 'human_reviews': [], 'applicability_review': 'pending',
            'plan02_full_gate': 'pending', 'evidence': evidence,
            'automated_reviews': [
                {'role': 'tester', 'actor_kind': 'codex_agent', 'reviewer': 'synthetic fixture tester',
                 'status': 'pass', 'evidence_path': 'reports/corpus-tests.json'},
                {'role': 'code-reviewer', 'actor_kind': 'codex_agent', 'reviewer': 'synthetic fixture reviewer',
                 'status': 'pass', 'evidence_path': 'reports/corpus-code-review.md'},
            ],
        }

    def validate(self, **kwargs):
        write_json(self.receipt_path, self.receipt)
        with mock.patch.object(self.module, 'IMPL', self.work), mock.patch.object(
            self.module, 'validate_corpus', return_value={'corpus_hash': 'a' * 64}
        ):
            return self.module.validate_review_receipt(self.receipt_path, self.candidate, self.config_path, **kwargs)

    def test_technical_receipt_pass_does_not_authorize_human_release(self):
        self.assertEqual(self.validate()['human_gate'], 'pending')
        with self.assertRaisesRegex(CorpusError, 'RELEASE_PENDING'):
            self.validate(require_reviewed=True)

    def test_changed_evidence_bytes_invalidate_receipt(self):
        (self.work / 'reports/corpus-tests.json').write_text('changed fixture evidence')
        with self.assertRaisesRegex(CorpusError, 'REVIEW_EVIDENCE_HASH'):
            self.validate()

    def test_changed_manifest_bytes_invalidate_receipt(self):
        write_json(self.candidate / 'corpus-manifest.json', {'synthetic': 'changed'})
        with self.assertRaisesRegex(CorpusError, 'REVIEW_MANIFEST_HASH'):
            self.validate()

    def test_fabricated_human_reviews_are_rejected(self):
        self.receipt['human_reviews'] = [{'reviewer': 'synthetic claimed human'}]
        with self.assertRaisesRegex(CorpusError, 'REVIEW_HUMAN_STATE'):
            self.validate()

if __name__ == '__main__':
    unittest.main()
