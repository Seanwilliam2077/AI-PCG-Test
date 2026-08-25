"""Width term: correct the silhouette cross-section per height, and close the internal
gaps that the scored channel actually punishes.

WHAT WAS MEASURED  (all of it re-derived at runtime; nothing below is hard-coded)

The judge scores `20 * mean_views(exp(-width_rms_core_pct / 2))`, and `core` is the
width of the WIDEST CONTIGUOUS RUN in a row, not the leftmost-to-rightmost span. The
build's own local metric (tools/evaluate.py) measures the span, so it has been reading
a channel nobody scores: span RMS 3.00 pct and improving across the ledger, run RMS
4.05 pct and flat. Every patch so far moved outer envelopes; none moved an internal
gap. Reproduced exactly from `baseline/metrics_accepted.json`: per-view core RMS
3.619 / 4.188 / 3.299 / 4.901 / 4.455 / 3.838 pct, width term 2.7330 of 20.

Splitting the 240 band errors by run count, 49 pct of the squared error is bands where
the reference is one run and the render is two or three, and the offending gaps are
hairline -- 3 to 25 mm of world. Because `core` takes the widest run the response is
binary: a 4 mm gap costs exactly what a 60 mm one costs. Two gaps carry nearly all of
it, and both are visible in `baseline/meshes_accepted.json`:

  * the braid chain hangs 3-25 mm clear of the back from y 0.75 to 1.23 (bands 17-28,
    both side views, ref nrun 1.0 against render 2.0);
  * the gloved forearms stand 8-24 mm clear of the waist at y 0.80, 0.97 and 1.10
    (bands 18, 22, 25, both front and back views).

For the continuous part the six panels are decomposed BY AXIS rather than fitted by
least squares over all yaws, because a 180-degree pair of one rigid body has identical
width profiles -- so yaw 0/180 measure X alone and yaw 90/270 measure Z alone, exactly,
with no conditioning problem and no 45-degree support-function approximation. Our own
renders satisfy that identity to 0-2 mm, which is the check that the thing being
corrected really is rigid. The reference panels do not satisfy it: the two panels of a
pair disagree by up to 156 mm in the legs and by 3-34 mm in the trunk. That
disagreement is used as the reliability weight, so where the reference contradicts
itself by more than the correction, the correction is damped away.

What survives the weighting is one coherent story: the trunk is about 13 pct too deep
from y 1.0 to 1.4 (ref/render 0.87, 0.86, 0.90, 0.87, 0.85, 0.83, 0.85, with the two
panels agreeing to 3-13 mm), and the hips and waist are 4-30 pct too narrow from
y 0.84 to 1.14 (panels agreeing to 8-24 mm).

WHAT THIS CHANGES

1. A per-height anisotropic size field on the body / garment / footwear components
   only. X and Z are corrected independently for components that have independent
   width and depth: every implicit component here carries transform.scale [1,1,1], so
   scale_vector() emits 1.0 and its SDF primitives are already in metres 1:1 -- a ring's
   radii[0] and radii[2] are edited directly, ring by ring, each at its own world
   height, which is what makes this a profile and not a scale. Components that are
   swept cylinders have a circular cross-section and no independent depth (spec rule
   2), so they take the geometric mean sqrt(fX*fZ), applied separately to baseRadius
   and endRadius at their own two heights so the taper carries the profile.
   No global factor is applied anywhere: earlier rounds already spent blob depth x1.33,
   blob width x1.12 and limb radius x1.19, and a per-band correction laid on top of a
   global one double-counts.
   Offsets scale with sizes, not only radii. A per-height scale that moves a surface
   but not the detail glued to it slides the detail off: shrinking the top's depth
   while leaving x-lacing at its old z left the brass lacing 2 mm proud of the top and
   split the side silhouette in two at bands 30-31 -- the patch inventing a fresh
   instance of the defect it exists to remove. transform.position X and Z therefore
   take the same factor.
2. The braid is one chain of shared endpoints -- braid-l.localEnd IS braid-l-2.localStart
   -- so it is translated forward in +Z as a chain, by a piecewise-linear shift fitted
   over the chain's own nodes to the closure each flagged band needs, with every node
   that does not terminate a segment spanning a flagged band pinned at zero so the
   tassels and the crown stay put. Fitted here: +25.8 mm at y 0.902, +11.2 at 0.949,
   +12.6 at 0.981, +16.3 at 1.394, leaving 4.6 mm mean residual on 11 flagged bands.
3. The gaps still open after that are closed by extending the body-side surface toward
   the other side -- the pelvis / hip-belt / abdomen / chest / top rings grow rearward
   to meet the braid and outward to meet the glove. This does not move the outer
   envelope, because the braid and the glove are the outermost surfaces at those
   heights; it only merges two runs into one, which is the whole of the scored defect.
   The same sweep also closes any hairline gap under 8 mm against a one-run reference,
   whether or not the judge already flagged it, which is what catches a contact the
   size field itself has just broken.

DAMPING, and why this number

lam = 0.60 on the size field, a reliability weight 1/(1+(panel_disagreement/25mm)^2),
and a hard cap of 10 pct per component per axis. Three reasons, largest first.
  (a) The map from a declared radius to the rendered silhouette is not the identity.
      The implicit path is a voxel surface at 3-4 mm, smooth-union bulges outside the
      primitive envelope, and quadric decimation pulls the surface back in. The
      geometry model in this file reproduces the judge's own rendered envelope to about
      2 pct over y 0.24-1.40 and no better, so a full correction would be applying a
      number the model cannot resolve.
  (b) Half of the six views are not a rigid turnaround of one pose, so the target is a
      compromise between panels that disagree; a full correction chases that noise.
  (c) The shape term carries weight 0.30 and is this build's lead. Every edit here
      moves the silhouette that IoU scores, so the correction is deliberately short.
The contact edits in steps 2 and 3 are NOT damped. A gap either closes or it does not,
and a damped contact is worth exactly nothing.

lam was chosen by sweeping the whole patch end to end -- re-running it at each setting
and re-scoring the resulting spec on the judge's bands. 0.0 gives +0.34, 0.40 +0.56,
0.60 +0.59, 0.80 +0.55, 1.00 with cap 0.20 +0.69. The curve is flat from 0.4 upward, so
0.60 buys essentially all of it at the smallest displacement of a silhouette the shape
term is currently winning on.

TRIANGLE COST: about -1,100, i.e. it gives budget back. Swept cylinders take their
radial segment count from the spec rather than from their radius, so only the implicit
components can move at all, and for those, bounds are scaled by the same mean factor as
the primitives, which leaves the voxel grid proportional and the occupancy alone. The
counts printed at the end are exact, not estimated: raw triangles are two per exposed
voxel face of polygonizeSdf, times geometryDescriptor.decimate.targetRatio, which
reproduces every implicit entry of baseline/meshes_accepted.json to the rounding.

EXPECTED MEASURABLE EFFECT, stated so it can be falsified

The prediction is not a hand wave: the patched spec was pushed back through the same
geometry model, projected to all six yaws, and scored on the judge's own bands and
reference profiles. On the UNPATCHED spec that end-to-end model returns width 2.8043
where the judge returns 2.7330, and per-view core RMS 3.24/4.46/3.05/4.95/4.23/4.35
against the judge's 3.62/4.19/3.30/4.90/4.45/3.84 -- close enough to steer with, not
close enough to quote to three places.

  * The judge's width term should rise from 2.733 to between 3.2 and 3.7 of 20. The
    model says 3.395 with its per-band bias divided out and 3.700 without. Splitting
    the patch: the contact edits alone are worth +0.34 and the size field adds +0.25,
    so if the result lands near 3.1 the size field did nothing and only the contacts
    landed; if it lands below 2.9 the contacts did not land either.
  * `width_rms_core_pct` should fall in ALL SIX views, and most in render_yaw90 and
    render_yaw270 (3.299 and 4.455 now, driven 53-68 pct by the braid split). Model
    per-view after: 3.19 / 4.11 / 2.49 / 4.51 / 3.85 / 3.80.
  * `profile.render.nrun` should read 1.0 at bands 19-21 and 24-28 of render_yaw90 and
    render_yaw270, and at bands 25-26 of render_yaw0 and render_yaw180. This is the
    sharpest test in the list: if those bands still read 2.0 or 3.0 then the contact
    edits missed and anything that moved is the size field alone.
  * Silhouette IoU should hold or rise: every size change moves our envelope toward the
    panel consensus, and closing an internal gap adds area the reference has there. If
    IoU falls by more than 0.005 the size field overshot, and the answer is to halve
    lam and re-run, not to tune the result after the fact.
  * Bands 17 and 18 of the side views will NOT be fixed, and the model says so: the
    braid still stands 6 and 10 mm clear of the body at y 0.75 and 0.80 afterwards. The
    only components at that height are the trouser and thigh cylinders, which cannot
    gain depth without gaining the same width, and the width at the knee is already too
    big. The braid tilt recovers about half. Closing the rest needs a new rear
    component, which is a larger change than a width patch should be making.
  * The clearest place this can be wrong is band 20 of the front and back views. The
    judge measures our widest run there at 310 mm against a 382 mm reference and the
    panels agree to 8 mm, so the field widens the hips 10 pct; but this file's own
    geometry model already puts that run at 382 mm, and if the model is right rather
    than the judge, band 20 gets worse by about 70 mm instead of better by 70 mm. Every
    other band the two agree on.

WHY THE REFERENCE PANELS ARE READ THROUGH THE JUDGE. `ref/views/clay_*.png` is not
opened here. The judge's own `profile.ref` block is a measurement OF those panels --
full, core, sum and run count at 40 bands, taken with the matte, the crop, the
1024-normalise and the per-band median it scores with. A previous round wrote its own
detector against the panels and it asked for the knee to drop 60 mm and the calf to
rise 60 mm in one pass. Reading the judge's numbers removes a whole class of that.

IDEMPOTENCE. Every field this patch writes is recorded, with its pre-patch value, under
the spec key `widthProfilePatchV2`. Each run restores those values first and then
recomputes from the measurement files, so a second run is a no-op and a re-run after
the measurements change is a clean re-fit rather than a compounding one. The restore
only touches fields this patch owns; if another patch later edits one of the same
fields and this patch is then re-run, the restore wins, which is why the key names them.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
JUDGE = ROOT / 'baseline/metrics_accepted.json'
MESHES = ROOT / 'baseline/meshes_accepted.json'

SNAP_KEY = 'widthProfilePatchV2'
NB = 40
LAMBDA = 0.60          # fraction of the measured size error applied in one pass
TRUST_MM = 25.0        # panel disagreement at which a band's target is worth half
CAP = 0.10             # no component may change by more than this on one axis
MAX_CONTACT_M = 0.045  # a single contact edit may not move a surface further than this
MAX_BRAID_M = 0.030    # nor a braid node further than this
MIN_ACT_M = 0.0025     # below 2.5 mm (1.5 judge px) nothing is worth writing
MIN_FACTOR = 0.004     # nor is a size change below 0.4 pct
HAIRLINE_M = 0.008     # a gap this small against a one-run reference is closed on sight

# The body volume: the components that compose the scored CORE run. Arms, hands,
# gloves, the zapper, the braids, the head and the hair are deliberately absent -- they
# own the outer envelope, not the scored run, and their placement belongs to the
# landmark, hair and prop dimensions.
WHITELIST = {
    'pelvis', 'abdomen', 'chest', 'hip-belt', 'sash', 'canvas-panel', 'pouch',
    'diagonal-strap', 'top', 'top-band', 'top-strap', 'x-lacing',
    'thigh-l', 'thigh-r', 'shin-l', 'shin-r', 'pants-l', 'pants-r',
    'pants-hem-l', 'pants-hem-r', 'thigh-strap', 'foot-l', 'foot-r',
    'boot-l', 'boot-r', 'boot-toecap', 'boot-toecap-r', 'boot-lace', 'boot-lace-r',
    'shin-patch',
}
# `tattoo-region` is deliberately not in that set: it is an interior volume that carries
# the cloud-tattoo material and never sets the silhouette, so resizing it only risks
# pushing tattoo texels through the chest into a view that should not see them.

# The braid is one chain of shared endpoints -- braid-l.localEnd IS braid-l-2.localStart
# -- so it is moved as a chain, by a shift that is a function of height, or it comes
# apart at the joins.
BRAID_CHAIN = ('braid-l', 'braid-l-2', 'braid-l-3', 'braid-l-4', 'braid-l-5', 'braid-l-6',
               'braid-r', 'braid-r-2', 'braid-r-3', 'braid-r-4', 'braid-r-5', 'braid-r-6',
               'braid-ties')


# --------------------------------------------------------------------------- geometry
def _euler(r):
    cx, cy, cz = (math.cos(v) for v in r)
    sx, sy, sz = (math.sin(v) for v in r)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rx @ ry @ rz


def _fib(n=240):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1)


_SP = _fib()


def prim_points(p):
    """A surface point cloud for one SDF primitive, in the descriptor's own frame."""
    t = p['type']
    tr = p.get('transform') or {}
    c = np.array(p.get('center') or tr.get('position') or [0, 0, 0], float)
    rot = _euler(tr.get('rotation') or [0, 0, 0])
    sc = np.array(tr.get('scale') or [1, 1, 1], float)
    if t == 'sphere':
        pts = _SP * float(p['radius'])
    elif t == 'ellipsoid':
        pts = _SP * np.array(p['radii'], float)
    elif t == 'box':
        s = np.array(p['size'], float) / 2
        g = np.linspace(-1, 1, 7)
        a, b = np.meshgrid(g, g)
        a, b = a.ravel(), b.ravel()
        o = np.ones_like(a)
        pts = np.concatenate([np.stack([o, a, b], 1), np.stack([-o, a, b], 1),
                              np.stack([a, o, b], 1), np.stack([a, -o, b], 1),
                              np.stack([a, b, o], 1), np.stack([a, b, -o], 1)]) * s
    elif t == 'capsule':
        r = float(p['radius'])
        h = float(p.get('height', 1))
        th = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        ys = np.linspace(-h / 2, h / 2, 9)
        a, y = np.meshgrid(th, ys)
        pts = np.stack([r * np.cos(a).ravel(), y.ravel(), r * np.sin(a).ravel()], 1)
        pts = np.concatenate([pts, _SP * r + [0, h / 2, 0], _SP * r + [0, -h / 2, 0]])
    elif t == 'cone':
        r = float(p['radius'])
        h = float(p.get('height', 1))
        th = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        ts = np.linspace(0, 1, 9)
        a, tt = np.meshgrid(th, ts)
        rr = (r * (1 - tt)).ravel()
        pts = np.stack([rr * np.cos(a).ravel(), -h / 2 + tt.ravel() * h, rr * np.sin(a).ravel()], 1)
    else:
        pts = np.zeros((1, 3))
    return (rot @ (pts * sc).T).T + c


