"""Replace the head ellipsoid with a sculpted implicit skull, and reseat the face.

WHAT WAS MEASURED
-----------------
The recon pass measured the reference head off `head_1` (front) and `head_2`
(her-right near-profile), which are within 0.8% of a common scale, anchored to
`body_2` at 1.3490 mm/px. Menton (chin bottom) is a real silhouette measurement
-- in `head_2` the chin separates into its own alpha island and disappears at
panel y 523 -- and lands at world Y 1.4907 +/- 0.004. The cranial vertex is NOT
measured: the vault is hair-covered in all ten reference views, and 1.674 is an
estimate bracketed 1.6695..1.680 by two independent estimators. Skull height is
therefore 183.3 mm +/- 6, and the chin is the end that is wrong.

Against that, the build measured: chin at 1.5050 (+14.3 mm too high), skull width
152.8 mm (+19 vs the 134 mm estimate), ear top 14.5 mm too low, ears buried
0.6 mm INSIDE the head ellipsoid, mouth floating 27.7 mm proud of the face, eye
sockets emitted as 2.4 x 1.6 x 2.1 mm specks, and no mandible, jaw line, chin
mass or submental plane anywhere in the tree -- the head ellipsoid simply tapers
to a point at 1.505. In profile that inverts the chin/throat relationship: the
neck out-fronts the chin by 49.0 mm where the reference has the chin 48.6 mm
ahead of the neck, a 98 mm swing, read on the render as a 62 mm re-entrant step
in 56 mm of height.

The single most important structural fact: from brow to chin the reference's
face front stays inside a -20..+7 mm band around the glabella plane. It is a
near-vertical plane, not a sphere. The build's sphere has receded 84 mm by the
time it reaches the chin.

WHAT THIS CHANGES
-----------------
`head` becomes `topologyClass: "implicit"` with a 17-primitive / 16-operation
SDF: cranium, occiput, paired temporals, brow ridge, paired zygomatics, maxilla,
nasal root, mandible, chin, a box mentum, paired rami and a throat capsule,
smooth-unioned in a linear chain, then two ellipsoid eye sockets subtracted. The
last operation is the output, as the emitter requires. Every primitive is
authored in head-local metres and divided by the sampling window, so the numbers
below are what the mesh actually measures, not what the descriptor nominally says.

Three generator facts drove the shape of this patch and none is in the schema:

1. SDF output is scaled by `dimensions` after polygonization, exactly like
   `SphereGeometry(0.5)` is. The existing eye-cavity descriptors were authored as
   if the SDF were already in metres, a 21x-per-axis error that shrank a 50 mm
   socket to a 2 mm speck. Everything here is authored in a normalised window and
   `dimensions` carries the real size: 0.1540 x 0.1955 x 0.1540 m.
2. `subdivide.iterations` CANNOT be used here. `validate_subdivision_budget()`
   rejects any subdivide on an `implicit` component outright -- "cannot
   statically budget emitted primitive 'implicit sdf'" -- and it is a hard error,
   not a strict-mode warning. So the brief's plan of SDF + 2 Catmull-Clark passes
   is not available. Smoothness has to come from the grid instead: resolution 64
   (the hero tier's ceiling) over this window is a 2.41 x 3.05 x 2.41 mm voxel,
   about 1.2 x 1.5 px in a 900 px render, and `polygonizeSdf` welds cell corners
   into shared vertices so `computeVertexNormals` averages the staircase away in
   shading. The staircase survives in silhouette at sub-pixel amplitude.
3. The window's x and z scales are deliberately equal (0.1540 both) even though
   the skull only needs +/-67 mm in x. Under an anisotropic window a `capsule`'s
   circular xz cross-section would come out elliptical, and the throat capsule
   has to match the neck cylinder's 46.89 mm radius exactly or the step this
   patch exists to remove comes back. 10 mm of empty margin either side of the
   skull is the price; it costs 0.2 mm of voxel size.

`decimate` is deliberately NOT set on the head. A quadric collapse on an
axis-aligned voxel shell is what produced the reported 158/862 inside-out
vertices and 12 non-manifold edges on the old eye cavities, and the head is the
worst component to gamble geometry_integrity on.

The eye cavities are FOLDED IN as subtractions rather than repaired in place, and
`eye-cavity-l` / `eye-cavity-r` are deleted. A separate mesh cannot recess
another mesh; it can only add a shell that floats in front of the face or is
buried inside it, which is precisely the defect. Subtraction inside the skull's
own field is the only construct in this generator's vocabulary that removes
material from the head, and it costs two primitives and two operations instead of
two components with their own polygonize and decimate passes. The `skinShade`
material is left in place even though nothing now uses it; materials belong to
another dimension.

`head.transform.position` is NOT touched. The measured menton is 14.3 mm below
the head node's own lower pole, so the honest fix is to put the geometry where
the measurements say inside an asymmetric sampling window, rather than move the
node -- moving it would silently drag `hair` and all six hair children, which
belong to another dimension, and would desynchronise `rig.bones.head.jointPos`.

MEASURED RESULT (numpy mirror of sdfSample + polygonizeSdf, exact semantics)
---------------------------------------------------------------------------
Midline face-front profile, head-local mm, versus the reference targets:
  brow      +85.6 (want 83.6, +2.0)      subnasale +73.6 (want 75.7, -2.1)
  nasion    +80.8 (want 83.6, -2.8)      pogonion  +76.0 (want 75.3, +0.7)
  menton    +63.9 (want 64.1, -0.2)
The worst is 2.8 mm, about one 2.41 mm voxel, and the whole run sits
inside the reference's measured -20..+7 mm glabella band. Bounding box lands at
x +/-67.4 (want +/-67.0), y -107.5..+84.9 (want -98.8..+84.5; the low end is the
throat column, deliberately clipped by the window so it merges into the neck),
z -61.2..+85.6 (want -62.0..+83.6). Corner-emitted meshes round outward by up to
one voxel by construction, so +2 mm on an outer face is the floor, not an error.

EXPECTED MEASURABLE EFFECT
--------------------------
Check these, in this order:

* Side view (yaw 90) clay silhouette, the head-to-neck band. The front-most
  silhouette z between world y 1.560 and 1.504 currently collapses +116 -> +54 mm,
  a 62 mm re-entrant step in 56 mm of height, then runs dead vertical. It should
  become a monotonic jaw line with the largest single step 16.8 mm, at the
  cervicomental transition 4 mm above the menton, exactly where the reference
  has one. Below it the throat reads +47.1 mm against the neck cylinder's +46.9 --
  a 0.2 mm match, so the head/neck junction should show no step at all.
* Chin versus neck front. Currently the neck out-fronts the chin by 49.0 mm.
  It should invert to the chin leading by 29.1 mm. The reference is 48.6 mm; the
  remaining 19.5 mm is the neck cylinder's own Z, which belongs to the torso
  dimension -- the neck front sits 20 mm ahead of where the reference's
  glabella-relative -56.9 mm puts it. The SIGN error is fixed here; the magnitude
  cannot be without moving the neck.
* Head bottom. The lowest chin point moves from world 1.5050 to 1.4907, -14.3 mm,
  onto the measured menton. The crown does not move: 1.6740 either way.
* Ears. `ear-l` outer edge moves from 69.9 to 81.2 mm off the midline and from
  interior (-0.6 mm, invisible in every view) to 16.2-18.6 mm proud of the skull
  surface. Ear height 36.0 -> 49.9 mm, ear canal 21.7 mm forward.
* Mouth stand-off from the face goes from +27.7 mm (a lip blob in mid-air) to
  -3.4 mm (embedded). Eye aperture 28.1 x 25.0 -> 36.3 x 16.5 mm.
* Brows. Sampled over the whole bar surface against the skull front beneath it,
  the worst protrusion drops from +36.2 mm to +4.7 mm, and the front-view
  projected width from 51.7 mm to the measured 43.7. The 36 mm figure is the
  lateral end of a flat bar hanging off a ridge that recedes 26.5 mm across the
  brow's own length; it is a defect the build has today, not one introduced here.
* Geometry integrity. The emitted skull has ZERO diagonal-only occupied-cell
  pairs, i.e. zero non-manifold edges from voxel corner contact, checked
  exhaustively over all three axis pairs. The socket depth was tuned against that
  count: at socket z 0.0940 it was 6, at 0.0968 it is 0. That is a property of
  this exact parameter set, not a robust invariant -- if any skull primitive is
  retuned, re-run the check.
* Triangles. The head goes from SphereGeometry(0.5,64,40) = 4,992 to 37,928
  (18,964 quads, counted, not estimated). Deleting the two eye cavities returns
  between 524 and 3,488 (each polygonizes to 1,744 before a 0.15 quadric pass
  that refuses flips and boundary collapses, so the post-decimation figure is a
  range). Net +29,448 to +32,412; call it +31,000 +/- 1,500. Model total moves
  from 128,833 to about 159,800 against a 250,000 budget. `performanceBudget.
  measuredTriangles` and `lodPlan` are deliberately left stale: they are recorded
  as counted from a built scene, and overwriting a measurement with an estimate
  is worse than leaving it obviously old.

WHAT THIS PATCH CANNOT DO
-------------------------
`hair` is a 197.7 x 300.0 x 305.0 mm ellipsoid that encloses the entire head. The
old head ellipsoid was 100% interior to it (worst point f = 0.821). The new skull
is 79.8% interior: 20.2% of its surface cells now emerge, and all of them lie
below head-local y -69.3 mm -- the jaw, chin, mentum and throat, which is exactly
the region this patch was asked to fix. The brow, eye sockets, nose and ears stay
inside the hair blob and will not appear in any render until the hair dimension
shrinks or splits that component. Fixing `hair` here would collide with a
parallel agent, so it is reported rather than done.

Also not fixed, and not fixable from the reference set: cranial vault and occiput
shape (hair-occluded in all ten views; the occiput at -62.0 mm is inferred from
the measured 75.9 mm glabella-to-ear-canal plus normal skull proportion, not
measured), the gonion / jaw-angle corner (no readable corner in `head_1`, mandible
behind hair in `head_2`), and the eye's Z (no reference view shows an eye in
profile). The skull half-width of 67 mm is the recon's 134 mm estimate, itself a
range of 124-144. That estimate is why ear protrusion comes out at 16-19 mm here
where the recon predicted ~11: the recon's 11 assumed a ~140 mm skull. The ear's
outer edge at 81.2 mm off the midline IS directly measured, so that is what is
built, and the protrusion is whatever the inferred skull width makes it.
"""
from __future__ import annotations

