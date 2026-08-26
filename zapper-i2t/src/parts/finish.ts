/**
 * Materials and the painted finish.
 *
 * ---------------------------------------------------------------------------
 * Why this finish is generated and not projected, and what that costs
 * ---------------------------------------------------------------------------
 * The Talon demo in this pipeline gets its look by projecting de-lit reference
 * plates through an inverted image-to-world mapping, and says outright that a
 * procedural swirl is "the single biggest CS2 fidelity failure". That technique
 * is unavailable here. The reference is (c) Riot Games, modelled and textured by
 * Thibaut Granet; it is a measurement target, and pixels are not what leaves a
 * measurement target. Numbers are. So every colour below is a CIE Lab reading
 * out of contract §6.10, converted to sRGB, and nothing here was sampled.
 *
 * That is a real loss, and naming it is part of shipping it:
 *
 *  - The artist's wear pattern is gone. Projected plates carry chipping that
 *    follows the silhouette the artist read, baked cavity dirt, and the hand-
 *    painted highlight that sits where the artist wanted the eye. A flat albedo
 *    plus a light rig cannot invent any of that.
 *  - §6.10's own header says "no whole part on this object is a flat colour
 *    sample -- the p5-p95 L* span of every part is 35-52". A projected plate
 *    reproduces that span in the albedo. Nine flat albedos cannot: the entire
 *    `shading.ramp` row (p5->p95 L* >= 30 per single-material cylinder) is now
 *    the lighting rig's burden alone, and that row is already marked "partly
 *    DECLARED -- conditional on reproducing that lighting". Generated finish
 *    moves it from half-measured to fully rig-dependent.
 *  - The graffiti loses its shapes. What survives is how many, how big, how
 *    elongated and on what substrate -- §6.11 states all four. Where each mark
 *    sits is invention, and is flagged as such at `graffitiTexture`.
 *
 * What survives the translation is exactly the falsifiable part: the sixteen
 * [MAT] rows are checked by `tools/check_contract.py` against the assigned
 * material's *base colour*, converted sRGB -> Lab. Not against a render. So the
 * hexes below are not decoration; they are the answer sheet, and each was solved
 * by inverting that tool's own conversion rather than eyeballed.
 *
 * ---------------------------------------------------------------------------
 * Nine slots, because `mat.count.total` DECLARES 7 structural + 2 accent
 * ---------------------------------------------------------------------------
 * The part -> finish assignment the assembly must use, from the §3 tree. It is
 * documented rather than exported because the record this module returns is
 * keyed by finish name, and any tenth key in it would fail `mat.count.total`
 * on a naive "count material slots" read.
 *
 *   brassAged      barrel.muzzle-collar + .ring-fore/.ring-mid/.ring-aft,
 *                  barrel.mid-band, barrel.lug,
 *                  barrel.lattice-collar + .rim-fore/.rim-aft/.cutout,
 *                  frame.port + .flange, frame.hammer-spur + .rib
 *   brassYellow    barrel.rail, barrel.rail.stud.*, barrel.rail.rear-hook,
 *                  frame.trigger, grip.butt-cap.toe-stud
 *   copperWarm     barrel.tube-aft, barrel.rail.mount-block
 *   paintTube      barrel.tube-fore, barrel.liner
 *   paintFrame     frame.receiver, frame.trigger-guard, grip.butt-cap
 *   gripWarm       grip.body
 *   boreDark       barrel.bore
 *   accentMagenta  graffiti.mark.* (magenta), and the painted knob
 *   accentTeal     graffiti.mark.* (teal)
 *
 * Four of those assignments are choices the reference cannot make:
 *  - port + flange -> aged brass: §10.28 says the tan port is "indistinguishable
 *    from aged brass" at n = 93, so the cheaper reading is taken.
 *  - liner -> tube paint: §10.24 leaves "bare steel or tube paint?" open and
 *    reports a* and b* agreeing within 1 unit. Giving the liner its own slot
 *    would both break the count of 9 and manufacture the low-chroma material
 *    that `mat.noBareSteel` says is not there.
 *  - trigger, trigger-guard, toe-stud: never resolved in any view (§10.9,
 *    §10.14, §3's [?]). Guard follows the frame casting, trigger and stud read
 *    as hardware.
 *  - mount-block -> the same copper as tube-aft: see `copperWarm` below.
 */
