import json,sys
sys.path.insert(0, r"C:/Users/lvhaochen/.claude/skills/img2threejs/forge/stage4_review")
sys.stdout.reconfigure(encoding='utf-8')
from geometry_integrity import measure_geometry_integrity
meshes=json.load(open(r"C:/AI Pipeline Test/jinx-i2t/analysis/stage4/raw/meshes.json",encoding='utf-8'))["meshes"]
spec=json.load(open(r"C:/AI Pipeline Test/jinx-i2t/object-sculpt-spec.json",encoding='utf-8'))
byid={c['name']:c for c in spec['componentTree']}
for m in meshes:
    c=byid.get(m['id'])
    if c:
        m['role']=c.get('role'); m['attachment']=c.get('attachment'); m['seamAxis']=(c.get('seams') or [{}])[0].get('axis') if c.get('seams') else None
res=measure_geometry_integrity({"meshes":meshes,"performanceBudget":{"triangleBudget":spec['performanceBudget']['targetTriangles']},"lodPlan":spec.get('lodPlan')})
slim={k:v for k,v in res.items() if k!='meshes'}
slim['meshSummary']=[{k:mm.get(k) for k in ('id','boundaryEdges','nonManifoldEdges','triangleCount','normalConsistency')} for mm in res['meshes']]
json.dump(slim,open(r"C:/AI Pipeline Test/jinx-i2t/analysis/stage4/raw/geometry_integrity_full.json",'w'),indent=1)
print('passed',res['passed'],'triangles',res['triangleCount'],'budget',res['triangleBudget'],'lodValid',res['lodPlanValid'])
print('failures',len(res['failures']))
for f in res['failures'][:20]: print('  !',f)
from collections import Counter
print('issue codes',Counter(i['code'] for i in res['issues']))
open_e=[(m['id'],m.get('boundaryEdges'),m.get('nonManifoldEdges')) for m in res['meshes'] if m.get('boundaryEdges') or m.get('nonManifoldEdges')]
print('meshes with open/non-manifold edges:',len(open_e))
for e in open_e[:15]: print('   ',e)
