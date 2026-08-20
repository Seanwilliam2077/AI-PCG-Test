/**
 * Boots -- the chunky black combat boots, and a big part of why the figure
 * reads bottom-heavy.
 *
 * Three shells per pair, because they want three different voxel sizes: the
 * slab sole is coarse and blocky, the upper carries the cuff and the toe cap,
 * and the laces are 8 mm cords that need a voxel well under the body's to
 * survive the mesher at all.
 *
 * Everything is authored in a *local foot frame* -- origin on the floor under
 * the ankle, +z toward the toe, +x outboard on the left foot -- and then yawed
 * by `pose.footToeOut` and dropped onto `skel.ankle{L,R}`.  That is the only
 * way the toe-out stays consistent between the sole outline, the lace rails
 * and the cuff wings; authoring in world space and fudging the x offsets puts
 * the overhang on the wrong side of the toe.
 *
 * **The local frame's floor is the ankle joint's, not the world's.**  The
 * skeleton carries a contrapposto: `skel.ankleL` sits `pose.footLift` = 47 mm
 * above `skel.ankleR` and `pose.footForward` = 28 mm in front of it.  `place()`
 * therefore translates by `ankle - [0, landmarks.ankleJoint, 0]`, so the local
 * y = 0 plane lands on the floor under a *planted* foot and 47 mm up under the
 * raised one.  Round 2 translated y by a literal 0 and the whole 47 mm stagger
 * silently vanished: both boots stood on the floor, the two of them merged into
 * one run at every height, and the three-quarter views measured 2-3x the
 * reference's width in the bottom 4 % of the figure.  `landmarks.footBed` is
 * still the slab's top face, but it is now a *local* height -- 0.042 above
 * whichever floor this boot stands on -- and never a world one.
 *
 * ## The side profile, measured
 *
 * Everything below is read off `clay_0` with a metric grid anchored on the
 * panel's alpha bbox, converted to boot-local z by z = 0.1976 - X_panel.  The
 * panel is an orthographic side view, so panel-x *is* world z: the union of
 * the two boots covers z in [c*zMin - s*halfW, c*zMax + s*halfW] with
 * c = cos(footToeOut), s = sin(footToeOut).  (An earlier pass divided the panel
 * distances by cos to "de-yaw" them, which is wrong -- it is the model that
 * gets projected, not the panel that gets stretched -- and it made the heel
 * look 20 mm short when it is 3 mm long.)
 *
 *     y      ref z front   ref z back      what is on the silhouette
 *     0.035    +0.165        -0.075        sole slab at its longest
 *     0.085    +0.154        -0.079        toe box / heel counter
 *     0.095    +0.145        -0.075        top of the toe box
 *     0.125    +0.121        -0.068        throat: the front steps back 25 mm
 *     0.165    +0.114        -0.056        throat and shaft
 *     0.195    +0.097        -0.133        cuff rim, at its lowest and deepest
 *     0.245    +0.091        -0.103        cuff, mid-hang
 *     0.295    +0.100        -0.076        just under the fold
 *
 * Three things fall straight out of that table and they are the three shapes
 * this file is built around:
 *
 * 1. **The front is a stack of walls, not a slope.**  The toe box's front face
 *    is near-vertical from the welt to y = 0.10 at z = 0.152; it steps back
 *    25 mm to the instep, which holds z = 0.130 to y = 0.178; and that steps
 *    back another 13 mm to the throat -- the panel the lacing runs up -- which
 *    is vertical at z = 0.098 all the way to the fold.  A boot built as a chain
 *    of boxes ramping up to a round shaft is 30 mm shallow through the whole
 *    ankle, which is what the review measured; a single tapered tongue through
 *    both panels is 20 mm proud at the top and 20 mm shallow at the bottom.
 * 2. **The cuff hangs backwards.**  Its rim reaches z = -0.133 at y = 0.195
 *    against a shaft back face at z = -0.055, and the rim's height and its
 *    reach fall off together as you come round to the front -- so the plan
 *    outline is an oval pushed 8 mm aft, not a circle.  It is *not* pushed
 *    outboard.  Round 3 adds the other half of that: the rim is also the
 *    *narrow* end of the collar across, see `foldR`.
 * 3. **The leather laps the sole, not the other way round.**  At the toe the
 *    leather stands 16 mm proud of the slab and at the heel 13 mm, and only
 *    24 mm of sole shows below the leather's edge -- not the 42 mm the slab is
 *    thick.  A 3 mm lap, which is what this file used to have, is a third of
 *    the sole's own voxel: it vanishes in the bake and the sole reads as a
 *    brick the boot is standing on.
 *
 * ## Round 2: the front view, measured across
 *
 * Everything above reads the side.  Reading `clay_2` and `clay_5` across, with
 * `tools/grid.py --metres` and a run decomposition per row, says two more
 * things, and they pull in opposite directions:
 *
 *     y      clay_2 runs / gap        clay_5 runs / gap    what it is
 *     0.06   0.117 0.093 / 0.071      -    -    /  -       soles, wide apart
 *     0.10   0.104 0.109 / 0.035      0.120 0.134 / 0.019  ankles, closing
 *     0.15   0.085 0.093 / 0.015      0.104 0.119 / 0.033  shafts, nearly shut
 *     0.21     one run 0.198          one run 0.293        cuffs, TOUCHING
 *     0.25     one run 0.238          one run 0.316
 *     0.29     one run 0.285          one run 0.272
 *
 * So the boots separate downwards and merge upwards, and the model did neither:
 * its gap was a flat 0.033-0.038 from the floor to the fold.  `splay()` opens
 * the bottom and the cuff outline closes the top.  The two panels disagree
 * about the absolute widths by up to 40% -- the turnaround is a perspective
 * render and the near boot is inflated -- so every target here is the mean of
 * the two, which is also what the scoreboard's core-width bands compare against
 * one panel each.
 *
 * What round 2 could **not** fix: at yaw 45 and 315 the reference shows its two
 * boots as separate runs 0.10 m wide with 0.111 m of daylight between them, and
 * this render shows one run of 0.30.  That is not a modelling error.  A boot
 * 0.21 m long and 0.09 m wide projects 0.20-0.22 m wide at 45 degrees, so two
 * of them split only if their centres are more than 0.21 m apart on screen;
 * ours are 0.124 * cos 45 = 0.088 apart, because that is the stance the calf
 * calibration fixes.  The reference splits because it is a perspective camera
 * looking down at a near boot and a far one, which an orthographic preview
 * matched to a metric grid cannot reproduce.  Chasing it would need the stance
 * widened by 0.17 m.
 *
 * ## Round 3: the pose, the ball, and which end of the cuff is wide
 *
 * Four measured changes, all of them read off a per-row run decomposition
 * (`out/boots_probe.py` for a panel, `out/boots_raw.py` for a `--frame 1.80`
 * preview) rather than off a grid by eye:
 *
 * 1. **The pose was not reaching the shells.**  `place()` translated y by a
 *    literal 0, so both boots stood on the world floor and the 47 mm stagger in
 *    `skel.ankleL/R` vanished.  `clay_2`'s bottom 47 mm is ONE run.  With the
 *    lift wired through, the scoreboard's GROUND CONTACT row for yaw 0 reads
 *    ref -2.74 %H against render -2.54 %H -- 3 mm out, from 47 mm out.
 * 2. **The cuff is widest at the fold and narrowest at the hem, across.**  Both
 *    earlier versions had it the other way round and flared the collar into a
 *    bell, which is the "splayed pancake" the review measured.  See `foldR`.
 * 3. **There is a ball in the boot.**  Meaned over `clay_2` and `clay_5` the
 *    boot is 0.122 across at 60-80 mm of local height and 0.091 at the ankle;
 *    the model was a flat 0.096-0.104 all the way up.  The vamp carries the
 *    bulge and the waist and heel behind it are pulled in 6 mm.
 * 4. **The boot was 11-18 % too long fore-and-aft and 19 % too deep at the
 *    ankle**, and the sole slab was 18 mm shorter than the leather where the
 *    two side panels agree it is only 8 mm shorter.
 *
 * And one correction to the round-2 note above: the reason yaw 45 and 315
 * cannot be matched is not only the stance.  Solving for the view angle from
 * the boot's own plan outline -- a 0.20 x 0.09 m boot cannot project narrower
 * than 0.19 m at 45 degrees off its axis, and both `clay_1` and `clay_3` read
 * it at 0.10-0.11 m -- puts `clay_3` within about 15 degrees of frontal.  The
 * intermediate panels are not 45-degree views at all, which is the same
 * conclusion `docs/MEASUREMENTS.md` reaches from the trouser leg.
 */