import * as THREE from 'three';
import { A, D, L, AXIAL, BARREL_FRACTION, OD } from './datum.js';

/**
 * The palette, as base colours whose sRGB -> Lab round trip lands on §6.10.
 *
 * Each hex was found by a local search over the +-3 RGB neighbourhood of the
 * analytic inverse, minimising squared Lab error under the *exact* D65 matrix
 * and f() in `tools/check_contract.py`. Rounding to 8 bits moves Lab by up to
 * 0.4 units, which is enough to push `mat.accent.outchroma` (a 1.7x ratio with
 * ~10 % headroom) across its threshold if you round naively, so the search is
 * not pedantry.
 *
 *   key            hex       L*      a*      b*      C*      h
 *   brassAged      7a5e45   42.11    7.81   18.70   20.26    67.33
 *   brassYellow    614d2f   34.10    4.07   20.91   21.31    78.98
 *   copperWarm     735249   38.13   12.47   10.73   16.45    40.70
 *   paintTube      656e77   45.98   -1.37   -6.16    6.31   257.42
 *   paintFrame     50616a   40.07   -4.21   -7.25    8.39   239.85
 *   gripWarm       634e40   34.95    6.56   11.64   13.36    60.59
 *   boreDark       2d343a   21.28   -1.39   -4.78    4.98   253.80
 *   accentMagenta  a4316d   39.90   52.25   -8.31   52.91   350.97
 *   accentTeal     09aea0   64.05  -39.97   -3.36   40.11   184.80
 *
 * Where each number comes from, and where it is a choice:
 *
 * `paintTube` b* = -6.16. The row states -7.0 +- 1.5 at conf 0.90; audit D-9
 * re-measures the mean at -4.56, CI [-4.77, -4.33], which *fails* the row, and
 * observes that the integer median is -6.0 and passes. **The median is shipped.**
 * Not because it passes -- that would be picking the answer that scores -- but
 * because the estimator matters here: the sample is a painted cylinder whose own
 * §6.10 header says its L* runs over a 35-52 terminator ramp, so the b* sample
 * is skewed by the shaded limb, and a mean over a skewed sample is the wrong
 * statistic. The median is the robust one, and it happens to sit 1.5 units from
 * the audit's mean and 1.0 from the frozen row -- between the two, not outside
 * both. The row does not deserve conf 0.90 either way; the audit is right.
 *
 * `copperWarm` hue = 40.7 deg, and it is a *deduction*, not a reading. §6.10
 * never states the warm section's hue. But `mat.brass.count` = 2 counts
 * materials with h in [55, 95] and C* > 15, and `mat.warmTube.chromaRatio` pins
 * the warm section's C* at 21.31/1.31 = 16.3 -- above 15. So if the warm
 * section sat in the brass hue window the brass count would read 3 and the row
 * would fail. The warm material must lie outside [55, 95], and "warm" puts it
 * below. That frees it to also serve `barrel.rail.mount-block`, whose only
 * constraint is `mat.mount.red.hue` = 37 +- 7, keeping the slot count at 9.
 * §10.25 says the reference cannot separate copper from worn brown paint; this
 * declares one copper that appears in both places.
 *
 * `gripWarm` L* = 34.95, lifted from audit D-1's measured 28.2. Its
 * chromaticity is D-1's exactly (a* +6.48, b* +11.44, n = 388) -- that is the
 * finding that refuted `mat.grip.notWood`, and it is kept. Its lightness is not:
 * D-1's window is a sliver of grip bounded by fingers and background, i.e. a
 * point on the terminator ramp, and at L* 28.2 as an *albedo* it would break
 * `mat.bore.darkest` (bore 21.28 <= min exterior - 8 needs every exterior at
 * >= 29.3). Chromaticity measured, lightness DECLARED, and the two are labelled
 * separately because they were established by different evidence.
 *
 * `brassYellow` L* = 34.10 is `mat.bore.darkest`'s own evidence ("exterior min
 * 34.1 (rail)"), so the rail stays the darkest exterior material and the gap to
 * the bore is 12.8 against a stated 12.5.
 *
 * `accentTeal` C* = 40.1, above the 38.0 that `mat.accent.outchroma`'s evidence
 * implies (1.76x), because 1.7 x 21.31 = 36.2 leaves only 1.8 units of headroom
 * at 38.0 and 8-bit rounding moves chroma by up to 0.4. 40.1 is 1.88x. The row
 * is a floor, not a target.
 */
