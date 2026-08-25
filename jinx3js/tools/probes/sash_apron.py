"""sash: how far round her left rear the khaki apron should run.

body_5 puts the khaki between her x = +0.037 and +0.145 at the back, which is
bearing ~1.9 to ~2.87 -- but that centre estimate is worth +/-0.2 m of panel,
so sweep the band's far end and let the scoreboard pick inside the reading's
own uncertainty.  `flapOut` is held at the 2 mm the depth sweep chose.
"""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'spec', 'parts', 'sash.json')
KEEP = os.path.join(ROOT, 'out', 'sash_new.json')
YAWS = '0,45,90,180,270,315'

ENDS = [2.90, 2.60, 2.30, 2.05, 1.85]


def write(end):
    d = json.load(open(KEEP))
    s = d['sash']
    s['flapOut'] = 0.002
    s['canvas']['wedge'] = [-0.68, end]
    json.dump(d, open(LIVE, 'w'), indent=2)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, shell=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


rows = []
for end in ENDS:
    name = str(end).replace('.', 'p')
    write(end)
    gen = f'out/ru_{name}'
    run(f'npx tsx tools/bake.ts --lod low --gen {gen}')
    run(f'npx tsx tools/preview.ts --lod low --gen {gen} --yaw {YAWS} '
        f'--size 560x1000 --frame 1.80 --out {gen}_img')
    run(f'python tools/compare.py --tag ru_{name} --renders {gen}_img --pin')
    m = json.load(open(os.path.join(ROOT, 'out', f'metrics_ru_{name}.json')))
    terms = {}
    for v in m['views']:
        for k, val in v['score']['terms'].items():
            terms[k] = terms.get(k, 0) + val / len(m['views'])
    rows.append((end, m['score'],
                 sum(v['geometry']['full']['iou'] for v in m['views']) / len(m['views']),
                 terms))
shutil.copyfile(KEEP, LIVE)

keys = ['shape', 'edge', 'chamfer', 'width', 'landmark', 'colour']
print('wedgeEnd    score    IoU   ' + ''.join(k.rjust(10) for k in keys))
for end, sc, iou, t in rows:
    print(f'{end:<10}{sc:7.2f}  {iou:.4f}  ' + ''.join(f'{t[k]:10.4f}' for k in keys))
