/**
 * The frame group: receiver, port (+ flange), hammer spur, trigger, trigger guard.
 *
 * Everything behind the barrel/frame junction at x = 0 and forward of the grip.
 * Contract §6.8, plus §7's J1/J2, plus §8 H3's rake pivot.
 *
 * This is the part of the object the reference resolves worst, and §10.8-10.9 say so:
 * "the receiver's underside and true height, its forward face, and any rivet, pin or
 * panel line on it -- nothing on the receiver exceeds 3 px in any pose", and "the
 * trigger guard's shape ... every dimension of it is DECLARED". So the honest way to
 * build this group is to derive every station from a §6.8 row or from a joint, and to
 * name the handful of quantities that come from nowhere. They are collected in
 * `DECLARED` below and nowhere else.
 *
 * ---------------------------------------------------------------------------
 * IDIOM
 *
 * Traced profiles through ExtrudeGeometry and LatheGeometry, as in the Talon demo --
 * not primitives stacked in a hierarchy. Two of that demo's lessons carry directly:
 *
 *  - Constant thickness reads as a toy cutout the moment it rotates. The receiver and
 *    the spur are extrudes whose every cap vertex Z is warped by a crown field, so the
 *    frame is pillowed and the spur tapers toward its tip.
 *  - Ear-clipping shatters facet normals, so the warped caps get ANALYTIC normals from
 *    the field gradient. The walls keep the extruder's own normals, which stay exactly
 *    right: a pure-Z warp leaves the side surface a cylinder over the 2-D profile, so
 *    its normal is still the profile normal. Nothing here calls computeVertexNormals.
 *  - bevelEnabled is off on the warped parts. The Talon note is that a bevel
 *    self-intersects on concave corners and spikes into bright white creases; the
 *    receiver profile has four concave corners (the pivot post's two roots and the
 *    breech shoulder), so the crown field supplies the edge softness instead by falling
 *    to 0.38 of its peak at the profile boundary. The two thin parts -- guard and
 *    trigger -- are 8-16 px features with no concave corners, and take a real bevel of
 *    0.0012 m.
 *
 * ---------------------------------------------------------------------------
 * FINISH
 *
 * The reference is a measurement target only, so the Talon projected-plate technique is
 * the one thing that does not transfer: no pixel of it may land on this model. Colour
 * therefore comes from §6.10's CIE Lab numbers through `labToSrgb()` below, and the
 * only generated texture is a canvas-drawn ROUGHNESS map. Albedo is left as the exact
 * measured value with no `map`, so `check_contract.py`'s [MAT] check -- which reads the
 * assigned base colour and converts it back to Lab -- round-trips to the numbers it is
 * testing against rather than to whatever a texture averaged out to.
 *
 * What that costs, precisely: §6.10 records that no whole part on this object is a flat
 * colour sample, and that the p5-p95 L* span of every part is 35-52 -- painted
 * terminator ramp, not sampling error. A projected de-lit plate would carry that ramp,
 * the paint chips and the grime in the albedo itself. A single measured Lab value
 * cannot, so the whole of `shading.ramp`'s >= 30 L* span has to be produced by the light
 * rig, which is exactly why the contract marks that row "Partly DECLARED -- conditional
 * on reproducing that lighting". The finish here is honest about hue and chroma and
 * silent about everything the painter did with value.
 */
import * as THREE from 'three';
import { D, R, PART, xOf } from './datum.js';

/* ==========================================================================
 * Choices the reference cannot adjudicate. Every number in this block is a
 * DECLARATION, not a reading; §10 is why.
 * ========================================================================== */
const DECLARED = {
  /** Receiver width across (Z). Floor: it must enclose the breech of a 1.00 D tube.
   *  Ceiling: `gun.maxWidth.isLatticeCollar` keeps the 1.45 D lattice the widest thing
   *  on the object. 1.02 D is the floor plus a wall, and §10.29 says no view can
   *  measure it -- there is no top view and no orthographic muzzle-on view. */
  receiverWidth: 1.02 * D,
  /** Guard bar thickness across. §10.9: every guard dimension is DECLARED. */
  guardThickness: 0.110 * D,
  /** Trigger blade thickness. The blade is 8x15 px in the one view that shows it;
   *  its third dimension is not in any view. */
  triggerThickness: 0.100 * D,
  /** Hammer-spur peak thickness. Held BELOW the spur's in-plane minor width (0.122 D)
   *  on purpose: if the plate were thicker than it is wide, the spur's second-longest
   *  extent would become its thickness and `frame.spur.aspect` would be measuring the
   *  wrong pair of numbers. */
  spurThickness: 0.095 * D,
  /** Pivot-post width. `frame.spur.clearance` allows the spur to touch the frame only
   *  at a neck <= 0.45 x its own diameter; 0.040 D against the spur's 0.122 D minor
   *  width is 0.33 of it. At §6.1's 1.400 mm/px this post is 1.5 px wide, which is why
   *  §10.13 could not see a hinge pin: "a hinge pin would be 1-2 px". */
  pivotPostWidth: 0.040 * D,
  /** Hammer rib count, `frame.hammer.ribs.count` = 6 +- 2. Modelled as serrations in
   *  the spur's own traced profile rather than as child meshes -- see NOTE 4. */
  spurSerrations: 6,
} as const;

/* ==========================================================================
 * Stations. Each cites the row it comes from.
 * ========================================================================== */

/** `frame.receiverRear.u` = 0.955 +- 0.020. */
const X_RECEIVER_REAR = xOf(0.955);
/** `frame.port.centre.u` = 0.884 +- 0.030. */
const X_PORT = xOf(0.884);

