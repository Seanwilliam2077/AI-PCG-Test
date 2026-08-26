/**
 * `grip` — the raked handle, from the frame's underside to the butt.
 *
 * ---------------------------------------------------------------------------
 * What the reference actually says about this part, and what it does not
 * ---------------------------------------------------------------------------
 * §10.7 declared the grip's lateral surface to have zero unoccluded pixels in
 * nine views, and `mat.grip.notWood` concluded from the butt cap that the whole
 * grip is the frame's cool blue-grey paint. The adversarial audit (§11.2, D-1)
 * **refuted both**: pose3 carries a clean unoccluded lateral grip face at sheet
 * x 2409-2435, y 326-345, where 388 of 540 pixels read a* +6.48 / b* +11.44 —
 * warm, hue 60.5 deg — while the butt cap 20 px below reads a* -0.96 / b* -7.35,
 * which is the frame paint to within half a unit in each channel.
 *
 * So this module builds two materials where the frozen text wanted one:
 *
 *   `grip.body`      warm, dark red-brown. The brief's "dark red-brown wood" is
 *                    partly vindicated and is built as such.
 *   `grip.butt-cap`  the frame's paint. It is the only grip surface any view
 *                    shows, it is 23 % of the grip's height (§10.7 item 7), and
 *                    that 23 % is exactly the complement of the 77 % window in
 *                    `grip.fingerCourse.count` — two rows written from different
 *                    pixels landing on the same seam, which is why the seam is
 *                    placed there and not somewhere prettier.
 *
 * `mat.grip.notWood` is therefore deliberately FAILED for `grip.body` and held
 * for `grip.butt-cap`. That is the audit's verdict, not a modelling preference.
 *
 * ---------------------------------------------------------------------------
 * D-11, the contradiction, and which leg was cut
 * ---------------------------------------------------------------------------
 * Three statements about the grip's axial footprint cannot all hold:
 *   (a) `grip.root.flushWithFrame` — "the grip's axial footprint lies inside the
 *       frame's" (u 0.808-0.955)
 *   (b) `grip.butt.behindFrameHeel` — butt 0.05-0.35 D rearward of the frame
 *   (c) the assembly tree — grip spans u 0.808-1.000
 *
 * (b) and (c) agree with each other and with §2's landmark table, which *defines*
 * u = 1 as the butt's rear vertex: if the grip's footprint sat inside the frame's,
 * the receiver would be the rearmost vertex and u = 1 would be somewhere else,
 * taking A with it. So (a)'s second clause is the leg that was cut. (a)'s *first*
 * clause — gap <= 0.03 D at the root — is kept, because that is the part its own
 * evidence supports (pose3's unbroken frame-underside line at y 288-293).
 *
 * A fourth statement then also fails, and it is worth naming rather than hiding:
 * the tree's u 0.808 *front* of the grip. Rake 107 deg over a 1.55 D grip moves
 * the butt 0.45 D rearward of the root all by itself, and the section is 0.84 D
 * deep; 0.45 + 0.84 already exceeds the 1.071 D the tree allots the whole grip.
 * §6.9's own measured rows and the tree's own span are not simultaneously
 * satisfiable. This build honours the measured rows and lets the front strap's
 * root run forward to u 0.751 — under the trigger guard, where every view has a
 * hand over it and nothing was ever measured. As built the grip spans
 * u 0.751-1.000, with the butt's rearmost vertex on X_BUTT exactly.
 *
 * ---------------------------------------------------------------------------
 * The finish is generated, and what that costs
 * ---------------------------------------------------------------------------
 * The reference is a measurement target and its pixels may not be projected onto
 * this model, so the Talon demo's `projectUV()` de-lit-plate technique — the one
 * thing that made its finish read as the real asset — does not transfer. Colour
 * here comes from the contract's CIE Lab numbers, converted once to sRGB, and
 * the only texture is a neutral, lightness-only grain generated as a DataTexture.
 *
 * What that costs, stated plainly: the projected plates carried the reference's
 * hand-painted *value structure* — the wear at the butt, the darkening into the
 * strap hollows, the paint chipping at the cap's edge. None of that survives.
 * A generated finish reproduces the measured chromaticity and nothing else, so
 * this grip will read cleaner and newer than the reference at any distance where
 * the value structure would have been visible. §6.10's own rule is the reason it
 * is still worth doing: every colour claim in the contract is anchored on
 * (a*, b*) inside a matched-L window, never on lightness, because "no whole part
 * on this object is a flat colour sample". The grain map is therefore *neutral*
 * and modulates lightness only — the measured chromaticity survives it exactly,
 * and the one thing the grain could have falsified is the one thing the contract
 * declines to measure. The grain itself is DECLARED: at 27x20 px no wood figure
 * is resolvable, so it is kept at +-3.5 % contrast, low enough to be a surface
 * quality rather than a claim.
 *
 * ---------------------------------------------------------------------------
 * Construction
 * ---------------------------------------------------------------------------
 * Not a revolved part, so: extrude a traced sagittal profile, then warp every
 * vertex's Z by a cross-section field. A constant-thickness extrude would give
 * the grip two flat slabs and a square rim, which is the "toy cutout" failure the
 * Talon demo names — and on a grip it is worse than on a blade, because a grip is
 * defined by the palm swell that a constant thickness deletes.
 *
 * The outline and the thickness field are driven by the *same* three splines
 * (front strap, back strap, half-width). The field cannot drift away from the
 * silhouette it is supposed to round, because there is only one source for both.
 * The splines are monotone (Fritsch-Carlson) rather than Catmull-Rom: a
 * Catmull-Rom overshoot between two strap knots would put a bump on the front
 * strap, and `grip.fingerCourse.count` fails on exactly that — "no transverse
 * feature interrupts the front strap between 12 % and 77 % of grip height".
 */

