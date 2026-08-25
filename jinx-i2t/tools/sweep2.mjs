/** Second-stage lighting calibration: exposure against ambient, on real materials. */
import { execFileSync } from 'node:child_process';
const T = { mean: 37, p10: 14, p90: 75 };
let best = null;
for (const exp of [0.80, 0.88, 0.95, 1.0])
  for (const amb of [1.0, 1.8, 2.6, 3.4]) {
    execFileSync('node', ['tools/render.mjs', '--out', 'out/_s2', '--size', '250x450',
      '--yaw', '0,90,180', '--exp', String(exp), '--amb', String(amb)], { encoding: 'utf8' });
    const s = JSON.parse(execFileSync('python', ['tools/lstats.py', 'out/_s2'], { encoding: 'utf8' }));
    const cost = Math.abs(s.mean - T.mean) + Math.abs(s.p10 - T.p10) + Math.abs(s.p90 - T.p90);
    console.log(`exp=${exp} amb=${amb}  mean ${s.mean.toFixed(1)} p10 ${s.p10.toFixed(1)} p90 ${s.p90.toFixed(1)} spread ${s.spread.toFixed(2)}  cost ${cost.toFixed(2)}`);
    if (!best || cost < best.cost) best = { exp, amb, ...s, cost };
  }
console.log('\nbest:', JSON.stringify(best));
