/**
 * The barrel, built as ONE silhouette put on a lathe and then cut into named meshes.
 *
 * The Talon demo's hard surface is extrudes because a knife blade is a plate. This
 * object is the opposite case: from the muzzle to the lattice's forward face the gun
 * is a pure body of revolution, so the honest primitive is a profile in (x, r) revolved
 * about +X. Everything the contract measures over that span -- `barrel.tube.constantOd`,
 * `barrel.midBand.od`, `muzzle.ring.count`, `barrel.bore.dOverLinerOd` -- is a statement
 * about that one profile, so building the parts as separate primitives stacked on an
 * axis would let two of them disagree about where the surface is. Here they cannot:
 * `tube-fore` and `tube-aft` are literally two spans of the same polyline, which is why
 * their radii are equal to the last bit rather than to five decimal places.
 *
 * Three constructions are deliberate and each avoids a specific artefact:
 *
 * 1. ONE profile, SPLIT BY SPAN. Consecutive named meshes share their boundary ring
 *    vertex-for-vertex, so there is no hairline crack at a part seam and no z-fighting
 *    from a collar "ring" modelled as a torus sunk into a cylinder. The mid-band is not
 *    a separate ring sitting on the tube -- it is the part of the profile that bulges.
 *
 * 2. ANALYTIC NORMALS from the profile tangent, never `computeVertexNormals()`. A lathe
 *    built by three's own `LatheGeometry` and then vertex-normalled averages across the
 *    90-degree corner at the collar's rear step, which softens the sharpest edge on the
 *    object into a 3 mm smear -- and that edge is `barrel.muzzleCollar.step.u`, the
 *    highest-confidence axial landmark in the whole contract. Emitting each segment with
 *    its own exact normal keeps every corner a corner and every cylinder perfectly smooth
 *    at the same time.
 *
 * 3. SMALL CHAMFERS, clamped. Every corner of the profile is broken by a 0.3 mm flat --
 *    a tenth of the shallowest feature and 0.006 D, which is a fifth of a pixel in the
 *    reference sheet, so it invents nothing the reference could have resolved. It exists
 *    because a perfectly sharp revolved edge on brass renders as an aliased white thread
 *    that crawls when the camera moves. Following the Talon note about bevels spiking on
 *    concave corners, each chamfer is clamped to 0.4 of the shorter adjoining edge, so
 *    the two chamfers on the 3.5 mm groove floor can never meet and invert it.
 *
 * FINISH. The reference may not be projected (see the module brief), so every colour
 * here is reconstructed from the contract's measured CIE Lab values in Section 6.10 and
 * the mottling is canvas-drawn. What that costs against Talon's projected de-lit plates
 * is specific and worth naming: the projection carries the painter's *spatial* decisions
 * -- where the wear sits, which edge got rubbed, the hand-placed graffiti -- and a noise
 * field carries none of them. So this finish can be right about hue, chroma and the
 * warm/cool ordering (which is what Section 6.10 actually measures, and what a check can
 * falsify) and will be wrong about placement (which Section 6.11 says is unmeasurable
 * per-object anyway, because no clean orthographic view of either face exists). The
 * trade is: correct where the contract can score it, generic where it cannot.
 *
 * WHAT THIS MODULE DELIBERATELY FAILS is recorded at the bottom of the file, next to the
 * numbers that force each failure. Read it before assuming a mismatch is a bug.
 */
import * as THREE from 'three';
import { D, R, L, PART, AXIAL, OD, MUZZLE, xOf } from './datum.js';

/** A profile vertex in the (x, radius) half-plane that gets revolved about +X. */
type Pt = { x: number; r: number };

// ---------------------------------------------------------------------------
// Tessellation
// ---------------------------------------------------------------------------

/**
 * 64 spokes.
 *
 * The target render is the gun at ~800 px overall, i.e. 800 px across A = 290 mm, or
 * 2759 px/m. The widest thing on this profile is the mid-band at 1.18 D, radius 84.6 px
 * at that scale, and an inscribed N-gon's silhouette sags by r(1 - cos(pi/N)): at N = 64
 * that is 0.10 px. A tenth of a pixel is an order of magnitude under the point where a
 * silhouette reads as faceted, and because the normals are analytic rather than averaged
 * the *shading* is smooth at any N -- only the outline needed the budget.
 *
 * 64 rather than 60 for two reasons that cost nothing. It is 4 x 16, so a ring vertex
 * lands on every one of the lattice's 16 cutout centres (`LATTICE.pitchDeg` = 22.5) and
 * the two modules' silhouettes cannot beat against each other. And it is divisible by 4,
 * so vertices sit exactly on +-Y and +-Z: the AABB is isotropic to machine precision,
 * which is what `barrel.tube.circular` measures (Y-extent = Z-extent within 4 %). An odd
 * or 4-indivisible count makes that ratio cos(pi/N) by construction -- a free 0.2 % error
 * on a constraint that did not have to be spent.
 */
const RADIAL_SEGMENTS = 64;