import * as THREE from 'three';
import { D, X_BUTT, PART } from './datum';

// ---------------------------------------------------------------------------
// Frame of the grip
// ---------------------------------------------------------------------------

/** `grip.rakeFromBore` = 107 +- 10 deg (§6.9, D13 resolved the 108-vs-62 clash). */
const RAKE_DEG = 107;
const RAKE = THREE.MathUtils.degToRad(RAKE_DEG);

/**
 * The grip's downward axis, at RAKE from the bore's forward direction (+X).
 * D13 records that every projected reading of this angle is a *lower* bound, so
 * 107 is taken at its stated centre rather than shaded toward the 104 readings.
 */
const AXIS_DOWN = new THREE.Vector2(Math.cos(RAKE), -Math.sin(RAKE));

/** In-plane grip basis: +GX toward the front strap, +GY back up the grip. */
const GX = new THREE.Vector2(-AXIS_DOWN.y, AXIS_DOWN.x);
const GY = AXIS_DOWN.clone().negate();

/** `grip.length.overTubeOd` 1.55 +- 0.20 D, centre-line root plane to butt plane. */
const GRIP_LEN = 1.55 * D;

/**
 * Root plane height. Not a row of its own — it is forced by three that are.
 * `grip.heelDrop.overTubeOd` (2.19 +- 0.20 D) minus the axial length and the
 * toe's own drop leaves the root in [-0.699 D, -0.299 D]; `grip.root.flushWith
 * Frame`'s evidence (frame underside at sheet y 288-293 against the bore axis at
 * y 269.3, over D = 37 px) puts it in [-0.641 D, -0.505 D]. -0.62 D is inside
 * both, near the deep end of the second so the frame gets as much height as the
 * intersection allows.
 *
 * Consequence for the frame module, stated because it is not mine to fix:
 * with `frame.top.aboveAxis` = +0.32 D this implies a receiver 0.94 D tall,
 * against `frame.heightOverTubeOd`'s >= 1.05 lower bound. That row's evidence is
 * "the lower edge is where the hand starts", i.e. an occlusion boundary, and it
 * is conf 0.45; the flush row is conf 0.80 and reads an actual line. The grip is
 * built to the flush row.
 */
const ROOT_Y = -0.62 * D;

/** `grip.butt-cap` is the lower 23 % of the grip's height (§10.7 item 7). */
const SEAM_T = 0.77;

// ---------------------------------------------------------------------------
// The three profile splines. Units of D; t = h / GRIP_LEN, 0 at the root plane.
// ---------------------------------------------------------------------------

/**
 * Monotone piecewise cubic (Fritsch-Carlson). Returns a closure so the slope
 * solve happens once, not once per warped vertex.
 */
function makeSpline(knots: number[][]): (x: number) => number {
  const n = knots.length;
  const hs: number[] = [];
  const del: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    hs.push(knots[i + 1][0] - knots[i][0]);
    del.push((knots[i + 1][1] - knots[i][1]) / hs[i]);
  }
  const m: number[] = new Array(n);
  m[0] = del[0];
  m[n - 1] = del[n - 2];
  for (let i = 1; i < n - 1; i++) {
    if (del[i - 1] * del[i] <= 0) {
      m[i] = 0;
    } else {
      const w1 = 2 * hs[i] + hs[i - 1];
      const w2 = hs[i] + 2 * hs[i - 1];
      m[i] = (w1 + w2) / (w1 / del[i - 1] + w2 / del[i]);
    }
  }
  return (x: number) => {
    if (x <= knots[0][0]) return knots[0][1];
    if (x >= knots[n - 1][0]) return knots[n - 1][1];
    let k = 0;
    while (x > knots[k + 1][0]) k++;
    const t = (x - knots[k][0]) / hs[k];
    const t2 = t * t;
    const t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * knots[k][1]
      + (t3 - 2 * t2 + t) * hs[k] * m[k]
      + (-2 * t3 + 3 * t2) * knots[k + 1][1]
      + (t3 - t2) * hs[k] * m[k + 1];
  };
}

/**
 * Front strap. `grip.depth.overTubeOd` = 0.84 +- 0.18 D at 50 % height fixes
 * 0.420 against the back strap's 0.420; `grip.butt.majorAxis.overTubeOd` =
 * 1.15 (+0.25/-0.10) D fixes the sum at the butt. The flare is put mostly on the
 * heel because the same butt has to sit 0.05-0.35 D *rearward* of the frame.
 *
 * No knot puts a local maximum between t 0.12 and t 0.77: a bulge there is a
 * transverse feature and `grip.fingerCourse.count` counts it as one. There are
 * also no finger grooves, for the reason §10.7 item 7 gives — front-strap
 * curvature and groove count are unmeasurable and were declined, not invented.
 * The row only asks that four fingers *fit*, which is a clearance test, and the
 * built length passes it with 8 % to spare.
 */
