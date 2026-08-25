#!/usr/bin/env node
/**
 * Headless turnaround renderer.
 *
 *     node tools/render.mjs                          # 8 yaws, lod high, 900x1500
 *     node tools/render.mjs --lod low --size 600x1000
 *     node tools/render.mjs --yaw 0,45,90 --out out/views
 *     node tools/render.mjs --no-build               # reuse an existing dist/
 *     node tools/render.mjs --expose -0.5            # exposure trim, in stops
 *
 * It builds the app with Vite, serves `dist/` from an in-process static server
 * on an ephemeral port, and drives the page's shot mode (`?shot=1&...`) with
 * Playwright.  One page load, one WebGL context, N frames -- re-aiming through
 * `window.__VIEW__` instead of reloading, because spinning up a SwiftShader
 * context per view is by far the slowest part of the loop.
 *
 * A blank render is a silent killer for the review loop, so every frame is
 * measured in-page (opaque-pixel fraction plus a uniformity check) and anything
 * that looks empty is a hard failure, not a written file.
 *
 * Every frame also reports CIE L* over the alpha -- mean, p10, p90 -- because
 * that is the axis the scoreboard's colour term lives on.  The reference sheet
 * `ref/views/body_2.png` measures L mean 36.7, p10 12.3, p90 74.7; a full
 * character should land in the band printed at the end of the run.
 */
import { spawnSync } from 'node:child_process';
import { createReadStream, existsSync, mkdirSync, statSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import { dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium } from 'playwright';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

/* --------------------------------------------------------------------- args */

const argv = process.argv.slice(2);
function arg(name, dflt) {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : dflt;
}
const flag = (name) => argv.includes(`--${name}`);

/**
 * The reference turnaround has 6 panels whose yaws are not yet known --
 * `tools/compare.py` fits the mapping -- so shoot every 45 degrees by default
 * and let the fit pick.
 */
const DEFAULT_YAWS = [0, 45, 90, 135, 180, 225, 270, 315];

const yaws = (arg('yaw', DEFAULT_YAWS.join(',')))
  .split(',')
  .map((s) => Number(s.trim()))
  .filter((n) => Number.isFinite(n));
const lod = String(arg('lod', 'high')).toLowerCase();
const bg = String(arg('bg', 'transparent')).toLowerCase();
const exposeRaw = arg('expose', null);
const expose = exposeRaw === null ? null : Number(exposeRaw);
if (exposeRaw !== null && !Number.isFinite(expose)) {
  console.error(`[render] --expose wants a number of stops, got "${exposeRaw}"`);
  process.exit(2);
}
const outDir = resolve(ROOT, arg('out', 'out/views'));
const sizeRaw = String(arg('size', '900x1500'));
const sizeMatch = /^(\d+)\s*[xX*]\s*(\d+)$/.exec(sizeRaw.trim());
if (!sizeMatch) {
  console.error(`[render] --size must look like 900x1500, got "${sizeRaw}"`);
  process.exit(2);
}
const width = Number(sizeMatch[1]);
const height = Number(sizeMatch[2]);
if (yaws.length === 0) {
  console.error('[render] --yaw produced no usable angles');
  process.exit(2);
}

/* -------------------------------------------------------------------- build */

const dist = resolve(ROOT, 'dist');
const wantBuild = !flag('no-build') || !existsSync(join(dist, 'index.html'));
if (wantBuild) {
  const viteBin = resolve(ROOT, 'node_modules', 'vite', 'bin', 'vite.js');
  if (!existsSync(viteBin)) {
    console.error('[render] vite is not installed; run npm install');
    process.exit(2);
  }
  console.log('[render] vite build ...');
  const built = spawnSync(process.execPath, [viteBin, 'build'], { cwd: ROOT, stdio: 'inherit' });
  if (built.status !== 0) {
    console.error('[render] vite build failed');
    process.exit(built.status ?? 1);
  }
} else {
  console.log('[render] reusing existing dist/');
}
if (!existsSync(join(dist, 'index.html'))) {
  console.error('[render] dist/index.html is missing after build');
  process.exit(1);
}

/* ------------------------------------------------------------ static server */

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.map': 'application/json; charset=utf-8',
  '.woff2': 'font/woff2',
};

const server = http.createServer((req, res) => {
  let pathname = '/';
  try {
    pathname = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
  } catch {
    pathname = '/';
  }
  if (pathname === '/' || pathname.endsWith('/')) pathname += 'index.html';
  const file = resolve(dist, `.${pathname}`);
  // Never serve outside dist/.
  if (file !== dist && !file.startsWith(dist + sep)) {
    res.writeHead(403).end('forbidden');
    return;
  }
  if (!existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404).end('not found');
    return;
  }
  res.writeHead(200, {
    'content-type': MIME[extname(file).toLowerCase()] ?? 'application/octet-stream',
    'cache-control': 'no-store',
  });
  createReadStream(file).pipe(res);
});

