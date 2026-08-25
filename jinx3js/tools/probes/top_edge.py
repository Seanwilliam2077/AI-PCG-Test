"""top: trace the black-cloth region of a reference panel, in metres.

  python out/top_edge.py --panel ref/views/body_2.png --cx 195 --y0 1.22 --y1 1.44
"""
import argparse
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument('--panel', required=True)
ap.add_argument('--cx', type=float, default=195.0)
ap.add_argument('--height', type=float, default=1.715)
ap.add_argument('--y0', type=float, default=1.22)
ap.add_argument('--y1', type=float, default=1.44)
ap.add_argument('--step', type=float, default=0.01)
ap.add_argument('--xlim', type=float, default=0.13)
ap.add_argument('--mask', default='out/top_mask.png')
a = ap.parse_args()

im = cv2.imread(os.path.join(ROOT, a.panel), cv2.IMREAD_UNCHANGED)
al = im[:, :, 3]
ys, xs = np.nonzero(al > 8)
top, bot = int(ys.min()), int(ys.max())
ppm = (bot - top + 1) / a.height
b, g, r = [im[:, :, i].astype(np.float32) for i in range(3)]
v = np.maximum(np.maximum(r, g), b)
# black garment cloth: dark, and not blue-dominant (that is hair)
cloth = (v < 105) & ((b - r) < 30) & (al > 8)
# brass: warm, mid-bright, r>g>b
brass = (r > 110) & (r > b + 45) & (g > b + 15) & (al > 8)
# canvas lace: pale olive
canv = (v > 120) & (g > b + 25) & (abs(r - g) < 45) & (r < 210) & (al > 8)

row = lambda y: int(round(bot - y * ppm))
mcol = lambda px: (px - a.cx) / ppm

print(f'{a.panel}  {ppm:.2f} px/m  cx={a.cx}')
print('  y      cloth runs (m)                                   | brass runs')
y = a.y0
while y <= a.y1 + 1e-9:
    rr = row(y)
    out = []
    for name, m in (('cloth', cloth), ('brass', brass)):
        line = m[rr]
        runs = []
        i = 0
        while i < len(line):
            if line[i]:
                j = i
                while j + 1 < len(line) and line[j + 1]:
                    j += 1
                if j - i >= 1:
                    p, q = mcol(i), mcol(j + 1)
                    if p < a.xlim and q > -a.xlim:
                        runs.append((max(p, -a.xlim), min(q, a.xlim)))
                i = j + 1
            else:
                i += 1
        out.append(' '.join(f'[{p:+.3f}..{q:+.3f}]' for p, q in runs))
    print(f'{y:.3f}  {out[0]:<50s} | {out[1]}')
    y += a.step

vis = np.zeros(im.shape[:2] + (3,), np.uint8)
vis[cloth] = (255, 255, 255)
vis[brass] = (0, 200, 255)
vis[canv] = (0, 255, 0)
r0, r1 = row(a.y1), row(a.y0)
c0, c1 = int(a.cx - a.xlim * ppm), int(a.cx + a.xlim * ppm)
sub = vis[r0:r1, c0:c1]
sub = cv2.resize(sub, (sub.shape[1] * 3, sub.shape[0] * 3), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(os.path.join(ROOT, a.mask), sub)
print('mask ->', a.mask)