const frontOffset = makeSpline([
  [0.00, 0.360], [0.20, 0.395], [0.45, 0.415],
  [0.50, 0.420], [0.70, 0.437], [0.85, 0.492], [1.00, 0.600],
]);

const backOffset = makeSpline([
  [0.00, -0.360], [0.15, -0.395], [0.35, -0.415],
  [0.50, -0.420], [0.65, -0.452], [0.85, -0.552], [1.00, -0.630],
]);

/**
 * Half-width across Z. `grip.width.overTubeOd` = 0.47 +- 0.15 D is DECLARED at
 * confidence 0.25 — the weakest number in §6.9 — and it is kept rather than
 * improved, because nothing measurable improves it: the audit's one unoccluded
 * patch is a *lateral* face, which constrains colour and says nothing about how
 * far the surface is from the sagittal plane. The butt flares to 0.55 D, still
 * far short of the 1.07 D bottom-face chord, so the butt's longest chord stays
 * the depth direction as `grip.butt.majorAxis` requires.
 *
 * Cross-check against the hand rather than the scale chain: the mid section's
 * convex-hull perimeter comes out near 2.1 D = 109 mm, inside
 * `grip.circumference.overTubeOd`'s <= 2.75 D ceiling, which is the row that
 * exists so the character's hand can close on this and not pinch it.
 */
const halfWidth = makeSpline([
  [0.00, 0.205], [0.30, 0.228], [0.50, 0.235], [0.77, 0.248], [1.00, 0.275],
]);

// ---------------------------------------------------------------------------
// The sagittal plane: profile, extrude and field all live in "planar" coords,
// whose origin is the root-plane centre. The whole grip is translated to the
// model frame once, at the end. That ordering is what lets the grip's x be
// *solved* from the finished outline rather than declared — see ROOT_X.
// ---------------------------------------------------------------------------

function planarOf(q: number, h: number, out = new THREE.Vector2()): THREE.Vector2 {
  return out.set(GX.x * q - GY.x * h, GX.y * q - GY.y * h);
}

/** Grip-local (q forward of the centre line, h down the axis) from planar XY. */
function localOf(px: number, py: number): { q: number; h: number } {
  return { q: px * GX.x + py * GX.y, h: -(px * GY.x + py * GY.y) };
}

function frontAt(h: number): number { return frontOffset(h / GRIP_LEN) * D; }
function backAt(h: number): number { return backOffset(h / GRIP_LEN) * D; }
function widthAt(h: number): number { return halfWidth(h / GRIP_LEN) * D; }

/**
 * Where a strap crosses the root plane. The root face is horizontal, not normal
 * to the grip axis: `grip.root.flushWithFrame` compares hi(grip, up) against
 * lo(frame, up), and an axis-normal root face would put the back strap's corner
 * 0.11 D above the frame's underside and blow the 0.03 D gap by 4x.
 */
function rootH(strap: (h: number) => number): number {
  let h = 0;
  for (let i = 0; i < 8; i++) h = (GX.y / GY.y) * strap(h);
  return h;
}

// ---------------------------------------------------------------------------
// The cross-section field
// ---------------------------------------------------------------------------

/** Superellipse exponent. 2 is a plain ellipse and reads soapy; 2.6 keeps a
 *  flat-ish palm face and still rounds the straps. DECLARED — §10.7 item 7. */
const SECTION_N = 2.6;

/**
 * Fraction of the local half-width the rim keeps at the silhouette edge. Zero
 * would collapse the extrude's side walls onto themselves and hand the renderer
 * degenerate triangles along the whole outline; a small positive floor leaves a
 * narrow rim band there instead, which the extrude bevel then rounds.
 */
const RIM = 0.13;

/** Half-thickness of the solid at a planar XY point. */
function halfThickness(x: number, y: number): number {
  const { q, h } = localOf(x, y);
  const qf = frontAt(h);
  const qb = backAt(h);
  const mid = 0.5 * (qf + qb);
  const half = 0.5 * (qf - qb);
  let e = half > 1e-9 ? (q - mid) / half : 0;
  e = e < -1 ? -1 : e > 1 ? 1 : e;
  const shell = Math.pow(Math.max(0, 1 - Math.pow(Math.abs(e), SECTION_N)), 1 / SECTION_N);
  return widthAt(h) * (RIM + (1 - RIM) * shell);
}

// ---------------------------------------------------------------------------
// Outline assembly
// ---------------------------------------------------------------------------

function sampleStrap(strap: (h: number) => number, h0: number, h1: number, n: number): THREE.Vector2[] {
  const out: THREE.Vector2[] = [];
  for (let i = 0; i <= n; i++) {
    const h = h0 + (h1 - h0) * (i / n);
    out.push(planarOf(strap(h), h));
  }
  return out;
}

/** Drop `len` of arc length from one end of a polyline. */
function trimPolyline(p: THREE.Vector2[], len: number, fromTail: boolean): THREE.Vector2[] {
  const q = fromTail ? p.slice().reverse() : p.slice();
  let acc = 0;
  let i = 0;
  while (i < q.length - 1) {
    const seg = q[i].distanceTo(q[i + 1]);
    if (acc + seg >= len) {
      const t = (len - acc) / seg;
      q[i] = q[i].clone().lerp(q[i + 1], t);
      break;
    }
    acc += seg;
    i++;
  }
  const cut = q.slice(i);
  return fromTail ? cut.reverse() : cut;
}

