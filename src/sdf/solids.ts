/**
 * Higher-level solids built on the primitives: lathes, lofts, angular repeats.
 *
 * These exist because the same three shapes kept getting open-coded. A boot
 * sole, a gun barrel, a buckle and a belt eyelet are all lathes; a trouser leg
 * and a braid envelope are lofts; a boot tread and a revolver chamber are
 * angular repeats. Hand-rolling each one as a pile of capsules is slower to
 * write, slower to evaluate, and gets the Lipschitz bound wrong.
 */
import { Box, Field, Vec3, box, boxExpand, boxOf } from './types.js';
import { capsuleOval, clamp, field, smoothUnion } from './ops.js';

/**
 * Lathe: revolve a 2D signed distance field in (r, y) about the Y axis at `c`.
 *
 * `profile(r, y)` is measured in the half-plane r >= 0, with y relative to `c`.
 * The result is an exact distance field wherever the profile is, which is why
 * this is preferable to stacking rings.
 */
export function revolveY(
  c: Vec3,
  profile: (r: number, y: number) => number,
  bounds: { r: number; y0: number; y1: number },
): Field {
  const b: Box = box(
    [c[0] - bounds.r, c[1] + bounds.y0, c[2] - bounds.r],
    [c[0] + bounds.r, c[1] + bounds.y1, c[2] + bounds.r],
  );
  return field((x, y, z) => profile(Math.hypot(x - c[0], z - c[2]), y - c[1]), b);
}

/** A 2D rounded box in the lathe half-plane, the usual lathe profile. */
export const profileBox = (r0: number, r1: number, y0: number, y1: number, round = 0) =>
  (r: number, y: number) => {
    const cx = (r0 + r1) / 2, cy = (y0 + y1) / 2;
    const hx = Math.max(0, (r1 - r0) / 2 - round), hy = Math.max(0, (y1 - y0) / 2 - round);
    const qx = Math.abs(r - cx) - hx, qy = Math.abs(y - cy) - hy;
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - round;
  };

/** Union of lathe profiles -- stack sections without leaving a seam. */
export const profileUnion = (...ps: ((r: number, y: number) => number)[]) =>
  (r: number, y: number) => {
    let m = Infinity;
    for (const p of ps) {
      const v = p(r, y);
      if (v < m) m = v;
    }
    return m;
  };

export interface LoftSample {
  /** Half-width in x. */
  x: number;
  /** Half-depth in z; defaults to `x`. */
  z?: number;
  /** Centre offset in x and z at this height. */
  cx?: number;
  cz?: number;
}

/**
 * Loft an elliptical section along Y, sampling `at(y)` every `step` metres.
 *
 * Sampling finely matters: a coarse stack leaves a visible ring at every joint
 * because both the radius and the squash step between segments. At ~12 mm the
 * steps fall below the blend radius and it reads as one surface.
 */
export function loftY(
  y0: number,
  y1: number,
  at: (y: number) => LoftSample,
  opts: { step?: number; blend?: number } = {},
): Field {
  const step = opts.step ?? 0.012;
  const blend = opts.blend ?? 0.018;
  const n = Math.max(2, Math.round(Math.abs(y1 - y0) / step));
  const segs: Field[] = [];
  for (let i = 0; i < n; i++) {
    const ya = y0 + ((y1 - y0) * i) / n;
    const yb = y0 + ((y1 - y0) * (i + 1)) / n;
    const a = at(ya), b = at(yb);
    const az = a.z ?? a.x, bz = b.z ?? b.x;
    segs.push(capsuleOval(
      [a.cx ?? 0, ya, a.cz ?? 0],
      [b.cx ?? 0, yb, b.cz ?? 0],
      a.x, b.x,
      ((az / a.x) + (bz / b.x)) / 2,
      1,
    ));
  }
  return smoothUnion(blend, ...segs);
}

/**
 * Repeat `f` `n` times around the Y axis through `c`.
 *
 * Exact inside each wedge. `f` should be authored in the +Z half and stay
 * inside its wedge, or neighbouring copies will clip each other.
 */
