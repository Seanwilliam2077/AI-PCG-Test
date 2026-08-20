/**
 * The head: cranium, face, jaw, eyes, brows, nose, lips, ears.
 *
 * TWO shells, not one, and the split is the whole round-3 story.
 *
 * Materials are resolved per *vertex*, so a material band narrower than a voxel
 * comes out as a row of blocks -- which is exactly what the face was: a pale
 * mask with dark smudges where the eyes and mouth should be.  The reference's
 * lash liner is 4.4 mm and its iris 14 mm; at the low LOD's 10.5 mm voxel, even
 * halved for this part, those are 1 and 3 samples across.  Two answers, both
 * used here:
 *
 *  A. **Spend voxels only where the bands are.**  The eyeballs are their own
 *     closed surface, so they can be meshed at `eyeVoxelScale` (0.20 -> 2.1 mm
 *     at the low LOD) for a couple of thousand triangles, while the skull stays
 *     coarse.  At that size the iris is seven samples across instead of three,
 *     and the lash line can be *painted on the globe* -- the band between the
 *     lid rim and a copy of the rim curve shifted down by `lashT` -- instead of
 *     being a floating slab that never lined up with the opening.
 *
 *     The liner is drawn on the lid in the reference, *above* the opening, so
 *     the opening has to carry both: 13.6 mm of aperture, of which the top
 *     3.4 mm is painted.  Building it to show 12 mm of white and then darkening
 *     the top gives an eye 4 mm too small, which is what the first attempt
 *     did.
 *
 *  B. **Give the rest of the bands relief.**  A boundary that exists only in
 *     the material function has nothing to snap to.  The brow is now a ridge
 *     11 mm wide standing 2 mm proud (a tube of radius `ridgeRInner` pushed
 *     `ridgeBack` *along the skull's inward normal*, not along -z, which stops
 *     mattering the moment x passes 30 mm), the lips are two masses split by a
 *     3.2 mm groove, and `mento` cuts the mentolabial crease the profile had
 *     no chin edge without.
 *
 * The eye opening is a **lens** -- two big circles intersected -- rather than
 * an ellipsoid.  An ellipsoid has no corner, and the reference's outer canthus
 * is a sharp flick; the lens closes to a point at both canthi for free, and
 * skewing the painted lash band by `lashSkew` thickens it toward the outer one
 * the way liner is actually drawn.
 *
 * Shape strategy for the mass, unchanged from round 2 because it measures well:
 *
 *  1. The cranium is a *loft* -- a stack of elliptical cross-sections through
 *     measured heights.  A second, shallower stack (`frontLoft`) flattens the
 *     plane of the face; one ellipse alone puts the surface 5 mm behind where
 *     the eyeball has to be.  Both are monotonic in zFront and their slices are
 *     at least twice as tall as the slice spacing, because anything thinner
 *     scallops and the scallop lands on the forehead as corduroy.
 *  2. Everything below the nose base is anatomy: zygomatic arch, mandible
 *     ramus, a jaw tube swept to a small chin, the maxilla.  The hollow cheek
 *     is the gap between arch and mandible rather than a gouge.
 *  3. The eye is a ball in a socket with a lid *mass* over it: a larger ball,
 *     squashed in y, with the lens aperture cut through it.  The lid is
 *     smooth-unioned into the face so it has no cliff at the cheek.
 *
 * Two notes on the shared operators, both of which cost a bake to find:
 *   - `rotateX/Y/Z` rotate about the *world* origin, so a feature authored at
 *     y = 1.6 and rotated by 0.25 rad swings 0.40 m forward in z.  Everything
 *     here rotates through `rotZAt`, which brackets the rotation with
 *     translations about a pivot.
 *   - `halfSpace(n, d)` is negative where n.p < d, so "keep everything above
 *     y = cutY" is the *downward* normal with d = -cutY.
 */
