import os
import shutil
import pytest
from pathlib import Path
from src.demo.loaders import DemoDataLoader, ViewModel, EvidenceView, Metadata
from src.demo.app import render_case_page, render_compare_page, export_static_html

def test_render_case_page_three_panels():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    cases = config["cases"]
    c1 = next(c for c in cases if c["case_id"] == "fixture:case_01_success")
    vm = loader.load_view_model(c1)
    
    html = render_case_page(vm, cases)
    
    # Check 3 visual panels exist
    assert 'id="panel-observations"' in html
    assert 'id="panel-evidence"' in html
    assert 'id="panel-claims"' in html
    
    # Check text badge
    assert "DỮ LIỆU MÔ PHỎNG (FIXTURE)" in html
    
    # Check interactive citation button and target evidence ID
    assert 'onclick="highlightEvidence(\'know_redis_manifest_01\')"' in html
    assert 'id="ev-know_redis_manifest_01"' in html
    assert "redis Kubernetes manifest" in html

def test_render_case_03_abstain():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    c3 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_03_missing_evidence")
    vm = loader.load_view_model(c3)
    
    html = render_case_page(vm, config["cases"])
    assert "HỆ THỐNG TỪ CHỐI CHẨN ĐOÁN (ABSTAINED)" in html
    assert "Missing Information" in html
    assert "No domain knowledge or architecture documentation provided" in html

def test_render_case_04_invalid_citation_error():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    c4 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_04_invalid_citation")
    vm = loader.load_view_model(c4)
    
    html = render_case_page(vm, config["cases"])
    assert "LỖI VALIDATOR: INVALID_CITATION" in html
    assert "hallucinated_evidence_external_99" in html

def test_render_compare_page():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    
    html = render_compare_page(config["cases"], loader)
    assert "Đối chiếu điều kiện: BM25 (GB) vs Hybrid (GH)" in html
    assert "col-gb" in html
    assert "col-gh" in html
    assert "BM25 Lexical Retrieval" in html
    assert "Hybrid Retrieval" in html

def test_html_escaping_security():
    loader = DemoDataLoader()
    config = loader.load_case_config("configs/demo-cases.yaml")
    c1 = next(c for c in config["cases"] if c["case_id"] == "fixture:case_01_success")
    vm = loader.load_view_model(c1)
    
    # Inject malicious script in evidence and observation
    vm.evidence_items.append(
        EvidenceView(
            evidence_id="xss_test",
            actual_context_text='<script>alert("XSS")</script>',
            source_kind="doc"
        )
    )
    
    html = render_case_page(vm, config["cases"])
    assert '<script>alert("XSS")</script>' not in html
    assert '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;' in html

def test_export_static_html(tmp_path):
    output_dir = tmp_path / "static_demo"
    export_static_html(output_dir, "configs/demo-cases.yaml")
    
    files = list(output_dir.glob("*.html"))
    assert len(files) == 6  # 5 cases + 1 compare page
    assert (output_dir / "fixture_case_01_success.html").exists()
    assert (output_dir / "compare_gb_gh.html").exists()
