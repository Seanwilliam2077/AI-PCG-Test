/**
 * The body under the clothes: torso, neck, shoulder yoke, arms, hands, legs.
 *
 * The trunk is an elliptical loft through the measured landmark heights, so the
 * silhouette is driven entirely by `spec.widths` via `torsoHalfWidth()` -- and,
 * crucially, the meshed surface lands *on* that profile rather than somewhere
 * outside it.  That is not free: the obvious construction (a stack of capsule
 * sections joined with `smoothUnion`) inflates.  Each section overlaps its
 * neighbours, so at almost every point two or three of them report nearly the
 * same distance, `smin` subtracts up to k each time, and the fixed point of
 * that recursion over a long stack is a full k of radius everywhere.  Measured
 * on the previous build: +13 mm of half-width and +14 mm of half-depth at every
 * height, which is what welded the arms to the ribs, filled in the waist and
 * turned the top of the column into a 220 mm ball where the neck should be.
 *
 * So the trunk is one field instead of a stack: an ellipse whose half-axes are
 * functions of height, evaluated by radial scaling.  It is exact in the
 * horizontal plane, has no section-to-section rings to blend away, is cheaper,
 * and it under-estimates distance everywhere (proved in `loftEllipse`), which
 * is what the mesher's empty-space skipping needs.
 *
 * Nothing here knows about clothing -- every garment is its own shell sitting
 * just outside this one -- but the whole body is still built even where it is
 * covered, because the review loop compares silhouettes.
 */
import { Field, Vec3, box } from '../sdf/types.js';
import { capsuleOval, ellipsoid, field, smoothUnion, subtract, union, capsule } from '../sdf/ops.js';
import { PartContext, PartModule, Shell, constMaterial, paint, nums } from './types.js';
import { tattooField } from './tattoo.js';
import { torsoHalfWidth } from '../spec.js';

/** Half-width in x, half-depth in z, and the section's centre in z. */
interface Section { x: number; z: number; cz: number }

/**
 * Monotone cubic Hermite (Fritsch-Carlson) through a column of the key table.
 *
 * Interpolating each pair of keys with an independent smoothstep is C1 but its
 * *curvature* jumps at every key, and on a shape this smooth that reads as a
 * hard shading line right across the chest and the upper back -- two of them,
 * at the two keys where the taper changes pace.  Fritsch-Carlson gives each
 * key a tangent from both of its neighbours, so the curvature stays bounded,
 * and it clamps that tangent so the curve never overshoots into a bulge.
 * The end tangents are pinned to zero because `torsoHalfWidth()` hands over at
 * a landmark, where its own smoothstep has zero slope.
 */
function hermiteColumn(keys: number[][], col: number): (y: number) => number {
  const n = keys.length;
  const h: number[] = [], d: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    h.push(keys[i + 1][0] - keys[i][0]);
    d.push((keys[i + 1][col] - keys[i][col]) / (keys[i + 1][0] - keys[i][0]));
  }
  const m: number[] = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) {
    if (d[i - 1] * d[i] <= 0) { m[i] = 0; continue; }
    const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1];
    m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]);
  }
  return (y: number) => {
    if (y <= keys[0][0]) return keys[0][col];
    if (y >= keys[n - 1][0]) return keys[n - 1][col];
    let i = 0;
    while (i < n - 2 && y > keys[i + 1][0]) i++;
    const t = (y - keys[i][0]) / h[i], t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * keys[i][col]
      + (t3 - 2 * t2 + t) * h[i] * m[i]
      + (-2 * t3 + 3 * t2) * keys[i + 1][col]
      + (t3 - t2) * h[i] * m[i + 1];
  };
}

/**
 * The trunk's section at a height.
 *
 * Below `yokeY0` this is exactly `torsoHalfWidth()`, which is the contract every
 * clothing part fits against.  Above it the spec's own table runs out -- its
 * last key is a hemisphere of radius `neckR * 1.9` at `neckBase`, i.e. a 137 mm
 * ball where the throat is -- so the shoulder yoke and the neck column are
 * carried by `body.yoke`, measured off clay_2 / clay_0 (see the report).
 */
