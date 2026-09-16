import os
import sys
import json
import html
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional, List

from src.demo.loaders import DemoDataLoader, ViewModel, EvidenceView, SecurityError, ArtifactMismatchError

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG = "configs/demo-cases.yaml"

def render_badge(text: str, badge_type: str = "primary") -> str:
    escaped = html.escape(text)
    return f'<span class="badge badge-{badge_type}">{escaped}</span>'

def render_header(cases: List[Dict[str, Any]], active_case_id: str, is_compare: bool = False) -> str:
    nav_items = []
    for c in cases:
        cid = c["case_id"]
        order = c.get("display_order", 0)
        label = f"#{order}: {cid.replace('fixture:', '')}"
        active_cls = "active" if cid == active_case_id and not is_compare else ""
        nav_items.append(f'<a href="/?case_id={html.escape(cid)}" class="nav-item {active_cls}">{html.escape(label)}</a>')
        
    compare_active = "active" if is_compare else ""
    nav_items.append(f'<a href="/compare" class="nav-item nav-compare {compare_active}">⚖️ So sánh đối chứng (GB vs GH)</a>')
    
    nav_html = "\n".join(nav_items)
    
    return f"""
    <header class="app-header">
        <div class="header-brand">
            <div class="logo-icon">🔬</div>
            <div>
                <h1>CS221 AIOps RAG — Offline Evidence Demo</h1>
                <p class="subtitle">Hệ thống kiểm chứng liên kết bằng chứng viễn trắc & tri thức cục bộ (Plan 09)</p>
            </div>
        </div>
        <div class="system-disclaimer">
            <span class="badge badge-warning">LƯU Ý NGHIÊN CỨU</span>
            <span>Chạy 100% Offline (Localhost). Chưa có 08.results; các ca gắn nhãn DỮ LIỆU MÔ PHỎNG không dùng làm số liệu thống kê.</span>
        </div>
        <nav class="case-nav">
            {nav_html}
        </nav>
    </header>
    """

def render_observations_panel(vm: ViewModel) -> str:
    obs = vm.observations
    inc_id = html.escape(vm.incident_id)
    sys_id = html.escape(str(obs.get("system_id", "online_boutique")))
    t_start = html.escape(str(obs.get("observation_start", "N/A")))
    t_end = html.escape(str(obs.get("observation_end_exclusive", "N/A")))
    
    metrics = obs.get("metric_summary_ids", [])
    logs = obs.get("log_span_ids", [])
    traces = obs.get("trace_span_ids", [])
    
    metrics_rows = []
    for m in metrics[:10]:
        parts = m.split(":metric:")
        name = parts[-1] if len(parts) > 1 else m
        metrics_rows.append(f'<li class="telemetry-item metric-item">📊 {html.escape(name)}</li>')
    if len(metrics) > 10:
        metrics_rows.append(f'<li class="telemetry-item more-item">... và {len(metrics) - 10} metrics khác</li>')
        
    log_rows = []
    for l in logs[:6]:
        parts = l.split(":log:")
        lid = parts[-1] if len(parts) > 1 else l
        log_rows.append(f'<li class="telemetry-item log-item">📜 span_id: {html.escape(lid)}</li>')
    if len(logs) > 6:
        log_rows.append(f'<li class="telemetry-item more-item">... và {len(logs) - 6} log spans khác</li>')

    trace_rows = []
    for t in traces[:6]:
        parts = t.split(":trace:")
        tid = parts[-1] if len(parts) > 1 else t
        trace_rows.append(f'<li class="telemetry-item trace-item">🔗 trace_id: {html.escape(tid)}</li>')
    if len(traces) > 6:
        trace_rows.append(f'<li class="telemetry-item more-item">... và {len(traces) - 6} trace spans khác</li>')

    return f"""
    <section class="panel panel-left" id="panel-observations">
        <div class="panel-header">
            <h2>1. Incident & Viễn trắc (Observations)</h2>
            <span class="count-badge">{len(metrics)} metrics | {len(logs)} logs</span>
        </div>
        <div class="panel-body">
            <div class="card meta-card">
                <div class="meta-row"><strong>Incident ID:</strong> <code>{inc_id}</code></div>
                <div class="meta-row"><strong>Hệ thống:</strong> <span>{sys_id}</span></div>
                <div class="meta-row"><strong>Khoảng thời gian:</strong> <span class="time-range">{t_start} → {t_end}</span></div>
                <div class="meta-row"><strong>Hash viễn trắc:</strong> <code class="hash-code">{html.escape(vm.observations_hash[:16])}...</code></div>
            </div>
            
            <div class="section-block">
                <h3>Các chỉ số bất thường (Metrics Telemetry)</h3>
                <ul class="telemetry-list">
                    {"".join(metrics_rows) if metrics_rows else '<li class="empty-hint">Không có metric bất thường</li>'}
                </ul>
            </div>
            
            <div class="section-block">
                <h3>Log Spans ghi nhận</h3>
                <ul class="telemetry-list">
                    {"".join(log_rows) if log_rows else '<li class="empty-hint">Không có log span</li>'}
                </ul>
            </div>

            <div class="section-block">
                <h3>Trace Spans viễn trắc</h3>
                <ul class="telemetry-list">
                    {"".join(trace_rows) if trace_rows else '<li class="empty-hint">Không có trace span</li>'}
                </ul>
            </div>
        </div>
    </section>
    """

