"""Write explicit proposal config and blank results table; never run or fabricate experiments."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '05_research'
resources = json.loads((OUT / 'source-snapshots/support-resources.json').read_text(encoding='utf-8'))
models = {r['repo_id']: r for r in resources if r['resource_kind'] == 'models'}
config = {
    'schema_version': '1.0',
    'status': 'proposal_not_executed_not_test_frozen',
    'task': 'offline_evidence_grounded_incident_assistance',
    'primary_dataset': 'RCAEval/RE2-OB',
    'proposed_language': 'en',
    'inputs': {
        'observations': '02_datasets/processed/observations.jsonl',
        'knowledge_documents': '03_collection_plan/knowledge-corpus-historical/documents.jsonl',
        'knowledge_chunks': '03_collection_plan/knowledge-corpus-historical/chunks.jsonl',
        'knowledge_snapshot_policy': 'pre_2024_commit_snapshot_primary; deployment_compatibility_still_requires_review',
        'current_snapshot_comparison': '03_collection_plan/knowledge-corpus/chunks.jsonl',
        'labels_are_model_inputs': False,
        'raw_paths_are_model_inputs': False,
        'historical_simulation_eligible': False,
    },
    'dense': {
        'model_id': 'intfloat/e5-small-v2',
        'revision': models['intfloat/e5-small-v2']['revision'],
        'query_prefix': 'query: ', 'passage_prefix': 'passage: ',
        'normalize_embeddings': True, 'max_input_tokens': 512,
        'candidate_depth': 50, 'weights_downloaded': False,
    },
    'dense_alternative': {
        'model_id': 'BAAI/bge-small-en-v1.5',
        'revision': models['BAAI/bge-small-en-v1.5']['revision'],
        'query_prefix': 'Represent this sentence for searching relevant passages: ',
        'passage_prefix': '', 'normalize_embeddings': True, 'weights_downloaded': False,
    },
    'bm25': {'k1': 1.2, 'b': 0.75, 'candidate_depth': 50, 'tokenizer': 'must_freeze_entity_preserving_implementation_on_dev'},
    'fusion': {'method': 'reciprocal_rank_fusion', 'rrf_constant': 60, 'weights': [1.0, 1.0]},
    'reranker': {
        'model_id': 'BAAI/bge-reranker-base',
        'revision': models['BAAI/bge-reranker-base']['revision'],
        'pair_max_input_tokens': 512, 'candidate_depth': 50, 'weights_downloaded': False,
    },
    'generator': {'model_id': None, 'revision': None, 'decoding': None, 'selection_status': 'choose_after_hardware_and_pilot_then_hold_fixed'},
    'context': {'top_k': 5, 'max_tokens': None, 'budget_status': 'set_once_generator_tokenizer_is_selected'},
    'evaluation': {'k_values': [1, 3, 5, 10], 'primary_k': 5, 'unit': 'incident_or_scenario_family', 'qrels_status': 'human_annotation_required', 'test_results': None},
    'conditions': ['IR-1_BM25', 'IR-2_dense', 'IR-3_hybrid', 'IR-4_hybrid_rerank', 'GEN-0_no_RAG', 'GEN-1_naive_RAG', 'GEN-2_hybrid_RAG', 'GEN-3_reranked_RAG'],
    'freeze_checks': ['human_qrels_adjudicated', 'family_split_reviewed', 'knowledge_version_policy_accepted', 'redaction_reviewed_before_external_model', 'all_models_and_tokenizers_pinned', 'prompt_context_and_decoding_fixed', 'test_not_used_for_model_selection'],
}
(OUT / 'experiment-proposal.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
with (OUT / 'experiment-results-template.tsv').open('w', encoding='utf-8', newline='') as file:
    fields = ['condition', 'run_id', 'status', 'n_incidents', 'n_groups', 'qrels_version', 'split_hash', 'corpus_hash', 'config_hash', 'recall_at_5', 'mrr_at_5', 'ndcg_at_5', 'rca_hit_at_1', 'citation_precision', 'unsupported_claim_rate', 'coverage', 'selective_risk', 'latency_p50_ms', 'latency_p95_ms', 'ci_low', 'ci_high', 'ci_method']
    writer = csv.DictWriter(file, fieldnames=fields, delimiter='\t')
    writer.writeheader()
    for condition in config['conditions']:
        writer.writerow({'condition': condition, 'status': 'NOT_RUN'})
print('Wrote proposal config and 8 empty experiment rows.')