import { Field, Vec3, box } from '../sdf/types.js';
import {
  capsule, capsuleOval, ellipsoid, halfSpace, intersect, offset, rotateZ,
  smoothSubtract, smoothUnion, sphere, subtract, translate, union,
} from '../sdf/ops.js';
import { Curve, tube } from '../sdf/curve.js';
import { cut } from '../sdf/solids.js';
import {
  PartContext, PartModule, Shell, Tagged, constMaterial, nearestMaterial, paint,
} from './types.js';

/* ------------------------------------------------------------------ */
/* spec view                                                           */

interface Seg3 { c: Vec3; r: Vec3 }

interface HeadSpec {
  cutY: number;
  loftBlend: number;
  coreBlend: number;
  /** The dome above the top section, which no stack of slices renders cleanly. */
  crownCap: Seg3;
  /** [y, halfX, zFront, zBack, ry] per cross-section, crown first. */
  sections: number[][];
  /** Same form, a shallower stack that flattens the plane of the face. */
  frontLoft: number[][];
  neck: { y0: number; y1: number; z0: number; z1: number; r0: number; r1: number; squashZ: number };
  zygo: { back: Vec3; front: Vec3; rBack: number; rFront: number };
  ramus: { low: Vec3; high: Vec3; rLow: number; rHigh: number };
  jaw: { curve: Vec3[]; rEnd: number; rMid: number; segments: number };
  chinBall: Seg3;
  maxilla: Seg3;
  hollow: { c: Vec3; r: number; blend: number };
  orbit: { c: Vec3; r: Vec3; blend: number };
  eye: {
    x: number; y: number; z: number; r: number; lidT: number; blend: number;
    lidSquashY: number;
    apZ: number; apHalfW: number; apHalfH: number; apDepth: number; tilt: number;
    irisR: number; irisZ: number; pupilR: number; pupilZ: number;
    lashT: number; lashSkew: number; lowLashT: number; lowLashSkew: number;
    socketClear: number; backCut: number;
  };
  browRidge: {
    curve: Vec3[]; inward: Vec3; segments: number;
    ridgeBack: number; ridgeRInner: number; ridgeROuter: number;
    ridgeBlend: number; paintGrow: number;
  };
  nose: {
    bridgeTop: Vec3; bridgeLow: Vec3; rTop: number; rLow: number;
    tipC: Vec3; tipR: Vec3; alaC: Vec3; alaR: Vec3;
    nostrilC: Vec3; nostrilR: Vec3; nostrilBlend: number; nostrilPaint: number;
    blend: number; faceBlend: number;
  };
  lips: {
    upper: Vec3[]; lower: Vec3[]; line: Vec3[];
    rUpperEnd: number; rUpperMid: number; rLowerEnd: number; rLowerMid: number;
    rLine: number; lineBlend: number; blend: number; paintGrow: number; segments: number;
  };
  mento: { curve: Vec3[]; r: number; lift: number; blend: number; segments: number };
  ear: {
    plateC: Vec3; plateR: Vec3;
    helix: Vec3[]; helixR: number;
    antihelix: Vec3[]; antihelixR: number;
    tragusC: Vec3; tragusR: Vec3;
    bowlC: Vec3; bowlR: Vec3;
    lobeC: Vec3; lobeR: number;
    blend: number; innerBlend: number; segments: number;
  };
  voxelScale: number;
  eyeVoxelScale: number;
}

/* ------------------------------------------------------------------ */
/* helpers                                                             */

const neg = (p: Vec3): Vec3 => [-p[0], -p[1], -p[2]];

/** rotateZ about a pivot -- the shared rotateZ turns about the world origin. */
const rotZAt = (f: Field, ang: number, pivot: Vec3): Field =>
  translate(rotateZ(translate(f, neg(pivot)), ang), pivot);

/** Mirror a point to -X. */
const mx = (p: Vec3, side: number): Vec3 => [p[0] * side, p[1], p[2]];
const mr = (r: Vec3): Vec3 => [r[0], r[1], r[2]];

