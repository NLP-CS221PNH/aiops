"""Check authored document links, offline HTML data/JS syntax, and annotation overwrite protection."""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
checks = []


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'script':
            self.current = {'type': attrs.get('type', 'javascript'), 'text': ''}
    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.scripts.append(self.current)
            self.current = None


def localtarget(url, base):
    url = unquote(url.split('#', 1)[0])
    if not url or re.match(r'^[a-z][a-z0-9+.-]*://', url, re.I) or url.startswith('mailto:'):
        return None
    return Path(url) if re.match(r'^[A-Za-z]:[/\\]', url) else base / url


bad_links = []
for p in [ROOT / 'START-HERE.md', *sorted((ROOT / '05_research').glob('*.md')), ROOT / '05_research/retrieval-preview/README.md']:
    if not p.is_file():
        bad_links.append(str(p))
        continue
    for match in re.finditer(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
        target = localtarget(match.group(1).strip('<>'), p.parent)
        if target is not None and not target.exists():
            bad_links.append({'from': str(p.relative_to(ROOT)), 'target': match.group(1)})
checks.append({'check': 'authored_markdown_local_links', 'passed': not bad_links, 'details': bad_links})
html = Parser()
html.feed((ROOT / 'START-HERE.html').read_text(encoding='utf-8'))
bad = [u for u in html.links if (p := localtarget(u, ROOT)) is not None and not p.exists()]
checks.append({'check': 'html_static_links', 'passed': not bad, 'details': bad})
data = json.loads(next(s['text'] for s in html.scripts if s['type'] == 'application/json'))
checks.append({'check': 'html_embedded_data_counts', 'passed': len(data['papers']) == 1009 and len(data['observations']) == 90 and len(data['documents']) == 73 and len(data['historicalDocuments']) == 74})
javascript = '\n'.join(s['text'] for s in html.scripts if s['type'] != 'application/json')
syntax = subprocess.run(['node', '--check', '-'], input=javascript, text=True, encoding='utf-8', capture_output=True)
checks.append({'check': 'html_javascript_syntax_only', 'passed': syntax.returncode == 0, 'details': syntax.stderr.strip()})

# Fixtures stay within the workspace; verify the resolved temp target before cleanup.
with tempfile.TemporaryDirectory(prefix='annotation-protection-', dir=str(ROOT)) as tmp:
    base = Path(tmp).resolve()
    assert base.is_relative_to(ROOT.resolve()) and base != ROOT.resolve()
    for rel in ['scripts', '03_collection_plan/knowledge-corpus-historical', '02_datasets/processed', '05_research/retrieval-preview']:
        (base / rel).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'scripts/preview-retrieval.py', base / 'scripts/preview-retrieval.py')
    for rel in ['03_collection_plan/knowledge-corpus-historical/chunks.jsonl', '02_datasets/processed/observations.jsonl', '02_datasets/processed/split-map.tsv']:
        shutil.copy2(ROOT / rel, base / rel)
    a = base / '05_research/retrieval-preview/annotator-a.tsv'
    b = base / '05_research/retrieval-preview/annotator-b.tsv'
    a.write_text('candidate_id\trelevance_grade\trationale\tannotator_id\tannotation_state\nfixture\t2\thuman evidence note\tA\tjudged\n', encoding='utf-8')
    b.write_text('candidate_id\trelevance_grade\trationale\tannotator_id\tannotation_state\nfixture\t\t\t\tunjudged\n', encoding='utf-8')
    before = [p.read_bytes() for p in [a, b]]
    run = subprocess.run([sys.executable, str(base / 'scripts/preview-retrieval.py'), '--prepare-pilot'], capture_output=True, text=True, encoding='utf-8')
    protected = run.returncode != 0 and 'Refusing to overwrite annotations' in run.stderr and before == [p.read_bytes() for p in [a, b]]
    checks.append({'check': 'preview_refuses_overwrite_without_mutating_either_form', 'passed': protected})

report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'passed': all(x['passed'] for x in checks), 'checks': checks, 'browser_visual_validation': 'not_performed_local_file_URL_blocked_by_browser_policy; no workaround attempted', 'script_sha256': hashlib.sha256((ROOT / 'scripts/preview-retrieval.py').read_bytes()).hexdigest()}
(ROOT / '04_audit/handoff-files-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
sys.exit(0 if report['passed'] else 1)
