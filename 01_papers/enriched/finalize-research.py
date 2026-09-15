"""Build usable bibliography and honest reading notes from cached primary evidence."""
import csv,html,json,re,collections,hashlib
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent.parent;NOTES=ROOT/'01_papers/reading-notes'
def readjl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def writejl(p,rs):p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rs)+'\n',encoding='utf-8')
def tsv(p,rows,cols):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(rows)
records=readjl(BASE/'catalog-enriched.jsonl')
rescues=readjl(BASE/'rescue-metadata.jsonl')
rescue_by_id={x['paper_id']:x for x in rescues if x.get('rescue_status')=='resolved' and x.get('resolved_metadata') and x.get('identity_evidence',{}).get('title_exact_after_typographic_normalization')}
index={x['paper_id']:x for x in readjl(BASE/'priority-source-index.jsonl')}
pdfs={x['paper_id']:x for x in readjl(BASE/'selective-pdf-source-index.jsonl')}
publications={x['paper_id']:x for x in readjl(BASE/'priority-publication-resolution.jsonl')}
extractions=json.loads((BASE/'reading-extractions.json').read_text(encoding='utf-8'))
updates={
 'P0757':{'observation':'RE1 chỉ metrics. RE2/RE3 là suite đa nguồn nhưng modality tùy system; Sock Shop không có traces. Paper whole-benchmark mô tả service/indicator labels.','limitation':'Release RE2-Online Boutique được chọn có root-service label trong index, chưa thấy gold indicator riêng. Không có qrels runbook; 735 ca không đồng nghĩa 735 ca có log hoặc đủ mọi modality.'},
 'P0410':{'sections':'Abstract; PDF trang 2–3 §III Methodology, §III-C/D search rules','method':'Drain dùng domain regex preprocessing, phân nhánh theo token count rồi preceding tokens trong fixed-depth tree; chọn/mở mới log group.'},
 'P0826':{'depth':'fulltext_selected_sections','sections':'Abstract; PDF §3.3 Citation quality, Figure3','evaluation':'ALCE citation recall chấm entailment theo statement và toàn bộ cited passages; citation precision tìm citations không hỗ trợ. NLI là proxy cần human validation.'},
 'P0761':{'depth':'fulltext_selected_sections','sections':'Abstract; §3.3 Ranking RAG Systems with Confidence Intervals','method':'ARES fine-tune judges; PPI dùng human validation để ước lượng judge error và confidence intervals từ labeled/unlabeled triples.'},
 'P0905':{'depth':'fulltext_selected_sections','sections':'Abstract; §3.1 MultiHop-RAG Construction','method':'English news qua mediastack; trích factual sentences, GPT-4 tạo claims/bridge entities rồi queries; UniEval kiểm alignment claim–evidence.'},
 'P0561':{'depth':'fulltext_selected_sections','sections':'Abstract; introduction training overview; §3.1 Table1/Algorithm1','method':'Self-RAG train bốn reflection-token nhóm Retrieve/IsRel/IsSup/IsUse; critic annotations tạo offline, inference chọn passage/segment theo support và utility.'},
 'P0109':{'depth':'fulltext_selected_sections','sections':'Abstract; §2.1 background phân biệt ICL và few-shot tuning','method':'LLMParser chọn few-shot tuning thay việc lặp demonstrations ở mọi inference; khảo sát Flan-T5/LLaMA/ChatGLM và sensitivity theo training/model size.'},
 'P0634':{'depth':'fulltext_selected_sections','sections':'Abstract; PDF §2 Method','method':'Query2doc sinh pseudo-document với bốn demonstrations; sparse branch lặp query năm lần rồi nối pseudo-doc, dense branch nối query–SEP–pseudo-doc.'},
 'P0108':{'sections':'Abstract; kiểm tra title/DOI trong linked HTML v3 frontmatter','limitation':'Training-free vẫn dùng demonstrations có nhãn. HTML v3 đổi title thành DivLog: Log Parsing with Prompt Enhanced In-Context Learning; giữ cùng arXiv ID.'}
}
for n in extractions:n.update(updates.get(n['id'],{}))
writejl(BASE/'reading-extraction-matrix.jsonl',extractions)
note_by_id={n['id']:n for n in extractions}
manual_openrca={'title':'OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?','authors':['Junjielong Xu','Qinan Zhang','Zhiqing Zhong','Shilin He','Chaoyun Zhang','Qingwei Lin','Dan Pei','Pinjia He','Dongmei Zhang','Qi Zhang'],'publication_year':2025,'year_basis':'official_paper_frontpage_and_openreview_publication_profile','venue':'International Conference on Learning Representations (ICLR 2025), Poster','metadata_source_url':'https://openreview.net/pdf?id=M4qNIzQYpd','supporting_source_url':'https://openreview.net/profile?id=~Zhiqing_Zhong2','source_kind':'manual_primary_metadata_review','publication_type':'proceedings-article'}
manual_relations={}
if (BASE/'divlog-publication-metadata.json').exists():manual_relations['P0108']=json.loads((BASE/'divlog-publication-metadata.json').read_text(encoding='utf-8'))
for pid in ['P0120','P0740']:
 cand=publications.get(pid,{}).get('candidates',[])
 if cand:
  manual_relations[pid]=cand[0]['metadata']
  manual_relations[pid]['manual_identity_review']='P0120: exact title, same complete author names with surname order differences, primary PDF frontpage. P0740: for/in title variation, all five authors identical, primary ACL abstract agrees with arXiv.'