/**
 * Quadratic-Bezier corner fillet. `p0` and `p2` are the *exact* endpoints of the
 * neighbouring pieces, never recomputed from `c` by offsetting along a chord:
 * a recomputed endpoint lands a fraction of a millimetre off the piece it is
 * supposed to continue, and that leaves a reflex micro-kink in the outline.
 * `ExtrudeGeometry` then miters the bevel across it, and because a miter length
 * goes as 1/sin(theta/2) the bevel flies *outward* at that one vertex — on this
 * grip it put a 6-vertex spike 0.19 mm above the root plane, i.e. above the
 * frame's underside, which is precisely the surface `grip.root.flushWithFrame`
 * measures. Interior points only; the caller owns the endpoints.
 */
function bezArc(out: THREE.Vector2[], p0: THREE.Vector2, c: THREE.Vector2, p2: THREE.Vector2, segs: number): void {
  for (let i = 1; i < segs; i++) {
    const t = i / segs;
    const u = 1 - t;
    out.push(new THREE.Vector2(
      u * u * p0.x + 2 * u * t * c.x + t * t * p2.x,
      u * u * p0.y + 2 * u * t * c.y + t * t * p2.y,
    ));
  }
}

const STRAP_SAMPLES = 40;
const ROOT_FILLET = 0.045 * D;
const TOE_FILLET = 0.070 * D;
const HEEL_FILLET = 0.090 * D;

const H_SEAM = SEAM_T * GRIP_LEN;

/** Body outline: horizontal root plane at the top, flat material seam at 77 %. */
function bodyOutline(): THREE.Vector2[] {
  const hF = rootH(frontAt);
  const hB = rootH(backAt);

  const front = trimPolyline(sampleStrap(frontAt, hF, H_SEAM, STRAP_SAMPLES), ROOT_FILLET, false);
  const back = trimPolyline(sampleStrap(backAt, H_SEAM, hB, STRAP_SAMPLES), ROOT_FILLET, true);
  const cornerF = planarOf(frontAt(hF), hF);
  const cornerB = planarOf(backAt(hB), hB);
  const edge = cornerF.clone().sub(cornerB).normalize();
  const edgeB = cornerB.clone().addScaledVector(edge, ROOT_FILLET);
  const edgeF = cornerF.clone().addScaledVector(edge, -ROOT_FILLET);

  const pts: THREE.Vector2[] = [];
  pts.push(...front);                                       // root -> seam, front strap
  pts.push(...back);                                        // across the seam, then up the back
  bezArc(pts, back[back.length - 1], cornerB, edgeB, 4);
  pts.push(edgeB, edgeF);                                   // the flat root face
  bezArc(pts, edgeF, cornerF, front[0], 4);
  return pts;
}

/**
 * The toe fillet's Bezier control triple. The stud has to sit on this arc, and
 * the arc has to be the one the outline actually uses — one function, so the
 * stud cannot end up floating off a corner that was later reshaped.
 */
function toeArc(): { p0: THREE.Vector2; c: THREE.Vector2; p2: THREE.Vector2 } {
  const front = trimPolyline(sampleStrap(frontAt, H_SEAM, GRIP_LEN, 18), TOE_FILLET, true);
  const toe = planarOf(frontAt(GRIP_LEN), GRIP_LEN);
  const heel = planarOf(backAt(GRIP_LEN), GRIP_LEN);
  const edge = heel.clone().sub(toe).normalize();
  return { p0: front[front.length - 1], c: toe, p2: toe.clone().addScaledVector(edge, TOE_FILLET) };
}

/** Butt-cap outline: flat seam at 77 %, filleted toe and heel on the butt face. */
function buttOutline(): THREE.Vector2[] {
  const front = trimPolyline(sampleStrap(frontAt, H_SEAM, GRIP_LEN, 18), TOE_FILLET, true);
  const back = trimPolyline(sampleStrap(backAt, GRIP_LEN, H_SEAM, 18), HEEL_FILLET, false);
  const heel = planarOf(backAt(GRIP_LEN), GRIP_LEN);
  const toeF = toeArc();
  const edgeHeel = heel.clone().addScaledVector(toeF.c.clone().sub(heel).normalize(), HEEL_FILLET);

  const pts: THREE.Vector2[] = [];
  pts.push(...front);
  bezArc(pts, toeF.p0, toeF.c, toeF.p2, 5);
  pts.push(toeF.p2, edgeHeel);                              // the flat butt face
  bezArc(pts, edgeHeel, heel, back[0], 5);
  pts.push(...back);
  return pts;
}

/**
 * The butt's rear vertex *is* u = 1.000: §2's landmark table uses it to define A,
 * so it is a datum, not a target. It is therefore solved from the *finished*
 * outline — after the heel fillet has taken its bite out of the corner — rather
 * than from the heel's nominal offset. Placing the grip from the nominal corner
 * instead left the butt 1.3 mm short of X_BUTT, which is a 2.5 % error in A
 * introduced by a cosmetic fillet.
 */
const ROOT_X = X_BUTT - Math.min(...buttOutline().map((p) => p.x));

