"""pants: per-row run probe on a normalised silhouette.

    python tools/pants_probe.py --a ref/views/clay_4.png --b out/r3_pants_all/preview_yaw270.png \
        --t 0.60 0.55 0.512 0.47 0.438 0.40 0.35 0.30 0.25 0.188

Both images are put through silhouette.normalize (figure height -> 1024 px,
centroid on CENTER_X, soles on BASE_Y-1), so a width in %H means the same thing
here as it does in tools/compare.py.  Runs are printed in %H offsets from the
canvas centre so the two can be laid side by side.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silhouette as S  # noqa: E402

FIG_M = 1.72


def load(path):
    bgr, a = S.load_rgba(path)
    m, _ = S.clean_mask(a)
    n = S.normalize(m, bgr)
    return n["mask"]


def row_of(t):
    return int(round(S.BASE_Y - 1 - t * (S.FIG_H - 1)))


def describe(mask, t):
    r = row_of(t)
    if r < 0 or r >= mask.shape[0]:
        return "row out of canvas"
    row = mask[r]
    idx = np.nonzero(row)[0]
    if idx.size == 0:
        return "empty"
    p = np.zeros(len(row) + 2, np.int8)
    p[1:-1] = row
    d = np.diff(p)
    s = np.nonzero(d == 1)[0]
    e = np.nonzero(d == -1)[0]
    pct = 100.0 / (S.FIG_H - 1)
    parts = []
    for a, b in zip(s, e):
        parts.append("[%+6.2f %+6.2f]w%5.2f" % ((a - S.CENTER_X) * pct,
                                                (b - S.CENTER_X) * pct,
                                                (b - a) * pct))
    core = max(b - a for a, b in zip(s, e)) * pct
    full = (e[-1] - s[0]) * pct
    return "n=%d core=%5.2f full=%5.2f  %s" % (len(s), core, full, " ".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b")
    ap.add_argument("--t", nargs="+", type=float, required=True)
    ap.add_argument("--runs", action="store_true",
                    help="also scan every row and report where run count changes")
    args = ap.parse_args()

    A = load(args.a)
    B = load(args.b) if args.b else None
    print("A = %s" % args.a)
    if B is not None:
        print("B = %s" % args.b)
    print("%-7s %-6s %s" % ("t", "y(m)", "runs"))
    for t in args.t:
        y = t * FIG_M
        print("%-7.3f %-6.3f A  %s" % (t, y, describe(A, t)))
        if B is not None:
            print("%-7s %-6s B  %s" % ("", "", describe(B, t)))

    if args.runs:
        for name, M in (("A", A), ("B", B)):
            if M is None:
                continue
            st = S.row_stats(M)
            nr = st["nrun"]
            print("\n%s run-count transitions (t, y):" % name)
            prev = 0
            for r in range(S.TOP_Y, S.BASE_Y):
                if nr[r] != prev:
                    t = (S.BASE_Y - 1 - r) / float(S.FIG_H - 1)
                    print("   row %4d  t %.4f  y %.4f  runs %d -> %d"
                          % (r, t, t * FIG_M, prev, nr[r]))
                    prev = nr[r]


if __name__ == "__main__":
    main()
