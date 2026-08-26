/**
 * The eight edit handles of CONTRACT.md section 8, as code.
 *
 * Section 8 opens by saying "the must-not list *is* the locality specification", and it
 * was written before any modelling. The build that followed shipped none of it: the
 * parts read frozen constants out of `datum.ts`, so there was nothing to perturb and the
 * locality claim could not be tested at all. This file is the missing half.
 *
 * Two kinds of handle, and the difference is not cosmetic:
 *
 *   - `lattice.opening.count` and `muzzle.collar.rings` are GENERATION parameters. They
 *     reach the part builders and change what gets built. This is the strong form -- the
 *     one Nova3D (arXiv 2607.22738) reports 18/18 locality on -- because the handle is a
 *     term in the code that produces the geometry.
 *   - the other six are SCOPED TRANSFORMS applied to named subtrees of the finished
 *     scene. This is the weak form. A stretch here scales a built cylinder rather than
 *     re-lofting it, which is exact for the plain tube section (section 8 H1 chose that
 *     section precisely because it is the only plain cylinder on the object) but would
 *     not be exact for anything with a profile. Reported as the weak form rather than
 *     folded in with the other two.
 *
 * Implementing section 8 also falsified one of its rows -- see H1 below. That row had
 * survived a 25-defect adversarial audit, because reading a constraint and satisfying a
 * constraint fail in different places.
 */
import * as THREE from 'three';

export interface ZapperEdits {
  /** H1, metres of additional barrel. */
  'barrel.length'?: number;
  /** H2, metres of radial offset on the tube's outer surface. */
  'barrel.tube.od'?: number;
  /** H3, degrees about Z at the guard's rear attach. */
  'grip.rake'?: number;
  /** H4, integer 12-20. A generation parameter. */
  'lattice.opening.count'?: number;
  /** H5, metres of additional rail, growing forward. */
  'rail.length'?: number;
  /** H6, integer 2-4. A generation parameter. */
  'muzzle.collar.rings'?: number;
  /** H7, degrees about Z. */
  'hammer.angle'?: number;
  /** H8, degrees about Z. */
  'trigger.angle'?: number;
}

export const HANDLE_KIND: Record<keyof ZapperEdits, 'generation' | 'transform'> = {
  'lattice.opening.count': 'generation',
  'muzzle.collar.rings': 'generation',
  'barrel.length': 'transform',
  'barrel.tube.od': 'transform',
  'grip.rake': 'transform',
  'rail.length': 'transform',
  'hammer.angle': 'transform',
  'trigger.angle': 'transform',
};

/** Anchor for H1: the rear face of the plain tube, which is the mid-band's front face. */
const H1_ANCHOR_X = 0.1103;
/** The plain tube's forward face, where the muzzle collar begins. */
const H1_TUBE_FORE_X = 0.1798;
/** Anchor for H5: the rail's breech end, where the fixed hook sits. */
const H5_ANCHOR_X = 0.0;
/** The rail bar's forward end. */
const H5_RAIL_FORE_X = 0.2167;
/** H3's pivot, DECLARED in section 8 at (u 0.815, -2.4 R, 0). */
const H3_PIVOT = new THREE.Vector3(-0.0024, -0.0624, 0);

function find(root: THREE.Object3D, name: string): THREE.Object3D | null {
  let hit: THREE.Object3D | null = null;
  root.traverse((o) => {
    if (!hit && o.name === name) hit = o;
  });
  return hit;
}

function collect(root: THREE.Object3D, names: string[]): THREE.Object3D[] {
  const want = new Set(names);
  const out: THREE.Object3D[] = [];
  root.traverse((o) => {
    if (o.name && want.has(o.name)) out.push(o);
  });
  return out;
}

/**
 * Apply a world-space matrix to every mesh under `node`, by baking it into geometry.
 *
 * Setting node.position/scale would be simpler, but a handle's scope is a set of NAMED
 * parts that are not always siblings, and several of them -- the rail bar and its studs
 * -- are siblings whose parent must not move. Baking keeps every node transform
 * untouched, so a part outside the scope cannot be dragged along by a shared ancestor,
 * which is the exact failure mode the locality test is looking for.
 */
function bakeWorld(node: THREE.Object3D, world: THREE.Matrix4): void {
  node.updateWorldMatrix(true, true);
  node.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh || !mesh.geometry) return;
    mesh.updateWorldMatrix(true, false);
    const toLocal = new THREE.Matrix4().copy(mesh.matrixWorld).invert();
    mesh.geometry = mesh.geometry.clone();
    const m = new THREE.Matrix4().multiplyMatrices(
      toLocal,
      new THREE.Matrix4().multiplyMatrices(world, mesh.matrixWorld),
    );
    mesh.geometry.applyMatrix4(m);
    mesh.geometry.computeBoundingBox();
    mesh.geometry.computeBoundingSphere();
  });
}

function translateParts(root: THREE.Object3D, names: string[], v: THREE.Vector3): void {
  const m = new THREE.Matrix4().makeTranslation(v.x, v.y, v.z);
  for (const n of collect(root, names)) bakeWorld(n, m);
}

/** Scale along X about `anchor`, so a part's rear face stays put and its front face moves. */
function stretchX(root: THREE.Object3D, names: string[], anchor: number, s: number): void {
  const m = new THREE.Matrix4()
    .makeTranslation(anchor, 0, 0)
    .multiply(new THREE.Matrix4().makeScale(s, 1, 1))
    .multiply(new THREE.Matrix4().makeTranslation(-anchor, 0, 0));
  for (const n of collect(root, names)) bakeWorld(n, m);
}

