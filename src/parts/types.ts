/**
 * What a part module hands back, and the helpers every one of them uses.
 *
 * A part returns *shells*, not one merged field.  Meshing each shell on its own
 * grid is what keeps the bake affordable -- the boots do not pay for the head's
 * voxel size -- and it is also physically right: clothing is a separate surface
 * from the skin under it, so it should be a separate closed mesh, not a bump on
 * a single blob.  Blending only happens *within* a shell, via smoothUnion.
 */
import { Field, Vec3 } from '../sdf/types.js';
import { Skeleton, Spec } from '../spec.js';

export interface Shell {
  name: string;
  field: Field;
  /** Material index for a surface point. */
  material: (x: number, y: number, z: number) => number;
  /**
   * Multiplier on the LOD's voxel size.  The head and the face need about half
   * the body's voxel to hold an eyelid; the boots can take twice it.
   */
  voxelScale?: number;
}

export interface PartContext {
  spec: Spec;
  skel: Skeleton;
  /** Material name to index. */
  mat: Record<string, number>;
}

export interface PartModule {
  id: string;
  /** Ordered after these part ids in the shell list (cosmetic only). */
  build(ctx: PartContext): Shell[];
}

/** A field tagged with the material its surface should take. */
export interface Tagged {
  field: Field;
  mat: number;
}

/**
 * Material resolver: at a surface point, take the material of whichever tagged
 * field is nearest.  `bias` lets a decal-like field (a tattoo, a stripe) win
 * even though it sits fractionally inside the surface that carries it.
 */
export function nearestMaterial(entries: Tagged[], fallback: number): (x: number, y: number, z: number) => number {
  return (x, y, z) => {
    let best = Infinity;
    let m = fallback;
    for (let i = 0; i < entries.length; i++) {
      const d = entries[i].field.sdf(x, y, z);
      if (d < best) { best = d; m = entries[i].mat; }
    }
    return m;
  };
}

/** Constant material, for shells that are one colour throughout. */
export const constMaterial = (m: number) => () => m;

/**
 * Paint material `m` wherever `where` is within `depth` of the surface,
 * otherwise fall back.  This is how tattoos, stripes and trims are applied
 * without adding geometry.
 */
export function paint(
  base: (x: number, y: number, z: number) => number,
  where: Field,
  m: number,
  depth = 0.004,
): (x: number, y: number, z: number) => number {
  return (x, y, z) => (where.sdf(x, y, z) < depth ? m : base(x, y, z));
}

export const v3 = (x: number, y: number, z: number): Vec3 => [x, y, z];

/**
 * Read a spec block as plain numbers.
 *
 * Spec blocks carry a `$comment` string (or array of strings) alongside their
 * numbers, so `spec.boots as Record<string, number>` does not typecheck. This
 * does the cast once, in one place, instead of every part repeating it.
 */
export function nums(block: unknown): Record<string, number> {
  return block as Record<string, number>;
}

/** Squared distance from a point to a segment -- used by several parts. */
export function segmentDistance(p: Vec3, a: Vec3, b: Vec3): number {
  const bx = b[0] - a[0], by = b[1] - a[1], bz = b[2] - a[2];
  const px = p[0] - a[0], py = p[1] - a[1], pz = p[2] - a[2];
  const l2 = bx * bx + by * by + bz * bz || 1e-12;
  const t = Math.max(0, Math.min(1, (px * bx + py * by + pz * bz) / l2));
  return Math.hypot(px - bx * t, py - by * t, pz - bz * t);
}
