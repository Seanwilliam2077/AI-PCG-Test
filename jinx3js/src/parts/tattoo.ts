/**
 * Jinx's cloud tattoos.
 *
 * They are ink, not geometry, so this part contributes no shell: it exports a
 * field whose interior body.ts paints with the `tattoo` material.  Owned by the
 * tattoo author -- edit `tattooField` and nothing else.
 *
 * HANDEDNESS: the ink is on her **RIGHT**, which is **-X** in this frame and
 * appears on the **left** of a front view.  Round 1 had it on +X; see
 * docs/HANDEDNESS.md.  The tattooed arm is the **bare** one, and the two black
 * arm bands are on the *other* arm -- an earlier brief called the banded arm
 * "the tattooed arm", which is what put the ink on the wrong side.
 *
 * Three independent checks, all read off the reference by segmenting the ink's
 * pale blue-grey out of the skin (tools in out/zapper_tattoo_extent.py):
 *
 *   body_2 (front)  ink only on the image-LEFT arm and flank; the image-RIGHT
 *                   arm carries the two black bands and is clean.
 *   body_5 (back)   ink on the image-RIGHT half of the back and that arm;
 *                   in a back view her right IS image-right.
 *   body_4 (her right side)  5.2% of the figure is ink.
 *   body_0 (her left side)   the same segmentation finds essentially none.
 *
 * MEASURED EXTENT.  Heights are metres above the floor; `ang` is the torso
 * azimuth from the front (+Z) round toward her right flank, so 90 deg is the
 * flank and 180 deg the spine.
 *
 *   arm     from the deltoid cap (y 1.40) down to the glove (y 1.06), on the
 *           back and outer faces, spilling onto the front edge but never
 *           reaching the inner face that lies against the ribs.
 *   torso   y 1.06 to 1.40.  At the scapula the ink is on the OUTER part of
 *           the back only -- at y = 1.35 body_5 puts it 0.083 m out from the
 *           spine, i.e. ang 90-160, not across the spine.  At the waist it
 *           wraps much further forward: body_2 shows it reaching within
 *           0.015 m of the navel at y = 1.20, i.e. ang down to about 20.
 *
 * The chest, the sternum, the whole left side and both legs are bare.  It is
 * never one solid patch: every motif is a curl of two or three lobes with bare
 * skin between, so the region is built as clusters of spheres sunk just under
 * the skin.  Only the sign matters, so depth is crude; the outline is not.
 */
import { Field, Vec3 } from '../sdf/types.js';
import { sphere, union } from '../sdf/ops.js';
import { PartContext, PartModule } from './types.js';
import { torsoHalfWidth } from '../spec.js';

interface TattooSpec {
  seed: number;
  armCloudR: number;
  torsoCloudR: number;
  /** How far under the skin a lobe centre sits, as a fraction of its radius. */
  sink: number;
  lobeMin: number;
  lobeVar: number;
  /** Extra radius added to the limb before placing, to clear the smoothUnion. */
  skinPad: number;
}

const DEFAULTS: TattooSpec = {
  seed: 20250819,
  armCloudR: 0.029,
  torsoCloudR: 0.032,
  sink: 0.42,
  lobeMin: 0.34,
  lobeVar: 0.28,
  skinPad: 0.006,
};