def render_evidence_panel(vm: ViewModel) -> str:
    evidence_cards = []
    if not vm.evidence_items:
        evidence_cards.append("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <p><strong>Không có đoạn tri thức nào được gửi (Condition G0 / No-RAG).</strong></p>
            <p class="subtext">Mô hình chỉ dựa vào triệu chứng viễn trắc thô hoặc chủ động từ chối chẩn đoán (abstain).</p>
        </div>
        """)
    else:
        for ev in vm.evidence_items:
            eid = html.escape(ev.evidence_id)
            rank_str = f"#{ev.rank}" if ev.rank is not None else "N/A"
            doc_id = html.escape(ev.document_id or "unknown")
            chunk_id = html.escape(ev.chunk_id or "unknown")
            rev = html.escape(ev.source_revision[:12] if ev.source_revision else "unknown")
            text_content = html.escape(ev.actual_context_text)
            
            claims_tag = ""
            if ev.used_by_claim_ids:
                claim_links = [f'<span class="claim-tag">➡️ {html.escape(c)}</span>' for c in ev.used_by_claim_ids]
                claims_tag = f'<div class="evidence-usage">Sử dụng bởi: {" ".join(claim_links)}</div>'
                
            card_html = f"""
            <div class="card evidence-card" id="ev-{eid}" data-evidence-id="{eid}">
                <div class="evidence-header">
                    <div class="rank-pill">Rank {rank_str}</div>
                    <div class="evidence-id"><code>{eid}</code></div>
                    <div class="evidence-kind badge badge-info">{html.escape(ev.source_kind)}</div>
                </div>
                <div class="evidence-provenance">
                    <span>Doc: <code>{doc_id}</code></span>
                    <span>Chunk: <code>{chunk_id}</code></span>
                    <span>Rev: <code>{rev}</code></span>
                    <span>Offsets: <code>{html.escape(ev.offsets)}</code></span>
                </div>
                <div class="evidence-text">
                    <div class="text-label">Đoạn text gửi generator (Actual Context):</div>
                    <pre class="code-snippet"><code>{text_content}</code></pre>
                </div>
                {claims_tag}
            </div>
            """
            evidence_cards.append(card_html)

    return f"""
    <section class="panel panel-center" id="panel-evidence">
        <div class="panel-header">
            <h2>2. Tri thức truy xuất (Retrieved Evidence)</h2>
            <span class="count-badge">{len(vm.evidence_items)} chunks</span>
        </div>
        <div class="panel-body">
            <div class="panel-info-note">
                <small>💡 <strong>Exact Context Guarantee:</strong> Dưới đây là chính xác các đoạn text và offsets được trích lọc gửi vào context prompt của mô hình, kèm hash xác thực.</small>
            </div>
            {"".join(evidence_cards)}
        </div>
    </section>
    """

def render_claims_panel(vm: ViewModel) -> str:
    # Origin & Mode badge
    origin_badge = '<span class="badge badge-fixture">DỮ LIỆU MÔ PHỎNG (FIXTURE)</span>' if vm.origin == "fixture" else '<span class="badge badge-replay">PHÁT LẠI KẾT QUẢ ĐÃ LƯU (REPLAY)</span>'
    cond_badge = f'<span class="badge badge-condition">Condition: {html.escape(vm.condition)}</span>'
    
    # Status banner
    status_banner = ""
    if vm.status == "invalid_citation":
        status_banner = f"""
        <div class="alert alert-danger">
            <strong>❌ LỖI VALIDATOR: INVALID_CITATION</strong>
            <p>{html.escape(vm.validation_error or 'Trích dẫn không hợp lệ hoặc không có trong actual_context_ids.')}</p>
        </div>
        """
    elif vm.status == "weak_diagnosis":
        status_banner = f"""
        <div class="alert alert-warning">
            <strong>⚠️ CHẨN ĐOÁN YẾU (WEAK DIAGNOSIS)</strong>
            <p>{html.escape(vm.validation_error or 'Truy xuất không cung cấp đủ căn cứ chi tiết; độ tin cậy thấp.')}</p>
        </div>
        """
    elif vm.status == "abstained":
        status_banner = f"""
        <div class="alert alert-info">
            <strong>🛑 HỆ THỐNG TỪ CHỐI CHẨN ĐOÁN (ABSTAINED)</strong>
            <p>Mô hình chủ động từ chối kết luận do thiếu bằng chứng kiến trúc cần thiết thay vì suy đoán.</p>
        </div>
        """
    elif vm.status == "success":
        status_banner = f"""
        <div class="alert alert-success">
            <strong>✅ CHẨN ĐOÁN HỢP LỆ & CÓ BẰNG CHỨNG (GROUNDED)</strong>
            <p>Mọi tuyên bố (claims) đều có liên kết chính xác tới actual context đã được xác thực.</p>
        </div>
        """

    # Causes
    causes_html = []
    for c in vm.candidate_causes:
        causes_html.append(f"""
        <div class="cause-card">
            <div class="cause-title"><strong>Service:</strong> <code>{html.escape(c.get('service_id', 'unknown'))}</code> — <em>{html.escape(c.get('fault_type', ''))}</em></div>
            <div class="cause-reason">{html.escape(c.get('reason', ''))}</div>
        </div>
        """)

    # Supported claims with clickable citations
    claims_html = []
    for cl in vm.supported_claims:
        cid = html.escape(cl.get("claim_id", ""))
        ctype = html.escape(cl.get("type", "observation"))
        text = html.escape(cl.get("text", ""))
        eids = cl.get("evidence_ids", [])
        
        cit_buttons = []
        for eid in eids:
            e_esc = html.escape(eid)
            cit_buttons.append(f'<button type="button" class="cit-btn" onclick="highlightEvidence(\'{e_esc}\')">📎 [{e_esc}]</button>')
            
        cit_group = f'<div class="claim-citations"><strong>Bằng chứng:</strong> {" ".join(cit_buttons)}</div>' if cit_buttons else '<div class="claim-citations empty">Không có citation</div>'

        claims_html.append(f"""
        <div class="claim-card" id="claim-{cid}">
            <div class="claim-header">
                <span class="claim-id"><code>{cid}</code></span>
                <span class="badge badge-type badge-{ctype}">{ctype}</span>
            </div>
            <div class="claim-text">{text}</div>
            {cit_group}
        </div>
        """)

    # Missing info & next checks
    missing_items = [f'<li>{html.escape(m)}</li>' for m in vm.missing_information]
    next_items = [f'<li>{html.escape(n)}</li>' for n in vm.next_checks]
    
    # Raw response modal or collapsible
    raw_snippet = html.escape(vm.raw_response)

    return f"""
    <section class="panel panel-right" id="panel-claims">
        <div class="panel-header">
            <h2>3. Chẩn đoán & Claims (Model Output)</h2>
            <div class="header-badges">{origin_badge} {cond_badge}</div>
        </div>
        <div class="panel-body">
            {status_banner}
            
            <div class="card decision-summary">
                <div class="meta-row"><strong>Độ tin cậy:</strong> <span class="conf-badge conf-{html.escape(vm.confidence_label)}">{html.escape(vm.confidence_label.upper())}</span></div>
                <div class="meta-row"><strong>Trạng thái Abstain:</strong> <span>{'CÓ (Từ chối)' if vm.abstain else 'KHÔNG'}</span></div>
                <div class="meta-row"><strong>Lý do chọn case:</strong> <em>{html.escape(vm.selection_reason)}</em></div>
            </div>

            <div class="section-block">
                <h3>Nguyên nhân đề xuất (Candidate Causes)</h3>
                {"".join(causes_html) if causes_html else '<p class="empty-hint">Không có nguyên nhân đề xuất (do Abstain hoặc Lỗi).</p>'}
            </div>

            <div class="section-block">
                <h3>Tuyên bố có kiểm chứng (Supported Claims & Citations)</h3>
                <div class="claims-note"><small>👉 Nhấp vào mã trích dẫn <code>[evidence_id]</code> để highlight đoạn context tương ứng ở Cột 2.</small></div>
                {"".join(claims_html) if claims_html else '<p class="empty-hint">Không có claims.</p>'}
            </div>

            <div class="section-block">
                <h3>Thông tin còn thiếu (Missing Information)</h3>
                <ul class="info-list">
                    {"".join(missing_items) if missing_items else '<li>Không có ghi chú thông tin thiếu</li>'}
                </ul>
            </div>

            <div class="section-block">
                <h3>Đề xuất kiểm tra tiếp theo (Next Checks)</h3>
                <ul class="info-list">
                    {"".join(next_items) if next_items else '<li>Không có đề xuất thêm</li>'}
                </ul>
            </div>

            <div class="section-block raw-block">
                <details>
                    <summary>🔍 Xem Raw Output của Mô hình</summary>
                    <pre class="raw-code"><code>{raw_snippet}</code></pre>
                </details>
            </div>
        </div>
    </section>
    """

def render_compare_page(cases: List[Dict[str, Any]], loader: DemoDataLoader) -> str:
    # Compare fixture:case_05_compare_gb_gh (GB) with fixture:case_01_success (GH)
    c_gb = next((c for c in cases if c["case_id"] == "fixture:case_05_compare_gb_gh"), None)
    c_gh = next((c for c in cases if c["case_id"] == "fixture:case_01_success"), None)
    
    if not c_gb or not c_gh:
        return "<p>Lỗi: Không tìm thấy ca đối chứng để so sánh.</p>"
        
    vm_gb = loader.load_view_model(c_gb)
    vm_gh = loader.load_view_model(c_gh)
    
    # Verify compare preconditions
    mismatch_warning = ""
    if vm_gb.incident_id != vm_gh.incident_id or vm_gb.observations_hash != vm_gh.observations_hash:
        mismatch_warning = """
        <div class="alert alert-danger">
            <strong>❌ CẢNH BÁO: SAI LỆCH TIỀN ĐIỀU KIỆN SO SÁNH!</strong>
            Hai case không có cùng incident_id hoặc cùng hash viễn trắc. Kết quả so sánh bị vô hiệu hóa.
        </div>
        """
        
    header_html = render_header(cases, "", is_compare=True)
    
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="utf-8">
        <title>So sánh đối chứng BM25 vs Hybrid — CS221 Demo</title>
        <style>{get_styles()}</style>
    </head>
    <body>
        {header_html}
        <main class="compare-container">
            <div class="compare-intro">
                <h2>Đối chiếu điều kiện: BM25 (GB) vs Hybrid (GH)</h2>
                <p>Cùng một incident viễn trắc (<code>{html.escape(vm_gb.incident_id)}</code>) với cùng observation hash (<code>{html.escape(vm_gb.observations_hash[:16])}...</code>).</p>
                {mismatch_warning}
            </div>
            
            <div class="compare-grid">
                <div class="compare-col col-gb">
                    <div class="compare-col-header">
                        <h3>Điều kiện GB: BM25 Lexical Retrieval</h3>
                        <span class="badge badge-warning">Baseline</span>
                    </div>
                    <div class="compare-content">
                        <h4>Tri thức truy xuất (Evidence Context):</h4>
                        <div class="ev-mini-list">
                            {render_mini_evidence(vm_gb)}
                        </div>
                        <h4>Chẩn đoán & Tuyên bố:</h4>
                        <div class="diag-summary">
                            <p><strong>Causes:</strong> {html.escape(vm_gb.candidate_causes[0]['fault_type']) if vm_gb.candidate_causes else 'None'}</p>
                            <p><strong>Confidence:</strong> <span class="conf-badge conf-{vm_gb.confidence_label}">{html.escape(vm_gb.confidence_label.upper())}</span></p>
                            <p><strong>Claims:</strong> {len(vm_gb.supported_claims)} claims (Tài liệu tổng quan, thiếu chi tiết resource limits)</p>
                        </div>
                    </div>
                </div>

                <div class="compare-col col-gh">
                    <div class="compare-col-header">
                        <h3>Điều kiện GH: Hybrid Retrieval (BM25 + Dense)</h3>
                        <span class="badge badge-success">Candidate GH</span>
                    </div>
                    <div class="compare-content">
                        <h4>Tri thức truy xuất (Evidence Context):</h4>
                        <div class="ev-mini-list">
                            {render_mini_evidence(vm_gh)}
                        </div>
                        <h4>Chẩn đoán & Tuyên bố:</h4>
                        <div class="diag-summary">
                            <p><strong>Causes:</strong> {html.escape(vm_gh.candidate_causes[0]['fault_type']) if vm_gh.candidate_causes else 'None'}</p>
                            <p><strong>Confidence:</strong> <span class="conf-badge conf-{vm_gh.confidence_label}">{html.escape(vm_gh.confidence_label.upper())}</span></p>
                            <p><strong>Claims:</strong> {len(vm_gh.supported_claims)} claims (Truy xuất đúng manifest và IO tuning ở Rank 1 & 2)</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        <script>{get_scripts()}</script>
    </body>
    </html>
    """

def render_mini_evidence(vm: ViewModel) -> str:
    rows = []
    for ev in vm.evidence_items:
        rows.append(f"""
        <div class="mini-ev-card">
            <div class="mini-ev-header">
                <strong>Rank #{ev.rank or 1}:</strong> <code>{html.escape(ev.evidence_id)}</code>
            </div>
            <pre class="mini-ev-text"><code>{html.escape(ev.actual_context_text[:160])}...</code></pre>
        </div>
        """)
    return "".join(rows)

def render_case_page(vm: ViewModel, cases: List[Dict[str, Any]]) -> str:
    header_html = render_header(cases, vm.case_id, is_compare=False)
    panel_obs = render_observations_panel(vm)
    panel_ev = render_evidence_panel(vm)
    panel_claims = render_claims_panel(vm)
    
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Offline Evidence Demo — {html.escape(vm.case_id)}</title>
        <style>{get_styles()}</style>
    </head>
    <body>
        {header_html}
        <main class="three-panel-layout">
            {panel_obs}
            {panel_ev}
            {panel_claims}
        </main>
        <footer class="app-footer">
            <span>CS221 AIOps RAG Research Pack • Plan 09 Offline Demo • Port: Localhost</span>
            <span>Phím tắt: [1] Case trước • [2] Case sau • [C] So sánh đối chứng</span>
        </footer>
        <script>{get_scripts()}</script>
    </body>
    </html>
    """

def get_styles() -> str:
    return """
    :root {
        --bg-color: #0f172a;
        --panel-bg: #1e293b;
        --card-bg: #334155;
        --border-color: #475569;
        --text-color: #f1f5f9;
        --text-muted: #94a3b8;
        --accent-blue: #38bdf8;
        --accent-green: #4ade80;
        --accent-yellow: #facc15;
        --accent-red: #f87171;
        --highlight-bg: #854d0e;
        --highlight-border: #facc15;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        line-height: 1.5;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    /* Header */
    .app-header {
        background-color: var(--panel-bg);
        border-bottom: 2px solid var(--border-color);
        padding: 12px 24px;
    }
    .header-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .logo-icon { font-size: 28px; }
    .app-header h1 { font-size: 1.3rem; font-weight: 700; color: var(--accent-blue); }
    .subtitle { font-size: 0.85rem; color: var(--text-muted); }
    
    .system-disclaimer {
        display: flex;
        align-items: center;
        gap: 8px;
        background-color: rgba(250, 204, 21, 0.1);
        border-left: 4px solid var(--accent-yellow);
        padding: 6px 12px;
        margin-bottom: 12px;
        font-size: 0.85rem;
    }

    /* Nav */
    .case-nav {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .nav-item {
        color: var(--text-color);
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 6px;
        background-color: var(--card-bg);
        font-size: 0.85rem;
        transition: all 0.15s ease;
    }
    .nav-item:hover { background-color: var(--border-color); }
    .nav-item.active {
        background-color: var(--accent-blue);
        color: #0f172a;
        font-weight: 600;
    }
    .nav-compare { background-color: #4338ca; }
    .nav-compare.active { background-color: #6366f1; color: #fff; }

    /* Layout */
    .three-panel-layout {
        display: grid;
        grid-template-columns: 1fr 1.25fr 1.15fr;
        gap: 16px;
        padding: 16px;
        flex: 1;
        overflow: hidden;
    }
    @media (max-width: 1200px) {
        .three-panel-layout { grid-template-columns: 1fr; overflow: auto; }
    }

    .panel {
        background-color: var(--panel-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .panel-header {
        padding: 12px 16px;
        background-color: rgba(0,0,0,0.2);
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .panel-header h2 { font-size: 1.05rem; font-weight: 600; }
    .count-badge { font-size: 0.75rem; background: var(--card-bg); padding: 2px 8px; border-radius: 12px; }
    .panel-body { padding: 16px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 16px; }

    /* Cards */
    .card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 12px;
    }
    .meta-row { margin-bottom: 6px; font-size: 0.85rem; }
    .meta-row:last-child { margin-bottom: 0; }
    .hash-code { font-family: monospace; font-size: 0.8rem; color: var(--accent-yellow); }
    .time-range { font-size: 0.8rem; color: var(--text-muted); }

    /* Telemetry */
    .telemetry-list { list-style: none; display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem; }
    .telemetry-item { background: rgba(0,0,0,0.15); padding: 4px 8px; border-radius: 4px; }
    .more-item { color: var(--text-muted); font-style: italic; }

    /* Evidence Items */
    .evidence-card {
        transition: all 0.2s ease;
        border-left: 4px solid var(--accent-blue);
    }
    .evidence-card.highlighted {
        background-color: var(--highlight-bg) !important;
        border-color: var(--highlight-border) !important;
        box-shadow: 0 0 12px rgba(250, 204, 21, 0.5);
        transform: scale(1.01);
    }
    .evidence-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .rank-pill { background: var(--accent-blue); color: #000; font-weight: 700; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; }
    .evidence-provenance { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
    .text-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px; }
    .code-snippet { background: #0b0f19; padding: 10px; border-radius: 4px; font-size: 0.8rem; overflow-x: auto; white-space: pre-wrap; }

    /* Claims */
    .cause-card { background: #1e1e38; border-left: 4px solid var(--accent-green); padding: 10px; border-radius: 4px; margin-bottom: 8px; }
    .cause-title { font-size: 0.9rem; margin-bottom: 4px; }
    .cause-reason { font-size: 0.85rem; color: var(--text-muted); }

    .claim-card { background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; margin-bottom: 8px; }
    .claim-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .claim-text { font-size: 0.9rem; margin-bottom: 8px; }
    .cit-btn {
        background: #0284c7; color: white; border: none; padding: 4px 8px; border-radius: 4px;
        font-size: 0.75rem; cursor: pointer; font-family: monospace; font-weight: bold;
    }
    .cit-btn:hover { background: #0ea5e9; }
    .claim-citations.empty { font-size: 0.75rem; color: var(--accent-red); }

    /* Badges & Alerts */
    .badge { font-size: 0.75rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
    .badge-fixture { background-color: #854d0e; color: #fef08a; }
    .badge-replay { background-color: #065f46; color: #a7f3d0; }
    .badge-condition { background-color: #3730a3; color: #e0e7ff; }
    .badge-warning { background-color: var(--accent-yellow); color: #000; }
    .badge-info { background-color: var(--accent-blue); color: #000; }

    .alert { padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 12px; }
    .alert-success { background: rgba(74, 222, 128, 0.15); border-left: 4px solid var(--accent-green); }
    .alert-warning { background: rgba(250, 204, 21, 0.15); border-left: 4px solid var(--accent-yellow); }
    .alert-danger { background: rgba(248, 113, 113, 0.15); border-left: 4px solid var(--accent-red); }
    .alert-info { background: rgba(56, 189, 248, 0.15); border-left: 4px solid var(--accent-blue); }

    .conf-badge { padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; }
    .conf-high { background: var(--accent-green); color: #000; }
    .conf-medium { background: var(--accent-yellow); color: #000; }
    .conf-low { background: var(--accent-red); color: #fff; }
    .conf-abstain { background: #64748b; color: #fff; }

    /* Compare */
    .compare-container { padding: 24px; max-width: 1400px; margin: 0 auto; flex: 1; }
    .compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 16px; }
    .compare-col { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; }
    .compare-col-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-bottom: 16px; }
    .mini-ev-card { background: var(--card-bg); padding: 8px; border-radius: 4px; margin-bottom: 8px; font-size: 0.8rem; }
    .mini-ev-text { font-size: 0.75rem; white-space: pre-wrap; }

    /* Footer */
    .app-footer { background: var(--panel-bg); border-top: 1px solid var(--border-color); padding: 8px 24px; font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between; }
    
    .empty-hint { color: var(--text-muted); font-style: italic; font-size: 0.85rem; }
    .raw-code { background: #050811; padding: 10px; border-radius: 4px; font-size: 0.75rem; max-height: 200px; overflow-y: auto; }
    """

def get_scripts() -> str:
    return """
    function highlightEvidence(evidenceId) {
        // Remove previous highlight
        document.querySelectorAll('.evidence-card').forEach(card => {
            card.classList.remove('highlighted');
        });
        
        const target = document.getElementById('ev-' + evidenceId);
        if (target) {
            target.classList.add('highlighted');
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            alert('Trích dẫn [' + evidenceId + '] không tồn tại trong danh sách bằng chứng thực tế!');
        }
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'c' || e.key === 'C') {
            window.location.href = '/compare';
        }
    });
    """

class DemoRequestHandler(BaseHTTPRequestHandler):
    loader: DemoDataLoader = None
    config_path: str = DEFAULT_CONFIG

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            config = self.loader.load_case_config(self.config_path)
            cases = config.get("cases", [])
            
            if path == "/compare":
                html_body = render_compare_page(cases, self.loader)
                self._respond_html(html_body)
                return
                
            case_id = query.get("case_id", [cases[0]["case_id"] if cases else ""])[0]
            selected_case = next((c for c in cases if c["case_id"] == case_id), cases[0] if cases else None)
            
            if not selected_case:
                self._respond_error(404, "Không tìm thấy case yêu cầu.")
                return

            vm = self.loader.load_view_model(selected_case)
            html_body = render_case_page(vm, cases)
            self._respond_html(html_body)
            
        except SecurityError as e:
            self._respond_error(403, f"Lỗi bảo mật: {str(e)}")
        except ArtifactMismatchError as e:
            self._respond_error(500, f"Lỗi toàn vẹn dữ liệu (Artifact Mismatch): {str(e)}")
        except Exception as e:
            self._respond_error(500, f"Lỗi nội bộ server: {str(e)}")

    def _respond_html(self, content: str, status_code: int = 200):
        data = content.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _respond_error(self, status_code: int, message: str):
        escaped_msg = html.escape(message)
        body = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head><meta charset="utf-8"><title>Lỗi Demo</title><style>{get_styles()}</style></head>
        <body style="padding: 40px;">
            <div class="alert alert-danger">
                <h2>Lỗi {status_code}</h2>
                <p>{escaped_msg}</p>
                <p><a href="/" style="color: #fff;">Quay về trang chủ</a></p>
            </div>
        </body>
        </html>
        """
        self._respond_html(body, status_code)

    def log_message(self, format, *args):
        # Mute normal HTTP logs during automated runs unless needed
        pass

def run_server(host: str = "127.0.0.1", port: int = 8080, config_path: str = DEFAULT_CONFIG):
    loader = DemoDataLoader()
    DemoRequestHandler.loader = loader
    DemoRequestHandler.config_path = config_path
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, DemoRequestHandler)
    print(f"CS221 Evidence Demo Server running at http://{host}:{port}/")
    print("Press Ctrl+C to stop server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server...")
        httpd.server_close()

def export_static_html(output_dir: Path, config_path: str = DEFAULT_CONFIG):
    """Xuất tĩnh toàn bộ các trang demo sang HTML để phục vụ backup offline."""
    loader = DemoDataLoader()
    config = loader.load_case_config(config_path)
    cases = config.get("cases", [])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for c in cases:
        vm = loader.load_view_model(c)
        page_html = render_case_page(vm, cases)
        cid_clean = c["case_id"].replace(":", "_")
        target_file = output_dir / f"{cid_clean}.html"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(page_html)
            
    # Export compare page
    compare_html = render_compare_page(cases, loader)
    with open(output_dir / "compare_gb_gh.html", "w", encoding="utf-8") as f:
        f.write(compare_html)
        
    print(f"Static HTML export completed successfully to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="CS221 Offline Evidence Demo Server")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ host (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Cổng lắng nghe (mặc định: 8080)")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Đường dẫn file cấu hình cases")
    parser.add_argument("--export-static", type=str, default=None, help="Xuất các trang HTML tĩnh ra thư mục chỉ định")
    
    args = parser.parse_args()
    
    if args.export_static:
        export_static_html(Path(args.export_static), args.config)
    else:
        run_server(args.host, args.port, args.config)

if __name__ == "__main__":
    main()
