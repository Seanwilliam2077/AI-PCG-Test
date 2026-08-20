"""sash: interleaved A/B of the sash spec against the live checkout.

Other authors are editing their parts while this runs -- between two bakes a
minute apart the boots, braids, hair and pants shells all changed triangle
count, which moved the global score by more than the sash can.  So bake
A,B,A,B back to back and read the PAIRED differences: drift shows up as
spread within a variant, the sash's effect as a consistent sign across pairs.

    python out/sash_paired.py 2
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'spec', 'parts', 'sash.json')
KEEP = os.path.join(ROOT, 'out', 'sash_new.json')
YAWS = '0,45,90,180,270,315'

OLD = {
    'splitX': 10.0,
    'hem': [[-3.1416, 0.998], [-2.6, 0.972], [-2.1, 0.947], [-1.55, 0.912],
            [-1.1, 0.928], [-0.7, 0.972], [-0.3, 1.002], [0.0, 1.008],
            [1.2, 1.010], [2.4, 1.004], [3.1416, 0.998]],
    'flapHem': [[-3.1416, 1.115], [-2.45, 1.11], [-1.55, 0.966], [-0.65, 1.11],
                [3.1416, 1.115]],
    'flapOut': 0.008,
    'flapFloor': 0.90,
}
OLD_CANVAS = {
    'wedge': [-0.68, 1.85],
    'round': 0.014,
    'hem': [[-3.1416, 1.06], [-1.05, 1.056], [-0.75, 1.008], [-0.45, 0.982],
            [-0.1, 0.966], [0.3, 0.948], [0.55, 0.937], [0.75, 0.946],
            [1.15, 1.0], [1.6, 1.03], [2.0, 1.062], [3.1416, 1.06]],
}


def write(variant):
    d = json.load(open(KEEP))
    if variant == 'A':
        d['sash'].update(OLD)
        d['sash']['canvas'].update(OLD_CANVAS)
    json.dump(d, open(LIVE, 'w'), indent=2)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, shell=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def measure(tag):
    gen = f'out/rp_{tag}'
    run(f'npx tsx tools/bake.ts --lod low --gen {gen}')
    run(f'npx tsx tools/preview.ts --lod low --gen {gen} --yaw {YAWS} '
        f'--size 560x1000 --frame 1.80 --out {gen}_img')
    run(f'python tools/compare.py --tag rp_{tag} --renders {gen}_img --pin')
    m = json.load(open(os.path.join(ROOT, 'out', f'metrics_rp_{tag}.json')))
    out = {'score': m['score'],
           'tris': None,
           'iou': {v['yaw']: v['geometry']['full']['iou'] for v in m['views']}}
    rep = json.load(open(os.path.join(ROOT, 'out', f'bake_report_{gen.replace("/", "_")}.json')))
    out['tris'] = {k.split('/')[1]: v['triangles'] for k, v in rep['shells'].items()}
    return out


reps = int(sys.argv[1]) if len(sys.argv) > 1 else 2
res = {'A': [], 'B': []}
for i in range(reps):
    for v in ('A', 'B'):
        write(v)
        res[v].append(measure(f'{v}{i}'))
shutil.copyfile(KEEP, LIVE)

yaws = sorted(res['A'][0]['iou'])
print('rep  var   score  ' + '  '.join(f'yaw{int(y):<3}' for y in yaws) + '   sash tris  others')
for i in range(reps):
    for v in ('A', 'B'):
        r = res[v][i]
        others = sum(t for k, t in r['tris'].items() if k != 'sash')
        print(f'{i}    {v}   {r["score"]:6.2f}  '
              + '  '.join(f'{r["iou"][y]:.4f}' for y in yaws)
              + f'   {r["tris"]["sash"]:9d}  {others}')
print('\npaired B - A')
for i in range(reps):
    a, b = res['A'][i], res['B'][i]
    print(f'  rep {i}: score {b["score"] - a["score"]:+.2f}   '
          + '  '.join(f'{b["iou"][y] - a["iou"][y]:+.4f}' for y in yaws))
