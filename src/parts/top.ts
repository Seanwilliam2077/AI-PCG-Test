/**
 * The black halter crop top: brass X lacing over the chest, a buckled band
 * under the bust, a bare back closed by a strap down the spine.
 *
 * Shape rules the reference forces (ref/views/body_2.png, body_1.png, clay_5.png):
 *
 *   - Halter, not a bandeau.  Classifying the front panel into skin and black
 *     cloth splits the cloth into two straps flanking the throat above
 *     y = 1.3865 -- [-0.044..-0.004] and [+0.040..+0.065] at y = 1.400 -- which
 *     carry on up to the choker.  The top edge is a scoop that climbs.
 *   - The cut edge from the hem to the throat is a **curve**, not a chord.  Its
 *     slope is ~0 below y = 1.30 and 0.75 by y = 1.38; `top.edge` is that curve
 *     as a monotone-cubic table, and `top.collar` continues it into the neck
 *     strap so the neckline has no corner where the two meet.  Round 1 butted a
 *     constant-width slab onto a single plane and both faults showed: a straight
 *     armhole and a right-angle notch at (0.060, 1.375).
 *   - The back is bare.  Nothing of the top is visible from directly behind
 *     above the band, so the opening is bitten out behind a plane that tilts
 *     forward with height.  The *collar* is exempt: the strap really does ring
 *     the neck, and body_5 shows it as a dark band at the nape.
 *   - The neckline is a rounded V that widens as it climbs -- half-width 0.0155
 *     at y = 1.390, 0.022 at 1.400, 0.0275 at 1.410 -- and it is off centre
 *     toward her left, centred at x = +0.017.
 *   - The strap does not stop against the choker, it runs under it.  So the
 *     cloth's offset thins from 9 mm to 5.8 mm over y = 1.400..1.430 and the
 *     top is cut at 1.4365, inside the choker's lowest wrap, with a rounded
 *     edge.  Round 1's flat cut at 1.4315 read as a ledge.
 *
 * The shell is authored as a *solid* -- the body inflated by gap + thickness,
 * then cut -- rather than as a hollow `shell()`.  A 6 mm hollow garment is
 * thinner than the low LOD voxel and meshes into speckle; a solid is thick
 * everywhere, so it survives every LOD, costs half the triangles, and its inner
 * faces are buried inside the body shell where nothing can see them.
 *
 * Everything that has to *read* -- the X, the eyelets, the band, the keeper, the
 * spine strap -- is sized by the mesher, not by the reference.  The reference's
 * lace is a few millimetres of webbing; built at 5 mm it baked into an H -- four
 * grommet blobs in a 2x2 grid with nothing between them -- because a 5 mm ridge
 * is under one low-LOD voxel.  Those pieces are therefore built at roughly 10 mm
 * proud, and their material is *also* painted on with `paint()`, so the colour
 * survives even at the coarsest LOD where the geometry rounds off.
 */
import { Field, Vec3, box, boxExpand } from '../sdf/types.js';
import {
  capsuleOval, cylinder, ellipsoid, field, intersect, offset,
  smoothUnion, subtract, union,
} from '../sdf/ops.js';
import { orientedBox } from '../sdf/curve.js';
import { PartContext, PartModule, Shell, Tagged, nearestMaterial, nums, paint } from './types.js';
import { torsoHalfWidth } from '../spec.js';

/* ------------------------------ small vector helpers ------------------------------ */

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mid = (a: Vec3, b: Vec3): Vec3 => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
const len = (a: Vec3): number => Math.hypot(a[0], a[1], a[2]);
const unit = (a: Vec3): Vec3 => {
  const l = len(a) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};
const cross = (a: Vec3, b: Vec3): Vec3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const along = (p: Vec3, n: Vec3, d: number): Vec3 => [p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d];

/**
 * A monotone cubic (Fritsch-Carlson) through a `[y, value]` table, plus the
 * largest gradient it actually reaches.
 *
 * Every garment edge on this top is a curve read off the sheet at 10 mm
 * intervals, and each one has to be turned back into a plane-like SDF term.
 * Fritsch-Carlson is the right interpolant for that: it never overshoots into a
 * bulge between two keys, and it gives each key a tangent from both neighbours,
 * so the curvature stays bounded and the meshed edge has no shading break at a
 * key.  `maxSlope` is sampled rather than guessed, because it is what the
 * field's Lipschitz normaliser is divided by -- guessing it low punches holes.
 */
