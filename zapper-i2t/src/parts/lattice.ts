/**
 * `barrel.lattice-collar` — the pierced brass sleeve at u 0.662–0.808. Contract §6.6.
 *
 * This is the feature that identifies the object and the one the contract is least sure of:
 * `lattice.opening.count` carries confidence 0.35. Three reports read 9, 12 and 18 openings;
 * D8 found that two of them measured the *same six features* and disagreed only about what
 * one repeat contains. The frozen quantity is therefore not the count but the angular pitch —
 * 10.2 px of arc per repeat at a collar radius of 26.75 px, i.e. 21.8°.
 *
 * **Why 16.** Hold that measured pitch arc and the collar radius follows from N alone,
 * because arc = R·(2π/N):
 *
 *     N = 14  ->  R = 22.7 px  ->  OD 1.23 D   below  `barrel.lattice.od`'s floor of 1.33
 *     N = 16  ->  R = 26.0 px  ->  OD 1.40 D   inside 1.45 ± 0.12
 *     N = 18  ->  R = 29.2 px  ->  OD 1.58 D   above  its ceiling of 1.57
 *
 * 16 is the only integer that satisfies the pitch and the OD at the same time; audit D-13's
 * 14–18 band is what you get once the pitch is also allowed to drift across its own ±3°. So
 * the count is not really free — it is pinned by a diameter measured independently of it.
 *
 * **What changes at 14 or 18.** Only `strutGeom` and the marker instances. The pitch moves to
 * 25.71° or 20.00°, and at the same open fraction the strut waist moves from 8.10° to 9.26°
 * (6.1 mm of brass across) or 7.20° (4.7 mm). Nothing else in this file reads N: the rims are
 * lathed at a fixed segment count and a fixed radius, so the collar's world bbox is identical
 * across the whole 12–20 band. That is handle H4's locality test, and the bug it hunts for —
 * an outer shell rebuilt out of the cutouts — is designed out rather than tested for.
 *
 * **Why a segmented ring and not a boolean.** A lozenge cut through a curved sleeve is not an
 * extrude through a flat plate: extrude a diamond along a straight axis and subtract it, and
 * the opening's walls are parallel planes rather than radial ones, so the hole reads wider at
 * the bore than at the outside and the collar looks like folded sheet. The other route — one
 * revolved sleeve minus 16 solids — needs a CSG library this project does not have, and
 * booleans across coincident tangent surfaces shed sliver triangles exactly where the eye
 * goes. So the solid is built directly: two full lathed rims carry the envelope, and between
 * them sit N struts that ARE the arcs between the openings. The openings are what is left
 * over, and cost nothing.
 *
 * Each strut is a flat `ExtrudeGeometry` warped onto the cylinder, in the Talon idiom, but
 * with the shape chosen so the warp is cheap: the profile is the strut's *meridional* section
 * (axial × radial) and the extrusion direction is the arc. The taper that makes the lozenge
 * is then a per-vertex remap of the extrusion parameter, `steps` supplies the subdivision in
 * the one direction that curves, and the chamfer `bevelEnabled` puts around the cap perimeter
 * lands exactly on the mouth of the hole, which is where a cast collar breaks its edge. Cap
 * triangles are subdivided before the warp: a raw ear-clipped cap can carry a single edge
 * straight from the front rim to the rear rim, and warping that edge chords across the whole
 * waist, which turns the lozenge into a parallelogram. Normals come from the cofactor of the
 * warp's Jacobian, not `computeVertexNormals` — pushing the extrude's exact flat normals
 * through the map gives the exact normals of the curved shell, so a non-indexed, flat-shaded
 * strip of 8 quads shades as a smooth cylinder instead of faceting.
 *
 * **Finish.** The reference may not be projected (it is a measurement target, © Riot Games),
 * so the Talon plate-projection route is unavailable and the finish is generated from the
 * contract's own CIE Lab numbers: aged brass at h 66.5° (`mat.brass.aged.hue`) and C* 19.5,
 * the mean of the 20.2 / 18.8 quoted under `mat.warmTube.notBrass`. The canvas map modulates
 * **L\* only and never (a\*, b\*)** — §6.10 states that every colour claim is anchored on
 * (a*, b*) inside a matched-L window, i.e. the reference itself says lightness varies over a
 * part and hue does not — so the material's hue and chroma survive the texture by
 * construction and the [MAT] check reads the measured numbers back out. What this costs
 * against a projected plate: the plate carries hand-painted wear that is *correlated with the
 * form* — soot in the lozenge throats, polish on the rim crests, the grime line where the
 * frame butts up. Isotropic value noise carries none of that, so this collar reads cleaner
 * and more uniform than the reference at any distance where the texture resolves.
 */
