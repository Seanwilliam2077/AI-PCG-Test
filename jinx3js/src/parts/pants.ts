/**
 * The purple pinstripe capris.
 *
 * Built as one solid garment rather than a hollow shell: the wall the reference
 * shows is 10-12 mm, which is a single voxel at the low LOD, and a one-voxel
 * wall meshes as speckle.  A solid whose outer surface is the cloth reads the
 * same from outside -- the waist cap sits inside the pelvis and the hem cap
 * inside the calf -- and it halves the triangle count.
 *
 * The shape is the body's own leg section (the same thigh/knee/calf radii AND
 * the same z-squash body.ts uses) pushed out by a flare curve, so the trousers
 * can never interpenetrate the skin however the widths are retuned.  The flare
 * is widest over the seat and hip, where the reference blouses, and is a flat
 * 6 mm from mid-thigh to the hem.
 *
 * ROUND 2.  The legs were 17-19 mm off the skin, which read as jodhpurs: the
 * back view measured +22 % on the core run at the knee and the two side views
 * +34 to +39 % on the leg's depth.  Re-measured off `body_2.png`, whose matte
 * (unlike `clay_2.png`) keeps the inseam gap open, her right leg is trousered
 * to these half-widths, against the radius body.ts carries at the same height:
 *
 *     y      ref half-width   body leg radius   difference
 *     0.50      0.0530            0.0464          +0.0066
 *     0.58      0.0546            0.0490          +0.0056
 *     0.62      0.0563            0.0506          +0.0057
 *     0.66      0.0580            0.0523          +0.0057
 *     0.70      0.0572            0.0539          +0.0033
 *     0.74      0.0622            0.0556          +0.0066
 *
 * so the flare over the leg is +6 mm, not +17.  Her LEFT leg measures 0.042 to
 * 0.049 over the same range, i.e. 5-8 mm *inside* the body's own radius; that
 * is the reference's leg-to-leg asymmetry (axes -0.0885 / +0.048 against a
 * symmetric stance of +/-0.062), not a negative flare, and a symmetric build
 * can only sit on one of the two.  The scoreboard's width term reads the
 * *widest* run, which is her right leg, so 6 mm is the number to hold.
 *
 * The tattered hem is a cut, not modelled teeth: the garment is intersected
 * with `y > hemLine(azimuth)`, where hemLine is a saw of eight teeth per leg
 * whose boundaries, tip position and depth all jitter per tooth, so the teeth
 * lean and vary in width the way the reference's rag does rather than reading
 * as a regular zig-zag.  It is the one part of this field that is not an exact
 * distance function, and `lip` is raised to match: the azimuth's gradient goes
 * as 1/r, so the tooth amplitude is faded out below RMIN of the leg axis --
 * round 1 computed that clamp and then never used it, leaving the field's
 * gradient unbounded on the axis.
 *
 * Measured off ref/views/body_2.png and body_5.png with a metre grid:
 *   waistband on the +X hip      y = 1.086
 *   hem, her right leg, front    y = 0.442 .. 0.520   (deepest teeth ~75 mm)
 *   hem, her left leg, front     y = 0.486 .. 0.556
 *   hem, her left leg, side      y = 0.450 .. 0.490   (so the front rides high)
 *   pinstripe pitch, mid-thigh   21 mm of arc, ~9 stripes across the front
 *
 * ROUND 3.  Three things, all measured on the CLAY panels (the geometry target)
 * with tools/pants_probe.py, which normalises exactly as compare.py does, and
 * against the pants-only render read in world metres by tools/pants_abs.py.
 * The full tables are in spec/parts/pants.json.
 *
 * 1. THE SECTION WAS TOO DEEP BELOW THE KNEE, not too shallow.  The round-2
 *    brief read the side views at t = 0.44 and 0.51 -- y = 0.75 and 0.88 -- and
 *    called the leg 40 % shallow.  At those heights `clay_4`'s single run is the
 *    whole hip with her braids and the Zapper in it, not a leg.  Where the leg
 *    IS separable the numbers go the other way: 101 / 99 / 116 / 138 mm of run
 *    at y = 0.55 / 0.60 / 0.65 / 0.70 against the render's 133 / 133 / 133 /
 *    139.  The trouser carried no taper in z at all, because one `flare` number
 *    was added to a section that is already 18 % deeper than wide.  `flareZ`
 *    splits that standoff out and takes it to 1 mm at the calf.
 *
 * 2. THE LEG PAIR WAS 25 mm NARROW ACROSS.  clay_2 and clay_5 agree on the
 *    outer-edge-to-outer-edge span -- 0.232/0.237, 0.229/0.234, 0.234/0.240 at
 *    y = 0.50/0.55/0.60 -- against 0.209/0.209/0.218 rendered, while clay_5's
 *    open matte puts the gap between the legs at 42-45 mm where the render has
 *    43.  So the gap was right and each leg was ~13 mm short on its OUTER edge.
 *    `legOut` hangs the tube that far outboard AND widens it by the same, which
 *    moves the outer edge by twice it and leaves the inner edge exactly where
 *    the flare had put it.
 *
 * 3. THE RAG WAS 28 mm TOO HIGH, and had been since round 1: the two hem
 *    numbers above are FRONT readings, and the build spends them as if they
 *    were the BACK, then adds `tatterFrontRise` on top.  hemY 0.466 -> 0.438.
 *
 * Ablated back to back against the same checkout (tools/pants_sweep.py, five
 * whole-figure bakes so no other author's edit could drift between them):
 * `legOut` is worth +0.24 score and +0.0038 mean IoU -- yaw 0 IoU 0.8535 ->
 * 0.8613 and its width rms 1.82 -> 1.36 -- and the other two are inside the
 * +/-0.09 noise but land on measurements, so they stay.
 *
 * NOT FIXED HERE, and both belong to other files:
 *   - the leg is still ~25 mm too deep at the calf because body.ts's shin is,
 *     at squashZ 1.18/1.14; the trouser is only 2 mm proud of it and cannot go
 *     inside without showing skin through the cloth.
 *   - `body.json blendLeg 0.028` smooth-unions the two legs into one mass, so
 *     the render's silhouette never opens between them.  clay_5 carries a
 *     42-45 mm gap from y = 0.49 to 0.75 and compare.py's width term therefore
 *     reads the reference's core as ONE leg and ours as the merged pair, which
 *     is the whole of the "+90 to +127 %" in the yaw 180 column.
 */
