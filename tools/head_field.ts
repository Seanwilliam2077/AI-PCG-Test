/** scratch (part: head) -- march the head shell's field along +z and report
 *  where the skin surface actually is, so socket depth and the visible eye
 *  aperture are measured rather than inferred from a shaded render.
 *  Runs in ~2 s, where a bake + render loop is ~40 s. */
import { SPEC, MAT, buildSkeleton } from '../src/spec.js';
import { headPart } from '../src/parts/head.js';

const shells = headPart.build({ spec: SPEC, skel: buildSkeleton(SPEC), mat: MAT });
const head = shells.find((s) => s.name === 'head')!;
const eyes = shells.find((s) => s.name === 'eyes')!;

/** frontmost z with f < 0 */
function frontZ(f: { sdf: (x: number, y: number, z: number) => number }, x: number, y: number): number | null {
  const z1 = 0.12, z0 = -0.02, n = 2800;
  for (let i = 0; i <= n; i++) {
    const z = z1 - (i / n) * (z1 - z0);
    if (f.sdf(x, y, z) < 0) return z;
  }
  return null;
}

const e = (SPEC.head as unknown as { eye: Record<string, number> }).eye;

/* --- visible globe: for each v, the u range where the globe beats the skin --- */
console.log('VISIBLE GLOBE (her left eye), u = lateral from eye axis, v = vertical');
console.log('   v(mm)   uMin    uMax   width(mm)   skinZ@u0');
let wmax = 0, vTop = 0, vBot = 0;
for (let vi = 10; vi >= -10; vi--) {
  const v = vi * 0.001;
  let umin = NaN, umax = NaN;
  for (let ui = -80; ui <= 80; ui++) {
    const u = ui * 0.00025;
    const s = frontZ(head.field, e.x + u, e.y + v);
    const g = frontZ(eyes.field, e.x + u, e.y + v);
    const vis = s !== null && g !== null && g > s + 0.0002;
    if (vis) { if (Number.isNaN(umin)) umin = u; umax = u; }
  }
  const s0 = frontZ(head.field, e.x, e.y + v);
  const w = Number.isNaN(umin) ? 0 : (umax - umin) * 1000;
  if (w > 0) { if (vTop === 0) vTop = v; vBot = v; }
  wmax = Math.max(wmax, w);
  console.log(
    `${(v * 1000).toFixed(0).padStart(6)}  ${Number.isNaN(umin) ? '  --  ' : (umin * 1000).toFixed(1).padStart(6)}` +
    `  ${Number.isNaN(umax) ? '  --  ' : (umax * 1000).toFixed(1).padStart(6)}` +
    `   ${w.toFixed(1).padStart(6)}      ${s0 === null ? 'none' : s0.toFixed(4)}`,
  );
}
console.log(`=> visible aperture ${wmax.toFixed(1)} x ${((vTop - vBot) * 1000).toFixed(1)} mm`
  + `  (reference 29.9 x 12.1)`);

/* --- how far the lid bulges past the brow, in profile --- */
console.log('\nPROFILE at x = eye axis: y -> skin z');
for (let y = 1.612; y >= 1.564; y -= 0.004) {
  const s = frontZ(head.field, e.x, y);
  console.log(`  ${y.toFixed(3)}  ${s === null ? 'none' : s.toFixed(4)}`);
}

/* --- midline profile: nose, lips, mento crease, chin --- */
console.log('\nPROFILE at midline: y -> skin z');
for (let y = 1.562; y >= 1.504; y -= 0.002) {
  const s = frontZ(head.field, 0, y);
  console.log(`  ${y.toFixed(3)}  ${s === null ? 'none' : s.toFixed(4)}`);
}
