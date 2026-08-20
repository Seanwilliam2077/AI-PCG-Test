"""hair: where the crest sits, anchored on the head band's own centre.

For every panel/render the anchor is the mid-x of the silhouette over
y = 1.55..1.60 (nose-to-back-of-hair), which is stable under the whole-figure
registration error.  Reports the top-of-silhouette profile above y = 1.66.
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.72
PAIRS = [(0, "clay_2"), (45, "clay_1"), (90, "clay_0"),
         (180, "clay_5"), (270, "clay_4"), (315, "clay_3")]


def alpha_of(path):
    im = cv2.imread(os.path.join(ROOT, path), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit("missing " + path)
    if im.ndim == 3 and im.shape[2] == 4:
        return im[:, :, 3]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return (g > 8).astype(np.uint8) * 255


def profile(alpha, rowf, mpp, ys):
    out = {}
    for y in ys:
        r = int(round(rowf(y)))
        if 0 <= r < alpha.shape[0]:
            cols = np.nonzero(alpha[r] > 8)[0]
            out[y] = None if len(cols) == 0 else (cols.min(), cols.max())
        else:
            out[y] = None
    return out


def anchor(alpha, rowf):
    r0, r1 = int(round(rowf(1.60))), int(round(rowf(1.55)))
    seg = alpha[r0:r1]
    ys, xs = np.nonzero(seg > 8)
    return (xs.min() + xs.max()) / 2.0


def top_y(alpha, rowf_inv):
    ys, xs = np.nonzero(alpha > 8)
    return rowf_inv(ys.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default=None)
    ap.add_argument("--frame", type=float, default=1.80)
    args = ap.parse_args()

    ys = [1.66, 1.67, 1.68, 1.69, 1.70, 1.71, 1.715, 1.72, 1.725]
    for yaw, panel in PAIRS:
        if args.renders:
            a = alpha_of(f"{args.renders}/preview_yaw{yaw}.png")
            h = a.shape[0]
            ppm = h / args.frame
            rowf = lambda y: h / 2.0 - (y - args.frame / 2.0) * ppm
            rowi = lambda r: args.frame / 2.0 + (h / 2.0 - r) / ppm
            mpp = 1.0 / ppm
            label = f"render yaw {yaw}"
        else:
            a = alpha_of(f"ref/views/{panel}.png")
            yy, xx = np.nonzero(a > 8)
            top, bot = yy.min(), yy.max()
            ppm = (bot - top) / HEIGHT
            rowf = lambda y, t=top, p=ppm: t + (HEIGHT - y) * p
            rowi = lambda r, t=top, p=ppm: HEIGHT - (r - t) / p
            mpp = 1.0 / ppm
            label = f"{panel} (yaw {yaw})"
        mid = anchor(a, rowf)
        pr = profile(a, rowf, mpp, ys)
        print(f"--- {label}   top y {top_y(a, rowi):.4f}")
        for y in ys:
            v = pr[y]
            if v is None:
                print(f"   {y:.3f}       -")
            else:
                x0 = (v[0] - mid) * mpp
                x1 = (v[1] - mid) * mpp
                print(f"   {y:.3f}  {x0:8.4f} {x1:8.4f}  w {x1-x0:7.4f}  c {(x0+x1)/2:8.4f}")


if __name__ == "__main__":
    main()