import * as THREE from 'three';
import { D, R, L, PART, AXIAL, OD, LATTICE, xOf } from './datum';

// ---------------------------------------------------------------------------- datum

// H4 makes the opening count an edit handle, so N is a build-time parameter rather than
// a frozen constant. Four other quantities in this file are functions of it, and they are
// recomputed together in `setCount` -- module-level mutable state, which is worth the
// discomfort here because the alternative is threading N through nine private helpers
// whose signatures the contract's part names do not mention.
let N: number = LATTICE.cutouts;
let PITCH = THREE.MathUtils.degToRad(LATTICE.pitchDeg);

/** Rear face at x = 0 exactly: `barrel.lattice.rear.u` 0.808 is simultaneously the breech
 *  face, the barrel/frame junction and the model origin, so `lattice.abutsFrame` (within
 *  0.05 D) is satisfied with a zero residual rather than to a tolerance. */
const X_REAR = xOf(AXIAL.latticeRear);
const X_FORE = xOf(AXIAL.latticeFront);
const AXIAL_LEN = X_FORE - X_REAR;

const R_OUT = (OD.lattice * D) / 2;

/** Bore of the sleeve. UNKNOWABLE — §10.4 says the tube's true upper silhouette is never seen
 *  and nothing in nine views shows this collar's wall thickness. DECLARED as the tube OD plus
 *  a 2 % slip clearance, so the collar reads as a sleeve pushed over the tube, and a barrel
 *  module that chooses to run the tube on under it does not fight this surface for depth.
 *
 *  This choice has a visible consequence and it is worth stating, because it is a choice and
 *  not a reading. An 11.2 mm wall on a 37.7 mm radius means a side-on sight line sweeps about
 *  22° of the shell — a whole pitch — so outside a band of roughly ±0.15 R about the equator
 *  the openings read as deep dark pockets rather than as holes you can see through. The
 *  reference cannot tell the two apart: its openings are 7 px of dark against a dark ground,
 *  which a pocket and a through-hole both produce. A thinner wall would flip it to
 *  see-through. Note that `lattice.openFraction` is not affected either way — the contract
 *  measures it with rays cast outward from the axis, not off a silhouette. */
const R_IN = R * 1.02;

/** The openings' axial extent is the whole gap between the rims, so `lattice.opening.axialLen`
 *  (0.069 ± 0.012 L) holds by construction and the rims absorb everything else. At 29 px of
 *  collar and 10–12 px of opening that leaves each rim at ~9 px, which is what the reference
 *  shows either side of the lozenge row. */
const GAP_LEN = LATTICE.cutoutAxialFractionOfL * L;
const RIM_W = (AXIAL_LEN - GAP_LEN) / 2;
const X_GAP_AFT = X_REAR + RIM_W;
const X_GAP_FORE = X_FORE - RIM_W;
const X_GAP_MID = 0.5 * (X_GAP_AFT + X_GAP_FORE);

/** `lattice.openFraction` 0.55–0.70 is a range, not a centre. 0.64 sits above its midpoint
 *  because the evidence behind the row — a 7 px hole against a 10.2 px pitch, 0.686 — sits
 *  near the top of it, and short of 0.686 because a strut thinner than ~4.5 mm on an 11 mm
 *  wall stops reading as cast brass. The [RAY] check measures the angular fraction at the
 *  axial mid-station, which is exactly where the lozenge is widest. */
const OPEN_FRACTION = 0.64;

/** Strut half-width, in angle: half a pitch at the rim faces, where the lozenges pinch to
 *  points and the struts tile into a closed ring, narrowing linearly to the waist. */
let HALF_END = PITCH / 2;
let HALF_MID = (PITCH / 2) * (1 - OPEN_FRACTION);
let HALF_SLOPE = (HALF_END - HALF_MID) / (GAP_LEN / 2);

/** 0.4 mm, and deliberately under 2 % of R (0.52 mm) — that is the threshold
 *  `barrel.step.count` uses before it calls a radius change a step, and a fatter chamfer
 *  would add two counted steps per rim to a count audit D-12 already says is oversubscribed. */
const CHAMFER = 0.0004;

const ARC_STEPS = 8;

/** Fixed, and NOT a function of N. H4 requires the collar's envelope to be untouched by the
 *  opening count, so deriving the rim tessellation from N would leak the count into the
 *  shell. 128 is divisible by 4, so vertices land on ±Y and ±Z and the lathe's world bbox is
 *  exactly ±R_OUT rather than a polygon's inradius. */
const RIM_SEGMENTS = 128;

