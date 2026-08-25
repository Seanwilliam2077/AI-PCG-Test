"""Rebuild the boots, hands and gloves as measured solids instead of stacked tubes.

WHAT WAS MEASURED
-----------------
Reference panels `ref/views/clay_2.png`, `body_2.png`, `clay_0.png`, `body_4.png`, each
scaled by its own alpha bbox (top = 1.72 m, sole = 0), which puts clay_2 at 742.44 px/m.

Boots, her right (planted) boot, front view, width above its own sole:
    y 0.020 -> 102 mm, 0.036 -> 116, 0.052 -> 117, 0.085 -> 121 (max),
    y 0.117 ->  96 mm, 0.129 ->  93 (ankle minimum), 0.153 -> 83, 0.166 -> 81.
  The reference boot is WIDEST AT THE SOLE and NARROWEST AT THE ANKLE, 121 -> 93 mm.
  The built boot was a cone that ran the other way, 118.7 mm at the bottom to 137.7 at
  the top, with no fore-aft direction at all (a circular cross-section, so depth was
  forced equal to width: 118.7 mm against a measured 235 mm sole).
Boot height sole -> cuff top: 248 mm (three independent probes agreeing to +/-7 mm).
Sole length 235 mm; toe +177 mm ahead of the shin axis, heel -58 mm behind it (3.05:1).
Depth at the ankle (y 0.13): 127 mm.
Collar: a folded, floppy collar with a pointed outboard wing. Its outboard reach from the
  boot centre-line (clay_2, her right boot, centre col 128) is 118 mm at y 0.18, 116 at
  0.20, 111 at 0.22, 102 at 0.24, 93 at 0.26, 82 at 0.28, 71 at 0.30 -- i.e. it flares up
  and out and is still 71 mm proud where the shaft is 93 mm wide in total.
The built model put the sole slab at y 0.249-0.285 (a disc at mid-calf), the cuff at
  0.539-0.601 (a ring at the knee, level with `kneeL`), the lacing at 0.339-0.539 as a
  24 mm round rod, and gave `boot-r` none of those four parts at all.

Hands, her right hand, body_2 (her left hand is occluded by the zapper):
  wrist y 0.936 and 42 mm wide; knuckle line (glove hem) y 0.869; fingertips y ~0.838;
  hand width across the knuckles 57 mm; fist depth 65-73 mm read off body_4;
  exposed fingerless mass 51 mm wide x 45 mm tall, SVD principal axis (-0.83, +0.56),
  64 mm along that axis -- ONE curled wedge, not five rods. Glove top y 1.108.
The built model had 30 phalanges of identical 19.0 mm diameter spaced 11.0 mm apart, so
  adjacent fingers interpenetrated by 8 mm (42% of a diameter), and a `nails` slab
  45 x 20 x 26.5 mm sitting at the KNUCKLE line, on the left hand only.

WHY THE 30 PHALANGES ARE COLLAPSED RATHER THAN RE-SPLAYED
---------------------------------------------------------
Measured on `out/clay/render_yaw0.png` and `render_yaw90.png` at the scoreboard's own
500 px/m: the fifteen phalanges of one hand contribute 450 px of silhouette beyond the
arm (rows 455-495, cols 346-371) -- 30 px each -- and that coverage is 1-3 px islands,
not a solid mass (row 477 reads `347-350 353-354 356-357 360-361 364-365 367-367`). At
yaw 90 the whole bundle projects INSIDE a solid silhouette run: silhouette contribution
zero. The reference's exposed fingers are 274 px at the same scale as one clean wedge.
So 30 components, 30 of the build's 104 draw calls and 3,720 triangles buy 450 px of
fragmented, self-intersecting silhouette in the only view that sees them, against 274 px
for the correct answer. Fixing the splay cannot help: the correct reference form is a
closed, curled fist (plainly visible in body_4), not five separated rods at any spacing.
They are deleted and replaced by one implicit fist inside the glove plus one four-lobed
skin mass below the glove hem.

THE CHANGE
----------
boot-l, boot-r, glove-l, glove-r, hand-l, hand-r become `topologyClass: "implicit"` with
a `geometryDescriptor.sdf`, which is the only route in this generator to a shape that is
not a swept circular cylinder. Each boot is a smooth-union of outsole slab, heel block,
forefoot, toe cap, ankle, shaft, collar and outboard wing; each glove is a seven-sphere
sleeve along the real forearm axis plus a fist ellipsoid; each hand is four curled
fingertip lobes. `boot-sole` and `boot-cuff` are deleted because their form is now inside
the boot field, and their two component slots pay for `boot-toecap-r` and `boot-lace-r`,
which give the right boot the toe cap and lacing it never had. `nails` moves from the
knuckle line to the fingertips and gains a right-hand twin. The two `foot-*` skin barrels
(152 mm diameter, larger than the boots meant to contain them) shrink to 56 mm so they
stop punching through.

Three emitter behaviours forced specific choices and are worth recording, because each
one passes strict validation while being wrong:
  * `transform.scale` -- and, failing that, `dimensions` -- is multiplied into the vertex
    data of any component WITHOUT an attachment, implicit ones included. An SDF authored
    in metres therefore needs scale (1,1,1). `eye-cavity-l` in this same spec does not do
    this: its 25.2 mm sphere is multiplied by its 47 mm dimensions and emits a 1.2 mm
    speck. That is the head dimension's bug, not fixed here, but it is the proof.
  * that same `transform.scale` is what `derive_envelope_radius` reads to size a bone's
    skin envelope, and `hand-l`/`hand-r` ARE bone components. Setting scale (1,1,1) there
    would give the hand bones a 600 mm envelope instead of the 30 mm fallback every bone
    uses today. So the two hands drop `dimensions` entirely instead (absent dimensions and
    absent scale both fall through to (1,1,1) in the emitter, and to the 0.05 m fallback
    in the rigger); their real extents are recorded in `topologyRationale`.
  * `subdivide` is NOT available on this path. Catmull-Clark after `polygonizeSdf` is what
    would turn the voxel staircase into a smooth sculpt, but `validate_subdivision_budget`
    rejects `implicit sdf` outright ("subdivision is unsupported for this generator path"),
    so the surface stays blocky at the sampling grid and resolution is the only lever.

Resolutions were chosen by counting the exact face output of a numpy port of
`polygonizeSdf`, not estimated: boot 48 (4.1 x 6.5 x 5.8 mm voxels, 2.0 x 3.3 x 2.9 px at
the scoreboard's 500 px/m), glove 36, hand 20. Bounds on the boots are deliberately set so
that a grid LINE, not a voxel centre, lands exactly on y = 0, which is what keeps the sole
flat on the floor instead of dipping a random fraction of a voxel below it.

TRIANGLE COST
-------------
Measured with that same port for the implicit parts, and from the tier's own segment counts
for the primitive ones. The port is checked against a component this build has already
executed: on `eye-cavity-l`'s existing SDF it predicts 1,744 triangles, and 262 after that
component's own 0.15 decimation, against the 260 `out/_tris.json` actually recorded -- 0.8%. Added: 2 x 15,228 (boots) + 2 x 8,540 (gloves) + 2 x 2,704 (hands)
+ 2 x 1,397 (toe caps) + 2 x 864 (lace panels) + 2 x 749 (nail clusters) = 58,964.
Removed: 3,720 (30 phalanges) + 832 (boot-sole) + 416 (boot-cuff) + 1,664 (the two boot
cones) + 1,664 (the two glove tubes) + 464 (the two hand cones) + 1,397 + 416 + 259 (the
single-sided toe cap, lace and nails being rebuilt) = 10,832. Net about +48,100, taking
the build from 128,833 to roughly 177,000 against the 250,000 budget, and componentTree
entries from 103 to 74, i.e. draw calls from 104 to about 75 against 160. Nothing here is
decimated: a quadric collapse on a voxel staircase is unverified in this build, so the
sampling grids alone carry the cost.

EXPECTED MEASURABLE EFFECT
--------------------------
Check these on a re-render:
  * Front view, her right boot, width above the floor: currently 119 mm at y 0.02 rising
    to 127 mm at y 0.13 (taper inverted). Should become ~114 mm at y 0.02 falling to
    ~94 mm at y 0.13 -- the sign of dW/dy flips, and the 121:93 reference ratio of 1.30
    should be reproduced within ~8 mm RMS over the fifteen sampled bands.
  * Side view (yaw 90), boot fore-aft extent at the sole: currently 118.7 mm. Should
    become ~240 mm, with the toe reaching z ~+0.177 and the heel z ~-0.058 relative to
    the ankle, i.e. a toe:heel ratio near 3:1 instead of the present 1:1.
  * `boot-sole` and `boot-cuff` disappear from the mid-calf and knee: no clay pixel of
    either boot should exist above y 0.30 any more except the collar wing.
  * Model bounding box floor: unchanged or better. Both boot fields emit their lowest
    quad exactly on their own y = 0 grid line, so the right boot's sole lands on 0.000
    and the left on 0.047; nothing here can push the box below the present -0.013.
  * Hands at yaw 0: the 1-3 px speckle in rows 455-495 becomes one solid run per row.
    Silhouette area beyond the arm should move from 450 px of fragments toward the
    reference's 274 px of solid wedge, and draw calls fall by 29.
  * Triangle count rises by roughly 48,100 and draw calls fall by about 29.

NOT FIXED, AND WHY
------------------
The magenta lacing stays a flat slab on the SHAFT only (y ~0.10-0.23 in boot-local
metres). The reference lacing runs from y 0.053 to 0.225, but the boot's front surface
steps back 86 mm between y 0.090 and y 0.105 where the instep meets the ankle, and no
single convex slab can follow that break without floating 40 mm off the shaft. Modelling
the cross-lacing properly needs its own SDF, which costs ~5,000 triangles for a feature
that is 35 x 90 px in the scoring render; that trade was declined.
"""