def sdf_points(sdf):
    """Surface cloud of the whole CSG tree. The last operation is the output."""
    prims = {p['id']: p for p in sdf['primitives']}
    ops = {o['id']: o for o in (sdf.get('operations') or [])}
    cache = {}

    def ev(i):
        if i in cache:
            return cache[i]
        if i in prims:
            r = prim_points(prims[i])
        else:
            o = ops[i]
            a = ev(o['left'])
            if o['type'] == 'subtract':
                r = a
            elif o['type'] == 'intersect':
                b = prims.get(o['right'])
                r = a
                if b is not None and b['type'] == 'box':
                    tr = b.get('transform') or {}
                    c = np.array(b.get('center') or tr.get('position') or [0, 0, 0], float)
                    rot = _euler(tr.get('rotation') or [0, 0, 0])
                    s = np.array(b['size'], float) / 2
                    loc = (a - c) @ rot
                    keep = a[np.all(np.abs(loc) <= s + 1e-9, axis=1)]
                    if len(keep):
                        r = keep
            else:
                r = np.concatenate([a, ev(o['right'])])
        cache[i] = r
        return r

    ol = sdf.get('operations') or []
    root = ol[-1]['id'] if ol else sdf['primitives'][0]['id']
    return ev(root)


def cyl_points(att):
    """A component WITH an attachment is a tapered cylinder swept localStart->localEnd."""
    s = np.array(att['localStart'], float)
    e = np.array(att['localEnd'], float)
    rb = att.get('baseRadius') or 0.0
    re = att.get('endRadius') or rb
    d = e - s
    length = float(np.linalg.norm(d))
    if length < 1e-6:
        return np.zeros((1, 3))
    u = d / length
    a = np.array([0.0, 1.0, 0.0])
    if abs(float(u @ a)) > 0.95:
        a = np.array([1.0, 0.0, 0.0])
    v1 = np.cross(u, a)
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(u, v1)
    th = np.linspace(0, 2 * math.pi, 28, endpoint=False)
    out = []
    for t in np.linspace(0, 1, 17):
        r = rb + (re - rb) * t
        out.append(t * d + r * (np.cos(th)[:, None] * v1 + np.sin(th)[:, None] * v2))
    return np.concatenate(out)


