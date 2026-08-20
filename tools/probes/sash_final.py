"""sash: final check -- round 2 with the flap's stand-off cut to 2 mm, against
round 1 and against dropping each of the three changes in turn."""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'spec', 'parts', 'sash.json')
KEEP = os.path.join(ROOT, 'out', 'sash_new.json')
YAWS = '0,45,90,180,270,315'

OLD_WRAP = {
    'splitX': 10.0,
    'hem': [[-3.1416, 0.998], [-2.6, 0.972], [-2.1, 0.947], [-1.55, 0.912],
            [-1.1, 0.928], [-0.7, 0.972], [-0.3, 1.002], [0.0, 1.008],
            [1.2, 1.010], [2.4, 1.004], [3.1416, 0.998]],
}
OLD_FLAP = {
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

# name -> (flapOut or None to keep round 1's fold, old wrap, old canvas)
VARIANTS = [
    ('round1', None, True, True),
    ('final02', 0.002, False, False),
    ('final04', 0.004, False, False),
    ('f02_oldapron', 0.002, False, True),
    ('f02_nosplit', 0.002, True, False),
    ('round1b', None, True, True),
    ('final02b', 0.002, False, False),
]


def write(out, oldw, oldc):
    d = json.load(open(KEEP))
    s = d['sash']
    if out is None:
        s.update(OLD_FLAP)
    else:
        s['flapOut'] = out
    if oldw:
        s.update(OLD_WRAP)
    if oldc:
        s['canvas'].update(OLD_CANVAS)
    json.dump(d, open(LIVE, 'w'), indent=2)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, shell=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


rows = []
for name, out, oldw, oldc in VARIANTS:
    write(out, oldw, oldc)
    gen = f'out/rt_{name}'
    run(f'npx tsx tools/bake.ts --lod low --gen {gen}')
    run(f'npx tsx tools/preview.ts --lod low --gen {gen} --yaw {YAWS} '
        f'--size 560x1000 --frame 1.80 --out {gen}_img')
    run(f'python tools/compare.py --tag rt_{name} --renders {gen}_img --pin')
    m = json.load(open(os.path.join(ROOT, 'out', f'metrics_rt_{name}.json')))
    terms = {}
    for v in m['views']:
        for k, val in v['score']['terms'].items():
            terms[k] = terms.get(k, 0) + val / len(m['views'])
    rep = json.load(open(os.path.join(ROOT, 'out',
                                      f'bake_report_out_rt_{name}.json')))
    rows.append((name, m['score'],
                 sum(v['geometry']['full']['iou'] for v in m['views']) / len(m['views']),
                 terms, rep['shells']['low/sash']['triangles']))
shutil.copyfile(KEEP, LIVE)

keys = ['shape', 'edge', 'chamfer', 'width', 'landmark', 'colour']
print('variant       score    IoU   ' + ''.join(k.rjust(10) for k in keys) + '   sashTris')
for name, sc, iou, t, tris in rows:
    print(f'{name:<12}{sc:7.2f}  {iou:.4f}  '
          + ''.join(f'{t[k]:10.4f}' for k in keys) + f'{tris:11d}')
