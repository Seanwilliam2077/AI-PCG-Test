/**
 * SDF primitives, boolean operators and transforms.
 *
 * Every constructor returns a `Field`, so bounds and the Lipschitz bound
 * propagate on their own and the mesher can skip empty blocks without the
 * caller tracking anything by hand.
 */
import { Box, Field, Sdf, Vec3, box, boxExpand, boxOf, boxUnion } from './types.js';

export const clamp = (v: number, a: number, b: number) => (v < a ? a : v > b ? b : v);
export const mix = (a: number, b: number, t: number) => a + (b - a) * t;
export const smoothstep = (e0: number, e1: number, x: number) => {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
};

export function field(sdf: Sdf, bounds: Box, lip = 1): Field {
  return { sdf, bounds, lip };
}

/* ---------------- primitives ---------------- */

export function sphere(c: Vec3, r: number): Field {
  return field(
    (x, y, z) => Math.hypot(x - c[0], y - c[1], z - c[2]) - r,
    boxExpand(box(c, c), r),
  );
}

export function ellipsoid(c: Vec3, r: Vec3): Field {
  // The usual scaled bound is not exact; it under-estimates by at most
  // max(r)/min(r), which is what `lip` records.
  const lo = Math.max(1e-6, Math.min(r[0], r[1], r[2]));
  const hi = Math.max(r[0], r[1], r[2]);
  return field(
    (x, y, z) => {
      const px = (x - c[0]) / r[0], py = (y - c[1]) / r[1], pz = (z - c[2]) / r[2];
      const k0 = Math.hypot(px, py, pz);
      if (k0 < 1e-9) return -lo;
      const k1 = Math.hypot(px / r[0], py / r[1], pz / r[2]);
      return (k0 * (k0 - 1)) / k1;
    },
    boxExpand(box(c, c), hi),
    hi / lo,
  );
}

export function roundBox(c: Vec3, h: Vec3, r = 0): Field {
  return field(
    (x, y, z) => {
      const qx = Math.abs(x - c[0]) - h[0] + r;
      const qy = Math.abs(y - c[1]) - h[1] + r;
      const qz = Math.abs(z - c[2]) - h[2] + r;
      const ox = Math.max(qx, 0), oy = Math.max(qy, 0), oz = Math.max(qz, 0);
      return Math.hypot(ox, oy, oz) + Math.min(Math.max(qx, qy, qz), 0) - r;
    },
    box(
      [c[0] - h[0], c[1] - h[1], c[2] - h[2]],
      [c[0] + h[0], c[1] + h[1], c[2] + h[2]],
    ),
  );
}

/** Capsule with a different radius at each end (a round cone). */
export function capsule(a: Vec3, b: Vec3, ra: number, rb = ra): Field {
  const bax = b[0] - a[0], bay = b[1] - a[1], baz = b[2] - a[2];
  const l2 = bax * bax + bay * bay + baz * baz || 1e-12;
  return field(
    (x, y, z) => {
      const px = x - a[0], py = y - a[1], pz = z - a[2];
      const h = clamp((px * bax + py * bay + pz * baz) / l2, 0, 1);
      const dx = px - bax * h, dy = py - bay * h, dz = pz - baz * h;
      return Math.hypot(dx, dy, dz) - (ra + (rb - ra) * h);
    },
    boxUnion(boxExpand(box(a, a), ra), boxExpand(box(b, b), rb)),
  );
}

/** Capsule whose cross-section is an ellipse -- limbs are not round. */
export function capsuleOval(a: Vec3, b: Vec3, ra: number, rb: number, squashZ = 1, squashX = 1): Field {
  const bax = b[0] - a[0], bay = b[1] - a[1], baz = b[2] - a[2];
  const l2 = bax * bax + bay * bay + baz * baz || 1e-12;
  const lo = Math.min(1, squashZ, squashX);
  return field(
    (x, y, z) => {
      const px = x - a[0], py = y - a[1], pz = z - a[2];
      const h = clamp((px * bax + py * bay + pz * baz) / l2, 0, 1);
      const dx = (px - bax * h) / squashX, dy = py - bay * h, dz = (pz - baz * h) / squashZ;
      return (Math.hypot(dx, dy, dz) - (ra + (rb - ra) * h)) * lo;
    },
    boxUnion(
      boxExpand(box(a, a), ra * Math.max(1, squashZ, squashX)),
      boxExpand(box(b, b), rb * Math.max(1, squashZ, squashX)),
    ),
    Math.max(1, squashZ, squashX) / lo,
  );
}