function curveY(keys: number[][]): { at: (y: number) => number; maxSlope: number } {
  const n = keys.length;
  const h: number[] = [], d: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    h.push(keys[i + 1][0] - keys[i][0]);
    d.push((keys[i + 1][1] - keys[i][1]) / (keys[i + 1][0] - keys[i][0]));
  }
  const m: number[] = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) {
    if (d[i - 1] * d[i] <= 0) { m[i] = 0; continue; }
    const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1];
    m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]);
  }
  const at = (y: number): number => {
    if (y <= keys[0][0]) return keys[0][1];
    if (y >= keys[n - 1][0]) return keys[n - 1][1];
    let i = 0;
    while (i < n - 2 && y > keys[i + 1][0]) i++;
    const t = (y - keys[i][0]) / h[i], t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * keys[i][1]
      + (t3 - 2 * t2 + t) * h[i] * m[i]
      + (-2 * t3 + 3 * t2) * keys[i + 1][1]
      + (t3 - t2) * h[i] * m[i + 1];
  };
  let maxSlope = 0;
  const y0 = keys[0][0], y1 = keys[n - 1][0], N = 512;
  for (let i = 0; i < N; i++) {
    const a = y0 + ((y1 - y0) * i) / N, b = y0 + ((y1 - y0) * (i + 1)) / N;
    maxSlope = Math.max(maxSlope, Math.abs(at(b) - at(a)) / (b - a));
  }
  return { at, maxSlope };
}

const smootherstep = (u: number) => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));

/**
 * Rounded intersection of two half-spaces, both negative inside.
 *
 * Used for the top of the neck strap, where a plain `max` leaves a horizontal
 * cut face -- a ledge -- and this leaves a rolled edge instead.
 */
function roundedMax2(a: number, b: number, r: number): number {
  const pa = a + r, pb = b + r;
  return Math.min(Math.max(pa, pb), 0) + Math.hypot(Math.max(pa, 0), Math.max(pb, 0)) - r;
}

/** Where does the ray from (x, y, 0) along +z (dir 1) or -z (dir -1) leave `f`?
 *  Used to lay the lacing, the buckle and the spine strap on the garment's own
 *  surface instead of guessing a z. */
function surfaceZ(f: Field, x: number, y: number, dir: 1 | -1): number {
  if (f.sdf(x, y, 0) > 0) return NaN;
  let lo = 0, hi = dir * 0.32;
  for (let i = 0; i < 44; i++) {
    const m = 0.5 * (lo + hi);
    if (f.sdf(x, y, m) < 0) lo = m; else hi = m;
  }
  return 0.5 * (lo + hi);
}

function normalAt(f: Field, p: Vec3): Vec3 {
  const e = 2e-4;
  return unit([
    f.sdf(p[0] + e, p[1], p[2]) - f.sdf(p[0] - e, p[1], p[2]),
    f.sdf(p[0], p[1] + e, p[2]) - f.sdf(p[0], p[1] - e, p[2]),
    f.sdf(p[0], p[1], p[2] + e) - f.sdf(p[0], p[1], p[2] - e),
  ]);
}

/**
 * A flat band lying on a surface: rounded boxes whose local z is the surface
 * normal at each sample.
 *
 * `strap()` in sdf/curve.ts almost does this, but its frame comes from
 * frameAt(), which picks the normal from world-up rather than from the surface
 * the band is lying on -- for a band across a chest that swaps its `width` and
 * `thickness` axes.  Passing the normals in explicitly is clearer than
 * remembering the swap.
 */
function bandOnSurface(pts: Vec3[], normals: Vec3[], width: number, thick: number, over = 0): Field {
  const segs: Field[] = [];
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i];
    const ex = unit(sub(b, a));
    const nAvg = unit(mid(normals[i - 1], normals[i]));
    // Gram-Schmidt: the box frame has to stay orthonormal for orientedBox.
    const d = nAvg[0] * ex[0] + nAvg[1] * ex[1] + nAvg[2] * ex[2];
    const ez = unit([nAvg[0] - d * ex[0], nAvg[1] - d * ex[1], nAvg[2] - d * ex[2]]);
    const ey = cross(ez, ex);
    const half: Vec3 = [len(sub(b, a)) / 2 + over, width / 2, thick / 2];
    segs.push(orientedBox(mid(a, b), ex, ey, ez, half, Math.min(width, thick) * 0.3));
  }
  return union(...segs);
}

