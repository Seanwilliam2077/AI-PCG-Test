/**
 * Calibrate the lighting envelope against the reference's six-yaw L statistics.
 *
 * The reference sheet is nearly shadowless: its per-view L means span 2.61 L.
 * A rig that falls off toward the back cannot match that no matter how the
 * exposure is set, so the search optimises mean, p10, p90 AND spread together.
 */
import { execFileSync } from 'node:child_process';

const trials = [];
for (const key of [0.7, 0.85, 1.0])
  for (const amb of [1.0, 1.6, 2.4])
    for (const env of [0.9, 1.6, 2.4])
      trials.push({ key, amb, env });

const target = { mean: 37, p10: 14, p90: 75, spread: 2.6 };
let best = null;
for (const t of trials) {
  const out = execFileSync('node', ['tools/render.mjs', '--out', 'out/_sweep', '--size', '200x360',
    '--yaw', '0,90,180', '--key', String(t.key), '--amb', String(t.amb), '--env', String(t.env)],
    { encoding: 'utf8' });
  const m = execFileSync('python', ['tools/lstats.py', 'out/_sweep'], { encoding: 'utf8' });
  const s = JSON.parse(m);
  // exposure is a free scalar afterwards, so score shape first: spread and the
  // p90/mean ratio are what exposure cannot fix.
  const cost = Math.abs(s.spread - target.spread) * 3
             + Math.abs(s.p90 / s.mean - target.p90 / target.mean) * 20
             + Math.abs(s.p10 / s.mean - target.p10 / target.mean) * 20;
  console.log(`key=${t.key} amb=${t.amb} env=${t.env}  mean ${s.mean.toFixed(1)} p10 ${s.p10.toFixed(1)} p90 ${s.p90.toFixed(1)} spread ${s.spread.toFixed(2)}  cost ${cost.toFixed(3)}`);
  if (!best || cost < best.cost) best = { ...t, ...s, cost };
}
console.log('\nbest shape:', JSON.stringify(best));
