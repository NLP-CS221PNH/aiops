// Documentation QA only. Does not run any research/implementation pipeline.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const plansRoot = path.join(root, 'plans');
const dirs = fs.readdirSync(plansRoot).filter(n => /^260913-0057-cs221-\d\d-/.test(n)).sort();
const errors = [], plannedLinks = [], checkedLinks = [], records = [];
const field = (s,k) => (s.match(new RegExp('^'+k+':\\s*(.*)$','m'))||[])[1];
const refs = (s,k) => { const v=field(s,k)||'[]'; return v.replace(/^\[|\]$/g,'').split(',').map(x=>x.trim().replace(/^['"]|['"]$/g,'')).filter(Boolean); };
if(dirs.length !== 10) errors.push('Expected 10 independent plan directories; got '+dirs.length);
const names = new Set([...dirs, '260913-0020-cs221-aiops-rag-master-plan']);
const graph = new Map();
for(const dir of names) {
  const text=fs.readFileSync(path.join(plansRoot,dir,'plan.md'),'utf8');
  graph.set(dir,{blockedBy:refs(text,'blockedBy'),blocks:refs(text,'blocks')});
}
for(const [name,g] of graph) {
  for(const before of g.blockedBy) {
    if(!names.has(before)) errors.push(name+': unresolved blockedBy '+before);
    else if(!graph.get(before).blocks.includes(name)) errors.push(name+': missing reverse blocks in '+before);
  }
  for(const after of g.blocks) {
    if(!names.has(after)) errors.push(name+': unresolved blocks '+after);
    else if(!graph.get(after).blockedBy.includes(name)) errors.push(name+': missing reverse blockedBy in '+after);
  }
}
const visited=new Set(),stack=new Set();
function visit(n) {if(stack.has(n)) {errors.push('Dependency cycle: '+n);return;} if(visited.has(n))return; stack.add(n); for(const p of graph.get(n)?.blockedBy||[])if(graph.has(p))visit(p);stack.delete(n);visited.add(n);}
for(const n of names)visit(n);
const files = dirs.flatMap(d => fs.readdirSync(path.join(plansRoot,d)).filter(n=>n==='plan.md'||/^phase-.*\.md$/.test(n)).map(n=>path.join(plansRoot,d,n)));
files.push(path.join(plansRoot,'260913-independent-plans-index.md'));
for(const n of ['260913-independent-plans-contracts.md','260913-independent-plans-research.md','260913-independent-plans-review.md']) {
  const p=path.join(__dirname,n);if(fs.existsSync(p))files.push(p);else errors.push('Missing support report: '+n);
}
for(const file of files) {
  const text = fs.readFileSync(file,'utf8');
  const isPhase=/^phase-/.test(path.basename(file));
  const isPlan=path.basename(file)==='plan.md';
  if(isPhase||isPlan){
    if(!text.startsWith('---\n')&&!text.startsWith('---\r\n'))errors.push(file+': frontmatter missing');
    if(field(text,'status')!=='pending')errors.push(file+': status must be pending');
    if(!field(text,'effort'))errors.push(file+': effort missing');
    if(/\[[xX]\]/.test(text))errors.push(file+': completed checkbox in unimplemented plan');
    if(text.split(/\r?\n/).length<(isPhase?75:40))errors.push(file+': unexpectedly short plan content');
  }
  if(isPhase)for(const aliases of [['Overview','Tổng quan'],['Requirements','Yêu cầu'],['Architecture','Kiến trúc và ranh giới trách nhiệm'],['Related Code Files','Các file liên quan'],['Implementation Steps','Các task triển khai'],['Success Criteria','Tiêu chí thành công'],['Risk Assessment','Rủi ro và xử lý','Handoff và Risk Assessment']])if(!aliases.some(header=>text.includes('## '+header)))errors.push(file+': missing '+aliases[0]);
  if(/_TBD_|_Describe what|Requirement A|Requirement B|_Add a brief|_Define done\.|^1\. Step 1$|^2\. Step 2$/m.test(text))errors.push(file+': unfilled scaffold');
  if(text.includes('\uFFFD'))errors.push(file+': replacement character');
  const withoutCode=text.replace(/```[\s\S]*?```/g,'');
  const links=[...withoutCode.matchAll(/\[[^\]\n]+\]\(([^)\n]+)\)/g)];
  for(const [,raw] of links){
    const url=raw.replace(/^<|>$/g,'').replace(/\s+"[^"]*"$/,'');
    if(/^(https?:|mailto:|codex:|#)/.test(url))continue;
    const clean=decodeURIComponent(url.split('#')[0]).replace(/:\d+$/,'');
    if(!clean)continue;
    const target=path.isAbsolute(clean)?path.normalize(clean):path.resolve(path.dirname(file),clean);
    if(target.includes(path.sep+'06_implementation'+path.sep)&&!fs.existsSync(target)){plannedLinks.push({file:path.relative(root,file),target});continue;}
    checkedLinks.push({file:path.relative(root,file),target});
    if(!fs.existsSync(target))errors.push(path.relative(root,file)+': broken link '+raw);
  }
  // Audit claims that backticked paths outside the future implementation already exist.
  for(const [raw] of text.matchAll(/C:\/Users\/Siinn\/Downloads\/CS221_AIOps_RAG_Research_Pack\/[^`\s)]+/g)){
    const clean=raw.replace(/[.,;]+$/,'').replace(/:\d+$/,'');
    if(/\/06_implementation(?:\/|$)/.test(clean)||/[{}*<>]/.test(clean))continue;
    if(!fs.existsSync(clean))errors.push(path.relative(root,file)+': cited existing path not found '+clean);
  }
  records.push({path:path.relative(root,file).replaceAll('\\','/'),lines:text.split(/\r?\n/).length,bytes:Buffer.byteLength(text),sha256:crypto.createHash('sha256').update(text).digest('hex')});
}
const hours = s => {const m=(s||'').match(/(\d+(?:\.\d+)?)(?:[–-](\d+(?:\.\d+)?))?h/);return m?[Number(m[1]),Number(m[2]||m[1])]:null;};
const effortTotals=[0,0];
for(const d of dirs){
  const names=fs.readdirSync(path.join(plansRoot,d)).filter(n=>/^phase-.*\.md$/.test(n));
  if(names.length!==3)errors.push(d+': expected 3 phase files');
  const t=fs.readFileSync(path.join(plansRoot,d,'plan.md'),'utf8');
  const total=hours(field(t,'effort')), phaseSum=[0,0];
  for(const n of names){
    if(!t.includes(n))errors.push(d+': phase absent from overview '+n);
    const p=fs.readFileSync(path.join(plansRoot,d,n),'utf8');
    const h=hours(field(p,'effort'));if(h){phaseSum[0]+=h[0];phaseSum[1]+=h[1];}else errors.push(d+'/'+n+': effort is not parseable hours');
  }
  if(total){effortTotals[0]+=total[0];effortTotals[1]+=total[1];if(total[0]!==phaseSum[0]||total[1]!==phaseSum[1])errors.push(d+': plan effort differs from phase sums');}
}
if(effortTotals[0]!==308||effortTotals[1]!==374)errors.push('Total planned effort differs from 308–374 hours: '+effortTotals);
const result={scope:'Planning artifacts only; no experiments, human labeling, API calls or implementation tests.',checkedAt:new Date().toISOString(),pass:errors.length===0,independentPlans:dirs.length,phaseFiles:records.filter(r=>/\/phase-/.test(r.path)).length,markdownFiles:records.length,localLinksChecked:checkedLinks.length,plannedLinks:plannedLinks.length,plannedEffortHours:effortTotals,dependencyCyclesDetected:errors.filter(x=>x.includes('cycle')).length,errors,files:records};
fs.writeFileSync(path.join(__dirname,'260913-independent-plans-validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({...result,files:undefined},null,2));
process.exitCode=errors.length?1:0;
