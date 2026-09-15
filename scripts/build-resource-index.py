"""Build a standalone local resource browser from collected records; no external assets."""
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def jl(name):
    p = ROOT / name
    return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()] if p.exists() else []


def obj(name):
    p = ROOT / name
    return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}


papers = jl('01_papers/enriched/catalog-enriched.jsonl') or jl('01_papers/catalog.jsonl')
compact = []
for p in papers:
    entry = {k: p.get(k) for k in ['paper_id', 'title', 'authors', 'venue', 'publication_year', 'canonical_url', 'verification_status', 'topic_vi', 'topic_code', 'metadata_source_url', 'enrichment_status', 'metadata_status', 'full_text_read']}
    research = p.get('research', {})
    meta = research.get('publication_metadata') or research.get('metadata') or {}
    if research.get('identity_status') == 'matched':
        for k in ['authors', 'venue', 'publication_year', 'metadata_source_url']:
            entry[k] = meta.get(k) or entry.get(k)
    if p.get('reference_title'):
        entry['title'] = p['reference_title']
    if p.get('reference_year'):
        entry['publication_year'] = p['reference_year']
    if p.get('publication_doi'):
        entry['canonical_url'] = 'https://doi.org/' + p['publication_doi']
    entry['metadata_status'] = research.get('identity_status') or research.get('acquisition_status')
    entry['year_basis'] = meta.get('year_basis')
    entry['read_depth'] = research.get('read_depth')
    candidates = sorted((ROOT / '01_papers/reading-notes').glob(p['paper_id'] + '*.md'))
    entry['note_path'] = candidates[0].relative_to(ROOT).as_posix() if candidates else None
    compact.append(entry)
