/// <reference types="vite/client" />
/**
 * The viewer.
 *
 * Two jobs in one bundle:
 *
 *  1. An interactive gallery-detail page -- orbit, LOD switch, wireframe,
 *     turntable, canonical views.
 *  2. A deterministic offscreen renderer driven by query parameters, which is
 *     what `tools/render.mjs` and the review loop actually depend on:
 *
 *       ?shot=1&yaw=45&lod=low&w=600&h=1000&bg=transparent&expose=-0.5
 *
 *     In shot mode all chrome is hidden, the drawing buffer is exactly `w x h`
 *     at pixel ratio 1, one frame is rendered, and then `window.__READY__` goes
 *     true and `window.__SHOT__()` returns a PNG data URL.  The context is
 *     created with `preserveDrawingBuffer` so that read-back is legal.
 *
 * Geometry comes from `src/generated` -- base64 typed arrays compiled into the
 * bundle by `tools/bake.ts`, inflated by `src/mesh/decode.ts`.  Nothing is
 * fetched at runtime.
 */
import {
  AmbientLight,
  BufferGeometry,
  CanvasTexture,
  Color,
  DirectionalLight,
  Group,
  MathUtils,
  Mesh,
  NeutralToneMapping,
  Object3D,
  OrthographicCamera,
  PMREMGenerator,
  SRGBColorSpace,
  Scene,
  Vector3,
  WebGLRenderer,
} from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

import { decodeMesh } from '../mesh/decode.js';
import type { EncodedLod } from '../mesh/format.js';
import * as GENERATED from '../generated/index.js';
import { MaterialLibrary } from './materials.js';
import {
  CANONICAL_YAWS,
  Framing,
  applyAspect,
  applyCanonicalView,
  computeFraming,
  yawOf,
} from './camera.js';
import { buildControls, buildDetailPanel } from './ui.js';

declare global {
  interface Window {
    /** Set once the requested shot has been rendered. */
    __READY__?: boolean;
    /** PNG data URL of the current drawing buffer. */
    __SHOT__?: () => string;
    /** Re-aim at another yaw and render one frame, without a page reload. */
    __VIEW__?: (yawDeg: number) => void;
    /** What the page actually did, for the renderer's log line. */
    __INFO__?: {
      requestedLod: string;
      lod: string;
      lods: string[];
      triangles: number;
      width: number;
      height: number;
      background: string;
      exposure: number;
      exposeStops: number;
      frustumHeight: number;
      center: [number, number, number];
    };
    /** Set if start-up threw, so the renderer can fail loudly. */
    __ERROR__?: string;
  }
}

const VERSION = 'v1.5.1';

/**
 * Tone-mapping exposure that puts a full-character render inside the
 * reference's measured band (L mean 36-38, p10 12-16, p90 72-78).  See the rig
 * comment below.
 */
// Re-calibrated after spec.materials was re-authored from medians sampled off
// the reference sheet.  Those samples come from the artist's *render*, so they
// already carry some of its lighting; applying ours on top made everything
// about 5 L too dark, and this is the compensation.  Measured on the front
// view: mean 36.9 against the sheet's 36.7, p10 10.6 against 12.3.
const BASE_EXPOSURE = 0.60;

/** Weight of the procedural studio IBL against the directional rig. */
const ENV_INTENSITY = 0.9;
const LOD_ORDER = ['high', 'medium', 'low'] as const;

/* ------------------------------------------------------------------ options */

const params = new URLSearchParams(location.search);
const num = (k: string, dflt: number): number => {
  const v = Number(params.get(k));
  return Number.isFinite(v) && v > 0 ? v : dflt;
};

const SHOT = params.get('shot') === '1';
const REQUESTED_YAW = Number(params.get('yaw')) || 0;
const REQUESTED_LOD = (params.get('lod') ?? (SHOT ? 'high' : 'low')).toLowerCase();
const SHOT_W = Math.round(num('w', 900));
const SHOT_H = Math.round(num('h', 1500));
const BG = params.get('bg') === 'transparent' ? 'transparent' : 'dark';
/**
 * Exposure trim in stops, on top of `BASE_EXPOSURE`.  The rig below is
 * calibrated against the reference sheets, so this exists to *iterate*, not to
 * be left set: a render taken at a different `expose` is not comparable with the
 * scoreboard's target band.
 */