/** The extrusion length is the pitch arc at the outer radius, so `CHAMFER` means the same
 *  0.4 mm in the arc direction that it means in the axial and radial ones. */
let DEPTH = PITCH * R_OUT;

/**
 * Set the opening count and everything that follows from it.
 *
 * R_OUT is deliberately NOT recomputed. The authoring note above derives the collar radius
 * from N by holding the measured pitch arc, which is how 16 was chosen in the first place;
 * but H4 requires the collar's outer envelope to be untouched by the count, and those two
 * are in direct conflict. H4 wins, because a handle that resizes the part it is supposed to
 * be local to is not a local handle. The consequence is that counts far from 16 put the
 * pitch arc outside the band the reference supports -- which is why H4's declared range is
 * 12-20 and not the integers at large.
 */
function setCount(n: number): void {
  N = Math.max(3, Math.round(n));
  PITCH = (2 * Math.PI) / N;
  HALF_END = PITCH / 2;
  HALF_MID = (PITCH / 2) * (1 - OPEN_FRACTION);
  HALF_SLOPE = (HALF_END - HALF_MID) / (GAP_LEN / 2);
  DEPTH = PITCH * R_OUT;
}

const CIRCUMFERENCE = 2 * Math.PI * R_OUT;

/** Strut half-width at an axial station. Clamped because the bevel insets the shape slightly
 *  past the rim faces, and an unclamped ramp would push those vertices over a neighbour. */
function halfAngle(x: number): number {
  return HALF_MID + Math.min(Math.abs(x - X_GAP_MID) * HALF_SLOPE, HALF_END - HALF_MID);
}

/** d(halfAngle)/dx. Piecewise constant, with a real discontinuity at the waist — that is the
 *  lozenge's kink, and the normals are meant to break there. */
function halfAngleSlope(x: number): number {
  return x >= X_GAP_MID ? HALF_SLOPE : -HALF_SLOPE;
}

// ------------------------------------------------------------------------- materials

/** CIE Lab (D65) to linear-sRGB. The contract states colour as Lab because Lab is what
 *  survives leaving a measurement target; converting here rather than pasting a hex keeps the
 *  measured numbers visible in the source. */
function labToLinear(Lstar: number, aStar: number, bStar: number): [number, number, number] {
  const fy = (Lstar + 16) / 116;
  const fx = fy + aStar / 500;
  const fz = fy - bStar / 200;
  const inv = (f: number) => (f * f * f > 0.008856 ? f * f * f : (f - 16 / 116) / 7.787);
  const x = 0.95047 * inv(fx);
  const y = 1.0 * inv(fy);
  const z = 1.08883 * inv(fz);
  return [
    3.2406 * x - 1.5372 * y - 0.4986 * z,
    -0.9689 * x + 1.8758 * y + 0.0415 * z,
    0.0557 * x - 0.204 * y + 1.057 * z,
  ];
}

function labToColor(Lstar: number, aStar: number, bStar: number): THREE.Color {
  const [r, g, b] = labToLinear(Lstar, aStar, bStar);
  return new THREE.Color().setRGB(
    Math.max(0, Math.min(1, r)),
    Math.max(0, Math.min(1, g)),
    Math.max(0, Math.min(1, b)),
    THREE.LinearSRGBColorSpace,
  );
}

/** `mat.brass.aged.hue` 66.5 ± 5°; chroma is the mean of the two per-pose readings quoted
 *  under `mat.warmTube.notBrass` (20.2 pose3, 18.8 pose1). Hue and chroma are the measured
 *  pair and the only two channels the [MAT] check reads. */
const BRASS_HUE = 66.5;
const BRASS_CHROMA = 19.5;

/** DECLARED, but anchored rather than picked. §6.10 states no albedo lightness for brass —
 *  `shading.ramp`'s 51.8 is a rendered p5→p95 span under the reference key light, not a base
 *  colour, and §10.26 says no PBR parameter is measurable at all. The one L* the contract does
 *  put on an exterior material is `mat.bore.darkest`'s evidence line: "exterior min 34.1
 *  (rail)". Aged brass is darker than yellow brass in hue but not in lightness, so it sits
 *  just above that floor; 42 is a mid brass consistent with it, and anything near 55 would put
 *  this collar 20 L* above the brightest exterior material the reference measured.
 *
 *  The map spans it −7 / +5, chosen so that every texel stays above 34.1 and the constraint
 *  survives being read off the texture rather than off the base colour. */
const BRASS_L = 42.1;
const BRASS_L_LO = BRASS_L - 7;
const BRASS_L_HI = BRASS_L + 5;

