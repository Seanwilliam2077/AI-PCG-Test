/**
 * The hip wrap: a band of mauve cloth slung under the belt with ONE long flap
 * hanging over her right hip, the khaki canvas apron tucked under the belt
 * across the front and round her left hip to her left rear, and the pocket
 * sewn on that apron.
 *
 * Every layer is the trousers' own field grown outward and then cut, not a
 * guessed oval: below the crotch the garment's section is two tubes, and an
 * oval mandrel there either sinks into the thigh or floats 40 mm off the front
 * of the crotch.  The layers are solids rather than hollow slabs -- see
 * `layer` for why -- so the visible cloth thickness is the annulus each cut
 * leaves where the free edge crosses the surface underneath it.
 *
 * ROUND 2.  Three things measured off the textured panels at 4x changed:
 *
 * 1. The mauve is on her RIGHT ONLY.  `body_2` (front) shows unstriped mauve
 *    from the belt down over her right hip and striped trousers on her left;
 *    `body_5` (back) shows unstriped mauve over her right buttock and khaki
 *    over her left.  The wrap is therefore `cut` at x = `splitX`, keeping her
 *    right half -- it is a wrap, not a barrel, and the cut halves its bounds.
 *
 * 2. The flap hangs 100 mm LOWER than round 1 had it.  On `body_2` at 4x the
 *    cream-piped hem runs from a rounded corner on the silhouette at
 *    y = 0.815 up and inboard to the belt; round 1 read 0.912 off the same
 *    panel because the arm gap above it was mistaken for the hem.  On
 *    `body_5` the same hem is at y = 0.945 where it crosses her right rear.
 *    So the low corner is forward of her side, at bearing ~ -1.1, and the
 *    hem climbs both ways from it: that is the "spiral" a single plane could
 *    not make.
 *
 * 3. The khaki apron runs round to her LEFT REAR, not just her left side.
 *    `body_5` shows it from her left flank across to the spine with its hem
 *    at y ~ 0.985.  Its bearing band is now wider than pi, so it is a union
 *    of two overlapping wedges rather than one.
 *
 * Measured heights, panel by panel (metre grid keyed to each alpha bbox):
 *   wrap top edge, her right hip        body_3   y = 1.091
 *   flap low corner, her right front    body_2   y = 0.815   (4x, piped hem)
 *   flap hem, her right rear            body_5   y = 0.945
 *   wrap hem near the spine             body_5   y ~ 1.02
 *   apron lower edge, her left front    body_2   y = 0.930
 *   apron lower edge, front centre      body_2   y = 0.991
 *   apron lower edge, her left rear     body_5   y = 0.985
 *   apron top                           body_1   under the hip belt
 */
import { Box, Field, Vec3, box } from '../sdf/types.js';
import {
  field,
  intersect,
  offset,
  smoothIntersect,
  smoothUnion,
  union,
} from '../sdf/ops.js';
import { cut } from '../sdf/solids.js';
import { orientedBox } from '../sdf/curve.js';
import { PartContext, PartModule, Shell, constMaterial, paint } from './types.js';
import { pantsBody } from './pants.js';

interface SashSpec {
  topY: number;
  topTiltX: number;
  topFrontDrop: number;
  thickness: number;
  clearance: number;
  /** Keep the mauve at x <= this: her right half plus a little past the midline. */
  splitX: number;
  /** [bearing from +Z toward +X, height]; wraps at +/-pi. */
  hem: [number, number][];
  /** How far the free flap stands off the wrap under it. */
  flapOut: number;
  flapHem: [number, number][];
  /** Bounds clamp: the flap never reaches below this, so do not scan below it. */
  flapFloor: number;
  canvas: {
    out: number;
    thickness: number;
    tuck: number;
    topY: number;
    topTiltX: number;
    round: number;
    backing: number;
    wedge: [number, number];
    hem: [number, number][];
  };
  /** centre is [bearing from +Z toward +X, height]; half is [depth, height, width]/2. */
  pouch: {
    centre: [number, number];
    half: [number, number, number];
    round: number;
    /** How far into the apron the patch is buried, as a fraction of its depth. */
    sink: number;
  };
  voxelScale: number;
}

