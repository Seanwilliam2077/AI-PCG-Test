"""top: crop a reference panel in metre coords with a centreline + tick marks."""
import argparse
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument('--panel', required=True)
ap.add_argument('--y0', type=float, required=True)
ap.add_argument('--y1', type=float, required=True)
ap.add_argument('--x0', type=float, default=-0.16)
ap.add_argument('--x1', type=float, default=0.16)
ap.add_argument('--cx', type=float, default=195.0, help='centreline px')
ap.add_argument('--height', type=float, default=1.715)
ap.add_argument('--zoom', type=int, default=4)
ap.add_argument('--grid', type=float, default=0.02)
ap.add_argument('--out', default='out/top_ref.png')
a = ap.parse_args()

im = cv2.imread(os.path.join(ROOT, a.panel), cv2.IMREAD_UNCHANGED)
al = im[:, :, 3].astype(np.float32) / 255.0
rgb = (im[:, :, :3].astype(np.float32) * al[..., None] + 255 * (1 - al[..., None])).astype(np.uint8)
H, W = rgb.shape[:2]
ys, xs = np.nonzero(im[:, :, 3] > 8)
bot = int(ys.max())
ppm = (bot - int(ys.min()) + 1) / a.height

row = lambda y: int(round(bot - y * ppm))
col = lambda x: int(round(a.cx + x * ppm))

crop = rgb[row(a.y1):row(a.y0), col(a.x0):col(a.x1)].copy()
z = a.zoom
crop = cv2.resize(crop, (crop.shape[1] * z, crop.shape[0] * z), interpolation=cv2.INTER_NEAREST)

# horizontal metre lines
y = a.y0
while y <= a.y1 + 1e-9:
    r = int(round((row(y) - row(a.y1)) * z))
    if 0 <= r < crop.shape[0]:
        cv2.line(crop, (0, r), (crop.shape[1], r), (0, 190, 255), 1)
        cv2.putText(crop, f'{y:.3f}', (2, max(10, r - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 140, 210), 1)
    y += a.grid
x = a.x0
while x <= a.x1 + 1e-9:
    c = int(round((col(x) - col(a.x0)) * z))
    if 0 <= c < crop.shape[1]:
        colr = (255, 0, 0) if abs(x) < 1e-6 else (255, 150, 60)
        cv2.line(crop, (c, 0), (c, crop.shape[0]), colr, 1)
        cv2.putText(crop, f'{x:+.02f}', (c + 2, crop.shape[0] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 90, 0), 1)
    x += a.grid

cv2.imwrite(os.path.join(ROOT, a.out), crop)
print(a.out, crop.shape[1], 'x', crop.shape[0], f'{ppm:.2f} px/m  cx={a.cx}')