/**
 * D-10, decided.
 *
 * `frame.top.aboveAxis` states 0.32 +- 0.10 D as a LOCAL reading at the receiver's rear
 * but checks `receiver AABB max-up / D`, and the auditor measures that maximum at
 * 0.47-0.67 D because the receiver rises forward. The row and its check disagree.
 *
 * The auditor's number cannot be the build target either, and this is the argument that
 * settles it: `frame.topBelowBarrelTop` requires receiver max-up < tube max-up, and the
 * tube top is at exactly 0.50 D. Every value in 0.47-0.67 D either violates that row
 * outright or sits inside its noise. The two rows' bands intersect only over
 * [0.28, 0.42] D:
 *
 *      frame.top.aboveAxis     0.32 +- 0.10  ->  [0.22, 0.42]
 *      frame.topBelowBarrelTop 0.50 - (0.13 +- 0.09) -> [0.28, 0.46]
 *
 * So the receiver is built with its AABB maximum at 0.350 D -- inside both -- and the
 * forward rise the audit describes is kept as SHAPE: 0.350 D at the standing breech
 * falling to a 0.215 D top strap over the rear two thirds. The audit's observation is
 * honoured (the receiver does rise forward); its magnitude is not, because no magnitude
 * in the range it reports can pass the contract's own adjacent row.
 */
const RECEIVER_TOP = 0.350 * D;
/** Top strap, aft of the standing breech. Set by the hammer, not by a row: it is
 *  RECEIVER_TOP minus whatever is needed to keep the whole of J1's declared swing clear
 *  of the frame. See NOTE 1. */
const RECEIVER_TOPSTRAP = 0.215 * D;

/**
 * Frame underside. Not measured -- §10.8 says the receiver's underside is occluded in
 * every view and `frame.heightOverTubeOd` is explicitly "a lower bound, not a target"
 * because "the lower edge is where the hand starts".
 *
 * Derived instead from the grip, which the reference does resolve at its butt:
 *
 *      grip.heelDrop.overTubeOd  = 2.19 D below the axis
 *      grip.length.overTubeOd    = 1.55 D along the grip axis
 *      grip.rakeFromBore         = 107 deg from the bore's forward direction
 *      vertical run of the grip  = 1.55 * sin(107 deg) = 1.482 D
 *      grip top face             = -(2.19 - 1.482) D  = -0.708 D
 *
 * `grip.root.flushWithFrame` then demands |grip max-up - frame min-up| <= 0.03 D, so the
 * frame's underside is that number. It also lands the frame's height at
 * 0.350 + 0.710 = 1.060 D, just over `frame.heightOverTubeOd`'s >= 1.05 floor -- which
 * is a genuine corroboration, since nothing in the derivation used that row.
 */
const FRAME_BOTTOM = -0.710 * D;

/**
 * J1, the hammer pivot. Row: u = 0.92 +- 0.04, +0.6 +- 0.3 R, z = 0.
 *
 * Both coordinates are moved inside their bands rather than to their centres, and each
 * move buys a specific row:
 *
 *  - u 0.935 rather than 0.92, so the spur's pivot boss clears the port's rear face.
 *    At u 0.92 the boss and the port's 0.35 D cylinder interpenetrate; the two are the
 *    two protrusions `frame.protrusionsAbove.count` counts, and two protrusions that
 *    intersect are one protrusion.
 *  - +0.84 R rather than +0.6 R, so the boss's underside clears
 *    `frame.protrusionsAbove.count`'s own threshold of (receiver max-up - 0.10 D) =
 *    0.25 D. At +0.6 R the boss bottom is 0.21 D and the spur does not register as a
 *    protrusion at all -- the check would return 1, which is what D-4 reports pose3
 *    showing. +0.75 R is not enough either, and the reason is worth writing down: the
 *    render harness measures with `Box3.setFromObject`, which for a ROTATED mesh
 *    transforms the eight corners of the local box rather than the vertices, and the
 *    spur is the only rotated mesh in this group. That overestimates its downward extent
 *    by 0.035 D and lands it exactly on the threshold. The margin below is sized against
 *    the number the harness will actually report, not the one the mesh actually has.
 */
const PIVOT_HAMMER = new THREE.Vector2(xOf(0.935), 0.84 * R);
/** `frame.spur.attitude` = 32 +- 8 deg above the bore, pointing rearward. 34 deg is the
 *  PCA figure the row cites as its own evidence, and is inside the band. */
const SPUR_ATTITUDE = THREE.MathUtils.degToRad(34);

/**
 * J2, the trigger pivot. Row: u = 0.824 +- 0.030, -1.40 +- 0.20 R, z = 0.
 *
 * u is taken at 0.845 -- inside the band, at the rear of it. At the row's 0.824 the
 * blade fouls the guard's forward leg, and moving the leg forward instead would carry
 * the guard out past u 0.79 under the barrel for no reason the reference supports. The
 * vertical stays at the row's centre: -1.40 R = -0.700 D puts the pivot 0.010 D inside
 * the frame's underside, which is where a trigger pivot belongs.
 */
const PIVOT_TRIGGER = new THREE.Vector2(xOf(0.845), -1.40 * R);

/**
 * §8 H3 declares the grip's rake pivot "at the trigger guard's rear attach",
 * (u 0.815, -2.4 R, 0) -- and D-22 uses that to argue `frame.trigger.insideGuard`
 * cannot hold, because J2 puts the trigger at u 0.824, rearward of it.
 *
 * D-22 is right about the arithmetic and wrong about which end of the guard that point
 * is. §3 describes the guard as "a bow from the frame's underside to the grip root":
 * the frame's underside is FORWARD, the grip root is AFT, so u 0.815 is the guard's
 * forward attach and H3's label is the error. Built that way -- forward attach at
 * u ~0.805, rear attach at u ~0.912 -- the trigger at u 0.845 falls between them and the
 * containment row holds. H3's declared point still lies inside the guard's material
 * (the assertion below is what keeps it there), so the rake handle stays local.
 */
const H3_RAKE_PIVOT = new THREE.Vector2(xOf(0.815), -2.4 * R);

/* ==========================================================================
 * Colour. §6.10's Lab numbers, converted here rather than pasted as hex.
 * ========================================================================== */

/** CIE L*a*b* (D65) to an sRGB hex integer, inverting exactly the transform
 *  `check_contract.py:srgb_to_lab` applies, so a [MAT] row reads back what it was
 *  given. */
