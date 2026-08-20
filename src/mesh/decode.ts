/**
 * Browser-side inverse of `encode.ts`: base64 to a Three BufferGeometry.
 *
 * Runs without Buffer or fetch, so the viewer stays a single JS bundle.
 */
import { BufferAttribute, BufferGeometry } from 'three';
import { EncodedMesh } from './format.js';

function fromBase64(s: string): Uint8Array {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function inflate(bytes: Uint8Array): Promise<Uint8Array> {
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('deflate'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function unpack(s: string, codec: 'raw' | 'deflate'): Promise<Uint8Array> {
  const raw = fromBase64(s);
  return codec === 'deflate' ? inflate(raw) : raw;
}

/** Copy into a fresh buffer: atob output is not guaranteed to be aligned. */
function typed<T extends Uint16Array | Int8Array | Uint8Array | Uint32Array>(
  bytes: Uint8Array,
  Ctor: new (buf: ArrayBuffer) => T,
): T {
  const copy = new ArrayBuffer(bytes.byteLength);
  new Uint8Array(copy).set(bytes);
  return new Ctor(copy);
}

export async function decodeMesh(enc: EncodedMesh): Promise<BufferGeometry> {
  const [pb, nb, mb, ib] = await Promise.all([
    unpack(enc.position, enc.codec),
    unpack(enc.normal, enc.codec),
    unpack(enc.material, enc.codec),
    unpack(enc.index, enc.codec),
  ]);
  const q = typed(pb, Uint16Array);
  const nq = typed(nb, Int8Array);
  const mat = typed(mb, Uint8Array);
  const idx = typed(ib, Uint32Array);

  const n = enc.vertexCount;
  const { min, max } = enc.bounds;
  const span = [
    Math.max(1e-6, max[0] - min[0]),
    Math.max(1e-6, max[1] - min[1]),
    Math.max(1e-6, max[2] - min[2]),
  ];

  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = min[0] + (q[i * 3] / 65535) * span[0];
    pos[i * 3 + 1] = min[1] + (q[i * 3 + 1] / 65535) * span[1];
    pos[i * 3 + 2] = min[2] + (q[i * 3 + 2] / 65535) * span[2];
  }

  const nor = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const x = nq[i * 3] / 127, y = nq[i * 3 + 1] / 127, z = nq[i * 3 + 2] / 127;
    const L = Math.hypot(x, y, z) || 1;
    nor[i * 3] = x / L; nor[i * 3 + 1] = y / L; nor[i * 3 + 2] = z / L;
  }

  const geo = new BufferGeometry();
  geo.setAttribute('position', new BufferAttribute(pos, 3));
  geo.setAttribute('normal', new BufferAttribute(nor, 3));
  geo.setAttribute('matId', new BufferAttribute(Float32Array.from(mat), 1));
  geo.setIndex(new BufferAttribute(idx, 1));
  for (const g of enc.groups) geo.addGroup(g.start, g.count, enc.groups.indexOf(g));
  geo.computeBoundingSphere();
  return geo;
}
