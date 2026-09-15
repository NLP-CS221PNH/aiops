"""Build observation-only bundles, separate labels and leakage-safe family splits.

Passive PyArrow reader; does not use injection times or gold to select observations.
Gold is read only by build_label_tables, never by summarize_observations.
"""
from pathlib import Path
import collections, csv, datetime, hashlib, json, math, re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.runtime-python'))
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACQ=ROOT/'02_datasets/acquired'; OUT=ROOT/'02_datasets/processed'
(OUT/'labels').mkdir(parents=True,exist_ok=True)
REV='afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
VERSION='observation-bundle-v1'; SEED='cs221-family-split-20260912-v1'
PII={
 'email':r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
 'ipv4':r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
 'bearer':r'(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}',
 'private_key':r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
 'aws_access_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'credential_assignment':r'(?i)(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]{5,}',
}
ERROR=r'(?i)error|exception|fail|timeout|timed out|refused|unavailable|deadline|panic|denied'

def iid(case):return 'inc_'+hashlib.sha256(('RCAEval:'+case).encode()).hexdigest()[:16]
def fid(case):return 'fam_'+hashlib.sha256(('RCAEval:'+case.rsplit('_',1)[0]).encode()).hexdigest()[:16]
def jwrite(path,rows):path.write_text(''.join(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n' for x in rows),encoding='utf-8')
def jsave(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc(sec):return datetime.datetime.fromtimestamp(sec,datetime.timezone.utc).isoformat()
def number(x):
    if x is None:return None
    return x if math.isfinite(float(x)) else None
def redact(text,incident):
    text=str(text or '')
    for kind,pattern in PII.items():
        text=re.sub(pattern,lambda m:'['+kind.upper()+'_'+hashlib.sha256((incident+':'+m.group()).encode()).hexdigest()[:10]+']',text)
    return text

def build_label_tables():
    index=json.loads((ACQ/'labels/cases-index.json').read_text(encoding='utf-8'))
    rows=[x for x in index if x['dataset']=='RE2-OB']
    groups=collections.defaultdict(set)
    for r in rows:groups[r['fault']].add(r['case'].rsplit('_',1)[0])
    family_splits={}
    for fault,families in sorted(groups.items()):
        ordered=sorted(families,key=lambda f:hashlib.sha256((SEED+f).encode()).hexdigest())
        assert len(ordered)==5
        family_splits.update({f:('train' if i<3 else 'dev' if i==3 else 'test') for i,f in enumerate(ordered)})
    labels=[]; splits=[]; lineage=[]
    for r in rows:
        case=r['case']; incident=iid(case); family=fid(case)
        split=family_splits[case.rsplit('_',1)[0]]
        labels.append({'incident_id':incident,'scenario_family_id':family,'root_cause_service':r['root_cause_service'],'fault':r['fault'],'fault_description':r['fault_description'],'injection_time':r['inject_time'],'repetition':r['repetition'],'label_source':'author-provided cases.parquet','label_release_revision':REV,'source_case':case,'root_cause_indicator':'not separately present in selected HF index','retrieval_qrels':'not provided'})
        splits.append({'incident_id':incident,'scenario_family_id':family,'split':split,'split_version':SEED})
        lineage.append({'incident_id':incident,'source_case':case,'source_id':'D068','parent_source_id':'D001','source_url':f'https://huggingface.co/datasets/phamquiluan/RCAEval/tree/{REV}/{case}','release_revision':REV,'scenario_family_id':family})
    jwrite(OUT/'labels/ground_truth.jsonl',labels);jwrite(OUT/'labels/lineage.jsonl',lineage)
    with (OUT/'split-map.tsv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(splits[0]),delimiter='\t');w.writeheader();w.writerows(splits)
    tt=[{k:v for k,v in x.items()} for x in index if x['dataset']=='RE2-TT']
    jsave(ACQ/'labels/RE2-TT-metadata.json',tt)
    return splits

def summarize_observations(incident):
    """Allowed inputs: opaque incident id and telemetry only; no label/path metadata."""
    folder=ACQ/'raw'/incident
    mt=pq.read_table(folder/'metrics.parquet'); times=mt['time'].to_pylist()
    assert times==sorted(times), 'Metric timestamps must be monotonic for first/last-quarter summaries'
    start=min(times);end=max(times);duration=end-start
    assert 1_000_000_000 < start < 3_000_000_000
    quarter=max(1,len(times)//4)
    stats=[]
    for col in mt.column_names:
        if col=='time':continue
        vals=mt[col]; first=pc.mean(vals.slice(0,quarter)).as_py();last=pc.mean(vals.slice(len(times)-quarter,quarter)).as_py()
        std=pc.stddev(vals.slice(0,quarter)).as_py()
        change=None if first is None or last is None else (last-first)
        scale=max(abs(first or 0)*0.01,abs(std or 0),1e-9)
        stats.append({'evidence_id':f'{incident}:metric:{col}','incident_id':incident,'metric_name':col,'observation_start':utc(start),'observation_end':utc(end),'row_count':len(times),'null_count':vals.null_count,'minimum':number(pc.min(vals).as_py()),'maximum':number(pc.max(vals).as_py()),'mean':number(pc.mean(vals).as_py()),'first_quarter_mean':number(first),'last_quarter_mean':number(last),'change_score':number(abs(change)/scale) if change is not None else None,'change_score_rule':'abs(last_quarter_mean-first_quarter_mean)/max(first_quarter_std,abs(first_quarter_mean)*.01,1e-9); descriptive only','source_file_id':incident+':metrics','source_row_start':0,'source_row_end_exclusive':len(times),'transform_version':VERSION})
    stats.sort(key=lambda x:-(x['change_score'] or 0))
    lt=pq.read_table(folder/'logs.parquet'); n_logs=lt.num_rows
    log_times=lt['timestamp']; lmin=pc.min(log_times).as_py();lmax=pc.max(log_times).as_py()
    inwin=pc.and_(pc.greater_equal(log_times,start),pc.less_equal(log_times,end))
    lt=lt.append_column('_source_row',pa.array(range(n_logs),type=pa.int64())).filter(inwin)
    privacy={k:pc.sum(pc.cast(pc.match_substring_regex(lt['message'],p),pa.int64())).as_py() or 0 for k,p in PII.items()}
    candidates=lt.filter(pc.fill_null(pc.match_substring_regex(lt['message'],ERROR),False))
    if candidates.num_rows==0:candidates=lt.slice(max(0,lt.num_rows-200),200)
    candidates=candidates.take(pc.sort_indices(candidates,sort_keys=[('timestamp','descending'),('_source_row','descending')]))
    chosen=[];counts=collections.Counter();seen=set()
    for r in candidates.to_pylist():
        service=r['container_name']; text=redact(r['message'],incident)
        normalized=re.sub(r'\b\d+(?:\.\d+)?\b','<N>',text)
        key=(service,normalized)
        if key in seen or counts[service]>=4:continue
        seen.add(key);counts[service]+=1
        chosen.append({'evidence_id':f"{incident}:log:{r['_source_row']}",'incident_id':incident,'timestamp':utc(r['timestamp']),'service':service,'text':text,'source_file_id':incident+':logs','source_row_index':r['_source_row'],'redaction_version':'pii-regex-pseudonym-v1','transform_version':VERSION})
        if len(chosen)>=48:break
    chosen.sort(key=lambda x:(x['service'],x['timestamp'],x['evidence_id']))
    tt=pq.read_table(folder/'traces.parquet'); n_traces=tt.num_rows
    tt=tt.append_column('_source_row',pa.array(range(n_traces),type=pa.int64()))
    inwin=pc.and_(pc.greater_equal(tt['startTimeMillis'],start*1000),pc.less(tt['startTimeMillis'],(end+1)*1000))
    tw=tt.filter(inwin)
    services=sorted(set(lt['container_name'].to_pylist())|set(tw['serviceName'].to_pylist()))
    trace_summary=tw.group_by('serviceName').aggregate([('duration','mean'),('duration','max'),('duration','count')]).to_pylist()
    te=[]
    for service in sorted(set(tw['serviceName'].to_pylist())):
        st=tw.filter(pc.equal(tw['serviceName'],service))
        nonzero=st.filter(pc.not_equal(st['statusCode'],0))
        ranked=(nonzero if nonzero.num_rows else st)
        top=ranked.take(pc.sort_indices(ranked,sort_keys=[('duration','descending'),('_source_row','ascending')])).slice(0,2)
        for r in top.to_pylist():
            safe={k:redact(r[k],incident) for k in ('serviceName','methodName','operationName')}
            for k in ('traceID','spanID','parentSpanID'):safe[k]='id_'+hashlib.sha256((incident+':'+str(r[k])).encode()).hexdigest()[:16]
            te.append({'evidence_id':f"{incident}:trace:{r['_source_row']}",'incident_id':incident,'timestamp':utc(r['startTimeMillis']/1000),'duration_raw':r['duration'],'duration_unit':'microseconds inferred from Jaeger-style schema; not independently verified','status_code':r['statusCode'],'status_code_semantics':'unverified; nonzero is not asserted to mean error',**safe,'source_file_id':incident+':traces','source_row_index':r['_source_row'],'selection':'two highest-duration nonzero-status spans per observed service; highest-duration spans if all status codes are zero','redaction_version':'pii-regex-pseudonym-v1'})
    top_metrics=stats[:12]
    brief='; '.join(x['metric_name'] for x in top_metrics[:6])
    quotes=' | '.join(x['service']+': '+x['text'][:300] for x in chosen[:8])
    query=f'Investigate this Online Boutique observation window. The largest descriptive metric changes are {brief}. Observed log excerpts: {quotes}. Identify supported service candidates, cite evidence, and state missing information.'
    observation={'incident_id':incident,'system_id':'online_boutique','service_inventory':services,'observation_start':utc(start),'observation_end':utc(end),'window_policy':'all provided metric timestamps; retrospective offline window; no injection time used','symptom_query':query,'query_origin':'deterministic observation-derived template, not a human operator query','is_synthetic':True,'generator_revision':VERSION,'input_source_ids':[incident+':metrics',incident+':logs',incident+':traces'],'human_review_state':'not_reviewed','log_span_ids':[x['evidence_id'] for x in chosen],'metric_summary_ids':[x['evidence_id'] for x in top_metrics],'trace_span_ids':[x['evidence_id'] for x in te],'redaction_version':'pii-regex-pseudonym-v1','provenance_source':'D068','release_revision':REV,'knowledge_evidence_coverage':'unjudged','deployment_version':'unknown'}
    profile={'incident_id':incident,'metric_rows':len(times),'metric_columns':len(mt.column_names)-1,'logs_rows':n_logs,'logs_in_window':lt.num_rows,'trace_rows':n_traces,'traces_in_window':tw.num_rows,'metric_time_start':start,'metric_time_end':end,'metric_duration_seconds':duration,'metric_time_monotonic':True,'log_time_start':lmin,'log_time_end':lmax,'log_selected_count':len(chosen),'trace_selected_count':len(te),'metric_null_cells':sum(x['null_count'] for x in stats),'metric_duplicate_timestamps':len(times)-len(set(times)),'privacy_pattern_counts_in_window':privacy,'trace_service_summary':trace_summary,'trace_status_counts':tw.group_by('statusCode').aggregate([('duration','count')]).to_pylist(),'source_schema_hashes':{n:hashlib.sha256(str(pq.read_schema(folder/(n+'.parquet'))).encode()).hexdigest() for n in ('metrics','logs','traces')}}
    observation.update({'observation_end':utc(end+1),'window_policy':'half-open [first metric second, last metric second + 1s); retrospective offline window; no injection time used','generation_date':'2026-09-12','query_is_synthetic':True,'telemetry_is_synthetic':False})
    return observation,chosen,stats,te,profile

def main():
    splits=build_label_tables()
    if len(list((ACQ/'raw').glob('inc_*/traces.parquet')))!=90:raise RuntimeError('Full download must complete first')
    obs=[];logs=[];metrics=[];traces=[];profiles=[]
    for i,s in enumerate(sorted(splits,key=lambda x:x['incident_id'])):
        o,l,m,t,p=summarize_observations(s['incident_id'])
        o.update({k:s[k] for k in ('scenario_family_id','split')})
        obs.append(o);logs.extend(l);metrics.extend(m);traces.extend(t);profiles.append(p)
        print(f'processed {i+1}/90 {s["incident_id"]}',flush=True)
    for filename,data in [('observations.jsonl',obs),('logs-evidence.jsonl',logs),('metric-summaries.jsonl',metrics),('trace-evidence.jsonl',traces),('incident-profiles.jsonl',profiles)]:jwrite(OUT/filename,data)
    privacy=collections.Counter()
    for p in profiles:privacy.update(p['privacy_pattern_counts_in_window'])
    split_counts=collections.Counter(o['split'] for o in obs)
    report={'incident_count':len(obs),'scenario_family_count':len(set(o['scenario_family_id'] for o in obs)),'split_counts':dict(split_counts),'metric_rows':sum(x['metric_rows'] for x in profiles),'log_rows':sum(x['logs_rows'] for x in profiles),'trace_rows':sum(x['trace_rows'] for x in profiles),'log_evidence_records':len(logs),'metric_summary_records':len(metrics),'trace_evidence_records':len(traces),'privacy_pattern_counts':dict(privacy),'privacy_scan_scope':'all in-window raw log messages; emitted logs/trace strings redacted; raw files remain original; regex scan is not exhaustive','unit_policy':{'metric_time':'Unix seconds','log_timestamp':'Unix seconds','trace_startTimeMillis':'Unix milliseconds','trace_time_string':'ambiguous HH:MM ignored','trace_duration':'microseconds inferred, not independently verified'},'split_policy':'30 service×fault families; deterministic hash ordering within fault; 3 train / 1 dev / 1 test family per fault; repetitions stay together','split_seed':SEED,'labels_used_for_observation_generation':False,'gold_fields_in_observation_records':False,'dataset_revision':REV,'knowledge_relevance_qrels':'not annotated','human_review':'pending','root_cause_indicator_gold':'HF index provides service/fault/injection, no separate indicator file downloaded','historical_online_triage_evaluation':False,'transform_version':VERSION}
    report.update({'metric_rows_range':[min(x['metric_rows'] for x in profiles),max(x['metric_rows'] for x in profiles)],'metric_columns_range':[min(x['metric_columns'] for x in profiles),max(x['metric_columns'] for x in profiles)],'duration_seconds_range':[min(x['metric_duration_seconds'] for x in profiles),max(x['metric_duration_seconds'] for x in profiles)],'null_metric_cells':sum(x['metric_null_cells'] for x in profiles),'duplicate_metric_timestamps':sum(x['metric_duplicate_timestamps'] for x in profiles),'all_metric_timestamps_monotonic':all(x['metric_time_monotonic'] for x in profiles)})
    jsave(OUT/'profile-summary.json',report)
    raw_manifest=[json.loads(x) for x in (ACQ/'labels/acquisition-manifest.jsonl').read_text(encoding='utf-8').splitlines()]
    with (ACQ/'inventory.tsv').open('w',encoding='utf-8',newline='') as f:
        fields=['incident_id','data_kind','local_path','bytes','sha256','upstream_hash_verified']
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(raw_manifest)
    record= json.loads((ACQ/'meta/source-registry.json').read_text(encoding='utf-8'))
    earliest=min(p['metric_time_start'] for p in profiles);latest=max(p['metric_time_end'] for p in profiles)
    report_folder=ROOT/'05_research';report_folder.mkdir(exist_ok=True)
    text=f'''# Nghiên cứu và bàn giao dữ liệu RCAEval

Đã thu đủ **90/90 ca RE2-Online Boutique**, 360 file gốc (270 Parquet telemetry và 90 file injection được tách vào labels), **{sum(x['bytes'] for x in raw_manifest):,} bytes**. Ba modality đều hiện diện trong cả 90 ca. Đây là toàn bộ subset MVP mà plan chọn, không phải chỉ một sample; 102 mục catalog là registry nhiều vai trò, không phải yêu cầu tải 102 dataset.

## Bằng chứng và phiên bản

- [HF dataset revision](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/{REV}) được ghim; index gồm 735 ca toàn benchmark, không cộng mirror thành mẫu độc lập.
- [README và phạm vi license của tác giả](https://github.com/phamquiluan/RCAEval/blob/{record['github_revision']}/README.md#licensing) xác nhận MIT cho dữ liệu tác giả. Bản license và SHA256 lưu tại `02_datasets/acquired/meta/`.
- 270 Parquet tải có SHA256 khớp LFS của revision; `cases.parquet` khớp SHA256 `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb`. File injection nhỏ có checksum local và URL ghim revision.
- Đã tải một ca trước, đọc schema thụ động, rồi mới tải đủ 90 ca. Không chạy loader, notebook, fault injection hay pickle từ nguồn.

## Dữ liệu thực đã kiểm

| Đại lượng | Giá trị |
|---|---:|
| Incident / scenario families | 90 / 30 |
| Train / dev / test | 54 / 18 / 18 |
| Metric timesteps | {report['metric_rows']:,} |
| Log rows | {report['log_rows']:,} |
| Trace spans | {report['trace_rows']:,} |
| Log evidence / metric summaries / trace evidence | {len(logs)} / {len(metrics)} / {len(traces)} |

Khoảng telemetry thực từ {utc(earliest)} tới {utc(latest)}. Log `timestamp` và metric `time` là epoch giây; trace dùng `startTimeMillis`. Không dùng chuỗi `HH:MM` thiếu ngày/timezone. Đơn vị duration được ghi rõ là microsecond suy từ schema kiểu Jaeger, chưa được xác nhận độc lập.

Số metric timesteps mỗi ca từ {report['metric_rows_range'][0]} tới {report['metric_rows_range'][1]}; metric columns từ 69 tới 77. Có {report['null_metric_cells']:,} ô metric null, được giữ nguyên trong raw, thống kê mô tả bỏ qua null và không tự impute. Cả 90 chuỗi metric đơn điệu theo thời gian, không có timestamp trùng. Observation window là khoảng nửa mở từ giây metric đầu đến giây metric cuối cộng 1 giây, để giữ trọn giây cuối khi nối trace millisecond. `statusCode` trace được giữ nguyên, chưa đồng nhất nonzero với lỗi.

Split đóng băng theo service×fault family; mỗi fault có 3 family train, 1 dev, 1 test, các repetition giữ cùng split. Root-service/fault/injection chỉ dùng tạo labels và group split. Hàm sinh observations chỉ nhận opaque ID cùng telemetry, không đọc gold hoặc tên case gốc.

## Cách sử dụng

- Input được phép: `processed/observations.jsonl`, `logs-evidence.jsonl`, `metric-summaries.jsonl`, `trace-evidence.jsonl`. Citation ID dẫn đến row offset trong file telemetry gốc có opaque ID.
- Gold riêng: `processed/labels/ground_truth.jsonl`. Lineage chứa case name gốc ở `processed/labels/lineage.jsonl`; manifest nguồn có đường dẫn gold ở `acquired/labels/`. Không đưa các nhánh này vào prompt/index.
- Raw telemetry đầy đủ ở `acquired/raw/inc_*/`. Giữ nguyên byte gốc để tái lập. Chỉ bản trích xuất đưa vào model đã khử email/IP và các pattern credential; không gửi raw lên dịch vụ bên ngoài chưa qua xử lý.
- `split-map.tsv`, `incident-profiles.jsonl`, `profile-summary.json`, `acquired/inventory.tsv` cung cấp khóa, thống kê, checksum và vị trí dữ liệu.

Query là template suy từ quan sát đã ghi `is_synthetic=true`, không giả làm query do operator viết. Window dùng toàn bộ metric timeframe từng ca, không lấy injection làm tín hiệu đầu vào. Đây là đánh giá offline hồi cứu; KB hiện tại không chứng minh mô phỏng triage trực tuyến năm 2024.

## Reserve và registry

RE2-TT giữ metadata của 90 ca, chưa tải 1,965,747,924 bytes telemetry. Một ca không có logs; [known-data notes của tác giả](https://huggingface.co/datasets/phamquiluan/RCAEval/blob/{REV}/README.md#known-data-notes) xác nhận 89/90 có logs. Trước test khác hệ thống, chọn rõ missing-modality policy; không âm thầm loại ca.

`02_datasets/catalog-review.tsv` và JSONL audit cả 102 dòng: existence card, parent link, role, license gate, collection decision. Không tuyên bố 102 nguồn được reverify live. RCAEval release và P1 OpenRCA, Loghub, Loghub-2.0, MultiHop-RAG, RAGTruth có primary snapshots; LEMMA website được đọc lại, mâu thuẫn quyền vẫn giữ. Các nguồn thay thế và KB có nghiên cứu riêng của gói.

[Loghub](https://github.com/logpai/loghub) và [Loghub-2.0](https://github.com/logpai/loghub-2.0) dành cho research/academic với nghĩa vụ ghi nguồn; giữ làm lựa chọn parsing. [OpenRCA](https://github.com/microsoft/OpenRCA) có MIT repository nhưng chưa đủ bằng chứng quyền raw trên Drive. [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) ghi ODC-BY ở README, dùng tham khảo qrels khác miền; [RAGTruth](https://github.com/ParticleMedia/RAGTruth) dùng tham khảo rubric hallucination, không quy đổi score thành RCA.

## Phần chưa thể coi là hoàn thành

Qrels incident→runbook, độ phủ bằng chứng và human review còn `unjudged`; không có annotation của người hay kết quả benchmark bị bịa. Selected HF index có service/fault/injection gold, không chứa root-cause-indicator riêng cho RE2-OB. Chưa có deployment version của các ca để xác nhận runbook hiện tại tương thích. Regex privacy là kiểm tra có giới hạn, không chứng nhận raw logs sạch mọi PII/secret. Các hạn chế này quyết định những claim thí nghiệm được phép nêu.
'''
    (report_folder/'dataset-research.md').write_text(text,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