import { Field, Vec3, box } from '../sdf/types.js';
import {
  capsuleOval, clamp, ellipsoid, field, intersect, offset, roundBox, rotateY, smoothUnion,
  smoothstep, subtract, translate, union,
} from '../sdf/ops.js';
import { Curve, orientedBox, tube } from '../sdf/curve.js';
import { PartContext, PartModule, Shell, constMaterial, nums, paint } from './types.js';

/* ------------------------------------------------------------------ frame */

/**
 * Splay: slide the boot outboard by `k * (hinge - y)` below `hinge`, in world
 * x, leaving everything above the hinge exactly where it was.
 *
 * Measured on `clay_2`.  The reference's two boots are separate all the way
 * from the floor to the top of the shaft, and the gap between them *opens
 * downwards*: 0.015 m at y = 0.15, 0.027 at 0.12, 0.035 at 0.10, 0.071 at 0.06.
 * The overall span does the same, 0.192 -> 0.281 over that range.  The model's
 * gap was flat at 0.033-0.038 and its span flat at 0.218-0.232, so the soles
 * were 0.05 m short of the reference's while the shafts were right.
 *
 * A shear, not a roll: `rotateAbout(_, 2, ...)` about the ankle would tip the
 * sole off the floor, and the reference's soles are flat on it.  A shear costs
 * a factor (1 + k) on `lip` -- 1.20 here -- because d/dy picks up k times the
 * x derivative; claiming 1 would let the mesher take steps it cannot afford and
 * punch holes in the sole at the coarse LODs.
 *
 * The hinge is at the ankle joint rather than higher up because the body's own
 * heel ellipsoid sits at x = +-0.032 with the boot's inboard wall at 0.019:
 * 13 mm of clearance.  Shearing the boot outboard eats that, so the shift at
 * heel height (y = 0.072) is held to 7.6 mm.
 */
function splay(f: Field, side: 1 | -1, hinge: number, k: number): Field {
  if (k <= 0) return f;
  const b = f.bounds;
  const dMax = k * Math.max(0, hinge - b.min[1]);
  return field(
    (x, y, z) => f.sdf(x - side * k * Math.max(0, hinge - y), y, z),
    box(
      [b.min[0] - (side > 0 ? 0 : dMax), b.min[1], b.min[2]],
      [b.max[0] + (side > 0 ? dMax : 0), b.max[1], b.max[2]],
    ),
    f.lip * (1 + k),
  );
}

/**
 * Yaw a locally-authored field out to one foot.  `side` is +1 for her left
 * (+X) and -1 for her right; the toe swings outboard on both, which is a
 * positive yaw on the left and a negative one on the right.
 *
 * The splay is applied *after* the yaw but *before* the drop onto the ankle, so
 * it is still a shear in world x -- `rotateY` has already fixed the axes and
 * `translate` does not turn them -- but its hinge is a boot-local height and so
 * rides up with the raised foot.  Shearing after the translate, which is what
 * this did in round 2, measures the hinge against the world floor: the raised
 * boot would then be sheared as though its sole were 47 mm underground and it
 * would come out 9 mm further outboard than the planted one for no reason.
 *
 * Every shell and every paint mask goes through here, so the sole, the leather,
 * the laces and the brass regions all move together.
 */
function place(f: Field, ctx: PartContext, side: 1 | -1): Field {
  const ank = side > 0 ? ctx.skel.ankleL : ctx.skel.ankleR;
  const B = nums(ctx.spec.boots);
  // The pose lift.  `landmarks.ankleJoint` is where the ankle sits on a planted
  // foot, so the difference is exactly how far this boot is off the floor.
  const lift = ank[1] - ctx.spec.landmarks.ankleJoint;
  return translate(
    splay(rotateY(f, side * ctx.spec.pose.footToeOut), side, B.splayY, B.splay),
    [ank[0], lift, ank[2]],
  );
}

/* ---------------------------------------------------------------- outline */

/**
 * The footprint, as a slab between two heights.  A combat boot sole is a
 * rounded rectangle that is widest across the ball and narrows through the
 * waist to a squarer heel, which three overlapping round boxes give for far
 * less than an extruded polygon costs.
 */
