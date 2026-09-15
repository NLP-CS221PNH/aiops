"""Write a streaming SHA-256 manifest only after artifact and handoff validation pass."""
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.runtime-python', '__pycache__', '.git', '.agents', '.codex', 'node_modules'}
MANIFEST = ROOT / 'MANIFEST_RESEARCH_SHA256.txt'
INVENTORY = ROOT / '04_audit/research-file-inventory.tsv'


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and p not in {MANIFEST, INVENTORY} and not any(x in EXCLUDED or x.startswith('annotation-protection-') for x in p.relative_to(ROOT).parts))


for name in ['04_audit/research-pack-validation.json', '04_audit/handoff-files-validation.json']:
    result = json.loads((ROOT / name).read_text(encoding='utf-8'))
    if not result['passed']:
        raise SystemExit(f'Cannot freeze while validation fails: {name}')

rows = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files()]
with INVENTORY.open('w', encoding='utf-8', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['path', 'bytes', 'sha256'], delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)
rows.append({'path': INVENTORY.relative_to(ROOT).as_posix(), 'bytes': INVENTORY.stat().st_size, 'sha256': sha(INVENTORY)})
MANIFEST.write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in sorted(rows, key=lambda r: r['path'])), encoding='utf-8')
print(json.dumps({'frozen_at': datetime.now(timezone.utc).isoformat(), 'payload_files': len(rows), 'payload_bytes': sum(r['bytes'] for r in rows), 'manifest': str(MANIFEST), 'excluded': sorted(EXCLUDED), 'note': 'Runtime package binaries are excluded; data-runtime.json records the tested interpreter and PyArrow versions.'}))
