import pytest
import math
from src.evaluation.metrics import (
    calculate_ndcg,
    calculate_mrr,
    calculate_recall,
    collapse_to_documents,
    CalculationResult,
    Status
)
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]

def test_ndcg_calculation():
    # qrels: doc1->2, doc2->1, doc3->0
    qrels = {"doc1": 2, "doc2": 1, "doc3": 0}
    # Ranking: doc1, doc2, doc3
    ranking = ["doc1", "doc2", "doc3"]
    
    res = calculate_ndcg(ranking, qrels, k=5)
    assert res.status == Status.ELIGIBLE
    
    # IDCG: gain(2)/log2(2) + gain(1)/log2(3) = 3/1 + 1/1.5849 = 3 + 0.6309 = 3.6309
    # DCG: same
    assert math.isclose(res.value, 1.0)
    
def test_ndcg_no_relevant():
    qrels = {"doc3": 0}
    ranking = ["doc3"]
    res = calculate_ndcg(ranking, qrels, k=5)
    assert res.status == Status.UNDEFINED
    assert res.reason == "no_relevant_qrels"

def test_ndcg_empty_ranking():
    qrels = {"doc1": 1}
    ranking = []
    res = calculate_ndcg(ranking, qrels, k=5)
    assert res.status == Status.ELIGIBLE
    assert res.value == 0.0

def test_ndcg_unjudged_top_k():
    qrels = {"doc1": 2}
    ranking = ["doc1", "doc4"]
    res = calculate_ndcg(ranking, qrels, k=5)
    assert res.status == Status.UNDEFINED
    assert res.reason == "unjudged_in_top_k"

def test_mrr_calculation():
    qrels = {"doc1": 0, "doc2": 1}
    ranking = ["doc1", "doc2"]
    res = calculate_mrr(ranking, qrels, k=10)
    assert res.status == Status.ELIGIBLE
    assert res.value == 0.5

def test_mrr_no_relevant():
    qrels = {"doc1": 0}
    ranking = ["doc1"]
    res = calculate_mrr(ranking, qrels, k=10)
    assert res.status == Status.UNDEFINED
    
def test_mrr_unjudged():
    qrels = {"doc1": 1}
    ranking = ["doc2", "doc1"]
    res = calculate_mrr(ranking, qrels, k=10)
    assert res.status == Status.UNDEFINED
    assert res.reason == "unjudged_in_top_k"

def test_pooled_recall():
    qrels = {"doc1": 1, "doc2": 1, "doc3": 0}
    ranking = ["doc1", "doc3"]
    res = calculate_recall(ranking, qrels, k=2)
    assert res.status == Status.ELIGIBLE
    assert res.value == 0.5
    assert res.diagnostics["judged_at_k"] == 2
    assert res.diagnostics["relevant_in_pool"] == 2

def test_document_collapse():
    ranking = [
        {"id": "c1", "doc_id": "d1"},
        {"id": "c2", "doc_id": "d1"},
        {"id": "c3", "doc_id": "d2"}
    ]
    collapsed = collapse_to_documents(ranking)
    assert collapsed == ["d1", "d2"]


def test_execute_evaluation_has_no_pasted_ci_literals():
    text = (IMPL / "scripts" / "execute_evaluation.py").read_text(encoding="utf-8")
    for token in ("0.642", "0.671", "[+0.009, +0.075]"):
        assert token not in text

