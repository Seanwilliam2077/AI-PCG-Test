"""hair: A/B one braid drape against another, everything else frozen.

WARNING: this REWRITES spec/parts/hair.json to inject braidRows/braidLDelta.
out/hair_frag_keep.json holds the copy taken before the first run; restore it
(cp out/hair_frag_keep.json spec/parts/hair.json) when you are done.

    python out/hair_ab.py A      # A C D E F, see variant() below
"""
import json, subprocess, sys, os
ROOT = r"C:/AI Pipeline Test/jinx3js"
frag = os.path.join(ROOT, "spec/parts/hair.json")

R2 = [[1.695,0.021,-0.078],[1.665,0.023,-0.100],[1.635,0.024,-0.111],[1.600,0.025,-0.114],
      [1.560,0.025,-0.115],[1.520,0.025,-0.116],[1.470,0.024,-0.113],[1.420,0.024,-0.104],
      [1.380,0.025,-0.099],[1.340,0.025,-0.100],[1.300,0.027,-0.099],[1.240,0.031,-0.095],
      [1.180,0.036,-0.089],[1.120,0.040,-0.099],[1.060,0.043,-0.126],[1.000,0.045,-0.140],
      [0.940,0.048,-0.132],[0.900,0.050,-0.112],[0.860,0.052,-0.100],[0.820,0.054,-0.092],
      [0.760,0.057,-0.080],[0.700,0.059,-0.073],[0.640,0.062,-0.071],[0.580,0.065,-0.072],
      [0.500,0.067,-0.087],[0.420,0.069,-0.089],[0.340,0.071,-0.092],[0.270,0.073,-0.118],
      [0.215,0.075,-0.132]]

def variant(name):
    rows = [r[:] for r in R2]
    delta = [[1.100,0,0],[0.215,0,0]]
    if name == "A":
        pass
    elif name == "F":              # round-2 drape, round-3 root only
        rows[0] = [1.686, 0.016, -0.070]
        rows[1] = [1.665, 0.021, -0.098]
    elif name == "C":              # half the round-3 z push, no asymmetry
        push = {0.760:-0.003,0.700:-0.012,0.640:-0.015,0.580:-0.014,0.500:-0.005,
                0.420:-0.007,0.340:-0.016,0.270:-0.017,0.215:-0.017}
        for r in rows:
            if r[0] in push: r[2] += push[r[0]]
    elif name == "D":              # round-2 z, her left plait carried out in x only
        delta = [[1.100,0.000,0.0],[0.900,0.014,0.0],[0.800,0.024,0.0],
                 [0.560,0.028,0.0],[0.215,0.020,0.0]]
    elif name == "E":              # C plus the x-only asymmetry
        push = {0.760:-0.003,0.700:-0.012,0.640:-0.015,0.580:-0.014,0.500:-0.005,
                0.420:-0.007,0.340:-0.016,0.270:-0.017,0.215:-0.017}
        for r in rows:
            if r[0] in push: r[2] += push[r[0]]
        delta = [[1.100,0.000,0.0],[0.900,0.014,0.0],[0.800,0.024,0.0],
                 [0.560,0.028,0.0],[0.215,0.020,0.0]]
    return rows, delta

name = sys.argv[1]
rows, delta = variant(name)
d = json.load(open(frag))
d['hair']['braidRows'] = rows
d['hair']['braidLDelta'] = delta
json.dump(d, open(frag, 'w'), indent=2)

gen = f"out/r3_hair_{name}"
img = f"{gen}_img"
subprocess.run(["npx","tsx","tools/bake.ts","--lod","low","--gen",gen], cwd=ROOT, check=True,
               stdout=subprocess.DEVNULL, shell=True)
subprocess.run(["npx","tsx","tools/preview.ts","--lod","low","--gen",gen,"--yaw","0,45,90,180,270,315",
                "--size","560x1000","--frame","1.80","--out",img], cwd=ROOT, check=True,
               stdout=subprocess.DEVNULL, shell=True)
subprocess.run([sys.executable,"tools/compare.py","--tag",f"h{name}","--renders",img,"--pin"],
               cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
m = json.load(open(os.path.join(ROOT, f"out/metrics_h{name}.json")))
ious = [v['geometry']['full']['iou'] for v in m['views']]
print(name, "score %.2f  meanIoU %.4f" % (m['score'], sum(ious)/len(ious)),
      " ".join("%d:%.3f" % (v['yaw'], v['geometry']['full']['iou']) for v in m['views']),
      " braid", " ".join("%d:%.3f" % (v['yaw'], v['geometry']['braid_area_frac_render']) for v in m['views']))