/** 0.3 mm. 0.006 D; 0.21 px in the reference sheet, i.e. below what it could resolve. */
const CHAMFER = 0.0003;

/** Corners flatter than this are left alone, so a chamfer is never inserted into a line. */
const CORNER_MIN_DEG = 8;

// ---------------------------------------------------------------------------
// Stations and radii -- every one of them read from the datum, none restated
// ---------------------------------------------------------------------------

const xMuzzle = xOf(AXIAL.muzzleTip);
const xCollarFront = xOf(AXIAL.muzzleCollarFrontLip);
const xCollarStep = xOf(AXIAL.muzzleCollarStep);
const xBandCentre = xOf(AXIAL.midBandCentre);
const xLatticeFront = xOf(AXIAL.latticeFront);

// `OD` is in multiples of D and R is D/2, so `OD.tube * R` is the tube's radius.
const rBore = OD.bore * R;
const rLiner = OD.liner * R;
const rTube = OD.tube * R;
const rCollar = OD.muzzleCollar * R;
const rBand = OD.midBand * R;

/**
 * `barrel.midBand.length` = 0.050 +- 0.013 L, taken at its centre value. The band is the
 * one part of this profile whose axial extent is not pinned by two stations in `AXIAL`,
 * so it is the one number here that comes from the constraint table rather than the datum.
 */
const BAND_LEN_OVER_L = 0.050;
const bandLen = BAND_LEN_OVER_L * L;
const xBandFront = xBandCentre + bandLen / 2;
const xBandRear = xBandCentre - bandLen / 2;

/**
 * Bore depth: DECLARED. Section 10.18 lists "anything inside the bore -- rifling, liner
 * depth, internal step" as unmeasurable, so this is a choice and is marked as one.
 * 0.25 L puts the flat bottom at u 0.202, just behind the collar's rear step. At that
 * depth-to-diameter ratio (2.2) the bottom only comes into view within ~13 degrees of the
 * axis, and it is the darkest material on the object, so the choice is unobservable in
 * every view the reference contains -- which is the point. A through-bore was rejected:
 * `lattice.openFraction` (0.55-0.70 of rays from the axis missing geometry) requires the
 * lattice sleeve to be hollow, and a bore open at both ends would let a viewer see the
 * background straight down the gun.
 */
const BORE_DEPTH_OVER_L = 0.25;
const xBoreBottom = xMuzzle - BORE_DEPTH_OVER_L * L;

/**
 * Muzzle collar: three crests and two grooves inside u 0.078-0.187.
 *
 * `muzzle.ring.count` = 3 with two grooves, `muzzle.collar.rings.equalOd` DECLARED that
 * the three ODs differ by under 0.03 D. Built literally: all three crests sit at exactly
 * `rCollar`, so they differ by zero. Only the split between crest and groove width is
 * free, and 1.5:1 reproduces the reference's own proportion -- a 22.5 px collar reading
 * as ~5 px crests separated by ~3.5 px grooves, both of which resolve there.
 */
/** H6: `muzzle.collar.rings`, 2-4, default 3. A build-time parameter. */
let RING_COUNT: number = MUZZLE.rings;

/**
 * At 3 this is the canonical triple the contract names. Away from 3 the parts are
 * numbered instead, because inventing a fourth name like "ring-mid-2" would let a
 * constraint row match a part whose position depends on the handle -- and a row that
 * silently re-targets under an edit is worse than a row that stops matching.
 */
function ringNameTable(n: number): string[] {
  if (n === 3) return [PART.ringFore, PART.ringMid, PART.ringAft];
  return Array.from({ length: n }, (_, k) => `barrel.muzzle-collar.ring.${k}`);
}

/** R crests at 1.5 groove-lengths each, plus R-1 grooves, fill the collar exactly. */
function grooveLenFor(n: number): number {
  return (xCollarFront - xCollarStep) / (n * 1.5 + (n - 1));
}

let grooveLen = grooveLenFor(MUZZLE.rings);
let crestLen = 1.5 * grooveLen;

function setRingCount(n: number): void {
  RING_COUNT = Math.min(4, Math.max(2, Math.round(n)));
  grooveLen = grooveLenFor(RING_COUNT);
  crestLen = 1.5 * grooveLen;
}

/**
 * Groove depth: DECLARED. Section 6.7's evidence says only that the grooves resolve while
 * the ring-to-ring radius differences do not, which brackets the depth between about 1 and
 * 2 px, i.e. 1.4-2.8 mm. 0.05 D = 2.6 mm sits at the top of that, and lands the groove
 * floor at 1.04 D -- still proud of the tube. That is the reading worth having: the collar
 * is one turned brass body with two decorative grooves cut in it, not three loose rings
 * with the tube showing between them.
 *
 * The walls are raked 15 degrees off vertical rather than square. A square-walled groove
 * 2.6 mm deep and 3.5 mm wide has two internal corners under 1 px apart in the reference
 * frame and reads as a black slot; the rake keeps the groove a groove and, as a bonus,
 * leaves the collar's rear step the only vertical exterior wall in the collar group, which
 * is what `barrel.muzzleCollar.step.u` calls the sharpest edge on the object.
 */