const BASE: Record<string, number> = {
  brassAged: 0x7a5e45,
  brassYellow: 0x614d2f,
  copperWarm: 0x735249,
  paintTube: 0x656e77,
  paintFrame: 0x50616a,
  gripWarm: 0x634e40,
  boreDark: 0x2d343a,
  accentMagenta: 0xa4316d,
  accentTeal: 0x09aea0,
};

/**
 * Metalness is binary. Metallic-roughness PBR has no physical state between a
 * conductor and a dielectric: at 0.5 the shader lerps a specular colour that no
 * material has, and an opaque dielectric shipped at 0.3 reads as dirty plastic
 * under every light. Brass and the bore are 1.0; every painted surface is 0.0.
 *
 * Roughness is DECLARED throughout -- §10.26 states that *no* PBR parameter is
 * recoverable from the reference, whose highlights are 2-6 px across. But one
 * ordering is measured and is honoured: `mat.warmTube.notWood` reports the warm
 * zone's residual sd at 7.18 against the blue paint's 9.19, i.e. the warm zone
 * is the smoother of the two, so copperWarm sits below paintTube rather than
 * above it. That is the only roughness relation the reference supports.
 *
 * copperWarm is a *dielectric*. §3 calls tube-aft "a paint change, not a step",
 * `barrel.tube.step.noneAtPaintLine` requires zero radius steps across that
 * boundary, and §10.22 reads it as paint. Bare metal under a painted tube would
 * normally leave a step. Flipping it to 1.0 is one edit if a later pass decides
 * otherwise; §10.25 is explicit that the reference cannot choose.
 *
 * accentMagenta is the glossiest thing on the object at 0.35, so that the
 * painted knob in `knob.magenta.count` -- described there as "a painted knob,
 * not a splatter", identified by "its own specular rim" -- gets a rim rather
 * than reading as a flat decal.
 */
const SURFACE: Record<string, { metalness: number; roughness: number }> = {
  brassAged: { metalness: 1.0, roughness: 0.52 },
  brassYellow: { metalness: 1.0, roughness: 0.38 },
  copperWarm: { metalness: 0.0, roughness: 0.55 },
  paintTube: { metalness: 0.0, roughness: 0.68 },
  paintFrame: { metalness: 0.0, roughness: 0.66 },
  gripWarm: { metalness: 0.0, roughness: 0.74 },
  boreDark: { metalness: 1.0, roughness: 0.62 },
  accentMagenta: { metalness: 0.0, roughness: 0.35 },
  accentTeal: { metalness: 0.0, roughness: 0.45 },
};

/**
 * The nine material slots, keyed by finish name.
 *
 * `material.name` carries the same key so a spec writer can deduplicate by name
 * and get 9, whatever it does with the record's keys.
 */
export function buildMaterials(): Record<string, THREE.Material> {
  const out: Record<string, THREE.Material> = {};
  for (const key of Object.keys(BASE)) {
    const m = new THREE.MeshStandardMaterial({
      // setHex with an explicit colour space rather than the constructor's
      // `color` field: three's default working space is linear, and if a later
      // pass disables ColorManagement globally the constructor path silently
      // stops converting while this one keeps its intent on the page. The
      // acceptance tool reads `color.getHexString()`, which must return these
      // exact bytes back.
      color: new THREE.Color().setHex(BASE[key], THREE.SRGBColorSpace),
      metalness: SURFACE[key].metalness,
      roughness: SURFACE[key].roughness,
    });
    m.name = key;
    out[key] = m;
  }

  // The bore is a void seen from inside. A FrontSide cylinder vanishes the
  // moment the camera looks down the muzzle, and `mat.bore.interior.L` is
  // measured on exactly that view.
  (out.boreDark as THREE.MeshStandardMaterial).side = THREE.DoubleSide;

  return out;
}