function footprint(b: BootDims, halfW: number, y0: number, y1: number): Field {
  const cy = (y0 + y1) / 2, hy = (y1 - y0) / 2;
  // Small corner radius on purpose: a slab sole wants a crisp horizontal line
  // where the leather lands on it, and a 14 mm round on a 42 mm slab softens
  // that join into a pill.
  const r = Math.min(hy * 0.55, 0.009);
  // The slab is inset from the leather at both ends -- see the header table:
  // the boot's longest point is the leather at y = 0.035, and the sole under
  // it is 16 mm shorter at the toe and 13 mm at the heel.
  const zF = b.toeZ - b.soleToeInset, zB = b.heelZ + b.soleHeelInset;
  return union(
    roundBox([0, cy, (zF + zB) / 2], [halfW - 0.005, hy, (zF - zB) / 2 - 0.004], r),
    roundBox([0, cy, zF - 0.028], [halfW, hy, 0.026], r),
    roundBox([0, cy, zB + 0.026], [halfW - 0.006, hy, 0.024], r),
  );
}

/* -------------------------------------------------------------------- sole */

function sole(b: BootDims): Field {
  const top = b.soleTop;

  // The slab runs a few millimetres past both faces of the 0..footBed band it
  // nominally occupies, so the corner round does not pinch the outline in.
  // The surplus above footBed is buried in the leather, which now laps 18 mm
  // down the slab; the surplus below is under the floor.
  const slab = footprint(b, b.soleHalfW, -0.003, top + 0.004);
  // The welt is a proud band around the sole.  It has to sit *below* the
  // leather's lower edge (top - soleLap) or it is buried and the sole reads as
  // one extruded block again.
  const weltTop = top - b.soleLap - 0.004;
  const welt = footprint(b, b.soleHalfW + b.soleWeltProud, weltTop - 0.013, weltTop);

  // Waist of the sole, scooped away underneath between the forefoot pad and
  // the heel block: that gap is what makes the heel read as raised.
  const arch = roundBox(
    [0, b.archLift / 2 - 0.004, b.heelZ + 0.076],
    [b.soleHalfW + 0.02, b.archLift / 2 + 0.004, 0.026],
    0.008,
  );
  // Toe spring: the front lip of the sole lifts a few millimetres off the floor.
  const spring = roundBox(
    [0, -0.016, b.toeZ - b.soleToeInset + 0.018], [b.soleHalfW + 0.02, 0.018, 0.028], 0.010,
  );

  return subtract(union(slab, welt), union(arch, spring));
}

/* ------------------------------------------------------------------- upper */

/** Half-width and half-depth of the shaft at height y -- ankle to the fold. */
function shaftR(b: BootDims, y: number): number {
  const t = clamp((y - b.ankleY) / Math.max(1e-6, b.cuffY - b.ankleY), 0, 1);
  return b.shaftRAnkle + (b.shaftRTop - b.shaftRAnkle) * t;
}

/**
 * Radius of the shaft's *oval* section at azimuth `a` (0 = toe, +pi/2 = +x).
 *
 * The cuff plates start on this rather than on `shaftR`, or the plates at the
 * front and back -- where the shaft is 30% deeper than it is wide -- begin
 * inside the leather and the fold line disappears exactly where the side view
 * is read.
 */
function shaftOvalR(b: BootDims, y: number, a: number): number {
  const rx = shaftR(b, y), rz = rx * b.shaftDepth;
  const sx = Math.sin(a) / rx, sz = Math.cos(a) / rz;
  return 1 / Math.sqrt(sx * sx + sz * sz);
}

/**
 * The instep and the throat: the two panels that make up the front of the
 * boot, from the top of the toe box to the fold of the cuff.
 *
 * This is the shape the old version was missing.  It is not a "tongue" sitting
 * in a gap -- on the reference it *is* the front of the boot, and it comes in
 * two steps, not one slope: the instep bulges out over the top of the foot and
 * holds z = 0.121 from y = 0.105 to 0.175, then the front drops 12 mm in
 * 20 mm of height and the throat carries on at a near-constant z = 0.095 all
 * the way to the fold.  A single tapered capsule through both leaves the boot
 * 20 mm too proud at the top and 20 mm too shallow at the bottom.
 *
 * `side` only enters through `laceInset`: the panel is pulled a few mm inboard
 * so that after the toe-out yaw it sits over the leg rather than swung out past
 * the boot's outer edge.  Measured on body_2, the two eyelet columns straddle
 * x = 0.277 and the ankle is at x = 0.277; a panel authored on the local
 * centreline lands 16 mm outboard of that once the boot is yawed, because it
 * sits 110 mm forward of the pivot.
 */
/**
 * Both panels are deep as well as wide -- their half-depth reaches back far
 * enough to overlap the shaft.  That is not cosmetic: authored as thin skins
 * 12 mm deep they stood 30 mm clear of a shaft whose front face is at z = 0.065,
 * more than `smoothUnion` can bridge, and the bake came out with a hole
 * straight through the boot at the instep.  The z the reference measures is the
 * panel's *front*, so the axis is that front less the half-depth.
 */
function instep(b: BootDims, side: 1 | -1): Field {
  const dx = -side * b.laceInset;
  return capsuleOval(
    [dx, b.vampY0, b.vampZ0], [dx, b.vampY1, b.vampZ1],
    b.vampR, b.vampR, b.vampSquashZ, b.vampSquashX,
  );
}

function throat(b: BootDims, side: 1 | -1): Field {
  const dx = -side * b.laceInset;
  return capsuleOval(
    [dx, b.throatY0, b.tongueZ0], [dx, b.cuffY - 0.003, b.tongueZ1],
    b.tongueR, b.tongueR, b.tongueSquashZ, b.tongueSquashX,
  );
}

/**
 * The z of the front surface at height y -- what the lace rails ride on.
 * Whichever of the two front panels is proud at that height wins, which is the
 * same rule the union of the two fields applies.
 */
function frontZ(b: BootDims, y: number): number {
  // A segment contributes only inside its own height range.  Clamping t to
  // [0,1] instead -- which is what this did first -- holds the instep's front z
  // for every height above the instep, so the lace rails ran up a wall at a
  // constant z = 0.116 and the boot measured 20 mm too proud for the whole
  // length of the cuff.  The laces, not the leather, were setting the front
  // edge of the silhouette.
  const seg = (y0: number, y1: number, z0: number, z1: number, half: number) => {
    if (y < y0 || y > y1) return -1;
    return z0 + (z1 - z0) * ((y - y0) / (y1 - y0)) + half;
  };
  return Math.max(
    seg(b.vampY0, b.vampY1, b.vampZ0, b.vampZ1, b.vampR * b.vampSquashZ),
    seg(b.throatY0, b.cuffY - 0.003, b.tongueZ0, b.tongueZ1, b.tongueR * b.tongueSquashZ),
  );
}

