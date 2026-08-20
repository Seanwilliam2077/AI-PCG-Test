/**
 * Fold the built viewer into one self-contained HTML file.
 *
 *     node tools/pack.mjs                     # build, then write out/jinx.html
 *     node tools/pack.mjs --no-build --out out/jinx.html
 *
 * The character already ships as code -- the meshes are base64 inside the
 * bundle -- so the only thing standing between `dist/` and a single file is the
 * script tag, the stylesheet and the reference thumbnail. All three get inlined
 * here, which is also what lets the result be published as an artifact: a strict
 * CSP blocks every external request, so anything left behind as a URL would
 * simply not load.
 *
 * The output is a page *fragment*: a <title>, a <style> and a <script>, plus the
 * markup. It carries no <html>/<head>/<body> because the artifact host supplies
 * those. It opens fine in a browser regardless.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const arg = (n, d) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 ? argv[i + 1] : d;
};
const outFile = resolve(ROOT, arg('out', 'out/jinx.html'));

if (!argv.includes('--no-build')) {
  console.log('[pack] vite build');
  execFileSync('npx', ['vite', 'build'], { cwd: ROOT, stdio: 'inherit', shell: process.platform === 'win32' });
}

const dist = `${ROOT}/dist`;
if (!existsSync(`${dist}/index.html`)) throw new Error('dist/index.html missing -- run without --no-build');

const MIME = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
};

/** Every emitted asset, as a data URI, keyed by its dist-relative path. */
const assets = new Map();
const walk = (dir, prefix = '') => {
  for (const name of readdirSync(dir)) {
    const full = `${dir}/${name}`;
    const rel = prefix ? `${prefix}/${name}` : name;
    if (statSync(full).isDirectory()) { walk(full, rel); continue; }
    const ext = extname(name).toLowerCase();
    if (!MIME[ext]) continue;
    assets.set(rel, `data:${MIME[ext]};base64,${readFileSync(full).toString('base64')}`);
  }
};
if (existsSync(`${dist}/assets`)) walk(`${dist}/assets`, 'assets');

/**
 * The reference sheets belong to the artist and to Riot Games.  Using them
 * locally as a measurement target is one thing; embedding one in a page that
 * gets published is redistribution, so the packed build swaps the thumbnail for
 * a credit card and says so.
 */
const creditCard = () => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 440">
<rect width="320" height="440" fill="#191a1e"/>
<rect x="0.5" y="0.5" width="319" height="439" fill="none" stroke="#33353c"/>
<text x="160" y="186" fill="#8b8f99" font-family="ui-monospace,Menlo,monospace" font-size="13" text-anchor="middle">SOURCE REFERENCE</text>
<text x="160" y="214" fill="#c9cdd6" font-family="ui-sans-serif,system-ui,sans-serif" font-size="15" text-anchor="middle">Thibaut Granet</text>
<text x="160" y="236" fill="#c9cdd6" font-family="ui-sans-serif,system-ui,sans-serif" font-size="15" text-anchor="middle">ARCANE &#8212; Jinx</text>
<text x="160" y="266" fill="#7c8089" font-family="ui-sans-serif,system-ui,sans-serif" font-size="12.5" text-anchor="middle">&#169; Riot Games</text>
<text x="160" y="292" fill="#5f636c" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11.5" text-anchor="middle">turnaround not reproduced here</text>
</svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg, 'utf8').toString('base64')}`;
};
const CREDIT = creditCard();
const isReference = (name) => /(^|\/)(body|clay|head)_\d/.test(name);

const inlineAssets = (text) => {
  let out = text;
  // Vite also emits `new URL("name.png", import.meta.url)`, which resolves
  // against the module URL and so carries no directory prefix.
  // The trailing `.href` has to be swallowed too: Vite emits
  // `""+new URL(...).href`, and replacing only the URL leaves `"data:…".href`,
  // which is `undefined` and silently breaks the image.
  out = out.replace(/new URL\(\s*["']([^"']+)["']\s*,\s*import\.meta\.url\s*\)(\.href)?/g, (m, file) => {
    const hit = [...assets.entries()].find(([rel]) => rel.endsWith(`/${file}`) || rel === file);
    if (!hit) return m;
    return JSON.stringify(isReference(file) ? CREDIT : hit[1]);
  });
  for (const [rel, uri] of assets) {
    // Vite writes these as "/assets/x.png", "./assets/x.png" or "assets/x.png".
    out = out.split(`"/${rel}"`).join(`"${uri}"`)
      .split(`"./${rel}"`).join(`"${isReference(rel) ? CREDIT : uri}"`)
      .split(`"${rel}"`).join(`"${isReference(rel) ? CREDIT : uri}"`)
      .split(`'/${rel}'`).join(`'${isReference(rel) ? CREDIT : uri}'`)
      .split(`'${rel}'`).join(`'${isReference(rel) ? CREDIT : uri}'`);
  }
  return out;
};

const html = readFileSync(`${dist}/index.html`, 'utf8');

const scripts = [...html.matchAll(/<script[^>]*src="([^"]+)"[^>]*><\/script>/g)];
const styles = [...html.matchAll(/<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g)];

let css = '';
for (const [, href] of styles) {
  const p = `${dist}/${href.replace(/^\.?\//, '')}`;
  if (existsSync(p)) css += inlineAssets(readFileSync(p, 'utf8'));
}
// Vite inlines a small stylesheet straight into <head> rather than emitting a
// .css file.  Missing this leaves the packed page completely unstyled, which is
// how it first shipped: the viewport collapsed to a 150 px strip.
for (const [, block] of html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)) {
  css += `${inlineAssets(block)}
`;
}

let js = '';
for (const [, src] of scripts) {
  const p = `${dist}/${src.replace(/^\.?\//, '')}`;
  if (existsSync(p)) js += `${inlineAssets(readFileSync(p, 'utf8'))}\n`;
}
if (!js) throw new Error('[pack] no bundled script found in dist/index.html');

// Body markup only: strip the doctype/head/html wrapper and the tags we inlined.
let body = html;
const bodyMatch = /<body[^>]*>([\s\S]*?)<\/body>/i.exec(html);
if (bodyMatch) body = bodyMatch[1];
body = body
  .replace(/<script[^>]*src="[^"]+"[^>]*><\/script>/g, '')
  .replace(/<link[^>]*rel="stylesheet"[^>]*>/g, '')
  .replace(/<style[^>]*>[\s\S]*?<\/style>/g, '');
body = inlineAssets(body);

const title = (/<title>([\s\S]*?)<\/title>/i.exec(html)?.[1] ?? 'Jinx — TypeScript procedural surfaces').trim();

// <title> first: an artifact host only scans the head of the file for it, and
// the script below is megabytes long.
const packed =
  `<title>${title}</title>\n` +
  `<style>\n${css}\n</style>\n` +
  `${body}\n` +
  `<script type="module">\n${js}\n</script>\n`;

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, packed);

const mb = (n) => `${(n / 1024 / 1024).toFixed(2)} MB`;
console.log(`[pack] ${outFile}`);
console.log(`[pack] script ${mb(js.length)}  css ${(css.length / 1024).toFixed(0)} kB  assets ${assets.size} (${mb([...assets.values()].reduce((a, v) => a + v.length, 0))})`);
console.log(`[pack] total ${mb(packed.length)}${packed.length > 16 * 1024 * 1024 ? '  *** OVER THE 16 MB ARTIFACT LIMIT ***' : ''}`);