await new Promise((ok, fail) => {
  server.on('error', fail);
  server.listen(0, '127.0.0.1', ok);
});
const port = server.address().port;
const origin = `http://127.0.0.1:${port}`;

/* ------------------------------------------------------------------ browser */

// Headless Chromium has no GPU here; force the ANGLE SwiftShader backend and
// explicitly allow WebGL on it (Chrome refuses by default since 119).
const browser = await chromium.launch({
  args: [
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--ignore-gpu-blocklist',
    '--disable-gpu-sandbox',
    '--disable-dev-shm-usage',
    '--hide-scrollbars',
    '--force-color-profile=srgb',
    '--force-device-scale-factor=1',
  ],
});

const failures = [];
const lStats = [];
let exitCode = 0;

/**
 * The band a full-character render should land in, measured off
 * `ref/views/body_2.png`.  Reported, never enforced: a partial bake legitimately
 * sits outside it, and failing the run would stop the review loop dead.
 */
const TARGET = { mean: [36, 38], p10: [12, 16], p90: [72, 78] };

try {
  const page = await browser.newPage({
    viewport: { width: Math.max(width, 320) + 40, height: Math.max(height, 240) + 40 },
    deviceScaleFactor: 1,
  });

  const consoleErrors = [];
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text());
  });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));

  const first = yaws[0];
  const url =
    `${origin}/?shot=1&yaw=${first}&lod=${encodeURIComponent(lod)}` +
    `&w=${width}&h=${height}&bg=${encodeURIComponent(bg)}` +
    (expose === null ? '' : `&expose=${expose}`);
  console.log(`[render] ${url}`);
  await page.goto(url, { waitUntil: 'load', timeout: 60_000 });

  await page.waitForFunction(() => window.__READY__ === true, null, { timeout: 120_000 });

  const err = await page.evaluate(() => window.__ERROR__ ?? null);
  if (err) throw new Error(`viewer failed to start:\n${err}`);

  const info = await page.evaluate(() => window.__INFO__ ?? null);
  if (!info) throw new Error('viewer did not publish window.__INFO__');
  if (info.lod !== info.requestedLod) {
    console.warn(
      `[render] lod "${info.requestedLod}" is not baked; rendering "${info.lod}" ` +
        `(available: ${info.lods.join(', ') || 'none'})`,
    );
  }
  console.log(
    `[render] lod ${info.lod} · ${info.triangles.toLocaleString('en-US')} tris · ` +
      `frame ${info.frustumHeight.toFixed(3)} m tall · centre y=${info.center[1].toFixed(3)} · ` +
      `exposure ${info.exposure.toFixed(3)}${info.exposeStops ? ` (${info.exposeStops > 0 ? '+' : ''}${info.exposeStops} stop trim)` : ''}`,
  );

  mkdirSync(outDir, { recursive: true });

  for (const yaw of yaws) {
    const shot = await page.evaluate((y) => {
      window.__VIEW__(y);
      const canvas = document.querySelector('canvas');
      if (!canvas) return { error: 'no canvas on the page' };
      const url = window.__SHOT__();

      // Measure the buffer we are about to write: a SwiftShader failure shows up
      // as a fully transparent or perfectly uniform image, never as an exception.
      const probe = document.createElement('canvas');
      probe.width = canvas.width;
      probe.height = canvas.height;
      const ctx = probe.getContext('2d', { willReadFrequently: true });
      ctx.clearRect(0, 0, probe.width, probe.height);
      ctx.drawImage(canvas, 0, 0);
      const data = ctx.getImageData(0, 0, probe.width, probe.height).data;

      // sRGB byte -> linear, memoised: the inner loop runs a few million times.
      const toLinear = new Float64Array(256);
      for (let v = 0; v < 256; v++) {
        const c = v / 255;
        toLinear[v] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      }
      const EPS = (6 / 29) ** 3;
      const K = 3 * (6 / 29) ** 2;

      const total = probe.width * probe.height;
      let opaque = 0;
      let lumSum = 0;
      let lSum = 0;
      const seen = new Set();
      // 0.1-L buckets: enough resolution for p10/p90 without sorting a million floats.
      const hist = new Int32Array(1001);
      let lCount = 0;

      for (let i = 0; i < data.length; i += 4) {
        const a = data[i + 3];
        if (a > 8) {
          opaque++;
          lumSum += 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
        }
        // CIE L* is measured over the solid interior only, so half-covered edge
        // pixels -- which are darkened by the transparent background -- do not
        // drag the distribution down.
        if (a > 128) {
          const Y =
            0.2126 * toLinear[data[i]] + 0.7152 * toLinear[data[i + 1]] + 0.0722 * toLinear[data[i + 2]];
          const f = Y > EPS ? Math.cbrt(Y) : Y / K + 4 / 29;
          const L = 116 * f - 16;
          lSum += L;
          lCount++;
          const b = L <= 0 ? 0 : L >= 100 ? 1000 : Math.round(L * 10);
          hist[b]++;
        }
        if (seen.size < 64) {
          seen.add(((data[i] >> 4) << 8) | ((data[i + 1] >> 4) << 4) | (data[i + 2] >> 4));
        }
      }

      const pct = (q) => {
        if (lCount === 0) return 0;
        const want = q * lCount;
        let run = 0;
        for (let b = 0; b <= 1000; b++) {
          run += hist[b];
          if (run >= want) return b / 10;
        }
        return 100;
      };

      return {
        url,
        width: canvas.width,
        height: canvas.height,
        opaqueFraction: opaque / total,
        meanLuma: opaque ? lumSum / opaque / 255 : 0,
        distinctColors: seen.size,
        lMean: lCount ? lSum / lCount : 0,
        lP10: pct(0.1),
        lP50: pct(0.5),
        lP90: pct(0.9),
      };
    }, yaw);

    const name = `render_yaw${yaw}.png`;
    const file = join(outDir, name);

    if (shot.error) {
      failures.push(`yaw ${yaw}: ${shot.error}`);
      continue;
    }
    if (shot.width !== width || shot.height !== height) {
      failures.push(`yaw ${yaw}: canvas is ${shot.width}x${shot.height}, expected ${width}x${height}`);
      continue;
    }

    const blank =
      shot.opaqueFraction < 0.005 ||
      shot.distinctColors < 3 ||
      (bg !== 'transparent' && shot.meanLuma < 0.005);
    if (blank) {
      failures.push(
        `yaw ${yaw}: blank render (opaque ${(shot.opaqueFraction * 100).toFixed(2)}%, ` +
          `${shot.distinctColors} distinct colours) -- WebGL almost certainly failed`,
      );
      continue;
    }

    const b64 = shot.url.slice(shot.url.indexOf(',') + 1);
    const buf = Buffer.from(b64, 'base64');
    writeFileSync(file, buf);

    console.log(
      `  ${name.padEnd(20)} ${String(shot.width).padStart(4)}x${String(shot.height).padEnd(5)} ` +
        `${(buf.length / 1024).toFixed(0).padStart(5)} kB  ` +
        `opaque ${(shot.opaqueFraction * 100).toFixed(2).padStart(6)}%  ` +
        `L mean ${shot.lMean.toFixed(1).padStart(5)}  ` +
        `p10 ${shot.lP10.toFixed(1).padStart(5)}  ` +
        `p50 ${shot.lP50.toFixed(1).padStart(5)}  ` +
        `p90 ${shot.lP90.toFixed(1).padStart(5)}`,
    );
    lStats.push(shot);
  }
} catch (e) {
  failures.push(e instanceof Error ? e.message : String(e));
} finally {
  await browser.close().catch(() => {});
  await new Promise((ok) => server.close(ok));
}

