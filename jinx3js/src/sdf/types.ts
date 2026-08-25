/**
 * Signed distance fields, in metres.
 *
 * Frame: Y up, origin on the floor midway between the feet, the character
 * facing +Z.  So +X is the viewer's right (the character's left) in the front
 * view, which is what a default Three.js camera on +Z sees.
 *
 * A field returns the signed distance to its surface, negative inside.  Fields
 * built with smooth operators or non-uniform scale are no longer true distance
 * -- they under-estimate -- so every field carries a `lip` (Lipschitz) bound
 * saying by how much, and the mesher divides by it before trusting a value as
 * a safe step.  Keeping that honest is what lets the mesher skip empty space
 * instead of sampling the whole grid.
 */
export type Vec3 = readonly [number, number, number];

export type Sdf = (x: number, y: number, z: number) => number;

export interface Box {
  min: Vec3;
  max: Vec3;
}

export interface Field {
  sdf: Sdf;
  /** Conservative bound on |grad| (1 for an exact distance field). */
  lip: number;
  /** Bound on the surface; the mesher only samples inside it. */
  bounds: Box;
}

export const box = (min: Vec3, max: Vec3): Box => ({ min, max });

export const boxUnion = (a: Box, b: Box): Box =>
  box(
    [Math.min(a.min[0], b.min[0]), Math.min(a.min[1], b.min[1]), Math.min(a.min[2], b.min[2])],
    [Math.max(a.max[0], b.max[0]), Math.max(a.max[1], b.max[1]), Math.max(a.max[2], b.max[2])],
  );

export const boxExpand = (a: Box, r: number): Box =>
  box(
    [a.min[0] - r, a.min[1] - r, a.min[2] - r],
    [a.max[0] + r, a.max[1] + r, a.max[2] + r],
  );

export const boxContains = (a: Box, x: number, y: number, z: number): boolean =>
  x >= a.min[0] && x <= a.max[0] &&
  y >= a.min[1] && y <= a.max[1] &&
  z >= a.min[2] && z <= a.max[2];

export const boxOverlaps = (a: Box, b: Box): boolean =>
  a.min[0] <= b.max[0] && a.max[0] >= b.min[0] &&
  a.min[1] <= b.max[1] && a.max[1] >= b.min[1] &&
  a.min[2] <= b.max[2] && a.max[2] >= b.min[2];

export const boxSize = (a: Box): Vec3 =>
  [a.max[0] - a.min[0], a.max[1] - a.min[1], a.max[2] - a.min[2]];

export const boxOf = (points: Vec3[], pad = 0): Box => {
  const mn: [number, number, number] = [Infinity, Infinity, Infinity];
  const mx: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (const p of points) {
    for (let i = 0; i < 3; i++) {
      if (p[i] < mn[i]) mn[i] = p[i];
      if (p[i] > mx[i]) mx[i] = p[i];
    }
  }
  return boxExpand(box(mn, mx), pad);
};

/** Distance from a point to a box, 0 inside -- the mesher's block test. */
export const boxDistance = (a: Box, x: number, y: number, z: number): number => {
  const dx = Math.max(a.min[0] - x, 0, x - a.max[0]);
  const dy = Math.max(a.min[1] - y, 0, y - a.max[1]);
  const dz = Math.max(a.min[2] - z, 0, z - a.max[2]);
  return Math.hypot(dx, dy, dz);
};
