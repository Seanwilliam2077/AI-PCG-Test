"""zapper: silhouette runs off a --frame preview, in world metres.

The preview maps world (x,y,z) -> col = W/2 + u*scale, row = H/2 - (y-f/2)*scale
with scale = H/f, so both axes are exact world metres and no bbox guessing is
needed.  u is +Z at yaw 270 and -Z at yaw 90.
"""
import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def runs(row):
    out, x, n = [], 0, len(row)
    while x < n:
        if row[x]:
            s = x
            while x < n and row[x]:
                x += 1
            out.append((s, x - 1))
        else:
            x += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", required=True)
    ap.add_argument("--frame", type=float, default=1.80)
    ap.add_argument("--ys", type=float, nargs="+", required=True)
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.png), cv2.IMREAD_UNCHANGED)
    H, W = im.shape[:2]
    a = im[:, :, 3] > 8
    scale = H / args.frame
    print(f"{args.png}  {W}x{H}  {scale:.1f} px/m")
    for y in args.ys:
        r = int(round(H / 2 - (y - args.frame / 2) * scale))
        if r < 0 or r >= H:
            continue
        rr = runs(a[r])
        txt = "  ".join(f"[{(s - W / 2) / scale:+.3f},{(e - W / 2) / scale:+.3f}]" for s, e in rr)
        span = (rr[-1][1] - rr[0][0]) / scale if rr else 0
        print(f"  y={y:.3f}  span {span:.3f}  {txt}")


if __name__ == "__main__":
    sys.exit(main())
