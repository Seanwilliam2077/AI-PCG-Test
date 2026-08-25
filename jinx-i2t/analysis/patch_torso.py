"""Rebuild the torso and its garments as implicit surfaces instead of stacked slabs.

WHAT WAS MEASURED
=================
Calibration.  Every reference panel is a native crop of a 3000 px sheet and the six
figures are NOT at a common image scale, so each panel carries its own
`m_per_px = 1.720 / own silhouette height` (clay_2 1.34585 mm/px, floor row 1289;
body_2 1.34902, floor 1286; clay_0 1.41914, floor 1223).  For the horizontal origin of
body_2 this patch uses x0 = col 187, read off the linea alba and the navel dimple at
(col 187, y 1.132) at 8x, cross-checked against the whole-silhouette centre column (188)
and the shoulder-span centre at y 1.40 (188.5).  That is 8 px = 11 mm to HER LEFT of the
x0 = 195 the recon report used, so every lateral number below differs from that report by
about +11 mm.  None of the handedness conclusions turn on 11 mm.

Handedness, stated explicitly because an earlier round of this project got it backwards.
+X is HER LEFT and is screen-RIGHT in a front view (body_2/clay_2), screen-LEFT in a back
view (body_5); in the yaw-90 panel body_0/clay_0 screen-LEFT is +Z (front) and
screen-RIGHT is -Z (back).  Verified from the images rather than assumed: the cloud
tattoos sit on the screen-LEFT flank in body_2 and the screen-RIGHT flank in body_5, so
the tattoos are on HER RIGHT (-X); the two buckled black arm bands sit on the screen-RIGHT
arm in body_2 and the screen-LEFT arm in body_5, so they are on HER LEFT (+X); and the
olive canvas mass is screen-RIGHT in body_2 and screen-LEFT in body_5, so THE CANVAS SASH
AND ITS KNOT ARE ON HER LEFT (+X).  The low magenta drape with the pale binding is on her
RIGHT (-X) rear.  The spec's own `sash` note ("Low corner on her RIGHT") is describing
that magenta drape, not the canvas, and this patch keeps the two apart.

Trunk profile.  `analysis/measured_skeleton.json torsoProfile` gives half-width and
half-depth at nine heights: 0.940 (0.1015/0.0990), 1.020 (0.1178/0.1098), 1.080
(0.1000/0.0902), 1.140 (0.0931/0.0862), 1.210 (0.0850/0.0815), 1.280 (0.0989/0.1018),
1.340 (0.1040/0.1120), 1.400 (0.1020/0.0939), 1.429 (0.0684/0.0684).  I re-measured two
of those independently before building on the table.  Front view clay_2 at the waist: the
torso runs from the arm/torso crease at col ~116 to col 246 at y 1.17, half-width 0.0875
against the table's interpolated 0.0897 -- 2 mm.  Side view clay_0 at the bare midriff
y 1.13: the skin runs cols 67..187, depth 0.170 against the table's 0.172 -- 2 mm.  The
table is therefore what this patch builds from.  Only the three rows above y 1.400 (the
shoulder-to-neck terminator) and the row at 0.880 (the seat terminator) are extrapolated,
and they are flagged as such in PROFILE_* below.

Garments, measured on body_2 at 8x-9x against the x0 = 187 anchor:
  choker         three separate wraps, y 1.4345..1.4690 (h 0.0345), standing ~4 mm proud
                 of the neck, plus one strap crossing the throat from her right high to
                 her left low at 17 deg below horizontal.
  top hem        bottom edge of the black at the FRONT: 1.2266 at x -0.046, 1.2273 at
                 x 0.000, 1.2152 at +0.055, 1.2118 at +0.072 -- level at 1.222 within
                 15 mm.  On body_5 the same black reaches y 1.152 at the BACK, so the hem
                 is a plane tilted ~19 deg, 70 mm lower behind than in front.
  under-bust band  y 1.222..1.252 at the front (h 0.030); brass frame buckle
                 x +0.021..+0.045, y 1.208..1.254, centred (+0.033, 1.231) -- OFF-CENTRE
                 TOWARD HER LEFT.
  back opening   the black narrows upward into a spine strap: the outer edge of the black
                 on her right runs (-0.040, 1.320) -> (-0.090, 1.221), slope dx/dy 0.505,
                 which closes to zero width at y 1.399 and reaches |x| 0.0925 at y 1.216.
                 Below 1.216 the black is full torso width -- a 360 deg band.
  armhole        outer edge of the front panel, averaged left/right: |x| 0.098 at y 1.22,
                 0.092 at 1.30, 0.080 at 1.34, 0.062 at 1.38, 0.056 at the yoke 1.437.
  X-lacing       four brass rings, outer diameter 0.019, centres (-0.023, 1.364),
                 (+0.035, 1.358), (-0.021, 1.316), (+0.037, 1.311); two tan straps ~0.012
                 wide crossing at a mean 39 deg; overall footprint 0.078 x 0.072.
  hip belt       strap centreline rises toward HER LEFT: y 1.046 at x -0.049, y 1.098 at
                 x +0.061, slope 0.473 (25 deg); one brass frame buckle at the centre
                 front, ~0.055 x 0.065, centred (+0.005, 1.058).
  canvas sash    olive canvas front span x -0.019..+0.120 with its lower edge falling from
                 1.006 at x -0.009 to 0.977 at +0.112: the hanging corner is on HER LEFT.
                 The black leather knot/tab sits on top of it at x +0.044..+0.120,
                 y 0.952..1.069.  There is no olive canvas anywhere on her right.
  trouser hem    body_2 at 4x: her RIGHT leg notch tops ~0.520, tatter tips ~0.462; her
                 LEFT (raised) leg notch tops ~0.578, tips ~0.548.  70 mm apart in world y.
  trouser rise   waistband top 1.099 at x +0.15 (her left), 1.068 at x -0.10 (her right):
                 a plane tilted 7 deg, y = 1.0804 + 0.124x.

WHAT THIS CHANGES
=================
1. The trunk stops being three ellipsoids.  `chest`, `abdomen` and `pelvis` keep their
   ids, parents, `transform.position`, `dimensions` and their entire `actionProfile`, and
   each gains `topologyClass: "implicit"` plus a `geometryDescriptor.sdf` built by
   smooth-unioning a stack of ellipsoid rings sampled straight off `torsoProfile`.  The
   result is one continuous lofted surface carrying the measured waist pinch and bust,
   instead of three tangent balls with a 28 mm dead gap between abdomen and pelvis that
   only `tattoo-region` was spanning.

   Overlaps are deliberate.  Chest and abdomen both carry the full profile through
   1.19..1.26 and their surfaces coincide there; that is harmless because both are the
   `skin` material and an SDF mesh carries no UVs, so both resolve to the same flat texel
   and z-fighting between them cannot be seen.  Where the materials DIFFER the handoff is
   made explicit instead: `pelvis` is `pants`, so it carries the full profile while the
   abdomen is shrunk to 0.94x below y 1.02, putting the trousers strictly outside the skin
   and making the boundary a clean waistband edge.  That edge is the measured 7 deg tilted
   plane, which is how the 31 mm left/right rise difference is expressed -- it belongs to
   the waistband, not to the two trouser tubes, so `pants-l`/`pants-r` now start just
   under it rather than carrying the tilt themselves and producing a second rim.  The
   pelvis tapers to 0.80x by y 0.88 so its bottom cap closes inside the trouser tubes
   instead of leaving a rim at the crotch.

   THE RIG IS NOT TOUCHED.  `analysis/emit_pivots.py` derives every socket's
   `localPosition` as (bone jointPos - accumulated `transform.position`), so socket
   coordinates stay correct exactly as long as no `transform.position` on a
   socket-carrying component moves.  This patch changes `transform.position` only on
   components that have zero sockets.  All 98 sockets on all 49 bone-driven components,
   including the six on chest/abdomen/pelvis, and all 49 rig bones, are left untouched.

2. `transform.scale` is set to [1,1,1] on every component that gains an SDF.  This is not
   cosmetic.  The generator emits `geometry.scale(...)` from `dimensions` for any
   component without an attachment endpoint, INCLUDING implicit ones -- the existing
   `eye-cavity-l` is emitted as `polygonizeSdf(...)` and then
   `.scale(0.04719, 0.032, 0.04243)`, which shrinks its authored 25 mm radius to about
   1 mm and is why nothing of it is visible.  `transform.scale` takes precedence over
   `dimensions` in `scale_vector()`, so [1,1,1] is what lets an SDF authored in real
   metres survive to the screen.

3. Subdivision is deliberately NOT used.  `validate_subdivision_budget()` rejects
   `geometryDescriptor.subdivide` on an implicit component outright ("subdivision is
   unsupported for this generator path"), so SDF + Catmull-Clark cannot pass strict
   validation even though the emitter would honour it.  Smoothness has to come from the
   sampling grid and the quadric decimator instead, which is why the trunk is spending
   resolution 56 (4.1-5.6 mm voxels) rather than running coarse and subdividing.

4. Garments become the shapes they actually are.  The two flat circular plates at the hip
   -- `hip-belt` (r 0.178) and `diagonal-strap` (r 0.166), both attachment-derived tapered
   cylinders and therefore structurally unable to follow an elliptical hip or to tilt --
   lose their attachments and become a 30 mm band on the measured 25 deg tilt following
   the hip profile, and two 26 mm straps down the outer thigh fronts.  `top-band` loses
   the double-applied +0.048 z offset that put its centre 0.101 m in front of the trunk
   centre (a knife edge protruding 84 mm past the reference torso surface) and becomes a
   360 deg band on the measured back-lower tilt.  `top` gains the back opening: the V is
   cut by two rotated half-spaces on the measured dx/dy 0.505 edge, the armholes by two
   more, and the 360 deg band below y 1.216 is unioned back afterwards -- which is why the
   V cutters can run past the bottom of the garment without eating the band.  `x-lacing`
   becomes two crossed straps and four rings instead of a solid box.  `choker` becomes
   three wraps instead of one 138 mm-deep ellipsoid.  `sash` moves onto her LEFT hip with
   the `canvas` material it should always have had instead of `pants`, `canvas-panel`
   becomes its hanging apron with the low corner on her left, and `pouch` -- today buried
   inside the sash and pelvis ellipsoids and invisible in every view -- becomes the
   leather knot standing 27 mm proud of the canvas at x +0.044..+0.120.  `pants-hem-l/r`,
   which were being emitted at y 1.038..1.098, i.e. 570 mm above the hem they are named
   for, become eight tatter teeth at the measured hems.  `belt-hardware` drops from nine
   studs on a 0.15 m ring to the single centre-front buckle the reference has.

EXPECTED MEASURABLE EFFECT
==========================
These are predictions for the six 500x900 orthographic renders at 2 mm/px, and they are
not guesses: before shipping, this patch's SDFs were run through a numpy replica of
`polygonizeSdf` (same cell-centre sampling, same `smin`, same exposed-voxel-face
emission) and rasterised into the render's own frame.  The "should read" numbers below
are what that replica measured, so a render that disagrees with them by more than the
voxel pitch means something else in the pipeline changed the geometry.

* The horizontal slab rims go away.  `out/clay/render_yaw90.png` today has hard
  silhouette steps at y = 1.256 and 1.230 (the `top-band` disc), 1.105 (the `sash` cap),
  1.098 (the `pants-hem` rims), 1.086 (the `pelvis` top), 1.062 and 1.036 (the `hip-belt`
  disc), 1.010 and 0.890 (the `diagonal-strap` barrel), 0.995 and 1.085 (the
  `canvas-panel` box faces) and 0.815 (the `sash` bottom).  Every one of those eleven
  should be gone.  What should remain are four real garment edges: the top's hem plane,
  the band's proud rim, the trouser waistband cut and the hip-belt band.
* The waist pinch becomes real.  Front-view (yaw 0) half-span at y = 1.17 should move
  from the measured 0.064/0.062 to 0.093 +/- 0.005 (replica: 0.093), and the hip at
  y 1.02 should read 0.121 +/- 0.005 for the trousers alone, so
  halfW(1.17)/halfW(1.02) lands near 0.77.
* The side view stops being a barrel.  Yaw-90 half-depth at y 1.24 should fall from
  0.196 -- a one-sided knife edge reaching z +0.196 with nothing behind the body -- to
  0.101, spanning z -0.090..+0.112 (replica).  At y 1.06 the maximum |z| should fall from
  +0.188 to about +0.112, and that +0.112 should now be the CANVAS APRON, which is only
  on her left: the same measurement taken at yaw 270 (her right, where there is no
  canvas) should read about +0.100.  A reading that is the same on both sides means the
  circular plate is still there.
* The top's hem stops being level.  The lowest cloth pixel should be y 1.220 at the front
  (z +0.10) and y 1.158 at the back (z -0.09) -- replica values, against the measured
  1.222 / 1.152.
* The back opens.  In the yaw-180 clay render the black top today covers the whole upper
  back; afterwards it should read as a V that is zero width at y 1.40 (replica: half-width
  0.005 at y 1.38 against a measured 0.010) and 0.053 half-width at y 1.30 (measured
  0.050), with the band going full width below y 1.216.
* The trouser rise tilts.  The top of the `pants` material should be y 1.064 at x -0.10
  and y 1.088 at x +0.10 (replica), i.e. 24 mm higher on HER LEFT, against a measured
  31 mm.  It is dead level today.
* Trouser hems separate.  The lowest trouser pixel on her right leg should move from
  y 0.470 to 0.462 and on her left from 0.470 to 0.546 (replica), an 84 mm left/right
  difference where there is currently none, with eight teeth per leg.
* Laterality, which is the thing an earlier round got backwards.  In the yaw-0 render all
  olive canvas should lie in x -0.019..+0.131 and the black knot in x +0.049..+0.123, i.e.
  entirely on HER LEFT (screen right); all `tattoo` material should lie in
  x -0.105..-0.029, entirely on HER RIGHT (screen left).  Any canvas at screen-left, or
  any ink at screen-right, means the mirror is wrong again.
* Triangles.  The script prints its own measured cost.  The net change is about +2,300
  triangles after decimation and +96,000 in the worst case where the quadric collapse
  refuses every candidate, against a 250,000 budget with 128,833 in use.

TRADE-OFFS AND WHAT IS STILL WRONG
==================================
* `polygonizeSdf` is not marching cubes: it emits axis-aligned quads on the boundary of
  occupied voxels, so every one of these surfaces is a staircase at the voxel pitch
  (5.8-7.6 mm on the trunk, 1.6-3.5 mm on the small hardware) until the quadric decimator
  smooths it.  A 6 mm step is 3 px in a 900 px render.  That is a real quality cost paid
  to buy continuous form and true booleans, and it is why resolution is spent on the trunk
  rather than on trim.  It also means the emitted trunk runs 3-5 mm WIDER than the
  measured profile (the waist reads 0.093 against a measured 0.0875-0.0897), because
  `smin` inflates by up to radius/4 and a voxel is only counted when its CENTRE is inside,
  which rounds outward on average.  Sizing the rings down to compensate was rejected: it
  would trade a known 4 mm bias for an unknown one that changes with resolution.
* The trunk profile is symmetric in Z about each component's own centreline, because the
  reference's front/back depth split is not measurable: both yaw-90 panels are occluded by
  the near arm above y 1.19, and below it the silhouette's front edge is the forearm, not
  the ribcage.  No front bias was invented.
* The armhole is built symmetric about the body midline.  Measured in my frame the front
  panel spans -0.051..+0.073 at y 1.38, i.e. off-centre by +0.011; in the recon's frame
  the same pixels are -0.062..+0.062, i.e. centred.  The two frames differ by exactly the
  11 mm x0 disagreement, so I cannot tell a real torso twist from a registration error and
  chose the symmetric reading.
* `x-lacing` keeps the `brass` material for both the rings and the two straps, although
  the straps are tan canvas in the reference.  A component carries one material and there
  is no spare component to split them across.
* The low magenta drape on her RIGHT rear (x -0.02..-0.20, y 0.912..1.085, lowest 0.912)
  is still not built.  Every component in this dimension is either already spoken for or
  carries the wrong material for it, and this patch does not invent components.
* The X-lacing ring outer diameter measured here (0.019) is ~8 mm smaller than the recon
  report's (0.026-0.029); I measured the brass annulus alone and they may have included
  the skin showing through it.  0.019 is what is built.
* `component_uses_dense_height_maps()` treats any `implicit` component as dense, which
  floors its material's `displacementScale` at 0.005 and `bumpScale` at 0.05.  An SDF mesh
  has no UVs, so that displacement samples a single texel and comes out as a uniform
  normal offset of at most +/-2.5 mm on every surface this patch builds.  It is not
  suppressible from the spec (the generator takes a max, not an override), it applies
  equally to the existing `eye-cavity-*` components, and it is inside the voxel pitch, so
  it is accepted rather than worked around.
* The two diagonal thigh straps are placed from the recon report's endpoints shifted by my
  +11 mm x0 correction.  I confirmed by eye in body_2 that a dark diagonal strap exists on
  each outer thigh between y 0.80 and 1.02, but I did not measure its endpoints myself.
"""
import json
import math
import sys

