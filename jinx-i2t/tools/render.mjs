/**
 * Render the generated factory at the six canonical yaws, headlessly.
 *
 *   node tools/render.mjs --out out/blockout --size 620x1100
 *   node tools/render.mjs --yaw 0,90 --wire 1 --no-build
 *
 * Fails loudly on a blank frame rather than writing an empty PNG: a review loop
 * that scores a transparent image is worse than one that stops.
 */
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { extname, join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const arg = (n, d) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 ? argv[i + 1] : d;
};

const yaws = (arg('yaw', '0,45,90,180,270,315')).split(',').map(Number);
const [W, H] = arg('size', '620x1100').split('x').map(Number);
const outDir = resolve(ROOT, arg('out', 'out/views'));
const frame = arg('frame', '1.8');
const wire = arg('wire', '0');
const bg = arg('bg', 'transparent');

if (!argv.includes('--no-build')) {
  execFileSync('npx', ['vite', 'build'], { cwd: ROOT, stdio: 'inherit', shell: process.platform === 'win32' });
}

const dist = join(ROOT, 'dist');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.json': 'application/json' };
const server = createServer((req, res) => {
  const url = (req.url || '/').split('?')[0];
  const file = join(dist, url === '/' ? 'index.html' : url);
  if (!existsSync(file)) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'content-type': MIME[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: { width: W + 40, height: H + 40 } });
page.on('pageerror', (e) => console.error('[page]', String(e).slice(0, 300)));

const extraQuery = ['exp', 'key', 'amb', 'env', 'flat']
  .filter((k) => process.argv.includes(`--${k}`))
  .map((k) => `&${k}=${process.argv[process.argv.indexOf(`--${k}`) + 1]}`).join('');
const url = `http://127.0.0.1:${port}/?w=${W}&h=${H}&frame=${frame}&wire=${wire}&bg=${bg}&yaw=${yaws[0]}${extraQuery}`;
console.log('[render]', url);
await page.goto(url, { waitUntil: 'load' });
await page.waitForFunction(() => window.__READY__ === true || window.__ERROR__, null, { timeout: 90000 });

const err = await page.evaluate(() => window.__ERROR__);
if (err) { console.error('[render] factory threw:\n' + err); await browser.close(); server.close(); process.exit(1); }

const info = await page.evaluate(() => window.__INFO__);
console.log('[render] geometry triangles', info.triangles, '| draw calls', info.drawCalls, '| meshes', info.meshCount, '| bbox y', info.bbox.min[1].toFixed(3), '..', info.bbox.max[1].toFixed(3));
for (const l of info.lowest || []) console.log(`    low : ${l.name.padEnd(28)} y ${String(l.minY).padStart(8)} .. ${l.maxY}`);
if (process.argv.includes('--allmeshes')) {
  const fs = await import('node:fs');
  fs.writeFileSync('out/_meshes.json', JSON.stringify(info.widest ?? [], null, 1));
  console.log(`all meshes -> out/_meshes.json`);
}
if (process.argv.includes('--sockets')) {
  const fs = await import('node:fs');
  fs.writeFileSync('out/_sockets.json', JSON.stringify(info.sockets ?? {}, null, 1));
  console.log(`sockets probed: ${Object.keys(info.sockets ?? {}).length} -> out/_sockets.json`);
}
if (process.argv.includes('--tris')) {
  const fs = await import('node:fs');
  fs.writeFileSync('out/_tris.json', JSON.stringify(info.heaviest ?? [], null, 1));
  const tot = (info.heaviest || []).reduce((a, m) => a + m.tris, 0);
  console.log(`per-mesh triangles -> out/_tris.json  (${(info.heaviest||[]).length} meshes, ${tot} tris)`);
}
console.log('widest meshes:');
for (const w of info.widest || [])
  console.log(`    ${String(w.name).padEnd(30)} w ${String(w.w).padStart(6)}  x ${String(w.x0).padStart(7)} .. ${String(w.x1).padStart(6)}  y ${w.minY}..${w.maxY}`);
const mats = info.materials || {};
const names = Object.keys(mats).slice(0, 10);
console.log('materials sample:');
for (const n of names) console.log(`    ${n.padEnd(26)} ${mats[n]}`);
for (const l of info.tallest || []) console.log(`    high: ${l.name.padEnd(28)} y ${String(l.minY).padStart(8)} .. ${l.maxY}`);

mkdirSync(outDir, { recursive: true });
let bad = 0;
for (const yaw of yaws) {
  await page.evaluate((y) => window.__VIEW__(y), yaw);
  const shot = await page.evaluate(() => window.__SHOT__());
  const buf = Buffer.from(shot.split(',')[1], 'base64');
  const file = join(outDir, `render_yaw${yaw}.png`);
  writeFileSync(file, buf);
  const opaque = await page.evaluate((yy) => {
    const c = document.querySelector('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl');
    void g; void yy;
    const tmp = document.createElement('canvas');
    tmp.width = c.width; tmp.height = c.height;
    tmp.getContext('2d').drawImage(c, 0, 0);
    const d = tmp.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
    return n / (c.width * c.height);
  }, yaw);
  const flag = opaque < 0.02 ? '  *** BLANK ***' : '';
  if (opaque < 0.02) bad++;
  console.log(`  yaw ${String(yaw).padStart(3)}  ${(buf.length / 1024).toFixed(0)} kB  opaque ${(opaque * 100).toFixed(2)}%${flag}`);
}
await browser.close();
server.close();
if (bad) { console.error(`[render] ${bad} view(s) came out blank`); process.exit(1); }
console.log('[render] wrote', yaws.length, 'view(s) to', outDir);
