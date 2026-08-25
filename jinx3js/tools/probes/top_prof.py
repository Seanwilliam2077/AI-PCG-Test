"""top: per-column top/bottom edge of the black-cloth mask, in metres."""
import argparse
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument('--panel', required=True)
ap.add_argument('--cx', type=float, default=195.0)
ap.add_argument('--height', type=float, default=1.715)
ap.add_argument('--ylo', type=float, default=1.20)
ap.add_argument('--yhi', type=float, default=1.44)
ap.add_argument('--x0', type=float, default=-0.10)
ap.add_argument('--x1', type=float, default=0.10)
ap.add_argument('--step', type=float, default=0.005)
a = ap.parse_args()

im = cv2.imread(os.path.join(ROOT, a.panel), cv2.IMREAD_UNCHANGED)
al = im[:, :, 3]
ys, xs = np.nonzero(al > 8)
top, bot = int(ys.min()), int(ys.max())
ppm = (bot - top + 1) / a.height
b, g, r = [im[:, :, i].astype(np.float32) for i in range(3)]
v = np.maximum(np.maximum(r, g), b)
cloth = (v < 105) & ((b - r) < 30) & (al > 8)

row = lambda y: int(round(bot - y * ppm))
print(f'  x      botY    topY    (cloth column extent, {ppm:.1f} px/m)')
x = a.x0
while x <= a.x1 + 1e-9:
    c = int(round(a.cx + x * ppm))
    col = cloth[row(a.yhi):row(a.ylo), c]
    idx = np.nonzero(col)[0]
    if len(idx) == 0:
        print(f'{x:+.3f}   --      --')
    else:
        ytop = a.yhi - idx.min() / ppm
        ybot = a.yhi - idx.max() / ppm
        print(f'{x:+.3f}  {ybot:.4f}  {ytop:.4f}')
    x += a.step