const grooveDepth = 0.05 * D;
const rGroove = rCollar - grooveDepth;
const grooveWallRun = grooveDepth * Math.tan((15 * Math.PI) / 180);

// ---------------------------------------------------------------------------
// The profile
// ---------------------------------------------------------------------------

/**
 * Traced muzzle-first, x descending, starting on the axis at the bottom of the bore and
 * ending on the axis at the lattice's forward face. `parts[k]` names the mesh that owns
 * the segment from `nodes[k]` to `nodes[k+1]`.
 *
 * Two ownership decisions, neither of which any constraint measures: each groove is given
 * to the ring BEHIND it, so every ring mesh is one contiguous run of the profile rather
 * than three disjoint pieces; and the rear cap disc at the lattice face is given to
 * `tube-aft`, because something has to close the tube or the lattice's openings look
 * through into an open pipe.
 */
function traceProfile(): { nodes: Pt[]; parts: string[] } {
  const nodes: Pt[] = [{ x: xBoreBottom, r: 0 }];
  const parts: string[] = [];
  const to = (x: number, r: number, part: string) => {
    nodes.push({ x, r });
    parts.push(part);
  };

  to(xBoreBottom, rBore, PART.bore); // flat bottom of the blind bore
  to(xMuzzle, rBore, PART.bore); // bore wall, facing the axis
  to(xMuzzle, rLiner, PART.liner); // the annular muzzle face
  to(xCollarFront, rLiner, PART.liner); // the liner standing proud of the collar
  // H6 makes the ring count an edit handle, so the three crests that were unrolled here
  // are now a loop. At the default of 3 the emitted node sequence is identical, node for
  // node, to the unrolled version it replaced -- and the part names it assigns are still
  // ring-fore / ring-mid / ring-aft, because contract rows name those parts and a handle
  // left at its default must not rename anything.
  const ringNames = ringNameTable(RING_COUNT);
  to(xCollarFront, rCollar, ringNames[0]); // collar front lip
  to(xCollarFront - crestLen, rCollar, ringNames[0]); // crest 1

  let x = xCollarFront - crestLen;
  for (let k = 1; k < RING_COUNT; k++) {
    to(x - grooveWallRun, rGroove, ringNames[k]);
    to(x - grooveLen + grooveWallRun, rGroove, ringNames[k]);
    to(x - grooveLen, rCollar, ringNames[k]);
    if (k < RING_COUNT - 1) {
      x -= grooveLen + crestLen;
      to(x, rCollar, ringNames[k]); // crest k+1
    }
  }
  // The last crest closes on the station itself, not on the accumulated x. R crests and
  // R-1 grooves is (1.5R + R - 1) groove-lengths by construction, so the two agree -- but
  // reading the landmark back out of AXIAL means a change there moves the step, instead
  // of silently desynchronising the collar from the map.
  const last = ringNames[RING_COUNT - 1];
  to(xCollarStep, rCollar, last);
  to(xCollarStep, rTube, last); // the rear step: vertical, deliberately unraked

  to(xBandFront, rTube, PART.tubeFore);
  to(xBandFront, rBand, PART.midBand);
  to(xBandRear, rBand, PART.midBand);
  to(xBandRear, rTube, PART.midBand);

  // `tube-aft` leaves this segment at exactly rTube, the same number `tube-fore` arrives
  // on. The warm/pale boundary is therefore a material change across the band and not a
  // diameter change anywhere -- which is the whole content of
  // `barrel.tube.step.noneAtPaintLine`, whatever its stated u-window says (see the notes).
  to(xLatticeFront, rTube, PART.tubeAft);
  to(xLatticeFront, 0, PART.tubeAft); // cap, coplanar with the lattice's forward face

  return { nodes, parts };
}

/**
 * Replace every real corner with a short flat. Runs on the polyline, before revolution,
 * so one pass chamfers all 20 corners and no ring geometry has to be re-normalled.
 *
 * The clamp to 0.4 of the adjoining edge is the load-bearing part. Talon's note is that
 * `bevelSize` self-intersects on concave corners and spikes into white creases; the same
 * failure here is two chamfers eating a short edge from both ends and crossing, which
 * turns a groove floor inside out and produces a ring of back-facing triangles. 0.4 makes
 * that arithmetically impossible.
 */