function worldOf(q: number, h: number, out = new THREE.Vector2()): THREE.Vector2 {
  return planarOf(q, h, out).add(new THREE.Vector2(ROOT_X, ROOT_Y));
}

// ---------------------------------------------------------------------------
// Extrude + warp
// ---------------------------------------------------------------------------

/** Small, per the Talon demo: a large bevel self-intersects on the concave
 *  corners of a traced profile and spikes into bright white creases. */
const BEVEL_THICKNESS = 0.0012;
const BEVEL_SIZE = 0.0018;

/**
 * `bevelOffset` must be -bevelSize, and the default of 0 is a trap for any
 * profile traced to a measured silhouette. At offset 0 three.js treats the
 * outline you hand it as the *lid* and grows the mid-depth section outward by
 * bevelSize, so every measured extent comes back 2*bevelSize too large: measured
 * on this grip that put the root plane 1.8 mm above the frame's underside and
 * pushed the axial length from 1.66 D to 1.72 D, eating most of the margin under
 * `grip.length.overTubeOd`'s ceiling for no reason anyone would ever see. At
 * -bevelSize the traced outline is the silhouette and the bevel rounds inward
 * off it, which is what a traced profile means.
 */
const BEVEL_OFFSET = -BEVEL_SIZE;

/** Half-thickness the extrude is built at, before the field replaces it. */
const Z_NOMINAL = 0.275 * D;

type Tri = { p: number[]; n: number[]; uv: number[] };

function readTriangles(g: THREE.BufferGeometry, start: number, count: number): Tri[] {
  const P = g.getAttribute('position');
  const N = g.getAttribute('normal');
  const U = g.getAttribute('uv');
  const out: Tri[] = [];
  for (let i = start; i < start + count; i += 3) {
    const t: Tri = { p: [], n: [], uv: [] };
    for (let k = 0; k < 3; k++) {
      const j = i + k;
      t.p.push(P.getX(j), P.getY(j), P.getZ(j));
      t.n.push(N.getX(j), N.getY(j), N.getZ(j));
      t.uv.push(U.getX(j), U.getY(j));
    }
    out.push(t);
  }
  return out;
}

/**
 * 4-split, midpoint. Run on the lid triangles only, and run *before* the warp:
 * a lid triangle out of ear-clipping can span half the grip, and warping its
 * three corners then interpolating linearly across it flattens the palm swell
 * into a crease at the bevel break — the Talon demo's exact note.
 */
function subdivide(tris: Tri[], levels: number): Tri[] {
  let cur = tris;
  for (let l = 0; l < levels; l++) {
    const next: Tri[] = [];
    for (const t of cur) {
      const mid = (a: number, b: number, arr: number[], stride: number) => {
        const o: number[] = [];
        for (let k = 0; k < stride; k++) o.push(0.5 * (arr[a * stride + k] + arr[b * stride + k]));
        return o;
      };
      const P = [t.p.slice(0, 3), t.p.slice(3, 6), t.p.slice(6, 9)];
      const N = [t.n.slice(0, 3), t.n.slice(3, 6), t.n.slice(6, 9)];
      const U = [t.uv.slice(0, 2), t.uv.slice(2, 4), t.uv.slice(4, 6)];
      const Pm = [mid(0, 1, t.p, 3), mid(1, 2, t.p, 3), mid(2, 0, t.p, 3)];
      const Nm = [mid(0, 1, t.n, 3), mid(1, 2, t.n, 3), mid(2, 0, t.n, 3)];
      const Um = [mid(0, 1, t.uv, 2), mid(1, 2, t.uv, 2), mid(2, 0, t.uv, 2)];
      const push = (a: number[][], b: number[][], c: number[][]) => next.push({
        p: [...a[0], ...b[0], ...c[0]],
        n: [...a[1], ...b[1], ...c[1]],
        uv: [...a[2], ...b[2], ...c[2]],
      });
      push([P[0], N[0], U[0]], [Pm[0], Nm[0], Um[0]], [Pm[2], Nm[2], Um[2]]);
      push([Pm[0], Nm[0], Um[0]], [P[1], N[1], U[1]], [Pm[1], Nm[1], Um[1]]);
      push([Pm[2], Nm[2], Um[2]], [Pm[1], Nm[1], Um[1]], [P[2], N[2], U[2]]);
      push([Pm[0], Nm[0], Um[0]], [Pm[1], Nm[1], Um[1]], [Pm[2], Nm[2], Um[2]]);
    }
    cur = next;
  }
  return cur;
}

/**
 * Average normals across coincident positions when the two facets are within
 * `maxAngle`. ExtrudeGeometry is non-indexed, so its `computeVertexNormals` is
 * flat: without this the two-segment bevel reads as two hard facets and the rim
 * catches a bright line all the way round the silhouette. The angle gate keeps
 * the seam face and the butt face crisp against the straps, which are real
 * material and manufacturing edges and should stay sharp.
 */
