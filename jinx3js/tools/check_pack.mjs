import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const file = process.argv[2] ?? `${ROOT}/out/jinx.html`;
const body = readFileSync(file, 'utf8');
const page_html = `<!doctype html><html><head><meta charset="utf-8"></head><body>${body}</body></html>`;

const server = createServer((_req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(page_html);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const errs = [];
page.on('pageerror', (e) => errs.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
await page.waitForTimeout(9000);
const info = await page.evaluate(() => ({
  ready: !!window.__READY__,
  info: window.__INFO__ ?? null,
  err: window.__ERROR__ ?? null,
  canvases: document.querySelectorAll('canvas').length,
  thumb: (() => {
    const i = document.querySelector('#ref-thumb');
    return i ? { srcHead: (i.src || '').slice(0, 42), complete: i.complete, w: i.naturalWidth, h: i.naturalHeight } : 'none';
  })(),
  drew: (() => {
    const c = document.querySelector('canvas');
    return c ? `${c.width}x${c.height}` : 'none';
  })(),
}));
await page.screenshot({ path: `${ROOT}/out/pack_check.png` });
console.log(JSON.stringify(info, null, 2));
if (errs.length) console.log('ERRORS:\n' + errs.slice(0, 8).join('\n'));
await browser.close();
server.close();
