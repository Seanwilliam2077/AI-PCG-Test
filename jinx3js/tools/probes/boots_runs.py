"""boots: alpha run decomposition at given heights, in metres.

Reference panel:  scale from the alpha bbox (sole..hair tip = --figh).
Render (--frame M): scale is fixed by the framing, x=0 at image centre,
y=0 on the bottom row.

    python out/boots_runs.py --img ref/views/clay_2.png --y 0.06 0.15 0.25
    python out/boots_runs.py --img out/r2_boots_img/preview_yaw0.png --frame 1.80 --y 0.06
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def runs_at(mask, row):
    r = mask[row]
    out = []
    inrun = False
    for i, v in enumerate(r):
        if v and not inrun:
            start = i
            inrun = True
        elif not v and inrun:
            out.append((start, i))
            inrun = False
    if inrun:
        out.append((start, len(r)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--y", type=float, nargs="+", required=True)
    ap.add_argument("--frame", type=float, default=0.0)
    ap.add_argument("--figh", type=float, default=1.72)
    ap.add_argument("--axis", default="x", choices=["x", "z"],
                    help="label only; side views measure depth")
    ap.add_argument("--minrun", type=float, default=0.004,
                    help="drop runs narrower than this, in metres")
    args = ap.parse_args()

    p = args.img if os.path.isabs(args.img) else os.path.join(ROOT, args.img)
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit("cannot read " + p)
    H, W = im.shape[:2]
    alpha = im[:, :, 3] if im.shape[2] == 4 else np.full((H, W), 255, np.uint8)
    mask = alpha > 127

    ys, xs = np.nonzero(mask)
    if args.frame > 0:
        ppm = H / args.frame
        floor_row = H - 0.5
        x0_px = W / 2.0
    else:
        ppm = (ys.max() - ys.min() + 1) / args.figh
        floor_row = ys.max() + 0.5
        x0_px = (xs.min() + xs.max() + 1) / 2.0
    print(f"{args.img}: {W}x{H}  {ppm:.1f} px/m  floor row {floor_row:.1f}  "
          f"x0 px {x0_px:.1f}")

    for y in args.y:
        row = int(round(floor_row - y * ppm))
        if not (0 <= row < H):
            print(f"  y={y:.3f}: row {row} out of image")
            continue
        rr = [(a, b) for (a, b) in runs_at(mask, row) if (b - a) / ppm >= args.minrun]
        parts = []
        for a, b in rr:
            parts.append("[%+.3f,%+.3f]w%.3f" % ((a - x0_px) / ppm, (b - x0_px) / ppm,
                                                 (b - a) / ppm))
        gaps = []
        for i in range(len(rr) - 1):
            gaps.append("%.3f" % ((rr[i + 1][0] - rr[i][1]) / ppm))
        span = ((rr[-1][1] - rr[0][0]) / ppm) if rr else 0.0
        print(f"  y={y:.3f} row {row}: {len(rr)} run(s) span {span:.3f}  " +
              " ".join(parts) + ("  gaps " + ",".join(gaps) if gaps else ""))


if __name__ == "__main__":
    main()