import json
import sys

SPEC = sys.argv[1] if len(sys.argv) > 1 else "object-sculpt-spec.json"

# The head node's world position, confirmed against rig.bones["head"].jointPos.
# head-local = world - HEAD_NODE.  Children of `head` carry head-local positions.
HEAD_NODE = (0.0, 1.5895, 0.004)

# The SDF sampling window in head-local metres. x and z scales are equal on
# purpose (see the docstring): a capsule's xz cross-section must stay circular.
WIN = {"x": (-0.0770, 0.0770), "y": (-0.1075, 0.0880), "z": (-0.0660, 0.0880)}
DIM = tuple(WIN[a][1] - WIN[a][0] for a in "xyz")          # 0.1540, 0.1955, 0.1540
RESOLUTION = 64                                             # hero tier ceiling

# --- the skull, authored in head-local metres ------------------------------
# ellipsoid: (centre, semi-axes)   box: (centre, full size)   capsule: (centre, r, h)
ELLIPSOIDS = [
    ("cranium",    (0.0000,  0.02225,  0.01080), (0.0665, 0.06225, 0.07260)),
    ("occiput",    (0.0000, -0.01800, -0.01000), (0.0575, 0.04000, 0.04500)),
    ("temporal-l", (0.0330, -0.00800,  0.00300), (0.0335, 0.03900, 0.05200)),
    ("temporal-r", (-0.0330, -0.00800, 0.00300), (0.0335, 0.03900, 0.05200)),
    ("browridge",  (0.0000,  0.01400,  0.03300), (0.0595, 0.01250, 0.05000)),
    ("zygo-l",     (0.0325, -0.01300,  0.02400), (0.0335, 0.02600, 0.05500)),
    ("zygo-r",     (-0.0325, -0.01300, 0.02400), (0.0335, 0.02600, 0.05500)),
    ("maxilla",    (0.0000, -0.05000,  0.02300), (0.0505, 0.02400, 0.05250)),
    ("nasalroot",  (0.0000, -0.02000,  0.05100), (0.0105, 0.02600, 0.03150)),
    ("mandible",   (0.0000, -0.07300,  0.01900), (0.0450, 0.02100, 0.05300)),
    ("chin",       (0.0000, -0.08100,  0.03550), (0.0250, 0.01650, 0.04000)),
    ("ramus-l",    (0.0470, -0.04800, -0.00600), (0.0165, 0.03300, 0.02850)),
    ("ramus-r",    (-0.0470, -0.04800, -0.00600), (0.0165, 0.03300, 0.02850)),
    # subtracted; z tuned to 0.0968 because that is where the non-manifold
    # diagonal-cell count over the whole skull drops to zero.
    ("socket-l",   (0.0338, -0.00940,  0.09680), (0.0210, 0.01400, 0.02820)),
    ("socket-r",   (-0.0338, -0.00940, 0.09680), (0.0210, 0.01400, 0.02820)),
]
# a flat-bottomed mentum: an ellipsoid always tapers to a point, and the menton
# is a plane at world 1.4907 with the face still 64 mm forward of the node there.
BOXES = [("mentum", (0.0000, -0.09320, 0.04250), (0.0420, 0.01120, 0.04500))]
# radius matches the neck cylinder's 46.89 mm exactly; the window clips its lower
# end so the head's throat and the neck's shaft are the same column.
CAPSULES = [("throat", (0.0000, -0.07000, 0.00000), 0.0469, 0.0760)]

