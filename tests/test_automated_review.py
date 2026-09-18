"""Automated review v2: unknown stays unknown, no invented licenses."""
from __future__ import annotations

import unittest

from src.corpus.automated_review import review_document, review_manifest


class AutomatedReviewTests(unittest.TestCase):
    def test_unverified_deployment_stays_unknown(self):
        record = {
            'source_id': 'D057',
            'release_revision': '80bea9bfd97bec107361d4663e207aa8d3f312c6',
            'license_data': 'Apache-2.0',
            'version_compatibility': 'unverified',
        }
        row = review_document(record, raw_text='Online Boutique README')
        self.assertEqual(row['applicability'], 'unknown')
        self.assertEqual(row['rule_result'], 'unknown')
        self.assertEqual(row['schema_version'], 'cs221-automated-review-v2')

    def test_missing_revision_is_rejected(self):
        with self.assertRaises(Exception):
            review_document({'source_id': 'D057', 'license_data': 'Apache-2.0'})

    def test_wrong_supporting_hash_is_rejected(self):
        record = {
            'source_id': 'D057',
            'release_revision': 'abc',
            'license_data': 'Apache-2.0',
            'version_compatibility': 'unverified',
        }
        with self.assertRaisesRegex(ValueError, 'SUPPORTING_HASH_MISMATCH'):
            review_document(record, supporting={'sha256': '0' * 64, 'raw_path': 'README.md'})

    def test_supporting_path_escape_is_rejected(self):
        record = {
            'source_id': 'D057',
            'release_revision': 'abc',
            'license_data': 'Apache-2.0',
            'version_compatibility': 'unverified',
        }
        with self.assertRaisesRegex(ValueError, 'PATH_ESCAPE'):
            review_document(record, supporting={'sha256': '0' * 64, 'raw_path': '../secret.bin'})

    def test_empty_eligible_reports_corpus_gap(self):
        result = review_manifest([{
            'source_id': 'D058',
            'release_revision': '7e631d0318dc279cb2d31231d8823360e61e9304',
            'license_data': 'CC-BY-4.0',
            'version_compatibility': 'unverified',
        }])
        self.assertFalse(result['corpus_ready'])
        self.assertEqual(result['error'], 'CORPUS_NO_ELIGIBLE_DOCUMENTS')


if __name__ == '__main__':
    unittest.main()
