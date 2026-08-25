"""Uncover the face: carve the hair mass off the front of the skull, and give the
brow and lip components a material whose albedo is actually the colour they are.

WHAT WAS MEASURED (all of it re-derived at runtime, nothing below is hard-coded)
-------------------------------------------------------------------------------
The head is NOT too small. Head+hair envelope width at matched figure height is
219 mm render against 212-220 mm reference across the whole head band -- the
envelope is right. What is wrong is that the hair is drawn IN FRONT OF the face.

Three numbers carry the patch:

1. EXPOSED-SKIN FRACTION of the head band (figure top down to the chin,
   t_sole >= 0.861, hair segmented as CIE b* < -8, aperture = hole-filled
   largest non-hair component):
       reference `ref/views/body_2.png`   10779 / 22912 px = 0.4705
       render    `out/final/render_yaw0`   3406 / 10635 px = 0.3203
   The render shows 68% of the reference's face. Target ratio 1.469.

2. THE HAIR SITS IN FRONT OF THE SKULL, not merely beside it. Voxelising the
   `head` and `hair` SDF descriptors exactly as `polygonizeSdf` does (res 64,
   cell centres, sdf * dimensions/boundsSize) and comparing front-surface z per
   (x, y) gives an analytic front-view aperture of 3457 px against the 3406 px
   measured off the render -- 1.5% agreement, so the analytic model is the
   render. That model says the skull's own front-view silhouette is 5469 px:
   2012 px of skull, 59% more than is currently visible, is behind hair.
   The existing `face-opening` carve is an ELLIPSOID, so its z depth is coupled
   to its width and collapses to nothing at the cheeks and the hairline -- at the
   jaw hinge it stops carving at head-local z = 0.051 m while the ramus surface
   is at 0.020 m. An ellipsoid cannot fix this. A `box` has constant depth.

3. THE HAIRLINE IS TOO LOW. Aperture top (topmost row at least 30% of the
   aperture's own max width, same detector both sides): reference t_sole 0.95922,
   render 0.94988 -- 16.1 mm of forehead covered that should not be.

And two colours, sampled from `body_2.png` through boxes placed by mapping the
brow and mouth components' own head-local positions into the panel's t_sole
frame (so the sample box is where the geometry says the feature is, not where a
detector guessed):
       reference brow  CIE Lab (17.3, 7, 6)   vs `brow` albedo (34.1, -3, -30)
       reference lip   CIE Lab (41.2, 20, 9)  vs `lip`  albedo (64.7, 9, 6)
The eyebrow's albedo PNG is CYAN. `baseColor` is dead on these materials --
`createSculptMaterial` forces color to white whenever all five reference maps
load, which they do -- so the rendered brow is the map, dE 41 from the target.

WHAT THIS CHANGES
-----------------
* `hair.geometryDescriptor.sdf` gains TWO box primitives and two `subtract`
  operations, appended last so the second is the output. Both boxes run from a
  common back plane out to z = +0.30 head-local, so they have CONSTANT depth
  where the ellipsoid's collapses:
      `face-carve`        jaw to cheekbone, |x| <= the head's own maximum
                          silhouette half-width over the face band (0.0670 m)
      `face-carve-upper`  cheekbone to hairline, |x| <= half the reference
                          aperture's own median width there (0.0540 m)
  The split height and the upper width are read off the reference's aperture
  taper (widest at t 0.9114, under 85% of that by t 0.9278), because the
  reference keeps hair on the temples above the cheekbone and a single
  full-width box would strip it. Everything hair-side of the skull inside those
  boxes is removed; everything behind them, and everything outside |x|, stands.
* `brow-l`, `brow-r` -> the existing unused `pupil` material (albedo Lab
  (16.5, 8, 6), dE 1.5 from the measured reference brow, against 40.8 now).
* `mouth` -> the existing `laceMagenta` material (Lab (36.9, 24, -6), dE 15.6
  against 27.6 now). Not a good match -- no material in the spec is -- but it is
  the only one that gets the polarity right: the render's mouth is currently
  12.9 L LIGHTER than the surrounding chin where the reference's is 25 darker.
  If the runtime search finds no material inside dE 22 of the measured lip, or
  none that is at least 6 dE better than the incumbent, the mouth is left alone
  and the script says so.

The material choices are re-derived every run by measuring every material's
albedo PNG mean and picking the nearest to the measured reference colour; the
ids above are what that search returns today, not constants in this file.

TRADE-OFF, and how it is bounded
--------------------------------
Removing hair can only cost silhouette. The patch therefore projects the
hair+head voxel union at all six judged yaws before and after the carve and
measures, per 0.5 mm row, the change in covered length and in outer extent, then
maps those deltas onto the judge's own 40 t-bands and recomputes
`width_rms_core_pct` per view and the width score `mean_v exp(-rms/2)` (verified
against `baseline/metrics_accepted.json`: this formula reproduces all six stored
values and the stored 0.13663 width score exactly). Candidates are tried from
most to least aggressive and the first one that keeps

    worst row silhouette loss  <= 12 mm  (about 6 px; the hair voxel is 3.5 mm)
    predicted width score change >= -0.02 points
    front-view (yaw 0) area loss = 0

is the one applied. If none passes, no carve is written.

Today's accepted candidate loses NOTHING at yaw 0 and yaw 180 -- the front-view
projected area is bit-identical, 45763 mm2 before and after, because the carve
never reaches past the skull in x -- and its worst row is a 7.5 mm loss at yaw 45
just above the jaw. Total projected area moves -220 mm2 at yaw 45 (0.45%) and
-5 mm2 at yaw 90. Predicted width score change is +0.0009 points, i.e. the carve
is marginally GOOD for width because several head bands are currently too wide.
The first, more aggressive candidate (box bottom on the chin rather than 4 mm
above it) is rejected at -21.0 mm: the hair beside the jaw is silhouette at yaw
90/270 and must not be touched. That rejection is printed, not hidden.

The second trade-off is honest overshoot risk: the reference's exposed face is
ASYMMETRIC (it runs -40..+111 mm about the head-band centre because her head is
turned), and this model is symmetric. A symmetric carve wins on three sides and
gives back a little on her right temple, where the render already shows 12 mm
more skin than the reference does. That is why the carve is stopped at the
reference's measured fraction rather than run to the skull.

EXPECTED MEASURABLE EFFECT (falsifiable)
----------------------------------------
* `views[yaw0].colour.regions.head.dE` must FALL from 31.37. It is the worst
  region in every view and its signature is hue_ref +43.7 deg (warm skin) against
  hue_render -81.1 deg (blue hair); db must move from -13.99 toward 0. Same
  direction required at yaw45 (dE 37.47), yaw315 (36.51), yaw270 (41.53).
  If head dE rises, this patch is wrong and should be reverted whole.
* `views[yaw0].colour.mean_dE` should fall by about 0.3 (23.010 -> ~22.7): the
  carve flips ~1050 front-view pixels from hair (measured dE 52.6 against the
  reference's face colour) to skin (dE 9.0). The `colour` term should rise from
  0.1952 by roughly +0.003 to +0.005, i.e. +0.03 to +0.05 points of the 100.
  That is the whole size of this dimension. It is NOT where the 4.89-point
  width+landmark deficit lives, and it should not be mistaken for it.
* `geometry.width_rms_core_pct` must NOT rise by more than 0.05 in any view, and
  the head/hair bands (t 0.8625..0.9875) must not move by more than 0.1 pct at
  yaw 0. Silhouette IoU (shape 0.7070) must hold to +/-0.002.
* `landmark_rms_pct` must not move at all: nothing this patch touches is on a
  landmark. head_top (0.29% error) and chin (1.96%) are unchanged by an interior
  carve, and the front-view silhouette is bit-identical by construction.

WHAT IS DELIBERATELY NOT FIXED
------------------------------
The eyebrows are 98% buried in the skull, not hidden by hair: the brow box's
centre sits 3.3 mm INSIDE the cranium and only the inner ~2 px of one brow
surfaces (3 pixels, measured). Pushing it forward is a transform edit costing no
triangles, but it is worth under 0.01 points, it would put a visible shelf on the
browridge, and at yaw 90/270 it would become the new front of the head-band
silhouette. Not worth it blind. Likewise the eyes: a 17x7 px all-iris lozenge,
1.8x too wide, but its measured contrast is already 0.76-0.89 of the reference's
and fixing the shape means adding sclera/pupil geometry to solve what is a
contrast problem. Left alone.

TRIANGLE COST
-------------
+84 triangles: the hair goes 12637 -> 12721, the model 203994 -> 204078 of the
250000 budget. That is 0.2% of the ~46000 shared headroom. `polygonizeSdf` emits
one quad per exposed voxel face, so carving deletes nearly as much boundary as
the new concave wall adds; the number is computed exactly here (the same
face-count loop over the same lattice, then the component's own decimate ratio),
not estimated -- the same routine reproduces the built meshes' counts exactly
(head 37928, hair 36108 raw -> 12637 at 0.35). Across the candidate ladder the
range is -92 to +227.
"""