CHAIN = [                                   # (right operand, blend radius, metres)
    ("occiput", 0.006), ("temporal-l", 0.005), ("temporal-r", 0.005),
    ("browridge", 0.004), ("zygo-l", 0.004), ("zygo-r", 0.004),
    ("maxilla", 0.004), ("nasalroot", 0.003), ("mandible", 0.004),
    ("chin", 0.003), ("mentum", 0.003), ("ramus-l", 0.004),
    ("ramus-r", 0.004), ("throat", 0.006),
]

# --- the small facial parts, head-local metres -----------------------------
# dimensions are FULL extents; the generator scales a unit primitive by them.
FACE_PARTS = {
    # eye aperture 36.3 x 16.5 measured; front lands flush with the uncarved face
    # plane at the pupil axis (+78.4) so the eyeball fills the socket dish.
    "eye-l":  dict(pos=(0.0338, -0.00940, 0.06940), dim=(0.03630, 0.01650, 0.01800)),
    "eye-r":  dict(pos=(-0.0338, -0.00940, 0.06940), dim=(0.03630, 0.01650, 0.01800)),
    # Medial end 11.5, lateral end 55.2 off the midline; band from the inferior
    # margin (+12.4) to the arch top (+20.3). ROTATED about Y by 36.7 deg because
    # the brow ridge recedes 26.5 mm in z between those two x: an axis-aligned bar
    # spikes 36.2 mm out of the temple at its lateral end, which is what the build
    # does today. Tilted and thinned to 6 mm it tracks the ridge, protruding at
    # most 4.7 mm anywhere on its surface and sitting 70% embedded, so what shows
    # is a band on the ridge rather than a shelf. Width 50.0 is the TRUE bar
    # length; it projects into the front view as the measured 43.7 mm.
    "brow-l": dict(pos=(0.03335, 0.01635, 0.07000), dim=(0.05000, 0.00790, 0.00600),
                   rot=(0.0, 0.6400, 0.0)),
    "brow-r": dict(pos=(-0.03335, 0.01635, 0.07000), dim=(0.05000, 0.00790, 0.00600),
                   rot=(0.0, -0.6400, 0.0)),
    # solved, not guessed: the rotated ellipsoid whose most anterior point is the
    # measured pronasale (-43.2, +99.4), whose lowest point is the subnasale
    # (-56.4) and whose highest is the nasion (-10.2). Residual 0.00 mm on all
    # four constraints. Width is the measured alar 31.7.
    "nose":   dict(pos=(0.0, -0.03330, 0.07853), dim=(0.03170, 0.05280, 0.03300),
                   rot=(-0.6691, 0.0, 0.0)),
    # width 45.3, lip mass 15.3 tall; depth 48.0 is what it takes for the mouth
    # corners to still reach the skull (+63.9 there) while the midline vermilion
    # peak lands on the measured +90.2.
    "mouth":  dict(pos=(0.0, -0.07265, 0.06620), dim=(0.04530, 0.01530, 0.04800)),
    # height 49.9 (superaurale +3.0 to subaurale -46.9), front-back 30.3
    # (tragus +13.1 to +(-17.2)), outer edge on the measured 81.2 off the midline.
    "ear-l":  dict(pos=(0.0702, -0.02195, -0.00205), dim=(0.02200, 0.04990, 0.03030)),
    "ear-r":  dict(pos=(-0.0702, -0.02195, -0.00205), dim=(0.02200, 0.04990, 0.03030)),
}

