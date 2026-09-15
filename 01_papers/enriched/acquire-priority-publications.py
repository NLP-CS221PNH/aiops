"""Resolve priority publication metadata; exact title and author checks, no fuzzy automatic merge."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,quote
spec=importlib.util.spec_from_file_location('acq',Path(__file__).with_name('acquire-metadata.py'));acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
BASE=Path(__file__).resolve().parent
rs=[json.loads(x) for x in (BASE/'catalog-enriched.jsonl').read_text(encoding='utf-8').splitlines()]
ix={x['paper_id']:x for x in map(json.loads,(BASE/'priority-source-index.jsonl').read_text(encoding='utf-8').splitlines())}
out=[]
for r in rs:
 if not r['research']['priority_reading']:continue
 pid=r['paper_id'];meta=r['research'].get('metadata',{});doi=ix.get(pid,{}).get('primary_metadata',{}).get('doi')
 if pid=='P0410':doi='10.1109/ICWS.2017.13'
 if pid=='P0757':doi='10.1145/3701716.3715290' # inspected primary fulltext frontmatter
 u=('https://api.crossref.org/works/'+quote(doi,safe='')) if doi else 'https://api.crossref.org/works?'+urlencode({'query.bibliographic':r['title'],'rows':'3'})
 e=acq.fetch(u,'priority_publication_metadata',1.0);row={'paper_id':pid,'source_url':u,'status':e['status'],'candidates':[]}
 if e['status']==200 and e['text'].lstrip().startswith('{'):
  msg=json.loads(e['text']).get('message',{});items=[msg] if doi else msg.get('items',[])
  for a in items:
   m=acq.from_crossref(a,'https://api.crossref.org/works/'+quote(a.get('DOI',''),safe=''));sim=acq.matches(m.get('title') or '',r)
   aa={acq.norm(x.split(',')[0].split()[-1]) for x in meta.get('authors',[]) if x}
   bb={acq.norm(x.get('family','')) for x in a.get('author',[]) if x.get('family')}
   overlap=len(aa&bb);accepted=sim>=.97 and (overlap>=min(2,len(aa)) if aa else bool(doi))
   row['candidates'].append({'metadata':m,'title_similarity':round(sim,4),'author_surname_overlap':overlap,'accepted':accepted})
   if accepted:row['resolved_metadata']=m;break
 out.append(row)
 print(pid,'resolved' if row.get('resolved_metadata') else 'unresolved',flush=True)
 (BASE/'priority-publication-resolution.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in out)+'\n',encoding='utf-8')
