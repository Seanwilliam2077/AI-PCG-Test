"""pants: red/green overlay of one reference panel against one render.

    python tools/pants_overlay.py ref/views/clay_4.png out/r3_pants_all/preview_yaw270.png out/pants_ov270.png

Both go through silhouette.normalize, then the render is shifted by the same
IoU-maximising offset compare.py uses, so what is left is shape error.
Green = reference only (we are missing it).  Magenta = render only (we invented
it).  Grey = agreement.  Height ticks every 0.05 t are drawn down the left.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silhouette as S  # noqa: E402


def load(path):
    _, a = S.load_rgba(path)
    m, _ = S.clean_mask(a)
    return S.normalize(m)["mask"]


ref = load(sys.argv[1])
ren = load(sys.argv[2])
out = sys.argv[3]
dx, dy, iou = S.refine_offset(ref, ren)
ren = S.shift(ren, dx, dy)
print("dx %d dy %d iou %.4f" % (dx, dy, iou))

img = np.zeros(ref.shape + (3,), np.uint8)
img[ref & ren] = (110, 110, 110)
img[ref & ~ren] = (60, 220, 60)
img[~ref & ren] = (220, 60, 220)

for k in range(0, 21):
    t = k * 0.05
    r = int(round(S.BASE_Y - 1 - t * (S.FIG_H - 1)))
    if 0 <= r < img.shape[0]:
        img[r, :] = np.maximum(img[r, :], (40, 40, 40))
        cv2.putText(img, "%.2f" % t, (2, r - 2), cv2.FONT_HERSHEY_PLAIN, 0.7,
                    (200, 200, 60), 1, cv2.LINE_AA)
cv2.imwrite(out, img)
print("wrote", out)