function sectionFn(ctx: PartContext, keys: number[][]): (y: number) => Section {
  const s = ctx.spec;
  const L = s.landmarks;
  const fx = hermiteColumn(keys, 1);
  const fz = hermiteColumn(keys, 2);
  const fc = hermiteColumn(keys, 3);
  const y0 = keys[0][0];
  const b = nums(s.body as unknown as Record<string, unknown>);
  // `torsoHalfWidth` clamps to its lowest key below the crotch, so the column
  // ends in a flat disc 180 mm across and 180 mm deep sitting on nothing: a
  // horizontal ledge under the pelvis that catches a hard shadow in the front
  // view.  Round it off instead, over the last 58 mm, down to something small
  // enough to hide inside the thighs.
  const taperTop = L.crotch + b.crotchTaperTop;
  return (y: number) => {
    if (y <= y0) {
      const t = torsoHalfWidth(y, s);
      const lean = s.pose.spineLean * ((y - L.crotch) / Math.max(1e-6, L.neckBase - L.crotch));
      const u = (taperTop - y) / b.crotchTaper;
      const k = u <= 0 ? 1 : Math.sqrt(Math.max(0.06, 1 - u * u));
      return { x: t.x * k, z: t.z * k, cz: lean };
    }
    return { x: fx(y), z: fz(y), cz: fc(y) };
  };
}

/**
 * An elliptical loft along Y, evaluated by radial scaling against a *constant*
 * scale `m`.
 *
 * `d = (hypot(x/X, (z-cz)/Z) - 1) * m` with `m <= min(X, Z)` everywhere.
 * Outside, the true distance to the ellipse in that direction is `r - R`, and
 * `(r/R - 1) * m <= r - R` whenever `m <= R`, so `d` never over-estimates;
 * inside, `m * (1 - r/R) <= R - r` for the same reason.  A constant `m` also
 * keeps the vertical gradient clean -- with `m(y)` the `(q-1)*m'` term grows
 * with distance from the axis and the Lipschitz bound stops being knowable --
 * so `lip` here is just `hypot(1, maxSlope)`, with `maxSlope` sampled off the
 * profile rather than guessed.
 */
function loftEllipse(y0: number, y1: number, at: (y: number) => Section): Field {
  const n = Math.max(8, Math.round((y1 - y0) / 0.0005));
  let m = Infinity, maxX = 0, maxZ = 0, slope = 0;
  let prev = at(y0);
  for (let i = 0; i <= n; i++) {
    const y = y0 + ((y1 - y0) * i) / n;
    const s = at(y);
    m = Math.min(m, s.x, s.z);
    maxX = Math.max(maxX, s.x);
    maxZ = Math.max(maxZ, Math.abs(s.cz) + s.z);
    if (i > 0) {
      const dy = (y1 - y0) / n;
      slope = Math.max(
        slope,
        Math.max(Math.abs(s.x - prev.x), Math.abs(s.z - prev.z)) / dy
          + Math.abs(s.cz - prev.cz) / dy,
      );
    }
    prev = s;
  }
  const lip = Math.hypot(1, slope) * 1.1;
  return field(
    (x, y, z) => {
      const yc = y < y0 ? y0 : y > y1 ? y1 : y;
      const s = at(yc);
      const u = x / s.x, v = (z - s.cz) / s.z;
      const radial = (Math.hypot(u, v) - 1) * m;
      const axial = Math.max(y0 - y, y - y1);
      // Flat ends, not rounded: `min(max(a,b),0) + hypot(max(a,0), max(b,0))`.
      // The rounded form leaves the column running on past y1 for another `m`
      // of height, which put a 41 mm bullet on top of the neck.
      return Math.min(Math.max(radial, axial), 0)
        + Math.hypot(Math.max(radial, 0), Math.max(axial, 0));
    },
    box([-maxX, y0, -maxZ], [maxX, y1, maxZ]),
    lip,
  );
}

/**
 * The trunk, split at the yoke so the steep neck taper pays its own `lip`.
 *
 * The two halves share one profile function and overlap by 10 mm, so a plain
 * `union` is seamless -- and it has to be plain: a `smoothUnion` between two
 * fields that agree over a whole band subtracts k/4 across that band and leaves
 * a ridge round the chest exactly where the join is.
 */
function trunk(ctx: PartContext): { field: Field; at: (y: number) => Section } {
  const raw = ctx.spec.body as unknown as Record<string, unknown>;
  const b = nums(raw);
  const yoke = raw.yoke as number[][];
  const L = ctx.spec.landmarks;
  const y0 = b.yokeY0;
  const top = torsoHalfWidth(y0, ctx.spec);
  const head: number[] = [
    y0, top.x, top.z,
    ctx.spec.pose.spineLean * ((y0 - L.crotch) / (L.neckBase - L.crotch)),
  ];
  const keys = [head, ...yoke];
  const at = sectionFn(ctx, keys);
  // Stop just short of where the crotch dome closes: the section there is a few
  // millimetres across and buried in the thighs, so the flat end cap costs
  // nothing and evaluating a near-zero section would not.
  const yBase = L.crotch + b.crotchTaperTop - b.crotchTaper * 0.965;
  return {
    field: union(
      loftEllipse(yBase, y0 + 0.010, at),
      loftEllipse(y0 - 0.010, keys[keys.length - 1][0], at),
    ),
    at,
  };
}

