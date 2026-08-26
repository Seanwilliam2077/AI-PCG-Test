/**
 * The top rail: a brass bar lying tangent on the barrel, with a mount block, three studs
 * and a forward-curving rear hook.
 *
 * The one thing this part has to get right is that it is NOT a bar on the tube. Audit D-6
 * is the contract's largest single correction and it is entirely about this mesh: the rail
 * is continuous **over** the lattice collar. It runs sheet x 2443-2592, a true span of
 * 0.93 L rather than the 0.706 L the frozen `barrel.rail.axialSpan` row's evidence claimed,
 * and its top steps DOWN by 8 px near the lattice's forward face -- exactly the difference
 * between the lattice's top (R 26.75 px) and the tube's top (R 18.5 px), i.e. 0.225 D. That
 * step is the proof the bar is tangent on *both* cylinders in turn, and colour settles that
 * the bar over the lattice is rail and not collar (h 87.9 deg, the yellow-brass family,
 * against the lattice body's 61.1 deg).
 *
 * So the spine of this module is a lofted bar whose seat radius is a step function of x and
 * whose underside is *dished* to that radius. A flat-bottomed bar would satisfy the
 * tangency row's number at z = 0 and open a wedge of background under its edges at every
 * other azimuth, which is the single observation `barrel.rail.tangent` rests on ("no
 * background pixel between rail underside and tube in any of four views"). The dish makes
 * the min radius exactly R at every point of the forward underside, not just on the
 * centreline.
 *
 * Everything not revolved is an extrude: the mount block is a saddle section swept along X,
 * the hook is a traced X-Y profile extruded through Z. The three studs are lathes, which is
 * what a rivet dome wants to be.
 *
 * FINISH. The reference is a measurement target and its pixels may not be projected onto
 * this model, so the one Talon technique that does not transfer is the projected de-lit
 * plate. Colour here is *generated*: `material.color` is built from the contract's measured
 * CIE Lab in §6.10 by an inline Lab->sRGB, and the canvas maps are strictly achromatic
 * modulation. That split is deliberate -- `tools/check_contract.py` reads the material's
 * base colour and converts it to Lab, so any chroma in the map would push the rendered hue
 * off the measured 79 deg without ever showing up in that read.
 *
 * What the generated finish costs, stated plainly: a projected plate would have carried the
 * hand-painted value variation, the 2-6 px specular decisions the texture artist actually
 * made, and the graffiti registration -- §6.11 records two accent islands that cross mesh
 * seams, one of them onto brass. None of that survives here. The streak field below is
 * invented micro-detail carrying zero information from the reference. What does survive is
 * hue and chroma, which are numbers, and numbers are the only thing that leaves a
 * measurement target.
 */
import * as THREE from 'three';
import { A, D, R, AXIAL, OD, PART, xOf } from './datum.js';

/**
 * Contract landmarks arrive as sheet x in §2's table and §11's audit prose. This converts
 * one into the frozen axial parameter and introduces no new denominator: u = 0 at sheet
 * x 2604 and A = 198 px are §2's own units, the same pair that produced every `AXIAL` entry
 * in `datum.ts`. Written as a function so that every `u` below carries its provenance in
 * the call rather than in a comment nobody re-checks.
 */
const uOfSheetX = (sheetX: number) => (2604 - sheetX) / 198;

/** Rear end of the bar. D-6 reads sheet 2443; the breech face is 2444 and is the frozen
 *  datum, so the bar terminates exactly on it. H5 makes this the rail's fixed end. */
const U_AFT = AXIAL.latticeRear;
/** Forward end, D-6's sheet 2592 -- 4 px forward of the muzzle collar's front lip. */
const U_FORE = uOfSheetX(2592);
/** Where the underside leaves the lattice and drops onto the tube. */
const U_SEAT_STEP = AXIAL.latticeFront;
/**
 * Where the *top* line steps down, D-6's sheet 2482. This is 9 px forward of the lattice's
 * front face (sheet 2473, two reports 0.1 px apart, §5.6), and the gap is not slop: the
 * underside must drop at the lattice's face while the top drops later, or the bar is two
 * disconnected boxes with a 0.225 D void between them. The stretch between the two is a
 * full-height knee sitting on the tube, and it is the only construction that reconciles
 * D-6's step location with §2's lattice face. INFERRED, not a contract row -- the competing
 * reading is that 2482 and 2473 are the same edge measured twice and the knee is zero
 * length, which cannot be built.
 */
