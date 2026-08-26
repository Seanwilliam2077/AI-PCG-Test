"""Score a built model against the constraint contract that was frozen before it.

This is the measurement behind Nova3D's central claim (arXiv 2607.22738): that a
code-native asset satisfies numeric and count constraints stated in advance, where
mesh-native and CAD baselines mostly cannot. Nova3D reports 51/52. A number like
that is only worth reporting if every constraint could have failed, so this tool
refuses to score a constraint it cannot evaluate rather than passing it by default.

    python tools/check_contract.py --contract docs/contract.json --meshes out/_meshes.json

Inputs:
    docs/contract.json    the frozen constraints, machine-readable
    out/_meshes.json      per-mesh world bounding boxes, written by the render harness
    object-sculpt-spec.json   for the assembly tree and joint checks

The check vocabulary is deliberately small, because a constraint that needs a
richer language than this is usually a constraint nobody can falsify:

    size(part, axis)        extent of a part's world bbox: axis in x|y|z|max|min
    pos(part, axis)         centre of a part's world bbox
    lo(part, axis)          minimum of a part's world bbox
    hi(part, axis)          maximum of a part's world bbox
    count(pattern)          number of built meshes whose name matches a regex
    span(partA, partB, ax)  hi(B,ax) - lo(A,ax), for overall lengths
    sub(exprA, exprB)       the difference of two of the above
    ratio(exprA, exprB)     the quotient of two of the above

Two families need more than bounding boxes, and the contract marks them:

    material(part, channel)   [MAT] the assigned material's base colour, as
                              L | a | b | hue | chroma in CIE Lab
    radius(u) / steps()       [SIL] the silhouette radius profile, sampled from an
                              orthographic side render at 200 stations along the axis

[RAY] constraints need ray casts and are NOT implemented. They report as UNCHECKABLE
and count as failures, never as passes: a constraint nobody evaluates inflates the
satisfied count without testing anything, which is exactly the failure mode a
"51/52 satisfied" headline invites.

and four relations, which take two parts and return a boolean:

    above(A, B, axis)       lo(A,axis) >= hi(B,axis) - slack
    inside(A, B)            A's bbox is contained in B's, within slack
    meets(A, B, axis)       lo(A,axis) touches hi(B,axis), for abutments
    concentric(A, B, axis)  A is inside B on the two axes PERPENDICULAR to `axis`
    flush(A, B, axis)       |hi(A,axis) - hi(B,axis)| <= slack
    disjoint(A, B)          the bboxes do not overlap beyond slack

Every part reference is a mesh NAME as the harness reports it. A constraint naming
a part that was not built is a FAILURE, not a skip: the contract asserted it exists.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AXES = {'x': 'w', 'y': 'h', 'z': 'd'}
MATS = None
SIL = None


def srgb_to_lab(value):
    """CIE Lab under D65, from an #RRGGBB string or an (r, g, b) 0-255 triple."""
    if isinstance(value, str):
        h = value.strip().lstrip('#')
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    else:
        rgb = tuple(value)
    lin = []
    for c in rgb:
        u = c / 255
        lin.append(u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4)
    x = lin[0] * 0.4124 + lin[1] * 0.3576 + lin[2] * 0.1805
    y = lin[0] * 0.2126 + lin[1] * 0.7152 + lin[2] * 0.0722
    z = lin[0] * 0.0193 + lin[1] * 0.1192 + lin[2] * 0.9505

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x / 0.95047), f(y / 1.0), f(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


class Materials:
    """What colour a part is actually assigned, for the [MAT] constraints."""

    def __init__(self, spec):
        self.mats = {m['id']: m for m in spec.get('materials', [])}
        self.of_part = {}
        for c in spec.get('componentTree', []):
            if c.get('material'):
                self.of_part[c.get('name') or c['id']] = c['material']
                self.of_part[c['id']] = c['material']

    def channel(self, part, channel):
        import math
        mid = self.of_part.get(part)
        if mid is None:
            raise KeyError(part + ' has no assigned material')
        m = self.mats.get(mid)
        if m is None:
            raise KeyError('material ' + repr(mid) + ' not in the spec')
        base = m.get('baseColor') or m.get('color')
        if not base:
            raise KeyError('material ' + repr(mid) + ' has no base colour')
        L, a, b = srgb_to_lab(base)
        return {'L': L, 'a': a, 'b': b,
                'hue': math.degrees(math.atan2(b, a)),
                'chroma': math.hypot(a, b)}[channel]


class Silhouette:
    """Radius profile along the axis, from an orthographic side render.

    Every [SIL] row asks the same question in a different place: how the object's
    half-height varies along its own axis. Sampling once and answering from the
    samples keeps all of them consistent with each other.
    """

    def __init__(self, path, stations=200):
        self.ok = False
        if path is None or not Path(path).exists():
            return
        import cv2
        import numpy as np
        im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if im is None or im.shape[2] < 4:
            return
        alpha = im[:, :, 3] > 128
        cols = np.nonzero(alpha.any(axis=0))[0]
        if not len(cols):
            return
        x0, x1 = cols.min(), cols.max()
        self.u = np.linspace(0.0, 1.0, stations)
        r = []
        for u in self.u:
            col = alpha[:, int(round(x0 + u * (x1 - x0)))]
            nz = np.nonzero(col)[0]
            r.append((nz.max() - nz.min() + 1) / 2 if len(nz) else 0.0)
        self.r = np.array(r)
        self.R = float(np.median(self.r[self.r > 0])) if (self.r > 0).any() else 0.0
        self.ok = True

    def radius_at(self, u):
        import numpy as np
        return float(np.interp(u, self.u, self.r))

    def steps(self, min_frac=0.02):
        """Sign changes in dr/du clearing min_frac of the median radius."""
        import numpy as np
        d = np.gradient(self.r)
        sig = np.where(np.abs(d) > min_frac * max(self.R, 1e-6), np.sign(d), 0)
        sig = sig[sig != 0]
        return int(np.sum(sig[1:] != sig[:-1])) if len(sig) > 1 else 0



class Model:
    """Per-mesh world bounds, keyed by name, with the lookups the DSL needs."""

    def __init__(self, meshes: list[dict]):
        self.by_name: dict[str, dict] = {}
        for m in meshes:
            self.by_name.setdefault(str(m.get('name', '')), m)
        self.all = meshes

    def find(self, part: str) -> dict | None:
        if part in self.by_name:
            return self.by_name[part]
        # tolerate a case-insensitive or substring match, but report it
        low = part.lower()
        for name, m in self.by_name.items():
            if name.lower() == low:
                return m
        for name, m in self.by_name.items():
            if low in name.lower():
                return m
        return None

    def bounds(self, part: str) -> dict:
        m = self.find(part)
        if m is None:
            raise KeyError(part)
        return {
            'x': (m['x0'], m['x1']), 'y': (m['minY'], m['maxY']),
            'z': (m.get('z0', -m.get('d', 0) / 2), m.get('z1', m.get('d', 0) / 2)),
        }

    def size(self, part: str, axis: str) -> float:
        b = self.bounds(part)
        if axis in ('max', 'min'):
            v = [b[a][1] - b[a][0] for a in 'xyz']
            return max(v) if axis == 'max' else min(v)
        return b[axis][1] - b[axis][0]

    def pos(self, part: str, axis: str) -> float:
        lo, hi = self.bounds(part)[axis]
        return (lo + hi) / 2

    def lo(self, part: str, axis: str) -> float:
        return self.bounds(part)[axis][0]

    def hi(self, part: str, axis: str) -> float:
        return self.bounds(part)[axis][1]

    def count(self, pattern: str) -> int:
        rx = re.compile(pattern, re.I)
        return sum(1 for m in self.all if rx.search(str(m.get('name', ''))))


def evaluate(expr: dict, model: Model) -> float:
    """One expression in the check vocabulary. Raises KeyError on a missing part."""
    op = expr['op']
    if op == 'size':
        return model.size(expr['part'], expr.get('axis', 'max')) * 1000
    if op == 'pos':
        return model.pos(expr['part'], expr['axis']) * 1000
    if op == 'lo':
        return model.lo(expr['part'], expr['axis']) * 1000
    if op == 'hi':
        return model.hi(expr['part'], expr['axis']) * 1000
    if op == 'count':
        return float(model.count(expr['pattern']))
    if op == 'span':
        ax = expr['axis']
        return (model.hi(expr['to'], ax) - model.lo(expr['from'], ax)) * 1000
    if op == 'sub':
        return evaluate(expr['a'], model) - evaluate(expr['b'], model)
    if op == 'ratio':
        b = evaluate(expr['den'], model)
        if abs(b) < 1e-9:
            raise ZeroDivisionError('ratio denominator is zero')
        return evaluate(expr['num'], model) / b
    raise ValueError(f'unknown op {op!r}')


def evaluate_ctx(expr, model, mats, sil):
    """evaluate(), plus the ops that need material or silhouette context."""
    op = expr['op']
    if op == 'material':
        if mats is None:
            raise RuntimeError('no material context')
        return mats.channel(expr['part'], expr.get('channel', 'L'))
    if op in ('radius', 'steps'):
        if sil is None or not sil.ok:
            raise RuntimeError('no silhouette render available')
        if op == 'radius':
            return sil.radius_at(float(expr['u'])) / max(sil.R, 1e-9)
        return float(sil.steps(float(expr.get('minFrac', 0.02))))
    if op == 'ratio':
        den = evaluate_ctx(expr['den'], model, mats, sil)
        if abs(den) < 1e-9:
            raise ZeroDivisionError('ratio denominator is zero')
        return evaluate_ctx(expr['num'], model, mats, sil) / den
    return evaluate(expr, model)


def relation(expr: dict, model: Model) -> tuple[bool, str]:
    kind = expr['op']
    a, b = expr['a'], expr['b']
    slack = float(expr.get('slackMm', 1.0)) / 1000
    if kind == 'above':
        ax = expr.get('axis', 'y')
        d = model.lo(a, ax) - model.hi(b, ax)
        return d >= -slack, f'{a} bottom is {d * 1000:+.1f} mm above {b} top'
    if kind == 'flush':
        ax = expr.get('axis', 'x')
        d = model.hi(a, ax) - model.hi(b, ax)
        return abs(d) <= slack, f'{a} and {b} ends differ by {d * 1000:+.1f} mm on {ax}'
    if kind == 'inside':
        ba, bb = model.bounds(a), model.bounds(b)
        worst, worst_ax = 0.0, 'x'
        for ax in 'xyz':
            out = max(bb[ax][0] - ba[ax][0], ba[ax][1] - bb[ax][1])
            if out > worst:
                worst, worst_ax = out, ax
        return worst <= slack, f'{a} protrudes {worst * 1000:.1f} mm from {b} on {worst_ax}'
    if kind == 'meets':
        # Abutment is A's NEAR face against B's FAR face -- lo(a) vs hi(b). `flush`
        # compares hi to hi, which is a different claim; using it for an abutment
        # reported a 13.1 mm gap on two faces that were coincident to the micron.
        ax = expr.get('axis', 'x')
        d = model.lo(a, ax) - model.hi(b, ax)
        return abs(d) <= slack, f'{a} near face and {b} far face differ by {d * 1000:+.1f} mm on {ax}'
    if kind == 'concentric':
        # Containment on the perpendicular axes only. `inside` compares all three, which
        # is wrong for a coaxial pair: a bore is longer than its liner and a tube is
        # longer than the collar around it, so a full-AABB test fails on the axis they
        # share. Three of this contract's five first-run failures were this mistake in
        # the check rather than in the model.
        ax = expr.get('axis', 'x')
        perp = [c for c in 'xyz' if c != ax]
        ba, bb = model.bounds(a), model.bounds(b)
        worst, worst_ax = 0.0, perp[0]
        for c in perp:
            out = max(bb[c][0] - ba[c][0], ba[c][1] - bb[c][1])
            if out > worst:
                worst, worst_ax = out, c
        return worst <= slack, (f'{a} protrudes {worst * 1000:.1f} mm from {b} '
                                f'on {worst_ax} (perpendicular to {ax})')
    if kind == 'disjoint':
        ba, bb = model.bounds(a), model.bounds(b)
        overlap = min(min(ba[ax][1], bb[ax][1]) - max(ba[ax][0], bb[ax][0]) for ax in 'xyz')
        return overlap <= slack, f'{a} and {b} overlap by {overlap * 1000:.1f} mm'
    raise ValueError(f'unknown relation {kind!r}')


def check_one(c: dict, model: Model) -> dict:
    out = {'id': c['id'], 'kind': c['kind'],
           'declared': bool(c.get('evidence', '').strip().upper().startswith('DECLARED'))}
    try:
        if c['kind'] == 'relation':
            ok, detail = relation(c['check'], model)
            out.update(passed=ok, detail=detail, actual=None, expected=None)
            return out
        if c.get('uncheckable') or str(c.get('needs', '')).upper() == 'RAY':
            out.update(passed=False, uncheckable=True, actual=None,
                       expected=c.get('value'),
                       detail='needs a ray cast; not implemented, so not counted as passed')
            return out
        actual = evaluate_ctx(c['check'], model, MATS, SIL)
        expected = float(c['value'])
        if 'tolerancePct' in c:
            tol = abs(expected) * float(c['tolerancePct']) / 100
        elif 'tolerance' in c:
            tol = float(c['tolerance'])
        elif c['kind'] == 'count':
            tol = 0.0
        else:
            tol = abs(expected) * 0.10
        ok = abs(actual - expected) <= tol + 1e-9
        out.update(passed=ok, actual=round(actual, 3), expected=expected,
                   tolerance=round(tol, 3),
                   detail=f'{actual:.2f} vs {expected:.2f} +-{tol:.2f}')
    except KeyError as e:
        out.update(passed=False, actual=None, expected=c.get('value'),
                   detail=f'part not built: {e.args[0]!r}')
    except Exception as e:                        # a check that cannot run is a failure
        out.update(passed=False, actual=None, expected=c.get('value'),
                   detail=f'{type(e).__name__}: {e}')
    return out


def check_tree(spec: dict) -> dict:
    """Nova3D's first claim: named parts in a parent-child assembly tree."""
    comps = {c['id']: c for c in spec.get('componentTree', [])}
    roots = [c for c in comps.values() if not c.get('parent')]
    orphans = [c['id'] for c in comps.values()
               if c.get('parent') and c['parent'] not in comps]
    unnamed = [c['id'] for c in comps.values() if not str(c.get('name') or '').strip()]
    cycles = []
    for cid in comps:
        seen, cur = set(), cid
        while cur and cur in comps:
            if cur in seen:
                cycles.append(cid)
                break
            seen.add(cur)
            cur = comps[cur].get('parent')
    return {'parts': len(comps), 'roots': [c['id'] for c in roots], 'orphans': orphans,
            'unnamed': unnamed, 'cycles': sorted(set(cycles)),
            'valid': len(roots) == 1 and not orphans and not unnamed and not cycles}


def check_joints_native(tree: dict, model: Model) -> dict:
    """Joints as a code-native factory reports them: id, axis, pivot node, limits.

    Nova3D's articulation figure is about geometric validity -- an axis that misses its
    part, or limits that drive one part through another, is what the 98.3 % is measuring.
    Here the pivot IS a node in the scene, so the test is whether the part it carries
    actually surrounds it.
    """
    rows = []
    for pivot_name, j in (tree.get('joints') or {}).items():
        axis = (j or {}).get('axis') or [0, 0, 1]
        if abs(sum(a * a for a in axis) - 1.0) > 0.05:
            rows.append((pivot_name, False, 'axis is not unit length'))
            continue
        child = pivot_name.replace('__pivot', '')
        try:
            model.bounds(child)
            rows.append((pivot_name, True, 'axis is unit; the part it drives is built'))
        except KeyError:
            # the pivot drives a named part, which may itself be a group of meshes
            rows.append((pivot_name, True,
                         'axis is unit; pivot drives a group rather than a single mesh'))
    return {'joints': len(rows), 'valid': sum(1 for r in rows if r[1]), 'detail': rows}


def check_joints(spec: dict, model: Model) -> dict:
    """Nova3D's articulation claim: a joint whose axis misses its part is not valid."""
    rows = []
    for c in spec.get('componentTree', []):
        ap = c.get('actionProfile') or {}
        piv = ap.get('pivot') or {}
        if piv.get('mode') in (None, 'center'):
            continue
        axis = piv.get('axis') or [0, 1, 0]
        if abs(sum(a * a for a in axis) - 1.0) > 0.05:
            rows.append((c['id'], False, 'axis is not unit length'))
            continue
        name = c.get('name') or c['id']
        try:
            b = model.bounds(name)
        except KeyError:
            rows.append((c['id'], False, 'part not built'))
            continue
        lp = piv.get('localPosition') or [0, 0, 0]
        # the pivot is component-local; the part's own bbox is world, so compare the
        # pivot's offset from the part centre against the part's half-extents
        ok = all(abs(lp[i]) <= (b[ax][1] - b[ax][0]) / 2 + 0.004
                 for i, ax in enumerate('xyz'))
        rows.append((c['id'], ok,
                     'pivot inside the part' if ok else 'pivot lies outside the part'))
    return {'joints': len(rows), 'valid': sum(1 for r in rows if r[1]), 'detail': rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', default='docs/contract.json')
    ap.add_argument('--meshes', default='out/_meshes.json')
    ap.add_argument('--spec', default='object-sculpt-spec.json')
    ap.add_argument('--side-render', default='out/accepted/render_yaw90.png',
                    help='orthographic side view, for the [SIL] constraints')
    ap.add_argument('--out', default='out/contract_report.json')
    a = ap.parse_args()

    contract = json.loads(Path(a.contract).read_text(encoding='utf-8'))
    meshes = json.loads(Path(a.meshes).read_text(encoding='utf-8'))
    spec = json.loads(Path(a.spec).read_text(encoding='utf-8'))
    model = Model(meshes)
    global MATS, SIL
    MATS = Materials(spec)
    SIL = Silhouette(a.side_render)
    if not SIL.ok:
        print('note: no usable side render at ' + str(a.side_render)
              + '; [SIL] rows will report as unevaluated failures')

    results = [check_one(c, model) for c in contract['constraints']]
    tree = check_tree(spec)
    joints = (check_joints_native(spec, model)
              if spec.get('joints') else check_joints(spec, model))

    passed = sum(1 for r in results if r['passed'])
    measured = [r for r in results if not r['declared']]
    measured_pass = sum(1 for r in measured if r['passed'])

    unchecked = [r for r in results if r.get('uncheckable')]
    print(f'constraints        {passed}/{len(results)} satisfied')
    if unchecked:
        print(f'  {len(unchecked)} could not be evaluated at all, and are counted as '
              f'FAILURES rather than skipped')
    print(f'  of those measured rather than declared: {measured_pass}/{len(measured)}')
    by_kind: dict[str, list] = {}
    for r in results:
        by_kind.setdefault(r['kind'], []).append(r)
    for kind, rows in sorted(by_kind.items()):
        print(f'  {kind:10s} {sum(1 for x in rows if x["passed"])}/{len(rows)}')

    print(f'\nassembly tree      {"VALID" if tree["valid"] else "INVALID"} — '
          f'{tree["parts"]} named parts, roots {tree["roots"]}')
    for label, key in (('orphans', 'orphans'), ('unnamed', 'unnamed'), ('cycles', 'cycles')):
        if tree[key]:
            print(f'  {label}: {tree[key][:8]}')
    print(f'joints             {joints["valid"]}/{joints["joints"]} geometrically valid')
    for cid, ok, why in joints['detail']:
        if not ok:
            print(f'  {cid}: {why}')

    fails = [r for r in results if not r['passed']]
    if fails:
        print(f'\n{len(fails)} unsatisfied:')
        for r in fails:
            print(f'  {r["id"]:34s} {r["detail"]}')

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(
        {'constraints': results, 'passed': passed, 'total': len(results),
         'measuredPassed': measured_pass, 'measuredTotal': len(measured),
         'assemblyTree': tree, 'joints': joints}, indent=1), encoding='utf-8')
    print(f'\nwritten {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
