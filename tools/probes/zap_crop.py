"""Crop + upscale a region of a reference panel, and report the metre mapping.

    python out/zap_crop.py --panel ref/views/body_0.png --y0 0.60 --y1 0.85 --x0 0.0 --x1 1.0 --zoom 5
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", default="out/zap_crop.png")
    ap.add_argument("--y0", type=float, default=0.0)
    ap.add_argument("--y1", type=float, default=1.0)
    ap.add_argument("--x0", type=float, default=0.0)
    ap.add_argument("--x1", type=float, default=1.0)
    ap.add_argument("--zoom", type=float, default=4.0)
    ap.add_argument("--height", type=float, default=1.72)
    ap.add_argument("--grid", type=float, default=0.05, help="metre grid step")
    ap.add_argument("--pxm", type=float, default=0.0, help="pixels per metre (preview renders)")
    ap.add_argument("--floor", type=float, default=-1.0, help="row of y=0 (preview renders)")
    ap.add_argument("--cx", type=float, default=-1.0, help="column of x=0 (preview renders)")
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    H, W = im.shape[:2]
    alpha = im[:, :, 3]
    ys, xs = np.nonzero(alpha > 8)
    top, bot = ys.min(), ys.max()
    left, right = xs.min(), xs.max()
    scale = args.height / (bot - top)  # metres per pixel
    if args.pxm > 0:
        scale = 1.0 / args.pxm
    if args.floor >= 0:
        bot = args.floor
    print(f"panel {W}x{H} alpha bbox x[{left},{right}] y[{top},{bot}] -> {scale*1000:.3f} mm/px")

    a = alpha[:, :, None].astype(np.float32) / 255.0
    rgb = (im[:, :, :3].astype(np.float32) * a + 30 * (1 - a)).astype(np.uint8)

    py0, py1 = int(H * args.y0), int(H * args.y1)
    px0, px1 = int(W * args.x0), int(W * args.x1)
    crop = rgb[py0:py1, px0:px1].copy()
    z = args.zoom
    ch0, cw0 = crop.shape[:2]
    crop = cv2.resize(crop, (int(cw0 * z), int(ch0 * z)), interpolation=cv2.INTER_CUBIC)
    ch, cw = crop.shape[:2]

    # horizontal lines every `grid` metres of height above the floor (= bot)
    m = 0.0
    while m <= args.height + 1e-6:
        ypix = bot - m / scale
        y = int((ypix - py0) * z)
        if 0 <= y < ch:
            major = abs(m / 0.1 - round(m / 0.1)) < 1e-6
            cv2.line(crop, (0, y), (cw, y), (0, 190, 255), 2 if major else 1)
            cv2.putText(crop, f"{m:.3f}", (3, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (0, 230, 255), 1, cv2.LINE_AA)
        m += args.grid

    # vertical lines every `grid` metres from the panel centre-x of the alpha bbox
    cx = args.cx if args.cx >= 0 else (left + right) / 2.0
    k = -20
    while k <= 20:
        xpix = cx + k * args.grid / scale
        x = int((xpix - px0) * z)
        if 0 <= x < cw:
            cv2.line(crop, (x, 0), (x, ch), (255, 140, 0), 1)
            cv2.putText(crop, f"{k*args.grid:+.2f}", (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.4, (255, 180, 70), 1, cv2.LINE_AA)
        k += 1

    cv2.imwrite(os.path.join(ROOT, args.out), crop)
    print(args.out, cw, "x", ch)


if __name__ == "__main__":
    main()
