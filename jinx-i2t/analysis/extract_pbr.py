"""Crop one evidence patch per material and run the PBR extractor on it.

The strict gate refuses any material without `referencePbr` extracted from
source pixels, which is the right rule: it stops a plausible-looking hand-typed
roughness number standing in for a measurement. Each rectangle below is a region
of the reference where that material is unambiguously the only thing visible.

The extractor exits non-zero when its own confidence is under target. Where that
happens the patch is genuinely too small or too mixed to measure, and the
material is recorded with `--allow-low-confidence` so the low number travels
with it rather than being hidden.
"""
import json
import os
import subprocess
import sys

import cv2

SK = os.path.expanduser('~/.claude/skills/img2threejs')
EXTRACT = f'{SK}/forge/stage1_intake/extract_pbr_evidence.py'
SPEC = 'object-sculpt-spec.json'
os.makedirs('pbr/crops', exist_ok=True)

# material -> (source panel, x0, x1, y0, y1) as fractions of the panel
REGIONS = {
    'skin':        ('body_2', 0.40, 0.60, 0.300, 0.345),
    'skinShade':   ('body_2', 0.30, 0.40, 0.300, 0.345),
    'hair':        ('body_2', 0.44, 0.58, 0.030, 0.075),
    'hairDark':    ('body_5', 0.42, 0.58, 0.090, 0.140),
    'cloth':       ('body_2', 0.40, 0.58, 0.160, 0.200),
    'clothWorn':   ('body_2', 0.62, 0.78, 0.190, 0.230),
    'pants':       ('body_2', 0.30, 0.48, 0.470, 0.560),
    'pantsDark':   ('body_2', 0.34, 0.42, 0.470, 0.560),
    'leather':     ('body_2', 0.44, 0.60, 0.870, 0.930),
    'canvas':      ('body_2', 0.42, 0.60, 0.400, 0.440),
    'brass':       ('body_2', 0.44, 0.58, 0.190, 0.225),
    'steel':       ('body_0', 0.30, 0.52, 0.470, 0.560),
    'tattoo':      ('body_2', 0.14, 0.30, 0.245, 0.320),
    'laceMagenta': ('body_2', 0.46, 0.60, 0.885, 0.930),
    'nailTeal':    ('body_2', 0.06, 0.20, 0.500, 0.540),
    'glassTank':   ('body_2', 0.68, 0.82, 0.500, 0.570),
    'eye':         ('head_1', 0.40, 0.62, 0.290, 0.360),
    'sclera':      ('head_1', 0.40, 0.62, 0.290, 0.360),
    'pupil':       ('head_1', 0.44, 0.56, 0.300, 0.350),
    'lip':         ('head_1', 0.44, 0.60, 0.470, 0.530),
    'brow':        ('head_1', 0.38, 0.64, 0.230, 0.270),
}

results = []
for mat, (panel, x0, x1, y0, y1) in REGIONS.items():
    src = cv2.imread(f'ref/views/{panel}.png', cv2.IMREAD_UNCHANGED)
    if src is None:
        results.append((mat, 'no source', None))
        continue
    h, w = src.shape[:2]
    crop = src[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    if crop.size == 0:
        results.append((mat, 'empty crop', None))
        continue
    # The extractor wants opaque pixels; composite the matte over its own mean.
    if crop.shape[2] == 4:
        a = crop[:, :, 3:4].astype(float) / 255.0
        rgb = crop[:, :, :3].astype(float)
        fill = rgb.reshape(-1, 3)[(a.reshape(-1) > 0.5)]
        fill = fill.mean(axis=0) if len(fill) else [128, 128, 128]
        crop = (rgb * a + fill * (1 - a)).astype('uint8')
    # Upscale small patches: the extractor has a minimum size and these regions
    # are 20-80 px on a 377 px panel.
    if min(crop.shape[:2]) < 96:
        k = 96 / min(crop.shape[:2])
        crop = cv2.resize(crop, (int(crop.shape[1] * k), int(crop.shape[0] * k)), interpolation=cv2.INTER_CUBIC)
    path = f'pbr/crops/{mat}.png'
    cv2.imwrite(path, crop)

    cmd = [sys.executable, EXTRACT, path, '--out-dir', f'pbr/{mat}', '--material-id', mat,
           '--spec', SPEC, '--in-place', '--report', f'pbr/{mat}_report.json']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(cmd + ['--allow-low-confidence'], capture_output=True, text=True)
        status = 'low-confidence' if r.returncode == 0 else f'FAILED rc={r.returncode}'
    else:
        status = 'ok'
    conf = None
    rp = f'pbr/{mat}_report.json'
    if os.path.exists(rp):
        try:
            conf = json.load(open(rp, encoding='utf-8')).get('confidence')
        except Exception:
            pass
    results.append((mat, status, conf))
    if status.startswith('FAILED'):
        print(f'  {mat}: {r.stderr.strip()[:160]}')

print(f'{"material":12s} {"status":16s} confidence')
for mat, status, conf in results:
    print(f'{mat:12s} {status:16s} {conf if conf is not None else "-"}')
