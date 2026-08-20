"""pants: read a fixed-frame preview straight off in world metres.

tools/preview.ts with --frame F centres the camera on (0, F/2, zmid) and scales
H px onto F metres, so a pixel maps back to world without any normalisation:

    y = F * (1 - row/H)          screen u = (col - W/2) / (H/F)

and at yaw 0 u = +x, 180 u = -x, 270 u = +z, 90 u = -z.

    python tools/pants_abs.py out/r3_pantsonly_img/preview_yaw180.png 180 \
        --y 0.90 0.85 0.80 0.75 0.70 0.65 0.60 0.55 0.50
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silhouette as S  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("png")
ap.add_argument("yaw", type=float)
ap.add_argument("--frame", type=float, default=1.80)
ap.add_argument("--y", nargs="+", type=float, required=True)
a = ap.parse_args()

_, alpha = S.load_rgba(a.png)
m = alpha > 127
H, W = m.shape
ppm = H / a.frame
axis = {0: "+x", 180: "-x", 270: "+z", 90: "-z"}.get(int(a.yaw) % 360, "?")
print("%s  %.1f px/m  screen u = %s" % (a.png, ppm, axis))
for y in a.y:
    row = int(round(H * (1.0 - y / a.frame)))
    if row < 0 or row >= H:
        print("  y %.3f  out of frame" % y)
        continue
    r = m[row]
    p = np.zeros(W + 2, np.int8)
    p[1:-1] = r
    d = np.diff(p)
    s = np.nonzero(d == 1)[0]
    e = np.nonzero(d == -1)[0]
    if s.size == 0:
        print("  y %.3f  empty" % y)
        continue
    parts = ["[%+.4f %+.4f]w%.4f" % ((i - W / 2) / ppm, (j - W / 2) / ppm,
                                     (j - i) / ppm) for i, j in zip(s, e)]
    print("  y %.3f  n=%d span %.4f  %s"
          % (y, len(s), (e[-1] - s[0]) / ppm, "  ".join(parts)))
