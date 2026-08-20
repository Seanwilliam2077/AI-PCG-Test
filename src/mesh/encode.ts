/**
 * Quantise and base64-encode a meshed shell into the shipping format.
 *
 * Triangles are sorted by material first, so each material becomes one
 * contiguous index range and the viewer can draw the mesh with real per-group
 * materials instead of decoding a palette inside a shader.
 */
import { deflateSync } from 'node:zlib';

import { MeshData } from './surfacenets.js';
import { EncodedGroup, EncodedMesh } from './format.js';

const b64 = (buf: ArrayBufferView): string =>
  deflateSync(
    Buffer.from(buf.buffer as ArrayBuffer, buf.byteOffset, buf.byteLength),
    { level: 9 },
  ).toString('base64');

export function encodeMesh(name: string, mesh: MeshData, materialNames: string[]): EncodedMesh {
  const n = mesh.positions.length / 3;
  const min: [number, number, number] = [Infinity, Infinity, Infinity];
  const max: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < 3; k++) {
      const v = mesh.positions[i * 3 + k];
      if (v < min[k]) min[k] = v;
      if (v > max[k]) max[k] = v;
    }
  }
  if (!Number.isFinite(min[0])) {
    min[0] = min[1] = min[2] = 0;
    max[0] = max[1] = max[2] = 0;
  }
  const span: [number, number, number] = [
    Math.max(1e-6, max[0] - min[0]),
    Math.max(1e-6, max[1] - min[1]),
    Math.max(1e-6, max[2] - min[2]),
  ];

  const pos = new Uint16Array(n * 3);
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < 3; k++) {
      const t = (mesh.positions[i * 3 + k] - min[k]) / span[k];
      pos[i * 3 + k] = Math.max(0, Math.min(65535, Math.round(t * 65535)));
    }
  }

  const nor = new Int8Array(n * 3);
  for (let i = 0; i < n * 3; i++) {
    nor[i] = Math.max(-127, Math.min(127, Math.round(mesh.normals[i] * 127)));
  }

  // Sort triangles by material so each becomes one draw range.
  const triCount = mesh.indices.length / 3;
  const triMat = new Uint8Array(triCount);
  for (let t = 0; t < triCount; t++) triMat[t] = mesh.materials[mesh.indices[t * 3]];
  const order = Array.from({ length: triCount }, (_, i) => i).sort((a, b) => triMat[a] - triMat[b]);

  const index = new Uint32Array(mesh.indices.length);
  const groups: EncodedGroup[] = [];
  let runStart = 0;
  let runMat = triCount > 0 ? triMat[order[0]] : 0;
  for (let t = 0; t < triCount; t++) {
    const src = order[t];
    index[t * 3] = mesh.indices[src * 3];
    index[t * 3 + 1] = mesh.indices[src * 3 + 1];
    index[t * 3 + 2] = mesh.indices[src * 3 + 2];
    if (triMat[src] !== runMat) {
      groups.push({
        name: `${name}:${materialNames[runMat] ?? runMat}`,
        material: materialNames[runMat] ?? String(runMat),
        start: runStart,
        count: t * 3 - runStart,
      });
      runStart = t * 3;
      runMat = triMat[src];
    }
  }
  if (triCount > 0) {
    groups.push({
      name: `${name}:${materialNames[runMat] ?? runMat}`,
      material: materialNames[runMat] ?? String(runMat),
      start: runStart,
      count: triCount * 3 - runStart,
    });
  }

  return {
    name,
    codec: 'deflate',
    bounds: { min, max },
    vertexCount: n,
    triangleCount: triCount,
    position: b64(pos),
    normal: b64(nor),
    material: b64(mesh.materials),
    index: b64(index),
    groups,
  };
}