const U_TOP_STEP = uOfSheetX(2482);

/** Studs. §5.5: joints 2511 / 2519 / 2584, scale-silhouette 2511 / 2516 / 2583, within 3 px
 *  on all three from different poses. The pair straddles the mount block. */
const U_STUD_AFT = uOfSheetX(2511);
const U_STUD_MID = uOfSheetX(2517.5);
const U_STUD_FORE = AXIAL.railFwdStud;

/**
 * `barrel.rail.proud.overTubeOd`, and this is the row the task asks me to declare against.
 *
 * The frozen row says 0.12 +- 0.04 from "pose3 x2554: rail top +26.0, tube top +21.6".
 * Audit D-8 found that +21.6 is R from the superseded D = 43 camp and was missed by D3's
 * rescale, and recomputes the ratio as 0.16 in the adopted frame -- sitting exactly on the
 * row's upper bound.
 *
 * BUILT TO 0.155. That is the audit's value pulled one notch inside the frozen band, so the
 * row is satisfied with margin instead of on a boundary where float noise in
 * (hi(rail,y) - R) / D decides the verdict. Building to the frozen centre 0.12 was rejected:
 * it reproduces a denominator error the audit already identified.
 *
 * This is the bar's thickness at z = 0, which is why the same number sets the top of both
 * stretches -- D-6's 8 px step means the bar keeps its section across the knee.
 */
const PROUD_OVER_D = 0.155;

const SEAT_TUBE = R;
/** The lattice is the widest thing on the object; the bar rides its outer surface aft of
 *  the seat step. `OD.lattice` is a multiple of D, so its radius is that times R. */
const SEAT_LATTICE = OD.lattice * R;
const BAR_T = PROUD_OVER_D * D;
const TOP_FORE = SEAT_TUBE + BAR_T;
const TOP_AFT = SEAT_LATTICE + BAR_T;

/**
 * Bar width and the chamfer on its two top arrises. DECLARED. §10.29 records that no top
 * view and no orthographic muzzle-on view exists, so the object's true width -- including
 * this bar's -- is unmeasurable in any of the nine views. 0.34 D keeps the bar visibly
 * narrower than the mount block that clamps it and an order of magnitude inside
 * `gun.maxWidth.isLatticeCollar`'s 1.45 D ceiling.
 */
const BAR_HALF_W = 0.17 * D;
const BAR_CHAMFER = 0.022 * D;

/** Mount block. Its axial centre is the midpoint of the stud pair it carries, not the
 *  mid-band below it -- the studs are the measured thing. That the two land within 0.005 A
 *  of each other is worth noticing: the block sits directly over `barrel.mid-band`, which
 *  is what a clamp at an encircling band would do. Its size is DECLARED; no contract row
 *  gives the block any dimension. */
const U_MOUNT = (U_STUD_AFT + U_STUD_MID) / 2;
const MOUNT_LEN = 0.075 * A;
const MOUNT_HALF_W = 0.21 * D;
const MOUNT_TOP = 0.765 * D;
const MOUNT_FOOT = 0.52 * D;

/** Studs. D-14 puts the rear pair 8 px apart and calls that "about 2.3 diameters", which
 *  fixes the diameter at ~3.5 px = 0.095 D. Rounded to 0.10 D. */
const STUD_R = 0.05 * D;
const STUD_H = 0.45 * STUD_R;

