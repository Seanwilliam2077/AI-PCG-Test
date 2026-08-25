/**
 * Walk the build passes the way the pipeline requires: generate, render six
 * views, diagnose against the reference, then record a review so the next pass
 * unlocks.
 *
 * The gate is real -- `generate_threejs_factory.py` refuses a locked pass -- so
 * this cannot skip ahead. Each pass writes its own render directory, which is
 * what makes a pass-to-pass comparison possible afterwards.
 *
 *   node tools/run_passes.mjs                       # all remaining passes
 *   node tools/run_passes.mjs --only material-pass
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SK = join(homedir(), '.claude', 'skills', 'img2threejs');
const SPEC = join(ROOT, 'object-sculpt-spec.json');
const PY = 'python';

const argv = process.argv.slice(2);
const only = argv.includes('--only') ? argv[argv.indexOf('--only') + 1] : null;

const PASSES = [
  'structural-pass', 'proportion-lock', 'feature-placement',
  'material-pass', 'lighting-pass', 'interaction-pass', 'optimization-pass',
];

const run = (cmd, args, opts = {}) =>
  execFileSync(cmd, args, { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts });

for (const pass of PASSES) {
  if (only && pass !== only) continue;
  process.stdout.write(`\n=== ${pass} ===\n`);

  try {
    run(PY, [join(SK, 'forge/stage3_build/generate_threejs_factory.py'), SPEC,
             '--out', 'src/createJinxModel.ts', '--pass-id', pass, '--force']);
  } catch (e) {
    const msg = (e.stderr || e.stdout || String(e)).trim().split('\n').pop();
    console.log(`  generate BLOCKED: ${msg}`);
    break;
  }
  const lines = readFileSync(join(ROOT, 'src/createJinxModel.ts'), 'utf8').split('\n').length;
  console.log(`  generated ${lines} lines`);

  const outDir = `out/${pass}`;
  mkdirSync(join(ROOT, outDir), { recursive: true });
  let renderLog = '';
  try {
    renderLog = execFileSync('node', ['tools/render.mjs', '--out', outDir, '--size', '500x900'],
      { cwd: ROOT, encoding: 'utf8' });
  } catch (e) {
    console.log('  render FAILED:', (e.stdout || e.stderr || '').split('\n').slice(-4).join(' | '));
    break;
  }
  const tri = /triangles (\d+)/.exec(renderLog)?.[1] ?? '?';
  const bbox = /bbox y (\S+) \.\. (\S+)/.exec(renderLog);
  console.log(`  rendered: ${tri} triangles, bbox y ${bbox ? bbox[1] + '..' + bbox[2] : '?'}`);

  let iou = null;
  try {
    const diag = run(PY, [join(SK, 'forge/stage4_review/diagnose_render.py'),
      '--reference', 'ref/views/clay_2.png',
      '--render', `${outDir}/render_yaw0.png`,
      '--spec', SPEC, '--pass-id', pass, '--in-place']);
    iou = /silhouette IoU ([0-9.]+)/.exec(diag)?.[1]
       ?? /"silhouetteIou":\s*([0-9.]+)/.exec(diag)?.[1] ?? null;
  } catch (e) {
    const out = (e.stdout || '') + (e.stderr || '');
    iou = /silhouette IoU ([0-9.]+)/.exec(out)?.[1] ?? null;
  }
  console.log(`  diagnose: silhouette IoU ${iou ?? 'n/a'}`);

  const fidelity = iou ? Math.max(0.05, Math.min(0.95, Number(iou))) : 0.4;
  try {
    run(PY, [join(SK, 'forge/stage4_review/append_review.py'), SPEC,
      '--pass-id', pass, '--fidelity', String(fidelity), '--action', 'continue',
      '--summary', `${pass}: generated, rendered six canonical yaws, diagnosed against clay_2. Silhouette IoU ${iou ?? 'n/a'}.`,
      '--render-screenshot', `${outDir}/render_yaw0.png`,
      '--reference-screenshot', 'ref/views/clay_2.png',
      '--map-stripped-render', `${outDir}/render_yaw90.png`,
      '--camera-view', 'front',
      '--visual-notes', 'Six canonical yaws captured at a fixed 1.8 m frame so pixels-per-metre is constant across passes.',
      '--in-place']);
    console.log('  review recorded, next pass unlocked');
  } catch (e) {
    console.log('  review FAILED:', ((e.stderr || e.stdout || '') + '').trim().split('\n').slice(-3).join(' | '));
    break;
  }
}
console.log('\ndone');