function bust(ctx: PartContext): Field {
  const { spec: s } = ctx;
  const L = s.landmarks, w = s.widths;
  const b = nums((s.body as unknown as Record<string, unknown>).bust);
  const y = L.bust - b.drop;
  const x = w.bustHalfW * b.x;
  const z = w.bustHalfD * b.z;
  const r: Vec3 = [b.rx, b.ry, b.rz];
  return union(ellipsoid([x, y, z], r), ellipsoid([-x, y, z], r));
}

/**
 * The trapezius: the ramp from the side of the neck out to the deltoid.
 *
 * Without it the yoke reaches full shoulder width the moment the neck column
 * ends and the front silhouette steps instead of sloping.  Measured on clay_2
 * on her left (screen-right), reading only below y = 1.443 where the hair lock
 * beside the jaw has ended: half-width 0.075 at y = 1.440, 0.088 at 1.429,
 * 0.104 at 1.420, 0.119 at 1.410, 0.131 at 1.402.
 *
 * It is an ellipsoid rather than a capsule because the top of that ramp is
 * nearly horizontal -- the mass tops out at y = 1.443 and is already 75 mm wide
 * 3 mm below that.  A capsule from the neck to the shoulder cannot do both; it
 * came out 26 mm narrow at 1.440 and 29 mm narrow at 1.429.  Its z centre sits
 * behind the column so the suprasternal notch survives.
 */
function trapezius(ctx: PartContext, side: 1 | -1): Field {
  const b = nums((ctx.spec.body as unknown as Record<string, unknown>).trap);
  return ellipsoid([side * b.cx, b.cy, b.cz], [b.rx, b.ry, b.rz]);
}

function arm(ctx: PartContext, side: 1 | -1): Field {
  const { spec: s, skel } = ctx;
  const w = s.widths;
  const d = nums((s.body as unknown as Record<string, unknown>).deltoid);
  const sh = side > 0 ? skel.shoulderL : skel.shoulderR;
  const el = side > 0 ? skel.elbowL : skel.elbowR;
  const wr = side > 0 ? skel.wristL : skel.wristR;
  const hd = side > 0 ? skel.handL : skel.handR;

  // The deltoid apex sits below the shoulder landmark, not on it: the reference
  // reaches its widest at y = 1.360..1.375 and has already lost 30 mm by 1.402.
  const dR = (w as unknown as Record<string, number>).deltoidR ?? 0.040;
  const deltoid = ellipsoid(
    [sh[0] * d.xScale, sh[1] + d.drop, sh[2] + d.dz],
    [dR * d.rx, dR * d.ry, dR * d.rz],
  );
  // Start the humerus below the joint: its own end cap used to stand 14 mm
  // proud of the deltoid and read as a pimple on top of the shoulder, and at
  // y = 1.425 it was a detached island in the front silhouette.
  const top: Vec3 = [
    sh[0] + (el[0] - sh[0]) * d.armStart,
    sh[1] + (el[1] - sh[1]) * d.armStart,
    sh[2] + (el[2] - sh[2]) * d.armStart,
  ];
  const upper = capsuleOval(top, el, w.upperArmR, w.elbowR, 0.94, 1);
  const fore = capsuleOval(el, wr, w.elbowR * 0.98, w.wristR, 0.88, 1);

  // A mitten with a thumb: fingers are below the voxel budget and the reference
  // has them inside fingerless gloves anyway, so the glove shell carries them.
  const palmDir: Vec3 = [hd[0] - wr[0], hd[1] - wr[1], hd[2] - wr[2]];
  const palm = capsuleOval(wr, hd, w.wristR * 1.05, w.wristR * 1.15, 0.62, 1);
  const thumb = capsule(
    [wr[0] - side * 0.012, wr[1] - 0.018, wr[2] + 0.020],
    [wr[0] - side * 0.020, wr[1] - 0.052, wr[2] + 0.030],
    0.014, 0.011,
  );
  const tips = capsule(
    hd,
    [hd[0] + palmDir[0] * 0.42, hd[1] + palmDir[1] * 0.42, hd[2] + palmDir[2] * 0.42],
    w.wristR * 1.05, w.wristR * 0.62,
  );

  return smoothUnion(0.022, deltoid, upper, fore, palm, thumb, tips);
}