const EXPOSE_STOPS = (() => {
  const raw = params.get('expose');
  if (raw === null) return 0;
  const v = Number(raw);
  return Number.isFinite(v) ? v : 0;
})();

/* ---------------------------------------------------------------- lod table */

/**
 * `src/generated/index.ts` re-exports only the LODs that have actually been
 * baked, so the table is discovered rather than assumed -- a body-only `--lod
 * low` bake must still produce a working page.
 */
const registry = GENERATED as unknown as Record<string, EncodedLod | undefined>;
const AVAILABLE: string[] = LOD_ORDER.filter((n) => !!registry[`LOD_${n.toUpperCase()}`]);

function pickLod(want: string): string {
  if (AVAILABLE.includes(want)) return want;
  // Prefer the finest thing that exists rather than failing: the review loop
  // asks for `high` long before `high` has been baked.
  return AVAILABLE[0] ?? '';
}

/* ------------------------------------------------------------------- render */

const stage = document.getElementById('stage') as HTMLElement;
const detail = document.getElementById('detail') as HTMLElement;
if (SHOT) document.body.classList.add('shot');

const renderer = new WebGLRenderer({
  antialias: true,
  alpha: true,
  // Required so `toDataURL` can read the buffer back after the frame is done.
  preserveDrawingBuffer: true,
  powerPreference: 'high-performance',
});
renderer.outputColorSpace = SRGBColorSpace;
renderer.toneMapping = NeutralToneMapping;
renderer.toneMappingExposure = BASE_EXPOSURE * Math.pow(2, EXPOSE_STOPS);
renderer.setPixelRatio(SHOT ? 1 : Math.min(window.devicePixelRatio || 1, 2));
stage.append(renderer.domElement);

const scene = new Scene();

/** A dark radial falloff, matching the studio backdrop of the reference sheets. */
function backdrop(): CanvasTexture {
  const s = 512;
  const c = document.createElement('canvas');
  c.width = c.height = s;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(s * 0.5, s * 0.44, s * 0.02, s * 0.5, s * 0.5, s * 0.86);
  grad.addColorStop(0.0, '#4a5265');
  grad.addColorStop(0.35, '#39404f');
  grad.addColorStop(0.72, '#232833');
  grad.addColorStop(1.0, '#12141a');
  g.fillStyle = grad;
  g.fillRect(0, 0, s, s);
  const t = new CanvasTexture(c);
  t.colorSpace = SRGBColorSpace;
  return t;
}

if (BG === 'transparent') {
  scene.background = null;
  renderer.setClearColor(new Color(0x000000), 0);
} else {
  scene.background = backdrop();
  renderer.setClearColor(new Color(0x14161b), 1);
}

/* ------------------------------------------------------------------- lights */

/**
 * Three-point studio rig, no shadow casters, calibrated against
 * `ref/views/body_2.png`.
 *
 * The reference sheet is a *dark, high-contrast* image: measured in CIE L over
 * the alpha it sits at mean 36.7, p10 12.3, p90 74.7.  Two things follow.
 *
 * **The rig turns with the camera.**  Measure the reference panels and they are
 * within 2 L of each other (body_2 mean 36.7, body_0 mean 34.3, both p10 ~12.4,
 * both p90 ~74.7) -- the artist's turnaround spins the model inside a fixed
 * studio, so the key is always over the viewer's left shoulder.  A rig nailed to
 * world space instead does the opposite: at yaw 90 the key ends up behind the
 * subject and the panel comes out at mean 13.8 against the front's 26.9, which
 * makes the panels incomparable and the colour term meaningless.  So the rig is
 * a Group parented to the framing centre and yawed to follow the camera.  Only
 * the yaw follows -- pitch stays put, so orbiting up and down still changes the
 * modelling instead of dragging the key around with you.
 *
 * **The dark end needs indirect specular, not more ambient.**  Cloth sits at
 * 0.0097 linear reflectance and leather at 0.028; ACES then crushes what little
 * comes back (scene linear 0.01 leaves the tone mapper at 0.0024), so an
 * ambient strong enough to drag those materials up to the reference's p10 of
 * 12.3 blows lit skin past L 85 long before it gets there.  What actually lifts
 * them is the 4% Fresnel floor every dielectric has -- and that needs an
 * environment to reflect.  With no `envMap`, `RE_IndirectSpecular` contributes
 * nothing and every dark material renders as flat, dead albedo.  So the indirect
 * term is a PMREM of `RoomEnvironment` (procedural, no asset fetched, in keeping
 * with the rest of the project) and the directional rig only does the modelling.
 *
 * Nothing casts a shadow: the sheets have no contact shadow, and a ground
 * shadow would corrupt the silhouette matte `tools/compare.py` scores.
 *
 * Tune with `?expose=<stops>` / `--expose`, then fold the result back into
 * `BASE_EXPOSURE` -- do not ship renders taken at a non-zero trim.
 */
