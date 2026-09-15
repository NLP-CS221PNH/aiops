"""Validate actual automated evidence without substituting human signatures."""
from __future__ import annotations

from pathlib import Path

from .common import DEFAULT_CONFIG, DEFAULT_OUTPUT, IMPL, read_json, require, safe_path, sha256
from .validate_corpus import validate_corpus


def validate_review_receipt(receipt_path=IMPL / 'reports/corpus-review-receipt.json',
                            corpus_root=DEFAULT_OUTPUT, config_path=DEFAULT_CONFIG,
                            require_reviewed=False):
    receipt = read_json(receipt_path)
    require(isinstance(receipt, dict) and receipt.get('schema_version') == 'cs221-corpus-review-v1', 'REVIEW_RECEIPT_SCHEMA')
    corpus_root = Path(corpus_root)
    validation = validate_corpus(corpus_root, config_path)
    require(receipt.get('corpus_hash') == validation['corpus_hash'], 'REVIEW_CORPUS_HASH')
    require(receipt.get('manifest_hash') == sha256(corpus_root / 'corpus-manifest.json'), 'REVIEW_MANIFEST_HASH')
    require(receipt.get('config_hash') == sha256(config_path), 'REVIEW_CONFIG_HASH')
    require(receipt.get('technical_gate') == 'pass', 'REVIEW_TECHNICAL_GATE')
    require(receipt.get('release_ready') is False and receipt.get('human_reviews') == [], 'REVIEW_HUMAN_STATE')
    require(receipt.get('applicability_review') == 'pending' and receipt.get('plan02_full_gate') == 'pending', 'REVIEW_RELEASE_GATE')
    evidence = receipt.get('evidence')
    require(isinstance(evidence, list) and evidence, 'REVIEW_EVIDENCE')
    seen = set()
    for entry in evidence:
        require(isinstance(entry, dict) and set(entry) == {'path', 'sha256'}, 'REVIEW_EVIDENCE_SCHEMA')
        path = safe_path(IMPL, entry['path'])
        require(path.is_relative_to(IMPL / 'reports') or path.is_relative_to(IMPL / 'tests') or path.is_relative_to(IMPL / 'configs'), 'REVIEW_EVIDENCE_PATH')
        require(entry['path'] not in seen, 'REVIEW_DUPLICATE_EVIDENCE')
        seen.add(entry['path'])
        require(sha256(path) == entry['sha256'], 'REVIEW_EVIDENCE_HASH')
    require({'reports/corpus-validation.json', 'reports/corpus-tests.json', 'reports/corpus-code-review.md',
             'configs/corpus-execution-authorization.json'} <= seen, 'REVIEW_REQUIRED_EVIDENCE')
    reviews = receipt.get('automated_reviews')
    require(isinstance(reviews, list) and len(reviews) >= 2 and all(isinstance(row, dict) for row in reviews), 'AUTOMATED_REVIEWS_REQUIRED')
    require({'tester', 'code-reviewer'} <= {row.get('role') for row in reviews}, 'AUTOMATED_REVIEW_ROLES')
    require(all(row.get('actor_kind') == 'codex_agent' and row.get('reviewer') and row.get('status') == 'pass'
                and row.get('evidence_path') in seen for row in reviews), 'AUTOMATED_REVIEW_EVIDENCE')
    if require_reviewed:
        require(False, 'RELEASE_PENDING: upstream human gate and applicability review not completed')
    return {'status': 'pass', 'corpus_hash': validation['corpus_hash'], 'technical_gate': 'pass',
            'release_ready': False, 'human_gate': 'pending'}