import { Box, Field, Vec3, box } from '../sdf/types.js';
import {
  capsuleOval,
  clamp,
  ellipsoid,
  field,
  intersect,
  mix,
  smoothUnion,
  smoothstep,
  subtract,
} from '../sdf/ops.js';
import { loftY } from '../sdf/solids.js';
import { PartContext, PartModule, Shell, constMaterial, paint } from './types.js';
import { torsoHalfWidth } from '../spec.js';

/** The slice of the spec this part owns; see spec/parts/pants.json. */
export interface PantsSpec {
  waistY: number;
  waistFrontDrop: number;
  hemY: number;
  hemSideOffset: [number, number];
  crotchY: number;
  inseamApexY: number;
  inseamR: number;
  inseamMidY: number;
  inseamBaseY: number;
  thickness: number;
  flare: [number, number][];
  flareZ: [number, number][];
  legOut: [number, number][];
  seatBulge: number;
  stripePitch: number;
  stripeDuty: number;
  stripeLegR: number;
  stripeHipR: number;
  tatterDepth: number;
  tatterCount: number;
  tatterFrontRise: number;
  voxelScale: number;
}

export const pantsSpec = (ctx: PartContext): PantsSpec =>
  ctx.spec.pants as unknown as PantsSpec;

/** Smooth piecewise lookup through a [height, value] table. */
function table(tbl: [number, number][], y: number): number {
  if (y <= tbl[0][0]) return tbl[0][1];
  const last = tbl[tbl.length - 1];
  if (y >= last[0]) return last[1];
  for (let i = 1; i < tbl.length; i++) {
    if (y <= tbl[i][0]) {
      const [y0, v0] = tbl[i - 1];
      const [y1, v1] = tbl[i];
      const t = (y - y0) / Math.max(1e-6, y1 - y0);
      return mix(v0, v1, t * t * (3 - 2 * t));
    }
  }
  return last[1];
}

/** How far the cloth stands off the skin ACROSS (x) at a height. */
export const flareAt = (ctx: PartContext, y: number): number =>
  table(pantsSpec(ctx).flare, y);

