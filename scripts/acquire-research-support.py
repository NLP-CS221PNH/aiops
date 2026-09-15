"""Download passive, pinned model cards and fallback resource metadata (no weights/code execution)."""
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '05_research' / 'source-snapshots'
OUT.mkdir(parents=True, exist_ok=True)
LOG = []


def fetch(url, name):
    path = OUT / name
    if path.exists():
        payload = path.read_bytes()
        status = 'cached'
    else:
        payload = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'CS221-Research-Pack/1.0 (academic metadata acquisition)'})
                with urllib.request.urlopen(req, timeout=45) as response:
                    payload = response.read(12_000_000)
                    status = str(response.status)
                path.write_bytes(payload)
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2:
                    LOG.append({'url': url, 'status': 'failed', 'error': str(exc), 'retrieved_at': datetime.now(timezone.utc).isoformat()})
                    return None
                time.sleep(2 ** attempt)
    LOG.append({'url': url, 'path': path.relative_to(ROOT).as_posix(), 'status': status, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'retrieved_at': datetime.now(timezone.utc).isoformat()})
    return payload


resources = []
for repo, kind in [('intfloat/e5-small-v2', 'models'), ('BAAI/bge-small-en-v1.5', 'models'), ('BAAI/bge-reranker-base', 'models'), ('PrimeQA/TechQA', 'datasets'), ('ibm-research/ITBench-Lite', 'datasets')]:
    slug = repo.lower().replace('/', '--')
    meta_raw = fetch(f'https://huggingface.co/api/{kind}/{repo}', slug + '-api.json')
    if not meta_raw:
        continue
    meta = json.loads(meta_raw)
    revision = meta.get('sha')
    base = 'https://huggingface.co/' + ('datasets/' if kind == 'datasets' else '') + repo
    card = fetch(f'{base}/resolve/{revision}/README.md', slug + '-readme.md')
    small = [x['rfilename'] for x in meta.get('siblings', []) if x['rfilename'].lower() in ['license', 'license.md', 'license.txt', 'config.json', 'tokenizer_config.json', 'modules.json', 'sentence_bert_config.json']]
    for filename in small:
        fetch(f'{base}/resolve/{revision}/{filename}', slug + '-' + filename.lower())
    resources.append({'repo_id': repo, 'resource_kind': kind, 'revision': revision, 'source_url': base, 'license_card': meta.get('cardData', {}).get('license'), 'model_weights_downloaded': False, 'raw_dataset_downloaded': False, 'files_listed': [x['rfilename'] for x in meta.get('siblings', [])], 'status': 'metadata_and_card_only', 'snapshot_slug': slug})
    print(f'Collected {repo} at {revision}', flush=True)

for repo in ['IBM/mt-rag-benchmark', 'castorini/pyserini']:
    slug = repo.lower().replace('/', '--')
    raw = fetch(f'https://api.github.com/repos/{repo}/commits/HEAD', slug + '-commit.json')
    if raw:
        rev = json.loads(raw)['sha']
        fetch(f'https://raw.githubusercontent.com/{repo}/{rev}/README.md', slug + '-readme.md')
        for fname in ['LICENSE']:
            fetch(f'https://raw.githubusercontent.com/{repo}/{rev}/{fname}', slug + '-' + fname.lower())
        resources.append({'repo_id': repo, 'resource_kind': 'repository_docs', 'revision': rev, 'source_url': f'https://github.com/{repo}/tree/{rev}', 'snapshot_slug': slug})

(OUT / 'acquisition-log.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in LOG), encoding='utf-8')
(OUT / 'support-resources.json').write_text(json.dumps(resources, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'resources': len(resources), 'requests': len(LOG), 'failed': sum(x['status'] == 'failed' for x in LOG)}))
