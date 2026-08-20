/** hair: what the crown blade alone measures, section by section and lofted. */
import { ellipsoid, smoothUnion } from '../src/sdf/ops.js';
import { rotateAbout } from '../src/sdf/solids.js';
import { Field } from '../src/sdf/types.js';

function crownSection(y: number, cx: number, cz: number, a: number, b: number, th: number, ry: number) {
  const t = (th * Math.PI) / 180;
  const phi = Math.atan2(-Math.cos(t), -Math.sin(t));
  return rotateAbout(ellipsoid([cx, y, cz], [a, ry, b]), [0, 1, 0], phi, [cx, y, cz]);
}

const AX: [string, number, number][] = [
  ['X  ', 1, 0], ['Z  ', 0, 1], ['45 ', 0.70711, -0.70711], ['315', 0.70711, 0.70711],
];

const CROWN_ROWS: number[][] = [
  [1.5750, -0.004, -0.043, 0.0940, 0.0870, 43, 0.032],
  [1.6000, -0.009, -0.042, 0.1187, 0.0968, 42, 0.030],
  [1.6200, -0.012, -0.041, 0.1198, 0.0958, 43, 0.026],
  [1.6400, -0.015, -0.039, 0.1173, 0.0897, 41, 0.026],
  [1.6600, -0.018, -0.035, 0.1135, 0.0805, 34, 0.024],
  [1.6800, -0.022, -0.030, 0.1046, 0.0660, 29, 0.021],
  [1.6960, -0.029, -0.024, 0.0930, 0.0440, 29, 0.014],
  [1.7060, -0.038, -0.018, 0.0740, 0.0270, 26, 0.009],
  [1.7120, -0.047, -0.013, 0.0470, 0.0160, 23, 0.006],
  [1.7155, -0.054, -0.009, 0.0230, 0.0090, 21, 0.004],
];

const blade = smoothUnion(0.010, ...CROWN_ROWS.map(
  ([y, cx, cz, a, b, th, ry]) => crownSection(y, cx, cz, a, b, th, ry)));

function measure(f: Field, y: number) {
  const N = 300;
  const pts: [number, number][] = [];
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      const x = -0.22 + (0.44 * i) / N, z = -0.28 + (0.46 * j) / N;
      if (f.sdf(x, y, z) <= 0) pts.push([x, z]);
    }
  }
  if (!pts.length) return `${y.toFixed(3)}  empty`;
  let s = `${y.toFixed(3)} `;
  for (const [nm, dx, dz] of AX) {
    let lo = Infinity, hi = -Infinity;
    for (const [x, z] of pts) { const v = dx * x + dz * z; if (v < lo) lo = v; if (v > hi) hi = v; }
    s += ` w${nm} ${(hi - lo).toFixed(4)}`;
  }
  return s;
}

for (let y = 1.60; y <= 1.725; y += 0.01) console.log(measure(blade, y));
