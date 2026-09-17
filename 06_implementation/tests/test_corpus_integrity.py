"""Independent fixtures and mutation tests for historical corpus contracts."""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from src.corpus.common import (
    IMPL, ROOT, CorpusError, canonical_hash, load_config, parse_json, safe_path,
    sha256, text_hash, read_json, read_jsonl, write_json, write_jsonl,
)
from src.corpus.normalize import normalize_document, clip_spans
from src.corpus.tokenizer import CorpusTokenizer
from src.corpus.chunking import chunk_document, sections
from src.corpus.build_corpus import _output_path, _publish, build_corpus, build_digest_payload


class CorpusFixture(unittest.TestCase):
    def setUp(self):
        base = IMPL / '.test-work'
        base.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='corpus-fixture-', dir=base)
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)

    def source(self, raw, source_path='guide.md', title='Operational guide'):
        path = self.work / source_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw.encode('utf-8'))
        return {
            'document_id': 'synthetic-original-document',
            'source_id': 'D059', 'source_path': source_path,
            'raw_path': source_path, 'raw_sha256': sha256(path),
            'source_url': 'https://example.invalid/synthetic/' + source_path,
            'version_scope': 'synthetic-revision', 'title': title,
            'text': raw.removeprefix('\ufeff').replace('\r\n', '\n').replace('\r', '\n'),
        }

    def normalized(self, raw, source_path='guide.md', title='Operational guide'):
        return normalize_document(self.source(raw, source_path, title), root=self.work)