export function repeatAngularY(c: Vec3, n: number, f: Field): Field {
  const seg = (2 * Math.PI) / n;
  const reach = Math.max(
    Math.hypot(f.bounds.max[0] - c[0], f.bounds.max[2] - c[2]),
    Math.hypot(f.bounds.min[0] - c[0], f.bounds.min[2] - c[2]),
  );
  return field(
    (x, y, z) => {
      const dx = x - c[0], dz = z - c[2];
      const a = Math.atan2(dx, dz);
      const k = Math.round(a / seg) * seg;
      const ca = Math.cos(-k), sa = Math.sin(-k);
      return f.sdf(c[0] + (ca * dx - sa * dz), y, c[2] + (sa * dx + ca * dz));
    },
    box(
      [c[0] - reach, f.bounds.min[1], c[2] - reach],
      [c[0] + reach, f.bounds.max[1], c[2] + reach],
    ),
    f.lip,
  );
}

/** Repeat along one axis a fixed number of times -- rivets, stripes, laces. */
export function repeatLinear(f: Field, axis: 0 | 1 | 2, spacing: number, count: number): Field {
  const half = ((count - 1) * spacing) / 2;
  return field(
    (x, y, z) => {
      const p = [x, y, z];
      const t = clamp(Math.round((p[axis] + half) / spacing), 0, count - 1);
      p[axis] -= t * spacing - half;
      return f.sdf(p[0], p[1], p[2]);
    },
    (() => {
      const b = { min: [...f.bounds.min] as [number, number, number], max: [...f.bounds.max] as [number, number, number] };
      b.min[axis] -= half;
      b.max[axis] += half;
      return box(b.min, b.max);
    })(),
    f.lip,
  );
}

/**
 * Twist about Y. `turns` is full turns per metre of height.
 *
 * A twist steepens the field in proportion to the radius it acts over, so the
 * Lipschitz bound has to grow with it or the mesher will punch holes.
 */
export function twistY(f: Field, turns: number, c: Vec3 = [0, 0, 0]): Field {
  const reach = Math.max(
    Math.hypot(f.bounds.max[0] - c[0], f.bounds.max[2] - c[2]),
    Math.hypot(f.bounds.min[0] - c[0], f.bounds.min[2] - c[2]),
  );
  const k = turns * 2 * Math.PI;
  return field(
    (x, y, z) => {
      const a = -k * (y - c[1]);
      const ca = Math.cos(a), sa = Math.sin(a);
      const dx = x - c[0], dz = z - c[2];
      return f.sdf(c[0] + ca * dx - sa * dz, y, c[2] + sa * dx + ca * dz);
    },
    box(
      [c[0] - reach, f.bounds.min[1], c[2] - reach],
      [c[0] + reach, f.bounds.max[1], c[2] + reach],
    ),
    f.lip * Math.hypot(1, k * reach),
  );
}

/**
 * Stretch a shape by moving its centre apart along each axis, keeping the ends
 * intact -- the cheap way to turn a sphere into a capsule or a box into a slab.
 * Exact for positive `h`.
 */
export function elongate(f: Field, h: Vec3): Field {
  return field(
    (x, y, z) => f.sdf(
      x - clamp(x, -h[0], h[0]),
      y - clamp(y, -h[1], h[1]),
      z - clamp(z, -h[2], h[2]),
    ),
    boxExpand(box(
      [f.bounds.min[0] - h[0], f.bounds.min[1] - h[1], f.bounds.min[2] - h[2]],
      [f.bounds.max[0] + h[0], f.bounds.max[1] + h[1], f.bounds.max[2] + h[2]],
    ), 0),
    f.lip,
  );
}

/**
 * Clip a field to one side of an axis-aligned plane, and shrink its bounds.
 *
 * Every garment author hit the same trap: `intersect` is a max, so a cut field
 * has to be NEGATIVE on the side it keeps.  Writing the plane the natural way
 * round (`y - hemY`, positive above) silently produced a shell with zero
 * triangles and no diagnostic beyond "produced no geometry".  This takes the
 * side you want as a word, and clips the bounds too, which is what actually
 * makes the mesher cheap -- `halfSpace` leaves them at the full body.
 */