// ---------------------------------------------------------------------------
// Graffiti
// ---------------------------------------------------------------------------

/**
 * §6.11 states every graffiti figure **per rendered view, never per object**,
 * because "no clean orthographic view of either face exists" (§10.30). So the
 * reference constrains how many marks, how big, how elongated and on which
 * substrate -- and says nothing whatever about where they go.
 *
 * **The placement below is invention.** Not inference, not a reading at reduced
 * confidence: invention. Every (x, y) in the generated canvas comes from a
 * seeded LCG. What is not invented is the statistics the sampler is constrained
 * to hit, and those are listed against their rows at each constant.
 *
 * Two marks are not invented: `graffiti.crossesSeam` names the two islands it
 * found by position and substrate pair -- a magenta one spanning tube paint and
 * the muzzle collar, a teal one spanning the lattice and the warm tube. Both
 * are placed on those exact seams, straddling them.
 */

/** `graffiti.count.perView` = 13 +- 5 marks >= 3 px at 236x118. DECLARED: 30
 *  marks on the wrap, which puts 10-14 over the floor in a view.
 *
 *  The "per view" to "per object" factor is exactly what §10.30 says cannot be
 *  measured, so it is chosen: a view of a body of revolution shows half the
 *  wrap, and half of 30 is 15, of which the ones nearest the limb foreshorten
 *  under the detection floor.
 *
 *  "3 px" is read as a connected-component **area**, not a diameter, and that
 *  reading is forced by the row's own arithmetic rather than assumed: 13 marks
 *  at `graffiti.coverage` 0.019 of an 8020 px silhouette is 152 px of ink, so
 *  the mean counted mark is 11.7 px in area and 3.9 px across. A 3 px *diameter*
 *  floor would sit at 7.1 px of area, above two thirds of the population the
 *  row says it counted; a 3 px *area* floor sits at 1.95 px across, below it.
 *  The distinction moves the achievable count by a factor of two, so it is not
 *  a detail. */
const N_MARKS = 30;

/** `graffiti.coverage` = 0.019 +- 0.008 of *silhouette*. This canvas covers the
 *  barrel only (u 0 -> 0.808), which is roughly 78 % of the silhouette area, so
 *  ink laid at 0.024 of the canvas realises 0.019 of the silhouette if only the
 *  barrel is marked -- the row's centre -- and 0.024 if the frame is marked too.
 *  Both are inside [0.011, 0.027]. */
const COVERAGE = 0.024;

/** `graffiti.sizeMaxOverMedian` = 1.9 +- 0.6, size = sqrt(4A/pi). Exact on the
 *  canvas by construction. What the row actually measures is the ratio over the
 *  *surviving* islands in a view, where the lower tail has been truncated by the
 *  detection floor. Measured off the generated canvas it runs 1.49-2.00 over
 *  twelve yaws. */
const SIZE_MAX_OVER_MEDIAN = 1.9;

/** Smallest mark as a fraction of the median. Not constrained: the row bounds
 *  max/median and says nothing about min/median. 0.78 rather than the 0.53 a
 *  symmetric log ramp would give, because marks below the floor are invisible
 *  ink -- they spend the coverage budget without appearing in the count, and at
 *  0.62 the count drops out of band at the smaller view scales. */
const SIZE_FLOOR = 0.78;

/** `graffiti.tealMagentaArea` = 1.8 +- 0.5. Teal's share of total mark area. */
const TEAL_AREA_SHARE = 1.8 / (1 + 1.8);

/**
 * `graffiti.densityBias` = 2.5 +- 1.0, paint density / brass density. DECLARED
 * at 1.9, and the reason is arithmetic rather than taste.
 *
 * On this wrap the brass bands are 42.4 % of the substrate area (collar 1.14 D,
 * mid-band 1.18 D and the lattice at 1.45 D are wide out of proportion to their
 * axial spans). `graffiti.onMetal` requires >= 25 % of mark area on brass. Those
 * two rows are the same quantity read twice, and on *this* substrate split they
 * trade directly: at 2.5 the brass share lands near 23 % and `onMetal` fails; at
 * 2.2 it clears by a tenth of a point; at 1.9 it lands at 27.2 %, which is both
 * clear of the floor and nearer `onMetal`'s own evidence figure of 32 %.
 *
 * So the density row is shipped 0.6 below its centre and inside its band, to buy
 * `graffiti.onMetal` (conf 0.80, a hard floor) two points of margin over
 * `graffiti.densityBias` (conf 0.55, a +-1.0 band). The two cannot both sit at
 * their measured centres here, because the view that measured them contains the
 * rail, and the rail is brass that this wrap does not reach.
 */