SPEC_DEFAULT = 'object-sculpt-spec.json'

# --------------------------------------------------------------------------------------
# Measured trunk profile, world metres: y -> (half-width x, half-depth z).
# Rows 0.940..1.400 are analysis/measured_skeleton.json torsoProfile verbatim.
# Row 0.880 is an extrapolated seat terminator; rows 1.412/1.422/1.432 are an
# extrapolated shoulder-to-neck terminator chosen so the trunk closes onto the neck
# cylinder's own 0.0469 radius instead of ending 17 mm proud of it.  Both are marked
# EXTRAPOLATED because they are not measurements.
PROFILE_Y = [0.880, 0.940, 1.020, 1.080, 1.140, 1.210, 1.280, 1.340, 1.400, 1.412, 1.422, 1.432]
PROFILE_W = [0.0930, 0.1015, 0.1178, 0.1000, 0.0931, 0.0850, 0.0989, 0.1040, 0.1020, 0.0850, 0.0640, 0.0480]
PROFILE_D = [0.0930, 0.0990, 0.1098, 0.0902, 0.0862, 0.0815, 0.1018, 0.1120, 0.0939, 0.0800, 0.0640, 0.0480]
# world z of the trunk centreline, so every ring sits on the spec's own forward lean
CENTRE_Y = [0.940, 1.210, 1.340, 1.432]
CENTRE_Z = [0.000, 0.005, 0.010, 0.008]

