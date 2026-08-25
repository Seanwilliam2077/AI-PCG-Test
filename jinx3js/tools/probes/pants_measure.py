"""pants: read horizontal silhouette runs off a panel or a render, at heights in metres.

    python out/pants_measure.py --panel ref/views/clay_5.png --ys 0.50 0.58 0.66 0.71 0.75 0.80 0.86
    python out/pants_measure.py --render out/r2_pants_all/preview_yaw180.png --ys ...
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silhouette as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--ys", type=float, nargs="+", required=True)
    ap.add_argument("--height", type=float, default=1.72)
    args = ap.parse_args()

    path = args.panel or args.render
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    _bgr, alpha = S.load_rgba(p)
    mask, _info = S.clean_mask(alpha)
    norm = S.normalize(mask)["mask"]

    # normalize() puts the figure bbox from row TOP_Y to BASE_Y-1, FIG_H tall,
    # and puts the silhouette's centroid on CENTER_X.
    px_per_m = (S.FIG_H - 1) / args.height
    cx = float(S.CENTER_X)

    print(f"{path}  fig height {args.height} m  ->  {px_per_m:.2f} px/m   centre col {cx:.1f}")
    print(f"{'y(m)':>7} {'t':>6} {'runs (metres from bbox centre)':<52} {'core %H':>8}")
    for y in args.ys:
        row = int(round(S.BASE_Y - 1 - y * px_per_m))
        if row < 0 or row >= norm.shape[0]:
            print(f"{y:7.3f}  out of canvas")
            continue
        line = norm[row]
        idx = np.nonzero(line)[0]
        runs = []
        if len(idx):
            brk = np.nonzero(np.diff(idx) > 1)[0]
            starts = np.concatenate(([idx[0]], idx[brk + 1]))
            ends = np.concatenate((idx[brk], [idx[-1]]))
            for a, b in zip(starts, ends):
                if b - a < 2:
                    continue
                runs.append(((a - cx) / px_per_m, (b + 1 - cx) / px_per_m))
        txt = "  ".join(f"[{a:+.4f},{b:+.4f}]w={b-a:.4f}" for a, b in runs)
        core = max((b - a for a, b in runs), default=0.0)
        t = y / args.height
        print(f"{y:7.3f} {t:6.3f} {txt:<52} {100*core/args.height:8.2f}")


if __name__ == "__main__":
    main()
