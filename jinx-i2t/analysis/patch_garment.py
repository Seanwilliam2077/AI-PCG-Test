#!/usr/bin/env python
"""patch_garment.py -- garment-detail corrections, re-measured from the reference every run.

WHAT WAS MEASURED (all numbers re-derived at runtime; the values below are what this
script printed against baseline/spec_accepted.json, so they are reproducible)

Frames.  Both frames are bbox-normalised exactly the way tools/evaluate.py normalises
before scoring: figure-height scale, top-anchored y, bbox-centre x, against the model
bbox from baseline/meshes_accepted.json (x -0.224..0.246, y -0.001..1.721).
  render  out/accepted/render_yaw0.png  861 rows  ->  2.000 mm/px
  ref     ref/views/clay_2.png         1278 rows  ->  1.347 mm/px  (body_2 is registered
          to clay_2 at alpha IoU 0.942 and is indexed in the same pixel coordinates)
Component local -> world offsets come from baseline/meshes_accepted.json minus the
occupied AABB of the same component's descriptor in baseline/spec_accepted.json, both
immutable.  A numpy re-implementation of sdfSample/polygonizeSdf reproduces all nine
touched components' AABBs to <0.5 mm and their triangle counts exactly (e.g. x-lacing
77.0x71.9x10.5 mm / 1046 tris, choker 101.2x30.0x101.6 / 5384, sash 4612, hem-r 2418).

The reference's absolute centreline is the weak axis of that alignment, so it is measured
rather than assumed: the ref X-lacing's four-ring centroid sits at x +0.0164 against the
render mesh's +0.0070, so ref x +0.0094 is render x 0.  An independent check falls out of
the choker: read at that offset, the reference's top wrap lands 0.6 mm from where the
render already puts it.  Everything x-sensitive here either uses that offset or is
expressed relative to the feature's own centroid; nothing is placed on raw reference x.

1. TROUSER HEMS -- the tatter is cut into the wrong edge, and it detaches the rings.
   Both hem rings subtract eight notch spheres at the ring's TOP (pants-hem-r local
   y +0.029, pants-hem-l +0.015).  Consequences measured in out/accepted/render_yaw0.png:
     - her right leg: purple runs per column are 0.520-0.600 (trouser) and 0.462-0.498
       (ring), i.e. a 6-22 mm band of bare SKIN between the trouser rim (flat 0.520 at
       every column) and the notched ring top.  Where the ring is also outside the shin
       this opens a genuine hole in the alpha: 51 px at x -0.135..-0.125, y 0.500..0.518.
     - her left leg: the notches eat the ring's whole front wall, so the visible hem is
       the pants-l rim at 0.596-0.598 with skin from there down; the ring survives only
       as 12- and 8-px fragments at x +0.091..+0.115.
     - the visible bottom edge is FLAT (0.462-0.464 her right, 0.548 her left) where the
       reference is tattered: ref lowest-purple per column is 0.4686..0.5009 on her right
       and 0.5481..0.5804 on her left, both 32.3 mm peak-to-peak.  HANDEDNESS: +X is her
       left = screen-right; her LEFT hem sits 74.1 mm HIGHER than her right, and the
       render already carries that asymmetry.
   CHANGE: move the eight notch spheres of each ring from the top of the ring to the
   bottom (pants-hem-r local y +0.029 -> -0.01267, pants-hem-l +0.015 -> -0.01247),
   placing each sphere's top at the reference's own cut-back level (95th percentile of the
   per-column ref hem edge on that leg: 0.5009 and 0.5737), and extend pants-hem-l's
   retaining box up from 0.5863 to the measured pants-l rim at 0.5980 so the ring meets
   the trouser at every column.  No radius, no x, no z, no component position is touched.
   Verified by voxelising the result: hem-r's projected top is now flat at 0.5273 with the
   bottom running 0.4630..0.5000, hem-l's top flat at 0.5983 with the bottom 0.5480..0.5720.
   TRADE-OFF: the ring's un-notched top becomes flat, which buys 7-25 mm of overlap with
   the trouser at every azimuth -- that is what closes the hole -- at the cost of losing
   the (invisible) tatter on the top edge.  The notch spheres never reach the ring's
   extreme-|x| point (they sit at 22.5 deg either side of it, 27.0 mm away with r 23.0 mm),
   so the ring's x-extent is unchanged at every height and the width profile cannot move.

2. THE PALE OLIVE BOX AT THE CROTCH -- FIXED, not removed.
   Per-row material composition of body_2 in the world band x -0.020..+0.066: sage canvas
   is 96% at y 1.030 and 1.020, 68/20 sage/purple at 1.015, 40/54 at 1.010, and 0/93 at
   1.000 -- the reference apron ENDS at y ~1.013, and below it is trouser.  The render's
   olive box runs down to a median y of 0.982 across x -0.023..+0.089.  That is a ~20-33 mm
   x 112 mm strip of canvas where the reference is 88-100% purple, inside the hips_sash
   colour region (21 150 px, dE 23.35, hue_delta +25.7 deg, the largest hue gap outside
   boots/braids).  The clay reference shows the same edge as a slanted geometric one.
   CHANGE: append a terminal `intersect` half-space to BOTH `canvas-panel` and `sash`
   (they share the edge; per-voxel front-depth puts canvas-panel in front above y 0.990
   and sash below) cutting everything below the reference's own lower edge, fitted over 87
   columns as y = -0.2062x + 1.0165 (-11.65 deg, fit rms 1.0 mm) -- a tilted line rather
   than a horizontal one because the reference edge falls toward her left.  In render
   coordinates that runs 1.0185 at x -0.019 to 0.9866 at x +0.136; voxelising the result
   gives canvas-panel 1.0165 -> 0.9885 and sash 1.0168 -> 0.9893, both within one voxel of
   the fit.  Removing the apron instead would delete a feature the reference plainly has;
   only its lower 20-33 mm is wrong.  What is exposed underneath is the pelvis (`pants`,
   purple) in the centre -- sampled directly in the render just below the current box at
   RGB (73,38,79) -- and the leather `pouch` on her left, both of which are what the
   reference shows there.

3. X-LACING -- split into two components, because one component carries one material.
   Reference (Lab segmentation of body_2, four brass connected components + the sage
   blob): the assembly is 99.7 x 74.1 mm and 62% cloth by area; four eyelet rings of
   31 mm mean outer diameter with open holes showing skin; two crossed cloth straps 14.1
   and 12.2 mm wide running ring-centre to ring-centre, at -38.58 deg and +26.09 deg.
   Ring geometry cross-checks: the ring-centre span (67.4 x 45.1 mm) plus twice the
   bbox-derived outer radius gives 98.4 x 76.1 mm against the measured 99.7 x 74.1 mm
   footprint, and the mean radial brass fraction about the ring centres is 0.00 out to
   6 mm, 0.43 at 10 mm, 0.65 at 13 mm and 0.00 by 18 mm -- an annulus with a hole of
   about 9 mm radius, which is what the median-radius estimator returns (9.3 mm).
   Render: a solid brass X, 77.0 x 71.9 mm, no eyelets (the current annuli do open, but
   the holes are 1-2 voxels = 3.5 x 2.9 mm and `decimate 0.4` plus smooth normals erase
   them), straps at -41.5 deg and +36.9 deg -- strap B is 10.8 deg too steep.
   CHANGE: `x-lacing` keeps its id, parent, material (`brass`) and position and becomes
   the four rings alone, at the measured centres relative to the assembly centroid, with
   the bounds tightened to the rings and the resolution raised from 32 to 44 so the
   x-voxel is 2.50 mm rather than 3.50; voxelising the result gives 95.2 x 76.0 mm with a
   17.5 mm hole through every ring.  A new `x-lacing-straps` (parent `top`, material
   `canvas`, same transform) carries the two straps as two rotated SDF boxes joined by a
   smooth-union.  BOXES, NOT ATTACHED CYLINDERS: an attachment cylinder has a circular
   cross-section (spec rule 2), so a 14 mm-wide strap would also stand 14 mm proud and
   read as a rod; and two attachment cylinders would need two components and two draw
   calls where one implicit component with two boxes gives flat straps that merge
   correctly at the crossing (authored 7 mm thick, 10.2 mm once voxelised -- z is not
   measurable from a front panel, and 10 mm matches the rings the straps pass through).  Ring positions are RELATIVE to the assembly centroid, so
   nothing here moves the component in world space.  All twelve sampled ring points were
   checked against `top`'s own front surface and stand 6-25 mm proud of it, so widening
   the assembly does not sink any ring into the halter.
   NOT DONE: the reference shows bare skin through each eyelet; the render will show the
   halter top instead.  Perforating `top` was rejected -- it is a 5.9 mm-voxel shell at
   resolution 40 and four 18 mm holes through it would ragged its front for about 130 px
   of gain.  The assembly's DEPTH is also unverified: nothing in a front panel measures
   how far the lacing should stand off the chest, so transform.position.z is untouched.

4. CHOKER -- pitch and tilt.
   Per-column dark-run scan of body_2 over the longest contiguous block of columns that
   resolves all three wraps (16 columns, ref x +0.0076..+0.0278, per-band line fits with
   rms 0.4-0.5 mm): tilts -14.04 / -27.20 / +7.83 deg (the top two descending toward her
   left), pitch 15.3 and 21.4 mm, thicknesses 10.1 / 10.8 / 5.4 mm.  Render: three flat
   bands, all tilt 0, stack height 24.7 mm against the reference's 36.6 mm.  Read at the
   measured x offset the reference's top wrap lands 0.6 mm from where the render already
   puts it, so band 1 is HELD FIXED and only the pitch below it is corrected.
   A wrap's VISIBLE thickness is not its disc's: the core subtraction leaves only the
   disc's rim, where an ellipsoid has already tapered, so the built discs are calibrated
   by voxelising and re-measuring rather than by formula -- 3.1/4.7/3.1 mm on the first
   pass, converging to 10.6/10.6/5.3 mm against the 10.1/10.8/5.4 targets, with the wrap
   centres landing at 1.4635/1.4477/1.4275 against 1.4641/1.4489/1.4275.
   `choker-straps` currently sits at world y 1.4329, a fourth band where the reference
   has bare skin; it is re-aimed onto the lowest wrap (tilt and height) so it reads as
   that wrap's proud front section instead.

EXPECTED MEASURABLE EFFECT (falsifiable, per view yaw0 unless stated)
  - The 51-px alpha hole at x -0.135..-0.125, y 0.500..0.518 must be GONE; `matte`
    hole_px for the render must not gain a component there.  If it survives, item 1 failed.
  - geometry.profile bands 7-10 ("calf (boots/pants)", t 0.1875-0.2625) currently run
    render/ref = 1.097 / 1.109 / 1.000 / 0.935 on `full`; they must not move by more than
    0.01 either way, because no hem radius changes.  Bands 11-14 (ratios 1.073 / 1.088 /
    1.115 / 1.121) must likewise hold.  A drop in bands 11-14 would mean the notches ate
    the silhouette and item 1 must be reverted.
  - width_rms_core_pct (3.619) and landmark_rms_pct (3.349) should both hold to +-0.05:
    this patch is deliberately width- and landmark-neutral.  Every touched component's
    world x extent is printed before and after; only x-lacing's moves, and it is an
    internal detail 47 mm inside the halter's own silhouette edge.
  - shape IoU (0.82533 on this scoreboard's `terms.shape`) should hold or rise slightly
    (the hole closes, the tatter replaces a flat edge).  A fall of more than 0.002 means
    the hem notches are cutting silhouette the reference keeps.
  - edge (0.53472) and chamfer (0.48658) should RISE: four resolved eyelets, two correctly
    angled straps, three tilted choker wraps and a correctly placed apron edge are all
    internal contours the clay reference resolves and the current render does not.
    This is the term this patch is really aimed at.
  - colour: region `hips_sash` dE 23.345 / hue_delta +25.68 deg should fall (the olive
    strip becomes purple); `knees` (dE 21.281, da +9.539) should fall as ~48 x 90 mm of
    skin on her left calf becomes trouser; `chest_top` (dE 22.101) should move as ~62% of
    the X-lacing turns from brass to canvas.  If hips_sash hue_delta does not fall, item 2
    cut the wrong component.

WHAT IS NOT MEASURED HERE.  Everything above is from the front panel.  No depth (z) of
any garment feature is verified -- strap thickness, ring thickness, sash depth and the
lacing's stand-off from the chest are all left exactly as they were.  The 45/90/135/270
degree panels were not opened for this dimension.

TRIANGLES: reported at the end of every run, computed by voxelising each touched
descriptor exactly as polygonizeSdf does and applying the component's decimate ratio.
Net -1598, so this patch returns headroom rather than spending it.
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GD = "gd_"  # reserved id prefix for primitives/operations this patch owns


# --------------------------------------------------------------------------------------
# polygonizeSdf / sdfSample, re-implemented from src/createJinxModel.ts
# --------------------------------------------------------------------------------------

def _euler_inv(p: np.ndarray, rot) -> np.ndarray:
    rx, ry, rz = rot
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return p @ (Rx @ Ry @ Rz)          # p @ R == R^T p == inverse rotation


def _prim(P: np.ndarray, pr: dict) -> np.ndarray:
    t = pr.get("transform") or {}
    tr = t.get("position") or t.get("translation") or pr.get("center") or [0, 0, 0]
    rot = t.get("rotation") or [0, 0, 0]
    sc = t.get("scale") or [1, 1, 1]
    L = P - np.array(tr, float)
    if any(abs(r) > 1e-12 for r in rot):
        L = _euler_inv(L, rot)
    L = L / np.array(sc, float)
    kind = pr["type"]
    if kind == "sphere":
        d = np.linalg.norm(L, axis=-1) - pr.get("radius", 0.5)
    elif kind == "capsule":
        r, h = pr.get("radius", 0.25), pr.get("height", 1.0)
        y = np.clip(L[..., 1], -h * 0.5, h * 0.5)
        d = np.sqrt(L[..., 0] ** 2 + (L[..., 1] - y) ** 2 + L[..., 2] ** 2) - r
    elif kind == "box":
        size = np.array(pr.get("size") or pr.get("dimensions") or [1, 1, 1], float)
        q = np.abs(L) - size * 0.5
        d = np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(np.max(q, axis=-1), 0)
    elif kind == "cone":
        r, h = pr.get("radius", 0.5), pr.get("height", 1.0)
        taper = r * (1 - (L[..., 1] + h * 0.5) / h)
        d = np.maximum(np.hypot(L[..., 0], L[..., 2]) - np.maximum(0, taper),
                       np.abs(L[..., 1]) - h * 0.5)
    elif kind == "ellipsoid":
        rad = np.array(pr.get("radii") or [pr["radius"]] * 3, float)
        d = (np.linalg.norm(L / rad, axis=-1) - 1) * rad.min()
    else:
        raise ValueError(kind)
    return d * min(sc)


def _eval_sdf(desc: dict, P: np.ndarray) -> np.ndarray:
    nodes = {}
    for pr in desc["primitives"]:
        nodes[pr["id"]] = _prim(P, pr)
    res = nodes[desc["primitives"][0]["id"]] if desc["primitives"] else None
    for i, op in enumerate(desc.get("operations") or []):
        left, right = nodes.get(op["left"]), nodes.get(op["right"])
        if left is None or right is None:
            continue
        if op["type"] == "smooth-union":
            r = op.get("radius", 0.1)
            blend = np.maximum(r - np.abs(left - right), 0) / r
            c = np.minimum(left, right) - blend * blend * r * 0.25
        elif op["type"] == "subtract":
            c = np.maximum(left, -right)
        elif op["type"] == "intersect":
            c = np.maximum(left, right)
        else:
            continue
        nodes[op.get("id") or op.get("output") or "op%d" % i] = c
        res = c
    return res


def voxelise(desc: dict):
    """Occupancy grid, bounds min and step -- byte-for-byte what polygonizeSdf samples."""
    res = max(4, min(64, int(desc.get("resolution", 32))))
    b = desc.get("bounds") or {"min": [-2, -2, -2], "max": [2, 2, 2]}
    mn, mx = np.array(b["min"], float), np.array(b["max"], float)
    step = (mx - mn) / res
    i = np.arange(res)
    Z, Y, X = np.meshgrid(mn[2] + (i + .5) * step[2],
                          mn[1] + (i + .5) * step[1],
                          mn[0] + (i + .5) * step[0], indexing="ij")
    return _eval_sdf(desc, np.stack([X, Y, Z], -1)) <= 0, mn, step, res


def sdf_stats(desc: dict, ratio: float | None):
    occ, mn, step, res = voxelise(desc)
    if not occ.any():
        return None
    pad = np.zeros((res + 2,) * 3, bool)
    pad[1:-1, 1:-1, 1:-1] = occ
    faces = 0
    for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
        faces += int((occ & ~np.roll(pad, sh, axis=ax)[1:-1, 1:-1, 1:-1]).sum())
    zs, ys, xs = np.nonzero(occ)
    lo = mn + np.array([xs.min(), ys.min(), zs.min()]) * step
    hi = mn + np.array([xs.max() + 1, ys.max() + 1, zs.max() + 1]) * step
    dense = faces * 2
    tris = max(4, int(dense * ratio)) if ratio and 0 < ratio < 1 else dense
    return {"lo": lo, "hi": hi, "ext": hi - lo, "dense": dense, "tris": tris,
            "occ": occ, "mn": mn, "step": step, "res": res}


# --------------------------------------------------------------------------------------
# image frames
# --------------------------------------------------------------------------------------

class Frame:
    """bbox-normalised pixel<->world mapping, matching tools/evaluate.py's normalise()."""

    def __init__(self, path, ymin, ymax, xmin, xmax):
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if im is None:
            raise SystemExit("cannot read %s" % path)
        self.im = im
        self.alpha = im[:, :, 3] > 128
        ys, xs = np.nonzero(self.alpha)
        self.r0, self.r1, self.c0, self.c1 = ys.min(), ys.max(), xs.min(), xs.max()
        self.S = (ymax - ymin) / (self.r1 - self.r0 + 1)
        self.xc = (xmin + xmax) / 2.0
        self.pc = (self.c0 + self.c1) / 2.0
        self.ymax = ymax
        lab = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
        self.L = lab[:, :, 0] * 100.0 / 255.0
        self.A = lab[:, :, 1] - 128.0
        self.B = lab[:, :, 2] - 128.0

    def y(self, py):  return self.ymax - (py - self.r0 + 0.5) * self.S
    def x(self, px):  return self.xc + (px - self.pc) * self.S
    def py(self, y):  return int(round(self.r0 - 0.5 + (self.ymax - y) / self.S))
    def px(self, x):  return int(round(self.pc + (x - self.xc) / self.S))


