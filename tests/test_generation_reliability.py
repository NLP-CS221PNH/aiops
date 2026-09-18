from pathlib import Path

import pytest

from src.generation.context_builder import pack_context
from src.generation.prompt_builder import build_messages, request_fingerprint
from src.generation.provider import generate_response
from src.generation.runner import run_generation
from src.generation.validator import validate_response


def test_context_truncation():
    obs = [{"evidence_id": f"obs_{i}", "text": "test"} for i in range(200)]
    know = [{"evidence_id": f"know_{i}", "text": "test"} for i in range(10)]

    a_obs, a_know, h, ledger = pack_context(obs, know)
    assert len(a_obs) == 100
    assert len(a_know) == 5
    assert ledger["observations_truncated"] is True
    assert ledger["knowledge_truncated"] is True


def test_token_budget_keeps_target_and_drops_tail():
    obs = [{"evidence_id": f"obs_{i}", "text": "alpha " * 20} for i in range(8)]
    know = [{"evidence_id": f"know_{i}", "chunk_id": f"know_{i}", "text": "beta " * 20} for i in range(4)]
    a_obs, a_know, _hash, ledger = pack_context(obs, know, obs_budget=40, know_budget=40)
    assert a_obs[0]["evidence_id"] == "obs_0"
    assert ledger["observations_truncated"] is True
    assert ledger["dropped_observation_ids"]
    assert a_know[0]["evidence_id"] == "know_0"


def test_same_ids_different_text_change_hash():
    obs_a = [{"evidence_id": "obs_1", "text": "checkout latency rising"}]
    obs_b = [{"evidence_id": "obs_1", "text": "cart timeout rising"}]
    know = [{"evidence_id": "k1", "chunk_id": "k1", "text": "same chunk"}]
    _, _, hash_a, _ = pack_context(obs_a, know)
    _, _, hash_b, _ = pack_context(obs_b, know)
    assert hash_a != hash_b


def test_prompt_contains_observation_and_chunk_text():
    messages = build_messages(
        "cartservice cpu 99 percent",
        [{"evidence_id": "chunk-9", "text": "cartservice readiness probe failed"}],
        condition="GH",
    )
    user = messages[1]["content"]
    assert "cartservice cpu 99 percent" in user
    assert "[chunk-9] cartservice readiness probe failed" in user


def test_g0_omits_knowledge_chunks():
    messages = build_messages(
        "same observations",
        [{"evidence_id": "chunk-9", "text": "must not appear in G0"}],
        condition="G0",
    )
    assert "must not appear in G0" not in messages[1]["content"]


def test_provider_budget_stopped():
    config = {"permissions": {"api": "approved"}, "approved_cap_usd": None}
    raw, meta = generate_response("prompt", {"incident_id": "i1"}, config)
    assert meta["status"] == "budget_stopped"
    assert meta.get("usage") is None


def test_provider_blocked_permission():
    config = {"permissions": {"api": "pending"}, "approved_cap_usd": 10.0}
    raw, meta = generate_response("prompt", {"incident_id": "i1"}, config)
    assert meta["status"] == "blocked_permission"


def test_api_approved_without_local_is_remote_disabled_not_mock():
    config = {
        "permissions": {"api": "approved", "local": "pending"},
        "approved_cap_usd": 10,
        "provider": {"model": "deepseek-flash"},
    }
    raw, meta = generate_response("prompt", {"incident_id": "i1"}, config)
    assert meta["status"] == "remote_api_disabled"
    assert "svc_a" not in raw
    assert meta.get("usage") is None


def test_wrong_incident_is_invalid():
    raw = '{"incident_id": "other", "candidate_causes": [{"service_id": "cartservice"}]}'
    payload, status, err = validate_response(raw, [], "inc-1")
    assert status == "invalid_incident"
    assert payload is None


def test_empty_service_id_is_invalid():
    raw = '{"candidate_causes": [{"service_id": "   "}]}'
    payload, status, err = validate_response(raw, [], "inc-1")
    assert status == "invalid_response"


def test_fingerprint_changes_with_context(tmp_path: Path):
    first = request_fingerprint(
        [{"role": "user", "content": "a"}],
        incident_id="i1", condition="G0", context_hash="h1",
        config_hash="c1", adapter_hash=None, tokenizer_hash="t", model_revision="r",
    )
    second = request_fingerprint(
        [{"role": "user", "content": "a"}],
        incident_id="i1", condition="G0", context_hash="h2",
        config_hash="c1", adapter_hash=None, tokenizer_hash="t", model_revision="r",
    )
    assert first != second


def test_freeze_and_input_manifest_are_enforced(tmp_path: Path):
    config = tmp_path / "generation.yaml"
    config.write_text(
        "permissions:\n  local: approved\nprovider:\n  model: deepseek-flash\n",
        encoding="utf-8",
    )
    freeze = tmp_path / "freeze.json"
    freeze.write_text('{"config_hash": "deadbeef"}', encoding="utf-8")
    with pytest.raises(SystemExit, match="freeze_config_mismatch"):
        run_generation("run-x", ["inc-1"], str(config), freeze_path=str(freeze))
    manifest = tmp_path / "input-manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="input_manifest_requires_freeze"):
        run_generation("run-y", ["inc-1"], str(config), input_manifest=str(manifest))