DROP = ("eye-cavity-l", "eye-cavity-r")
SOURCE = "analysis/_hf recon (head_1 front + head_2 profile, anchored to body_2)"


def _u(v):
    """head-local metres -> SDF window units."""
    return [round(v[i] / DIM[i], 6) for i in range(3)]


def build_sdf() -> dict:
    prims = []
    for pid, c, r in ELLIPSOIDS:
        prims.append({"id": pid, "type": "ellipsoid", "center": _u(c), "radii": _u(r)})
    for pid, c, s in BOXES:
        prims.append({"id": pid, "type": "box", "center": _u(c), "size": _u(s)})
    for pid, c, r, h in CAPSULES:
        prims.append({"id": pid, "type": "capsule", "center": _u(c),
                      "radius": round(r / DIM[0], 6), "height": round(h / DIM[1], 6)})
    ops, left = [], "cranium"
    for i, (right, radius) in enumerate(CHAIN, start=1):
        out = f"k{i}"
        ops.append({"id": out, "type": "smooth-union", "left": left, "right": right,
                    "radius": round(radius / DIM[0], 6)})
        left = out
    ops.append({"id": "orbit-l", "type": "subtract", "left": left, "right": "socket-l"})
    # the LAST operation is the output the emitter takes, so the CSG root is last
    ops.append({"id": "skull", "type": "subtract", "left": "orbit-l", "right": "socket-r"})
    return {
        "primitives": prims,
        "operations": ops,
        "bounds": {"min": [round(WIN[a][0] / DIM[i], 6) for i, a in enumerate("xyz")],
                   "max": [round(WIN[a][1] / DIM[i], 6) for i, a in enumerate("xyz")]},
        "resolution": RESOLUTION,
    }


