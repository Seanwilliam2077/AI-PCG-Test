/**
 * scratch (part: head) -- tools/preview.ts with two additions the head needs:
 *
 *   --ppm 3000 --cx 0 --cy 1.59      explicit pixels-per-metre and view centre,
 *                                    so a face crop is at a known scale and can
 *                                    be laid beside ref/views/head_*.png;
 *   --matmap                         flat, unlit, one saturated colour per
 *                                    material, so a material band can be
 *                                    measured in millimetres instead of guessed
 *                                    at from a shaded render.
 *
 * It does not replace tools/preview.ts -- the scoreboard still reads that.
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { deflateSync, inflateSync } from 'node:zlib';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { SPEC } from '../src/spec.js';
import { EncodedLod, EncodedMesh } from '../src/mesh/format.js';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function arg(name: string, dflt?: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : dflt;
}
const has = (name: string) => process.argv.includes(`--${name}`);

const lodName = arg('lod', 'low')!;
const yaws = (arg('yaw', '0,90')!).split(',').map(Number);
const [W, H] = (arg('size', '600x700')!).split('x').map(Number);
const outDir = resolve(ROOT, arg('out', 'out/head_preview')!);
const MATMAP = has('matmap');

const genDir = resolve(ROOT, arg('gen', 'src/generated')!);
const mod = await import(pathToFileURL(`${genDir}/lod_${lodName}.ts`).href);
const lod: EncodedLod = mod[`LOD_${lodName.toUpperCase()}`];

const inflateB64 = (s: string, codec: string): Buffer => {
  const raw = Buffer.from(s, 'base64');
  return codec === 'deflate' ? inflateSync(raw) : raw;
};
const asArrayBuffer = (b: Buffer): ArrayBuffer =>
  b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;

interface Tri { verts: Float32Array; nors: Float32Array; idx: Uint32Array; matOf: (t: number) => string }

function decode(enc: EncodedMesh): Tri {
  const pq = new Uint16Array(asArrayBuffer(inflateB64(enc.position, enc.codec)));
  const nq = new Int8Array(asArrayBuffer(inflateB64(enc.normal, enc.codec)));
  const idx = new Uint32Array(asArrayBuffer(inflateB64(enc.index, enc.codec)));
  const n = enc.vertexCount;
  const { min, max } = enc.bounds;
  const span = [max[0] - min[0] || 1e-6, max[1] - min[1] || 1e-6, max[2] - min[2] || 1e-6];
  const verts = new Float32Array(n * 3);
  const nors = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < 3; k++) {
      verts[i * 3 + k] = min[k] + (pq[i * 3 + k] / 65535) * span[k];
      nors[i * 3 + k] = nq[i * 3 + k] / 127;
    }
  }
  const ranges = enc.groups.map((g) => ({ from: g.start / 3, to: (g.start + g.count) / 3, m: g.material }));
  const matOf = (t: number) => ranges.find((r) => t >= r.from && t < r.to)?.m ?? 'skin';
  return { verts, nors, idx, matOf };
}

const meshes = lod.meshes.filter((m) => m.triangleCount > 0).map(decode);
if (meshes.length === 0) throw new Error(`lod ${lodName} has no geometry`);

let lo = [Infinity, Infinity, Infinity];
let hi = [-Infinity, -Infinity, -Infinity];
for (const enc of lod.meshes) {
  if (enc.triangleCount === 0) continue;
  for (let k = 0; k < 3; k++) {
    lo[k] = Math.min(lo[k], enc.bounds.min[k]);
    hi[k] = Math.max(hi[k], enc.bounds.max[k]);
  }
}

const ppm = arg('ppm') ? Number(arg('ppm')) : 0;
const cx = arg('cx') ? Number(arg('cx')) : (lo[0] + hi[0]) / 2;
const cy = arg('cy') ? Number(arg('cy')) : (lo[1] + hi[1]) / 2;
const cz = arg('cz') ? Number(arg('cz')) : (lo[2] + hi[2]) / 2;
const centre = [cx, cy, cz];
const scale = ppm > 0 ? ppm : H / ((hi[1] - lo[1]) * 1.06);

const MATS = SPEC.materials as unknown as Record<string, { color: number[]; roughness?: number; metalness?: number }>;
const EXPOSURE = arg('exposure') ? Number(arg('exposure')) : 0.82;
const toLinear = (c: number) => Math.pow(Math.max(0, Math.min(1, c)), 2.2);
const AMBIENT = arg('ambient') ? Number(arg('ambient')) : 0.022;
const srgb = (v: number) => Math.round(255 * Math.pow(Math.max(0, Math.min(1, v * EXPOSURE)), 1 / 2.2));

/** Flat, maximally separated colours for --matmap.  Nothing is near-neutral, so
 *  a band can be segmented by exact RGB rather than by hue guessing. */
const IDCOL: Record<string, [number, number, number]> = {
  skin: [255, 220, 180],
  lip: [255, 0, 0],
  brow: [0, 0, 0],
  sclera: [255, 255, 255],
  eye: [0, 128, 255],
  pupil: [0, 255, 0],
  hair: [255, 0, 255],
  hairDark: [128, 0, 128],
  skinShade: [255, 160, 60],
};

const LIGHTS: [number[], number[], number][] = [
  [[-0.45, 0.72, 0.52], [1.0, 0.97, 0.92], 1.05],
  [[0.72, 0.10, 0.36], [0.55, 0.68, 0.85], 0.42],
  [[0.10, 0.30, -0.92], [0.70, 0.80, 1.0], 0.55],
];

