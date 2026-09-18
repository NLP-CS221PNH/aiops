"""Package the Kaggle source ZIP, private inputs, DOCX, and checksums."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

_IMPL = Path(__file__).resolve().parents[1]
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from src.data.common import IMPL, sha256, write_json
from src.training.config import load_mapping

EXCLUDE_DIR_NAMES = {
    '.git', '.venv', '.runtime-python', '.corpus-deps', '.retrieval-deps',
    '__pycache__', '.pytest_cache', 'runs-test-resume', 'runs-test-export',
    'runs-test-objective',
}
EXCLUDE_SUFFIXES = {'.pyc', '.pyo', '.dotenv'}
SECRET_PATTERNS = (
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(r'\bsk-(?:ant|live|proj)-[A-Za-z0-9]{20,}\b'),
    re.compile(r'(?im)^OPENAI_API_KEY=\S+'),
)


def posix(path: Path) -> str:
    return path.as_posix()


def allowed_files(root: Path, file_list: list[str]) -> list[Path]:
    files = []
    for item in file_list:
        target = root / item
        if not target.is_file():
            print(json.dumps({'error': 'MISSING_PACKAGE_FILE', 'path': item}))
            raise SystemExit(4)
        if any(part in EXCLUDE_DIR_NAMES for part in target.parts):
            continue
        if target.suffix in EXCLUDE_SUFFIXES:
            continue
        files.append(target)
    unique = []
    seen = set()
    for path in files:
        rel = posix(path.relative_to(root))
        if rel in seen:
            continue
        seen.add(rel)
        unique.append(path)
    return sorted(unique, key=lambda item: posix(item.relative_to(root)))


def scan_secrets(path: Path) -> list[str]:
    if path.suffix.lower() in {'.png', '.jpg', '.safetensors', '.bin', '.pt', '.parquet'}:
        return []
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return []
    hits = [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(text)]
    win_users = "C:" + "\\Users\\"
    posix_users = "C:" + "/Users/"
    if win_users in text or posix_users in text:
        if "local_windows" not in path.name:
            hits.append("absolute_author_path")
    return hits


def add_zip_file(archive: zipfile.ZipFile, path: Path, arcname: str, epoch: int | None) -> None:
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o644 << 16)
    if epoch is not None:
        stamp = datetime.fromtimestamp(epoch, tz=timezone.utc).timetuple()
        info.date_time = stamp[:6]
    archive.writestr(info, path.read_bytes())


def copytree_files(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for path in src.rglob('*'):
        if path.is_file():
            target = dest / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def git_revision() -> dict:
    try:
        rev = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=IMPL, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=IMPL, text=True).strip())
        return {'code_revision': rev, 'git_dirty': dirty}
    except (OSError, subprocess.CalledProcessError):
        return {'code_revision': 'unresolved', 'git_dirty': None}


def source_tree_sha256(inventory: list[dict]) -> str:
    blob = '\n'.join(f"{row['sha256']}  {row['path']}" for row in inventory).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()


def package(config_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    config = load_mapping(config_path)
    file_list = list(config.get('package_files') or [])
    if not file_list:
        print(json.dumps({'error': 'MISSING_PACKAGE_FILES'}))
        raise SystemExit(4)
    files = allowed_files(IMPL, file_list)
    secret_hits = []
    for path in files:
        secret_hits.extend({'path': posix(path.relative_to(IMPL)), 'marker': hit} for hit in scan_secrets(path))
    if secret_hits:
        print(json.dumps({'error': 'SECRET_SCAN', 'hits': secret_hits}))
        raise SystemExit(4)
    epoch = int(os.environ['SOURCE_DATE_EPOCH']) if os.environ.get('SOURCE_DATE_EPOCH') else None
    zip_path = output / 'aiops-kaggle-source.zip'
    inventory = []
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for path in files:
            arc = posix(path.relative_to(IMPL))
            add_zip_file(archive, path, arc, epoch)
            inventory.append({'path': arc, 'sha256': sha256(path), 'bytes': path.stat().st_size})
    private = output / 'private-training-inputs'
    src_private = IMPL / 'data' / 'training-inputs' / 'v1'
    copytree_files(src_private, private)
    for name in ('aiops-report-vi.docx', 'aiops-report-en.docx'):
        src = output / name
        if not src.is_file():
            raise SystemExit(f'missing_docx:{name}')
    artifacts = [
        zip_path,
        output / 'aiops-report-vi.docx',
        output / 'aiops-report-en.docx',
    ]
    private_files = sorted(path for path in private.rglob('*') if path.is_file())
    sums = []
    for path in artifacts + private_files:
        rel = posix(path.relative_to(output))
        sums.append(f"{sha256(path)}  {rel}")
    (output / 'SHA256SUMS.txt').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    git = git_revision()
    tree_hash = source_tree_sha256(inventory)
    manifest = {
        'schema_version': 'cs221-kaggle-delivery-v1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'timezone': 'Asia/Saigon',
        'code_revision': git['code_revision'],
        'git_dirty': git['git_dirty'],
        'source_tree_sha256': tree_hash,
        'plan_ref': 'plans/260917-1948-kaggle-source-bilingual-reports',
        'self_manifest_sha256_excluded': True,
        'input_refs': {
            'data_yaml_sha256': sha256(IMPL / 'configs' / 'data.yaml'),
            'input_manifest_sha256': sha256(IMPL / 'data' / 'inference' / 'input-manifest.json'),
            'training_inputs': 'data/training-inputs/v1',
            'private_inputs': 'private-training-inputs',
        },
        'config_refs': {
            'kaggle_sha256': sha256(config_path),
            'training_sha256': sha256(IMPL / 'configs' / 'training.yaml'),
            'generation_sha256': sha256(IMPL / 'configs' / 'generation.yaml'),
            'methodology_kaggle_v2_sha256': sha256(IMPL / 'configs' / 'methodology-kaggle-v2.yaml'),
        },
        'model_refs': {
            'generator_id': config.get('model', {}).get('id'),
            'generator_revision': config.get('model', {}).get('revision'),
            'e5_id': config.get('e5', {}).get('id'),
            'e5_revision': config.get('e5', {}).get('revision'),
            'e5_trainable': config.get('e5', {}).get('trainable'),
            'adapter': 'not_exported_research_adapter',
            'tokenizer': 'bundled_with_qwen_local_assets',
        },
        'platform': {
            'packaging_os': os.name,
            'python': sys.version.split()[0],
            'linux_install_verified': False,
            'dependency_candidate': 'configs/kaggle-requirements.in',
        },
        'artifact_classification': {
            'aiops-kaggle-source.zip': 'public-source',
            'private-training-inputs': 'local-private-support',
            'aiops-report-vi.docx': 'public-report',
            'aiops-report-en.docx': 'public-report',
            'SHA256SUMS.txt': 'checksums',
            'delivery-manifest.json': 'receipt',
        },
        'artifacts': {
            'source_zip': {'path': 'aiops-kaggle-source.zip', 'sha256': sha256(zip_path), 'bytes': zip_path.stat().st_size, 'classification': 'public-source'},
            'report_vi': {'path': 'aiops-report-vi.docx', 'sha256': sha256(output / 'aiops-report-vi.docx'), 'classification': 'public-report'},
            'report_en': {'path': 'aiops-report-en.docx', 'sha256': sha256(output / 'aiops-report-en.docx'), 'classification': 'public-report'},
            'sha256sums': {'path': 'SHA256SUMS.txt', 'sha256': sha256(output / 'SHA256SUMS.txt'), 'classification': 'checksums'},
            'private_inputs': {'path': 'private-training-inputs', 'files': len(private_files), 'classification': 'local-private-support'},
        },
        'inventory': inventory,
        'checks': {
            'source_validated': False,
            'linux_install_verified': False,
            'tiny_training_mechanics_verified': True,
            'target_model_smoke_verified': False,
            'corpus_ready': False,
            'kaggle_execution_verified': False,
            'full_training_run_completed': False,
            'docx_layout_verified': False,
            'results_intentionally_blank': True,
        },
        'check_reasons': {
            'source_validated': 'pending validate-kaggle-delivery --clean-extract',
            'linux_install_verified': 'Windows author host; no Linux pip-check receipt',
            'kaggle_execution_verified': 'No actual Kaggle run',
            'full_training_run_completed': 'Out of agent scope; user-run',
            'corpus_ready': 'CORPUS_NO_ELIGIBLE_DOCUMENTS until deployment evidence exists',
            'docx_layout_verified': 'XML inspected; Word visual renderer not attached',
            'tiny_training_mechanics_verified': 'tests/test_training_objective.py adapter hash change',
            'target_model_smoke_verified': 'Qwen assets not attached on author host',
        },
        'limitations': [
            'No full Qwen LoRA research training in this delivery.',
            'No Kaggle GPU execution receipt.',
            'DOCX layout is XML-inspected, not visually page-rendered.',
            'Eligible knowledge corpus remains unknown/empty.',
        ],
    }
    write_json(output / 'delivery-manifest.json', manifest)
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Package Kaggle source delivery')
    parser.add_argument('--config', default=str(IMPL / 'configs' / 'kaggle.yaml'))
    parser.add_argument('--output', default=str(IMPL / 'artifacts' / 'kaggle-delivery' / 'v1'))
    args = parser.parse_args(argv)
    manifest = package(Path(args.config), Path(args.output))
    print(json.dumps({'zip': manifest['artifacts']['source_zip']['path'], 'inventory': len(manifest['inventory'])}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