import copy
import json
import math
import sys

SPEC = sys.argv[1] if len(sys.argv) > 1 else "object-sculpt-spec.json"

# ---------------------------------------------------------------- measurements
# All in metres, in each part's own local frame.
FOOT_LIFT_L = 0.047          # measured 47 mm in clay_2 and body_2 independently
FOOT_LIFT_R = 0.000
BOOT_DX, BOOT_DZ = 0.0002, 0.004     # the boot axis offsets already in the spec

BOOT_RESOLUTION = 48
GLOVE_RESOLUTION = 36
HAND_RESOLUTION = 20

# Sampled face counts from a numpy port of polygonizeSdf at these resolutions.
MEASURED_TRIS = {"boot": 15228, "glove": 8540, "hand": 2704}


def _r(value, places=5):
    return round(float(value), places)


def boot_sdf(outboard, resolution=BOOT_RESOLUTION):
    """Boot field in boot-local metres: y=0 is the sole, z=0 the ankle axis, x=0 the centre.

    `outboard` is +1 when +X points away from the body (her left boot) and -1 for the right,
    and only the collar and its wing use it -- the foot itself is symmetric to within the
    reading error of the reference.
    """
    ob = float(outboard)
    primitives = [
        {"id": "sole", "type": "box", "size": [0.094, 0.026, 0.214],
         "center": [0.0, 0.018, 0.056]},
        {"id": "heel", "type": "box", "size": [0.082, 0.042, 0.062],
         "center": [0.0, 0.026, -0.014]},
        {"id": "fore", "type": "box", "size": [0.112, 0.078, 0.170],
         "center": [0.0, 0.056, 0.078]},
        {"id": "toe", "type": "ellipsoid", "radii": [0.044, 0.034, 0.028],
         "center": [0.0, 0.042, 0.148]},
        {"id": "ankle", "type": "ellipsoid", "radii": [0.046, 0.046, 0.064],
         "center": [0.0, 0.124, 0.014]},
        {"id": "shaft", "type": "ellipsoid", "radii": [0.036, 0.052, 0.050],
         "center": [0.0, 0.152, 0.012]},
        {"id": "collar", "type": "ellipsoid", "radii": [0.070, 0.046, 0.065],
         "center": [_r(0.020 * ob), 0.210, 0.002]},
        {"id": "wing", "type": "ellipsoid", "radii": [0.030, 0.028, 0.042],
         "center": [_r(0.086 * ob), 0.200, -0.010]},
        {"id": "wingup", "type": "ellipsoid", "radii": [0.026, 0.034, 0.038],
         "center": [_r(0.062 * ob), 0.254, -0.014]},
    ]
    # The LAST operation is the emitted result, so the root of the tree must be last.
    operations = [
        {"id": "o1", "type": "smooth-union", "left": "sole", "right": "heel", "radius": 0.016},
        {"id": "o2", "type": "smooth-union", "left": "o1", "right": "fore", "radius": 0.018},
        {"id": "o3", "type": "smooth-union", "left": "o2", "right": "toe", "radius": 0.016},
        {"id": "o4", "type": "smooth-union", "left": "o3", "right": "ankle", "radius": 0.024},
        {"id": "o5", "type": "smooth-union", "left": "o4", "right": "shaft", "radius": 0.020},
        {"id": "o6", "type": "smooth-union", "left": "o5", "right": "collar", "radius": 0.018},
        {"id": "o7", "type": "smooth-union", "left": "o6", "right": "wing", "radius": 0.016},
        {"id": "boot", "type": "smooth-union", "left": "o7", "right": "wingup", "radius": 0.016},
    ]
    # y bounds: min is an exact multiple of the step, so a grid LINE lands on y = 0 and the
    # sole is emitted flat on the floor rather than a fraction of a voxel above or below it.
    y_range = 0.324
    y_min = _r(-4.0 * y_range / resolution, 6)
    x_bounds = (-0.066, 0.130) if ob > 0 else (-0.130, 0.066)
    return {
        "primitives": primitives,
        "operations": operations,
        "bounds": {"min": [x_bounds[0], y_min, -0.088],
                   "max": [x_bounds[1], _r(y_min + y_range, 6), 0.188]},
        "resolution": resolution,
    }