/**
 * The leather without the cuff: toe box, throat, heel counter and the shaft
 * over the ankle.
 */
function upperCore(b: BootDims, side: 1 | -1): Field {
  // The leather laps well down the sole slab.  18 mm is deliberate: it is more
  // than one sole voxel at every LOD, so the overlap survives the bake and the
  // two shells read as an upper welted onto a rand instead of a boot parked on
  // a kerb.
  const base = b.soleTop - b.soleLap;
  const halfW = b.upperHalfW;
  // The leather stands proud of the slab at both ends -- 14 mm at the toe,
  // 12 mm at the heel -- which is the way round the reference has it.
  const zF = b.toeZ + b.upperToeProud, zB = b.heelZ;

  // Toe box: a tall block whose front face is close to vertical but leans back
  // 16 mm over its 60 mm of height -- clay_0 reads z = 0.165 at y = 0.035 and
  // 0.145 at y = 0.095.  A box gives a wall and a wedge gives a ramp; a leaning
  // oval capsule is the only one of the three that is both.  Its top is
  // b.toeBoxY, which is where the reference's front edge steps back by 25 mm.
  const tip = capsuleOval(
    [0, base + 0.010, zF + b.toeLean], [0, b.toeBoxY - 0.010, zF - b.toeLean],
    0.016, 0.014, 1.0, (halfW - 0.004) / 0.016,
  );
  const toe = roundBox(
    [0, (base + b.toeBoxY) / 2, zF - 0.048], [halfW, (b.toeBoxY - base) / 2, 0.026], 0.014,
  );
  // Vamp and waist carry the foot back to the heel, rising as they go: the
  // reference's leather tops out at 0.10 over the toe and 0.13 over the heel.
  // The vamp reaches higher and further back than the toe box so it laps the
  // instep panel on one side and the waist on the other; that overlap is what
  // keeps the front of the boot one closed surface.
  //
  // The vamp carries the BALL, which is the boot's widest section and the one
  // thing the front and back panels agree on: 0.121-0.123 across at 60-80 mm of
  // local height, against 0.103 at the sole and 0.091 at the ankle.  The render
  // was a flat 0.096-0.104 from the floor to the fold -- a tube, where the sheet
  // has a foot in it.  So the vamp gets the full `upperHalfW` and the waist and
  // the heel behind it are pulled in 6 mm, and the vamp stops at 0.126 rather
  // than 0.148 so the bulge has faded by the time the shaft takes over.
  const vamp = roundBox(
    [0, (base + 0.126) / 2, zF - 0.086], [halfW, (0.126 - base) / 2, 0.036], 0.016,
  );
  const waist = roundBox(
    [0, (base + 0.122) / 2, 0.006], [halfW - 0.006, (0.122 - base) / 2, 0.032], 0.016,
  );
  const heel = roundBox(
    [0, (base + 0.128) / 2, zB + 0.028], [halfW - 0.006, (0.128 - base) / 2, 0.028], 0.017,
  );

  const shaft = capsuleOval(
    [0, base + 0.058, 0.004],
    [0, b.cuffY - 0.004, 0.006],
    b.shaftRAnkle, b.shaftRTop, b.shaftDepth, 1,
  );

  // 9 mm, not 14: nine fields chained through a 14 mm blend melt the toe box,
  // the step at the instep and the heel counter into one lump, and those three
  // edges are the whole read of the side view.
  return smoothUnion(0.009, tip, toe, vamp, waist, heel, shaft, instep(b, side), throat(b, side));
}

/**
 * The cuff: a ring of tilted leather facets folded down over the top of the
 * shaft.
 *
 * This is the shape that carries the boot in every view, so it is emphatically
 * not a cone of revolution.  On the reference the fold flares into a long
 * pointed wing outboard, hangs *further* off the back than anywhere else, and
 * pulls in under itself at the hem.  `foldR()` and `rimR()` are the two plan
 * outlines and everything else -- how far each facet reaches, how far it hangs,
 * how thick it is -- follows from the pair.  The two collars are meant to
 * overlap across the 0.104 m stance: from y = 0.18 up, both `clay_2` and
 * `clay_5` read the boot mass as a single run.
 *
 * Facets rather than a swept surface because the sculpt's cuff is planar and
 * creased, and because oriented boxes are exact distance fields -- the blend
 * that joins them costs one factor of 1.35 on `lip`, and nothing else here
 * inflates it, so the mesher's empty-space skipping stays valid.
 */
/**
 * A superellipse in plan, as a radius from the boot axis at azimuth `a`
 * (a = atan2(x, z), so 0 is the toe and +pi/2 is +x).  Two of them are used --
 * one for the FOLD where the leather turns over, one for the RIM it hangs down
 * to -- and `foldR`/`rimR` below are the only callers.
   *
   * The outline is a superellipse, not a circle; it is pushed aft.  A
   * folded tube of leather makes a rounded *rectangle* in plan, so it throws a
   * long point at each diagonal -- the wings that read in the three-quarter
   * views.  The aft push (cuffZ) is what puts the rim at z = -0.131 behind and
   * +0.099 in front, which is the 0.23 m span the side view measures at y = 0.20
   * and the old symmetric outline missed by 20%.
   *
   * **The two cuffs are meant to touch.**  The previous outline was pushed
   * 30 mm outboard specifically so they would not, on the theory that two 22 mm
   * cuffs cannot fit a 124 mm stance.  Measured, that was backwards: on both
   * `clay_2` and `clay_5` the boot mass is a *single* run from y = 0.20 to the
   * top of the fold -- 0.246 m across the front panel and 0.330 across the back
   * -- and the model's two separate 0.13 m runs were the single largest width
   * deviation left in the report (yaw 180, t = 0.138: ref 18.95 %H against
   * render 7.57 %H, 60 % too narrow).  So `cuffOutset` is now 8 mm, not 30, and
   * the half-widths grow by the same amount: the inboard reach passes the 0.052
   * half-stance, so the two collars overlap and read as one mass.  They are
   * unioned inside one shell, so overlapping costs nothing.
   */