class NormalizationTests(CorpusFixture):
    def test_bom_crlf_unicode_mapping_retains_exact_codepoint_and_byte_positions(self):
        raw = '\ufeff# Giám sát 🚀\r\nHTTP 503\rnext\n'
        document = self.normalized(raw)
        expected = '# Giám sát 🚀\nHTTP 503\nnext\n'
        self.assertEqual(document['normalized_text'], expected)
        self.assertEqual(document['normalized_text_hash'], text_hash(expected))
        rocket = expected.index('🚀')
        span, = clip_spans(document['source_spans'], rocket, rocket + 1, root=self.work)
        self.assertEqual(raw[span['raw_start']:span['raw_end']], '🚀')
        self.assertEqual(span['raw_end'] - span['raw_start'], 1)
        self.assertEqual(span['raw_byte_end'] - span['raw_byte_start'], 4)
        self.assertNotEqual(span['raw_start'], span['raw_byte_start'])
        newline = expected.index('\n')
        span, = clip_spans(document['source_spans'], newline, newline + 1, root=self.work)
        self.assertEqual(raw[span['raw_start']:span['raw_end']], '\r\n')
        self.assertEqual(document['removed_spans'][0]['reason'], 'utf8_bom')
        self.assertEqual(document['removed_spans'][0]['raw_byte_end'], 3)

    def test_frontmatter_removal_preserves_literal_technical_content(self):
        raw = '---\r\ntitle: Hidden title\r\n---\r\n# Redis\r\nRUN redis-cli --raw GET CaseSensitive:503\r\n'
        document = self.normalized(raw)
        self.assertEqual(document['normalized_text'], '# Redis\nRUN redis-cli --raw GET CaseSensitive:503\n')
        self.assertTrue(any(s['reason'] == 'markdown_frontmatter' for s in document['removed_spans']))
        self.assertEqual(document['original_title'], 'Operational guide')

    def test_unterminated_frontmatter_is_kept_with_warning(self):
        raw = '---\nnot closed\nHTTP 503\n'
        document = self.normalized(raw)
        self.assertEqual(document['normalized_text'], raw)
        self.assertTrue(any(x['kind'] == 'unterminated_frontmatter' for x in document['rendering_warnings']))

    def test_yaml_copyright_is_metadata_not_markdown_and_license_attribution_survives(self):
        raw = '# Copyright 2018 Google LLC\n# Licensed under the Apache License\n# limitations under the License.\napiVersion: v1\nkind: Service\n'
        document = self.normalized(raw, 'redis-service.yaml', 'Copyright 2018 Google LLC')
        self.assertEqual(document['parser_kind'], 'yaml')
        self.assertEqual(document['normalized_text'], 'apiVersion: v1\nkind: Service\n')
        self.assertEqual(document['title'], 'redis-service Kubernetes manifest')
        self.assertEqual(document['original_title'], 'Copyright 2018 Google LLC')
        self.assertTrue(document['removed_spans'])
        self.assertEqual((self.work / 'redis-service.yaml').read_text(), raw)

    def test_proto_keeps_case_numeric_tags_and_commands(self):
        raw = 'syntax = "proto3";\n// # Not Markdown\nmessage CPUStatus { string HTTPCode = 503; }\n'
        document = self.normalized(raw, 'demo.proto')
        self.assertEqual(document['parser_kind'], 'proto')
        self.assertEqual(document['normalized_text'], raw)

    def test_technical_comment_adjacent_to_license_footer_is_preserved(self):
        for suffix, marker in (('yaml', '#'), ('proto', '//')):
            raw = (f'{marker} Copyright 2018 Google LLC\n'
                   f'{marker} Licensed under the Apache License\n'
                   f'{marker} limitations under the License.\n'
                   f'{marker} HTTP 503 requires checking redis-cache before restart\n'
                   'service: redis-cache\n')
            with self.subTest(suffix=suffix):
                document = self.normalized(raw, 'adjacent.' + suffix, 'Copyright 2018 Google LLC')
                self.assertEqual(document['normalized_text'],
                                 f'{marker} HTTP 503 requires checking redis-cache before restart\nservice: redis-cache\n')

    def test_unknown_hugo_include_is_never_fetched_or_silently_removed(self):
        raw = '# Check\n{{< include "missing.md" >}}\nHTTP 503\n'
        document = self.normalized(raw)
        self.assertEqual(document['normalized_text'], raw)
        self.assertTrue(any(w['kind'] == 'unresolved_local_directive' for w in document['rendering_warnings']))

    def test_known_include_uses_only_matching_local_asset_with_separate_provenance(self):
        source = self.source('# Check\n{{< include "snippet.md" >}}\n', 'content/en/guide.md')
        asset_path = self.work / 'asset.md'
        asset_path.write_bytes('Kiểm tra 🚀\r\n'.encode('utf-8'))
        asset = {'source_id': 'D059', 'source_path': 'content/en/includes/snippet.md',
                 'raw_path': 'asset.md', 'sha256': sha256(asset_path),
                 'source_url': 'https://example.invalid/synthetic/asset.md',
                 'release_revision': 'synthetic-revision',
                 'referenced_by_source_paths': ['content/en/guide.md']}
        document = normalize_document(source, [asset], root=self.work)
        self.assertEqual(document['normalized_text'], '# Check\nKiểm tra 🚀\n\n')
        inserted = [x for x in document['source_spans'] if x['role'] == 'supporting_asset']
        self.assertTrue(inserted)
        self.assertTrue(all(x['raw_path'] == 'asset.md' and x['include_origin']['raw_path'] == source['raw_path'] for x in inserted))
        wrong_revision = dict(asset, release_revision='another-revision')
        unchanged = normalize_document(source, [wrong_revision], root=self.work)
        self.assertEqual(unchanged['normalized_text'], source['text'])

    def test_corrupt_raw_hash_rejects_before_normalization(self):
        source = self.source('HTTP 503\n')
        (self.work / source['raw_path']).write_text('changed\n')
        with self.assertRaisesRegex(CorpusError, 'RAW_HASH'):
            normalize_document(source, root=self.work)

    def test_source_registry_text_cannot_disagree_with_raw(self):
        source = self.source('HTTP 503\n')
        source['text'] = 'HTTP 200\n'
        with self.assertRaisesRegex(CorpusError, 'SOURCE_TEXT_RAW_MISMATCH'):
            normalize_document(source, root=self.work)


