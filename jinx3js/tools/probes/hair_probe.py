"""hair part scratch probe: per-row runs in metres + braid_area_frac for one image.

    python out/hair_probe.py ref/views/clay_0.png --ys 1.40 1.20 1.00 0.80 0.62 0.45 0.30 0.15
"""
import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S  # noqa: E402

FIG_M = 1.72  # sole to hair tip, same convention as tools/grid.py --metres


def load(path):
    bgr, a = S.load_rgba(os.path.join(ROOT, path))
    m = S.clean_mask(a)
    if isinstance(m, tuple):
        m = m[0]
    n = S.normalize(m, bgr)
    return n["mask"], n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("panel")
    ap.add_argument("--ys", type=float, nargs="*",
                    default=[1.45, 1.30, 1.15, 1.00, 0.85, 0.70, 0.55, 0.40, 0.25, 0.12])
    ap.add_argument("--height", type=float, default=FIG_M)
    args = ap.parse_args()

    nm, info = load(args.panel)
    st = S.row_stats(nm)
    dst, dm = S.debraid_stats(nm, st, braid_px=0.042 * S.FIG_H)
    af, ad = float(nm.sum()), float(dm.sum())
    ppm = S.FIG_H / args.height

    print(f"{args.panel}  area {af:.0f}px  debraid {ad:.0f}px  "
          f"braid_area_frac {(af - ad) / af:.4f}   ({ppm:.1f} px/m)")
    sr, sc, ec, w = st["_runs"]
    for y in args.ys:
        row = int(S.BASE_Y - y * ppm)
        sel = sr == row
        runs = [(float(a), float(b)) for a, b in zip(sc[sel], ec[sel])]
        if not runs:
            print(f"  y={y:.2f}  -")
            continue
        # positions relative to the leftmost pixel of this row, in metres
        x0 = runs[0][0]
        txt = "  ".join(f"[{(a - x0) / ppm:.3f},{(b - x0) / ppm:.3f}]w{(b - a) / ppm:.3f}"
                        for a, b in runs)
        print(f"  y={y:.2f}  n={len(runs)}  {txt}")


if __name__ == "__main__":
    main()
