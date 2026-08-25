"""boots_fsweep -- boots-only bake + boot-band RMS, one point per spec value.

Restores spec/parts/boots.json on the way out.

    python out/boots_fsweep.py cuffY 0.288 0.298 0.308
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec", "parts", "boots.json")


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)


def rms():
    b = run("npx tsx tools/bake.ts --lod low --only boots --gen out/r3_boots_only")
    if "wrote" not in b.stdout:
        return float("nan"), b.stdout[-400:] + b.stderr[-400:]
    run("npx tsx tools/preview.ts --lod low --gen out/r3_boots_only "
        "--yaw 0,45,90,180,270,315 --size 460x900 --frame 1.80 --out out/r3_boots_img")
    r = run("python out/boots_fast.py --renders out/r3_boots_img --quiet --views 0,90,180,270")
    m = re.search(r"RMS ([0-9.]+)", r.stdout)
    return (float(m.group(1)) if m else float("nan")), b.stdout.strip().splitlines()[-2]


def main():
    orig = open(SPEC, encoding="utf-8").read()
    pairs = []
    i = 1
    while i < len(sys.argv):
        key = sys.argv[i]
        vals = []
        i += 1
        while i < len(sys.argv) and re.match(r"^-?[0-9.]+$", sys.argv[i]):
            vals.append(float(sys.argv[i]))
            i += 1
        pairs.append((key, vals))
    try:
        for key, vals in pairs:
            for v in vals:
                d = json.loads(orig)
                d["boots"][key] = v
                open(SPEC, "w", encoding="utf-8").write(json.dumps(d, indent=2) + "\n")
                s, note = rms()
                print("%-14s %-9s  RMS %.4f   %s" % (key, v, s, note))
                sys.stdout.flush()
    finally:
        open(SPEC, "w", encoding="utf-8").write(orig)
        print("restored")


if __name__ == "__main__":
    main()