/**
 * A flat washer lying on a surface: an eyelet, not a doughnut.
 *
 * A torus of the reference's 4 mm minor radius vanishes into the voxel grid and
 * a torus fat enough to survive stands off the cloth like a bead, so the eyelet
 * is a short cylinder with a hole through it -- 30 mm across, 16 mm bore, and
 * flat, which is what a stamped brass grommet actually is.
 */
function washerOnSurface(c: Vec3, n: Vec3, ro: number, ri: number, thick: number): Field {
  const h = thick / 2;
  return subtract(
    cylinder(along(c, n, -h), along(c, n, h), ro),
    cylinder(along(c, n, -3 * h), along(c, n, 3 * h), ri),
  );
}

/** The bore of an eyelet, as a region to paint through. */
function eyeletBore(c: Vec3, n: Vec3, ri: number, thick: number): Field {
  return cylinder(along(c, n, -2 * thick), along(c, n, 2 * thick), ri);
}

/**
 * A rectangular fitting lying flat on a band: the steel buckle frame and the
 * brass keeper loop beside it.
 */
function fittingOnBand(bandSkin: Field, x: number, y: number, halfW: number, halfH: number,
                       thick: number, frame: number): Field {
  const z = surfaceZ(bandSkin, x, y, 1);
  const p: Vec3 = [x, y, z];
  const n = normalAt(bandSkin, p);
  const ex = unit(cross([0, 1, 0], n));
  const ey = cross(n, ex);
  const c = along(p, n, thick * 0.5);
  const slab = orientedBox(c, ex, ey, n, [halfW, halfH, thick], 0.0025);
  if (frame <= 0) return slab;
  return subtract(slab, orientedBox(
    c, ex, ey, n, [halfW - frame, halfH - frame, thick * 3], 0.0015,
  ));
}

/* ------------------------------ the body under the cloth ------------------------------ */

interface Section { x: number; z: number; cz: number }

/**
 * body.ts's `hermiteColumn`: monotone cubic through one column of the key
 * table.  Same interpolant, so the proxy's profile is body.ts's profile and not
 * a smootherstep approximation of it -- the two differ by up to 4 mm over the
 * yoke, which is half the garment's whole standoff.
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
 * body.ts's `loftEllipse`: an elliptical loft evaluated by radial scaling
 * against a constant `m <= min(X, Z)`, so it never over-estimates distance.
 *
 * This is a copy, not an import -- parts export only their `PartModule` -- and
 * it has to stay a copy, because what the garment needs is not "a torso" but
 * *this* torso: offsetting a differently-built column by 9 mm can easily land
 * inside the real one, and cloth inside the body is cloth you cannot see.
 */
function loftEllipse(y0: number, y1: number, at: (y: number) => Section): Field {
  const n = Math.max(8, Math.round((y1 - y0) / 0.0005));
  let m = Infinity, maxX = 0, maxZ = 0, slope = 0;
  let prev = at(y0);
  for (let i = 0; i <= n; i++) {
    const y = y0 + ((y1 - y0) * i) / n;
    const sec = at(y);
    m = Math.min(m, sec.x, sec.z);
    maxX = Math.max(maxX, sec.x);
    maxZ = Math.max(maxZ, Math.abs(sec.cz) + sec.z);
    if (i > 0) {
      const dy = (y1 - y0) / n;
      slope = Math.max(
        slope,
        Math.max(Math.abs(sec.x - prev.x), Math.abs(sec.z - prev.z)) / dy
          + Math.abs(sec.cz - prev.cz) / dy,
      );
    }
    prev = sec;
  }
  const lip = Math.hypot(1, slope) * 1.1;
  return field(
    (x, y, z) => {
      const yc = y < y0 ? y0 : y > y1 ? y1 : y;
      const sec = at(yc);
      const u = x / sec.x, v = (z - sec.cz) / sec.z;
      const radial = (Math.hypot(u, v) - 1) * m;
      const axial = Math.max(y0 - y, y - y1);
      return Math.min(Math.max(radial, axial), 0)
        + Math.hypot(Math.max(radial, 0), Math.max(axial, 0));
    },
    box([-maxX, y0, -maxZ], [maxX, y1, maxZ]),
    lip,
  );
}

