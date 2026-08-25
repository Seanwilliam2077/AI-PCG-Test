/**
 * The on-disk mesh format.
 *
 * The bake meshes the character once and writes the result into TypeScript as
 * base64 typed arrays, so the viewer ships as code with no asset fetches and no
 * runtime meshing cost.  Positions are quantised to 16 bits inside the mesh's
 * own bounds -- at a body height of ~1.8 m that is a 28 micron step, well under
 * the finest voxel -- and normals to 8 bits, which together cut the payload to
 * about a third of raw floats.  Each buffer is then deflated, because the
 * index buffer of a Surface Nets mesh is extremely regular and compresses by
 * roughly 4x -- without that a high LOD is tens of megabytes of base64 and the
 * "ships as code" idea stops being practical.
 */
export interface EncodedGroup {
  name: string;
  /** Key into the material table. */
  material: string;
  /** Offset into the index array, in indices. */
  start: number;
  count: number;
}

export interface EncodedMesh {
  name: string;
  /** How the base64 payloads are packed. */
  codec: 'raw' | 'deflate';
  bounds: { min: [number, number, number]; max: [number, number, number] };
  vertexCount: number;
  triangleCount: number;
  /** base64 Uint16, 3 per vertex, quantised into `bounds`. */
  position: string;
  /** base64 Int8, 3 per vertex. */
  normal: string;
  /** base64 Uint8, 1 per vertex -- the material index for per-vertex effects. */
  material: string;
  /** base64 Uint32, 3 per triangle. */
  index: string;
  groups: EncodedGroup[];
}

export interface EncodedLod {
  name: string;
  voxel: number;
  meshes: EncodedMesh[];
}

export interface MaterialSpec {
  color: [number, number, number];
  roughness: number;
  metalness: number;
  /** Optional rim/emissive tint for hair and glowing bits. */
  sheen?: [number, number, number];
  transmission?: number;
}

export type MaterialTable = Record<string, MaterialSpec>;
