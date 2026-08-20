/**
 * hair scratch: frontmost surface z of the head shell (skin only) up the brow
 * column, so the fringe can be laid ON the forehead instead of floating.
 */
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
execFileSync(process.execPath, ['--import', 'tsx', `${ROOT}/tools/merge_spec.ts`], { stdio: 'ignore' });

const { buildShells } = await import('../src/scene.js');
const shells = (await buildShells()) as { name: string; field: { sdf(x: number, y: number, z: number): number } }[];
const want = (process.argv[2] ?? 'head').split(',');
const keep = shells.filter((s) => want.includes(s.name));
console.log('shells:', keep.map((s) => s.name).join(' '));

function frontZ(x: number, y: number): number | null {
  const f = (z: number) => Math.min(...keep.map((s) => s.field.sdf(x, y, z)));
  let prev = f(0.30);
  for (let z = 0.30; z > -0.30; z -= 0.0005) {
    const v = f(z);
    if (prev > 0 && v <= 0) return z;
    prev = v;
  }
  return null;
}
function halfX(y: number, z: number): number | null {
  const f = (x: number) => Math.min(...keep.map((s) => s.field.sdf(x, y, z)));
  let prev = f(0.20);
  for (let x = 0.20; x > -0.20; x -= 0.0005) {
    const v = f(x);
    if (prev > 0 && v <= 0) return x;
    prev = v;
  }
  return null;
}

const xs = (process.argv[3] ?? '0,-0.03,-0.06,0.03,0.06').split(',').map(Number);
const fmt = (v: number | null) => (v === null ? '   --  ' : v.toFixed(4).padStart(7));
console.log('   y   ' + xs.map((x) => ('fz x=' + x).padStart(8)).join(' ') + '   halfX@z0');
for (let y = 1.73; y >= 1.42; y -= 0.01) {
  console.log(y.toFixed(2) + '  ' + xs.map((x) => fmt(frontZ(x, y))).join(' ') + '  ' + fmt(halfX(y, 0)));
}