def ref_frame(ymin, ymax, xmin, xmax):
    """clay_2 sets the frame (it is what the judge scores geometry against); body_2 is
    registered to it at the same origin, so body_2 pixels are read in clay_2 coords."""
    f = Frame(os.path.join(ROOT, "ref/views/clay_2.png"), ymin, ymax, xmin, xmax)
    body = cv2.imread(os.path.join(ROOT, "ref/views/body_2.png"), cv2.IMREAD_UNCHANGED)
    h = min(f.im.shape[0], body.shape[0])
    w = min(f.im.shape[1], body.shape[1])
    pad = np.zeros_like(f.im)
    pad[:h, :w] = body[:h, :w]
    lab = cv2.cvtColor(pad[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    f.L = lab[:, :, 0] * 100.0 / 255.0
    f.A = lab[:, :, 1] - 128.0
    f.B = lab[:, :, 2] - 128.0
    f.alpha = pad[:, :, 3] > 128
    f.im = pad
    return f


def runs(col: np.ndarray):
    out, start = [], None
    for i, v in enumerate(col):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(col) - 1))
    return out


# --------------------------------------------------------------------------------------
# offsets: component local frame -> world, from the immutable baselines
# --------------------------------------------------------------------------------------

def world_offsets(accepted_spec, meshes, ids):
    by_id = {c["id"]: c for c in accepted_spec["componentTree"]}
    by_name = {m["name"]: m for m in meshes}
    out = {}
    for cid in ids:
        comp = by_id[cid]
        st = sdf_stats(comp["geometryDescriptor"]["sdf"], None)
        m = by_name[comp["name"]]
        out[cid] = (m["x0"] - st["lo"][0], m["minY"] - st["lo"][1])
    return out