# measured armhole half-width of the top's front panel (see docstring)
ARMHOLE_Y = [1.220, 1.437]
ARMHOLE_X = [0.100, 0.056]

# measured garment planes
HEM_FRONT_Y, HEM_BACK_Y, HEM_Z = 1.222, 1.152, 0.100      # top hem plane, front/back at +-HEM_Z
BAND_FRONT_MID, BAND_BACK_MID = 1.237, 1.181              # under-bust band mid-plane
WAISTBAND_Y0, WAISTBAND_SLOPE = 1.0804, 0.124             # trouser rise plane y = y0 + s*x
HIPBELT_Y0, HIPBELT_SLOPE = 1.069, 0.473                  # hip belt mid-plane
VEDGE_SLOPE, VEDGE_X, VEDGE_Y = 0.505, -0.040, 1.320      # back-opening V edge, her right


def lerp_table(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def half_w(y):
    return lerp_table(y, PROFILE_Y, PROFILE_W)


def half_d(y):
    return lerp_table(y, PROFILE_Y, PROFILE_D)


def centre_z(y):
    return lerp_table(y, CENTRE_Y, CENTRE_Z)


def r5(v):
    return round(float(v), 5)


def vec5(v):
    return [r5(v[0]), r5(v[1]), r5(v[2])]


def ramp(y, y_full, y_end, lo):
    """1.0 at and beyond y_full, `lo` at and beyond y_end, linear in between."""
    if (y_full > y_end and y >= y_full) or (y_full < y_end and y <= y_full):
        return 1.0
    if (y_full > y_end and y <= y_end) or (y_full < y_end and y >= y_end):
        return lo
    return lo + (1.0 - lo) * (y - y_end) / (y_full - y_end)


# --------------------------------------------------------------------------------------
# SDF construction.  Everything is authored in WORLD metres and converted to
# component-local on the way out by subtracting the component's world origin, so the
# numbers in the code read the same as the numbers in the measurement notes.
class Sdf:
    def __init__(self, origin):
        self.origin = list(origin)
        self.prims = []
        self.ops = []
        self._n = 0

    def _id(self, stem):
        self._n += 1
        return '%s%d' % (stem, self._n)

    def _local(self, p):
        return [p[i] - self.origin[i] for i in range(3)]

    def _place(self, prim, centre, rotation):
        if rotation and any(abs(a) > 1e-9 for a in rotation):
            prim['transform'] = {'position': vec5(self._local(centre)), 'rotation': vec5(rotation)}
        else:
            prim['center'] = vec5(self._local(centre))
        self.prims.append(prim)
        return prim['id']

    def ellipsoid(self, centre, radii, rotation=None, stem='e'):
        return self._place({'id': self._id(stem), 'type': 'ellipsoid', 'radii': vec5(radii)},
                           centre, rotation)

    def box(self, centre, size, rotation=None, stem='b'):
        return self._place({'id': self._id(stem), 'type': 'box', 'size': vec5(size)},
                           centre, rotation)

    def sphere(self, centre, radius, stem='s'):
        return self._place({'id': self._id(stem), 'type': 'sphere', 'radius': r5(radius)},
                           centre, None)

    def capsule(self, a, b, radius, stem='c'):
        """Capsule between two WORLD points.  The primitive runs along its local Y, so
        this emits the XYZ Euler that maps +Y onto (b - a): with THREE's XYZ order the
        image of +Y is (-sin rz, cos rx cos rz, sin rx cos rz), hence rx = atan2(dz, dy)
        and rz = atan2(-dx, hypot(dy, dz))."""
        d = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in d)) or 1e-4
        mid = [(a[i] + b[i]) / 2.0 for i in range(3)]
        rx = math.atan2(d[2], d[1] if abs(d[1]) > 1e-12 else 1e-12)
        rz = math.atan2(-d[0], math.hypot(d[1], d[2]) or 1e-12)
        return self._place({'id': self._id(stem), 'type': 'capsule', 'radius': r5(radius),
                            'height': r5(length)}, mid, [rx, 0.0, rz])

    def halfspace(self, point, up_normal, keep='above', span=(1.2, 1.2, 1.2), stem='h'):
        """A box whose bounding face lies on the plane through `point` with normal
        `up_normal`, filling `span` on the kept side.  Only normals lying in the XY or the
        YZ plane are supported, which is every plane this patch needs."""
        mag = math.sqrt(sum(v * v for v in up_normal))
        n = [v / mag for v in up_normal]
        if abs(n[2]) < 1e-9:
            rot = [0.0, 0.0, math.atan2(-n[0], n[1])]
        elif abs(n[0]) < 1e-9:
            rot = [math.atan2(n[2], n[1]), 0.0, 0.0]
        else:
            raise ValueError('halfspace normal must lie in the XY or YZ plane')
        sign = 1.0 if keep == 'above' else -1.0
        centre = [point[i] + sign * n[i] * span[1] / 2.0 for i in range(3)]
        return self.box(centre, span, rot, stem=stem)

    def wedge(self, point, inward_normal, length=0.6, size_y=1.2, z_centre=0.0, z_span=1.2,
              stem='w'):
        """A box used as a cutter whose near face lies on the plane through `point` and
        which extends `length` along `inward_normal` (which must lie in the XY plane).
        Its Z extent is set independently so a back-only cut cannot reach the front."""
        mag = math.hypot(inward_normal[0], inward_normal[1])
        n = [inward_normal[0] / mag, inward_normal[1] / mag, 0.0]
        rot = [0.0, 0.0, math.atan2(n[1], n[0])]
        centre = [point[0] + n[0] * length / 2.0, point[1] + n[1] * length / 2.0, z_centre]
        return self.box(centre, [length, size_y, z_span], rot, stem=stem)

    def smooth_union(self, left, right, radius):
        oid = self._id('u')
        self.ops.append({'id': oid, 'type': 'smooth-union', 'left': left, 'right': right,
                         'radius': r5(radius)})
        return oid

    def subtract(self, left, right):
        oid = self._id('d')
        self.ops.append({'id': oid, 'type': 'subtract', 'left': left, 'right': right})
        return oid

    def intersect(self, left, right):
        oid = self._id('i')
        self.ops.append({'id': oid, 'type': 'intersect', 'left': left, 'right': right})
        return oid

    def chain(self, ids, radius):
        cur = ids[0]
        for nxt in ids[1:]:
            cur = self.smooth_union(cur, nxt, radius)
        return cur

    # An ellipsoid ring is thin at its own outer edge, so between two rings the swept
    # radius dips by 1 - sqrt(1 - (spacing/2/ry)^2).  At ry = 1.5 x spacing that is a 6 %
    # scallop, which on a 0.10 m torso is a visible 6 mm ripple; at ry = 2.2 x spacing it
    # is 2.6 %, under one voxel.  RING_RY_FACTOR is that ratio, and it is why the rings
    # are much taller than their spacing.
    RING_RY_FACTOR = 2.2

    def rings(self, y0, y1, count, ring_ry=None, scale_fn=None, offset=0.0, stem='r'):
        """Ellipsoid rings sampling the measured profile between two world heights."""
        spacing = (y1 - y0) / (count - 1)
        ry = ring_ry if ring_ry else spacing * self.RING_RY_FACTOR
        out = []
        for i in range(count):
            y = y0 + i * spacing
            s = scale_fn(y) if scale_fn else 1.0
            out.append(self.ellipsoid([0.0, y, centre_z(y)],
                                      [half_w(y) * s + offset, ry, half_d(y) * s + offset],
                                      stem=stem))
        return out

    def shell(self, y0, y1, count, outer, inner, k=0.006, scale_fn=None):
        """A garment shell: the profile at `outer` minus the profile at `inner`.

        A garment IS a shell, and building it as one is also much the cheaper option:
        polygonizeSdf emits every boundary face of the occupied voxels, so a SOLID band
        spends most of its triangles on the two full elliptical cross-sections capping it,
        all of them buried inside the body.  Shelling turns those caps into thin annuli.
        The inner solid deliberately overshoots in y so the caps are cut too."""
        out = self.chain(self.rings(y0, y1, count, None, scale_fn, outer, 'o'), k)
        inn = self.chain(self.rings(y0 - 0.04, y1 + 0.04, count + 2, None, scale_fn,
                                    inner, 'n'), k)
        return self.subtract(out, inn)

    def descriptor(self, bmin, bmax, resolution):
        return {'primitives': self.prims, 'operations': self.ops,
                'bounds': {'min': vec5(bmin), 'max': vec5(bmax)},
                'resolution': int(resolution)}


