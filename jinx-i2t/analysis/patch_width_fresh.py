"""Correct component widths from a measurement taken of the build being patched.

The width patch authored against the baseline was rejected by the gate, and it
deserved to be: it carried hard-coded per-component deltas measured before the
extremity, hair and torso patches landed, so by the time it ran every number in
it described a model that no longer existed. Silhouette IoU fell 0.0039 and hull
IoU 0.0179. The same staleness killed the landmark patch outright -- it raised
KeyError on `hair-crest`, which the hair patch had consolidated away.

So this one measures instead of remembering. Every run it re-derives:

  * the reference and render silhouette width at 40 heights, from the panels and
    from the render of the build it is about to modify;
  * which mesh actually SETS the silhouette in each band, from that build's own
    per-mesh world bounds, because the widest mesh spanning a height is the one
    whose edge the silhouette follows there.

A component is then scaled by the inverse of the mean ratio over the bands it
governs, damped, and only where the error clears a threshold. Damping matters:
the mapping from a component's declared width to the silhouette it produces is
not the identity -- a limb is a circular cylinder seen at an angle, a garment
overlaps its neighbours -- so a full correction overshoots. Applying a fraction
and re-running converges instead.

Inputs, both written by the pipeline rather than by hand:
    baseline/meshes_accepted.json   per-mesh world bounds of the accepted build
    out/accepted/render_yaw*.png    that build's six canonical views

Expected measurable effect: width band RMS falls from 0.0310 and the front and
side band-means move toward 1.0 from 1.044. Silhouette IoU should rise or hold;
if it falls, the damping is too aggressive and the run should be reverted rather
than tuned after the fact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
MESHES = ROOT / 'baseline/meshes_accepted.json'
RENDERS = ROOT / 'out/accepted'
REF = ROOT / 'ref/views'

BANDS = 40
DAMP = 0.55           # fraction of the measured error to apply in one pass
DEADZONE = 0.04       # ignore bands within 4 percent; that is inside measurement noise
MAX_STEP = 0.22       # no component may change by more than this in one pass
# yaw -> (reference panel, silhouette axis the render's width measures)
VIEWS = ((0, 'clay_2', 'x'), (90, 'clay_0', 'z'))


def silhouette(path: Path) -> np.ndarray | None:
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    return None if im is None or im.shape[2] < 4 else im[:, :, 3] > 128


def band_widths(mask: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Width at BANDS heights as a fraction of figure height, plus the figure span."""
    ys, _ = mask.nonzero()
    top, bot = ys.min(), ys.max()
    H = bot - top + 1
    out = np.zeros(BANDS)
    for i, f in enumerate(np.linspace(0.02, 0.98, BANDS)):
        row = mask[int(top + H * f)]
        if row.any():
            nz = row.nonzero()[0]
            out[i] = (nz.max() - nz.min() + 1) / H
    return out, float(top), float(H)


def main() -> int:
    meshes = json.loads(MESHES.read_text(encoding='utf-8'))
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    comps = {c['id']: c for c in spec['componentTree']}
    by_name = {c.get('name') or c['id']: c for c in spec['componentTree']}

    # the model's own vertical extent, so a band index maps to a world height
    y_lo = min(m['minY'] for m in meshes)
    y_hi = max(m['maxY'] for m in meshes)

    # component id -> list of (band ratio) it governs
    governs: dict[str, list[float]] = {}
    report: list[tuple[str, int, float, float]] = []

    for yaw, panel, axis in VIEWS:
        r = silhouette(RENDERS / f'render_yaw{yaw}.png')
        c = silhouette(REF / f'{panel}.png')
        if r is None or c is None:
            continue
        pr, _, _ = band_widths(r)
        pc, _, _ = band_widths(c)
        for i in range(BANDS):
            if pr[i] < 0.01 or pc[i] < 0.01:
                continue
            ratio = pr[i] / pc[i]
            if abs(ratio - 1.0) < DEADZONE:
                continue
            # world height of this band, in the model's own frame
            f = 0.02 + (0.98 - 0.02) * i / (BANDS - 1)
            y = y_hi - f * (y_hi - y_lo)
            # the mesh that sets the silhouette here is the widest one spanning it,
            # measured on the axis this view actually projects
            span = [m for m in meshes if m['minY'] <= y <= m['maxY']]
            if not span:
                continue
            key = 'w' if axis == 'x' else 'd'
            winner = max(span, key=lambda m: m.get(key, 0.0))
            comp = by_name.get(winner['name'])
            if comp is None:
                continue
            governs.setdefault(comp['id'], []).append(ratio)
            report.append((comp['id'], yaw, round(ratio, 3), round(y, 3)))

    changed = []
    for cid, ratios in governs.items():
        comp = comps[cid]
        mean = float(np.mean(ratios))
        # move DAMP of the way from the measured ratio back to 1.0
        factor = 1.0 / (1.0 + (mean - 1.0) * DAMP)
        factor = float(np.clip(factor, 1 - MAX_STEP, 1 + MAX_STEP))
        if abs(factor - 1.0) < 0.01:
            continue
        att = comp.get('attachment') or {}
        if att.get('baseRadius') is not None:
            # a cylinder's cross-section is circular: one factor moves both views
            att['baseRadius'] = round(att['baseRadius'] * factor, 5)
            att['endRadius'] = round(att['endRadius'] * factor, 5)
            kind = 'radius'
        else:
            dim = comp.get('dimensions') or {}
            for k in ('width', 'depth'):
                if k in dim:
                    dim[k] = round(dim[k] * factor, 5)
            kind = 'dimensions'
        changed.append((cid, kind, len(ratios), round(mean, 3), round(factor, 3)))

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    print(f'{len(governs)} components govern at least one out-of-tolerance band; '
          f'{len(changed)} scaled')
    print(f'  {"component":26s} {"drives":>7s} {"bands":>6s} {"ratio":>6s} {"factor":>7s}')
    for cid, kind, n, mean, factor in sorted(changed, key=lambda r: abs(r[4] - 1), reverse=True):
        print(f'  {cid:26s} {kind:>7s} {n:6d} {mean:6.3f} {factor:7.3f}')
    if not changed:
        print('  nothing outside the dead zone -- the profile is already within '
              f'{DEADZONE:.0%} at every band')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
