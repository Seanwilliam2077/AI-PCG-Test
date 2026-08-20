/**
 * The choker: three leather wraps round the throat, a shallow X crossing the
 * front of them, and one strap dropping out of the bottom wrap toward the top.
 *
 * Every piece is a ring round the neck column, cut to shape: the wraps by
 * horizontal slabs, the X by tilted ones.  So the X really does pass round the
 * throat and end tucked inside a horizontal wrap, and the whole choker comes
 * out as one connected surface rather than straps floating on a band.
 *
 * The rings are hollow, not solid discs: a disc through a neck has two
 * elliptical cut faces of ~78 cm^2 each, all of it buried, and five of them
 * would spend more triangles on invisible caps than on the choker.  They are
 * however sunk 6 mm into the neck (see `ring`) so the shell stays thicker than
 * the coarsest voxel.
 */
import { Field, Vec3, box } from '../sdf/types.js';
import { capsuleOval, field, intersect, offset, shell, union } from '../sdf/ops.js';
import { orientedBox } from '../sdf/curve.js';
import { PartContext, PartModule, Shell, Tagged, nearestMaterial, nums } from './types.js';

const BOUNDS = box([-0.085, 1.400, -0.085], [0.085, 1.500, 0.085]);

const len = (a: Vec3): number => Math.hypot(a[0], a[1], a[2]);
const unit = (a: Vec3): Vec3 => {
  const l = len(a) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};
const cross = (a: Vec3, b: Vec3): Vec3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

/** Horizontal slab, exact and 1-Lipschitz. */
const ySlab = (y0: number, y1: number): Field =>
  field((_x, y, _z) => Math.max(y0 - y, y - y1), box([-0.3, y0, -0.3], [0.3, y1, 0.3]), 1);