const sashSpec = (ctx: PartContext): SashSpec => ctx.spec.sash as unknown as SashSpec;

/**
 * The hip belt's lower edge, as belts.ts builds it: a plane tilted about z.
 * Read from the spec rather than imported, because belts.ts imports *this*
 * module to fit its straps to the wrap and a real import would be a cycle.
 */
function beltBottom(ctx: PartContext): { c: number; tilt: number } {
  const b = (ctx.spec as unknown as {
    belts?: { hipY?: number; hipTilt?: number; beltWidth?: number };
  }).belts ?? {};
  const y = b.hipY ?? 1.062;
  const w = b.beltWidth ?? 0.033;
  return { c: y - w * 0.5, tilt: b.hipTilt ?? 0.29 };
}

/**
 * One-entry memo over a field.  The wrap, the flap, the apron and the pocket
 * are all offsets of the same trouser volume, and the mesher evaluates them at
 * the same point one after another, so caching the last sample turns six
 * evaluations of a twenty-five-capsule field into one.
 */
function memo(f: Field): Field {
  let lx = NaN, ly = NaN, lz = NaN, lv = 0;
  return field(
    (x, y, z) => {
      if (x === lx && y === ly && z === lz) return lv;
      lx = x; ly = y; lz = z;
      lv = f.sdf(x, y, z);
      return lv;
    },
    f.bounds,
    f.lip,
  );
}

/* --------------------------------------------------------------- bearings */

const TAU = Math.PI * 2;

const wrapPi = (a: number): number => {
  let v = a;
  while (v > Math.PI) v -= TAU;
  while (v <= -Math.PI) v += TAU;
  return v;
};

interface AzCurve {
  at: (a: number) => number;
  /** Bound on |d value / d bearing|, including smoothstep's 1.5x overshoot. */
  slope: number;
  min: number;
  max: number;
}

/**
 * Smooth periodic lookup over bearing.  The table is [bearing, height] with
 * bearings ascending and spanning -pi..pi; the two ends should carry the same
 * height or the seam at the back shows as a step.  Smoothstep between entries,
 * so the curve is C1 and its slope is bounded by 1.5x the steepest segment --
 * which is what the hem cut's Lipschitz bound is built from.
 */
function azCurve(tbl: [number, number][]): AzCurve {
  const n = tbl.length;
  let slope = 0, min = Infinity, max = -Infinity;
  for (let i = 1; i < n; i++) {
    const d = Math.abs(tbl[i][1] - tbl[i - 1][1]) / Math.max(1e-6, tbl[i][0] - tbl[i - 1][0]);
    if (d > slope) slope = d;
  }
  for (const e of tbl) {
    if (e[1] < min) min = e[1];
    if (e[1] > max) max = e[1];
  }
  const at = (a: number): number => {
    const u = wrapPi(a);
    if (u <= tbl[0][0]) return tbl[0][1];
    for (let i = 1; i < n; i++) {
      if (u <= tbl[i][0]) {
        const [a0, v0] = tbl[i - 1];
        const [a1, v1] = tbl[i];
        const t = (u - a0) / Math.max(1e-6, a1 - a0);
        return v0 + (v1 - v0) * t * t * (3 - 2 * t);
      }
    }
    return tbl[n - 1][1];
  };
  return { at, slope: slope * 1.5, min, max };
}

/** Pointwise minimum of two hem curves -- how the wrap is kept under the apron. */
const lowerOf = (a: AzCurve, b: AzCurve, lift: number): AzCurve => ({
  at: (t) => Math.min(a.at(t), b.at(t) + lift),
  slope: Math.max(a.slope, b.slope),
  min: Math.min(a.min, b.min + lift),
  max: Math.max(a.max, b.max + lift),
});

