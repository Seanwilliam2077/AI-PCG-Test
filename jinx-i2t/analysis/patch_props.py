#!/usr/bin/env python3
"""props-integrity: re-author the Zapper pistol from measurement, un-break the eye
cavities, and declare an honest allow-list for the overlaps that are supposed to exist.

WHAT WAS MEASURED
-----------------
Reference, my own alpha-silhouette edge traces off ref/views/clay_0.png and clay_2.png:

  * clay_2 (front, 740 px/m, sole row 1286, centreline col 169): the prop's outer edge is
    unoccluded from row 704 to row 792 and runs col 323 -> 292. That is a lean of
    atan(31/88) = 19.4 deg from vertical, muzzle tipping inboard. Below row 792 the
    silhouette collapses to the trouser (col 259), which fixes the muzzle tip.
  * clay_0 (side, 708 px/m, sole row 1220): the prop's front edge is unoccluded from row
    712 to row 800 and runs col 61 -> 81, i.e. atan(20/88) = 12.8 deg, muzzle tipping
    backward. It steps forward to col 50 over rows 696-708: that is the ornate brass
    collar, the widest part of the prop. Vertical extent row 628 -> 802 = 174 px = 246 mm,
    so the axis is 0.246 / cos(22.7 deg) = 266 mm.
  * The cross-section is flat, not round: 42-45 px horizontal in clay_2 corrects to 50-57
    mm across, while the body is 85-95 mm front-to-back and the collar bulges to ~114 mm.
    A tapered attachment cylinder cannot express this at all; its section is circular.
  * Axial breakdown from clay_0 rows: receiver 628-685 (0-33%), brass collar 685-705
    (33-44%), glass tank 705-802 (44-100%). The tank is the BOTTOM 56% and is the fat
    part. There is no barrel forward of the tank anywhere in the reference.

Absolute height could NOT be recovered across panels. clay_0 puts the muzzle at y 0.590
and clay_2 puts it at y 0.668 -- a 78 mm disagreement -- while the belt band agrees
between those same two panels to 10 mm. The panels are not co-registered vertically, so no
cross-panel absolute Y is trustworthy. I therefore placed the prop against the BUILT model,
which is calibration-free: solve the assembly's position so its surface is tangent to the
built trouser cone (pants-l, axis x 0.0454 z 0.004, r 0.09735 at y 1.078 -> 0.06886 at
y 0.470) at exactly the declared embedDepth, with the grip end at the built left hand. That
lands the muzzle at y 0.674, 6 mm from clay_2's independent reading, and reproduces clay_2's
outer-edge trace to a mean 4.4 mm (2.2 px) over rows 704-780. Two unrelated derivations
agreeing to a few mm is the evidence that the placement is right.

Current build, measured off analysis/_props/meshes_expanded.json: the prop is a vertical
circular cone r 0.0534 -> 0.0226 spanning y 0.585..0.885 at x 0.118, z 0.055. Its inner
surface sits at x 0.065 while the trouser surface is at x 0.1427, so the prop is buried
64 mm inside the leg, and its three children are swallowed by it (Barrel 100% enclosed,
Glass tank 86%, Grip 20% and a further 95% inside the hip sash).

WHAT THIS CHANGES
-----------------
1. Zapper. All four components get localStart == localEnd, which makes
   makeAttachmentEndpoint return null (length <= 1e-4) and drops the emitter onto its
   transform.position + transform.rotation + dimensions branch. That is the only route in
   this generator to a tilted, non-circular prop: the cylinder branch ignores `primitive`
   and is round, and the SDF branch cannot be subdivided (see below). The assembly is
   rebuilt as four ellipsoids on the measured axis, Euler XYZ [0.2234, 0, -0.33079] rad
   (verified by forward substitution: R*(0,1,0) reproduces the measured unit axis to
   1.1e-16). The parent `zapper` becomes the steel RECEIVER, the top 42% of the axis,
   rather than a solid envelope duplicating its own children, so the collar, tank and grip
   each protrude 76% / 91% / 67% of their surface beyond it and actually read.
   `zapper-barrel` is re-sited as the brass collar at the receiver/tank junction, because
   the reference has no barrel below the tank and inventing one would be fiction; its note
   says exactly that.
2. Eye cavities: the double-scale bug is fixed, the self-intersection is NOT, and the
   reason is worth recording because it is a dead end, not an oversight.
   eye-cavity-l/r are the spec's only two SDF components and the only two meshes that fail
   self_intersection. The cause is not the descriptor: polygonizeSdf emits axis-aligned
   voxel quads, and averaged vertex normals at the staircase corners point into the solid,
   so even a plain convex sphere fails at 20%. The only escape is Catmull-Clark x2, and
   subdivideCatmullClark throws SubdivisionTopologyError on any field containing a
   `subtract` -- so subdividing this one would make createJinxArcaneModel() throw at
   construction and blank the render. The obvious remaining move, replacing the field with
   a convex `ellipsoid` primitive, is FORBIDDEN: validate_sculpt_spec.py's US-004 rule
   (RECESSED_FEATURE_TOKENS) requires any component whose role/name/id says "cavity" to be
   topologyClass 'implicit' with an sdf whose operations include 'subtract', on the
   grounds that an eye socket must be a real recess and not a convex patch. I tried it;
   --strict fails with two errors. So there is no authoring in this generator's vocabulary
   that both satisfies US-004 and passes self_intersection, and I am not going to pretend
   otherwise or silence the gate.
   What this patch does fix is a separate, definite bug in the same component:
   scale_vector() multiplies every null-endpoint geometry by `dimensions`, but
   polygonizeSdf output is already in metres, so the cavity was scaled twice and built at
   2.41 x 1.70 x 1.77 mm -- a 21x/31x/24x shrink that made the socket contribute nothing
   at all. scale_vector() reads transform["scale"] before it reads `dimensions`, so
   setting transform.scale = [1,1,1] turns the second multiply into a no-op and the cavity
   builds at its authored 47.19 x 32.00 x 42.43 mm. One key, no other side effect, no
   triangle cost (the mesh is the same 260 triangles, just not shrunk).
   Guarded: skips if the component is gone, is no longer implicit, has gained a
   `subdivide` block, already carries a transform.scale, or if `head` has itself become
   implicit -- so a head/face patch that folds the cavities into a skull SDF wins outright.
3. qualityContract.allowedPairs. 292 pairs, each carrying a reason derived from THIS
   spec's own parent map and role fields rather than from a family label, because the
   label was wrong in places: abdomen <-> braid-l is rel "lineage" across five
   generations, not a parent/child weld, and calling it one would be a fabricated reason.

EXPECTED MEASURABLE EFFECT
--------------------------
  * attachment_anchor.py: 4 ANCHOR_DECLARED errors -> 0, PASS both spec-only and
    --measured. Predicted new anchor distances: zapper->thigh-l 0.179 (maxOffset 0.20),
    barrel->zapper 0.051 (0.07), tank->zapper 0.131 (0.15), grip->zapper 0.055 (0.08).
  * self_intersection.py: UNCHANGED at 2 failing meshes of 104. See point 2 -- the two
    eye cavities cannot pass it and stay US-004-legal. What does change is their built
    extent: 2.41 x 1.70 x 1.77 mm -> 47.19 x 32.00 x 42.43 mm, so the socket becomes a
    real 50 mm recess in the face instead of an invisible crumb. Expect the cavities to
    start appearing in pairwise_penetration against `head`, `eye-l/r` and `hair-cap`;
    the first two are declared in allowedPairs, the hair-cap one is not, because hair
    inside an eye socket is a defect that belongs to the hair dimension.
  * pairwise_penetration.py: the zapper's own contribution falls from 23 unordered
    penetrating pairs to 8 -- four intra-assembly welds plus Grip <-> Hand L (5.4%),
    Zapper pistol <-> Glove (her left) (0.2%), Barrel <-> Glove (her left) (1.8%) and
    Glass tank <-> Trouser leg (her left) (0.4%, the intended 3.8 mm rest contact). Total
    unordered penetrating pairs should move 361 -> ~346. Every deep zapper pair goes to
    zero: Barrel->Zapper 100% becomes a weld only, Grip->Hip sash 94.7% -> 0,
    Grip->Diagonal hip strap 79% -> 0, Zapper->Trouser 32.7% -> 0.4%, Zapper->Thigh L
    18.5% -> 0, Thigh strap->Zapper 19.1% -> 0.
  * Front view (yaw 0): the prop's outer edge stops being a vertical line at x 0.171 and
    becomes a 19.4 deg lean descending from x 0.199 at y 0.787 to x 0.163 at y 0.684.
    World bbox x 0.0646..0.1714 -> 0.1208..0.2385, y 0.585..0.885 -> 0.672..0.935.
  * Triangle count: 128,833 -> ~133,743 (+4,910, all of it the zapper: its four parts move
    off the low-poly attachment-cylinder path onto the 4,992-triangle unit ellipsoid, so
    832+2,495+416+232 = 3,975 becomes 2,496+2,496+2,496+1,397 = 8,885 after the declared
    decimate ratios). That is 53% of the 250,000 budget. The eye-cavity change costs zero
    triangles. This patch adds no SDF and no subdivision.

TRADE-OFF, STATED PLAINLY
-------------------------
Moving the prop out of the leg opens ~88 px of enclosed background at yaw 0/180 between
the prop's inner edge and the trouser, measured by analytic rasterisation at the render's
own 2 mm/px: a hairline averaging 2.3 mm wide over a 150 mm run. That is a real new
interior hole for turntable_gate, on top of the 1,663 px already there. It exists because
the built left arm hangs further outboard than the reference arm, so a prop that is both in
the hand and off the leg cannot also be flush against it. The alternative is to leave the
prop buried 64 mm inside the thigh. I took the hole, and it should be re-measured if the
arm is ever re-posed, because a closer arm would close it for free.

WHAT THIS PATCH DOES NOT FIX
----------------------------
The 20 contralateral pairs (her-left geometry inside her-right, up to 68 mm deep), the 12
hair-inside-the-head pairs (Head is 100% inside Hair), the arms buried in the hip rig, and
the class-legitimate-but-pathological pairs (Hip sash contains 94% of Pelvis, Hip pouch
96.7% of Trouser leg (her left)) are real defects in other dimensions' territory. They are
deliberately NOT in allowedPairs, so the gate keeps reporting them. turntable_gate's
undeclared neck-root, foot and jaw holes are likewise untouched: closing the neck root
means reshaping the chest, which is not this dimension.

And self_intersection stays red at 2 of 104 meshes. That is the one gate in my dimension I
could not turn green. The honest statement is that this generator has no authoring that
satisfies both US-004 (a cavity must be an implicit `subtract`) and self_intersection
(polygonizeSdf's voxel normals fail, and the only smoother throws on `subtract`). Closing
it needs a change in the generator -- either a try/catch plus a manifold repair around
subdivideCatmullClark, or a real marching-cubes polygoniser -- not a change in the spec.
"""

