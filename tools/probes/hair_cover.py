"""hair scratch: fraction of a view's silhouette covered by blue hair.

    python out/hair_cover.py ref/views/body_5.png out/r2_hair_all/preview_yaw180.png
"""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S  # noqa: E402

FIG_M = 1.72

for p in sys.argv[1:]:
    bgr, a = S.load_rgba(os.path.join(ROOT, p))
    m, _ = S.clean_mask(a)
    n = S.normalize(m, bgr)
    nm, rgb = n["mask"], n["rgb"]
    lab = cv2.cvtColor(rgb, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[:, :, 0] * 100.0 / 255.0
    b = lab[:, :, 2] - 128.0
    hair = nm & (b < -12)          # blue: negative b*
    ppm = S.FIG_H / FIG_M
    tot = float(nm.sum())
    print(f"{p}\n  hair px frac {hair.sum() / tot:.4f}   mean L over alpha {L[nm].mean():.1f}"
          f"   hair L {L[hair].mean() if hair.any() else -1:.1f}   skin/other L {L[nm & ~hair].mean():.1f}")
    for y0, y1 in [(1.40, 1.72), (1.00, 1.40), (0.60, 1.00), (0.20, 0.60)]:
        r0, r1 = int(S.BASE_Y - y1 * ppm), int(S.BASE_Y - y0 * ppm)
        sub, hs = nm[r0:r1], hair[r0:r1]
        print(f"    y {y0:.2f}-{y1:.2f}  hair frac {hs.sum() / max(1.0, float(sub.sum())):.4f}")