function reachAt(b: BootDims, side: 1 | -1, a: number, hx: number, hz: number): number {
  const dx = Math.sin(a), dz = Math.cos(a);
  const cx = side * b.cuffOutset, cz = b.cuffZ;
  const n = b.cuffPower;
  const f = (t: number) =>
    Math.abs((dx * t - cx) / hx) ** n + Math.abs((dz * t - cz) / hz) ** n - 1;
  let lo = 0, hi = (hx + hz) * 1.6;
  for (let k = 0; k < 34; k++) {
    const m = (lo + hi) / 2;
    if (f(m) < 0) lo = m; else hi = m;
  }
  return (lo + hi) / 2;
}

/**
 * The radius of the FOLD -- the top edge of the cuff, where the leather turns
 * over.  Shared by the geometry and by the tan-lining paint mask, which is why
 * it is a function rather than a constant: they drifted apart the last time one
 * of them moved.
 *
 * ROUND 3, and this is the big one: **the fold is wider than the rim across,
 * and narrower than it fore-and-aft.**  Both earlier versions had the lateral
 * relation the wrong way round -- the collar flared downward and outward into a
 * bell -- and that is a large part of why the boots read as a splayed pancake.
 * Measured off `clay_2`, following the planted boot's own axis (which drifts
 * from x = -0.066 at y = 0.16 to -0.055 at y = 0.30 as the leg closes):
 *
 *     y      panel run            boot axis   outer reach
 *     0.20   -0.123 .. +0.061      -0.060       0.063     the hem, at its lowest
 *     0.30   -0.146 .. +0.126      -0.055       0.091     the fold
 *
 * so the lateral reach *grows* 0.063 -> 0.091 on the way up.  Fore and aft it
 * does the opposite -- `clay_0` reads the boot 0.230 deep at y = 0.195 against
 * 0.178 at 0.295 -- which is what a flap of leather folded over a shaft
 * actually does: pinched and standing between the two legs, free and flopping
 * front and back.  So two outlines, not one plus an anisotropic fudge factor.
 */
function foldR(b: BootDims, side: 1 | -1, a: number): number {
  return reachAt(b, side, a, b.foldHalfX, b.foldHalfZ);
}

/** The outer radius at the hem: tucked in across, flared out fore and aft. */
function rimR(b: BootDims, side: 1 | -1, a: number): number {
  return reachAt(b, side, a, b.rimHalfX, b.rimHalfZ);
}