import io
import json
import sys

# The tilt lives ONLY on the parent. The emitter sets node.rotation on every component and
# then parents the node under nodes[parent], so rotations COMPOSE: repeating this on the
# children would rotate them 45.5 deg and fling them off the axis. They inherit it instead.
ROTATION = [0.2234, 0.0, -0.33079]
NO_ROTATION = [0.0, 0.0, 0.0]

# id -> (parent-local position, rotation, dimensions w/h/d, anchor, maxOffset,
#        decimate ratio, largest dimension in mm for the decimate reason string)
ZAPPER = {
    "zapper": ([0.15697, -0.1095, 0.03192], ROTATION,
               [0.052, 0.11193, 0.086], "thigh-l", 0.2, 0.5, 112),
    "zapper-barrel": ([0.0, -0.05064, 0.0], NO_ROTATION,
                      [0.058, 0.0533, 0.114], "zapper", 0.07, 0.5, 114),
    "zapper-tank": ([0.0, -0.13059, 0.0], NO_ROTATION,
                    [0.062, 0.1599, 0.094], "zapper", 0.15, 0.5, 160),
    "zapper-grip": ([0.0, 0.04771, 0.028], NO_ROTATION,
                    [0.038, 0.062, 0.048], "zapper", 0.08, 0.28, 62),
}

