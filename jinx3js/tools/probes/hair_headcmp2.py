"""hair: 2x3 grid of reference-vs-render head bands, matched px/m."""
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


def band(rgb, rowf, mpp, midc, ymin, ymax, target_mpp, halfw_m):
    r0 = int(round(rowf(ymax)))
    r1 = int(round(rowf(ymin)))
    c0 = int(round(midc - halfw_m / mpp))
    c1 = int(round(midc + halfw_m / mpp))
    h, w = rgb.shape[:2]
    pad_t, pad_b = max(0, -r0), max(0, r1 - h)
    pad_l, pad_r = max(0, -c0), max(0, c1 - w)
    im = cv2.copyMakeBorder(rgb, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=(26, 26, 26))
    crop = im[r0 + pad_t:r1 + pad_t, c0 + pad_l:c1 + pad_l]
    k = mpp / target_mpp
    out = cv2.resize(crop, (max(1, int(crop.shape[1] * k)), max(1, int(crop.shape[0] * k))),
                     interpolation=cv2.INTER_CUBIC)
    # metre rulings every 20 mm
    ppm = 1.0 / target_mpp
    y = ymin
    while y <= ymax + 1e-9:
        py = int(round((ymax - y) * ppm))
        if 0 <= py < out.shape[0]:
            col = (0, 190, 255) if abs(round(y * 100) % 10) < 1e-6 else (70, 110, 130)
            cv2.line(out, (0, py), (out.shape[1], py), col, 1)
        y += 0.02
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default="out/r3_hair_all")
    ap.add_argument("--out", default="out/hair_head.png")
    ap.add_argument("--ymin", type=float, default=1.50)
    ap.add_argument("--ymax", type=float, default=1.745)
    ap.add_argument("--halfw", type=float, default=0.15)
    ap.add_argument("--frame", type=float, default=1.80)
    ap.add_argument("--mpp", type=float, default=0.00055)
    args = ap.parse_args()

    tiles = []
    for yaw, panel in PAIRS:
        rrgb, ra = load(f"ref/views/{panel}.png")
        ys, xs = np.nonzero(ra > 8)
        top, bot = ys.min(), ys.max()
        ppm = (bot - top) / HEIGHT
        rowf = lambda y, t=top, p=ppm: t + (HEIGHT - y) * p
        hb = ra[int(rowf(1.70)):int(rowf(1.50))]
        hy, hx = np.nonzero(hb > 8)
        midc = (hx.min() + hx.max()) / 2.0
        a = band(rrgb, rowf, 1.0 / ppm, midc, args.ymin, args.ymax, args.mpp, args.halfw)

        prgb, pa = load(f"{args.renders}/preview_yaw{yaw}.png")
        h, w = prgb.shape[:2]
        rppm = h / args.frame
        rowg = lambda y, hh=h, p=rppm, f=args.frame: hh / 2.0 - (y - f / 2.0) * p
        hb2 = pa[int(rowg(1.70)):int(rowg(1.50))]
        hy2, hx2 = np.nonzero(hb2 > 8)
        midc2 = (hx2.min() + hx2.max()) / 2.0
        b = band(prgb, rowg, 1.0 / rppm, midc2, args.ymin, args.ymax, args.mpp, args.halfw)

        hgt = max(a.shape[0], b.shape[0])
        pad = lambda im: cv2.copyMakeBorder(im, 0, hgt - im.shape[0], 3, 3,
                                            cv2.BORDER_CONSTANT, value=(26, 26, 26))
        tile = np.hstack([pad(a), pad(b)])
        cv2.putText(tile, f"yaw {yaw} {panel}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (60, 225, 235), 1)
        tiles.append(tile)

    rows = []
    for r in range(2):
        row = tiles[r * 3:(r + 1) * 3]
        hgt = max(t.shape[0] for t in row)
        row = [cv2.copyMakeBorder(t, 0, hgt - t.shape[0], 0, 8, cv2.BORDER_CONSTANT,
                                  value=(26, 26, 26)) for t in row]
        rows.append(np.hstack(row))
    wid = max(r.shape[1] for r in rows)
    rows = [cv2.copyMakeBorder(r, 0, 8, 0, wid - r.shape[1], cv2.BORDER_CONSTANT,
                               value=(26, 26, 26)) for r in rows]
    out = np.vstack(rows)
    cv2.imwrite(os.path.join(ROOT, args.out), out)
    print(args.out, out.shape)


if __name__ == "__main__":
    main()
