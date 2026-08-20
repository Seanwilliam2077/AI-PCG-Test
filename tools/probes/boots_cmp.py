"""boots_cmp -- reference vs render core (widest-run) width through the boot band.

Both sides are read with the SAME normalisation the scoreboard uses
(tools/silhouette.py: figure scaled to 1024 px, soles on the base row, centroid
centred), so the numbers here move the same way compare.py's width bands do.

    python out/boots_cmp.py --renders out/r3_boots_all
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S                                        # noqa: E402

FIG_M = 1.72
PANEL = {0: "clay_2", 45: "clay_1", 90: "clay_0", 180: "clay_5",
         270: "clay_4", 315: "clay_3"}


def stats(path):
    _, a = S.load_rgba(path)
    m, _ = S.clean_mask(a)
    n = S.normalize(m)
    if n is None:
        return None
    return S.row_stats(n["mask"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", required=True)
    ap.add_argument("--y0", type=float, default=0.02)
    ap.add_argument("--y1", type=float, default=0.34)
    ap.add_argument("--step", type=float, default=0.02)
    args = ap.parse_args()

    ppm = (S.FIG_H - 1) / FIG_M
    ys = [args.y0 + i * args.step
          for i in range(int(round((args.y1 - args.y0) / args.step)) + 1)]

    tot_n = tot_e2 = 0.0
    for yaw in (0, 45, 90, 180, 270, 315):
        rp = os.path.join(args.renders, "preview_yaw%d.png" % yaw)
        if not os.path.exists(rp):
            rp = os.path.join(args.renders, "render_yaw%d.png" % yaw)
        if not os.path.exists(rp):
            print("no render for yaw %d in %s" % (yaw, args.renders))
            continue
        sr = stats(os.path.join(ROOT, "ref", "views", PANEL[yaw] + ".png"))
        sn = stats(rp)
        print("== yaw %-3d  vs %s" % (yaw, PANEL[yaw]))
        print("   %6s %8s %8s %8s   %6s %6s" %
              ("y(m)", "ref core", "ren core", "err %", "refRuns", "renRuns"))
        for y in ys:
            row = int(round(S.BASE_Y - 1 - y * ppm))
            r = float(sr["core_w"][row]) / ppm
            n = float(sn["core_w"][row]) / ppm
            err = 100.0 * (n - r) / r if r > 1e-6 else float("nan")
            if r > 1e-6:
                tot_n += 1
                tot_e2 += (n - r) ** 2
            print("   %6.3f %8.3f %8.3f %+8.1f   %6d %6d"
                  % (y, r, n, err, sr["nrun"][row], sn["nrun"][row]))
        print()
    if tot_n:
        print("boot-band core width RMS error: %.4f m over %d rows"
              % ((tot_e2 / tot_n) ** 0.5, tot_n))


if __name__ == "__main__":
    main()