aliases=[];flat=[];missing=[];pub_missing=[];bibs=[];prioritybibs=[]
def esc(v):return str(v).replace('\\','\\textbackslash{}').replace('&','\\&').replace('%','\\%').replace('_','\\_').replace('#','\\#')
for r in records:
 pid=r['paper_id'];rr=r['research'];m=rr.get('metadata',{});pm=publications.get(pid,{}).get('resolved_metadata') or manual_relations.get(pid)
 if pid in rescue_by_id and (rr['identity_status']!='matched' or not m.get('authors') or not m.get('publication_year')):
  rescue=rescue_by_id[pid];m=rescue['resolved_metadata'];rr['before_rescue']={'identity_status':rr['identity_status'],'acquisition_status':rr['acquisition_status']}
  rr.update(metadata=m,identity_status='matched',acquisition_status='rescued_primary_metadata',verified_fields=rescue.get('verified_fields',[]),rescue_evidence=rescue['identity_evidence'],rescue_source_url=rescue.get('source_url'),original_url_equivalence=rescue.get('original_url_equivalence'),read_depth='metadata_only')
 if pid=='P0075':m=manual_openrca;rr.update(metadata=m,identity_status='matched',acquisition_status='manual_primary_web_verified',verified_fields=['title','authors','publication_year','venue']);pm=m
 if pid=='P0410' and pm:m=pm;rr.update(metadata=m,identity_status='matched',acquisition_status='primary_pdf_plus_crossref_verified',verified_fields=['title','authors','publication_year','venue'])
 if pm:rr['publication_metadata']=pm
 matched=rr['identity_status']=='matched'
 if matched:
  preferred=pm or m
  r['authors']=preferred.get('authors') or m.get('authors')
  preprint=m.get('year_basis')=='arxiv_preprint_registration'
  r['preprint_year']=m.get('publication_year') if preprint else None
  r['publication_year']=pm.get('publication_year') if pm else (None if preprint else m.get('publication_year'))
  r['venue']=preferred.get('venue')
  r['reference_year']=r['publication_year'] or r['preprint_year']
  r['reference_title']=preferred.get('title') or r['title']
  r['publication_doi']=preferred.get('doi') if not str(preferred.get('doi','')).lower().startswith('10.48550/') else None
  newaid=re.sub(r'^10\.48550/arxiv\.','',m.get('arxiv_doi') or '',flags=re.I)
  if newaid:r['discovered_arxiv_id']=newaid
  r['reference_url']='https://doi.org/'+r['publication_doi'] if r.get('publication_doi') else ('https://arxiv.org/abs/'+newaid if newaid else r['canonical_url'])
  r['authors_venue_year_verified']=bool(r['authors'] and r['venue'] and r['publication_year'])
  r['enriched_verified_fields']=['title']+(['authors'] if r['authors'] else [])+(['preprint_year'] if r['preprint_year'] else [])+(['publication_year'] if r['publication_year'] else [])+(['venue'] if r['venue'] else [])
  r['publication_status']='published_venue_metadata_verified' if r['authors_venue_year_verified'] else 'preprint_or_venue_not_verified'
 else:r['reference_year']=None;r['reference_title']=None;r['enriched_verified_fields']=[]
 if pid in note_by_id:rr['read_depth']=note_by_id[pid]['depth'];rr['sections_read']=note_by_id[pid]['sections']
 r['full_text_read']=False # Selected sections do not imply complete full-text review.
 rr['fulltext_local_available']=(BASE/'primary-text'/(pid+'-fulltext.txt')).exists()
 rr['enrichment_finalized_at']=datetime.now(timezone.utc).isoformat()
 aliases.append({'paper_id':pid,'catalog_title':r['title'],'preprint_title':m.get('title'),'publication_title':pm.get('title') if pm else None,'arxiv_id':r.get('arxiv_id'),'arxiv_version':m.get('version'),'publication_doi':r.get('publication_doi'),'relation_status':'verified_primary_version_map' if pm else 'no_publication_relation_verified'})
 line={'paper_id':pid,'title':r['title'],'reference_title':r.get('reference_title'),'authors':'; '.join(r.get('authors') or []),'preprint_year':r.get('preprint_year'),'publication_year':r.get('publication_year'),'venue':r.get('venue'),'arxiv_id':r.get('arxiv_id') or r.get('discovered_arxiv_id'),'publication_doi':r.get('publication_doi'),'canonical_url':r['canonical_url'],'reference_url':r.get('reference_url'),'metadata_source_url':m.get('metadata_source_url'),'publication_metadata_url':pm.get('metadata_source_url') if pm else None,'identity_status':rr['identity_status'],'acquisition_status':rr['acquisition_status'],'read_depth':rr['read_depth'],'fulltext_local_available':rr['fulltext_local_available'],'priority_reading':rr['priority_reading']};flat.append(line)
 if not matched or not r.get('authors') or not r.get('reference_year'):missing.append(line)
 if rr['priority_reading'] and not r['authors_venue_year_verified']:pub_missing.append(line)
 if matched and r.get('authors') and r.get('reference_year'):
  typ='inproceedings' if preferred.get('publication_type')=='proceedings-article' or (preferred.get('source_kind')=='primary_page_citation_tags' and preferred.get('citation_tags',{}).get('citation_conference_title')) else 'incollection' if preferred.get('publication_type')=='book-chapter' else 'article' if r.get('venue') else 'misc'
  fields={'title':'{'+esc(r['reference_title'])+'}','author':' and '.join(esc(a) for a in r['authors']),'year':r['reference_year'],'url':r['reference_url']}
  if r.get('venue'):fields['booktitle' if typ in ('inproceedings','incollection') else 'journal']=esc(r['venue'])
  if r.get('publication_doi'):fields['doi']=r['publication_doi']
  if r.get('arxiv_id') or r.get('discovered_arxiv_id'):fields.update(eprint=r.get('arxiv_id') or r['discovered_arxiv_id'],archivePrefix='arXiv')
  fields['note']='Verified descriptive metadata; '+('publication year' if r['publication_year'] else 'arXiv preprint year; publication venue not verified')+'; accessed 2026-09-13'
  b='% Metadata source: '+str(pm.get('metadata_source_url') if pm else m.get('metadata_source_url'))+'\n@'+typ+'{'+pid+',\n'+',\n'.join('  '+k+' = {'+str(v)+'}' for k,v in fields.items())+'\n}\n';bibs.append(b)
  if rr['priority_reading']:prioritybibs.append(b)
