/**
 * Curves swept into fields: tubes, braids, straps and laces.
 *
 * Jinx is mostly curves -- two braids that reach the ankles, the choker wraps,
 * the belt runs, the boot laces -- so these get their own module rather than
 * being open-coded per part.  A swept curve is just a union of round cones
 * along a resampled polyline; that stays an exact distance field, which keeps
 * the mesher's empty-space skipping valid.
 */
import { Box, Field, Vec3, box, boxExpand, boxOf } from './types.js';
import { capsule, clamp, field, union } from './ops.js';

export type Curve = Vec3[];

/** Uniform Catmull-Rom through the control points, clamped at the ends. */
export function catmullRom(pts: Curve, t: number): Vec3 {
  const n = pts.length;
  if (n === 0) return [0, 0, 0];
  if (n === 1) return pts[0];
  const u = clamp(t, 0, 1) * (n - 1);
  const i = Math.min(n - 2, Math.floor(u));
  const f = u - i;
  const p0 = pts[Math.max(0, i - 1)];
  const p1 = pts[i];
  const p2 = pts[i + 1];
  const p3 = pts[Math.min(n - 1, i + 2)];
  const f2 = f * f, f3 = f2 * f;
  const out: [number, number, number] = [0, 0, 0];
  for (let k = 0; k < 3; k++) {
    out[k] = 0.5 * (
      2 * p1[k] +
      (-p0[k] + p2[k]) * f +
      (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f2 +
      (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * f3
    );
  }
  return out;
}

export function resample(pts: Curve, n: number): Curve {
  const out: Curve = [];
  for (let i = 0; i < n; i++) out.push(catmullRom(pts, n === 1 ? 0 : i / (n - 1)));
  return out;
}

export function curveLength(pts: Curve): number {
  let L = 0;
  for (let i = 1; i < pts.length; i++) {
    L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]);
  }
  return L;
}

/** Unit tangent at parameter t along the sampled curve. */
export function tangentAt(pts: Curve, t: number): Vec3 {
  const e = 1e-3;
  const a = catmullRom(pts, clamp(t - e, 0, 1));
  const b = catmullRom(pts, clamp(t + e, 0, 1));
  const d: [number, number, number] = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const L = Math.hypot(d[0], d[1], d[2]) || 1;
  return [d[0] / L, d[1] / L, d[2] / L];
}

/** A frame perpendicular to the tangent, kept stable by preferring world up. */
export function frameAt(pts: Curve, t: number): { tan: Vec3; nor: Vec3; bin: Vec3 } {
  const tan = tangentAt(pts, t);
  let up: Vec3 = Math.abs(tan[1]) > 0.9 ? [0, 0, 1] : [0, 1, 0];
  let nx = up[1] * tan[2] - up[2] * tan[1];
  let ny = up[2] * tan[0] - up[0] * tan[2];
  let nz = up[0] * tan[1] - up[1] * tan[0];
  const nl = Math.hypot(nx, ny, nz) || 1;
  nx /= nl; ny /= nl; nz /= nl;
  const bx = tan[1] * nz - tan[2] * ny;
  const by = tan[2] * nx - tan[0] * nz;
  const bz = tan[0] * ny - tan[1] * nx;
  return { tan, nor: [nx, ny, nz], bin: [bx, by, bz] };
}

export interface TubeOptions {
  /** Segments along the curve; more is smoother and slower. */
  segments?: number;
  /** Radius as a function of arc parameter in [0,1]. */
  radius: number | ((t: number) => number);
}

export function tube(pts: Curve, opts: TubeOptions): Field {
  const n = Math.max(2, opts.segments ?? Math.max(8, Math.round(curveLength(pts) / 0.02)));
  const line = resample(pts, n);
  const rf = typeof opts.radius === 'number' ? () => opts.radius as number : opts.radius;
  const segs: Field[] = [];
  for (let i = 1; i < n; i++) {
    const t0 = (i - 1) / (n - 1), t1 = i / (n - 1);
    segs.push(capsule(line[i - 1], line[i], rf(t0), rf(t1)));
  }
  return union(...segs);
}

/**
 * A plaited rope: three strands wound helically around the curve.
 *
 * The reference braid reads as a stack of lobes rather than as three visible
 * strands at this scale, so the default twist is tuned to produce the lobe
 * pitch seen on the sheet rather than an anatomically correct plait.
 */
export interface BraidOptions {
  segments?: number;
  /** Overall radius of the braid envelope. */
  radius: number | ((t: number) => number);
  /** Radius of one strand, as a fraction of the envelope radius. */
  strandScale?: number;
  /** Turns of the plait over the whole length. */
  turns?: number;
  strands?: number;
}