/**
 * Rear hook. J4 declares the pivot at (u 0.79, +1.35 R) and the shape as a hook curving
 * FORWARD, 19x13 px, with confidence 0.30 and an explicit note that it may be a lanyard
 * hook or a finial and not a sight at all.
 *
 * The +1.35 R is a pre-D-6 reading: it puts the hook's base on the rail's top surface only
 * if the rail's rear end sits on the *tube*, which is the span D-6 refuted. In the adopted
 * frame the rail's rear rides the lattice, and +1.35 R = 0.675 D is *inside* the lattice
 * collar (its outer radius is 0.725 D). So the hook's base moves up to the rail's actual
 * top there, 0.880 D. J4's declared pivot u 0.79 still lies inside the hook's axial span.
 *
 * The 13 px height is read from the lattice's top, not from the rail's: 0.725 D + 13/37 D
 * = 1.075 D. Taking 13 px above the *rail* instead would put this mesh at 1.23 D and make
 * it the tallest thing on the gun by 10 px, whereas `gun.height.overTubeOd`'s own evidence
 * measures the gun's top at the port (+0.95 D). At 1.075 D the hook still becomes the
 * highest mesh, by 4.6 px -- see the report; that is a consequence of D-6 and it is
 * declared rather than trimmed away.
 */
const HOOK_LEN_U = 19 / 198;
const HOOK_BASE = TOP_AFT;
const HOOK_TOP = SEAT_LATTICE + (13 / 37) * D;
const HOOK_HALF_T = 0.05 * D;

/* ------------------------------------------------------------------ colour and maps */

/**
 * CIE Lab (D65) -> sRGB. Inline rather than a hex literal because §6.10's rows *are* Lab,
 * and a hex would hide which of L, hue and chroma was actually measured and which was
 * chosen. `tools/check_contract.py` runs the inverse of this on the base colour, so the
 * numbers below are what the checker sees.
 */
function labColor(L: number, a: number, b: number): THREE.Color {
  const fy = (L + 16) / 116, fx = fy + a / 500, fz = fy - b / 200;
  const g = (t: number) => (t * t * t > 0.008856 ? t * t * t : (t - 16 / 116) / 7.787);
  const X = 0.95047 * g(fx), Y = g(fy), Z = 1.08883 * g(fz);
  const lin = [
    X * 3.2406 + Y * -1.5372 + Z * -0.4986,
    X * -0.9689 + Y * 1.8758 + Z * 0.0415,
    X * 0.0557 + Y * -0.2040 + Z * 1.0570,
  ].map((c) => {
    const v = Math.min(1, Math.max(0, c));
    return v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
  });
  return new THREE.Color().setRGB(lin[0], lin[1], lin[2], THREE.SRGBColorSpace);
}

const labFromPolar = (L: number, chroma: number, hueDeg: number) =>
  labColor(L, chroma * Math.cos((hueDeg * Math.PI) / 180), chroma * Math.sin((hueDeg * Math.PI) / 180));

/**
 * `mat.brass.yellow.hue` = 79 +- 6 deg, measured on "rail + rear hook" (81.1 pose3 n=84,
 * 77.7 pose1 n=204). Chroma is pinned at 21.6, the contract's own stated structural ceiling
 * from `mat.accent.outchroma`; going higher would raise the bar the accents must clear.
 * L* 34.1 is the exterior minimum `mat.bore.darkest`'s evidence attributes to this very
 * part, so using it keeps that row's anchor where the reference put it. It is an *observed*
 * L used as albedo, which will render darker than the reference under any exposure above
 * zero; the alternative -- lifting albedo L to compensate for lighting -- would invalidate
 * the one row that names the rail's lightness. Declared, and the bore module has to make
 * the same choice for the comparison to mean anything.
 */
const BRASS_YELLOW = labFromPolar(34.1, 21.6, 79);
/** `mat.mount.red.hue` = 37 +- 7 deg (34.3 / 39.3 / 38.9 across three poses). Chroma and L
 *  are DECLARED -- no row states either for this block. */
const MOUNT_RED = labFromPolar(36.0, 20.0, 37);

/**
 * The generated finish. Deterministic: a fixed-seed LCG, because a measurement pipeline
 * that re-renders the same model twice must get the same pixels, and Math.random() would
 * quietly move every acceptance number by a fraction of a level.
 *
 * Streaks run along the bar, so they are rows of constant v -- the loft's v runs around the
 * section and its u runs along X. Achromatic only, for the reason in the file header.
 */