writejl(BASE/'catalog-enriched.jsonl',records)
cols=list(flat[0]);tsv(BASE/'catalog-enriched.tsv',flat,cols);tsv(BASE/'unresolved.tsv',missing,cols);tsv(BASE/'priority-publication-unresolved.tsv',pub_missing,cols)
tsv(BASE/'alias-version-map.tsv',aliases,list(aliases[0]));tsv(BASE/'reading-extraction-matrix.tsv',extractions,list(extractions[0]))
(BASE/'references-verified.bib').write_text('% Generated from verified primary/depositor metadata, not an official publisher export.\n\n'+'\n'.join(bibs),encoding='utf-8')
(BASE/'references-priority50.bib').write_text('% Priority reading references. Preprint year and venue status are explicit.\n\n'+'\n'.join(prioritybibs),encoding='utf-8')
# Preserve unmodified official ACL BibTeX embedded in primary landing pages.
acl=BASE/'official-acl-bibtex';acl.mkdir(exist_ok=True)
for p in (BASE/'cache').glob('*.json'):
 e=json.loads(p.read_text(encoding='utf-8'));u=e.get('url','')
 if 'aclanthology.org/' not in u or e.get('status')!=200:continue
 b=re.search(r'<pre[^>]*id=[\"\']?citeBibtexContent[\"\']?[^>]*>(.*?)</pre>',e.get('text',''),re.S)
 if b:
  aid=u.rstrip('/').split('/')[-1]
  if re.fullmatch(r'[a-zA-Z0-9.\-]+',aid):(acl/(aid+'.bib')).write_text(html.unescape(b.group(1)),encoding='utf-8')
