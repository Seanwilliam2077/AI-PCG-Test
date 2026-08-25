"""Warp the figure vertically so every landmark lands where the reference's does.

The landmark term is the largest single gap in the composite score -- 2.44 percent
RMS for the competing build against 3.15 here -- and it is the one the eye reads
first, because it is where the waist, the hip and the knee sit, not how wide they
are.

The patch authored against the baseline tried to move landmarks one component at a
time and died on `hair-crest`, a component the hair patch had already consolidated
away. Per-landmark attribution is the wrong shape for this problem anyway: a waist
is a local minimum of the width profile, produced by two components meeting, so
"which component owns the waist" has no single answer.

So this fits ONE monotone piecewise-linear map from the render's landmark heights
to the reference's, and pushes the whole figure through it. Every landmark moves
at once, by construction, and the map is monotone so nothing can cross anything
else. Three things have to travel through the same map or the model comes apart:

  * every component's world Y, then rebased to its parent, because positions are
    parent-local and accumulate;
  * every attachment's localStart/localEnd Y, since those drive both position and
    the swept cylinder's length;
  * every rig bone's jointPos and tipPos -- 49 bones, and the 98 sockets derived
    from them, silently desynchronise from the geometry otherwise.

Component heights are scaled by the map's local slope, so a part spanning a
region the map compresses gets shorter rather than overlapping its neighbour.

Everything is re-measured from the build being patched, never remembered:
`out/accepted/render_yaw*.png` against the reference panels. Landmarks that the
detector could not locate, or located on a search boundary, are excluded from the
fit rather than contributing a fabricated pair.

Expected measurable effect: landmark RMS falls from 3.15 toward the 2.4 the
competing build reaches. Silhouette IoU and width band RMS should hold -- a
vertical warp moves features without changing widths -- and if IoU falls, the fit
has overshot and the run should be reverted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import evaluate as E  # noqa: E402  -- the landmark detector and its exclusions live there

SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
RENDERS = ROOT / 'out/accepted'
REF = ROOT / 'ref/views'
DAMP = 0.70          # fraction of each landmark's error to close in one pass
MIN_PAIRS = 6        # below this the fit is not worth trusting
MAX_SHIFT_M = 0.06   # no landmark may be moved more than 60 mm in one pass


def collect_pairs() -> list[tuple[float, float]]:
    """(render fraction, reference fraction) per landmark, averaged over the views."""
    acc: dict[str, list[tuple[float, float]]] = {}
    for yaw, panel in ((0, 2), (90, 0), (180, 5)):
        rm = E.alpha(RENDERS / f'render_yaw{yaw}.png')
        cm = E.alpha(REF / f'clay_{panel}.png')
        if rm is None or cm is None:
            continue
        lr = E.landmark_heights(E.normalise(rm))
        lc = E.landmark_heights(E.normalise(cm))
        for k, v in lr.items():
            if v is None or lc.get(k) is None:
                continue
            acc.setdefault(k, []).append((v, lc[k]))
    pairs = []
    for k, vs in acc.items():
        a = np.array(vs)
        pairs.append((float(a[:, 0].mean()), float(a[:, 1].mean()), k, len(vs)))
    return sorted(pairs)


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    comps = {c['id']: c for c in spec['componentTree']}

    raw = collect_pairs()
    if len(raw) < MIN_PAIRS:
        print(f'only {len(raw)} landmark pairs located; refusing to fit a warp on that')
        return 0

    # world Y of every component, by accumulating parent-local positions
    world: dict[str, list[float]] = {}

    def solve(cid: str, guard: tuple = ()) -> list[float]:
        if cid in world:
            return world[cid]
        c = comps.get(cid)
        if c is None or cid in guard:
            return [0.0, 0.0, 0.0]
        p = c.get('parent')
        base = solve(p, guard + (cid,)) if p and p in comps else [0.0, 0.0, 0.0]
        pos = c['transform']['position']
        world[cid] = [base[i] + pos[i] for i in range(3)]
        return world[cid]

    for cid in comps:
        solve(cid)

    # the map works in fractions measured from the crown down, so it needs the
    # figure's own extent in world metres
    y_hi = max(w[1] for w in world.values())
    y_lo = min(w[1] for w in world.values())
    # the crown is the hair, not the highest component pivot; take the model's
    # declared frame instead, which the render confirms
    y_hi = max(y_hi, 1.72)
    y_lo = min(y_lo, 0.0)
    span = y_hi - y_lo

    def frac_to_world(f: float) -> float:
        return y_hi - f * span

    # knots: render height -> damped target, in world metres, forced monotone
    knots = [(0.0, 0.0)]
    used = []
    for fr, fc, name, n in raw:
        wr, wc = frac_to_world(fr), frac_to_world(fc)
        shift = float(np.clip((wc - wr) * DAMP, -MAX_SHIFT_M, MAX_SHIFT_M))
        knots.append((wr, wr + shift))
        used.append((name, round(wr, 4), round(wr + shift, 4), round(shift * 1000, 1), n))
    knots.append((span * 2, span * 2))
    knots.sort()
    xs = np.array([k[0] for k in knots])
    ys = np.array([k[1] for k in knots])
    # monotone: a landmark may not be pushed past its neighbour
    ys = np.maximum.accumulate(ys)
    # collapse duplicate abscissae, which np.interp handles badly
    keep = np.concatenate(([True], np.diff(xs) > 1e-6))
    xs, ys = xs[keep], ys[keep]

    def warp(y: float) -> float:
        return float(np.interp(y, xs, ys))

    def slope(y: float, h: float = 0.004) -> float:
        return max(0.4, min(2.5, (warp(y + h) - warp(y - h)) / (2 * h)))

    # 1. component positions, rebased after warping
    new_world = {cid: [w[0], warp(w[1]), w[2]] for cid, w in world.items()}
    moved = 0
    for cid, c in comps.items():
        p = c.get('parent')
        base = new_world.get(p, [0.0, 0.0, 0.0]) if p in comps else [0.0, 0.0, 0.0]
        old = c['transform']['position'][1]
        c['transform']['position'][1] = round(new_world[cid][1] - base[1], 5)
        if abs(c['transform']['position'][1] - old) > 1e-5:
            moved += 1
        # a part in a compressed region has to get shorter, or it overlaps its neighbour
        dim = c.get('dimensions') or {}
        if 'height' in dim:
            dim['height'] = round(dim['height'] * slope(world[cid][1]), 5)

    # 2. attachment endpoints, which drive position AND the swept cylinder length
    for cid, c in comps.items():
        att = c.get('attachment')
        if not att or att.get('localStart') is None:
            continue
        p = c.get('parent')
        pw = world.get(p, [0.0, 0.0, 0.0]) if p in comps else [0.0, 0.0, 0.0]
        pw_new = new_world.get(p, [0.0, 0.0, 0.0]) if p in comps else [0.0, 0.0, 0.0]
        for key in ('localStart', 'localEnd'):
            v = att.get(key)
            if not isinstance(v, list) or len(v) != 3:
                continue
            att[key][1] = round(warp(pw[1] + v[1]) - pw_new[1], 5)

    # 3. the rig, or 49 bones and 98 sockets quietly stop matching the geometry
    bones = (spec.get('rig') or {}).get('bones') or []
    for b in bones:
        for key in ('jointPos', 'tipPos'):
            v = b.get(key)
            if isinstance(v, list) and len(v) == 3:
                v[1] = round(warp(v[1]), 5)

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    print(f'{len(used)} landmarks fitted, {moved} components repositioned, '
          f'{len(bones)} bones warped')
    print(f'  {"landmark":12s} {"render y":>9s} {"target y":>9s} {"shift mm":>9s} {"views":>6s}')
    for name, wr, wt, mm, n in sorted(used, key=lambda r: -abs(r[3])):
        print(f'  {name:12s} {wr:9.4f} {wt:9.4f} {mm:+9.1f} {n:6d}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