function brassMaps(): { map: THREE.Texture | null; roughnessMap: THREE.Texture | null } {
  if (typeof document === 'undefined') return { map: null, roughnessMap: null };
  let seed = 0x5eed >>> 0;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);

  const W = 512, H = 64;
  const albedo = document.createElement('canvas');
  albedo.width = W; albedo.height = H;
  const rough = document.createElement('canvas');
  rough.width = W; rough.height = H;
  const ca = albedo.getContext('2d');
  const cr = rough.getContext('2d');
  if (!ca || !cr) return { map: null, roughnessMap: null };

  // Per-row brushed value, plus a slow along-length wear term. Amplitudes are small on
  // purpose: the reference's per-part p5-p95 L span is 35-52 and that is the *lighting*
  // terminator, not the texture. A loud texture would double-count it.
  const rowBias: number[] = [];
  for (let y = 0; y < H; y++) rowBias.push((rnd() - 0.5) * 0.13);
  const wear: number[] = [];
  let w = 0;
  for (let x = 0; x < W; x++) {
    w = w * 0.965 + (rnd() - 0.5) * 0.055;
    wear.push(w);
  }

  const ia = ca.createImageData(W, H);
  const ir = cr.createImageData(W, H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const fine = (rnd() - 0.5) * 0.035;
      const v = Math.min(1, Math.max(0, 0.86 + rowBias[y] + wear[x] + fine));
      const i = (y * W + x) * 4;
      const c = Math.round(v * 255);
      ia.data[i] = ia.data[i + 1] = ia.data[i + 2] = c;
      ia.data[i + 3] = 255;
      // Dark = worn = rougher. Green channel is what MeshStandardMaterial samples.
      const rg = Math.round(Math.min(1, Math.max(0, 0.52 - (v - 0.86) * 1.6)) * 255);
      ir.data[i] = ir.data[i + 1] = ir.data[i + 2] = rg;
      ir.data[i + 3] = 255;
    }
  }
  ca.putImageData(ia, 0, 0);
  cr.putImageData(ir, 0, 0);

  const map = new THREE.CanvasTexture(albedo);
  map.colorSpace = THREE.SRGBColorSpace;
  map.wrapS = map.wrapT = THREE.RepeatWrapping;
  map.anisotropy = 4;
  const roughnessMap = new THREE.CanvasTexture(rough);
  roughnessMap.wrapS = roughnessMap.wrapT = THREE.RepeatWrapping;
  roughnessMap.anisotropy = 4;
  return { map, roughnessMap };
}

/**
 * §10.26: no PBR parameter on this object is measurable -- the texture is hand-painted and
 * stylised, and its highlights are 2-6 px. Talon's projected plates take metalness 0.08
 * because a de-lit albedo has to show through; there is no plate here, but the same
 * observation applies from the other side: a hand-painted stylised brass reads mostly
 * diffuse, and metalness near 1 would replace that diffuse with neutral environment
 * reflection and erase the measured hue. Both pairs -- brass 0.22 / 0.42 and the painted
 * mount block 0.12 / 0.55 -- are DECLARED.
 */
function standardMaterial(
  color: THREE.Color, metalness: number, roughness: number, shared: ReturnType<typeof brassMaps>,
): THREE.MeshStandardMaterial {
  const params: THREE.MeshStandardMaterialParameters = { color, metalness, roughness };
  // Assigned rather than spread with `?? undefined`: three warns on an explicitly undefined
  // parameter key, and the headless path (no `document`) has no canvas to hand it.
  if (shared.map) params.map = shared.map;
  if (shared.roughnessMap) params.roughnessMap = shared.roughnessMap;
  return new THREE.MeshStandardMaterial(params);
}

/* ------------------------------------------------------------------ the lofted bar */

interface RingPt { y: number; z: number; ny: number; nz: number; }
interface Station { x: number; seat: number; top: number; }

const ARC_SEGS = 8;

