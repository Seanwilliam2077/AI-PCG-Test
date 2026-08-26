/**
 * Jinx's pistol, assembled. The program is the asset; the mesh is what it compiles to.
 *
 * Five modules build the geometry -- `parts/barrel`, `parts/lattice`, `parts/rail`,
 * `parts/frameparts`, `parts/grip` -- against the datum in `parts/datum.ts` and the
 * contract frozen in `docs/CONTRACT.md` before any of them existed. This file does only
 * the things that need to see all of them at once: the hierarchy, the joints, the
 * sockets, and the runtime record.
 *
 * Following img2threejs's own hard-surface demo (the Talon knife), the parts are traced
 * profiles put through Lathe and Extrude rather than primitives stacked in a tree, and
 * the finish is a material set rather than a shader trick. One Talon technique is
 * deliberately absent: it projects de-lit plates of the real object through an inverted
 * image-to-world mapping, and says a procedural substitute is "the single biggest
 * fidelity failure". Those would be the artist's pixels. This project does not
 * redistribute them or anything derived from them pixel-wise, so the finish here is
 * generated from the contract's measured CIE Lab values instead, and `parts/finish.ts`
 * states what that costs.
 *
 * On the joints below: the contract describes both of them as "verified geometrically",
 * with interpenetration checked over sampled poses. Its own audit (§11.1) found that
 * claim to be the one fabrication in the document -- a mesh computation reported against
 * a model the same document said did not exist. The axes, pivots and limits are carried
 * through here as DECLARED intent. What establishes them is `tools/check_contract.py`,
 * which tests every pivot against the part it belongs to, and it runs on this output.
 */
import * as THREE from 'three';

import { buildBarrel } from './parts/barrel.js';
import { buildFrameParts } from './parts/frameparts.js';
import { buildGrip } from './parts/grip.js';
import { buildLatticeCollar } from './parts/lattice.js';
import { applyTransformEdits, type ZapperEdits } from './handles.js';
import { buildMaterials, graffitiTexture } from './parts/finish.js';
import { buildRail } from './parts/rail.js';
import { A, D, L, PART, R, X_MUZZLE, xOf } from './parts/datum.js';

export interface ZapperOptions {
  wireframe?: boolean;
  /**
   * The contract's section 8 edit handles. Two of them reach the part builders and change
   * what is generated; the other six are applied to the assembled scene. See `handles.ts`
   * for why that distinction is reported rather than smoothed over.
   */
  edits?: ZapperEdits;
}

interface JointSpec {
  readonly id: string;
  readonly child: string;
  readonly axis: readonly [number, number, number];
  readonly pivot: readonly [number, number, number];
  readonly rangeDeg: readonly [number, number];
  readonly restDeg: number;
  readonly confidence: number;
  readonly note: string;
}

/** Contract §7, the two shipped joints. Pivots are in model space, metres. */
const JOINTS: readonly JointSpec[] = [
  {
    id: 'frame.hammer',
    child: PART.hammerSpur,
    axis: [0, 0, 1],
    pivot: [xOf(0.92), 0.6 * R, 0],
    rangeDeg: [-55, 20],
    restDeg: 32,
    confidence: 0.45,
    note: 'a piece lying in the sagittal plane can only swing about Z. The audit (D-20) '
        + 'found the declared low half of this range drives the spur into the receiver '
        + 'unless the receiver carries a slot, which frame.surfaceFeatures.count = 0 '
        + 'denies; the range is carried unchanged and the check is left to say so.',
  },
  {
    id: 'frame.trigger',
    child: PART.trigger,
    axis: [0, 0, 1],
    pivot: [xOf(0.824), -1.40 * R, 0],
    rangeDeg: [0, 14],
    restDeg: 0,
    confidence: 0.75,
    note: '14 degrees comes from a 0.75 R blade swinging in a 0.9 R opening. The blade is '
        + '8 x 15 px in the only view that resolves it, so a travel figure read off the '
        + 'image would be invention.',
  },
];