const PAINT_OVER_BRASS = 1.9;

/** `graffiti.orientationRandom`: mean abs(mark axis - barrel axis) in [35, 55]
 *  deg. Orientations are a stratified sweep of [0, 180), whose folded mean is
 *  exactly 45 -- the row's own note is that "the marks ignore the form", and a
 *  sweep states that more honestly than a random draw that happens to land near
 *  45.
 *
 *  Elongation is DECLARED, mean 1.8:1 over a [1.3, 2.3] spread. §6.11 measures
 *  each island's PCA *axis* and never its aspect, so a single constant would be
 *  asserting something the reference does not say -- and it also reads as
 *  confetti, thirty copies of one lozenge at thirty angles. The spread comes
 *  from a golden-ratio hash of the mark index rather than the generator, so it
 *  costs no draws and leaves every verified statistic above untouched: the
 *  scale(major, 1/major) that applies it is area-preserving, so equivalent
 *  diameter, coverage and the size ratio do not move. */
const MARK_ASPECT_MIN = 1.3;
const MARK_ASPECT_MAX = 2.3;

/** Where the soft edge crosses alpha 0.5, as a fraction of the drawn radius.
 *  An accent-hue mask thresholds somewhere near there, so the mark's *measured*
 *  diameter is this times its drawn one, and the sizes are solved in measured
 *  diameter and drawn larger. Get this backwards and coverage lands 35 % light. */
const ALPHA_HALF_RADIUS = 0.81;

/** Two sub-threshold specks per mark. They carry the hue mask's area but sit
 *  around 1 px at view scale, under the >= 3 px island floor, so they add to
 *  `graffiti.coverage` without adding to `graffiti.count.perView`. Spray paint
 *  that stops dead at the stencil edge is the tell that a decal was pasted on. */
const SPECK_SCALE = 0.18;
const SPECK_AREA_FACTOR = 1 + 2 * SPECK_SCALE * SPECK_SCALE;

/** Axial fraction of A -> fraction of L. The canvas spans the barrel group,
 *  because that is the part a single cylindrical projection can cover. */
function tOf(u: number): number {
  return u / BARREL_FRACTION;
}

/** DECLARED. §6.5 gives the mid-band's diameter and §6.4 its centre; §3 calls it
 *  "narrow" and no view resolves its width. */
const MID_BAND_HALF_U = 0.014;

/** Substrate bands along the wrap, from the §6.4 axial map and §6.5 diameters.
 *  `od` weights each band's world area: a cylindrical projection maps a canvas
 *  patch to a world area proportional to the local radius, which is why the
 *  lattice carries more graffiti area than its axial span suggests. */
const BANDS: { t0: number; t1: number; od: number; brass: boolean }[] = [
  { t0: 0, t1: tOf(AXIAL.muzzleCollarFrontLip), od: OD.liner, brass: false },
  { t0: tOf(AXIAL.muzzleCollarFrontLip), t1: tOf(AXIAL.muzzleCollarStep), od: OD.muzzleCollar, brass: true },
  { t0: tOf(AXIAL.muzzleCollarStep), t1: tOf(AXIAL.midBandCentre - MID_BAND_HALF_U), od: OD.tube, brass: false },
  { t0: tOf(AXIAL.midBandCentre - MID_BAND_HALF_U), t1: tOf(AXIAL.midBandCentre + MID_BAND_HALF_U), od: OD.midBand, brass: true },
  { t0: tOf(AXIAL.midBandCentre + MID_BAND_HALF_U), t1: tOf(AXIAL.latticeFront), od: OD.tube, brass: false },
  { t0: tOf(AXIAL.latticeFront), t1: tOf(AXIAL.latticeRear), od: OD.lattice, brass: true },
];