/**
 * The skin the garment hangs on: body.ts's trunk, yoke, bust and trapezius,
 * blended with body.ts's own radii.
 *
 * This mirrors body.ts rather than idealising it, and that is load bearing.  An
 * earlier version built its own correct 45 mm neck column and coned the
 * shoulders into it at y = 1.39; body.ts's neck was a ~90 mm cone at the time,
 * so the whole collar baked *inside* the body and the top read as a flat band
 * across the chest with no halter neck at all.
 *
 * It drifted again between round 1 and round 2: body.ts turned `body.trap` from
 * a neck-to-shoulder capsule into an ellipsoid, and the copy here still tested
 * for the capsule's `x0`, so it quietly dropped the trapezius and hung the
 * strap on a torso 46 mm narrower than the real one at y = 1.42 (the yoke
 * column alone is 0.053 there; body.trap reaches 0.099).  The blocks
 * below therefore read exactly the keys body.ts reads -- `body.yoke`,
 * `body.trap`, `body.bust`, `body.blendBust`, `body.blendTrap` -- and nothing
 * of its own.
 *
 * Arms and legs are left out.  body.ts blends them at 16 mm and 28 mm, both far
 * from the garment's edge once the edge curve has cut it, and including the arms
 * would pull the proxy out into the gap the reference keeps between arm and
 * cloth.
 */
function torsoProxy(ctx: PartContext): Field {
  const s = ctx.spec;
  const L = s.landmarks;
  const w = s.widths;
  const t = nums(s.top);
  const raw = (s as unknown as { body?: Record<string, unknown> }).body ?? {};
  const b = nums(raw);

  const yokeY0 = Number.isFinite(b.yokeY0) ? b.yokeY0 : L.shoulder;
  const yokeKeys = (raw.yoke as number[][] | undefined) ?? [
    [L.shoulder, w.chestHalfW, w.chestHalfD * 0.92, s.pose.spineLean],
    [L.neckBase, w.neckR * 1.2, w.neckR * 1.33, s.pose.spineLean * 0.7],
  ];
  const top0 = torsoHalfWidth(yokeY0, s);
  const head: number[] = [
    yokeY0, top0.x, top0.z,
    s.pose.spineLean * ((yokeY0 - L.crotch) / Math.max(1e-6, L.neckBase - L.crotch)),
  ];
  const keys = [head, ...yokeKeys];
  const fx = hermiteColumn(keys, 1);
  const fz = hermiteColumn(keys, 2);
  const fc = hermiteColumn(keys, 3);
  const at = (y: number): Section => {
    if (y <= yokeY0) {
      const p = torsoHalfWidth(y, s);
      return {
        x: p.x, z: p.z,
        cz: s.pose.spineLean * ((y - L.crotch) / Math.max(1e-6, L.neckBase - L.crotch)),
      };
    }
    return { x: fx(y), z: fz(y), cz: fc(y) };
  };

  // Everything more than 140 mm below the hem is out of frame.  Starting the
  // loft there rather than at the crotch keeps the bounds -- and so the mesher's
  // block scan -- confined to the ribcage.
  const trunk = union(
    loftEllipse(Math.max(L.crotch - 0.02, t.hemY - 0.14), yokeY0 + 0.010, at),
    loftEllipse(yokeY0 - 0.010, keys[keys.length - 1][0], at),
  );

  const bu = nums(raw.bust);
  let core = trunk;
  if (Number.isFinite(bu.rx)) {
    const by = L.bust - bu.drop, bx = w.bustHalfW * bu.x, bz = w.bustHalfD * bu.z;
    const br: Vec3 = [bu.rx, bu.ry, bu.rz];
    core = smoothUnion(
      Number.isFinite(b.blendBust) ? b.blendBust : 0.036,
      trunk, ellipsoid([bx, by, bz], br), ellipsoid([-bx, by, bz], br),
    );
  }

  const tr = nums(raw.trap);
  if (!Number.isFinite(tr.rx)) return core;
  const trap = (side: 1 | -1) =>
    ellipsoid([side * tr.cx, tr.cy, tr.cz], [tr.rx, tr.ry, tr.rz]);
  return smoothUnion(
    Number.isFinite(b.blendTrap) ? b.blendTrap : 0.026,
    core, trap(1), trap(-1),
  );
}

/* ------------------------------ the part ------------------------------ */