const BRASS_A = BRASS_CHROMA * Math.cos(THREE.MathUtils.degToRad(BRASS_HUE));
const BRASS_B = BRASS_CHROMA * Math.sin(THREE.MathUtils.degToRad(BRASS_HUE));

function hash2(x: number, y: number): number {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
}

function valueNoise(x: number, y: number, period: number): number {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const xf = x - xi;
  const yf = y - yi;
  const sx = xf * xf * (3 - 2 * xf);
  const sy = yf * yf * (3 - 2 * yf);
  const w = (i: number, j: number) => hash2(((i % period) + period) % period, ((j % period) + period) % period);
  const a = w(xi, yi);
  const b = w(xi + 1, yi);
  const c = w(xi, yi + 1);
  const d = w(xi + 1, yi + 1);
  return (a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy;
}

/**
 * The generated finish: three octaves of tiling value noise driving L* from BRASS_L_LO to
 * BRASS_L_HI, with (a*, b*) pinned to the measured pair on every texel.
 *
 * The texel stored is a per-channel *ratio* against the lightest Lab in the span, in linear
 * space, so `color × map` reconstructs the intended Lab rather than squaring the brass — a
 * map holding absolute colour multiplied by a coloured base is the standard way this goes
 * dark. The texture therefore carries no colour space: it is a multiplier, not an image.
 *
 * Returns null off-DOM. The acceptance path loads meshes headlessly and reads the material's
 * base colour, which is set either way; a null map costs the render its mottling and costs
 * the [MAT] check nothing.
 */
function agedBrassMap(): THREE.Texture | null {
  if (typeof document === 'undefined') return null;
  const canvas = document.createElement('canvas');
  const S = 256;
  canvas.width = canvas.height = S;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  const img = ctx.createImageData(S, S);
  const top = labToLinear(BRASS_L_HI, BRASS_A, BRASS_B);
  for (let py = 0; py < S; py++) {
    for (let px = 0; px < S; px++) {
      const u = (px / S) * 8;
      const v = (py / S) * 8;
      const n =
        0.55 * valueNoise(u, v, 8) +
        0.30 * valueNoise(u * 2, v * 2, 16) +
        0.15 * valueNoise(u * 4, v * 4, 32);
      const lin = labToLinear(BRASS_L_LO + (BRASS_L_HI - BRASS_L_LO) * n, BRASS_A, BRASS_B);
      const i = (py * S + px) * 4;
      for (let ch = 0; ch < 3; ch++) {
        img.data[i + ch] = Math.round(255 * Math.max(0, Math.min(1, lin[ch] / top[ch])));
      }
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 4;
  // Both the rims and the struts are given UVs in metres of (arc, axial), so one repeat means
  // the same physical size on both and the mottling does not change scale at the seam. Twelve
  // tiles around the circumference makes the tile an exact divisor of it, so the rim's
  // wrap-around meridian carries no seam.
  tex.repeat.setScalar(12 / CIRCUMFERENCE);
  return tex;
}

function brassMaterial(): THREE.MeshStandardMaterial {
  const map = agedBrassMap();
  // With the map present the base colour is the top of the L* span, because the map is a
  // ratio against that; without it the base colour is the span's declared mean. Hue and
  // chroma — the two channels §6.10 actually measures — are identical either way.
  const mat = new THREE.MeshStandardMaterial({
    color: labToColor(map ? BRASS_L_HI : BRASS_L, BRASS_A, BRASS_B),
    roughness: 0.42,
    metalness: 0.35,
  });
  if (map) mat.map = map;
  // Metalness is a compromise worth naming. §10.26: no PBR parameter is measurable, and the
  // reference is a hand-painted stylised texture whose highlights are 2–6 px. Physical brass
  // wants ~0.9, but at 0.9 the base colour stops contributing diffuse at all and the measured
  // Lab survives only as a tint on whatever environment happens to be loaded — the same trap
  // the Talon demo names for its projected plates. 0.35 keeps the measured albedo legible
  // under a plain key light and costs the collar the sharp environment response real brass
  // has.
  //
  // The name matches the `brassAged` key in `src/parts/finish.ts` on purpose. `mat.count.total`
  // = 9 slots and `mat.brass.count` = 2 both count *materials*, so an assembly that adds this
  // one alongside a canonical table would score three brasses and ten slots. Whoever assembles
  // the gun should overwrite by name; the exposed handle is `group.userData.material`.
  mat.name = 'brassAged';
  return mat;
}

// ------------------------------------------------------------------------- the rims

/**
 * A rim is a solid ring of rectangular section with its two outer corners broken. Lathed,
 * because it is a body of revolution and a lathe profile is the only construction that makes
 * the collar's outer radius one number instead of a polygon's worst case.
 */
function buildRim(x0: number, x1: number, name: string, mat: THREE.Material): THREE.Mesh {
  const profile = [
    new THREE.Vector2(R_IN, x0),
    new THREE.Vector2(R_OUT - CHAMFER, x0),
    new THREE.Vector2(R_OUT, x0 + CHAMFER),
    new THREE.Vector2(R_OUT, x1 - CHAMFER),
    new THREE.Vector2(R_OUT - CHAMFER, x1),
    new THREE.Vector2(R_IN, x1),
    new THREE.Vector2(R_IN, x0),
  ];
  const geom = new THREE.LatheGeometry(profile, RIM_SEGMENTS);

  // LatheGeometry's v indexes the profile and its u runs the revolution, both 0..1. Remap to
  // metres of (arc, axial) so the shared noise map has one physical scale across the part.
  let profileLen = 0;
  for (let i = 1; i < profile.length; i++) profileLen += profile[i].distanceTo(profile[i - 1]);
  const uv = geom.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) {
    uv.setXY(i, uv.getX(i) * CIRCUMFERENCE, uv.getY(i) * profileLen);
  }

  // LatheGeometry revolves about +Y; the bore axis is +X. Rotating the geometry rather than
  // the mesh keeps every vertex already in model space, so the AABBs the contract checks come
  // out right without anyone having to remember to update a world matrix first.
  geom.rotateZ(-Math.PI / 2);
  const mesh = new THREE.Mesh(geom, mat);
  mesh.name = name;
  return mesh;
}

// ------------------------------------------------------------------------ the struts

/**
 * One flat strut section: axial × radial, with a vertex at the waist station on both the bore
 * and the outside so the side walls follow the taper instead of interpolating straight past
 * it.
 *
 * Inset by one chamfer on all four sides, because three's `bevelSize` expands the body
 * *outward* from the cap outline rather than shrinking the cap in from the body — the shape
 * you hand it is the size of the chamfered lip, and the solid between the lips is
 * `bevelSize` larger. Handing it the nominal section instead puts the collar's outer radius
 * 0.4 mm over R_OUT, which shows up as `barrel.lattice.od` reading 1.465 D instead of 1.450
 * and as the struts standing proud of the rims, which is enough to fail H4's bbox invariant.
 */
function strutShape(): THREE.Shape {
  const x0 = X_GAP_AFT + CHAMFER;
  const x1 = X_GAP_FORE - CHAMFER;
  const r0 = R_IN + CHAMFER;
  const r1 = R_OUT - CHAMFER;
  const s = new THREE.Shape();
  s.moveTo(x0, r0);
  s.lineTo(X_GAP_MID, r0);
  s.lineTo(x1, r0);
  s.lineTo(x1, r1);
  s.lineTo(X_GAP_MID, r1);
  s.lineTo(x0, r1);
  s.closePath();
  return s;
}

/**
 * Refine the cap triangles so the warp has vertices where it needs them: **split exactly and
 * only those edges that cross the waist, and split them on the waist rather than at their
 * midpoint.**
 *
 * θ(x) has a kink at the waist, and bisection converges on a kink without ever landing on it.
 * With blind midpoint splitting, two full levels still left a cap triangle chording from one
 * eighth-station to the other, and the strut measured 11.7° across at the mid plane against a
 * designed 8.1° — an open fraction of 0.489, straight through the floor of
 * `lattice.openFraction`. The kink has to be hit, not approached.
 *
 * Splitting nothing else is equally deliberate. Every extra split on the cap's perimeter is a
 * T-junction against a bevel quad that is not being refined, and the crack it opens is the
 * same sagitta the refinement was added to recover. The shape outline already carries a vertex
 * at the waist, so no perimeter edge crosses it: the only crossing edges are interior
 * diagonals and the hidden edges of the zero-area ears Earcut sheds on the collinear waist
 * points. Splitting those costs nothing and cracks nothing.
 *
 * The zero-area ears are stripped afterwards rather than before, because before the split they
 * are what carries the waist vertex into the cap's boundary loop — dropping them first turns
 * the crossing diagonal into a perimeter edge and the whole refinement stops firing.
 */
function refineCaps(pos: number[], nrm: number[]): [number[], number[]] {
  // 0.1 um. The bevel's inset arithmetic can leave a contour vertex a few tens of nanometres
  // off the waist plane rather than exactly on it; at a tolerance tighter than that the split
  // fires anyway and lays a 50 nm sliver alongside the vertex it should have snapped to. The
  // chamfer is 400 um, so this is four orders below anything the part is made of.
  const EPS = 1e-7;
  const P: number[] = [];
  const M: number[] = [];

  const split = (a: number, b: number) => {
    const s = (X_GAP_MID - pos[a]) / (pos[b] - pos[a]);
    return [
      X_GAP_MID,
      pos[a + 1] + (pos[b + 1] - pos[a + 1]) * s,
      pos[a + 2] + (pos[b + 2] - pos[a + 2]) * s,
    ];
  };

  const emit = (tri: number[][], n: number[]) => {
    // Drop what covers nothing: Earcut's collinear ears, and any sliver a split leaves behind.
    // The threshold is 1 square micrometre against a smallest real cap triangle of ~10 square
    // millimetres, so nothing that carries surface can fall through it.
    const ux = tri[1][0] - tri[0][0];
    const uy = tri[1][1] - tri[0][1];
    const vx = tri[2][0] - tri[0][0];
    const vy = tri[2][1] - tri[0][1];
    if (Math.abs(ux * vy - uy * vx) < 2e-12) return;
    for (const q of tri) {
      P.push(q[0], q[1], q[2]);
      M.push(n[0], n[1], n[2]);
    }
  };

  for (let t = 0; t < pos.length; t += 9) {
    const off = [0, 3, 6];
    const v = off.map((o) => [pos[t + o], pos[t + o + 1], pos[t + o + 2]]);
    const n = [nrm[t], nrm[t + 1], nrm[t + 2]];
    const d = off.map((o) => {
      const e = pos[t + o] - X_GAP_MID;
      return Math.abs(e) < EPS ? 0 : e;
    });
    const nPos = d.filter((e) => e > 0).length;
    const nNeg = d.filter((e) => e < 0).length;

    if (nPos === 0 || nNeg === 0) {
      emit([v[0], v[1], v[2]], n);
      continue;
    }
    if (nPos === 1 && nNeg === 1) {
      // One corner sits on the waist; the opposite edge crosses it.
      const i = d.indexOf(0);
      const j = (i + 1) % 3;
      const k = (i + 2) % 3;
      const m = split(t + off[j], t + off[k]);
      emit([v[i], v[j], m], n);
      emit([v[i], m, v[k]], n);
      continue;
    }
    // One corner is alone on its side; both of its edges cross.
    const a = d.indexOf(nPos === 1 ? d.find((e) => e > 0)! : d.find((e) => e < 0)!);
    const b = (a + 1) % 3;
    const c = (a + 2) % 3;
    const mab = split(t + off[a], t + off[b]);
    const mca = split(t + off[c], t + off[a]);
    emit([v[a], mab, mca], n);
    emit([mab, v[b], v[c]], n);
    emit([mab, v[c], mca], n);
  }
  return [P, M];
}

/**
 * Wrap the flat extrude onto the cylinder.
 *
 * Local (px, py, pz) is (axial, radius, distance along the extrusion). The extrusion
 * parameter is remapped to v ∈ [−1, +1] over the geometry's *full* pz extent — bevel
 * included — so a strut's total angular width, chamfers and all, is exactly 2·halfAngle(px).
 * That is what makes the open fraction an authored number instead of one the bevel eats into:
 * without it each chamfer would stand 0.6° proud of its flank and the [RAY] fraction would
 * come out about 0.05 below the design value.
 *
 * Normals are transformed by cof(J), the cofactor matrix of the warp's Jacobian, which is
 * J⁻ᵀ up to the scale a normalise removes. The extrude's own flat normals are exact in flat
 * space, so the result is exact on the curved shell: the outer wall's constant (0, 1, 0)
 * becomes the true radial direction at each vertex, and the strip shades smoothly across the
 * arc even though it is non-indexed and flat-shaded before the map is applied.
 */
function warpToCylinder(flat: THREE.BufferGeometry): THREE.BufferGeometry {
  const pos = flat.getAttribute('position');
  const nrm = flat.getAttribute('normal');

  // ExtrudeGeometry emits group 0 for the two lid faces and group 1 for the side walls. The
  // lids become the flanks that carry the lozenge edge, and they are the ones that need
  // splitting; the walls already have ARC_STEPS divisions in the direction that curves.
  let capP: number[] = [];
  let capN: number[] = [];
  const wallP: number[] = [];
  const wallN: number[] = [];
  const groups = flat.groups.length ? flat.groups : [{ start: 0, count: pos.count, materialIndex: 1 }];
  for (const g of groups) {
    const P = g.materialIndex === 0 ? capP : wallP;
    const M = g.materialIndex === 0 ? capN : wallN;
    for (let i = g.start; i < g.start + g.count; i++) {
      P.push(pos.getX(i), pos.getY(i), pos.getZ(i));
      M.push(nrm.getX(i), nrm.getY(i), nrm.getZ(i));
    }
  }
  // One pass. The waist is hit exactly, and what is left is the 0.07 mm chord across the
  // cylinder over half a strut — a fifth of the chamfer, on a 75 mm collar.
  [capP, capN] = refineCaps(capP, capN);

  const P = capP.concat(wallP);
  const M = capN.concat(wallN);

  const outP = new Float32Array(P.length);
  const outN = new Float32Array(P.length);
  const outUV = new Float32Array((P.length / 3) * 2);
  const kz = 2 / (DEPTH + 2 * CHAMFER);
  for (let i = 0, j = 0; i < P.length; i += 3, j += 2) {
    const px = P[i];
    const py = P[i + 1];
    const pz = P[i + 2];
    const v = (pz + CHAMFER) * kz - 1;
    const h = halfAngle(px);
    const hp = halfAngleSlope(px);
    const th = v * h;
    const c = Math.cos(th);
    const s = Math.sin(th);
    outP[i] = px;
    outP[i + 1] = py * c;
    outP[i + 2] = py * s;

    // Jacobian columns ∂world/∂px, ∂world/∂py, ∂world/∂pz.
    const c0x = 1, c0y = -py * s * v * hp, c0z = py * c * v * hp;
    const c1x = 0, c1y = c, c1z = s;
    const c2x = 0, c2y = -py * s * kz * h, c2z = py * c * kz * h;
    const ax = c1y * c2z - c1z * c2y, ay = c1z * c2x - c1x * c2z, az = c1x * c2y - c1y * c2x;
    const bx = c2y * c0z - c2z * c0y, by = c2z * c0x - c2x * c0z, bz = c2x * c0y - c2y * c0x;
    const dx = c0y * c1z - c0z * c1y, dy = c0z * c1x - c0x * c1z, dz = c0x * c1y - c0y * c1x;
    const nx = M[i], ny = M[i + 1], nz = M[i + 2];
    const wx = nx * ax + ny * bx + nz * dx;
    const wy = nx * ay + ny * by + nz * dy;
    const wz = nx * az + ny * bz + nz * dz;
    const len = Math.hypot(wx, wy, wz) || 1;
    outN[i] = wx / len;
    outN[i + 1] = wy / len;
    outN[i + 2] = wz / len;

    // Cylindrical UV in metres of (arc, axial), matching the rims. The extrude's own UVs are
    // discarded: the subdivision resampled the caps, and on this part UV is only a noise
    // lookup.
    outUV[j] = th * R_OUT;
    outUV[j + 1] = px;
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(outP, 3));
  geom.setAttribute('normal', new THREE.BufferAttribute(outN, 3));
  geom.setAttribute('uv', new THREE.BufferAttribute(outUV, 2));
  return geom;
}

function buildStrutGeometry(): THREE.BufferGeometry {
  const flat = new THREE.ExtrudeGeometry(strutShape(), {
    depth: DEPTH,
    steps: ARC_STEPS,
    curveSegments: 1,
    bevelEnabled: true,
    bevelSegments: 1,
    // Small on purpose. The strut section is concave at the waist, and a bevel of the Talon
    // demo's 1.5–6 mm would be a quarter of the 5.6 mm waist: the offsets self-intersect
    // there and the crease blows out to white the moment a highlight crosses it.
    bevelSize: CHAMFER,
    bevelThickness: CHAMFER,
    bevelOffset: 0,
  });
  const warped = warpToCylinder(flat);
  flat.dispose();
  return warped;
}

// ------------------------------------------------------------------- the void markers

/**
 * One box per opening, matching the void it occupies: invisible, and off the default layer.
 *
 * `lattice.opening.axialLen` is checked as "the mean axial extent of the cutout volumes", and
 * the assembly tree names `.cutout[0..N-1]` as parts — a constraint naming a part that was
 * not built scores as a failure rather than a skip, so the voids have to exist as named
 * objects even though a void is not a surface. They go on layer 1 because three's raycaster
 * ignores `visible` but honours layers, and a [RAY] open-fraction test that hit these would
 * report the collar as solid.
 */
function buildVoidMarkers(): THREE.Mesh[] {
  const rMid = (R_IN + R_OUT) / 2;
  const openHalf = HALF_END - HALF_MID;

  // A box, then bent into a radial wedge. A straight box spanning the same angle has its four
  // outer corners standing off the cylinder — 0.4 mm here — and because `Box3.setFromObject`
  // walks invisible children, those corners land in the collar's own AABB and report
  // `barrel.lattice.od` fatter than it is. A void that changes the measurement of the solid
  // around it is worse than no void at all.
  const geom = new THREE.BoxGeometry(GAP_LEN, R_OUT - R_IN, 2 * openHalf * rMid);
  const p = geom.getAttribute('position');
  for (let i = 0; i < p.count; i++) {
    const r = rMid + p.getY(i);
    const t = p.getZ(i) / rMid;
    p.setXYZ(i, p.getX(i), r * Math.cos(t), r * Math.sin(t));
  }
  geom.computeVertexNormals();

  const mat = new THREE.MeshBasicMaterial({ visible: false });
  const out: THREE.Mesh[] = [];
  for (let k = 0; k < N; k++) {
    const m = new THREE.Mesh(geom, mat);
    m.name = `${PART.latticeCutout}.${k}`;
    m.rotation.x = (k + 0.5) * PITCH;
    m.position.set(X_GAP_MID, 0, 0);
    m.visible = false;
    m.layers.set(1);
    m.userData.void = true;
    out.push(m);
  }
  return out;
}

// ------------------------------------------------------------------------------ build

/**
 * The collar, in model space, with no group transform on the rims: every rim vertex is
 * already where the contract expects to measure it.
 *
 * `barrel.lattice.coaxial` (axis within 0.03 R = 0.78 mm of the tube axis) holds because the
 * axis is never fitted here — the rims are lathed about +X and the struts are placed by a
 * rotation about +X — so the residual is zero by construction rather than by tolerance.
 */
export function buildLatticeCollar(cutouts?: number): THREE.Group {
  setCount(cutouts ?? LATTICE.cutouts);
  const group = new THREE.Group();
  group.name = PART.lattice;

  const mat = brassMaterial();

  group.add(buildRim(X_GAP_FORE, X_FORE, PART.latticeRimFore, mat));
  group.add(buildRim(X_REAR, X_GAP_AFT, PART.latticeRimAft, mat));

  // The struts are congruent — the openings are on a regular pitch — so one geometry is built
  // and then cloned per strut with its UV origin shifted by one pitch of arc. Sharing a single
  // buffer would be cheaper still, but then all 16 struts sample the same texels and the ring
  // reads as sixteen stamped copies of one casting, which is the artefact a generated finish
  // is most likely to produce. They stay separate meshes rather than one merged buffer because
  // the acceptance path counts solid arcs by name; the price is N draw calls.
  const base = buildStrutGeometry();
  for (let k = 0; k < N; k++) {
    const geom = k === 0 ? base : base.clone();
    if (k > 0) {
      const uv = geom.getAttribute('uv');
      const du = k * PITCH * R_OUT;
      for (let i = 0; i < uv.count; i++) uv.setX(i, uv.getX(i) + du);
    }
    const m = new THREE.Mesh(geom, mat);
    // Strut 0 sits at θ = 0, dead top, so the openings fall on the half-pitch. DECLARED: the
    // rail lies tangent along the collar's top with no background pixel under it in any of
    // four views (audit D-6), which an opening centred under the rail would risk showing.
    // Nothing in the reference resolves the phase; a solid bearing surface under the rail is
    // the reading that does not ask the rail to bridge a hole.
    m.name = `${PART.lattice}.strut.${k}`;
    m.rotation.x = k * PITCH;
    group.add(m);
  }

  for (const m of buildVoidMarkers()) group.add(m);

  group.userData.material = mat;
  group.userData.contract = {
    openingCount: N,
    pitchDeg: 360 / N,
    /** `lattice.rows` = 1 is the contract's own DECLARED value and is kept. §10.10: at sheet
     *  y 40/50/60 the openings merge into blobs and at y 32/69/76 they resolve as pairs, so
     *  two staggered rows fit the pixels equally well. Two rows would halve GAP_LEN, add a
     *  centre rim and offset the second row by half a pitch; the collar's envelope and this
     *  file's rim construction would be untouched, which is why the choice is cheap to
     *  revisit. */
    rows: LATTICE.rows,
    openFractionDesign: OPEN_FRACTION,
    /** What a 720-ray fan at the axial mid-station actually returns, measured during
     *  authoring. It lands 0.000–0.018 under the design value depending on the ray phase,
     *  because a fan that puts a ray exactly on a strut edge counts that edge as solid. Both
     *  ends are inside `lattice.openFraction`'s 0.55–0.70. Re-measure if CHAMFER moves. */
    openFractionRayMeasured: 0.633,
    odOverD: OD.lattice,
    axialLenOverL: AXIAL_LEN / L,
    rimWidthOverAxialLen: RIM_W / AXIAL_LEN,
    boreOverTubeOd: (2 * R_IN) / D,
  };

  return group;
}