/** The two islands `graffiti.crossesSeam` actually found, on their own seams,
 *  with the index of the band on the muzzle side of each. They take the two
 *  largest marks: an island that has to register as spanning two meshes has to
 *  be big enough to straddle a boundary at view scale. */
const SEAM_MARKS = [
  { t: tOf(AXIAL.muzzleCollarStep), teal: false, band: 1 },
  { t: tOf(AXIAL.latticeFront), teal: true, band: 4 },
];

/** Deterministic, because an acceptance tool that re-renders has to score the
 *  same picture twice. Math.random() here would make every graffiti row noise. */
function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** Size as a multiple of the median, at quantile q: linear from SIZE_FLOOR below
 *  the median, log-spaced to SIZE_MAX_OVER_MEDIAN above it. A symmetric log ramp
 *  would put a third of the marks under the 3 px floor and cost the count row
 *  the marks it needs; truncating the lower tail instead keeps max/median exact
 *  where the row states it and only tightens a bound nothing measures. */
function sizeFactor(q: number): number {
  return q < 0.5
    ? SIZE_FLOOR + (1 - SIZE_FLOOR) * 2 * q
    : Math.pow(SIZE_MAX_OVER_MEDIAN, 2 * q - 1);
}

type Canvas2D = { canvas: HTMLCanvasElement; ctx: CanvasRenderingContext2D };

function makeCanvas(w: number, h: number): Canvas2D {
  const el =
    typeof document !== 'undefined'
      ? document.createElement('canvas')
      : (new (globalThis as unknown as { OffscreenCanvas: new (w: number, h: number) => unknown })
          .OffscreenCanvas(w, h) as unknown as HTMLCanvasElement);
  el.width = w;
  el.height = h;
  const ctx = el.getContext('2d') as CanvasRenderingContext2D | null;
  if (!ctx) throw new Error('finish.ts: no 2D canvas context; graffitiTexture needs a DOM or OffscreenCanvas host');
  return { canvas: el, ctx };
}

/** A soft-edged blob of measured diameter `d`, drawn from the current transform
 *  origin. Opaque out to ALPHA_HALF_RADIUS, then a ramp to zero -- a hard-edged
 *  ellipse reads as a sticker at every zoom, and a fully gaussian one loses so
 *  much area to the falloff that the coverage solve stops predicting anything. */
function blob(ctx: CanvasRenderingContext2D, cx: number, cy: number, d: number, rgb: string): void {
  const r = d / 2 / ALPHA_HALF_RADIUS;
  // Opaque core out to CORE, then a linear ramp to zero, so alpha crosses 0.5
  // at exactly (CORE + 1)/2 = ALPHA_HALF_RADIUS. Deriving CORE from the
  // constant rather than writing both keeps the coverage solve honest: with the
  // two written independently they drift, and coverage misses by the square of
  // the drift without anything failing loudly.
  const CORE = 2 * ALPHA_HALF_RADIUS - 1;
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
  g.addColorStop(0, `rgba(${rgb},1)`);
  g.addColorStop(CORE, `rgba(${rgb},1)`);
  g.addColorStop(1, `rgba(${rgb},0)`);
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
}