def scale_vector(c):
    """Mirror of the emitter: transform.scale wins, dimensions otherwise."""
    tr = c['transform']
    if 'scale' in tr and isinstance(tr.get('scale'), list):
        return np.array(tr['scale'], float)
    dim = c.get('dimensions') or {}
    return np.array([dim.get('width') or 1, dim.get('height') or 1, dim.get('depth') or 1], float)


def world_model(spec):
    """World surface cloud and frame for every component; positions accumulate."""
    origin, rot, pts = {}, {}, {}
    for c in spec['componentTree']:
        cid = c['id']
        po = origin.get(c.get('parent'), np.zeros(3))
        pr = rot.get(c.get('parent'), np.eye(3))
        att = c.get('attachment')
        loc = np.array(att['localStart'], float) if att else np.array(c['transform']['position'], float)
        r = pr @ _euler(c['transform'].get('rotation') or [0, 0, 0])
        o = po + pr @ loc
        origin[cid], rot[cid] = o, r
        gd = c.get('geometryDescriptor') or {}
        sdf = gd.get('sdf')
        if c.get('topologyClass') == 'implicit' and sdf:
            p = sdf_points(sdf) * scale_vector(c)
        elif att:
            p = cyl_points(att)
        else:
            dim = c.get('dimensions') or {}
            h = np.array([dim.get('width') or 1e-3, dim.get('height') or 1e-3,
                          dim.get('depth') or 1e-3], float)
            p = _SP * (h / 2) if c.get('primitive') in ('ellipsoid', 'sphere') \
                else prim_points({'type': 'box', 'size': list(h)})
        pts[cid] = (r @ p.T).T + o
    return origin, rot, pts


