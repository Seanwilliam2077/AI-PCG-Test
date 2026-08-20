"""boots_sweep -- bake / render / score the whole character once per spec value.

Only touches spec/parts/boots.json, which this author owns, and puts it back
the way it was found on exit.

    python out/boots_sweep.py cuffY 0.290 0.298 0.306
    python out/boots_sweep.py splay 0.20 0.28 0.36
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec", "parts", "boots.json")
GEN = "out/r3_boots"
IMGS = "out/r3_boots_all"


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)


def score():
    run("npx tsx tools/bake.ts --lod low --gen %s" % GEN)
    run("npx tsx tools/preview.ts --lod low --gen %s --yaw 0,45,90,180,270,315 "
        "--size 560x1000 --frame 1.80 --out %s" % (GEN, IMGS))
    r = run("python tools/compare.py --tag bootsweep --renders %s --pin" % IMGS)
    m = re.search(r"SCORE\s+([0-9.]+)", r.stdout)
    ious = re.findall(r"preview_\s+([0-9.]+)", r.stdout)
    mean = sum(float(x) for x in ious) / len(ious) if ious else 0.0
    return (float(m.group(1)) if m else float("nan")), mean, r.stdout


def main():
    key = sys.argv[1]
    vals = [float(v) for v in sys.argv[2:]]
    orig = open(SPEC, encoding="utf-8").read()
    base = json.loads(orig)["boots"][key]
    try:
        for v in vals:
            d = json.loads(orig)
            d["boots"][key] = v
            open(SPEC, "w", encoding="utf-8").write(json.dumps(d, indent=2) + "\n")
            s, iou, _ = score()
            print("%-14s %-9s  score %5.2f   mean IoU %.4f" % (key, v, s, iou))
            sys.stdout.flush()
    finally:
        open(SPEC, "w", encoding="utf-8").write(orig)
        print("restored %s (%s = %s)" % (SPEC, key, base))


if __name__ == "__main__":
    main()