function chamfer(nodes: Pt[], parts: string[]): { nodes: Pt[]; parts: string[] } {
  const outN: Pt[] = [nodes[0]];
  const outP: string[] = [];
  const minCos = Math.cos((180 - CORNER_MIN_DEG) * (Math.PI / 180));

  for (let i = 1; i < nodes.length - 1; i++) {
    const p = nodes[i - 1];
    const c = nodes[i];
    const n = nodes[i + 1];
    const l0 = Math.hypot(c.x - p.x, c.r - p.r);
    const l1 = Math.hypot(n.x - c.x, n.r - c.r);
    const d0 = { x: (c.x - p.x) / l0, r: (c.r - p.r) / l0 };
    const d1 = { x: (n.x - c.x) / l1, r: (n.r - c.r) / l1 };
    const dot = d0.x * d1.x + d0.r * d1.r;

    // Near-collinear: leave it. A chamfer on a straight line is two extra rings of
    // geometry and a seam where the profile is meant to be continuous.
    if (dot > Math.cos((CORNER_MIN_DEG * Math.PI) / 180) || dot < minCos) {
      outN.push(c);
      outP.push(parts[i - 1]);
      continue;
    }
    const c0 = Math.min(CHAMFER, 0.4 * l0);
    const c1 = Math.min(CHAMFER, 0.4 * l1);
    outN.push({ x: c.x - d0.x * c0, r: c.r - d0.r * c0 });
    outP.push(parts[i - 1]);
    // The chamfer facet goes to whichever side reaches the larger radius, and this is not
    // cosmetic bookkeeping. Section 6.5's diameters are read off per-mesh world AABBs, and
    // the checker DEFINES D as `barrel.tube-fore`'s own perpendicular extent. Give the
    // chamfer at the tube/mid-band corner to `tube-fore` and its AABB grows by 0.3 mm --
    // 1.15 % -- so the denominator under every ratio in Section 6.5 is 1.15 % wrong, and
    // `tube-fore` and `tube-aft` stop reporting the identical diameter that
    // `barrel.tube.constantOd` exists to assert. Giving it to the taller neighbour, whose
    // extreme lies elsewhere, leaves every measured diameter exactly on its nominal.
    const toIncoming = Math.max(p.r, c.r) >= Math.max(c.r, n.r);
    outN.push({ x: c.x + d1.x * c1, r: c.r + d1.r * c1 });
    outP.push(toIncoming ? parts[i - 1] : parts[i]);
  }
  outN.push(nodes[nodes.length - 1]);
  outP.push(parts[parts.length - 1]);
  return { nodes: outN, parts: outP };
}

// ---------------------------------------------------------------------------
// Revolution
// ---------------------------------------------------------------------------

type Builder = { pos: number[]; nor: number[]; uv: number[]; idx: number[] };

/**
 * Revolve the profile about +X, emitting one geometry per named part.
 *
 * Each segment gets its own pair of vertex rings carrying that segment's exact normal.
 * For a surface of revolution generated by a segment with tangent (dx, dr), the outward
 * normal in the half-plane is (dr, -dx) normalised -- and it is exact everywhere on the
 * segment, including on the flat faces where a vertex-normal pass would tilt it. Cylinders
 * therefore shade as cylinders and corners stay corners, without a smoothing-angle
 * heuristic having to guess which is which.
 *
 * `RADIAL_SEGMENTS + 1` columns, so the seam at phi = 0 carries duplicated vertices with
 * u = 0 and u = 1. Without that the texture wraps back through the whole map in one
 * quad's width and draws a visible mirrored band down the top of the barrel.
 */
