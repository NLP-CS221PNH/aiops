"""Read-only public metadata collection; cache, one connection, resumable, no PDF bulk download."""
import csv, difflib, hashlib, html, json, re, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote, urlparse
from urllib.error import HTTPError
from html.parser import HTMLParser
from datetime import datetime, timezone

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent
CACHE=BASE/'cache'; CACHE.mkdir(exist_ok=True)
LOG=BASE/'acquisition-log.jsonl'
NOW=lambda: datetime.now(timezone.utc).isoformat()
last={}; blocked={}
class Page(HTMLParser):
 def __init__(self):
  super().__init__(); self.meta={}; self.text=[]; self.links=[]; self.skip=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('script','style'):self.skip+=1
  if tag=='meta':
   k=a.get('name',a.get('property','')).lower()
   if k:self.meta.setdefault(k,[]).append(html.unescape(a.get('content','')))
  if tag=='a' and a.get('href'):self.links.append(a['href'])
  if tag in ('p','section','h1','h2','h3','h4','tr','li'):self.text.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.text.append(data)

def fetch(url,kind='metadata',delay=0.65):
 key=hashlib.sha256(url.encode()).hexdigest(); path=CACHE/(key+'.json')
 if path.exists():return json.loads(path.read_text(encoding='utf-8'))
 host=urlparse(url).netloc
 if host in blocked:return {'url':url,'status':'host_backoff_after_429','text':''}
 time.sleep(max(0,delay-(time.monotonic()-last.get(host,0))))
 entry={'url':url,'requested_at':NOW(),'kind':kind}
 try:
  req=Request(url,headers={'User-Agent':'CS221-AIOps-RAG-Research/1.0 (personal academic metadata research)','Accept':'application/json,text/html,application/atom+xml;q=0.9,*/*;q=0.5'})
  with urlopen(req,timeout=22) as r:
   b=r.read(12_000_000);entry.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type',''),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
   if 'pdf' in entry['content_type'].lower() or b[:4]==b'%PDF':entry['status']='pdf_skipped_metadata_first';entry['text']=''
   else:entry['text']=b.decode('utf-8',errors='replace')
 except HTTPError as e:
  entry.update(status=e.code,error=str(e),text='')
  if e.code==429:blocked[host]=True
 except Exception as e:entry.update(status='network_error',error=type(e).__name__+': '+str(e),text='')
 last[host]=time.monotonic();path.write_text(json.dumps(entry,ensure_ascii=False),encoding='utf-8')
 with LOG.open('a',encoding='utf-8') as f:f.write(json.dumps({k:v for k,v in entry.items() if k!='text'},ensure_ascii=False)+'\n')
 return entry

def norm(s):return re.sub(r'[^a-z0-9]','',html.unescape(s).lower())
def matches(title,rec):
 vals=[rec['title']]+rec.get('original_titles',[])
 return max(difflib.SequenceMatcher(None,norm(title),norm(t)).ratio() for t in vals)
def from_datacite(a):
 return {'title':a.get('titles',[{}])[0].get('title'), 'authors':[c.get('name') for c in a.get('creators',[])], 'publication_year':a.get('publicationYear'),'year_basis':'arxiv_preprint_registration','venue':None,'publisher':a.get('publisher'),'arxiv_doi':a.get('doi'),'abstract':'\n'.join(d.get('description','') for d in a.get('descriptions',[]) if d.get('descriptionType')=='Abstract'),'version':a.get('version'),'dates':a.get('dates',[]),'licenses':a.get('rightsList',[]),'related_identifiers':a.get('relatedIdentifiers',[]),'metadata_source_url':'https://api.datacite.org/dois/'+a['doi'],'source_kind':'arxiv_deposited_datacite_metadata'}
def from_crossref(a,url):
 date=a.get('published',a.get('published-print',a.get('published-online',{}))).get('date-parts',[[]])[0]
 title=a.get('title',[None])[0];subtitle='; '.join(a.get('subtitle',[]))
 if subtitle and norm(subtitle) not in norm(title or ''):title=(title or '')+': '+subtitle
 return {'title':title,'authors':[(' '.join([c.get('given',''),c.get('family','')]).strip() or c.get('name')) for c in a.get('author',[])],'publication_year':date[0] if date else None,'year_basis':'crossref_published','venue':'; '.join(a.get('container-title',[])) or None,'publisher':a.get('publisher'),'doi':a.get('DOI'),'abstract':re.sub('<[^>]*>',' ',a.get('abstract','')),'licenses':a.get('license',[]),'publication_type':a.get('type'),'metadata_source_url':url,'source_kind':'publisher_deposited_crossref_metadata'}