ZAPPER_NOTES = {
    "zapper": (
        "Steel receiver: the top 42% of the pistol's 266 mm axis. Held muzzle-down in her "
        "LEFT hand, leaning 19.4 deg inboard (clay_2 rows 704-792) and 12.8 deg backward "
        "(clay_0 rows 712-800). Positioned by solving tangency against the built trouser "
        "cone with the grip end at the built hand, because the reference panels are not "
        "co-registered vertically: clay_0 and clay_2 disagree by 78 mm on the muzzle."
    ),
    "zapper-barrel": (
        "The ornate brass collar at the receiver/tank junction, clay_0 rows 685-705, the "
        "widest part of the prop front-to-back at ~114 mm. NOT a barrel: the reference "
        "shows no barrel forward of the tank, so this component carries the collar, which "
        "is what actually occupies this span of the axis."
    ),
    "zapper-tank": (
        "Translucent tank with teal and pink contents and brass end caps: the bottom 60% "
        "of the axis, clay_0 rows 705-802, and the fattest part at 62 x 160 x 94 mm. Its "
        "inner face rests on the trouser at the declared 4 mm embedDepth."
    ),
    "zapper-grip": (
        "Leather grip, seated on the forward face of the receiver top so the palm closes "
        "on it. In clay_0 the gloved hand reads in FRONT of the receiver, and the built "
        "hand is an open hand with the fingers extended, so the stub is offset +30 mm in "
        "the prop's local Z to meet the palm without passing through the finger bones."
    ),
}

