"""boots_probe -- per-row run decomposition of a silhouette, in metres.

Normalises exactly the way tools/silhouette.py does (figure scaled to FIG_H,
soles on BASE_Y-1, centroid on CENTER_X), then prints, for each requested
height above the floor, every horizontal run as [x0, x1] in metres measured
from the silhouette centroid, plus the run widths.

    python out/boots_probe.py ref/views/clay_0.png --ys 0.02 0.04 ... 0.32
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import silhouette as S                                       # noqa: E402

FIG_M = 1.72


def load(path):
    bgr, a = S.load_rgba(path)
    m, _ = S.clean_mask(a)
    n = S.normalize(m, bgr)
    return n["mask"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--ys", type=float, nargs="*", default=None)
    ap.add_argument("--y0", type=float, default=0.00)
    ap.add_argument("--y1", type=float, default=0.34)
    ap.add_argument("--step", type=float, default=0.02)
    ap.add_argument("--height", type=float, default=FIG_M)
    args = ap.parse_args()

    ys = args.ys
    if not ys:
        n = int(round((args.y1 - args.y0) / args.step)) + 1
        ys = [args.y0 + i * args.step for i in range(n)]

    px_per_m = (S.FIG_H - 1) / args.height

    for path in args.images:
        mask = load(path)
        st = S.row_stats(mask)
        sr, sc, ec, w = st["_runs"]
        print("== %s" % path)
        print("   %6s %6s  %-52s %s" % ("y(m)", "full", "runs [x0,x1] m", "widths m"))
        for y in ys:
            row = int(round(S.BASE_Y - 1 - y * px_per_m))
            if row < 0 or row >= mask.shape[0]:
                continue
            sel = sr == row
            if not sel.any():
                print("   %6.3f  ---" % y)
                continue
            xs0 = sc[sel]
            xs1 = ec[sel]
            order = np.argsort(xs0)
            xs0, xs1 = xs0[order], xs1[order]
            segs = " ".join("[%+.3f,%+.3f]" % ((a - S.CENTER_X) / px_per_m,
                                               (b - S.CENTER_X) / px_per_m)
                            for a, b in zip(xs0, xs1))
            wid = " ".join("%.3f" % ((b - a) / px_per_m) for a, b in zip(xs0, xs1))
            full = (xs1.max() - xs0.min()) / px_per_m
            print("   %6.3f %6.3f  %-52s %s" % (y, full, segs, wid))
        print()


if __name__ == "__main__":
    main()