if (failures.length) {
  console.error(`\n[render] ${failures.length} failure(s):`);
  for (const f of failures) console.error(`  - ${f}`);
  exitCode = 1;
} else {
  console.log(`\n[render] wrote ${yaws.length} view(s) to ${outDir}`);
}

if (lStats.length) {
  const avg = (k) => lStats.reduce((a, s) => a + s[k], 0) / lStats.length;
  const mean = avg('lMean');
  const p10 = avg('lP10');
  const p90 = avg('lP90');
  const band = (v, [lo, hi]) => (v >= lo && v <= hi ? 'in band' : v < lo ? 'BELOW band' : 'ABOVE band');
  console.log(
    `[render] CIE L* inside alpha, averaged over ${lStats.length} view(s): ` +
      `mean ${mean.toFixed(1)} (${band(mean, TARGET.mean)}), ` +
      `p10 ${p10.toFixed(1)} (${band(p10, TARGET.p10)}), ` +
      `p90 ${p90.toFixed(1)} (${band(p90, TARGET.p90)})`,
  );
  console.log(
    `[render] reference ref/views/body_2.png measures mean 36.7, p10 12.3, p90 74.7 · ` +
      `target mean ${TARGET.mean.join('-')}, p10 ${TARGET.p10.join('-')}, p90 ${TARGET.p90.join('-')}`,
  );
}

process.exit(exitCode);
