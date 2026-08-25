/**
 * Build one pass and stop: generate, render six yaws, write a comparison sheet.
 *
 * Deliberately does NOT record the review. The pipeline requires an AI vision
 * score on the sheet before a pass is credited, and a script cannot supply that
 * honestly -- the sheet has to be looked at.
 *
 *   node tools/pass_build.mjs structural-pass
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SK = join(homedir(), '.claude', 'skills', 'img2threejs');
const SPEC = join(ROOT, 'object-sculpt-spec.json');
const pass = process.argv[2];
if (!pass) throw new Error('usage: node tools/pass_build.mjs <pass-id>');

const run = (cmd, args) =>
  execFileSync(cmd, args, { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });

try {
  run('python', [join(SK, 'forge/stage3_build/generate_threejs_factory.py'), SPEC,
                 '--out', 'src/createJinxModel.ts', '--pass-id', pass, '--force']);
} catch (e) {
  console.log('generate BLOCKED:', ((e.stderr || e.stdout || '') + '').trim().split('\n').pop());
  process.exit(1);
}
console.log(`generated ${readFileSync(join(ROOT, 'src/createJinxModel.ts'), 'utf8').split('\n').length} lines`);

const outDir = `out/${pass}`;
mkdirSync(join(ROOT, outDir), { recursive: true });
console.log(execFileSync('node', ['tools/render.mjs', '--out', outDir, '--size', '500x900'],
  { cwd: ROOT, encoding: 'utf8' }).split('\n').filter((l) => /triangles|yaw|BLANK/.test(l)).join('\n'));

let iou = 'n/a';
try {
  const diag = run('python', [join(SK, 'forge/stage4_review/diagnose_render.py'),
    '--reference', 'ref/views/clay_2.png', '--render', `${outDir}/render_yaw0.png`,
    '--spec', SPEC, '--pass-id', pass, '--in-place']);
  iou = /silhouette IoU ([0-9.]+)/.exec(diag)?.[1] ?? /"iou":\s*([0-9.]+)/.exec(diag)?.[1] ?? 'n/a';
} catch (e) {
  const out = (e.stdout || '') + (e.stderr || '');
  iou = /silhouette IoU ([0-9.]+)/.exec(out)?.[1] ?? 'n/a';
}
console.log('diagnose: silhouette IoU', iou);

execFileSync('python', ['tools/sheet.py', pass], { cwd: ROOT, stdio: 'inherit' });
console.log(`sheet: out/${pass}_sheet.png  -- look at it before recording the review`);
