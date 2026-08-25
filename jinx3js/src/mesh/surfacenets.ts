/**
 * Naive Surface Nets over a sparsely sampled grid.
 *
 * Dual contouring without the QEF: one vertex per sign-changing cell, placed at
 * the mean of the cell's edge crossings, quads emitted around every
 * sign-changing grid edge.  It gives closed, watertight, evenly sized quads on
 * organic shapes, which is what a character wants, and unlike marching cubes it
 * has no ambiguous cases to resolve.
 *
 * The grid is sampled a z-layer at a time, and each layer is filled in blocks:
 * one probe at the block centre, and if the field's Lipschitz-corrected value
 * clears the block's half-diagonal the whole block is filled with that sign
 * without another evaluation.  On a character that skips well over 90 % of the
 * volume, which is what makes a 3 mm voxel affordable in plain TypeScript.
 */
import { Field } from '../sdf/types.js';

export interface MeshData {
  positions: Float32Array;
  normals: Float32Array;
  materials: Uint8Array;
  indices: Uint32Array;
  /** Grid statistics, reported so a bake can show what it cost. */
  stats: {
    dims: [number, number, number];
    samples: number;
    evaluated: number;
    blocksSkipped: number;
    blocksSampled: number;
    vertices: number;
    triangles: number;
    ms: number;
  };
}

export interface MeshOptions {
  voxel: number;
  /** Material id for each surface vertex; defaults to 0. */
  material?: (x: number, y: number, z: number) => number;
  /** Block edge in voxels for the empty-space test. */
  block?: number;
  /** Extra Lipschitz safety on top of the field's own bound. */
  safety?: number;
}

const BIG = 1e3;

/** Cube corner c has bit0 = +x, bit1 = +y, bit2 = +z. */
const EDGES: [number, number][] = [
  [0, 1], [2, 3], [4, 5], [6, 7],
  [0, 2], [1, 3], [4, 6], [5, 7],
  [0, 4], [1, 5], [2, 6], [3, 7],
];