class TokenizerAndPrimitiveTests(CorpusFixture):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.tokenizer = CorpusTokenizer(cls.config)

    def test_real_token_ids_include_passage_prefix_heading_and_special_overhead(self):
        content = self.tokenizer.content('Restart checks', 'Check HTTP 503 and redis-cache service logs.')
        # Independently measured pinned E5 IDs for this exact synthetic text.
        expected = [101, 6019, 1024, 23818, 14148, 4638, 8299, 2753, 2509, 1998, 2417, 2483, 1011, 17053, 2326, 15664, 1012, 102]
        actual = self.tokenizer.encode('passage: ' + content, add_special_tokens=True)
        self.assertEqual(actual.ids, expected)
        self.assertEqual(self.tokenizer.count(content), 18)
        self.assertEqual(actual.ids[0], 101)
        self.assertEqual(actual.ids[-1], 102)
        self.assertEqual(self.tokenizer.count('restart ' * 600), 604)
        self.assertIsNone(self.tokenizer.backend.truncation)
        self.assertIsNone(self.tokenizer.backend.padding)

    def test_tokenizer_asset_corruption_is_rejected(self):
        config = copy.deepcopy(self.config)
        config['tokenizer']['sha256'] = '0' * 64
        with self.assertRaisesRegex(CorpusError, 'TOKENIZER_ASSET_HASH'):
            CorpusTokenizer(config)

    def test_tokenizer_library_drift_is_rejected(self):
        config = copy.deepcopy(self.config)
        config['tokenizer']['library_version'] = '0.0.0'
        with self.assertRaisesRegex(CorpusError, 'TOKENIZER_LIBRARY_VERSION'):
            CorpusTokenizer(config)

    def test_unsupported_normalization_toggle_is_rejected_instead_of_ignored(self):
        config = copy.deepcopy(self.config)
        config['normalization']['remove_frontmatter'] = False
        path = self.work / 'unsupported-normalization.json'
        write_json(path, config)
        with self.assertRaisesRegex(CorpusError, 'NORMALIZATION'):
            load_config(path)

    def test_json_duplicate_keys_nonfinite_values_and_unstable_order(self):
        for value in ('{"id":1,"id":2}', '{"number":NaN}', '{"number":Infinity}'):
            with self.subTest(value=value), self.assertRaises(CorpusError):
                parse_json(value)
        self.assertEqual(canonical_hash({'a': 1, 'b': 2}), canonical_hash({'b': 2, 'a': 1}))

    def test_relative_paths_cannot_escape_root_or_use_absolute_path(self):
        for relative in ('../outside', str(self.work.parent / 'absolute')):
            with self.subTest(path=relative), self.assertRaises(CorpusError):
                safe_path(self.work, relative)


