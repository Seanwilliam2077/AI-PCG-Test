"""Max width-over-height of the render against the reference, front and side."""
import sys

import cv2
import numpy as np


def prof(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3] > 128
    ys, _ = a.nonzero()
    top, bot = ys.min(), ys.max()
    H = bot - top + 1
    out = []
    for f in np.linspace(0.05, 0.95, 19):
        r = a[int(top + H * f)]
        out.append(0.0 if not r.any() else (r.nonzero()[0].max() - r.nonzero()[0].min() + 1) / H)
    return np.array(out)


d = sys.argv[1]
for tag, ref, ren in (('front', 'ref/views/body_2.png', f'{d}/render_yaw0.png'),
                      ('side ', 'ref/views/body_0.png', f'{d}/render_yaw90.png')):
    pr, pd = prof(ref), prof(ren)
    ok = (pr > 0.01) & (pd > 0.01)
    print(f'  {tag}  max ratio {pd.max() / pr.max():.3f}   band-mean {(pd[ok] / pr[ok]).mean():.3f}')