payload = {
    'builtAt': datetime.now(timezone.utc).isoformat(),
    'papers': compact,
    'observations': jl('02_datasets/processed/observations.jsonl'),
    'logs': jl('02_datasets/processed/logs-evidence.jsonl'),
    'documents': jl('03_collection_plan/knowledge-corpus/documents.jsonl'),
    'historicalDocuments': jl('03_collection_plan/knowledge-corpus-historical/documents.jsonl'),
    'datasetProfile': obj('02_datasets/processed/profile-summary.json'),
    'knowledgeSnapshot': obj('03_collection_plan/knowledge-corpus/snapshot.json'),
    'validation': obj('04_audit/research-pack-validation.json'),
}
data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
html = r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CS221 · Tài nguyên nghiên cứu AIOps và Hybrid RAG</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#202020;background:#fafafa;line-height:1.6}*{box-sizing:border-box}body{max-width:1320px;margin:0 auto;padding:38px 30px}h1{font-size:30px;line-height:1.3;font-weight:650;margin:0 0 15px}h2{font-size:22px;margin-top:32px}h3{font-size:18px}p{max-width:950px}a{color:#204d77;text-underline-offset:3px}nav{display:flex;gap:8px;border-bottom:1px solid #bbb;margin:26px 0 20px;flex-wrap:wrap}button{font:inherit;color:inherit;background:#fff;border:1px solid #bbb;padding:9px 16px;cursor:pointer}nav button{border:0;border-bottom:3px solid transparent}nav button[aria-selected=true]{border-color:#202020;font-weight:650}input{font:inherit;width:100%;padding:11px 12px;border:1px solid #aaa;background:white;margin:8px 0 18px}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;vertical-align:top;padding:10px 13px;border-bottom:1px solid #dedede;font-size:14px}th{background:#f0f0f0;font-weight:650}tbody tr:nth-child(even){background:#fcfcfc}small,.muted{color:#666}code{font-size:12px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,Consolas,monospace;background:#f3f3f3;padding:16px;border:1px solid #ddd}details{margin:7px 0}summary{cursor:pointer}section[hidden]{display:none}.scroll{overflow:auto}.stats{font-size:18px;border-top:1px solid #bbb;border-bottom:1px solid #bbb;padding:18px 0}.tag{font-size:12px;color:#555}.notice{border-left:3px solid #777;padding-left:18px}.links{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px 26px}.links a{display:block;padding:8px 0;border-bottom:1px solid #ddd}@media(max-width:650px){body{padding:24px 14px}h1{font-size:25px}th,td{padding:8px}nav button{padding:8px 10px}}
</style></head><body>
<h1>Tài nguyên nghiên cứu AIOps và Hybrid RAG</h1>
<p>Dữ liệu, tài liệu đọc và bằng chứng nguồn theo kế hoạch CS221. Trang này hoạt động ngoại tuyến, đọc từ snapshot của gói và không gửi dữ liệu đi đâu.</p>
<nav aria-label="Nhóm tài nguyên" role="tablist"><button role="tab" aria-selected="true" data-tab="overview">Tổng quan</button><button role="tab" aria-selected="false" data-tab="incidents">90 sự cố</button><button role="tab" aria-selected="false" data-tab="papers">Thư mục paper</button><button role="tab" aria-selected="false" data-tab="knowledge">Kho tri thức</button></nav>
<section id="overview"><p id="stats" class="stats"></p>
<p class="notice"><strong>Trạng thái khoa học:</strong> dữ liệu được thu thập để chuẩn bị nghiên cứu. Qrels và chất lượng chẩn đoán chưa được người chấm; chưa có kết quả benchmark. Query của incident là mẫu được tạo có quy tắc từ quan sát, không phải câu hỏi gốc của người vận hành.</p>
<div class="links">
<a href="START-HERE.md">Hướng dẫn sử dụng và trạng thái bàn giao</a><a href="05_research/research-report.md">Báo cáo nghiên cứu tổng hợp</a>
<a href="05_research/dataset-research.md">Phân tích dataset và quyết định nguồn</a><a href="05_research/paper-research.md">Tổng hợp đọc paper</a>
<a href="05_research/knowledge-and-annotation.md">Kho tri thức và annotation</a><a href="05_research/method-and-experiment-design.md">Thiết kế retrieval và đánh giá</a>
<a href="03_collection_plan/annotation-kit/README.md">Bộ hướng dẫn và biểu mẫu chấm</a><a href="05_research/retrieval-preview/README.md">Pool gợi ý ban đầu để chấm</a>
<a href="01_papers/enriched/catalog-enriched.tsv">Danh mục paper TSV</a><a href="01_papers/enriched/references-verified.bib">Bibliography BibTeX đã bổ sung</a>
<a href="02_datasets/processed/observations.jsonl">Observations JSONL</a><a href="02_datasets/processed/labels/ground_truth.jsonl">Gold labels riêng cho đánh giá</a>
<a href="05_research/experiment-proposal.json">Cấu hình thí nghiệm đề xuất</a><a href="04_audit/research-pack-validation.json">Kết quả kiểm tra artifact</a>
</div><h2>Những ranh giới cần giữ</h2><p>Không đưa thư mục labels, injection files hoặc tên ca chứa gold vào model input. Snapshot tài liệu hiện tại không tự chứng minh tính phù hợp với sự cố lịch sử. Snapshot cũ, nếu có, vẫn cần kiểm phiên bản triển khai và mức liên quan. File gốc có thể còn thông tin cần khử định danh trước khi chia sẻ hoặc gửi đến dịch vụ mô hình.</p><p id="validation"></p></section>
<section id="incidents" hidden><label for="incident-search">Lọc ID, service quan sát hoặc split</label><input id="incident-search" placeholder="Ví dụ: train, checkoutservice"><p class="muted">Service trong query là tín hiệu quan sát, không phải nhãn nguyên nhân. Mở một dòng để xem query và log đã chọn.</p><div class="scroll"><table><thead><tr><th>Incident / split</th><th>Cửa sổ quan sát</th><th>Query và bằng chứng log</th></tr></thead><tbody id="incident-rows"></tbody></table></div></section>
<section id="papers" hidden><label for="paper-search">Tìm paper theo tiêu đề, ID, tác giả hoặc chủ đề</label><input id="paper-search" placeholder="Ví dụ: RCAEval, retrieval, P0757"><p id="paper-count" class="muted"></p><div class="scroll"><table><thead><tr><th>ID / chủ đề</th><th>Tiêu đề và nguồn</th><th>Metadata</th></tr></thead><tbody id="paper-rows"></tbody></table></div></section>
<section id="knowledge" hidden><label for="knowledge-search">Tìm trong tiêu đề và nội dung tài liệu</label><input id="knowledge-search" placeholder="Ví dụ: OOMKilled, network, shipping"><p class="muted">Danh sách bên dưới là snapshot hiện tại. <a href="03_collection_plan/knowledge-corpus-historical/">Mở snapshot lịch sử riêng</a>. Mapping chưa qua người chấm không phải gold evidence.</p><p id="knowledge-count" class="muted"></p><div class="scroll"><table><thead><tr><th>Tài liệu</th><th>Phạm vi / license</th><th>Nội dung</th></tr></thead><tbody id="knowledge-rows"></tbody></table></div></section>
<script id="resource-data" type="application/json">__DATA__</script>
<script>
const DATA=JSON.parse(document.getElementById('resource-data').textContent);
const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e};
function link(text,url){const a=el('a',text);if(url&&(url.startsWith('https://')||!url.includes(':')))a.href=url;return a}
function cell(row,value){const c=el('td');if(value instanceof Node)c.append(value);else c.textContent=value??'';row.append(c);return c}
function details(title,text){const d=el('details');d.append(el('summary',title),el('pre',text));return d}
function filtered(items,q){q=q.toLowerCase().trim();return items.filter(x=>JSON.stringify(x).toLowerCase().includes(q))}
function drawPapers(){let list=filtered(DATA.papers,document.getElementById('paper-search').value);document.getElementById('paper-count').textContent=list.length+' mục phù hợp; hiển thị tối đa 150 mục mỗi lần lọc. Trạng thái metadata không đồng nghĩa đã đọc toàn văn.';const body=document.getElementById('paper-rows');body.replaceChildren();list.slice(0,150).forEach(p=>{let tr=el('tr');cell(tr,p.paper_id+' · '+(p.topic_vi||p.topic_code||''));let td=cell(tr,link(p.title,p.canonical_url));if(p.note_path)td.append(el('br'),link('Ghi chú đọc',p.note_path));let authors=Array.isArray(p.authors)?p.authors.map(a=>typeof a==='string'?a:JSON.stringify(a)).join('; '):(p.authors||'Tác giả chưa xác nhận');cell(tr,authors+'\n'+(p.publication_year||'Năm chưa xác nhận')+' ('+(p.year_basis||'chưa có year basis')+') · '+(p.venue||'Venue chưa xác nhận')+'\n'+(p.enrichment_status||p.metadata_status||p.verification_status||'unknown')+' · '+(p.read_depth||'chưa đọc'));body.append(tr)})}
function drawIncidents(){let body=document.getElementById('incident-rows');body.replaceChildren();filtered(DATA.observations,document.getElementById('incident-search').value).forEach(o=>{let tr=el('tr');cell(tr,o.incident_id+' / '+o.split);cell(tr,o.observation_start+' → '+o.observation_end);let td=cell(tr,details('Mở query và log',o.symptom_query+'\n\n'+DATA.logs.filter(l=>l.incident_id===o.incident_id).map(l=>'['+l.evidence_id+'] '+l.service+' '+l.text).join('\n\n')));body.append(tr)})}
function drawKnowledge(){let list=filtered(DATA.documents,document.getElementById('knowledge-search').value);document.getElementById('knowledge-count').textContent=list.length+' tài liệu phù hợp';let body=document.getElementById('knowledge-rows');body.replaceChildren();list.forEach(d=>{let tr=el('tr');let td=cell(tr,link(d.title,d.source_url));td.append(el('br'),el('code',d.document_id));cell(tr,d.source_id+' · '+d.license+'\n'+d.available_at+'\n'+d.version_compatibility);cell(tr,details('Đọc nội dung',d.text));body.append(tr)})}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button').forEach(n=>n.setAttribute('aria-selected',String(n===b)));document.querySelectorAll('body>section').forEach(s=>s.hidden=s.id!==b.dataset.tab)});
document.getElementById('paper-search').oninput=drawPapers;document.getElementById('incident-search').oninput=drawIncidents;document.getElementById('knowledge-search').oninput=drawKnowledge;
document.getElementById('stats').textContent=DATA.observations.length+' incident · '+DATA.papers.length+' paper records · '+DATA.documents.length+' documents · '+(DATA.knowledgeSnapshot.chunk_count||0)+' chunks';
document.getElementById('validation').textContent='Kiểm tra artifact: '+(DATA.validation.passed?'đạt':'chưa hoàn tất')+'. Snapshot index: '+DATA.builtAt;
drawPapers();drawIncidents();drawKnowledge();
</script></body></html>'''
(ROOT / 'START-HERE.html').write_text(html.replace('__DATA__', data), encoding='utf-8')
print(json.dumps({'file': 'START-HERE.html', 'papers': len(papers), 'incidents': len(payload['observations']), 'documents': len(payload['documents']), 'bytes': (ROOT / 'START-HERE.html').stat().st_size}))
