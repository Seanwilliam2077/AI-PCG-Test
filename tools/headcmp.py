"""Put a head-only render beside the reference head at the same metres-per-pixel.

    python tools/headcmp.py --render out/gen_head_img/preview_yaw0.png --ref front
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Reference panels with the scale and origin needed to place them in metres.
# px_per_m and the pixel row of y = 1.584 (eye line) / column of x = 0 were read
# with tools/headcrop.py and the pixel grids in out/.
REFS = {
    # name: (file, px_per_m, eye_row, mid_col)
    "front": ("ref/views/head_1.png", 2646.0, 338.0, 425.0),
    "profile": ("ref/views/head_2.png", 2150.0, 320.0, 470.0),
}

EYE_Y = 1.584


def load(path):
    im = cv2.imread(os.path.join(ROOT, path), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        return (im[:, :, :3].astype(np.float32) * a + 30 * (1 - a)).astype(np.uint8), im[:, :, 3]
    return im, np.full(im.shape[:2], 255, np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--ref", default="front", choices=sorted(REFS))
    ap.add_argument("--out", default="out/headcmp.png")
    ap.add_argument("--ymin", type=float, default=1.46)
    ap.add_argument("--ymax", type=float, default=1.69)
    ap.add_argument("--zoom", type=float, default=2.6)
    args = ap.parse_args()

    ref_file, ppm, eye_row, mid_col = REFS[args.ref]
    ref, _ = load(ref_file)

    rnd, ra = load(args.render)
    ys, xs = np.nonzero(ra > 8)
    # The preview frames on the mesh bbox: H/2 is the bbox centre in y.
    # Recover px/m from the printed scale is awkward, so derive it from the
    # rendered bbox height against the known head extent.
    rh, rw = rnd.shape[:2]
    # preview.ts: scale = H / ((hi.y-lo.y)*1.06); centre at image centre.
    span = (ys.max() - ys.min()) + 1
    head_m = None
    # head shell runs cutY..crown; read it from the resolved spec
    import json
    spec = json.load(open(os.path.join(ROOT, "spec/resolved.json")))
    head_m = 1.6745 - spec["head"]["cutY"]
    rppm = span / head_m
    r_eye_row = ys.min() + (1.6745 - EYE_Y) * rppm
    r_mid_col = (xs.min() + xs.max()) / 2.0

    def crop(img, ppm_, eye_r, mid_c, halfw_m=0.105):
        top = int(eye_r - (args.ymax - EYE_Y) * ppm_)
        bot = int(eye_r + (EYE_Y - args.ymin) * ppm_)
        left = int(mid_c - halfw_m * ppm_)
        right = int(mid_c + halfw_m * ppm_)
        h, w = img.shape[:2]
        pad_t, pad_b = max(0, -top), max(0, bot - h)
        pad_l, pad_r = max(0, -left), max(0, right - w)
        img = cv2.copyMakeBorder(img, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=(30, 30, 30))
        top += pad_t; bot += pad_t; left += pad_l; right += pad_l
        c = img[top:bot, left:right]
        out_h = int((args.ymax - args.ymin) * 1000 * args.zoom)
        out_w = int(2 * halfw_m * 1000 * args.zoom)
        return cv2.resize(c, (out_w, out_h), interpolation=cv2.INTER_CUBIC)

    a = crop(ref, ppm, eye_row, mid_col)
    b = crop(rnd, rppm, r_eye_row, r_mid_col)
    gap = np.full((a.shape[0], 8, 3), 60, np.uint8)
    out = np.hstack([a, gap, b])

    # metre rulers across both
    for y_m in np.arange(1.46, 1.70, 0.02):
        py = int((args.ymax - y_m) * 1000 * args.zoom)
        if 0 <= py < out.shape[0]:
            cv2.line(out, (0, py), (out.shape[1], py), (0, 170, 235), 1)
            cv2.putText(out, f"{y_m:.2f}", (2, py - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 210, 255), 1)
    for panel in (0, a.shape[1] + 8):
        for k in (-2, -1, 0, 1, 2):
            px = panel + int((0.105 + k * 0.03) * 1000 * args.zoom)
            if 0 <= px < out.shape[1]:
                cv2.line(out, (px, 0), (px, out.shape[0]), (230, 130, 0), 1)

    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    cv2.imwrite(os.path.join(ROOT, args.out), out)
    print(args.out, out.shape[1], "x", out.shape[0], "| render px/m", round(rppm, 1))


if __name__ == "__main__":
    main()
