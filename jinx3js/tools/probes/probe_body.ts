/**
 * Scratch probe: root-find the body shell's surface along +X and +/-Z at a set
 * of heights, so a silhouette measurement can be attributed to the field rather
 * than to the mesher or the rasteriser.  Not part of the build.
 */
import { bodyPart } from '../src/parts/body.js';
import { SPEC, MAT, buildSkeleton, torsoHalfWidth } from '../src/spec.js';

const ctx = { spec: SPEC, skel: buildSkeleton(SPEC), mat: MAT };
const shells = bodyPart.build(ctx as never);
const f = shells[0].field;

function edge(dir: 'x' | 'z', y: number, sign: number, lo = 0.0, hi = 0.30): number {
  const at = (t: number) => (dir === 'x' ? f.sdf(sign * t, y, 0) : f.sdf(0, y, sign * t));
  if (at(lo) > 0) return NaN;
  let a = lo, b = hi;
  for (let i = 0; i < 60; i++) {
    const m = (a + b) / 2;
    if (at(m) < 0) a = m; else b = m;
  }
  return (a + b) / 2;
}

const ys = [1.42, 1.40, 1.38, 1.36, 1.342, 1.30, 1.26, 1.237, 1.209, 1.183, 1.15, 1.12, 1.078, 1.05, 1.016, 0.98, 0.94];
console.log('  y      fieldHalfW  probeX   dX      probeZ+  probeZ-  depth   fieldHalfD');
for (const y of ys) {
  const t = torsoHalfWidth(y, SPEC);
  const px = edge('x', y, +1);
  const zp = edge('z', y, +1);
  const zm = edge('z', y, -1);
  console.log(
    `${y.toFixed(3)}  ${t.x.toFixed(4)}      ${px.toFixed(4)}  ${(px - t.x).toFixed(4)}  ` +
    `${zp.toFixed(4)}   ${zm.toFixed(4)}   ${(zp + zm).toFixed(4)}  ${(2 * t.z).toFixed(4)}`,
  );
}
