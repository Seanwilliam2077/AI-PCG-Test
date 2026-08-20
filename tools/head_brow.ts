/** scratch (part: head) -- rebuild the head with the brow ridge switched off and
 *  report where the bare skin actually is along the brow line and the lip line,
 *  so browRidge.curve / lips can be authored against a measurement instead of
 *  against ellipse arithmetic that ignores 22 accumulated smoothUnion blends. */
import { SPEC, MAT, buildSkeleton } from '../src/spec.js';
import { headPart } from '../src/parts/head.js';

const bare = JSON.parse(JSON.stringify(SPEC));
bare.head.browRidge.ridgeRInner = 1e-5;
bare.head.browRidge.ridgeROuter = 1e-5;
bare.head.lips.rUpperEnd = 1e-5;
bare.head.lips.rUpperMid = 1e-5;
bare.head.lips.rLowerEnd = 1e-5;
bare.head.lips.rLowerMid = 1e-5;
bare.head.lips.rLine = 1e-5;
bare.head.mento.r = 1e-5;

const shells = headPart.build({ spec: bare, skel: buildSkeleton(bare), mat: MAT });
const head = shells.find((s) => s.name === 'head')!;

function frontZ(x: number, y: number): number | null {
  const z1 = 0.12, z0 = -0.02, n = 2800;
  for (let i = 0; i <= n; i++) {
    const z = z1 - (i / n) * (z1 - z0);
    if (head.field.sdf(x, y, z) < 0) return z;
  }
  return null;
}

const b = SPEC.head.browRidge as unknown as { curve: number[][] };
console.log('BARE SKIN along the brow line (x, y from browRidge.curve):');
for (const p of b.curve) {
  const z = frontZ(p[0], p[1]);
  console.log(`  x ${p[0].toFixed(4)}  y ${p[1].toFixed(4)}  authored z ${p[2].toFixed(4)}  actual ${z?.toFixed(4)}`);
}

console.log('\nBARE SKIN across the mouth (y = 1.5252, the lip seam):');
for (const x of [0, 0.004, 0.008, 0.012, 0.0158, 0.019]) {
  console.log(`  x ${x.toFixed(4)}  z ${frontZ(x, 1.5252)?.toFixed(4)}`);
}
console.log('\nBARE SKIN down the midline through the mouth:');
for (let y = 1.536; y >= 1.508; y -= 0.002) {
  console.log(`  y ${y.toFixed(4)}  z ${frontZ(0, y)?.toFixed(4)}`);
}
