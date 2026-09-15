"""Acquire linked HTML for priority reading; no bulk PDF acquisition."""
import importlib.util,json,re,sys,time
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('acq',Path(__file__).with_name('acquire-metadata.py'));acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
BASE=Path(__file__).resolve().parent
TEXT=BASE/'primary-text';TEXT.mkdir(exist_ok=True)
ROOT=BASE.parent.parent
records={r['paper_id']:r for r in map(json.loads,(ROOT/'01_papers/catalog.jsonl').read_text(encoding='utf-8').splitlines())}
ids=re.findall(r'### \d+\. \[(P\d+)',(ROOT/'01_papers/priority_reading.md').read_text(encoding='utf-8'))
index=[]
for pid in ids:
 r=records[pid];u=r['canonical_url'];row={'paper_id':pid,'landing_url':u,'fulltext_status':'not_available'}
 if r.get('arxiv_id') or r.get('acl_id'):
  e=acq.fetch(u,delay=3.2 if r.get('arxiv_id') else 1.0)
  row['landing_status']=e['status']
  if e['status']==200:
   m=acq.from_page(e);row['primary_metadata']=m
   p=acq.Page();p.feed(e['text'])
   abstract=' '.join(''.join(p.text).split())
   (TEXT/(pid+'-landing.txt')).write_text(abstract,encoding='utf-8')
   links=[urljoin(u,x) for x in p.links if '/html/' in x and 'arxiv.org' in urljoin(u,x)]
   if links:
    ht=acq.fetch(links[0],'fulltext_html',3.2);row.update(fulltext_url=links[0],fulltext_status=ht['status'])
    if ht['status']==200:
     pp=acq.Page();pp.feed(ht['text']);txt=''.join(pp.text);txt=re.sub(r'[ \t]+',' ',txt);txt=re.sub(r'\n\s*\n+','\n\n',txt)
     path=TEXT/(pid+'-fulltext.txt');path.write_text(txt,encoding='utf-8');row['local_text']=str(path.relative_to(ROOT));row['text_characters']=len(txt)
   if r.get('acl_id'):
    be=acq.fetch(u.rstrip('/')+'.bib','official_bibtex');row['official_bibtex_status']=be['status']
    if be['status']==200:(TEXT/(pid+'-official.bib')).write_text(be['text'],encoding='utf-8')
 index.append(row)
 (BASE/'priority-source-index.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in index)+'\n',encoding='utf-8')
 print(pid,row.get('landing_status'),row['fulltext_status'],row.get('text_characters'),flush=True)

# Freshness additions are separate candidates, never silently merged into original catalog.
new=[]
for aid in ['2604.13522','2607.01788','2508.12472','2608.08968','2608.21310','2607.04623']:
 u='https://arxiv.org/abs/'+aid;e=acq.fetch(u,delay=3.2)
 row={'arxiv_id':aid,'source_url':u,'retrieved_at':acq.NOW(),'status':e['status'],'catalog_overlap':[r['paper_id'] for r in records.values() if r.get('arxiv_id')==aid],'read_depth':'metadata_only'}
 if e['status']==200:row['metadata']=acq.from_page(e);row['read_depth']='abstract_available_not_read'
 new.append(row)
(BASE/'freshness-additions.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in new)+'\n',encoding='utf-8')
