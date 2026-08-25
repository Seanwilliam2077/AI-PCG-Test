"""Measure one build end to end and emit every number as JSON.

One place that answers "is this build better than that one", so a patch is
accepted or reverted on evidence rather than on how the render feels. Everything
here is measured off the six canonical yaws at a fixed 1.80 m metric frame, so
two runs are directly comparable.

    python tools/evaluate.py --renders out/optimization-pass --tag baseline

Reported:
  silhouetteIou      per view and mean, against the pinned reference panel
  widthRatio         front and side, max and 40-band mean, render over reference
  landmarkRms        16 landmark heights as a fraction of figure height
  lightness          L mean / p10 / p90 / six-view spread inside the alpha
  hullIou            volumetric IoU of the model's visual hull against the
                     reference's, on a shared 32^3 grid
  triangles          geometry triangles and draw calls, from the render log

The composite scoreboard score is deliberately NOT computed here: it lives in the
jinx3js checkout, is the independent judge, and should not be reimplemented in the
thing it judges. `tools/try_patch.py` calls it separately.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

# render yaw -> reference panel index, pinned from docs/HANDEDNESS.md rather than
# fitted: orthographic projection makes yaw y and y+180 exact mirrors, so an
# IoU fit cannot tell front from back on this character.
VIEW_MAP = {0: 2, 45: 1, 90: 0, 180: 5, 270: 4, 315: 3}
FRAME_M = 1.80
FIGURE_M = 1.72
BANDS = 40


def alpha(path: Path) -> np.ndarray | None:
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None or im.shape[2] < 4:
        return None
    return im[:, :, 3] > 128


def normalise(mask: np.ndarray, size: int = 512) -> np.ndarray:
    """Scale a silhouette so its own height fills the canvas, centred on its centroid.

    Both figures then occupy the same pixels-per-figure-height, which is the only
    way a reference panel cropped to its subject and a render framed to 1.80 m can
    be compared at all.
    """
    ys, xs = mask.nonzero()
    if not len(ys):
        return np.zeros((size, size), bool)
    top, bot = ys.min(), ys.max()
    k = (size * 0.94) / (bot - top + 1)
    small = cv2.resize(mask.astype(np.uint8), None, fx=k, fy=k,
                       interpolation=cv2.INTER_NEAREST).astype(bool)
    sy, sx = small.nonzero()
    out = np.zeros((size, size), bool)
    dy = int(size * 0.03) - sy.min()
    dx = size // 2 - int((sx.min() + sx.max()) / 2)
    ty, tx = sy + dy, sx + dx
    keep = (ty >= 0) & (ty < size) & (tx >= 0) & (tx < size)
    out[ty[keep], tx[keep]] = True
    return out


def width_profile(mask: np.ndarray, bands: int = BANDS) -> np.ndarray:
    ys, _ = mask.nonzero()
    if not len(ys):
        return np.zeros(bands)
    top, bot = ys.min(), ys.max()
    H = bot - top + 1
    out = np.zeros(bands)
    for i, f in enumerate(np.linspace(0.02, 0.98, bands)):
        row = mask[int(top + H * f)]
        if row.any():
            nz = row.nonzero()[0]
            out[i] = (nz.max() - nz.min() + 1) / H
    return out


LANDMARKS = [
    ('crown', 0.00), ('chin', 0.13), ('shoulder', 0.19), ('armpit', 0.24),
    ('bust', 0.27), ('underbust', 0.31), ('waist', 0.36), ('navel', 0.39),
    ('hip', 0.44), ('crotch', 0.49), ('midthigh', 0.55), ('knee', 0.63),
    ('hem', 0.68), ('calf', 0.75), ('ankle', 0.86), ('sole', 1.00),
]


def landmark_heights(mask: np.ndarray) -> dict[str, float]:
    """Locate landmarks from the width profile's own structure, not from a prior.

    Each landmark is found as the extremum of the width profile inside a window
    around its nominal fraction. A window that puts its answer on its own boundary
    is not a measurement, so those are returned as None and excluded upstream.
    """
    ys, _ = mask.nonzero()
    if not len(ys):
        return {}
    top, bot = ys.min(), ys.max()
    H = bot - top + 1
    prof = np.array([
        (lambda r: (r.nonzero()[0].max() - r.nonzero()[0].min() + 1) / H if r.any() else 0.0)(
            mask[min(mask.shape[0] - 1, int(top + H * f))])
        for f in np.linspace(0.0, 1.0, 200)
    ])
    out: dict[str, float | None] = {}
    for name, nominal in LANDMARKS:
        if name in ('crown', 'sole'):
            out[name] = 0.0 if name == 'crown' else 1.0
            continue
        lo = max(1, int((nominal - 0.055) * 200))
        hi = min(199, int((nominal + 0.055) * 200))
        if hi <= lo + 1:
            out[name] = None
            continue
        seg = prof[lo:hi]
        # shoulders, bust, hip and calf are local maxima; waist, armpit, knee and
        # ankle are local minima; the rest are read off the strongest gradient
        if name in ('shoulder', 'bust', 'hip', 'calf'):
            j = int(np.argmax(seg))
        elif name in ('armpit', 'underbust', 'waist', 'knee', 'ankle'):
            j = int(np.argmin(seg))
        else:
            j = int(np.argmax(np.abs(np.gradient(seg))))
        if j <= 0 or j >= len(seg) - 1:
            out[name] = None            # clamped on the window edge
            continue
        out[name] = (lo + j) / 200.0
    return out


def lightness(path: Path) -> tuple[float, float, float] | None:
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    m = im[:, :, 3] > 128
    if not m.any():
        return None
    L = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2LAB)[:, :, 0][m].astype(np.float32) * 100 / 255
    return float(L.mean()), float(np.percentile(L, 10)), float(np.percentile(L, 90))


def hull_voxels(front: np.ndarray, side: np.ndarray, res: int = 32) -> np.ndarray:
    """Intersection of the two silhouette prisms on a shared grid.

    An upper bound on the shape, never the shape: with two views the hull is loose
    along the third axis and can hold no concavity that neither view sees as
    background.
    """
    f = cv2.resize(front.astype(np.uint8), (res, res), interpolation=cv2.INTER_AREA) > 0.4
    s = cv2.resize(side.astype(np.uint8), (res, res), interpolation=cv2.INTER_AREA) > 0.4
    occ = np.zeros((res, res, res), bool)
    for j in range(res):                       # y, shared row between both views
        occ[:, j, :] = np.outer(f[j], s[j])
    return occ


def evaluate(renders: Path, ref: Path, clay: Path | None) -> dict:
    out: dict = {'renders': str(renders)}
    ious, ratios, lms = {}, {}, {}
    Ls = []
    for yaw, panel in VIEW_MAP.items():
        rp = renders / f'render_yaw{yaw}.png'
        cp = ref / f'clay_{panel}.png'
        rm, cm = alpha(rp), alpha(cp)
        if rm is None or cm is None:
            continue
        a, b = normalise(cm), normalise(rm)
        ious[str(yaw)] = round(float((a & b).sum() / max(1, (a | b).sum())), 4)
        pr, pd = width_profile(a), width_profile(b)
        ok = (pr > 0.01) & (pd > 0.01)
        ratios[str(yaw)] = {
            'max': round(float(pd.max() / max(1e-6, pr.max())), 4),
            'bandMean': round(float((pd[ok] / pr[ok]).mean()), 4) if ok.any() else None,
            'bandRms': round(float(np.sqrt(((pd[ok] - pr[ok]) ** 2).mean())), 5) if ok.any() else None,
        }
        la, lb = landmark_heights(a), landmark_heights(b)
        deltas = {k: round((lb[k] - la[k]) * 100, 3)
                  for k in la if la.get(k) is not None and lb.get(k) is not None}
        lms[str(yaw)] = deltas
        st = lightness(rp)
        if st:
            Ls.append(st)

    out['silhouetteIou'] = ious
    out['silhouetteIouMean'] = round(float(np.mean(list(ious.values()))), 4) if ious else None
    out['widthRatio'] = ratios
    bm = [v['bandMean'] for v in ratios.values() if v['bandMean'] is not None]
    out['widthBandMeanAll'] = round(float(np.mean(bm)), 4) if bm else None
    br = [v['bandRms'] for v in ratios.values() if v['bandRms'] is not None]
    out['widthBandRmsAll'] = round(float(np.mean(br)), 5) if br else None

    out['landmarkDelta'] = lms
    flat = [abs(v) for d in lms.values() for v in d.values()]
    out['landmarkRmsPct'] = round(float(np.sqrt(np.mean(np.square(flat)))), 3) if flat else None
    out['landmarksScored'] = len(flat)

    if Ls:
        means = [x[0] for x in Ls]
        out['lightness'] = {
            'mean': round(float(np.mean(means)), 3),
            'p10': round(float(np.mean([x[1] for x in Ls])), 3),
            'p90': round(float(np.mean([x[2] for x in Ls])), 3),
            'spread': round(float(max(means) - min(means)), 3),
        }

    src = clay if clay and (clay / 'render_yaw0.png').exists() else renders
    rf, rs = alpha(src / 'render_yaw0.png'), alpha(src / 'render_yaw90.png')
    cf, cs = alpha(ref / 'clay_2.png'), alpha(ref / 'clay_0.png')
    if all(x is not None for x in (rf, rs, cf, cs)):
        A = hull_voxels(normalise(cf), normalise(cs))
        B = hull_voxels(normalise(rf), normalise(rs))
        out['hull'] = {
            'iou': round(float((A & B).sum() / max(1, (A | B).sum())), 4),
            'outsideReference': round(float((B & ~A).sum() / max(1, B.sum())), 4),
            'referenceUnfilled': round(float((A & ~B).sum() / max(1, A.sum())), 4),
            'volumeRatio': round(float(B.sum() / max(1, A.sum())), 4),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--renders', default='out/optimization-pass')
    ap.add_argument('--clay', default='out/clay')
    ap.add_argument('--ref', default='ref/views')
    ap.add_argument('--tag', default='current')
    ap.add_argument('--out', default=None)
    ap.add_argument('--compare-to', default=None, help='a previous evaluate JSON to diff against')
    a = ap.parse_args()

    res = evaluate(Path(a.renders), Path(a.ref), Path(a.clay))
    res['tag'] = a.tag
    dest = Path(a.out or f'out/eval_{a.tag}.json')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(res, indent=1), encoding='utf-8')

    print(f"[{a.tag}]")
    print(f"  silhouette IoU mean   {res.get('silhouetteIouMean')}")
    print(f"    per view            {res.get('silhouetteIou')}")
    print(f"  width band-mean       {res.get('widthBandMeanAll')}   band RMS {res.get('widthBandRmsAll')}")
    print(f"  landmark RMS          {res.get('landmarkRmsPct')}%   ({res.get('landmarksScored')} readings)")
    if 'lightness' in res:
        li = res['lightness']
        print(f"  lightness             mean {li['mean']}  p10 {li['p10']}  p90 {li['p90']}  spread {li['spread']}")
    if 'hull' in res:
        h = res['hull']
        print(f"  hull IoU              {h['iou']}   outside ref {h['outsideReference']}   unfilled {h['referenceUnfilled']}")

    if a.compare_to and Path(a.compare_to).exists():
        base = json.loads(Path(a.compare_to).read_text(encoding='utf-8'))
        print(f"\n  vs [{base.get('tag')}]")
        for key, label, better in (
            ('silhouetteIouMean', 'silhouette IoU', 'up'),
            ('widthBandRmsAll', 'width band RMS', 'down'),
            ('landmarkRmsPct', 'landmark RMS %', 'down'),
        ):
            x, y = base.get(key), res.get(key)
            if x is None or y is None:
                continue
            d = y - x
            good = (d > 0) if better == 'up' else (d < 0)
            print(f"    {label:18s} {x:8.4f} -> {y:8.4f}  {d:+8.4f}  {'BETTER' if good else 'worse' if d else 'same'}")
        if 'hull' in base and 'hull' in res:
            d = res['hull']['iou'] - base['hull']['iou']
            print(f"    {'hull IoU':18s} {base['hull']['iou']:8.4f} -> {res['hull']['iou']:8.4f}  {d:+8.4f}"
                  f"  {'BETTER' if d > 0 else 'worse' if d else 'same'}")
    print(f"\n  written {dest}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
