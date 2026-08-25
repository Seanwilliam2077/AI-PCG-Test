/**
 * The hair: the swept coif, the big forward crest-lock, the face-framing locks,
 * and the two ankle-length braids.
 *
 * This is the silhouette people recognise before they recognise the face, so
 * every number here is measured off the turnaround rather than invented.  The
 * measurement frame matters: panel silhouettes are only comparable once the
 * body midline is found, because the braids drag the alpha-bbox centre 15 mm
 * off it.  `tools/grid.py` / `tools/headcrop.py` grid on the bbox centre, so
 * every x below has that 15 mm removed (found by mirror-fitting the torso band
 * of clay_2 and clay_5 against itself: bias -0.0148 m front, +0.0143 m back,
 * i.e. the same real asymmetry seen from either side).  Depths come from the
 * side panels anchored on the nose tip, which the head part puts at z +0.049.
 *
 *   ref/views/clay_2.png (front) + clay_5.png (back), about the true midline:
 *     y     her right (-x)   her left (+x)      the two panels agree to 3 mm
 *     1.71    -0.065           -0.050           at every height, which is what
 *     1.68    -0.076           +0.061           makes this the trustworthy
 *     1.65    -0.100           +0.084           pair of views.
 *     1.63    -0.120           +0.092
 *     1.61    -0.128           +0.089
 *     1.58    -0.121           +0.093
 *     1.54    -0.108           +0.084
 *     1.50    -0.096           +0.069
 *     1.46    -0.068           +0.056
 *   The head under it is only +-0.065 wide, so the mass is 60 mm thick on her
 *   RIGHT and 28 mm on her left: one big forward-swept lock, not a helmet.
 *
 *   ref/views/body_4.png (her right side).  The same lock carries forward to
 *   z +0.049 -- level with the nose tip -- from y 1.60 down to 1.48, and its
 *   z-thickness there is 0.059.  ref/views/body_0.png (her left side) has the
 *   hairline receding to z -0.005 by y 1.58: the face is bare on that side.
 *
 *   ref/views/clay_5.png (back).  The plaits are formed at the CROWN, y 1.695,
 *   and TOUCH each other from the nape down to the hip: at y 1.30 each is
 *   0.046 across, centres 0.046 apart, zero gap.  They taper steadily -- 0.055
 *   at the nape, 0.046 at the shoulder blades, 0.037 by the calf -- then splay
 *   to +-0.075 at the boot and fray into tassels reaching y 0.07.
 *
 * Two shells: the mass (fine voxel, it carries the part and the crest edges)
 * and the braids (coarse voxel, they are 1.5 m of rope each and would eat the
 * whole budget at the mass's resolution).  The braid roots start *inside* the
 * mass, under a gather bulge, so the two read as one head of hair.
 *
 * ROUND 2.  Two measured defects, both fixed, both written up with their
 * numbers in docs/MEASUREMENTS.md under "Hair, round 2":
 *
 *  1. `braid_area_frac` at yaw 90 / 270 was 0.127 against a reference
 *     0.044 / 0.034.  It was NOT thickness -- run by run the render's plait
 *     was 0.034-0.060 against the reference's 0.034-0.049.  It was standoff:
 *     the plait hung 7-58 mm clear of the back at almost every height from
 *     y 0.3 to 1.5, so it was its own thin silhouette run and `debraid`
 *     discarded all of it, while clay_0 is ONE run from y 0.70 to the crown.
 *     The fix is the z column of BRAID_ROWS, set from the assembled body's
 *     own rearmost surface (probed with out/hair_backz.ts), plus two nape
 *     gather lobes for the hollow behind the neck the rope cannot reach.
 *     Now 0.043.
 *  2. The head-and-hair band was 9-18 % under-built.  Anchored on the nose
 *     rather than on the figure (see below), the whole deficit was DEPTH at
 *     y 1.64-1.70: the crest overhang in front of the brow and the plait's
 *     first 75 mm behind the crown.  Band area at yaw 90 is now 508 cm^2
 *     against the reference's 504, and 471 against 465 in the front view.
 *
 * ROUND 3.  The crest was rebuilt from a pair of fattened cone chains into a
 * loft of SOLVED elliptical sections, and that is the whole of this round.
 *
 * The panels only measure four directions -- yaw 0 and 180 share the X axis,
 * yaw 90 and 270 share Z, and the three-quarter views take the diagonals -- so
 * a horizontal slice of the head is described by four support widths, one more
 * than an ellipse needs.  The identity that check gives, w45^2 + w315^2 =
 * wX^2 + wZ^2, holds on the clay panels to 1 % at y 1.64 and 1.66 and 2 % at
 * 1.68, so the crown IS an ellipse per height and its axes and heading can be
 * solved rather than sculpted.  See `crownSection` and `CROWN_ROWS`.
 *
 * Measured off the assembled render at 1000 px/m, mean |width error| over the
 * four axes at y 1.60 .. 1.70 fell from 14.7 mm to 4.4 mm, and the two errors
 * round 2 called a trade it could not win both fell at once: the front view
 * was 12.9 mm narrow at y 1.66 and is now 0.9 mm wide, while yaw 315 was
 * 64.4 mm WIDE at y 1.70 and is now 11.6 mm.  They were never a trade -- they
 * were one error, a crown too fat across its own blade and too short along it.
 *
 * Three things had to be fixed for the solved sections to survive to the
 * surface, and each is worth more than the table:
 *
 *  - `ellipsoid` reports `lip` = max(r)/min(r), and a crown section is 0.11 m
 *    long by 0.012 m tall, so its field can under-report distance eightfold.
 *    A chain of `smoothUnion(k)` over ten of those blends on reported distance
 *    and pushes the surface out by far more than k: the loft ended at y 1.7195
 *    and the finished mass ran to 1.734 with a 0.14 m-deep cap at y 1.72 where
 *    the reference has a 0.01 m point.  `crownBlade` unions them HARD instead,
 *    at 8 mm spacing, which has no such term.
 *  - Every piece unioned onto the crown has to sit INSIDE the solved ellipse
 *    or it is measured as crown.  The fringe's two locks on her left ran
 *    forward to z +0.054 at x +0.072, which is 37 mm outside the ellipse
 *    across the blade and so 26 mm of yaw-315 width; the axis-square cap
 *    sections carried material at (x +0.07, z +0.03) that a blade tilted 42
 *    degrees does not, worth 10 mm at every height from 1.61 to 1.67; and the
 *    plait standing 25 mm proud of the crown was 24 mm of yaw-315 width at
 *    y 1.70.  The fringe is now clipped to the blade, the cap stops at
 *    y 1.6050 and the plait root came down to y 1.686.
 *  - The reference's crown is a stack of layered blades, and the layers run
 *    ALONG the blade rather than up it, so the grooves are furrows at a fixed
 *    height and a fixed offset across.  Sinking them to 0.8 of the half
 *    thickness serrated the top; they ride on the surface now.
 *
 * What the crest is: a blade about 0.23 m long from y 1.60 to 1.66, thinning
 * from 0.19 m across to 0.04 m by y 1.71 and swinging its heading from 44
 * degrees off straight-ahead to 21 -- a wave rising off the crown and raking
 * back over it, which is what `head_1` and `head_2` show.
 *
 * NOT fixable from here: in the reference the nose sits about 20 mm IN FRONT
 * of the chest's front surface (clay_0, y 1.556 vs y 1.35), while in the
 * assembled model it sits 78 mm behind it (head front z +0.058, top front
 * z +0.136 at y 1.35).  So the head is roughly 0.06-0.10 m too far back
 * relative to the torso, and any side-view head-band metric that registers on
 * the whole silhouette will read that as "the hair is missing its forward
 * mass".  Growing the hair forward to chase it would detach it from the
 * skull; the check that matters is hair-front against the NOSE, and both the
 * reference and this part put the forward lock level with the nose tip.
 *
 * Also not fixable: clay_0 and clay_4 disagree about the braid drape by
 * 0.12 m of depth at the same height, and a silhouette is a union of
 * projections, so no single static rope satisfies both.  This follows clay_0,
 * which is the drape that also satisfies braid_area_frac on both panels.
 *
 * And a correction to what "asymmetric braids" can buy, because round 3 tried
 * it and measured it.  An orthographic yaw 90 and yaw 270 render the SAME
 * object to exactly mirrored silhouettes, so any quantity computed from the
 * render alone -- `braid_area_frac` included -- is identical in those two
 * views for any geometry whatever, symmetric or not.  Asking for 0.044 at
 * yaw 90 and 0.034 at yaw 270 asks for something no model can do; only the
 * REFERENCE numbers differ, and they differ because the two panels are not a
 * mirrored pair (`clay_4` reads 0.19 m of braid behind the leg at y 0.62 where
 * `clay_0` reads 0.07 m, which is 0.14 m of z-extent that one object cannot
 * have twice).  Four asymmetric drapes were baked and scored against the same
 * build of every other part:
 *
 *     variant                                        score   mean IoU
 *     round-2 drape, symmetric                       41.70    0.7092
 *     her left plait carried out in x only           40.73    0.7092
 *     plait 15 mm further back, symmetric            41.65    0.7080
 *     plait back + out in x                          40.63    0.7077
 *     plait 30 mm back + carried out and back        41.35    0.7050
 *
 * The x-only variant is the one that hits `braid_area_frac` 0.034 at both side
 * views, and it is a point WORSE than doing nothing.  `BRAID_L_DELTA` keeps
 * the mechanism and the zeros so the next round can retry it from the spec
 * fragment without touching code, but the drape itself stayed at round 2's.
 */