class ChunkingTests(CorpusFixture):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.tokenizer = CorpusTokenizer(cls.config)

    def document(self, raw, source_path='guide.md', title='Operational guide'):
        source = self.source(raw, source_path, title)
        document = {**source, **normalize_document(source, root=self.work)}
        document.update(source_revision='synthetic-revision', license='synthetic-license',
                        attribution='Synthetic fixture author', available_at='2023-01-01T00:00:00Z',
                        applicability={'decision': 'unknown', 'review_state': 'pending',
                                       'permitted_use': 'verify deployment before conditional reference use'})
        return document

    def test_fenced_markdown_heading_is_not_a_section_boundary(self):
        raw = '# First\n```sh\n# command comment\necho "HTTP 503"\n```\n## Second\ncheck\n'
        document = self.document(raw)
        parts = sections(document)
        self.assertEqual([item[2] for item in parts], ['First', 'Second'])
        self.assertEqual(parts[0][1], raw.index('## Second'))
        self.assertIn('# command comment', raw[parts[0][0]:parts[0][1]])

    def test_fence_marker_with_trailing_text_does_not_close_code_block(self):
        raw = '# First\n```sh\n```not-a-close\n# Still code\n```\n# Second\ncheck\n'
        document = self.document(raw)
        self.assertEqual([part[2] for part in sections(document)], ['First', 'Second'])

    def test_indented_local_yaml_include_comment_is_not_a_markdown_heading(self):
        source = self.source('  {{< code_sample file="pods/fixture.yaml" >}}\n', 'content/en/guide.md')
        asset_path = self.work / 'asset.yaml'
        asset_path.write_text('# YAML technical comment\nkind: Pod\n', encoding='utf-8')
        asset = {'source_id': 'D059', 'source_path': 'content/en/examples/pods/fixture.yaml',
                 'raw_path': 'asset.yaml', 'sha256': sha256(asset_path),
                 'source_url': 'https://example.invalid/synthetic/asset.yaml',
                 'release_revision': 'synthetic-revision',
                 'referenced_by_source_paths': ['content/en/guide.md']}
        document = {**source, **normalize_document(source, [asset], root=self.work)}
        self.assertEqual(document['normalized_text'], '  # YAML technical comment\nkind: Pod\n\n')
        self.assertEqual([part[2] for part in sections(document)], ['Operational guide'])

    def test_yaml_and_proto_comments_do_not_become_markdown_sections(self):
        for suffix, raw in (('yaml', '# Service\nkind: Service\n# Ports\nport: 80\n'),
                            ('proto', '// Protocol\n# synthetic comment\nmessage Ping {}\n')):
            with self.subTest(suffix=suffix):
                document = self.document(raw, 'fixture.' + suffix)
                self.assertEqual(sections(document), [(0, len(raw), 'Operational guide')])

    def test_long_command_block_splits_with_complete_coverage_real_budget_and_offsets(self):
        raw = '# Troubleshooting\n```sh\n' + ('kubectl exec redis -- redis-cli --raw GET CaseSensitive:503\n' * 120) + '```\n'
        document = self.document(raw)
        chunks, omitted = chunk_document(document, self.tokenizer, self.config, root=self.work)
        self.assertGreater(len(chunks), 2)
        self.assertEqual(omitted, [])
        covered = set()
        for chunk in chunks:
            start, end = chunk['start_offset'], chunk['end_offset']
            self.assertEqual(chunk['text'], raw[start:end])
            self.assertEqual(chunk['content'], chunk['section_heading'] + '\n' + chunk['text'])
            self.assertEqual(chunk['token_count'], self.tokenizer.count(chunk['content']))
            self.assertLessEqual(chunk['token_count'], 512)
            self.assertLessEqual(chunk['overlap_tokens'], self.config['chunking']['overlap_tokens'])
            self.assertEqual(chunk['text_hash'], text_hash(raw[start:end]))
            covered.update(range(start, end))
        self.assertEqual(covered, set(range(len(raw))))
        self.assertTrue(any(chunk['overlap_tokens'] > 0 for chunk in chunks))
        rebuilt = chunk_document(document, self.tokenizer, self.config, root=self.work)
        self.assertEqual(rebuilt, (chunks, omitted))

    def test_prefix_and_heading_overhead_force_split_before_512_content_tokens(self):
        raw = 'restart ' * 505
        document = self.document(raw, title='Operational restart incident checks')
        self.assertLess(len(self.tokenizer.encode(raw, add_special_tokens=False).ids), 512)
        self.assertGreater(self.tokenizer.count(self.tokenizer.content(document['title'], raw)), 512)
        chunks, _ = chunk_document(document, self.tokenizer, self.config, root=self.work)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk['token_count'] <= 512 for chunk in chunks))

    def test_overlong_heading_is_explicit_failure_not_silent_truncation(self):
        document = self.document('HTTP 503\n', title='restart ' * 510)
        with self.assertRaisesRegex(CorpusError, 'HEADING_EXCEEDS_TOKEN_BUDGET'):
            chunk_document(document, self.tokenizer, self.config, root=self.work)

    def test_content_or_chunking_version_change_invalidates_ids(self):
        document = self.document('HTTP 503\n')
        original, _ = chunk_document(document, self.tokenizer, self.config, root=self.work)
        changed = self.document('HTTP 504\n')
        replacement, _ = chunk_document(changed, self.tokenizer, self.config, root=self.work)
        self.assertNotEqual(original[0]['chunk_id'], replacement[0]['chunk_id'])
        config = copy.deepcopy(self.config)
        config['chunking_version'] = 'synthetic-new-version'
        versioned, _ = chunk_document(changed, self.tokenizer, config, root=self.work)
        self.assertNotEqual(replacement[0]['chunk_id'], versioned[0]['chunk_id'])


