"""Crop + upscale the head region of a reference panel, with a metre grid.

    python tools/headcrop.py --panel ref/views/clay_2.png --out out/head_front.png
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.72


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", default="out/headcrop.png")
    ap.add_argument("--ymin", type=float, default=1.40)
    ap.add_argument("--ymax", type=float, default=1.75)
    ap.add_argument("--zoom", type=float, default=4.0)
    ap.add_argument("--step", type=float, default=0.02, help="grid step in metres")
    ap.add_argument("--nogrid", action="store_true")
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        rgb = (im[:, :, :3].astype(np.float32) * a + 30 * (1 - a)).astype(np.uint8)
        alpha = im[:, :, 3]
    else:
        rgb = im
        alpha = np.full(im.shape[:2], 255, np.uint8)
    H, W = rgb.shape[:2]

    ys, xs = np.nonzero(alpha > 8)
    top, bot = ys.min(), ys.max()
    # figure occupies [top, bot] -> [HEIGHT, 0]
    def row(y_m):
        return top + (HEIGHT - y_m) / HEIGHT * (bot - top)

    r0 = int(max(0, row(args.ymax)))
    r1 = int(min(H, row(args.ymin)))
    crop = rgb[r0:r1].copy()
    z = args.zoom
    crop = cv2.resize(crop, (int(W * z), int((r1 - r0) * z)), interpolation=cv2.INTER_CUBIC)
    ch, cw = crop.shape[:2]

    if not args.nogrid:
        y = args.ymin
        while y <= args.ymax + 1e-9:
            py = int((row(y) - r0) * z)
            if 0 <= py < ch:
                cv2.line(crop, (0, py), (cw, py), (0, 190, 255), 1)
                cv2.putText(crop, f"{y:.3f}", (3, max(11, py - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1)
            y += args.step
        # vertical lines every 0.02 m about the panel centre in x
        cx = (xs.min() + xs.max()) / 2.0
        scale_px_per_m = (bot - top) / HEIGHT
        k = -6
        while k <= 6:
            px = int((cx + k * 0.02 * scale_px_per_m) * z)
            if 0 <= px < cw:
                cv2.line(crop, (px, 0), (px, ch), (255, 140, 0), 1)
                cv2.putText(crop, f"{k*0.02:+.2f}", (px + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 170, 60), 1)
            k += 1

    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    cv2.imwrite(os.path.join(ROOT, args.out), crop)
    print(args.out, crop.shape[1], "x", crop.shape[0], "| panel", W, "x", H,
          "| figure rows", top, bot, "| px/m", (bot - top) / HEIGHT,
          "| x centre", (xs.min() + xs.max()) / 2.0)


if __name__ == "__main__":
    main()
