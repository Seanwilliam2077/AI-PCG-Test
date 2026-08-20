"""sash: sweep the flap's depth and stand-off against the scoreboard.

The ablation says the long flap trades a width gain for an edge and landmark
loss, so the question is whether it is hanging too low, standing too proud, or
both.  Each variant scales the flap hem's drop below the wrap and sets
`flapOut`; `drop 1.0` is the measured hem (low corner y = 0.815), `drop 0.0`
lifts the whole flap to the wrap's own hem.
"""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'spec', 'parts', 'sash.json')
KEEP = os.path.join(ROOT, 'out', 'sash_new.json')
YAWS = '0,45,90,180,270,315'
TOP = 1.09          # where the flap runs out at either end

VARIANTS = [
    ('d100_o7', 1.0, 0.007),
    ('d100_o2', 1.0, 0.002),
    ('d100_o0', 1.0, 0.000),
    ('d060_o7', 0.6, 0.007),
    ('d060_o2', 0.6, 0.002),
    ('d030_o7', 0.3, 0.007),
]


def write(drop, out):
    d = json.load(open(KEEP))
    s = d['sash']
    s['flapHem'] = [[a, TOP - (TOP - v) * drop] for a, v in s['flapHem']]
    s['flapOut'] = out
    s['flapFloor'] = min(v for _, v in s['flapHem']) - 0.01
    json.dump(d, open(LIVE, 'w'), indent=2)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, shell=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


rows = []
for name, drop, out in VARIANTS:
    write(drop, out)
    gen = f'out/rs_{name}'
    run(f'npx tsx tools/bake.ts --lod low --gen {gen}')
    run(f'npx tsx tools/preview.ts --lod low --gen {gen} --yaw {YAWS} '
        f'--size 560x1000 --frame 1.80 --out {gen}_img')
    run(f'python tools/compare.py --tag rs_{name} --renders {gen}_img --pin')
    m = json.load(open(os.path.join(ROOT, 'out', f'metrics_rs_{name}.json')))
    terms = {}
    for v in m['views']:
        for k, val in v['score']['terms'].items():
            terms[k] = terms.get(k, 0) + val / len(m['views'])
    rows.append((name, m['score'],
                 sum(v['geometry']['full']['iou'] for v in m['views']) / len(m['views']),
                 terms))
shutil.copyfile(KEEP, LIVE)

keys = ['shape', 'edge', 'chamfer', 'width', 'landmark', 'colour']
print('variant     score    IoU   ' + ''.join(k.rjust(10) for k in keys))
for name, sc, iou, t in rows:
    print(f'{name:<10}{sc:7.2f}  {iou:.4f}  ' + ''.join(f'{t[k]:10.4f}' for k in keys))