/* ------------------------------------------------------------------ maths */

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a: Vec3, b: Vec3): Vec3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const norm = (a: Vec3): Vec3 => {
  const l = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** Deterministic PRNG -- the ink must land in the same place every bake. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ------------------------------------------------- placing on a limb/torso */

interface Surface {
  /** Point on the skin. */
  p: Vec3;
  /** Outward unit normal there. */
  n: Vec3;
  /** Local radius, used to turn a tangential offset into an angle. */
  r: number;
}

/**
 * Mirror a surface sample from her left to her right.
 *
 * The skeleton places the two arms symmetrically (shoulderR = -shoulderL and
 * so on) and the torso stack is symmetric in x, so building on the +X side and
 * negating x is exact -- and it is one line, which is one line's worth of
 * chances to get the side wrong instead of thirty.
 */
const toRight = (s: Surface): Surface => ({
  p: [-s.p[0], s.p[1], s.p[2]],
  n: [-s.n[0], s.n[1], s.n[2]],
  r: s.r,
});

/**
 * The arm as two segments: s in [0,1] runs shoulder -> elbow, s in [1,2] runs
 * elbow -> wrist.  `phi` is measured from the outer side, positive toward the
 * front, so phi = pi/2 is the front of the arm and -pi/2 the back.
 */
function armSurface(ctx: PartContext, s: number, phi: number, pad: number): Surface {
  const { skel, spec } = ctx;
  const w = spec.widths;
  const sc = s < -0.22 ? -0.22 : s > 1.62 ? 1.62 : s;
  const seg = sc <= 1 ? 0 : 1;
  const t = seg === 0 ? sc : sc - 1;
  const a: Vec3 = seg === 0 ? (skel.shoulderL as Vec3) : (skel.elbowL as Vec3);
  const b: Vec3 = seg === 0 ? (skel.elbowL as Vec3) : (skel.wristL as Vec3);
  const r0 = seg === 0 ? w.upperArmR : w.elbowR * 0.98;
  const r1 = seg === 0 ? w.elbowR : w.wristR;

  const axis: Vec3 = [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
  const r = r0 + (r1 - r0) * t + pad;

  const T = norm(sub(b, a));
  // Front direction, orthogonalised against the limb axis.
  const dot = T[2];
  const front = norm([-T[0] * dot, -T[1] * dot, 1 - T[2] * dot]);
  const out = norm(cross(front, T));

  const c = Math.cos(phi), sn = Math.sin(phi);
  const n: Vec3 = norm([
    out[0] * c + front[0] * sn,
    out[1] * c + front[1] * sn,
    out[2] * c + front[2] * sn,
  ]);
  return toRight({
    p: [axis[0] + n[0] * r, axis[1] + n[1] * r, axis[2] + n[2] * r], n, r,
  });
}

/**
 * The torso as the same stack of ellipses body.ts builds from, so the ink
 * follows a silhouette change instead of being pinned to absolute numbers.
 * `ang` is measured from the front (+Z) toward her RIGHT, so pi/2 is her right
 * flank and pi the spine.
 */
function torsoSurface(ctx: PartContext, y: number, ang: number, pad: number): Surface {
  const { spec: s } = ctx;
  const L = s.landmarks;
  const half = torsoHalfWidth(y, s);
  const lean = s.pose.spineLean * ((y - L.crotch) / Math.max(1e-6, L.neckBase - L.crotch));
  const hx = half.x + pad, hz = half.z + pad;
  const sn = Math.sin(ang), c = Math.cos(ang);
  const p: Vec3 = [hx * sn, y, lean + hz * c];
  const n = norm([sn / hx, 0, c / hz]);
  return toRight({ p, n, r: Math.min(hx, hz) });
}

/* ------------------------------------------------------------------ clouds */

/**
 * One motif: a few overlapping lobes, each placed on the skin in its own right
 * and sunk under it, so the patch it cuts on the surface is a lobed curl rather
 * than a disc.
 */
function cloud(
  place: (du: number, dv: number) => Surface,
  R: number,
  cfg: TattooSpec,
  rnd: () => number,
): Field {
  const lobes: Field[] = [];
  const count = 3 + Math.floor(rnd() * 3);
  // First lobe is the fat body of the curl, the rest trail off it.
  let du = 0, dv = 0;
  for (let i = 0; i < count; i++) {
    const r = R * (cfg.lobeMin + cfg.lobeVar * rnd()) * (i === 0 ? 1.12 : 0.9);
    const s = place(du, dv);
    const sink = r * cfg.sink;
    lobes.push(sphere(
      [s.p[0] - s.n[0] * sink, s.p[1] - s.n[1] * sink, s.p[2] - s.n[2] * sink],
      r,
    ));
    // Walk the next lobe off the last one.  Round 1 let this wander up to
    // 0.17 m, which is how motifs seeded on the flank ended up as blotches on
    // the chest; a curl is 30-50 mm across on the reference, so the walk is
    // now bounded by the motif's own radius.
    const step = R * (0.34 + 0.30 * rnd());
    const dir = rnd() * Math.PI * 2;
    du += Math.cos(dir) * step;
    dv += Math.sin(dir) * step * 0.8;
  }
  return union(...lobes);
}

/**
 * Motif layout.
 *
 * Rings up the limb, a few motifs per ring, each jittered off its slot: that
 * gives the scattered spray the sheet has without a hand-written table of
 * thirty positions, and it stays stable because the PRNG is seeded.
 *
 * `s` is the arm parameter (0 shoulder, 1 elbow, 2 wrist); 1.45 is where the
 * glove starts.  Ring -0.06 sits on the deltoid cap, above the shoulder joint;
 * the torso ellipse stack has necked toward the throat by that height and
 * would put the ink inside the shoulder rather than on it.
 *
 * `phi` runs from the outer face (0) toward the front (+); the reference has
 * the ink on the back and outer faces of the arm, spilling onto the front edge
 * but never onto the inner face that lies against the ribs, so the window is
 * off-centre rather than a full sleeve.
 */
const ARM_RINGS = [-0.06, 0.10, 0.28, 0.46, 0.66, 0.86, 1.06, 1.26, 1.45];
const ARM_PER_RING = 3;
const ARM_PHI_LO = (-150 * Math.PI) / 180;
const ARM_PHI_HI = (55 * Math.PI) / 180;

/** Torso rings: height, and the azimuth window in degrees that carries ink. */
const TORSO_RINGS: [number, number, number][] = [
  [1.400, 96, 148],
  [1.368, 88, 156],
  [1.330, 84, 158],
  [1.292, 76, 158],
  [1.254, 58, 156],
  [1.216, 34, 154],
  [1.178, 20, 152],
  [1.140, 24, 150],
  [1.100, 34, 148],
  [1.062, 52, 142],
];
const TORSO_PER_RING = 3;

/**
 * The ink never crosses the spine or the sternum.  Round 1 clamped at 28-166
 * globally, which still let a waist motif walk up onto the chest; the clamp is
 * now the ring's own window plus one motif of margin.
 */
const ANG_SLACK = (14 * Math.PI) / 180;

const clamp = (v: number, a: number, b: number) => (v < a ? a : v > b ? b : v);

/** Region to paint, or null for none.  Only the sign of the field is used. */
export function tattooField(ctx: PartContext): Field | null {
  const cfg: TattooSpec = {
    ...DEFAULTS,
    ...((ctx.spec as unknown as { tattoo?: Partial<TattooSpec> }).tattoo ?? {}),
  };
  const rnd = mulberry32(cfg.seed);
  const parts: Field[] = [];
  const rad = (d: number) => (d * Math.PI) / 180;

  ARM_RINGS.forEach((s0, ring) => {
    for (let i = 0; i < ARM_PER_RING; i++) {
      // Slots spread across the window, with each ring offset a third of a
      // slot off the last so the motifs spiral instead of stacking in columns.
      const span = ARM_PHI_HI - ARM_PHI_LO;
      const f = (i + 0.34 * ring) / ARM_PER_RING;
      const phi = ARM_PHI_LO + span * (f - Math.floor(f)) + (rnd() - 0.5) * 0.4;
      const s = s0 + (rnd() - 0.5) * 0.12;
      const R = cfg.armCloudR * (0.8 + 0.45 * rnd());
      const base = armSurface(ctx, s, phi, cfg.skinPad).r;
      parts.push(cloud(
        // du walks along the limb, dv around it; both in metres on the skin.
        (du, dv) => armSurface(
          ctx,
          s + du / 0.20,
          clamp(phi + dv / base, ARM_PHI_LO - 0.25, ARM_PHI_HI + 0.25),
          cfg.skinPad,
        ),
        R, cfg, rnd,
      ));
    }
  });

  for (const [y0, lo, hi] of TORSO_RINGS) {
    for (let i = 0; i < TORSO_PER_RING; i++) {
      const f = i / (TORSO_PER_RING - 1) + (rnd() - 0.5) * 0.28;
      const ang = rad(lo + (hi - lo) * clamp(f, 0, 1));
      const y = y0 + (rnd() - 0.5) * 0.022;
      const R = cfg.torsoCloudR * (0.78 + 0.5 * rnd());
      const base = torsoSurface(ctx, y, ang, cfg.skinPad).r;
      // Clamped to this ring's own window so a motif that walks too far never
      // crosses the spine or ends up on the sternum, both of which are bare.
      parts.push(cloud(
        (du, dv) => torsoSurface(
          ctx, y + du * 0.6,
          clamp(ang + dv / base, rad(lo) - ANG_SLACK, rad(hi) + ANG_SLACK),
          cfg.skinPad,
        ),
        R, cfg, rnd,
      ));
    }
  }

  return union(...parts);
}

export const tattooPart: PartModule = {
  id: 'tattoo',
  build() {
    return [];
  },
};