function cuff(b: BootDims, side: 1 | -1): Field {
  const N = b.cuffFacets;

  /**
   * The collar is split at the lace line, so it opens into a V over the throat
   * instead of closing into a ring.  Without this the front facets sit proud of
   * the throat and hide the top third of the lacing, which is the detail the
   * front view is read on.
   */
  const notch = (a: number) => {
    const aw = Math.abs(Math.atan2(Math.sin(a), Math.cos(a)));
    // Smoothstepped, or the facets either side of the split jump from a stub to
    // a full-length flap and the opening reads as a rectangular slot punched
    // out of the collar rather than as a V.
    return 0.10 + 0.90 * smoothstep(0.17, 0.74, aw);
  };

  const plates: Field[] = [];
  for (let i = 0; i < N; i++) {
    const a = (2 * Math.PI * (i + 0.5)) / N;
    const rShaft = shaftOvalR(b, b.cuffY, a);
    // `rFold` is the collar's OUTER radius where the leather turns over and
    // `rim` its outer radius at the hem, so both plate ends are expressed on
    // the same surface.  (An older version put the plate's *centre* at
    // rShaft + half and then gave the box another `half` of thickness, which
    // pushed the outer face out by a whole cuff thickness and made the hang
    // 13 mm too deep at every height between the two.)
    //
    // `flare` is now SIGNED.  Across the boot it is negative -- the hem tucks
    // back in under a fold that stands 28 mm further out -- and fore and aft it
    // is positive, the flap swinging out as it drops.  See `foldR`: the
    // reference grows 0.063 -> 0.091 laterally on the way up and shrinks
    // 0.115 -> 0.089 fore-and-aft over the same span.
    const rim = rimR(b, side, a);
    const rFold = foldR(b, side, a);
    // A flap of leather hangs lowest where it reaches furthest, so the drop is
    // driven by how far past the shaft the *hem* gets -- which is aft, where
    // clay_0 puts the lowest point of the rim at y = 0.193.
    const g = clamp((rim - rShaft) / b.cuffFlare, 0, 1);
    // 0.86 + 0.14 g, not 0.45 + 0.55: a hollow ring only projects solid from
    // -R to +R if the ring reaches that height most of the way round.  With too
    // much of the drop on `g`, only the facets either side of dead aft reached
    // y = 0.20 and the side view read a *detached* blob with a 26 mm hole above
    // it.  And clay_2 wants the lateral wings almost as low as the back: at
    // y = 0.18-0.20 the front panel is a SINGLE run 0.171-0.183 wide, i.e. the
    // two hems already meet across the stance, where a hem that only came down
    // to 0.218 outboard left the render with two 0.092 runs and a 14 mm gap.
    const drop = b.cuffDrop * (0.86 + 0.14 * g);
    // The hem is cut into tabs rather than run round as one clean circle: the
    // reference's lower edge is a row of overhanging points, and a smooth hem
    // is the single thing that most makes a folded cuff read as a turned cone.
    // Alternating whole facets is enough at this scale -- the plates still
    // share their top edge, so the collar stays one closed ring.
    const tab = (i % b.cuffTabPeriod) < b.cuffTabPeriod / 2 ? 1 : 1 - b.cuffTabDepth;
    const n = notch(a) * tab;
    // The fold thins where it is tight and thickens where it flares.  That is
    // how a folded tube behaves, and it is also the only thing that fits two
    // 22 mm cuffs onto a 124 mm stance: the plate's inner face sits on the
    // shaft, so its outer face is at shaftR + thickness, and at full thickness
    // the two cuffs weld into one skirt across the centre line.
    // The floor on the taper is a mesher constraint, not a shape one: a plate
    // thinner than about 1.2 voxels comes out of Surface Nets as a sheet full
    // of holes, and the tight facets round the front of the collar are exactly
    // the ones with the smallest g.  0.75 of a 28 mm cuff keeps every plate at
    // least 21 mm thick, which survives the low LOD's 20.6 mm upper voxel --
    // 0.70 of 24 mm did not, and it is the thin plates that were dropping out
    // of the hem.  Thickness does not change the reach: the plate's outer face
    // is pinned to the two outlines either way, because both ends are
    // (outline - half).
    const half = b.cuffThickness * 0.5 * (0.75 + 0.25 * g);
    const rTop = rFold - half;
    // Signed, and floored well inside the shaft so a deep lateral tuck cannot
    // walk the hem through the axis and turn the plate inside out.
    const rRim = Math.max(rShaft * 0.55, rTop + (rim - rFold) * n);
    const yRim = b.cuffY - drop * n;
    const dx = Math.sin(a), dz = Math.cos(a);

    const p0: Vec3 = [dx * rTop, b.cuffY, dz * rTop + b.cuffZ];
    const p1: Vec3 = [dx * rRim, yRim, dz * rRim + b.cuffZ];
    const vx = p1[0] - p0[0], vy = p1[1] - p0[1], vz = p1[2] - p0[2];
    const len = Math.hypot(vx, vy, vz) || 1e-6;

    const ex: Vec3 = [Math.cos(a), 0, -Math.sin(a)];          // tangential
    const ey: Vec3 = [vx / len, vy / len, vz / len];          // down the slope
    const ez: Vec3 = [                                        // plate normal
      ex[1] * ey[2] - ex[2] * ey[1],
      ex[2] * ey[0] - ex[0] * ey[2],
      ex[0] * ey[1] - ex[1] * ey[0],
    ];
    // Width from this facet's own rim radius, so the ring closes where it is
    // widest without inflating the tight inboard side into a blob.  Two
    // neighbouring plates meet when wHalf >= r*sin(pi/N), which the pi*r/N term
    // already is to within half a percent; 1.15 is the whole safety margin the
    // ring needs.  Anything more and the corner of the inboard-rear plate
    // reaches across the centre line and welds the two cuffs together.
    // 1.30, not 1.15: at 1.15 the plates only just meet and the skirt bakes as
    // 22 separate corrugations.
    // The radius that sizes the plate is now the LARGER of the two ends.  With
    // the lateral hem tucked 28 mm inside the fold, sizing on `rRim` alone left
    // the plates 30 % narrower than the ring they have to close at the top, and
    // the fold came out of the bake as a row of slots.
    // 1.34, not 1.30, and with the plate blend up from 8 to 11 mm: with the hem
    // tucked in the plates run close to vertical, so their side faces point at
    // the camera instead of away from it, and the high LOD baked the collar as
    // a fluted lampshade.  Widening further (1.50 was tried) buries the flutes
    // but inflates the collar -- the boot-band width RMS over the four panels
    // that agree with each other went 0.0508 -> 0.0520 m -- so the blend does
    // the smoothing and the width only closes the gap.
    const wHalf = ((Math.PI * Math.max(rTop, rRim)) / N) * 1.34;
    const c: Vec3 = [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2];
    plates.push(orientedBox(c, ex, ey, ez, [wHalf, len / 2 + 0.005, half], 0.004));
  }
  // The fold itself: a ring of fat capsules lying along the top edge, so the
  // leather turns over a real radius instead of coming to a knife edge where
  // the plates leave the shaft.  This is the "deep floppy roll" the review
  // asked for twice; it is what stops the cuff reading as a turned cone.
  //
  // Capsules, not boxes, and sized to BRIDGE the annulus between the shaft and
  // the fold rather than to sit on its outer lip.  A box roll has a flat top
  // and two hard corners, and at the low LOD's 20.6 mm voxel those corners
  // quantise onto the same vertices as the plate below them, so the roll
  // vanishes into the cone.  Worse, now that the fold is the widest ring there
  // is 15-25 mm of flat annulus between it and the shaft, and a thin lip round
  // its edge leaves that annulus as a horizontal plate: in the three-quarter
  // views the collar read as a bucket with a lid on it.  A capsule of radius
  // (rFold - rShaft)/2 fills the annulus and its top sits 0.45 r above the
  // fold, which is the rolled-over hem the review has asked for twice.
  const roll: Field[] = [];
  for (let i = 0; i < N; i++) {
    const a0 = (2 * Math.PI * i) / N, a1 = (2 * Math.PI * (i + 1)) / N;
    const rad = (a: number) =>
      Math.max(b.cuffRoll * 0.45, (foldR(b, side, a) - shaftOvalR(b, b.cuffY, a)) * 0.5);
    const r0 = rad(a0), r1 = rad(a1);
    const p = (a: number, rr: number): Vec3 => {
      const r = foldR(b, side, a) - rr;
      return [Math.sin(a) * r, b.cuffY - rr * 0.55, Math.cos(a) * r + b.cuffZ];
    };
    roll.push(capsuleOval(p(a0, r0), p(a1, r1), r0, r1, 1.0, 1.0));
  }
  // The plates are blended, not unioned: a hard union of 22 boxes bakes as a
  // corrugated lampshade at the high LOD, where the sheet's cuff is a smooth
  // skirt with a few big creases in it.  8 mm, not 5: now that the fold is out
  // near the rim the plates are close to vertical, so their edges point at the
  // camera instead of away from it and 5 mm left the high LOD reading as a
  // pleated shade.  11 mm is still under the 12 mm tab step, so the scalloped
  // hem survives.
  return union(smoothUnion(0.011, ...plates), ...roll);
}

/**
 * The rim of the cuff, as a region: where the folded leather shows its tan
 * lining.  Geometry-free -- it only feeds `paint`.
 */
function cuffRim(b: BootDims, side: 1 | -1): Field {
  const N = b.cuffFacets;
  const bits: Field[] = [];
  for (let i = 0; i < N; i++) {
    const a = (2 * Math.PI * i) / N;
    // On the fold, not on the shaft.  While the fold sat on the shaft the two
    // were the same place; now that it is interpolated out toward the rim, a
    // mask still centred on the shaft is 15-25 mm inboard of the edge it is
    // meant to trace, and with a radial half-extent of 1.4 cuffRoll it stopped
    // being a strip and painted the whole crown of the collar tan.
    const r = foldR(b, side, a);
    const dx = Math.sin(a), dz = Math.cos(a);
    // A continuous band along the fold -- boxes with 1.6x the facet pitch, not
    // spheres.  Spheres at the facet spacing paint a dotted line: `paint` is
    // evaluated per mesh vertex, and at the upper's voxel there are only two or
    // three vertices across each sphere, so the band comes out as a scatter of
    // tan blobs instead of a stripe.
    //
    // Thin, and sitting ON the roll rather than spanning it.  The collar's top
    // is a near-horizontal annulus now that the fold is the widest ring, so a
    // mask 19 mm tall and 28 mm across caught the whole crown and painted the
    // boot an olive lid; 10 mm by 22 mm, centred 4 mm under the fold, tracks
    // the outer edge the reference shows the lining on.
    bits.push(orientedBox(
      [dx * r, b.cuffY - 0.004, dz * r + b.cuffZ],
      [Math.cos(a), 0, -Math.sin(a)], [0, 1, 0], [dx, 0, dz],
      [((Math.PI * r) / N) * 1.6, 0.005, 0.011],
    ));
  }
  return union(...bits);
}

