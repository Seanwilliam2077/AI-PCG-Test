"""Build the LOD tiers and MEASURE them, rather than estimating their triangle counts.

`geometry_integrity` requires every lodPlan tier to carry an integer
`triangleCount`. Deriving those by multiplying ratios would be a guess: quadric
decimation collapses edges, and what it actually achieves on a given mesh is not
the ratio it was asked for. So each tier is generated, rendered and counted.
"""
import json
import shutil
import subprocess
import sys
import os

SPEC = 'object-sculpt-spec.json'
SK = os.path.expanduser('~/.claude/skills/img2threejs')
BACKUP = 'out/_spec_near.json'
shutil.copy(SPEC, BACKUP)

TIERS = [('near', 0, 1.0), ('mid', 12, 0.45), ('far', 30, 0.18)]
results = []
try:
    for name, distance, mult in TIERS:
        d = json.load(open(BACKUP, encoding='utf-8'))
        if mult < 1.0:
            for c in d['componentTree']:
                gd = c.setdefault('geometryDescriptor', {})
                cur = (gd.get('decimate') or {}).get('targetRatio', 1.0)
                gd['decimate'] = {'targetRatio': round(max(0.02, cur * mult), 4),
                                  'reason': f'LOD tier {name}'}
        json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
        subprocess.run([sys.executable, f'{SK}/forge/stage3_build/generate_threejs_factory.py', SPEC,
                        '--out', 'src/createJinxModel.ts', '--pass-id', 'optimization-pass', '--force'],
                       check=True, capture_output=True)
        # the child prints UTF-8; on this machine Python's default is gbk, which
        # dies on the box-drawing bytes in Vite's banner
        out = subprocess.run(['node', 'tools/render.mjs', '--out', 'out/_lod', '--size', '200x360',
                              '--yaw', '0'], capture_output=True, text=True,
                             encoding='utf-8', errors='replace').stdout
        tris = int(out.split('geometry triangles')[1].split('|')[0].strip())
        calls = int(out.split('draw calls')[1].split('|')[0].strip())
        results.append({'tier': name, 'distance': distance, 'triangleCount': tris,
                        'drawCalls': calls,
                        'strategy': ('full component tree and material layers' if mult == 1.0 else
                                     f'quadric decimation at {mult:.2f} of the near tier density')})
        print(f'  {name:5s} distance {distance:3d}  {tris:7d} tris  {calls:4d} draw calls')
finally:
    shutil.copy(BACKUP, SPEC)

d = json.load(open(SPEC, encoding='utf-8'))
d['lodPlan'] = results
d['performanceBudget'].update({
    'measuredTriangles': results[0]['triangleCount'],
    'measuredDrawCalls': results[0]['drawCalls'],
    'measurementNote': ('Geometry triangles summed over every mesh in the built scene. '
                        'renderer.info.render.triangles was NOT used: it is a per-frame '
                        'RENDERED count that accumulates across draw calls and read almost '
                        'exactly twice the geometry.'),
})
json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
b = d['performanceBudget']
print(f"\nbudget {b['targetTriangles']} tris / {b['maxDrawCalls']} calls   "
      f"built {b['measuredTriangles']} ({b['measuredTriangles']/b['targetTriangles']:.1%}) / "
      f"{b['measuredDrawCalls']} ({b['measuredDrawCalls']/b['maxDrawCalls']:.1%})")
