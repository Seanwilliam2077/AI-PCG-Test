/**
 * top: probe the `top` (and `choker`, and `body`) shells without rendering.
 *
 *   npx tsx out/top_probe.ts silh      # front-view silhouette half-width per y
 *   npx tsx out/top_probe.ts topedge   # highest cloth y per x (the neckline)
 *   npx tsx out/top_probe.ts vsbody    # how far the top stands outside the body
 */
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
execFileSync(process.execPath, ['--import', 'tsx', `${ROOT}/tools/merge_spec.ts`], { stdio: 'ignore' });

const { buildShells } = await import('../src/scene.js');
const shells = await buildShells();
const byName = (n: string) => shells.find((s: { name: string }) => s.name === n);
const top = byName('top')!.field;
const choker = byName('choker')?.field;
const body = byName('body')!.field;

const inside = (f: { sdf: (x: number, y: number, z: number) => number }, x: number, y: number, z: number) => f.sdf(x, y, z) <= 0;

/** Front-view silhouette half-extent on a given side, scanning all z. */
function silhouette(f: typeof top, y: number, side: 1 | -1): number | null {
  let best: number | null = null;
  for (let z = -0.16; z <= 0.18; z += 0.002) {
    for (let x = 0.16; x > 0; x -= 0.0005) {
      if (inside(f, side * x, y, z)) { if (best === null || x > best) best = x; break; }
    }
  }
  return best;
}

/** Highest y where the cloth exists on the column x (scanning all z). */
function topEdge(f: typeof top, x: number, y0 = 1.20, y1 = 1.50): number | null {
  for (let y = y1; y >= y0; y -= 0.0005) {
    for (let z = -0.16; z <= 0.18; z += 0.004) {
      if (inside(f, x, y, z)) return y;
    }
  }
  return null;
}

const mode = process.argv[2] ?? 'silh';

if (mode === 'silh') {
  console.log('   y     topR      topL   | bodyR   bodyL');
  for (let y = 1.22; y <= 1.45001; y += 0.01) {
    const tr = silhouette(top, y, -1), tl = silhouette(top, y, 1);
    const br = silhouette(body, y, -1), bl = silhouette(body, y, 1);
    const s = (v: number | null) => (v === null ? '  --  ' : v.toFixed(4));
    console.log(`${y.toFixed(3)}  ${s(tr)}  ${s(tl)}  | ${s(br)}  ${s(bl)}`);
  }
} else if (mode === 'topedge') {
  console.log('   x     topY(cloth)  topY(choker)');
  for (let x = -0.10; x <= 0.1001; x += 0.005) {
    const a = topEdge(top, x);
    const b = choker ? topEdge(choker, x, 1.38, 1.55) : null;
    console.log(`${x.toFixed(3)}  ${a === null ? ' --' : a.toFixed(4)}      ${b === null ? ' --' : b.toFixed(4)}`);
  }
} else if (mode === 'vsbody') {
  // front z of top vs front z of body up the centre column, and at x = ±0.05
  const frontZ = (f: typeof top, x: number, y: number) => {
    for (let z = 0.20; z > -0.20; z -= 0.0005) if (inside(f, x, y, z)) return z;
    return null;
  };
  console.log('   y    x      topZ     bodyZ    proud');
  for (const x of [0, 0.03, 0.05, -0.03, -0.05]) {
    for (let y = 1.24; y <= 1.44001; y += 0.02) {
      const a = frontZ(top, x, y), b = frontZ(body, x, y);
      const p = a !== null && b !== null ? (a - b) * 1000 : NaN;
      console.log(`${y.toFixed(3)} ${x.toFixed(2)}  ${a === null ? '  --  ' : a.toFixed(4)}  ${b === null ? '  --  ' : b.toFixed(4)}  ${Number.isNaN(p) ? '' : p.toFixed(1) + 'mm'}`);
    }
    console.log('');
  }
} else if (mode === 'lace') {
  // extent of the brass/canvas cluster: scan the whole shell for where the
  // material resolver returns brass or canvas.
  const sh = byName('top')!;
  const matNames = Object.keys((await import('../src/spec.js')).MAT);
  let minx = 9, maxx = -9, miny = 9, maxy = -9;
  for (let y = 1.25; y <= 1.42; y += 0.001) {
    for (let x = -0.09; x <= 0.09; x += 0.001) {
      let z: number | null = null;
      for (let zz = 0.18; zz > -0.02; zz -= 0.001) if (inside(top, x, y, zz)) { z = zz; break; }
      if (z === null) continue;
      const m = matNames[sh.material(x, y, z)];
      if (m === 'brass' || m === 'canvas') {
        minx = Math.min(minx, x); maxx = Math.max(maxx, x);
        miny = Math.min(miny, y); maxy = Math.max(maxy, y);
      }
    }
  }
  console.log(`lace cluster x ${minx.toFixed(4)}..${maxx.toFixed(4)}  y ${miny.toFixed(4)}..${maxy.toFixed(4)}`);
}
