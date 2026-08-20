/**
 * pants: probe the pants field along x at a set of heights, and report the
 * surface crossings (in metres) so the leg runs and the inseam gap can be read
 * without going through the mesher or the rasteriser.
 *
 *   npx tsx out/pants_probe.ts 0.50 0.58 0.62 0.66 0.71 0.75 0.80 0.86 0.90
 */
import { SPEC, buildSkeleton, MAT } from '../src/spec.js';
import { pantsPart } from '../src/parts/pants.js';
import { PartContext } from '../src/parts/types.js';

const ctx: PartContext = { spec: SPEC, skel: buildSkeleton(), mat: MAT };
const shells = pantsPart.build(ctx);
const f = shells[0].field;

const ys = process.argv.slice(2).map(Number).filter((v) => !Number.isNaN(v));
const heights = ys.length ? ys : [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05];

const N = 2400;
const X0 = -0.25, X1 = 0.25;

console.log('bounds', JSON.stringify(f.bounds));
console.log('y(m)     z=0 runs in x (metres)                              | z-extent at leg axis');
for (const y of heights) {
  // x runs at z = 0
  const runs: [number, number][] = [];
  let start: number | null = null;
  for (let i = 0; i <= N; i++) {
    const x = X0 + ((X1 - X0) * i) / N;
    const inside = f.sdf(x, y, 0) < 0;
    if (inside && start === null) start = x;
    if (!inside && start !== null) { runs.push([start, x]); start = null; }
  }
  if (start !== null) runs.push([start, X1]);

  // z extent through the +x leg axis
  const ax = 0.062;
  let z0 = NaN, z1 = NaN;
  for (let i = 0; i <= N; i++) {
    const z = -0.25 + (0.5 * i) / N;
    if (f.sdf(ax, y, z) < 0) { if (Number.isNaN(z0)) z0 = z; z1 = z; }
  }
  const txt = runs.map(([a, b]) => `[${a.toFixed(4)},${b.toFixed(4)}]w=${(b - a).toFixed(4)}`).join(' ');
  console.log(
    `${y.toFixed(3)}  ${txt.padEnd(52)} | z ${z0.toFixed(4)}..${z1.toFixed(4)} d=${(z1 - z0).toFixed(4)}`,
  );
}