/**
 * How far it stands off FRONT-TO-BACK (z).  Round 2 used one number for both,
 * which is what made the leg section too deep: the body's own shin is 18 %
 * deeper than wide (body.ts passes squashZ 1.18 below the knee), so a flat
 * 6 mm standoff on top of that put the trouser 133 mm deep at y = 0.55 where
 * `clay_4` measures the whole leg run at 101 mm.  The two now taper apart --
 * the cloth stands proud over the seat and the thigh and lies on the shin.
 */
export const flareZAt = (ctx: PartContext, y: number): number => {
  const P = pantsSpec(ctx);
  return table(P.flareZ ?? P.flare, y);
};

/**
 * How far outboard of the bone the trouser leg hangs.  A capri is not a sock:
 * it drapes to the OUTSIDE of the leg, and the inseam is where the cloth is
 * pulled tight.  Adding this to the tube's half-width AND to its centre moves
 * only the outer edge -- the inner edge stays exactly `flare` outside the skin,
 * so nothing is exposed at the inner thigh and the inseam gap is untouched.
 */
export const legOutAt = (ctx: PartContext, y: number): number => {
  const P = pantsSpec(ctx);
  return P.legOut ? table(P.legOut, y) : 0;
};

/**
 * The leg centreline at a height, following hip -> knee -> ankle.  Above the
 * hip joint it holds the hip's x so the trouser leg runs straight into the
 * seat instead of shearing.
 */
export function legAxis(ctx: PartContext, side: 1 | -1, y: number): [number, number] {
  const { skel } = ctx;
  const hip = side > 0 ? skel.hipL : skel.hipR;
  const knee = side > 0 ? skel.kneeL : skel.kneeR;
  const ankle = side > 0 ? skel.ankleL : skel.ankleR;
  if (y >= hip[1]) return [hip[0], hip[2]];
  if (y >= knee[1]) {
    const t = (hip[1] - y) / Math.max(1e-6, hip[1] - knee[1]);
    return [mix(hip[0], knee[0], t), mix(hip[2], knee[2], t)];
  }
  const t = clamp((knee[1] - y) / Math.max(1e-6, knee[1] - ankle[1]), 0, 1);
  return [mix(knee[0], ankle[0], t), mix(knee[2], ankle[2], t)];
}

/**
 * The trouser leg's centreline, `legOut` metres outboard of the bone.
 * Everything that has to stay concentric with the cloth -- the loft, the
 * tattered hem's azimuth -- takes this rather than `legAxis`.
 */
export function tubeAxis(ctx: PartContext, side: 1 | -1, y: number): [number, number] {
  const [ax, az] = legAxis(ctx, side, y);
  return [ax + side * legOutAt(ctx, y), az];
}

/**
 * The body's own leg half-width in x at a height -- the same profile body.ts
 * builds.  `capsuleOval(a, b, r0, r1, squashZ, squashX)` takes the *z* squash
 * fifth, and body.ts passes squashX = 1, so this radius is the x half-width
 * exactly and the depth is this times `bodySquashZ`.
 *
 * ROUND 3.  This took `skel.hipL`/`skel.kneeL` and `landmarks.calf` for BOTH
 * legs, so the pose's 47 mm foot lift went straight through it: at a given
 * height her lifted left leg was handed the planted right leg's radius, and the
 * contrapposto could not show in the garment however the skeleton moved.  Every
 * breakpoint now comes from that side's own joints, and the calf belly is
 * measured DOWN FROM THE ANKLE the way body.ts measures its own.
 */
export function bodyLegR(ctx: PartContext, side: 1 | -1, y: number): number {
  const { spec: s, skel } = ctx;
  const w = s.widths, L = s.landmarks;
  const hip = side > 0 ? skel.hipL : skel.hipR;
  const knee = side > 0 ? skel.kneeL : skel.kneeR;
  const ankle = side > 0 ? skel.ankleL : skel.ankleR;
  const hipY = hip[1] + 0.02;
  const kneeY = knee[1];
  const calfY = ankle[1] + (L.calf + 0.045 - L.ankleJoint);
  if (y >= hipY) return w.thighR;
  if (y >= kneeY) return mix(w.thighR, w.kneeR, (hipY - y) / Math.max(1e-6, hipY - kneeY));
  if (y >= calfY) return mix(w.kneeR * 0.94, w.calfR, (kneeY - y) / Math.max(1e-6, kneeY - calfY));
  return w.calfR;
}

