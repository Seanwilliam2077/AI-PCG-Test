/**
 * The frozen datum: the frame of reference, and the numbers every module measures against.
 *
 * Named `datum` rather than `frame` because the gun has a part group called the frame --
 * the receiver, port, hammer and trigger -- and two meanings of one word in one codebase
 * is how a module ends up importing the wrong thing.
 *
 * `docs/CONTRACT.md` §2 declares the model frame and §6 states every dimension as a
 * ratio against one of four quantities. Those four live here, once, so that a module
 * cannot quietly adopt its own denominator -- which is exactly how the six measurement
 * reports came to disagree before the contract reconciled them.
 *
 *   A  overall axial extent, muzzle vertex to butt vertex
 *   D  tube outside diameter; R = D / 2
 *   L  barrel group axial extent, muzzle vertex to the lattice's rear face
 *   u  axial parameter: 0 at the frontmost vertex, 1 at the rearmost
 *
 * Only two absolute numbers enter the whole model, and both are DECLARED rather than
 * measured, because the reference sheet carries no dimension anywhere:
 *
 *   A = 290 mm   contract `gun.length.mm`, 290 +- 45, confidence 0.35
 *   D =  52 mm   contract `barrel.tube.od.mm`, 52 +- 7, confidence 0.45
 *
 * Everything else is a ratio, so if the scale chain is wrong -- and the contract's own
 * audit puts it at "+-15 % at best, and it rests on an axiom" -- the shape survives and
 * only the millimetres move.
 */

/** Overall axial extent, metres. DECLARED. */
export const A = 0.290;

/** Tube outside diameter, metres. DECLARED. */
export const D = 0.052;

/** Tube outside radius, metres. */
export const R = D / 2;

/** Barrel axial fraction of A, contract `gun.barrel.axialFraction` = 0.808 +- 0.030. */
export const BARREL_FRACTION = 0.808;

/** Barrel group axial extent, metres. */
export const L = A * BARREL_FRACTION;

/**
 * The origin is the breech face on the bore axis, which is also the barrel/frame
 * junction and the lattice collar's rear face -- contract §2 and `barrel.lattice.rear.u`
 * put all three at u = 0.808. So the muzzle sits at +L and the butt at L - A.
 */
export const X_MUZZLE = L;
export const X_BUTT = L - A;

/** Axial parameter from a model-space x. u = 0 at the muzzle, 1 at the butt. */
export function uOf(x: number): number {
  return (X_MUZZLE - x) / A;
}

/** Model-space x from an axial parameter. */
export function xOf(u: number): number {
  return X_MUZZLE - u * A;
}

/** Model-space x from a fraction of the BARREL's length, measured from the muzzle. */
export function xOfBarrel(t: number): number {
  return X_MUZZLE - t * L;
}

/**
 * Every part the contract's assembly tree (§3) names, as the mesh name it must carry.
 *
 * `tools/check_contract.py` looks parts up by mesh name and treats a constraint naming
 * a part that was not built as a FAILURE rather than a skip, so these strings are the
 * interface between the model and its own acceptance test. A part renamed here without
 * the contract being renamed too will fail loudly, which is the intent.
 */
export const PART = {
  root: 'zapper',

  barrel: 'barrel',
  liner: 'barrel.liner',
  bore: 'barrel.bore',
  muzzleCollar: 'barrel.muzzle-collar',
  ringFore: 'barrel.muzzle-collar.ring-fore',
  ringMid: 'barrel.muzzle-collar.ring-mid',
  ringAft: 'barrel.muzzle-collar.ring-aft',
  tubeFore: 'barrel.tube-fore',
  midBand: 'barrel.mid-band',
  lug: 'barrel.lug',
  tubeAft: 'barrel.tube-aft',
  lattice: 'barrel.lattice-collar',
  latticeRimFore: 'barrel.lattice-collar.rim-fore',
  latticeRimAft: 'barrel.lattice-collar.rim-aft',
  latticeCutout: 'barrel.lattice-collar.cutout',

  rail: 'barrel.rail',
  railMount: 'barrel.rail.mount-block',
  railStud: 'barrel.rail.stud',
  railHook: 'barrel.rail.rear-hook',

  frame: 'frame',
  receiver: 'frame.receiver',
  port: 'frame.port',
  portFlange: 'frame.port.flange',
  hammerSpur: 'frame.hammer-spur',
  hammerRib: 'frame.hammer-spur.rib',
  trigger: 'frame.trigger',
  triggerGuard: 'frame.trigger-guard',

  grip: 'grip',
  gripBody: 'grip.body',
  gripButt: 'grip.butt-cap',
  gripToeStud: 'grip.butt-cap.toe-stud',
} as const;

/**
 * The axial map, contract §6.4, as fractions of A measured from the muzzle.
 * Anything a module places along the barrel reads it from here.
 */
export const AXIAL = {
  muzzleTip: 0.000,
  muzzleCollarFrontLip: 0.078,
  railFwdStud: 0.101,
  muzzleCollarStep: 0.187,
  lugCentre: 0.407,
  midBandCentre: 0.449,
  latticeFront: 0.662,
  latticeRear: 0.808,
  portCentre: 0.884,
  buttRear: 1.000,
} as const;

/**
 * Diameters, contract §6.5, as multiples of D. The lattice is the widest thing on the
 * object (`gun.maxWidth.isLatticeCollar`), which the assembly asserts rather than assumes.
 */
export const OD = {
  tube: 1.00,
  liner: 0.69,
  bore: 0.52,
  muzzleCollar: 1.14,
  midBand: 1.18,
  lattice: 1.45,
} as const;

/** Lattice collar, contract §6.6. */
export const LATTICE = {
  /** `lattice.opening.count` = 16, accept 12-20. Confidence 0.35 -- the least certain
   *  number in the document, and it is the object's signature feature. */
  cutouts: 16,
  /** `lattice.opening.pitch` = 22 +- 3 degrees. 360/16 = 22.5, inside the band. */
  pitchDeg: 360 / 16,
  /** `lattice.opening.axialLen` = 0.069 +- 0.012 L. */
  cutoutAxialFractionOfL: 0.069,
  /** `lattice.rows` = 1, DECLARED. Two staggered rows fit the pixels equally well and
   *  are explicitly not excluded by the reference. */
  rows: 1,
} as const;

/** Muzzle, contract §6.7. */
export const MUZZLE = {
  /** `muzzle.ring.count` = 3, accept 2-4. */
  rings: 3,
  /** `muzzle.liner.protrudes`: the liner's axial max exceeds the collar's by
   *  0.05 +- 0.03 L. One report reads this the opposite way (audit D11), so the
   *  contract kept "protrudes" at a reduced confidence of 0.45 and recorded the
   *  disagreement rather than averaging it away. */
  linerProtrudeFractionOfL: 0.05,
} as const;