/**
 * A curve authored on her left, closed across the midline into a symmetric
 * one.  The last control point must sit on x = 0 or the join will kink.
 */
function mirrorCurve(half: Vec3[]): Curve {
  const back = half.slice(0, -1).map((p) => [-p[0], p[1], p[2]] as Vec3).reverse();
  return [...half, ...back];
}

/** Move `p` a distance `d` toward `target` -- a cheap stand-in for "along the
 *  inward surface normal" on a shape that is roughly an ellipsoid. */
function pushToward(p: Vec3, target: Vec3, d: number): Vec3 {
  const v: Vec3 = [target[0] - p[0], target[1] - p[1], target[2] - p[2]];
  const L = Math.hypot(v[0], v[1], v[2]) || 1;
  return [p[0] + (v[0] / L) * d, p[1] + (v[1] / L) * d, p[2] + (v[2] / L) * d];
}

/* ------------------------------------------------------------------ */

export const headPart: PartModule = {
  id: 'head',
  build(ctx: PartContext): Shell[] {
    const { mat } = ctx;
    const h = ctx.spec.head as unknown as HeadSpec;
    const e = h.eye;

    /* ---------------- eye frame, shared by both shells ---------------- */

    const eyeC = (side: 1 | -1): Vec3 => [side * e.x, e.y, e.z];
    const eyeball = (side: 1 | -1) => sphere(eyeC(side), e.r);

    /** Radius of the two circles whose intersection is a lens of half-axes
     *  a (horizontal) and b (vertical). */
    const lensR = (a: number, b: number) => (a * a + b * b) / (2 * b);
    const R = lensR(e.apHalfW, e.apHalfH);
    const cOff = R - e.apHalfH;          // circle centre offset from the eye axis

    /** Place a field authored in the aperture's own frame (origin on the eye
     *  axis at z = e.z + apZ, +x temporal for her left eye) into the world. */
    const inEyeFrame = (f: Field, side: 1 | -1) =>
      rotZAt(translate(f, [side * e.x, e.y, e.z + e.apZ]), side * e.tilt, eyeC(side));

    /** The almond opening: two circles intersected, so both canthi come to a
     *  point instead of the rounded end an ellipsoid gives. */
    const aperture = (side: 1 | -1) => inEyeFrame(
      intersect(
        ellipsoid([0, -cOff, 0], [R, R, e.apDepth]),
        ellipsoid([0, cOff, 0], [R, R, e.apDepth]),
      ),
      side,
    );

    /* ---------------- 1. lofted cranium and upper face ---------------- */

    const slice = ([y, halfX, zFront, zBack, ry]: number[]) =>
      ellipsoid([0, y, (zFront + zBack) / 2], [halfX, ry, (zFront - zBack) / 2]);

    // Sections overlap by better than twice their spacing: a thinner slice
    // scallops, and the scallop lands exactly on the forehead where it reads
    // as corduroy.  The front stack is what turns the elliptical plan into a
    // face -- without it the surface at the pupils sits 5 mm behind where the
    // eyeball has to be, and the eyes read as stuck on.
    const loft = smoothUnion(
      h.loftBlend,
      ellipsoid(h.crownCap.c, mr(h.crownCap.r)),
      ...h.sections.map(slice),
      ...h.frontLoft.map(slice),
    );

    /* ---------------- 2. jaw, cheekbone, muzzle ---------------- */

    const n = h.neck;
    const neckCol = capsuleOval(
      [0, n.y0, n.z0], [0, n.y1, n.z1], n.r0, n.r1, n.squashZ, 1,
    );

    const zygomatic = (side: 1 | -1) => capsule(
      mx(h.zygo.back, side), mx(h.zygo.front, side), h.zygo.rBack, h.zygo.rFront,
    );
    const ramus = (side: 1 | -1) => capsule(
      mx(h.ramus.low, side), mx(h.ramus.high, side), h.ramus.rLow, h.ramus.rHigh,
    );

    const jawCurve = mirrorCurve(h.jaw.curve);
    const jawTube = tube(jawCurve, {
      segments: h.jaw.segments,
      radius: (t) => h.jaw.rMid + (h.jaw.rEnd - h.jaw.rMid) * Math.pow(Math.abs(2 * t - 1), 1.4),
    });

    const chinBall = ellipsoid(h.chinBall.c, mr(h.chinBall.r));
    const maxilla = ellipsoid(h.maxilla.c, mr(h.maxilla.r));

    let core = smoothUnion(
      h.coreBlend,
      loft, neckCol,
      zygomatic(1), zygomatic(-1),
      ramus(1), ramus(-1),
      jawTube, chinBall, maxilla,
    );

    /* Cheek hollow: a large sphere set out to the side and slightly forward,
     * so it shaves a broad 2-4 mm scoop off the plane between the arch and the
     * jaw rather than punching a dimple. */
    const hollow = (side: 1 | -1) => sphere(mx(h.hollow.c, side), h.hollow.r);
    core = smoothSubtract(h.hollow.blend, core, union(hollow(1), hollow(-1)));

    /* Orbits: the brow's overhang and the recess the cheekbone stands out of.
     * They are deliberately NOT the thing that clears the globe -- an orbit
     * deep enough to do that hollows the brow and the cheekbone with it.  See
     * `socketCut` below, which does the clearing locally. */
    const orbit = (side: 1 | -1) => ellipsoid(mx(h.orbit.c, side), mr(h.orbit.r));
    core = smoothSubtract(h.orbit.blend, core, union(orbit(1), orbit(-1)));

    /* ---------------- 3. brow ridge ---------------- */

    const b = h.browRidge;
    /* The tube is buried `ridgeBack` below the surface along the skull's
     * inward normal, so what surfaces is a band 2*sqrt(r^2 - back^2) wide
     * standing (r - back) proud.  The paint then stops against a real crease
     * instead of against nothing. */
    const browSpine = (side: 1 | -1): Curve =>
      b.curve.map((p) => mx(pushToward(p, b.inward, b.ridgeBack), side));
    const browRidgeF = (side: 1 | -1) => tube(browSpine(side), {
      segments: b.segments,
      radius: (t) => b.ridgeRInner + (b.ridgeROuter - b.ridgeRInner) * t,
    });
    const brows = union(browRidgeF(1), browRidgeF(-1));
    core = smoothUnion(b.ridgeBlend, core, brows);

    /* ---------------- 4. nose ---------------- */

    const ns = h.nose;
    const bridge = capsule(ns.bridgeTop, ns.bridgeLow, ns.rTop, ns.rLow);
    const tip = ellipsoid(ns.tipC, mr(ns.tipR));
    const ala = (side: 1 | -1) => ellipsoid(mx(ns.alaC, side), mr(ns.alaR));
    const nose = smoothUnion(ns.blend, bridge, tip, ala(1), ala(-1));

    let face = smoothUnion(ns.faceBlend, core, nose);

    /* A soft dimple plus a dark spot, not a pit.  Subtracting a 4 mm pit at a
     * 4.6 mm voxel produced a ragged black gash across the nose base -- the
     * feature was under one sample, so Surface Nets tore it.  Widening the
     * blend turns it into a dent the mesh can hold, and the near-black paint
     * does the reading. */
    const nostril = (side: 1 | -1) => ellipsoid(mx(ns.nostrilC, side), mr(ns.nostrilR));
    const nostrils = union(nostril(1), nostril(-1));
    face = smoothSubtract(ns.nostrilBlend, face, nostrils);

    /* ---------------- 5. lips ---------------- */

    const lp = h.lips;
    const bump = (t: number) => Math.sin(Math.PI * t) ** 0.75;
    const lipUpper = tube(mirrorCurve(lp.upper), {
      segments: lp.segments,
      radius: (t) => lp.rUpperEnd + (lp.rUpperMid - lp.rUpperEnd) * bump(t),
    });
    const lipLower = tube(mirrorCurve(lp.lower), {
      segments: lp.segments,
      radius: (t) => lp.rLowerEnd + (lp.rLowerMid - lp.rLowerEnd) * bump(t),
    });
    const lips = union(lipUpper, lipLower);
    const mouthLine = tube(mirrorCurve(lp.line), { segments: lp.segments, radius: lp.rLine });

    let solid = smoothUnion(lp.blend, face, lips);
    solid = smoothSubtract(lp.lineBlend, solid, mouthLine);

    /* Mentolabial crease.  Lifted `lift` proud of the skin so it takes out
     * (r - lift) rather than the whole tube radius. */
    const mt = h.mento;
    const mentoTube = tube(
      mirrorCurve(mt.curve.map((p) => [p[0], p[1], p[2] + mt.lift] as Vec3)),
      { segments: mt.segments, radius: mt.r },
    );
    solid = smoothSubtract(mt.blend, solid, mentoTube);

    /* ---------------- 6. ears ---------------- */

    /* Round 2's ear was a plate with a bowl bitten out of it, and at the low
     * LOD the bowl read as a hole.  This one has the three things that make an
     * ear legible at 20 px: a helix rim all the way round, an antihelix ridge
     * across the bowl to break it up, and a tragus at the front of it. */
    const er = h.ear;
    const ear = (side: 1 | -1) => {
      const plate = ellipsoid(mx(er.plateC, side), mr(er.plateR));
      const helix = tube(er.helix.map((p) => mx(p, side)), {
        segments: er.segments, radius: er.helixR,
      });
      const lobe = sphere(mx(er.lobeC, side), er.lobeR);
      let f = smoothUnion(er.innerBlend, plate, helix, lobe);
      f = smoothSubtract(er.innerBlend, f, ellipsoid(mx(er.bowlC, side), mr(er.bowlR)));
      const anti = tube(er.antihelix.map((p) => mx(p, side)), {
        segments: 14, radius: er.antihelixR,
      });
      const tragus = ellipsoid(mx(er.tragusC, side), mr(er.tragusR));
      return smoothUnion(er.innerBlend, f, anti, tragus);
    };
    solid = smoothUnion(er.blend, solid, ear(1), ear(-1));

    /* ---------------- 7. lids ---------------- */

    // Squashed in y: a full ball of lid would be 38 mm tall and its lower edge
    // reads as a crescent shadow across the cheekbone.
    const lidBall = (side: 1 | -1) => ellipsoid(
      eyeC(side),
      [e.r + e.lidT, (e.r + e.lidT) * e.lidSquashY, e.r + e.lidT],
    );
    const lidMass = (side: 1 | -1) => subtract(lidBall(side), aperture(side));

    // Blended into the face -- a hard union leaves a circular cliff where the
    // ball meets the cheek.  The globe itself is the other shell.
    solid = smoothUnion(e.blend, solid, lidMass(1), lidMass(-1));

    /* Open the socket to exactly the aperture.
     *
     * Measured, before this existed: the visible globe was 20.5 mm across
     * against a 31 mm opening, because the skin inside the opening climbs from
     * z 0.0357 on the eye axis to 0.0424 eleven millimetres out -- the loft's
     * own blends plus the lid's -- and overtakes the globe there.  Deepening
     * `orbit` cannot fix that without hollowing the brow and cheekbone with it.
     * So take the aperture itself, intersect it with the globe grown by
     * `socketClear`, and cut that out of the finished head: inside the opening
     * the skin is then always behind the globe, and outside it nothing moves.
     * The globe is wider than the opening (r 17 mm against a 15.5 mm half
     * width), so it caps the cavity and no hole shows. */
    const socketCut = (side: 1 | -1) =>
      intersect(aperture(side), offset(eyeball(side), e.socketClear));
    solid = subtract(solid, union(socketCut(1), socketCut(-1)));

    /* ---------------- 8. close the bottom ---------------- */

    // halfSpace is negative where n.p < d, so "keep above cutY" is the
    // downward normal.
    const lid = box([-0.16, h.cutY, -0.16], [0.16, 1.76, 0.16]);
    const field: Field = intersect(solid, halfSpace([0, -1, 0], -h.cutY, lid));

    /* ---------------- 9. head materials ---------------- */

    const tags: Tagged[] = [
      { field: offset(nostrils, ns.nostrilPaint), mat: mat.skinShade },
      { field: offset(brows, b.paintGrow), mat: mat.brow },
      { field: offset(lips, lp.paintGrow), mat: mat.lip },
      { field: solid, mat: mat.skin },
    ];

    /* ---------------- 10. the eyes, as their own shell ---------------- */

    const iris = (side: 1 | -1) => sphere([side * e.x, e.y, e.z + e.irisZ], e.irisR);
    const pupil = (side: 1 | -1) => sphere([side * e.x, e.y, e.z + e.pupilZ], e.pupilR);

    /**
     * The lash line, painted on the globe rather than floated in front of it.
     *
     * The upper lid margin is the top boundary of the aperture's lower... no:
     * of its *upper* circle.  Take a copy of that circle shifted down by
     * `lashT` and sideways by `lashSkew`, and darken everything above it.  What
     * is left visible is the band between the real rim and the shifted one --
     * 1.6 mm at the inner canthus, 2.7 mm at the pupil and 4.2 mm at the outer
     * one, which is how liner is drawn and which matches the 4.4 mm the
     * reference carries at its widest.  Everything else the region covers is
     * behind the lid.
     *
     * The bounding sphere is deliberately small: `union`ing the two sides'
     * regions with a big one would paint the far eye black, because "outside
     * this circle" is true almost everywhere.
     */
    const lashBand = (side: 1 | -1, t: number, skew: number, low: boolean) => {
      const cy = low ? cOff + t : -(cOff + t);
      const disc = ellipsoid([-side * skew, cy, 0], [R, R, e.apDepth * 2]);
      return inEyeFrame(subtract(sphere([0, 0, -e.apZ], e.r * 1.5), disc), side);
    };

    /* Only the front cap is ever seen -- the rest is buried in the socket --
     * and at eyeVoxelScale a whole sphere is 40 % more triangles for nothing.
     * The cut plane sits `backCut` in front of the globe centre, which is
     * still 12 mm behind the nearest point the skin ever exposes, and both the
     * lid ball and the core cover it. */
    const globe = (side: 1 | -1) => cut(eyeball(side), 2, e.z + e.backCut, 'above');
    const eyesField = union(globe(1), globe(-1));
    const eyesMaterial = paint(
      paint(
        paint(
          paint(constMaterial(mat.sclera), union(iris(1), iris(-1)), mat.eye, 0),
          union(pupil(1), pupil(-1)), mat.pupil, 0,
        ),
        union(
          lashBand(1, e.lowLashT, e.lowLashSkew, true),
          lashBand(-1, e.lowLashT, e.lowLashSkew, true),
        ), mat.brow, 0,
      ),
      union(
        lashBand(1, e.lashT, e.lashSkew, false),
        lashBand(-1, e.lashT, e.lashSkew, false),
      ), mat.brow, 0,
    );

    return [
      {
        name: 'head',
        field,
        material: nearestMaterial(tags, mat.skin),
        voxelScale: h.voxelScale,
      },
      {
        name: 'eyes',
        field: eyesField,
        material: eyesMaterial,
        voxelScale: h.eyeVoxelScale,
      },
    ];
  },
};
