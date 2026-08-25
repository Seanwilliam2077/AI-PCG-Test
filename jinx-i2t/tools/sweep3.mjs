/** Key against ambient: the p90/mean ratio is a lighting-contrast property that
 *  exposure cannot touch. Reference ratio is 74.9/36.75 = 2.04. */
import { execFileSync } from 'node:child_process';
let best = null;
for (const key of [0.35, 0.5, 0.65, 0.8])
  for (const amb of [2.0, 3.2, 4.4, 5.6])
    for (const exp of [1.0, 1.15]) {
      execFileSync('node', ['tools/render.mjs', '--out', 'out/_s3', '--size', '250x450',
        '--yaw', '0,90,180', '--key', String(key), '--amb', String(amb), '--exp', String(exp)],
        { encoding: 'utf8' });
      const s = JSON.parse(execFileSync('python', ['tools/lstats.py', 'out/_s3'], { encoding: 'utf8' }));
      const cost = Math.abs(s.mean - 37) + Math.abs(s.p10 - 14) + Math.abs(s.p90 - 75);
      console.log(`key=${key} amb=${amb} exp=${exp}  mean ${s.mean.toFixed(1)} p10 ${s.p10.toFixed(1)} p90 ${s.p90.toFixed(1)} ratio ${(s.p90/s.mean).toFixed(2)} spread ${s.spread.toFixed(2)}  cost ${cost.toFixed(2)}`);
      if (!best || cost < best.cost) best = { key, amb, exp, ...s, cost };
    }
console.log('\nbest:', JSON.stringify(best));