function leg(ctx: PartContext, side: 1 | -1): Field {
  const { spec: s, skel } = ctx;
  const w = s.widths, L = s.landmarks;
  const g = nums((s.body as unknown as Record<string, unknown>).glute);
  const hip = side > 0 ? skel.hipL : skel.hipR;
  const knee = side > 0 ? skel.kneeL : skel.kneeR;
  const ankle = side > 0 ? skel.ankleL : skel.ankleR;
  const toe = side > 0 ? skel.toeL : skel.toeR;

  // The trunk loft is an ellipse about the spine, so it cannot carry a seat.
  // clay_0 puts the buttock 30 mm behind the back of the waist column at
  // y = 0.94..1.00; the glute mass is what supplies that.
  const glute = ellipsoid(
    [hip[0], L.crotch + g.rise, -w.hipHalfD * g.back],
    [w.thighR * g.rx, g.ry, w.hipHalfD * g.rz],
  );
  const thigh = capsuleOval(
    [hip[0], hip[1] + 0.02, hip[2]], knee,
    w.thighR, w.kneeR, 1.06, 1,
  );
  // The calf belly sits high and to the back; without it the lower leg reads as
  // a cone and the side view loses the reference's curve.
  // Everything below the knee is measured DOWN FROM THE ANKLE JOINT, not up
  // from the floor.  The stance is a contrapposto -- her left foot sits 47 mm
  // higher than her right -- and absolute heights here silently swallowed that:
  // the skeleton lifted the ankle while the arch and heel stayed pinned to
  // `landmarks.footBed`, so the pose showed up as a 6 mm stagger instead of 47.
  const drop = L.ankleJoint - L.footBed;
  const calfMid: Vec3 = [knee[0] + (ankle[0] - knee[0]) * 0.32, L.calf + 0.045, knee[2] - 0.014];
  const shinUpper = capsuleOval(knee, calfMid, w.kneeR * 0.94, w.calfR, 1.18, 1);
  const shinLower = capsuleOval(calfMid, ankle, w.calfR, w.ankleR, 1.14, 1);
  // The foot hangs off the ankle joint, not off the floor: the boot's sole slab
  // lifts it to `footBed`.  Running the arch capsule from just under the joint
  // is what keeps it attached to the shin.
  const arch: Vec3 = [ankle[0], ankle[1] - drop + 0.030, ankle[2] + 0.008];
  const foot = smoothUnion(
    0.016,
    capsuleOval(ankle, arch, w.ankleR, 0.032, 0.86, 1),
    capsuleOval(arch, toe, 0.033, 0.026, 0.80, 1),
  );
  const heel = ellipsoid([ankle[0], ankle[1] - drop + 0.030, ankle[2] - 0.026], [0.030, 0.032, 0.030]);

  return smoothUnion(0.020, glute, thigh, shinUpper, shinLower, foot, heel);
}

export const bodyPart: PartModule = {
  id: 'body',
  build(ctx) {
    const { mat } = ctx;
    const b = nums(ctx.spec.body as unknown as Record<string, unknown>);
    const t = trunk(ctx);

    // Graded blends, not one radius for everything.  A single 38 mm smoothUnion
    // bridges any gap under 19 mm, and the gap between the forearm and the ribs
    // at the midriff is 20 mm -- which is why the arms used to weld to the
    // waist and the reference's three silhouette runs came out as one.  The
    // arms get 16 mm, enough to fair the deltoid into the shoulder and far too
    // little to close that gap.
    const core = smoothUnion(b.blendBust, t.field, bust(ctx));
    const yoked = smoothUnion(b.blendTrap, core, trapezius(ctx, 1), trapezius(ctx, -1));
    const withLegs = smoothUnion(b.blendLeg, yoked, leg(ctx, 1), leg(ctx, -1));
    const skin = smoothUnion(b.blendArm, withLegs, arm(ctx, 1), arm(ctx, -1));

    // The navel is a dimple, not a hole.  Its depth has to be measured from the
    // surface the trunk actually has, not from a fixed z: pinned to
    // `waistHalfD * 0.95` it cut 24 mm into the corrected profile and read as a
    // crater in the front view.
    const L = ctx.spec.landmarks;
    const belly = t.at(L.navel);
    const navelR: Vec3 = [0.011, 0.016, 0.014];
    const navel = ellipsoid(
      [0, L.navel, belly.cz + belly.z + navelR[2] - b.navelDepth],
      navelR,
    );

    // Tattoos are ink on this shell, not geometry of their own, so the tattoo
    // part hands over a region and it is painted here.
    const ink = tattooField(ctx);
    const base = constMaterial(mat.skin);
    const shell: Shell = {
      name: 'body',
      field: subtract(skin, navel),
      material: ink ? paint(base, ink, mat.tattoo, 0.0) : base,
      // The skin is by far the largest surface in the build; at voxelScale 1 it
      // is 155 k triangles at --lod high on its own.  1.5 puts it near 70 k --
      // a 6.75 mm voxel, which is what the medium LOD used to be and reads
      // clean, because nothing on this shell is finer than the thumb.
      voxelScale: b.voxelScale,
    };
    return [shell];
  },
};
