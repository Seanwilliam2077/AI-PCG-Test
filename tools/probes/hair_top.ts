/** hair: what exactly is inside the mass shell at the very top of the head. */
import { hairPart } from '../src/parts/hair.js';
import { SPEC, MAT, buildSkeleton } from '../src/spec.js';

const shells = hairPart.build({ spec: SPEC, skel: buildSkeleton(), mat: MAT });
const mass = shells[0].field;

for (const y of [1.705, 1.712, 1.718, 1.722]) {
  const N = 160;
  const rows: string[] = [];
  let n = 0;
  for (let j = N; j >= 0; j--) {
    const z = -0.18 + (0.30 * j) / N;
    let line = '';
    let any = false;
    for (let i = 0; i <= N; i++) {
      const x = -0.16 + (0.28 * i) / N;
      const v = mass.sdf(x, y, z);
      if (v <= 0) { line += '#'; any = true; n++; } else if (v < 0.004) line += '.'; else line += ' ';
    }
    if (any) rows.push(`z ${z.toFixed(3)} |${line}|`);
  }
  console.log(`=== y ${y}   inside ${n} samples   x -0.16..0.12`);
  for (const r of rows) console.log(r);
}
