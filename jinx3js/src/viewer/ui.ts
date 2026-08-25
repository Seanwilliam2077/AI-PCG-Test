/// <reference types="vite/client" />
/**
 * The page chrome: the fixed gallery-detail panel on the left and the small
 * control cluster over the bottom-right of the viewport.
 *
 * All of it is built here rather than in `index.html` so the one image on the
 * page -- the source-reference thumbnail -- can come through Vite's asset
 * pipeline as an import.  That keeps `ref/` out of the deployed bundle apart
 * from the single panel that is actually shown, and keeps the URL correct in
 * both `vite dev` and a built `dist/`.
 *
 * Nothing in here touches Three; `main.ts` wires the callbacks.
 */
import thumbUrl from '../../ref/views/body_2.png?url';

export interface PanelInfo {
  title: string;
  author: string;
  authorNote: string;
  version: string;
}

export interface PanelHandles {
  /** Update the triangle-count tag when the LOD changes. */
  setTriangles(count: number, lod: string): void;
}

const DESCRIPTION = `
  <p class="blurb">
    Arcane's Jinx rebuilt as <strong>code only</strong>. The figure is a signed
    distance field authored in TypeScript, sampled by a Surface Nets mesher and
    baked into <strong>encoded typed arrays embedded in TypeScript source</strong>
    &mdash; quantised positions, byte normals and deflated index buffers that the
    viewer inflates into Three.js buffer geometry on load. No model files, no
    textures, nothing fetched at runtime.
  </p>
  <p class="blurb">
    The same field is meshed at three voxel sizes, giving
    <strong>High</strong>, <strong>Medium</strong> and <strong>Low</strong> LODs
    that you can switch between live. Shading comes from a small material table
    in the spec: every geometry group carries a material name, and the viewer
    builds one physically based material per name.
  </p>
`;

export function buildDetailPanel(host: HTMLElement, info: PanelInfo): PanelHandles {
  host.innerHTML = `
    <nav class="crumbs">
      <a href="#" id="back-link">&larr; Back to gallery</a>
      <span class="here">Details</span>
    </nav>

    <p class="eyebrow">img2threejs &middot; reconstruction</p>
    <h1>${info.title}</h1>

    <p class="byline">
      <span class="lead">by</span>
      <span class="who">${info.author} <span>${info.authorNote}</span></span>
    </p>

    <p class="field-label">Source reference</p>
    <figure class="thumb">
      <img id="ref-thumb" alt="Reference turnaround panel: Jinx, front view" />
      <figcaption>
        ref/views/body_2.png &mdash; front panel of the artist turnaround<br />
        Thibaut Granet, &ldquo;ARCANE &mdash; Jinx&rdquo;
      </figcaption>
    </figure>

    <ul class="tags">
      <li>character</li>
      <li class="wide">img2threejs ${info.version} &middot; procedural TypeScript Surface Nets</li>
      <li id="tri-tag">&mdash; triangles</li>
    </ul>

    ${DESCRIPTION}
  `;

  const img = host.querySelector<HTMLImageElement>('#ref-thumb');
  if (img) img.src = thumbUrl;

  const back = host.querySelector<HTMLAnchorElement>('#back-link');
  back?.addEventListener('click', (e) => e.preventDefault());

  const tri = host.querySelector<HTMLElement>('#tri-tag');
  return {
    setTriangles(count: number, lod: string) {
      if (tri) tri.textContent = `${count.toLocaleString('en-US')} triangles · ${lod} LOD`;
    },
  };
}

export interface ControlsOptions {
  /** LOD names actually present in `src/generated`, coarse-to-fine order preserved. */
  lods: string[];
  activeLod: string;
  yaws: readonly number[];
  onLod(name: string): void;
  onWireframe(on: boolean): void;
  onTurntable(on: boolean): void;
  onView(yawDeg: number): void;
}

export interface ControlsHandles {
  root: HTMLElement;
  setLod(name: string): void;
  setReadout(html: string): void;
}

function button(label: string, cls?: string): HTMLButtonElement {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = label;
  if (cls) b.className = cls;
  return b;
}

function group(label: string, rowClass = 'row'): { el: HTMLElement; row: HTMLElement } {
  const el = document.createElement('div');
  el.className = 'grp';
  const l = document.createElement('div');
  l.className = 'grp-label';
  l.textContent = label;
  const row = document.createElement('div');
  row.className = rowClass;
  el.append(l, row);
  return { el, row };
}

const TITLE_CASE: Record<string, string> = { high: 'High', medium: 'Medium', low: 'Low' };

export function buildControls(opts: ControlsOptions): ControlsHandles {
  const root = document.createElement('div');
  root.id = 'controls';

  // --- LOD ---------------------------------------------------------------
  const lodGrp = group('Level of detail');
  const lodButtons = new Map<string, HTMLButtonElement>();
  for (const name of opts.lods) {
    const b = button(TITLE_CASE[name] ?? name);
    b.addEventListener('click', () => opts.onLod(name));
    lodButtons.set(name, b);
    lodGrp.row.append(b);
  }
  if (opts.lods.length === 0) {
    const b = button('none baked');
    b.disabled = true;
    lodGrp.row.append(b);
  }

  // --- display toggles ---------------------------------------------------
  const dispGrp = group('Display');
  const wire = button('Wireframe');
  const turn = button('Turntable');
  let wireOn = false;
  let turnOn = false;
  wire.setAttribute('aria-pressed', 'false');
  turn.setAttribute('aria-pressed', 'false');
  wire.addEventListener('click', () => {
    wireOn = !wireOn;
    wire.setAttribute('aria-pressed', String(wireOn));
    opts.onWireframe(wireOn);
  });
  turn.addEventListener('click', () => {
    turnOn = !turnOn;
    turn.setAttribute('aria-pressed', String(turnOn));
    opts.onTurntable(turnOn);
  });
  dispGrp.row.append(wire, turn);

  // --- canonical views ---------------------------------------------------
  const viewGrp = group('Canonical views', 'row views');
  for (const yaw of opts.yaws) {
    const b = button(`${yaw}°`);
    b.title = `Yaw ${yaw}° (0° = front, camera on +Z)`;
    b.addEventListener('click', () => {
      if (turnOn) {
        turnOn = false;
        turn.setAttribute('aria-pressed', 'false');
        opts.onTurntable(false);
      }
      opts.onView(yaw);
    });
    viewGrp.row.append(b);
  }

  const readout = document.createElement('div');
  readout.className = 'readout';

  root.append(lodGrp.el, dispGrp.el, viewGrp.el, readout);
  document.body.append(root);

  const handles: ControlsHandles = {
    root,
    setLod(name: string) {
      for (const [k, b] of lodButtons) b.setAttribute('aria-pressed', String(k === name));
    },
    setReadout(html: string) {
      readout.innerHTML = html;
    },
  };
  handles.setLod(opts.activeLod);
  return handles;
}