/**
 * One cross-section of the bar, in the Y-Z plane, as a closed run of points with authored
 * normals.
 *
 * Traversal order matters twice. It runs the top face from -z to +z because that is the
 * winding that makes the lofted quads face outward (the strip normal comes out as
 * (0, tz, -ty) for an in-ring tangent (0, ty, tz), so a +Z tangent on the top gives +Y).
 * And it duplicates the point at every arris -- the top/chamfer/flank/arc joins -- so the
 * hard edges stay hard without a smoothing-angle pass. The duplicated pairs generate
 * zero-area quads, which the loft skips by area, so they cost nothing.
 *
 * Underside normals are analytic, (0, -y, -z)/seat: the surface there is a function of z,
 * and `computeVertexNormals` would average it into the flanks and round off the arris the
 * dish is there to create.
 */
function railRing(seat: number, top: number): RingPt[] {
  const pts: RingPt[] = [];
  const push = (y: number, z: number, ny: number, nz: number) => pts.push({ y, z, ny, nz });
  const yAt = (z: number) => Math.sqrt(Math.max(seat * seat - z * z, 1e-12));
  const hw = BAR_HALF_W, c = BAR_CHAMFER, s = Math.SQRT1_2;

  push(top, -(hw - c), 1, 0);
  push(top, +(hw - c), 1, 0);
  push(top, +(hw - c), s, s);
  push(top - c, +hw, s, s);
  push(top - c, +hw, 0, 1);
  push(yAt(hw), +hw, 0, 1);
  for (let i = 0; i <= ARC_SEGS; i++) {
    const z = hw - (2 * hw * i) / ARC_SEGS;
    const y = yAt(z);
    push(y, z, -y / seat, -z / seat);
  }
  push(yAt(-hw), -hw, 0, -1);
  push(top - c, -hw, 0, -1);
  push(top - c, -hw, s, -s);
  push(top, -(hw - c), s, -s);
  return pts;
}

/**
 * Loft the stations into a closed bar.
 *
 * Every strip gets its own vertices. That is more vertices than a shared-ring loft, but the
 * mesh is under a thousand triangles and it buys exact per-strip normals -- which is the
 * whole reason the step reads as a step. Two of the strips are *walls*: consecutive
 * stations at the same x, where the seat or the top jumps. Their true normal is +-X, so
 * they take the geometric face normal instead of the ring's authored one; everywhere else
 * the ring's analytic normals win, for the reason in `railRing`.
 */