# --------------------------------------------------------------------------------------
# measurements
# --------------------------------------------------------------------------------------

def measure_hems(ref: Frame, ren: Frame, meshes):
    """Per-column lowest trouser pixel on each leg, ref and render, plus the render's
    pants-l rim (the highest point of the trouser cylinder's bottom edge)."""
    def purple(f, lmax):
        return (f.A > 6) & (f.B < 4) & (f.L < lmax) & f.alpha

    out = {}
    for tag, f, lmax in (("ref", ref, 52.0), ("render", ren, 55.0)):
        pm = purple(f, lmax)
        n, lab, st, _ = cv2.connectedComponentsWithStats(pm.astype(np.uint8), 8)
        big = lab == (int(np.argmax(st[1:, 4])) + 1)
        legs = {"r": [], "l": []}
        for pxi in range(f.im.shape[1]):
            col = np.nonzero(big[:, pxi])[0]
            if not len(col):
                continue
            yy = f.y(col)
            keep = col[(yy > 0.40) & (yy < 0.75)]
            if not len(keep):
                continue
            xw = f.x(pxi)
            if xw < -0.02:
                legs["r"].append((xw, f.y(keep.max())))
            elif xw > 0.005:
                legs["l"].append((xw, f.y(keep.max())))
        # Drop the columns at each leg's outer edge, where the "lowest trouser pixel"
        # is the side seam running up the thigh rather than the hem: keep only columns
        # within 35 mm of the leg's median hem height.
        clean = {}
        for k, v in legs.items():
            arr = np.array(v)
            med = float(np.median(arr[:, 1]))
            clean[k] = arr[np.abs(arr[:, 1] - med) <= 0.035]
        out[tag] = clean

    # render pants-l rim: walk down the contiguous trouser run that reaches y 0.68
    pm = purple(ren, 55.0)
    rim = []
    for pxi in range(ren.im.shape[1]):
        xw = ren.x(pxi)
        if not (0.0 < xw < 0.105):
            continue
        top, bot = ren.py(0.68), ren.py(0.50)
        col = pm[top:bot + 1, pxi]
        if not col[0]:
            continue
        i = 0
        while i < len(col) and col[i]:
            i += 1
        rim.append(ren.y(top + i - 1))
    out["pants_l_rim"] = float(np.max(rim)) if rim else None
    return out


def measure_apron(ref: Frame, meshes):
    """Lower edge of the reference's sage apron, fitted as a line over the render
    apron's own x span."""
    by_name = {m["name"]: m for m in meshes}
    x0 = min(by_name["Canvas panel"]["x0"], by_name["Hip sash"]["x0"])
    x1 = max(by_name["Canvas panel"]["x1"], by_name["Hip sash"]["x1"])
    sage = ((ref.A < 6) & (ref.B > 6) & (ref.L > 30) & (ref.L < 72)
            & ~((ref.A >= 9) & (ref.B >= 13) & (ref.L >= 50)) & ref.alpha)
    top, bot = ref.py(1.09), ref.py(0.94)
    pts = []
    for pxi in range(ref.px(x0), ref.px(x1) + 1):
        col = sage[top:bot + 1, pxi]
        rr = [r for r in runs(col) if r[1] - r[0] >= 3]
        if not rr:
            continue
        pts.append((ref.x(pxi), ref.y(top + rr[-1][1])))
    pts = np.array(pts)
    if len(pts) < 8:
        raise SystemExit("apron: only %d columns segmented" % len(pts))
    xs, ys = pts[:, 0], pts[:, 1]
    keep = np.ones(len(xs), bool)
    for _ in range(4):                                    # trimmed least squares
        m, c = np.polyfit(xs[keep], ys[keep], 1)
        resid = np.abs(ys - (m * xs + c))
        keep = resid <= max(0.006, 2.0 * np.median(resid[keep]))
    m, c = np.polyfit(xs[keep], ys[keep], 1)
    return {"slope": float(m), "intercept": float(c), "n": int(keep.sum()),
            "x0": float(x0), "x1": float(x1), "pts": pts,
            "fit_x0": float(xs[keep].min()), "fit_x1": float(xs[keep].max()),
            "rms": float(np.sqrt(np.mean((ys[keep] - (m * xs[keep] + c)) ** 2)))}


def measure_render_apron(ren: Frame, meshes):
    by_name = {m["name"]: m for m in meshes}
    x0 = min(by_name["Canvas panel"]["x0"], by_name["Hip sash"]["x0"])
    x1 = max(by_name["Canvas panel"]["x1"], by_name["Hip sash"]["x1"])
    olive = (ren.B > 9) & (ren.A < 6) & (ren.L > 32) & (ren.L < 68) & ren.alpha
    top, bot = ren.py(1.09), ren.py(0.93)
    lows = []
    for pxi in range(ren.px(x0), ren.px(x1) + 1):
        col = olive[top:bot + 1, pxi]
        rr = [r for r in runs(col) if r[1] - r[0] >= 4]
        if not rr:
            continue
        lows.append(ren.y(top + rr[-1][1]))
    return float(np.median(lows)) if lows else None