export function cylinder(a: Vec3, b: Vec3, r: number): Field {
  const bax = b[0] - a[0], bay = b[1] - a[1], baz = b[2] - a[2];
  const baba = bax * bax + bay * bay + baz * baz || 1e-12;
  const len = Math.sqrt(baba);
  return field(
    (x, y, z) => {
      const px = x - a[0], py = y - a[1], pz = z - a[2];
      const t = (px * bax + py * bay + pz * baz) / baba;
      const cx = px - bax * t, cy = py - bay * t, cz = pz - baz * t;
      const dRadial = Math.hypot(cx, cy, cz) - r;
      const dAxial = (Math.abs(t - 0.5) - 0.5) * len;
      return Math.min(Math.max(dRadial, dAxial), 0) + Math.hypot(Math.max(dRadial, 0), Math.max(dAxial, 0));
    },
    boxExpand(boxUnion(box(a, a), box(b, b)), r),
  );
}

export function torus(c: Vec3, major: number, minor: number, axis: 0 | 1 | 2 = 1): Field {
  return field(
    (x, y, z) => {
      const p = [x - c[0], y - c[1], z - c[2]];
      const u = p[(axis + 1) % 3], v = p[(axis + 2) % 3], w = p[axis];
      return Math.hypot(Math.hypot(u, v) - major, w) - minor;
    },
    boxExpand(box(c, c), major + minor),
  );
}

export function halfSpace(n: Vec3, d: number, bounds: Box): Field {
  const len = Math.hypot(n[0], n[1], n[2]) || 1;
  const nx = n[0] / len, ny = n[1] / len, nz = n[2] / len;
  return field((x, y, z) => x * nx + y * ny + z * nz - d, bounds);
}

/* ---------------- booleans ---------------- */

const unionBounds = (parts: Field[]): Box =>
  parts.slice(1).reduce((acc, f) => boxUnion(acc, f.bounds), parts[0].bounds);

export function union(...fs: (Field | null | undefined)[]): Field {
  const parts = fs.filter(Boolean) as Field[];
  if (parts.length === 1) return parts[0];
  return field(
    (x, y, z) => {
      let m = Infinity;
      for (let i = 0; i < parts.length; i++) {
        const v = parts[i].sdf(x, y, z);
        if (v < m) m = v;
      }
      return m;
    },
    unionBounds(parts),
    Math.max(...parts.map((f) => f.lip)),
  );
}

/** Polynomial smooth minimum; `k` is the blend radius in metres. */
export function smoothUnion(k: number, ...fs: (Field | null | undefined)[]): Field {
  const parts = fs.filter(Boolean) as Field[];
  if (parts.length === 1) return parts[0];
  return field(
    (x, y, z) => {
      let m = parts[0].sdf(x, y, z);
      for (let i = 1; i < parts.length; i++) {
        const v = parts[i].sdf(x, y, z);
        const h = clamp(0.5 + (0.5 * (m - v)) / k, 0, 1);
        m = mix(m, v, h) - k * h * (1 - h);
      }
      return m;
    },
    boxExpand(unionBounds(parts), k),
    Math.max(...parts.map((f) => f.lip)) * 1.35,
  );
}

export function subtract(a: Field, b: Field): Field {
  return field(
    (x, y, z) => Math.max(a.sdf(x, y, z), -b.sdf(x, y, z)),
    a.bounds,
    Math.max(a.lip, b.lip),
  );
}

export function smoothSubtract(k: number, a: Field, b: Field): Field {
  // -smin(-A, B, k), expanded.  As k -> 0 this must collapse to max(A, -B):
  // h -> 0 when A + B > 0 and the result is A, h -> 1 otherwise and it is -B.
  return field(
    (x, y, z) => {
      const A = a.sdf(x, y, z), B = b.sdf(x, y, z);
      const h = clamp(0.5 - (0.5 * (A + B)) / k, 0, 1);
      return mix(A, -B, h) + k * h * (1 - h);
    },
    boxExpand(a.bounds, k),
    Math.max(a.lip, b.lip) * 1.35,
  );
}

export function intersect(a: Field, b: Field): Field {
  const mn: Vec3 = [
    Math.max(a.bounds.min[0], b.bounds.min[0]),
    Math.max(a.bounds.min[1], b.bounds.min[1]),
    Math.max(a.bounds.min[2], b.bounds.min[2]),
  ];
  const mx: Vec3 = [
    Math.min(a.bounds.max[0], b.bounds.max[0]),
    Math.min(a.bounds.max[1], b.bounds.max[1]),
    Math.min(a.bounds.max[2], b.bounds.max[2]),
  ];
  return field((x, y, z) => Math.max(a.sdf(x, y, z), b.sdf(x, y, z)), box(mn, mx), Math.max(a.lip, b.lip));
}

export function smoothIntersect(k: number, a: Field, b: Field): Field {
  const inner = intersect(a, b);
  return field(
    (x, y, z) => {
      const d1 = a.sdf(x, y, z), d2 = b.sdf(x, y, z);
      const h = clamp(0.5 - (0.5 * (d2 - d1)) / k, 0, 1);
      return mix(d2, d1, h) + k * h * (1 - h);
    },
    boxExpand(inner.bounds, k),
    Math.max(a.lip, b.lip) * 1.35,
  );
}

