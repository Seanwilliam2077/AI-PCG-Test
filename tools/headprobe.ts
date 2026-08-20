/**
 * Ray-probe the head shell: for a grid of (x, y) print the frontmost z where
 * the field crosses zero, so a silhouette or a socket depth can be checked
 * against the reference numbers without re-rendering.
 *
 *   npx tsx tools/headprobe.ts z 0.031        # z profile up the pupil column
 *   npx tsx tools/headprobe.ts x              # half-width up the head
 */
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
execFileSync(process.execPath, ['--import', 'tsx', `${ROOT}/tools/merge_spec.ts`], { stdio: 'ignore' });

const { buildShells } = await import('../src/scene.js');
const shell = (await buildShells()).find((s: {name:string}) => s.name === 'head')!;
const f = shell.field;

/** Frontmost surface along +z at (x, y). */
function frontZ(x: number, y: number): number | null {
  let prev = f.sdf(x, y, 0.12);
  for (let z = 0.12; z > -0.02; z -= 0.0004) {
    const v = f.sdf(x, y, z);
    if (prev > 0 && v <= 0) return z;
    prev = v;
  }
  return null;
}

/** Half-width along +x at (y, z). */
function halfX(y: number, z: number): number | null {
  let prev = f.sdf(0.12, y, z);
  for (let x = 0.12; x > 0; x -= 0.0004) {
    const v = f.sdf(x, y, z);
    if (prev > 0 && v <= 0) return x;
    prev = v;
  }
  return null;
}

const mode = process.argv[2] ?? 'z';
const fmt = (v: number | null) => (v === null ? '  --  ' : v.toFixed(4));

if (mode === 'z') {
  const x = Number(process.argv[3] ?? 0);
  console.log(`front z at x=${x}`);
  for (let y = 1.62; y >= 1.50; y -= 0.004) console.log(y.toFixed(3), fmt(frontZ(x, y)));
} else if (mode === 'x') {
  console.log('half width (z = 0 slice) and front z at x=0');
  for (let y = 1.68; y >= 1.47; y -= 0.006) {
    console.log(y.toFixed(3), 'halfX', fmt(halfX(y, -0.005)), ' frontZ', fmt(frontZ(0, y)));
  }
} else if (mode === 'sil') {
  // Front-view silhouette: the largest half-width over any z at that height.
  console.log('front-view silhouette half width');
  for (let y = 1.68; y >= 1.47; y -= 0.006) {
    let best = 0;
    for (let z = -0.075; z <= 0.065; z += 0.002) {
      const w = halfX(y, z);
      if (w !== null && w > best) best = w;
    }
    console.log(y.toFixed(3), best.toFixed(4));
  }
} else if (mode === 'eye') {
  const ys = [1.596, 1.592, 1.590, 1.588, 1.586, 1.584, 1.582, 1.580, 1.578, 1.576, 1.574, 1.570];
  console.log('front z across the eye, columns x = 0.016 .. 0.048');
  const xs = [0.016, 0.020, 0.024, 0.028, 0.031, 0.034, 0.038, 0.042, 0.046];
  console.log('   y  ', xs.map((v) => v.toFixed(3)).join(' '));
  for (const y of ys) console.log(y.toFixed(3), xs.map((x) => fmt(frontZ(x, y))).join(' '));
}