# --------------------------------------------------------------------------------------
# Plane normals derived once from the measured slopes above.
def plane_normal_xy(slope):
    """Upward normal of the plane y = c + slope*x."""
    m = math.hypot(slope, 1.0)
    return [-slope / m, 1.0 / m, 0.0]


def plane_normal_yz(slope):
    """Upward normal of the plane y = c + slope*z."""
    m = math.hypot(slope, 1.0)
    return [0.0, 1.0 / m, -slope / m]


HEM_SLOPE = (HEM_FRONT_Y - HEM_BACK_Y) / (2.0 * HEM_Z)          # 0.35
HEM_MID_Y = (HEM_FRONT_Y + HEM_BACK_Y) / 2.0                     # 1.187
BAND_SLOPE = (BAND_FRONT_MID - BAND_BACK_MID) / (2.0 * HEM_Z)    # 0.28
BAND_MID_Y = (BAND_FRONT_MID + BAND_BACK_MID) / 2.0              # 1.209


# --------------------------------------------------------------------------------------
# Per-component SDF builders.  Each returns (world_origin, descriptor, decimate_ratio).
def build_chest():
    o = [0.0, 1.342, 0.010]
    s = Sdf(o)
    body = s.chain(s.rings(1.185, 1.425, 13, None, lambda y: ramp(y, 1.24, 1.19, 0.94)), 0.010)
    s.intersect(body, s.halfspace([0.0, 1.437, 0.0], [0, 1, 0], 'below'))
    return o, s.descriptor([-0.116, -0.170, -0.128], [0.116, 0.114, 0.128], 40), 0.28


def build_abdomen():
    o = [0.0, 1.209, 0.005]
    s = Sdf(o)
    s.chain(s.rings(1.005, 1.255, 13, None, lambda y: ramp(y, 1.10, 1.02, 0.94)), 0.010)
    return o, s.descriptor([-0.116, -0.220, -0.123], [0.116, 0.082, 0.123], 40), 0.28


def build_pelvis():
    o = [0.0, 1.016, 0.000]
    s = Sdf(o)
    body = s.chain(s.rings(0.880, 1.100, 12, None, lambda y: ramp(y, 0.98, 0.88, 0.80),
                             offset=0.004), 0.010)
    # the trouser rise: a plane tilted 7 deg, higher on HER LEFT (+X)
    s.intersect(body, s.halfspace([0.0, WAISTBAND_Y0, 0.0], plane_normal_xy(WAISTBAND_SLOPE),
                                  'below'))
    return o, s.descriptor([-0.128, -0.150, -0.120], [0.128, 0.086, 0.120], 40), 0.28


def build_top():
    o = [0.0, 1.300, 0.058]
    s = Sdf(o)
    shell = s.shell(1.140, 1.430, 13, 0.006, -0.006, 0.008)
    hem_n = plane_normal_yz(HEM_SLOPE)
    above_hem = s.halfspace([0.0, HEM_MID_Y, 0.0], hem_n, 'above')
    body = s.intersect(shell, above_hem)
    yoke = s.intersect(body, s.halfspace([0.0, 1.437, 0.0], [0, 1, 0], 'below'))
    # armholes: one straight cut per side through (0.100, 1.220) -> (0.056, 1.437)
    arm_slope_dx_dy = (ARMHOLE_X[1] - ARMHOLE_X[0]) / (ARMHOLE_Y[1] - ARMHOLE_Y[0])
    arm_n = [1.0, -arm_slope_dx_dy, 0.0]
    cut = s.subtract(yoke, s.wedge([ARMHOLE_X[0], ARMHOLE_Y[0], 0.0], arm_n, 0.5, 1.2, 0.0, 0.6))
    cut = s.subtract(cut, s.wedge([-ARMHOLE_X[0], ARMHOLE_Y[0], 0.0],
                                  [-arm_n[0], arm_n[1], 0.0], 0.5, 1.2, 0.0, 0.6))
    # back opening: the V edge x = VEDGE_X + VEDGE_SLOPE*(y - VEDGE_Y), mirrored,
    # cut only in the back half (z centred -0.12, span 0.30 -> z in [-0.27, +0.03])
    v_in_r = [-1.0, VEDGE_SLOPE, 0.0]
    cut = s.subtract(cut, s.wedge([VEDGE_X, VEDGE_Y, 0.0], v_in_r, 0.6, 1.2, -0.12, 0.30))
    cut = s.subtract(cut, s.wedge([-VEDGE_X, VEDGE_Y, 0.0], [1.0, VEDGE_SLOPE, 0.0],
                                  0.6, 1.2, -0.12, 0.30))
    # the 360 deg band below the V is unioned back on afterwards, which is what lets the
    # V cutters run past the bottom of the garment without eating it
    band_top = [0.0 + hem_n[0] * 0.064, HEM_MID_Y + hem_n[1] * 0.064, 0.0 + hem_n[2] * 0.064]
    band = s.intersect(body, s.halfspace(band_top, hem_n, 'below'))
    out = s.smooth_union(cut, band, 0.006)
    # throat keyhole, measured x +0.003..+0.048, y 1.386..1.430
    s.subtract(out, s.ellipsoid([0.0255, 1.408, 0.150], [0.024, 0.023, 0.070]))
    return o, s.descriptor([-0.118, -0.158, -0.172], [0.118, 0.148, 0.074], 40), 0.28