# Hand axis measured in body_2: the exposed finger mass runs 15.5 degrees outboard of
# vertical, down and away from the body.
_HAND_AXIS = (math.sin(math.radians(15.5)), -math.cos(math.radians(15.5)), 0.0)
# The top sphere's CENTRE, not its pole: 0.1199 + its own 0.0345 radius puts the top of the
# emitted surface on the measured glove edge at y 1.108, rather than 34 mm past it.
_GLOVE_TOP = 0.1199


def _along(axis, t, side):
    return [_r(axis[0] * t * side), _r(axis[1] * t), _r(axis[2] * t)]


def glove_sdf(side, forearm_axis, resolution=GLOVE_RESOLUTION):
    """Sleeve + fist, in wrist-local metres. `side` is +1 for the left arm, -1 for the right."""
    count = 7
    primitives = []
    for index in range(count):
        fraction = index / (count - 1)
        primitives.append({
            "id": "s%d" % index,
            "type": "sphere",
            # 27.0 mm at the wrist just covers the forearm's own 26.12 mm end radius; the
            # reference wrist is 42 mm across, but a glove narrower than the arm inside it
            # would show a ring of bare skin through the cloth.
            "radius": _r(0.0270 + (0.0345 - 0.0270) * fraction),
            "center": _along(forearm_axis, -_GLOVE_TOP * fraction, side),
        })
    fist = _along(_HAND_AXIS, 0.033, side)
    primitives.append({
        "id": "fist", "type": "ellipsoid",
        "radii": [0.0285, 0.038, 0.033],           # 57 x 76 x 66 mm: measured knuckle width / depth
        "center": [fist[0], fist[1], 0.010],
    })
    operations = []
    previous = "s0"
    for index in range(1, count):
        operations.append({"id": "g%d" % index, "type": "smooth-union",
                           "left": previous, "right": "s%d" % index, "radius": 0.012})
        previous = "g%d" % index
    operations.append({"id": "glove", "type": "smooth-union",
                       "left": previous, "right": "fist", "radius": 0.016})
    x_bounds = (-0.064, 0.046) if side > 0 else (-0.046, 0.064)
    return {
        "primitives": primitives,
        "operations": operations,
        "bounds": {"min": [x_bounds[0], -0.078, -0.046], "max": [x_bounds[1], 0.160, 0.050]},
        "resolution": resolution,
    }