export function surfaceNets(f: Field, opts: MeshOptions): MeshData {
  const t0 = Date.now();
  const h = opts.voxel;
  const block = opts.block ?? 8;
  const safety = opts.safety ?? 1.05;
  const lip = Math.max(1e-6, f.lip) * safety;
  const sdf = f.sdf;

  const pad = 2 * h;
  const ox = f.bounds.min[0] - pad, oy = f.bounds.min[1] - pad, oz = f.bounds.min[2] - pad;
  const nx = Math.max(2, Math.ceil((f.bounds.max[0] - f.bounds.min[0] + 2 * pad) / h) + 1);
  const ny = Math.max(2, Math.ceil((f.bounds.max[1] - f.bounds.min[1] + 2 * pad) / h) + 1);
  const nz = Math.max(2, Math.ceil((f.bounds.max[2] - f.bounds.min[2] + 2 * pad) / h) + 1);

  const layerSize = nx * ny;
  let cur = new Float32Array(layerSize);
  let next = new Float32Array(layerSize);
  const idx = new Int32Array(2 * layerSize).fill(-1);

  const positions: number[] = [];
  const materials: number[] = [];
  const indices: number[] = [];

  let evaluated = 0;
  let blocksSkipped = 0;
  let blocksSampled = 0;

  // Half-diagonal of a block measured in the plane of one layer.  The z extent
  // is not included: each layer is filled independently.
  const blockHalf = 0.5 * Math.hypot(block * h, block * h);

  const fillLayer = (dst: Float32Array, k: number) => {
    const z = oz + k * h;
    for (let bj = 0; bj < ny; bj += block) {
      const jEnd = Math.min(ny, bj + block);
      for (let bi = 0; bi < nx; bi += block) {
        const iEnd = Math.min(nx, bi + block);
        const cx = ox + (bi + (iEnd - bi) / 2) * h;
        const cy = oy + (bj + (jEnd - bj) / 2) * h;
        const v = sdf(cx, cy, z);
        evaluated++;
        if (Math.abs(v) / lip > blockHalf) {
          const fillValue = v > 0 ? BIG : -BIG;
          blocksSkipped++;
          for (let j = bj; j < jEnd; j++) dst.fill(fillValue, j * nx + bi, j * nx + iEnd);
          continue;
        }
        blocksSampled++;
        for (let j = bj; j < jEnd; j++) {
          const y = oy + j * h;
          const row = j * nx;
          for (let i = bi; i < iEnd; i++) {
            dst[row + i] = sdf(ox + i * h, y, z);
            evaluated++;
          }
        }
      }
    }
  };

  fillLayer(cur, 0);

  const corner = new Float32Array(8);
  const crossing = new Float32Array(3);

  for (let k = 0; k + 1 < nz; k++) {
    fillLayer(next, k + 1);
    const bufCur = (k & 1) * layerSize;
    const bufPrev = ((k + 1) & 1) * layerSize;
    idx.fill(-1, bufCur, bufCur + layerSize);

    for (let j = 0; j + 1 < ny; j++) {
      for (let i = 0; i + 1 < nx; i++) {
        const a = j * nx + i;
        corner[0] = cur[a];
        corner[1] = cur[a + 1];
        corner[2] = cur[a + nx];
        corner[3] = cur[a + nx + 1];
        corner[4] = next[a];
        corner[5] = next[a + 1];
        corner[6] = next[a + nx];
        corner[7] = next[a + nx + 1];

        let mask = 0;
        for (let c = 0; c < 8; c++) if (corner[c] < 0) mask |= 1 << c;
        if (mask === 0 || mask === 255) continue;

        crossing[0] = 0; crossing[1] = 0; crossing[2] = 0;
        let hits = 0;
        for (let e = 0; e < 12; e++) {
          const c0 = EDGES[e][0], c1 = EDGES[e][1];
          const in0 = (mask >> c0) & 1, in1 = (mask >> c1) & 1;
          if (in0 === in1) continue;
          const v0 = corner[c0], v1 = corner[c1];
          const t = v0 / (v0 - v1);
          crossing[0] += (c0 & 1) + t * ((c1 & 1) - (c0 & 1));
          crossing[1] += ((c0 >> 1) & 1) + t * (((c1 >> 1) & 1) - ((c0 >> 1) & 1));
          crossing[2] += ((c0 >> 2) & 1) + t * (((c1 >> 2) & 1) - ((c0 >> 2) & 1));
          hits++;
        }

        const px = ox + (i + crossing[0] / hits) * h;
        const py = oy + (j + crossing[1] / hits) * h;
        const pz = oz + (k + crossing[2] / hits) * h;

        const vi = positions.length / 3;
        positions.push(px, py, pz);
        materials.push(opts.material ? opts.material(px, py, pz) : 0);
        idx[bufCur + a] = vi;

        // One quad per sign-changing grid edge leaving this cell's low corner.
        // The four cells around that edge each own a vertex; three of them were
        // visited earlier, which is why the test needs i, j or k to be > 0.
        const inside0 = (mask & 1) !== 0;
        if (j > 0 && k > 0 && ((mask >> 1) & 1) !== (mask & 1)) {
          quad(indices,
            idx[bufCur + a], idx[bufCur + a - nx],
            idx[bufPrev + a - nx], idx[bufPrev + a], inside0);
        }
        if (i > 0 && k > 0 && ((mask >> 2) & 1) !== (mask & 1)) {
          quad(indices,
            idx[bufCur + a], idx[bufPrev + a],
            idx[bufPrev + a - 1], idx[bufCur + a - 1], inside0);
        }
        if (i > 0 && j > 0 && ((mask >> 4) & 1) !== (mask & 1)) {
          quad(indices,
            idx[bufCur + a], idx[bufCur + a - 1],
            idx[bufCur + a - 1 - nx], idx[bufCur + a - nx], inside0);
        }
      }
    }
    const swap = cur; cur = next; next = swap;
  }

  const nVerts = positions.length / 3;
  const pos = new Float32Array(positions);
  const nor = new Float32Array(nVerts * 3);
  const e = h * 0.5;
  for (let v = 0; v < nVerts; v++) {
    const x = pos[v * 3], y = pos[v * 3 + 1], z = pos[v * 3 + 2];
    let gx = sdf(x + e, y, z) - sdf(x - e, y, z);
    let gy = sdf(x, y + e, z) - sdf(x, y - e, z);
    let gz = sdf(x, y, z + e) - sdf(x, y, z - e);
    const L = Math.hypot(gx, gy, gz) || 1;
    nor[v * 3] = gx / L; nor[v * 3 + 1] = gy / L; nor[v * 3 + 2] = gz / L;
  }
  evaluated += nVerts * 6;

  return {
    positions: pos,
    normals: nor,
    materials: new Uint8Array(materials),
    indices: new Uint32Array(indices),
    stats: {
      dims: [nx, ny, nz],
      samples: nx * ny * nz,
      evaluated,
      blocksSkipped,
      blocksSampled,
      vertices: nVerts,
      triangles: indices.length / 3,
      ms: Date.now() - t0,
    },
  };
}

function quad(out: number[], a: number, b: number, c: number, d: number, flip: boolean) {
  if (a < 0 || b < 0 || c < 0 || d < 0) return;
  if (flip) out.push(a, b, c, a, c, d);
  else out.push(a, c, b, a, d, c);
}

/** Drop vertices no triangle references, and reindex. */
export function compact(mesh: MeshData): MeshData {
  const used = new Int32Array(mesh.positions.length / 3).fill(-1);
  for (let i = 0; i < mesh.indices.length; i++) used[mesh.indices[i]] = 0;
  let n = 0;
  for (let i = 0; i < used.length; i++) if (used[i] === 0) used[i] = n++;
  if (n === used.length) return mesh;
  const positions = new Float32Array(n * 3);
  const normals = new Float32Array(n * 3);
  const materials = new Uint8Array(n);
  for (let i = 0; i < used.length; i++) {
    const j = used[i];
    if (j < 0) continue;
    positions[j * 3] = mesh.positions[i * 3];
    positions[j * 3 + 1] = mesh.positions[i * 3 + 1];
    positions[j * 3 + 2] = mesh.positions[i * 3 + 2];
    normals[j * 3] = mesh.normals[i * 3];
    normals[j * 3 + 1] = mesh.normals[i * 3 + 1];
    normals[j * 3 + 2] = mesh.normals[i * 3 + 2];
    materials[j] = mesh.materials[i];
  }
  const indices = new Uint32Array(mesh.indices.length);
  for (let i = 0; i < mesh.indices.length; i++) indices[i] = used[mesh.indices[i]];
  return { ...mesh, positions, normals, materials, indices, stats: { ...mesh.stats, vertices: n } };
}
