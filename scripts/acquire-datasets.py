"""Passive, revision-pinned RCAEval acquisition. No remote dataset code is executed.

Run with Python 3.11 after installing pyarrow to .runtime-python:
  python scripts/acquire-datasets.py metadata
  python scripts/acquire-datasets.py pilot
  python scripts/acquire-datasets.py full
Full requires the locally verified pilot report; never downloads other suites.
"""
from pathlib import Path
import argparse, csv, datetime, hashlib, json, shutil, sys, time, urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.runtime-python'))
BASE = ROOT / '02_datasets/acquired'
META, LABELS, RAW = BASE/'meta', BASE/'labels', BASE/'raw'
for d in (META, LABELS, RAW): d.mkdir(parents=True, exist_ok=True)
REPO = 'phamquiluan/RCAEval'
REV = 'afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
UA = 'CS221-academic-research-pack/1.0 (passive-public-data-download)'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda:f.read(1024*1024), b''): h.update(buf)
    return h.hexdigest()

def fetch(url, target, sha=None, size=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (not size or target.stat().st_size == size):
        found = digest(target)
        if not sha or sha == found: return found
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':UA})
            with urllib.request.urlopen(req, timeout=120) as src, target.with_suffix(target.suffix+'.part').open('wb') as dst:
                shutil.copyfileobj(src, dst, 1024*1024)
            tmp = target.with_suffix(target.suffix+'.part')
            found = digest(tmp)
            if sha and found != sha: raise ValueError('SHA256 mismatch: '+url)
            if size is not None and tmp.stat().st_size != size: raise ValueError('size mismatch: '+url)
            tmp.replace(target)
            time.sleep(0.1)
            return found
        except Exception:
            if attempt == 3: raise
            time.sleep(2**attempt)

def hf(path): return f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/{path}'
def incident(case): return 'inc_' + hashlib.sha256(('RCAEval:'+case).encode()).hexdigest()[:16]
def write_json(path, obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def metadata():
    source=ROOT/'02_datasets/rcaeval-hf-api.json'
    if source.exists(): shutil.copy2(source, META/'hf-api-discovery.json')
    url=f'https://huggingface.co/api/datasets/{REPO}/revision/{REV}?blobs=true'
    fetch(url, META/'hf-api-pinned.json')
    api=json.loads((META/'hf-api-pinned.json').read_text(encoding='utf-8'))
    assert api['sha']==REV and api['cardData']['license']=='mit'
    fetch(hf('README.md'), META/'RCAEval-HF-README.md')
    index_item=next(x for x in api['siblings'] if x['rfilename']=='cases.parquet')
    fetch(hf('cases.parquet'), LABELS/'cases.parquet',(index_item.get('lfs') or {}).get('sha256'),index_item.get('size'))
    fetch('https://api.github.com/repos/phamquiluan/RCAEval/commits/main',META/'github-main-commit.json')
    gh=json.loads((META/'github-main-commit.json').read_text())['sha']
    for name in ('README.md','LICENSE'):
        fetch(f'https://raw.githubusercontent.com/phamquiluan/RCAEval/{gh}/{name}', META/('RCAEval-GitHub-'+name))
    assert 'for our datasets' in (META/'RCAEval-GitHub-README.md').read_text(encoding='utf-8')
    try: fetch('https://zenodo.org/api/records/14590730',META/'zenodo-14590730.json')
    except Exception as e: write_json(META/'zenodo-status.json',{'status':'not_acquired','reason':str(e)})
    import pyarrow.parquet as pq
    rows=pq.read_table(LABELS/'cases.parquet').to_pylist()
    write_json(LABELS/'cases-index.json',rows)
    sets={}
    for r in rows:
        group=r.get('dataset',r.get('suite','unknown'))
        sets[group]=sets.get(group,0)+1
    ob=[x for x in api['siblings'] if x['rfilename'].startswith('re2ob_')]
    tt=[x for x in api['siblings'] if x['rfilename'].startswith('re2tt_')]
    info={'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hf_revision':REV,'github_revision':gh,'license_data':'MIT','license_evidence_url':f'https://github.com/phamquiluan/RCAEval/blob/{gh}/README.md#licensing','license_snapshot_sha256':digest(META/'RCAEval-GitHub-LICENSE'),'case_counts':sets,'RE2_OB_files':len(ob),'RE2_OB_bytes':sum(x.get('size',0) for x in ob),'RE2_TT_files':len(tt),'RE2_TT_bytes':sum(x.get('size',0) for x in tt),'manifest_url':url,'release_lineage':'HF author-provided Parquet mirror of RCAEval, not an independent dataset','available_at':'2026-09-12','historical_online_claim':False}
    write_json(META/'source-registry.json',info)
    print(json.dumps(info,ensure_ascii=False),flush=True)
    print('Index schema:',pq.read_schema(LABELS/'cases.parquet'),flush=True)

def acquire(mode):
    api=json.loads((META/'hf-api-pinned.json').read_text(encoding='utf-8'))
    assert api['sha']==REV and api['cardData']['license']=='mit'
    files=[x for x in api['siblings'] if x['rfilename'].startswith('re2ob_')]
    cases=sorted({x['rfilename'].split('/')[0] for x in files})
    assert len(cases)==90
    if mode=='pilot': cases=cases[:1]
    else:
        pilot=json.loads((META/'pilot-schema.json').read_text(encoding='utf-8'))
        assert pilot['schema_gate']=='pass', 'Run and inspect pilot first'
    manifest_path=LABELS/'acquisition-manifest.jsonl'
    old={}
    if manifest_path.exists():
        old={x['source_path']:x for x in map(json.loads,manifest_path.read_text().splitlines())}
    for idx,case in enumerate(cases):
        for item in [x for x in files if x['rfilename'].split('/')[0]==case]:
            path=item['rfilename']; name=path.split('/')[-1]; iid=incident(case)
            target=(LABELS/'injection'/iid/name) if name=='inject_time.txt' else (RAW/iid/name)
            lfs=item.get('lfs') or {}; sha=lfs.get('sha256'); size=item.get('size')
            found=fetch(hf(path),target,sha,size)
            old[path]={'incident_id':iid,'source_path':path,'source_url':hf(path),'local_path':target.relative_to(ROOT).as_posix(),'release_revision':REV,'bytes':target.stat().st_size,'sha256':found,'upstream_sha256':sha,'upstream_hash_verified':bool(sha),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'data_kind':'label' if name=='inject_time.txt' else 'observation'}
            manifest_path.write_text(''.join(json.dumps(old[k],ensure_ascii=False)+'\n' for k in sorted(old)),encoding='utf-8')
        print(f'{mode}: {idx+1}/{len(cases)} cases; {iid}',flush=True)
    import pyarrow.parquet as pq
    if mode=='pilot':
        iid=incident(cases[0]); schemas={}
        for p in sorted((RAW/iid).glob('*.parquet')):
            pf=pq.ParquetFile(p)
            sample=next(pf.iter_batches(batch_size=3)).to_pylist()
            schemas[p.name]={'rows':pf.metadata.num_rows,'columns':pf.schema_arrow.names,'schema':str(pf.schema_arrow),'sample':sample}
        report={'incident_id':iid,'schema_gate':'pass' if set(schemas)=={'logs.parquet','metrics.parquet','traces.parquet'} else 'fail','schemas':schemas,'execution':'Parquet read only; no remote loader/pickle/notebook executed'}
        write_json(META/'pilot-schema.json',report)
        print(json.dumps(report,ensure_ascii=False,default=str)[:24000],flush=True)
    if mode=='full':
        assert len(old)==360 and sum(v['bytes'] for v in old.values())==922484805
    with (LABELS/'acquisition-manifest.tsv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(next(iter(old.values()))),delimiter='\t');writer.writeheader();writer.writerows(old[k] for k in sorted(old))
    write_json(META/'acquisition-status.json',{'mode':mode,'downloaded_case_count':len(list(RAW.iterdir())),'downloaded_file_count':len(old),'complete_RE2_OB':len(old)==360,'revision':REV,'bytes':sum(v['bytes'] for v in old.values()),'parquet_upstream_sha256_verified':sum(x['upstream_hash_verified'] for x in old.values())})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['metadata','pilot','full']);a=p.parse_args()
    metadata() if a.mode=='metadata' else acquire(a.mode)
