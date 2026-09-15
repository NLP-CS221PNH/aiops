"""Bind technical review evidence to a release; never invent a human approval."""
from pathlib import Path

from .common import IMPL, read_json, require, safe_path, sha256, validate_inference


def validate_review_receipt(receipt_path, inference_root, require_human=False):
    receipt = read_json(receipt_path)
    require(isinstance(receipt, dict), 'RECEIPT_SCHEMA')
    require(receipt.get('schema_version') == 'cs221-data-review-v1', 'RECEIPT_SCHEMA')
    require(receipt.get('manifest_hash') == sha256(Path(inference_root)/'input-manifest.json'), 'RECEIPT_MANIFEST')
    validate_inference(inference_root)
    require(receipt.get('local_gate') == 'pass', 'RECEIPT_LOCAL_GATE')
    require(isinstance(receipt.get('evidence'), list) and receipt['evidence'], 'RECEIPT_EVIDENCE')
    paths = set()
    for entry in receipt['evidence']:
        require(isinstance(entry, dict) and set(entry) == {'path','sha256'}, 'RECEIPT_EVIDENCE')
        require(isinstance(entry['path'],str) and isinstance(entry['sha256'],str), 'RECEIPT_EVIDENCE')
        require(entry['path'] not in paths, 'RECEIPT_EVIDENCE')
        paths.add(entry['path'])
        path = safe_path(IMPL, entry['path'], ['reports','configs','notebooks','tests','src','artifacts','data/private'])
        require(sha256(path) == entry['sha256'], 'RECEIPT_EVIDENCE_HASH')
    if require_human:
        reviews = receipt.get('human_reviews', [])
        require(isinstance(reviews,list) and all(isinstance(row,dict) for row in reviews), 'HUMAN_REVIEW_PENDING')
        require({row.get('owner') for row in reviews} == {'A','B','C'} and len(reviews) == 3, 'HUMAN_REVIEW_PENDING')
        require(all(row.get('status') == 'approved' and row.get('reviewer') and
                    row.get('manifest_hash') == receipt['manifest_hash'] and row.get('reviewed_at')
                    for row in reviews), 'HUMAN_REVIEW_PENDING')
    return {'status':'pass','manifest_hash':receipt['manifest_hash'],
            'human_gate':'pass' if require_human else 'not_asserted'}
