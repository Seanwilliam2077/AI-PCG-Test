/**
 * Review harness for the generated factory.
 *
 * Its only job is to put `createJinxArcaneModel()` in front of a deterministic
 * orthographic camera at the six canonical yaws, so the render can be scored
 * against the reference panels. Framing is fixed in metres rather than fitted
 * to the bounding box: a bbox fit rescales the moment a pass adds geometry, and
 * every earlier measurement with it.
 */
import * as THREE from 'three';
import {
  createJinxArcaneModel,
  createJinxArcaneLookDevLights,
  createJinxArcaneEnvironment,
  configureJinxArcaneRenderer,
} from './createJinxModel.js';

declare global {
  interface Window {
    __READY__?: boolean;
    __SHOT__?: () => string;
    __VIEW__?: (yawDeg: number) => void;
    __INFO__?: Record<string, unknown>;
    __ERROR__?: string;
  }
}

const params = new URLSearchParams(location.search);
const num = (k: string, d: number) => {
  const v = Number(params.get(k));
  return Number.isFinite(v) && v > 0 ? v : d;
};
const W = Math.round(num('w', 620));
const H = Math.round(num('h', 1100));
const FRAME = Number(params.get('frame')) || 1.8;   // metres of vertical field
const TRANSPARENT = params.get('bg') !== 'dark';
const WIRE = params.get('wire') === '1';

