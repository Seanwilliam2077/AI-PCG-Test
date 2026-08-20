/**
 * The part registry and the assembled shell list.
 *
 * Each part owns exactly one file under src/parts and appears here once. The
 * registry is fixed so several authors can work in parallel without touching a
 * shared file; a part that has nothing to contribute yet returns no shells and
 * simply does not appear in the bake.
 *
 * Parts are pulled in with **dynamic** imports, one try/catch each. That is not
 * a style choice: with static imports a module-level error in any one part --
 * a missing export, a typo at the top level -- takes down the bake for every
 * author at once, because the import is resolved before `buildShells` is ever
 * called and there is nothing to catch it. Two authors lost cycles to exactly
 * that during the first round. Now a broken part costs only its own shells.
 */
import { PartContext, PartModule, Shell } from './parts/types.js';
import { MAT, SPEC, Spec, buildSkeleton } from './spec.js';

/** Registry: part id to module loader. Order is cosmetic. */
const LOADERS: Record<string, () => Promise<Record<string, unknown>>> = {
  body: () => import('./parts/body.js'),
  head: () => import('./parts/head.js'),
  hair: () => import('./parts/hair.js'),
  tattoo: () => import('./parts/tattoo.js'),
  top: () => import('./parts/top.js'),
  choker: () => import('./parts/choker.js'),
  pants: () => import('./parts/pants.js'),
  sash: () => import('./parts/sash.js'),
  belts: () => import('./parts/belts.js'),
  gloves: () => import('./parts/gloves.js'),
  boots: () => import('./parts/boots.js'),
  zapper: () => import('./parts/zapper.js'),
};

export const PART_IDS = Object.keys(LOADERS);

export function makeContext(spec: Spec = SPEC): PartContext {
  return { spec, skel: buildSkeleton(spec), mat: MAT };
}

export interface BuildReport {
  shells: Shell[];
  /** Parts that failed, with why -- the bake prints these rather than dying. */
  failures: { part: string; stage: 'import' | 'build'; message: string }[];
}

export async function buildShellsDetailed(spec: Spec = SPEC, only?: Set<string>): Promise<BuildReport> {
  const ctx = makeContext(spec);
  const shells: Shell[] = [];
  const failures: BuildReport['failures'] = [];

  for (const [id, load] of Object.entries(LOADERS)) {
    if (only && !only.has(id)) continue;
    let mod: Record<string, unknown>;
    try {
      mod = await load();
    } catch (err) {
      failures.push({ part: id, stage: 'import', message: (err as Error).message });
      continue;
    }
    const part = (mod[`${id}Part`] ?? mod.default) as PartModule | undefined;
    if (!part || typeof part.build !== 'function') {
      failures.push({ part: id, stage: 'import', message: `no exported ${id}Part with a build()` });
      continue;
    }
    try {
      for (const s of part.build(ctx) ?? []) shells.push(s);
    } catch (err) {
      failures.push({ part: id, stage: 'build', message: (err as Error).message });
    }
  }
  return { shells, failures };
}

export async function buildShells(spec: Spec = SPEC): Promise<Shell[]> {
  return (await buildShellsDetailed(spec)).shells;
}