/**
 * Keep the cloth above a hem that is a function of bearing.  Negative above
 * the hem, so `intersect` (a max) keeps the garment.
 *
 * |grad| = sqrt(1 + (d hem/d bearing)^2 / r^2), and the bearing's 1/r blows up
 * on the axis, so the radius is clamped at RMIN the way pants.ts clamps its
 * tattered hem.  RMIN stays small even though every *visible* surface this
 * cuts is at r > 0.10: these layers are solids that contain the trouser
 * volume, so the hem also caps them across the middle, and that buried cap
 * needs the honest bound or the mesher skips blocks it should not.
 */
const HEM_RMIN = 0.05;

function hemCut(curve: AzCurve, b: Box): Field {
  const at = curve.at;
  return field(
    (x, y, z) => at(Math.atan2(x, z)) - y,
    box([b.min[0], Math.max(b.min[1], curve.min - 0.006), b.min[2]], b.max),
    Math.hypot(1, curve.slope / HEM_RMIN),
  );
}

/**
 * A plane, negative on the side it keeps. `s` is +1 to keep below.  The bounds
 * are clipped to the half the plane keeps: every layer here starts life as the
 * whole trouser volume offset outward, and without this the mesher would sample
 * a 1.0 m tall box to find a 0.2 m band.
 */
function plane(kx: number, kz: number, c: number, s: 1 | -1, b: Box): Field {
  const xs = [kx * b.min[0], kx * b.max[0]];
  const zs = [kz * b.min[2], kz * b.max[2]];
  const yHi = c + Math.max(...xs) + Math.max(...zs);
  const yLo = c + Math.min(...xs) + Math.min(...zs);
  const clipped = s > 0
    ? box(b.min, [b.max[0], Math.min(b.max[1], yHi), b.max[2]])
    : box([b.min[0], Math.max(b.min[1], yLo), b.min[2]], b.max);
  return field((x, y, z) => s * (y - (c + kx * x + kz * z)), clipped, Math.hypot(1, kx, kz));
}

/**
 * The wedge of azimuth between two bearings, measured from +Z toward +X.  Two
 * planes through the vertical axis, so it stays an exact distance field.  Only
 * good up to pi: the intersection of two half-planes cannot be reflex.
 */
function wedge(a0: number, a1: number, b: Box): Field {
  const s0 = Math.sin(a0), c0 = Math.cos(a0);
  const s1 = Math.sin(a1), c1 = Math.cos(a1);
  return intersect(
    field((x, _y, z) => s0 * z - c0 * x, b),
    field((x, _y, z) => c1 * x - s1 * z, b),
  );
}

/**
 * The same band, but allowed to be wider than pi -- which the apron now is,
 * because it runs from her right front all the way round to her left rear.
 * Two wedges that OVERLAP by 0.25 rad: butted exactly they would both be zero
 * on the shared plane and the smooth intersection that rounds the band's ends
 * would carve a few-millimetre groove down it.
 */
function bearingBand(a0: number, a1: number, b: Box): Field {
  if (a1 - a0 <= Math.PI - 0.02) return wedge(a0, a1, b);
  const m = 0.5 * (a0 + a1);
  return union(wedge(a0, m + 0.25, b), wedge(m - 0.25, a1, b));
}

/**
 * A layer of cloth lying on `base`: the trousers grown by `out`, not a hollow
 * slab.  A slab of the reference's ~10 mm would be under one voxel at the low
 * LOD and would mesh as a chain of blobs, and its inner face costs triangles
 * that are never seen -- the trouser shell already occupies that space, so the
 * only surface a viewer can reach is the outer one and the annulus left where
 * a cut crosses the free edge, which is exactly the cloth's thickness.
 */
const layer = (base: Field, out: number): Field => offset(base, out);

/**
 * The waistband cut: the wrap's top edge, higher on her right, lower in front.
 * The z coefficient is NEGATIVE -- `topFrontDrop` is a drop, and an earlier
 * version passed it positive, which raised the top edge at the front by 30 mm
 * instead of lowering it.  Sanity check: at z = +0.13 this lands on 1.052 and
 * the trousers' own waistband is at 1.053, which is what body_2 shows.
 */
function topCut(ctx: PartContext, b: Box): Field {
  const S = sashSpec(ctx);
  return plane(S.topTiltX, -S.topFrontDrop / 0.1, S.topY, 1, b);
}