export function braid(pts: Curve, opts: BraidOptions): Field {
  const n = Math.max(8, opts.segments ?? Math.max(24, Math.round(curveLength(pts) / 0.012)));
  const strands = opts.strands ?? 3;
  const strandScale = opts.strandScale ?? 0.62;
  const turns = opts.turns ?? Math.max(4, curveLength(pts) / 0.055);
  const rf = typeof opts.radius === 'number' ? () => opts.radius as number : opts.radius;

  const paths: Curve[] = Array.from({ length: strands }, () => []);
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    const p = catmullRom(pts, t);
    const { nor, bin } = frameAt(pts, t);
    const R = rf(t) * (1 - strandScale);
    for (let s = 0; s < strands; s++) {
      const a = 2 * Math.PI * (turns * t + s / strands);
      paths[s].push([
        p[0] + (nor[0] * Math.cos(a) + bin[0] * Math.sin(a)) * R,
        p[1] + (nor[1] * Math.cos(a) + bin[1] * Math.sin(a)) * R,
        p[2] + (nor[2] * Math.cos(a) + bin[2] * Math.sin(a)) * R,
      ]);
    }
  }
  return union(...paths.map((path) => {
    const segs: Field[] = [];
    for (let i = 1; i < path.length; i++) {
      const t0 = (i - 1) / (path.length - 1), t1 = i / (path.length - 1);
      segs.push(capsule(path[i - 1], path[i], rf(t0) * strandScale, rf(t1) * strandScale));
    }
    return union(...segs);
  }));
}

/**
 * A flat strap following a curve: a tube squashed along the curve's normal.
 *
 * Implemented as boxes rather than as a scaled tube so it keeps hard edges,
 * which is what reads as leather at this scale.
 */
export function strap(pts: Curve, width: number, thickness: number, segments?: number): Field {
  const n = Math.max(3, segments ?? Math.max(10, Math.round(curveLength(pts) / 0.015)));
  const line = resample(pts, n);
  const segs: Field[] = [];
  for (let i = 1; i < n; i++) {
    const t = (i - 0.5) / (n - 1);
    const { nor, bin } = frameAt(pts, t);
    const a = line[i - 1], b = line[i];
    const mid: Vec3 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
    const half = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) / 2 + thickness * 0.5;
    const tan = tangentAt(pts, t);
    segs.push(orientedBox(mid, tan, nor, bin, [half, width / 2, thickness / 2], thickness * 0.35));
  }
  return union(...segs);
}

/** Rounded box in an arbitrary orthonormal frame. */
export function orientedBox(c: Vec3, ex: Vec3, ey: Vec3, ez: Vec3, half: Vec3, round = 0): Field {
  const corners: Vec3[] = [];
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
    corners.push([
      c[0] + ex[0] * half[0] * sx + ey[0] * half[1] * sy + ez[0] * half[2] * sz,
      c[1] + ex[1] * half[0] * sx + ey[1] * half[1] * sy + ez[1] * half[2] * sz,
      c[2] + ex[2] * half[0] * sx + ey[2] * half[1] * sy + ez[2] * half[2] * sz,
    ]);
  }
  const bounds: Box = boxExpand(boxOf(corners), round);
  const hx = half[0] - round, hy = half[1] - round, hz = half[2] - round;
  return field((x, y, z) => {
    const px = x - c[0], py = y - c[1], pz = z - c[2];
    const qx = Math.abs(px * ex[0] + py * ex[1] + pz * ex[2]) - hx;
    const qy = Math.abs(px * ey[0] + py * ey[1] + pz * ey[2]) - hy;
    const qz = Math.abs(px * ez[0] + py * ez[1] + pz * ez[2]) - hz;
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0), Math.max(qz, 0)) + Math.min(Math.max(qx, qy, qz), 0) - round;
  }, bounds);
}

/** Cross-lacing between two rails -- the boot laces and the top's X. */
export function lacing(left: Curve, right: Curve, rungs: number, radius: number): Field {
  const segs: Field[] = [];
  for (let i = 0; i < rungs; i++) {
    const t0 = i / rungs, t1 = (i + 1) / rungs;
    segs.push(tube([catmullRom(left, t0), catmullRom(right, t1)], { radius, segments: 3 }));
    segs.push(tube([catmullRom(right, t0), catmullRom(left, t1)], { radius, segments: 3 }));
  }
  return union(...segs);
}

export const curveBounds = (pts: Curve, pad: number): Box => boxOf(pts, pad);
export { box };
