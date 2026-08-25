/**
 * Belts, straps and the arm bands -- the leather rig slung round the hips and
 * down the drop-leg thigh, plus the two black bands on the upper arm.
 *
 * Everything here is a *run*: a list of points with an outward normal at each,
 * swept into a flat band by `bandRun`.  A belt is not a torus -- on the
 * reference it is a tilted loop that follows an elliptical body section and the
 * drop-leg rig hangs off it -- so every loop starts from `torsoHalfWidth` (or a
 * limb axis) and is then *fitted to what is actually there*: the trousers and
 * the hip wrap are probed at build time and each strap is moved along its own
 * normal until it lies on them.  That is the only way a belt stays a belt while
 * two other authors are still changing how baggy their cloth is.
 *
 * Read off the reference (see the fragment's $comment for the numbers):
 *   - the hip belt is a *tilted* loop, ~80 mm higher on the rig hip than on the
 *     other one; a plane tilt about z, so the back tilts the same way, which is
 *     what `clay_5` shows.
 *   - a second, narrower strap runs ~25 mm below it at a steeper tilt and
 *     crosses the back diagonally -- both drop straps hang off that.
 *   - both thighs carry a hanging strap with square brass keepers; the rig one
 *     ends on a strap round the thigh at y = 0.855 carrying the holster cradle.
 *
 * Sides come from `belts.rigSide` (+1 = her left, +X) per docs/HANDEDNESS.md:
 * the Zapper, the arm bands and the drop-leg rig are all on the same side and
 * the tattooed arm is the other one.
 *
 * Brass is ink, not a separate shell: `paint` overrides the leather wherever a
 * buckle, keeper or rivet field encloses the surface, so one closed shell
 * carries both materials.
 */
import { Field, Vec3, boxDistance, boxUnion } from '../sdf/types.js';
import { field, sphere } from '../sdf/ops.js';
import { orientedBox } from '../sdf/curve.js';
import { PartContext, PartModule, Shell, constMaterial, paint } from './types.js';
import { torsoHalfWidth } from '../spec.js';
import { bodyPart } from './body.js';
import { pantsPart } from './pants.js';
import { sashPart } from './sash.js';

/* ---------------------------------------------------------------- vectors */

type V3 = [number, number, number];