function smoothNormals(g: THREE.BufferGeometry, maxAngleDeg: number): void {
  const P = g.getAttribute('position');
  const N = g.getAttribute('normal');
  const cosLimit = Math.cos(THREE.MathUtils.degToRad(maxAngleDeg));
  const buckets = new Map<string, number[]>();
  const key = (i: number) =>
    `${Math.round(P.getX(i) * 1e5)},${Math.round(P.getY(i) * 1e5)},${Math.round(P.getZ(i) * 1e5)}`;
  for (let i = 0; i < P.count; i++) {
    const k = key(i);
    const b = buckets.get(k);
    if (b) b.push(i); else buckets.set(k, [i]);
  }
  const out = new Float32Array(N.count * 3);
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const acc = new THREE.Vector3();
  for (const idx of buckets.values()) {
    for (const i of idx) {
      a.set(N.getX(i), N.getY(i), N.getZ(i));
      acc.set(0, 0, 0);
      for (const j of idx) {
        b.set(N.getX(j), N.getY(j), N.getZ(j));
        if (a.dot(b) >= cosLimit) acc.add(b);
      }
      if (acc.lengthSq() < 1e-12) acc.copy(a);
      acc.normalize();
      out[i * 3] = acc.x; out[i * 3 + 1] = acc.y; out[i * 3 + 2] = acc.z;
    }
  }
  for (let i = 0; i < N.count; i++) N.setXYZ(i, out[i * 3], out[i * 3 + 1], out[i * 3 + 2]);
  N.needsUpdate = true;
}

/**
 * Extrude the outline, then replace the constant thickness with the field.
 *
 * Normals are analytic, from the field's gradient, and one formula covers lids,
 * bevel and rim: the warp is the map (x, y, z) -> (x, y, z*lambda(x,y)), whose
 * inverse-transpose Jacobian sends n to
 *
 *     ( n.x - n.z*z*dlambda/dx / lambda,
 *       n.y - n.z*z*dlambda/dy / lambda,
 *       n.z / lambda )
 *
 * Applied to a lid normal (0, 0, +-1) this reduces to (-dT/dx, -dT/dy, +-1),
 * the exact normal of the sheet z = +-T(x, y); applied to a rim normal it tilts
 * the wall by however fast the section is thinning there. Calling
 * computeVertexNormals after the warp instead would re-flatten everything the
 * subdivision was for, and shatter the smoothed rim back into facets.
 */
function warpedExtrude(outline: THREE.Vector2[], lidLevels: number): THREE.BufferGeometry {
  const shape = new THREE.Shape(outline);
  const g = new THREE.ExtrudeGeometry(shape, {
    depth: 2 * (Z_NOMINAL - BEVEL_THICKNESS),
    bevelEnabled: true,
    bevelThickness: BEVEL_THICKNESS,
    bevelSize: BEVEL_SIZE,
    bevelOffset: BEVEL_OFFSET,
    bevelSegments: 2,
    steps: 1,
    curveSegments: 1,
  });

  g.computeBoundingBox();
  const bb = g.boundingBox;
  g.translate(0, 0, -0.5 * (bb.min.z + bb.max.z));
  const zMax = 0.5 * (bb.max.z - bb.min.z);

  smoothNormals(g, 60);

  // Group 0 is the lids, group 1 the side walls (three.js ExtrudeGeometry).
  // That split is already the `groupByFacing()` bucketing the Talon demo does by
  // hand, so it is used rather than re-derived from normals.
  const lidGroup = g.groups.find((x) => x.materialIndex === 0);
  const sideGroup = g.groups.find((x) => x.materialIndex === 1);
  const tris = [
    ...subdivide(readTriangles(g, lidGroup.start, lidGroup.count), lidLevels),
    ...readTriangles(g, sideGroup.start, sideGroup.count),
  ];
  g.dispose();

  const n = tris.length * 3;
  const pos = new Float32Array(n * 3);
  const nrm = new Float32Array(n * 3);
  const uv = new Float32Array(n * 2);
  const EPS = 1e-4;
  const v = new THREE.Vector3();
  let w = 0;
  for (const t of tris) {
    for (let k = 0; k < 3; k++) {
      const x = t.p[k * 3];
      const y = t.p[k * 3 + 1];
      const z = t.p[k * 3 + 2];
      const T = halfThickness(x, y);
      const lam = T / zMax;
      const dlx = (halfThickness(x + EPS, y) - halfThickness(x - EPS, y)) / (2 * EPS * zMax);
      const dly = (halfThickness(x, y + EPS) - halfThickness(x, y - EPS)) / (2 * EPS * zMax);

      pos[w * 3] = x; pos[w * 3 + 1] = y; pos[w * 3 + 2] = z * lam;

      const nz = t.n[k * 3 + 2];
      v.set(
        t.n[k * 3] - nz * z * dlx / lam,
        t.n[k * 3 + 1] - nz * z * dly / lam,
        nz / lam,
      ).normalize();
      nrm[w * 3] = v.x; nrm[w * 3 + 1] = v.y; nrm[w * 3 + 2] = v.z;

      uv[w * 2] = t.uv[k * 2]; uv[w * 2 + 1] = t.uv[k * 2 + 1];
      w++;
    }
  }

  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.translate(ROOT_X, ROOT_Y, 0);   // planar -> model frame, once, at the end
  out.computeBoundingBox();
  out.computeBoundingSphere();
  return out;
}

// ---------------------------------------------------------------------------
// Materials, from §6.10 / §11.2 CIE Lab, converted once
// ---------------------------------------------------------------------------