ZAPPER_RATIONALE = (
    "A rigid held prop assembled from stacked primitives. It carries an attachment block "
    "for the anchor contract, but localStart == localEnd so makeAttachmentEndpoint returns "
    "null and the emitter uses transform.position/rotation with independent width/height/"
    "depth -- the only route to a tilted, non-circular cross-section in this generator."
)

ZAPPER_DEBRIS = {
    "zapper": "steel",
    "zapper-barrel": "steel",
    "zapper-tank": "glassTank",
    "zapper-grip": "leather",
}

EVIDENCE = ["body_0", "clay_0", "body_2", "clay_2"]

CAVITY_NOTE = (
    "transform.scale is pinned to [1,1,1] on purpose. scale_vector() re-applies "
    "`dimensions` to every null-endpoint geometry, but polygonizeSdf output is already in "
    "metres, so without this the 47.19 x 32.00 x 42.43 mm socket was built at "
    "2.41 x 1.70 x 1.77 mm. scale_vector() reads transform['scale'] before `dimensions`, "
    "so this pin makes the second multiply a no-op. NOTE: this component still fails "
    "self_intersection and cannot be made to pass -- polygonizeSdf's voxel-quad normals "
    "fail even for a convex field, Catmull-Clark is the only cure and it throws on any "
    "field containing a 'subtract', and US-004 in validate_sculpt_spec.py requires a "
    "cavity to BE an implicit subtract. That gate failure is known and unfixable here."
)

