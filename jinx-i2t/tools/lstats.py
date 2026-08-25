"""Six-yaw lightness statistics inside the alpha, as JSON."""
import glob
import json
import re
import sys

import cv2
import numpy as np

means, p10s, p90s = [], [], []
for p in sorted(glob.glob(f'{sys.argv[1]}/render_yaw*.png'),
                key=lambda s: int(re.search(r'yaw(\d+)', s).group(1))):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    m = im[:, :, 3] > 128
    L = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2LAB)[:, :, 0][m].astype(np.float32) * 100 / 255
    means.append(float(L.mean()))
    p10s.append(float(np.percentile(L, 10)))
    p90s.append(float(np.percentile(L, 90)))
print(json.dumps({'mean': sum(means) / len(means), 'p10': sum(p10s) / len(p10s),
                  'p90': sum(p90s) / len(p90s), 'spread': max(means) - min(means)}))
