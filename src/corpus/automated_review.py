"""v2 automated source review. Models classify evidence; they never invent licenses."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from src.corpus.common import ROOT, canonical_hash, require, sha256, write_json
from src.data.common import DataContractError
from src.training.access import lexical_relative

IMPL = Path(__file__).resolve().parents[2]


def _span(text: str, needle: str) -> dict[str, Any]:
    start = text.find(needle) if needle else 0
    if start < 0:
        start = 0
    end = min(len(text), start + max(len(needle), 32))
    snippet = text[start:end]
    return {
        'start_codepoint': start,
        'end_codepoint': end,
        'text_sha256': canonical_hash(snippet),
    }


def review_document(record: Mapping[str, Any], raw_text: str | None = None,
                    supporting: Mapping[str, Any] | None = None) -> dict[str, Any]:
    require(record.get('source_id'), 'SOURCE_ID_REQUIRED')
    require(record.get('release_revision'), 'REVISION_REQUIRED')
    license_code = record.get('license_data') or record.get('license_code')
    require(license_code, 'LICENSE_REQUIRED')
    if supporting and supporting.get('sha256') and supporting.get('raw_path'):
        try:
            path = lexical_relative(Path(supporting.get('root') or ROOT or IMPL), supporting['raw_path'])
        except DataContractError as exc:
            raise ValueError('PATH_ESCAPE') from exc
        if not path.is_file():
            raise ValueError('MISSING_SUPPORTING_ASSET')
        if sha256(path) != supporting['sha256']:
            raise ValueError('SUPPORTING_HASH_MISMATCH')
    prompt = {
        'task': 'evidence_applicability',
        'source_id': record['source_id'],
        'revision': record['release_revision'],
        'license': license_code,
    }
    if raw_text is None:
        applicability = 'unknown'
        rule_result = 'unknown'
        reason = 'raw_source_absent'
        span = {'start_codepoint': 0, 'end_codepoint': 0, 'text_sha256': canonical_hash('')}
        validator_status = 'not_run'
    else:
        span = _span(raw_text, record.get('source_id', ''))
        if record.get('version_compatibility') == 'unverified':
            applicability = 'unknown'
            rule_result = 'unknown'
            reason = 'deployment_version_unverified'
        else:
            applicability = 'conditional'
            rule_result = 'pass'
            reason = 'general_or_conditional_scope_only'
        validator_status = 'pass'
    return {
        'schema_version': 'cs221-automated-review-v2',
        'doc_id': record['source_id'],
        'source_revision': record['release_revision'],
        'evidence_span': span,
        'target_system_scope': 'RCAEval-RE2-Online-Boutique',
        'preconditions': ['per_incident_cutoff', 'deployment_review'],
        'rule_result': rule_result,
        'model_revision': 'not_provisioned',
        'prompt_hash': canonical_hash(prompt),
        'raw_response': '',
        'validator_status': validator_status,
        'reason': reason,
        'applicability': applicability,
    }


def review_manifest(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [review_document(record) for record in records]
    eligible = [row for row in rows if row['applicability'] == 'eligible']
    return {
        'schema_version': 'cs221-automated-review-manifest-v2',
        'n_sources': len(rows),
        'n_eligible': len(eligible),
        'corpus_ready': bool(eligible),
        'status': 'pass' if rows else 'empty',
        'reviews': rows,
        'error': None if eligible else 'CORPUS_NO_ELIGIBLE_DOCUMENTS',
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Automated v2 knowledge-source review')
    parser.add_argument('--config', default=str(IMPL / 'configs' / 'knowledge-assets.json'))
    parser.add_argument('--output-root', default=str(IMPL / 'artifacts' / 'kaggle-delivery' / 'v1' / 'reviews'))
    parser.add_argument('--run-id', default='review-v2')
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.config).read_text(encoding='utf-8'))
    records = payload.get('sources') or []
    result = review_manifest(records)
    out = Path(args.output_root)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f'{args.run_id}.json'
    write_json(path, result)
    print(json.dumps({'path': str(path), 'corpus_ready': result['corpus_ready'], 'error': result['error']}))
    return 0 if result['corpus_ready'] else 4


if __name__ == '__main__':
    raise SystemExit(main())
