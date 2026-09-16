import pytest
from src.generation.validator import validate_response

def test_valid_response():
    raw = '{"incident_id": "test", "candidate_causes": [], "supported_claims": [{"claim_id": "c1", "text": "test", "type": "observation", "evidence_ids": ["obs1"]}], "missing_information": [], "next_checks": [], "abstain": false, "confidence_label": "high"}'
    actual_ids = ["obs1"]
    payload, status, err = validate_response(raw, actual_ids)
    assert status == "success"
    assert payload is not None

def test_invalid_citation():
    raw = '{"incident_id": "test", "candidate_causes": [], "supported_claims": [{"claim_id": "c1", "text": "test", "type": "observation", "evidence_ids": ["obs2"]}], "missing_information": [], "next_checks": [], "abstain": false, "confidence_label": "high"}'
    actual_ids = ["obs1"]
    payload, status, err = validate_response(raw, actual_ids)
    assert status == "invalid_citation"
    assert "not found in actual context" in err

def test_invalid_json():
    raw = '{"incident_id": "test", "candidate_causes": [],'
    actual_ids = ["obs1"]
    payload, status, err = validate_response(raw, actual_ids)
    assert status == "invalid_response"
    assert "JSON parse error" in err