import { Box, Field, Vec3, box, boxDistance, boxUnion } from '../sdf/types.js';
import {
  capsule, capsuleOval, clamp, cylinder, displace, ellipsoid, field, halfSpace, intersect, offset,
  roundBox, smoothSubtract, smoothUnion, union,
} from '../sdf/ops.js';
import { braid, catmullRom, frameAt, resample, tangentAt, Curve } from '../sdf/curve.js';
import { rotateAbout } from '../sdf/solids.js';
import { PartContext, PartModule, Shell, Tagged, constMaterial, nearestMaterial, paint } from './types.js';

/* ------------------------------------------------------------------ *
 * Local helpers
 * ------------------------------------------------------------------ */

/**
 * Union that skips a part whose bounding box is already further away than the
 * best distance found so far.
 *
 * `union` in ops.ts evaluates every member at every sample, which is right for
 * the handful of blobs a normal part is made of.  A braid is not that: it is
 * ~800 capsules per side, and the mesher would pay for all of them at every
 * sample near the head.  A shape never reaches outside its own bounds, so
 * `boxDistance` is a valid lower bound on its distance and the part can be
 * dropped without changing the answer.  Parts whose box *contains* the sample
 * are always evaluated, so values inside the solid stay exact and the surface
 * nets interpolation is untouched.
 */
function pruneUnion(parts: Field[]): Field {
  if (parts.length === 0) throw new Error('pruneUnion: no parts');
  if (parts.length === 1) return parts[0];
  const bounds: Box = parts.reduce((a, f) => boxUnion(a, f.bounds), parts[0].bounds);
  const lip = Math.max(...parts.map((f) => f.lip));
  const n = parts.length;
  return field(
    (x, y, z) => {
      let m = Infinity;
      for (let i = 0; i < n; i++) {
        const p = parts[i];
        const bd = boxDistance(p.bounds, x, y, z);
        if (bd > 0 && bd >= m) continue;
        const v = p.sdf(x, y, z);
        if (v < m) m = v;
      }
      return m;
    },
    bounds,
    lip,
  );
}

/**
 * One section of the crown: an ellipse in the (x, z) plane, tilted about Y.
 *
 * The six reference panels only measure four distinct directions -- yaw 0 and
 * 180 both project X, yaw 90 and 270 both project Z, and the two three-quarter
 * views project the diagonals -- so a horizontal slice of the head is fully
 * described by its support widths along X, Z, (1,0,-1) and (1,0,1).  That is
 * one measurement more than an ellipse has parameters, and the check comes out
 * right: for an ellipse w45^2 + w315^2 must equal wX^2 + wZ^2, and off the
 * clay panels that identity holds to 1 % at y 1.64 and 1.66 and to 2 % at
 * 1.68.  So the crown IS an ellipse per height, and its axes and tilt can be
 * solved for rather than sculpted by eye.  `CROWN_ROWS` is that solution.
 *
 * `theta` is the heading of the long axis, degrees from straight ahead (+Z)
 * toward her right (-X), so 45 is a blade running from her left-back to her
 * right-front.
 */
function crownSection(
  y: number, cx: number, cz: number, a: number, b: number, thetaDeg: number, ry: number,
): Field {
  const t = (thetaDeg * Math.PI) / 180;
  // rotateAbout maps local +x to (cos phi, 0, -sin phi); we want it on the
  // long axis u = (-sin t, 0, cos t).
  const phi = Math.atan2(-Math.cos(t), -Math.sin(t));
  return rotateAbout(ellipsoid([cx, y, cz], [a, ry, b]), [0, 1, 0], phi, [cx, y, cz]);
}