class PublicationBoundaryTests(CorpusFixture):
    def test_outputs_cannot_target_raw_preparation_or_unowned_files(self):
        from src.corpus.common import ROOT
        for output in (ROOT / '03_collection_plan/knowledge-corpus-historical/raw',
                       IMPL / 'data/knowledge-preparation', IMPL / 'data',
                       IMPL / 'configs'):
            with self.subTest(path=str(output)), self.assertRaises(CorpusError):
                _output_path(output)
        foreign = self.work / 'foreign'
        foreign.mkdir()
        (foreign / 'unrelated.txt').write_text('must be preserved')
        with self.assertRaisesRegex(CorpusError, 'OUTPUT_CONTAINS_FOREIGN_FILES'):
            _output_path(foreign)
        self.assertEqual((foreign / 'unrelated.txt').read_text(), 'must be preserved')

    def test_failed_atomic_publish_restores_previous_candidate_bytes(self):
        import os
        output = self.work / 'previous'
        output.mkdir()
        (output / 'data.txt').write_bytes(b'previous exact bytes')
        stage = self.work / '.previous-build-synthetic'
        stage.mkdir()
        (stage / 'data.txt').write_bytes(b'new candidate bytes')
        real_replace = os.replace

        def fail_stage(source, destination):
            if Path(source) == stage:
                raise OSError('synthetic publication failure')
            return real_replace(source, destination)

        with mock.patch('src.corpus.build_corpus.os.replace', side_effect=fail_stage):
            with self.assertRaisesRegex(OSError, 'synthetic publication failure'):
                _publish(stage, output)
        self.assertEqual((output / 'data.txt').read_bytes(), b'previous exact bytes')
        self.assertEqual((stage / 'data.txt').read_bytes(), b'new candidate bytes')