function labToSrgb(L: number, a: number, b: number): number {
  const fy = (L + 16) / 116;
  const fx = fy + a / 500;
  const fz = fy - b / 200;
  const finv = (t: number) => (t > 6 / 29 ? t * t * t : 3 * (6 / 29) * (6 / 29) * (t - 4 / 29));
  const X = 0.95047 * finv(fx);
  const Y = 1.0 * finv(fy);
  const Z = 1.08883 * finv(fz);
  const lin = [
    X * 3.2406 + Y * -1.5372 + Z * -0.4986,
    X * -0.9689 + Y * 1.8758 + Z * 0.0415,
    X * 0.0557 + Y * -0.204 + Z * 1.057,
  ];
  let hex = 0;
  for (const c of lin) {
    const u = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(Math.max(c, 0), 1 / 2.4) - 0.055;
    hex = (hex << 8) | THREE.MathUtils.clamp(Math.round(u * 255), 0, 255);
  }
  return hex;
}

/** Polar Lab: §6.10 states the brasses as hue and chroma, so state them that way here
 *  too rather than pre-multiplying into a* and b* by hand. */
function labPolar(L: number, hueDeg: number, chroma: number): number {
  const h = THREE.MathUtils.degToRad(hueDeg);
  return labToSrgb(L, chroma * Math.cos(h), chroma * Math.sin(h));
}

/**
 * The generated finish: a grayscale roughness field. Albedo is untouched.
 *
 * Drawn rather than proceduralised in the shader because the reference's wear is
 * blotchy and directional, and value noise reads as sand. `mat.warmTube.notWood`
 * measures the painted zones as SMOOTHER than the plain tube (residual sd 7.18 vs
 * 9.19), so the amplitude here is deliberately low -- a loud wear map would be
 * inventing a surface the one texture statistic in the contract says is not there.
 */
function roughnessField(seed: number, base: number, amount: number): THREE.Texture | null {
  if (typeof document === 'undefined') return null;
  const S = 256;
  const cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const g = cv.getContext('2d');
  if (!g) return null;
  const v = Math.round(base * 255);
  g.fillStyle = `rgb(${v},${v},${v})`;
  g.fillRect(0, 0, S, S);
  // Deterministic: two passes of soft blotches, then a fine speckle. A Math.random()
  // here would give a different asset every reload and make any render comparison
  // between passes meaningless.
  let s = seed >>> 0;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let pass = 0; pass < 2; pass++) {
    const r0 = pass === 0 ? 34 : 12;
    const n = pass === 0 ? 26 : 90;
    for (let i = 0; i < n; i++) {
      const x = rnd() * S;
      const y = rnd() * S;
      const r = r0 * (0.4 + rnd());
      const d = (rnd() * 2 - 1) * amount * 255;
      const grad = g.createRadialGradient(x, y, 0, x, y, r);
      const c = THREE.MathUtils.clamp(v + d, 0, 255) | 0;
      grad.addColorStop(0, `rgba(${c},${c},${c},0.55)`);
      grad.addColorStop(1, `rgba(${c},${c},${c},0)`);
      g.fillStyle = grad;
      g.beginPath();
      g.arc(x, y, r, 0, Math.PI * 2);
      g.fill();
    }
  }
  const tex = new THREE.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(3, 3);
  return tex;
}

/**
 * Exactly three material slots leave this module, and each is one of the seven
 * structural slots `mat.count.total` budgets for the whole object -- the receiver shares
 * the frame/grip paint, the port and spur share the aged brass, and the port's flange
 * shares the rail mount block's red. Minting a fourth here would spend a slot the rest
 * of the model needs.
 *
 * Metalness is DECLARED. §10.26: "Any PBR parameter -- metalness, roughness. The texture
 * is hand-painted and stylised; highlights are 2-6 px." Brass is held at 0.35 rather
 * than a physical 0.9 because above about 0.5 the diffuse term vanishes and the
 * environment replaces the measured albedo entirely, which would make `area.brassShare`
 * and `shading.ramp` -- both [SIL] render checks -- read the studio instead of the
 * object.
 */
function frameMaterials() {
  // mat.paint.frame.greener: a*(frame) <= a*(tube) - 1.5, and mat.paint.tube.ab puts the
  // tube at a* -1.5. -4.2 is pose0's direct reading of the frame in the same image and
  // the same light. b* follows the tube's -7.0; nothing separates them in b*.
  const paint = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setHex(labToSrgb(36.0, -4.2, -7.0), THREE.SRGBColorSpace),
    roughness: 0.62,
    metalness: 0.0,
  });
  // mat.brass.aged.hue = 66.5 +- 5 deg; chroma 20.2 is pose3's own figure from
  // mat.warmTube.notBrass. NOT the yellow brass at 79 deg -- that row's evidence is
  // "on rail + rear hook", neither of which is in this group.
  const brass = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setHex(labPolar(46.0, 66.5, 20.2), THREE.SRGBColorSpace),
    roughness: 0.42,
    metalness: 0.35,
  });
  // mat.mount.red.hue = 37 +- 7 deg. Chroma held at 21.0 rather than higher because
  // mat.accent.outchroma needs every accent to reach 1.7x the largest structural
  // chroma, and 21.6 is the ceiling that row was measured against.
  const red = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setHex(labPolar(44.0, 37.0, 21.0), THREE.SRGBColorSpace),
    roughness: 0.48,
    metalness: 0.30,
  });
  const rPaint = roughnessField(0x5ea1, 0.62, 0.13);
  const rBrass = roughnessField(0x2b71, 0.42, 0.17);
  if (rPaint) paint.roughnessMap = rPaint;
  if (rBrass) { brass.roughnessMap = rBrass; red.roughnessMap = rBrass; }
  return { paint, brass, red };
}

/* ==========================================================================
 * Extrusion with a thickness field.
 * ========================================================================== */

type Field = (x: number, y: number) => number;