/**
 * Loft the crown sections: resampled to 8 mm and unioned HARD, not smoothly.
 *
 * A section is 0.11 m long and 0.012 m tall, and `ellipsoid` reports its own
 * `lip` as max(r)/min(r) -- about 8 -- because the scaled-sphere estimate can
 * under-report distance by that factor.  A chain of `smoothUnion(k)` over ten
 * such fields then blends on *reported* distance and pushes the surface out by
 * far more than k: measured, the loft alone ended at y 1.7195 and the finished
 * mass ran to 1.734 with a 0.14 m-deep cap at y 1.72 where the reference has a
 * 0.01 m point.  A hard union has no such term -- its zero set is exactly the
 * union of the ellipsoids -- and at 8 mm spacing against ry 0.016 the scallop
 * between sections is under 4 mm, well inside the low LOD's voxel.
 */
function crownBlade(rows: number[][]): Field {
  const y0 = rows[0][0];
  const y1 = rows[rows.length - 1][0];
  const yTop = y1 + 0.0040;
  const n = Math.max(2, Math.round((y1 - y0) / 0.008));
  const parts: Field[] = [];
  for (let i = 0; i <= n; i++) {
    const y = y0 + ((y1 - y0) * i) / n;
    let k = 0;
    while (k < rows.length - 2 && rows[k + 1][0] < y) k++;
    const A = rows[k], B = rows[k + 1];
    const t = clamp((y - A[0]) / Math.max(1e-9, B[0] - A[0]), 0, 1);
    const at = (j: number) => A[j] + (B[j] - A[j]) * t;
    const ry = clamp(Math.min(0.016, yTop - y), 0.0035, 0.016);
    parts.push(crownSection(y, at(1), at(2), at(3), at(4), at(5), ry));
  }
  return pruneUnion(parts);
}

/** Piecewise-linear lookup through (t, value) control points. */
function ramp(table: [number, number][], t: number): number {
  if (t <= table[0][0]) return table[0][1];
  const last = table[table.length - 1];
  if (t >= last[0]) return last[1];
  for (let i = 1; i < table.length; i++) {
    if (t <= table[i][0]) {
      const [t0, v0] = table[i - 1];
      const [t1, v1] = table[i];
      return v0 + ((v1 - v0) * (t - t0)) / Math.max(1e-9, t1 - t0);
    }
  }
  return last[1];
}

const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a: Vec3, k: number): Vec3 => [a[0] * k, a[1] * k, a[2] * k];

/**
 * A hanging lock: a chain of round cones through `[y, cx, cz, r]` rows.
 *
 * Round cones stay an exact distance field, which a lofted stack of ellipsoids
 * does not, so the mesher keeps skipping empty blocks around it.  `squash`
 * flattens the section in z where a lock reads as a sheet rather than a rope.
 */
function lockChain(rows: number[][], squashZ = 1, squashX = 1): Field {
  const segs: Field[] = [];
  for (let i = 1; i < rows.length; i++) {
    const [ya, xa, za, ra] = rows[i - 1];
    const [yb, xb, zb, rb] = rows[i];
    segs.push(capsuleOval([xa, ya, za], [xb, yb, zb], ra, rb, squashZ, squashX));
  }
  return union(...segs);
}

/* ------------------------------------------------------------------ *
 * Spec access
 * ------------------------------------------------------------------ */

interface HairNums {
  num(key: string, dflt: number): number;
  arr(key: string, dflt: number[]): number[];
  arr2(key: string, dflt: number[][]): number[][];
}

/**
 * Spec access that tolerates keys the checked-in resolved.json does not have
 * yet.  `Spec` is `typeof resolved.json`, so a fragment key added in the same
 * commit as the code that reads it would not typecheck until someone reran the
 * merge; reading through a defaulted lookup keeps the part buildable either way.
 */
function nums(ctx: PartContext): HairNums {
  const H = (ctx.spec as unknown as { hair?: Record<string, unknown> }).hair ?? {};
  return {
    num: (k, d) => (typeof H[k] === 'number' ? (H[k] as number) : d),
    arr: (k, d) => (Array.isArray(H[k]) ? (H[k] as number[]) : d),
    arr2: (k, d) => (Array.isArray(H[k]) && Array.isArray((H[k] as unknown[])[0])
      ? (H[k] as number[][]) : d),
  };
}

/* ------------------------------------------------------------------ *
 * The mass
 * ------------------------------------------------------------------ */

/**
 * Scalp cap sections: `[y, halfX, zFront, zBack, ry]`, crown first.
 *
 * halfX is the front-view half-width the section has to hit, taken off clay_2
 * / clay_5 on her LEFT side (the tight one) less 3 mm for the smooth-union
 * bulge; her right side gets its width from `SWEEP_ROWS` instead.  zBack runs
 * to -0.117, which is where the back of the mass sits in body_0 once the
 * braid runs behind it are excluded (the blue mask there reads
 * mass -0.092, gap, braid -0.123 .. -0.144; the gap is a specular break on
 * the hair, not skin, so the mass is continuous to about -0.12).
 */
const CAP_SECTIONS: number[][] = [
  // ROUND 3.  Rows above y 1.6050 are gone: the crown blade owns that band now.
  // These sections are ellipses square to the axes, and a square ellipse of the
  // right width and depth still carries material at (x +0.07, z +0.03) that a
  // blade tilted 42 degrees does not -- measured, that corner alone was 10 mm
  // of the yaw-315 width at every height from 1.61 to 1.67.
  [1.6050, 0.086, 0.036, -0.116, 0.021],
  [1.5975, 0.087, 0.031, -0.115, 0.021],
  [1.5900, 0.088, 0.025, -0.113, 0.021],
  [1.5825, 0.090, 0.019, -0.111, 0.021],
  [1.5750, 0.091, 0.013, -0.109, 0.021],
  [1.5675, 0.091, 0.006, -0.106, 0.021],
  [1.5600, 0.091, 0.000, -0.104, 0.021],
  [1.5525, 0.089, -0.007, -0.100, 0.020],
  [1.5450, 0.086, -0.014, -0.098, 0.020],
  [1.5375, 0.082, -0.021, -0.096, 0.019],
  [1.5300, 0.077, -0.028, -0.094, 0.019],
  [1.5225, 0.072, -0.034, -0.092, 0.018],
  [1.5150, 0.068, -0.040, -0.090, 0.018],
  [1.5075, 0.065, -0.046, -0.088, 0.017],
  [1.5000, 0.063, -0.050, -0.086, 0.017],
  [1.4925, 0.059, -0.054, -0.083, 0.016],
  [1.4850, 0.054, -0.058, -0.080, 0.015],
  [1.4775, 0.047, -0.062, -0.076, 0.013],
];

