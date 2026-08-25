/**
 * The Zapper -- Jinx's shock pistol, holstered barrel-down on her LEFT thigh.
 *
 * HANDEDNESS: the pistol is on her **left**, which is **+X** in this frame and
 * appears on the **right** of a front view.  See docs/HANDEDNESS.md; round 1
 * had it on -X, which cost the front view and the whole colour term on that
 * flank.  Cross-check: the gun is visible in `body_0` (her left side) and
 * absent from `body_4` (her right side).
 *
 * The part is three volumes, not one gun:
 *
 *   canister  the fat glass/steel tank that hangs down the thigh
 *   gun       muzzle cap, brass bands, openwork collar, receiver, grip, rail
 *   holster   a slate sheath cradling the tank's inboard and rear faces,
 *             plus the two straps that tie it to the thigh
 *
 * The holster and the canister are what put the assembly on the silhouette;
 * modelling only the gun leaves the whole thing inside the trouser leg.
 *
 * Authored in a gun-local frame and then swung into place:
 *
 *   local +Y runs up the gun from the muzzle to the grip
 *   local +Z is the gun's front -- the side the barrel rail sits on
 *   local +X points outboard, away from the thigh
 *
 * MEASUREMENTS (ref/views/body_2.png, the front view, hue-segmented for the
 * gun's brass and steel; x is metres from the leg centreline, +X = her left):
 *
 *   y      assembly [inner, outer]      leg alone
 *   0.66   -- (assembly has ended)      0.124
 *   0.68   [0.125, 0.173]               0.122
 *   0.70   [0.132, 0.178]               0.123
 *   0.74   [0.144, 0.190]               0.128
 *   0.78   [0.152, 0.205]               0.132
 *   0.82   [0.162, 0.232]               0.142
 *
 * So the assembly is ~0.050 m across, its inboard face rides on the trouser
 * and its axis leans **outboard going up** at dx/dy = 0.31, which is why the
 * muzzle end disappears inside the leg's outline below y = 0.67.  The side
 * view (body_0) puts the gun's centre ~0.045 m forward of the thigh axis and
 * gives the matching forward lean, dz/dy = 0.28.
 *
 * `pitch` and `roll` produce those two slopes: rotateX tips the grip toward
 * +Z, rotateZ with a NEGATIVE angle tips it toward +X.  Do not set `yaw` --
 * transform() composes about world axes, so a yaw would shear the other two.
 */
import { Field, Vec3 } from '../sdf/types.js';
import { capsule, cylinder, roundBox, scale, torus, transform, union } from '../sdf/ops.js';
import { cut } from '../sdf/solids.js';
import { PartContext, PartModule, Shell, Tagged, nearestMaterial, paint } from './types.js';

interface ZapperSpec {
  anchor: number[];
  pitch: number;
  yaw: number;
  roll: number;
  /** Half-depth (local z) of the canister; half-width is this times `flat`. */
  tankR: number;
  /** How flat the assembly is against the thigh: local x half / local z half. */
  flat: number;
  tankBottom: number;
  tankTop: number;
  muzzleY: number;
  muzzleR: number;
  muzzleRingH: number;
  bandY: number;
  bandR: number;
  collarY: number;
  collarR: number;
  collarH: number;
  receiverY: number;
  receiverZ: number;
  receiverHalf: number[];
  gripY: number;
  gripZ: number;
  gripLength: number;
  gripR: number;
  guardY: number;
  guardZ: number;
  guardR: number;
  barrelZ: number;
  barrelR: number;
  barrelLength: number;
  /** Sheath: radius over the canister, inboard shift, and its y span. */
  holsterR: number;
  holsterX: number;
  holsterBottom: number;
  holsterTop: number;
  /** Local x above which the sheath is cut away, so the gun's outboard face shows. */
  holsterOpenX: number;
  /** Above this local y the sheath wraps all the way round the receiver. */
  holsterWrapY: number;
  /** Backing plate between the sheath and the thigh: how far inboard it reaches. */
  backingX: number;
  backingY: number[];
  backingZ: number;
  strapR: number;
  voxelScale: number;
}

