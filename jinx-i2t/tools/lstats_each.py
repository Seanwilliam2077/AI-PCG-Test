"""Per-view lightness inside the alpha, for a render directory."""
import glob
import re
import sys

import cv2
import numpy as np

pat = re.compile(r'yaw(\d+)')
for p in sorted(glob.glob(f'{sys.argv[1]}/render_yaw*.png'), key=lambda s: int(pat.search(s).group(1))):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    m = im[:, :, 3] > 128
    L = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2LAB)[:, :, 0][m].astype(np.float32) * 100 / 255
    print('  yaw%3s  L %5.2f  p10 %5.2f  p90 %5.2f' % (pat.search(p).group(1), L.mean(),
                                                       np.percentile(L, 10), np.percentile(L, 90)))
