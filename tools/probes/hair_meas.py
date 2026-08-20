"""hair: per-row silhouette extents in metres, for reference panels and renders.

Reference panels are normalised by their own alpha bbox (top = 1.72 m = HEIGHT,
bottom = 0), which is what tools/grid.py --metres does.  Renders made with
--frame 1.80 carry their own metric mapping: the frustum is 1.80 m tall and
centred on y = 0.90, x = 0.

    python out/hair_meas.py --panel ref/views/clay_2.png --rows 1.62:1.74:0.01
    python out/hair_meas.py --render out/r3_hair_all/preview_yaw0.png --rows ...
"""
import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.72


def load_alpha(path):
    im = cv2.imread(os.path.join(ROOT, path), cv2.IMREAD_UNCHANGED)
    if im is None:
        sys.exit("no such image: " + path)
    if im.ndim == 3 and im.shape[2] == 4:
        return im[:, :, 3]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return (g > 8).astype(np.uint8) * 255


def ref_map(alpha):
    """Return (row_of_y, m_per_px, mid_col) for a reference panel."""
    ys, xs = np.nonzero(alpha > 8)
    top, bot = ys.min(), ys.max()
    ppm = (bot - top) / HEIGHT
    return (lambda y: top + (HEIGHT - y) * ppm), 1.0 / ppm, (xs.min() + xs.max()) / 2.0


def render_map(alpha, frame):
    h, w = alpha.shape[:2]
    ppm = h / frame
    return (lambda y: h / 2.0 - (y - frame / 2.0) * ppm), 1.0 / ppm, w / 2.0


def runs(row, thresh=8):
    on = row > thresh
    out = []
    i = 0
    n = len(on)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel")
    ap.add_argument("--render")
    ap.add_argument("--frame", type=float, default=1.80)
    ap.add_argument("--rows", default="1.60:1.74:0.01")
    ap.add_argument("--origin", type=float, default=None,
                    help="x of the midline in metres relative to the auto centre")
    ap.add_argument("--runs", action="store_true")
    args = ap.parse_args()

    path = args.panel or args.render
    alpha = load_alpha(path)
    if args.panel:
        rowf, mpp, midc = ref_map(alpha)
    else:
        rowf, mpp, midc = render_map(alpha, args.frame)
    if args.origin is not None:
        midc += args.origin / mpp

    a, b, step = [float(v) for v in args.rows.split(":")]
    print(f"# {path}  m/px {mpp*1000:.2f} mm  midcol {midc:.1f}")
    print("#    y      xmin      xmax     width" + ("     runs" if args.runs else ""))
    y = a
    while y <= b + 1e-9:
        r = int(round(rowf(y)))
        if 0 <= r < alpha.shape[0]:
            rr = runs(alpha[r])
            if rr:
                x0 = (rr[0][0] - midc) * mpp
                x1 = (rr[-1][1] - midc) * mpp
                s = f"{y:7.3f} {x0:9.4f} {x1:9.4f} {x1-x0:9.4f}"
                if args.runs:
                    s += "   " + " ".join(f"[{(p-midc)*mpp:.3f},{(q-midc)*mpp:.3f}]" for p, q in rr)
                print(s)
            else:
                print(f"{y:7.3f}        -         -         -")
        y += step


if __name__ == "__main__":
    main()