const rig = new Group();
rig.name = 'lightRig';
/** Shared aim point at the rig's own origin, so the lights stay camera-relative. */
const rigTarget = new Object3D();
rig.add(rigTarget);

// Flattened against the sheet.  The six reference panels sit within 2.6 L of
// each other; a key-dominant rig gave this model a 10 L spread, with the back
// view -6.9 L because the braids cover the lit skin there.  Raising fill and
// ambient against the key trades modelling for the reference's even, almost
// shadowless read, which is what the panels actually show.
const key = new DirectionalLight(0xfff2e2, 1.45);
key.position.set(-1.55, 2.05, 2.35);
const fill = new DirectionalLight(0x9fbcdf, 0.80);
fill.position.set(2.5, 0.55, 1.15);
const rim = new DirectionalLight(0xcfe0ff, 0.62);
rim.position.set(0.7, 1.55, -2.7);
const under = new DirectionalLight(0x6e7788, 0.22);
under.position.set(-0.3, -1.4, 0.9);
const ambient = new AmbientLight(0x9aa4b4, 0.52);
for (const l of [key, fill, rim, under]) {
  l.target = rigTarget;
  rig.add(l);
}
scene.add(rig, ambient);

// Procedural studio IBL.  `fromScene` is deterministic for a fixed renderer and
// scene, so it does not cost the renders their reproducibility.
const pmrem = new PMREMGenerator(renderer);
const roomScene = new RoomEnvironment();
scene.environment = pmrem.fromScene(roomScene, 0.04).texture;
scene.environmentIntensity = ENV_INTENSITY;
roomScene.traverse((o) => {
  const m = o as Mesh;
  (m.geometry as BufferGeometry | undefined)?.dispose();
});
pmrem.dispose();

/** Park the rig on the model and yaw it to match the camera. */
function orientRig(): void {
  rig.position.copy(framing.center);
  rig.rotation.y = MathUtils.degToRad(yawOf(camera, framing));
}

/* ------------------------------------------------------------------ geometry */

const materials = new MaterialLibrary();
const model = new Group();
model.name = 'jinx';
scene.add(model);

let framing: Framing = computeFraming(model);
let triangles = 0;
let activeLod = '';

function clearModel(): void {
  for (const child of [...model.children]) {
    model.remove(child);
    const m = child as Mesh;
    (m.geometry as BufferGeometry | undefined)?.dispose();
  }
}

async function loadLod(name: string): Promise<void> {
  const enc = registry[`LOD_${name.toUpperCase()}`];
  if (!enc) throw new Error(`LOD "${name}" is not baked; available: ${AVAILABLE.join(', ') || 'none'}`);

  clearModel();
  triangles = 0;

  for (const encoded of enc.meshes) {
    if (encoded.triangleCount === 0) continue;
    const geometry = await decodeMesh(encoded);
    // `decodeMesh` writes one geometry group per encoded group, with the group's
    // own index as its material index -- so the material array is the group list
    // resolved through the spec table, in order.
    const mesh = new Mesh(geometry, materials.forGroups(encoded.groups));
    mesh.name = encoded.name;
    mesh.frustumCulled = false;
    model.add(mesh);
    triangles += encoded.triangleCount;
  }

  activeLod = name;
  framing = computeFraming(model);
}

/* -------------------------------------------------------------------- camera */

const camera = new OrthographicCamera(-1, 1, 1, -1, 0.01, 100);
scene.add(camera);
let target = new Vector3();

function viewportSize(): { w: number; h: number } {
  if (SHOT) return { w: SHOT_W, h: SHOT_H };
  return {
    w: Math.max(1, stage.clientWidth || window.innerWidth),
    h: Math.max(1, stage.clientHeight || window.innerHeight),
  };
}

function resize(): void {
  const { w, h } = viewportSize();
  renderer.setSize(w, h, !SHOT ? false : true);
  if (SHOT) {
    // Exact pixels, no CSS scaling: the drawing buffer *is* the deliverable.
    renderer.domElement.style.width = `${w}px`;
    renderer.domElement.style.height = `${h}px`;
  }
  applyAspect(camera, framing, w / h);
}