const vsub = (a: Vec3, b: Vec3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const vadd = (a: Vec3, b: Vec3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const vmul = (a: Vec3, s: number): V3 => [a[0] * s, a[1] * s, a[2] * s];
const vmid = (a: Vec3, b: Vec3): V3 => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
const vlen = (a: Vec3): number => Math.hypot(a[0], a[1], a[2]);
const vnorm = (a: Vec3): V3 => {
  const l = vlen(a) || 1e-9;
  return [a[0] / l, a[1] / l, a[2] / l];
};
const vcross = (a: Vec3, b: Vec3): V3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

/**
 * Union that rejects a child on its bounding box before evaluating it.
 *
 * A strap rig is a hundred-odd oriented boxes and the plain `union` evaluates
 * every one at every sample.  `sdf_i >= distance(p, bounds_i)` for any point
 * outside the child's bounds, so a child whose box is already farther than the
 * running minimum cannot win and never has to be evaluated.  The result is
 * identical to `union`, about four times cheaper here.
 */
function fastUnion(parts: Field[]): Field {
  if (parts.length === 1) return parts[0];
  const bs = parts.map((p) => p.bounds);
  let b = bs[0];
  for (let i = 1; i < bs.length; i++) b = boxUnion(b, bs[i]);
  const lip = Math.max(...parts.map((p) => p.lip));
  return field(
    (x, y, z) => {
      let m = Infinity;
      for (let i = 0; i < parts.length; i++) {
        if (boxDistance(bs[i], x, y, z) >= m) continue;
        const v = parts[i].sdf(x, y, z);
        if (v < m) m = v;
      }
      return m;
    },
    b,
    lip,
  );
}

/* ------------------------------------------------------------------- runs */

interface Run {
  pts: V3[];
  /** Outward surface normal at each point: the direction the strap's face looks. */
  nrm: V3[];
}

/**
 * Sweep a flat band along a run.
 *
 * `width` is measured across the band (up the body for a belt) and `thickness`
 * along the run's normal, which is the opposite of what `strap()` in curve.ts
 * produces on a horizontal curve -- its frame prefers world up, so a belt comes
 * out lying flat like a shelf.  Hence the explicit normals.
 */
function bandRun(run: Run, width: number, thickness: number): Field[] {
  const segs: Field[] = [];
  const round = Math.min(thickness, width) * 0.28;
  for (let i = 1; i < run.pts.length; i++) {
    const a = run.pts[i - 1], b = run.pts[i];
    const d = vsub(b, a);
    const len = vlen(d);
    if (len < 1e-6) continue;
    const ex = vnorm(d);
    const n = vnorm(vadd(run.nrm[i - 1], run.nrm[i]));
    const ez = vnorm(vcross(ex, n));      // across the band
    const ey = vnorm(vcross(ez, ex));     // through the leather
    segs.push(orientedBox(
      vmid(a, b), ex, ey, ez,
      [len / 2 + thickness * 0.4, thickness / 2, width / 2],
      round,
    ));
  }
  return segs;
}

/** Resample a coarse control run into a smooth one by chordal subdivision. */
function refine(run: Run, per: number): Run {
  const pts: V3[] = [], nrm: V3[] = [];
  for (let i = 1; i < run.pts.length; i++) {
    for (let k = 0; k < per; k++) {
      const t = k / per;
      pts.push(vadd(vmul(run.pts[i - 1], 1 - t), vmul(run.pts[i], t)));
      nrm.push(vnorm(vadd(vmul(run.nrm[i - 1], 1 - t), vmul(run.nrm[i], t))));
    }
  }
  pts.push(run.pts[run.pts.length - 1]);
  nrm.push(run.nrm[run.nrm.length - 1]);
  return { pts, nrm };
}

/* ------------------------------------------------------------- hip loops */

/**
 * A point on a hip loop: an ellipse taken from the body section at that height
 * and pushed out by a standoff, tilted so `y` falls linearly with x.
 *
 * The radius depends on the height and the height on x, so it is solved by two
 * fixed-point passes -- enough at this scale, the section changes by a couple
 * of millimetres over the tilt.
 */
function hipPoint(
  ctx: PartContext, yMid: number, tilt: number, padX: number, padZ: number, th: number,
): { p: V3; n: V3 } {
  const s = Math.sin(th), c = Math.cos(th);
  let y = yMid, rx = 0, rz = 0;
  for (let k = 0; k < 3; k++) {
    const w = torsoHalfWidth(y, ctx.spec);
    rx = w.x + padX;
    rz = w.z + padZ;
    y = yMid - tilt * (rx * s);
  }
  const nx = s / rx, nz = c / rz;
  const nl = Math.hypot(nx, nz) || 1;
  return { p: [rx * s, y, rz * c], n: [nx / nl, 0, nz / nl] };
}

function hipLoop(
  ctx: PartContext, yMid: number, tilt: number, padX: number, padZ: number, n: number,
): Run {
  const pts: V3[] = [], nrm: V3[] = [];
  for (let i = 0; i <= n; i++) {
    const { p, n: nv } = hipPoint(ctx, yMid, tilt, padX, padZ, (2 * Math.PI * i) / n);
    pts.push(p);
    nrm.push(nv);
  }
  return { pts, nrm };
}

/* ------------------------------------------------- riding over the clothes */

/**
 * How far a point has to move along its normal to clear the garments under it.
 *
 * A belt is worn *over* whatever is there.  The trousers and the hip wrap are
 * other authors' shells and both are still moving, so rather than guessing a
 * standoff this marches outward through their fields until it is clear of
 * them.  Only the PartModule contract is used -- `build(ctx)` giving shells
 * with a field -- and a part that throws or is still a stub simply contributes
 * nothing, which leaves the strap sitting on the body pad instead.
 */
interface Probe {
  /**
   * Signed distance to move `p` along `n` so it lies just outside the clothes:
   * positive when it starts buried, negative when it is floating clear of
   * them.  Capped either way, so a strap never chases a fold across the body
   * and never collapses into a limb when nothing is under it.
   */
  push(p: Vec3, n: Vec3, max: number): number;
  /** Radius from `c` along `n` at which everything under it is clear. */
  fit(c: Vec3, n: Vec3, minR: number, maxR: number): number;
}

function garmentProbe(ctx: PartContext): Probe {
  const collect = (parts: PartModule[]): Field[] => {
    const out: Field[] = [];
    for (const part of parts) {
      try {
        for (const s of part.build(ctx)) out.push(s.field);
      } catch {
        /* a part mid-edit must not take the belt down with it */
      }
    }
    return out;
  };
  // Everything for the hip runs -- they are worn over the wrap.  Only the body
  // and the trousers for a strap round a limb: the hip wrap hangs past the
  // thigh, and fitting a thigh strap to it would blow the strap out to the
  // width of the cloth.
  const all = collect([bodyPart, pantsPart, sashPart]);
  const limb = collect([bodyPart, pantsPart]);

  const STEP = 0.002, SKIN = 0.003;
  const clear = (fs: Field[], x: number, y: number, z: number): boolean => {
    for (let i = 0; i < fs.length; i++) if (fs[i].sdf(x, y, z) < SKIN) return false;
    return true;
  };
  return {
    push(p, n, max) {
      if (all.length === 0 || max <= 0) return 0;
      if (!clear(all, p[0], p[1], p[2])) {
        for (let t = STEP; t <= max; t += STEP) {
          if (clear(all, p[0] + n[0] * t, p[1] + n[1] * t, p[2] + n[2] * t)) return t;
        }
        // Everything within `max` is buried -- most likely the point started
        // inside the *other* leg's trouser, where pushing further would drag
        // the strap across the body.  Stay put rather than chase it.
        return 0;
      }
      // Already clear: come back in until the cloth is met, so the strap lies
      // on the garment instead of hovering off it wherever the cloth is thin.
      for (let t = STEP; t <= max; t += STEP) {
        if (!clear(all, p[0] - n[0] * t, p[1] - n[1] * t, p[2] - n[2] * t)) return -(t - STEP);
      }
      return -max;
    },
    fit(c, n, minR, maxR) {
      if (limb.length === 0) return minR;
      for (let r = minR; r <= maxR; r += STEP) {
        if (clear(limb, c[0] + n[0] * r, c[1] + n[1] * r, c[2] + n[2] * r)) return r;
      }
      return maxR;
    },
  };
}

/**
 * A loop round a limb sized by what is actually there.
 *
 * The spec radius of a thigh is not the radius of the *dressed* thigh, and the
 * body shell is a smooth union of several primitives, so the section is fitted
 * by marching out from the limb axis until the surface is clear.  Directions
 * that never clear -- the inboard arc of a thigh strap, which starts inside the
 * other leg -- are pulled back to the median so the strap does not shoot across
 * the body.
 */
function fitLoop(
  centre: Vec3, axis: Vec3, n: number, minR: number, maxR: number, pad: number, probe: Probe,
): Run {
  const ax = vnorm(axis);
  const u = vnorm(vcross([0, 0, 1], ax));
  const v = vnorm(vcross(ax, u));
  const dirs: V3[] = [];
  const rs: number[] = [];
  for (let i = 0; i <= n; i++) {
    const a = (2 * Math.PI * i) / n;
    const dir = vnorm(vadd(vmul(u, Math.cos(a)), vmul(v, Math.sin(a))));
    dirs.push(dir);
    rs.push(probe.fit(centre, dir, minR, maxR));
  }
  const sorted = rs.slice(0, n).sort((a, b) => a - b);
  const med = sorted[Math.floor(sorted.length / 2)];
  for (let i = 0; i < rs.length; i++) rs[i] = Math.min(rs[i], med * 1.18);
  // two smoothing passes round the closed loop
  for (let pass = 0; pass < 2; pass++) {
    const src = rs.slice();
    for (let i = 0; i < rs.length; i++) {
      const a = src[(i - 1 + n) % n], b = src[(i + 1) % n];
      rs[i] = (a + 2 * src[i] + b) / 4;
    }
  }
  rs[n] = rs[0];
  return {
    pts: dirs.map((dir, i) => vadd(centre, vmul(dir, rs[i] + pad))),
    nrm: dirs,
  };
}

/**
 * Push a run out along its normals until it clears the clothes, then smooth
 * the offsets round the run so a fold in the cloth does not put a kink in the
 * leather.
 */
function clearRun(
  run: Run, probe: Probe,
  extra: number, closed: boolean, max: number,
): Run {
  const n = run.pts.length;
  let off = run.pts.map((p, i) => probe.push(p, run.nrm[i], max));
  for (let pass = 0; pass < 2; pass++) {
    const src = off;
    off = src.map((_, i) => {
      const a = closed ? src[(i - 1 + n - 1) % (n - 1)] : src[Math.max(0, i - 1)];
      const b = closed ? src[(i + 1) % (n - 1)] : src[Math.min(n - 1, i + 1)];
      return (a + 2 * src[i] + b) / 4;
    });
  }
  return {
    pts: run.pts.map((p, i) => vadd(p, vmul(run.nrm[i], off[i] + extra))),
    nrm: run.nrm,
  };
}

/** A loop round a limb: `axis` is the limb direction, u/v the section axes. */
function limbLoop(centre: Vec3, axis: Vec3, rx: number, rz: number, n: number): Run {
  const ax = vnorm(axis);
  const u = vnorm(vcross([0, 0, 1], ax));   // ~+x for a hanging limb
  const v = vnorm(vcross(ax, u));           // ~+z
  const pts: V3[] = [], nrm: V3[] = [];
  for (let i = 0; i <= n; i++) {
    const a = (2 * Math.PI * i) / n;
    const ca = Math.cos(a), sa = Math.sin(a);
    pts.push(vadd(centre, vadd(vmul(u, rx * ca), vmul(v, rz * sa))));
    nrm.push(vnorm(vadd(vmul(u, ca / rx), vmul(v, sa / rz))));
  }
  return { pts, nrm };
}

/** Point and outward normal at angle `a` on a limb loop (same frame as above). */
function limbPoint(centre: Vec3, axis: Vec3, rx: number, rz: number, a: number): { p: V3; n: V3 } {
  const ax = vnorm(axis);
  const u = vnorm(vcross([0, 0, 1], ax));
  const v = vnorm(vcross(ax, u));
  const ca = Math.cos(a), sa = Math.sin(a);
  return {
    p: vadd(centre, vadd(vmul(u, rx * ca), vmul(v, rz * sa))),
    n: vnorm(vadd(vmul(u, ca / rx), vmul(v, sa / rz))),
  };
}

/* ---------------------------------------------------------------- fittings */

/**
 * A buckle frame: four bars round a hole, with the tongue across the middle.
 * `ex` runs along the strap, `ez` across it, `ey` out through the leather.
 */
function buckle(c: Vec3, ex: Vec3, ey: Vec3, ez: Vec3, w: number, h: number, t: number): Field[] {
  const bar = 0.007;
  const out: Field[] = [];
  const half: V3 = [w / 2, t / 2, bar / 2];
  // top and bottom bars (offset across the strap)
  for (const s of [-1, 1]) {
    out.push(orientedBox(vadd(c, vmul(ez, s * (h / 2 - bar / 2))), ex, ey, ez, half, bar * 0.3));
  }
  // side bars (offset along the strap)
  for (const s of [-1, 1]) {
    out.push(orientedBox(
      vadd(c, vmul(ex, s * (w / 2 - bar / 2))), ex, ey, ez,
      [bar / 2, t / 2, h / 2], bar * 0.3,
    ));
  }
  // tongue: a bar across the hole, lying a touch proud
  out.push(orientedBox(
    vadd(c, vmul(ey, t * 0.15)), ex, ey, ez,
    [bar * 0.42, t * 0.45, h / 2 - bar * 0.6], bar * 0.2,
  ));
  return out;
}

/** A square keeper -- the loops that ride the drop straps. */
function keeper(c: Vec3, ex: Vec3, ey: Vec3, ez: Vec3, w: number, h: number, t: number): Field[] {
  const bar = 0.006;
  const out: Field[] = [];
  for (const s of [-1, 1]) {
    out.push(orientedBox(vadd(c, vmul(ez, s * (h / 2 - bar / 2))), ex, ey, ez, [w / 2, t / 2, bar / 2], bar * 0.3));
    out.push(orientedBox(vadd(c, vmul(ex, s * (w / 2 - bar / 2))), ex, ey, ez, [bar / 2, t / 2, h / 2], bar * 0.3));
  }
  return out;
}

/* ------------------------------------------------------------------ dims */

interface Dims {
  hipY: number; hipTilt: number; hipPadX: number; hipPadZ: number;
  beltWidth: number; beltThickness: number;
  buckleX: number; buckleW: number; buckleH: number; buckleT: number;
  rivetCount: number; rivetR: number;
  slungY: number; slungTilt: number; slungPadX: number; slungPadZ: number;
  slungWidth: number; slungThickness: number;
  hipMaxPush: number; dropMaxPush: number;
  dropWidth: number; dropThickness: number;
  thighStrapY: number; thighPad: number; thighWidth: number; thighThickness: number;
  holsterY: number; holsterR: number;
  rigSide: 1 | -1; armBandUpperY: number; armBandLowerY: number;
  bandWidth: number; bandThickness: number; bandPad: number;
  segsRing: number; voxelScale: number;
}

function dims(ctx: PartContext): Dims {
  const B = ctx.spec.belts as unknown as Record<string, number>;
  const num = (k: string, dflt: number) => (typeof B[k] === 'number' ? B[k] : dflt);
  return {
    hipY: num('hipY', 1.062),
    hipTilt: num('hipTilt', 0.29),
    hipPadX: num('hipPadX', 0.018),
    hipPadZ: num('hipPadZ', 0.020),
    beltWidth: num('beltWidth', 0.033),
    beltThickness: num('beltThickness', 0.012),
    buckleX: num('buckleX', 0.022),
    buckleW: num('buckleW', 0.050),
    buckleH: num('buckleH', 0.040),
    buckleT: num('buckleT', 0.013),
    rivetCount: Math.round(num('rivetCount', 10)),
    rivetR: num('rivetR', 0.0045),
    slungY: num('slungY', 1.004),
    slungTilt: num('slungTilt', 0.50),
    slungPadX: num('slungPadX', 0.018),
    slungPadZ: num('slungPadZ', 0.023),
    slungWidth: num('slungWidth', 0.024),
    slungThickness: num('slungThickness', 0.011),
    hipMaxPush: num('hipMaxPush', 0.055),
    dropMaxPush: num('dropMaxPush', 0.040),
    dropWidth: num('dropWidth', 0.026),
    dropThickness: num('dropThickness', 0.011),
    thighStrapY: num('thighStrapY', 0.855),
    thighPad: num('thighPad', 0.004),
    thighWidth: num('thighWidth', 0.030),
    thighThickness: num('thighThickness', 0.011),
    holsterY: num('holsterY', 0.884),
    holsterR: num('holsterR', 0.034),
    // +1 = her left = +X, which is the side the Zapper, the drop-leg rig and
    // the two arm bands are all on; see docs/HANDEDNESS.md and the fragment.
    rigSide: num('rigSide', 1) >= 0 ? 1 : -1,
    armBandUpperY: num('armBandUpperY', 1.266),
    armBandLowerY: num('armBandLowerY', 1.230),
    bandWidth: num('bandWidth', 0.032),
    bandThickness: num('bandThickness', 0.010),
    bandPad: num('bandPad', 0.005),
    segsRing: Math.round(num('segsRing', 30)),
    voxelScale: num('voxelScale', 1.2),
  };
}

/* ---------------------------------------------------------------- geometry */

/** Axis and section of a limb between two joints, sampled at a height. */
function limbAt(
  a: Vec3, b: Vec3, ra: number, rb: number, squashZ: number, y: number,
): { c: V3; axis: V3; rx: number; rz: number } {
  const t = Math.max(0, Math.min(1, (y - a[1]) / (b[1] - a[1] || 1e-6)));
  const c: V3 = [a[0] + (b[0] - a[0]) * t, y, a[2] + (b[2] - a[2]) * t];
  const rx = ra + (rb - ra) * t;
  return { c, axis: vsub(b, a), rx, rz: rx * squashZ };
}

export const beltsPart: PartModule = {
  id: 'belts',
  build(ctx) {
    const { mat, skel, spec } = ctx;
    const d = dims(ctx);
    const w = spec.widths;
    const leather: Field[] = [];
    const brass: Field[] = [];
    const probe = garmentProbe(ctx);

    /** Frame at index `i` of a run: along the strap, out of it, across it. */
    const frameOf = (run: Run, i: number) => {
      const a = run.pts[Math.max(0, i - 1)], b = run.pts[Math.min(run.pts.length - 1, i + 1)];
      const ex = vnorm(vsub(b, a));
      const ez = vnorm(vcross(ex, run.nrm[i]));
      const ey = vnorm(vcross(ez, ex));
      return { ex, ey, ez, p: run.pts[i] };
    };

    /* ------------------------------------------------------- the hip belt */

    // The belt rides high on the rig side and falls away across the other hip.
    const beltTilt = -d.rigSide * Math.abs(d.hipTilt);
    const slungTilt = -d.rigSide * Math.abs(d.slungTilt);

    const belt = clearRun(
      hipLoop(ctx, d.hipY, beltTilt, d.hipPadX, d.hipPadZ, d.segsRing),
      probe, d.beltThickness * 0.5 + 0.002, true, d.hipMaxPush,
    );
    leather.push(...bandRun(belt, d.beltWidth, d.beltThickness));

    // Buckle at the front, a couple of centimetres off centre toward the rig
    // side, as on the sheet.
    {
      // Nearest run sample to buckleX on the front half of the loop.
      let bi = 0, best = Infinity;
      for (let i = 0; i < belt.pts.length - 1; i++) {
        if (belt.pts[i][2] <= 0) continue;
        const e = Math.abs(belt.pts[i][0] - d.buckleX * d.rigSide);
        if (e < best) { best = e; bi = i; }
      }
      const f = frameOf(belt, bi);
      const c = vadd(f.p, vmul(f.ey, d.buckleT * 0.22));
      brass.push(...buckle(c, f.ex, f.ey, f.ez, d.buckleW, d.buckleH, d.buckleT));
      // The tail of the belt folds back through the buckle and hangs.
      const tail = refine({
        pts: [c, vadd(c, vmul(f.ex, 0.050)), vadd(vadd(c, vmul(f.ex, 0.078)), [0, -0.032, 0])],
        nrm: [f.ey, f.ey, f.ey],
      }, 3);
      leather.push(...bandRun(tail, d.beltWidth * 0.72, d.beltThickness * 0.8));
    }

    // Rivets round the run: brass domes sitting half in the leather.
    {
      const step = Math.max(1, Math.round((belt.pts.length - 1) / d.rivetCount));
      for (let i = 1; i < belt.pts.length - 1; i += step) {
        brass.push(sphere(vadd(belt.pts[i], vmul(belt.nrm[i], d.beltThickness * 0.30)), d.rivetR));
      }
    }

    /* --------------------------------- the slung strap under it, and its drops */

    const slung = clearRun(
      hipLoop(ctx, d.slungY, slungTilt, d.slungPadX, d.slungPadZ, d.segsRing),
      probe, d.slungThickness * 0.5 + 0.002, true, d.hipMaxPush,
    );
    leather.push(...bandRun(slung, d.slungWidth, d.slungThickness));

    /**
     * A strap hanging from the hip rig down the front-outer face of a thigh.
     * `side` is +1 for her left; it leaves the belt just forward of the hip's
     * widest point and lands on the thigh, bowing out where it crosses the
     * crease, then is pushed clear of the trousers like everything else.
     */
    const dropStrap = (side: 1 | -1, yEnd: number): Run => {
      const th = side > 0 ? 1.10 : -1.10;
      const top = hipPoint(ctx, d.hipY, beltTilt, d.hipPadX, d.hipPadZ, th);
      // Where that azimuth actually ended up on the belt, after the belt was
      // pushed out over the clothes: the drop has to start *on* the leather,
      // not where the loop was before it was fitted, or the two come apart.
      let bi = 0, bd = Infinity;
      for (let i = 0; i < belt.pts.length - 1; i++) {
        const dd = Math.hypot(
          belt.pts[i][0] - top.p[0], belt.pts[i][1] - top.p[1], belt.pts[i][2] - top.p[2],
        );
        if (dd < bd) { bd = dd; bi = i; }
      }
      const anchorPt = vadd(belt.pts[bi], vmul(belt.nrm[bi], -d.beltThickness * 0.25));
      const hip = side > 0 ? skel.hipL : skel.hipR;
      const knee = side > 0 ? skel.kneeL : skel.kneeR;
      const lower = limbAt(
        [hip[0], hip[1] + 0.02, hip[2]], knee, w.thighR, w.kneeR, 0.94, yEnd,
      );
      const end = limbPoint(lower.c, lower.axis, lower.rx, lower.rz,
        side > 0 ? 0.62 : Math.PI - 0.62);
      const pts: V3[] = [];
      const nrm: V3[] = [];
      const N = 7;
      for (let i = 0; i <= N; i++) {
        const t = i / N;
        const s = t * t * (3 - 2 * t);
        const p = vadd(vmul(top.p, 1 - s), vmul(end.p, s));
        const n = vnorm(vadd(vmul(top.n, 1 - s), vmul(end.n, s)));
        pts.push(p);
        nrm.push(n);
      }
      const run = clearRun({ pts, nrm }, probe, d.dropThickness * 0.5 + 0.002, false, d.dropMaxPush);
      run.pts[0] = anchorPt;
      run.nrm[0] = belt.nrm[bi];
      return run;
    };

    for (const side of [1, -1] as (1 | -1)[]) {
      // Only the rig side reaches the thigh strap; the other hangs shorter.
      const run = dropStrap(side, side === d.rigSide ? d.thighStrapY : 0.880);
      leather.push(...bandRun(run, d.dropWidth, d.dropThickness));
      // two keepers down each drop, at the heights they read on the sheet
      for (const k of [3, 5]) {
        const f = frameOf(run, k);
        brass.push(...keeper(
          vadd(f.p, vmul(f.ey, d.dropThickness * 0.10)), f.ex, f.ey, f.ez,
          d.dropWidth + 0.014, d.dropWidth + 0.006, d.dropThickness * 1.5,
        ));
      }
    }

    /* -------------------------------------- the thigh strap and the holster */

    {
      const hip = d.rigSide > 0 ? skel.hipL : skel.hipR;
      const knee = d.rigSide > 0 ? skel.kneeL : skel.kneeR;
      const at = limbAt([hip[0], hip[1] + 0.02, hip[2]], knee, w.thighR, w.kneeR, 0.94, d.thighStrapY);
      const thigh = fitLoop(at.c, at.axis, 20, at.rx * 0.55, at.rx * 1.8, d.thighPad, probe);
      leather.push(...bandRun(thigh, d.thighWidth, d.thighThickness));

      // Buckle on the outboard face of the thigh strap.
      let bi = 0, bx = -Infinity;
      for (let i = 0; i < thigh.pts.length - 1; i++) {
        const outward = thigh.pts[i][0] * d.rigSide;
        if (outward > bx) { bx = outward; bi = i; }
      }
      const bf = frameOf(thigh, bi);
      brass.push(...buckle(
        vadd(bf.p, vmul(bf.ey, d.thighThickness * 0.2)), bf.ex, bf.ey, bf.ez,
        0.036, d.thighWidth + 0.006, 0.011,
      ));

      // Holster: a backing plate against the thigh and two retention straps
      // round where the Zapper hangs, left open at the front so the pistol
      // shell can sit in the cradle instead of inside solid leather.
      // The pistol's own anchor, mirrored onto the rig side: the Zapper part is
      // still authored on the old (mirrored) convention, and the holster has to
      // be on the side docs/HANDEDNESS.md puts the gun, not the side the stale
      // number puts it.  When that fragment is corrected the two coincide.
      const anchor = (spec.zapper as unknown as { anchor: number[] }).anchor;
      const ax = (anchor ? Math.abs(anchor[0]) : 0.118) * d.rigSide;
      const az = anchor ? anchor[2] : 0.055;
      const dirx = ax - at.c[0], dirz = az - at.c[2];
      const dl = Math.hypot(dirx, dirz) || 1;
      const pn: V3 = [dirx / dl, 0, dirz / dl];
      const pt: V3 = [-pn[2], 0, pn[0]];
      const plateR = probe.fit([at.c[0], d.holsterY - 0.015, at.c[2]], pn, at.rx * 0.55, at.rx * 1.8);
      const plateC: V3 = [
        at.c[0] + pn[0] * (plateR + 0.008),
        d.holsterY - 0.015,
        at.c[2] + pn[2] * (plateR + 0.008),
      ];
      leather.push(orientedBox(plateC, pt, pn, [0, 1, 0], [0.030, 0.006, 0.052], 0.006));
      for (const yy of [d.holsterY + 0.030, d.holsterY - 0.040]) {
        const c: V3 = [ax, yy, az];
        const loop = limbLoop(c, [0, 1, 0], d.holsterR, d.holsterR, 14);
        // keep only the outboard/front three quarters -- the arc that faces
        // the thigh is the plate above
        const keep: Run = { pts: [], nrm: [] };
        for (let i = 0; i < loop.pts.length; i++) {
          const p = loop.pts[i];
          if ((p[0] - c[0]) * pn[0] + (p[2] - c[2]) * pn[2] > -d.holsterR * 0.35) {
            keep.pts.push(p);
            keep.nrm.push(loop.nrm[i]);
          }
        }
        if (keep.pts.length > 1) leather.push(...bandRun(keep, 0.020, 0.008));
      }
    }

    /* --------------------------------------------------------- arm bands */

    {
      const side = d.rigSide;
      const sh = side > 0 ? skel.shoulderL : skel.shoulderR;
      const el = side > 0 ? skel.elbowL : skel.elbowR;
      for (const y of [d.armBandUpperY, d.armBandLowerY]) {
        const at = limbAt(sh, el, w.upperArmR, w.elbowR, 0.94, y);
        // Fitted, not spec-derived: the deltoid is a smooth union and the arm
        // is fatter than upperArmR where these bands sit.
        const band = fitLoop(at.c, at.axis, 18, at.rx * 0.5, at.rx * 2.2, d.bandPad, probe);
        leather.push(...bandRun(band, d.bandWidth, d.bandThickness));
        // small buckle plate outboard, where the reference hangs its tag
        let oi = 0, ox = side > 0 ? -Infinity : Infinity;
        for (let i = 0; i < band.pts.length - 1; i++) {
          const x = band.pts[i][0];
          if (side > 0 ? x > ox : x < ox) { ox = x; oi = i; }
        }
        const of = frameOf(band, oi);
        const p0 = { p: of.p, n: of.ey };
        const ex = of.ex, ey = of.ey, ez = of.ez;
        brass.push(...keeper(
          vadd(p0.p, vmul(ey, d.bandThickness * 0.25)), ex, ey, ez,
          0.020, d.bandWidth + 0.004, 0.010,
        ));
        // the tail of the band, hanging a couple of centimetres
        const tail = refine({
          pts: [
            vadd(p0.p, vmul(ey, d.bandThickness * 0.5)),
            vadd(vadd(p0.p, vmul(ey, d.bandThickness * 0.9)), [0, -0.018, 0]),
            vadd(vadd(p0.p, vmul(ey, d.bandThickness * 0.6)), [0, -0.032, 0]),
          ],
          nrm: [ey, ey, ey],
        }, 2);
        leather.push(...bandRun(tail, 0.014, 0.006));
      }
    }

    /* ------------------------------------------------------------- shell */

    const brassField = fastUnion(brass);
    const shell: Shell = {
      name: 'belts',
      field: fastUnion([...leather, ...brass]),
      // 1.5 mm of slack: the surface net's vertices sit off the true zero set
      // by up to half a voxel, and a buckle bar is only 7 mm across.
      material: paint(constMaterial(mat.leather), brassField, mat.brass, 0.0015),
      voxelScale: d.voxelScale,
    };
    return [shell];
  },
};
