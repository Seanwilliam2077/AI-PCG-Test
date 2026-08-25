"""Compare the model's visual hull with the reference's, in voxels.

A per-view silhouette IoU scores each projection on its own. Two solids can match
every projection separately and still be incompatible, because a silhouette says
nothing about how the views must agree in depth. The intersection of the cones
does: it is a 3D volume, and a model sitting outside the reference's hull cannot
be right regardless of how any single view scores, since no solid consistent with
those silhouettes occupies that space.

Both hulls are carved on the same 32^3 grid in the same metric box, from
silhouettes framed identically, so the voxel sets are directly comparable.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

SK = os.path.expanduser('~/.claude/skills/img2threejs')
RES, MASK = 32, 96
BMIN, BMAX = [-0.45, 0.0, -0.45], [0.45, 1.80, 0.45]


def mask_rows(path, metric_frame):
    """Binary rows in the metric box. `metric_frame` renders are already framed to
    1.80 m top to bottom, so they need no rescaling; reference panels do."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = (im[:, :, 3] > 128).astype(np.uint8)
    H, W = a.shape
    ys, xs = a.nonzero()
    if metric_frame:
        m_per_px = (BMAX[1] - BMIN[1]) / H
        floor_px = H
        cx = W / 2
    else:
        top, bot = ys.min(), ys.max()
        m_per_px = 1.72 / (bot - top + 1)
        floor_px = bot
        cx = (xs.min() + xs.max()) / 2
    out = np.zeros((MASK, MASK), np.uint8)
    for r in range(MASK):
        y_m = BMAX[1] - (r + 0.5) / MASK * (BMAX[1] - BMIN[1])
        sy = int(floor_px - y_m / m_per_px)
        if not (0 <= sy < H):
            continue
        for c in range(MASK):
            x_m = BMIN[0] + (c + 0.5) / MASK * (BMAX[0] - BMIN[0])
            sx = int(cx + x_m / m_per_px)
            if 0 <= sx < W and a[sy, sx]:
                out[r, c] = 1
    return [''.join('1' if v else '0' for v in row) for row in out]


def carve(front, side, metric, tag):
    desc = {'projection': 'orthographic', 'boundsSpace': 'component-local',
            'bounds': {'min': BMIN, 'max': BMAX}, 'resolution': RES,
            'triangleBudget': 393216,
            'views': [{'axis': 'front', 'confidence': 0.9, 'mask': mask_rows(front, metric)},
                      {'axis': 'side', 'confidence': 0.85, 'mask': mask_rows(side, metric)}]}
    dp, op = f'analysis/_hull_{tag}_desc.json', f'analysis/_hull_{tag}.json'
    json.dump(desc, open(dp, 'w'))
    subprocess.run([sys.executable, f'{SK}/forge/stage3_build/visual_hull.py', dp, '--out', op],
                   check=True, capture_output=True)
    return json.load(open(op, encoding='utf-8')), desc


def voxels(desc):
    """Re-derive the occupied voxel set from the same masks the carve consumed."""
    fm = np.array([[c == '1' for c in row] for row in desc['views'][0]['mask']])
    sm = np.array([[c == '1' for c in row] for row in desc['views'][1]['mask']])
    occ = np.zeros((RES, RES, RES), bool)
    for i in range(RES):       # x
        for j in range(RES):   # y
            for k in range(RES):  # z
                r = int((RES - 1 - j) * MASK / RES)
                if fm[r, int(i * MASK / RES)] and sm[r, int(k * MASK / RES)]:
                    occ[i, j, k] = True
    return occ


ref, ref_d = carve('ref/views/clay_2.png', 'ref/views/clay_0.png', False, 'ref')
ren, ren_d = carve('out/optimization-pass/render_yaw0.png',
                   'out/optimization-pass/render_yaw90.png', True, 'render')
A, B = voxels(ref_d), voxels(ren_d)
inter, union = (A & B).sum(), (A | B).sum()
vox_m3 = ((BMAX[0] - BMIN[0]) / RES) * ((BMAX[1] - BMIN[1]) / RES) * ((BMAX[2] - BMIN[2]) / RES)

print(f"reference hull  {ref['occupiedVoxelCount']:5d} voxels  "
      f"{ref['occupiedFraction']:.4f} of the box   {A.sum() * vox_m3 * 1000:.1f} L")
print(f"render hull     {ren['occupiedVoxelCount']:5d} voxels  "
      f"{ren['occupiedFraction']:.4f}                {B.sum() * vox_m3 * 1000:.1f} L")
print(f"\nvolumetric IoU        {inter / union:.4f}")
print(f"outside the reference {(B & ~A).sum() / max(1, B.sum()):.4f} of the model's own hull "
      f"({(B & ~A).sum() * vox_m3 * 1000:.1f} L)")
print(f"reference not filled  {(A & ~B).sum() / max(1, A.sum()):.4f} ({(A & ~B).sum() * vox_m3 * 1000:.1f} L)")
print('\nlimitations reported by the carver:')
for line in ref['limitations']:
    print('  -', line)
json.dump({'volumetricIou': round(inter / union, 4),
           'outsideReferenceFraction': round(float((B & ~A).sum() / max(1, B.sum())), 4),
           'referenceUnfilledFraction': round(float((A & ~B).sum() / max(1, A.sum())), 4),
           'referenceVoxels': int(A.sum()), 'renderVoxels': int(B.sum()),
           'resolution': RES, 'voxelMetres': round(((BMAX[1] - BMIN[1]) / RES), 4),
           'unconstrainedAxes': ref['unconstrainedAxes'],
           'limitations': ref['limitations']},
          open('analysis/hull_comparison.json', 'w'), indent=1)