/** Contract §7, the three attachment frames. Not articulation. */
const SOCKETS: readonly { id: string; pos: readonly [number, number, number];
                          rot: readonly [number, number, number]; note: string }[] = [
  { id: 'socket.muzzle', pos: [X_MUZZLE, 0, 0], rot: [0, 0, 0],
    note: 'on the bore axis at u = 0, +X forward' },
  { id: 'socket.rail', pos: [xOf(0.101), 0.62 * D, 0], rot: [0, 0, 0],
    note: "on the mount block's top face, +Y up" },
  { id: 'socket.grip', pos: [xOf(0.90), -1.9 * R, 0], rot: [0, 0, -1.87],
    note: "the grip's mid-front, aligned to the grip axis (107 deg from the bore)" },
];

/**
 * Give every mesh the component id the harness's material tools key on.
 *
 * `render.mjs --flat 1 --keep <id>` flattens every material except the named ones, which
 * is how a figure showing one generated texture can be published without the extracted
 * ones travelling beside it. That lookup reads `userData.sculptComponent.id`, so a mesh
 * without one silently becomes unkeepable.
 */
function tagComponents(root: THREE.Object3D): number {
  let tagged = 0;
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const ud = m.userData as { sculptComponent?: { id: string } };
    if (!ud.sculptComponent) {
      ud.sculptComponent = { id: m.name };
      tagged += 1;
    }
  });
  return tagged;
}