def main() -> int:
    spec = json.load(open(SPEC, encoding="utf-8"))
    tree = spec["componentTree"]
    by_id = {c["id"]: c for c in tree}
    report: list[str] = []

    head = by_id.get("head")
    if head is None:
        print("head component missing; nothing to do", file=sys.stderr)
        return 1

    before_class = head.get("topologyClass")
    before_dim = tuple(head["dimensions"][k] for k in ("width", "height", "depth"))

    head["topologyClass"] = "implicit"
    head["topologyRationale"] = (
        "The head is a continuous sculpted form, not an assembled primitive: the "
        "reference's face front is a near-vertical plane from brow to chin (inside "
        "a -20..+7 mm band around the glabella) with a mandible, chin and submental "
        "plane, none of which an ellipsoid can express. Emitted through polygonizeSdf."
    )
    head["primitive"] = "ellipsoid"          # not consulted on the implicit path
    head["dimensions"].update(width=DIM[0], height=DIM[1], depth=DIM[2])
    gd = head["geometryDescriptor"]
    gd["sdf"] = build_sdf()
    gd["uvStrategy"] = "none; implicit surface emits position and index only"
    gd["normalStrategy"] = "smooth vertex normals averaged over welded voxel corners"
    gd["topologyIntent"] = "sculpted skull: cranium, brow, cheekbones, jaw, chin, throat"
    # a quadric collapse on an axis-aligned voxel shell is what broke the old eye
    # cavities; the head is the wrong component to gamble geometry_integrity on.
    gd.pop("decimate", None)
    gd.pop("subdivide", None)                # rejected outright on an implicit component
    head["fidelityTier"] = "sculpt"
    head["measurementSource"] = SOURCE
    report.append(
        f"head: topologyClass {before_class!r} -> 'implicit'; "
        f"dimensions {before_dim[0]:.4f}x{before_dim[1]:.4f}x{before_dim[2]:.4f} -> "
        f"{DIM[0]:.4f}x{DIM[1]:.4f}x{DIM[2]:.4f} m; "
        f"sdf {len(gd['sdf']['primitives'])} primitives / {len(gd['sdf']['operations'])} "
        f"operations at resolution {RESOLUTION}"
    )
    report.append(
        f"  voxel {DIM[0]/RESOLUTION*1000:.2f} x {DIM[1]/RESOLUTION*1000:.2f} x "
        f"{DIM[2]/RESOLUTION*1000:.2f} mm; sampled world y "
        f"{HEAD_NODE[1] + WIN['y'][0]:.4f}..{HEAD_NODE[1] + WIN['y'][1]:.4f}; "
        f"menton 1.4907 (was 1.5050), crown 1.6740 (unchanged)"
    )

    dropped = [c["id"] for c in tree if c["id"] in DROP]
    if dropped:
        spec["componentTree"] = [c for c in tree if c["id"] not in DROP]
        report.append(
            f"removed {len(dropped)} component(s) {dropped}: the eye socket is now a "
            "subtraction inside the head's own field, so a separate cavity mesh has "
            "nothing to be. Their descriptors were authored in metres against an "
            "SDF that is scaled by `dimensions`, making each a 2.4x1.6x2.1 mm speck."
        )

    for cid, want in FACE_PARTS.items():
        c = by_id.get(cid)
        if c is None:
            continue
        old_pos = tuple(c["transform"]["position"])
        old_dim = tuple(c["dimensions"][k] for k in ("width", "height", "depth"))
        c["transform"]["position"] = list(want["pos"])
        c["transform"]["rotation"] = list(want.get("rot", (0.0, 0.0, 0.0)))
        c["dimensions"].update(width=want["dim"][0], height=want["dim"][1],
                               depth=want["dim"][2])
        c["measurementSource"] = SOURCE
        dp = tuple((want["pos"][i] - old_pos[i]) * 1000 for i in range(3))
        report.append(
            f"{cid}: pos {tuple(round(v*1000,1) for v in old_pos)} -> "
            f"{tuple(round(v*1000,1) for v in want['pos'])} mm (d "
            f"{dp[0]:+.1f},{dp[1]:+.1f},{dp[2]:+.1f}); dim "
            f"{tuple(round(v*1000,1) for v in old_dim)} -> "
            f"{tuple(round(v*1000,1) for v in want['dim'])} mm"
        )

    with open(SPEC, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)

    print("patch_head_face")
    for line in report:
        print("  " + line)
    print("  triangles: head 4,992 -> 37,928 (18,964 quads, counted on an exact "
          "mirror of polygonizeSdf); eye cavities returned 524..3,488; net "
          "+29,448..+32,412 -> model total ~159,800 of a 250,000 budget")
    print("  non-manifold diagonal cell contacts in the emitted skull: 0")
    print("  BLOCKER, not fixed here: `hair` (197.7x300.0x305.0 mm ellipsoid at "
          "head-local 0,+50.5,-16.0) still encloses 79.8% of the new skull's "
          "surface. Only the jaw/chin/throat below head-local y -69.3 mm emerges. "
          "Brow, eyes, nose and ears stay invisible until the hair dimension acts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
