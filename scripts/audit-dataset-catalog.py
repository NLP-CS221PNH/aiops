"""Audit all existing dataset rows and pin selected P1 primary-source documents.
Local audit is distinct from live primary verification and from asset acquisition.
"""
from pathlib import Path
import argparse,collections,csv,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('acquire',ROOT/'scripts/acquire-datasets.py')
acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
OUT=ROOT/'02_datasets/acquired/meta/catalog-review';OUT.mkdir(parents=True,exist_ok=True)
SELECTED={'D002':'microsoft/OpenRCA','D005':'logpai/loghub','D006':'logpai/loghub-2.0','D024':'yixuantt/MultiHop-RAG','D043':'ParticleMedia/RAGTruth'}

def snapshots():
    reports=[]
    for source,repo in SELECTED.items():
        record={'dataset_id':source,'official_url':'https://github.com/'+repo,'verification_scope':'primary repository documentation; per-file access state recorded; no raw data downloaded'}
        try:
            p=OUT/(source+'-commit.json');acq.fetch(f'https://api.github.com/repos/{repo}/commits/HEAD',p)
            rev=json.loads(p.read_text(encoding='utf-8'))['sha'];record['revision']=rev
            docs=[]
            for name in ('README.md','LICENSE'):
                url=f'https://raw.githubusercontent.com/{repo}/{rev}/{name}'
                target=OUT/(source+'-'+name)
                try:
                    sha=acq.fetch(url,target)
                    docs.append({'source_url':url,'local_path':target.relative_to(ROOT).as_posix(),'sha256':sha})
                except Exception as e:docs.append({'source_url':url,'status':'fetch_failed','error':str(e)})
            record['documents']=docs;record['access_state']='primary_documents_read'
        except Exception as e:record['access_state']='fetch_failed';record['error']=str(e)
        reports.append(record)
        print(source,record['access_state'],flush=True)
    try:
        acq.fetch('https://lemma-rca.github.io/',OUT/'D004-website.html')
        reports.append({'dataset_id':'D004','official_url':'https://lemma-rca.github.io/','access_state':'primary_landing_read','verification_scope':'website only; conflict across release rights retained, not resolved','sha256':acq.digest(OUT/'D004-website.html')})
    except Exception as e:reports.append({'dataset_id':'D004','access_state':'fetch_failed','error':str(e)})
    acq.write_json(OUT/'primary-review.json',reports)

def audit():
    rows=list(csv.DictReader((ROOT/'02_datasets/catalog.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
    assert len(rows)==102
    ids={r['dataset_id'] for r in rows};assert len(ids)==102
    snapshots=json.loads((OUT/'primary-review.json').read_text(encoding='utf-8')) if (OUT/'primary-review.json').exists() else []
    primary={x['dataset_id']:x for x in snapshots}
    status_path=ROOT/'02_datasets/acquired/meta/acquisition-status.json'
    status=json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    inventory=json.loads((ROOT/'02_datasets/acquired/meta/source-registry.json').read_text(encoding='utf-8'))
    result=[]
    for r in rows:
        source=r['dataset_id'];kind=r['resource_type'];parent=r['parent_id']
        if source=='D068':decision='selected_main_complete' if status.get('complete_RE2_OB') else 'selected_main_acquiring'
        elif source=='D001':decision='parent_registry_selected_via_D068'
        elif source=='D070':decision='metadata_only_cross_system_reserve'
        elif kind in ('method_only','generation_platform'):decision='method_or_platform_reference_no_dataset_download'
        elif r['license_gate']=='HOLD_FOR_CLARIFICATION':decision='hold_existing_license_or_release_uncertainty'
        elif source in ('D058','D059'):decision='selected_KB_see_knowledge_corpus_artifacts'
        elif source in ('D027','D032','D051','D101','D102'):decision='alternative_track_primary_metadata_see_research_artifacts'
        elif kind=='subset':decision='defer_subset_not_selected_do_not_count_independently'
        else:decision='defer_not_required_by_selected_MVP'
        record={'dataset_id':source,'name':r['name'],'priority':r['priority'],'resource_type':kind,'parent_id':parent,'family':r['family'],'official_url':r['official_url'],'original_license_status':r['license_status'],'original_license_gate':r['license_gate'],'original_access_status':r['access_status'],'current_collection_decision':decision,'local_card_exists':(ROOT/'02_datasets/cards'/f'{source}.md').exists(),'parent_id_resolves':not parent or parent in ids,'live_verification_scope':'not_reverified_this_execution; original card retained','asset_download_scope':'none_by_dataset_agent','review_evidence_path':'','next_action':r['next_collection_action']}
        if source in primary:
            p=primary[source];record.update(live_verification_scope=p.get('verification_scope',p['access_state']),review_evidence_path='02_datasets/acquired/meta/catalog-review/primary-review.json')
        if source in ('D001',)+tuple(f'D{x:03d}' for x in range(65,74)):
            record.update(live_verification_scope='author-pinned-HF-index-release-and-license-verified',review_evidence_path='02_datasets/acquired/meta/source-registry.json')
        if source=='D068':
            record.update(asset_download_scope='90 complete cases' if status.get('complete_RE2_OB') else str(status.get('downloaded_case_count',0))+' cases currently downloaded',next_action='human relevance mapping and blinded qrel annotation; no invented labels')
        if source=='D070':record.update(next_action=f"Hold full telemetry ({inventory['RE2_TT_bytes']} bytes); before cross-system evaluation inspect one missing file/modality in 359-file index and freeze pipeline.")
        if source in ('D005','D006'):record['next_action']='Research-use terms inspected; reserve for parsing ablation; no RCA/qrels inferred.'
        if source=='D002':record['next_action']='Repository MIT does not establish scope of Drive raw data; hold until explicit raw data terms are established.'
        result.append(record)
    with (ROOT/'02_datasets/catalog-review.tsv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]),delimiter='\t');w.writeheader();w.writerows(result)
    (ROOT/'02_datasets/catalog-review.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in result),encoding='utf-8')
    acq.write_json(OUT/'audit-summary.json',{'row_count':len(result),'local_cards_existing':sum(x['local_card_exists'] for x in result),'unresolved_parent_rows':[x['dataset_id'] for x in result if not x['parent_id_resolves']],'resource_types':dict(collections.Counter(x['resource_type'] for x in result)),'decisions':dict(collections.Counter(x['current_collection_decision'] for x in result)),'all_102_reverified_live':False,'scope':'All rows locally audited; selected primary sources verified. Alternatives and knowledge sources are owned by sibling research artifacts. No 102-asset completeness claim.'})
    print('102 rows audited; local audit and live verification separated.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshots',action='store_true');a=p.parse_args()
    if a.snapshots:snapshots()
    audit()
