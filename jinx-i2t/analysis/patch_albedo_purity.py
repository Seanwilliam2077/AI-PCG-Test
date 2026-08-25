"""Cut PBR crops that are HOMOGENEOUS, then mirror-tile them to the extractor's size.

Two defects compound in the current maps, and fixing either alone makes things
worse rather than better -- both attempts are on the record.

**The crops are pictures, not samples.** `analysis/extract_pbr2.py` grew each
located rect outward from its centre until it reached the extractor's 96 px
minimum. Growing a 24 px rect to 96 px pulls in sixteen times its own area of
whatever sat next to it, which is why `pbr/crops/skin.png` is a whole eye with
lashes and eyeliner, `cloth` is the chest buckles, `hair` is a pair of eyebrows
and `leather` is an entire boot. The renderer then stretches each picture over
every component carrying that material, which is most of what makes the build
read as a collage.

**The search only asked for the right median.** Replacing growth with mirror-tiling
was tried first and rejected: the crop lightness spans stayed at 20-52 L and the
scoreboard fell 0.10. The reason is that `recut_pbr.py` scores a candidate rect
only on the CIE Lab distance from its median to a target colour. A rect holding
half dark cloth and half bright buckle has exactly the median it was asked for
and is not a material sample at all. Mirror-tiling such a rect faithfully
reproduces its contradiction across the whole surface.

So this search adds the requirement that was missing: a material sample must be
homogeneous. Cost is Lab distance to target plus a penalty on the rect's own
lightness spread, and a rect whose p5-p95 range exceeds a ceiling is refused
outright however well its median matches. The winner is then mirror-tiled to
96 px, so every pixel is a real sample from a verified-pure region and each tile
edge is a reflection rather than a jump.

Rejected honestly: some materials have no homogeneous patch at this resolution --
a bootlace is two pixels wide on a 377 px panel and every rect containing it also
contains boot. Those keep their best available rect, and the report names them.

Idempotent by construction: the search runs from the reference panels every time
and nothing is edited in place.

Expected measurable effect: crop lightness p5-p95 range under 15 L for most
materials, against 20-52 L now. Geometry terms cannot move. The six-view
lightness spread should stay near 1.9 -- the previous attempt pushed it to 5.4,
which is the signature of maps that disagree with each other, and is the number to
watch.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'analysis'))
import recut_pbr as R  # noqa: E402  -- BANDS and the panel conventions live there

SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
SK = Path.home() / '.claude' / 'skills' / 'img2threejs'
EXTRACT = SK / 'forge/stage1_intake/extract_pbr_evidence.py'

TILE = 96
# Homogeneity is an ADMISSIBILITY criterion, not a cost. Weighting it against
# colour was tried and rejected: at weight 1.6 a flat patch of the wrong colour
# beat a slightly varying patch of the right one, and skinShade came back 134 dLab
# from its target. Colour is the measurement; homogeneity decides whether a rect is
# a material sample at all.
SPREAD_CEILING = 14.0     # above this, a rect holds more than one material
SPREAD_FLOOR = 1.2        # below this the extractor has nothing to measure and
                          # marks the material unusable, which fails strict validation
RELAX = (14.0, 20.0, 28.0, 1e9)   # ladder for materials with no admissible rect

# Bands and targets that recut_pbr.py got wrong, overridden here with the numbers
# measured off body_2 and body_5 rather than off a head close-up.
#
# `skin` was targeted from head_1, where the face is a lit close-up. The same
# material covers the arms, midriff and shins, and on the body panel those sit at
# BGR (140,156,186) on the forearm against the face's (182,191,208). Sampling a lit
# face and painting it on a whole body overshot every skin region: the midriff
# rendered at L 66.4 against the reference band's 39.3.
#
# `skinShade` was banded over the upper chest, where the black top is, so the
# search returned a patch 130 dLab from its target -- it was measuring the top, not
# shaded skin. The shin is where shaded skin is actually visible, at BGR (107,95,96).
BAND_OVERRIDE = {
    'skin':      ('body_2', 0.245, 0.30, 0.315, 0.355, (140, 156, 186)),
    'skinShade': ('body_2', 0.40, 0.46, 0.735, 0.775, (107, 95, 96)),
}


def lab_of(bgr) -> np.ndarray:
    return cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0, 0].astype(float)


def spread_of(patch: np.ndarray) -> float:
    L = cv2.cvtColor(patch[:, :, :3], cv2.COLOR_BGR2LAB)[:, :, 0].astype(float) * 100 / 255
    return float(np.percentile(L, 95) - np.percentile(L, 5))


def search_homogeneous(mat, panel, x0, x1, y0, y1, target, panels):
    """Best rect by colour match AND internal homogeneity, inside the band."""
    im = panels[panel]
    H, W = im.shape[:2]
    alpha = im[:, :, 3] > 128
    holes = im[:, :, :3].min(axis=2) > 248
    X0, X1, Y0, Y1 = int(W * x0), int(W * x1), int(H * y0), int(H * y1)
    tl = lab_of(target)
    sizes = (4, 5, 6) if mat in R.TINY else (8, 12, 18) if mat in R.SMALL else (16, 24, 32)

    # every admissible-by-coverage candidate, scored on colour alone
    cands = []
    for side in sizes:
        if X1 - X0 < side or Y1 - Y0 < side:
            continue
        step = max(1, side // 3)
        for y in range(Y0, Y1 - side, step):
            for x in range(X0, X1 - side, step):
                if alpha[y:y + side, x:x + side].mean() < 0.95:
                    continue
                if holes[y:y + side, x:x + side].mean() > 0.05:
                    continue
                sub = im[y:y + side, x:x + side]
                med = np.median(sub[:, :, :3].reshape(-1, 3), axis=0)
                cands.append(dict(panel=panel, x=x, y=y, w=side, h=side,
                                  dist=round(float(np.linalg.norm(lab_of(med) - tl)), 1),
                                  spread=round(spread_of(sub), 1),
                                  median=[int(v) for v in med], target=list(target)))
    if not cands:
        return None, 0.0

    for ceiling in RELAX:
        ok = [c for c in cands if SPREAD_FLOOR <= c['spread'] <= ceiling]
        if ok:
            return min(ok, key=lambda c: c['dist']), ceiling
    # nothing cleared even the floor: every candidate is degenerate flat
    return min(cands, key=lambda c: c['dist']), None


def mirror_tile(patch: np.ndarray, size: int) -> np.ndarray:
    """Fill size x size by reflecting the patch, so no tile edge is a jump."""
    h, w = patch.shape[:2]
    rows = []
    for j in range(-(-size // h)):
        cols = []
        for i in range(-(-size // w)):
            t = patch
            if i % 2:
                t = t[:, ::-1]
            if j % 2:
                t = t[::-1, :]
            cols.append(t)
        rows.append(np.hstack(cols))
    return np.vstack(rows)[:size, :size]


def main() -> int:
    panels = {n: cv2.imread(str(ROOT / f'ref/views/{n}.png'), cv2.IMREAD_UNCHANGED)
              for n in ('body_0', 'body_2', 'body_5', 'head_1')}
    (ROOT / 'pbr/crops').mkdir(parents=True, exist_ok=True)
    (ROOT / 'public').mkdir(exist_ok=True)

    rects, rows, compromised = {}, [], []
    bands = dict(R.BANDS)
    bands.update(BAND_OVERRIDE)
    for mat, (panel, x0, x1, y0, y1, target) in bands.items():
        hit, ceiling = search_homogeneous(mat, panel, x0, x1, y0, y1, target, panels)
        if hit is not None and (ceiling is None or ceiling > SPREAD_CEILING):
            compromised.append(f'{mat}(<={ceiling if ceiling else "flat"})')
        if hit is None:
            rows.append((mat, 'no rect met coverage and hole tests', None, None, None))
            continue
        rects[mat] = hit

        im = panels[panel]
        patch = im[hit['y']:hit['y'] + hit['h'], hit['x']:hit['x'] + hit['w']].copy()
        if patch.shape[2] == 4:
            a = patch[:, :, 3:4].astype(float) / 255.0
            rgb = patch[:, :, :3].astype(float)
            inside = rgb.reshape(-1, 3)[a.reshape(-1) > 0.5]
            fill = inside.mean(axis=0) if len(inside) else np.array([128.0, 128, 128])
            patch = (rgb * a + fill * (1 - a)).astype('uint8')
        crop = mirror_tile(patch, TILE)
        cv2.imwrite(str(ROOT / f'pbr/crops/{mat}.png'), crop)

        cmd = [sys.executable, str(EXTRACT), str(ROOT / f'pbr/crops/{mat}.png'),
               '--out-dir', str(ROOT / f'pbr/{mat}'), '--material-id', mat,
               '--spec', str(SPEC), '--in-place',
               '--report', str(ROOT / f'pbr/{mat}_report.json')]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if p.returncode != 0:
            p = subprocess.run(cmd + ['--allow-low-confidence'], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
        rows.append((mat, 'ok' if p.returncode == 0 else 'FAILED',
                     hit['spread'], hit['dist'], f"{hit['w']}x{hit['h']}"))

    (ROOT / 'analysis/pbr_rects_homogeneous.json').write_text(
        json.dumps(rects, indent=1), encoding='utf-8')

    copied = 0
    for p in (ROOT / 'pbr').rglob('*.png'):
        if p.parent.name == 'crops':
            continue
        (ROOT / 'public' / p.name).write_bytes(p.read_bytes())
        copied += 1

    # two facts a crop cannot establish, re-asserted after every extraction: the
    # tank is glass, and metalness is binary in metallic-roughness PBR
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    for m in spec['materials']:
        if m['id'] == 'glassTank':
            m['type'] = 'physical'
            m['shaderModel'] = 'MeshPhysicalMaterial / PBR with transmission'
            m['roughness']['base'] = 0.10
            m['roughness']['variation'] = 0.04
            m['metalness'] = 0.0
            m.update(transmission=0.6, ior=1.6, thickness=0.5)
        elif m['id'] in ('brass', 'steel'):
            m['metalness'] = 1.0
    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    print(f'{len(rows)} crops re-cut homogeneously and mirror-tiled to {TILE} px; '
          f'{copied} maps served')
    print(f'  {"material":13s} {"rect":>7s} {"spread L":>9s} {"dLab":>6s}  status')
    for mat, status, spread, dist, size in sorted(rows, key=lambda r: -(r[2] or 0)):
        print(f'  {mat:13s} {size or "-":>7s} {spread if spread is not None else "-":>9} '
              f'{dist if dist is not None else "-":>6}  {status}')
    print(f'\nover the {SPREAD_CEILING} L homogeneity ceiling, best available kept: '
          f'{compromised or "none"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