/**
 * How much deeper than wide the body's leg is at a height: 1.06 down the thigh
 * and 1.18 through the calf, the two squash factors body.ts passes.  Round 1
 * lofted the trouser at a flat 1.05, so below the knee the cloth was 6 mm
 * shallower than the shin inside it -- invisible only because the flare was
 * 17 mm.  Matching it is what lets the flare come down to 6 mm without the
 * calf breaking out through the back of the trouser leg.
 */
export function bodySquashZ(ctx: PartContext, side: 1 | -1, y: number): number {
  const kneeY = (side > 0 ? ctx.skel.kneeL : ctx.skel.kneeR)[1];
  return mix(1.18, 1.06, smoothstep(kneeY - 0.035, kneeY + 0.035, y));
}

/** Half-extents of the seat block of the trousers at a height. */
export function pantsOuterHalf(ctx: PartContext, y: number): { x: number; z: number } {
  const t = torsoHalfWidth(y, ctx.spec);
  const f = flareAt(ctx, y);
  return { x: t.x + f, z: t.z + f };
}

/* ------------------------------------------------------------------ */

/**
 * One trouser leg: the body's own section, offset outward by the flare, lofted
 * along the leg bones.
 *
 * Round 1 stacked ten capsules 62 mm apart and welded them with
 * `smoothUnion(0.03)`.  That blend is a max-radius operator on nearly colinear
 * solids, so it inflated the tube by a further 3-7 mm on top of the flare --
 * probed at y = 0.58 the leg came out 0.0728 half-wide where the capsules
 * asked for 0.0660.  `loftY` samples every 10 mm instead, which needs almost no
 * blend to stay smooth, so the number in the spec is the number on the surface.
 */
function legTube(ctx: PartContext, side: 1 | -1): Field {
  const P = pantsSpec(ctx);
  const top = P.crotchY + 0.09;
  const bot = P.hemY - 0.05;
  return loftY(
    top,
    bot,
    (y) => {
      const [ax, az] = tubeAxis(ctx, side, y);
      const r = bodyLegR(ctx, side, y);
      const out = legOutAt(ctx, y);
      // The flare is a standoff, not a scale: adding it after the squash keeps
      // the same millimetres of cloth over the shin as over the thigh.  `out`
      // is added to the half-width and to the centre alike, which pushes the
      // outer edge by 2*out and leaves the inner edge where it was.
      return {
        x: r + flareAt(ctx, y) + out,
        z: r * bodySquashZ(ctx, side, y) + flareZAt(ctx, y),
        cx: ax,
        cz: az,
      };
    },
    { step: 0.010, blend: 0.006 },
  );
}

/** The seat and hips: the torso profile pushed out by the flare. */
function pelvis(ctx: PartContext): Field {
  const P = pantsSpec(ctx);
  const { spec: s, skel } = ctx;
  const ys = [P.crotchY, 0.945, 0.985, 1.025, 1.06, P.waistY + 0.012];
  const segs: Field[] = [];
  for (let i = 1; i < ys.length; i++) {
    const y0 = ys[i - 1], y1 = ys[i];
    const a = pantsOuterHalf(ctx, y0);
    const b = pantsOuterHalf(ctx, y1);
    const squash = (a.z / a.x + b.z / b.x) / 2;
    segs.push(capsuleOval([0, y0, 0], [0, y1, 0], a.x, b.x, squash, 1));
  }
  // The reference blouses over the buttock; without it the back view reads as
  // a cylinder and the sash has nothing to sit on.
  const gy = s.landmarks.crotch + 0.062;
  const gz = -s.widths.hipHalfD * 0.34;
  const gr: Vec3 = [0.076, 0.072, 0.066 + P.seatBulge];
  const seatL = ellipsoid([skel.hipL[0], gy, gz], gr);
  const seatR = ellipsoid([skel.hipR[0], gy, gz], gr);

  // Small k: the sections are colinear, so a wide blend only fattens the hips.
  const stack = smoothUnion(0.022, ...segs, seatL, seatR);
  // Flat-bottom the pelvis so its end cap does not balloon down through the
  // crotch; the leg tubes carry everything below.  Cut fields are negative
  // inside the half they keep, because intersect() is a max.
  const b = stack.bounds;
  const floor = field((_x, y) => P.crotchY - y, box([b.min[0], P.crotchY, b.min[2]], b.max));
  return intersect(stack, floor);
}

