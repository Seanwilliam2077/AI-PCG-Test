"""top: IoU of the black-cloth mask between a render crop and the reference.

Both are resampled onto a common metre grid over the chest, so this measures the
garment's cut, not the figure's silhouette.

  python out/top_clothiou.py out/top_chest_yaw0.png
"""
import sys
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the window every out/top_chest_*.png crop was made with
CY0, CY1, CX0, CX1 = 1.19, 1.50, -0.16, 0.16
# the box the comparison is made over
BY0, BY1, BX0, BX1 = 1.232, 1.425, -0.099, 0.099
STEP = 0.001

REF = 'ref/views/body_2.png'
REF_PPM = 743.44
REF_CX = 195.0
REF_BOT = 1286


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
        if r < 0 or r >= H:
            continue
        cols = np.clip(np.round(colf(xs)).astype(int), 0, W - 1)
        out[j] = mask[r, cols]
    return out


def main():
    crop_path = sys.argv[1]
    crop = cv2.imread(os.path.join(ROOT, crop_path), cv2.IMREAD_UNCHANGED)
    ch, cw = crop.shape[:2]
    ppm_x = cw / (CX1 - CX0)
    ppm_y = ch / (CY1 - CY0)
    ren = sample(cloth_mask(crop[:, :, :3]),
                 lambda x: (x - CX0) * ppm_x,
                 lambda y: (CY1 - y) * ppm_y)

    im = cv2.imread(os.path.join(ROOT, REF), cv2.IMREAD_UNCHANGED)
    ref = sample(cloth_mask(im[:, :, :3], im[:, :, 3]),
                 lambda x: REF_CX + x * REF_PPM,
                 lambda y: REF_BOT - y * REF_PPM)

    inter = np.count_nonzero(ren & ref)
    uni = np.count_nonzero(ren | ref)
    print(f'{crop_path}: cloth IoU {inter / max(uni,1):.4f}  '
          f'ref px {np.count_nonzero(ref)}  render px {np.count_nonzero(ren)}  '
          f'(render/ref area {np.count_nonzero(ren)/max(np.count_nonzero(ref),1):.3f})')


main()