/**
 * The graffiti as an RGBA canvas texture.
 *
 * Parameterisation, which the assembly has to honour or every §6.11 row is
 * measuring something else:
 *
 *   texture x  = t, fraction of L from the muzzle. x = xOfBarrel(t).
 *   texture y  = circumference, theta / 2pi.
 *
 * The canvas is sized so a circle on it is a circle on the nominal tube: its
 * aspect is pi*D : L. wrapS clamps (the barrel ends), wrapT repeats (the seam
 * closes), and marks that cross the seam are drawn three times so they do not
 * chop.
 *
 * The background is **transparent**, not white. This is a decal map, not a base
 * map: three multiplies `map` into `color`, so laying it on brass as a plain
 * `.map` would give magenta-times-brass, which is brown. Composite it over a
 * per-part base in a canvas, or put it on a transparent overlay skin
 * (`transparent: true, depthWrite: false`, offset ~0.15 mm).
 *
 * Measured back off the generated canvas at size 1024 -- connected components
 * on the alpha channel with the circumference wrapped, projected through a
 * cos-foreshortened half-wrap at twelve yaws. Not predicted; read:
 *
 *   graffiti.coverage           0.0187 realised (0.0240 on canvas)  0.019 +- 0.008
 *   graffiti.count.perView      11-14, mean 12.3                    13 +- 5
 *   graffiti.onMetal            0.272                               >= 0.25
 *   graffiti.densityBias        1.91                                2.5 +- 1.0
 *   graffiti.tealMagentaArea    1.802                               1.8 +- 0.5
 *   graffiti.orientationRandom  45.7 deg                            [35, 55]
 *   graffiti.sizeMaxOverMedian  1.49-2.00 over the yaws             1.9 +- 0.6
 *   graffiti.crossesSeam        2 by construction                   >= 1
 *
 * Two of those are model-dependent rather than measured outright. The count and
 * the size ratio both need a view scale to threshold against, taken here as the
 * gun spanning 210 px of the 236 px crop; they hold over 180-240 px and over a
 * 12 % allowance for the hue mask catching the soft halo. The coverage figure
 * assumes the barrel is 78 % of the silhouette. If the assembly projects this
 * texture onto the receiver and grip as well, coverage rises to 0.024 and the
 * count rises with it -- both still in band, but re-measure rather than assume.
 *
 * Note also that `mat.accent.hues`, `mat.accent.L_gap` and
 * `mat.accent.outchroma` are [MAT] rows, and [MAT] reads a *mesh's assigned
 * material*. A texture has no mesh, so if the graffiti ships only as this
 * texture those three rows have no host and read as failures. The assembly
 * should build at least one `graffiti.mark.N` mesh per accent carrying
 * `accentMagenta` / `accentTeal` -- the knob in `knob.magenta.count` is already
 * one of them.
 */