/** Keep only her right half (x <= splitX).  This is what makes it a wrap. */
const halfWrap = (ctx: PartContext, f: Field): Field =>
  cut(f, 0, sashSpec(ctx).splitX, 'below');

/* ------------------------------------------------------------------ hems */

interface Hems { wrap: AzCurve; flap: AzCurve; canvas: AzCurve; }

function hems(ctx: PartContext): Hems {
  const S = sashSpec(ctx);
  const canvas = azCurve(S.canvas.hem);
  // Where the apron hangs below the wrap, the wrap follows it down and past it
  // by |backing|.  Without this the apron's free edge is a 23 mm cliff straight
  // onto the trousers; with it the apron lands on cloth and the eye reads an
  // 8 mm step, which is what the reference's rolled canvas edge is.
  return {
    wrap: lowerOf(azCurve(S.hem), canvas, S.canvas.backing),
    flap: azCurve(S.flapHem),
    canvas,
  };
}

/**
 * The wrap itself: the turn of cloth that goes round under the belt, cut off
 * at the midline front and back.  Its hem sits 20-100 mm above the flap's, so
 * both edges are visible and the cloth reads as folded rather than as one
 * smooth skirt.
 */
function wrap(ctx: PartContext, base: Field, h: Hems): Field {
  const S = sashSpec(ctx);
  const slab = layer(base, S.clearance + S.thickness);
  const b = slab.bounds;
  return halfWrap(ctx, intersect(intersect(slab, topCut(ctx, b)), hemCut(h.wrap, b)));
}

/**
 * The free end hanging over her right hip: a second thickness whose hem is the
 * measured one -- low corner y = 0.815 at bearing -1.1, climbing to 0.945 by
 * her right rear and above the waistband cut at either end, where the layer
 * simply runs out and needs no wedge.
 *
 * `flapFloor` only clamps the bounds.  The hem is a function of bearing and a
 * bearing table's bound is taken over the whole box, so without it the mesher
 * would scan from y = 0.06 upward to find a panel that starts at 0.81.
 */
function flap(ctx: PartContext, base: Field, h: Hems): Field {
  const S = sashSpec(ctx);
  const slab = layer(base, S.clearance + S.thickness + S.flapOut);
  const b = slab.bounds;
  const shaped = intersect(intersect(slab, topCut(ctx, b)), hemCut(h.flap, b));
  return halfWrap(ctx, cut(shaped, 1, S.flapFloor, 'above'));
}

/**
 * The khaki canvas apron.
 *
 * Its top edge is the LOWER of two planes: the reference's own near-level top
 * (body_2: 1.044 on her right, 1.035 on her left) and the hip belt's lower
 * edge plus `tuck`.  Following the belt alone -- which is what an earlier fix
 * did -- climbs 58 mm across the hip, because belts.json tilts it 0.29, and
 * that pushes a wedge of khaki up her left hip that the reference does not
 * have.  Taking the minimum keeps the raw top edge behind the belt wherever
 * the belt is the lower of the two, and level with the reference elsewhere.
 *
 * Its ends are rounded off the bearing band with a smooth intersection rather
 * than chopped square, which is what made the outboard end read as a tear.
 */
function canvas(ctx: PartContext, base: Field, h: Hems): Field {
  const S = sashSpec(ctx);
  const C = S.canvas;
  const slab = layer(base, S.clearance + S.thickness + C.out + C.thickness);
  const b = slab.bounds;
  const belt = beltBottom(ctx);
  const under = intersect(
    plane(C.topTiltX, 0, C.topY, 1, b),
    plane(belt.tilt, 0, belt.c + C.tuck, 1, b),
  );
  const shaped = intersect(intersect(slab, under), hemCut(h.canvas, b));
  return smoothIntersect(C.round, shaped, bearingBand(C.wedge[0], C.wedge[1], b));
}

/**
 * Where the garment's outer surface is at a height and a bearing, and which way
 * it faces.  Bisecting the field beats hard-coding a point: the pocket then
 * stays on the apron if the flare or the cloth thickness is retuned.
 */
