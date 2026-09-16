import pytest
from src.generation.context_builder import pack_context
from src.generation.provider import generate_response

def test_context_truncation():
    obs = [{"evidence_id": f"obs_{i}", "text": "test"} for i in range(200)]
    know = [{"evidence_id": f"know_{i}", "text": "test"} for i in range(10)]
    
    a_obs, a_know, h, ledger = pack_context(obs, know)
    assert len(a_obs) == 100
    assert len(a_know) == 5
    assert ledger["observations_truncated"] is True
    assert ledger["knowledge_truncated"] is True

def test_provider_budget_stopped():
    config = {"permissions": {"api": "approved"}, "approved_cap_usd": None}
    raw, meta = generate_response("prompt", {"incident_id": "i1"}, config)
    assert meta["status"] == "budget_stopped"

def test_provider_blocked_permission():
    config = {"permissions": {"api": "pending"}, "approved_cap_usd": 10.0}
    raw, meta = generate_response("prompt", {"incident_id": "i1"}, config)
    assert meta["status"] == "blocked_permission"