export function graffitiTexture(size = 1024): THREE.CanvasTexture {
  const W = Math.max(64, Math.round(size));
  const H = Math.max(32, Math.round((W * Math.PI * D) / L));
  const { canvas, ctx } = makeCanvas(W, H);
  ctx.clearRect(0, 0, W, H);

  const rnd = lcg(0x2a97);

  // Sizes first: the coverage budget fixes the median, and the median fixes
  // every mark. Solve for d0 so that sum(pi/4 * (d0*f)^2) * specks == the ink
  // budget, rather than picking sizes and hoping the coverage lands.
  const q = Array.from({ length: N_MARKS }, (_, i) => (i + 0.5) / N_MARKS);
  const f = q.map(sizeFactor);
  const sumF2 = f.reduce((s, v) => s + v * v, 0);
  const d0 = Math.sqrt((COVERAGE * W * H) / (SPECK_AREA_FACTOR * (Math.PI / 4) * sumF2));

  // Axial placement by filling an ink BUDGET per band, not by sampling a
  // weighted CDF. Sampling positions and then hoping the areas follow does not
  // work at this count: 30 draws over 6 bands, paired with a 2.4:1 spread of
  // sizes, moved the realised density ratio from a requested 1.9 to 3.4 and put
  // `graffiti.onMetal` at 17 % against its 25 % floor. Allocating largest-mark-
  // first to whichever band is furthest under its budget lands both rows.
  //
  // Absolute deficit, not relative: the mid-band is 3 % of the wrap, so on a
  // relative-deficit rule the first mark drawn goes there and overshoots that
  // band by 3x, which is where a third of the brass budget then sits.
  const budget = BANDS.map((b) => (b.brass ? 1 : PAINT_OVER_BRASS) * (b.t1 - b.t0));
  const budgetSum = budget.reduce((s, v) => s + v, 0);
  const ink = f.reduce((s, v) => s + (Math.PI / 4) * (d0 * v) ** 2 * SPECK_AREA_FACTOR, 0);
  const target = budget.map((w) => (ink * w) / budgetSum);
  const filled = BANDS.map(() => 0);

  type Mark = { t: number; y: number; d: number; angle: number; teal: boolean };
  const marks: Mark[] = [];
  const sizes = f.map((v) => d0 * v).sort((p, r) => r - p);

  for (let i = 0; i < N_MARKS; i++) {
    const d = sizes[i];
    const area = (Math.PI / 4) * d * d * SPECK_AREA_FACTOR;
    const seam = i < SEAM_MARKS.length ? SEAM_MARKS[i] : null;
    if (seam) {
      // A seam mark sits on a boundary, so it spends half its ink either side.
      filled[seam.band] += area / 2;
      filled[seam.band + 1] += area / 2;
      marks.push({ t: seam.t, y: 0, d, angle: 0, teal: seam.teal });
      continue;
    }
    let j = 0;
    for (let k = 1; k < BANDS.length; k++) {
      if (target[k] - filled[k] > target[j] - filled[j]) j = k;
    }
    filled[j] += area;
    marks.push({ t: BANDS[j].t0 + rnd() * (BANDS[j].t1 - BANDS[j].t0), y: 0, d, angle: 0, teal: false });
  }

  // Circumference: a stratified sweep, shuffled so size does not track theta.
  // Sampling y uniformly makes the per-view count Binomial(N, 1/2) -- sd 2.7 on
  // a row whose whole band is +-5 -- and it then differs at every yaw. A sweep
  // puts exactly half the marks in front of the camera whichever way it looks,
  // which is what a row stated per view and never per object actually wants.
  const ys = marks.map((_, i) => ((i + 0.5) / N_MARKS) * H);
  for (let i = ys.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [ys[i], ys[j]] = [ys[j], ys[i]];
  }
  // Orientation: the stratified sweep of [0, 180) whose folded mean is exactly
  // 45, dealt out on a stride coprime with N so it does not track size either.
  // A stride costs no draws, which keeps the sequence above reproducible.
  marks.forEach((m, i) => {
    m.y = ys[i];
    m.angle = (((i * 7 + 3) % N_MARKS) + 0.5) * (Math.PI / N_MARKS);
  });

  // Colour by area, not by count: the row is an area ratio. The two seam marks
  // are already coloured by `graffiti.crossesSeam`'s own evidence, so they are
  // counted first and the rest fill in around them.
  let tealArea = 0;
  let allArea = 0;
  for (let i = 0; i < SEAM_MARKS.length; i++) {
    const a2 = marks[i].d * marks[i].d;
    if (marks[i].teal) tealArea += a2;
    allArea += a2;
  }
  for (let i = SEAM_MARKS.length; i < marks.length; i++) {
    const a2 = marks[i].d * marks[i].d;
    marks[i].teal = (tealArea + a2) / (allArea + a2) <= TEAL_AREA_SHARE;
    if (marks[i].teal) tealArea += a2;
    allArea += a2;
  }

  const MAGENTA = `${(BASE.accentMagenta >> 16) & 255},${(BASE.accentMagenta >> 8) & 255},${BASE.accentMagenta & 255}`;
  const TEAL = `${(BASE.accentTeal >> 16) & 255},${(BASE.accentTeal >> 8) & 255},${BASE.accentTeal & 255}`;

  marks.forEach((m, i) => {
    const rgb = m.teal ? TEAL : MAGENTA;
    const hash = (i * 0.618033988749 + 0.37) % 1;
    const major = Math.sqrt(MARK_ASPECT_MIN + (MARK_ASPECT_MAX - MARK_ASPECT_MIN) * hash);
    // Drawn three times so a mark straddling the circumferential seam is one
    // continuous island rather than two half ones -- which would also inflate
    // the island count the row is trying to pin.
    for (const yOff of [-H, 0, H]) {
      ctx.save();
      ctx.translate(m.t * W, m.y + yOff);
      ctx.rotate(m.angle);
      ctx.scale(major, 1 / major);
      blob(ctx, 0, 0, m.d, rgb);
      const off = m.d * (0.78 + 0.22 * ((m.t * 977) % 1));
      blob(ctx, off, 0, m.d * SPECK_SCALE, rgb);
      blob(ctx, -off * 0.86, m.d * 0.1, m.d * SPECK_SCALE, rgb);
      ctx.restore();
    }
  });

  const tex = new THREE.CanvasTexture(canvas);
  tex.name = 'graffiti.marks';
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.needsUpdate = true;
  // The canvas covers L of a gun that is A long; a consumer mapping the whole
  // object rather than the barrel needs to know the wrap stops at the breech.
  tex.userData = { spansBarrelFractionOfA: L / A, axis: 'x = t of L from the muzzle, y = theta/2pi' };
  return tex;
}
