/**
 * hair: the head-and-hair cross-section at each height, measured the way the
 * six reference panels measure it.
 *
 * preview.ts projects with screen-x = cos(a)*x - sin(a)*z, so a panel's width
 * at height y is the support width of the solid along the (x, z) direction
 * (cos a, -sin a).  Only four of the six panels give distinct axes -- yaw 0
 * and 180 share X, yaw 90 and 270 share Z -- so a section is fully described
 * by its widths along X, Z, (1,-1)/sqrt2 (yaw 45) and (1,1)/sqrt2 (yaw 315),
 * which is one constraint more than an ellipse needs.  Printing all four next
 * to the reference is what turns "the crest is too small" into a number.
 *
 *   npx tsx out/hair_probe.ts 1.60:1.73:0.01
 */
import { hairPart } from '../src/parts/hair.js';
import { headPart } from '../src/parts/head.js';
import { Field } from '../src/sdf/types.js';
import { SPEC, MAT, buildSkeleton } from '../src/spec.js';

const rowsArg = process.argv[2] ?? '1.60:1.73:0.01';
const [ra, rb, rs] = rowsArg.split(':').map(Number);
const only = process.argv[3];

const ctx = { spec: SPEC, skel: buildSkeleton(), mat: MAT };
let shells = [...headPart.build(ctx), ...hairPart.build(ctx)];
if (only) shells = shells.filter((s) => only.split(',').includes(s.name));

// Reference widths, read off ref/views/clay_*.png with out/hair_crest.py.
// [y, wX, wZ, w45, w315]; wX is the mean of yaw 0 and 180, wZ of 90 and 270
// (each pair shares a projection axis, so an orthographic render cannot tell
// them apart and the mean is the only fittable target).
const REF: Record<string, number[]> = {
  '1.600': [0.2135, 0.2196, 0.2344, 0.1904],
  '1.620': [0.2165, 0.2174, 0.2344, 0.1850],
  '1.640': [0.2053, 0.2124, 0.2344, 0.1796],
  '1.660': [0.1819, 0.2103, 0.2248, 0.1662],
  '1.680': [0.1514, 0.1953, 0.2015, 0.1394],
  '1.700': [0.1134, 0.1581, 0.1686, 0.0724],
  '1.710': [0.0632, 0.1265, 0.1096, 0.0362],
  '1.715': [0.0310, 0.1050, 0.0192, 0.0188],
  '1.720': [0.0168, 0.0065, 0.0069, 0.0107],
};

const AX: [string, number, number][] = [
  ['X  ', 1, 0], ['Z  ', 0, 1], ['45 ', 0.70711, -0.70711], ['315', 0.70711, 0.70711],
];

const N = 260;
const X0 = -0.20, X1 = 0.20, Z0 = -0.26, Z1 = 0.18;

function solidAt(y: number, fields: Field[]): [number, number][] {
  const pts: [number, number][] = [];
  for (let i = 0; i <= N; i++) {
    const x = X0 + ((X1 - X0) * i) / N;
    for (let j = 0; j <= N; j++) {
      const z = Z0 + ((Z1 - Z0) * j) / N;
      for (const f of fields) {
        if (f.sdf(x, y, z) <= 0) { pts.push([x, z]); break; }
      }
    }
  }
  return pts;
}

const fields = shells.map((s) => s.field);
console.log(shells.map((s) => s.name).join(' + '));
console.log('    y  |      wX  (ref)  |      wZ  (ref)  |     w45  (ref)  |    w315  (ref)  |   cx      cz');
for (let y = ra; y <= rb + 1e-9; y += rs) {
  const pts = solidAt(y, fields);
  if (pts.length === 0) { console.log(`${y.toFixed(3)}  empty`); continue; }
  const ref = REF[y.toFixed(3)];
  let line = `${y.toFixed(3)}  `;
  let cx = 0, cz = 0;
  for (let k = 0; k < AX.length; k++) {
    const [, dx, dz] = AX[k];
    let lo = Infinity, hi = -Infinity;
    for (const [x, z] of pts) {
      const s = dx * x + dz * z;
      if (s < lo) lo = s;
      if (s > hi) hi = s;
    }
    if (k === 0) cx = (lo + hi) / 2;
    if (k === 1) cz = (lo + hi) / 2;
    const r = ref ? ref[k] : NaN;
    const d = ref ? (hi - lo) - r : NaN;
    line += `| ${(hi - lo).toFixed(4)} ${ref ? `(${r.toFixed(3)}) ${d >= 0 ? '+' : ''}${(d * 1000).toFixed(0).padStart(3)}` : '  -        '} `;
  }
  line += `|  ${cx.toFixed(4)} ${cz.toFixed(4)}`;
  console.log(line);
}