from __future__ import annotations

import json
import math
import sys
from itertools import product

import cv2
import numpy as np

SPEC = sys.argv[1] if len(sys.argv) > 1 else "object-sculpt-spec.json"
ROOT = "."

CARVE_PRIM_ID = "face-carve"
CARVE_OP_ID = "hair-face-carve"
CARVE_BROW_ID = "face-carve-upper"
CARVE_BROW_OP_ID = "hair-face-carve-upper"
OWNED_PRIMS = (CARVE_PRIM_ID, CARVE_BROW_ID)
OWNED_OPS = (CARVE_OP_ID, CARVE_BROW_OP_ID)

# Guard thresholds. Stated here so they are auditable, not buried in the loop.
MAX_ROW_LOSS_M = 0.012          # ~6 px at 498 px/m; hair voxel is 3.5 mm
MAX_WIDTH_SCORE_LOSS = 0.02     # points of 100
OVERSHOOT_TOLERANCE = 1.02      # do not expose more than the reference does
MIN_LIP_GAIN_DE = 6.0           # do not swap the mouth for a marginal improvement
MAX_LIP_DE = 22.0               # ...and not at all if nothing is close

YAWS = (0, 45, 90, 180, 270, 315)


# --------------------------------------------------------------------------- #
# SDF evaluation -- a line-for-line mirror of src/createJinxModel.ts.          #
# sdfSample / polygonizeSdf / sdfPrimitive. Verified: it reproduces the built  #
# meshes' triangle counts exactly (head 37928, hair 36108 -> 12637 at 0.35).   #
# --------------------------------------------------------------------------- #

def _sdf_primitive(P, prim):
    tr = prim.get("transform") or {}
    t = tr.get("position") or tr.get("translation") or prim.get("center") or [0, 0, 0]
    rot = tr.get("rotation") or [0, 0, 0]
    sc = np.array(tr.get("scale") or [1, 1, 1], float)
    L = P - np.array(t, float)
    if any(abs(r) > 1e-12 for r in rot):
        cx, sx = math.cos(rot[0]), math.sin(rot[0])
        cy, sy = math.cos(rot[1]), math.sin(rot[1])
        cz, sz = math.cos(rot[2]), math.sin(rot[2])
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        L = L @ (Rx @ Ry @ Rz)          # inverse rotation
    L = L / sc
    kind = prim["type"]
    if kind == "sphere":
        d = np.linalg.norm(L, axis=-1) - float(prim.get("radius", 0.5))
    elif kind == "capsule":
        h = float(prim.get("height", 1.0)) * 0.5
        yc = np.clip(L[..., 1], -h, h)
        d = np.sqrt(L[..., 0] ** 2 + (L[..., 1] - yc) ** 2 + L[..., 2] ** 2) \
            - float(prim.get("radius", 0.25))
    elif kind == "box":
        size = np.array(prim.get("size") or prim.get("dimensions") or [1, 1, 1], float)
        q = np.abs(L) - size * 0.5
        d = np.linalg.norm(np.maximum(q, 0.0), axis=-1) + np.minimum(q.max(axis=-1), 0.0)
    elif kind == "cone":
        h = float(prim.get("height", 1.0)) * 0.5
        r = float(prim.get("radius", 0.5))
        taper = r * (1 - (L[..., 1] + h) / (2 * h))
        d = np.maximum(np.hypot(L[..., 0], L[..., 2]) - np.maximum(0, taper), np.abs(L[..., 1]) - h)
    elif kind == "ellipsoid":
        radii = prim.get("radii")
        if radii is None:
            r = prim.get("radius", [0.5, 0.5, 0.5])
            radii = [r, r, r] if isinstance(r, (int, float)) else r
        radii = np.array(radii, float)
        d = (np.linalg.norm(L / radii, axis=-1) - 1) * radii.min()
    else:
        raise ValueError("unknown sdf primitive %r" % kind)
    return d * sc.min()