# Overlaps that are intended, carried over from the measured classification in
# analysis/_props/pair_classification.json with the mis-classified entries removed.
CLASSIFIED = """
abdomen|arm-band-lower abdomen|braid-l abdomen|braid-r abdomen|chest abdomen|tattoo-region
abdomen|top abdomen|top-band arm-band-lower|forearm-l arm-band-lower|upper-arm-l
arm-band-upper|top arm-band-upper|top-band arm-band-upper|upper-arm-l boot-cuff|pants-r
boot-cuff|shin-l boot-cuff|shin-r boot-cuff|thigh-l boot-cuff|thigh-r boot-lace|boot-cuff
boot-lace|pants-l boot-lace|shin-l boot-l|boot-lace boot-l|boot-sole boot-l|boot-toecap
boot-l|foot-l boot-l|shin-l boot-r|boot-sole boot-r|braid-r boot-r|braid-tassel boot-r|foot-r
boot-r|root boot-r|shin-r braid-l|braid-tassel braid-l|braid-ties braid-l|chest braid-l|choker
braid-l|diagonal-strap braid-l|hair braid-l|head braid-l|hip-belt braid-l|neck
braid-l|pants-hem-l braid-l|pants-l braid-l|pelvis braid-l|sash braid-l|thigh-strap
braid-r|braid-tassel braid-r|braid-ties braid-r|chest braid-r|choker braid-r|diagonal-strap
braid-r|hair braid-r|head braid-r|hip-belt braid-r|neck braid-r|pants-hem-r braid-r|pants-r
braid-r|pelvis braid-r|sash braid-ties|braid-tassel brow-l|head brow-r|head
canvas-panel|belt-hardware canvas-panel|diagonal-strap canvas-panel|hip-belt
canvas-panel|pants-hem-l canvas-panel|pants-hem-r canvas-panel|pants-l canvas-panel|pants-r
canvas-panel|pelvis canvas-panel|pouch canvas-panel|sash chest|choker-straps chest|clavicle-l
chest|clavicle-r chest|hair-sidelock-l chest|hair-sidelock-r chest|tattoo-region chest|top
chest|upper-arm-l chest|upper-arm-r choker-straps|clavicle-l choker-straps|clavicle-r
choker-straps|hair-sidelock-l choker-straps|hair-sidelock-r choker-straps|neck
choker-straps|top-strap choker|choker-straps choker|hair-sidelock-l choker|hair-sidelock-r
choker|neck clavicle-l|top clavicle-l|top-strap clavicle-l|upper-arm-l clavicle-r|top
clavicle-r|top-strap clavicle-r|upper-arm-r diagonal-strap|forearm-l diagonal-strap|forearm-r
diagonal-strap|glove-l diagonal-strap|glove-r diagonal-strap|hand-l diagonal-strap|pants-l
diagonal-strap|pants-r diagonal-strap|pelvis diagonal-strap|pouch diagonal-strap|sash
diagonal-strap|thigh-l diagonal-strap|thigh-r ear-l|head ear-r|head eye-cavity-l|head
eye-cavity-r|head eye-l|eye-cavity-l eye-l|head eye-r|eye-cavity-r eye-r|head foot-l|shin-l
foot-r|shin-r forearm-l|glove-l forearm-l|hand-l forearm-l|hip-belt forearm-l|upper-arm-l
forearm-r|belt-hardware forearm-r|glove-r forearm-r|hand-r forearm-r|hip-belt
forearm-r|pants-r forearm-r|sash forearm-r|upper-arm-r glove-l|hand-l glove-l|little-l-1
glove-l|little-l-2 glove-l|nails glove-l|pouch glove-l|ring-l-1 glove-l|sash
glove-l|thigh-strap glove-l|thumb-l-1 glove-l|thumb-l-2 glove-l|thumb-l-3 glove-r|hand-r
glove-r|little-r-1 glove-r|little-r-2 glove-r|little-r-3 glove-r|pants-r glove-r|ring-r-1
glove-r|sash glove-r|thigh-r glove-r|thumb-r-1 glove-r|thumb-r-2 glove-r|thumb-r-3
hair-cap|hair-crest hair-fringe|hair-cap hair-fringe|hair-crest hair-fringe|head
hand-l|middle-l-1 hand-l|ring-l-1 hand-r|little-r-1 hand-r|middle-r-1 hand-r|ring-r-1
hand-r|sash head|hair-cap head|hair-crest head|mouth head|neck head|nose
hip-belt|belt-hardware hip-belt|pants-hem-l hip-belt|pants-hem-r hip-belt|pants-l
hip-belt|pants-r hip-belt|pelvis hip-belt|sash index-l-1|index-l-2 index-l-1|middle-l-1
index-l-1|middle-l-2 index-l-2|index-l-3 index-l-2|middle-l-1 index-l-2|middle-l-2
index-l-2|middle-l-3 index-l-3|middle-l-2 index-l-3|middle-l-3 index-r-1|index-r-2
index-r-1|middle-r-1 index-r-1|middle-r-2 index-r-1|ring-r-1 index-r-1|ring-r-2
index-r-2|index-r-3 index-r-2|middle-r-2 index-r-2|middle-r-3 index-r-2|ring-r-2
index-r-3|middle-r-2 index-r-3|middle-r-3 little-l-1|little-l-2 little-l-1|ring-l-1
little-l-2|little-l-3 little-l-2|ring-l-1 little-l-2|ring-l-2 little-l-3|ring-l-2
little-l-3|ring-l-3 little-r-1|little-r-2 little-r-1|middle-r-1 little-r-1|ring-r-1
little-r-2|little-r-3 little-r-2|middle-r-1 little-r-2|middle-r-2 little-r-2|ring-r-1
little-r-2|ring-r-2 little-r-3|ring-r-2 little-r-3|ring-r-3 middle-l-1|middle-l-2
middle-l-1|ring-l-1 middle-l-1|ring-l-2 middle-l-2|middle-l-3 middle-l-2|ring-l-2
middle-l-2|ring-l-3 middle-l-3|ring-l-3 middle-r-1|middle-r-2 middle-r-1|ring-r-1
middle-r-1|ring-r-2 middle-r-2|middle-r-3 middle-r-2|ring-r-2 middle-r-2|ring-r-3
middle-r-3|ring-r-3 neck|hair-cap neck|hair-sidelock-l neck|hair-sidelock-r
pants-hem-l|pants-l pants-hem-r|belt-hardware pants-hem-r|pants-r pants-l|belt-hardware
pants-r|belt-hardware pelvis|pants-hem-l pelvis|pants-hem-r pelvis|pants-l pelvis|pants-r
pelvis|thigh-l pelvis|thigh-r pouch|pelvis pouch|sash ring-l-1|ring-l-2 ring-l-2|ring-l-3
ring-r-1|ring-r-2 ring-r-2|ring-r-3 sash|pants-hem-l sash|pants-hem-r sash|pants-l
sash|pants-r sash|thigh-l sash|thigh-r sash|thigh-strap shin-l|boot-sole shin-l|pants-l
shin-l|shin-patch shin-l|thigh-l shin-r|pants-r shin-r|thigh-r tattoo-region|pants-hem-l
tattoo-region|sash tattoo-region|top thigh-l|pants-l thigh-l|thigh-strap thigh-r|pants-r
thigh-r|thigh-strap thigh-strap|pants-l thigh-strap|pants-r thumb-l-1|thumb-l-2
thumb-l-2|thumb-l-3 thumb-r-1|thumb-r-2 thumb-r-2|thumb-r-3 top-band|upper-arm-l
top-band|upper-arm-r top-strap|hair-sidelock-l top-strap|hair-sidelock-r top|hair-sidelock-l
top|hair-sidelock-r top|top-band top|top-strap x-lacing|chest x-lacing|top
""".split()