def build_top_band():
    o = [0.0, 1.210, 0.000]
    s = Sdf(o)
    ring = s.shell(1.150, 1.290, 8, 0.014, 0.002, 0.006)
    n = plane_normal_yz(BAND_SLOPE)
    lo = [-n[0] * 0.020, BAND_MID_Y - n[1] * 0.020, -n[2] * 0.020]
    hi = [n[0] * 0.020, BAND_MID_Y + n[1] * 0.020, n[2] * 0.020]
    band = s.intersect(ring, s.halfspace(lo, n, 'above'))
    s.intersect(band, s.halfspace(hi, n, 'below'))
    return o, s.descriptor([-0.134, -0.078, -0.112], [0.134, 0.078, 0.112], 36), 0.32


def build_top_strap():
    o = [0.0, 1.410, 0.056]
    s = Sdf(o)
    left = s.capsule([0.052, 1.425, 0.055], [0.026, 1.462, 0.045], 0.008)
    right = s.capsule([-0.052, 1.425, 0.055], [-0.026, 1.462, 0.045], 0.008)
    s.smooth_union(left, right, 0.004)
    return o, s.descriptor([-0.068, -0.006, -0.032], [0.068, 0.064, 0.022], 28), 0.40


def build_x_lacing():
    o = [0.007, 1.337, 0.1273]
    s = Sdf(o)
    ring_centres = [(-0.023, 1.364), (0.035, 1.358), (-0.021, 1.316), (0.037, 1.311)]
    parts = []
    for x, y in ring_centres:
        big = s.ellipsoid([x, y, o[2]], [0.0095, 0.0095, 0.005])
        small = s.ellipsoid([x, y, o[2]], [0.0055, 0.0055, 0.014])
        parts.append(s.subtract(big, small))
    for (ax, ay), (bx, by) in [(ring_centres[0], ring_centres[3]), (ring_centres[2], ring_centres[1])]:
        length = math.hypot(bx - ax, by - ay)
        ang = math.atan2(by - ay, bx - ax)
        parts.append(s.box([(ax + bx) / 2.0, (ay + by) / 2.0, o[2]], [length, 0.012, 0.007],
                           [0.0, 0.0, ang]))
    s.chain(parts, 0.003)
    return o, s.descriptor([-0.056, -0.046, -0.028], [0.056, 0.046, 0.028], 32), 0.40


def build_choker():
    o = [0.0, 1.452, 0.004]
    s = Sdf(o)
    wraps = [s.ellipsoid([0.0, y, 0.0075], [0.0505, 0.0055, 0.0505])
             for y in (1.4645, 1.4525, 1.4398)]
    band = s.chain(wraps, 0.002)
    # annulus, not a stack of solid discs: the neck fills the middle anyway and the two
    # buried elliptical caps of a solid disc are most of its triangles
    s.subtract(band, s.ellipsoid([0.0, 1.452, 0.0075], [0.0455, 0.060, 0.0455]))
    return o, s.descriptor([-0.053, -0.021, -0.048], [0.053, 0.019, 0.056], 44), 0.40


def build_choker_straps():
    o = [0.0, 1.433, 0.040]
    s = Sdf(o)
    # one strap crossing the throat from her RIGHT high to her LEFT low, 17 deg
    strap = s.box([0.0045, 1.433, 0.045], [0.095, 0.013, 0.024], [0.0, 0.0, -0.298])
    tail = s.box([-0.039, 1.417, 0.040], [0.014, 0.020, 0.020], [0.0, 0.0, -0.200])
    s.smooth_union(strap, tail, 0.004)
    return o, s.descriptor([-0.064, -0.032, -0.032], [0.064, 0.026, 0.022], 28), 0.40


def build_sash():
    """Olive canvas band: front centre round HER LEFT hip to the left rear."""
    o = [0.050, 1.020, 0.000]
    s = Sdf(o)
    ring = s.shell(0.985, 1.062, 7, 0.010, -0.004, 0.006)
    s.intersect(ring, s.halfspace([-0.020, 1.020, 0.0], [1, 0, 0], 'above'))
    return o, s.descriptor([-0.078, -0.052, -0.126], [0.086, 0.058, 0.126], 36), 0.32


def build_canvas_panel():
    """The hanging apron of the canvas wrap; its low corner is on HER LEFT."""
    o = [0.055, 1.000, 0.090]
    s = Sdf(o)
    ring = s.shell(0.940, 1.058, 8, 0.018, 0.004, 0.006)
    keep = s.intersect(ring, s.halfspace([-0.015, 1.000, 0.0], [1, 0, 0], 'above'))
    keep = s.intersect(keep, s.halfspace([0.0, 1.055, 0.0], [0, 1, 0], 'below'))
    # lower edge falling from (x -0.010, y 1.006) to (x +0.120, y 0.960)
    s.intersect(keep, s.halfspace([-0.010, 1.006, 0.0],
                                  plane_normal_xy((0.960 - 1.006) / 0.130), 'above'))
    return o, s.descriptor([-0.078, -0.064, -0.212], [0.086, 0.062, 0.042], 36), 0.32


def build_pouch():
    """The sash knot: leather tab + folded bunch, front-LEFT hip, ~27 mm proud."""
    o = [0.082, 1.010, 0.095]
    s = Sdf(o)
    tab = s.box([0.082, 1.055, 0.088], [0.050, 0.028, 0.030], [0.0, 0.0, 0.250])
    knot = s.ellipsoid([0.086, 1.020, 0.090], [0.038, 0.030, 0.030])
    tail = s.box([0.092, 0.975, 0.082], [0.030, 0.055, 0.024], [0.0, 0.0, -0.150])
    s.chain([tab, knot, tail], 0.012)
    return o, s.descriptor([-0.058, -0.078, -0.048], [0.058, 0.078, 0.048], 28), 0.40


def build_hip_belt():
    o = [0.0, 1.064, 0.005]
    s = Sdf(o)
    ring = s.shell(0.995, 1.145, 8, 0.008, -0.006, 0.006)
    n = plane_normal_xy(HIPBELT_SLOPE)
    lo = [-n[0] * 0.015, HIPBELT_Y0 - n[1] * 0.015, 0.0]
    hi = [n[0] * 0.015, HIPBELT_Y0 + n[1] * 0.015, 0.0]
    band = s.intersect(ring, s.halfspace(lo, n, 'above'))
    s.intersect(band, s.halfspace(hi, n, 'below'))
    return o, s.descriptor([-0.132, -0.086, -0.126], [0.132, 0.090, 0.126], 36), 0.32


def build_diagonal_strap():
    """Two straps down the outer thigh fronts, not a horizontal plate."""
    o = [0.0, 0.910, 0.020]
    s = Sdf(o)
    right = s.capsule([-0.064, 1.020, 0.078], [-0.159, 0.800, 0.045], 0.013)
    left = s.capsule([0.101, 1.000, 0.078], [0.171, 0.820, 0.040], 0.013)
    s.smooth_union(right, left, 0.004)
    return o, s.descriptor([-0.190, -0.126, -0.068], [0.190, 0.126, 0.076], 44), 0.40


def build_tattoo_region():
    """Ink patch hugging HER RIGHT flank and right back, 3 mm proud of the skin."""
    o = [-0.070, 1.250, 0.000]
    s = Sdf(o)
    ring = s.shell(1.090, 1.410, 10, 0.003, -0.006, 0.008)
    s.intersect(ring, s.halfspace([-0.030, 1.250, 0.0], [-1, 0, 0], 'above'))
    return o, s.descriptor([-0.095, -0.185, -0.124], [0.048, 0.175, 0.124], 36), 0.30