def _smin(a, b, r):
    blend = np.maximum(r - np.abs(a - b), 0.0) / r
    return np.minimum(a, b) - blend * blend * r * 0.25


def _sdf_field(desc, P):
    nodes = {}
    for prim in desc["primitives"]:
        nodes[prim["id"]] = _sdf_primitive(P, prim)
    result = nodes[desc["primitives"][0]["id"]]
    for index, op in enumerate(desc.get("operations") or []):
        left = nodes.get(op["left"])
        right = nodes.get(op["right"])
        if left is None or right is None:
            continue                                    # emitter skips it silently too
        if op["type"] == "smooth-union":
            combined = _smin(left, right, float(op.get("radius", 0.1)))
        elif op["type"] == "subtract":
            combined = np.maximum(left, -right)
        elif op["type"] == "intersect":
            combined = np.maximum(left, right)
        else:
            continue
        nodes[op.get("id") or op.get("output") or ("operation-%d" % index)] = combined
        result = combined
    return result


def dims_vec(component):
    d = component["dimensions"]
    return np.array([d["width"], d["height"], d["depth"]], float)


def voxelise(component, extra_prims=(), extra_ops=()):
    """Occupancy grid on the emitter's own lattice. Returns (occ[z,y,x], bmin, step, scale)."""
    desc = json.loads(json.dumps(component["geometryDescriptor"]["sdf"]))
    desc["primitives"] = list(desc["primitives"]) + list(extra_prims)
    desc["operations"] = list(desc.get("operations") or []) + list(extra_ops)
    n = min(64, max(4, int(desc["resolution"])))
    bmin = np.array(desc["bounds"]["min"], float)
    bmax = np.array(desc["bounds"]["max"], float)
    step = (bmax - bmin) / n
    idx = np.arange(n)
    Z, Y, X = np.meshgrid(bmin[2] + (idx + 0.5) * step[2],
                          bmin[1] + (idx + 0.5) * step[1],
                          bmin[0] + (idx + 0.5) * step[0], indexing="ij")
    occ = _sdf_field(desc, np.stack([X, Y, Z], axis=-1)) <= 0
    scale = dims_vec(component) / (bmax - bmin)
    return occ, bmin, step, scale


def triangle_count(occ, decimate_ratio):
    """Exact polygonizeSdf output: one quad (2 tris) per exposed voxel face."""
    n = occ.shape[0]
    pad = np.zeros((n + 2, n + 2, n + 2), bool)
    pad[1:-1, 1:-1, 1:-1] = occ
    quads = 0
    quads += np.count_nonzero(occ & ~pad[1:-1, 1:-1, 0:-2])
    quads += np.count_nonzero(occ & ~pad[1:-1, 1:-1, 2:])
    quads += np.count_nonzero(occ & ~pad[1:-1, 0:-2, 1:-1])
    quads += np.count_nonzero(occ & ~pad[1:-1, 2:, 1:-1])
    quads += np.count_nonzero(occ & ~pad[0:-2, 1:-1, 1:-1])
    quads += np.count_nonzero(occ & ~pad[2:, 1:-1, 1:-1])
    tris = quads * 2
    if decimate_ratio and 0 < decimate_ratio < 1:
        tris = max(4, int(tris * decimate_ratio))
    return tris


# --------------------------------------------------------------------------- #
# Projection helpers                                                          #
# --------------------------------------------------------------------------- #

GX = np.arange(-0.13, 0.1301, 0.0005)
GY = np.arange(-0.20, 0.1401, 0.0005)
DU = DY = 0.0005
U0, U1 = -0.20, 0.20
Y0, Y1 = -0.22, 0.16
NU = int((U1 - U0) / DU) + 1
NY = int((Y1 - Y0) / DY) + 1
ROW_Y = Y0 + np.arange(NY) * DY


def axes_of(bmin, step, scale, offset):
    idx = np.arange(64)
    return ((bmin[0] + (idx + 0.5) * step[0]) * scale[0] + offset[0],
            (bmin[1] + (idx + 0.5) * step[1]) * scale[1] + offset[1],
            (bmin[2] + (idx + 0.5) * step[2]) * scale[2] + offset[2],
            0.5 * step[0] * scale[0], 0.5 * step[1] * scale[1], 0.5 * step[2] * scale[2])


def front_surface(occ, bmin, step, scale, offset):
    """(max z of occupied voxel front faces) and (occupied at all), on the common GX/GY grid."""
    xs, ys, zs, hx, hy, hz = axes_of(bmin, step, scale, offset)
    maxz = np.where(occ, zs[:, None, None] + hz, -9.9).max(axis=0)
    anyz = occ.any(axis=0)

    def regrid(arr, fill):
        xi = np.clip(np.searchsorted(xs + hx, GX), 0, len(xs) - 1)
        yi = np.clip(np.searchsorted(ys + hy, GY), 0, len(ys) - 1)
        out = arr[np.ix_(yi, xi)].astype(float)
        out[(GY < ys[0] - hy) | (GY > ys[-1] + hy), :] = fill
        out[:, (GX < xs[0] - hx) | (GX > xs[-1] + hx)] = fill
        return out

    return regrid(maxz, -9.9), regrid(anyz.astype(float), 0.0) > 0.5


