"""Gridded, labelled crops of a reference panel, for reading measurements off.

    python tools/grid.py --panel ref/views/clay_2.png --out out/grid_front.png
    python tools/grid.py --panel ref/views/clay_2.png --rows 0.0 0.25 --zoom 3
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", default="out/grid.png")
    ap.add_argument("--rows", type=float, nargs=2, default=(0.0, 1.0))
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--step", type=float, default=0.05, help="grid step as a fraction of figure height")
    ap.add_argument("--metres", action="store_true",
                    help="label rows in metres above the floor instead of image fractions, "
                         "taking the panel's alpha bbox as sole (0) to hair tip (--height)")
    ap.add_argument("--height", type=float, default=1.72, help="figure height in metres for --metres")
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (im[:, :, :3].astype(np.float32) * a + 26 * (1 - a)).astype(np.uint8)
    H, W = rgb.shape[:2]

    y0, y1 = int(H * args.rows[0]), int(H * args.rows[1])
    crop = rgb[y0:y1]
    z = args.zoom
    crop = cv2.resize(crop, (int(W * z), int((y1 - y0) * z)), interpolation=cv2.INTER_NEAREST)
    ch, cw = crop.shape[:2]

    # Metre labels save every author from redoing the panel-fraction arithmetic,
    # which is where several measurement errors came from.
    ys_fg, _ = np.nonzero(im[:, :, 3] > 0) if im.shape[2] == 4 else (np.array([0, H - 1]), None)
    fg_top, fg_bot = (int(ys_fg.min()), int(ys_fg.max())) if len(ys_fg) else (0, H - 1)
    px_per_m = max(1.0, fg_bot - fg_top + 1) / args.height

    for t in np.arange(0, 1.0001, args.step):
        y = int((t * H - y0) * z)
        if 0 <= y < ch:
            cv2.line(crop, (0, y), (cw, y), (0, 190, 255), 1)
            if args.metres:
                metres = (fg_bot - (t * H)) / px_per_m
                text = f"{metres:.3f}m"
            else:
                text = f"{t:.2f}"
            cv2.putText(crop, text, (3, max(11, y - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 220, 255), 1)
    for t in np.arange(0, 1.0001, 0.1):
        x = int(t * W * z)
        if 0 <= x < cw:
            cv2.line(crop, (x, 0), (x, ch), (255, 140, 0), 1)
            cv2.putText(crop, f"{t:.1f}", (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 170, 60), 1)

    cv2.imwrite(os.path.join(ROOT, args.out), crop)
    print(args.out, crop.shape[1], "x", crop.shape[0], "| panel", W, "x", H,
          f"| {px_per_m:.1f} px/m, figure rows {fg_top}..{fg_bot}" if args.metres else "")


if __name__ == "__main__":
    main()