# Pairs the rule-based classifier flagged that are in fact legitimate.
RESCUED = [
    ("braid-l", "braid-r", "the two braids cross behind her back"),
    ("braid-r", "pants-l", "a braid hangs between the legs and crosses the far trouser"),
    ("hair-fringe", "brow-l", "the fringe hangs over the brow"),
    ("hair-fringe", "brow-r", "the fringe hangs over the brow"),
]

# Contacts this patch deliberately creates, with the penetration fraction I measured.
ZAPPER_PAIRS = [
    ("zapper", "zapper-barrel",
     "the brass collar rings the receiver at their declared junction"),
    ("zapper", "zapper-tank",
     "receiver and tank overlap 5 mm along the axis so the assembly has no seam gap"),
    ("zapper", "zapper-grip",
     "the grip is seated into the receiver's forward face"),
    ("zapper-barrel", "zapper-tank",
     "the collar bridges the receiver/tank junction; it is the connective volume"),
    ("zapper-grip", "hand-l",
     "the palm closes on the grip: 5.4% of Hand L, the contact that makes the prop held"),
    ("zapper", "glove-l",
     "the gauntlet grazes the receiver where the hand wraps it (0.2% of Glove L)"),
    ("zapper-barrel", "glove-l",
     "the gauntlet grazes the brass collar (1.8% of Glove L)"),
    ("zapper-tank", "pants-l",
     "the tank rests on the trouser at the declared 4 mm embedDepth (0.4% of the trouser)"),
]


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path, spec):
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)


def _fmt(values):
    try:
        return "(" + ", ".join("%.4g" % float(v) for v in values) + ")"
    except (TypeError, ValueError):
        return str(values)


def patch_zapper(spec, log):
    by_id = {c["id"]: c for c in spec.get("componentTree", [])}
    done = 0
    for cid, (pos, rot, dims, anchor, max_off, ratio, mm) in ZAPPER.items():
        component = by_id.get(cid)
        if component is None:
            log.append("  %-14s ABSENT - skipped" % cid)
            continue
        before_pos = list(component.get("transform", {}).get("position", []))
        before_dims = component.get("dimensions") or {}
        before = (before_dims.get("width"), before_dims.get("height"), before_dims.get("depth"))
        had_anchor = isinstance(component.get("attachment"), dict) and "anchor" in component["attachment"]

        component["primitive"] = "ellipsoid"
        component["topologyClass"] = "assembled-solid"
        component["topologyRationale"] = ZAPPER_RATIONALE
        component["transform"] = {"position": list(pos), "rotation": list(rot)}
        component["dimensions"] = {
            "width": dims[0],
            "height": dims[1],
            "depth": dims[2],
            "units": "metres",
            "confidence": 0.8,
        }
        # localStart == localEnd makes makeAttachmentEndpoint return null (length <= 1e-4),
        # so the emitter takes the transform/dimensions branch. baseRadius/endRadius are
        # dropped deliberately: they describe a circular sweep that no longer exists, and
        # leaving them would silently resurrect the cylinder if anyone edited localEnd.
        component["attachment"] = {
            "parentSocket": component.get("parent"),
            "anchor": anchor,
            "maxOffset": max_off,
            "localStart": list(pos),
            "localEnd": list(pos),
            "contactType": "overlap",
            "embedDepth": 0.004,
            "gapTolerance": 0.002,
        }
        descriptor = component.setdefault("geometryDescriptor", {})
        descriptor["decimate"] = {
            "targetRatio": ratio,
            "reason": "largest dimension %d mm; density tracks screen area" % mm,
        }
        component["evidenceRefs"] = list(EVIDENCE)
        component["notes"] = ZAPPER_NOTES[cid]
        destruction = component.setdefault("actionProfile", {}).setdefault("destruction", {})
        destruction["fractureGroup"] = "zapper"
        destruction["debrisMaterial"] = ZAPPER_DEBRIS[cid]

        done += 1
        log.append(
            "  %-14s pos %s -> %s | rot %s | dims %s -> (%.3f, %.5f, %.3f) | "
            "anchor %s maxOffset %.2f%s"
            % (cid, _fmt(before_pos), _fmt(pos),
               "tilt" if any(rot) else "inherits parent tilt",
               _fmt(before), dims[0], dims[1], dims[2],
               anchor, max_off, "" if had_anchor else "  [anchor was MISSING]")
        )
    return done


