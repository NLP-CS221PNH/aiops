"""Validate delivery checksums and optional clean-extract data-only preflight."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_IMPL = Path(__file__).resolve().parents[1]
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from src.data.common import sha256, write_json


def verify_sums(root: Path) -> list[str]:
    errors = []
    lines = (root / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines()
    for line in lines:
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        path = root / name.strip()
        if not path.is_file():
            errors.append(f'missing:{name}')
            continue
        if sha256(path) != digest:
            errors.append(f'hash_mismatch:{name}')
    manifest = json.loads((root / 'delivery-manifest.json').read_text(encoding='utf-8'))
    if 'self_sha256' in manifest:
        errors.append('manifest_self_hash_loop')
    zip_meta = manifest['artifacts']['source_zip']
    if sha256(root / zip_meta['path']) != zip_meta['sha256']:
        errors.append('zip_manifest_mismatch')
    return errors


def clean_extract(root: Path, python_exe: str) -> dict:
    extract = Path(tempfile.mkdtemp(prefix='kaggle-clean-'))
    try:
        with zipfile.ZipFile(root / 'aiops-kaggle-source.zip') as archive:
            archive.extractall(extract)
        if (extract / '.git').exists():
            return {'ok': False, 'error': 'git_present'}
        resolved = {
            'schema_version': 'cs221-kaggle-resolved-v1',
            'inference_root': str(extract / 'data' / 'inference'),
            'private_train_root': str((root / 'private-training-inputs' / 'private-train').resolve()),
            'private_dev_root': str((root / 'private-training-inputs' / 'private-dev').resolve()),
            'output_root': str(extract / 'artifacts' / 'kaggle-delivery' / 'v1'),
            'qwen_assets': None,
        }
        cfg = extract / 'configs' / 'kaggle.resolved.json'
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(resolved, indent=2), encoding='utf-8')
        proc = subprocess.run(
            [python_exe, '-m', 'src.training', 'preflight', '--config', str(cfg), '--data-only'],
            cwd=extract, capture_output=True, text=True,
        )
        return {
            'ok': proc.returncode == 0,
            'returncode': proc.returncode,
            'stdout': proc.stdout[-2000:],
            'stderr': proc.stderr[-2000:],
            'extract': str(extract),
        }
    finally:
        shutil.rmtree(extract, ignore_errors=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Validate Kaggle delivery artifacts')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--clean-extract', action='store_true')
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    root = manifest_path.parent
    errors = verify_sums(root)
    extract_receipt = None
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    checks = manifest.setdefault('checks', {})
    if args.clean_extract:
        extract_receipt = clean_extract(root, sys.executable)
        if not extract_receipt.get('ok'):
            errors.append('clean_extract_preflight_failed')
        source_validated = not errors
        write_json(root / 'validation-receipt.json', {
            'schema_version': 'cs221-delivery-validation-v1',
            'errors': errors,
            'clean_extract': extract_receipt,
            'source_validated': source_validated,
        })
        checks['source_validated'] = source_validated
        manifest.setdefault('check_reasons', {})['source_validated'] = (
            'validation-receipt.json clean-extract preflight' if source_validated
            else 'clean_extract_failed: ' + ','.join(errors)
        )
        write_json(manifest_path, manifest)
    elif errors:
        checks['source_validated'] = False
        manifest.setdefault('check_reasons', {})['source_validated'] = 'checksums_failed: ' + ','.join(errors)
        write_json(manifest_path, manifest)
        source_validated = False
    else:
        source_validated = bool(checks.get('source_validated'))
    print(json.dumps({'source_validated': source_validated, 'errors': errors, 'clean_extract': bool(args.clean_extract)}))
    return 0 if not errors else 4


if __name__ == '__main__':
    raise SystemExit(main())
