/**
 * Pull the reference sheets for the target ArtStation project into ref/.
 *
 * ArtStation sits behind Cloudflare, so plain HTTP clients get a JS challenge.
 * A real Chromium solves it, and page.request reuses the page's cookies, so the
 * asset downloads inherit the cleared challenge.
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PROJECT = process.argv[2] ?? 'https://www.artstation.com/projects/X1aWVw';

const browser = await chromium.launch();
const ctx = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  viewport: { width: 1600, height: 1200 },
});
const page = await ctx.newPage();
await page.goto(PROJECT, { waitUntil: 'domcontentloaded', timeout: 90000 });
await page.waitForTimeout(9000);
for (let i = 0; i < 8; i++) { await page.mouse.wheel(0, 1400); await page.waitForTimeout(700); }

const title = await page.title();
const urls = await page.evaluate(() => {
  const out = new Set();
  for (const img of document.querySelectorAll('img')) {
    const s = img.currentSrc || img.src || '';
    if (/artstation\.com\/p\/assets\/images/.test(s)) out.add(s);
  }
  for (const m of document.documentElement.innerHTML.matchAll(/https:\?\/\?\/cdn[ab]?\.artstation\.com\/p\/assets\/images\/[^"'\ )]+/g)) {
    out.add(m[0].replace(/\\//g, '/'));
  }
  return [...out];
});

// collapse size variants to one entry per asset, preferring the biggest served tier
const TIERS = ['original', '4k', 'large', 'medium', 'small', 'smaller', 'micro'];
const byAsset = new Map();
for (const u of urls) {
  const m = u.match(/\/images\/(\d{3}\/\d{3}\/\d{3})\/([a-z0-9_]+)\//i);
  if (!m) continue;
  const [, id, tier] = m;
  const rank = TIERS.indexOf(tier.toLowerCase());
  const cur = byAsset.get(id);
  if (!cur || rank < cur.rank) byAsset.set(id, { url: u, rank, tier });
}

mkdirSync(`${ROOT}/ref`, { recursive: true });
const manifest = { project: PROJECT, title, fetched: [] };
let n = 0;
for (const [id, { url, tier }] of [...byAsset.entries()].sort()) {
  for (const up of ['4k', 'large', tier]) {
    const tryUrl = url.replace(/\/(original|4k|large|medium|small|smaller|micro)\//, `/${up}/`);
    const r = await page.request.get(tryUrl, { timeout: 60000 });
    if (!r.ok()) continue;
    const buf = await r.body();
    if (buf.length < 20000) continue;
    const name = `sheet_${String(++n).padStart(2, '0')}.jpg`;
    writeFileSync(`${ROOT}/ref/${name}`, buf);
    manifest.fetched.push({ file: name, asset: id, tier: up, bytes: buf.length, url: tryUrl });
    console.log(name, up, (buf.length / 1024).toFixed(0) + 'kB', tryUrl);
    break;
  }
}
writeFileSync(`${ROOT}/ref/manifest.json`, JSON.stringify(manifest, null, 2));
console.log('title:', title, '| assets:', manifest.fetched.length);
await browser.close();