def hand_sdf(side, resolution=HAND_RESOLUTION):
    """The exposed fingerless mass below the glove hem, in wrist-local metres.

    Four lobes 12.2 mm apart across a 54 mm span reproduce the measured 51 mm wide, 45 mm
    tall skin patch; the smooth-union radius of 10 mm merges them into one curled wedge with
    shallow lobes rather than four separate fingers, which is what the reference reads as.
    """
    centre = _along(_HAND_AXIS, 0.085, side)
    cx, cy, cz = centre[0], centre[1], 0.020
    primitives = []
    for index, offset in enumerate((-0.0183, -0.0061, 0.0061, 0.0183)):
        primitives.append({
            "id": "f%d" % index, "type": "ellipsoid",
            "radii": [0.0085, 0.019, 0.017],
            "center": [_r(cx + offset * side), _r(cy), cz],
        })
    operations = []
    previous = "f0"
    for index in range(1, 4):
        name = "hand" if index == 3 else "h%d" % index
        operations.append({"id": name, "type": "smooth-union",
                           "left": previous, "right": "f%d" % index, "radius": 0.010})
        previous = name
    x_lo, x_hi = sorted((_r(cx - 0.032), _r(cx + 0.032)))
    return {
        "primitives": primitives,
        "operations": operations,
        "bounds": {"min": [x_lo, _r(cy - 0.026), _r(cz - 0.024)],
                   "max": [x_hi, _r(cy + 0.026), _r(cz + 0.024)]},
        "resolution": resolution,
    }


