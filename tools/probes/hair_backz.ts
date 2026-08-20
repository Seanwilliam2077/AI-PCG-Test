/**
 * hair scratch: rearmost surface z of the assembled body, excluding the hair
 * braids, at a column of heights.  This is the target the braid centreline has
 * to hug so the side-view silhouette fuses instead of splitting.
 *
 *   npx tsx out/hair_backz.ts            # x = 0 and x = +-0.03
 */
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
execFileSync(process.execPath, ['--import', 'tsx', `${ROOT}/tools/merge_spec.ts`], { stdio: 'ignore' });

const { buildShells } = await import('../src/scene.js');
const shells = (await buildShells()) as { name: string; field: { sdf(x: number, y: number, z: number): number } }[];
const skip = new Set(['braids']);
const keep = shells.filter((s) => !skip.has(s.name));
console.log('shells:', keep.map((s) => s.name).join(' '));

/** Rearmost surface along -z at (x, y), scanning from far behind forward. */
function backZ(x: number, y: number): number | null {
  const f = (z: number) => Math.min(...keep.map((s) => s.field.sdf(x, y, z)));
  let prev = f(-0.40);
  for (let z = -0.40; z < 0.30; z += 0.0005) {
    const v = f(z);
    if (prev > 0 && v <= 0) return z;
    prev = v;
  }
  return null;
}

const xs = (process.argv[2] ?? '0,0.030,-0.030,0.060,-0.060').split(',').map(Number);
const fmt = (v: number | null) => (v === null ? '   --  ' : v.toFixed(4).padStart(7));
console.log('   y   ' + xs.map((x) => ('x=' + x).padStart(8)).join(''));
for (let y = 1.66; y >= 0.10; y -= 0.02) {
  console.log(y.toFixed(2) + '  ' + xs.map((x) => fmt(backZ(x, y))).join(' '));
}