export const chokerPart: PartModule = {
  id: 'choker',
  build(ctx: PartContext): Shell[] {
    const { mat } = ctx;
    const c = nums(ctx.spec.choker);

    /* ---- the neck the choker is cut against ---- */

    const neck = capsuleOval(
      [0, c.neckY0, c.neckZ0], [0, c.neckY1, c.neckZ1],
      c.neckR0, c.neckR1, c.neckSquashZ, 1,
    );

    /** A point on the neck surface: theta is measured from the front, +X to her left. */
    const neckPoint = (theta: number, y: number, dr: number): Vec3 => {
      const h = Math.max(0, Math.min(1, (y - c.neckY0) / (c.neckY1 - c.neckY0)));
      const r = c.neckR0 + (c.neckR1 - c.neckR0) * h;
      const zc = c.neckZ0 + (c.neckZ1 - c.neckZ0) * h;
      return [
        (r + dr) * Math.sin(theta),
        y,
        zc + (r * c.neckSquashZ + dr) * Math.cos(theta),
      ];
    };

    /**
     * A ring hugging the neck, spanning `from`..`to` off the skin.
     *
     * Every piece is sunk `neckInset` *into* the neck rather than stopping at
     * the skin.  A 5 mm-proud leather band is thinner than the low LOD voxel
     * and meshes into loose speckle; carrying it 6 mm inside makes the shell
     * 13 mm thick everywhere, and the inner face is buried in the neck column
     * where nothing sees it.  Only `to` is visible, so the band still reads as
     * 5 mm of leather.
     */
    const ring = (to: number): Field => {
      const from = -c.neckInset;
      return shell(offset(neck, (from + to) / 2), (to - from) / 2);
    };

    /* ---- three horizontal wraps ---- */

    const skinRing = ring(c.gap + c.thickness);
    const bands = union(
      ...[c.bandY0, c.bandY1, c.bandY2].map((y) =>
        intersect(skinRing, ySlab(y - c.bandHalf, y + c.bandHalf))),
    );

    /* ---- the X across the front ---- */

    // Each arm is the same ring cut by a tilted slab, so it wraps the throat
    // instead of floating across it.  The tilt is chosen so that where the
    // wedge ends it at the side of the neck, its centre line is exactly on the
    // height of the bottom or top wrap and the two fuse.
    const proudRing = ring(c.gap + c.wrapProud + c.thickness);
    const wrapWedge = field(
      (_x, _y, z) => c.wrapBackZ - z,
      box([-0.09, 1.40, c.wrapBackZ], [0.09, 1.50, 0.09]),
      1,
    );
    // Clipped to the choker's own height as well: a tilted slab across a ring
    // keeps climbing at the sides, and without this the arms rear up past the
    // top wrap into a pair of horns.
    const wrapLimit = ySlab(c.bandY0 - c.bandHalf, c.bandY2 + c.bandHalf);
    const wrap = (tilt: number): Field => {
      const n = Math.hypot(1, tilt);
      return intersect(
        intersect(
          intersect(
            proudRing,
            field(
              (x, y, _z) => Math.abs(y - c.bandY1 - tilt * x) / n - c.wrapHalf,
              BOUNDS,
              1,
            ),
          ),
          wrapWedge,
        ),
        wrapLimit,
      );
    };
    const wraps = union(wrap(c.wrapTilt), wrap(-c.wrapTilt));

    /* ---- the strap dropping out of the bottom wrap ---- */

    const dropOut = c.gap + c.dropProud + c.dropThick;
    const dropSpan = dropOut + c.neckInset;
    const dr = (dropOut - c.neckInset) / 2;
    const N = 7;
    const pts: Vec3[] = [];
    const nrm: Vec3[] = [];
    for (let i = 0; i < N; i++) {
      const u = i / (N - 1);
      const th = c.dropTheta0 + (c.dropTheta1 - c.dropTheta0) * u;
      const y = c.dropY0 + (c.dropY1 - c.dropY0) * u;
      pts.push(neckPoint(th, y, dr));
      // Radially outward from the neck axis is close enough to the surface
      // normal on a column this straight.
      const a = neckPoint(th, y, 0), b = neckPoint(th, y, 0.01);
      nrm.push(unit([b[0] - a[0], 0, b[2] - a[2]]));
    }
    const segs: Field[] = [];
    for (let i = 1; i < N; i++) {
      const a = pts[i - 1], b = pts[i];
      const ex = unit([b[0] - a[0], b[1] - a[1], b[2] - a[2]]);
      const nA: Vec3 = [
        (nrm[i - 1][0] + nrm[i][0]) / 2,
        (nrm[i - 1][1] + nrm[i][1]) / 2,
        (nrm[i - 1][2] + nrm[i][2]) / 2,
      ];
      const d = nA[0] * ex[0] + nA[1] * ex[1] + nA[2] * ex[2];
      const ez = unit([nA[0] - d * ex[0], nA[1] - d * ex[1], nA[2] - d * ex[2]]);
      const ey = cross(ez, ex);
      const half: Vec3 = [
        len([b[0] - a[0], b[1] - a[1], b[2] - a[2]]) / 2 + 0.002,
        c.dropWidth / 2,
        dropSpan / 2,
      ];
      segs.push(orientedBox(
        [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2],
        ex, ey, ez, half, c.dropThick * 0.35,
      ));
    }
    const drop = union(...segs);

    const tags: Tagged[] = [
      { field: bands, mat: mat.cloth },
      { field: wraps, mat: mat.leather },
      { field: drop, mat: mat.leather },
    ];

    return [{
      name: 'choker',
      field: union(bands, wraps, drop),
      material: nearestMaterial(tags, mat.leather),
      // The gaps between the wraps are 4..6 mm.  At the round 1 value of 0.5 --
      // a 5.3 mm low-LOD voxel -- they were under one sample and the three
      // wraps plus the X baked as a single dark lump round the throat.
      voxelScale: Number.isFinite(c.voxelScale) ? c.voxelScale : 0.5,
    }];
  },
};
