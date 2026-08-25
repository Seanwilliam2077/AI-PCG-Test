"""zapper/tattoo: where the cloud ink actually is on the reference.

The ink is a pale blue-grey laid over skin, so it separates from bare skin by
hue (skin is warm, ink is cool) while staying much brighter and less saturated
than the braids or the top.
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--height", type=float, default=1.72)
    ap.add_argument("--dump", default=None)
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    bgr = im[:, :, :3].astype(np.float32)
    a = im[:, :, 3] > 8
    H, W = a.shape
    ys, _ = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    ppm = (bot - top + 1) / args.height

    b, g, r = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]
    v = bgr.max(axis=2)
    mn = bgr.min(axis=2)
    sat = np.where(v > 0, (v - mn) / np.maximum(v, 1), 0)
    # ink: bright, cool (blue >= red), weakly saturated.  skin is r > b by a
    # wide margin; the braid blue is far more saturated and much darker.
    ink = a & (v > 120) & (v < 235) & (b >= r + 4) & (sat < 0.28)
    ink &= (g > r - 6)

    n, lab, stats, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
    keep = np.zeros_like(ink)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 25:
            keep |= lab == i
    ink = keep

    print(f"{args.panel}  {W}x{H}  {ppm:.1f} px/m   ink {ink.sum()} px "
          f"({100.0*ink.sum()/max(1,a.sum()):.1f}% of the figure)")
    print("   y      ink[left,right] (panel metres)   n_px   figure[left,right]")
    y = 1.50
    while y >= 0.25:
        r0 = int(round(bot - y * ppm))
        i = np.nonzero(ink[r0])[0]
        f = np.nonzero(a[r0])[0]
        s = f"[{i.min()/ppm:.3f},{i.max()/ppm:.3f}]" if len(i) else "      --      "
        fs = f"[{f.min()/ppm:.3f},{f.max()/ppm:.3f}]" if len(f) else "  --  "
        print(f"  {y:.2f}  {s}  {len(i):4d}   {fs}")
        y -= 0.05

    if args.dump:
        out = im[:, :, :3].copy()
        out[ink] = (0, 0, 255)
        cv2.imwrite(os.path.join(ROOT, args.dump), out)
        print("wrote", args.dump)


if __name__ == "__main__":
    main()