class WholeCorpusTests(CorpusFixture):
    """Exercise all 74 originals; mutations affect temporary derivatives only."""
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        snapshot_receipt = (
            ROOT / "03_collection_plan/knowledge-corpus-historical/raw/source-snapshots/D057/LICENSE.receipt.json"
        )
        if not snapshot_receipt.is_file():
            raise unittest.SkipTest(
                "source-snapshots are archive_private and absent from the public tree"
            )
        base = IMPL / '.test-work'
        base.mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix='corpus-full-suite-', dir=base)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.suite_root = Path(cls.temporary.name)
        cls.baseline = cls.suite_root / 'baseline'
        cls.manifest = build_corpus(output=cls.baseline)
        cls.artifact_hashes = {p.name: sha256(p) for p in cls.baseline.iterdir()}

    def setUp(self):
        super().setUp()
        self.candidate = self.work / 'candidate'
        shutil.copytree(self.baseline, self.candidate)
        self.records = {name: read_jsonl(self.candidate / name) for name in
                        ('documents.jsonl', 'chunks.jsonl', 'citation-registry.jsonl', 'chunk-lineage.jsonl')}
        self.current_manifest = read_json(self.candidate / 'corpus-manifest.json')
        self.audit = read_json(self.candidate / 'token-audit.json')
        with (self.candidate / 'applicability.tsv').open(encoding='utf-8', newline='') as handle:
            self.applicability = list(csv.DictReader(handle, delimiter='\t'))

    def refresh(self, *, recompute_digest=True):
        if recompute_digest:
            payload = build_digest_payload(self.config, self.current_manifest['source_checksums'],
                                           self.records['documents.jsonl'], self.records['chunks.jsonl'],
                                           self.records['citation-registry.jsonl'], self.records['chunk-lineage.jsonl'],
                                           self.applicability)
            digest = canonical_hash(payload)
            self.current_manifest['corpus_hash'] = digest
            self.current_manifest['validation_receipt']['corpus_hash'] = digest
            self.audit['corpus_hash'] = digest
            for rows in self.records.values():
                for row in rows:
                    row['corpus_hash'] = digest
        for name, rows in self.records.items():
            write_jsonl(self.candidate / name, rows)
        write_json(self.candidate / 'token-audit.json', self.audit)
        with (self.candidate / 'applicability.tsv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.applicability[0]), delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(self.applicability)
        for name in self.current_manifest['derived_file_hashes']:
            self.current_manifest['derived_file_hashes'][name] = sha256(self.candidate / name)
        write_json(self.candidate / 'corpus-manifest.json', self.current_manifest)

    def validate(self, **kwargs):
        from src.corpus.validate_corpus import validate_corpus
        return validate_corpus(self.candidate, **kwargs)

    def test_all_74_sources_integrity_true_counts_and_no_release_claim(self):
        from collections import Counter
        result = self.validate()
        self.assertTrue(result['technical_valid'])
        self.assertFalse(result['release_ready'])
        self.assertEqual(result['counts']['source_documents'], 74)
        self.assertEqual(result['counts']['old_chunks'], 580)
        self.assertEqual(Counter(d['source_id'] for d in self.records['documents.jsonl']),
                         {'D057': 25, 'D058': 14, 'D059': 35})
        self.assertEqual(self.current_manifest['counts']['supporting_assets'], 12)
        self.assertEqual(self.current_manifest['index_whitelist'], [])
        self.assertEqual(result['coverage'], 'unjudged')
        self.assertEqual(result['compatibility'], 'unknown')
        self.assertGreater(result['counts']['candidate_chunks'], 0)
        self.assertLessEqual(result['counts']['max_tokens'], 512)
        self.assertTrue(all(d['applicability']['review_state'] == 'pending' for d in self.records['documents.jsonl']))

    def test_independent_process_rebuild_is_byte_identical(self):
        destination = self.work / 'independent-replay'
        script = (f'import sys; sys.path.insert(0, {str(IMPL)!r}); '
                  'from src.corpus.build_corpus import build_corpus; '
                  f'build_corpus(output={str(destination)!r})')
        completed = subprocess.run([sys.executable, '-I', '-B', '-c', script],
                                   text=True, capture_output=True, timeout=180)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual({p.name: sha256(p) for p in destination.iterdir()}, self.artifact_hashes)

    def test_human_release_gate_remains_pending_after_technical_pass(self):
        with self.assertRaisesRegex(CorpusError, 'RELEASE_PENDING'):
            self.validate(require_reviewed=True)

    def test_altered_artifact_bytes_and_extra_mapping_file_are_rejected(self):
        path = self.candidate / 'chunks.jsonl'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(CorpusError, 'DERIVATIVE_FILE_HASH'):
            self.validate()
        path.write_bytes((self.baseline / 'chunks.jsonl').read_bytes())
        (self.candidate / 'proposed-mappings.jsonl').write_text('{"synthetic":"annotation answers forbidden"}\n')
        with self.assertRaisesRegex(CorpusError, 'INVENTORY|FOREIGN|ARTIFACT'):
            self.validate()

    def test_foreign_document_and_corpus_ids_rejected_after_outer_rehash(self):
        chunk = self.records['chunks.jsonl'][0]
        chunk['document_id'] = 'current-snapshot-document'
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'FOREIGN_DOCUMENT_ID'):
            self.validate()

    def test_foreign_corpus_stamp_rejected_after_file_hash_refreshed(self):
        self.records['chunks.jsonl'][0]['corpus_hash'] = '0' * 64
        self.refresh(recompute_digest=False)
        with self.assertRaisesRegex(CorpusError, 'FOREIGN_CORPUS_ID'):
            self.validate()

    def test_forged_chunk_and_citation_provenance_rejected_after_full_rehash(self):
        self.records['chunks.jsonl'][0]['source_url'] = 'https://example.invalid/forged'
        self.records['citation-registry.jsonl'][0]['source_url'] = 'https://example.invalid/forged'
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'CHUNK_PROVENANCE'):
            self.validate()

    def test_incorrect_token_counts_rejected_after_full_rehash(self):
        self.records['chunks.jsonl'][0]['token_count'] -= 1
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'TOKEN_BUDGET'):
            self.validate()

    def test_corrupt_citation_span_rejected_after_full_rehash(self):
        self.records['citation-registry.jsonl'][0]['normalized_span']['end'] -= 1
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'CITATION_NORMALIZED_SPAN'):
            self.validate()

    def test_citation_cannot_change_license_applicability_or_offset_units(self):
        original = copy.deepcopy(self.records['citation-registry.jsonl'][0])
        changes = [('license', 'invented-license'), ('source_id', 'D000'),
                   ('attribution', 'incorrect-author'), ('offset_unit', 'utf8-bytes'),
                   ('review_state', 'approved'),
                   ('applicability', {**original['applicability'], 'decision': 'allowed'})]
        for field, value in changes:
            self.records['citation-registry.jsonl'][0] = copy.deepcopy(original)
            self.records['citation-registry.jsonl'][0][field] = value
            self.refresh()
            with self.subTest(field=field), self.assertRaisesRegex(CorpusError, 'CITATION_METADATA'):
                self.validate()

    def test_lineage_relation_rejected_after_full_rehash(self):
        self.records['chunk-lineage.jsonl'][0]['relation'] = 'one_to_one_confirmed_relevant'
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'LINEAGE_RELATION'):
            self.validate()

    def test_lineage_foreign_chunks_rejected_after_full_rehash(self):
        row = self.records['chunk-lineage.jsonl'][0]
        other = next(c['chunk_id'] for c in self.records['chunks.jsonl'] if c['document_id'] != row['parent_document_id'])
        row['new_chunk_ids'] = [other]
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'LINEAGE_FOREIGN_CHUNK'):
            self.validate()

    def test_lineage_new_spans_rejected_after_full_rehash(self):
        row = next(r for r in self.records['chunk-lineage.jsonl'] if r['new_spans'])
        row['new_spans'][0]['spans'][0]['raw_end'] += 1
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'LINEAGE_NEW_SPANS'):
            self.validate()

    def test_misreported_counts_rejected(self):
        self.current_manifest['counts']['candidate_chunks'] += 1
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'MANIFEST_COUNTS'):
            self.validate()

    def test_released_index_whitelist_cannot_contain_candidate_ids(self):
        self.current_manifest['index_whitelist'] = [self.records['documents.jsonl'][0]['document_id']]
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'RELEASE|INDEX|WHITELIST'):
            self.validate()

    def test_shifted_valid_content_cannot_reuse_old_chunk_id(self):
        from src.corpus.common import ROOT
        chunk = self.records['chunks.jsonl'][0]
        document = next(d for d in self.records['documents.jsonl'] if d['document_id'] == chunk['document_id'])
        chunk['start_offset'] += 1
        chunk['text'] = document['normalized_text'][chunk['start_offset']:chunk['end_offset']]
        chunk['content'] = chunk['section_heading'] + '\n' + chunk['text']
        chunk['text_hash'] = text_hash(chunk['text'])
        chunk['content_hash'] = text_hash(chunk['content'])
        chunk['token_count'] = CorpusTokenizer(self.config).count(chunk['content'])
        chunk['source_spans'] = clip_spans(document['source_spans'], chunk['start_offset'], chunk['end_offset'], root=ROOT)
        citation = self.records['citation-registry.jsonl'][0]
        citation['normalized_span']['start'] = chunk['start_offset']
        for key in ('source_spans', 'text_hash', 'content_hash'):
            citation[key] = copy.deepcopy(chunk[key])
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'CHUNK_CONTENT_ID'):
            self.validate()

    def test_citation_resolver_accepts_matching_ids_and_rejects_unknown_or_stale(self):
        from src.corpus.citation_registry import resolve_citation
        chunk = self.records['chunks.jsonl'][0]
        citation = resolve_citation(chunk['chunk_id'], self.candidate, self.current_manifest['corpus_hash'])
        self.assertEqual(citation['document_id'], chunk['document_id'])
        self.assertEqual(citation['normalized_span'], {'start': chunk['start_offset'], 'end': chunk['end_offset']})
        with self.assertRaisesRegex(CorpusError, 'UNKNOWN_OR_DUPLICATE_CITATION'):
            resolve_citation('foreign-current-chunk', self.candidate)
        with self.assertRaisesRegex(CorpusError, 'FOREIGN_CORPUS_HASH'):
            resolve_citation(chunk['chunk_id'], self.candidate, '0' * 64)

    def test_token_audit_omitted_prefix_policy_rejected(self):
        self.audit['token_count_includes_prefix_and_special_tokens'] = False
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'TOKEN_AUDIT_POLICY'):
            self.validate()

    def test_dropped_chunk_cannot_pass_by_rebuilding_lineage_counts_and_all_hashes(self):
        from collections import Counter
        from src.corpus.common import ROOT
        from src.corpus.build_corpus import _lineage
        counts = Counter(c['document_id'] for c in self.records['chunks.jsonl'])
        lost = next(c for c in self.records['chunks.jsonl'] if counts[c['document_id']] > 1)
        self.records['chunks.jsonl'] = [c for c in self.records['chunks.jsonl'] if c['chunk_id'] != lost['chunk_id']]
        self.records['citation-registry.jsonl'] = [c for c in self.records['citation-registry.jsonl'] if c['chunk_id'] != lost['chunk_id']]
        source_root = ROOT / self.config['source_root']
        self.records['chunk-lineage.jsonl'] = _lineage(
            read_jsonl(source_root / 'chunks.jsonl'), read_jsonl(source_root / 'documents.jsonl'),
            self.records['documents.jsonl'], self.records['chunks.jsonl'], self.config)
        chunks = self.records['chunks.jsonl']
        self.current_manifest['chunk_whitelist'] = [c['chunk_id'] for c in chunks]
        self.current_manifest['counts']['candidate_chunks'] = len(chunks)
        self.audit.update(candidate_chunk_count=len(chunks), max_tokens=max(c['token_count'] for c in chunks),
                          short_chunk_count=sum(c['short_chunk'] for c in chunks),
                          overlap_chunk_count=sum(c['overlap_characters'] > 0 for c in chunks))
        self.audit['chunks'] = [{'chunk_id': c['chunk_id'], 'token_count': c['token_count'],
                                 'characters': len(c['text']), 'overlap_tokens': c['overlap_tokens'],
                                 'short_chunk': c['short_chunk']} for c in chunks]
        self.refresh()
        with self.assertRaisesRegex(CorpusError, 'COVERAGE|UNCOVERED|GAP'):
            self.validate()

    def test_changed_config_cannot_overwrite_existing_candidate_without_version_decision(self):
        config = copy.deepcopy(self.config)
        config['chunking']['overlap_tokens'] = 31
        config_path = self.work / 'changed-corpus.json'
        write_json(config_path, config)
        before = {p.name: sha256(p) for p in self.candidate.iterdir()}
        with self.assertRaisesRegex(CorpusError, 'OUTPUT_VERSION_CONFLICT'):
            build_corpus(config_path, self.candidate)
        self.assertEqual({p.name: sha256(p) for p in self.candidate.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