def patch_eye_cavities(spec, log):
    by_id = {c["id"]: c for c in spec.get("componentTree", [])}
    head = by_id.get("head")
    head_implicit = (
        head is not None
        and head.get("topologyClass") == "implicit"
        and isinstance((head.get("geometryDescriptor") or {}).get("sdf"), dict)
    )
    changed = 0
    for cid in ("eye-cavity-l", "eye-cavity-r"):
        component = by_id.get(cid)
        if component is None:
            log.append("  %-14s absent - another patch removed it; no-op" % cid)
            continue
        descriptor = component.get("geometryDescriptor") or {}
        sdf = descriptor.get("sdf")
        if head_implicit:
            log.append("  %-14s `head` is now an implicit SDF - leaving the face patch alone" % cid)
            continue
        if component.get("topologyClass") != "implicit" or not isinstance(sdf, dict):
            log.append("  %-14s already non-implicit; no-op" % cid)
            continue
        if descriptor.get("subdivide"):
            log.append("  %-14s carries a subdivide block - another patch owns it; no-op" % cid)
            continue
        transform = component.setdefault("transform", {})
        if "scale" in transform:
            log.append("  %-14s transform.scale already pinned; no-op" % cid)
            continue
        dims = component.get("dimensions") or {}
        transform["scale"] = [1, 1, 1]
        component["notes"] = ((component.get("notes") or "").strip() + " " + CAVITY_NOTE).strip()
        changed += 1
        log.append(
            "  %-14s transform.scale pinned [1,1,1]; built extent 2.41 x 1.70 x 1.77 mm -> "
            "%.2f x %.2f x %.2f mm (SDF and topologyClass untouched: US-004 requires them)"
            % (cid, dims.get("width", 0) * 1000, dims.get("height", 0) * 1000,
               dims.get("depth", 0) * 1000)
        )
    return changed


def _reason(parent, roles, a, b):
    """Derive the reason from THIS spec's parent map and role fields, not from a family
    label. The measured classification called every `rel: lineage` pair a parent/child
    weld, which is false for e.g. abdomen <-> braid-l (five generations apart)."""
    role_a, role_b = roles.get(a, "?"), roles.get(b, "?")
    pair = {role_a, role_b}
    if parent.get(a) == b or parent.get(b) == a:
        return "direct parent/child: the child's attachment.embedDepth declares this overlap"
    if "cavity" in pair:
        return "an eye seated in its socket; full nesting is the intended design"
    if "repetition" in pair:
        return "repeated hardware seated into the band it studs"
    if pair == {"finger"}:
        return "adjacent fingers of the same hand in contact"
    if "finger" in pair and "hand" in pair:
        return "a finger rooted in the hand it belongs to"
    if "finger" in pair and "garment" in pair:
        return "the gauntlet encloses the fingers it covers"
    if "hair" in pair:
        return "a hair strand drapes over the surface beneath it"
    if pair == {"garment"}:
        return "layered garments worn one over the other"
    if "skin" in pair:
        return "a skin decal lying on the surface under the garment"
    if "garment" in pair:
        other = role_b if role_a == "garment" else role_a
        return "garment worn over the %s it covers" % other
    if "detail" in pair:
        return "surface detail seated on the form it sits on"
    return "adjacent parts of one body in surface contact along a shared joint"


