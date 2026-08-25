"""zapper: isolate the Zapper's pixels in a textured panel and report, per
height, how far the gun reaches beyond the rest of the figure.

The gun is the only brass / steel-blue mass on the thigh, so a hue+saturation
window separates it from the purple pants, the pale skin and the blue braids.
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="ref/views/body_0.png")
    ap.add_argument("--y0", type=float, default=0.52)
    ap.add_argument("--y1", type=float, default=0.92)
    ap.add_argument("--height", type=float, default=1.72)
    ap.add_argument("--dump", default=None)
    args = ap.parse_args()

    im = cv2.imread(os.path.join(ROOT, args.panel), cv2.IMREAD_UNCHANGED)
    bgr = im[:, :, :3]
    a = im[:, :, 3] > 8
    ys, _ = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    ppm = (bot - top + 1) / args.height

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)

    # OpenCV hue is 0..179.  brass ~ 15-30, steel/glass blue-grey ~ 95-115 with
    # low saturation, braid blue ~ 100-110 with HIGH saturation, pants purple
    # ~ 145-175, skin ~ 5-20 but very bright and low sat.
    brass = (h >= 12) & (h <= 32) & (s >= 70) & (v >= 60) & (v <= 210)
    steel = (h >= 90) & (h <= 125) & (s >= 20) & (s <= 110) & (v >= 60)
    gun = (brass | steel) & a

    # keep the largest connected blob only
    n, lab, stats, _ = cv2.connectedComponentsWithStats(gun.astype(np.uint8), 8)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        gun = lab == big
    st = stats[big]
    print(f"{args.panel}  {ppm:.1f} px/m   gun blob {st[cv2.CC_STAT_AREA]} px  "
          f"bbox x {st[0]}..{st[0]+st[2]-1}  y "
          f"{(bot-st[1])/ppm:.3f}..{(bot-(st[1]+st[3]-1))/ppm:.3f} m")

    print("   y      gun[left,right]        rest-of-figure[left,right]   (metres from panel left)")
    y = args.y1
    while y >= args.y0 - 1e-9:
        r = int(round(bot - y * ppm))
        g = np.nonzero(gun[r])[0]
        o = np.nonzero(a[r] & ~gun[r])[0]
        gs = f"[{g.min()/ppm:.3f},{g.max()/ppm:.3f}]" if len(g) else "     --     "
        os_ = f"[{o.min()/ppm:.3f},{o.max()/ppm:.3f}]" if len(o) else "     --     "
        print(f"  {y:.3f}  {gs}   {os_}")
        y -= 0.02

    if args.dump:
        out = bgr.copy()
        out[gun] = (0, 0, 255)
        cv2.imwrite(os.path.join(ROOT, args.dump), out)
        print("wrote", args.dump)


if __name__ == "__main__":
    main()
