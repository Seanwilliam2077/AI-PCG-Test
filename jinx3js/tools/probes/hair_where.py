"""hair scratch: where along y does the 'braid' (debraid-dropped) area live?"""
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


def bands(path, nb=17):
    nm = load(path)
    st = S.row_stats(nm)
    _, dm = S.debraid_stats(nm, st, braid_px=0.042 * S.FIG_H)
    d = nm.astype(np.int32) - dm.astype(np.int32)
    ppm = S.FIG_H / FIG_M
    rows = np.arange(S.TOP_Y, S.BASE_Y)
    ys = (S.BASE_Y - rows) / ppm
    per = d[rows].sum(axis=1)
    tot = float(nm.sum())
    out = []
    edges = np.linspace(0, FIG_M, nb + 1)
    for i in range(nb):
        sel = (ys >= edges[i]) & (ys < edges[i + 1])
        out.append(per[sel].sum() / tot)
    return out, edges, (float(d.sum()) / tot)


for p in sys.argv[1:]:
    v, e, tot = bands(p)
    print(f"{p}  braid_area_frac {tot:.4f}")
    for i, f in enumerate(v):
        if f > 0.0005:
            print(f"   y {e[i]:.2f}-{e[i+1]:.2f}  {f:.4f}  {'#' * int(f * 600)}")
