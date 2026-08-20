"""Silhouette edge columns at named heights, in metres, for a turnaround panel."""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--ys", type=float, nargs="+", required=True)
    ap.add_argument("--height", type=float, default=1.72)
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    H, W = im.shape[:2]
    alpha = im[:, :, 3]
    ys, xs = np.nonzero(alpha > 16)
    top, bot = ys.min(), ys.max()
    left, right = xs.min(), xs.max()
    mm = args.height / (bot - top)
    cx = (left + right) / 2.0
    print(f"{args.panel}: {W}x{H} bbox x[{left},{right}] y[{top},{bot}] {mm*1000:.3f} mm/px cx={cx:.1f}")
    for m in args.ys:
        row = int(round(bot - m / mm))
        if row < 0 or row >= H:
            print(f"  y={m:.3f}  out of range")
            continue
        cols = np.nonzero(alpha[row] > 16)[0]
        if len(cols) == 0:
            print(f"  y={m:.3f}  empty")
            continue
        # report all runs so occluding braids are visible as separate spans
        runs = []
        start = cols[0]
        prev = cols[0]
        for c in cols[1:]:
            if c != prev + 1:
                runs.append((start, prev))
                start = c
            prev = c
        runs.append((start, prev))
        txt = "  ".join(f"[{(a-cx)*mm:+.3f}..{(b-cx)*mm:+.3f}]" for a, b in runs)
        print(f"  y={m:.3f} row={row}  {txt}")


if __name__ == "__main__":
    main()