/**
 * The forward-swept lock on her RIGHT: `[y, cx, cz, r]`.
 *
 * This one shape carries the whole read of the hairstyle.  It springs off the
 * crown as the tallest point on the figure (y 1.715, x -0.055), sweeps out and
 * FORWARD over her right brow to x -0.129 / z +0.049 at eye level -- exactly
 * level with the nose in body_4 -- then falls past the cheek and tucks back in
 * at the jaw.  cx - r reproduces the measured front-view edge to about 3 mm
 * from y 1.715 down to y 1.44.
 */
const SWEEP_ROWS: number[][] = [
  // ROUND 3.  Above y 1.60 the sweep now traces the crown blade's own
  // her-right-front rim (c + a*u, pulled in by its radius) instead of standing
  // proud of it: measured, the old rows put the lock 26 mm outside the blade
  // along the blade's long axis at y 1.60, which is most of the +31 mm the
  // yaw-45 width was over.  Rows above y 1.685 are gone -- the blade owns that
  // band, and leaving a capsule up there let `massBlend` bridge the two and
  // grow a 0.14 m-deep cap at y 1.72 where the reference has a point.
  [1.6800, -0.062, 0.041, 0.021],
  [1.6700, -0.065, 0.040, 0.024],
  [1.6600, -0.068, 0.038, 0.026],
  [1.6500, -0.070, 0.035, 0.027],
  [1.6400, -0.073, 0.030, 0.028],
  [1.6300, -0.074, 0.027, 0.029],
  [1.6200, -0.074, 0.026, 0.029],
  [1.6100, -0.072, 0.026, 0.029],
  [1.6000, -0.070, 0.026, 0.029],
  [1.5950, -0.076, 0.026, 0.028],
  [1.5850, -0.091, 0.033, 0.027],
  [1.5750, -0.089, 0.032, 0.026],
  [1.5650, -0.088, 0.031, 0.026],
  [1.5550, -0.084, 0.030, 0.025],
  [1.5450, -0.083, 0.028, 0.024],
  [1.5350, -0.081, 0.025, 0.023],
  [1.5250, -0.078, 0.021, 0.022],
  [1.5150, -0.075, 0.017, 0.021],
  [1.5050, -0.072, 0.012, 0.020],
  [1.4950, -0.068, 0.006, 0.018],
  [1.4850, -0.050, 0.000, 0.013],
  [1.4750, -0.057, -0.005, 0.013],
  [1.4650, -0.057, -0.009, 0.011],
  [1.4550, -0.057, -0.013, 0.010],
  [1.4450, -0.057, -0.016, 0.009],
  [1.4350, -0.055, -0.019, 0.007],
  [1.4250, -0.051, -0.021, 0.004],
];

/**
 * The crown as a stack of solved ellipses: `[y, cx, cz, a, b, theta, ry]`.
 *
 * ROUND 3.  Round 2 built the crest as two round-cone chains widened in x, and
 * measured against all six panels that was a fin pointing the right way but far
 * too fat across itself: at y 1.70 the render was 0.137 wide from yaw 315 where
 * `clay_3` is 0.072, and 0.151 from the side where the two side panels average
 * 0.158.  Solving the ellipse per height instead (see `crownSection`) gives the
 * whole shape in one table.  The four measured widths, in metres, and the
 * ellipse they imply:
 *
 *     y      wX     wZ     w45    w315  ->  long   short   heading
 *   1.600  0.2135 0.2196 0.2344 0.1904    0.2374  0.1936    41 deg
 *   1.620  0.2165 0.2174 0.2344 0.1850    0.2396  0.1916    44
 *   1.640  0.2053 0.2124 0.2344 0.1796    0.2347  0.1794    41
 *   1.660  0.1819 0.2103 0.2248 0.1662    0.2270  0.1610    32
 *   1.680  0.1514 0.1953 0.2015 0.1394    0.2092  0.1319    27
 *   1.700  0.1134 0.1581 0.1686 0.0724    0.1791  0.0759    31
 *   1.710  0.0632 0.1265 0.1096 0.0362    0.1344  0.0436    21
 *
 * wX is the mean of `clay_2` and `clay_5` and wZ the mean of `clay_0` and
 * `clay_4`, because each pair shares a projection axis: an orthographic render
 * gives those two panels exactly mirrored silhouettes, so the mean is the only
 * thing a single model can be fitted to.  (The two members of each pair differ
 * by up to 0.06 m at the crown, which is the turnaround's own perspective, not
 * something geometry can chase.)
 *
 * So the crest is a blade that stays about 0.23 m long from y 1.60 to 1.66 and
 * thins from 0.19 m across to 0.04 m by y 1.71 while swinging from 44 degrees
 * to 21 -- a breaking wave rising off the crown and raking back over it, which
 * is what `head_1` and `head_2` show and what a pair of fat cones cannot be.
 */
const CROWN_ROWS: number[][] = [
  //  y      cx      cz       a       b     theta
  [1.5600, -0.002, -0.056, 0.0800, 0.0740, 44],
  [1.5850, -0.006, -0.059, 0.1030, 0.0895, 43],
  [1.6000, -0.010, -0.058, 0.1140, 0.0940, 42],
  [1.6200, -0.014, -0.054, 0.1170, 0.0910, 43],
  [1.6400, -0.017, -0.043, 0.1180, 0.0855, 41],
  [1.6600, -0.020, -0.037, 0.1140, 0.0755, 34],
  [1.6800, -0.024, -0.030, 0.1046, 0.0600, 29],
  [1.6960, -0.031, -0.024, 0.0900, 0.0330, 29],
  [1.7060, -0.040, -0.018, 0.0580, 0.0150, 26],
  [1.7120, -0.049, -0.013, 0.0380, 0.0100, 23],
  [1.7155, -0.056, -0.009, 0.0200, 0.0070, 21],
];

/**
 * The forward fringe: locks that leave the hairline and fall over the brow.
 *
 * `clay_2` has hair down to y 1.645 across the whole forehead with a point on
 * the midline; round 1 cut the hairline with a plane and put nothing in front
 * of it, so the forehead read as bald to the parting.  Rows are
 * `[y, cx, cz, r]` per lock, tip last.
 */
const FRINGE_ROWS: number[][][] = [
  // ROUND 3.  The two locks on her LEFT used to run forward to z +0.054 at
  // x +0.072.  Solving the crown ellipse says that point is 37 mm outside it
  // across the blade, and 37 mm across the blade is 26 mm of yaw-315 width,
  // which is where most of that view's +47 mm came from.  On the reference
  // her left side is swept BACK, not forward: at y 1.66 the ellipse's own
  // her-left extreme (x +0.074) sits at z -0.067, well behind the ear.
  [[1.6640, -0.050, 0.040, 0.012], [1.6560, -0.058, 0.049, 0.010], [1.6460, -0.062, 0.052, 0.008]],
  [[1.6660, -0.026, 0.045, 0.011], [1.6580, -0.030, 0.055, 0.010], [1.6480, -0.032, 0.058, 0.008]],
  [[1.6680, 0.000, 0.048, 0.011], [1.6600, 0.002, 0.057, 0.009], [1.6500, 0.004, 0.059, 0.007]],
  [[1.6660, 0.024, 0.040, 0.010], [1.6580, 0.030, 0.044, 0.009], [1.6500, 0.034, 0.042, 0.007]],
  [[1.6620, 0.046, 0.016, 0.010], [1.6540, 0.054, 0.010, 0.008], [1.6480, 0.060, 0.000, 0.006]],
];

