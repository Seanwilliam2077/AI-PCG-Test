"""top: visual diff of the black-cloth mask, render vs reference.
green = both, red = reference only, blue = render only."""
import sys
import os
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CY0, CY1, CX0, CX1 = 1.19, 1.50, -0.16, 0.16
BY0, BY1, BX0, BX1 = 1.232, 1.425, -0.099, 0.099
STEP = 0.001
REF = 'ref/views/body_2.png'
REF_PPM, REF_CX, REF_BOT = 743.44, 195.0, 1286


def cloth_mask(bgr, alpha=None):
    b, g, r = [bgr[..., i].astype(np.float32) for i in range(3)]
    v = np.maximum(np.maximum(r, g), b)
    m = (v < 105) & ((b - r) < 30)
    if alpha is not None:
        m &= alpha > 8
    return m


def sample(mask, colf, rowf):
    xs = np.arange(BX0, BX1 + 1e-9, STEP)
    ys = np.arange(BY0, BY1 + 1e-9, STEP)
    out = np.zeros((len(ys), len(xs)), bool)
    H, W = mask.shape
    for j, y in enumerate(ys):
        r = int(round(rowf(y)))
        if 0 <= r < H:
            out[j] = mask[r, np.clip(np.round(colf(xs)).astype(int), 0, W - 1)]
    return out


crop = cv2.imread(os.path.join(ROOT, sys.argv[1]), cv2.IMREAD_UNCHANGED)
ch, cw = crop.shape[:2]
ren = sample(cloth_mask(crop[:, :, :3]),
             lambda x: (x - CX0) * (cw / (CX1 - CX0)),
             lambda y: (CY1 - y) * (ch / (CY1 - CY0)))
im = cv2.imread(os.path.join(ROOT, REF), cv2.IMREAD_UNCHANGED)
ref = sample(cloth_mask(im[:, :, :3], im[:, :, 3]),
             lambda x: REF_CX + x * REF_PPM,
             lambda y: REF_BOT - y * REF_PPM)
vis = np.zeros(ren.shape + (3,), np.uint8)
vis[ren & ref] = (60, 200, 60)
vis[ref & ~ren] = (60, 60, 235)
vis[ren & ~ref] = (235, 160, 60)
vis = vis[::-1]
vis = cv2.resize(vis, (vis.shape[1] * 3, vis.shape[0] * 3), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(os.path.join(ROOT, sys.argv[2]), vis)
print(sys.argv[2], vis.shape, 'green=both  red=ref only  blue=render only')
