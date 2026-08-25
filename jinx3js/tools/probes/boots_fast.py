"""boots_fast -- boots-only bake scored against the reference boot band.

The reference panels are normalised to a 1.72 m figure and tools/preview.ts
--frame 1.80 is already a metric frame, so the two sets of run widths are
directly comparable in metres without normalising the render (which a
boots-only render cannot be: its own bbox is not the figure).

Restricted to y <= --y1 because above the cuff the full character has calves
there and a boots-only render has nothing.

    python out/boots_fast.py --renders out/r3_boots_img
"""
import argparse
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S                                        # noqa: E402

FIG_M = 1.72
PANEL = {0: "clay_2", 45: "clay_1", 90: "clay_0", 180: "clay_5",
         270: "clay_4", 315: "clay_3"}


def ref_core(panel):
    _, a = S.load_rgba(os.path.join(ROOT, "ref", "views", panel + ".png"))
    m, _ = S.clean_mask(a)
    n = S.normalize(m)
    return S.row_stats(n["mask"]), (S.FIG_H - 1) / FIG_M


def ren_core(path, frame):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    H, W = im.shape[:2]
    mask = im[:, :, 3] > 127
    return S.row_stats(mask), H / frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", required=True)
    ap.add_argument("--frame", type=float, default=1.8)
    ap.add_argument("--y0", type=float, default=0.02)
    ap.add_argument("--y1", type=float, default=0.30)
    ap.add_argument("--step", type=float, default=0.02)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--views", default="0,45,90,180,270,315")
    args = ap.parse_args()
    want = [int(v) for v in args.views.split(",")]

    ys = [args.y0 + i * args.step
          for i in range(int(round((args.y1 - args.y0) / args.step)) + 1)]
    n = e2 = 0.0
    for yaw in want:
        p = os.path.join(args.renders, "preview_yaw%d.png" % yaw)
        if not os.path.exists(p):
            continue
        sr, rppm = ref_core(PANEL[yaw])
        sn, nppm = ren_core(p, args.frame)
        if not args.quiet:
            print("== yaw %-3d vs %s" % (yaw, PANEL[yaw]))
        for y in ys:
            rr = int(round(S.BASE_Y - 1 - y * rppm))
            nr = int(round(sn["core_w"].shape[0] - y * nppm)) - 1
            r = float(sr["core_w"][rr]) / rppm
            v = float(sn["core_w"][nr]) / nppm
            if r <= 1e-6:
                continue
            n += 1
            e2 += (v - r) ** 2
            if not args.quiet:
                print("   %6.3f ref %6.3f ren %6.3f  %+7.1f%%"
                      % (y, r, v, 100.0 * (v - r) / r))
        if not args.quiet:
            print()
    print("RMS %.4f m over %d rows" % ((e2 / n) ** 0.5, n))


if __name__ == "__main__":
    main()