/** The shorter lock in front of her LEFT ear: `[y, cx, cz, r]`. */
const LOCK_L_ROWS: number[][] = [
  [1.6100, 0.078, -0.016, 0.012],
  [1.5900, 0.080, -0.020, 0.014],
  [1.5700, 0.079, -0.018, 0.014],
  [1.5500, 0.076, -0.010, 0.013],
  [1.5300, 0.071, 0.000, 0.012],
  [1.5100, 0.066, 0.002, 0.010],
  [1.4900, 0.060, -0.002, 0.009],
  [1.4700, 0.055, -0.006, 0.008],
  [1.4500, 0.050, -0.010, 0.007],
  [1.4350, 0.046, -0.013, 0.005],
];

function hairMass(ctx: PartContext, H: HairNums): Field {
  const L = ctx.spec.landmarks;
  const hairTop = L.hairTop;

  /* ---- scalp cap ------------------------------------------------- *
   * A loft of elliptical sections, not a ball: the head under it is a
   * loft too, and a ball 15 mm outside the widest section is 30 mm
   * proud of the temples, which is what made the first pass read as a
   * motorcycle helmet.  Solid rather than hollowed -- the head is its
   * own closed surface underneath, so an inner wall costs triangles
   * nobody will ever see.                                            */
  const sections = H.arr2('capSections', CAP_SECTIONS);
  const cap = smoothUnion(
    0.010,
    ...sections.map(([y, halfX, zFront, zBack, ry]) =>
      ellipsoid([0, y, (zFront + zBack) / 2], [halfX, ry, (zFront - zBack) / 2])),
  );

  /* ---- the face is not hair -------------------------------------- *
   * The hairline is a plane, tilted back as it descends.  Cutting a
   * lofted skull with one plane gives exactly the arc a hairline is:
   * high over the middle of the forehead where the skull bulges
   * forward, sweeping down and back over the temples.  Slope 0.62
   * through (1.668, 0.052) reproduces body_0's LEFT-side hairline --
   * z +0.047 at y 1.66, z -0.003 at y 1.58 -- which is the side where
   * the forehead and temple are bare.  Her right side gets its cover
   * back from the sweep, which is unioned after this cut.            */
  const hairlineY = H.num('hairlineY', 1.668);
  const hairlineZ = H.num('hairlineZ', 0.052);
  const slope = H.num('hairlineSlope', 0.62);
  const norm = Math.hypot(slope, 1);
  const faceCut = halfSpace(
    [0, slope, -1],
    (slope * hairlineY - hairlineZ) / norm,
    box([-0.22, L.jaw - 0.12, -0.06], [0.22, hairTop + 0.08, 0.28]),
  );

  /* ---- the crest -------------------------------------------------- *
   * A loft of tilted ellipses, one per measured height, rather than a
   * pair of fattened cone chains: the panels measure a section's four
   * support widths and four widths over-determine an ellipse, so the
   * blade is solved rather than styled.  See CROWN_ROWS.              */
  const crest = crownBlade(H.arr2('crownRows', CROWN_ROWS));

  /* ---- the forward fringe ----------------------------------------- *
   * Unioned AFTER the hairline cut, so it lies over the forehead
   * instead of being sliced off by it.  Measured deficit it closes:
   * 10-15 mm of forward depth at y 1.50-1.66 in clay_0, and the whole
   * of the forehead cover in clay_2.                                  */
  // Clipped to the crown blade grown by 3 mm.  The fringe's job is to put back
  // the hair the hairline plane cut off the FRONT of the crown, not to add
  // volume the solved ellipse does not have: hand-placing the five locks left
  // three of them 5-18 mm outside it across the blade, and across the blade is
  // exactly the direction yaw 315 measures.
  const fringe = intersect(
    union(...FRINGE_ROWS.map((rows) => lockChain(rows, 0.72, 1.35))),
    offset(crest, H.num('fringeClip', 0.003)),
  );

  /* ---- the swept lock and the face-framing locks ------------------ */
  const sweep = lockChain(H.arr2('sweepRows', SWEEP_ROWS));
  const lockL = lockChain(H.arr2('lockLRows', LOCK_L_ROWS));

  /* ---- the gather -------------------------------------------------*
   * Where the plaits leave the head.  Without this the braid shell
   * looks pushed into the skull rather than grown from it: the plait
   * is 54 mm across at the nape and the cap's own back is only 20 mm
   * behind the braid axis there.                                     */
  const gatherZ = H.num('gatherZ', -0.104);
  const gather = (side: 1 | -1) => smoothUnion(
    0.018,
    ellipsoid([side * 0.030, 1.598, gatherZ], [0.038, 0.042, 0.032]),
    ellipsoid([side * 0.028, 1.545, gatherZ + 0.004], [0.034, 0.036, 0.030]),
    // Down the nape.  Without these the side view splits into three runs
    // between y 1.44 and 1.50 -- neck, air, braid -- where clay_0 is one
    // continuous 0.188 m run: the gathered plaits fill the whole hollow
    // behind the neck, and that 44 mm hole was a fifth of the braid-area
    // error at yaw 90.
    ellipsoid([side * 0.026, 1.500, gatherZ + 0.018], [0.024, 0.034, 0.046]),
    ellipsoid([side * 0.025, 1.452, gatherZ + 0.016], [0.021, 0.030, 0.044]),
  );

  /* ---- the centre part ------------------------------------------- *
   * A shallow groove down the midline of the FRONT only.  Running it
   * over the crown, as the first pass did, cut a hard notch across the
   * top of the crest that read as a crease in the silhouette.        */
  const partGroove = capsuleOval(
    [0, hairlineY - 0.006, hairlineZ + 0.004],
    [0, 1.6740, -0.012],
    0.010, 0.010, 1.0, 0.30,
  );

  /* ---- ear windows ------------------------------------------------ *
   * Both ears are bare in the reference -- head_3 and clay_4 show the
   * whole helix and a strip of bare temple in front of it, because the
   * hair is pulled up off the sides into the sweep.  Without this the
   * cap swallows the ear, and the ear is one of the few hard landmarks
   * the head has.  The -X window doubles as the notch that separates
   * the sweep from the skull in the profile.                          */
  const earWindow = (side: 1 | -1) => ellipsoid(
    [side * 0.074, 1.5680, -0.022], [0.028, 0.027, 0.021],
  );

  /* ---- surface grooves -------------------------------------------- *
   * The mass is a stack of plates, not a bob.  One groove separates the
   * sweep from the crown (the dark slot visible in clay_4 between them
   * at y 1.66-1.70) and the angular ripple below does the rest.        */
  const sweepGroove = lockChain([
    [1.7080, -0.040, -0.030, 0.005],
    [1.6900, -0.036, -0.026, 0.008],
    [1.6700, -0.040, -0.019, 0.009],
    [1.6500, -0.049, -0.011, 0.009],
    [1.6300, -0.059, -0.005, 0.008],
    [1.6100, -0.067, -0.003, 0.007],
    [1.5900, -0.071, -0.005, 0.006],
    [1.5700, -0.072, -0.010, 0.005],
  ]);

  /* ---- crest grooves ---------------------------------------------- *
   * The reference crown is a stack of thin layered blades with daylight
   * between them, not one loaf.  The layers run ALONG the blade -- from
   * the hairline back over the crown -- and are stacked across it, so
   * each groove is a furrow along u at a fixed height and a fixed
   * offset across v.  They are cut into the merged mass rather than
   * left as gaps between solids: round 1's separate blades showed
   * daylight at their roots in the three-quarter views, which the
   * reference never does.                                             */
  const crownRows = H.arr2('crownRows', CROWN_ROWS);
  const flank = (y: number, sv: number, su: number): number[] => {
    let best = crownRows[0];
    for (const r of crownRows) if (Math.abs(r[0] - y) < Math.abs(best[0] - y)) best = r;
    const [, cx, cz, a, b, th] = best;
    const t = (th * Math.PI) / 180;
    const ux = -Math.sin(t), uz = Math.cos(t);
    const vx = Math.cos(t), vz = Math.sin(t);
    return [y, cx + su * a * ux + sv * b * vx, cz + su * a * uz + sv * b * vz,
      H.num('furrowR', 0.0045)];
  };
  // The furrow's axis rides ON the surface (sv = +-1), so it takes a scallop
  // about one radius deep and leaves the blade's thickness alone.  Sinking it
  // to 0.8 b, as the first attempt did, put an 11 mm channel under a 35 mm
  // half-thickness and the crown came out serrated at the top.
  const furrow = (y: number, sv: number) => lockChain([
    flank(y, sv, -0.66), flank(y, sv, -0.22), flank(y, sv, 0.22), flank(y, sv, 0.62),
  ]);
  const crestGrooves = union(
    furrow(1.6440, 1.00), furrow(1.6440, -1.00),
    furrow(1.6720, 0.98), furrow(1.6720, -0.98),
  );

  // The crest joins the cap at a wide k so the wave and the skull are one
  // mass; the hairline is cut out of that, and only then do the pieces that
  // hang IN FRONT of the hairline -- fringe, sweep, left lock -- come back.
  const skullSide = smoothSubtract(0.007,
    smoothUnion(H.num('crownBlend', 0.020), cap, crest), faceCut);

  let solid = smoothSubtract(0.005, smoothUnion(
    H.num('massBlend', 0.018),
    skullSide,
    fringe,
    sweep,
    lockL,
    gather(1),
    gather(-1),
  ), partGroove);
  solid = smoothSubtract(0.008, solid, union(earWindow(1), earWindow(-1)));
  solid = smoothSubtract(0.006, solid, sweepGroove);
  solid = smoothSubtract(0.007, solid, crestGrooves);

  /* ---- strand corrugation ----------------------------------------- *
   * A ~2 cm ripple around the head's axis, damped to nothing near the
   * axis itself so the crown does not get a gradient spike (which is
   * what punches speckle holes at coarse LODs).                       */
  const amp = H.num('strandAmp', 0.0007);
  if (amp <= 0) return solid;
  const axisZ = -0.030;
  const freq = H.num('strandFreq', 17);
  return displace(solid, amp, H.num('strandWave', 0.012), (x, y, z) => {
    const dx = x, dz = z - axisZ;
    const r = Math.hypot(dx, dz);
    const damp = clamp((r - 0.022) / 0.030, 0, 1);
    return Math.sin(Math.atan2(dx, dz) * freq) * damp * damp;
  });
}

