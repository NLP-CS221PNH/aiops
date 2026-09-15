"""Offline BM25 browsing and annotation seed pool. Not a measured IR/RAG experiment."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
STOP = set('a an and are as at be been by for from has have in into is it of on or that the their this to was were will with'.split())


def tokens(text):
    # Preserve exact technical tokens and add components for mixed natural language queries.
    out = []
    for value in re.findall(r'[\w]+(?:[-.:/][\w]+)*', text.lower()):
        if value in STOP:
            continue
        out.append(value)
        parts = re.split(r'[-.:/]', value)
        if len(parts) > 1:
            out.extend(x for x in parts if len(x) > 1 and x not in STOP)
    return out


def readjsonl(path):
    with path.open(encoding='utf-8') as file:
        return [json.loads(line) for line in file if line.strip()]


class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tf = [Counter(tokens(c['section_heading'] + '\n' + c['text'])) for c in chunks]
        self.lengths = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        self.postings = defaultdict(list)
        for i, terms in enumerate(self.tf):
            for term, freq in terms.items():
                self.postings[term].append((i, freq))

    def search(self, query, depth):
        scores = defaultdict(float)
        n = len(self.chunks)
        for term in set(tokens(query)):
            posts = self.postings.get(term, [])
            if not posts:
                continue
            idf = math.log(1 + (n - len(posts) + 0.5) / (len(posts) + 0.5))
            for i, freq in posts:
                denominator = freq + 1.2 * (0.25 + 0.75 * self.lengths[i] / self.avg)
                scores[i] += idf * freq * 2.2 / denominator
        result = []
        for rank, (i, score) in enumerate(sorted(scores.items(), key=lambda item: (-item[1], self.chunks[item[0]]['chunk_id']))[:depth], 1):
            c = self.chunks[i]
            result.append({'rank': rank, 'score': score, 'chunk_id': c['chunk_id'], 'document_id': c['parent_document_id'], 'section_heading': c['section_heading'], 'source_url': c['source_url'], 'text': c['text']})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query')
    parser.add_argument('--incident')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--prepare-pilot', action='store_true')
    parser.add_argument('--corpus', default='03_collection_plan/knowledge-corpus-historical/chunks.jsonl')
    args = parser.parse_args()
    chunks_path = ROOT / args.corpus
    chunks = readjsonl(chunks_path)
    searcher = BM25(chunks)
    if args.prepare_pilot or args.incident:
        observations = readjsonl(ROOT / '02_datasets/processed/observations.jsonl')
    if args.prepare_pilot:
        with (ROOT / '02_datasets/processed/split-map.tsv').open(encoding='utf-8-sig') as file:
            training = {r['incident_id'] for r in csv.DictReader(file, delimiter='\t') if r['split'] == 'train'}
        eligible = sorted([o for o in observations if o['incident_id'] in training], key=lambda o: o['incident_id'])
        # Spread the pilot across families before taking repeated runs.
        selected, seen = [], set()
        for o in eligible:
            family = o.get('scenario_family_id', o['incident_id'])
            if family not in seen:
                selected.append(o)
                seen.add(family)
        selected += [o for o in eligible if o not in selected]
        selected = selected[:20]
        out = ROOT / '05_research/retrieval-preview'
        out.mkdir(parents=True, exist_ok=True)
        # Never erase human work during a repeated preparation command.
        for name in ['annotator-a.tsv', 'annotator-b.tsv']:
            target = out / name
            if target.exists():
                with target.open(encoding='utf-8-sig', newline='') as file:
                    existing = list(csv.DictReader(file, delimiter='\t'))
                if any(any((r.get(k) or '').strip() for k in ['relevance_grade', 'evidence_role', 'rationale', 'annotator_id']) or r.get('annotation_state', 'unjudged') != 'unjudged' for r in existing):
                    raise RuntimeError(f'Refusing to overwrite annotations in {target}; preserve this version before building a new pool.')
        diagnostics, blind = [], []
        for obs in selected:
            iid = obs['incident_id']
            hits = searcher.search(obs['symptom_query'], 20)
            for hit in hits:
                candidate_id = hashlib.sha256((iid + ':' + hit['chunk_id']).encode()).hexdigest()[:16]
                diagnostics.append({'candidate_id': candidate_id, 'incident_id': iid, 'query': obs['symptom_query'], 'retriever': 'bm25_preview_only', **hit})
                blind.append({'candidate_id': candidate_id, 'incident_id': iid, 'document_id': hit['document_id'], 'chunk_id': hit['chunk_id'], 'relevance_grade': '', 'evidence_role': '', 'rationale': '', 'annotator_id': '', 'annotation_state': 'unjudged'})
        random.Random(221).shuffle(blind)
        (out / 'candidate-diagnostics.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in diagnostics), encoding='utf-8')
        for name in ['annotator-a.tsv', 'annotator-b.tsv']:
            with (out / name).open('w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=list(blind[0]) if blind else ['candidate_id'], delimiter='\t')
                writer.writeheader()
                writer.writerows(blind)
        info = {'status': 'annotation_seed_pool_only_not_final_qrels', 'n_incidents': len(selected), 'n_candidates': len(blind), 'incident_ids': [o['incident_id'] for o in selected], 'selection': 'train_only_family_spread_then_id_order', 'retrievers_included': ['bm25_preview_only'], 'retrievers_missing_for_plan_pool': ['dense', 'hybrid'], 'human_judgments_completed': 0, 'corpus_path': chunks_path.relative_to(ROOT).as_posix(), 'corpus_hash': hashlib.sha256(chunks_path.read_bytes()).hexdigest(), 'query_source': 'deterministic_observation_only_symptom_query', 'limitations': ['Not an estimate of retrieval quality.', 'Pool must be extended with dense and hybrid before final evaluation.', 'Historical corpus still needs deployment/version applicability review.']}
        (out / 'pilot-pool-status.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
        print(json.dumps(info))
        return
    query = args.query
    if args.incident:
        obs = next((o for o in observations if o['incident_id'] == args.incident), None)
        if obs is None:
            parser.error('Unknown incident ID; use IDs from observations.jsonl.')
        query = obs['symptom_query']
    if not query:
        parser.error('Use --query, --incident, or --prepare-pilot.')
    print(json.dumps({'query': query, 'incident_id': args.incident, 'status': 'unjudged_preview', 'retriever': 'bm25-preview-v1', 'corpus_path': chunks_path.relative_to(ROOT).as_posix(), 'corpus_sha256': hashlib.sha256(chunks_path.read_bytes()).hexdigest(), 'hits': searcher.search(query, args.top_k)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
