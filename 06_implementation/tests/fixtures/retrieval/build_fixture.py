"""Explicit synthetic integration inputs, separate from all real candidate data."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

IMPL = Path(__file__).resolve().parents[3]
if str(IMPL) not in sys.path:
    sys.path.insert(0, str(IMPL))
from src.retrieval.common import canonical_bytes, digest, read_json, safe_path, sha256, text_hash


def build_fixture(directory):
    directory = safe_path(directory, write=True, roots=('.test-work/retrieval',))
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError('fixture directory must be empty; choose a new directory')

    def write(name, value, jsonl=False):
        path = directory / name
        path.write_bytes(b''.join(canonical_bytes(row) + b'\n' for row in value) if jsonl
                         else canonical_bytes(value) + b'\n')
        return path

    content = [('fixture-a', 'fixture-doc-a', 'alpha', 'alpha beta'),
               ('fixture-b', 'fixture-doc-b', 'beta', 'beta gamma'),
               ('fixture-c', 'fixture-doc-c', 'gamma', 'gamma delta')]
    corpus_hash = digest({'synthetic': True, 'content': content})
    chunks = [{'chunk_id': cid, 'document_id': did, 'section_heading': heading,
               'text': text, 'content': heading + '\n' + text,
               'content_hash': text_hash(heading + '\n' + text), 'corpus_hash': corpus_hash}
              for cid, did, heading, text in content]
    chunks_path = write('chunks.jsonl', chunks, True)
    corpus_path = write('corpus-manifest.json', {'schema_version': 'cs221-synthetic-corpus-v1',
                'synthetic': True, 'corpus_hash': corpus_hash,
                'index_whitelist': [row[1] for row in content],
                'derived_file_hashes': {'chunks.jsonl': sha256(chunks_path)}})
    input_path = write('input-manifest.json', {'schema_version': 'cs221-synthetic-input-v1', 'synthetic': True})
    window = {'start': '2000-01-01T00:00:00Z', 'end': '2000-01-01T00:01:00Z'}
    queries = [{'incident_id': iid, 'representation_id': 'R2', 'query_text': text,
                'query_hash': text_hash(text), 'input_manifest_hash': sha256(input_path), 'window': window}
               for iid, text in [('fixture-one', 'alpha'), ('fixture-empty', 'zzznomatchzzz')]]
    query_path = write('queries.jsonl', queries, True)
    properties = {key: {'type': 'string'} for key in queries[0] if key != 'window'}
    properties['window'] = {'type': 'object', 'additionalProperties': False,
                            'properties': {'start': {'type': 'string'}, 'end': {'type': 'string'}},
                            'required': ['start', 'end']}
    schema_path = write('query-schema.json', {'$defs': {'query': {'type': 'object',
                'additionalProperties': False, 'properties': properties, 'required': list(properties)}}})
    query_manifest = write('query-manifest.json', {'schema_version': 'cs221-synthetic-queries-v1',
              'synthetic': True, 'input_manifest_hash': sha256(input_path),
              'outputs': [{'path': query_path.name, 'rows': len(queries), 'sha256': sha256(query_path)}]})
    config = deepcopy(read_json(IMPL / 'configs/retrieval.yaml'))
    for key, path in [('corpus_manifest', corpus_path), ('query_manifest', query_manifest),
                      ('query_schema', schema_path), ('input_manifest', input_path)]:
        config[key] = path.relative_to(IMPL).as_posix()
        config[key + '_sha256'] = sha256(path)
    config.update(fixture=True, query_file='queries.jsonl',
                  cache_dir=(directory / 'cache').relative_to(IMPL).as_posix(),
                  run_root=(directory / 'runs').relative_to(IMPL).as_posix())
    config_path = write('retrieval.json', config)
    allowlist = write('allowlist.json', {'schema_version': 'cs221-retrieval-allowlist-v1',
                    'mode': 'fixture', 'incident_ids': [q['incident_id'] for q in queries],
                    'query_manifest_hash': sha256(query_manifest)})
    return {'config_path': config_path, 'allowlist_path': allowlist, 'directory': directory}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print({key: str(value) for key, value in build_fixture(args.output).items()})