# ---------------------------------------------------------------- spec helpers
def node_world(index, component_id):
    """World position of a component's pivot, using the emitter's own rule: the pivot sits at
    `attachment.localStart` whenever the attachment spans a real length, else at
    `transform.position`, and offsets accumulate down the parent chain."""
    component = index[component_id]
    attachment = component.get("attachment")
    local = None
    if isinstance(attachment, dict):
        start, end = attachment.get("localStart"), attachment.get("localEnd")
        if (isinstance(start, list) and isinstance(end, list)
                and len(start) == 3 and len(end) == 3
                and math.dist([float(v) for v in start], [float(v) for v in end]) > 1e-4):
            local = [float(v) for v in start]
    if local is None:
        local = [float(v) for v in (component.get("transform") or {}).get("position") or [0, 0, 0]]
    parent = component.get("parent")
    if parent and parent != "root" and parent in index:
        up = node_world(index, parent)
        return [up[axis] + local[axis] for axis in range(3)]
    return local


def scrub_refs(node, removed):
    """Drop deleted component ids from every `componentRefs` array anywhere in the spec."""
    dropped = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "componentRefs" and isinstance(value, list):
                keep = [item for item in value if item not in removed]
                dropped += len(value) - len(keep)
                node[key] = keep
            else:
                dropped += scrub_refs(value, removed)
    elif isinstance(node, list):
        for item in node:
            dropped += scrub_refs(item, removed)
    return dropped


def add_ref(spec, pass_ids, component_id):
    """Make sure a new component is listed by the build passes that already list its sibling."""
    added = 0
    for build_pass in spec.get("buildPasses", []):
        if not isinstance(build_pass, dict) or build_pass.get("id") not in pass_ids:
            continue
        refs = build_pass.get("componentRefs")
        if isinstance(refs, list) and component_id not in refs:
            refs.append(component_id)
            added += 1
    return added


def passes_listing(spec, component_id):
    return {build_pass.get("id") for build_pass in spec.get("buildPasses", [])
            if isinstance(build_pass, dict)
            and isinstance(build_pass.get("componentRefs"), list)
            and component_id in build_pass["componentRefs"]}


def place_after(components, anchor_id, component):
    """Insert (or replace) `component` immediately after `anchor_id`, so that its parent is
    always emitted before it -- the generator attaches to `root` when the parent is missing."""
    existing = next((i for i, c in enumerate(components) if c.get("id") == component["id"]), None)
    if existing is not None:
        components[existing] = component
        return False
    anchor = next(i for i, c in enumerate(components) if c.get("id") == anchor_id)
    components.insert(anchor + 1, component)
    return True


