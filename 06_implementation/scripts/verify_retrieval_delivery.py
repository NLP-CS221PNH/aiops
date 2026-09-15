"""Reproduce the authorized synthetic delivery; never execute a real pilot."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import uuid

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))
for dependency in (IMPL / '.corpus-deps', IMPL / '.retrieval-deps'):
    sys.path.insert(0, str(dependency))
from src.retrieval.common import canonical_bytes, digest, read_json, sha256, utc_now
from src.retrieval.consumer import read_run, read_hits
from src.retrieval.runner import environment, implementation_hashes


def main():
    started = perf_counter()
    module_spec = importlib.util.spec_from_file_location('synthetic_fixture', IMPL / 'tests/fixtures/retrieval/build_fixture.py')
    fixture_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(fixture_module)
    directory = IMPL / '.test-work/retrieval' / ('verification-' + uuid.uuid4().hex[:12])
    fixture = fixture_module.build_fixture(directory)
    config = read_json(fixture['config_path'])
    config['run_root'] = 'runs/retrieval'
    fixture['config_path'].write_bytes(canonical_bytes(config) + b'\n')
    suffix = directory.name
    commands = []

    def cli(arguments, expected_code=0):
        command = [sys.executable, '-B', '-m', 'src.retrieval', *arguments]
        clock = perf_counter()
        result = subprocess.run(command, cwd=IMPL, capture_output=True, text=True)
        commands.append({'command': subprocess.list2cmdline(command), 'exit_code': result.returncode,
                         'expected_exit_code': expected_code, 'seconds': perf_counter() - clock,
                         'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()})
        if result.returncode != expected_code:
            raise RuntimeError('CLI verification failed: ' + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else json.loads(result.stderr)

    common = ['--mode', 'fixture', '--config', str(fixture['config_path'])]
    running = [*common, '--incident-list', str(fixture['allowlist_path'])]
    cli(['preflight', *common])
    cli(['index', *common, '--methods', 'bm25'])
    manifests = {}
    for label in ('fresh', 'repeat'):
        response = cli(['run', *running, '--methods', 'bm25', '--run-id', label + '-' + suffix])
        manifests[label] = Path(response['manifest'])
        cli(['validate-run', '--manifest', response['manifest']])
    response = cli(['run', *running, '--methods', 'bm25', '--run-id', 'resume-' + suffix,
                    '--stop-after', '1'], expected_code=1)
    interrupted = Path(response['manifest'])
    partial, partial_rows = read_run(interrupted)
    assert partial['counts'] == {'complete': 1, 'failed': 0, 'pending': 1}
    committed = {entry['path']: entry['sha256'] for entry in partial['records'] if entry['status'] == 'complete'}
    cli(['validate-run', '--manifest', str(interrupted)])
    cli(['run', *running, '--methods', 'bm25', '--run-id', 'resume-' + suffix, '--resume'])
    manifests['resume'] = interrupted
    for name, value in committed.items():
        assert sha256(interrupted.parent / name) == value
    cli(['validate-run', '--manifest', str(interrupted)])
    # Complete replay must not re-encode/rewrite any committed record.
    _, complete_rows = read_run(interrupted)
    complete_before = {row['record_key']: digest(row) for row in complete_rows}
    cli(['run', *running, '--methods', 'bm25', '--run-id', 'resume-' + suffix, '--resume'])
    assert complete_before == {row['record_key']: digest(row) for row in read_run(interrupted)[1]}
    ranked = lambda path: {row['record_key']: row['hits'] for row in read_run(path)[1]}
    assert ranked(manifests['fresh']) == ranked(manifests['repeat']) == ranked(manifests['resume'])
    context = read_hits(manifests['fresh'], 'fixture-empty', 'IR-B', limit=5)
    assert context['hits'] == [] and context['available_count'] == 0
    response = cli(['run', *running, '--methods', 'bm25,dense,hybrid', '--run-id', 'unavailable-' + suffix], expected_code=1)
    manifests['unavailable'] = Path(response['manifest'])
    unavailable, rows = read_run(manifests['unavailable'])
    assert unavailable['counts'] == {'complete': 2, 'failed': 4, 'pending': 0}
    assert all(row['error']['code'] == 'MODEL_UNAVAILABLE' for row in rows if row['status'] == 'failed')
    cli(['validate-run', '--manifest', response['manifest']])
    blocked = cli(['preflight', '--config', 'configs/retrieval.yaml'], expected_code=1)
    assert blocked['error'].startswith('CORPUS_RELEASE_PENDING')
    no_f1 = cli(['run', '--mode', 'frozen', '--config', 'configs/retrieval.yaml',
                 '--incident-list', str(fixture['allowlist_path'])], expected_code=1)
    assert no_f1['error'] == 'F1_AUTHENTICATED_HASH_REQUIRED'
    notebook = read_json(IMPL / 'notebooks/02_retrieval.ipynb')
    original_directory = Path.cwd()
    try:
        os.chdir(IMPL)
        namespace = {}
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                exec(compile(''.join(cell['source']), '02_retrieval.ipynb', 'exec'), namespace)
    finally:
        os.chdir(original_directory)
    artifacts = {}
    for manifest in manifests.values():
        artifacts[manifest.relative_to(IMPL).as_posix()] = sha256(manifest)
        for path in manifest.parent.rglob('*.json'):
            artifacts[path.relative_to(IMPL).as_posix()] = sha256(path)
    for path in directory.glob('*'):
        if path.is_file():
            artifacts[path.relative_to(IMPL).as_posix()] = sha256(path)
    result = {'schema_version': 'cs221-retrieval-technical-verification-v1', 'timestamp': utc_now(),
              'status': 'pass', 'synthetic_only': True, 'pilot_status': 'pending_reviewed_corpus',
              'neural_model_execution': 'not_performed_missing_runtime_and_weights',
              'seconds': perf_counter() - started, 'environment': environment(),
              'implementation_hashes': implementation_hashes(),
              'commands': commands, 'artifact_hashes': artifacts,
              'checks': {'bm25_repeat_exact': True, 'interruption_resume_preserves_committed': True,
                         'resume_no_record_rewrite': True, 'empty_context_no_padding': True,
                         'dense_hybrid_missing_model_records': True, 'candidate_release_gate': True,
                         'missing_f1_gate': True, 'notebook_same_cli_executed': True},
              'manifests': {key: value.relative_to(IMPL).as_posix() for key, value in manifests.items()}}
    report = IMPL / 'reports/retrieval-reproducibility.json'
    report.write_bytes(canonical_bytes(result) + b'\n')
    print(json.dumps({'status': result['status'], 'report': str(report), 'commands': len(commands),
                      'artifact_hashes': len(artifacts), 'seconds': result['seconds']}))


if __name__ == '__main__':
    main()