function buildBar(material: THREE.Material): THREE.Mesh {
  const stations: Station[] = [];
  const at = (u: number, seat: number, top: number) => stations.push({ x: xOf(u), seat, top });

  const REAR_STEPS = 4;
  for (let i = 0; i <= REAR_STEPS; i++) {
    at(U_AFT + (U_SEAT_STEP - U_AFT) * (i / REAR_STEPS), SEAT_LATTICE, TOP_AFT);
  }
  // The underside leaves the lattice at its forward face: a rearward-facing annular wall.
  at(U_SEAT_STEP, SEAT_TUBE, TOP_AFT);
  // ... and the top holds its height across the knee before dropping 0.225 D at D-6's step.
  at(U_TOP_STEP, SEAT_TUBE, TOP_AFT);
  at(U_TOP_STEP, SEAT_TUBE, TOP_FORE);
  const FORE_STEPS = 14;
  for (let i = 1; i <= FORE_STEPS; i++) {
    at(U_TOP_STEP + (U_FORE - U_TOP_STEP) * (i / FORE_STEPS), SEAT_TUBE, TOP_FORE);
  }

  const pos: number[] = [], nrm: number[] = [], uv: number[] = [], idx: number[] = [];
  const xSpan = stations[stations.length - 1].x - stations[0].x;

  // Perimeter parameter for v, computed once on the forward ring so v does not slide as the
  // seat radius changes -- a sliding v would make the streaks crawl across the step.
  const refRing = railRing(SEAT_TUBE, TOP_FORE);
  const vAt: number[] = [0];
  for (let k = 1; k < refRing.length; k++) {
    const dy = refRing[k].y - refRing[k - 1].y, dz = refRing[k].z - refRing[k - 1].z;
    vAt.push(vAt[k - 1] + Math.hypot(dy, dz));
  }
  const vTotal = vAt[vAt.length - 1] || 1;

  const ax = new THREE.Vector3(), bx = new THREE.Vector3(), fn = new THREE.Vector3();
  for (let s = 0; s < stations.length - 1; s++) {
    const s0 = stations[s], s1 = stations[s + 1];
    const isWall = Math.abs(s1.x - s0.x) < 1e-9;
    const r0 = railRing(s0.seat, s0.top);
    const r1 = railRing(s1.seat, s1.top);
    const base = pos.length / 3;
    for (const [st, ring] of [[s0, r0], [s1, r1]] as [Station, RingPt[]][]) {
      for (let k = 0; k < ring.length; k++) {
        pos.push(st.x, ring[k].y, ring[k].z);
        nrm.push(0, ring[k].ny, ring[k].nz);
        uv.push((st.x - stations[0].x) / xSpan, vAt[k] / vTotal);
      }
    }
    const n = r0.length;
    for (let k = 0; k < n - 1; k++) {
      const a0 = base + k, a1 = base + k + 1, b0 = base + n + k, b1 = base + n + k + 1;
      ax.set(pos[a1 * 3] - pos[a0 * 3], pos[a1 * 3 + 1] - pos[a0 * 3 + 1], pos[a1 * 3 + 2] - pos[a0 * 3 + 2]);
      bx.set(pos[b1 * 3] - pos[a0 * 3], pos[b1 * 3 + 1] - pos[a0 * 3 + 1], pos[b1 * 3 + 2] - pos[a0 * 3 + 2]);
      fn.crossVectors(ax, bx);
      // Duplicated arris points and the collinear runs on a wall's flanks both land here.
      //
      // The skip leaves four T-junctions, one on each flank plane at each of the two wall
      // stations: the wall's side edge meets a flank edge that spans the same line without
      // a vertex at the break. The surface is closed -- the two short edges cover the long
      // one exactly, verified, so nothing leaks and no crack rasterises -- but 12 edges are
      // index-non-conforming. Splitting them needs a break inserted in every ring at both
      // wall heights and the split then just migrates to the next strip, so it is left and
      // named here instead: if this mesh is ever booleaned or exported as a manifold solid,
      // weld it first.
      if (fn.lengthSq() < 1e-16) continue;
      idx.push(a0, a1, b1, a0, b1, b0);
      if (isWall) {
        fn.normalize();
        for (const v of [a0, a1, b0, b1]) {
          nrm[v * 3] = fn.x; nrm[v * 3 + 1] = fn.y; nrm[v * 3 + 2] = fn.z;
        }
      }
    }
  }

  // End caps. Ear-clipping is fine here and only here: the cap is planar, so every triangle
  // it emits carries the same +-X normal and there is no facet to shatter.
  const cap = (st: Station, forward: boolean) => {
    const ring = railRing(st.seat, st.top);
    const outline: RingPt[] = [];
    for (const p of ring) {
      const last = outline[outline.length - 1];
      if (!last || Math.abs(last.y - p.y) > 1e-12 || Math.abs(last.z - p.z) > 1e-12) outline.push(p);
    }
    const first = outline[0], last = outline[outline.length - 1];
    if (Math.abs(first.y - last.y) < 1e-12 && Math.abs(first.z - last.z) < 1e-12) outline.pop();
    // Seen from +X the screen frame is right = -Z, up = +Y, so a CCW loop in (-z, y) faces +X.
    const c2 = outline.map((p) => new THREE.Vector2(-p.z, p.y));
    if (THREE.ShapeUtils.isClockWise(c2)) { c2.reverse(); outline.reverse(); }
    const base = pos.length / 3;
    for (const p of outline) {
      pos.push(st.x, p.y, p.z);
      nrm.push(forward ? 1 : -1, 0, 0);
      uv.push(0.5 + p.z / (4 * BAR_HALF_W), 0.5 + (p.y - st.seat) / (4 * BAR_T));
    }
    for (const f of THREE.ShapeUtils.triangulateShape(c2, [])) {
      if (forward) idx.push(base + f[0], base + f[1], base + f[2]);
      else idx.push(base + f[2], base + f[1], base + f[0]);
    }
  };
  cap(stations[0], false);
  cap(stations[stations.length - 1], true);

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);

  const mesh = new THREE.Mesh(geo, material);
  mesh.name = PART.rail;
  return mesh;
}