/**
 * Grow each part's radius by the SAME absolute amount, which is what section 8 H2 means
 * by "offset, not scale": a common scale factor would multiply the gap between the bore
 * and the tube wall, and that wall thickness is a real quantity the contract constrains.
 * Each part therefore gets its own factor, computed from its own present radius.
 */
function offsetRadial(root: THREE.Object3D, names: string[], dR: number): void {
  for (const n of collect(root, names)) {
    const box = new THREE.Box3().setFromObject(n);
    const r = Math.max(Math.abs(box.max.y), Math.abs(box.min.y));
    if (r < 1e-6) continue;
    const s = (r + dR) / r;
    bakeWorld(n, new THREE.Matrix4().makeScale(1, s, s));
  }
}

function rotateZ(
  root: THREE.Object3D, names: string[], pivot: THREE.Vector3, deg: number,
): void {
  const m = new THREE.Matrix4()
    .makeTranslation(pivot.x, pivot.y, pivot.z)
    .multiply(new THREE.Matrix4().makeRotationZ(THREE.MathUtils.degToRad(deg)))
    .multiply(new THREE.Matrix4().makeTranslation(-pivot.x, -pivot.y, -pivot.z));
  for (const n of collect(root, names)) bakeWorld(n, m);
}

const MUZZLE_RINGS = [
  'barrel.muzzle-collar.ring-fore',
  'barrel.muzzle-collar.ring-mid',
  'barrel.muzzle-collar.ring-aft',
];

/**
 * The six transform handles. The two generation handles are applied in
 * `createZapperModel` instead, because they change what is built rather than where it is.
 * Returns any notes worth carrying into the locality report.
 */
export function applyTransformEdits(model: THREE.Object3D, edits: ZapperEdits): string[] {
  const notes: string[] = [];

  const dL = edits['barrel.length'];
  if (dL) {
    // CONTRACT DEFECT, found by implementing this handle rather than by reading it.
    // Section 8 H1 lists `mid-band` under "move rigidly (+D along X)" AND fixes
    // `tube-fore`'s min.x. In the built object tube-fore spans 110.3..179.8 mm and
    // mid-band spans 98.0..110.3 mm: they share the plane at 110.3. Honouring both rows
    // opens a D-wide gap in the barrel, so they are not jointly satisfiable by any model.
    // The defect is in the contract, not in the build.
    //
    // Resolved by holding the anchor and NOT moving the mid-band, because the anchor is
    // load-bearing for the handle's whole purpose -- confining deformation to the one
    // plain cylinder -- whereas the mid-band's presence in the move list is not
    // referenced anywhere else in section 8. Recorded rather than silently chosen.
    notes.push(
      'H1: section 8 lists mid-band as moving while also fixing tube-fore min.x at the '
      + 'mid-band own front face (both at 110.3 mm). Not jointly satisfiable; mid-band '
      + 'held fixed and the contradiction reported.',
    );
    const span = H1_TUBE_FORE_X - H1_ANCHOR_X;
    stretchX(model, ['barrel.tube-fore', 'barrel.tube-fore.graffiti'],
      H1_ANCHOR_X, (span + dL) / span);
    const railSpan = H5_RAIL_FORE_X - H5_ANCHOR_X;
    stretchX(model, ['barrel.rail'], H5_ANCHOR_X, (railSpan + dL) / railSpan);
    translateParts(model,
      [...MUZZLE_RINGS, 'barrel.liner', 'barrel.bore', 'barrel.rail.stud.2'],
      new THREE.Vector3(dL, 0, 0));
  }

  const dR = edits['barrel.tube.od'];
  if (dR) {
    offsetRadial(model, [
      'barrel.tube-aft', 'barrel.tube-fore',
      'barrel.tube-aft.graffiti', 'barrel.tube-fore.graffiti',
      'barrel.mid-band', 'barrel.mid-band.graffiti',
      'barrel.lattice-collar', ...MUZZLE_RINGS,
    ], dR);
    translateParts(model, [
      'barrel.rail', 'barrel.rail.mount-block', 'barrel.rail.rear-hook',
      'barrel.rail.stud.0', 'barrel.rail.stud.1', 'barrel.rail.stud.2',
    ], new THREE.Vector3(0, dR / 2, 0));
  }

  const rake = edits['grip.rake'];
  if (rake) rotateZ(model, ['grip.body', 'grip.butt-cap'], H3_PIVOT, rake);

  const dRail = edits['rail.length'];
  if (dRail) {
    const railSpan = H5_RAIL_FORE_X - H5_ANCHOR_X;
    stretchX(model, ['barrel.rail'], H5_ANCHOR_X, (railSpan + dRail) / railSpan);
    translateParts(model, ['barrel.rail.stud.2'], new THREE.Vector3(dRail, 0, 0));
  }

  const joints: [keyof ZapperEdits, string][] = [
    ['hammer.angle', 'frame.hammer__pivot'],
    ['trigger.angle', 'frame.trigger__pivot'],
  ];
  for (const [key, pivot] of joints) {
    const a = edits[key];
    if (!a) continue;
    const node = find(model, pivot);
    // These two are real joints with real pivot nodes, so they rotate the node rather
    // than baking geometry. That is what a joint is for, and it is also the only way the
    // joint limits recorded in userData stay meaningful after an edit.
    if (node) node.rotation.z += THREE.MathUtils.degToRad(a as number);
    else notes.push(`${key}: pivot ${pivot} not found`);
  }

  return notes;
}