/**
 * Extrude a shape, subdivide the caps, warp them by a half-thickness field, and give
 * the cap vertices analytic normals.
 *
 * Subdivision first, because ExtrudeGeometry's caps come out of an ear-clipper as long
 * slivers: warping those linearly flattens the crown into facets exactly where the
 * crown is supposed to be smoothest. `levels` is per-part -- the receiver's cap is the
 * largest flat area on the object and takes 2 (x16 triangles); the spur takes 1.
 *
 * Normals are closed-form, not computed:
 *   caps  z = +-h(x,y)  ->  n = normalize(-h_x, -h_y, +-1)
 *   walls the surface is still a cylinder over the 2-D profile after a pure-Z warp, so
 *         the extruder's own (nx, ny, 0) is already exact and is left alone.
 * ExtrudeGeometry tags the caps as group 0 and the walls as group 1, which is what
 * separates them here.
 */
function warpedExtrude(shape: THREE.Shape, half: Field, levels: number): THREE.BufferGeometry {
  // Depth is a placeholder: every cap vertex is about to be moved to +-h anyway. It only
  // has to be non-zero so the extruder builds two distinct cap planes.
  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: 0.01, bevelEnabled: false, curveSegments: 6, steps: 1,
  });
  geo.translate(0, 0, -0.005);

  const capGroup = geo.groups.find((g) => g.materialIndex === 0);
  const pos = geo.getAttribute('position') as THREE.BufferAttribute;
  const nrm = geo.getAttribute('normal') as THREE.BufferAttribute;
  const uv = geo.getAttribute('uv') as THREE.BufferAttribute;

  const P: number[] = [];
  const N: number[] = [];
  const U: number[] = [];
  const capStart = capGroup ? capGroup.start : 0;
  const capEnd = capGroup ? capGroup.start + capGroup.count : 0;

  // Walls pass through untouched except for the Z of their endpoints, done below.
  for (let i = 0; i < pos.count; i++) {
    if (i >= capStart && i < capEnd) continue;
    P.push(pos.getX(i), pos.getY(i), pos.getZ(i));
    N.push(nrm.getX(i), nrm.getY(i), nrm.getZ(i));
    U.push(uv.getX(i), uv.getY(i));
  }
  const wallCount = P.length / 3;

  // Caps, subdivided by repeated midpoint split.
  let tris: number[][] = [];
  for (let i = capStart; i < capEnd; i += 3) {
    tris.push([
      pos.getX(i), pos.getY(i), pos.getZ(i),
      pos.getX(i + 1), pos.getY(i + 1), pos.getZ(i + 1),
      pos.getX(i + 2), pos.getY(i + 2), pos.getZ(i + 2),
    ]);
  }
  for (let lvl = 0; lvl < levels; lvl++) {
    const out: number[][] = [];
    for (const t of tris) {
      const [ax, ay, az, bx, by, bz, cx, cy, cz] = t;
      const abx = (ax + bx) / 2, aby = (ay + by) / 2, abz = (az + bz) / 2;
      const bcx = (bx + cx) / 2, bcy = (by + cy) / 2, bcz = (bz + cz) / 2;
      const cax = (cx + ax) / 2, cay = (cy + ay) / 2, caz = (cz + az) / 2;
      out.push([ax, ay, az, abx, aby, abz, cax, cay, caz]);
      out.push([abx, aby, abz, bx, by, bz, bcx, bcy, bcz]);
      out.push([cax, cay, caz, bcx, bcy, bcz, cx, cy, cz]);
      out.push([abx, aby, abz, bcx, bcy, bcz, cax, cay, caz]);
    }
    tris = out;
  }

  const e = 1e-5;
  for (const t of tris) {
    for (let k = 0; k < 3; k++) {
      const x = t[k * 3], y = t[k * 3 + 1];
      const s = t[k * 3 + 2] >= 0 ? 1 : -1;
      const h = half(x, y);
      const hx = (half(x + e, y) - half(x - e, y)) / (2 * e);
      const hy = (half(x, y + e) - half(x, y - e)) / (2 * e);
      const n = new THREE.Vector3(-hx, -hy, s).normalize();
      P.push(x, y, s * h);
      N.push(n.x, n.y, n.z);
      U.push(x, y);
    }
  }

  // The walls' endpoints have to land on the same warped cap rim, or the shell opens.
  for (let i = 0; i < wallCount; i++) {
    const x = P[i * 3], y = P[i * 3 + 1];
    P[i * 3 + 2] = (P[i * 3 + 2] >= 0 ? 1 : -1) * half(x, y);
  }

  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
  out.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
  return out;
}

/** A crown that falls to 0.38 of its peak at the profile's edge. This is what replaces
 *  a bevel on the parts whose profiles have concave corners. */
function crownField(cx: number, cy: number, ax: number, ay: number, peak: number): Field {
  return (x, y) => {
    const q = ((x - cx) / ax) ** 2 * 0.55 + ((y - cy) / ay) ** 2 * 0.9;
    const t = Math.sqrt(THREE.MathUtils.clamp(1 - q, 0, 1));
    return peak * (0.38 + 0.62 * t);
  };
}

/**
 * Offset a polyline both ways into a closed loop -- the guard's bow, and nothing else in
 * this file needs it. Ends are cut square, which is right: both of the guard's ends are
 * let into the frame and never seen.
 *
 * The `keep` filter is not defensive coding, it is the whole difficulty of the routine.
 * Offsetting a polyline inward by more than its local radius of curvature makes the
 * inner edge cross itself, and the triangulator turns that crossing into a dart -- a
 * thin spike of geometry pointing into the guard's opening, which is exactly where the
 * trigger has to travel. Dropping any offset point that does not advance along the
 * tangent removes the fold without touching the outer edge. The bow's centreline is also
 * laid out with a minimum radius of about 0.009 m against a 0.0029 m half-width, so the
 * filter should have nothing to do; it is here because "should" is not a test.
 */