# ------------------------------------------------------------------ triangle accounting
def _prim_sdf(pt, p):
    tr = p.get('transform') or {}
    c = np.array(p.get('center') or tr.get('position') or [0, 0, 0], float)
    rot = _euler(tr.get('rotation') or [0, 0, 0])
    q = (pt - c) @ rot
    s = 1.0
    if tr.get('scale'):
        sv = np.array(tr['scale'], float)
        q = q / sv
        s = float(np.min(np.abs(sv)))
    t = p['type']
    if t == 'sphere':
        d = np.linalg.norm(q, axis=1) - float(p['radius'])
    elif t == 'ellipsoid':
        r = np.array(p['radii'], float)
        k0 = np.linalg.norm(q / r, axis=1)
        k1 = np.linalg.norm(q / (r * r), axis=1)
        d = np.where(k0 > 0, k0 * (k0 - 1) / np.maximum(k1, 1e-12), -float(np.min(r)))
    elif t == 'box':
        b = np.array(p['size'], float) / 2
        a = np.abs(q) - b
        d = np.linalg.norm(np.maximum(a, 0), axis=1) + np.minimum(np.max(a, axis=1), 0)
    elif t == 'capsule':
        r = float(p['radius'])
        h = float(p.get('height', 1))
        y = np.clip(q[:, 1], -h / 2, h / 2)
        d = np.linalg.norm(q - np.stack([np.zeros_like(y), y, np.zeros_like(y)], 1), axis=1) - r
    elif t == 'cone':
        r = float(p['radius'])
        h = float(p.get('height', 1))
        rad = np.linalg.norm(q[:, [0, 2]], axis=1)
        d = np.maximum(rad - r * (0.5 - q[:, 1] / h), np.abs(q[:, 1]) - h / 2)
    else:
        d = np.full(len(q), 1e9)
    return d * s


def _smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def sdf_tris(sdf):
    """Exact triangle count of polygonizeSdf: two per exposed voxel face."""
    n = max(4, min(64, int(sdf.get('resolution', 32))))
    b = sdf.get('bounds') or {'min': [-2, -2, -2], 'max': [2, 2, 2]}
    mn = np.array(b['min'], float)
    step = (np.array(b['max'], float) - mn) / n
    ax = [mn[k] + (np.arange(n) + 0.5) * step[k] for k in range(3)]
    zz, yy, xx = np.meshgrid(ax[2], ax[1], ax[0], indexing='ij')
    pt = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], 1)
    nodes = {p['id']: _prim_sdf(pt, p) for p in sdf['primitives']}
    res = nodes[sdf['primitives'][0]['id']] if sdf['primitives'] else np.zeros(len(pt))
    for i, o in enumerate(sdf.get('operations') or []):
        left, right = nodes.get(o['left']), nodes.get(o['right'])
        if left is None or right is None:
            continue
        if o['type'] == 'smooth-union':
            v = _smin(left, right, o.get('radius', 0.1))
        elif o['type'] == 'subtract':
            v = np.maximum(left, -right)
        elif o['type'] == 'intersect':
            v = np.maximum(left, right)
        else:
            continue
        nodes[o.get('id') or 'op%d' % i] = v
        res = v
    ins = (res <= 0).reshape(n, n, n)
    faces = 0
    for axis in (0, 1, 2):
        for sh in (1, -1):
            nb = np.roll(ins, sh, axis=axis)
            sl = [slice(None)] * 3
            sl[axis] = 0 if sh == 1 else -1
            nb[tuple(sl)] = False
            faces += int(np.count_nonzero(ins & ~nb))
    return 2 * faces


def component_tris(c):
    gd = c.get('geometryDescriptor') or {}
    sdf = gd.get('sdf')
    if not (c.get('topologyClass') == 'implicit' and sdf):
        return None
    ratio = (gd.get('decimate') or {}).get('targetRatio')
    raw = sdf_tris(sdf)
    return int(round(raw * ratio)) if isinstance(ratio, (int, float)) else raw


# --------------------------------------------------------------------------- snapshot
def _find(spec, cid):
    for c in spec['componentTree']:
        if c['id'] == cid:
            return c
    return None