export const topPart: PartModule = {
  id: 'top',
  build(ctx: PartContext): Shell[] {
    const s = ctx.spec;
    const { mat } = ctx;
    const t = nums(s.top);
    const rawTop = s.top as unknown as Record<string, unknown>;

    const proxy = torsoProxy(ctx);
    const outer = t.gap + t.thickness;

    /**
     * The cloth's standoff, thinning over the throat.
     *
     * 9 mm everywhere the garment lies on the ribs -- it has to clear the body
     * shell, which bakes on a 15.8 mm voxel and can wander several millimetres
     * off its own profile -- but only 5.8 mm above y = 1.430, so that the neck
     * strap's outer radius there (0.0430 + 0.0058 = 0.0488) passes *under* the
     * choker's lowest wrap, whose outer radius is 0.0499.  That is what turns
     * round 1's ledge into a strap that disappears beneath the leather.
     */
    const offAt = (y: number) =>
      outer - t.neckThinBy * smootherstep((y - t.neckThinY0) / Math.max(1e-6, t.neckThinY1 - t.neckThinY0));
    const offSlope = (1.5 * t.neckThinBy) / Math.max(1e-6, t.neckThinY1 - t.neckThinY0);
    const skin = field(
      (x, y, z) => proxy.sdf(x, y, z) - offAt(y),
      boxExpand(proxy.bounds, outer),
      proxy.lip + offSlope,
    );

    const hull = box(
      [-0.17, t.hemY - 0.03, -0.15],
      [0.17, t.collarTopY + 0.03, 0.18],
    );

    /* ---- where the cloth is ---- */

    // The bib's cut edge: |x| <= edge(y) + depth*(z - zc).  `edge` is a curve,
    // because the reference's is: read off the front panel its slope is ~0 up
    // to y = 1.30 and 0.75 by 1.38, and round 1's single plane -- one slope for
    // the whole run -- both cut the armhole straight and left it 8..15 mm wide
    // across the ribs.
    //
    // `depth` is *positive*, i.e. coverage grows as z grows: this garment is
    // widest at the front and narrows as it goes round the ribs.  With the sign
    // that way the edge closes on its own and needs no constant-z box to keep
    // it off the back -- that box's front face used to show as a hard vertical
    // line down the flank in every three-quarter view.
    const edge = curveY(rawTop.edge as number[][]);
    const nArm = Math.hypot(1, edge.maxSlope, t.armEdgeDepth);
    const coverage = field(
      (x, y, z) => Math.max(
        t.hemY - y,
        y - t.bibTopY,
        (Math.abs(x) - edge.at(y) - t.armEdgeDepth * (z - t.armEdgeZc)) / nArm,
      ),
      hull,
      1,
    );

    /* ---- the bare back ---- */

    // What is left of the back below the collar is bitten out behind a plane
    // that tilts forward as it rises: z < backZ0 + backSlope*(y - backY0).  It
    // is 25 mm deep at the band and has swung past the widest point of the ribs
    // by y = 1.34, which is what body_5 shows -- bare skin from the spine right
    // out to the silhouette above the band, and no cloth visible from behind.
    const nBack = Math.hypot(1, t.backSlope);
    const backLower = field(
      (_x, y, z) => Math.max(
        (z - (t.backZ0 + t.backSlope * (y - t.backY0))) / nBack,
        t.backLowY - y,
      ),
      box([-0.17, t.backLowY, -0.15], [0.17, t.collarTopY + 0.03, 0.10]),
      1,
    );

    /* ---- the V at the throat ---- */

    // A wedge through the front of the collar, widening as it climbs and
    // rounded where it bottoms out.  Round 1 used a constant-width slot; the
    // reference's opening is 0.0155 half-wide at y = 1.390 and 0.0275 at 1.410,
    // and it is centred at x = +0.017, not on the spine.  It runs off the top of
    // the garment so the opening reads as continuous with the choker above it.
    const nkFlare = Math.hypot(1, t.neckOpenFlare);
    const nkZ1 = t.neckOpenZ0 + 0.32;
    const neckHole = field(
      (x, y, z) => {
        const w = Math.min(t.neckOpenW0 + t.neckOpenFlare * (y - t.neckOpenY), t.neckOpenWMax);
        const side = (Math.abs(x - t.neckOpenX) - w) / nkFlare;
        const bottom = t.neckOpenY - y;
        return Math.max(
          roundedMax2(side, bottom, t.neckOpenRound),
          Math.max(t.neckOpenZ0 - z, z - nkZ1),
          y - t.neckOpenTopY,
        );
      },
      box(
        [t.neckOpenX - t.neckOpenWMax, t.neckOpenY, t.neckOpenZ0],
        [t.neckOpenX + t.neckOpenWMax, t.neckOpenTopY, nkZ1],
      ),
      1,
    );

    const bib = subtract(intersect(skin, coverage), union(backLower, neckHole));

    /* ---- the halter's neck strap ---- */

    // The strap that makes this a halter rather than a bandeau, and the one
    // piece the bib's cut cannot produce: the reference's strap is *outboard*
    // of the throat at y = 1.42 (cloth at +0.048..+0.067) while the bib has
    // narrowed past that by then, so it is a band round the neck, not a
    // continuation of the panel.  Its half-width is the same curve carried on,
    // so the two share an edge with no corner between them; round 1's constant
    // 0.060 slab left a right-angle notch at (0.060, 1.375).
    //
    // The region is a slab in x, not a cylinder about the neck.  A cylinder is
    // the tempting shape -- it is a collar, after all -- but its wall runs
    // *through* the solid, so the surface it leaves is the wall itself, buried:
    // at radius 0.060 it cut the front of the neck off at z = 0.041 where the
    // body is already at 0.069, and the whole collar baked inside the body.  A
    // slab only ever cuts sideways, so what survives is the body's own surface.
    const colw = curveY(rawTop.collar as number[][]);
    const nCol = Math.hypot(1, colw.maxSlope);
    // ...and it is not centred on the spine, because the reference's is not:
    // the cloth spans -0.051..+0.062 at y = 1.390 and -0.042..+0.066 at 1.410,
    // i.e. a span centred at x = +0.006..+0.012 with the opening at +0.017
    // inside it, which is what makes her right strap 31 mm wide and her left
    // 22 mm.  Centring the slab on x = 0 while the opening stays off centre
    // leaves the left strap a 5 mm spike.
    const collarRegion = field(
      (x, y, _z) => Math.max(
        t.collarY0 - y,
        roundedMax2((Math.abs(x - t.collarX) - colw.at(y)) / nCol, y - t.collarTopY, t.collarRound),
      ),
      box(
        [t.collarX - 0.075, t.collarY0, -0.15],
        [t.collarX + 0.075, t.collarTopY + 0.002, 0.18],
      ),
      1,
    );
    const collar = subtract(intersect(skin, collarRegion), neckHole);

    const cloth = union(bib, collar);

    /* ---- the strap down the spine ---- */

    // The halter has to close somewhere: the neck strap meets at the nape and
    // runs down the spine into the band.  Without it the band is a hoop with two
    // free ends and the back view shows a bar floating on bare skin.
    const spineSkin = field(
      (x, y, z) => proxy.sdf(x, y, z) - (offAt(y) + t.spineProud),
      boxExpand(proxy.bounds, outer + t.spineProud),
      proxy.lip + offSlope,
    );
    const spinePts: Vec3[] = [];
    const spineNrm: Vec3[] = [];
    const nSpine = 14;
    for (let i = 0; i < nSpine; i++) {
      const y = t.spineTopY + ((t.spineBotY - t.spineTopY) * i) / (nSpine - 1);
      const z = surfaceZ(spineSkin, 0, y, -1);
      if (Number.isNaN(z)) continue;
      const p: Vec3 = [0, y, z];
      spinePts.push(p);
      spineNrm.push(normalAt(spineSkin, p));
    }
    const spine = bandOnSurface(spinePts, spineNrm, t.spineWidth, t.spineThick, 0.002);

    /* ---- the band that finishes the hem ---- */

    const bandHalf = t.underBandWidth / 2;
    const bandRegion = field(
      (_x, y, _z) => Math.max(y - (t.underBandY + bandHalf), (t.underBandY - bandHalf) - y),
      box([-0.17, t.underBandY - bandHalf, -0.15], [0.17, t.underBandY + bandHalf, 0.18]),
      1,
    );
    const bandSkin = offset(proxy, outer + t.underBandProud);
    const band = intersect(bandSkin, bandRegion);

    // Two fittings on the band, each sitting on the band's own surface.  The
    // steel one on her left is a frame, not a slab: the reference's keeper is an
    // open rectangle with the band's leather showing through, and at 3 mm voxels
    // a 4.5 mm bar resolves, so it is worth cutting the middle out.  The brass
    // one on her right -- 9 mm on the sheet, built at 12 mm to clear the voxel --
    // is solid, which is what a stamped keeper loop looks like at this size.
    const buckle = fittingOnBand(
      bandSkin, t.buckleX, t.underBandY,
      t.buckleHalfW, t.buckleHalfH, t.buckleThick, t.buckleFrame,
    );
    const keeper = fittingOnBand(
      bandSkin, t.keeperX, t.underBandY,
      t.keeperHalfW, t.keeperHalfH, t.keeperThick, 0,
    );

    /* ---- the brass X ---- */

    // Eyelet centres, measured off the brass mask in body_2.png.  The straps run
    // corner to corner -- topLeft->botRight and topRight->botLeft -- so the pair
    // list below is a cross, not a ladder.
    const yTop = t.laceY + t.laceHalfH, yBot = t.laceY - t.laceHalfH;
    const corners: Vec3[] = [
      [-t.laceHalfW, yTop, 0], [t.laceHalfW, yTop, 0],
      [-t.laceHalfW, yBot, 0], [t.laceHalfW, yBot, 0],
    ];

    // The straps ride into the cloth so the union fuses instead of just
    // touching, which would leave a pinched, non-manifold seam, and stand
    // laceProud out of it so the mesher can still see them.
    const laceSkin = offset(proxy, outer + t.laceProud - t.laceThick / 2);
    const ringSkin = offset(proxy, outer + t.ringProud - t.ringThick / 2);
    const onSurface = (f: Field, x: number, y: number): Vec3 => [x, y, surfaceZ(f, x, y, 1)];

    const straps: Field[] = [];
    for (const [ai, bi] of [[0, 3], [1, 2]] as [number, number][]) {
      const a = corners[ai], b = corners[bi];
      const pts: Vec3[] = [];
      const nrm: Vec3[] = [];
      const N = 5;
      // Stopping the webbing just short of the eyelet centres is what lets the
      // bores read: on the sheet the pink of the skin shows through the outboard
      // half of each ring while the strap fills the inboard half.
      for (let i = 0; i < N; i++) {
        const u = t.laceEndInset + (1 - 2 * t.laceEndInset) * (i / (N - 1));
        const p = onSurface(laceSkin, a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u);
        pts.push(p);
        nrm.push(normalAt(laceSkin, p));
      }
      straps.push(bandOnSurface(pts, nrm, t.laceWidth, t.laceThick, t.laceOver));
    }
    const laceStraps = union(...straps);

    const eyelets = corners.map((c) => {
      const p = onSurface(ringSkin, c[0], c[1]);
      return { p, n: normalAt(ringSkin, p) };
    });
    const rings = union(...eyelets.map((e) =>
      washerOnSurface(e.p, e.n, t.ringOuter, t.ringInner, t.ringThick)));
    const bores = union(...eyelets.map((e) =>
      eyeletBore(e.p, e.n, t.ringInner - 0.0012, t.ringThick)));

    /* ---- assemble ---- */

    const shellField = union(cloth, spine, band, buckle, keeper, laceStraps, rings);

    const tags: Tagged[] = [
      { field: cloth, mat: mat.cloth },
      { field: spine, mat: mat.cloth },
      { field: band, mat: mat.leather },
      { field: buckle, mat: mat.steel },
      { field: keeper, mat: mat.brass },
      { field: laceStraps, mat: mat.canvas },
      { field: rings, mat: mat.brass },
    ];

    // Painted as well as built.  nearestMaterial alone loses the eyelets at the
    // low LOD, where surface nets rounds a 30 mm washer on an 7 mm grid into a
    // lump and the nearest tagged field over most of that lump is the cloth
    // under it.  Painting the same fields on top keeps the colour right at every
    // LOD; the reference shows skin through the eyelet bores, so those are
    // painted too, and the lace is painted last because it passes over the rings.
    let material = nearestMaterial(tags, mat.cloth);
    material = paint(material, rings, mat.brass, 0.0025);
    material = paint(material, keeper, mat.brass, 0.0025);
    material = paint(material, buckle, mat.steel, 0.0025);
    material = paint(material, bores, mat.skin, 0.0);
    material = paint(material, laceStraps, mat.canvas, 0.0018);

    return [{
      name: 'top',
      field: shellField,
      material,
      voxelScale: t.voxelScale,
    }];
  },
};
