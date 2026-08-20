"""pants: ablate the round-3 spec changes back to back.

Each variant patches spec/parts/pants.json, bakes the WHOLE figure into the
same directory, renders the six pinned yaws and scores.  Running them in one
go is the point: another author's edit landing between two bakes is what makes
a remembered baseline useless.

    python tools/pants_sweep.py r2 flareZ legOut all
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAG = os.path.join(ROOT, "spec", "parts", "pants.json")
GEN = "out/r3_pants_sw"
IMG = "out/r3_pants_sw_img"

base = json.load(open(FRAG))
KEEP = json.loads(json.dumps(base))          # deep copy, restored at the end

FLARE_Z = KEEP["pants"]["flareZ"]
LEG_OUT = KEEP["pants"]["legOut"]
HEM_NEW = KEEP["pants"]["hemY"]
HEM_OLD = 0.466


def variant(name):
    p = json.loads(json.dumps(KEEP))["pants"]
    if name == "r2":
        p.pop("flareZ", None)
        p.pop("legOut", None)
        p["hemY"] = HEM_OLD
        p["voxelScale"] = 1.55
    elif name == "flareZ":
        p.pop("legOut", None)
        p["hemY"] = HEM_OLD
    elif name == "hem":
        p.pop("legOut", None)
    elif name == "legOut":
        p.pop("flareZ", None)
        p["hemY"] = HEM_OLD
    elif name == "nohem":
        p["hemY"] = HEM_OLD
    elif name == "noout":
        p.pop("legOut", None)
    elif name == "nofz":
        p.pop("flareZ", None)
    elif name == "all":
        pass
    elif name.startswith("out"):             # out0.004 -> legOut scaled
        s = float(name[3:])
        p["legOut"] = [[y, round(v / LEG_OUT[0][1] * s, 5)] for y, v in LEG_OUT]
    elif name.startswith("fz"):              # fz-0.004 -> flareZ floor
        s = float(name[2:])
        p["flareZ"] = [[y, (s if v <= 0.0011 else v)] for y, v in FLARE_Z]
    elif name.startswith("vox"):             # vox1.15 -> pants voxelScale
        p["voxelScale"] = float(name[3:])
    elif name.startswith("seat"):            # seat0.6 -> scale the seat blouse
        s = float(name[4:])
        p["flare"] = [[y, (round(v * s, 5) if y >= 0.78 else v)]
                      for y, v in KEEP["pants"]["flare"]]
        p["flareZ"] = [[y, (round(v * s, 5) if y >= 0.78 else v)]
                       for y, v in FLARE_Z]
    else:
        raise SystemExit("unknown variant %s" % name)
    return p


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:])
        raise SystemExit("failed: %s" % cmd)
    return r.stdout


results = []
try:
    for name in sys.argv[1:]:
        doc = json.loads(json.dumps(KEEP))
        doc["pants"] = variant(name)
        json.dump(doc, open(FRAG, "w"), indent=2)
        run("npx tsx tools/bake.ts --lod low --gen %s" % GEN)
        run("npx tsx tools/preview.ts --lod low --gen %s --yaw 0,45,90,180,270,315 "
            "--size 560x1000 --frame 1.80 --out %s" % (GEN, IMG))
        run("python tools/compare.py --tag sw_%s --renders %s --pin" % (name, IMG))
        m = json.load(open(os.path.join(ROOT, "out", "metrics_sw_%s.json" % name)))
        ious = [v["geometry"]["full"]["iou"] for v in m["views"]]
        wr = [v["geometry"]["width_rms_core_pct"] for v in m["views"]]
        results.append((name, m["score"], sum(ious) / len(ious), ious, wr))
        print("  %-10s score %6.2f  meanIoU %.4f" % (name, m["score"],
                                                     sum(ious) / len(ious)))
finally:
    json.dump(KEEP, open(FRAG, "w"), indent=2)

print("\n%-10s %7s %8s  %s" % ("variant", "score", "meanIoU", "per-view IoU (0/45/90/180/270/315)"))
for name, sc, mi, ious, wr in results:
    print("%-10s %7.2f %8.4f  %s" % (name, sc, mi,
                                     " ".join("%.4f" % v for v in ious)))
print("\n%-10s %s" % ("variant", "width_rms_core per view"))
for name, sc, mi, ious, wr in results:
    print("%-10s %s" % (name, " ".join("%5.2f" % v for v in wr)))