function png(w: number, h: number, rgba: Uint8Array): Buffer {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0;
    Buffer.from(rgba.buffer, y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1);
  }
  const chunk = (type: string, data: Buffer) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body) >>> 0);
    return Buffer.concat([len, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 6 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf: Buffer): number {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

mkdirSync(outDir, { recursive: true });

for (const yawDeg of yaws) {
  const a = (yawDeg * Math.PI) / 180;
  const ca = Math.cos(a), sa = Math.sin(a);
  const rot = (x: number, y: number, z: number): [number, number, number] => {
    const dx = x - centre[0], dy = y - centre[1], dz = z - centre[2];
    return [ca * dx - sa * dz, dy, sa * dx + ca * dz];
  };

  const rgba = new Uint8Array(W * H * 4);
  const depth = new Float32Array(W * H).fill(-Infinity);

  for (const m of meshes) {
    const triCount = m.idx.length / 3;
    for (let t = 0; t < triCount; t++) {
      const i0 = m.idx[t * 3], i1 = m.idx[t * 3 + 1], i2 = m.idx[t * 3 + 2];
      const p: [number, number, number][] = [];
      const nrm: [number, number, number][] = [];
      for (const i of [i0, i1, i2]) {
        const v = rot(m.verts[i * 3], m.verts[i * 3 + 1], m.verts[i * 3 + 2]);
        p.push([W / 2 + v[0] * scale, H / 2 - v[1] * scale, v[2]]);
        const nx = m.nors[i * 3], ny = m.nors[i * 3 + 1], nz = m.nors[i * 3 + 2];
        nrm.push([ca * nx - sa * nz, ny, sa * nx + ca * nz]);
      }
      const area = (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1]);
      if (area === 0) continue;
      const minX = Math.max(0, Math.floor(Math.min(p[0][0], p[1][0], p[2][0])));
      const maxX = Math.min(W - 1, Math.ceil(Math.max(p[0][0], p[1][0], p[2][0])));
      const minY = Math.max(0, Math.floor(Math.min(p[0][1], p[1][1], p[2][1])));
      const maxY = Math.min(H - 1, Math.ceil(Math.max(p[0][1], p[1][1], p[2][1])));
      if (minX > maxX || minY > maxY) continue;

      const name = m.matOf(t);
      const spec = MATS[name];
      const raw = spec?.color ?? [0.8, 0.8, 0.8];
      const col = [toLinear(raw[0]), toLinear(raw[1]), toLinear(raw[2])];
      const rough = spec?.roughness ?? 0.7;
      const shin = 4 + 120 * (1 - rough) * (1 - rough);
      const ks = 0.42 * (1 - rough) + 0.05;
      const flat = IDCOL[name] ?? [128, 128, 128];

      for (let y = minY; y <= maxY; y++) {
        for (let x = minX; x <= maxX; x++) {
          const px = x + 0.5, py = y + 0.5;
          const w0 = ((p[1][0] - p[0][0]) * (py - p[0][1]) - (px - p[0][0]) * (p[1][1] - p[0][1])) / area;
          const w1 = ((px - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (py - p[0][1])) / area;
          const w2 = 1 - w0 - w1;
          if (w0 < 0 || w1 < 0 || w2 < 0) continue;
          const z = p[0][2] * w2 + p[1][2] * w1 + p[2][2] * w0;
          const o = y * W + x;
          if (z <= depth[o]) continue;
          depth[o] = z;
          if (MATMAP) {
            rgba[o * 4] = flat[0]; rgba[o * 4 + 1] = flat[1];
            rgba[o * 4 + 2] = flat[2]; rgba[o * 4 + 3] = 255;
            continue;
          }
          let nx = nrm[0][0] * w2 + nrm[1][0] * w1 + nrm[2][0] * w0;
          let ny = nrm[0][1] * w2 + nrm[1][1] * w1 + nrm[2][1] * w0;
          let nz = nrm[0][2] * w2 + nrm[1][2] * w1 + nrm[2][2] * w0;
          const nl = Math.hypot(nx, ny, nz) || 1;
          nx /= nl; ny /= nl; nz /= nl;
          let r = col[0] * AMBIENT, g = col[1] * AMBIENT * 1.06, b = col[2] * AMBIENT * 1.19;
          for (const [dir, lc, inten] of LIGHTS) {
            const dl = Math.hypot(dir[0], dir[1], dir[2]) || 1;
            const lx = dir[0] / dl, ly = dir[1] / dl, lz = dir[2] / dl;
            const d = Math.max(0, nx * lx + ny * ly + nz * lz);
            r += col[0] * lc[0] * d * inten;
            g += col[1] * lc[1] * d * inten;
            b += col[2] * lc[2] * d * inten;
            const hx = lx, hy = ly, hz = lz + 1;
            const hl = Math.hypot(hx, hy, hz) || 1;
            const sp = Math.pow(Math.max(0, (nx * hx + ny * hy + nz * hz) / hl), shin) * ks * inten;
            r += lc[0] * sp; g += lc[1] * sp; b += lc[2] * sp;
          }
          rgba[o * 4] = srgb(r); rgba[o * 4 + 1] = srgb(g); rgba[o * 4 + 2] = srgb(b); rgba[o * 4 + 3] = 255;
        }
      }
    }
  }

  const file = `${outDir}/${MATMAP ? 'mat' : 'shade'}_yaw${yawDeg}.png`;
  writeFileSync(file, png(W, H, rgba));
  console.log(
    `${file}  ${W}x${H}  ${scale.toFixed(1)} px/m  centre ${centre.map((v) => v.toFixed(4)).join(',')}`,
  );
}
