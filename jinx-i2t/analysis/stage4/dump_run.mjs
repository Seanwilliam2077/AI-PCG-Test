import http from 'node:http';
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { join, extname, resolve } from 'node:path';
import { chromium } from 'playwright';

const ROOT = resolve('C:/AI Pipeline Test/jinx-i2t');
const APP = join(ROOT, 'analysis/stage4/dumpapp');
const PUB = join(ROOT, 'public');
const TYPES = { '.js': 'text/javascript', '.html': 'text/html', '.png': 'image/png', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/index.html';
  let file = join(APP, p);
  if (!existsSync(file)) file = join(PUB, p);
  if (!existsSync(file)) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(5599, r));
const browser = await chromium.launch();
const page = await browser.newPage();
const errs = [];
page.on('pageerror', (e) => errs.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
await page.goto('http://127.0.0.1:5599/index.html');
await page.waitForFunction('window.__READY2__ === true', null, { timeout: 120000 });
const err = await page.evaluate('window.__DUMPERR__ || null');
if (err) { console.log('DUMP ERROR:', err.slice(0, 2000)); }
else {
  const manifest = await page.evaluate(`(() => { const d = window.__DUMP__;
    return { model: d.model, parts: d.parts, unnamedMeshes: d.unnamedMeshes, integralMeshes: d.integralMeshes,
             totalTriangles: d.totalTriangles, bbox: d.bbox }; })()`);
  writeFileSync(join(ROOT, 'analysis/stage4/raw/parts_manifest.json'), JSON.stringify(manifest, null, 1));
  console.log('parts:', manifest.parts.length, 'unnamed:', manifest.unnamedMeshes, 'triangles:', manifest.totalTriangles);
  console.log('bbox:', JSON.stringify(manifest.bbox));
  const meshes = await page.evaluate('window.__DUMP__.meshes');
  writeFileSync(join(ROOT, 'analysis/stage4/raw/meshes.json'), JSON.stringify({ meshes }));
  console.log('meshes.json written, meshes:', meshes.length);
}
if (errs.length) console.log('page errors:', errs.slice(0, 5));
await browser.close();
server.close();