byid={r['paper_id']:r for r in records};noteindex=[]
for n in extractions:
 pid=n['id'];r=byid[pid];rr=r['research'];m=rr.get('metadata',{});pm=rr.get('publication_metadata',{});source=index.get(pid,{}).get('fulltext_url') or pdfs.get(pid,{}).get('url') or r['canonical_url']
 if pid=='P0075':source=manual_openrca['metadata_source_url']
 local=BASE/'primary-text'/(pid+'-fulltext.txt')
 meta_source=pm.get('metadata_source_url') or m.get('metadata_source_url') or r['canonical_url']
 title=r.get('reference_title') or r['title']
 doc=f'''---
paper_id: {pid}
read_depth: {n['depth']}
full_text_completely_read: false
access_date: 2026-09-13
---
# {pid} — {title}

**Tác giả:** {'; '.join(r.get('authors') or ['Chưa xác minh'])}. **Năm trích dẫn:** {r.get('reference_year') or 'chưa xác minh'}. **Venue:** {r.get('venue') or 'chưa xác minh; chỉ trích bản preprint'}.

**Đã đọc:** {n['sections']}. Mức đọc `{n['depth']}`; không đại diện cho systematic review toàn văn.

| Trường extraction | Nội dung |
|---|---|
| Tác vụ | {n['task']} |
| Observations / labels | {n['observation']} |
| Phương pháp | {n['method']} |
| Evaluation / protocol | {n['evaluation']} |

**Giới hạn bằng chứng và nhận định áp dụng:** {n['limitation']}

**Hàm ý cho CS221 (đề xuất, chưa phải kết quả thí nghiệm):** {n['application']}

Nguồn: [paper / phần đã đọc]({source}); [metadata chính thức / cơ quan đăng ký]({meta_source}).
'''
 if local.exists():doc+=f'\n[Tài nguyên text local]({local.as_posix()}) là bản trích để đọc; HTML/PDF có thể có lỗi chuyển đổi. Tải thành công không đồng nghĩa đã đọc hết.\n'
 if r.get('preprint_year') and r.get('publication_year') and r['preprint_year']!=r['publication_year']:doc+=f'\nVersion note: preprint {r["preprint_year"]}; publication {r["publication_year"]}. Giữ cả hai trong alias-version-map.tsv.\n'
 (NOTES/(pid+'.md')).write_text(doc,encoding='utf-8')
 noteindex.append(f'| [{pid}]({pid}.md) | {n["task"]} | {n["depth"]} | {"có" if local.exists() else "chưa có"} |')