/* ------------------------------------------------------- mount block, studs, hook */

/**
 * Replace an ExtrudeGeometry's UVs with a planar (x, y) projection so the brushed streaks
 * run along the barrel on these parts too. Three's default extrude UV generator maps the
 * walls by their own path length, which sends the streaks around the section instead.
 */
function planarUv(geo: THREE.BufferGeometry, scaleX: number, scaleY: number): void {
  const p = geo.getAttribute('position');
  const uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    uv[i * 2] = p.getX(i) / scaleX;
    uv[i * 2 + 1] = p.getY(i) / scaleY;
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

/**
 * The mount block as a saddle: its section is traced in the Z-Y plane and swept along X, so
 * its legs come down over the bar's flanks rather than sitting on top of it as a floating
 * cube. The legs stop at 0.52 D -- clear of the tube at 1.12 R, and hidden in silhouette
 * behind the bar's own dished flanks, which dip to 0.47 D.
 */
function buildMount(material: THREE.Material): THREE.Mesh {
  const outerHalf = MOUNT_HALF_W, innerHalf = BAR_HALF_W;
  const shape = new THREE.Shape();
  shape.moveTo(-outerHalf, MOUNT_FOOT);
  shape.lineTo(-outerHalf, MOUNT_TOP);
  shape.lineTo(outerHalf, MOUNT_TOP);
  shape.lineTo(outerHalf, MOUNT_FOOT);
  shape.lineTo(innerHalf, MOUNT_FOOT);
  shape.lineTo(innerHalf, TOP_FORE);
  shape.lineTo(-innerHalf, TOP_FORE);
  shape.lineTo(-innerHalf, MOUNT_FOOT);
  shape.closePath();

  // Small on purpose. The notch has two concave corners and a bevel that approaches the leg
  // thickness self-intersects there and spikes into a bright white crease.
  const bevel = 0.0012;
  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: MOUNT_LEN - 2 * bevel,
    bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2,
    curveSegments: 1,
  });
  // Shape (a, b) extruded along +c; rotateY(+90) sends (a,b,c) -> (c, b, -a), i.e. the
  // extrusion axis becomes X and the traced section lands in the Z-Y plane.
  geo.rotateY(Math.PI / 2);
  geo.translate(xOf(U_MOUNT) - MOUNT_LEN / 2 + bevel, 0, 0);
  planarUv(geo, MOUNT_LEN * 4, D);

  const mesh = new THREE.Mesh(geo, material);
  mesh.name = PART.railMount;
  return mesh;
}

/** A stud is a revolved dome, which is what `LatheGeometry` exists for. It closes on the
 *  axis at both ends so nothing shows through at a grazing angle. */
function studGeometry(): THREE.BufferGeometry {
  const profile: THREE.Vector2[] = [new THREE.Vector2(0, STUD_H)];
  const SEGS = 3;
  for (let i = 1; i <= SEGS; i++) {
    const t = (i / SEGS) * (Math.PI / 2);
    profile.push(new THREE.Vector2(STUD_R * Math.sin(t), STUD_H * Math.cos(t)));
  }
  profile.push(new THREE.Vector2(STUD_R, -0.15 * STUD_H));
  profile.push(new THREE.Vector2(0, -0.15 * STUD_H));
  // 12 radial segments on a 3.7 px feature. At 16 the three studs cost more triangles than
  // the whole stepped bar, which is the wrong place to spend them.
  return new THREE.LatheGeometry(profile, 12);
}

/**
 * The hook, traced in X-Y and extruded through Z.
 *
 * It curves FORWARD -- the contract says so twice, in the assembly tree and in J4, and it is
 * the detail that makes this not a rear sight. The throat therefore opens toward the muzzle,
 * and the foot occupies only the rear 42 % of the span so the rest overhangs.
 */