def from_page(entry):
 p=Page();p.feed(entry.get('text',''));m=p.meta
 one=lambda *keys:next((m[k][0] for k in keys if m.get(k)),None)
 title=one('citation_title','dc.title','dc.title','og:title')
 authors=m.get('citation_author',m.get('dc.creator',[]))
 date=one('citation_publication_date','citation_date','dc.date','dc.date.issued')
 year=re.search(r'(19|20)\d{2}',date or '')
 abstract=one('citation_abstract')
 if 'aclanthology.org' in entry['url']:
  am=re.search(r'&lt;abstract&gt;(.*?)&lt;/abstract&gt;',entry.get('text',''),re.S)
  if am:abstract=re.sub(r'<[^>]*>',' ',html.unescape(am.group(1)))
 venue=one('citation_conference_title','citation_journal_title','citation_inbook_title')
 return {'title':title,'authors':authors,'publication_year':int(year[0]) if year else None,'date':date,'year_basis':'primary_page_citation_tags','venue':venue,'doi':one('citation_doi','dc.identifier'),'abstract':abstract,'page_description':one('description','og:description'),'metadata_source_url':entry['url'],'source_kind':'primary_page_citation_tags','fulltext_links':[x for x in p.links if '/html/' in x or x.endswith('.pdf')],'citation_tags':m}

def main():
 records=[json.loads(x) for x in (ROOT/'01_papers/catalog.jsonl').read_text(encoding='utf-8').splitlines()]
 priorities=re.findall(r'### \d+\. \[(P\d+)',(ROOT/'01_papers/priority_reading.md').read_text(encoding='utf-8'))
 mapping={}; arx=[r for r in records if r.get('arxiv_id')]
 for i in range(0,len(arx),40):
  ids=['10.48550/arXiv.'+re.sub(r'v\d+$','',r['arxiv_id']) for r in arx[i:i+40]]
  u='https://api.datacite.org/dois?'+urlencode({'query':'id:('+' OR '.join(ids)+')','page[size]':'100'})
  e=fetch(u)
  if e['status']==200:
   for d in json.loads(e['text']).get('data',[]):mapping[d['id'].lower()]=from_datacite(d['attributes'])
  print('datacite_batch',i,len(mapping),flush=True)
 out=[]
 ordered=sorted(records,key=lambda r:(r['paper_id'] not in priorities,r['paper_id']))
 for i,r in enumerate(ordered):
  meta=None;status='not_attempted';e={}
  if r.get('arxiv_id'):
   meta=mapping.get(('10.48550/arxiv.'+re.sub(r'v\d+$','',r['arxiv_id'])).lower());status='ok' if meta else 'identifier_not_returned'
  elif r.get('doi'):
   u='https://api.crossref.org/works/'+quote(r['doi'],safe='');e=fetch(u)
   status=e['status']
   if status==200:
    try:meta=from_crossref(json.loads(e['text'])['message'],u)
    except Exception:status='parse_error'
  elif r.get('acl_id'):
   e=fetch(r['canonical_url']);status=e['status']
   if status==200:meta=from_page(e)
  elif '/pdf/' in r['canonical_url'] or r['canonical_url'].lower().endswith('.pdf'):
   status='pdf_skipped_metadata_first'
  elif 'openreview.net/forum?' in r['canonical_url']:
   nid=r['canonical_url'].split('id=')[-1].split('&')[0];u='https://api2.openreview.net/notes?id='+quote(nid);e=fetch(u);status=e['status']
   if status==200 and e['text'].lstrip().startswith('{'):
    js=json.loads(e['text']);notes=js.get('notes',[])
    if notes:
     n=notes[0];c=n.get('content',{});v=lambda k:c.get(k,{}).get('value') if isinstance(c.get(k),dict) else c.get(k)
     meta={'title':v('title'),'authors':v('authors'),'abstract':v('abstract'),'venue':v('venue'),'publication_year':datetime.fromtimestamp(n.get('pdate',n.get('cdate',0))/1000,timezone.utc).year if n.get('pdate',n.get('cdate')) else None,'year_basis':'openreview_note_date','metadata_source_url':u,'source_kind':'openreview_primary_api','publication_date_millis':n.get('pdate'),'license':n.get('license'),'pdf':v('pdf')}
    else:status='openreview_note_not_returned'
   elif status==200:status='non_json_interstitial_unreadable'
  else:
   e=fetch(r['canonical_url']);status=e['status']
   if status==200:meta=from_page(e)
  rr=dict(r);research={'metadata_checked_at':NOW(),'acquisition_status':status,'priority_reading':r['paper_id'] in priorities,'read_depth':'metadata_only'}
  if meta and meta.get('title'):
   sim=matches(meta['title'],r);research.update(metadata=meta,title_similarity=round(sim,4),identity_status='matched' if sim>=.9 else 'title_mismatch_review_required')
   if sim>=.9:
    research['verified_fields']=[f for f in ['title','authors','publication_year','venue'] if meta.get(f)]
    research['read_depth']='abstract_available_not_read' if meta.get('abstract') else 'metadata_only'
  else:research['identity_status']='unresolved'
  rr['research']=research;out.append(rr)
  if (i+1)%25==0:print('processed',i+1,'/',len(records),flush=True)
 out.sort(key=lambda r:r['paper_id'])
 (BASE/'catalog-enriched.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in out)+'\n',encoding='utf-8')
 print('DONE',len(out),flush=True)
if __name__=='__main__':main()