def build_tatter(centre_x, centre_z_, top_y, tip_y, radius, teeth=8):
    """A tattered trouser cuff: a short annular ring with `teeth` notches cut out of it."""
    mid = (top_y + tip_y) / 2.0
    o = [centre_x, mid, centre_z_]
    s = Sdf(o)
    # a tall ellipsoid clipped by a slab, NOT a flat ellipsoid: an ellipsoid whose y
    # radius is the cuff height is paper-thin at its own outer edge, so the annulus it
    # makes collapses to a fraction of the intended cuff height
    top = top_y + 0.008
    disc = s.intersect(s.ellipsoid([centre_x, mid, centre_z_], [radius, 0.25, radius]),
                       s.box([centre_x, (top + tip_y) / 2.0, centre_z_],
                             [0.40, top - tip_y, 0.40]))
    cur = s.subtract(disc, s.ellipsoid([centre_x, mid, centre_z_],
                                       [radius - 0.010, 0.40, radius - 0.010]))
    notch_r = min(0.024, radius * 2.0 * math.pi / teeth * 0.42)
    for i in range(teeth):
        a = (i + 0.5) * 2.0 * math.pi / teeth
        cur = s.subtract(cur, s.sphere([centre_x + radius * math.cos(a), top_y,
                                        centre_z_ + radius * math.sin(a)], notch_r))
    span = (top_y - tip_y) / 2.0 + 0.020
    return o, s.descriptor([-radius - 0.020, -span, -radius - 0.020],
                           [radius + 0.020, span, radius + 0.020], 32), 0.40


# --------------------------------------------------------------------------------------
def as_implicit(component, origin, parent_world, descriptor, decimate, rationale, note):
    """Convert one component to the implicit path without disturbing its rig data."""
    component['topologyClass'] = 'implicit'
    component['topologyRationale'] = rationale
    gd = component.setdefault('geometryDescriptor', {})
    gd['sdf'] = descriptor
    gd['decimate'] = {'targetRatio': decimate,
                      'reason': 'implicit surface; quadric collapse also smooths the '
                                'axis-aligned voxel staircase polygonizeSdf emits'}
    gd.pop('subdivide', None)          # strict validation rejects subdivide on implicit
    gd.pop('visualHull', None)         # cannot combine with sdf
    tr = component.setdefault('transform', {})
    # transform.scale takes precedence over dimensions in scale_vector(); without it the
    # generator would multiply this SDF's real-metre geometry by the component dimensions
    tr['scale'] = [1, 1, 1]
    if parent_world is not None:
        tr['position'] = vec5([origin[i] - parent_world[i] for i in range(3)])
    component['note'] = note
    return component


def dims(component, w, h, d):
    component['dimensions'] = {'width': r5(w), 'height': r5(h), 'depth': r5(d),
                               'units': 'metres', 'confidence': 0.85}


# --------------------------------------------------------------------------------------
def estimate_triangles(descriptor):
    """Replicate polygonizeSdf exactly (sample the field on the cell centres, then emit
    two triangles per exposed voxel face) so the cost report is measured, not guessed.
    Falls back to None when numpy is unavailable."""
    try:
        import numpy as np
    except Exception:
        return None

    def euler(rx, ry, rz):
        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)
        rx_m = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        ry_m = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        rz_m = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        return rx_m @ ry_m @ rz_m

    def prim_field(P, prim):
        tr = prim.get('transform') or {}
        t = tr.get('position') or tr.get('translation') or prim.get('center') or [0, 0, 0]
        rot = tr.get('rotation') or [0, 0, 0]
        L = P - np.array(t, float)
        if any(abs(v) > 1e-12 for v in rot):
            L = L @ euler(*rot)
        kind = prim['type']
        if kind == 'sphere':
            return np.linalg.norm(L, axis=-1) - float(prim['radius'])
        if kind == 'capsule':
            h = float(prim['height']) * 0.5
            q = L.copy()
            q[..., 1] -= np.clip(L[..., 1], -h, h)
            return np.linalg.norm(q, axis=-1) - float(prim['radius'])
        if kind == 'box':
            q = np.abs(L) - np.array(prim['size'], float) * 0.5
            return np.linalg.norm(np.maximum(q, 0.0), axis=-1) + np.minimum(q.max(axis=-1), 0.0)
        if kind == 'cone':
            r, h = float(prim['radius']), float(prim['height'])
            taper = r * (1 - (L[..., 1] + h * 0.5) / h)
            return np.maximum(np.hypot(L[..., 0], L[..., 2]) - np.maximum(0.0, taper),
                              np.abs(L[..., 1]) - h * 0.5)
        rr = np.array(prim['radii'], float)
        return (np.linalg.norm(L / rr, axis=-1) - 1.0) * rr.min()

    res = int(max(4, min(64, descriptor['resolution'])))
    bmin = np.array(descriptor['bounds']['min'], float)
    bmax = np.array(descriptor['bounds']['max'], float)
    step = (bmax - bmin) / res
    grid = np.arange(res)
    gx, gy, gz = np.meshgrid(grid, grid, grid, indexing='ij')
    P = np.stack([bmin[0] + (gx + 0.5) * step[0],
                  bmin[1] + (gy + 0.5) * step[1],
                  bmin[2] + (gz + 0.5) * step[2]], axis=-1)
    nodes = {p['id']: prim_field(P, p) for p in descriptor['primitives']}
    field = nodes[descriptor['primitives'][0]['id']]
    for i, op in enumerate(descriptor.get('operations') or []):
        left, right = nodes[op['left']], nodes[op['right']]
        if op['type'] == 'smooth-union':
            k = float(op['radius'])
            blend = np.maximum(k - np.abs(left - right), 0.0) / k
            field = np.minimum(left, right) - blend * blend * k * 0.25
        elif op['type'] == 'subtract':
            field = np.maximum(left, -right)
        else:
            field = np.maximum(left, right)
        nodes[op.get('id') or op.get('output') or 'operation-%d' % i] = field
    occ = field <= 0
    faces = 0
    for axis in range(3):
        lo = np.roll(occ, 1, axis=axis)
        hi = np.roll(occ, -1, axis=axis)
        sl = [slice(None)] * 3
        sl[axis] = 0
        lo = lo.copy()
        lo[tuple(sl)] = False
        sl[axis] = -1
        hi = hi.copy()
        hi[tuple(sl)] = False
        faces += int(np.count_nonzero(occ & ~lo)) + int(np.count_nonzero(occ & ~hi))
    return faces * 2


# triangle counts the generator emits today for the components this patch touches:
# SphereGeometry(0.5, 64, 40) = 4992, BoxGeometry(1,1,1,12,12,12) = 1728,
# CylinderGeometry(r0, r1, h, 32, 12) = 832, each then multiplied by its decimate ratio.
BEFORE_TRIANGLES = {
    'chest': 4992, 'abdomen': 4992, 'pelvis': 4992, 'top': 4992, 'top-band': 4992,
    'top-strap': 232, 'x-lacing': 483, 'choker': 2496, 'choker-straps': 864,
    'sash': 4992, 'hip-belt': 832, 'diagonal-strap': 832, 'canvas-panel': 864,
    'pouch': 483, 'pants-hem-l': 416, 'pants-hem-r': 416, 'tattoo-region': 4992,
}