def _resolve(spec, path):
    """`compid|key|key|3|key` -> (container, last key). Keyed by id, not by index,
    so another patch reordering the component tree cannot misdirect the restore."""
    parts = path.split('|')
    node = _find(spec, parts[0])
    if node is None:
        raise KeyError(parts[0])
    for k in parts[1:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = parts[-1]
    return node, (int(last) if isinstance(node, list) else last)


class Journal:
    """Records every field written, with its pre-patch value, so the patch is exactly
    idempotent: restore, re-measure, re-apply."""

    def __init__(self, spec):
        self.spec = spec
        self.orig = {}

    def restore(self):
        snap = self.spec.pop(SNAP_KEY, None)
        if not snap:
            return 0
        n = 0
        for path, val in snap.get('originals', {}).items():
            try:
                node, key = _resolve(self.spec, path)
                node[key] = val
                n += 1
            except (KeyError, IndexError, TypeError):
                pass
        return n

    def set(self, path, value):
        node, key = _resolve(self.spec, path)
        if path not in self.orig:
            self.orig[path] = node[key]
        node[key] = value

    def commit(self, note):
        self.spec[SNAP_KEY] = {
            'version': 2,
            'writtenBy': 'analysis/patch_width_v2.py',
            'measuredFrom': ['baseline/metrics_accepted.json', 'baseline/meshes_accepted.json'],
            'note': note,
            'originals': self.orig,
        }
        return len(self.orig)


# ------------------------------------------------------------------------- measurement
def measure():
    judge = json.loads(JUDGE.read_text(encoding='utf-8'))
    meshes = json.loads(MESHES.read_text(encoding='utf-8'))
    ymin = min(m['minY'] for m in meshes)
    height = max(m['maxY'] for m in meshes) - ymin
    mpp = height / 1024.0
    prof = {int(v['yaw']): v['geometry']['profile'] for v in judge['views']}
    missing = [y for y in (0, 90, 180, 270) if y not in prof]
    if missing:
        raise SystemExit('judge file is missing yaws %s; the axis decomposition needs '
                         'both members of each 180-degree pair' % missing)

    def arr(y, side, ch):
        return np.array(prof[y][side][ch], float)

    axes = {}
    for name, (a, b) in (('X', (0, 180)), ('Z', (90, 270))):
        ref_core = (arr(a, 'ref', 'core') + arr(b, 'ref', 'core')) / 2
        ref_nrun = (arr(a, 'ref', 'nrun') + arr(b, 'ref', 'nrun')) / 2
        ren_core = (arr(a, 'render', 'core') + arr(b, 'render', 'core')) / 2
        ren_full = (arr(a, 'render', 'full') + arr(b, 'render', 'full')) / 2
        ren_sum = (arr(a, 'render', 'sum') + arr(b, 'render', 'sum')) / 2
        ren_nrun = (arr(a, 'render', 'nrun') + arr(b, 'render', 'nrun')) / 2
        dis = np.abs(arr(a, 'ref', 'core') - arr(b, 'ref', 'core')) * mpp
        split = (ren_nrun >= 1.5) & (ref_nrun < 1.5)
        # where a gap is about to be closed the scored run becomes the whole span, so
        # the size target is measured against the span, not against today's core
        eff = np.where(split, ren_full, ren_core)
        raw = ref_core / np.maximum(eff, 1e-6)
        trust = 1.0 / (1.0 + (dis * 1000.0 / TRUST_MM) ** 2)
        f = np.clip(1.0 + LAMBDA * trust * (raw - 1.0), 1 - CAP, 1 + CAP)
        axes[name] = dict(f=f, raw=raw, trust=trust, dis=dis, split=split, ref_nrun=ref_nrun,
                          gap=(ren_full - ren_sum) * mpp,
                          selfcheck=np.abs(arr(a, 'render', 'full') - arr(b, 'render', 'full')) * mpp)
    yb = ymin + (np.arange(NB) + 0.5) / NB * height
    edges = ymin + np.arange(NB + 1) / NB * height
    return dict(judge=judge, ymin=ymin, height=height, mpp=mpp, axes=axes, yb=yb, edges=edges)


def field(m, name, y):
    """The damped size factor for one axis at world height y, linear between bands."""
    return float(np.interp(y, m['yb'], m['axes'][name]['f']))


# ------------------------------------------------------------------------ edit helpers
def carve_ids(sdf):
    """Primitive ids that only subtract or clip, found transitively through the ops."""
    ops = {o['id']: o for o in (sdf.get('operations') or [])}
    prims = {p['id'] for p in sdf['primitives']}
    stack = [o['right'] for o in (sdf.get('operations') or [])
             if o['type'] in ('subtract', 'intersect')]
    seen, out = set(), set()
    while stack:
        i = stack.pop()
        if i in seen:
            continue
        seen.add(i)
        if i in prims:
            out.add(i)
        elif i in ops:
            stack += [ops[i]['left'], ops[i]['right']]
    return out


def is_clipper(p):
    """A 1.2 m box inside a 0.2 m component is a half-space cut, not a solid."""
    return p['type'] == 'box' and max(p['size']) > 1.0


def prim_axis_size(p, k):
    t = p['type']
    if t == 'sphere':
        return float(p['radius'])
    if t == 'ellipsoid':
        return float(p['radii'][k])
    if t == 'box':
        return float(p['size'][k]) / 2
    if t in ('capsule', 'cone'):
        return float(p.get('height', 1)) / 2 if k == 1 else float(p['radius'])
    return 0.0


def prim_centre(p, k):
    tr = p.get('transform') or {}
    c = p.get('center') or tr.get('position') or [0, 0, 0]
    return float(c[k])


def prim_world_y(cid, p, origin, rot, sv):
    local = np.array(p.get('center') or (p.get('transform') or {}).get('position') or [0, 0, 0], float)
    return float((rot[cid] @ (local * sv))[1] + origin[cid][1])


ISOTROPIC = ('sphere', 'capsule', 'cone')   # one radius, no independent X and Z


def set_prim_size(j, cid, idx, p, k, size):
    t = p['type']
    base = '%s|geometryDescriptor|sdf|primitives|%d' % (cid, idx)
    if t == 'sphere' or (t in ('capsule', 'cone') and k != 1):
        j.set(base + '|radius', round(size, 6))
    elif t == 'ellipsoid':
        j.set(base + '|radii|%d' % k, round(size, 6))
    elif t == 'box':
        j.set(base + '|size|%d' % k, round(size * 2, 6))


def set_prim_centre(j, cid, idx, p, k, centre):
    base = '%s|geometryDescriptor|sdf|primitives|%d' % (cid, idx)
    if p.get('center') is not None:
        j.set(base + '|center|%d' % k, round(centre, 6))
    elif (p.get('transform') or {}).get('position') is not None:
        j.set(base + '|transform|position|%d' % k, round(centre, 6))


def settle_bounds(j, cid, sdf, factor):
    """polygonizeSdf samples ONLY inside bounds and snaps the surface to that grid, so a
    widened primitive that outruns its bounds is silently sliced off -- and bounds that
    grow faster than the primitives coarsen the voxel and quietly delete triangles.

    Both failure modes are real here. Re-deriving bounds from the raw primitive envelope
    destroys pants-hem-l: its descriptor holds a 0.4 m clipping box and a 0.5 m tall
    carving ellipsoid inside 0.18 m bounds, and fitting to those blows the voxel from
    5 mm to 25 mm and the garment vanishes. Scaling bounds by the largest factor any
    primitive took costs the boots 10 pct of their triangles, because the field varies
    from 0.90 to 1.10 across their height.

    So: scale bounds by the MEAN factor, which keeps the voxel proportional and the
    triangle count stable, then take the union with the actual post-edit surface cloud,
    which accounts for intersect and subtract properly. Bounds therefore never shrink
    below the proportional grid and never clip the surface."""
    b = sdf['bounds']
    cloud = sdf_points(sdf)
    lo_c, hi_c = cloud.min(0) * 1.03, cloud.max(0) * 1.03
    for k in range(3):
        lo = min(b['min'][k] * factor[k], float(lo_c[k]))
        hi = max(b['max'][k] * factor[k], float(hi_c[k]))
        if abs(lo - b['min'][k]) > 1e-9:
            j.set('%s|geometryDescriptor|sdf|bounds|min|%d' % (cid, k), round(float(lo), 6))
        if abs(hi - b['max'][k]) > 1e-9:
            j.set('%s|geometryDescriptor|sdf|bounds|max|%d' % (cid, k), round(float(hi), 6))


def intervals_at(pts, ids, k, y0, y1):
    out = []
    for cid in ids:
        p = pts[cid]
        sel = (p[:, 1] >= y0) & (p[:, 1] < y1)
        if sel.any():
            q = p[sel]
            out.append([float(q[:, k].min()), float(q[:, k].max()), {cid}])
    return sorted(out, key=lambda r: r[0])


def merge_intervals(iv, eps=1e-4):
    out = []
    for lo, hi, owners in iv:
        if out and lo <= out[-1][1] + eps:
            out[-1][1] = max(out[-1][1], hi)
            out[-1][2] |= owners
        else:
            out.append([lo, hi, set(owners)])
    return out


# --------------------------------------------------------------------------------- main
def main() -> int:
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    comps = {c['id']: c for c in spec['componentTree']}
    j = Journal(spec)
    restored = j.restore()

    m = measure()
    ax_x, ax_z = m['axes']['X'], m['axes']['Z']

    print('== measured, on the judge\'s own 40 bands ==')
    print('figure height %.4f m; one judge pixel is %.3f mm of world'
          % (m['height'], m['mpp'] * 1000))
    print('rigidity self-check, our own 0/180 and 90/270 span disagreement:'
          '  median %.1f / %.1f mm,  max %.1f / %.1f mm'
          % (np.median(ax_x['selfcheck']) * 1000, np.median(ax_z['selfcheck']) * 1000,
             ax_x['selfcheck'].max() * 1000, ax_z['selfcheck'].max() * 1000))
    print('reference panel self-disagreement, which is the reliability weight:'
          '  median %.1f / %.1f mm,  max %.1f / %.1f mm'
          % (np.median(ax_x['dis']) * 1000, np.median(ax_z['dis']) * 1000,
             ax_x['dis'].max() * 1000, ax_z['dis'].max() * 1000))
    base_term = 20 * float(np.mean([math.exp(-v['geometry']['width_rms_core_pct'] / 2)
                                    for v in m['judge']['views']]))
    print('width term now %.4f of 20; per-view core RMS %s pct'
          % (base_term, ' '.join('%.2f' % v['geometry']['width_rms_core_pct']
                                 for v in m['judge']['views'])))
    print()
    print('band   Y(m)    fX     fZ    raw ref/render   trust     split   judge gap mm')
    for i in range(NB):
        quiet = (abs(ax_x['f'][i] - 1) < 5e-4 and abs(ax_z['f'][i] - 1) < 5e-4
                 and not (ax_x['split'][i] or ax_z['split'][i]))
        if quiet:
            continue
        print(' %2d   %6.3f %6.4f %6.4f    %5.3f %5.3f    %4.2f %4.2f     %d %d      %5.1f %5.1f'
              % (i, m['yb'][i], ax_x['f'][i], ax_z['f'][i], ax_x['raw'][i], ax_z['raw'][i],
                 ax_x['trust'][i], ax_z['trust'][i], ax_x['split'][i], ax_z['split'][i],
                 ax_x['gap'][i] * 1000, ax_z['gap'][i] * 1000))

    origin, rot, pts = world_model(spec)
    tris_before = {c['id']: component_tris(c) for c in spec['componentTree']}

    # ------------------------------------------------------------- 1. the size field
    bounds_plan = {}
    print('\n== 1. per-height size field on the body volume ==')
    print('%-16s %-10s  fX     fZ    how' % ('component', 'kind'))
    for cid in sorted(WHITELIST):
        c = comps.get(cid)
        if c is None:
            continue                       # consolidated away by another patch: skip, do not raise
        gd = c.get('geometryDescriptor') or {}
        sdf = gd.get('sdf')
        att = c.get('attachment')
        # A per-height scale of the cross-section scales OFFSETS as well as sizes. If it
        # does not, a surface detail slides off the surface it is glued to: shrinking the
        # top's depth by 8 pct while leaving x-lacing at its old z left the brass lacing
        # floating 2 mm proud of the top, which split the side silhouette into two runs
        # at bands 30-31 -- a new instance of exactly the defect this patch exists to fix.
        if not att:
            pos = c['transform'].get('position')
            if isinstance(pos, list) and len(pos) == 3:
                y = float(origin[cid][1])
                for k, name in ((0, 'X'), (2, 'Z')):
                    f = field(m, name, y)
                    if abs(pos[k]) > 1e-6 and abs(f - 1) >= MIN_FACTOR:
                        j.set('%s|transform|position|%d' % (cid, k), round(pos[k] * f, 6))

        implicit = c.get('topologyClass') == 'implicit' and sdf
        if implicit and isinstance(c['transform'].get('scale'), list):
            sv = scale_vector(c)
            eff = {0: [], 2: []}          # the factor IN FORCE on every primitive, 1.0 if skipped
            wrote = False
            for idx, p in enumerate(sdf['primitives']):
                if is_clipper(p):
                    continue
                y = prim_world_y(cid, p, origin, rot, sv)
                fx, fz = field(m, 'X', y), field(m, 'Z', y)
                if p['type'] in ISOTROPIC:
                    # one radius, so it cannot hold X and Z apart: geometric mean, once
                    fx = fz = math.sqrt(fx * fz)
                    if abs(fx - 1) >= MIN_FACTOR:
                        set_prim_size(j, cid, idx, p, 0, prim_axis_size(p, 0) * fx)
                        wrote = True
                for k, f in ((0, fx), (2, fz)):
                    if abs(f - 1) < MIN_FACTOR:
                        eff[k].append(1.0)
                        continue
                    if p['type'] not in ISOTROPIC:
                        set_prim_size(j, cid, idx, p, k, prim_axis_size(p, k) * f)
                    if abs(prim_centre(p, k)) > 1e-9:
                        set_prim_centre(j, cid, idx, p, k, prim_centre(p, k) * f)
                    eff[k].append(f)
                    wrote = True
            if wrote:
                bounds_plan[cid] = [float(np.mean(eff[0] or [1.0])), 1.0,
                                    float(np.mean(eff[2] or [1.0]))]
                print('%-16s %-10s %6.4f %6.4f  %d primitives, each at its own world height'
                      % (cid, 'sdf/metres', float(np.mean(eff[0] or [1])), float(np.mean(eff[2] or [1])),
                         len(sdf['primitives'])))
        elif implicit:
            # no transform.scale, so the emitter scales the SDF by dimensions: the
            # descriptor is normalised and the metres live in dimensions.width/depth
            y = float(origin[cid][1])
            fx, fz = field(m, 'X', y), field(m, 'Z', y)
            dim = c.get('dimensions') or {}
            if dim.get('width') and abs(fx - 1) > 1e-4:
                j.set('%s|dimensions|width' % cid, round(dim['width'] * fx, 6))
            if dim.get('depth') and abs(fz - 1) > 1e-4:
                j.set('%s|dimensions|depth' % cid, round(dim['depth'] * fz, 6))
            if abs(fx - 1) > 1e-4 or abs(fz - 1) > 1e-4:
                print('%-16s %-10s %6.4f %6.4f  dimensions (this descriptor is normalised)'
                      % (cid, 'sdf/norm', fx, fz))
        elif att:
            ys = float(origin[cid][1])
            ye = float((rot[cid] @ (np.array(att['localEnd'], float)
                                    - np.array(att['localStart'], float)))[1] + ys)
            fb = math.sqrt(field(m, 'X', ys) * field(m, 'Z', ys))
            fe = math.sqrt(field(m, 'X', ye) * field(m, 'Z', ye))
            wrote = False
            if abs(fb - 1) > 1e-4 and att.get('baseRadius'):
                j.set('%s|attachment|baseRadius' % cid, round(att['baseRadius'] * fb, 6))
                wrote = True
            if abs(fe - 1) > 1e-4 and att.get('endRadius'):
                j.set('%s|attachment|endRadius' % cid, round(att['endRadius'] * fe, 6))
                wrote = True
            if wrote:
                print('%-16s %-10s %6.4f %6.4f  circular section, sqrt(fX.fZ) at y %.3f and %.3f'
                      % (cid, 'cylinder', fb, fe, ys, ye))
        else:
            dim = c.get('dimensions') or {}
            if not (dim.get('width') and dim.get('depth')):
                continue
            y = float(origin[cid][1])
            fx, fz = field(m, 'X', y), field(m, 'Z', y)
            if abs(fx - 1) > 1e-4:
                j.set('%s|dimensions|width' % cid, round(dim['width'] * fx, 6))
            if abs(fz - 1) > 1e-4:
                j.set('%s|dimensions|depth' % cid, round(dim['depth'] * fz, 6))
            if abs(fx - 1) > 1e-4 or abs(fz - 1) > 1e-4:
                print('%-16s %-10s %6.4f %6.4f  dimensions.width/depth' % (cid, 'primitive', fx, fz))

    # ------------------------------------------------- 2. braid forward until contact
    origin, rot, pts = world_model(spec)
    body_ids = [cid for cid in WHITELIST if cid in comps]
    print('\n== 2. braid chain forward in +Z until it touches the back ==')

    # every braid endpoint, as (world height, component, which end)
    nodes = []
    for cid in BRAID_CHAIN:
        c = comps.get(cid)
        if c is None or not c.get('attachment'):
            continue
        att = c['attachment']
        start = np.array(att['localStart'], float)
        for endname in ('localStart', 'localEnd'):
            w = rot[cid] @ (np.array(att[endname], float) - start) + origin[cid]
            r = att.get('baseRadius' if endname == 'localStart' else 'endRadius') or 0.0
            nodes.append(dict(y=float(w[1]), z=float(w[2]), r=r, cid=cid, end=endname))
    knots = sorted({round(n['y'], 5) for n in nodes})

    # the closure each flagged band wants: body rear minus braid front, in that band
    want_y, want_e = [], []
    for i in range(NB):
        if not ax_z['split'][i]:
            continue
        y0, y1 = m['edges'][i], m['edges'][i + 1]
        back = braid_front = None
        for bid in body_ids:
            p = pts[bid]
            sel = (p[:, 1] >= y0) & (p[:, 1] < y1)
            if sel.any():
                v = float(p[sel][:, 2].min())
                back = v if back is None else min(back, v)
        for bid in BRAID_CHAIN:
            if bid not in pts:
                continue
            p = pts[bid]
            sel = (p[:, 1] >= y0) & (p[:, 1] < y1)
            if sel.any():
                v = float(p[sel][:, 2].max())
                braid_front = v if braid_front is None else max(braid_front, v)
        if back is None or braid_front is None or back <= braid_front:
            continue
        want_y.append(m['yb'][i])
        want_e.append(min(back - braid_front, MAX_BRAID_M))

    shifts = {k: 0.0 for k in knots}
    if want_y:
        # a knot may move only if one of the two chain segments it terminates actually
        # spans a band the judge flagged; that keeps the tassels and the crown still
        free = []
        for q, k in enumerate(knots):
            a = knots[q - 1] if q else -1e9
            b = knots[q + 1] if q + 1 < len(knots) else 1e9
            if any(a < y < b for y in want_y):
                free.append(k)
        if free:
            # piecewise-linear hat basis on the knots; knots outside the flagged span stay
            # pinned at zero so the tassels and the crown do not travel
            basis = np.zeros((len(want_y), len(free)))
            for col, k in enumerate(free):
                unit = {q: (1.0 if q == k else 0.0) for q in knots}
                basis[:, col] = np.interp(want_y, knots, [unit[q] for q in knots])
            sol, *_ = np.linalg.lstsq(np.vstack([basis, 0.05 * np.eye(len(free))]),
                                      np.concatenate([want_e, np.zeros(len(free))]), rcond=None)
            for k, s in zip(free, np.clip(sol, 0.0, MAX_BRAID_M)):
                shifts[k] = float(s)
        fit = np.interp(want_y, knots, [shifts[k] for k in knots])
        print('  wanted closure at %d flagged bands, %.1f to %.1f mm; chain fit leaves'
              ' %.1f mm mean residual' % (len(want_y), min(want_e) * 1000, max(want_e) * 1000,
                                          float(np.mean(np.abs(fit - np.array(want_e)))) * 1000))
    braid_moves = 0
    for n in nodes:
        s = shifts.get(round(n['y'], 5), 0.0)
        if s < MIN_ACT_M:
            continue
        att = comps[n['cid']]['attachment']
        j.set('%s|attachment|%s|2' % (n['cid'], n['end']),
              round(float(np.array(att[n['end']], float)[2] + s), 6))
        braid_moves += 1
    for k in knots:
        if shifts[k] >= MIN_ACT_M:
            print('  chain node at y %.3f  ->  +%.1f mm in Z' % (k, shifts[k] * 1000))
    if not braid_moves:
        print('  no braid node sits inside a band the judge flags as split: nothing moved')

    # --------------------------------------- 3. body surface outward until contact
    origin, rot, pts = world_model(spec)
    print('\n== 3. close the gaps still flagged, by growing the body-side surface ==')
    all_ids = [c['id'] for c in spec['componentTree'] if len(pts[c['id']]) > 4]
    closed, refused = 0, 0
    for name, k in (('X', 0), ('Z', 2)):
        axd = m['axes'][name]
        for i in range(NB):
            # act where the reference is ONE run: either the judge already sees us split
            # there, or the model shows a hairline gap the size field may have opened.
            # Closing a gap against a merged reference can only help, and `core` pays the
            # same price for a 1 mm gap as for a 60 mm one.
            if axd['ref_nrun'][i] >= 1.5:
                continue
            y0, y1 = m['edges'][i], m['edges'][i + 1]
            runs = merge_intervals(intervals_at(pts, all_ids, k, y0, y1))
            for t in range(len(runs) - 1):
                width = runs[t + 1][0] - runs[t][1]
                if width < MIN_ACT_M:
                    continue
                if not axd['split'][i] and width > HAIRLINE_M:
                    continue
                cand = []
                for side, run in ((+1, runs[t]), (-1, runs[t + 1])):
                    owners = sorted(o for o in run[2] if o in WHITELIST and o in comps)
                    if owners:
                        cand.append((min(abs(run[0]), abs(run[1])), side, owners))
                if not cand:
                    refused += 1
                    print('  %s band %2d y %.3f  gap %5.1f mm: no body component on either side'
                          % (name, i, m['yb'][i], width * 1000))
                    continue
                cand.sort(key=lambda r: r[0])
                _, side, owners = cand[0]
                need = min(width + 0.002, MAX_CONTACT_M)
                picked, blocked = [], []
                for cid in owners:
                    c = comps[cid]
                    gd = c.get('geometryDescriptor') or {}
                    sdf = gd.get('sdf')
                    if not (c.get('topologyClass') == 'implicit' and sdf
                            and isinstance(c['transform'].get('scale'), list)):
                        blocked.append(cid)
                        continue
                    sv = scale_vector(c)
                    carve = carve_ids(sdf)
                    e = need / max(abs(sv[k]), 1e-6) / 2.0
                    touched = 0
                    for idx, p in enumerate(sdf['primitives']):
                        if p['id'] in carve or is_clipper(p) or p['type'] in ISOTROPIC:
                            continue
                        if any((p.get('transform') or {}).get('rotation') or []):
                            continue
                        y = prim_world_y(cid, p, origin, rot, sv)
                        if not (y0 - 0.03 <= y <= y1 + 0.03):
                            continue
                        set_prim_size(j, cid, idx, p, k, prim_axis_size(p, k) + e)
                        set_prim_centre(j, cid, idx, p, k, prim_centre(p, k) + side * e)
                        touched += 1
                    if touched:
                        bounds_plan.setdefault(cid, [1.0, 1.0, 1.0])
                        picked.append('%s(%d)' % (cid, touched))
                if picked:
                    closed += 1
                    print('  %s band %2d y %.3f  model gap %5.1f mm, judge gap %5.1f mm  ->  %s'
                          ' grows %+.1f mm' % (name, i, m['yb'][i], width * 1000,
                                               axd['gap'][i] * 1000, ' '.join(picked),
                                               side * need * 1000))
                else:
                    refused += 1
                    print('  %s band %2d y %.3f  gap %5.1f mm: only %s here, and a swept cylinder'
                          ' cannot gain one axis without the other (rule 2) -- left alone'
                          % (name, i, m['yb'][i], width * 1000, ','.join(sorted(blocked or owners))))

    for cid, factor in bounds_plan.items():
        settle_bounds(j, cid, comps[cid]['geometryDescriptor']['sdf'], factor)

    # ------------------------------------------------------------------- accounting
    n = j.commit('per-height X/Z size field lam=%.2f trust=%.0fmm cap=%.2f, plus contact edits'
                 % (LAMBDA, TRUST_MM, CAP))
    tris_after = {c['id']: component_tris(c) for c in spec['componentTree']}
    rows, delta = [], 0
    for cid, before in tris_before.items():
        after = tris_after.get(cid)
        if before is None or after is None or before == after:
            continue
        rows.append((after - before, cid, before, after))
        delta += after - before
    print('\n== triangle cost ==')
    for d, cid, a, b in sorted(rows, key=lambda r: -abs(r[0])):
        print('  %-16s %7d -> %7d   %+d' % (cid, a, b, d))
    print('  net %+d triangles. Swept cylinders take their radial segment count from the'
          ' spec, not from their radius, so only the implicit components can move at all.'
          % delta)

    print('\n== summary ==')
    print('  %d gaps closed, %d flagged gaps left alone and named above' % (closed, refused))
    print('  %d fields restored from a previous run, %d fields written this run' % (restored, n))

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')   # the file's own style
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