function revolve(nodes: Pt[], parts: string[]): Map<string, THREE.BufferGeometry> {
  const stride = RADIAL_SEGMENTS + 1;
  const cos: number[] = [];
  const sin: number[] = [];
  for (let j = 0; j <= RADIAL_SEGMENTS; j++) {
    const phi = (j / RADIAL_SEGMENTS) * Math.PI * 2;
    cos.push(Math.cos(phi));
    sin.push(Math.sin(phi));
  }

  // v runs on cumulative arc length, so the canvas mottle keeps a constant scale across
  // a step instead of stretching over the tube and bunching on the collar.
  const arc: number[] = [0];
  for (let i = 1; i < nodes.length; i++) {
    arc.push(arc[i - 1] + Math.hypot(nodes[i].x - nodes[i - 1].x, nodes[i].r - nodes[i - 1].r));
  }
  const total = arc[arc.length - 1] || 1;

  const builders = new Map<string, Builder>();
  for (let k = 0; k < parts.length; k++) {
    const a = nodes[k];
    const b = nodes[k + 1];
    const dx = b.x - a.x;
    const dr = b.r - a.r;
    const len = Math.hypot(dx, dr);
    if (len < 1e-9) continue;
    const nx = dr / len;
    const nr = -dx / len;

    let bd = builders.get(parts[k]);
    if (!bd) {
      bd = { pos: [], nor: [], uv: [], idx: [] };
      builders.set(parts[k], bd);
    }
    const base = bd.pos.length / 3;

    for (const [ring, node] of [[0, a], [1, b]] as [number, Pt][]) {
      const v = arc[k + ring] / total;
      for (let j = 0; j <= RADIAL_SEGMENTS; j++) {
        bd.pos.push(node.x, node.r * cos[j], node.r * sin[j]);
        bd.nor.push(nx, nr * cos[j], nr * sin[j]);
        bd.uv.push(j / RADIAL_SEGMENTS, v);
      }
    }

    for (let j = 0; j < RADIAL_SEGMENTS; j++) {
      const a0 = base + j;
      const a1 = base + j + 1;
      const b0 = base + stride + j;
      const b1 = base + stride + j + 1;
      // Winding is (a0, b0, b1) / (a0, b1, a1) with j increasing in +phi and the profile
      // running muzzle-first; that is front-facing against the (dr, -dx) normal above.
      // On a ring that collapses to the axis the quad becomes a triangle fan, and exactly
      // one of the two triangles degenerates: (a0, b0, b1) dies when the FAR ring is on
      // the axis (b0 and b1 are the same point), (a0, b1, a1) when the NEAR one is. Get
      // the two guards the wrong way round and both discs -- the bore's flat bottom and
      // the tube's rear cap -- ship as 64 zero-area triangles each and 128 real ones go
      // missing, which renders as an open pipe you can see the background through.
      if (b.r > 0) bd.idx.push(a0, b0, b1);
      if (a.r > 0) bd.idx.push(a0, b1, a1);
    }
  }

  const out = new Map<string, THREE.BufferGeometry>();
  for (const [name, bd] of builders) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(bd.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(bd.nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(bd.uv, 2));
    g.setIndex(bd.idx);
    g.computeBoundingBox();
    g.computeBoundingSphere();
    out.set(name, g);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Generated finish
// ---------------------------------------------------------------------------

/** CIE Lab (D65) to a linear-sRGB THREE.Color, so Section 6.10's numbers go in directly. */
function lab(Lstar: number, a: number, b: number): THREE.Color {
  const fy = (Lstar + 16) / 116;
  const fx = fy + a / 500;
  const fz = fy - b / 200;
  const g = (t: number) => (t > 6 / 29 ? t * t * t : 3 * (6 / 29) ** 2 * (t - 4 / 29));
  const X = 0.95047 * g(fx);
  const Y = g(fy);
  const Z = 1.08883 * g(fz);
  const cl = (v: number) => Math.min(1, Math.max(0, v));
  return new THREE.Color().setRGB(
    cl(3.2406 * X - 1.5372 * Y - 0.4986 * Z),
    cl(-0.9689 * X + 1.8758 * Y + 0.0415 * Z),
    cl(0.0557 * X - 0.204 * Y + 1.057 * Z),
    THREE.LinearSRGBColorSpace,
  );
}

/** Section 6.10 states brass as hue and chroma, not as a* and b*, so accept it that way. */
function labHC(Lstar: number, hueDeg: number, chroma: number): THREE.Color {
  const h = (hueDeg * Math.PI) / 180;
  return lab(Lstar, chroma * Math.cos(h), chroma * Math.sin(h));
}

/**
 * Two octaves of value noise on a canvas, used as a roughness map only.
 *
 * It is not used as an albedo map on purpose. `mat.paint.tube.ab` and the brass hue rows
 * are checked against the material's BASE COLOUR, and multiplying a noise map into that
 * would drag the checked value away from the measured one by however much the noise
 * happens to darken -- a finish that quietly falsifies the constraint it was built to
 * honour. Perturbing roughness instead breaks up the specular without touching a single
 * number in Section 6.10.
 */
let mottleCache: THREE.Texture | null | undefined;
function mottle(): THREE.Texture | null {
  if (mottleCache !== undefined) return mottleCache;
  mottleCache = null;
  try {
    if (typeof document === 'undefined') return mottleCache;
    const S = 256;
    const cv = document.createElement('canvas');
    cv.width = cv.height = S;
    const ctx = cv.getContext('2d');
    if (!ctx) return mottleCache;
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, S, S);
    // Deterministic: a finish that changes between renders makes two passes of the
    // acceptance render incomparable for no gain.
    let seed = 0x9e3779b9;
    const rnd = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 0x100000000;
    };
    for (const [cells, alpha] of [[16, 0.55], [48, 0.3]] as [number, number][]) {
      const small = document.createElement('canvas');
      small.width = small.height = cells;
      const sc = small.getContext('2d');
      if (!sc) continue;
      const img = sc.createImageData(cells, cells);
      for (let i = 0; i < cells * cells; i++) {
        // Biased to the bright end on purpose: `roughnessMap` MULTIPLIES the scalar, so a
        // map centred on mid-grey silently halves every roughness in this file. Keeping
        // the field in [0.7, 1.0] makes it a modulation of the value asked for rather than
        // a replacement of it.
        const v = 178 + Math.floor(rnd() * 78);
        img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
        img.data[i * 4 + 3] = 255;
      }
      sc.putImageData(img, 0, 0);
      ctx.globalAlpha = alpha;
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(small, 0, 0, S, S);
    }
    ctx.globalAlpha = 1;
    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(3, 6);
    // Read the composite's mean back off the canvas instead of predicting it. Two octaves
    // alpha-composited over a base do not average to any of the three inputs, and a
    // guessed constant here would bias every roughness in the file by whatever the guess
    // was wrong by -- silently, because nothing downstream measures roughness.
    const px = ctx.getImageData(0, 0, S, S).data;
    let sum = 0;
    for (let i = 0; i < px.length; i += 4) sum += px[i];
    tex.userData.mean = sum / (px.length / 4) / 255;
    mottleCache = tex;
  } catch {
    // A finish is not worth throwing over. Without a DOM the parts still render, flatter.
    mottleCache = null;
  }
  return mottleCache;
}

