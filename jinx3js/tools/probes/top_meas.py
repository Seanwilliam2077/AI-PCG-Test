"""top: measure runs of a colour class across rows of a reference panel, in metres.

  python out/top_meas.py --panel ref/views/body_2.png --info
  python out/top_meas.py --panel ref/views/body_2.png --rows 1.38 1.39 1.40 --cls black
"""
import argparse
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(panel, height):
    im = cv2.imread(os.path.join(ROOT, panel), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3]
    ys, xs = np.nonzero(a > 8)
    top, bot = int(ys.min()), int(ys.max())
    ppm = (bot - top + 1) / height
    return im, a, top, bot, ppm


def classify(bgr):
    b, g, r = [bgr[..., i].astype(np.float32) for i in range(3)]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    cls = np.full(bgr.shape[:2], '?', dtype='<U6')
    cls[(v < 95)] = 'black'          # black cloth / dark leather
    cls[(v >= 95) & (r > g) & (r > b) & (s > 0.10)] = 'skin'
    cls[(v >= 95) & (b > r + 12)] = 'blue'   # hair
    return cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--panel', required=True)
    ap.add_argument('--height', type=float, default=1.715)
    ap.add_argument('--cx', type=float, default=None, help='centreline in px')
    ap.add_argument('--rows', type=float, nargs='*', default=[])
    ap.add_argument('--cls', default='black')
    ap.add_argument('--info', action='store_true')
    ap.add_argument('--alpha', action='store_true', help='report alpha silhouette runs')
    a = ap.parse_args()

    im, alpha, top, bot, ppm = load(a.panel, a.height)
    H, W = alpha.shape
    if a.info:
        print(f'panel {W}x{H} alpha rows {top}..{bot}  {ppm:.2f} px/m  ({1/ppm*1000:.3f} mm/px)')
        # centreline from the alpha bbox of the whole figure
        ys, xs = np.nonzero(alpha > 8)
        print(f'alpha cols {xs.min()}..{xs.max()}  mid {(xs.min()+xs.max())/2:.1f}')
        return
    cx = a.cx if a.cx is not None else None
    if cx is None:
        ys, xs = np.nonzero(alpha > 8)
        cx = (xs.min() + xs.max()) / 2
    cls = classify(im[:, :, :3])
    cls[alpha <= 8] = '.'
    for y in a.rows:
        row = int(round(bot - y * ppm))
        if row < 0 or row >= H:
            print(f'{y:.3f}  out of panel')
            continue
        m = (cls[row] == a.cls) if not a.alpha else (alpha[row] > 8)
        runs = []
        i = 0
        while i < W:
            if m[i]:
                j = i
                while j + 1 < W and m[j + 1]:
                    j += 1
                if j - i >= 1:
                    runs.append(((i - cx) / ppm, (j + 1 - cx) / ppm))
                i = j + 1
            else:
                i += 1
        print(f'y={y:.3f} row={row}  ' + '  '.join(f'[{p:+.4f}..{q:+.4f}]' for p, q in runs))


main()