/**
 * The toe cap and the heel counter plate, as regions: the same fields both cut
 * the geometry and paint it.
 *
 * The old version read "toe cap" as a bumper bolted across the front face and
 * built a 20 mm-tall sliver at the very bottom of the toe.  On body_0 and
 * body_2 the cap is a *plate over the toe box*: body_2 puts it between
 * y = 0.075 and 0.115 and 90 mm across, body_0 shows it wrapping forward and
 * down the front face, and it reaches back to z = 0.09 with its rivets along
 * the lower edge.  It is the single biggest light shape on the boot and leaving
 * it as a lip loses it entirely.  The two panels disagree about how low it
 * goes, so it is cut at y = 0.058, between the two readings, which leaves a
 * band of dark leather above the welt on both.
 *
 * Ellipsoids rather than boxes: a box clips the plate along a vertical plane
 * and the step reads as a saw cut, where the sheet's plate ends on a curve.
 */
function brassRegions(b: BootDims): Field {
  const zF = b.toeZ + b.upperToeProud, zB = b.heelZ;
  return union(
    ellipsoid(
      [0, b.soleTop + 0.046, zF - b.toeCapLength * 0.30],
      [b.upperHalfW - 0.008, 0.030, b.toeCapLength * 0.58],
    ),
    ellipsoid([0, b.soleTop + 0.034, zB + 0.006], [b.upperHalfW - 0.010, 0.026, 0.024]),
  );
}

function upper(b: BootDims, side: 1 | -1): Field {
  const core = upperCore(b, side);
  // A copy of the leather pushed a few millimetres out and clipped to the two
  // plate regions, so each plate stands proud with a hard edge instead of being
  // a change of colour on a smooth toe.
  const plates = intersect(offset(core, b.toeCapProud), brassRegions(b));
  return union(smoothUnion(0.010, core, cuff(b, side)), plates);
}

/* ------------------------------------------------------------------- laces */

/**
 * One lace rail up the front of the throat; `s` is -1 for the left eyelets.
 * The z values track the throat's front surface, a couple of millimetres
 * outside it so each crossing half-embeds instead of hovering.
 */
function rail(b: BootDims, side: 1 | -1, s: 1 | -1): Curve {
  const pts: Curve = [];
  const n = 8;
  // Clamped to the throat panel the rails ride on.  `frontZ` returns -1 as a
  // "no panel at this height" sentinel, and a rail point that ran past the top
  // of the throat took that -1 *as a z coordinate*: the lace tube shot a metre
  // out of the front of the boot, the shell's bounds went with it and the bake
  // came back with 15 392 lace triangles instead of 4 812.  It only showed up
  // when cuffY moved below laceTopY, which is exactly the kind of coupling a
  // spec sweep hits and a fixed spec does not.
  const y0 = b.laceBottomY, y1 = Math.min(b.laceTopY, b.cuffY - 0.006);
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    const y = y0 + (y1 - y0) * t;
    const xr = b.laceHalfSpan + 0.004 * t;
    // The rail rides the *curve* of the front panel, not its crest, and it is
    // sunk into the leather on top of that.  Sitting the cords on the crest
    // leaves them standing clear of an oval 76 mm wide, and in the side view
    // the lacing then reads as a magenta bar hanging in front of the boot --
    // and it is the lacing, not the leather, that sets the measured front edge.
    const k = clamp(xr / (b.tongueR * b.tongueSquashX), 0, 1);
    const half = b.tongueR * b.tongueSquashZ;
    // Belt and braces on the sentinel: if a rail point ever lands off both
    // panels, put it on the throat's own front face rather than at z = -1.
    const fz = frontZ(b, y);
    const zFront = fz > -0.5 ? fz : b.tongueZ1 + half;
    pts.push([
      -side * b.laceInset + s * xr,
      y,
      zFront - half * (1 - Math.sqrt(1 - k * k)) - b.laceSink,
    ]);
  }
  return pts;
}

/**
 * The X ladder.
 *
 * `curve.lacing()` is not used here, and that is the whole point of this
 * function.  It builds each rung as a straight chord between the two rails, so
 * the two cords of a crossing are *coincident* at the rung's midpoint -- they
 * meet at the same 3D point.  No voxel size separates them: the mesher welds
 * every crossing into a lump, and six crossings up a boot come out as a stack
 * of magenta rings, which is exactly what the review saw.
 *
 * Here each cord bows out of the lace plane at its midpoint, one forward and
 * one back, and which is in front alternates row by row the way a real lace
 * does.  With a 4 mm cord and a 5.5 mm bow the two tubes clear each other by
 * 3 mm, so the crossing survives down to the low LOD's voxel.
 */
function crossLacing(b: BootDims, left: Curve, right: Curve): Field {
  const segs: Field[] = [];
  const n = b.laceRows;
  const lerp = (p: Vec3, q: Vec3, k: number): Vec3 =>
    [p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k, p[2] + (q[2] - p[2]) * k];
  const at = (c: Curve, t: number): Vec3 => {
    const u = clamp(t, 0, 1) * (c.length - 1);
    const i = Math.min(c.length - 2, Math.floor(u));
    return lerp(c[i], c[i + 1], u - i);
  };
  for (let i = 0; i < n; i++) {
    const t0 = i / n, t1 = (i + 1) / n;
    const over = i % 2 === 0 ? 1 : -1;
    for (const [A, B, k] of [[left, right, over], [right, left, -over]] as [Curve, Curve, number][]) {
      const p = at(A, t0), q = at(B, t1);
      const mid: Vec3 = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2 + k * b.laceBow];
      segs.push(tube([p, mid, q], { radius: b.laceR, segments: 7 }));
    }
  }
  return union(...segs);
}