export function cut(f: Field, axis: 0 | 1 | 2, at: number, keep: 'below' | 'above'): Field {
  const mn = [...f.bounds.min] as [number, number, number];
  const mx = [...f.bounds.max] as [number, number, number];
  if (keep === 'below') mx[axis] = Math.min(mx[axis], at);
  else mn[axis] = Math.max(mn[axis], at);
  return field(
    (x, y, z) => {
      const p = axis === 0 ? x : axis === 1 ? y : z;
      const d = keep === 'below' ? p - at : at - p;
      return Math.max(f.sdf(x, y, z), d);
    },
    box(mn, mx),
    f.lip,
  );
}

/** Smooth version of `cut`, for a garment edge that should roll rather than snap. */
export function cutSoft(f: Field, axis: 0 | 1 | 2, at: number, keep: 'below' | 'above', k: number): Field {
  const hard = cut(f, axis, at, keep);
  return field(
    (x, y, z) => {
      const p = axis === 0 ? x : axis === 1 ? y : z;
      const d = keep === 'below' ? p - at : at - p;
      const a = f.sdf(x, y, z);
      const h = clamp(0.5 - (0.5 * (d - a)) / k, 0, 1);
      return a + (d - a) * h + k * h * (1 - h);
    },
    hard.bounds,
    f.lip * 1.35,
  );
}

/**
 * Rotate about an arbitrary axis through a pivot -- the object's own frame.
 *
 * `transform()` applies rotateX then rotateY then rotateZ about the *world*
 * axes, so "spin this about its own barrel" is not expressible with it.  The
 * pistol author had to set yaw to 0 and compose only pitch and roll.
 */
export function rotateAbout(f: Field, axis: Vec3, angle: number, pivot: Vec3 = [0, 0, 0]): Field {
  const L = Math.hypot(axis[0], axis[1], axis[2]) || 1;
  const ux = axis[0] / L, uy = axis[1] / L, uz = axis[2] / L;
  // Inverse rotation (-angle), since the field is sampled in the object's frame.
  const c = Math.cos(-angle), s = Math.sin(-angle), t = 1 - c;
  const m = [
    [t * ux * ux + c, t * ux * uy - s * uz, t * ux * uz + s * uy],
    [t * ux * uy + s * uz, t * uy * uy + c, t * uy * uz - s * ux],
    [t * ux * uz - s * uy, t * uy * uz + s * ux, t * uz * uz + c],
  ];
  const corners: Vec3[] = [];
  const fwd = Math.cos(angle), fs = Math.sin(angle), ft = 1 - fwd;
  const M = [
    [ft * ux * ux + fwd, ft * ux * uy - fs * uz, ft * ux * uz + fs * uy],
    [ft * ux * uy + fs * uz, ft * uy * uy + fwd, ft * uy * uz - fs * ux],
    [ft * ux * uz - fs * uy, ft * uy * uz + fs * ux, ft * uz * uz + fwd],
  ];
  for (const X of [f.bounds.min[0], f.bounds.max[0]]) {
    for (const Y of [f.bounds.min[1], f.bounds.max[1]]) {
      for (const Z of [f.bounds.min[2], f.bounds.max[2]]) {
        const dx = X - pivot[0], dy = Y - pivot[1], dz = Z - pivot[2];
        corners.push([
          pivot[0] + M[0][0] * dx + M[0][1] * dy + M[0][2] * dz,
          pivot[1] + M[1][0] * dx + M[1][1] * dy + M[1][2] * dz,
          pivot[2] + M[2][0] * dx + M[2][1] * dy + M[2][2] * dz,
        ]);
      }
    }
  }
  return field(
    (x, y, z) => {
      const dx = x - pivot[0], dy = y - pivot[1], dz = z - pivot[2];
      return f.sdf(
        pivot[0] + m[0][0] * dx + m[0][1] * dy + m[0][2] * dz,
        pivot[1] + m[1][0] * dx + m[1][1] * dy + m[1][2] * dz,
        pivot[2] + m[2][0] * dx + m[2][1] * dy + m[2][2] * dz,
      );
    },
    boxOf(corners),
    f.lip,
  );
}
