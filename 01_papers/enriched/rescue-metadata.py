"""Additive rescue of unresolved paper metadata using public primary registries.
Never mutates catalog-enriched.jsonl or the first collector's caches.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote,urlencode,urlparse
from urllib.error import HTTPError
import collections,datetime,difflib,hashlib,html,importlib.util,json,re,time,unicodedata
BASE=Path(__file__).resolve().parent;CACHE=BASE/'rescue-cache';CACHE.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('base_metadata',BASE/'acquire-metadata.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
last={};blocked=set();log=BASE/'rescue-acquisition-log.jsonl'

def fetch(url):
    key=hashlib.sha256(url.encode()).hexdigest()+'.json';p=CACHE/key
    if p.exists():return json.loads(p.read_text(encoding='utf-8'))
    prior=BASE/'cache'/key
    if prior.exists():
        old=json.loads(prior.read_text(encoding='utf-8'))
        if old.get('status')==200:return old
    host=urlparse(url).netloc
    if host in blocked:return {'status':'host_backoff_after_429','url':url,'text':''}
    time.sleep(max(0,.9-(time.monotonic()-last.get(host,0))))
    e={'url':url,'requested_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req=Request(url,headers={'User-Agent':'CS221-AIOps-RAG-Research/1.0 (academic bibliographic metadata only)','Accept':'application/json,text/html;q=0.9'})
        with urlopen(req,timeout=18) as r:
            kind=r.headers.get('Content-Type','');e.update(status=r.status,final_url=r.url,content_type=kind)
            if r.status in (202,403) or 'pdf' in kind.lower():e.update(text='',status='challenge_or_pdf_not_read')
            else:
                raw=r.read(5_000_000);e.update(text=raw.decode('utf-8',errors='replace'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    except HTTPError as exc:
        e.update(status=exc.code,text='',error=str(exc))
        if exc.code==429:blocked.add(host)
    except Exception as exc:e.update(status='network_error',text='',error=type(exc).__name__+': '+str(exc))
    last[host]=time.monotonic();p.write_text(json.dumps(e,ensure_ascii=False),encoding='utf-8')
    with log.open('a',encoding='utf-8') as f:f.write(json.dumps({k:v for k,v in e.items() if k!='text'})+'\n')
    return e

def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',html.unescape(re.sub('<[^>]+>',' ',s or ''))).casefold())
def similarity(a,b):return difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()
def exact(title,r):return any(norm(title)==norm(t) for t in [r['title']]+r.get('original_titles',[]))
def document(entry):
    if entry.get('status')!=200:return None
    try:return json.loads(entry.get('text',''))
    except ValueError:return None

def landings(url):
    out=[]
    if 'proceedings.mlr.press/' in url and url.endswith('.pdf'):out.append(url[:-4]+'.html')
    if 'jmlr.org/papers/volume' in url:
        hit=re.search(r'/volume(\d+)/([^/]+)/',url)
        if hit:out.append(f'https://www.jmlr.org/papers/v{hit[1]}/{hit[2]}.html')
    if ('neurips.cc/' in url or 'nips.cc/' in url) and '/file/' in url:
        out.append(re.sub(r'-Paper(?:-Conference)?\.pdf$','-Abstract.html',url.replace('/file/','/hash/')))
    if 'ijcai.org/' in url and url.endswith('.pdf'):out.append(re.sub(r'\.pdf$','',url).replace('/Proceedings/','/proceedings/'))
    if 'usenix.org/system/files/' in url:
        name=url.rsplit('/',1)[-1]
        match=re.match(r'([a-z]+\d{2})-(?:paper-)?([^/.]+)',name)
        if match and not match[2].startswith('final'):
            out.append(f'https://www.usenix.org/conference/{match[1]}/presentation/{match[2].replace("_0","")}')
    if 'usenix.org/conference/' in url:out.append(url)
    if 'berkeley.edu/Pubs/TechRpts/' in url:out.append(url[:-4]+'.html')
    return list(dict.fromkeys(out))

def resolved(rec,meta,evidence,method):
    return {'paper_id':rec['paper_id'],'original_title':rec['title'],'original_url':rec['canonical_url'],'source_url':meta.get('metadata_source_url'),'identity_status':'matched','rescue_status':'resolved','title':meta['title'],'authors':meta.get('authors'),'publication_year':meta.get('publication_year'),'year_basis':meta.get('year_basis'),'venue':meta.get('venue'),'doi':meta.get('doi'),'arxiv_doi':meta.get('arxiv_doi'),'identity_evidence':evidence,'resolution_method':method,'resolved_metadata':meta,'verified_fields':[k for k in ('title','authors','publication_year','venue') if meta.get(k)],'full_text_read':False,'original_url_equivalence':'see identity evidence; a title-resolved DOI does not verify an inaccessible original URL'}

def rescue(r):
    attempts=[];u=r['canonical_url'];title=r['title'];source_doi=r.get('doi')
    if not source_doi:
        hit=re.search(r'(10\.\d{4,9}/[^?# ]+)',u)
        if hit:source_doi=hit[1].rstrip('/')
    if r['paper_id']=='P0810':
        return {'paper_id':r['paper_id'],'original_title':title,'original_url':u,'identity_status':'title_mismatch_review_required','rescue_status':'still_unresolved','reason':'Existing DOI is a valid ExaRanker publication but supplied title is not the registered title. No original-title alias evidence; do not silently replace/claim matched.','candidate_metadata':r.get('research',{}).get('metadata')}
    for landing in landings(u):
        e=fetch(landing);attempts.append({'url':landing,'status':e.get('status'),'method':'primary_landing_transform'})
        if e.get('status')!=200:continue
        meta=m.from_page(e)
        if meta.get('title') and exact(meta['title'],r) and meta.get('authors'):
            return resolved(r,meta,{'title_exact_after_typographic_normalization':True,'primary_landing_title_verified':True,'original_url_to_landing':'deterministic publisher URL structure','attempts':attempts},'primary_landing_citation_metadata')
    if source_doi:
        du='https://api.crossref.org/works/'+quote(source_doi,safe='');e=fetch(du);js=document(e)
        attempts.append({'url':du,'status':e.get('status'),'method':'original_identifier_crossref'})
        if js and js.get('message',{}).get('DOI'):
            meta=m.from_crossref(js['message'],du)
            if exact(meta['title'],r):return resolved(r,meta,{'title_exact_after_typographic_normalization':True,'original_doi_verified':source_doi,'attempts':attempts},'original_DOI_registry')
    query='https://api.crossref.org/works?'+urlencode({'query.bibliographic':title,'rows':3})
    e=fetch(query);js=document(e);attempts.append({'url':query,'status':e.get('status'),'method':'crossref_exact_title_candidate_search'})
    candidates=[]
    for item in ((js or {}).get('message',{}).get('items',[])):
        du='https://api.crossref.org/works/'+quote(item.get('DOI',''),safe='');meta=m.from_crossref(item,du)
        sim=max(similarity(meta.get('title'),t) for t in [title]+r.get('original_titles',[]))
        candidate={'title':meta.get('title'),'doi':item.get('DOI'),'title_similarity':round(sim,4),'exact_title':exact(meta.get('title'),r)}
        candidates.append(candidate)
        if not candidate['exact_title'] or len(norm(title))<25 or not meta.get('authors'):continue
        primary=fetch(du);pj=document(primary);attempts.append({'url':du,'status':primary.get('status'),'method':'independent_DOI_registration_confirmation'})
        if not pj:continue
        confirmed=pj.get('message',{})
        if confirmed.get('DOI','').lower()!=item['DOI'].lower():continue
        meta2=m.from_crossref(confirmed,du)
        if not exact(meta2['title'],r):continue
        identifier_in_source=bool(source_doi and source_doi.lower()==confirmed['DOI'].lower())
        ieee=re.search(r'ieeexplore\.ieee\.org/document/(\d+)',u)
        registered_urls=[x.get('URL','') for x in confirmed.get('link',[])]+[confirmed.get('resource',{}).get('primary',{}).get('URL','')]
        if ieee and any(ieee[1] in z for z in registered_urls):identifier_in_source=True
        return resolved(r,meta2,{'title_exact_after_typographic_normalization':True,'new_identifier_confirmed_by_primary_DOI_registration':confirmed['DOI'],'original_url_identifier_corroborated':identifier_in_source,'registered_resource_urls':registered_urls,'original_url_not_retried_if_challenged':True,'candidate_count_returned':len((js or {}).get('message',{}).get('items',[])),'attempts':attempts},'exact_title_plus_confirmed_publisher_DOI_registration')
    # Crossref often omits ICLR/NeurIPS. Search primary DataCite records only after no exact registry match.
    if 'openreview.net' in u or 'neurips.cc' in u or 'nips.cc' in u or r['topic_code'] in ('LLM_AIOPS_RCA',):
        query='https://api.datacite.org/dois?'+urlencode({'query':'titles.title:"'+title.replace('"','')+'"','page[size]':5})
        e=fetch(query);js=document(e);attempts.append({'url':query,'status':e.get('status'),'method':'datacite_exact_title_search'})
        for item in ((js or {}).get('data',[])):
            if not item.get('id','').lower().startswith('10.48550/arxiv.'):
                continue  # Do not confuse similarly titled datasets/software with papers.
            a=item.get('attributes',{});t=(a.get('titles') or [{}])[0].get('title')
            if not exact(t,r) or not a.get('creators'):continue
            du='https://api.datacite.org/dois/'+quote(item['id'],safe='/');primary=fetch(du);pjs=document(primary)
            if not pjs:continue
            b=pjs.get('data',{}).get('attributes',{});t2=(b.get('titles') or [{}])[0].get('title')
            if not exact(t2,r):continue
            meta=m.from_datacite(b)
            if not item['id'].lower().startswith('10.48550/arxiv.'):
                meta['year_basis']='datacite_publication_year';meta['source_kind']='primary_datacite_registration'
            return resolved(r,meta,{'title_exact_after_typographic_normalization':True,'new_identifier_confirmed_by_primary_DOI_registration':item['id'],'original_url_identifier_corroborated':False,'publication_identity_limit':'preprint metadata does not establish peer-reviewed conference version','attempts':attempts},'exact_title_plus_confirmed_DataCite_registration')
    return {'paper_id':r['paper_id'],'original_title':title,'original_url':u,'identity_status':'unresolved','rescue_status':'still_unresolved','reason':'No exact title match with primary citation metadata or confirmed DOI registration; candidates retained, not auto-accepted.','candidates':candidates,'attempts':attempts,'full_text_read':False}

def main():
    records=[json.loads(x) for x in (BASE/'catalog-enriched.jsonl').read_text(encoding='utf-8').splitlines()]
    out=[];path=BASE/'rescue-metadata.jsonl'
    old={x['paper_id']:x for x in map(json.loads,path.read_text(encoding='utf-8').splitlines())} if path.exists() else {}
    targets=[r for r in records if r.get('research',{}).get('identity_status')!='matched' or r['paper_id'] in old]
    targets=sorted(targets,key=lambda r:(r['topic_code'] not in ('AIOPS_RCA','LLM_AIOPS_RCA','LOG_NLP','LOG_TRACE_METRIC'),r['paper_id']))
    for i,r in enumerate(targets):
        if r['paper_id'] in old:x=old[r['paper_id']]
        elif r['paper_id'] in ('P0075','P0410'):x={'paper_id':r['paper_id'],'rescue_status':'owned_by_priority_research','identity_status':'defer_to_priority_artifact','reason':'Already resolved/handled by paper research agent; do not duplicate.'}
        else:
            try:x=rescue(r)
            except Exception as exc:x={'paper_id':r['paper_id'],'rescue_status':'still_unresolved','identity_status':'unresolved','reason':'Processing error: '+type(exc).__name__+': '+str(exc)}
        out.append(x)
        path.write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in out),encoding='utf-8')
        print(f'{i+1}/{len(targets)} {r["paper_id"]} {x["rescue_status"]}',flush=True)
    additions=BASE/'rescue-publication-additions.jsonl'
    if additions.exists():
        extra={x['paper_id']:x for x in map(json.loads,additions.read_text(encoding='utf-8').splitlines())}
        out=[extra.get(x['paper_id'],x) for x in out]
        path.write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in out),encoding='utf-8')
    extras=BASE/'rescue-extra-metadata.jsonl'
    if extras.exists():
        extra={x['paper_id']:x for x in map(json.loads,extras.read_text(encoding='utf-8').splitlines())}
        merged={x['paper_id']:x for x in out};merged.update(extra)
        out=[merged[k] for k in sorted(merged)]
        path.write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in out),encoding='utf-8')
    counts=dict(collections.Counter(x['rescue_status'] for x in out))
    (BASE/'rescue-summary.json').write_text(json.dumps({'counts':counts,'row_count':len(out),'acceptance_rule':'Exact title after typography-only normalization + primary landing citation authors OR independent DOI registration confirmation. No fuzzy-title candidates accepted.','all_original_urls_reverified':False,'full_text_read':False,'catalog_mutated':False},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts),flush=True)

if __name__=='__main__':main()