export function createZapperModel(options: ZapperOptions = {}): THREE.Group {
  const root = new THREE.Group();
  root.name = PART.root;

  const materials = buildMaterials();
  if (options.wireframe) {
    for (const m of Object.values(materials)) {
      (m as THREE.MeshStandardMaterial).wireframe = true;
    }
  }

  const edits = options.edits ?? {};
  const barrel = buildBarrel(edits['muzzle.collar.rings']);
  const lattice = buildLatticeCollar(edits['lattice.opening.count']);
  const rail = buildRail();
  const frame = buildFrameParts();
  const grip = buildGrip();

  // The lattice is authored in model space and named as a child of the barrel in the
  // contract's tree, but it is added as a sibling here: Box3.setFromObject unions a
  // child into its parent, and `barrel.lattice-collar` is the widest thing on the object
  // (`gun.maxWidth.isLatticeCollar`), so parenting it would inflate every barrel AABB
  // the acceptance tool reads. The tree relation is a statement about the assembly, not
  // about which Object3D holds which -- the same reasoning `parts/barrel.ts` applies to
  // the bore inside the liner.
  root.add(barrel, lattice, rail, frame, grip);

  // The graffiti was the one surface feature nothing was calling. `parts/finish.ts`
  // generates it -- marks in the measured magenta and teal, at the measured count and
  // size distribution, allocated across axial bands by an ink budget rather than by
  // sampling positions and hoping the coverage follows -- but each geometry module
  // builds its own materials from the same contract rows, so the overlay had no owner.
  // Composing it is the assembly's job, and this is the assembly.
  //
  // It goes on as an alpha-blended second material on a cloned mesh rather than into
  // each base map: the [MAT] rows check `material.color`, and compositing marks into a
  // base colour would move the very numbers they check. A decal layer leaves the base
  // material's bytes exactly as measured.
  const graffiti = new THREE.MeshStandardMaterial({
    map: graffitiTexture(1024),
    transparent: true,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    roughness: 0.55,
    metalness: 0.0,
  });
  graffiti.name = 'graffiti-decal';
  let decals = 0;
  for (const host of [PART.tubeFore, PART.tubeAft, PART.midBand, PART.lattice]) {
    const src = barrel.getObjectByName(host) ?? lattice.getObjectByName(host);
    const m = src as THREE.Mesh;
    if (!m || !m.isMesh || !m.geometry.getAttribute('uv')) continue;
    const decal = new THREE.Mesh(m.geometry, graffiti);
    decal.name = `${host}.graffiti`;
    decal.position.copy(m.position);
    decal.rotation.copy(m.rotation);
    decal.scale.copy(m.scale).multiplyScalar(1.0008);
    (decal.userData as { decalOf?: string }).decalOf = host;
    m.parent?.add(decal);
    decals += 1;
  }

  const nodes: Record<string, THREE.Object3D> = {};
  const meshes: Record<string, THREE.Mesh> = {};
  root.traverse((o) => {
    if (o.name) nodes[o.name] = o;
    const m = o as THREE.Mesh;
    if (m.isMesh && m.name) meshes[m.name] = m;
  });

  // Joints are pivot Groups inserted above their child, so rotating the Group rotates
  // the part about the contract's pivot rather than about the part's own centre -- the
  // defect that cost the companion character build a whole pass.
  const joints: Record<string, THREE.Object3D> = {};
  for (const j of JOINTS) {
    const child = nodes[j.child];
    if (!child) continue;
    const parent = child.parent ?? root;
    const pivot = new THREE.Group();
    pivot.name = `${j.id}__pivot`;
    pivot.position.set(j.pivot[0], j.pivot[1], j.pivot[2]);
    parent.add(pivot);
    child.position.sub(pivot.position);
    pivot.add(child);
    pivot.userData.joint = {
      id: j.id, axis: j.axis, rangeDeg: j.rangeDeg, restDeg: j.restDeg,
      confidence: j.confidence, note: j.note,
      basis: 'DECLARED in docs/CONTRACT.md §7; the geometric verification that section '
           + 'claims was fabricated (§11.1) and is re-established by tools/check_contract.py',
    };
    joints[j.id] = pivot;
    nodes[pivot.name] = pivot;
  }

  const sockets: Record<string, THREE.Object3D> = {};
  for (const s of SOCKETS) {
    const o = new THREE.Object3D();
    o.name = s.id;
    o.position.set(s.pos[0], s.pos[1], s.pos[2]);
    o.rotation.set(s.rot[0], s.rot[1], s.rot[2]);
    o.userData.socket = { id: s.id, note: s.note };
    root.add(o);
    sockets[s.id] = o;
    nodes[s.id] = o;
  }

  const tagged = tagComponents(root);

  let triangles = 0;
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh || !m.geometry) return;
    const g = m.geometry;
    triangles += (g.index ? g.index.count : g.getAttribute('position').count) / 3;
  });

  // Applied after assembly and after the sockets are placed, so a handle moves the parts
  // AND the sockets that ride on them. Applying before would leave a socket behind on a
  // part that has moved, which is the sort of thing that only shows up when something is
  // attached to it later.
  const editNotes = applyTransformEdits(root, edits);

  root.userData.sculptRuntime = { nodes, meshes, sockets, joints };
  root.userData.zapper = {
    contract: 'docs/CONTRACT.md, frozen before any geometry existed and audited in §11',
    datum: { A, D, L, R },
    counts: {
      meshes: Object.keys(meshes).length,
      triangles,
      joints: Object.keys(joints).length,
      sockets: Object.keys(sockets).length,
      componentsTagged: tagged,
      graffitiDecals: decals,
    },
    finish: 'generated from measured CIE Lab values; no reference pixel is sampled, '
          + 'which is the one Talon technique that does not transfer here',
    edits,
    editNotes,
  };
  return root;
}

/**
 * Put the renderer into the state the finish was balanced under.
 *
 * The companion character build spent a whole pass discovering that its harness was
 * discarding the calibrated tone mapping and rendering at linear 1.0, which put every
 * lightness statistic a stop and a half high. Setting it here, next to the values it
 * belongs with, is what stops that from being rediscovered.
 */
export function configureZapperRenderer(renderer: THREE.WebGLRenderer): void {
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
}