function buildHook(material: THREE.Material): THREE.Mesh {
  const xR = xOf(U_AFT);
  const xF = xOf(U_AFT - HOOK_LEN_U);
  const len = xF - xR;
  const h = HOOK_TOP - HOOK_BASE;
  const yB = HOOK_BASE, yT = HOOK_TOP;

  const s = new THREE.Shape();
  s.moveTo(xR, yB);
  s.lineTo(xR + 0.42 * len, yB);
  // Throat: the underside of the overhang, concave and opening forward.
  s.quadraticCurveTo(xR + 0.60 * len, yB + 0.10 * h, xR + 0.72 * len, yB + 0.38 * h);
  s.quadraticCurveTo(xR + 0.86 * len, yB + 0.62 * h, xF, yB + 0.46 * h);
  // The tip, curling down-forward.
  s.lineTo(xF, yB + 0.72 * h);
  // Back over the crest to the rear post.
  s.quadraticCurveTo(xR + 0.55 * len, yT, xR + 0.16 * len, yT);
  s.quadraticCurveTo(xR, yT, xR, yT - 0.22 * h);
  s.lineTo(xR, yB);

  const bevel = 0.0008;
  const geo = new THREE.ExtrudeGeometry(s, {
    depth: 2 * HOOK_HALF_T - 2 * bevel,
    bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2,
    curveSegments: 5,
  });
  // The bevel grows the traced outline outward, which would put the hook's rear face 0.8 mm
  // aft of the breech plane. H5 fixes the hook at the rail's min.x, so shift it back on.
  geo.translate(bevel, 0, -(HOOK_HALF_T - bevel));
  planarUv(geo, len * 3, D);

  const mesh = new THREE.Mesh(geo, material);
  mesh.name = PART.railHook;
  return mesh;
}

/* ------------------------------------------------------------------------ assembly */

/**
 * The rail assembly.
 *
 * The returned Group is deliberately NOT named `PART.rail`. `barrel.rail` belongs to the bar
 * mesh, and `tools/check_contract.py` evaluates `barrel.rail.proud.overTubeOd` and
 * `barrel.rail.axialSpan` off that name's world bbox. A group carrying the same name would
 * shadow the mesh for `getObjectByName` and hand those rows a bbox that includes the hook,
 * which stands 0.2 D higher than the bar does.
 */
export function buildRail(): THREE.Group {
  const group = new THREE.Group();
  group.name = `${PART.rail}.assembly`;

  // Exactly two of `mat.count.total`'s seven structural materials are introduced here, and
  // the studs share the bar's brass rather than claiming a third: no row measures a stud,
  // and the material/variant boundary is DECLARED, so spending a slot on one would inflate
  // that count against nothing.
  const maps = brassMaps();
  const brass = standardMaterial(BRASS_YELLOW, 0.22, 0.42, maps);
  const red = standardMaterial(MOUNT_RED, 0.12, 0.55, maps);

  group.add(buildBar(brass));
  group.add(buildMount(red));
  group.add(buildHook(brass));

  // Index order follows the contract, not the sheet: H1 and H5 both name `rail.stud[2]` as
  // the forward one and `rail.stud[0..1]` as the mount-block pair, and the edit handles are
  // written against those indices. Within the pair, index increases forward.
  const studGeo = studGeometry();
  const seats: { u: number; y: number }[] = [
    { u: U_STUD_AFT, y: MOUNT_TOP },
    { u: U_STUD_MID, y: MOUNT_TOP },
    { u: U_STUD_FORE, y: TOP_FORE },
  ];
  seats.forEach((seat, i) => {
    const stud = new THREE.Mesh(studGeo, brass);
    stud.name = `${PART.railStud}.${i}`;
    stud.position.set(xOf(seat.u), seat.y, 0);
    group.add(stud);
  });

  // §7's third socket, "on the mount block's top face, +Y up". Not a mesh, so it carries no
  // PART name; the assembler can lift it out of userData without traversing for it.
  const socket = new THREE.Object3D();
  socket.name = 'socket.rail';
  socket.position.set(xOf(U_MOUNT), MOUNT_TOP, 0);
  group.add(socket);
  group.userData.sockets = { 'socket.rail': socket };

  return group;
}
