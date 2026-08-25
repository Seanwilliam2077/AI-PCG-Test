/**
 * Fold spec/parts/*.json onto spec/jinx.json and write spec/resolved.json.
 *
 * Several part authors work in the same checkout at once.  If they all edited
 * spec/jinx.json they would clobber each other, so each owns one fragment under
 * spec/parts/ holding only their own top-level key, and this merges them.
 * spec/resolved.json is generated -- never edit it, and never edit another
 * author's fragment.
 */
import { mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

type Json = Record<string, unknown>;

const isPlainObject = (v: unknown): v is Json =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

/** Deep merge; arrays and scalars from the fragment replace the base outright. */
function merge(base: Json, over: Json): Json {
  const out: Json = { ...base };
  for (const [k, v] of Object.entries(over)) {
    out[k] = isPlainObject(v) && isPlainObject(out[k]) ? merge(out[k] as Json, v) : v;
  }
  return out;
}

const base = JSON.parse(readFileSync(`${ROOT}/spec/jinx.json`, 'utf8')) as Json;
mkdirSync(`${ROOT}/spec/parts`, { recursive: true });

const fragments = readdirSync(`${ROOT}/spec/parts`).filter((f) => f.endsWith('.json')).sort();
let resolved = base;
const applied: string[] = [];
for (const f of fragments) {
  try {
    const frag = JSON.parse(readFileSync(`${ROOT}/spec/parts/${f}`, 'utf8')) as Json;
    resolved = merge(resolved, frag);
    applied.push(f);
  } catch (err) {
    console.error(`[spec] fragment ${f} is not valid JSON, skipped: ${(err as Error).message}`);
  }
}

writeFileSync(`${ROOT}/spec/resolved.json`, `${JSON.stringify(resolved, null, 2)}\n`);
console.log(`[spec] resolved.json <- jinx.json${applied.length ? ` + ${applied.join(', ')}` : ''}`);