const DEFAULTS: ZapperSpec = {
  anchor: [0.174, 0.752, 0.062],
  pitch: 0.26,
  yaw: 0.0,
  roll: -0.31,
  tankR: 0.028,
  flat: 0.75,
  tankBottom: -0.078,
  tankTop: 0.016,
  muzzleY: -0.1,
  muzzleR: 0.0325,
  muzzleRingH: 0.024,
  bandY: -0.022,
  bandR: 0.0315,
  collarY: 0.016,
  collarR: 0.032,
  collarH: 0.04,
  receiverY: 0.086,
  receiverZ: -0.004,
  receiverHalf: [0.021, 0.034, 0.038],
  gripY: 0.064,
  gripZ: 0.014,
  gripLength: 0.05,
  gripR: 0.016,
  guardY: 0.058,
  guardZ: 0.004,
  guardR: 0.02,
  barrelZ: 0.034,
  barrelR: 0.008,
  barrelLength: 0.15,
  holsterR: 0.035,
  holsterX: -0.007,
  holsterBottom: -0.09,
  holsterTop: 0.104,
  holsterOpenX: 0.004,
  holsterWrapY: 0.048,
  backingX: -0.056,
  backingY: [-0.07, 0.095],
  backingZ: 0.018,
  strapR: 0.007,
  voxelScale: 0.7,
};

function resolve(ctx: PartContext): ZapperSpec {
  const raw = (ctx.spec as unknown as { zapper?: Partial<ZapperSpec> }).zapper ?? {};
  return { ...DEFAULTS, ...raw } as ZapperSpec;
}

/**
 * A flattened cylinder: half-depth `rz` in local z, `rz * flat` in local x.
 *
 * Everything in this assembly has that section -- a holstered pistol is a slab
 * pressed against a thigh, not a rod -- and `scale` keeps the Lipschitz bound
 * honest for us, which a hand-written ellipse SDF would not.
 */
function oval(y0: number, y1: number, rz: number, flat: number, cx = 0, cz = 0): Field {
  return scale(
    cylinder([cx / flat, y0, cz], [cx / flat, y1, cz], rz),
    [flat, 1, 1],
  );
}

/** Everything in gun-local metres; caller swings it onto the thigh. */
function gunParts(z: ZapperSpec): { steel: Field[]; brass: Field[] } {
  const f = z.flat;

  // --- steel: canister, receiver, grip, guard ----------------------------
  // The canister is the part that carries the outline: it is the full length
  // of the thigh drop and it is what the reference reads as at 2 mm voxels.
  const tank = oval(z.tankBottom, z.tankTop, z.tankR, f);

  // Receiver is a wedge, not a brick: the frame proper plus a shorter, deeper
  // hammer shroud behind it, which is what gives the sheet's stepped rear.
  const receiver = roundBox(
    [0, z.receiverY, z.receiverZ],
    [z.receiverHalf[0], z.receiverHalf[1], z.receiverHalf[2]],
    0.012,
  );
  const shroud = roundBox(
    [0, z.receiverY + z.receiverHalf[1] * 0.5, z.receiverZ - z.receiverHalf[2] * 0.78],
    [z.receiverHalf[0] * 0.82, z.receiverHalf[1] * 0.5, z.receiverHalf[2] * 0.42],
    0.009,
  );

  // Grip rakes forward and up out of the receiver's front face, short and fat.
  const gripTop: Vec3 = [0, z.gripY + z.gripLength * 0.9, z.gripZ + z.gripLength * 0.74];
  const grip = capsule([0, z.gripY, z.gripZ], gripTop, z.gripR, z.gripR * 0.86);

  // Trigger guard hangs below the frame; only its lower arc is proud of the
  // receiver, which is all that is visible on the sheet at this size.
  const guard = torus([0, z.guardY, z.guardZ], z.guardR, 0.006, 0);

  // --- brass: muzzle cap, tank bands, collar, grip cap, barrel rail -------
  const muzzle = oval(z.muzzleY, z.muzzleY + z.muzzleRingH, z.muzzleR, f);
  const muzzleStep = oval(
    z.muzzleY + z.muzzleRingH,
    z.muzzleY + z.muzzleRingH + 0.010,
    z.muzzleR * 0.88,
    f,
  );
  const bandLow = oval(z.bandY - 0.044, z.bandY - 0.032, z.bandR * 0.98, f);
  const band = oval(z.bandY, z.bandY + 0.013, z.bandR, f);

  // Collar is two stacked rings of slightly different radius: at 2 mm voxels
  // that reads as the banded brass cuff on the sheet without modelling the
  // openwork diamonds, which fall below the voxel anyway.
  const collarLo = oval(z.collarY, z.collarY + z.collarH * 0.58, z.collarR, f);
  const collarHi = oval(
    z.collarY + z.collarH * 0.58,
    z.collarY + z.collarH,
    z.collarR * 0.90,
    f,
  );

  const gripCap = cylinder(
    [0, gripTop[1] + 0.003, gripTop[2] - 0.004],
    [0, gripTop[1] + 0.003, gripTop[2] + 0.012],
    z.gripR * 0.95,
  );

  // The rail is one plain brass strip the whole length on the sheet, ending in
  // a stub below the muzzle ring.
  const barrelTop = z.muzzleY + z.barrelLength;
  const barrel = cylinder(
    [0, z.muzzleY + 0.004, z.barrelZ],
    [0, barrelTop, z.barrelZ],
    z.barrelR,
  );

  return {
    steel: [tank, receiver, shroud, grip, guard],
    brass: [muzzle, muzzleStep, bandLow, band, collarLo, collarHi, gripCap, barrel],
  };
}