/* ------------------------------------------------------------------ *
 * The braids
 * ------------------------------------------------------------------ */

/**
 * Centreline of one braid, her left when `side` is +1: `[y, x, z]`.
 *
 * x comes off clay_5: the plaits are one column at the nape, 46 mm apart at
 * the shoulder blades, then splay to +-0.045 at the waist and +-0.075 over
 * the boots.
 *
 * z is the whole braid fix, and it is measured, not styled.  A braid *lies
 * on* the back; round 1 hung it in the air behind one.  Measured on the
 * assembled figure at yaw 90, the render split into two silhouette runs --
 * body, gap, braid -- at almost every height from y 0.3 to 1.5, and every
 * such run is thin enough for `debraid` to throw away, which is exactly the
 * `braid_area_frac` the scoreboard reads:
 *
 *      y      clay_0 runs                 round-1 render runs
 *    1.40     one run, 0.208              0.186 + gap 0.007 + 0.060
 *    1.20     one run, 0.255              0.191 + gap 0.037 + 0.047
 *    0.80     one run, 0.289              0.200 + gap 0.022 + 0.037
 *    0.50     0.131 + gap 0.015 + 0.034   0.118 + gap 0.026 + 0.037
 *
 * The reference is one run from y 0.70 all the way to the crown; it only
 * hangs free below the hip, and there it is 34 mm across.  So z here is set
 * from the body's own rearmost surface, probed shell by shell with
 * `out/hair_backz.ts`, as `backZ - r + ~0.010`: the plait's front face
 * overlaps the back by a centimetre from the crown to the hip, rides the
 * sash bustle at z -0.151 around y 1.00, and only clears the calf below
 * y 0.62.  Above the nape it also stands ~25 mm proud of the cap, which is
 * what makes the plait *visible* from y 1.69 as it is in clay_5 rather than
 * emerging from under the mass at y 1.55.
 *
 * ROUND 3, two corrections to that.
 *
 *  1. It is one run from y 0.70 to the crown, but BELOW y 0.72 `clay_0` has
 *     TWO, and round 2 glued the plait to the leg all the way down.  Measured
 *     with `tools/compare.py`'s own aligned bands, the yaw-90 render was
 *     1.7-1.9 %H (29-32 mm) NARROWER than `clay_0` at y 0.28-0.33 and again at
 *     y 0.62-0.67, while its de-braided CORE was 2.6-2.8 %H (45-48 mm) WIDER
 *     than the reference's over the same band -- the two errors are the same
 *     error, a plait fused to a calf.  The z column below y 0.76 now carries
 *     that deficit.
 *  2. The root came off the crown, y 1.695 -> 1.686, and in to x 0.016.  The
 *     solved crown ellipse is only 0.076 m thick across at y 1.70, and a plait
 *     standing 25 mm proud of it was 24 mm of the yaw-315 width and 30 mm of
 *     the yaw-45 width at y 1.71.
 */
