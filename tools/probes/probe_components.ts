/** Scratch: connected-component count of a baked shell. Not part of the build. */
import { inflateSync } from 'node:zlib';
import { pathToFileURL } from 'node:url';

const genDir = process.argv[2];
const lod = process.argv[3] ?? 'high';
const mod = await import(pathToFileURL(`${genDir}/lod_${lod}.ts`).href);
const enc = mod[`LOD_${lod.toUpperCase()}`].meshes.find((m: { name: string }) => m.name === 'body');
const buf = Buffer.from(enc.index, 'base64');
const raw = enc.codec === 'deflate' ? inflateSync(buf) : buf;
const idx = new Uint32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength));

const n = enc.vertexCount;
const parent = new Int32Array(n);
for (let i = 0; i < n; i++) parent[i] = i;
const find = (a: number): number => { while (parent[a] !== a) { parent[a] = parent[parent[a]]; a = parent[a]; } return a; };
const uni = (a: number, b: number) => { const ra = find(a), rb = find(b); if (ra !== rb) parent[ra] = rb; };
for (let t = 0; t < idx.length; t += 3) { uni(idx[t], idx[t + 1]); uni(idx[t + 1], idx[t + 2]); }

const size = new Map<number, number>();
for (let i = 0; i < n; i++) { const r = find(i); size.set(r, (size.get(r) ?? 0) + 1); }
const parts = [...size.values()].sort((a, b) => b - a);
console.log(`${genDir} ${lod}: ${enc.triangleCount} tris, ${n} verts, ${parts.length} components`);
console.log('  largest:', parts.slice(0, 8).join(', '));
