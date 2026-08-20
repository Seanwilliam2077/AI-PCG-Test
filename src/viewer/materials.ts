/**
 * Three materials built from `spec.materials`.
 *
 * The bake writes a *name* into every geometry group (`EncodedGroup.material`),
 * never an index, so the viewer can be rebuilt against a spec that gained or
 * reordered materials without a re-bake.  This module is the only place that
 * turns those names into GPU state.
 *
 * Colours in the spec are **sRGB** display values -- they were authored by eye
 * against the reference sheets, not measured as linear reflectance -- so they
 * are tagged `SRGBColorSpace` and Three decodes them into its linear working
 * space.  Reading them as linear instead is not a subtle error: `skin`
 * [0.913, 0.784, 0.706] taken as linear is very nearly white, which blows the
 * whole figure out to paper and collapses the Lab colour term of the
 * scoreboard.  `src/mesh/format.ts` still documents the field as linear; the
 * spec is the authority and it is sRGB.
 */
import {
  Color,
  DoubleSide,
  FrontSide,
  Material,
  MeshPhysicalMaterial,
  MeshStandardMaterial,
  SRGBColorSpace,
} from 'three';

import { SPEC } from '../spec.js';
import type { MaterialSpec, MaterialTable } from '../mesh/format.js';

/** `spec/jinx.json` types `color` as `number[]`; the contract says it is a triple. */
const TABLE = SPEC.materials as unknown as MaterialTable;

const FALLBACK: MaterialSpec = { color: [0.75, 0.75, 0.78], roughness: 0.7, metalness: 0.0 };

/** Spec triple (sRGB 0..1) -> a Three colour in the linear working space. */
function srgb(rgb: readonly number[]): Color {
  return new Color().setRGB(rgb[0] ?? 0, rgb[1] ?? 0, rgb[2] ?? 0, SRGBColorSpace);
}

function create(name: string, spec: MaterialSpec): MeshStandardMaterial {
  const common = {
    name,
    color: srgb(spec.color),
    roughness: spec.roughness,
    metalness: spec.metalness,
    side: FrontSide,
    flatShading: false,
  };

  // Sheen and transmission only exist on the physical model.  MeshPhysicalMaterial
  // *is* a MeshStandardMaterial (it extends it), so the mesh still sees one type.
  if (spec.sheen || spec.transmission) {
    const m = new MeshPhysicalMaterial(common);
    if (spec.sheen) {
      // A restrained rim: enough to lift the silhouette of hair and cloth off the
      // backdrop without reading as an emissive.
      m.sheen = 0.55;
      m.sheenColor = srgb(spec.sheen);
      m.sheenRoughness = 0.45;
    }
    if (spec.transmission) {
      m.transmission = spec.transmission;
      m.thickness = 0.02;
      m.ior = 1.4;
      m.transparent = true;
    }
    return m;
  }

  return new MeshStandardMaterial(common);
}

/**
 * Name -> material, memoised so every shell that uses `skin` shares one program
 * and one wireframe/flat-shading toggle.
 */
export class MaterialLibrary {
  private readonly cache = new Map<string, MeshStandardMaterial>();

  /** Names declared by the spec, in spec order. */
  readonly names: string[] = Object.keys(TABLE);

  get(name: string): MeshStandardMaterial {
    let m = this.cache.get(name);
    if (!m) {
      const spec = TABLE[name];
      if (!spec) console.warn(`[viewer] material "${name}" is not in spec.materials; using fallback`);
      m = create(name, spec ?? FALLBACK);
      this.cache.set(name, m);
    }
    return m;
  }

  /** Materials for one encoded mesh, indexed to match its geometry groups. */
  forGroups(groups: readonly { material: string }[]): MeshStandardMaterial[] {
    if (groups.length === 0) return [this.get(this.names[0] ?? 'skin')];
    return groups.map((g) => this.get(g.material));
  }

  all(): MeshStandardMaterial[] {
    return [...this.cache.values()];
  }

  setWireframe(on: boolean): void {
    for (const m of this.cache.values()) {
      m.wireframe = on;
      // Wireframe on a closed Surface Nets shell reads much better with both
      // faces drawn; solid shading stays single sided so backfaces do not fight.
      m.side = on ? DoubleSide : FrontSide;
      m.needsUpdate = true;
    }
  }

  dispose(): void {
    for (const m of this.cache.values()) (m as Material).dispose();
    this.cache.clear();
  }
}