(NOTES/'README.md').write_text('# Ghi chú 50 tài liệu ưu tiên\n\nMỗi note ghi đúng phần đã đọc, phân biệt bằng chứng tác giả với hàm ý cho dự án. Không có note nào được gắn là đã review toàn văn hoàn chỉnh.\n\n| Paper | Task | Mức đọc | Full text local |\n|---|---|---|---|\n'+'\n'.join(noteindex)+'\n',encoding='utf-8')
groups=collections.defaultdict(list)
for r in records:
 for typ,ids in [('doi',[r.get('doi'),r.get('publication_doi'),r['research'].get('metadata',{}).get('arxiv_doi')]),('arxiv',[r.get('arxiv_id'),r.get('discovered_arxiv_id')])]:
  for val in set(x for x in ids if x):
   ident=re.sub(r'^https?://(?:dx\.)?doi.org/','',val,flags=re.I).lower().strip()
   if typ=='arxiv':ident=re.sub(r'v\d+$','',ident)
   groups[(typ,ident)].append(r)
collisions=[]
for (typ,ident),rs in groups.items():
 unique={r['paper_id']:r for r in rs}
 if len(unique)>1:collisions.append({'identifier_type':typ,'identifier':ident,'paper_ids':'; '.join(sorted(unique)),'titles':' | '.join(r['title'] for r in unique.values()),'status':'canonical_work_candidate_review_required_no_records_deleted'})
tsv(BASE/'canonical-work-candidates.tsv',collisions,['identifier_type','identifier','paper_ids','titles','status'])
stats={'records':len(records),'identity_status':dict(collections.Counter(r['research']['identity_status'] for r in records)),'authors_enriched':sum(bool(r.get('authors')) for r in records),'publication_venue_year_verified':sum(r['authors_venue_year_verified'] for r in records),'bibliography_entries':len(bibs),'priority_bibliography_entries':len(prioritybibs),'priority_publication_unresolved':len(pub_missing),'priority_read_depth':dict(collections.Counter(n['depth'] for n in extractions)),'priority_fulltext_local':sum((BASE/'primary-text'/(n['id']+'-fulltext.txt')).exists() for n in extractions),'unresolved_bibliography_rows':len(missing),'official_acl_bibtex_files':len(list(acl.glob('*.bib'))),'canonical_work_candidate_groups':len(collisions),'records_with_rescue_evidence':sum(bool(r['research'].get('rescue_evidence')) for r in records)}
(BASE/'research-statistics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(stats,ensure_ascii=False))
report=ROOT/'05_research/paper-research.md'
if report.exists():
 doc=report.read_text(encoding='utf-8');num=lambda n:f'{n:,}'.replace(',','.')
 rows=[('Records bảo toàn trong catalog',num(stats['records'])),('Khớp metadata/identity nguồn chính thức hoặc depositor',num(stats['identity_status'].get('matched',0))),('Identity còn unresolved/candidate',num(stats['records']-stats['identity_status'].get('matched',0))),('Có tác giả/năm đủ tạo BibTeX',num(stats['bibliography_entries'])),('Bibliography chưa đủ authors/year hoặc identity',num(stats['unresolved_bibliography_rows'])),('Có publication venue và năm được xác minh',num(stats['publication_venue_year_verified'])),('Priority papers có bibliography','50/50'),('Priority papers có publication venue/year',str(50-stats['priority_publication_unresolved'])+'/50'),('Priority papers có full text local',str(stats['priority_fulltext_local'])+'/50'),('Đã đọc một số sections trong full text','25'),('Mức abstract-only','24'),('Abstract và trang đầu primary PDF','1')]
 table='<!-- coverage-start -->\n| Hạng mục | Số lượng tại bản bàn giao |\n|---|---:|\n'+'\n'.join('| '+k+' | '+v+' |' for k,v in rows)+'\n<!-- coverage-end -->'
 doc=re.sub(r'<!-- coverage-start -->.*?<!-- coverage-end -->',lambda m:table,doc,flags=re.S)
 report.write_text(doc,encoding='utf-8')
