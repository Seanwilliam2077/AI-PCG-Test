"""sash: where does the silhouette split into two legs, and how wide is the gap.

Reports, for a panel or a render, the horizontal alpha runs on each row of a
height band, in metres above the floor.  The floor is the alpha bbox bottom;
the scale is either the figure height (reference panels) or a given px/m
(renders made with --frame).

    python out/sash_split.py --img ref/views/clay_2.png --height 1.72
    python out/sash_split.py --img out/r2_x/preview_yaw0.png --ppm 422.2
"""
import argparse
import os

import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def runs(mask):
    """[(x0, x1)] inclusive index runs of True."""
    out = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--height", type=float, default=1.72)
    ap.add_argument("--ppm", type=float, default=0.0)
    ap.add_argument("--y0", type=float, default=0.40)
    ap.add_argument("--y1", type=float, default=1.10)
    ap.add_argument("--step", type=float, default=0.01)
    ap.add_argument("--minrun", type=int, default=2)
    ap.add_argument("--calib", type=float, default=0.55,
                    help="height whose run midpoint defines x = 0; 0 = use the alpha median")
    args = ap.parse_args()

    p = args.img if os.path.isabs(args.img) else os.path.join(ROOT, args.img)
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit("no image " + p)
    a = im[:, :, 3] > 8
    ys, xs = np.nonzero(a)
    top, bot = int(ys.min()), int(ys.max())
    if args.ppm > 0:
        # a --frame render puts the floor on the bottom row, not at the alpha
        # bbox, so a part that does not reach the ground still reads in metres
        ppm = args.ppm
        bot = a.shape[0] - 1
    else:
        ppm = (bot - top + 1) / args.height
    # Body centre x.  The median of every alpha column is pulled sideways by
    # the braids and the pistol and differs by ~15 mm between panels, which is
    # the same order as the flap being measured.  Anchor instead on the
    # midpoint of the shin run at --calib, where only legs exist in every view.
    if args.calib > 0:
        row = int(round(bot - args.calib * ppm))
        rr = [r for r in runs(a[row]) if r[1] - r[0] + 1 >= args.minrun]
        cx = 0.5 * (rr[0][0] + rr[-1][1]) if rr else float(np.median(xs))
    else:
        cx = float(np.median(xs))
    print(f"{os.path.basename(p)}  bbox rows {top}..{bot}  px/m {ppm:.1f}  "
          f"figure {(bot - top + 1) / ppm:.3f} m  centre x {cx:.1f}px")

    y = args.y1
    first_split = None
    while y >= args.y0 - 1e-9:
        row = int(round(bot - y * ppm))
        if 0 <= row < a.shape[0]:
            rr = [r for r in runs(a[row]) if r[1] - r[0] + 1 >= args.minrun]
            desc = "  ".join(
                f"[{(r[0] - cx) / ppm:+.3f},{(r[1] - cx) / ppm:+.3f}]" for r in rr)
            # a gap straddling the centre = the crotch V
            gap = ""
            for i in range(1, len(rr)):
                g0, g1 = rr[i - 1][1], rr[i][0]
                if g0 < cx < g1:
                    w = (g1 - g0 - 1) / ppm
                    gap = f"   CENTRE GAP {w:.3f} m"
                    if first_split is None and w > 0.004:
                        first_split = (y, w)
            print(f"  y {y:.3f}  n={len(rr)}  {desc}{gap}")
        y -= args.step
    if first_split:
        print(f"SPLIT at y = {first_split[0]:.3f} m (gap {first_split[1]:.3f} m)")
    else:
        print("SPLIT: none in band")


main()