/**
 * The sheath: a slate cradle round the canister's inboard and rear faces, cut
 * open at the front so the tank and its brass bands still read.
 *
 * It is authored as a *solid* larger than the tank rather than `shell(tank,t)`
 * -- at the low LOD's 6 mm voxel a 4 mm wall meshes as a chain of blobs.  The
 * tank lives inside it and `paint` decides which surface is which.
 */
function holsterParts(z: ZapperSpec): { sheath: Field; straps: Field } {
  const f = z.flat;
  const cup = oval(z.holsterBottom, z.holsterTop, z.holsterR, f, z.holsterX, -0.004);
  // Below the receiver the sheath is only the inboard cradle -- the reference
  // shows the tank's brass and glass from the front, the side and the back --
  // and it closes right round above it.  `cut` takes the side it keeps as a
  // word, because getting the sign of an `intersect` backwards silently
  // produces a shell with no triangles.
  // The backing plate is what makes the assembly one silhouette with the leg
  // rather than a floating gun: measured on clay_2 the reference's outline is a
  // single run across the thigh at y = 0.80, while gun-only left a 0.016 m hole
  // between the trouser edge and the holster.
  const by = z.backingY;
  const backing = roundBox(
    [(z.backingX + 0.004) / 2, (by[0] + by[1]) / 2, -0.004],
    [(0.004 - z.backingX) / 2, (by[1] - by[0]) / 2, z.backingZ],
    0.012,
  );
  const sheath = union(
    cut(cup, 0, z.holsterOpenX, 'below'),
    cut(cup, 1, z.holsterWrapY, 'above'),
    backing,
  );

  // Two retention straps round the sheath, and the drop strap that carries the
  // whole thing up to the hip belt.
  const ring = (y: number, r: number) =>
    scale(torus([z.holsterX / f, y, -0.004], r, z.strapR, 1), [f, 1, 1]);
  const straps = union(
    ring(-0.052, z.holsterR + 0.002),
    ring(0.044, z.holsterR + 0.002),
    capsule(
      [z.holsterX - 0.004, z.holsterTop - 0.01, -0.016],
      [z.holsterX - 0.030, z.holsterTop + 0.085, -0.036],
      z.strapR * 1.5,
      z.strapR * 1.2,
    ),
  );
  return { sheath, straps };
}

export const zapperPart: PartModule = {
  id: 'zapper',
  build(ctx) {
    const { mat } = ctx;
    const z = resolve(ctx);
    const { steel, brass } = gunParts(z);
    const { sheath, straps } = holsterParts(z);

    const place = (f: Field) =>
      transform(f, {
        rotate: [z.pitch, z.yaw, z.roll],
        translate: [z.anchor[0], z.anchor[1], z.anchor[2]],
      });

    const steelField = place(union(...steel));
    const brassField = place(union(...brass));
    const sheathField = place(sheath);
    const strapField = place(straps);

    // The gun's own two metals sit *beside* each other, so nearestMaterial is
    // right for them.  The sheath and the straps are *stacked* on the tank, and
    // nearestMaterial would hand every point on the sheath to whichever gun
    // part it is deepest inside -- so those go on with paint(), outermost last.
    const tagged: Tagged[] = [
      { field: brassField, mat: mat.brass },
      { field: steelField, mat: mat.steel },
    ];
    let material = nearestMaterial(tagged, mat.steel);
    // Sampled off body_5 at the sheath: RGB 0.264 0.290 0.326, a slate
    // blue-grey -- `cloth` is within dE ~8 of that, `leather` is 25 away.
    material = paint(material, sheathField, mat.cloth, 0.003);
    material = paint(material, strapField, mat.leather, 0.003);

    const shell: Shell = {
      name: 'zapper',
      field: union(steelField, brassField, sheathField, strapField),
      material,
      voxelScale: z.voxelScale,
    };
    return [shell];
  },
};