function ribbon(pts: THREE.Vector2[], half: number, samples: number): THREE.Shape {
  const curve = new THREE.CatmullRomCurve3(
    pts.map((p) => new THREE.Vector3(p.x, p.y, 0)), false, 'catmullrom', 0.5,
  );
  const line = curve.getPoints(samples);
  const tans: THREE.Vector2[] = [];
  for (let i = 0; i < line.length; i++) {
    const a = line[Math.max(i - 1, 0)];
    const b = line[Math.min(i + 1, line.length - 1)];
    tans.push(new THREE.Vector2(b.x - a.x, b.y - a.y).normalize());
  }
  const side = (sign: number) => {
    const out: THREE.Vector2[] = [];
    for (let i = 0; i < line.length; i++) {
      const t = tans[i];
      const p = new THREE.Vector2(line[i].x + sign * t.y * half, line[i].y - sign * t.x * half);
      const prev = out[out.length - 1];
      if (prev && (p.x - prev.x) * t.x + (p.y - prev.y) * t.y <= 0) continue;
      out.push(p);
    }
    return out;
  };
  return new THREE.Shape(side(1).concat(side(-1).reverse()));
}

function shapeOf(pts: number[][]): THREE.Shape {
  const s = new THREE.Shape();
  s.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) s.lineTo(pts[i][0], pts[i][1]);
  s.closePath();
  return s;
}

/* ==========================================================================
 * Build
 * ========================================================================== */