def make_implicit(component, sdf, rationale, dimensions):
    component["topologyClass"] = "implicit"
    component["primitive"] = "ellipsoid"
    component["topologyRationale"] = rationale
    component.pop("attachment", None)
    descriptor = component.setdefault("geometryDescriptor", {})
    descriptor["sdf"] = sdf
    # A quadric collapse on a voxel staircase has not been verified in this build, and the
    # resolutions above are already chosen to sit inside the budget.
    descriptor.pop("decimate", None)
    descriptor.pop("subdivide", None)
    if dimensions is None:
        component.pop("dimensions", None)
        (component.get("transform") or {}).pop("scale", None)
    else:
        component["dimensions"] = dimensions
        component.setdefault("transform", {})["scale"] = [1.0, 1.0, 1.0]


# ---------------------------------------------------------------- the patch
def main():
    with open(SPEC, encoding="utf-8") as handle:
        spec = json.load(handle)

    components = spec["componentTree"]
    index = {c["id"]: c for c in components}
    started_with = len(components)
    report = []

    # ---- 1. boots -----------------------------------------------------------
    for boot_id, foot_id, outboard, lift in (("boot-l", "foot-l", +1, FOOT_LIFT_L),
                                             ("boot-r", "foot-r", -1, FOOT_LIFT_R)):
        if boot_id not in index or foot_id not in index:
            continue
        boot = index[boot_id]
        foot_y = node_world(index, foot_id)[1]
        # Derived, not hard-coded: whatever the leg dimension does to the ankle, the boot's
        # own y = 0 (its sole) still lands on the floor plus this foot's contrapposto lift.
        boot["transform"] = {"position": [BOOT_DX, _r(lift - foot_y), BOOT_DZ],
                             "rotation": [0, 0, 0]}
        make_implicit(
            boot,
            boot_sdf(outboard),
            "Implicit solid. A swept circular cylinder cannot express a boot: the reference "
            "sole is 235 mm long against a 121 mm width and the toe sits 177 mm ahead of the "
            "ankle while the heel sits 58 mm behind it. Sole slab, heel block, forefoot, toe, "
            "ankle, shaft, folded collar and outboard wing are smooth-unioned into one field, "
            "sampled so that a grid line falls exactly on the sole plane.",
            {"width": 0.176, "height": 0.290, "depth": 0.242,
             "units": "metres", "confidence": 0.85},
        )
        report.append("%s -> implicit SDF, res %d, sole on y=%.3f, toe z +0.177, heel z -0.058"
                      % (boot_id, BOOT_RESOLUTION, lift))

    # ---- 2. sole and cuff are now inside the boot field ---------------------
    removed = set()
    for dead in ("boot-sole", "boot-cuff"):
        if dead in index:
            components.remove(index.pop(dead))
            removed.add(dead)

    # ---- 3. the 30 phalanges ------------------------------------------------
    phalanges = [c["id"] for c in components
                 if c.get("role") == "finger" and c.get("parent") is not None]
    for dead in phalanges:
        components.remove(index.pop(dead))
        removed.add(dead)

    dropped = scrub_refs(spec, removed)
    if removed:
        report.append("deleted %d components (%d phalanges, plus %s); "
                      "%d build-pass componentRefs scrubbed"
                      % (len(removed), len(phalanges),
                         ", ".join(sorted(removed - set(phalanges))) or "nothing else", dropped))
    else:
        report.append("no components to delete (already applied)")

    # `rig.bones` is deliberately left alone: the finger bones deform nothing on their own
    # (no component in this spec carries an authored pose, so `_posed_bone_rotations` is
    # empty and every bone sits at rest), and rewriting another dimension's skeleton to
    # chase 30 dead entries would risk the rig admission checks for no visible gain.

    # ---- 4. toe caps and lacing, on BOTH boots ------------------------------
    if "boot-toecap" in index:
        cap = index["boot-toecap"]
        cap["parent"] = "boot-l"
        # 120 x 96 x 98 mm rather than the measured 105 x 85: the cap has to stand proud of a
        # boot that is itself 114 mm wide at that height, and a cap at the measured width
        # would be entirely inside the boot surface and invisible.
        cap["dimensions"] = {"width": 0.120, "height": 0.096, "depth": 0.098,
                             "units": "metres", "confidence": 0.7}
        cap["transform"] = {"position": [0.0, 0.048, 0.130], "rotation": [0, 0, 0]}
        cap.pop("attachment", None)
        report.append("boot-toecap -> boot-local y 0.000-0.096, z 0.081-0.179 (was y 0.247, "
                      "z 0.120 world = 192 mm too high)")

        cap_r = copy.deepcopy(cap)
        cap_r["id"] = "boot-toecap-r"
        cap_r["name"] = "Brass toe cap (her right)"
        cap_r["parent"] = "boot-r"
        if place_after(components, "boot-toecap", cap_r):
            report.append("boot-toecap-r created (the right boot had no toe cap at all)")
        add_ref(spec, passes_listing(spec, "boot-toecap"), "boot-toecap-r")

    if "boot-lace" in index:
        lace = index["boot-lace"]
        lace["parent"] = "boot-l"
        lace["primitive"] = "box"
        # Flat 70 mm panel, not a 24 mm round rod, tilted back 11.5 degrees so it lies along
        # the shaft front; buried below y 0.10 where the instep breaks forward.
        lace["dimensions"] = {"width": 0.066, "height": 0.155, "depth": 0.024,
                              "units": "metres", "confidence": 0.6}
        lace["transform"] = {"position": [0.0, 0.156, 0.070], "rotation": [-0.20, 0, 0]}
        lace.pop("attachment", None)
        report.append("boot-lace -> flat panel, boot-local y 0.080-0.232 (was world y "
                      "0.339-0.539, a 290 mm-high round rod)")

        lace_r = copy.deepcopy(lace)
        lace_r["id"] = "boot-lace-r"
        lace_r["name"] = "Cross lacing (her right)"
        lace_r["parent"] = "boot-r"
        if place_after(components, "boot-lace", lace_r):
            report.append("boot-lace-r created (the right boot had no lacing at all)")
        add_ref(spec, passes_listing(spec, "boot-lace"), "boot-lace-r")

    # ---- 5. the bare-foot barrels stop punching through the boots -----------
    for foot_id in ("foot-l", "foot-r"):
        if foot_id not in index:
            continue
        attachment = index[foot_id].get("attachment")
        if isinstance(attachment, dict):
            attachment["baseRadius"] = 0.028
            attachment["endRadius"] = 0.028
    report.append("foot-l/foot-r radius 0.07598 -> 0.028 (152 mm skin barrels were wider "
                  "than the 119-138 mm boots containing them)")

    # ---- 6. gloves and hands ------------------------------------------------
    for side, tag in ((+1, "l"), (-1, "r")):
        forearm = index.get("forearm-%s" % tag)
        if forearm is None:
            continue
        attachment = forearm["attachment"]
        # The wrist, in the forearm pivot's own frame. Derived so this stays correct (and
        # idempotent) whatever the arm dimension does to the forearm.
        wrist = [_r(float(attachment["localEnd"][axis]) - float(attachment["localStart"][axis]))
                 for axis in range(3)]
        axis_length = math.dist([0, 0, 0], wrist) or 1.0
        forearm_axis = tuple(value / axis_length for value in wrist)
        forearm_axis = (abs(forearm_axis[0]), forearm_axis[1], forearm_axis[2])

        glove = index.get("glove-%s" % tag)
        if glove is not None:
            glove["parent"] = "forearm-%s" % tag
            glove["transform"] = {"position": list(wrist), "rotation": [0, 0, 0]}
            make_implicit(
                glove,
                glove_sdf(side, forearm_axis),
                "Implicit solid. The glove is a sleeve that swells into a closed fist "
                "(body_4 shows the fist plainly), which a single tapered cylinder cannot be: "
                "the emitted tube ran vertically while the forearm is tilted 11.2 degrees, "
                "swallowed the whole hand and then overshot 30 mm past the lowest fingertip. "
                "Seven spheres along the measured forearm axis carry the sleeve from the "
                "wrist to y 1.108; one ellipsoid carries the 57 x 66 mm fist down to the "
                "knuckle line.",
                {"width": 0.095, "height": 0.225, "depth": 0.081,
                 "units": "metres", "confidence": 0.8},
            )
            report.append("glove-%s -> implicit SDF, res %d, sleeve on the real forearm axis, "
                          "hem at the knuckle line" % (tag, GLOVE_RESOLUTION))

        hand = index.get("hand-%s" % tag)
        if hand is not None:
            hand["parent"] = "forearm-%s" % tag
            hand["transform"] = {"position": list(wrist), "rotation": [0, 0, 0]}
            make_implicit(
                hand,
                hand_sdf(side),
                "Implicit solid, and deliberately WITHOUT `dimensions` or `transform.scale`: "
                "this component carries a rig bone, and `derive_envelope_radius` reads "
                "`transform.scale` to size that bone's skin envelope, so the (1,1,1) the "
                "emitter needs for a metre-authored field would ask for a 600 mm envelope "
                "instead of the 30 mm fallback every bone in this rig uses. Absent on both "
                "fields gives the emitter its (1,1,1) and the rigger its fallback. Four "
                "curled fingertip lobes, real extents 0.051 x 0.042 x 0.034 m, replacing "
                "fifteen interpenetrating phalanx rods per hand.",
                None,
            )
            report.append("hand-%s -> implicit SDF, res %d, one curled 54 x 42 mm finger mass"
                          % (tag, HAND_RESOLUTION))

    # ---- 7. nails move to the fingertips, on both hands ---------------------
    if "nails" in index:
        nails = index["nails"]
        nails["parent"] = "hand-l"
        nails["primitive"] = "ellipsoid"
        nails["dimensions"] = {"width": 0.042, "height": 0.020, "depth": 0.016,
                               "units": "metres", "confidence": 0.6}
        nails["transform"] = {"position": [0.0227, -0.0930, 0.0340], "rotation": [0, 0, 0]}
        nails.pop("attachment", None)
        report.append("nails -> hand-l fingertips, wrist-local y -0.093 (was y -0.086 under "
                      "glove-l, i.e. the knuckle line, 50-61 mm above its own fingertips)")

        nails_r = copy.deepcopy(nails)
        nails_r["id"] = "nails-r"
        nails_r["name"] = "Teal fingernails (her right)"
        nails_r["parent"] = "hand-r"
        nails_r["transform"] = {"position": [-0.0227, -0.0930, 0.0340], "rotation": [0, 0, 0]}
        if place_after(components, "nails", nails_r):
            report.append("nails-r created (the right hand had no nails at all)")
        add_ref(spec, passes_listing(spec, "nails"), "nails-r")

    # ---- 8. the detail inventory must not point at a deleted component ------
    details = ((spec.get("preSpecAssessment") or {}).get("detailInventory") or {}).get("details")
    if isinstance(details, list):
        for detail in details:
            maps_to = detail.get("mapsTo") if isinstance(detail, dict) else None
            if isinstance(maps_to, dict) and maps_to.get("ref") in removed:
                was = maps_to["ref"]
                maps_to["ref"] = "boot-l" if was.startswith("boot") else "hand-l"
                report.append("detailInventory %r remapped %s -> %s"
                              % (detail.get("id"), was, maps_to["ref"]))

    # ---- 9. bookkeeping -----------------------------------------------------
    added = (MEASURED_TRIS["boot"] * 2 + MEASURED_TRIS["glove"] * 2
             + MEASURED_TRIS["hand"] * 2 + 1397 * 2 + 864 * 2 + 749 * 2)
    freed = 3720 + 832 + 416 + 1664 + 1664 + 464 + 1397 + 416 + 259
    budget = (spec.get("performanceBudget") or {}).get("targetTriangles", 250000)
    baseline = (spec.get("performanceBudget") or {}).get("measuredTriangles", 128833)

    with open(SPEC, "w", encoding="utf-8") as handle:
        json.dump(spec, handle, indent=1)

    print("patch_extremities: %d components (was %d)" % (len(components), started_with))
    for line in report:
        print("  - " + line)
    print("  triangle estimate: +%d added, -%d freed, net %+d -> about %d against a %d budget"
          % (added, freed, added - freed, baseline + added - freed, budget))
    print("  componentTree: %d entries (was 104 meshes + 5 instanced systems; max draw calls 160)"
          % len(components))


if __name__ == "__main__":
    main()