def coverage(parts, theta):
    """Orthographic projection of a voxel union at yaw theta.
    Returns per-row covered length, min u, max u."""
    c, s = math.cos(theta), math.sin(theta)
    diff = np.zeros((NY, NU + 1), np.int32)
    umin = np.full(NY, np.inf)
    umax = np.full(NY, -np.inf)
    for occ, bmin, step, scale, offset in parts:
        xs, ys, zs, hx, hy, hz = axes_of(bmin, step, scale, offset)
        uh = abs(hx * c) + abs(hz * s)
        for yi in range(occ.shape[1]):
            sl = occ[:, yi, :]
            if not sl.any():
                continue
            zi, xi = np.nonzero(sl)
            u = xs[xi] * c + zs[zi] * s
            a = np.clip(((u - uh - U0) / DU).astype(int), 0, NU - 1)
            b = np.clip(((u + uh - U0) / DU).astype(int) + 1, 1, NU)
            j0 = max(0, int((ys[yi] - hy - Y0) / DY))
            j1 = min(NY, int((ys[yi] + hy - Y0) / DY) + 1)
            if j1 <= j0:
                continue
            row = np.zeros(NU + 1, np.int32)
            np.add.at(row, a, 1)
            np.add.at(row, b, -1)
            diff[j0:j1] += row
            umin[j0:j1] = np.minimum(umin[j0:j1], (u - uh).min())
            umax[j0:j1] = np.maximum(umax[j0:j1], (u + uh).max())
    mask = np.cumsum(diff[:, :-1], axis=1) > 0
    return mask.sum(1) * DU, umin, umax, mask.sum()


# --------------------------------------------------------------------------- #
# Image measurement                                                           #
# --------------------------------------------------------------------------- #