function surfaceFrame(f: Field, y: number, bearing: number): { p: Vec3; n: Vec3 } {
  const dx = Math.sin(bearing), dz = Math.cos(bearing);
  let lo = 0.02, hi = 0.40;
  for (let i = 0; i < 44; i++) {
    const m = 0.5 * (lo + hi);
    if (f.sdf(dx * m, y, dz * m) < 0) lo = m; else hi = m;
  }
  const t = 0.5 * (lo + hi);
  const p: Vec3 = [dx * t, y, dz * t];
  const e = 2e-4;
  let nx = f.sdf(p[0] + e, y, p[2]) - f.sdf(p[0] - e, y, p[2]);
  let nz = f.sdf(p[0], y, p[2] + e) - f.sdf(p[0], y, p[2] - e);
  const len = Math.hypot(nx, nz) || 1;
  nx /= len; nz /= len;
  return { p, n: [nx, 0, nz] };
}

/**
 * The pocket on the apron: a rounded patch sunk most of its depth into the
 * canvas so it stands about 5 mm proud.
 *
 * An earlier version was a free-standing 34 mm leather box on the hip, which
 * read as a crate and collided with the glove.  A pocket is part of the panel
 * it is sewn to, so this is smooth-unioned into the apron and takes the
 * apron's own khaki: body_1 at 4.5x shows a pocket on the canvas with a soft
 * curved top and no dark welt -- the black diagonal over it there is the
 * drop-leg strap, which belongs to belts.ts.
 */
function pocket(ctx: PartContext, base: Field): Field {
  const S = sashSpec(ctx);
  const P = S.pouch;
  const C = S.canvas;
  const outer = offset(base, S.clearance + S.thickness + C.out + C.thickness);
  const { p: s, n } = surfaceFrame(outer, P.centre[1], P.centre[0]);
  const ex: Vec3 = n;                       // out of the hip
  const ey: Vec3 = [0, 1, 0];
  const ez: Vec3 = [n[2], 0, -n[0]];        // along the hip
  const d = P.half[0], hh = P.half[1], w = P.half[2];
  const at = (out: number, up: number): Vec3 => [
    s[0] + ex[0] * out,
    s[1] + up,
    s[2] + ex[2] * out,
  ];
  return orientedBox(at(-d * P.sink, 0), ex, ey, ez, [d, hh, w], P.round);
}

export const sashPart: PartModule = {
  id: 'sash',
  build(ctx) {
    const { mat } = ctx;
    const S = sashSpec(ctx);
    const base = memo(pantsBody(ctx));
    const h = hems(ctx);

    // Smooth, not hard: the free end is the same piece of cloth turned back on
    // itself, so the two layers meet in a fold, not a step.
    const cloth = smoothUnion(0.006, wrap(ctx, base, h), flap(ctx, base, h));
    const canvasF = smoothUnion(0.009, canvas(ctx, base, h), pocket(ctx, base));
    const shellField = union(cloth, canvasF);

    // NOT DONE, and the measurement is worth keeping: the compare bands say the
    // hip is 15-36 mm narrow in the front and back views, and `elongate` along
    // x would widen the wrap laterally without adding the depth those views do
    // not want.  Tried at 10 and 18 mm: the full-figure outline did not move at
    // all above y = 0.92, because her forearms are 20-40 mm OUTSIDE the wrap
    // there and they, not the cloth, are the silhouette.  The hip-width deficit
    // belongs to the arms and the body's own widths, not to this part.

    // The volumes nest, so nearestMaterial would hand every surface point to
    // whichever field it lies deepest inside -- the wrap, always.  Painting in
    // layers asks the right question instead: is this point on the apron or on
    // the wrap.  The wrap carries no pinstripes: the reference's sash is a
    // lighter, flat mauve, and that colour break is what makes the one-sided
    // flap read at all.
    const material = paint(constMaterial(mat.sashCloth), canvasF, mat.canvas, 0.0015);

    const shell: Shell = {
      name: 'sash',
      field: shellField,
      material,
      voxelScale: S.voxelScale,
    };
    return [shell];
  },
};
