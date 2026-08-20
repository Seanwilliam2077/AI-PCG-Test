"""boots_crop -- crop the boot band out of a reference panel or a preview PNG,
composite it on a light grey card and scale it up, so the shape can be looked at.

    python out/boots_crop.py ref/views/clay_3.png --y0 -0.01 --y1 0.36 --zoom 4 \
        --out out/boots_ref315.png
"""
import argparse

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", required=True)
    ap.add_argument("--y0", type=float, default=-0.01)
    ap.add_argument("--y1", type=float, default=0.36)
    ap.add_argument("--zoom", type=float, default=4.0)
    ap.add_argument("--frame", type=float, default=None,
                    help="preview --frame value; omit for a reference panel")
    ap.add_argument("--height", type=float, default=1.72)
    args = ap.parse_args()

    im = cv2.imread(args.image, cv2.IMREAD_UNCHANGED)
    H, W = im.shape[:2]
    alpha = im[:, :, 3] if im.shape[2] == 4 else np.full((H, W), 255, np.uint8)
    bgr = im[:, :, :3]

    if args.frame:
        ppm = H / args.frame
        base = H                      # world y = 0 is the bottom row
    else:
        ys, xs = np.nonzero(alpha > 127)
        top, bot = ys.min(), ys.max() + 1
        ppm = (bot - top) / args.height
        base = bot

    r0 = int(round(base - args.y1 * ppm))
    r1 = int(round(base - args.y0 * ppm))
    r0, r1 = max(0, r0), min(H, r1)

    sub_a = alpha[r0:r1].astype(np.float32) / 255.0
    sub_c = bgr[r0:r1].astype(np.float32)
    card = np.full_like(sub_c, 210.0)
    comp = (sub_c * sub_a[..., None] + card * (1 - sub_a[..., None])).astype(np.uint8)

    z = args.zoom
    comp = cv2.resize(comp, None, fx=z, fy=z, interpolation=cv2.INTER_NEAREST)

    # horizontal rule every 20 mm, labelled
    hh, ww = comp.shape[:2]
    y = args.y0
    while y <= args.y1 + 1e-9:
        rr = int(round((base - y * ppm - r0) * z))
        if 0 <= rr < hh:
            col = (40, 40, 220) if abs(y * 100 - round(y * 100)) < 1e-6 and \
                round(y * 100) % 10 == 0 else (150, 150, 150)
            comp[rr:rr + 1, :] = col
            cv2.putText(comp, "%.3f" % y, (2, max(10, rr - 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.32, (20, 20, 20), 1, cv2.LINE_AA)
        y += 0.02

    cv2.imwrite(args.out, comp)
    print("%s  %dx%d  %.1f px/m" % (args.out, ww, hh, ppm * z))


if __name__ == "__main__":
    main()
