"""hair: reference head band beside the render's, at one metres-per-pixel.

    python out/hair_headcmp.py --renders out/r3_hair_all --out out/hair_head.png
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.72
PAIRS = [(0, "clay_2"), (45, "clay_1"), (90, "clay_0"),
         (180, "clay_5"), (270, "clay_4"), (315, "clay_3")]


def load(path):
    im = cv2.imread(os.path.join(ROOT, path), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit("missing " + path)
    if im.ndim == 3 and im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        rgb = (im[:, :, :3].astype(np.float32) * a + 26 * (1 - a)).astype(np.uint8)
        return rgb, im[:, :, 3]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return im, (g > 8).astype(np.uint8) * 255


def band(rgb, alpha, rowf, mpp, midc, ymin, ymax, target_mpp, halfw_m):
    r0 = int(round(rowf(ymax)))
    r1 = int(round(rowf(ymin)))
    c0 = int(round(midc - halfw_m / mpp))
    c1 = int(round(midc + halfw_m / mpp))
    h, w = rgb.shape[:2]
    pad_t = max(0, -r0); pad_b = max(0, r1 - h)
    pad_l = max(0, -c0); pad_r = max(0, c1 - w)
    im = cv2.copyMakeBorder(rgb, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=(26, 26, 26))
    crop = im[r0 + pad_t:r1 + pad_t, c0 + pad_l:c1 + pad_l]
    k = mpp / target_mpp
    return cv2.resize(crop, (int(crop.shape[1] * k), int(crop.shape[0] * k)),
                      interpolation=cv2.INTER_CUBIC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default="out/r3_hair_all")
    ap.add_argument("--out", default="out/hair_head.png")
    ap.add_argument("--ymin", type=float, default=1.44)
    ap.add_argument("--ymax", type=float, default=1.745)
    ap.add_argument("--halfw", type=float, default=0.17)
    ap.add_argument("--frame", type=float, default=1.80)
    ap.add_argument("--mpp", type=float, default=0.00035)
    args = ap.parse_args()

    tiles = []
    for yaw, panel in PAIRS:
        rrgb, ra = load(f"ref/views/{panel}.png")
        ys, xs = np.nonzero(ra > 8)
        top, bot = ys.min(), ys.max()
        ppm = (bot - top) / HEIGHT
        rowf = lambda y, t=top, p=ppm: t + (HEIGHT - y) * p
        # midline: the alpha-bbox centre of the HEAD band only, which the braids
        # do not drag the way they drag the whole figure's.
        hb = ra[int(rowf(1.70)):int(rowf(1.50))]
        hy, hx = np.nonzero(hb > 8)
        midc = (hx.min() + hx.max()) / 2.0
        a = band(rrgb, ra, rowf, 1.0 / ppm, midc, args.ymin, args.ymax, args.mpp, args.halfw)

        prgb, pa = load(f"{args.renders}/preview_yaw{yaw}.png")
        h, w = prgb.shape[:2]
        rppm = h / args.frame
        rowg = lambda y, hh=h, p=rppm, f=args.frame: hh / 2.0 - (y - f / 2.0) * p
        hb2 = pa[int(rowg(1.70)):int(rowg(1.50))]
        hy2, hx2 = np.nonzero(hb2 > 8)
        midc2 = (hx2.min() + hx2.max()) / 2.0
        b = band(prgb, pa, rowg, 1.0 / rppm, midc2, args.ymin, args.ymax, args.mpp, args.halfw)

        hgt = max(a.shape[0], b.shape[0])
        def pad(im):
            return cv2.copyMakeBorder(im, 0, hgt - im.shape[0], 4, 4,
                                      cv2.BORDER_CONSTANT, value=(26, 26, 26))
        tile = np.hstack([pad(a), pad(b)])
        cv2.putText(tile, f"yaw {yaw}  {panel}", (6, 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (60, 225, 235), 1)
        tiles.append(tile)

    hgt = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, hgt - t.shape[0], 0, 6, cv2.BORDER_CONSTANT,
                                value=(26, 26, 26)) for t in tiles]
    out = np.hstack(tiles)
    cv2.imwrite(os.path.join(ROOT, args.out), out)
    print(args.out, out.shape)


if __name__ == "__main__":
    main()