def load_lab(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit("cannot read %s" % path)
    h, w = img.shape[:2]
    alpha = img[..., 3] if img.shape[2] == 4 else np.full((h, w), 255, np.uint8)
    lab = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    return img, alpha > 128, lab[..., 0] * (100.0 / 255.0), lab[..., 1] - 128.0, lab[..., 2] - 128.0


def face_aperture(path, t_chin):
    """Exposed-skin mask of the head band. Hair = CIE b* < -8; aperture = the
    hole-filled largest non-hair connected component inside the band."""
    img, fg, L, A, B = load_lab(path)
    h, w = fg.shape
    rows = np.where(fg.any(1))[0]
    r0, r1 = int(rows.min()), int(rows.max())
    H = r1 - r0 + 1
    hair = fg & (B < -8)
    band = np.zeros_like(fg)
    band[r0:int(round(r1 - t_chin * H)) + 1, :] = True
    head_band = fg & band
    nonhair = head_band & ~hair
    ncc, lbl = cv2.connectedComponents(nonhair.astype(np.uint8))
    if ncc < 2:
        raise SystemExit("no face component found in %s" % path)
    best = 1 + int(np.argmax([(lbl == i).sum() for i in range(1, ncc)]))
    face = lbl == best
    inv = (1 - face.astype(np.uint8)).astype(np.uint8)
    cv2.floodFill(inv, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 2)
    face = face | (inv == 1)
    widths = face.sum(1)
    wmax = int(widths.max())
    tall = np.where(widths >= 0.30 * wmax)[0]
    cols = np.where(head_band.any(0))[0]
    rows_all = np.arange(len(widths))
    return dict(H=H, r0=r0, r1=r1, face_px=int(face.sum()), band_px=int(head_band.sum()),
                frac=float(face.sum()) / float(head_band.sum()),
                t_hairline=float((r1 - tall.min()) / H),
                xc=float((cols.min() + cols.max()) / 2.0),
                widths=widths, wmax=wmax, t_rows=(r1 - rows_all) / H,
                t_widest=float((r1 - int(np.argmax(widths))) / H),
                L=L, A=A, B=B, fg=fg, hair=hair, face=face)


def sample_box(panel, off_y, y_min, fig_h, y_local, half_w, half_h, mode):
    """Median Lab of a feature, in a box placed by the component's own head-local
    position mapped through t_sole into the panel. mode picks the extreme tail."""
    px_per_m = panel["H"] / fig_h
    rc = panel["r1"] - (y_local + off_y - y_min) * px_per_m
    cc = panel["xc"]
    r_lo = max(0, int(round(rc - half_h * px_per_m)))
    r_hi = int(round(rc + half_h * px_per_m))
    c_lo = max(0, int(round(cc - half_w * px_per_m)))
    c_hi = int(round(cc + half_w * px_per_m))
    sel = np.zeros_like(panel["fg"])
    sel[r_lo:r_hi + 1, c_lo:c_hi + 1] = True
    sel &= panel["fg"] & ~panel["hair"]
    if sel.sum() < 20:
        return None, 0
    L, A = panel["L"], panel["A"]
    if mode == "dark":
        pick = sel & (L <= np.percentile(L[sel], 25))
    elif mode == "red":
        pick = sel & (A >= np.percentile(A[sel], 75))
    else:
        pick = sel
    if pick.sum() < 8:
        return None, 0
    return np.array([float(np.median(L[pick])), float(np.median(A[pick])),
                     float(np.median(panel["B"][pick]))]), int(pick.sum())


def dE(a, b):
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def albedo_lab(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    mean = img.reshape(-1, 3).mean(0)
    px = np.uint8([[[mean[0], mean[1], mean[2]]]])
    lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0].astype(float)
    return np.array([lab[0] * 100.0 / 255.0, lab[1] - 128.0, lab[2] - 128.0])


# --------------------------------------------------------------------------- #

def main():
    with open(SPEC, encoding="utf-8") as handle:
        spec = json.load(handle)
    components = {c["id"]: c for c in spec["componentTree"]}
    materials = {m["id"]: m for m in spec["materials"]}
    report = []

    for cid in ("head", "hair"):
        if cid not in components:
            raise SystemExit("patch_face_scale: component %r is gone; nothing to do" % cid)

    hair = components["hair"]
    head = components["head"]
    sdf = hair["geometryDescriptor"]["sdf"]

    # -- 0. strip any previous run so the derivation always starts from the
    #       uncarved hair. This is what makes the script idempotent AND correct
    #       when re-run after somebody else has moved the head.
    had_carve = any(p.get("id") in OWNED_PRIMS for p in sdf["primitives"])
    sdf["primitives"] = [p for p in sdf["primitives"] if p.get("id") not in OWNED_PRIMS]
    sdf["operations"] = [o for o in sdf["operations"]
                         if (o.get("id") or o.get("output")) not in OWNED_OPS]
    if not sdf["operations"]:
        raise SystemExit("patch_face_scale: hair sdf has no operations to build on")
    output_op = sdf["operations"][-1].get("id") or sdf["operations"][-1].get("output")

    # -- 1. frame constants, re-derived --------------------------------------
    meshes = json.load(open(ROOT + "/baseline/meshes_accepted.json", encoding="utf-8"))
    metrics = json.load(open(ROOT + "/baseline/metrics_accepted.json", encoding="utf-8"))
    y_min = min(m["minY"] for m in meshes)
    y_max = max(m["maxY"] for m in meshes)
    fig_h = y_max - y_min
    head_mesh = next((m for m in meshes if m["name"] == "Head"), None)
    if head_mesh is None:
        raise SystemExit("patch_face_scale: no 'Head' mesh in meshes_accepted.json")

    occ_head, bmin_h, step_h, scale_h = voxelise(head)
    yi = np.nonzero(occ_head.any(axis=(0, 2)))[0]
    ys_head = (bmin_h[1] + (yi + 0.5) * step_h[1]) * scale_h[1]
    half_step_y = 0.5 * step_h[1] * scale_h[1]
    local_lo, local_hi = ys_head.min() - half_step_y, ys_head.max() + half_step_y
    off_y = 0.5 * ((head_mesh["minY"] - local_lo) + (head_mesh["maxY"] - local_hi))

    # Cross-check against the parent chain. The mesh-derived value is the one used
    # -- it is what actually got built -- but the chain walk catches a concurrent
    # patch that has RELOCATED the head since the baseline was measured, in which
    # case the reference-hairline target below is stale by that amount.
    chain_y, cursor, guard_seen = 0.0, "head", set()
    while cursor and cursor in components and cursor not in guard_seen:
        guard_seen.add(cursor)
        node = components[cursor]
        att = node.get("attachment")
        if att and att.get("localStart"):
            chain_y += float(att["localStart"][1])
        else:
            chain_y += float(((node.get("transform") or {}).get("position") or [0, 0, 0])[1])
        cursor = node.get("parent")
    chain_bias = chain_y - off_y
    if abs(chain_bias) > 0.015:
        report.append("WARNING: head parent chain puts the origin at %.5f but the accepted "
                      "build measured %.5f (%+.1f mm). The head has probably been moved by "
                      "another patch in this pass; the hairline target below is that stale."
                      % (chain_y, off_y, chain_bias * 1000))

    hair_off = np.array(hair["transform"]["position"], float)
    occ_hair, bmin_a, step_a, scale_a = voxelise(hair)
    decim = ((hair["geometryDescriptor"].get("decimate") or {}).get("targetRatio"))
    tris_before = triangle_count(occ_hair, decim)

    head_z, head_on = front_surface(occ_head, bmin_h, step_h, scale_h, [0, 0, 0])
    hair_z, _ = front_surface(occ_hair, bmin_a, step_a, scale_a, hair_off)
    aperture0 = head_on & (head_z > hair_z)
    cell = 0.0005 * 0.0005
    t_chin = (local_lo + off_y - y_min) / fig_h

    def analytic_hairline(ap):
        widths = ap.sum(1)
        if not widths.any():
            return None
        rows = np.where(widths >= 0.30 * widths.max())[0]
        return float(GY[rows.max()])

    hairline_now = analytic_hairline(aperture0)

    report.append("frame: figure %.3f..%.3f m (H %.4f), head origin y %.5f, chin t_sole %.5f"
                  % (y_min, y_max, fig_h, off_y, t_chin))
    report.append("analytic front aperture %.0f px, skull front silhouette %.0f px "
                  "(%.0f px of skull behind hair)"
                  % (aperture0.sum() * cell / (0.002008 ** 2),
                     head_on.sum() * cell / (0.002008 ** 2),
                     (head_on.sum() - aperture0.sum()) * cell / (0.002008 ** 2)))

    # -- 2. reference vs render exposed-skin fraction and hairline ------------
    ref_panel = face_aperture(ROOT + "/ref/views/body_2.png", t_chin)
    ren_panel = face_aperture(ROOT + "/out/final/render_yaw0.png", t_chin)
    target_ratio = ref_panel["frac"] / ren_panel["frac"]
    report.append("exposed skin in head band: ref %d/%d = %.4f, render %d/%d = %.4f "
                  "-> target ratio %.3f"
                  % (ref_panel["face_px"], ref_panel["band_px"], ref_panel["frac"],
                     ren_panel["face_px"], ren_panel["band_px"], ren_panel["frac"],
                     target_ratio))

    # analytic hairline in pixel terms, so the pixel->world residual cancels
    t_render_analytic = (hairline_now + off_y - y_min) / fig_h
    hairline_bias = t_render_analytic - ren_panel["t_hairline"]
    t_target = ref_panel["t_hairline"] + hairline_bias
    y_top_target = y_min + t_target * fig_h - off_y
    report.append("hairline t_sole: ref %.5f, render pixels %.5f, render analytic %.5f "
                  "(bias %+.5f) -> carve top head-local y %+.5f (%+.1f mm)"
                  % (ref_panel["t_hairline"], ren_panel["t_hairline"], t_render_analytic,
                     hairline_bias, y_top_target, (y_top_target - hairline_now) * 1000))

    # -- 3. carve rectangle from the skull's own geometry ---------------------
    face_rows = (GY >= local_lo) & (GY <= y_top_target)
    if not face_rows.any():
        raise SystemExit("patch_face_scale: empty face band")
    skull_cols = head_on[face_rows].any(0)
    x_half_full = float(max(abs(GX[skull_cols].min()), abs(GX[skull_cols].max())))
    rect = head_on & (np.abs(GX)[None, :] <= x_half_full) & face_rows[:, None]
    front_z = head_z[rect]
    report.append("carve rect: |x| <= %.4f m (skull's own half-width), y %.4f..%.4f m; "
                  "skull front z p8=%.1f p12=%.1f p18=%.1f mm"
                  % (x_half_full, local_lo, y_top_target,
                     np.percentile(front_z, 8) * 1000, np.percentile(front_z, 12) * 1000,
                     np.percentile(front_z, 18) * 1000))

    # The reference's aperture is widest at the cheekbones and tapers toward the
    # hairline; a single box would expose the temples right to the top, which the
    # reference does not. Split the carve where the reference's own width first
    # falls below 85% of its maximum, and cap the upper box at the reference's
    # median width there. Purely a re-measurement, no constants.
    ref_t = ref_panel["t_rows"]
    ref_w_m = ref_panel["widths"] / ref_panel["H"] * fig_h
    upper = (ref_t > ref_panel["t_widest"]) & (ref_t <= ref_panel["t_hairline"]) \
        & (ref_panel["widths"] < 0.85 * ref_panel["wmax"])
    if upper.any():
        t_split = float(ref_t[upper].min())
        y_split = y_min + t_split * fig_h - off_y
        band = upper & (ref_t >= t_split)
        x_half_top = min(x_half_full, float(np.median(ref_w_m[band])) * 0.5)
    else:
        t_split, y_split, x_half_top = None, None, x_half_full
    report.append("reference aperture taper: widest at t %.4f (%.0f mm), falls under 85%% "
                  "at t %s -> upper carve half-width %.4f m (skull allows %.4f)"
                  % (ref_panel["t_widest"], ref_panel["wmax"] / ref_panel["H"] * fig_h * 1000,
                     "n/a" if t_split is None else "%.4f" % t_split, x_half_top, x_half_full))

    def build_boxes(x_half, y_bot, y_top, z_back, z_front=0.30):
        """One box for the jaw-to-cheekbone band, an optional narrower one above it."""
        def mk(pid, xh, lo, hi):
            centre = (np.array([0.0, 0.5 * (lo + hi), 0.5 * (z_back + z_front)])
                      - hair_off) / scale_a
            size = np.array([2.0 * xh, hi - lo, z_front - z_back]) / scale_a
            return {"id": pid, "type": "box",
                    "center": [round(float(v), 6) for v in centre],
                    "size": [round(float(v), 6) for v in size]}
        split = y_split
        taper = (split is not None and y_bot + 0.01 < split < y_top - 0.01
                 and x_half_top < x_half - 0.004)
        if not taper:
            prims = [mk(CARVE_PRIM_ID, x_half, y_bot, y_top)]
            ops = [{"id": CARVE_OP_ID, "type": "subtract",
                    "left": output_op, "right": CARVE_PRIM_ID}]
            return prims, ops
        prims = [mk(CARVE_PRIM_ID, x_half, y_bot, split),
                 mk(CARVE_BROW_ID, min(x_half, x_half_top), split, y_top)]
        ops = [{"id": CARVE_OP_ID, "type": "subtract",
                "left": output_op, "right": CARVE_PRIM_ID},
               {"id": CARVE_BROW_OP_ID, "type": "subtract",
                "left": CARVE_OP_ID, "right": CARVE_BROW_ID}]
        return prims, ops

    # -- 4. baseline projections and the width-score model --------------------
    parts0 = [(occ_head, bmin_h, step_h, scale_h, np.zeros(3)),
              (occ_hair, bmin_a, step_a, scale_a, hair_off)]
    base_cov = {y: coverage(parts0, math.radians(y)) for y in YAWS}
    base_width_score = float(np.mean([math.exp(-v["geometry"]["width_rms_core_pct"] / 2.0)
                                      for v in metrics["views"]]))

    def evaluate(prims, ops):
        occ, bmin, step, scale = voxelise(hair, prims, ops)
        z_map, _ = front_surface(occ, bmin, step, scale, hair_off)
        ratio = float((head_on & (head_z > z_map)).sum()) / float(aperture0.sum())
        parts = [(occ_head, bmin_h, step_h, scale_h, np.zeros(3)),
                 (occ, bmin, step, scale, hair_off)]
        worst_row = 0.0
        worst_where = None
        yaw0_area = 0.0
        deltas = {}
        for yaw in YAWS:
            cov0, u0, u1, area0 = base_cov[yaw]
            cov1, v0, v1, area1 = coverage(parts, math.radians(yaw))
            drow = cov1 - cov0
            if float(drow.min()) < worst_row:
                worst_row = float(drow.min())
                worst_where = (yaw, float(ROW_Y[int(np.argmin(drow))]))
            with np.errstate(invalid="ignore"):
                ext = (v1 - v0) - (u1 - u0)
            deltas[yaw] = np.where(np.isfinite(ext), ext, 0.0)
            if yaw == 0:
                yaw0_area = (area1 - area0) * DU * DY
        t_rows = (ROW_Y + off_y - y_min) / fig_h
        rms_after = {}
        for view in metrics["views"]:
            yaw = int(round(view["yaw"])) % 360
            d_ext = deltas.get(yaw)
            if d_ext is None:
                # yaw not among the six this patch can project: carry it through
                # unchanged so the mean is still over all six views.
                rms_after[view["render"]] = view["geometry"]["width_rms_core_pct"]
                continue
            bands = view["geometry"]["profile"]["bands"]
            out = []
            for band in bands:
                sel = (t_rows >= band["t"] - 0.0125) & (t_rows < band["t"] + 0.0125)
                add = (float(d_ext[sel].mean()) / fig_h * 100.0) if sel.any() else 0.0
                out.append(band["core"]["d_pct"] + add)
            rms_after[view["render"]] = math.sqrt(float(np.mean(np.array(out) ** 2)))
        score_after = float(np.mean([math.exp(-r / 2.0) for r in rms_after.values()]))
        return dict(occ=occ, ratio=ratio, worst_row=worst_row, worst_where=worst_where,
                    yaw0_area=yaw0_area,
                    d_width_points=(score_after - base_width_score) * 20.0,
                    rms_after=rms_after, tris=triangle_count(occ, decim))

    # -- 5. candidate ladder, most aggressive first ---------------------------
    # y_top raises the hairline, z_back sets how much of the skull's own front
    # surface the carve clears, y_bot keeps the box off the chin (the hair below
    # the jaw is silhouette at yaw 45/90/270 and must not be touched), x_half is
    # capped at the skull so the front-view silhouette cannot move at all.
    y_tops = [y_top_target, y_top_target - 0.004, y_top_target - 0.008, hairline_now]
    z_backs = [float(np.percentile(front_z, p)) for p in (8, 12, 18)]
    x_halves = [x_half_full, x_half_full - 0.006]
    y_bots = [local_lo, local_lo + 0.004, local_lo + 0.008]
    ordered, seen = [], set()
    for y_top, z_back, x_half, y_bot in product(y_tops, z_backs, x_halves, y_bots):
        if y_top - y_bot < 0.05 or x_half <= 0.02:
            continue
        key = (round(x_half, 5), round(z_back, 5), round(y_bot, 5), round(y_top, 5))
        if key not in seen:
            seen.add(key)
            ordered.append(key)

    chosen = None
    tried = []
    for x_half, z_back, y_bot, y_top in ordered[:24]:
        prims, ops = build_boxes(x_half, y_bot, y_top, z_back)
        result = evaluate(prims, ops)
        ok = (result["ratio"] <= target_ratio * OVERSHOOT_TOLERANCE
              and result["worst_row"] >= -MAX_ROW_LOSS_M
              and result["d_width_points"] >= -MAX_WIDTH_SCORE_LOSS
              and result["yaw0_area"] >= -1e-9)
        tried.append((x_half, z_back, y_bot, y_top, result, ok))
        if ok:
            chosen = (x_half, z_back, y_bot, y_top, prims, ops, result)
            break

    for x_half, z_back, y_bot, y_top, res, ok in tried:
        where = res["worst_where"]
        report.append("  candidate x_half=%.4f z_back=%.4f y=%.4f..%.4f -> ratio %.3f, "
                      "worst row %+.1f mm%s, d_width %+.4f pts, yaw0 area %+.0f mm2  %s"
                      % (x_half, z_back, y_bot, y_top, res["ratio"], res["worst_row"] * 1000,
                         "" if where is None else " (yaw %d, y %+.3f)" % where,
                         res["d_width_points"], res["yaw0_area"] * 1e6,
                         "ACCEPT" if ok else "reject"))

    tris_after = tris_before
    if chosen is None:
        report.append("NO CARVE APPLIED: every candidate failed the silhouette or "
                      "overshoot guard. Hair descriptor left as found.")
    else:
        x_half, z_back, y_bot, y_top, prims, ops, result = chosen
        sdf["primitives"].extend(prims)
        sdf["operations"].extend(ops)
        tris_after = result["tris"]
        recovered_px = (result["ratio"] - 1.0) * ren_panel["face_px"]
        report.append("CARVE: %d box%s, z >= %.4f m (head-local), appended as the last "
                      "operation%s" % (len(prims), "" if len(prims) == 1 else "es", z_back,
                                       "s" if len(prims) > 1 else ""))
        for box_prim in prims:
            c = np.array(box_prim["center"], float) * scale_a + hair_off
            hs = np.array(box_prim["size"], float) * scale_a * 0.5
            report.append("    %-17s |x| <= %.4f m, y %.4f..%.4f m"
                          % (box_prim["id"], hs[0], c[1] - hs[1], c[1] + hs[1]))
        report.append("  front-view exposed skin %.0f -> %.0f px (x%.3f of %.3f wanted); "
                      "head-band skin fraction %.4f -> %.4f (ref %.4f)"
                      % (ren_panel["face_px"], ren_panel["face_px"] * result["ratio"],
                         result["ratio"], target_ratio,
                         ren_panel["frac"], ren_panel["frac"] * result["ratio"],
                         ref_panel["frac"]))
        report.append("  predicted width_rms_core_pct per view: " + ", ".join(
            "%s %.3f->%.3f" % (k.replace("render_", "").replace(".png", ""),
                               next(v["geometry"]["width_rms_core_pct"]
                                    for v in metrics["views"] if v["render"] == k), r)
            for k, r in sorted(result["rms_after"].items())))
        report.append("  hair triangles %d -> %d (%+d)" % (tris_before, tris_after,
                                                           tris_after - tris_before))

        # predicted colour movement, from measured pixel colours
        band_hair = ren_panel["hair"] & ~ren_panel["face"]
        if band_hair.sum() > 50 and ren_panel["face"].sum() > 50:
            hair_lab = [float(np.median(ren_panel[k][band_hair])) for k in ("L", "A", "B")]
            ren_face_lab = [float(np.median(ren_panel[k][ren_panel["face"]])) for k in ("L", "A", "B")]
            ref_face_lab = [float(np.median(ref_panel[k][ref_panel["face"]])) for k in ("L", "A", "B")]
            gain = dE(hair_lab, ref_face_lab) - dE(ren_face_lab, ref_face_lab)
            view0 = next((v for v in metrics["views"] if int(round(v["yaw"])) == 0), None)
            if view0 and gain > 0:
                n_px = view0["colour"]["pixels"]
                mean_de = view0["colour"]["mean_dE"]
                d_de = recovered_px * gain / n_px
                d_colour = math.exp(-(mean_de - d_de) / 15.0) - math.exp(-mean_de / 15.0)
                report.append("  colour model: %.0f px flip from dE %.1f to dE %.1f "
                              "-> yaw0 mean_dE %.3f -> %.3f, colour %.4f -> %.4f "
                              "(+%.3f pts if all six views move alike)"
                              % (recovered_px, dE(hair_lab, ref_face_lab),
                                 dE(ren_face_lab, ref_face_lab), mean_de, mean_de - d_de,
                                 math.exp(-mean_de / 15.0),
                                 math.exp(-(mean_de - d_de) / 15.0), d_colour * 10.0))

        hair["measurementSource"] = (
            "analysis/patch_face_scale.py -- face aperture re-measured from body_2.png "
            "(%.4f exposed-skin fraction) against render_yaw0.png (%.4f), carve solved "
            "against the head SDF's own front surface" % (ref_panel["frac"], ren_panel["frac"]))

    # -- 6. materials: contrast, not shape ------------------------------------
    mat_lab = {}
    for mid, mat in materials.items():
        path = (((mat.get("referencePbr") or {}).get("maps") or {}).get("albedo") or {}).get("path")
        if not path:
            continue
        lab = albedo_lab(path)
        if lab is not None:
            mat_lab[mid] = lab
    if not mat_lab:
        report.append("no material albedo maps readable; material pass skipped")

    def best_material(target, exclude=()):
        pool = [(dE(lab, target), mid) for mid, lab in mat_lab.items() if mid not in exclude]
        pool.sort()
        return pool[0] if pool else (None, None)

    brow_l = components.get("brow-l")
    mouth = components.get("mouth")

    if mat_lab and brow_l is not None:
        y_brow = float(brow_l["transform"]["position"][1])
        half_w = abs(float(brow_l["transform"]["position"][0])) + \
            0.5 * float(brow_l["dimensions"]["width"])
        ref_brow, n = sample_box(ref_panel, off_y, y_min, fig_h, y_brow,
                                 half_w, 0.009, "dark")
        if ref_brow is None or not (5.0 <= ref_brow[0] <= 40.0 and abs(ref_brow[1]) < 22
                                    and abs(ref_brow[2]) < 22):
            report.append("brow: reference colour not measurable (%s); brows left alone"
                          % (None if ref_brow is None else np.round(ref_brow, 1)))
        else:
            d_new, pick = best_material(ref_brow)
            for cid in ("brow-l", "brow-r"):
                comp = components.get(cid)
                if comp is None:
                    continue
                old = comp.get("material")
                d_old = dE(mat_lab[old], ref_brow) if old in mat_lab else float("nan")
                if old != pick:
                    comp["material"] = pick
                    comp["materialLayers"] = [pick]
                    report.append("%s material %s (albedo Lab %s, dE %.1f) -> %s "
                                  "(Lab %s, dE %.1f) against measured reference brow "
                                  "Lab %s from %d px"
                                  % (cid, old, np.round(mat_lab.get(old, [0, 0, 0]), 1), d_old,
                                     pick, np.round(mat_lab[pick], 1), d_new,
                                     np.round(ref_brow, 1), n))
                else:
                    report.append("%s material already %s (dE %.1f) -- unchanged"
                                  % (cid, pick, d_new))

    if mat_lab and mouth is not None:
        y_mouth = float(mouth["transform"]["position"][1])
        ref_lip, n = sample_box(ref_panel, off_y, y_min, fig_h, y_mouth,
                                0.5 * float(mouth["dimensions"]["width"]) + 0.008,
                                0.011, "red")
        if ref_lip is None or not (15.0 <= ref_lip[0] <= 60.0 and ref_lip[1] >= 12.0):
            report.append("mouth: reference lip colour not measurable (%s); mouth left alone"
                          % (None if ref_lip is None else np.round(ref_lip, 1)))
        else:
            d_new, pick = best_material(ref_lip)
            old = mouth.get("material")
            d_old = dE(mat_lab[old], ref_lip) if old in mat_lab else float("nan")
            if d_new > MAX_LIP_DE:
                report.append("mouth: nearest material %s is dE %.1f from the measured "
                              "reference lip Lab %s -- over the %.0f dE bar, left alone"
                              % (pick, d_new, np.round(ref_lip, 1), MAX_LIP_DE))
            elif old == pick:
                report.append("mouth material already %s (dE %.1f) -- unchanged" % (pick, d_new))
            elif not (d_old - d_new >= MIN_LIP_GAIN_DE):
                report.append("mouth: %s (dE %.1f) beats %s (dE %.1f) by only %.1f dE, "
                              "under the %.0f dE bar -- left alone"
                              % (pick, d_new, old, d_old, d_old - d_new, MIN_LIP_GAIN_DE))
            else:
                mouth["material"] = pick
                mouth["materialLayers"] = [pick]
                report.append("mouth material %s (albedo Lab %s, dE %.1f) -> %s "
                              "(Lab %s, dE %.1f) against measured reference lip Lab %s "
                              "from %d px; this also flips the polarity -- the render's "
                              "lip is currently lighter than the chin, the reference's "
                              "is darker"
                              % (old, np.round(mat_lab[old], 1), d_old, pick,
                                 np.round(mat_lab[pick], 1), d_new, np.round(ref_lip, 1), n))

    # -- 7. write ------------------------------------------------------------
    with open(SPEC, "w", encoding="utf-8") as handle:
        json.dump(spec, handle, indent=1)

    budget = (spec.get("performanceBudget") or {}).get("targetTriangles", 250000)
    total = sum(m["tris"] for m in meshes)
    print("patch_face_scale: %s%s" % (SPEC, "  (re-run: previous carve replaced)" if had_carve else ""))
    for line in report:
        print("  - " + line)
    print("  - TRIANGLE COST %+d (hair %d -> %d); model %d -> %d of %d budget"
          % (tris_after - tris_before, tris_before, tris_after,
             total, total + (tris_after - tris_before), budget))


if __name__ == "__main__":
    main()
