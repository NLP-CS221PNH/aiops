"""Management-only source census. This module may read evaluator metadata."""
from __future__ import annotations

import argparse
import collections
import csv
from pathlib import Path

from .common import (DEFAULT_CONFIG, IMPL, FILES, DataContractError,
                     canonical_hash, load_config, parse_json, read_jsonl, require,
                     require_research_pack_root, safe_path, sha256, timestamp, write_json)


def validate_inputs(config_path=DEFAULT_CONFIG, source_root=None):
    import pyarrow.parquet as pq
    root = Path(source_root if source_root is not None else require_research_pack_root()).resolve()
    config = load_config(config_path)
    # Pin both processed source files and inventory before trusting any path/row.
    for relative, expected in config['source_hashes'].items():
        path = safe_path(root, relative, config['allowed_roots']['audit'])
        require(sha256(path) == expected, 'SOURCE_HASH_MISMATCH')
    registry = parse_json((root/'02_datasets/acquired/meta/source-registry.json').read_text(encoding='utf-8'))
    require(registry['hf_revision'] == config['source_revision'], 'SOURCE_REVISION')
    with (root/'02_datasets/acquired/inventory.tsv').open(encoding='utf-8-sig', newline='') as handle:
        inventory = list(csv.DictReader(handle, delimiter='\t'))
    require(len(inventory) == 360, 'INVENTORY_COUNT')
    files, paths, roles, source_map = [], set(), collections.Counter(), {}
    for row in inventory:
        incident = row['incident_id']
        require(incident in config['incident_ids'], 'INCIDENT_ID')
        require(row['data_kind'] in ('observation', 'label'), 'SOURCE_ROLE', incident)
        role = row['data_kind']
        filename = Path(row['local_path']).name
        if role == 'observation':
            require(filename in ('metrics.parquet','logs.parquet','traces.parquet'), 'SOURCE_FILENAME', incident)
            expected_path = '02_datasets/acquired/raw/' + incident + '/' + filename
            allowed = ['02_datasets/acquired/raw']
        else:
            require(filename == 'inject_time.txt', 'SOURCE_FILENAME', incident)
            expected_path = '02_datasets/acquired/labels/injection/' + incident + '/inject_time.txt'
            allowed = ['02_datasets/acquired/labels/injection']
        require(row['local_path'] == expected_path, 'SOURCE_PATH_ROLE', incident)
        path = safe_path(root, expected_path, allowed)
        require(path not in paths, 'DUPLICATE_SOURCE', incident)
        paths.add(path)
        require(path.stat().st_size == int(row['bytes']) and sha256(path) == row['sha256'], 'SOURCE_HASH_MISMATCH', incident)
        modality = path.stem if role == 'observation' else 'label'
        source_id = incident + ':' + modality
        info = {'incident_id':incident,'source_file_id':source_id,'role':role,
                'path':expected_path,'bytes':int(row['bytes']),'sha256':row['sha256'],
                'rows':None,'schema_hash':None}
        if role == 'observation':
            parquet = pq.ParquetFile(path)
            info['rows'] = parquet.metadata.num_rows
            info['schema_hash'] = canonical_hash(str(parquet.schema_arrow.remove_metadata()))
            info['columns'] = parquet.schema_arrow.names
            columns = set(info['columns'])
            required = {'metrics':{'time'}, 'logs':{'timestamp','container_name','message'},
                        'traces':{'startTimeMillis','duration','statusCode','serviceName','traceID','spanID','parentSpanID'}}[modality]
            require(required <= columns, 'RAW_SCHEMA', incident)
            time_col = {'metrics':'time','logs':'timestamp','traces':'startTimeMillis'}[modality]
            require(str(parquet.schema_arrow.field(time_col).type) == 'int64', 'RAW_TIME_TYPE', incident)
        files.append(info)
        source_map[source_id] = info
        roles[role] += 1
    require(dict(roles) == {'label':90,'observation':270}, 'ROLE_COUNT')
    expected_ids = set(config['incident_ids'])
    require(len(expected_ids) == 90 and {row['incident_id'] for row in files} == expected_ids, 'INCIDENT_COUNT')
    require(all({incident+':'+kind for kind in ('metrics','logs','traces','label')} <= set(source_map)
                for incident in expected_ids), 'MISSING_MODALITY')
    with (root/config['private_sources']['split-map.tsv']['path']).open(encoding='utf-8-sig', newline='') as handle:
        splits = list(csv.DictReader(handle, delimiter='\t'))
    split_map = {row['incident_id']:row for row in splits}
    require(len(splits) == len(split_map) == 90 and set(split_map) == expected_ids, 'SPLIT_IDS')
    counts = dict(collections.Counter(row['split'] for row in splits))
    require(counts == {'train':54,'dev':18,'test':18}, 'SPLIT_COUNTS')
    family = collections.defaultdict(list)
    for row in splits:
        require(row['split_version'] == config['split_version'], 'SPLIT_VERSION', row['incident_id'])
        family[row['scenario_family_id']].append(row['split'])
    require(len(family) == 30 and all(len(values) == 3 and len(set(values)) == 1 for values in family.values()), 'FAMILY_OVERLAP')
    gold = read_jsonl(root/config['private_sources']['ground_truth.jsonl']['path'])
    require(len(gold) == 90 and {row['incident_id'] for row in gold} == expected_ids, 'GOLD_IDS')
    require(all(row['label_release_revision'] == config['source_revision'] and row['scenario_family_id'] == split_map[row['incident_id']]['scenario_family_id'] for row in gold), 'GOLD_LINEAGE')
    observations = read_jsonl(root/config['inference_sources']['observations.jsonl']['path'])
    obs = {row['incident_id']:row for row in observations}
    require(len(obs) == len(observations) == 90 and set(obs) == expected_ids, 'OBSERVATION_IDS')
    for incident, row in obs.items():
        require(row['release_revision'] == config['source_revision'], 'SOURCE_REVISION', incident)
        require(all(row[key] == split_map[incident][key] for key in ('split','scenario_family_id')), 'OBSERVATION_MANAGEMENT', incident)
    evidence = {}
    row_counts = {'observations':len(obs)}
    for filename, kind in FILES.items():
        rows = read_jsonl(root/config['inference_sources'][filename]['path'])
        row_counts[kind] = len(rows)
        require(all(set(row) == set(config['source_fields'][filename]) for row in rows), 'SOURCE_SCHEMA')
        if kind == 'observations':
            continue
        for row in rows:
            incident = row['incident_id']
            require(incident in obs, 'FOREIGN_INCIDENT', incident)
            require(row['source_file_id'] == incident+':'+kind, 'FOREIGN_SOURCE', incident)
            require(row['evidence_id'] not in evidence, 'DUPLICATE_EVIDENCE', incident)
            evidence[row['evidence_id']] = row
            info = source_map[row['source_file_id']]
            start, end = timestamp(obs[incident]['observation_start']), timestamp(obs[incident]['observation_end'])
            if kind == 'metrics':
                require(row['source_row_start'] == 0 and row['source_row_end_exclusive'] == row['row_count'] == info['rows'], 'ROW_RANGE', incident)
                require(row['metric_name'] in info['columns'], 'METRIC_COLUMN', incident)
                require(timestamp(row['observation_start']) == start and timestamp(row['observation_end']) + 1 == end, 'END_CONVERSION', incident)
            else:
                require(type(row['source_row_index']) is int and 0 <= row['source_row_index'] < info['rows'], 'ROW_RANGE', incident)
                require(start <= timestamp(row['timestamp']) < end, 'WINDOW', incident)
    for incident, row in obs.items():
        for key in ('log_span_ids','metric_summary_ids','trace_span_ids'):
            require(len(row[key]) == len(set(row[key])), 'DUPLICATE_EVIDENCE', incident)
            require(all(ref in evidence and evidence[ref]['incident_id'] == incident for ref in row[key]), 'EVIDENCE_JOIN', incident)
    census = {'status':'pass','schema_version':config['schema_version'],'source_revision':config['source_revision'],
              'source_hash':canonical_hash(config['source_hashes']), 'incident_ids':sorted(expected_ids),
              'sample_train_ids':sorted(row['incident_id'] for row in splits if row['split']=='train')[:6],
              'counts':{'incidents':90,'families':len(family),'split':counts,'files':len(files),**dict(roles),
                        'bytes':sum(row['bytes'] for row in files),'processed_rows':row_counts,
                        'raw_rows':{kind:sum(row['rows'] for row in files if row['source_file_id'].endswith(':'+kind)) for kind in ('metrics','logs','traces')}},
              'files':sorted(files,key=lambda row:row['source_file_id']),
              'checks':['source_hashes','source_revision','path_role_allowlist','90_ids','54_18_18_split','30_disjoint_families','raw_schema','evidence_uniqueness','row_bounds','window_conversion','source_joins'],
              'scope':'All incidents: hashes/IDs/schema/counts/offsets/window only. Manual payload review uses six train incidents; see data-contract-review.md.'}
    return census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        census = validate_inputs(args.config)
        write_json(IMPL/'data/private/source-census.json', census)
        write_json(IMPL/'reports/input-validation.json', {key:value for key,value in census.items() if key not in ('files','incident_ids')})
        print('SOURCE_GATE_PASS:90 incidents;360 files')
    except DataContractError as exc:
        write_json(IMPL/'reports/input-validation.json', {'status':'fail','error_code':exc.code,'incident_id':exc.opaque_id})
        raise SystemExit(str(exc)) from None


if __name__ == '__main__':
    main()
