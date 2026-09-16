import pytest
import copy
from pathlib import Path
from src.demo.loaders import DemoDataLoader, SecurityError, ArtifactMismatchError, safe_resolve_path

def test_load_all_configured_cases():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    cases = config.get("cases", [])
    assert len(cases) == 5, f"Expected 5 cases, got {len(cases)}"
    
    for case in cases:
        vm = loader.load_view_model(case)
        assert vm.case_id == case["case_id"]
        assert vm.incident_id == case["incident_id"]
        assert vm.condition == case["condition"]
        assert vm.origin == "fixture"
        assert vm.display_mode == "fixture"
        assert vm.observations is not None

def test_case_01_success_citation_link():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    case_01 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_01_success")
    vm = loader.load_view_model(case_01)
    
    assert vm.status == "success"
    assert vm.abstain is False
    assert vm.confidence_label == "high"
    assert len(vm.candidate_causes) == 1
    assert vm.candidate_causes[0]["service_id"] == "redis"
    assert len(vm.supported_claims) == 2
    assert len(vm.evidence_items) == 2
    
    # Evidence 1 should be linked to claim_01
    ev_01 = next(e for e in vm.evidence_items if e.evidence_id == "know_redis_manifest_01")
    assert "claim_01" in ev_01.used_by_claim_ids
    assert ev_01.rank == 1
    assert "redis Kubernetes manifest" in ev_01.actual_context_text

def test_case_03_missing_evidence_abstain():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    case_03 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_03_missing_evidence")
    vm = loader.load_view_model(case_03)
    
    assert vm.status == "abstained"
    assert vm.abstain is True
    assert len(vm.candidate_causes) == 0
    assert len(vm.missing_information) > 0

def test_case_04_invalid_citation():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    case_04 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_04_invalid_citation")
    vm = loader.load_view_model(case_04)
    
    assert vm.status == "invalid_citation"
    assert vm.validation_error is not None
    assert "hallucinated_evidence_external_99" in vm.validation_error

def test_compare_preconditions():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    c1 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_01_success")
    c5 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_05_compare_gb_gh")
    
    vm1 = loader.load_view_model(c1)
    vm5 = loader.load_view_model(c5)
    
    # Preconditions for comparison: same incident_id and same observations_hash
    assert vm1.incident_id == vm5.incident_id
    assert vm1.observations_hash == vm5.observations_hash
    # But different conditions (GH vs GB)
    assert vm1.condition == "GH"
    assert vm5.condition == "GB"

def test_security_path_traversal_rejection():
    loader = DemoDataLoader()
    with pytest.raises(SecurityError):
        loader.load_case_config("../../../../../windows/system32/cmd.exe")

def test_security_outside_allowlist_rejection():
    with pytest.raises(SecurityError):
        safe_resolve_path("C:/Windows/System32/notepad.exe")

def test_hash_mismatch_error():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    case = copy.deepcopy(config["cases"][0])
    # Tamper with the expected manifest hash
    case["manifest_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with pytest.raises(ArtifactMismatchError):
        loader.load_view_model(case)
