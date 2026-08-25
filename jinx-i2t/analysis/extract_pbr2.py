"""Crop one evidence patch per material from the SEARCHED rects, then extract PBR.

Supersedes analysis/extract_pbr.py, whose rectangles were hand-placed as panel
fractions. The stage1 sweep found 15 of 20 of them sampling the wrong pixels --
every head material on bare cheek, `nailTeal` only 30.4 percent inside the
silhouette, `eye.png` and `sclera.png` byte-identical. Rects now come from
analysis/recut_pbr.py, which searches an anatomical band for the patch whose
median matches a measured target, and reports its CIE Lab error so a bad crop is
visible instead of silent.

Crops are padded out from the located rect rather than upscaled from it: the
extractor wants at least 96 px, and interpolating a 5 px patch up to 96 invents
detail the reference never had. Padding keeps every pixel a real sample and lets
the extractor's own confidence reflect how little evidence there is.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

SK = os.path.expanduser('~/.claude/skills/img2threejs')
EXTRACT = f'{SK}/forge/stage1_intake/extract_pbr_evidence.py'
SPEC = 'object-sculpt-spec.json'
MIN_SIDE = 96
os.makedirs('pbr/crops', exist_ok=True)

rects = json.load(open('analysis/pbr_rects.json', encoding='utf-8'))
panels = {}
results = []

for mat, r in rects.items():
    panel = r['panel']
    if panel not in panels:
        panels[panel] = cv2.imread(f'ref/views/{panel}.png', cv2.IMREAD_UNCHANGED)
    src = panels[panel]
    H, W = src.shape[:2]
    # grow the located rect symmetrically until it reaches the extractor's minimum,
    # clamped to the panel, keeping every pixel a genuine sample
    cx, cy = r['x'] + r['w'] // 2, r['y'] + r['h'] // 2
    half = max(MIN_SIDE // 2, r['w'] // 2, r['h'] // 2)
    x0, x1 = max(0, cx - half), min(W, cx + half)
    y0, y1 = max(0, cy - half), min(H, cy + half)
    crop = src[y0:y1, x0:x1].copy()
    alpha_frac = float((crop[:, :, 3] > 128).mean()) if crop.shape[2] == 4 else 1.0
    # The located rect was checked for matting holes, but growing it out to the
    # extractor's 96 px minimum can pull them back in -- and a pure-white hole
    # baked into an albedo map renders as a white blob on the braid. Inpaint them
    # from their surroundings rather than letting them travel as evidence.
    holes = (crop[:, :, :3].min(axis=2) > 248).astype(np.uint8)
    if crop.shape[2] == 4:
        holes |= (crop[:, :, 3] <= 128).astype(np.uint8)
    if holes.any():
        crop[:, :, :3] = cv2.inpaint(crop[:, :, :3].copy(), holes, 3, cv2.INPAINT_TELEA)
        if crop.shape[2] == 4:
            crop[:, :, 3] = 255
    if crop.shape[2] == 4:
        a = crop[:, :, 3:4].astype(float) / 255.0
        rgb = crop[:, :, :3].astype(float)
        inside = rgb.reshape(-1, 3)[a.reshape(-1) > 0.5]
        fill = inside.mean(axis=0) if len(inside) else np.array([128.0, 128, 128])
        crop = (rgb * a + fill * (1 - a)).astype('uint8')
    if min(crop.shape[:2]) < MIN_SIDE:
        pad_y = max(0, MIN_SIDE - crop.shape[0])
        pad_x = max(0, MIN_SIDE - crop.shape[1])
        crop = cv2.copyMakeBorder(crop, pad_y // 2, pad_y - pad_y // 2,
                                  pad_x // 2, pad_x - pad_x // 2, cv2.BORDER_REFLECT_101)
    path = f'pbr/crops/{mat}.png'
    cv2.imwrite(path, crop)

    cmd = [sys.executable, EXTRACT, path, '--out-dir', f'pbr/{mat}', '--material-id', mat,
           '--spec', SPEC, '--in-place', '--report', f'pbr/{mat}_report.json']
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        p = subprocess.run(cmd + ['--allow-low-confidence'], capture_output=True, text=True)
        status = 'low-confidence' if p.returncode == 0 else f'FAILED rc={p.returncode}'
    else:
        status = 'ok'
    conf = None
    rp = f'pbr/{mat}_report.json'
    if os.path.exists(rp):
        try:
            conf = json.load(open(rp, encoding='utf-8')).get('confidence')
        except Exception:
            pass
    results.append((mat, status, conf, r['dist'], alpha_frac))
    if status.startswith('FAILED'):
        print(f'  {mat}: {(p.stderr or p.stdout).strip()[:200]}')

print(f'{"material":13s} {"status":16s} {"conf":>6s} {"dLab":>6s} {"alpha":>6s}')
for mat, status, conf, dist, af in results:
    print(f'{mat:13s} {status:16s} {conf if conf is not None else "-":>6} {dist:6.1f} {af:6.2f}')

# the crops must not be duplicates of each other any more
import hashlib
seen = {}
for mat in rects:
    h = hashlib.md5(open(f'pbr/crops/{mat}.png', 'rb').read()).hexdigest()[:10]
    seen.setdefault(h, []).append(mat)
dupes = {h: m for h, m in seen.items() if len(m) > 1}
print('\nduplicate crops:', dupes if dupes else 'none')