/**
 * Metalness stays low on everything, which looks wrong for brass and is not.
 *
 * Section 10.26 says no PBR parameter is recoverable from the reference at all -- the
 * texture is hand-painted and the highlights are 2-6 px -- so these are DECLARED. What
 * decides them is `shading.ramp`: every single-material cylinder must show a p5-p95 L*
 * spread of at least 30 under the reference key. That spread is a diffuse terminator.
 * Metalness near 1 deletes diffuse and replaces it with a neutral environment reflection,
 * which on a bare lathe flattens the terminator to a couple of specular bands and drops
 * the spread well under 30. 0.35 keeps a brass-like edge highlight while leaving the ramp
 * intact. This is the same trade Talon makes at 0.08 for its projected plates, arrived at
 * from the opposite direction: there, to let de-lit albedo through; here, to let a
 * measurable shading ramp survive.
 */
function surface(
  color: THREE.Color,
  roughness: number,
  metalness: number,
  name: string,
  mottled = true,
) {
  const m = new THREE.MeshStandardMaterial({ color, roughness, metalness });
  m.name = name;
  const tex = mottled ? mottle() : null;
  if (tex) {
    m.roughnessMap = tex;
    // Divide by the map's measured mean so the material's EFFECTIVE mean roughness is the
    // number written at the call site. Without this the argument stops meaning anything
    // and every value in `materials()` has to be read as "some fraction of this".
    m.roughness = Math.min(1, roughness / (tex.userData.mean as number));
  }
  return m;
}

function materials(): Record<string, THREE.MeshStandardMaterial> {
  const table = materialTable();
  // H6 can generate ring names outside the canonical three. They get the identical aged
  // brass, so the handle changes how many rings there are and nothing else about them.
  for (const n of ringNameTable(RING_COUNT)) {
    if (!table[n]) table[n] = table[PART.ringMid].clone();
  }
  return table;
}

