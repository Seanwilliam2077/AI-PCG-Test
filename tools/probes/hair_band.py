"""hair scratch: silhouette area + x-extent of a height band, ref vs render.

    python out/hair_band.py 1.44 1.73 ref/views/clay_2.png out/r2_hair_all/preview_yaw0.png
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S  # noqa: E402

FIG_M = 1.72


def load(path):
    bgr, a = S.load_rgba(os.path.join(ROOT, path))
    m, _ = S.clean_mask(a)
    return S.normalize(m, bgr)["mask"]


y0, y1 = float(sys.argv[1]), float(sys.argv[2])
ppm = S.FIG_H / FIG_M
r0 = int(S.BASE_Y - y1 * ppm)
r1 = int(S.BASE_Y - y0 * ppm)
for p in sys.argv[3:]:
    nm = load(p)
    sub = nm[r0:r1]
    area = sub.sum() / ppm ** 2
    # centroid x and extent, in metres, about the whole figure's centroid
    ys, xs = np.nonzero(nm)
    cx = xs.mean()
    ys2, xs2 = np.nonzero(sub)
    print(f"{p}\n  band y {y0:.2f}..{y1:.2f}  area {area * 1e4:7.1f} cm^2"
          f"  cx {(xs2.mean() - cx) / ppm:+.4f}"
          f"  xmin {(xs2.min() - cx) / ppm:+.4f}  xmax {(xs2.max() - cx) / ppm:+.4f}"
          f"  ymax {(S.BASE_Y - ys2.min()) / ppm:.4f}")
    for y in np.arange(y1, y0 - 1e-6, -0.02):
        row = int(S.BASE_Y - y * ppm)
        r = np.nonzero(nm[row])[0]
        if r.size == 0:
            print(f"    y {y:.2f}   -")
            continue
        print(f"    y {y:.2f}  [{(r.min() - cx) / ppm:+.4f} .. {(r.max() - cx) / ppm:+.4f}]"
              f"  w {(r.max() - r.min()) / ppm:.4f}  fill {r.size / ppm:.4f}")