try {
  const renderer = new THREE.WebGLRenderer({
    antialias: true, alpha: true, preserveDrawingBuffer: true,
  });
  configureJinxArcaneRenderer(renderer);
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  if (TRANSPARENT) {
    scene.background = null;
    renderer.setClearColor(0x000000, 0);
  } else {
    scene.background = new THREE.Color(0x14161b);
  }

  try {
    scene.environment = createJinxArcaneEnvironment(renderer);
  } catch {
    /* environment is optional; the directional rig alone still renders */
  }

  const model = createJinxArcaneModel({ wireframe: WIRE });
  scene.add(model);

  // The rig turns with the camera: the reference's six panels sit within 2.6 L
  // of each other, which only happens if the studio is fixed and the model spins.
  const rig = new THREE.Group();
  try {
    // Returns a Group, not an array. `for...of` over it throws, and the catch
    // below swallowed that silently -- so every pass so far rendered on the
    // two-light fallback, not the rig the pipeline calibrated.
    const lights = createJinxArcaneLookDevLights();
    rig.add(lights as unknown as THREE.Object3D);
    // The spec carries a tone-mapping entry calibrated against the reference
    // sheet (Khronos PBR Neutral, exposure 0.60). Read it off the generated rig
    // rather than hard-coding a number here -- otherwise the harness renders at
    // linear 1.0 and every pass reads a stop and a half too bright.
    const tm = ((lights as THREE.Group).userData?.lightingFromPhoto || [])
      .find((e: { type?: string }) => e.type === 'tonemap');
    if (tm) {
      const modes: Record<string, THREE.ToneMapping> = {
        'Khronos PBR Neutral': THREE.NeutralToneMapping,
        ACES: THREE.ACESFilmicToneMapping,
        AgX: THREE.AgXToneMapping,
        Reinhard: THREE.ReinhardToneMapping,
      };
      renderer.toneMapping = modes[tm.mode] ?? THREE.NeutralToneMapping;
      renderer.toneMappingExposure = tm.exposure ?? 1.0;
    }
    // Search hooks for calibrating the lighting envelope against the six-yaw L
    // statistics. The winning values get written back into the spec; these only
    // exist so a sweep does not have to regenerate the factory each trial.
    const q = new URLSearchParams(location.search);
    const num = (k: string, d: number) => (q.has(k) ? Number(q.get(k)) : d);
    renderer.toneMappingExposure *= num('exp', 1);
    const kKey = num('key', 1), kAmb = num('amb', 1), kEnv = num('env', 1);
    lights.traverse((o) => {
      const l = o as THREE.Light;
      if (!l.isLight) return;
      if ((l as THREE.AmbientLight).isAmbientLight || (l as THREE.HemisphereLight).isHemisphereLight) {
        l.intensity *= kAmb;
      } else {
        l.intensity *= kKey;
      }
    });
    if (scene.environment) scene.environmentIntensity = kEnv;
    // Uniform-albedo probe: with every material replaced by the same white, any
    // remaining front-to-back L difference is the rig, not the textures.
    if (num('flat', 0)) {
      const flat = new THREE.MeshStandardMaterial({ color: 0xb0b0b0, roughness: 0.7, metalness: 0 });
      model.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.isMesh) m.material = flat;
      });
    }
  } catch {
    rig.add(new THREE.AmbientLight(0x9aa4b4, 0.6));
    const key = new THREE.DirectionalLight(0xfff2e2, 1.45);
    key.position.set(-1.55, 2.05, 2.35);
    rig.add(key);
  }
  scene.add(rig);

  const box = new THREE.Box3().setFromObject(model);
  const centre = box.getCenter(new THREE.Vector3());

  const aspect = W / H;
  const halfH = FRAME / 2;
  const camera = new THREE.OrthographicCamera(-halfH * aspect, halfH * aspect, halfH, -halfH, 0.01, 40);

  function view(yawDeg: number) {
    const a = (yawDeg * Math.PI) / 180;
    // Frame on the metric floor-to-FRAME window, not on the bounding box.
    const target = new THREE.Vector3(0, FRAME / 2, 0);
    camera.position.set(target.x + Math.sin(a) * 6, target.y, target.z + Math.cos(a) * 6);
    camera.up.set(0, 1, 0);
    camera.lookAt(target);
    camera.updateProjectionMatrix();
    rig.quaternion.copy(camera.quaternion);
    // The environment has to turn with the rig as well. It was the one part of the
    // studio left in world space, and with every other light camera-relative it was
    // the whole of the front-to-back falloff: a uniform-albedo probe measured a
    // six-view L spread of 14.38 with the environment on and 2.19 with it off,
    // against the reference sheet's 2.61.
    scene.environmentRotation.set(0, a, 0);
    renderer.render(scene, camera);
  }

  window.__VIEW__ = view;
  window.__SHOT__ = () => renderer.domElement.toDataURL('image/png');
  // Per-mesh extents, so a stray component below the floor can be named rather
  // than hunted for in the spec.
  const lows: { name: string; minY: number; maxY: number }[] = [];
  model.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh || !m.geometry) return;
    const b = new THREE.Box3().setFromObject(m);
    lows.push({ name: m.name || o.name || '(unnamed)', minY: +b.min.y.toFixed(3), maxY: +b.max.y.toFixed(3),
      w: +(b.max.x - b.min.x).toFixed(3), d: +(b.max.z - b.min.z).toFixed(3),
      tris: (m.geometry.index ? m.geometry.index.count : m.geometry.attributes.position.count) / 3
        * (m instanceof THREE.InstancedMesh ? m.count : 1),
      x0: +b.min.x.toFixed(3), x1: +b.max.x.toFixed(3) });
  });
  lows.sort((a, b) => a.minY - b.minY);

  // What colour did the materials actually resolve to? A uniform grey means the
  // factory fell back to its 0x888888 default rather than the spec palette.
  const mats: Record<string, string> = {};
  model.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh || !m.material) return;
    const mat = m.material as THREE.MeshStandardMaterial;
    if (mat && mat.color && !mats[m.name]) {
      mats[m.name] = '#' + mat.color.getHexString() + (mat.map ? ' +map' : '') +
        ` m=${(mat.metalness ?? -1).toFixed(2)} r=${(mat.roughness ?? -1).toFixed(2)}`;
    }
  });
  const wides = [...lows].sort((a, b) => (b.w ?? 0) - (a.w ?? 0));
  // Sockets are declared in component-local metres; the only way to know they
  // landed on the joint is to read their world position back out.
  const socketProbe: Record<string, number[]> = {};
  const rt = (model.userData as { sculptRuntime?: { sockets?: Record<string, THREE.Object3D> } }).sculptRuntime;
  for (const [k, o] of Object.entries(rt?.sockets ?? {})) {
    const w = new THREE.Vector3();
    o.getWorldPosition(w);
    socketProbe[k] = [+w.x.toFixed(4), +w.y.toFixed(4), +w.z.toFixed(4)];
  }
  const talls = [...lows].sort((a, b) => b.maxY - a.maxY);
  window.__INFO__ = {
    materials: mats,
    heaviest: [...lows].sort((a, b) => (b.tris ?? 0) - (a.tris ?? 0))
      .map((m) => ({ name: m.name, tris: m.tris })),
    sockets: socketProbe,
    widest: wides,
    lowest: lows.slice(0, 5),
    tallest: talls.slice(0, 6),
    meshCount: lows.length,
    width: W, height: H, frameMetres: FRAME,
    bbox: { min: box.min.toArray(), max: box.max.toArray() },
    centre: centre.toArray(),
    // renderer.info.render.triangles is a per-frame RENDERED count and accumulates
    // across draw calls, so it read ~2x the model. The budget is about geometry, so
    // report the sum over meshes and keep the rendered figure beside it, named.
    triangles: lows.reduce((a, m) => a + (m.tris ?? 0), 0),
    trianglesRendered: renderer.info.render.triangles,
    drawCalls: lows.length,
  };

  view(Number(params.get('yaw')) || 0);
  window.__INFO__.trianglesRendered = renderer.info.render.triangles;
  window.__READY__ = true;
} catch (err) {
  window.__ERROR__ = String((err as Error)?.stack || err);
  // Make the failure loud rather than shipping a blank PNG.
  document.body.innerHTML = `<pre style="color:#f66;font:12px monospace;white-space:pre-wrap">${window.__ERROR__}</pre>`;
}