def measure_xlacing(ref: Frame):
    """Four brass eyelet rings + two sage straps, measured relative to the assembly's
    own centroid so the reference's absolute x centreline never enters."""
    y0, y1, x0, x1 = 1.285, 1.405, -0.080, 0.090
    a, b = ref.py(y1), ref.py(y0)
    c, d = ref.px(x0), ref.px(x1)
    sl = (slice(a, b + 1), slice(c, d + 1))
    L, A, B = ref.L[sl], ref.A[sl], ref.B[sl]
    skin = (A >= 9) & (B >= 13) & (L >= 45)
    sage = (L >= 45) & (A < 7) & (B >= 5) & (B < 22) & ~skin
    brass = (L >= 28) & (L < 62) & (B >= 14) & (A >= 1) & ~skin & ~sage
    wx = lambda j: ref.x(c + j)
    wy = lambda i: ref.y(a + i)

    asm = (sage | brass).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(asm, 8)
    blob = lab == (int(np.argmax(st[1:, 4])) + 1)
    ys, xs = np.nonzero(blob)
    footprint = ((xs.max() - xs.min() + 1) * ref.S, (ys.max() - ys.min() + 1) * ref.S)
    cloth_frac = float((sage & blob).sum()) / max(1, int(((sage | brass) & blob).sum()))

    bm = cv2.morphologyEx((brass & blob).astype(np.uint8), cv2.MORPH_CLOSE,
                          np.ones((3, 3), np.uint8))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(bm, 8)
    cands = sorted(((st2[i][4], i) for i in range(1, n2) if st2[i][4] >= 25), reverse=True)
    if len(cands) < 4:
        raise SystemExit("x-lacing: found %d brass rings, expected 4" % len(cands))
    rings = []
    for _, i in cands[:4]:
        x, y, w, h, _a = st2[i]
        rings.append({"cx": (wx(x) + wx(x + w - 1)) / 2.0,
                      "cy": (wy(y) + wy(y + h - 1)) / 2.0,
                      "rx": w * ref.S / 2.0, "ry": h * ref.S / 2.0,
                      "col": x + w // 2, "row": y + h // 2})
    cx = float(np.mean([r["cx"] for r in rings]))
    cy = float(np.mean([r["cy"] for r in rings]))
    named = {}
    for r in rings:
        key = ("T" if r["cy"] > cy else "B") + ("L" if r["cx"] < cx else "R")
        named[key] = r
    if set(named) != {"TL", "TR", "BL", "BR"}:
        raise SystemExit("x-lacing: rings did not fall into four quadrants: %s" % sorted(named))

    # Outer radius from the ring bounding boxes.  Cross-check: the whole assembly is
    # (ring-centre span) + 2*outer_r in each axis, and that reproduces the measured
    # sage-plus-brass footprint -- printed by the caller.
    outer_r = float(np.mean([(r["rx"] + r["ry"]) / 2.0 for r in rings]))
    # Hole radius from the MEDIAN RADIUS of each ring's brass pixels.  For an annulus
    # the area-weighted median radius is sqrt((r^2+R^2)/2), so r = sqrt(2*med^2 - R^2).
    # The straps occlude particular ANGLES, not particular radii, so this estimator is
    # unbiased where a scanline or a flood-fill is not (the straps break the annulus, so
    # a scanline through the centre can miss one wall entirely).
    inners, profiles = [], []
    for _, i in cands[:4]:
        x, y, w, h, _a = st2[i]
        ys2, xs2 = np.nonzero(lab2 == i)
        ccx, ccy = (2 * x + w - 1) / 2.0, (2 * y + h - 1) / 2.0
        R = (w + h) / 4.0 * ref.S
        med = float(np.median(np.hypot((xs2 - ccx) * ref.S, (ys2 - ccy) * ref.S)))
        inners.append(math.sqrt(max(0.0, 2 * med * med - R * R)))
        ang = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        prof = []
        for k in range(14):
            rc = (k + 0.5) * ref.S
            qx = np.round(ccx + rc * np.cos(ang) / ref.S).astype(int)
            qy = np.round(ccy + rc * np.sin(ang) / ref.S).astype(int)
            ok = (qx >= 0) & (qy >= 0) & (qx < lab2.shape[1]) & (qy < lab2.shape[0])
            prof.append((rc, float((lab2[qy[ok], qx[ok]] == i).mean())))
        profiles.append(prof)
    hole_r = float(np.mean(inners))
    wall = outer_r - hole_r
    prof_mean = [(p[0], float(np.mean([pr[k][1] for pr in profiles])))
                 for k, p in enumerate(profiles[0])]

    sm = sage.astype(np.uint8)
    n3, lab3, st3, _ = cv2.connectedComponentsWithStats(sm, 8)
    smask = lab3 == (int(np.argmax(st3[1:, 4])) + 1)
    sy, sx = np.nonzero(smask)
    P = np.stack([np.array([wx(j) for j in sx]), np.array([wy(i) for i in sy])], 1)
    axes = {"A": (named["TL"], named["BR"]), "B": (named["BL"], named["TR"])}
    geom, tt, pp = {}, {}, {}
    for k, (p_, q_) in axes.items():
        p = np.array([p_["cx"], p_["cy"]])
        q = np.array([q_["cx"], q_["cy"]])
        v = q - p
        ln = float(np.linalg.norm(v))
        u = v / ln
        dd = P - p
        tt[k] = dd @ u
        pp[k] = dd[:, 0] * (-u[1]) + dd[:, 1] * u[0]
        geom[k] = {"p": p, "q": q, "u": u, "len": ln,
                   "angle": math.atan2(v[1], v[0])}
    own = np.where(np.abs(pp["A"]) <= np.abs(pp["B"]), 0, 1)
    for i, k in enumerate(("A", "B")):
        sel = own == i
        t = tt[k][sel]
        near = sel & (np.abs(pp[k]) < 0.012)
        widths = []
        lo, hi = t.min(), t.max()
        step = 0.006
        e = lo
        while e < hi:
            s3 = near & (tt[k] >= e) & (tt[k] < e + step)
            if s3.sum() >= 4 and (e + step / 2 < 0.020 or e + step / 2 > 0.052):
                widths.append(pp[k][s3].max() - pp[k][s3].min())
            e += step
        geom[k]["t0"] = float(t.min())
        geom[k]["t1"] = float(t.max())
        geom[k]["span"] = float(t.max() - t.min())
        geom[k]["width_mask"] = float(np.median(widths)) if widths else 0.013
        geom[k]["width"] = max(0.008, geom[k]["width_mask"] - ref.S)
    return {"rings": named, "cx": cx, "cy": cy, "outer_r": outer_r, "hole_r": hole_r,
            "wall": wall, "footprint": footprint, "cloth_frac": cloth_frac, "straps": geom,
            "radial": prof_mean}


def measure_choker(ref: Frame, dx: float, render_band1_y: float):
    """Three wraps: per-column dark runs over the longest CONTIGUOUS block of columns
    that resolves exactly three, then a line fit per band.

    `dx` is the ref->render x offset (ref x + (-dx) == render x); the three fitted lines
    are evaluated at the render choker's own centreline so that the pitch, which is
    x-dependent because the wraps have different tilts, is read at the right place."""
    y0, y1, x0, x1 = 1.415, 1.480, -0.010, 0.062
    a, b = ref.py(y1), ref.py(y0)
    c, d = ref.px(x0), ref.px(x1)
    sl = (slice(a, b + 1), slice(c, d + 1))
    L, B = ref.L[sl], ref.B[sl]
    dark = (L < 38) & (B > -12)
    per_col = {}
    for j in range(dark.shape[1]):
        rr = [r for r in runs(dark[:, j]) if r[1] - r[0] >= 2]
        if len(rr) == 3:
            per_col[j] = [(ref.y(a + (s + e) / 2.0), (e - s + 1) * ref.S) for s, e in rr]
    best, cur = [], []
    for j in range(dark.shape[1]):
        if j in per_col:
            cur.append(j)
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = []
    if len(best) < 8:
        raise SystemExit("choker: longest contiguous 3-wrap block is only %d columns"
                         % len(best))
    xs = np.array([ref.x(c + j) for j in best])
    bands = []
    for i in range(3):                                    # index 0 = topmost run
        ys = np.array([per_col[j][i][0] for j in best])
        th = np.array([per_col[j][i][1] for j in best])
        m, cc = np.polyfit(xs, ys, 1)
        bands.append({"slope": float(m), "tilt": math.atan(float(m)),
                      "thick": float(np.median(th)),
                      "y_at": float(m * dx + cc), "n": len(xs),
                      "rms": float(np.sqrt(np.mean((ys - (m * xs + cc)) ** 2)))})
    return {"bands": bands, "read_at_x": dx, "ncols": len(best),
            "x_span": (float(xs.min()), float(xs.max())),
            "band1_check": bands[0]["y_at"] - render_band1_y,
            "pitch": [bands[0]["y_at"] - bands[1]["y_at"],
                      bands[1]["y_at"] - bands[2]["y_at"]]}


# --------------------------------------------------------------------------------------
# edits
# --------------------------------------------------------------------------------------

def strip_gd(sdf: dict):
    sdf["primitives"] = [p for p in sdf["primitives"] if not str(p.get("id", "")).startswith(GD)]
    sdf["operations"] = [o for o in (sdf.get("operations") or [])
                         if not str(o.get("id", "")).startswith(GD)]


def half_space_box(px, py, theta, pz=0.0, size=1.2):
    """Box whose LOWER face passes through (px, py) at angle theta -- intersecting with
    it keeps everything above that line.  Same construction as canvas-panel's h40."""
    return {"id": GD + "cut", "type": "box", "size": [size, size, size],
            "transform": {"position": [px - (size / 2) * math.sin(theta),
                                       py + (size / 2) * math.cos(theta), pz],
                          "rotation": [0.0, 0.0, theta]}}


def apply_apron(spec, offsets, apron, comps, dx):
    changed = []
    theta = math.atan(apron["slope"])
    for cid in ("canvas-panel", "sash"):
        comp = comps[cid]
        sdf = comp["geometryDescriptor"]["sdf"]
        strip_gd(sdf)
        ox, oy = offsets[cid]
        # anchor the cut line at the component's own x centre so rounding is symmetric
        xa = (apron["x0"] + apron["x1"]) / 2.0
        ya = apron["slope"] * (xa + dx) + apron["intercept"]
        pz = float(np.mean([p.get("center", p.get("transform", {}).get("position", [0, 0, 0]))[2]
                            for p in sdf["primitives"][:1]]))
        sdf["primitives"].append(half_space_box(xa - ox, ya - oy, theta, pz))
        last = (sdf["operations"] or [])[-1]
        sdf["operations"].append({"id": GD + "isect", "type": "intersect",
                                  "left": last.get("id") or last.get("output"),
                                  "right": GD + "cut"})
        changed.append(cid)
    return changed


def apply_hems(spec, offsets, hems, comps, acc_by_id):
    report = {}
    for cid, leg in (("pants-hem-r", "r"), ("pants-hem-l", "l")):
        comp = comps[cid]
        sdf = comp["geometryDescriptor"]["sdf"]
        acc_sdf = acc_by_id[cid]["geometryDescriptor"]["sdf"]
        ox, oy = offsets[cid]
        ref_edge = hems["ref"][leg][:, 1]
        cutback = float(np.percentile(ref_edge, 95))
        tips = float(np.percentile(ref_edge, 5))
        spheres = [p for p in sdf["primitives"] if p["type"] == "sphere"]
        if not spheres:
            raise SystemExit("%s: no notch spheres" % cid)
        r = float(spheres[0].get("radius"))
        before = float(next(p for p in acc_sdf["primitives"]
                            if p["type"] == "sphere")["center"][1])
        newy = (cutback - oy) - r
        for p in spheres:
            p["center"] = [p["center"][0], round(newy, 5), p["center"][2]]
        report[cid] = {"n": len(spheres), "radius": r, "from": before, "to": round(newy, 5),
                       "cutback": cutback, "tips": tips}
        if cid == "pants-hem-l" and hems["pants_l_rim"] is not None:
            box = next((p for p in sdf["primitives"]
                        if p["type"] == "box" and p.get("size", [0, 0, 0])[0] > 0.2), None)
            acc_box = next((p for p in acc_sdf["primitives"]
                            if p["type"] == "box" and p.get("size", [0, 0, 0])[0] > 0.2), None)
            if box is not None:
                bmax = float(sdf["bounds"]["max"][1])
                low = float(acc_box["center"][1]) - float(acc_box["size"][1]) / 2.0
                want_top = min(bmax, hems["pants_l_rim"] - oy)
                box["size"] = [box["size"][0], round(want_top - low, 5), box["size"][2]]
                box["center"] = [box["center"][0], round((want_top + low) / 2.0, 5),
                                 box["center"][2]]
                report[cid]["box_top"] = {
                    "from": round(float(acc_box["center"][1])
                                  + float(acc_box["size"][1]) / 2.0 + oy, 4),
                    "to": round(want_top + oy, 4),
                    "rim": round(hems["pants_l_rim"], 4)}
    return report


def build_ring_sdf(xl, res=44):
    rings = xl["rings"]
    cx, cy = xl["cx"], xl["cy"]
    RO = xl["outer_r"]
    RI = xl["hole_r"]
    prims, ops, prev = [], [], None
    for i, key in enumerate(("TL", "TR", "BL", "BR")):
        r = rings[key]
        x, y = r["cx"] - cx, r["cy"] - cy
        o, h, dd = "e%d" % (i * 3 + 1), "e%d" % (i * 3 + 2), "d%d" % (i * 3 + 3)
        prims.append({"id": o, "type": "ellipsoid", "radii": [round(RO, 5), round(RO, 5), 0.005],
                      "center": [round(x, 5), round(y, 5), 0.0]})
        prims.append({"id": h, "type": "ellipsoid", "radii": [round(RI, 5), round(RI, 5), 0.02],
                      "center": [round(x, 5), round(y, 5), 0.0]})
        ops.append({"id": dd, "type": "subtract", "left": o, "right": h})
        if prev is None:
            prev = dd
        else:
            u = "u%d" % (i * 3 + 4)
            ops.append({"id": u, "type": "smooth-union", "left": prev, "right": dd,
                        "radius": 0.002})
            prev = u
    xs = [rings[k]["cx"] - cx for k in rings]
    ys = [rings[k]["cy"] - cy for k in rings]
    mx0, mx1 = min(xs) - RO, max(xs) + RO
    my0, my1 = min(ys) - RO, max(ys) + RO
    pad = (mx1 - mx0) * 0.06
    bx0, bx1 = mx0 - pad, mx1 + pad
    by0, by1 = my0 - pad, my1 + pad
    bz = (bx1 - bx0) / 2.0                      # keep the z voxel the size of the x voxel
    return {"primitives": prims, "operations": ops,
            "bounds": {"min": [round(bx0, 4), round(by0, 4), round(-bz, 4)],
                       "max": [round(bx1, 4), round(by1, 4), round(bz, 4)]},
            "resolution": res}


def build_strap_sdf(xl, res=32, thickness=0.007):
    rings, cx, cy = xl["rings"], xl["cx"], xl["cy"]
    prims = []
    for i, (k, pair) in enumerate((("A", ("TL", "BR")), ("B", ("BL", "TR")))):
        g = xl["straps"][k]
        p, q = rings[pair[0]], rings[pair[1]]
        mid = ((p["cx"] + q["cx"]) / 2.0 - cx, (p["cy"] + q["cy"]) / 2.0 - cy)
        prims.append({"id": "b%d" % (i + 1), "type": "box",
                      "size": [round(g["span"], 5), round(g["width"], 5), thickness],
                      "transform": {"position": [round(mid[0], 5), round(mid[1], 5), 0.0],
                                    "rotation": [0.0, 0.0, round(g["angle"], 5)]}})
    ops = [{"id": "u3", "type": "smooth-union", "left": "b1", "right": "b2", "radius": 0.002}]
    hx = hy = 0.0
    for p in prims:                       # true half-extents of each rotated box
        L, W = p["size"][0], p["size"][1]
        t = p["transform"]["rotation"][2]
        px_, py_ = p["transform"]["position"][:2]
        hx = max(hx, abs(px_) + (L * abs(math.cos(t)) + W * abs(math.sin(t))) / 2)
        hy = max(hy, abs(py_) + (L * abs(math.sin(t)) + W * abs(math.cos(t))) / 2)
    hx += 0.004
    hy += 0.004
    return {"primitives": prims, "operations": ops,
            "bounds": {"min": [round(-hx, 4), round(-hy, 4), round(-hx, 4)],
                       "max": [round(hx, 4), round(hy, 4), round(hx, 4)]},
            "resolution": res}


def apply_choker(spec, offsets, ch, comps, accepted_pos, accepted_sdf):
    comp = comps["choker"]
    sdf = comp["geometryDescriptor"]["sdf"]
    acc_sdf = accepted_sdf["choker"]
    ox, oy = offsets["choker"]
    discs = [p for p in sdf["primitives"] if p["type"] == "ellipsoid"
             and p["id"] != "e6"][:3]
    if len(discs) != 3:
        raise SystemExit("choker: expected 3 band ellipsoids, got %d" % len(discs))
    key = lambda p: -(p.get("center") or p["transform"]["position"])[1]
    discs.sort(key=key)
    acc_discs = sorted((p for p in acc_sdf["primitives"]
                        if p["type"] == "ellipsoid" and p["id"] != "e6"), key=key)[:3]
    # anchor on the ACCEPTED top band so the anchor cannot drift across runs
    top_world = float((acc_discs[0].get("center")
                       or acc_discs[0]["transform"]["position"])[1]) + oy
    worlds = [top_world, top_world - ch["pitch"][0], top_world - ch["pitch"][0] - ch["pitch"][1]]
    core = next(p for p in sdf["primitives"] if p["id"] == "e6")
    core["radii"] = [core["radii"][0], max(core["radii"][1], 0.08), core["radii"][2]]
    before = [(round(float((ap.get("center") or ap["transform"]["position"])[1]) + oy, 4), 0.0)
              for ap in acc_discs]
    after = [(round(w, 4), round(math.degrees(b["tilt"]), 2))
             for w, b in zip(worlds, ch["bands"])]

    # A wrap's VISIBLE thickness is not the disc's: the core subtraction leaves only the
    # disc's rim, where an ellipsoid has already tapered, so a disc of half-thickness ry
    # reads about half as thick as 2*ry/cos(tilt) would suggest.  Rather than model that,
    # build, voxelise exactly as polygonizeSdf will, measure the front-view run at the
    # component's own centreline, and rescale ry.  Two passes converge.
    def build(scales):
        for p, w, band, k in zip(discs, worlds, ch["bands"], scales):
            c = list(p.get("center") or p["transform"]["position"])
            rx = p["radii"][0]
            ry = max(0.0022, k * band["thick"] / 2.0 * math.cos(band["tilt"]))
            p.pop("center", None)
            p["radii"] = [rx, round(ry, 5), p["radii"][2]]
            p["transform"] = {"position": [c[0], round(w - oy, 5), c[2]],
                              "rotation": [0.0, 0.0, round(band["tilt"], 5)]}
        ylo2, yhi2 = 1e9, -1e9
        for p, w, band in zip(discs, worlds, ch["bands"]):
            half = (abs(p["radii"][0] * math.sin(band["tilt"]))
                    + p["radii"][1] * abs(math.cos(band["tilt"])))
            ylo2 = min(ylo2, w - oy - half)
            yhi2 = max(yhi2, w - oy + half)
        sdf["bounds"]["min"] = [sdf["bounds"]["min"][0], round(ylo2 - 0.003, 4),
                                sdf["bounds"]["min"][2]]
        sdf["bounds"]["max"] = [sdf["bounds"]["max"][0], round(yhi2 + 0.003, 4),
                                sdf["bounds"]["max"][2]]

    def measure_bands():
        s = sdf_stats(sdf, None)
        proj = s["occ"].any(axis=0)
        xi = int(round((-ox - s["mn"][0]) / s["step"][0]))       # component's own x = 0
        xi = min(max(xi, 0), s["res"] - 1)
        rr = runs(proj[:, xi][::-1])
        out = []
        for a2, b2 in rr:
            ytop = s["mn"][1] + (s["res"] - a2) * s["step"][1] + oy
            ybot = s["mn"][1] + (s["res"] - 1 - b2) * s["step"][1] + oy
            out.append(((ytop + ybot) / 2.0, ytop - ybot))
        return out

    scales = [1.0, 1.0, 1.0]
    thickness_trace, best, best_err = [], list(scales), 1e9
    for _ in range(6):
        build(scales)
        got = measure_bands()
        thickness_trace.append([round(float(t) * 1000, 1) for _c, t in got])
        if len(got) != 3:
            break
        err = max(abs(float(t) - b["thick"]) for (_c, t), b in zip(got, ch["bands"]))
        if err < best_err:
            best_err, best = err, list(scales)
        if err <= 0.0012:                       # inside one voxel; stop
            break
        # damped so the 1.6 mm voxel quantisation cannot make it oscillate
        scales = [min(4.0, max(0.5, k + 0.6 * (k * b["thick"] / max(float(t), 1e-4) - k)))
                  for k, (_c, t), b in zip(scales, got, ch["bands"])]
    build(best)
    thickness_trace.append([round(float(t) * 1000, 1) for _c, t in measure_bands()])

    # re-aim choker-straps onto the lowest wrap instead of leaving a fourth band.
    # `soy` is the local->world offset of the ACCEPTED build, so it pairs with the
    # accepted transform.position; solve for the new position absolutely rather than
    # nudging the current one, or a second run would move it twice.
    st = comps["choker-straps"]
    ssdf = st["geometryDescriptor"]["sdf"]
    sox, soy = offsets["choker-straps"]
    acc_y = float(accepted_pos["choker-straps"][1])
    bar = max((p for p in ssdf["primitives"] if p["type"] == "box"),
              key=lambda p: p["size"][0])
    bar_local = float(bar["transform"]["position"][1])
    bar_world_accepted = soy + bar_local
    dy = worlds[2] - bar_world_accepted
    st["transform"]["position"][1] = round(acc_y + dy, 5)
    tilt = ch["bands"][2]["tilt"]
    for p in ssdf["primitives"]:
        tr = p.setdefault("transform", {"position": list(p.pop("center", [0, 0, 0]))})
        tr.setdefault("position", [0, 0, 0])
        tr["rotation"] = [0.0, 0.0, round(tilt, 5)]
    bar["size"] = [bar["size"][0], round(max(0.005, ch["bands"][2]["thick"] * 0.75), 5),
                   bar["size"][2]]
    return {"before": before, "after": after, "straps_dy": round(dy, 4),
            "straps_tilt_deg": round(math.degrees(tilt), 2),
            "thickness_trace": thickness_trace,
            "disc_ry": [round(p["radii"][1] * 1000, 2) for p in discs],
            "measured": [(round(float(c), 4), round(float(t) * 1000, 1))
                         for c, t in measure_bands()],
            "bounds_y": (sdf["bounds"]["min"][1], sdf["bounds"]["max"][1])}


# --------------------------------------------------------------------------------------

def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "object-sculpt-spec.json")
    with open(path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    with open(os.path.join(ROOT, "baseline/spec_accepted.json"), "r", encoding="utf-8") as fh:
        accepted = json.load(fh)
    with open(os.path.join(ROOT, "baseline/meshes_accepted.json"), "r", encoding="utf-8") as fh:
        meshes = json.load(fh)
    with open(os.path.join(ROOT, "baseline/metrics_accepted.json"), "r", encoding="utf-8") as fh:
        metrics = json.load(fh)

    comps = {c["id"]: c for c in spec["componentTree"]}
    ymin = min(m["minY"] for m in meshes); ymax = max(m["maxY"] for m in meshes)
    xmin = min(m["x0"] for m in meshes);   xmax = max(m["x1"] for m in meshes)

    ref = ref_frame(ymin, ymax, xmin, xmax)
    ren = Frame(os.path.join(ROOT, "out/accepted/render_yaw0.png"), ymin, ymax, xmin, xmax)

    touched = ["x-lacing", "choker", "choker-straps", "canvas-panel", "sash",
               "pants-hem-r", "pants-hem-l"]
    offsets = world_offsets(accepted, meshes, touched)
    acc_by_id = {c["id"]: c for c in accepted["componentTree"]}
    for cid in touched:
        cur = list(comps[cid]["transform"]["position"])
        acc = list(acc_by_id[cid]["transform"]["position"])
        if cid == "choker-straps":
            cur[1] = acc[1]          # this patch owns that axis; see apply_choker
        if cur != acc:
            print("WARNING: %s transform.position differs from the accepted baseline; "
                  "the local->world offset used here may be stale." % cid)

    # "before" is always the ACCEPTED build, never the file on disk -- otherwise a second
    # run would report a zero delta and rewrite the budget with the wrong total.
    before_tris = {}
    for cid in touched:
        gd = acc_by_id[cid]["geometryDescriptor"]
        before_tris[cid] = sdf_stats(gd["sdf"],
                                     (gd.get("decimate") or {}).get("targetRatio"))["tris"]

    v0 = metrics["views"][0]
    print("=" * 86)
    print("patch_garment -- garment-detail")
    print("spec            : %s" % path)
    print("ref frame       : clay_2 %d rows -> %.4f mm/px  (body_2 read in the same coords)"
          % (ref.r1 - ref.r0 + 1, ref.S * 1000))
    print("render frame    : accepted %d rows -> %.4f mm/px"
          % (ren.r1 - ren.r0 + 1, ren.S * 1000))
    print("judge baseline  : shape %.5f edge %.5f chamfer %.5f width %.5f landmark %.5f colour %.5f"
          % tuple(v0["score"]["terms"][k] for k in
                  ("shape", "edge", "chamfer", "width", "landmark", "colour")))
    print("=" * 86)

    # ------------------------------------------------- ref->render x offset, measured
    # The reference's absolute centreline is the least reliable axis in this frame.
    # Measure it once from a feature both images resolve unambiguously: the X-lacing
    # assembly.  ref_x + dx is the reference point that corresponds to render x.
    xl = measure_xlacing(ref)
    by_name = {m["name"]: m for m in meshes}
    xl_render_cx = (by_name["Brass X lacing"]["x0"] + by_name["Brass X lacing"]["x1"]) / 2.0
    dx = xl["cx"] - xl_render_cx
    print("\n[0] REF->RENDER X OFFSET, measured off the X-lacing assembly")
    print("  ref four-ring centroid x %+.4f, render x-lacing mesh centre x %+.4f -> dx %+.1f mm"
          % (xl["cx"], xl_render_cx, dx * 1000))
    if abs(dx) > 0.025:
        print("  dx implausible (>25 mm); falling back to 0 and treating the frames as aligned")
        dx = 0.0

    # ---------------------------------------------------------------- 1. hems
    hems = measure_hems(ref, ren, meshes)
    print("\n[1] TROUSER HEMS  (+X is HER LEFT = screen-right)")
    for leg, name in (("r", "her RIGHT leg (screen-left, x<0)"),
                      ("l", "her LEFT leg (screen-right, x>0)")):
        rr = hems["ref"][leg][:, 1]
        rn = hems["render"][leg][:, 1]
        print("  %-34s ref hem %.4f..%.4f (p5 %.4f p95 %.4f, %.1f mm p-p)  render %.4f..%.4f (%.1f mm p-p)"
              % (name, rr.min(), rr.max(), np.percentile(rr, 5), np.percentile(rr, 95),
                 (rr.max() - rr.min()) * 1000, rn.min(), rn.max(), (rn.max() - rn.min()) * 1000))
    print("  ref asymmetry : her left hem is %+.1f mm relative to her right"
          % ((np.median(hems["ref"]["l"][:, 1]) - np.median(hems["ref"]["r"][:, 1])) * 1000))
    print("  render pants-l rim (highest point of the trouser cylinder's bottom edge): %.4f"
          % hems["pants_l_rim"])
    hem_rep = apply_hems(spec, offsets, hems, comps, acc_by_id)
    for cid, r in hem_rep.items():
        print("  %-13s %d notch spheres r %.5f : local y %+.5f -> %+.5f  "
              "(world cut-back %.4f -> %.4f, ref p95 %.4f)"
              % (cid, r["n"], r["radius"], r["from"], r["to"],
                 r["from"] + r["radius"] + offsets[cid][1],
                 r["to"] + r["radius"] + offsets[cid][1], r["cutback"]))
        if "box_top" in r:
            print("  %-13s ring top raised %.4f -> %.4f to meet the measured rim %.4f"
                  % (cid, r["box_top"]["from"], r["box_top"]["to"], r["box_top"]["rim"]))

    # ---------------------------------------------------------------- 2. apron
    apron = measure_apron(ref, meshes)
    ren_apron = measure_render_apron(ren, meshes)
    ya0 = apron["slope"] * (apron["x0"] + dx) + apron["intercept"]
    ya1 = apron["slope"] * (apron["x1"] + dx) + apron["intercept"]
    print("\n[2] CROTCH CANVAS APRON  (fixed, not removed)")
    print("  ref lower edge: %d columns over ref x %.3f..%.3f, y = %+.4f*x %+.4f  "
          "(%.2f deg, fit rms %.1f mm)"
          % (apron["n"], apron["fit_x0"], apron["fit_x1"], apron["slope"],
             apron["intercept"], math.degrees(math.atan(apron["slope"])),
             apron["rms"] * 1000))
    print("  same edge in render coords over the render apron's span x %.3f..%.3f : %.4f -> %.4f"
          % (apron["x0"], apron["x1"], ya0, ya1))
    print("  render olive box lower edge (median over columns): %.4f  -> raising it by %.1f mm"
          % (ren_apron, ((ya0 + ya1) / 2 - ren_apron) * 1000))
    print("  hips_sash colour region now: %d px, dE %.3f, hue_delta %+.2f deg"
          % (v0["colour"]["regions"]["hips_sash"]["pixels"],
             v0["colour"]["regions"]["hips_sash"]["dE"],
             v0["colour"]["regions"]["hips_sash"]["hue_delta"]))
    for cid in apply_apron(spec, offsets, apron, comps, dx):
        print("  %-13s + terminal intersect half-space (last operation)" % cid)

    # ---------------------------------------------------------------- 3. x-lacing
    print("\n[3] X-LACING  (split: rings stay `x-lacing`/brass, straps become `x-lacing-straps`/canvas)")
    print("  ref assembly  : %.1f x %.1f mm, %.0f%% cloth by area; ring outer r %.1f mm, "
          "wall %.1f mm, hole r %.1f mm"
          % (xl["footprint"][0] * 1000, xl["footprint"][1] * 1000, xl["cloth_frac"] * 100,
             xl["outer_r"] * 1000, xl["wall"] * 1000, xl["hole_r"] * 1000))
    print("  radial brass fraction about the ring centres (mm:frac): %s"
          % " ".join("%.0f:%.2f" % (r * 1000, f) for r, f in xl["radial"]))
    xspan = max(r["cx"] for r in xl["rings"].values()) - min(r["cx"] for r in xl["rings"].values())
    yspan = max(r["cy"] for r in xl["rings"].values()) - min(r["cy"] for r in xl["rings"].values())
    print("  consistency   : ring-centre span %.1f x %.1f mm + 2*outer_r = %.1f x %.1f mm "
          "against the measured footprint %.1f x %.1f mm"
          % (xspan * 1000, yspan * 1000, (xspan + 2 * xl["outer_r"]) * 1000,
             (yspan + 2 * xl["outer_r"]) * 1000,
             xl["footprint"][0] * 1000, xl["footprint"][1] * 1000))
    old = sdf_stats(acc_by_id["x-lacing"]["geometryDescriptor"]["sdf"], None)
    print("  render now    : %.1f x %.1f mm, one brass mesh, no resolved eyelets"
          % (old["ext"][0] * 1000, old["ext"][1] * 1000))
    for k in ("TL", "TR", "BL", "BR"):
        r = xl["rings"][k]
        print("    ring %s rel to assembly centroid (%+.4f, %+.4f)  bbox %.1f x %.1f mm"
              % (k, r["cx"] - xl["cx"], r["cy"] - xl["cy"], r["rx"] * 2000, r["ry"] * 2000))
    for k, pair in (("A", "TL->BR"), ("B", "BL->TR")):
        g = xl["straps"][k]
        print("    strap %s %s : angle %+.2f deg, ring centres %.1f mm apart, sage spans %.1f mm, width %.1f mm (mask %.1f)"
              % (k, pair, math.degrees(g["angle"]), g["len"] * 1000, g["span"] * 1000,
                 g["width"] * 1000, g["width_mask"] * 1000))
    xlc = comps["x-lacing"]
    xlc["geometryDescriptor"]["sdf"] = build_ring_sdf(xl)
    xlc["dimensions"] = dict(xlc["dimensions"])
    straps = next((c for c in spec["componentTree"] if c["id"] == "x-lacing-straps"), None)
    fresh = straps is None
    if fresh:
        straps = copy.deepcopy(acc_by_id["x-lacing"])
        spec["componentTree"].insert(
            [c["id"] for c in spec["componentTree"]].index("x-lacing") + 1, straps)
    straps["id"] = "x-lacing-straps"
    straps["name"] = "Cloth X straps"
    straps["material"] = "canvas"
    straps["materialRef"] = "canvas"
    straps["materialLayers"] = ["canvas"]
    straps["parent"] = "top"
    straps["primitive"] = "box"
    straps["topologyRationale"] = ("Two crossed straps that merge at the crossing: a box "
                                  "primitive cannot cross itself, and an attachment "
                                  "cylinder would be round in section and read as a rod.")
    straps["transform"] = copy.deepcopy(acc_by_id["x-lacing"]["transform"])
    straps["localFeatures"] = []
    straps["geometryDescriptor"] = copy.deepcopy(xlc["geometryDescriptor"])
    straps["geometryDescriptor"]["sdf"] = build_strap_sdf(xl)
    straps["geometryDescriptor"]["decimate"] = {
        "targetRatio": 0.4,
        "reason": "implicit surface; quadric collapse also smooths the axis-aligned voxel "
                  "staircase polygonizeSdf emits"}
    straps["colorMaterialRecipe"] = {
        "dominantAlbedo": "rgba(122, 115, 83, 1.0)",
        "secondaryAlbedo": "rgba(111, 107, 86, 1.0)",
        "materialClass": "fabric", "materialClassConfidence": 0.85,
        "evidenceRef": "analysis/patch_garment.py; sage cloth segmented off body_2.png"}

    for cid, sdfd, note in (
        ("x-lacing", xlc["geometryDescriptor"]["sdf"],
         "Four brass eyelet rings only. Outer radius %.1f mm, hole radius %.1f mm, centres "
         "relative to the assembly centroid measured off body_2.png. The cloth straps are a "
         "separate component because one mesh carries one material."
         % (xl["outer_r"] * 1000, xl["hole_r"] * 1000)),
        ("x-lacing-straps", straps["geometryDescriptor"]["sdf"],
         "Two crossed cloth straps, %.1f mm at %+.1f deg and %.1f mm at %+.1f deg, %.1f/%.1f mm "
         "wide, measured off body_2.png."
         % (xl["straps"]["A"]["span"] * 1000, math.degrees(xl["straps"]["A"]["angle"]),
            xl["straps"]["B"]["span"] * 1000, math.degrees(xl["straps"]["B"]["angle"]),
            xl["straps"]["A"]["width"] * 1000, xl["straps"]["B"]["width"] * 1000))):
        target = xlc if cid == "x-lacing" else straps
        s = sdf_stats(sdfd, target["geometryDescriptor"]["decimate"]["targetRatio"])
        target["dimensions"].update({"width": round(float(s["ext"][0]), 5),
                                     "height": round(float(s["ext"][1]), 5),
                                     "depth": round(float(s["ext"][2]), 5)})
        target["note"] = note
        target["notes"] = note
        print("  %-16s -> %.1f x %.1f x %.1f mm, res %d, voxel %.2f x %.2f x %.2f mm, %d tris"
              % (cid, s["ext"][0] * 1000, s["ext"][1] * 1000, s["ext"][2] * 1000,
                 sdfd["resolution"], s["step"][0] * 1000, s["step"][1] * 1000,
                 s["step"][2] * 1000, s["tris"]))
    ring_s = sdf_stats(xlc["geometryDescriptor"]["sdf"], None)
    proj = ring_s["occ"].any(axis=0)
    holes = []
    for k in ("TL", "TR", "BL", "BR"):
        r = xl["rings"][k]
        xi = int((r["cx"] - xl["cx"] - ring_s["mn"][0]) / ring_s["step"][0])
        yi = int((r["cy"] - xl["cy"] - ring_s["mn"][1]) / ring_s["step"][1])
        row = proj[yi]
        a2, b2 = xi, xi
        while a2 > 0 and not row[a2 - 1]:
            a2 -= 1
        while b2 < len(row) - 1 and not row[b2 + 1]:
            b2 += 1
        holes.append((b2 - a2 + 1) * ring_s["step"][0] * 1000)
    print("  eyelet holes in the z-projection: %s mm (ref %.1f mm) -- if any read 0 the "
          "rings collapsed to discs" % (np.round(holes, 1).tolist(), xl["hole_r"] * 2000))

    # ---------------------------------------------------------------- 4. choker
    chk = acc_by_id["choker"]["geometryDescriptor"]["sdf"]
    band1_world = max(float((p.get("center") or p["transform"]["position"])[1])
                      for p in chk["primitives"]
                      if p["type"] == "ellipsoid" and p["id"] != "e6") + offsets["choker"][1]
    band3_world = min(float((p.get("center") or p["transform"]["position"])[1])
                      for p in chk["primitives"]
                      if p["type"] == "ellipsoid" and p["id"] != "e6") + offsets["choker"][1]
    ch = measure_choker(ref, dx, band1_world)
    print("\n[4] CHOKER  (band 1 held fixed; only the pitch below it and the tilts change)")
    print("  ref: %d contiguous columns resolve all three wraps, ref x %+.4f..%+.4f; "
          "lines read at ref x %+.4f (= render x 0)"
          % (ch["ncols"], ch["x_span"][0], ch["x_span"][1], ch["read_at_x"]))
    for i, band in enumerate(ch["bands"]):
        print("    wrap %d  y %.4f, tilt %+.2f deg, %.1f mm thick (fit rms %.1f mm)"
              % (i + 1, band["y_at"], math.degrees(band["tilt"]), band["thick"] * 1000,
                 band["rms"] * 1000))
    print("  cross-check: ref wrap 1 lands %+.1f mm from the render's top band (%.4f); "
          "the render's own stack is %.1f mm against the reference's %.1f mm"
          % (ch["band1_check"] * 1000, band1_world,
             (band1_world - band3_world) * 1000, sum(ch["pitch"]) * 1000))
    print("  ref pitch 1->2 %.1f mm, 2->3 %.1f mm"
          % (ch["pitch"][0] * 1000, ch["pitch"][1] * 1000))
    crep = apply_choker(spec, offsets, ch, comps,
                        {cid: acc_by_id[cid]["transform"]["position"] for cid in touched},
                        {cid: acc_by_id[cid]["geometryDescriptor"]["sdf"] for cid in touched})
    for (yb, tb), (ya, ta) in zip(crep["before"], crep["after"]):
        print("    band world y %.4f (tilt %+.1f) -> %.4f (tilt %+.1f)" % (yb, tb, ya, ta))
    print("    disc half-thickness calibration (visible band mm per pass): %s -> targets %s"
          % (crep["thickness_trace"],
             [round(b["thick"] * 1000, 1) for b in ch["bands"]]))
    print("    built wraps at the component centreline (world y, visible mm): %s"
          % crep["measured"])
    print("    choker bounds y -> %.4f .. %.4f ; choker-straps moved %+.1f mm and tilted %+.2f deg"
          % (crep["bounds_y"][0], crep["bounds_y"][1], crep["straps_dy"] * 1000,
             crep["straps_tilt_deg"]))

    # --------------------------------------------- notes, dimensions, silhouette check
    notes = {
        "pants-hem-r": ("Tattered hem, her RIGHT leg (screen-left, -X). Eight notch spheres "
                        "cut the ring's BOTTOM edge back to world %.4f; the tips stay at the "
                        "ring's own rim. Reference edge %.4f..%.4f. The top is left un-notched "
                        "so the ring overlaps pants-r's flat rim at 0.520 at every azimuth."
                        % (hem_rep["pants-hem-r"]["cutback"],
                           hems["ref"]["r"][:, 1].min(), hems["ref"]["r"][:, 1].max())),
        "pants-hem-l": ("Tattered hem, her LEFT leg (screen-right, +X), which the reference "
                        "carries ~%.0f mm HIGHER than her right. Notches cut the bottom back "
                        "to world %.4f (reference edge %.4f..%.4f); the ring top is extended "
                        "to %.4f to meet the pants-l rim."
                        % ((np.median(hems["ref"]["l"][:, 1])
                            - np.median(hems["ref"]["r"][:, 1])) * 1000,
                           hem_rep["pants-hem-l"]["cutback"],
                           hems["ref"]["l"][:, 1].min(), hems["ref"]["l"][:, 1].max(),
                           hems["pants_l_rim"])),
        "canvas-panel": ("Canvas apron. Lower edge cut to the reference's own line, y = "
                         "%+.4f*x %+.4f in render coordinates (%.1f deg, falling toward her "
                         "left); below it the reference is 88-100%% purple trouser."
                         % (apron["slope"], apron["intercept"] + apron["slope"] * dx,
                            math.degrees(math.atan(apron["slope"])))),
        "choker": ("Three wraps at world y %s, tilts %s deg, visible thickness %s mm, "
                   "measured off body_2.png. The top wrap is unchanged; the two below it "
                   "carry the reference's 15.3 / 21.4 mm pitch instead of 12.0 / 12.7."
                   % ([a for a, _t in crep["after"]],
                      [t for _a, t in crep["after"]],
                      [t for _c, t in crep["measured"]])),
        "choker-straps": ("The proud front section of the lowest wrap, at world y %.4f and "
                          "tilt %+.2f deg to match it. The reference has no fourth band."
                          % (crep["after"][2][0], crep["straps_tilt_deg"])),
    }
    notes["sash"] = notes["canvas-panel"].replace("Canvas apron", "Hip sash")
    for cid, text in notes.items():
        comps[cid]["note"] = text
    for cid in touched:
        comp = comps[cid]
        s = sdf_stats(comp["geometryDescriptor"]["sdf"], None)
        if cid not in ("x-lacing",):
            comp["dimensions"].update({"width": round(float(s["ext"][0]), 5),
                                       "height": round(float(s["ext"][1]), 5),
                                       "depth": round(float(s["ext"][2]), 5)})

    print("\n[5] SILHOUETTE SAFETY -- world AABB of every touched component")
    print("  %-16s %-30s %-30s" % ("component", "before (x0..x1 / y0..y1)", "after"))
    for cid in touched:
        ox, oy = offsets[cid]
        a = sdf_stats(acc_by_id[cid]["geometryDescriptor"]["sdf"], None)
        b = sdf_stats(comps[cid]["geometryDescriptor"]["sdf"], None)
        shift = 0.0
        if cid == "choker-straps":
            shift = (float(comps[cid]["transform"]["position"][1])
                     - float(acc_by_id[cid]["transform"]["position"][1]))
        print("  %-16s %+.4f..%+.4f / %.4f..%.4f   %+.4f..%+.4f / %.4f..%.4f  %s"
              % (cid, a["lo"][0] + ox, a["hi"][0] + ox, a["lo"][1] + oy, a["hi"][1] + oy,
                 b["lo"][0] + ox, b["hi"][0] + ox, b["lo"][1] + oy + shift,
                 b["hi"][1] + oy + shift,
                 "x unchanged" if abs(a["lo"][0] - b["lo"][0]) < 1e-9
                 and abs(a["hi"][0] - b["hi"][0]) < 1e-9
                 else "x widened on purpose; clears the `top` silhouette edge by %.0f mm"
                      % (min(b["lo"][0] + ox - by_name["Halter crop top"]["x0"],
                             by_name["Halter crop top"]["x1"] - (b["hi"][0] + ox)) * 1000)))

    # ---------------------------------------------------------------- triangles
    print("\n[6] TRIANGLE COST")
    total_before = sum(m["tris"] for m in meshes)
    delta = 0
    for cid in touched + ["x-lacing-straps"]:
        comp = next(c for c in spec["componentTree"] if c["id"] == cid)
        ratio = (comp["geometryDescriptor"].get("decimate") or {}).get("targetRatio")
        s = sdf_stats(comp["geometryDescriptor"]["sdf"], ratio)
        b = before_tris.get(cid, 0)
        delta += s["tris"] - b
        print("  %-16s %6d -> %6d  (%+d)" % (cid, b, s["tris"], s["tris"] - b))
    print("  build total     %6d -> %6d  (%+d of a 250000 budget; 46006 headroom before)"
          % (total_before, total_before + delta, delta))
    print("  performanceBudget.measuredTriangles is left alone on purpose: it is a MEASURED "
          "field, five other patches land in the same file, and last-writer-wins there "
          "would silently discard their deltas.")

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
        fh.write("\n")
    print("\nwrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
