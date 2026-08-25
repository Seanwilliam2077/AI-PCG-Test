"""Carve the reference's visual hull and use it as what it is: an upper bound.

`visual_hull.py` is the one geometry tool in the skill that consumes the reference
silhouettes directly, and its own docstring is emphatic about the limit: a visual
hull is the INTERSECTION OF SILHOUETTE CONES, so it can only ever be an upper
bound on the true shape, and it can never represent a concavity that does not
break the silhouette from some supplied view. Resolution is capped at 32, which
over a 1.8 m figure is 56 mm voxels -- far too coarse to build from.

So it is not used here to make geometry. It is used to answer a question nothing
else in the pipeline answers: how much of this model sits OUTSIDE the volume the
reference's own silhouettes permit? Anything outside the hull cannot be right, no
matter how the silhouette IoU scores, because no solid consistent with those
silhouettes occupies that space.

Front and side masks are resampled into a shared metric box so the two cones are
in the same frame. There is no top view in the reference sheet, so the hull is the
intersection of two prisms and the tool reports the vertical axis as
unconstrained -- true, and the reason the result is read as a bound and not a
shape.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

SK = os.path.expanduser('~/.claude/skills/img2threejs')
RES = 32
BOUNDS_MIN = [-0.45, 0.0, -0.45]
BOUNDS_MAX = [0.45, 1.80, 0.45]
MASK = 96


def mask_rows(path, flip_x=False):
    """Resample one matted view into the metric box as binary rows, top-down."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = (im[:, :, 3] > 128).astype(np.uint8)
    ys, xs = a.nonzero()
    top, bot = ys.min(), ys.max()
    # the figure spans floor .. 1.80 m of the box; centre it horizontally on its
    # own silhouette centroid so front and side share an origin
    h_px = bot - top + 1
    m_per_px = 1.72 / h_px * (1.80 / 1.80)
    cx = (xs.min() + xs.max()) / 2
    out = np.zeros((MASK, MASK), np.uint8)
    for r in range(MASK):
        # row 0 is the top of the box (y = BOUNDS_MAX)
        y_m = BOUNDS_MAX[1] - (r + 0.5) / MASK * (BOUNDS_MAX[1] - BOUNDS_MIN[1])
        src_y = int(bot - y_m / m_per_px)
        if not (0 <= src_y < a.shape[0]):
            continue
        for c in range(MASK):
            x_m = BOUNDS_MIN[0] + (c + 0.5) / MASK * (BOUNDS_MAX[0] - BOUNDS_MIN[0])
            src_x = int(cx + x_m / m_per_px * (-1 if flip_x else 1))
            if 0 <= src_x < a.shape[1] and a[src_y, src_x]:
                out[r, c] = 1
    return [''.join('1' if v else '0' for v in row) for row in out]


descriptor = {
    'projection': 'orthographic',
    'boundsSpace': 'component-local',
    'bounds': {'min': BOUNDS_MIN, 'max': BOUNDS_MAX},
    'resolution': RES,
    # the validator computes the budget a resolution demands and refuses a smaller
    # one -- 6 * res^2 * 2 * 64 for res 32; declaring less would let the carve be
    # silently truncated
    'triangleBudget': 393216,
    'views': [
        {'axis': 'front', 'confidence': 0.9, 'mask': mask_rows('ref/views/clay_2.png')},
        {'axis': 'side', 'confidence': 0.85, 'mask': mask_rows('ref/views/clay_0.png')},
    ],
}
json.dump(descriptor, open('analysis/visual_hull_descriptor.json', 'w'))

p = subprocess.run([sys.executable, f'{SK}/forge/stage3_build/visual_hull.py',
                    'analysis/visual_hull_descriptor.json',
                    '--out', 'analysis/visual_hull.json', '--json'],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print(p.stdout[:900] or p.stderr[:900])