/**
 * The inseam: a slot between the legs, opening downward from the crotch and
 * then holding a constant width.  It has to cut the whole depth of the
 * garment, front to back -- a cone about the vertical axis only carves the
 * middle of the crotch and leaves the front of the trousers bridged, which
 * reads as a skirt.  Written as |x| - halfWidth(y) so it stays close to a true
 * distance and the gap can widen and then stop, which a single cone cannot do.
 */
function inseam(ctx: PartContext): Field {
  const P = pantsSpec(ctx);
  const apex = P.inseamApexY, midY = P.inseamMidY, R = P.inseamR;
  const halfWidth = (y: number): number => {
    if (y >= apex) return -(y - apex) * 0.4;
    if (y >= midY) return (R * (apex - y)) / (apex - midY);
    return R;
  };
  return field(
    (x, y) => Math.abs(x) - halfWidth(y),
    box([-R - 0.02, P.inseamBaseY - 0.05, -0.3], [R + 0.02, apex + 0.05, 0.3]),
    Math.hypot(1, 0.4),
  );
}

/** Waistband: a plane that dips toward the front, as the low rise does. */
function waistCut(ctx: PartContext, b: Box): Field {
  const P = pantsSpec(ctx);
  const kz = P.waistFrontDrop / 0.095;
  const lip = Math.hypot(1, kz);
  const top = P.waistY + kz * Math.abs(b.min[2]) + 0.01;
  return field(
    (_x, y, z) => y - (P.waistY - kz * z),
    box(b.min, [b.max[0], Math.min(b.max[1], top), b.max[2]]),
    lip,
  );
}

/**
 * The tattered hem.  Negative above the ragged line, so intersecting keeps the
 * garment.  The line is a saw in the azimuth about the leg axis, lifted at the
 * front where the reference hem rides ~35 mm higher than at the side.
 *
 * Round 1 made this an even triangle wave with a per-tooth depth jitter only,
 * which reads as a regular zig-zag: every tooth the same width, every tooth
 * symmetric.  The reference's rag does none of that -- on `body_2` her right
 * leg shows three or four teeth across the front of one leg, of visibly
 * different widths, and each leans one way or the other.  So each tooth now
 * carries three jitters: where its boundary falls (+/-0.22 of a tooth, which
 * still leaves every tooth at least 0.56 wide), where its tip sits inside it
 * (0.30 to 0.70, the lean), and how deep it cuts (0.40 to 1.00 of the depth).
 * The line is still exactly zero at every boundary, so it stays continuous.
 *
 * The amplitude fades out inside RMIN of the leg axis.  The azimuth's gradient
 * goes as 1/r, so without that fade the field's true Lipschitz bound is
 * unbounded on the axis whatever `lip` claims -- round 1 computed the clamp and
 * then never referenced it, which is the classic way to get speckled holes at a
 * coarse LOD.
 */