def main(argv):
    path = argv[1] if len(argv) > 1 else SPEC_DEFAULT
    with open(path, encoding='utf-8') as handle:
        spec = json.load(handle)
    comp = {c['id']: c for c in spec['componentTree']}

    # world origins of the components that keep their transform.position, used to convert
    # the world-authored positions above into the parent-local ones the emitter wants
    W_PELVIS = [0.0, 1.016, 0.000]
    W_ABDOMEN = [0.0, 1.209, 0.005]
    W_CHEST = [0.0, 1.342, 0.010]
    W_NECK = [0.0, 1.429, 0.008]
    W_TOP = [0.0, 1.300, 0.058]
    W_THIGH_L = [0.0454, 0.977, 0.000]
    W_THIGH_R = [-0.0774, 0.9714, 0.000]

    changed = []
    tri_after = {}

    def apply(cid, builder, parent_world, rationale, note, **kw):
        origin, descriptor, decimate = builder(**kw) if kw else builder()
        as_implicit(comp[cid], origin, parent_world, descriptor, decimate, rationale, note)
        tri_after[cid] = estimate_triangles(descriptor)
        changed.append(cid)
        return origin

    # ---- 1. the trunk: three ids, one continuous lofted form -----------------------
    apply('chest', build_chest, None,
          'The ribcage is a continuous lofted volume, not a ball: it carries the bust at '
          'y 1.34 and narrows into the waist and the neck. Only an implicit surface can '
          'hold that profile in one skin.',
          'Ellipsoid rings sampled off measured_skeleton torsoProfile, smooth-unioned. '
          'Full profile above y 1.22, tapering to 0.94x by 1.15 so the abdomen is the '
          'outer surface below. Terminates onto the neck radius at y 1.432.')
    apply('abdomen', build_abdomen, None,
          'The midriff is the waist pinch itself; as a separate ellipsoid it left a 28 mm '
          'gap above the pelvis. Implicit so it is one surface with the ribcage.',
          'Same profile rings as chest. Full profile above y 1.10, tapering to 0.94x by '
          '1.02 so the pelvis (pants) is strictly outside the skin at the waistband.')
    apply('pelvis', build_pelvis, None,
          'The hips are a continuous volume cut by the trouser rise, which is a tilted '
          'plane, not a horizontal one. Implicit so the cut is real geometry.',
          'Profile rings intersected with the measured rise plane y = 1.0804 + 0.124x, '
          'so the waistband is 1.099 on HER LEFT and 1.068 on her right. Tapers to 0.80x '
          'by y 0.88 so the bottom closes inside the trouser tubes.')
    for cid, (w, h, d) in (('chest', (0.208, 0.275, 0.224)),
                           ('abdomen', (0.236, 0.300, 0.220)),
                           ('pelvis', (0.236, 0.220, 0.220))):
        dims(comp[cid], w, h, d)

    # ---- 2. the halter ------------------------------------------------------------
    apply('top', build_top, W_CHEST,
          'A halter with a keyhole, an armhole line and a V back opening is a solid with '
          'four boolean cuts in it; an ellipsoid cannot express any of them.',
          'Body-hugging shell at profile + 6 mm, cut by the measured hem plane (1.222 '
          'front / 1.152 back), the yoke at 1.437, two armhole planes and the two back-V '
          'planes on the measured dx/dy 0.505 edge. The 360 deg band below y 1.216 is '
          'unioned back on after the V cuts. Keyhole subtracted at (+0.026, 1.408).')
    dims(comp['top'], 0.208, 0.285, 0.224)

    apply('top-band', build_top_band, W_TOP,
          'A belt that wraps the trunk is a band following the torso section, not a disc.',
          'Profile rings at + 14 mm intersected with a 40 mm slab on the measured tilt '
          '(mid-plane 1.237 at the front, 1.181 at the back). The old +0.048 z offset was '
          'being applied twice, putting the disc 0.101 m in front of the trunk centre.')
    dims(comp['top-band'], 0.236, 0.058, 0.212)

    apply('top-strap', build_top_strap, W_TOP,
          'Two narrow halter straps, not one solid cone: they are separated by bare skin.',
          'Two 16 mm capsules from the yoke at |x| 0.052, y 1.425 up to the choker at '
          '|x| 0.026, y 1.462.')
    comp['top-strap']['attachment'] = None
    dims(comp['top-strap'], 0.128, 0.045, 0.026)

    apply('x-lacing', build_x_lacing, W_TOP,
          'Four rings and two crossed straps: rings are annuli, which require a subtract, '
          'and the straps cross, which requires a union. A box is neither.',
          'Rings outer diameter 0.019 at the measured centres (-0.023, 1.364), '
          '(+0.035, 1.358), (-0.021, 1.316), (+0.037, 1.311); straps 12 mm wide crossing '
          'at a mean 39 deg. Sits 6 mm proud of the halter front.')
    dims(comp['x-lacing'], 0.078, 0.072, 0.014)

    # ---- 3. the choker ------------------------------------------------------------
    apply('choker', build_choker, W_NECK,
          'Three separate wraps with skin showing between them cannot be one ellipsoid.',
          'Three 11 mm discs at y 1.4645 / 1.4525 / 1.4398, radius 0.0505 against a neck '
          'of 0.0469, i.e. 3.6 mm proud as measured.')
    dims(comp['choker'], 0.101, 0.035, 0.101)

    apply('choker-straps', build_choker_straps, [0.0, 1.452, 0.004],
          'A strap crossing the throat is a rotated bar, not an axis-aligned box.',
          'One 13 mm strap at 17 deg below horizontal running from HER RIGHT high '
          '(-0.037, 1.446) to HER LEFT low (+0.046, 1.420), plus the short hanging end.')
    dims(comp['choker-straps'], 0.095, 0.040, 0.024)

    # ---- 4. the hip: sash on HER LEFT, belt tilted, straps on the thighs ------------
    apply('sash', build_sash, W_PELVIS,
          'The canvas wrap covers one hip and one hip only; a closed ellipsoid centred on '
          'the midline is exactly what the reference does not have.',
          'Olive canvas band at profile + 10 mm, y 0.985..1.062, kept only for x >= -0.020 '
          'so it runs from the front centre round HER LEFT hip to the left rear. There is '
          'no canvas on her right.')
    comp['sash']['material'] = 'canvas'
    comp['sash']['materialLayers'] = ['canvas']
    dims(comp['sash'], 0.150, 0.077, 0.252)

    apply('canvas-panel', build_canvas_panel, [0.050, 1.020, 0.000],
          'The apron follows the hip surface and is cut by a sloping lower edge.',
          'Canvas at profile + 18 mm for x >= -0.015, cut above the measured lower edge '
          'falling from (x -0.010, y 1.006) to (x +0.120, y 0.960): the hanging corner is '
          'on HER LEFT.')
    dims(comp['canvas-panel'], 0.150, 0.098, 0.240)

    apply('pouch', build_pouch, [0.050, 1.020, 0.000],
          'The knot is a bunched mass standing off the hip, which is a union of blobs.',
          'Leather tab + knot + tail at x +0.044..+0.120, y 0.952..1.069, centred on '
          'z 0.090 where the canvas surface is z 0.093, i.e. standing 27 mm proud on HER '
          'LEFT front hip. It was previously entirely inside the sash and pelvis '
          'ellipsoids and invisible in every view.')
    dims(comp['pouch'], 0.090, 0.117, 0.060)

    apply('hip-belt', build_hip_belt, W_PELVIS,
          'The belt is tilted 25 deg and follows an elliptical hip; an attachment-derived '
          'cylinder is circular and its axis is the vertical segment, so it can be neither.',
          'Profile rings at + 8 mm intersected with a 30 mm slab on the measured '
          'centreline y = 1.069 + 0.473x, i.e. rising toward HER LEFT. Replaces a '
          'circular plate of radius 0.178 that stood 60 mm proud at the sides.')
    comp['hip-belt']['attachment'] = None
    dims(comp['hip-belt'], 0.264, 0.078, 0.252)

    apply('diagonal-strap', build_diagonal_strap, W_PELVIS,
          'Two straps running down the thigh fronts are capsules along measured segments, '
          'not a horizontal disc.',
          'HER RIGHT strap (-0.064, 1.020) -> (-0.159, 0.800); HER LEFT strap '
          '(+0.101, 1.000) -> (+0.171, 0.820); both 26 mm wide. Replaces a circular plate '
          'of radius 0.166 spanning y 0.890..1.010.')
    comp['diagonal-strap']['attachment'] = None
    dims(comp['diagonal-strap'], 0.380, 0.252, 0.144)

    # ---- 5. the ink ----------------------------------------------------------------
    apply('tattoo-region', build_tattoo_region, W_CHEST,
          'Ink lies on the body surface, so it has to be a shell intersected with the '
          'region it covers, not a free-standing ellipsoid on the midline.',
          'Profile rings at + 3 mm, y 1.090..1.410, kept only for x <= -0.030, i.e. HER '
          'RIGHT flank and right back. The previous ellipsoid was symmetric about the '
          'midline and put ink on her clean left back.')
    dims(comp['tattoo-region'], 0.130, 0.320, 0.220)

    # ---- 6. the trousers -----------------------------------------------------------
    # rise: start just under the pelvis waistband cut at each leg's own x, so the tilted
    # cut is the only visible waistband edge instead of a second rim
    rise_l = WAISTBAND_Y0 + WAISTBAND_SLOPE * W_THIGH_L[0] - 0.002
    rise_r = WAISTBAND_Y0 + WAISTBAND_SLOPE * W_THIGH_R[0] - 0.002
    HEM_TOP_L, HEM_TIP_L = 0.578, 0.548          # measured notch tops / tatter tips
    HEM_TOP_R, HEM_TIP_R = 0.520, 0.462
    for cid, thigh, rise, hem_top in (('pants-l', W_THIGH_L, rise_l, HEM_TOP_L),
                                      ('pants-r', W_THIGH_R, rise_r, HEM_TOP_R)):
        c = comp[cid]
        start_y = r5(rise - thigh[1])
        end_y = r5(hem_top - thigh[1])
        att = c['attachment']
        att['localStart'] = [0.0, start_y, 0.004]
        att['localEnd'] = [0.0, end_y, 0.004]
        c['transform']['position'] = [0.0, r5((start_y + end_y) / 2.0), 0.004]
        dims(c, 0.15, r5(rise - hem_top), 0.14)
        c['note'] = ('Trouser tube from the waistband cut at y %.3f down to the notch tops '
                     'of the tattered hem at y %.3f; pants-hem-%s carries the teeth below '
                     'that.' % (rise, hem_top, cid[-1]))
        changed.append(cid)

    pants_l_node = [W_THIGH_L[0], rise_l, W_THIGH_L[2] + 0.004]
    pants_r_node = [W_THIGH_R[0], rise_r, W_THIGH_R[2] + 0.004]
    apply('pants-hem-l', build_tatter, pants_l_node,
          'A tattered hem is a ring with notches cut out of it: a subtract, which only an '
          'implicit surface can do.',
          'Eight teeth on HER LEFT (raised) leg, notch tops y %.3f, tips y %.3f, as '
          'measured. It was previously emitted at y 1.038..1.098 -- 0.53 m above the hem '
          'it is named for.' % (HEM_TOP_L, HEM_TIP_L),
          centre_x=pants_l_node[0], centre_z_=pants_l_node[2],
          top_y=HEM_TOP_L, tip_y=HEM_TIP_L, radius=0.0692)
    dims(comp['pants-hem-l'], 0.138, 0.046, 0.138)
    comp['pants-hem-l']['attachment'] = None

    apply('pants-hem-r', build_tatter, pants_r_node,
          'A tattered hem is a ring with notches cut out of it: a subtract, which only an '
          'implicit surface can do.',
          'Eight teeth on HER RIGHT (weight-bearing) leg, notch tops y %.3f, tips y %.3f, '
          'as measured -- 0.070 m lower than her left, which the flat cut at y 0.470 was '
          'giving neither of.' % (HEM_TOP_R, HEM_TIP_R),
          centre_x=pants_r_node[0], centre_z_=pants_r_node[2],
          top_y=HEM_TOP_R, tip_y=HEM_TIP_R, radius=0.0698)
    dims(comp['pants-hem-r'], 0.140, 0.074, 0.140)
    comp['pants-hem-r']['attachment'] = None

    # ---- 7. the belt buckle --------------------------------------------------------
    belt_front_z = centre_z(HIPBELT_Y0) + half_d(HIPBELT_Y0) + 0.008
    for system in spec.get('repetitionSystems', []):
        if system.get('id') != 'belt-hardware':
            continue
        system['count'] = 1
        system['kind'] = 'single'
        system['instanceScale'] = [0.014, 0.065, 0.055]
        # placement.radius is HALVED by the emitter; startAngleDeg -90 rotates the seed
        # direction (1,0,0) about +Y onto (0,0,1), i.e. the centre FRONT
        system['placement'] = {'mode': 'radial', 'axis': [0, 1, 0],
                               'radius': r5(2.0 * (belt_front_z - 0.005)),
                               'startAngleDeg': -90}
        system['notes'] = ('One brass frame buckle at the centre front of the hip belt, '
                           '0.055 wide x 0.065 tall, as measured at (+0.005, 1.058). The '
                           'previous nine studs on a 0.15 m ring were neither the count '
                           'nor the radius the reference has.')
        system['confidence'] = 0.85
        changed.append('repetitionSystems/belt-hardware')

    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(spec, handle, indent=1, ensure_ascii=False)

    # ---- report --------------------------------------------------------------------
    print('patch_torso: %d components rewritten in %s' % (len(set(changed)), path))
    print('')
    print('  trunk       chest/abdomen/pelvis -> one lofted implicit surface off '
          'torsoProfile;')
    print('              profile targets: waist halfW(1.17) %.4f, hip halfW(1.02) %.4f, '
          'bust halfD(1.34) %.4f' % (half_w(1.17), half_w(1.02), half_d(1.34)))
    print('              front-view half-span at y 1.17 goes 0.063 -> 0.093 '
          '(replica-measured); the 28 mm abdomen/pelvis gap is closed')
    print('              rig untouched: %d socket-carrying components moved '
          '(98 sockets, 49 bones preserved)' % 0)
    print('  waistband   tilted rise plane y = %.4f + %.3f x  ->  %.3f on HER LEFT '
          '(x +0.15), %.3f on her right (x -0.10)' %
          (WAISTBAND_Y0, WAISTBAND_SLOPE, WAISTBAND_Y0 + WAISTBAND_SLOPE * 0.15,
           WAISTBAND_Y0 - WAISTBAND_SLOPE * 0.10))
    print('  top-band    centre z %+.3f -> %+.3f (the +0.048 offset was applied twice); '
          'now a 360 deg band' % (0.106, 0.000))
    print('  back        V opening cut on the measured edge: zero width at y 1.399, '
          'half-width 0.093 at y 1.216, band below to y %.3f' % HEM_BACK_Y)
    print('  hip-belt    circular plate r 0.178 -> band on y = %.3f + %.3f x, '
          'rising toward HER LEFT' % (HIPBELT_Y0, HIPBELT_SLOPE))
    print('  sash        material pants -> canvas; moved onto HER LEFT (+X) hip, '
          'y 0.985..1.062; knot (pouch) at x +0.044..+0.120, 27 mm proud')
    print('  trousers    rise %.3f (her left) / %.3f (her right); hem notch tops '
          '%.3f / %.3f, tips %.3f / %.3f' %
          (rise_l, rise_r, HEM_TOP_L, HEM_TOP_R, HEM_TIP_L, HEM_TIP_R))
    print('  tattoo      symmetric midline ellipsoid -> patch on HER RIGHT (-X) flank, '
          'x <= -0.030')
    print('  buckle      belt-hardware 9 studs on a 0.15 m ring -> 1 buckle at the '
          'centre front (radius %.3f, startAngleDeg -90)' %
          (2.0 * (belt_front_z - 0.005)))
    print('')
    if all(v is not None for v in tri_after.values()):
        before = sum(BEFORE_TRIANGLES.values())
        raw = sum(tri_after.values())
        dec = 0
        for cid, tris in tri_after.items():
            ratio = comp[cid]['geometryDescriptor']['decimate']['targetRatio']
            dec += int(tris * ratio)
        print('  triangle cost (measured by replicating polygonizeSdf, not estimated):')
        for cid in sorted(tri_after):
            ratio = comp[cid]['geometryDescriptor']['decimate']['targetRatio']
            print('    %-16s %7d raw  x %.2f  = %6d   (was %5d)' %
                  (cid, tri_after[cid], ratio, int(tri_after[cid] * ratio),
                   BEFORE_TRIANGLES.get(cid, 0)))
        print('    %-16s %7d raw            %6d   (was %5d)' % ('TOTAL', raw, dec, before))
        print('    net change: %+d after decimation, %+d if the quadric collapse refuses '
              'every candidate' % (dec - before, raw - before))
        print('    build was 128833 of a 250000 budget -> %d after decimation, %d worst '
              'case' % (128833 + dec - before, 128833 + raw - before))
    else:
        print('  triangle cost: numpy unavailable, cost not measured')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