/** Hollow a solid into a shell of thickness 2t -- how the clothing is cut. */
export function shell(a: Field, t: number): Field {
  return field((x, y, z) => Math.abs(a.sdf(x, y, z)) - t, boxExpand(a.bounds, t), a.lip);
}

export function offset(a: Field, r: number): Field {
  return field((x, y, z) => a.sdf(x, y, z) - r, boxExpand(a.bounds, r), a.lip);
}

/* ---------------- transforms ---------------- */

export function translate(a: Field, t: Vec3): Field {
  return field(
    (x, y, z) => a.sdf(x - t[0], y - t[1], z - t[2]),
    box(
      [a.bounds.min[0] + t[0], a.bounds.min[1] + t[1], a.bounds.min[2] + t[2]],
      [a.bounds.max[0] + t[0], a.bounds.max[1] + t[1], a.bounds.max[2] + t[2]],
    ),
    a.lip,
  );
}

const mappedBounds = (b: Box, m: (p: Vec3) => Vec3): Box => {
  const pts: Vec3[] = [];
  for (const X of [b.min[0], b.max[0]]) {
    for (const Y of [b.min[1], b.max[1]]) {
      for (const Z of [b.min[2], b.max[2]]) pts.push(m([X, Y, Z]));
    }
  }
  return boxOf(pts);
};

export function rotateY(a: Field, ang: number): Field {
  const c = Math.cos(ang), s = Math.sin(ang);
  return field(
    (x, y, z) => a.sdf(c * x - s * z, y, s * x + c * z),
    mappedBounds(a.bounds, ([x, y, z]) => [c * x + s * z, y, -s * x + c * z]),
    a.lip,
  );
}

export function rotateX(a: Field, ang: number): Field {
  const c = Math.cos(ang), s = Math.sin(ang);
  return field(
    (x, y, z) => a.sdf(x, c * y + s * z, -s * y + c * z),
    mappedBounds(a.bounds, ([x, y, z]) => [x, c * y - s * z, s * y + c * z]),
    a.lip,
  );
}

export function rotateZ(a: Field, ang: number): Field {
  const c = Math.cos(ang), s = Math.sin(ang);
  return field(
    (x, y, z) => a.sdf(c * x + s * y, -s * x + c * y, z),
    mappedBounds(a.bounds, ([x, y, z]) => [c * x - s * y, s * x + c * y, z]),
    a.lip,
  );
}

export function scale(a: Field, s: Vec3): Field {
  const mn = Math.min(s[0], s[1], s[2]), mx = Math.max(s[0], s[1], s[2]);
  return field(
    (x, y, z) => a.sdf(x / s[0], y / s[1], z / s[2]) * mn,
    box(
      [a.bounds.min[0] * s[0], a.bounds.min[1] * s[1], a.bounds.min[2] * s[2]],
      [a.bounds.max[0] * s[0], a.bounds.max[1] * s[1], a.bounds.max[2] * s[2]],
    ),
    a.lip * (mx / mn),
  );
}

/** Mirror across x = 0, so a limb authored once appears on both sides. */
export function mirrorX(a: Field): Field {
  const b = a.bounds;
  const ex = Math.max(Math.abs(b.min[0]), Math.abs(b.max[0]));
  return field(
    (x, y, z) => a.sdf(Math.abs(x), y, z),
    box([-ex, b.min[1], b.min[2]], [ex, b.max[1], b.max[2]]),
    a.lip,
  );
}

export function transform(a: Field, opts: { rotate?: Vec3; translate?: Vec3; scale?: Vec3 }): Field {
  let f = a;
  if (opts.scale) f = scale(f, opts.scale);
  if (opts.rotate) {
    if (opts.rotate[0]) f = rotateX(f, opts.rotate[0]);
    if (opts.rotate[1]) f = rotateY(f, opts.rotate[1]);
    if (opts.rotate[2]) f = rotateZ(f, opts.rotate[2]);
  }
  if (opts.translate) f = translate(f, opts.translate);
  return f;
}

/**
 * Displace a field by a function of position -- ribs on a braid, folds in
 * cloth.  `amp` is added to the Lipschitz bound because a displacement of
 * amplitude a over wavelength w steepens the field by roughly 2*pi*a/w.
 */
export function displace(a: Field, amp: number, wavelength: number, f: (x: number, y: number, z: number) => number): Field {
  return field(
    (x, y, z) => a.sdf(x, y, z) + amp * f(x, y, z),
    boxExpand(a.bounds, Math.abs(amp)),
    a.lip + (2 * Math.PI * Math.abs(amp)) / Math.max(1e-4, wavelength),
  );
}
