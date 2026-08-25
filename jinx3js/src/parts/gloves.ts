/**
 * Fingerless gloves: black cloth over the hand and most of the forearm.
 *
 * body.ts deliberately models the hand as a mitten with a thumb, so the glove
 * is where the hand gets its shape: it is a solid sleeve built round the same
 * wrist/hand joints, a couple of millimetres bigger than the skin, then *cut*
 * -- a plane across the knuckles and a sphere off the thumb -- so the mitten's
 * tip and thumb come through as bare fingers.  A hollow shell would need the
 * cut edge to be a rim of its own; cutting a solid gives the open edge for
 * free and keeps the surface closed.
 *
 * The two arms are not the same on the reference.  The arm that carries the
 * black bands wears a long sleeve that reaches over the elbow and stops right
 * under the lower band (measured at y = 1.208 on clay_2); the other stops
 * mid-forearm at y = 1.115.  Both are driven from `belts.rigSide` so the pair
 * stays consistent if that side is flipped.
 *
 * Materials: cloth for the sleeve, leather for the rolled wrist cuff, brass for
 * the knuckle plate -- all `paint` overrides on one shell.
 */
import { Field, Vec3 } from '../sdf/types.js';
import {
  capsule, capsuleOval, cylinder, halfSpace, sphere, smoothUnion, subtract, union,
} from '../sdf/ops.js';
import { PartContext, PartModule, Shell, constMaterial, paint } from './types.js';
import { orientedBox } from '../sdf/curve.js';

type V3 = [number, number, number];

