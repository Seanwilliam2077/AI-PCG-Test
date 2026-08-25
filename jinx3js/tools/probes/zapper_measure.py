"""zapper: silhouette runs off a panel, in metres, with a chosen mid-line.

    python out/zapper_measure.py --panel ref/views/clay_2.png --ys 0.60 0.70 0.80 0.90
"""
import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def runs(mask_row):
    out = []
    x = 0
    n = len(mask_row)
    while x < n:
        if mask_row[x]:
            s = x
            while x < n and mask_row[x]:
                x += 1
            out.append((s, x - 1))
        else:
            x += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--ys", type=float, nargs="+", required=True)
    ap.add_argument("--height", type=float, default=1.72)
    ap.add_argument("--mid", type=float, default=None,
                    help="mid-line as a panel fraction; default = mid of the "
                         "figure at the neck rows (1.40-1.45 m)")
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3] > 8
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    ppm = (bot - top + 1) / args.height

    if args.mid is None:
        r0, r1 = int(bot - 1.45 * ppm), int(bot - 1.40 * ppm)
        cols = np.nonzero(a[r0:r1].any(axis=0))[0]
        mid = 0.5 * (cols.min() + cols.max())
    else:
        mid = args.mid * im.shape[1]

    print(f"{args.panel}  {im.shape[1]}x{im.shape[0]}  {ppm:.1f} px/m  "
          f"rows {top}..{bot}  mid col {mid:.1f}")
    for y in args.ys:
        r = int(round(bot - y * ppm))
        if r < 0 or r >= a.shape[0]:
            continue
        rr = runs(a[r])
        txt = "  ".join(f"[{(s - mid) / ppm:+.3f},{(e - mid) / ppm:+.3f}]" for s, e in rr)
        span = (rr[-1][1] - rr[0][0]) / ppm if rr else 0
        print(f"  y={y:.3f}  span {span:.3f}  {txt}")


if __name__ == "__main__":
    sys.exit(main())
