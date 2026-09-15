import urllib.request,json,pathlib,hashlib,datetime
root=pathlib.Path('03_collection_plan/knowledge-corpus/raw/source-snapshots')
repos={'D057':('GoogleCloudPlatform/microservices-demo','b9a978db9e01f4ad3dca9494a22cb9edc17548fe'),'D058':('kubernetes/website','76a0e90f253e924a7b55f01f92a37555bd89be68'),'D059':('prometheus-operator/runbooks','a685d14cf5128bb30e2bf935c3983decd772d885')}
for sid,(repo,sha) in repos.items():
 dest=root/sid;dest.mkdir(exist_ok=True)
 url=f'https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1'
 data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CS221-research-acquisition'}),timeout=60).read()
 (dest/'repository-tree.json').write_bytes(data)
 tree=json.loads(data)
 print(sid,'truncated=',tree.get('truncated'))
 for x in tree.get('tree',[]):
  p=x['path']
  if x['type']!='blob':continue
  if sid=='D057' and (p.lower().endswith('.md') or p.startswith('LICENSE')):print(p)
  if sid=='D058' and (p.startswith('LICENSE') or p.startswith('content/en/docs/tasks/debug') or p.startswith('content/en/docs/concepts/configuration/manage-resources')):print(p)
  if sid=='D059' and (p.lower().endswith('.md') or p.startswith('LICENSE')):print(p)