function hemCut(ctx: PartContext, b: Box): Field {
  const P = pantsSpec(ctx);
  const N = P.tatterCount;
  const depth = P.tatterDepth;
  const rise = P.tatterFrontRise;
  const RMIN = 0.050;
  const TAU = Math.PI * 2;
  const SKEW = 0.22;        // boundary jitter, in teeth
  const LEAN = 0.20;        // tip offset from centre, as a fraction of the tooth

  /** Deterministic hash in [0, 1) for tooth `i` of `side`, channel `k`. */
  const rnd = (i: number, side: number, k: number) => {
    const h = Math.sin(i * 12.9898 + side * 78.233 + k * 37.719) * 43758.5453;
    return h - Math.floor(h);
  };
  /** Where tooth `i` starts, in tooth units. Monotone: |offset| <= SKEW < 0.5. */
  const edge = (i: number, side: number) => i + SKEW * (2 * rnd(i, side, 0) - 1);

  const hemLine = (x: number, y: number, z: number): number => {
    const side: 1 | -1 = x >= 0 ? 1 : -1;
    const [ax, az] = tubeAxis(ctx, side, y);
    const dx = x - ax, dz = z - az;
    const r = Math.hypot(dx, dz);
    const th = Math.atan2(dx, dz);            // 0 at the front, +/-pi at the back
    const base = P.hemY + P.hemSideOffset[side > 0 ? 1 : 0] + depth
      + rise * (0.5 + 0.5 * Math.cos(th));
    const u = (th / TAU) * N + (side > 0 ? 0.37 : 0.11);

    // Which tooth holds u.  Boundaries move by less than half a tooth, so the
    // candidate is floor(u) or one of its neighbours.
    let i = Math.floor(u);
    if (u < edge(i, side)) i -= 1;
    else if (u >= edge(i + 1, side)) i += 1;
    const u0 = edge(i, side), u1 = edge(i + 1, side);
    const f = clamp((u - u0) / (u1 - u0), 0, 1);

    const p = 0.5 + LEAN * (2 * rnd(i, side, 1) - 1);       // tip position, leans
    const tri = f < p ? f / p : (1 - f) / (1 - p);          // 0 at the edges, 1 at the tip
    const deep = 0.40 + 0.60 * rnd(i, side, 2);
    const fade = clamp(r / RMIN, 0, 1);                     // bounds the 1/r gradient
    return base - depth * deep * tri * fade;
  };

  // |grad| = sqrt(1 + |d hemLine/d theta|^2 / r^2 + |d hemLine/d r|^2).  The
  // steepest tooth flank is 1/(1/2 - LEAN) per unit f over a tooth at least
  // (1 - 2*SKEW) wide, and there are N/TAU teeth per radian.
  const perTooth = 1 / (0.5 - LEAN) / (1 - 2 * SKEW);
  const slope = depth * perTooth * (N / TAU) + rise * 0.5;
  const lip = Math.hypot(1, slope / RMIN, depth / RMIN) * 1.1;
  const lo = P.hemY + Math.min(P.hemSideOffset[0], P.hemSideOffset[1]) - 0.01;
  return field(
    (x, y, z) => hemLine(x, y, z) - y,
    box([b.min[0], Math.max(b.min[1], lo), b.min[2]], b.max),
    lip,
  );
}

/**
 * The pinstripes, as a material region rather than geometry.  The phase is arc
 * length around the local vertical axis -- the leg axis below the crotch,
 * blending to the body axis at the waist -- so the pitch stays 21 mm of fabric
 * everywhere and the stripes converge down the tapering calf the way printed
 * cloth does.
 */
export function stripeField(ctx: PartContext, b: Box, hip = false): Field {
  const P = pantsSpec(ctx);
  const L = ctx.spec.landmarks;
  const pitch = P.stripePitch;
  const half = P.stripeDuty * 0.5;
  // The arc is measured with a *constant* reference radius. Anything that
  // varies with height -- the sample's own radius, or the section's mean --
  // shifts the phase at the back seam as the leg tapers, and the stripes fan
  // out into nested chevrons across the seat. A constant keeps every stripe
  // dead vertical and leaves one seam per column, which is what the garment
  // really has; the pitch on the surface then breathes with the radius, wider
  // over the hip and finer at the hem, exactly as printed cloth does.
  const ref = hip ? P.stripeHipR : P.stripeLegR;
  return field((x, y, z) => {
    const side: 1 | -1 = x >= 0 ? 1 : -1;
    const t = hip ? 0 : smoothstep(L.iliac, L.crotch, y);
    const [lx, lz] = legAxis(ctx, side, y);
    const dx = x - lx * t, dz = z - lz * t;
    const arc = Math.atan2(dx, dz) * ref;
    const q = arc / pitch;
    const f = q - Math.floor(q);
    return (Math.abs(f - 0.5) - half) * pitch;
  }, b, 6);
}

/**
 * The whole trouser volume before the waist and hem are cut off it.  The sash
 * lies on this rather than on a guessed oval: below the crotch the garment's
 * cross-section is two tubes, not an ellipse, and an oval mandrel there either
 * sinks into the thigh or floats 40 mm off the front of the crotch.
 */
export function pantsBody(ctx: PartContext): Field {
  const solid = smoothUnion(
    0.026,
    pelvis(ctx),
    legTube(ctx, 1),
    legTube(ctx, -1),
  );
  return subtract(solid, inseam(ctx));
}

export const pantsPart: PartModule = {
  id: 'pants',
  build(ctx) {
    const { mat } = ctx;
    const P = pantsSpec(ctx);

    const parted = pantsBody(ctx);
    const b = parted.bounds;
    const cut = intersect(intersect(parted, waistCut(ctx, b)), hemCut(ctx, b));

    const material = paint(constMaterial(mat.pants), stripeField(ctx, b), mat.pantsDark, 0);

    return [{ name: 'pants', field: cut, material, voxelScale: P.voxelScale }];
  },
};