/**
 * A three-quarter key with a cool fill and a rim, plus the tone mapping the finish was
 * balanced under.
 *
 * A pistol is mostly brass and painted steel, and both are specular: with a single key
 * the rings read as flat rings and the tube reads as a flat tube. The rim is what makes
 * a cylinder legible as a cylinder, and the fill keeps the shadow side from clipping to
 * the ground the way it did on the companion build before its environment was made
 * camera-relative.
 */
export function createZapperLookDevLights(): THREE.Group {
  const lights = new THREE.Group();
  lights.name = 'zapper look-dev lights';

  const hemi = new THREE.HemisphereLight(0xc9d6e6, 0x2a2620, 0.55);
  lights.add(hemi);

  const key = new THREE.DirectionalLight(0xfff3e4, 2.1);
  key.position.set(-0.35, 0.72, 0.60);
  lights.add(key);

  const fill = new THREE.DirectionalLight(0xa8c2e8, 0.55);
  fill.position.set(0.55, 0.15, 0.45);
  lights.add(fill);

  const rim = new THREE.DirectionalLight(0xffe9c8, 1.15);
  rim.position.set(0.30, 0.45, -0.85);
  lights.add(rim);

  lights.userData.lightingFromPhoto = [
    { id: 'key', type: 'directional', direction: [-0.35, 0.72, 0.60],
      colorHex: '#FFF3E4', intensity: 2.1, note: 'upper front-left, camera-relative' },
    { id: 'fill', type: 'directional', direction: [0.55, 0.15, 0.45],
      colorHex: '#A8C2E8', intensity: 0.55 },
    { id: 'rim', type: 'directional', direction: [0.30, 0.45, -0.85],
      colorHex: '#FFE9C8', intensity: 1.15,
      note: 'a rim is what makes a cylinder read as a cylinder rather than a flat band' },
    { id: 'hemisphere', type: 'hemisphere', colorHex: '#C9D6E6',
      groundHex: '#2A2620', intensity: 0.55 },
    { id: 'tone-mapping', type: 'tonemap', mode: 'AgX', exposure: 1.0,
      note: 'AgX rather than ACES. The Talon demo enforces the same choice in its own '
          + 'material registry, because ACES desaturates saturated primaries toward '
          + 'orange -- and this object carries measured magenta and teal accents whose '
          + 'hue is exactly what the [MAT] rows check.' },
  ];
  return lights;
}

/**
 * A small procedural room, pre-filtered.
 *
 * Brass without an environment has nothing to reflect and renders as flat dead albedo.
 * The companion build measured that directly: adding an environment moved its p10
 * lightness from 2.1 to 17.6.
 */
export function createZapperEnvironment(renderer: THREE.WebGLRenderer): THREE.Texture {
  const scene = new THREE.Scene();
  const geo = new THREE.BoxGeometry(6, 4, 6);
  geo.deleteAttribute('uv');

  const room = new THREE.Mesh(
    geo,
    new THREE.MeshStandardMaterial({ side: THREE.BackSide, color: 0x4a5260, roughness: 1 }),
  );
  scene.add(room);

  const panel = (x: number, y: number, z: number, w: number, h: number, i: number) => {
    const p = new THREE.Mesh(
      new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: 0xffffff.valueOf() }),
    );
    (p.material as THREE.MeshBasicMaterial).color.setScalar(i);
    p.position.set(x, y, z);
    p.lookAt(0, 0, 0);
    scene.add(p);
  };
  panel(-2.0, 1.6, 1.8, 2.6, 1.4, 3.0);
  panel(2.2, 0.6, 1.2, 1.6, 1.0, 0.9);
  panel(0.6, 1.2, -2.2, 2.2, 1.2, 1.8);

  const pmrem = new THREE.PMREMGenerator(renderer);
  const target = pmrem.fromScene(scene, 0.04);
  pmrem.dispose();
  geo.dispose();
  return target.texture;
}