function setView(yawDeg: number): void {
  const { w, h } = viewportSize();
  target = applyCanonicalView(camera, framing, yawDeg, w / h);
  if (controls) {
    controls.target.copy(target);
    controls.update();
  }
}

/* ------------------------------------------------------------------ controls */

let controls: OrbitControls | null = null;
let turntable = false;

function draw(): void {
  orientRig();
  renderer.render(scene, camera);
}

/* --------------------------------------------------------------------- boot */

async function boot(): Promise<void> {
  const lod = pickLod(REQUESTED_LOD);
  if (!lod) throw new Error('no LODs in src/generated -- run: npx tsx tools/bake.ts --lod low');
  await loadLod(lod);

  resize();
  setView(SHOT ? REQUESTED_YAW : 0);

  if (!SHOT) {
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = true;
    controls.minZoom = 0.25;
    controls.maxZoom = 12;
    controls.target.copy(target);
    controls.update();

    const panel = buildDetailPanel(detail, {
      title: 'Jinx — TypeScript procedural surfaces',
      author: 'img2threejs',
      authorNote: '· after Thibaut Granet, ARCANE',
      version: VERSION,
    });
    panel.setTriangles(triangles, activeLod);

    const ui = buildControls({
      lods: AVAILABLE,
      activeLod,
      yaws: CANONICAL_YAWS,
      onLod: (name) => {
        void (async () => {
          await loadLod(name);
          ui.setLod(name);
          panel.setTriangles(triangles, name);
          resize();
          setView(yawOf(camera, framing));
          updateReadout();
        })();
      },
      onWireframe: (on) => materials.setWireframe(on),
      onTurntable: (on) => {
        turntable = on;
      },
      onView: (yaw) => setView(yaw),
    });

    const updateReadout = (): void => {
      const { w, h } = viewportSize();
      ui.setReadout(
        `yaw <b>${yawOf(camera, framing).toFixed(0)}°</b> &middot; ` +
          `frame <b>${(framing.height * 1.06).toFixed(2)} m</b><br />` +
          `<b>${triangles.toLocaleString('en-US')}</b> tris &middot; ${w}&times;${h}`,
      );
    };
    updateReadout();
    controls.addEventListener('change', updateReadout);

    const ro = new ResizeObserver(() => {
      resize();
      updateReadout();
    });
    ro.observe(stage);
    window.addEventListener('resize', () => {
      resize();
      updateReadout();
    });

    let last = performance.now();
    renderer.setAnimationLoop(() => {
      const now = performance.now();
      const dt = Math.min((now - last) / 1000, 0.1);
      last = now;
      if (turntable && controls) {
        const offset = camera.position.clone().sub(controls.target);
        const a = dt * 0.45;
        const cos = Math.cos(a);
        const sin = Math.sin(a);
        camera.position.set(
          controls.target.x + offset.x * cos + offset.z * sin,
          camera.position.y,
          controls.target.z - offset.x * sin + offset.z * cos,
        );
        camera.lookAt(controls.target);
      }
      controls?.update();
      draw();
    });
    return;
  }

  /* ------------------------------------------------------------ shot mode */

  draw();

  window.__VIEW__ = (yawDeg: number) => {
    setView(yawDeg);
    draw();
  };
  window.__SHOT__ = () => renderer.domElement.toDataURL('image/png');
  window.__INFO__ = {
    requestedLod: REQUESTED_LOD,
    lod: activeLod,
    lods: AVAILABLE,
    triangles,
    width: SHOT_W,
    height: SHOT_H,
    background: BG,
    exposure: renderer.toneMappingExposure,
    exposeStops: EXPOSE_STOPS,
    frustumHeight: framing.height * 1.06,
    center: [framing.center.x, framing.center.y, framing.center.z],
  };
  window.__READY__ = true;
}

boot().catch((err: unknown) => {
  const message = err instanceof Error ? `${err.message}\n${err.stack ?? ''}` : String(err);
  window.__ERROR__ = message;
  // Still flip READY so the renderer stops waiting and reports the reason.
  window.__READY__ = true;
  console.error('[viewer] boot failed', err);
  if (!SHOT) {
    detail.innerHTML = `<p class="eyebrow">error</p><pre style="color:#ff8054;white-space:pre-wrap;font-size:12px">${message}</pre>`;
  }
});