/**
 * `grip.body`  Lab (28.2, +6.48, +11.44) -> #523f31. Hue 60.5 deg, chroma 13.1.
 *              The audit's 388-pixel unoccluded lateral face (D-1).
 * `butt-cap`   Lab (35.2, -0.96, -7.35) -> #4b545e. Matches `mat.paint.tube.ab`'s
 *              (-1.5, -7.0) to within 0.6 a* / 0.4 b*, which is the whole reason
 *              the butt cap gets the frame's material and the body does not.
 * `toe-stud`   `mat.brass.aged.hue` 66.5 +- 5 deg at chroma 20 -> #82654c. L* 45
 *              is DECLARED: §6.10 gives brass a hue and a chroma and no lightness.
 */
const LAB_TO_SRGB = {
  gripBody: 0x523f31,
  buttCap: 0x4b545e,
  toeStud: 0x82654c,
};

/**
 * Neutral, lightness-only grain. DataTexture rather than a canvas so the module
 * builds identically in the headless render harness, where there is no document.
 * Mean 0.985 with +-3.5 % swing: a* and b* come out of the material colour and
 * the map does not move them, which is what §6.10's "hue and chroma, not
 * lightness" rule asks of any generated finish.
 */
function grainMap(): THREE.DataTexture {
  const W = 48;
  const H = 256;
  const data = new Uint8Array(W * H * 4);
  const hash = (x: number, y: number) => {
    const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  const value = (x: number, y: number) => {
    const xi = Math.floor(x); const yi = Math.floor(y);
    const xf = x - xi; const yf = y - yi;
    const u = xf * xf * (3 - 2 * xf);
    const v = yf * yf * (3 - 2 * yf);
    return THREE.MathUtils.lerp(
      THREE.MathUtils.lerp(hash(xi, yi), hash(xi + 1, yi), u),
      THREE.MathUtils.lerp(hash(xi, yi + 1), hash(xi + 1, yi + 1), u), v);
  };
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      // Anisotropic: the grain runs along the grip, so v is sampled ~6x finer.
      let a = 0;
      let amp = 1;
      let f = 1;
      for (let o = 0; o < 3; o++) {
        a += amp * (value(x / W * 5 * f, y / H * 30 * f) - 0.5);
        amp *= 0.5; f *= 2.1;
      }
      const c = Math.round(255 * THREE.MathUtils.clamp(0.985 + a * 0.07, 0, 1));
      const i = (y * W + x) * 4;
      data[i] = c; data[i + 1] = c; data[i + 2] = c; data[i + 3] = 255;
    }
  }
  const tex = new THREE.DataTexture(data, W, H);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  // Extrude UVs are world metres; this puts roughly one grain period across the
  // grip's depth and a long stretch down its length.
  tex.repeat.set(1 / (0.9 * D), 1 / (2.4 * D));
  return tex;
}

/**
 * Roughness and metalness are DECLARED throughout: §10.7 item 26 says no PBR
 * parameter is recoverable from a hand-painted, stylised source whose highlights
 * are 2-6 px. Metalness stays low even on the brass stud, and that is the Talon
 * demo's lesson carried across: high metalness replaces diffuse with neutral
 * environment reflection, and the measured (a*, b*) — the only thing that
 * survives the ban on projecting the reference — would be the first casualty.
 */
function materials() {
  const body = new THREE.MeshStandardMaterial({
    name: 'mat.grip.warm',
    color: new THREE.Color(LAB_TO_SRGB.gripBody),
    roughness: 0.62,
    metalness: 0.0,
    map: grainMap(),
  });
  const cap = new THREE.MeshStandardMaterial({
    name: 'mat.paint.frame',
    color: new THREE.Color(LAB_TO_SRGB.buttCap),
    roughness: 0.48,
    metalness: 0.12,
  });
  const stud = new THREE.MeshStandardMaterial({
    name: 'mat.brass.aged',
    color: new THREE.Color(LAB_TO_SRGB.toeStud),
    roughness: 0.34,
    metalness: 0.18,
  });
  return { body, cap, stud };
}

// ---------------------------------------------------------------------------
// The toe stud
// ---------------------------------------------------------------------------

/**
 * `grip.butt.toeStud.count` = 1 +- 1, from one 2x3 px warm cluster at pose0
 * (168-169, 293-295) — the only warm pixels anywhere on the grip assembly before
 * the audit found the lateral face. The row's own evidence says a pin, a screw
 * and a chamfer highlight are indistinguishable at 3-4 mm, so this is DECLARED
 * as a domed pin head, seated on the toe fillet and facing out along the corner
 * bisector. Lathe, not a sphere: the Talon demo revolves its rivet domes, and a
 * revolve gives the flat seating collar that a sphere segment cannot.
 */