const vsub = (a: Vec3, b: Vec3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const vadd = (a: Vec3, b: Vec3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const vmul = (a: Vec3, s: number): V3 => [a[0] * s, a[1] * s, a[2] * s];
const vlen = (a: Vec3): number => Math.hypot(a[0], a[1], a[2]);
const vnorm = (a: Vec3): V3 => {
  const l = vlen(a) || 1e-9;
  return [a[0] / l, a[1] / l, a[2] / l];
};
const vdot = (a: Vec3, b: Vec3): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const vcross = (a: Vec3, b: Vec3): V3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

interface Dims {
  topY: number; longTopY: number; thickness: number;
  knuckleT: number; cuffY: number; cuffWidth: number; cuffProud: number;
  hemProud: number; plateW: number; plateH: number; plateT: number; voxelScale: number;
  bandSide: number;
}

function dims(ctx: PartContext): Dims {
  const G = ctx.spec.gloves as unknown as Record<string, number>;
  const B = ctx.spec.belts as unknown as Record<string, number>;
  const num = (o: Record<string, number>, k: string, dflt: number) =>
    (typeof o[k] === 'number' ? o[k] : dflt);
  return {
    topY: num(G, 'topY', 1.112),
    longTopY: num(G, 'longTopY', 1.208),
    thickness: num(G, 'thickness', 0.005),
    // Fraction along the palm (wrist -> hand -> fingertips) where the glove is
    // cut: 0 is the wrist, 1 the hand joint, and body.ts runs the finger stub
    // to 1.42.  The reference cut lands just past the knuckles.
    knuckleT: num(G, 'knuckleT', 1.14),
    cuffY: num(G, 'cuffY', 0.966),
    cuffWidth: num(G, 'cuffWidth', 0.044),
    cuffProud: num(G, 'cuffProud', 0.008),
    hemProud: num(G, 'hemProud', 0.004),
    plateW: num(G, 'plateW', 0.030),
    plateH: num(G, 'plateH', 0.016),
    plateT: num(G, 'plateT', 0.006),
    voxelScale: num(G, 'voxelScale', 1.05),
    bandSide: num(B, 'rigSide', 1) >= 0 ? 1 : -1,
  };
}

interface Hand {
  wr: V3; hd: V3; el: V3;
  /** Wrist -> fingertips. */
  palm: V3;
  palmLen: number;
  thumbA: V3; thumbB: V3;
  top: V3; topR: number;
  side: 1 | -1;
}

/** The joints and radii the glove is built from -- the same ones body.ts uses. */
function hand(ctx: PartContext, side: 1 | -1, d: Dims): Hand {
  const { skel, spec } = ctx;
  const w = spec.widths;
  const wr = (side > 0 ? skel.wristL : skel.wristR) as V3;
  const hd = (side > 0 ? skel.handL : skel.handR) as V3;
  const el = (side > 0 ? skel.elbowL : skel.elbowR) as V3;
  const palm = vsub(hd, wr);

  const topY = side === d.bandSide ? d.longTopY : d.topY;
  // Up the forearm, and past the elbow along the same line if the sleeve is
  // the long one -- the elbow only bends by four degrees, so extending the
  // forearm axis is within a millimetre of following the upper arm.
  const fore = vsub(el, wr);
  const t = (topY - wr[1]) / (fore[1] || 1e-6);
  const top = vadd(wr, vmul(fore, t));
  const topR = w.wristR + (w.elbowR * 0.98 - w.wristR) * Math.min(1.15, Math.max(0, t));

  return {
    wr, hd, el, palm, palmLen: vlen(palm),
    thumbA: [wr[0] - side * 0.012, wr[1] - 0.018, wr[2] + 0.020],
    thumbB: [wr[0] - side * 0.020, wr[1] - 0.052, wr[2] + 0.030],
    top, topR, side,
  };
}

/** The solid the glove occupies, before the fingers are cut out of it. */
function gloveSolid(ctx: PartContext, h: Hand, d: Dims): Field {
  const w = ctx.spec.widths;
  const t = d.thickness;

  // Sleeve: the forearm, one thickness bigger, running from inside the palm up
  // to the hem so the two pieces are one solid.
  const sleeve = capsuleOval(
    vadd(h.wr, vmul(h.palm, 0.35)), h.top,
    w.wristR * 1.02 + t, h.topR + t + 0.002, 0.90, 1,
  );
  // A thicker ring at the hem so the top edge reads as a cuff, not a cut tube.
  // Cylinders, not capsules, for both bands: a capsule's round caps would run
  // the bulge a whole radius past each end and swallow the sleeve.
  const hemDir = vnorm(vsub(h.top, h.wr));
  const hem = cylinder(
    vadd(h.top, vmul(hemDir, -0.014)), vadd(h.top, vmul(hemDir, 0.001)),
    h.topR + t + d.hemProud,
  );

  // The rolled cuff at the wrist: on the reference it is a doubled-over band
  // about 45 mm tall sitting right on the wrist bone.
  const cuffDir = vnorm(vsub(h.top, h.wr));
  const cuffMid = vadd(h.wr, vmul(cuffDir, d.cuffY - h.wr[1]));
  const cuff = cylinder(
    vadd(cuffMid, vmul(cuffDir, -d.cuffWidth / 2)),
    vadd(cuffMid, vmul(cuffDir, d.cuffWidth / 2)),
    w.wristR + t + d.cuffProud,
  );

  // Hand: the same mitten body.ts builds, one thickness bigger, and the finger
  // stub with it so the knuckles are covered up to the cut.
  const palmPiece = capsuleOval(
    h.wr, h.hd, w.wristR * 1.05 + t, w.wristR * 1.15 + t, 0.62, 1,
  );
  const knuckles = capsuleOval(
    h.hd, vadd(h.hd, vmul(h.palm, 0.42)),
    w.wristR * 1.05 + t, w.wristR * 0.62 + t, 0.66, 1,
  );
  const thumb = capsule(h.thumbA, h.thumbB, 0.014 + t, 0.011 + t);

  return smoothUnion(0.012, sleeve, hem, cuff, palmPiece, knuckles, thumb);
}

/** Region painted as the rolled leather cuff. */
function cuffRegion(ctx: PartContext, h: Hand, d: Dims): Field {
  const w = ctx.spec.widths;
  const dir = vnorm(vsub(h.top, h.wr));
  const mid = vadd(h.wr, vmul(dir, d.cuffY - h.wr[1]));
  return cylinder(
    vadd(mid, vmul(dir, -d.cuffWidth / 2 - 0.002)),
    vadd(mid, vmul(dir, d.cuffWidth / 2 + 0.002)),
    w.wristR + d.thickness + d.cuffProud + 0.006,
  );
}

/**
 * The brass plate over the knuckles, on the back of the hand.
 *
 * body.ts flattens the palm in z (squashZ 0.62), so the flat of the hand faces
 * front and back: the plate lies on +z with a little outboard lean.
 */
function knucklePlate(ctx: PartContext, h: Hand, d: Dims): { plate: Field; bumps: Field } {
  const along = vnorm(h.palm);
  const out = vnorm([h.side * 0.22, 0, 0.975]);
  const ez = vnorm(vcross(along, out));
  const ey = vnorm(vcross(ez, along));
  const rz = (ctx.spec.widths.wristR * 1.10 + d.thickness) * 0.62;
  const base = vadd(h.wr, vmul(h.palm, 1.02));
  const c = vadd(base, vmul(ey, rz + d.plateT * 0.20));
  const plate = orientedBox(c, along, ey, ez, [d.plateH / 2, d.plateT / 2, d.plateW / 2], 0.003);
  // Three knuckles under the cut edge: the glove is where the hand gets them,
  // since the mitten underneath has none.
  const knuckle: Field[] = [];
  for (const s of [-1, 0, 1]) {
    knuckle.push(sphere(
      vadd(vadd(h.wr, vmul(h.palm, 1.10)), vadd(vmul(ez, s * 0.0125), vmul(ey, rz * 0.55))),
      0.0105,
    ));
  }
  return { plate, bumps: union(...knuckle) };
}

export const glovesPart: PartModule = {
  id: 'gloves',
  build(ctx) {
    const { mat } = ctx;
    const d = dims(ctx);
    const sides: (1 | -1)[] = [1, -1];

    const solids: Field[] = [];
    const cuffs: Field[] = [];
    const plates: Field[] = [];

    for (const side of sides) {
      const h = hand(ctx, side, d);
      const along = vnorm(h.palm);

      // Knuckle cut: a plane square to the palm, just past the knuckles.  The
      // half space is signed so `subtract` takes the fingertip side away.
      const cut = vadd(h.wr, vmul(h.palm, d.knuckleT));
      const bounds = {
        min: [h.hd[0] - 0.12, h.hd[1] - 0.14, h.hd[2] - 0.12] as Vec3,
        max: [h.hd[0] + 0.12, h.hd[1] + 0.10, h.hd[2] + 0.12] as Vec3,
      };
      const beyond = halfSpace(vmul(along, -1), -vdot(along, cut), bounds);

      // Thumb opening: the last third of the thumb, taken off with a sphere so
      // the hole is local instead of a plane through the palm.
      const thumbDir = vnorm(vsub(h.thumbB, h.thumbA));
      const thumbCut = sphere(vadd(h.thumbB, vmul(thumbDir, 0.008)), 0.019);

      const kp = knucklePlate(ctx, h, d);
      solids.push(subtract(
        smoothUnion(0.008, gloveSolid(ctx, h, d), kp.bumps),
        union(beyond, thumbCut),
      ));
      cuffs.push(cuffRegion(ctx, h, d));
      plates.push(kp.plate);
    }

    const cuffMask = union(...cuffs);
    const plateMask = union(...plates);
    const shell: Shell = {
      name: 'gloves',
      field: union(...solids),
      material: paint(
        paint(constMaterial(mat.cloth), cuffMask, mat.leather, 0.0),
        plateMask, mat.brass, 0.001,
      ),
      voxelScale: d.voxelScale,
    };
    return [shell];
  },
};
