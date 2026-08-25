"""boots_raw -- run decomposition of a preview PNG in its own metric frame.

tools/preview.ts with --frame F and --size WxH puts world y = F/2 at the image
centre, so px_per_m = H / F and world y = (H - row) / px_per_m exactly (the
floor lands on the bottom row).  Horizontal origin is the image centre column;
only widths and gaps are meaningful there, not absolute x.

    python out/boots_raw.py out/r3_boots_img/preview_yaw0.png --frame 1.8
"""
import argparse
import sys

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--frame", type=float, default=1.8)
    ap.add_argument("--y0", type=float, default=0.00)
    ap.add_argument("--y1", type=float, default=0.34)
    ap.add_argument("--step", type=float, default=0.02)
    ap.add_argument("--ys", type=float, nargs="*", default=None)
    args = ap.parse_args()

    for path in args.images:
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if im is None:
            print("cannot read %s" % path, file=sys.stderr)
            continue
        H, W = im.shape[:2]
        alpha = im[:, :, 3] if im.ndim == 3 and im.shape[2] == 4 else \
            np.full((H, W), 255, np.uint8)
        mask = alpha > 127
        ppm = H / args.frame
        cx = W / 2.0

        ys = args.ys
        if not ys:
            n = int(round((args.y1 - args.y0) / args.step)) + 1
            ys = [args.y0 + i * args.step for i in range(n)]

        print("== %s  (%dx%d, %.1f px/m)" % (path, W, H, ppm))
        print("   %6s %6s  %-52s %s" % ("y(m)", "full", "runs [x0,x1] m", "widths m"))
        for y in ys:
            row = int(round(H - y * ppm)) - 1
            if row < 0 or row >= H:
                continue
            r = mask[row]
            d = np.diff(np.concatenate(([0], r.astype(np.int8), [0])))
            s = np.nonzero(d == 1)[0]
            e = np.nonzero(d == -1)[0]
            if s.size == 0:
                print("   %6.3f  ---" % y)
                continue
            segs = " ".join("[%+.3f,%+.3f]" % ((a - cx) / ppm, (b - cx) / ppm)
                            for a, b in zip(s, e))
            wid = " ".join("%.3f" % ((b - a) / ppm) for a, b in zip(s, e))
            full = (e.max() - s.min()) / ppm
            print("   %6.3f %6.3f  %-52s %s" % (y, full, segs, wid))
        print()


if __name__ == "__main__":
    main()
