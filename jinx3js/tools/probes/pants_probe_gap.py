"""pants: sample alpha and colour along a row of a reference panel, in metres."""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
panel = sys.argv[1]
ys = [float(a) for a in sys.argv[2:]] or [0.58]
H_M = 1.72

im = cv2.imread(os.path.join(ROOT, panel), cv2.IMREAD_UNCHANGED)
alpha = im[:, :, 3]
rows, _ = np.nonzero(alpha > 0)
top, bot = int(rows.min()), int(rows.max())
ppm = (bot - top) / H_M
cols = np.nonzero(alpha[:, :].max(axis=0) > 0)[0]
# figure centre by centroid of the whole mask, matching silhouette.normalize
yy, xx = np.nonzero(alpha > 127)
cx = xx.mean()
print(f"{panel}: rows {top}..{bot}  {ppm:.1f} px/m  centroid col {cx:.1f}")

for y in ys:
    r = int(round(bot - y * ppm))
    a = alpha[r]
    print(f"\n--- y = {y:.3f} m (row {r}) ---")
    xs = np.nonzero(a > 127)[0]
    if not len(xs):
        print("  empty")
        continue
    for c in range(xs.min(), xs.max() + 1, 4):
        mx = (c - cx) / ppm
        b, g, rr = im[r, c, :3]
        print(f"   x={mx:+.4f}  a={a[c]:3d}  rgb=({rr:3d},{g:3d},{b:3d})")