const BRAID_ROWS: number[][] = [
  [1.686, 0.016, -0.070],
  [1.665, 0.021, -0.098],
  [1.635, 0.024, -0.111],
  [1.600, 0.025, -0.114],
  [1.560, 0.025, -0.115],
  [1.520, 0.025, -0.116],
  [1.470, 0.024, -0.113],
  [1.420, 0.024, -0.104],
  [1.380, 0.025, -0.099],
  [1.340, 0.025, -0.100],
  [1.300, 0.027, -0.099],
  [1.240, 0.031, -0.095],
  [1.180, 0.036, -0.089],
  [1.120, 0.040, -0.099],
  [1.060, 0.043, -0.126],
  [1.000, 0.045, -0.140],
  [0.940, 0.048, -0.132],
  [0.900, 0.050, -0.112],
  [0.860, 0.052, -0.100],
  [0.820, 0.054, -0.092],
  [0.760, 0.057, -0.080],
  [0.700, 0.059, -0.073],
  [0.640, 0.062, -0.071],
  [0.580, 0.065, -0.072],
  [0.500, 0.067, -0.087],
  [0.420, 0.069, -0.089],
  [0.340, 0.071, -0.092],
  [0.270, 0.073, -0.118],
  [0.215, 0.075, -0.132],
];

/**
 * How her LEFT plait's drape differs from her right's: `[y, dx, dz]`.
 *
 * The two plaits do not have to be mirror images, and the panels say they are
 * not.  What an asymmetric drape can and cannot buy is worth stating exactly,
 * because it is easy to ask it for the impossible: an orthographic yaw 90 and
 * yaw 270 render the same object to exactly mirrored silhouettes, so any
 * quantity computed from the render alone -- `braid_area_frac` included -- is
 * IDENTICAL in those two views for any geometry whatever.  Asymmetry cannot
 * split them.  What it can do is move mass in the plane: yaw 45 measures
 * (x - z)/sqrt2 and yaw 315 measures (x + z)/sqrt2, so a plait carried out to
 * her LEFT and BACK (+dx, -dz) lengthens the yaw-45 silhouette while leaving
 * yaw 315 almost untouched, and at y 0.80 the render IS 8.4 %H narrow against
 * `clay_1` and 4.8 %H wide against `clay_3`.
 *
 * It was tried, at four amplitudes, and every one of them scored worse than
 * leaving the two plaits mirrored -- see the table in the file header.  The
 * yaw-45 deficit is not the plait: `clay_1`'s two runs at y 0.4 to 0.8 are the
 * two LEGS, 0.09 m apart in a projection where two legs at the same depth
 * would overlap, so what that view is short of is a z stagger in the stance,
 * not hair.  The table is kept at zero so the next round can retry it from
 * `spec/parts/hair.json` without touching this file.
 */
const BRAID_L_DELTA: number[][] = [
  [1.100, 0.000, 0.000],
  [0.215, 0.000, 0.000],
];

function braidCurve(H: HairNums, side: 1 | -1): Curve {
  const rows = H.arr2('braidRows', BRAID_ROWS);
  const delta = H.arr2('braidLDelta', BRAID_L_DELTA);
  // `ramp` wants ascending keys and the tables descend, so read them reversed.
  const dxT: [number, number][] = delta.map(([y, dx]) => [y, dx] as [number, number]).reverse();
  const dzT: [number, number][] = delta.map(([y, , dz]) => [y, dz] as [number, number]).reverse();
  return rows.map(([y, x, z]) => (side > 0
    ? [x + ramp(dxT, y), y, z + ramp(dzT, y)] as Vec3
    : [-x, y, z] as Vec3));
}

/**
 * Envelope radius along the braid, with the lobes baked into it.
 *
 * The three helical strands do give a plaited *surface*, but their groove is
 * only 45 % of a 25 mm radius, i.e. about one voxel at the braid's LOD, so at
 * any sane triangle budget the plait sands itself into a smooth rope and the
 * silhouette stays a straight line.  Pulsing the envelope at the lobe rate --
 * three lobes per turn, exactly where the strands cross -- moves that detail
 * into the outline, where a voxel and a half of relief is plenty to read.
 *
 * The taper: the plait is thickest just below the gather and thins steadily,
 * and it is the FREE-HANGING part below the hip that the scoreboard sees, so
 * that end is sized off the side panels rather than the back.  clay_0 gives
 * a separate braid run of 0.049 at y 0.65, 0.034 at y 0.50 and 0.034 at
 * y 0.35 -- half-widths 0.024, 0.017, 0.017 -- while clay_5 gives 0.055
 * across at the nape and 0.038 at the calf.  The curve now starts at the
 * crown, so t = 0 is a thin root that thickens into the gather by t = 0.10.
 */
function braidRadius(H: HairNums, lobed = true): (t: number) => number {
  const scale = H.num('braidRScale', 1);
  const bulge = lobed ? H.num('braidBulge', 0.14) : 0;
  const lobes = 3 * H.num('braidTurns', 16);
  const table: [number, number][] = [
    [0.00, H.num('braidR0', 0.0195)],
    [0.04, 0.0250],
    [0.12, 0.0270],
    [0.24, 0.0265],
    [0.38, 0.0250],
    [0.52, 0.0235],
    [0.64, 0.0215],
    [0.76, 0.0190],
    [0.88, 0.0172],
    [1.00, H.num('braidR1', 0.0158)],
  ];
  return (t: number) => ramp(table, t) * scale * (1 + bulge * Math.sin(2 * Math.PI * lobes * t));
}

/**
 * The plait itself, cut into chunks so the mesher can skip most of it.
 *
 * `braid()` hands back one union over every capsule in all three strands, and
 * near the head that is ~800 distance evaluations per sample.  Braiding chunk
 * by chunk instead gives `pruneUnion` boxes to reject.  The chunk count has to
 * divide the twist into whole numbers of 1/3 turn or the strands would step
 * sideways at each seam: turns 16 over 16 chunks is exactly one turn each, so
 * strand s lands on strand s at every join.
 */