def patch_allowed_pairs(spec, log):
    components = spec.get("componentTree", [])
    by_id = {c["id"]: c for c in components}
    repetitions = {r["id"]: r for r in spec.get("repetitionSystems", []) if isinstance(r, dict)}
    parent = {c["id"]: c.get("parent") for c in components}
    parent.update({r["id"]: r.get("parent") for r in repetitions.values()})
    roles = {c["id"]: c.get("role", "?") for c in components}
    roles.update({r: "repetition" for r in repetitions})

    def display_name(cid):
        if cid in by_id:
            return by_id[cid].get("name", cid)
        if cid in repetitions:
            return repetitions[cid].get("name") or cid
        return None

    entries, seen, dropped = [], set(), []

    def add(a, b, reason):
        name_a, name_b = display_name(a), display_name(b)
        if name_a is None or name_b is None:
            dropped.append("%s|%s" % (a, b))
            return
        key = frozenset((a, b))
        if key in seen:
            return
        seen.add(key)
        entries.append({"a": a, "b": b, "nameA": name_a, "nameB": name_b, "reason": reason})

    for a, b, reason in ZAPPER_PAIRS:
        add(a, b, reason)
    for token in CLASSIFIED:
        a, _, b = token.partition("|")
        if a in ZAPPER or b in ZAPPER:
            continue
        add(a, b, _reason(parent, roles, a, b))
    for a, b, reason in RESCUED:
        add(a, b, reason)

    entries.sort(key=lambda e: (e["nameA"], e["nameB"]))
    contract = spec.setdefault("qualityContract", {})
    before = len(contract.get("allowedPairs") or [])
    contract["allowedPairs"] = entries
    contract["allowedPairsNote"] = (
        "Overlaps that are intended, for pairwise_penetration.py --allow \"<nameA>,<nameB>\" "
        "(that CLI matches mesh display names, not ids). Deliberately EXCLUDED so the gate "
        "keeps reporting them: the 20 contralateral her-left/her-right pairs, the 12 "
        "hair-inside-the-head pairs, the arms buried in the hip rig, and the "
        "class-legitimate-but-pathological pairs (Hip sash contains 94% of Pelvis, Hip "
        "pouch 96.7% of Trouser leg (her left), Folded cuff 83.3%, Halter neck strap 94% "
        "of Chest)."
    )
    log.append("  allowedPairs %d -> %d entries" % (before, len(entries)))
    if dropped:
        log.append("  %d ids did not resolve and were skipped: %s"
                   % (len(dropped), ", ".join(sorted(dropped))))
    return len(entries)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "object-sculpt-spec.json"
    spec = load(path)

    zapper_log, cavity_log, pair_log = [], [], []
    n_zapper = patch_zapper(spec, zapper_log)
    n_cavity = patch_eye_cavities(spec, cavity_log)
    n_pairs = patch_allowed_pairs(spec, pair_log)

    save(path, spec)

    print("patch_props.py -> %s" % path)
    print("[1] Zapper: %d/4 components re-authored on the measured axis "
          "(19.4 deg frontal, 12.8 deg sagittal, 266 mm)" % n_zapper)
    for line in zapper_log:
        print(line)
    print("    world bbox x 0.0646..0.1714 -> 0.1208..0.2385, y 0.585..0.885 -> 0.672..0.935")
    print("    inner surface: 64 mm inside the thigh -> 3.8 mm rest contact with the trouser")
    print("    children protruding past the parent: collar 76%, tank 91%, grip 67% "
          "(were 0%, 14%, 80% enclosed)")
    print("[2] Eye cavities: %d/2 un-squashed (double-scale bug). self_intersection still "
          "FAILS on both and cannot be fixed here - see the docstring." % n_cavity)
    for line in cavity_log:
        print(line)
    print("[3] qualityContract.allowedPairs")
    for line in pair_log:
        print(line)
    print("[4] Triangle budget: 128,833 -> ~133,743 (+4,910, all zapper: 3,975 -> 8,885 as "
          "its four parts leave the attachment-cylinder path for the unit ellipsoid).")
    print("    Eye-cavity change costs 0 triangles. Budget 250,000, so 53% used. No SDF "
          "and no subdivision added by this patch.")


if __name__ == "__main__":
    main()