function materialTable(): Record<string, THREE.MeshStandardMaterial> {
  // `mat.paint.tube.ab`: a* -1.5, b* -7.0, each +-1.5, at conf 0.90 -- the most
  // reproducible pair in the document. (The audit's D-9 reproduces b* as -4.56 by mean
  // and -6.0 by median; -7.0 is what the frozen row says and it is inside the audit's
  // own median, so the row is built as stated rather than re-derived here.)
  // L* is DECLARED throughout: Section 6.10's own header says no part is a flat colour
  // sample, so it states chromaticity and leaves lightness to the shading.
  const tubePaint = lab(52, -1.5, -7.0);

  return {
    // Section 10.24: the liner is bare steel or tube paint and nothing separates them --
    // a* and b* agree within one unit and only L* differs. So: the paint's chromaticity
    // at a higher L*. A neutral steel would also trip `mat.noBareSteel` (no material with
    // C* < 3 over 2 % of visible area); this one has C* 7.2.
    [PART.liner]: surface(lab(68, -1.5, -7.0), 0.38, 0.25, 'liner.pale-steel'),

    // `mat.bore.interior.L` = 21.5 +- 3 and `mat.bore.darkest` (>= 8 L* below every
    // exterior). The darkest exterior here is the warm tube at 38, so 21.5 clears it.
    // Unmottled: at roughness 0.9 the lift would clamp and the map would end up REDUCING
    // roughness instead of modulating it, and a blind hole has nothing to modulate anyway.
    [PART.bore]: surface(lab(21.5, -1.0, -5.0), 0.9, 0.0, 'bore.interior', false),

    // `mat.brass.aged.hue` = 66.5 +- 5 deg on collar / lattice / mid-band; C* 20.2 from
    // `mat.warmTube.notBrass`'s pose3 evidence line.
    // Every ring is the same aged brass, so H6 adding or removing one cannot change what
    // the collar is made of. The canonical three are spelled out because contract [MAT]
    // rows name them; any ring the handle generates beyond that is filled in below.
    [PART.ringFore]: surface(labHC(47, 66.5, 20.2), 0.42, 0.35, 'brass.aged'),
    [PART.ringMid]: surface(labHC(47, 66.5, 20.2), 0.42, 0.35, 'brass.aged'),
    [PART.ringAft]: surface(labHC(47, 66.5, 20.2), 0.42, 0.35, 'brass.aged'),
    [PART.midBand]: surface(labHC(47, 66.5, 20.2), 0.42, 0.35, 'brass.aged'),

    [PART.tubeFore]: surface(tubePaint, 0.62, 0.0, 'paint.tube'),

    // The warm zone. `mat.warmTube.notBrass` requires C* <= C*(aged) - 2.0, so 16.8
    // against 20.2. The hue is DECLARED at 62 deg: the contract fixes the warm section's
    // chroma and says it is the same hue family as aged brass, but never states its hue.
    // Section 10.25 adds that copper versus worn brown paint is undecidable, so this is
    // painted, not metal -- metalness 0, matching `mat.warmTube.notWood`'s finding that
    // the warm zone is smoother than the blue paint rather than grainier.
    [PART.tubeAft]: surface(labHC(38, 62, 16.8), 0.55, 0.0, 'paint.warm'),
  };
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------

/**
 * The barrel as a body of revolution, u 0.000 to u 0.662.
 *
 * It stops at the lattice collar's FORWARD face, not its rear. The barrel group in the
 * assembly tree runs to u 0.808, but the span from 0.662 back is the pierced sleeve,
 * which is another module's extrude, and no tube may continue underneath it:
 * `lattice.openFraction` counts rays from the axis that MISS geometry and wants 0.55-0.70
 * of them, which a core inside the sleeve would drive to zero. So the revolved barrel ends
 * here, capped, flush with `barrel.lattice.front.u`.
 *
 * `barrel.bore` is a sibling of `barrel.liner` in the scene graph and its child in the
 * spec; the comment at the call site says why the two have to differ.
 */
export function buildBarrel(rings?: number): THREE.Group {
  setRingCount(rings ?? MUZZLE.rings);
  const traced = traceProfile();
  const profile = chamfer(traced.nodes, traced.parts);
  const geo = revolve(profile.nodes, profile.parts);
  const mats = materials();

  const mesh = (part: string) => {
    const g = geo.get(part);
    if (!g) throw new Error(`barrel: no geometry emitted for ${part}`);
    const m = new THREE.Mesh(g, mats[part]);
    m.name = part;
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  };

  const barrel = new THREE.Group();
  barrel.name = PART.barrel;

  // The tree parents `barrel.bore` under `barrel.liner`, and that relation belongs in the
  // spec's componentTree, which is where `check_contract.py` reads it. It must NOT become
  // scene-graph parenting: every AABB in this pipeline is `Box3().setFromObject(mesh)`,
  // which unions a child's bounds into its parent's, and the bore runs 0.25 L deep against
  // a liner 0.0965 L long -- so `barrel.liner` would report a 0.25 L axial extent against
  // the 0.10 +- 0.035 L that `barrel.zone.axialFractions` asks of it. Siblings here, parent
  // and child in the spec. (Section 3 already marks that parenting DECLARED: the bore is a
  // void and whichever mesh owns the cut is a modelling choice.)
  barrel.add(mesh(PART.liner), mesh(PART.bore));

  // The collar is a named Group as well as three named meshes. `barrel.brassRing.count`
  // counts three encircling brass ASSEMBLIES, and a checker that counts meshes with
  // OD > 1.05 D finds five here (three rings + band + lattice); the group gives an
  // assembly-level count something to land on. See the notes.
  const collar = new THREE.Group();
  collar.name = PART.muzzleCollar;
  for (const n of ringNameTable(RING_COUNT)) collar.add(mesh(n));
  barrel.add(collar);

  barrel.add(mesh(PART.tubeFore), mesh(PART.midBand), mesh(PART.tubeAft));

  let triangles = 0;
  for (const g of geo.values()) triangles += (g.getIndex()?.count ?? 0) / 3;
  barrel.userData.triangles = triangles;
  barrel.userData.radialSegments = RADIAL_SEGMENTS;
  barrel.userData.profileNodes = profile.nodes.length;

  return barrel;
}

// ---------------------------------------------------------------------------
// What this module does not satisfy, and why
// ---------------------------------------------------------------------------
//
// FAILED ON PURPOSE
//
// `barrel.step.count` = 5 (conf 0.70). Measured on this build with a 200-station radial
//   probe at the row's own 2 %-of-median-R threshold: 7 sign changes of dr/dx over the
//   barrel's span alone -- liner->collar up, two grooves down-and-up, collar->tube down,
//   band up, band down. The audit's D-12 already names this as a contradiction with
//   Sections 6.5-6.7 and predicts 11-13 for the whole gun. The rings are built and the
//   count is failed, for three reasons. `muzzle.ring.count` = 3 is carried by two disjoint
//   pose pairs (Section 5.7) where the step count is one report's enumeration of the five
//   steps it happened to list. The assembly tree in Section 3 makes ring-fore, ring-mid and
//   ring-aft named parts, and a missing named part is a hard failure in the checker while a
//   count row is one row. And the row's threshold is 2 % of R = 0.37 px in the reference
//   frame, which is below the sheet's own resolution -- it counts what was visible, not
//   what is there. The one way to pass both is to make the grooves shallower than the
//   checker's gradient threshold, which would satisfy the letter of both rows by building
//   grooves nobody can see. That is gaming a test, not modelling an object.
//
// `barrel.tube.step.noneAtPaintLine` = 0 steps in u 0.45-0.66 (conf 0.85). The mid-band is
//   centred at u 0.449 (`AXIAL.midBandCentre`) and is 0.050 L long, so its rear wall lands
//   at u 0.4692 -- inside the window. This is unsatisfiable jointly with
//   `barrel.midBand.centre.u` + `barrel.midBand.length` + `barrel.midBand.od` = 1.18: to
//   clear u 0.45 the band would have to be 0.007 L long against a stated floor of 0.037 L.
//   It is a contradiction the audit's D-12 family did not list. The row's INTENT is met
//   exactly and is the more important half: `tube-fore` and `tube-aft` are two spans of one
//   polyline at identical radius, the warm/pale boundary carries no diameter change at all,
//   and the only step near it belongs to a separately measured brass ring.
//
// `barrel.zone.blueOverWarm` = 1.62 +- 0.15 (built: 1.250) and
// `barrel.copperOverSteel.length` = 0.71 +- 0.08 (built: 0.800). Both fail, and both fail
//   for the same reason: the axial map's own stations give (0.449 - 0.187) : (0.662 -
//   0.449) = 1.230 before the band's span is subtracted from either zone. There is no
//   placement of the paint line that recovers 1.62 while the three stations stand, and
//   those three are conf 0.85, 0.70 and 0.75 against these two rows' derived ratios. The
//   individual zone extents still pass: blue 0.297 L against 0.32 +- 0.035, warm 0.237 L
//   against 0.21 +- 0.035. Tolerances on the parts do not compose to the tolerance on the
//   ratio, which is worth saying plainly. Audit D-2 had already shown these two rows to be
//   mutually unsatisfiable; this build fails both rather than picking one.
//
// `muzzle.liner.protrudes` = 0.05 +- 0.03 L (built: 0.0953 L). The RELATION holds -- the
//   liner stands proud of the collar, not recessed, which is the half that Section 6.7
//   kept at conf 0.45 with scale-silhouette reading it the other way. The MAGNITUDE is
//   double the stated one, because the axial map puts the muzzle tip at u 0.000 and the
//   collar's front lip at u 0.078, and 0.078 A is 0.0965 L by arithmetic. Two
//   higher-confidence rows agree with the map: `barrel.zone.axialFractions` gives the liner
//   zone 0.10 +- 0.035 L. The 0.05 figure is inconsistent with the document's own axial
//   map, and the map is what the datum exposes and what this module was told to read.
//
// NOTED, NOT FAILED BY THIS GEOMETRY
//
// `barrel.tube.constantOd` -- "max radius varies < 3 % over u 0.10-0.66" is unsatisfiable
//   as literally written by ANY model matching Section 6.5, because that window contains
//   the muzzle collar (1.14 D) and the mid-band (1.18 D). Read as a statement about the
//   tube meshes, this build satisfies it in its strongest form: `tube-fore` and `tube-aft`
//   vary by exactly zero.
//
// `barrel.muzzleCollar.step.u` -- the station is built at exactly u 0.187, but the row's
//   [SIL] check ("largest positive dr/dx in the forward half") would report u 0.469
//   instead, because Section 6.5 makes the mid-band (1.18 D) a taller step than the collar
//   (1.14 D) and the band sits in the forward half. The check cannot find the landmark it
//   names, for any build that honours Section 6.5's diameters.
//
// `barrel.brassRing.count` = 3 -- the check counts MESHES forming a full ring with
//   OD > 1.05 D. The tree requires three separately named collar rings, so a mesh count
//   returns 5 for the whole gun, not 3. `barrel.muzzle-collar` is emitted as a named Group
//   so an assembly-level count has something to find; a mesh-level count fails on the tree,
//   not on this module.
//
// Section 3's `barrel.bore` under `barrel.liner` -- kept as a SPEC relation, not as scene-
//   graph parenting, because `Box3().setFromObject()` unions a child's bounds into its
//   parent's and a 0.25 L bore inside a 0.0965 L liner would report the liner as 0.25 L
//   long. Section 3 marks that parenting DECLARED in the first place.
//
// DECLARED HERE, BECAUSE THE REFERENCE CANNOT SETTLE IT
//
//   bore depth 0.25 L with a flat bottom (Section 10.18: nothing inside the bore is
//     measurable); groove depth 0.05 D and 15-degree groove walls (Section 6.7 says only
//     that grooves resolve and ring-to-ring differences do not); crest:groove = 1.5:1;
//     the 0.3 mm chamfer on every corner (0.21 px in the sheet -- below what the reference
//     resolves, which is the condition for it not being an invention); L* for every
//     material and the warm zone's hue of 62 degrees (Section 6.10 states chromaticity, not
//     lightness, and never states the warm hue); all roughness and metalness values
//     (Section 10.26: no PBR parameter is recoverable); and the choice to end the revolved
//     barrel at u 0.662 with a cap rather than run a core under the lattice.