function plait(H: HairNums, curve: Curve): Field {
  const chunks = Math.max(1, Math.round(H.num('braidChunks', 16)));
  const turns = H.num('braidTurns', 16);
  const strandScale = H.num('braidStrandScale', 0.56);
  const rf = braidRadius(H);
  const segPer = Math.max(4, Math.round(H.num('braidSegPerChunk', 16)));

  // A dense polyline first: slicing the spline and re-splining each slice would
  // drift, sampling it finely and slicing the samples does not.
  const dense = resample(curve, chunks * segPer + 1);

  const parts: Field[] = [];
  for (let c = 0; c < chunks; c++) {
    const from = c * segPer;
    const sub = dense.slice(from, from + segPer + 1);
    const t0 = c / chunks, t1 = (c + 1) / chunks;
    parts.push(braid(sub, {
      segments: segPer + 1,
      radius: (t) => rf(t0 + (t1 - t0) * t),
      strandScale,
      turns: turns / chunks,
      strands: 3,
    }));
  }
  return pruneUnion(parts);
}

/** Parameter along `curve` whose point sits closest to height `y`. */
function tAtHeight(curve: Curve, y: number): number {
  const n = 160;
  let best = 0, bestD = Infinity;
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const d = Math.abs(catmullRom(curve, t)[1] - y);
    if (d < bestD) { bestD = d; best = t; }
  }
  return best;
}

/** Bands clamping the plait: a short cylinder square to the braid's tangent. */
function braidTies(H: HairNums, curve: Curve, rf: (t: number) => number): Field[] {
  const ys = H.arr('tieYs', [1.400, 1.180, 0.940, 0.640, 0.290]);
  const halfW = H.num('tieWidth', 0.013) * 0.5;
  const out: Field[] = [];
  for (const y of ys) {
    const t = tAtHeight(curve, y);
    const p = catmullRom(curve, t);
    const tan = tangentAt(curve, t);
    // `rf` here is the un-lobed radius, so the band has to clear the lobe
    // pulse's peak (1 + braidBulge) or it disappears inside the plait.
    const r = rf(t) * 1.14 + 0.0022;
    out.push(cylinder(add(p, mul(tan, -halfW)), add(p, mul(tan, halfW)), r));
  }
  return out;
}

/**
 * The frayed end: the plait is tied off and the loose hair fans out below it.
 *
 * clay_5 and clay_4 both end the plait proper at about y 0.20 and carry a
 * splayed tassel down across the boot cuff to y 0.07.  Round 1 tapered to a
 * 2.2 mm tip -- a sixth of a voxel at this shell's LOD -- so it never meshed
 * and the braid stopped dead at the tie; measured on the side views, the
 * reference puts 0.014 of its silhouette below y 0.20 and the round-1 render
 * put 0.0035 there.  Every blade radius is now floored at `tuftMinR`, which
 * is a voxel and a half, so the fray survives the mesher.
 */
function braidTuft(H: HairNums, curve: Curve, side: 1 | -1, rf: (t: number) => number): Field {
  const p = catmullRom(curve, 1);
  const { nor, bin } = frameAt(curve, 1);
  const tipY = H.num('braidTipY', 0.062);
  const blades = Math.max(2, Math.round(H.num('tuftBlades', 6)));
  const r = rf(1);
  const spread = H.num('tuftSpread', 0.040);
  const minR = H.num('tuftMinR', 0.0090);
  // The fan is written in world x/z, not in the curve's own frame: the frame
  // twists with the drape, and round 1's tassel opened almost entirely across
  // the figure, where a side view sees none of it.  clay_0 wants a 54 mm run
  // at y 0.12 hanging clear behind the boot, which is a spread in DEPTH.
  const out: Field[] = [];
  void nor; void bin;
  for (let i = 0; i < blades; i++) {
    const u = blades === 1 ? 0 : (i / (blades - 1)) * 2 - 1;   // -1 .. 1
    const end: Vec3 = [
      p[0] + side * 0.012 + u * 0.016,
      tipY + Math.abs(u) * 0.024,
      p[2] - spread * 0.72 + u * spread * 0.70,
    ];
    const mid: Vec3 = [
      (p[0] + end[0]) * 0.5,
      p[1] - (p[1] - end[1]) * 0.42,
      (p[2] + end[2]) * 0.5 + 0.005,
    ];
    out.push(capsuleOval(p, mid, r * 0.86, Math.max(minR, r * 0.74), 0.8, 1));
    out.push(capsuleOval(mid, end, Math.max(minR, r * 0.74), minR, 0.8, 1));
  }
  // A collar just under the tie so the blades leave one solid root.
  out.push(capsule(p, [p[0], p[1] - 0.018, p[2]], r * 1.00, r * 0.88));
  return union(...out);
}

/* ------------------------------------------------------------------ */

export const hairPart: PartModule = {
  id: 'hair',
  build(ctx) {
    const { mat } = ctx;
    const H = nums(ctx);
    const L = ctx.spec.landmarks;

    /* ---------------- mass ---------------- */
    const massField = hairMass(ctx, H);
    // Roots and the underside of the sweep go darker; it is what gives the
    // back view any depth at all once the braids are the same blue.
    const darkZone = union(
      roundBox([0, L.neckBase + 0.055, -0.085], [0.085, 0.060, 0.055], 0.02),
      ellipsoid([0, L.brow + 0.055, -0.070], [0.070, 0.045, 0.070]),
    );
    const massShell: Shell = {
      name: 'hair',
      field: massField,
      material: paint(constMaterial(mat.hair), darkZone, mat.hairDark ?? mat.hair, 0.0),
      voxelScale: H.num('massVoxelScale', 1.0),
    };

    /* ---------------- braids ---------------- */
    // Ties and tufts size off the *mean* radius: a tie whose radius rode the
    // lobe pulse would be a different size on every braid.
    const rf = braidRadius(H, false);
    const plaits: Field[] = [];
    const ties: Field[] = [];
    const tufts: Field[] = [];
    for (const side of [1, -1] as const) {
      const curve = braidCurve(H, side);
      plaits.push(plait(H, curve));
      ties.push(...braidTies(H, curve, rf));
      tufts.push(braidTuft(H, curve, side, rf));
    }
    const tieField = pruneUnion(ties);
    const braidField = pruneUnion([...plaits, ...tufts, tieField]);

    const tags: Tagged[] = [
      { field: tieField, mat: mat.leather ?? mat.hair },
      { field: pruneUnion(tufts), mat: mat.hairDark ?? mat.hair },
      { field: pruneUnion(plaits), mat: mat.hair },
    ];
    const braidShell: Shell = {
      name: 'braids',
      field: braidField,
      material: nearestMaterial(tags, mat.hair),
      voxelScale: H.num('braidVoxelScale', 1.25),
    };

    return [massShell, braidShell];
  },
};