/*
 * Eyelets were tried here as a paint region -- a sphere on the leather at each
 * rail point, tagged brass.  They are not worth it: at the low LOD's 14.7 mm
 * voxel a 12 mm disc lands on one or two vertices, so instead of ten dots you
 * get a ragged gold stripe up each side of the lacing, which reads far worse
 * than plain leather.  If they come back they want geometry at the lace shell's
 * voxel, not ink at the upper's.
 */

/* -------------------------------------------------------------------- dims */

interface BootDims {
  soleTop: number; soleHalfW: number; soleWeltProud: number; archLift: number;
  toeZ: number; heelZ: number; upperHalfW: number;
  soleLap: number; soleToeInset: number; soleHeelInset: number;
  upperToeProud: number; toeBoxY: number; toeLean: number;
  vampY0: number; vampY1: number; vampZ0: number; vampZ1: number;
  vampR: number; vampSquashX: number; vampSquashZ: number; throatY0: number;
  shaftRAnkle: number; shaftRTop: number; shaftDepth: number; ankleY: number;
  cuffY: number; cuffFlare: number; cuffDrop: number; cuffThickness: number;
  cuffFacets: number; cuffZ: number; cuffRoll: number;
  cuffTabDepth: number; cuffTabPeriod: number;
  foldHalfX: number; foldHalfZ: number; rimHalfX: number; rimHalfZ: number;
  cuffOutset: number; cuffPower: number;
  toeCapLength: number; toeCapProud: number;
  tongueR: number; tongueZ0: number; tongueZ1: number;
  tongueSquashZ: number; tongueSquashX: number;
  laceRows: number; laceR: number; laceBottomY: number; laceTopY: number;
  laceHalfSpan: number; laceInset: number; laceBow: number; laceSink: number;
}

function dims(ctx: PartContext): BootDims {
  const B = nums(ctx.spec.boots);
  const L = ctx.spec.landmarks;
  return {
    soleTop: L.footBed,
    soleHalfW: B.soleHalfW,
    soleWeltProud: B.soleWeltProud,
    archLift: B.archLift,
    toeZ: B.toeZ,
    heelZ: B.heelZ,
    upperHalfW: B.upperHalfW,
    soleLap: B.soleLap,
    soleToeInset: B.soleToeInset,
    soleHeelInset: B.soleHeelInset,
    upperToeProud: B.upperToeProud,
    toeBoxY: B.toeBoxY,
    toeLean: B.toeLean,
    vampY0: B.vampY0,
    vampY1: B.vampY1,
    vampZ0: B.vampZ0,
    vampZ1: B.vampZ1,
    vampR: B.vampR,
    vampSquashX: B.vampSquashX,
    vampSquashZ: B.vampSquashZ,
    throatY0: B.throatY0,
    shaftRAnkle: B.shaftRAnkle,
    shaftRTop: B.shaftRTop,
    shaftDepth: B.shaftDepth,
    ankleY: L.ankleJoint,
    cuffY: B.cuffY,
    cuffFlare: B.cuffFlare,
    cuffDrop: B.cuffDrop,
    cuffThickness: B.cuffThickness,
    cuffFacets: Math.round(B.cuffFacets),
    cuffZ: B.cuffZ,
    cuffRoll: B.cuffRoll,
    cuffTabDepth: B.cuffTabDepth,
    cuffTabPeriod: Math.max(2, Math.round(B.cuffTabPeriod)),
    foldHalfX: B.foldHalfX,
    foldHalfZ: B.foldHalfZ,
    rimHalfX: B.rimHalfX,
    rimHalfZ: B.rimHalfZ,
    cuffOutset: B.cuffOutset,
    cuffPower: B.cuffPower,
    toeCapLength: B.toeCapLength,
    toeCapProud: B.toeCapProud,
    tongueR: B.tongueR,
    tongueZ0: B.tongueZ0,
    tongueZ1: B.tongueZ1,
    tongueSquashZ: B.tongueSquashZ,
    tongueSquashX: B.tongueSquashX,
    laceRows: Math.round(B.laceRows),
    laceR: B.laceR,
    laceBottomY: B.laceBottomY,
    laceTopY: B.laceTopY,
    laceHalfSpan: B.laceHalfSpan,
    laceInset: B.laceInset,
    laceBow: B.laceBow,
    laceSink: B.laceSink,
  };
}

/* ------------------------------------------------------------------- part */

export const bootsPart: PartModule = {
  id: 'boots',
  build(ctx) {
    const { mat } = ctx;
    const b = dims(ctx);
    const sides: (1 | -1)[] = [1, -1];

    const soleField = union(...sides.map((s) => place(sole(b), ctx, s)));
    const upperField = union(...sides.map((s) => place(upper(b, s), ctx, s)));
    const capMask = union(...sides.map((s) => place(brassRegions(b), ctx, s)));
    const rimMask = union(...sides.map((s) => place(cuffRim(b, s), ctx, s)));
    const laceField = union(
      ...sides.map((s) => place(crossLacing(b, rail(b, s, -1), rail(b, s, 1)), ctx, s)),
    );

    const shells: Shell[] = [
      {
        name: 'bootSole',
        field: soleField,
        // clothWorn, not cloth: the reference's sole is a warm near-black, and
        // cloth's blue cast is a good part of why the slab read as a grey brick
        // parked under the boot.
        material: constMaterial(mat.clothWorn),
        // 1.7 put the sole's whole visible height inside two voxels, so the
        // welt and the lap over the leather both quantised away.  1.15 keeps
        // them and still costs under 2 k triangles at low.
        voxelScale: 1.15,
      },
      {
        name: 'bootUpper',
        field: upperField,
        // The cap is geometry *and* ink: the plate stands proud of the leather,
        // and everything inside its region takes brass, so the step edge is a
        // hard line rather than a brass smear halfway down the toe.  The cuff's
        // fold takes the tan lining the same way, without a triangle.
        material: paint(
          paint(constMaterial(mat.leather), capMask, mat.brass, 0.0),
          rimMask, mat.canvas, 0.0,
        ),
        voxelScale: 1.4,
      },
      {
        name: 'bootLace',
        field: laceField,
        // There is no magenta in spec.materials and the palette is not mine to
        // extend; `pants` is the closest hue to the reference's pink laces.
        material: constMaterial(mat.pants),
        // 4 mm cord wants a voxel near half its radius or the bow that keeps
        // the two cords of a crossing apart is quantised out and they weld.
        voxelScale: 0.45,
      },
    ];
    return shells;
  },
};