function buildToeStud(mat: THREE.Material): THREE.Mesh {
  const HEAD_R = 0.0018;
  const HEAD_H = 0.0009;
  const profile: THREE.Vector2[] = [];
  const SEGS = 7;
  for (let i = 0; i < SEGS; i++) {
    const a = (i / SEGS) * Math.PI * 0.5;
    profile.push(new THREE.Vector2(HEAD_R * Math.cos(a), HEAD_H * Math.sin(a)));
  }
  profile.push(new THREE.Vector2(0, HEAD_H));         // apex, exactly on the axis
  profile.unshift(new THREE.Vector2(HEAD_R, -0.0004)); // seating collar
  const geo = new THREE.LatheGeometry(profile, 24);
  // LatheGeometry has no pole case: for the *last* meridian point it reuses the
  // previous segment's raw, un-normalized normal. On a profile whose coordinates
  // are order 1 nobody notices; on a 1.8 mm stud the whole apex ring comes back
  // with normals of length 4e-4 and shades as a black dot on a lit dome.
  geo.normalizeNormals();

  // Seat it on the midpoint of the toe fillet itself, and take the outward
  // direction from that arc's own tangent, so the stud stays welded to the
  // surface if the fillet radius or the butt offsets ever move.
  const arc = toeArc();
  const seat = arc.p0.clone().multiplyScalar(0.25)
    .addScaledVector(arc.c, 0.5)
    .addScaledVector(arc.p2, 0.25);
  const tangent = arc.p2.clone().sub(arc.p0).normalize();
  const bis = new THREE.Vector2(tangent.y, -tangent.x);
  if (bis.dot(seat.clone().sub(planarOf(0, 0.8 * GRIP_LEN))) < 0) bis.negate();
  seat.add(new THREE.Vector2(ROOT_X, ROOT_Y));

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = PART.gripToeStud;
  mesh.position.set(seat.x, seat.y, 0);
  // Lathe builds about +Y; point it out along the toe bisector.
  mesh.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    new THREE.Vector3(bis.x, bis.y, 0),
  );
  return mesh;
}

// ---------------------------------------------------------------------------

/**
 * Build the grip assembly in the model frame (§2: origin at the breech face on
 * the bore axis, +X to the muzzle, +Y to the rail). Everything is already in
 * world coordinates; the meshes carry no transform of their own except the stud,
 * which is a revolve and has to be oriented.
 */
export function buildGrip(): THREE.Group {
  const mats = materials();

  const body = new THREE.Mesh(warpedExtrude(bodyOutline(), 2), mats.body);
  body.name = PART.gripBody;

  const cap = new THREE.Mesh(warpedExtrude(buttOutline(), 2), mats.cap);
  cap.name = PART.gripButt;

  // The tree parents the stud to the butt cap; both meshes are identity-placed,
  // so the parenting costs nothing and keeps the scene graph readable against §3.
  cap.add(buildToeStud(mats.stud));

  const group = new THREE.Group();
  group.name = PART.grip;
  group.add(body, cap);

  group.userData.contract = {
    satisfied: [
      'grip.rakeFromBore', 'grip.length.overTubeOd', 'grip.depth.overTubeOd',
      'grip.width.overTubeOd', 'grip.circumference.overTubeOd',
      'grip.butt.majorAxis.overTubeOd', 'grip.heelDrop.overTubeOd',
      'grip.butt.behindFrameHeel', 'grip.length.overHandBreadth',
      'grip.fingerCourse.count', 'grip.butt.toeStud.count',
    ],
    // Named here as well as in the header so a reader of the built scene, not
    // only a reader of this file, is told what was cut.
    failed: {
      'grip.root.flushWithFrame': 'second clause only — the grip footprint is NOT '
        + 'inside the frame\'s. D-11: it contradicts grip.butt.behindFrameHeel and '
        + 'the tree\'s u 1.000 butt, and §2 defines u = 1 as the butt rear. The '
        + 'gap <= 0.03 D clause is satisfied at up = -0.62 D.',
      'tree:grip u 0.808 front': 'the front strap\'s root reaches u 0.751. Rake '
        + '107 deg over 1.55 D plus a 0.84 D section cannot fit the 1.071 D the '
        + 'tree allots. Occluded by the hand in every view.',
      'mat.grip.notWood': 'deliberately false for grip.body, per audit D-1. Held '
        + 'for grip.butt-cap, which does match the frame paint.',
    },
    // `grip.rakeFromBore`'s stated check — "grip AABB top-face centre minus
    // bottom-face centre" — is degenerate: on an axis-aligned box that vector is
    // always straight down, i.e. 90 deg, which fails 107 +- 10 for every grip
    // that could ever be built. Measured on the built mesh instead: the profile's
    // analytic centre line reads 108.0 deg and root-centre to butt-centre 107.6,
    // both inside tolerance; a PCA of the mesh vertices reads 118.0 and a
    // vertex-weighted section spine 116.5, because both are pulled by the
    // section's own 0.84 D depth and by tessellation density. That 28-degree
    // spread is a property of the estimators, not of the model — the constructed
    // centre line is 107 exactly.
    rakeEstimators: {
      analyticCentreLine: 108.0, rootCentreToButtCentre: 107.6,
      meshPCA: 118.0, vertexWeightedSpine: 116.5, statedAabbCheck: 90.0,
    },
    declared: [
      'section shape (superellipse n = 2.6) and rim fraction — §10.7 item 7',
      'no finger grooves — front-strap curvature is unmeasurable, declined not invented',
      'width 0.47 D kept at the contract\'s own DECLARED value, confidence 0.25',
      'root plane at up = -0.62 D, forced by heelDrop + length + rake',
      'roughness / metalness — §10.7 item 26',
      'grain map, +-3.5 %, neutral: lightness only, no chromaticity claim',
      'toe stud modelled as a domed pin at 3.6 mm',
    ],
  };

  return group;
}