export function buildFrameParts(): THREE.Group {
  const group = new THREE.Group();
  group.name = PART.frame;
  const M = frameMaterials();

  /* ---------------------------------------------------------------- receiver */

  const postHalf = DECLARED.pivotPostWidth / 2;
  const postX = PIVOT_HAMMER.x;
  // Boss underside, which the post has to reach. See NOTE 1.
  const bossR = 0.090 * D;
  const postTop = PIVOT_HAMMER.y - bossR;

  const receiverProfile: number[][] = [
    // Standing breech: the tallest point, at the barrel/frame junction.
    [0.0, RECEIVER_TOP],
    [-0.00260, RECEIVER_TOP],
    [-0.00560, 0.330 * D],
    [-0.00860, 0.288 * D],
    [-0.01120, 0.243 * D],
    [-0.01300, 0.219 * D],
    // Top strap.
    [-0.01700, RECEIVER_TOPSTRAP],
    [postX + postHalf + 0.0006, RECEIVER_TOPSTRAP],
    // Pivot post. Part of the receiver's own outline, NOT a child mesh: a child with a
    // bounding diagonal over 0.02 L would break `frame.surfaceFeatures.count` = 0.
    [postX + postHalf, postTop - 0.0004],
    [postX + postHalf - 0.0004, postTop],
    [postX - postHalf + 0.0004, postTop],
    [postX - postHalf, postTop - 0.0004],
    [postX - postHalf - 0.0006, RECEIVER_TOPSTRAP],
    [X_RECEIVER_REAR, RECEIVER_TOPSTRAP],
    // Rear face. `frame.rearFace.angle`: within 15 deg of the axis normal over its lower
    // 60 %. Vertical from the top strap down to -0.56 D, i.e. over 82 % of that band.
    [X_RECEIVER_REAR, -0.560 * D],
    [X_RECEIVER_REAR + 0.0008, -0.660 * D],
    [X_RECEIVER_REAR + 0.0031, -0.706 * D],
    // Underside. `grip.root.flushWithFrame`'s evidence is "pose3's frame underside is one
    // unbroken dark line at y 288-293 with no gap or step", so there is no trigger slot
    // here and the blade's top simply disappears into the frame.
    [X_RECEIVER_REAR + 0.0066, FRAME_BOTTOM],
    [-0.00600, FRAME_BOTTOM],
    [-0.00280, -0.700 * D],
    [-0.00050, -0.660 * D],
    // Breech face, on the plane x = 0.
    [0.0, -0.600 * D],
  ];

  const rcx = X_RECEIVER_REAR / 2;
  const rcy = (RECEIVER_TOP + FRAME_BOTTOM) / 2;
  const receiver = new THREE.Mesh(
    warpedExtrude(
      shapeOf(receiverProfile),
      crownField(rcx, rcy, Math.abs(X_RECEIVER_REAR) * 0.72,
        (RECEIVER_TOP - FRAME_BOTTOM) * 0.60, DECLARED.receiverWidth / 2),
      2,
    ),
    M.paint,
  );
  receiver.name = PART.receiver;
  group.add(receiver);

  /* -------------------------------------------------------------------- port */

  /**
   * D-3, decided.
   *
   * `frame.port.od` states 0.41 +- 0.07 D; the auditor re-measures the port at 12-13 px
   * and gets 0.33 D, below the row's 0.34 floor. Neither number has to lose. At §6.2's
   * D = 37 px, 0.35 D is 12.95 px -- dead inside the auditor's own 12-13 px reading --
   * and it is also inside the row's band with 0.01 D to spare. It is the one value that
   * satisfies the measurement and the constraint at once, so it is not a split of the
   * difference; it is the intersection.
   */
  const portOd = 0.350 * D;
  const portR = portOd / 2;
  const flangeR = 0.700 * portOd; // ".flange: orange base flange, ~1.4x port OD"
  const flangeBase = RECEIVER_TOPSTRAP;
  const flangeTop = 0.305 * D;
  // `frame.port.heightOverOd` = 1.3 +- 0.4, checked as
  // (port max-up - RECEIVER max-up) / port OD. Note whose maximum: the standing breech at
  // 0.350 D, not the top strap the port actually stands on. That is D-10's defect
  // propagating into a second row -- a receiver built with the forward rise the audit
  // describes has to grow its port by the height of the rise to hit the same ratio, and
  // §3's "short brass cylinder" stops being short.
  //
  // Resolved by taking 1.0, which is the row's own pose3 figure, rather than 1.3, which is
  // a mean across poses whose out-of-plane angles differ by 29 degrees. §2 designates
  // pose3 the primary view precisely because it is the only near-orthographic one, and
  // 1.0 is inside the row's band. The port then stands 1.13 x its own diameter above its
  // flange and reads as the part the tree describes.
  const portTop = RECEIVER_TOP + 1.0 * portOd;
  // `frame.port.hollow`: top face recessed, bore/OD 0.45 +- 0.15. §10.19 records this as
  // unsettled -- "5 interior pixels against a 2 px rim, in one pose, read oppositely by
  // two reports" -- and its check is [RAY], which check_contract.py does not implement
  // and scores as a failure either way. Built hollow because that is what the row says;
  // the cost of being wrong is a 4 mm recess nobody can see.
  const portBore = 0.45 * portOd;
  const portFloor = portTop - 0.20 * D;

  const port = new THREE.Mesh(
    new THREE.LatheGeometry([
      new THREE.Vector2(0, flangeTop),
      new THREE.Vector2(portR, flangeTop),
      new THREE.Vector2(portR, portTop - 0.020 * D),
      new THREE.Vector2(portR * 0.97, portTop),
      new THREE.Vector2(portBore + 0.0008, portTop),
      new THREE.Vector2(portBore, portTop - 0.010 * D),
      new THREE.Vector2(portBore, portFloor + 0.0008),
      new THREE.Vector2(portBore * 0.6, portFloor),
      new THREE.Vector2(0, portFloor),
    ], 28),
    M.brass,
  );
  port.name = PART.port;
  port.position.x = X_PORT;
  group.add(port);

  const flange = new THREE.Mesh(
    new THREE.LatheGeometry([
      new THREE.Vector2(0, flangeBase),
      new THREE.Vector2(flangeR, flangeBase),
      new THREE.Vector2(flangeR, flangeBase + 0.015 * D),
      new THREE.Vector2(flangeR * 0.88, flangeTop),
      new THREE.Vector2(portR * 1.02, flangeTop),
      new THREE.Vector2(0, flangeTop),
    ], 24),
    M.red,
  );
  flange.name = PART.portFlange;
  flange.position.x = X_PORT;
  group.add(flange);

  /* ------------------------------------------------------------- hammer spur */

  /**
   * NOTE 1 -- D-20 and D-21, and what "build it so a valid joint is possible" means.
   *
   * D-20: at J1's declared +0.6 R pivot with the receiver top at +0.64 R and 0.37 R of
   * receiver behind the pivot, the spur lies inside the receiver's footprint below about
   * +7 deg, so the whole negative half of the declared [-55, +20] range interpenetrates
   * -- unless the receiver carries a slot, which `frame.surfaceFeatures.count` = 0
   * denies.
   *
   * D-21: J1's high-limit condition, "no child vertex lies below the frame's top face",
   * is unsatisfiable at rest, because the pivot itself sits below that face.
   *
   * Both are geometry problems, and both are fixed here by geometry rather than by
   * editing the joint:
   *
   *  - the pivot is lifted to +0.84 R (inside its +-0.3 R band) and the top strap is
   *    dropped to 0.215 D, which puts the pivot 0.410 R ABOVE the frame's local top face
   *    instead of below it. D-21's condition becomes satisfiable at rest, and stays
   *    satisfiable through the whole range, because the boss is centred on the pivot and
   *    its underside at 0.330 D is rotation-invariant.
   *  - the swing is then checked against the top strap, not asserted. The blade's lowest
   *    reachable point over [-55, +20] is at the low limit, where the spur axis is at
   *    34 - 55 = -21 deg:
   *        y = 0.84 R + Ls*sin(-21 deg) - w*cos(21 deg)
   *          = 0.420 D - 0.0958 D - 0.0453 D = 0.279 D,
   *    against a top strap at 0.215 D. Clear by 0.064 D = 3.3 mm, over the entire range,
   *    with no slot anywhere in the receiver. The assertion at the end of this function
   *    is what keeps that true if anybody edits these numbers.
   *
   * That clearance is what Nova3D's 98.3 % geometric-validity figure actually measures,
   * and it is why the top strap is 0.215 D rather than a number read off anything.
   */

  /**
   * NOTE 2 -- `frame.spur.lengthOverTubeOd` = 0.82 +- 0.20 D is NOT satisfied, and
   * cannot be by any geometry that satisfies the rows around it. The arithmetic:
   *
   *   the spur's forward-lower corner is J1's pivot, at u <= 0.96 by its own band;
   *   the port occupies u 0.869-0.905 and the boss may not enter it, so u >= 0.925;
   *   the spur's rear may not pass u ~0.985, because `grip.butt.behindFrameHeel` needs
   *     the butt 0.05-0.35 D rearward of the frame's rearmost, and the butt is at u 1.0;
   *   -> at most 0.06 of A, = 0.37 D, of axial run is available;
   *   a rectangle of aspect 2.8 inclined at `frame.spur.attitude`'s 32 +- 8 deg projects
   *     1.00-1.04 x its own length onto the axis, so its longest AABB extent is 0.37 D;
   *   the row's floor is 0.62 D.
   *
   * Letting it reach 0.62 D means running the spur rearward past the butt, which makes
   * the spur the gun's rearmost vertex, grows A by 7 %, and drops
   * `gun.barrel.axialFraction` from 0.808 to 0.756 -- outside a 0.75-confidence band, to
   * rescue a 0.45-confidence one whose evidence is "32.7 px against pose1's tube" and
   * whose own note says it was rescaled from a superseded denominator. §10.3 warns that
   * raw pixels between panels are not comparable at all (tube OD reads 31/36/45/37 px
   * across four poses). The spur is built at the 0.42 D the harness reports, and the row
   * is recorded as failed.
   */

  /**
   * NOTE 3 -- `frame.spur.aspect` = 2.8 +- 0.7 is not satisfiable AS CHECKED at any
   * attitude in `frame.spur.attitude`'s own band, and this appears to be a fresh instance
   * of the defect class §11.7 counts four of: the check tests something other than the
   * stated value.
   *
   * The evidence is a PCA over 238 brass pixels giving 32.7 x 11.8. The check is
   * "spur AABB longest / second-longest extent". For a rectangle of length Ls and width
   * Wn inclined at theta, those extents are
   *     axial    = Ls cos(theta) + Wn sin(theta)
   *     vertical = Ls sin(theta) + Wn cos(theta)
   * and their ratio is bounded above by cot(theta) as Wn -> 0. At theta = 32 deg that
   * ceiling is 1.60; at the band's most favourable end, 24 deg, it is 2.25 -- and 2.25 is
   * only reached by a sliver of aspect 25, which fails the same row read as PCA. The
   * row's floor is 2.1. There is no rectangle, at any attitude the contract allows, that
   * passes.
   *
   * The spur is therefore built with a PCA aspect of 2.75 -- what the evidence measured,
   * and what the shape reads as -- and its AABB ratio comes out at 1.15.
   */
  const spurLen = 0.267 * D;
  const spurHalfW = spurLen / 2.75 / 2;

  // Local (s, n): +s runs rearward-up along the spur, +n is perpendicular. Built here,
  // then rotated and translated onto the pivot, so the serration pitch and the boss stay
  // readable as the numbers they are.
  const spurLocal: number[][] = [];
  // Pivot boss: the exposed arc only, from +78 deg round through 180 to -78 deg.
  for (let i = 0; i <= 14; i++) {
    const a = THREE.MathUtils.degToRad(78 + (360 - 156) * (i / 14));
    spurLocal.push([bossR * Math.cos(a), bossR * Math.sin(a)]);
  }
  // Leading (lower) edge out to the tip.
  spurLocal.push([spurLen * 0.30, -spurHalfW * 1.02]);
  spurLocal.push([spurLen * 0.72, -spurHalfW * 0.94]);
  spurLocal.push([spurLen, -spurHalfW * 0.55]);
  // Tip nose.
  spurLocal.push([spurLen + 0.0012, spurHalfW * 0.10]);
  spurLocal.push([spurLen + 0.0008, spurHalfW * 0.86]);
  /**
   * NOTE 4 -- `frame.hammer-spur.rib[0..5]` is NOT emitted as child meshes, and this is
   * the one part in §3's tree that this module leaves unnamed. The reason is that the two
   * rows collide:
   *
   *   `frame.protrusionsAbove.count` = 2 counts MESHES whose AABB min-up clears
   *      (receiver max-up - 0.10 D), restricted to u > 0.81. Six ribs sitting on the spur
   *      all clear it, because the spur clears it -- the check returns 8, not 2.
   *   `frame.hammer.ribs.count` = 6 +- 2 checks something else entirely: "sample surface
   *      radius along the spur's own axis; count local maxima". That is a profile
   *      measurement, and serrations cut into the spur's own outline satisfy it exactly as
   *      well as six separate meshes would.
   *
   * So the ribs are built as profile serrations. The count row passes on its own stated
   * check; the protrusion row passes because it now sees the two things it is counting.
   * The cost is that a name lookup for `frame.hammer-spur.rib.*` reports the part missing.
   * That is the honest trade: the rib is marked `[?]` in the tree -- existence inferred,
   * not resolved -- §10.20 says the count is no better than +-2 and that what pose3
   * seemed to show is JPEG chroma noise, and `frame.hammer.ribs.count` carries confidence
   * 0.45, against `frame.protrusionsAbove.count`'s 0.65. Six named meshes would buy one
   * inferred part and break a measured one.
   *
   * Depth is 0.22 of the spur's half-width: at §6.1's 1.400 mm/px these ridges are 0.5 px
   * deep, which is why no pose resolves them and why the count is what it is.
   */
  const nSerr = DECLARED.spurSerrations;
  for (let i = nSerr; i >= 0; i--) {
    const t = i / nSerr;
    const s = spurLen * (0.16 + 0.80 * t);
    spurLocal.push([s, spurHalfW * (1.0 - 0.22 * (i % 2))]);
    spurLocal.push([s - spurLen * 0.04, spurHalfW * (1.0 - 0.22 * ((i + 1) % 2))]);
  }

  // Local +n maps to world DOWN-and-rearward under the rotation applied below -- the two
  // frames have opposite handedness and no pure rotation about Z fixes both axes at once.
  // So the outline is authored thumb-face-up and mirrored across the spur's own axis
  // here. Built without the mirror, the checkering lands on the hammer's underside, where
  // no thumb can reach it and where it reads as a burr rather than a grip.
  const spurShape = shapeOf(spurLocal.map(([s, n]) => [s, -n]));
  // Thickness tapers from the boss to the tip: a hammer that is as thick at its tip as at
  // its pin reads as a cardboard tab in three-quarter view, which is the same failure the
  // Talon blade's grind field exists to avoid.
  const spurField: Field = (s, n) => {
    const along = THREE.MathUtils.clamp(s / spurLen, 0, 1);
    const across = THREE.MathUtils.clamp(Math.abs(n) / (spurHalfW * 1.35), 0, 1);
    const taper = 0.46 + 0.54 * (1 - along * along);
    const crown = 0.40 + 0.60 * Math.sqrt(Math.max(0, 1 - across * across));
    return (DECLARED.spurThickness / 2) * taper * crown;
  };

  const spur = new THREE.Mesh(warpedExtrude(spurShape, spurField, 1), M.brass);
  spur.name = PART.hammerSpur;
  // Local +s is rearward-up: rotate local +x onto (-cos(att), +sin(att)). The thickness
  // field is authored in the same local frame, so the rotation costs it nothing.
  spur.rotation.z = Math.PI - SPUR_ATTITUDE;
  spur.position.set(PIVOT_HAMMER.x, PIVOT_HAMMER.y, 0);
  group.add(spur);

  /* ---------------------------------------------------------------- guard */

  /**
   * §10.9: "The trigger guard's shape. Present in clay c1 at ~8x16 px; every dimension of
   * it is DECLARED." Three things pin it anyway, and they are the only reasons any of
   * these nodes is where it is:
   *
   *   - both roots must be let into the frame's underside at -0.710 D, or the guard
   *     floats;
   *   - node C must put H3's declared rake pivot (u 0.815, -2.4 R) INSIDE the guard's
   *     material, or §8's "any other pivot placement makes H3 non-local" bites;
   *   - the bow's interior must clear the trigger blade through J2's whole 0 -> +14 deg
   *     travel, which is what sets the rear leg's station.
   */
  const guardPath = [
    new THREE.Vector2(-0.00120, -0.630 * D), // forward root, let into the frame
    new THREE.Vector2(-0.00160, -0.900 * D),
    // H3's declared rake pivot, put ON the centreline rather than merely near it, so no
    // half-width argument is needed to show the handle stays inside the part it turns.
    new THREE.Vector2(H3_RAKE_PIVOT.x, H3_RAKE_PIVOT.y),
    new THREE.Vector2(-0.00560, -1.360 * D),
    new THREE.Vector2(-0.01120, -1.410 * D),
    new THREE.Vector2(-0.01760, -1.385 * D),
    new THREE.Vector2(-0.02360, -1.245 * D),
    new THREE.Vector2(-0.02660, -1.010 * D),
    new THREE.Vector2(-0.02740, -0.800 * D),
    new THREE.Vector2(-0.02740, -0.630 * D), // rear root, let into the frame
  ];
  const guard = new THREE.Mesh(
    new THREE.ExtrudeGeometry(ribbon(guardPath, DECLARED.guardThickness / 2, 44), {
      depth: 0.160 * D, bevelEnabled: true, bevelThickness: 0.0012,
      bevelSize: 0.0012, bevelSegments: 2, curveSegments: 4, steps: 1,
    }),
    M.paint,
  );
  guard.name = PART.triggerGuard;
  guard.position.z = -0.080 * D;
  group.add(guard);

  /* --------------------------------------------------------------- trigger */

  // "blade inside the guard; 8x15 px in the only view that shows it" -- at §6.2's
  // D = 37 px that is 0.216 D x 0.405 D. Drawn in a pivot-local frame so J2's rotation is
  // about the origin and the toe's return curve stays readable, then scaled so the
  // FINISHED extrude measures 8x15 px: the bevel grows the silhouette by 2 x bevelSize in
  // both directions, and on a 0.011 m part that is 16 % of its width. Sizing the outline
  // and then bevelling it would put the blade a fifth over the only figure the reference
  // offers for it.
  const trigBevel = 0.0009;
  const trigTarget = [0.216 * D - 2 * trigBevel, 0.405 * D - 2 * trigBevel];
  const triggerRaw: number[][] = [
    [0.00310, 0.00190],
    [0.00260, -0.00340],
    [0.00075, -0.00920],
    [-0.00210, -0.01390],
    [-0.00525, -0.01690],
    [-0.00700, -0.01890],
    [-0.00800, -0.01830],
    [-0.00740, -0.01550],
    [-0.00575, -0.01080],
    [-0.00400, -0.00560],
    [-0.00290, -0.00060],
    [-0.00244, 0.00190],
  ];
  const rawW = Math.max(...triggerRaw.map((p) => p[0])) - Math.min(...triggerRaw.map((p) => p[0]));
  const rawH = Math.max(...triggerRaw.map((p) => p[1])) - Math.min(...triggerRaw.map((p) => p[1]));
  const triggerLocal = triggerRaw.map((p) => [p[0] * (trigTarget[0] / rawW), p[1] * (trigTarget[1] / rawH)]);
  const trigger = new THREE.Mesh(
    new THREE.ExtrudeGeometry(shapeOf(triggerLocal), {
      depth: DECLARED.triggerThickness, bevelEnabled: true, bevelThickness: trigBevel,
      bevelSize: trigBevel, bevelSegments: 2, curveSegments: 4, steps: 1,
    }),
    M.brass,
  );
  trigger.name = PART.trigger;
  trigger.position.set(PIVOT_TRIGGER.x, PIVOT_TRIGGER.y, -DECLARED.triggerThickness / 2);
  group.add(trigger);

  /* ---------------------------------------------------------------- checks */

  // These are not tests of three.js; they are the four places where an edit to one number
  // silently breaks a different contract row, written down where the edit happens.
  const boxes = new Map<string, THREE.Box3>();
  group.updateMatrixWorld(true);
  group.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) boxes.set(m.name, new THREE.Box3().setFromObject(m));
  });
  const rc = boxes.get(PART.receiver)!;
  const tg = boxes.get(PART.trigger)!;
  const gd = boxes.get(PART.triggerGuard)!;
  const sp = boxes.get(PART.hammerSpur)!;

  // frame.trigger.insideGuard, conf 0.85 -- the highest-confidence row in §6.8.
  console.assert(
    tg.min.x >= gd.min.x && tg.max.x <= gd.max.x &&
    tg.min.y >= gd.min.y && tg.max.y <= gd.max.y &&
    tg.min.z >= gd.min.z && tg.max.z <= gd.max.z,
    'frame.trigger.insideGuard violated',
  );
  // frame.protrusionsAbove.count = 2: the port and the spur clear
  // (receiver max-up - 0.10 D); the flange, deliberately, does not.
  console.assert(
    sp.min.y > rc.max.y - 0.10 * D && boxes.get(PART.port)!.min.y > rc.max.y - 0.10 * D &&
    boxes.get(PART.portFlange)!.min.y < rc.max.y - 0.10 * D,
    'frame.protrusionsAbove.count != 2',
  );
  // NOTE 1's swing clearance, at J1's low limit.
  const lowLimit = SPUR_ATTITUDE - THREE.MathUtils.degToRad(55);
  console.assert(
    PIVOT_HAMMER.y + spurLen * Math.sin(lowLimit) - spurHalfW * Math.cos(lowLimit)
      > RECEIVER_TOPSTRAP,
    'J1 low limit drives the spur into the receiver (D-20)',
  );
  // H3's rake pivot must lie in the guard's material, or the grip handle stops being
  // local however the locality test is written.
  console.assert(
    H3_RAKE_PIVOT.x > gd.min.x && H3_RAKE_PIVOT.x < gd.max.x &&
    H3_RAKE_PIVOT.y > gd.min.y && H3_RAKE_PIVOT.y < gd.max.y,
    'H3 rake pivot is outside the trigger guard',
  );

  return group;
}
