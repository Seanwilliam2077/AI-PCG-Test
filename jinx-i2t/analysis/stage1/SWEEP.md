# Stage1/Stage2 tool sweep — jinx-i2t

Run 2026-08-20. `object-sculpt-spec.json` was **not modified**; every spec-writing tool ran
against `analysis/stage1/spec_scratch.json` (a byte-identical copy, verified with `cmp`).
All artefacts are under `analysis/stage1/`.

## Table

| tool | ran? | headline output | what it tells us about this Jinx build |
|---|---|---|---|
| `analyze_texture.py` | yes, 21/21 crops | `analysis/stage1/analyze_texture/*.json`. finishClass is wrong for the metals (brass, steel → `painted-metal`, metalness 0.0) and wrong for skin (`plastic`) / tattoo + skinShade (`brushed-steel`, metalness **1.0**) | The finish classes are inverted relative to the spec. Not a style-transfer artefact — it is the first signal that the crops feeding it are not the materials they are named after. |
| `detect_reference_effects.py` | yes, 3/5 | `body_2` dof=true bloom=false; `head_0` dof=true **bloom=true** (hotFraction 0.0134, halo 56.5%); `clay_2` dof=true bloom=false. The two `.jpg` sheets error: `could not decode … as PNG and macOS sips is unavailable` | `dof=true` is an artefact — matted PNGs have a flat background, so backgroundEnergy is ~0 by construction. The **bloom verdict on `head_0` is real** (measured on subject highlights) and the spec currently authorises no presentation-stage bloom. |
| `extract_gradient_stops.py` | yes, 12 mats × 2 axes | `analysis/stage1/gradient/`. `hairDark` flags `blue-collapse` on **all 5** stops; `hair` on 2 of 5; `skinShade` on 2 of 5 | Jinx's identity colour is exactly the hue the tool says will collapse to flat dark in-render. It emits a magenta-lean corrected RGB per stop. `hair`'s stops are 60% light warm grey — the crop is mostly not hair. |
| `extract_part_color_recipe.py` | yes, 13 components | `analysis/stage1/part_recipe/`. Roughness estimates **0.12–0.55**, versus the spec's 0.68–0.71 for the same materials. `hair` dominantAlbedo = `rgba(211,197,192)` (background), secondary = `rgba(46,93,128)` (the actual blue) | An independent (CIE-Lab + specular-hotspot) estimator disagrees with the spec's roughness across the board, and independently confirms the hair crop is majority non-hair. |
| `material_region_analysis.py` | yes, 21 regions, `status: proceed` | `analysis/stage1/material-analysis.json` + `material_regions/`. All 21 bound to registry profiles, conf 0.77–0.86. renderPriors: skin 0.52, hair 0.45, fabric **0.85**, leather 0.62, glass **0.05**, metals metalness **1.0** | The one tool that produces a defensible per-material contract: profileId, renderPrior, requiredMaps, validationViews, and per-region crop provenance. First run returned `probe`/`request-input` for 11 regions because I passed profile ids as `subtype`; corrected tokens (`woven`, `brass-bronze`, `steel`, …) give `proceed`. |
| `semantic_decomposition.py` | **N/A** | no CLI; `assess_semantic_decomposition()` takes GLB node/mesh/primitive/material metadata | No `.glb` exists anywhere in the project — this is a procedural Three.js build, not a GLB import. Nothing to assess without fabricating counts. |
| `bind_detail_properties.py` | yes, 17 details from `di.json` | `analysis/stage1/bind_detail_properties.json`. 8/17 bound. zapper + zapper-tank → `transmission 0.6, ior 1.6, thickness 0.5, roughness 0.1, requiresEnvMap`; braid-ties/boots/x-lacing → `metalness 1.0, roughness 0.3, requiresEnvMap` | Confirms the tank needs a real transmissive contract. 9 details bind nothing (tattoo, pinstripe, crest, shin-patch, boot-lacing, tattered-hem, arm bands, belts) — its keyword table has no rules for them, so it is silent, not wrong. |
| `check_intake_correctness.py` | yes, on `assessment.json` and the spec | `action: proceed`, **`confirmed: false`** — "no objectness source available yet … confirmation DEFERRED to Phase 3 (OSIM)" | The object-class claim ("full-body humanoid game character, stylised realism") has never been cross-checked. Standing gap, not an error. Identical output for both inputs. |
| `solve_camera_pose.py` | yes, 6/6 body views | `analysis/stage1/camera/`. Perspective **fov 38.0°** (`source: default-guess`), yaw/pitch/roll placeholders, confidence 0.35. Exact dims: `body_2` 377×1299, aspect 0.2902 | Its own `limitations` block says the FOV is "a genre default, not a measurement". The spec's orthographic finding is better evidence. **Do not apply this output.** Its exact per-panel pixel dimensions are worth keeping. |
| `camera_fitting_solver.py` | **N/A** | library only; direct `--help` fails `ModuleNotFoundError: No module named 'forge'` (needs the skill root on `sys.path`). Verified importable that way; `fit_parameters(correspondences, initial_camera, limits)` needs `NormalizedCorrespondence(name, world, observed)` — 2D↔3D pairs | The spec's `silhouette.landmarks` are 1-D heights (`heightMetres`) only, with no image-pixel partners, so there is no correspondence set. It also fits fov + Euler + position for a **perspective** camera, which is structurally inapplicable to an orthographic turnaround. |
| `humanoid_proportions.py` | yes (exit 2, refused) | `error: spec names a reference image (ref/views/body_2.png); measure anatomy from it rather than substituting the canon table` | Fail-closed and correct. Positively confirms the spec's measured `styleHeads: 8.19` must not be replaced by the canon table. Tried `--style-heads 8.19` and `8.0`; both refused. |
| `derive_geometry.py` | yes, clay_0/2/5 | `analysis/stage1/geometry/`. 24-point medial-axis profiles. Max half-width: clay_2 0.1295, clay_0 0.0956, clay_5 0.1358 (normalised by height) | Built for axisymmetric lathe subjects, so the profile itself is not usable for a biped — but the widths it measures are a real, independent check on the spec's silhouette numbers, and they do not agree (see below). |
| `apply_material_analysis.py` | yes, on the scratch copy | `analysis/stage1/spec_after_material_analysis.json`, **799 diffs**, `status: proceed`. Diff summary in `apply_material_analysis_substantive.txt` | Would add `materialPipeline`, `materialAnalysisHistory`, per-material `materialFamily/Subtype/Finish/referenceMaterialId/materialReference/materialEvidence/textureAnalysis`, `clearcoat`/`sheen`/`anisotropy`/`ior`/`needsEnvironment` blocks, a **21st material `clothWorn`**, and `uvContract` + `materialRegions` on 18 components. It also rewrites every `roughness.base` and converts `metalness` to `{base, variation}`. Not applied. |

## (a) Measurements that contradict `object-sculpt-spec.json`

1. **Silhouette aspect ratio — the largest numeric disagreement.**
   Spec `silhouette.aspectRatios`: front `widthOverHeight: 0.176`, side `depthOverHeight: 0.11`
   (consistent with `boundingShape: "1.72 x 0.30 x 0.19 m at the ribcage"`).
   `derive_geometry.py` on `ref/views/clay_2.png` gives max half-width 0.1295 → **0.259**; on
   `clay_0.png` 0.0956 → **0.191**; `clay_5.png` 0.1358 → **0.272**. A direct alpha-bbox
   measurement agrees: clay_2 354×1278 px → **0.277**, clay_0 274×1212 px → **0.226**.
   So the spec's front number is low by **1.57×** and its side number by **2.05×**. The spec is
   recording a *ribcage cross-section* in a field named `silhouette.aspectRatios`; anything
   downstream that reads it as the object bounding box (framing, camera fit, LOD bounds, culling)
   will be wrong by that factor. In metres: 0.30 × 0.19 declared vs **0.48 × 0.39** actual bbox.

2. **Roughness is effectively a two-valued constant, which the spec's own contract forbids.**
   Histogram of `materials[*].roughness.base`: **7 materials at exactly 0.34**, 13 clustered in
   **[0.683, 0.709]** — two values for twenty materials. Meanwhile
   `lookDevTargets.materialPass.mustAvoid` literally lists `"uniform roughness"`.
   Three independent estimators disagree with it and with each other, but none reproduce the
   cluster: `material_region_analysis` renderPriors say skin 0.52 / hair 0.45 / fabric **0.85** /
   leather 0.62 / glass **0.05**; `extract_part_color_recipe` says skin 0.545 / hair 0.23 /
   cloth 0.124 / pants 0.175 / leather 0.129; `analyze_texture` says skin 0.6 / hair 0.5 /
   cloth 0.18. Concrete pairs — cloth **0.699 → 0.85**, hair **0.686 → 0.45**,
   glassTank **0.34 → 0.05**, nailTeal **0.34 → 0.45**.

3. **`glassTank` declares transmission on a material type that cannot render it.**
   Spec: `type: "standard"`, `shaderModel: "MeshStandardMaterial / PBR approximation"`,
   `transmission: 0.85`, `roughness.base: 0.34`, and a note calling it "the ONLY translucent
   material in the subject". MeshStandardMaterial has no `transmission` channel, so 0.85 is inert;
   the spec's own `shaderNotes[0]` says to prefer MeshPhysicalMaterial when transmission is
   observed. `material_region_analysis` resolves it to `glass.clear` with roughness **0.05** and
   `needsEnvironment: true`; `bind_detail_properties` on the zapper description independently
   asks for `transmission 0.6, ior 1.6, thickness 0.5, roughness 0.1`. Three sources, one
   conclusion: **0.85 vs 0.6**, and the type must change.

4. **Metalness is fractional where the workflow requires binary.**
   Spec brass **0.85**, steel **0.9**. The registry's metallic-roughness profiles
   (`metal.brass`, `metal.steel-brushed`) both give **1.0**, and `apply_material_analysis`
   rewrites both. Separately `analyze_texture` reports metalness **0.0** for those two crops and
   **1.0** for `skinShade` and `tattoo` — an exact inversion, which is symptom, not cause (see 5).

5. **Fifteen of twenty materials have `referencePbr` extracted from pixels that are not that
   material.** Re-sampling the exact rectangles in `analysis/extract_pbr.py`'s `REGIONS` table
   against the source panels and comparing the region's median RGB to the spec's declared
   `baseColor` (`analysis/stage1/crop_provenance_recheck.txt`):

   | material | region median | spec `baseColor` | RGB distance |
   |---|---|---|---|
   | pupil | `#CDB8B2` | `#1B1A20` | 279 |
   | brow | `#D5C7C3` | `#3A2C28` | 269 |
   | glassTank | `#573F49` | `#9FB6BE` | 182 |
   | brass | `#2E2A26` | `#B48B49` | 169 |
   | sclera | `#AD8C84` | `#ECE8E4` | 147 |
   | lip | `#CFC0BC` | `#A96766` | 130 |
   | nailTeal | `#706562` | `#3FB8B0` | 124 |
   | steel | `#48343D` | `#797D82` | 112 |
   | laceMagenta | `#302827` | `#8E3A5C` | 109 |
   | eye | `#AD8C84` | `#5A8296` | 86 |
   | canvas | `#57374D` | `#7A7353` | 70 |
   | hair | `#4D6E86` | `#274E69` | 58 |
   | tattoo | `#C4AA9F` | `#BEC7CB` | 53 |
   | skinShade | `#9BA09D` | `#BCA298` | 33 |
   | pantsDark | `#55324B` | `#402439` | 31 |

   Only `skin` (2.4), `leather` (1.7), `hairDark` (10.4), `pants` (11.4) and `cloth` (17.4) hold up.
   All five head materials (`eye`, `sclera`, `pupil`, `lip`, `brow`) land on bare cheek/forehead
   skin. Three rectangles are partly outside the alpha silhouette entirely — `nailTeal` is only
   **30.4%** inside, `tattoo` **50.7%**, `hairDark` **60.3%** — so the transparent matte was
   flattened into the crop (all 21 crops are 3-channel RGB, alpha discarded).
   `pbr/crops/eye.png` and `pbr/crops/sclera.png` are **byte-identical** (md5 `ab3b19b0fa`,
   same rect in the REGIONS table), so `sclera`'s "measured" roughness/normal/AO are the eye's.
   The albedo, roughness, normal, AO, palette and `colorVariation` of all fifteen carry the
   contaminated pixels' statistics, which is exactly why every roughness landed on ~0.69.

6. **`clothWorn` is an orphan.** `pbr/crops/clothWorn.png`, `pbr/clothWorn/*` (5 maps) and
   `pbr/clothWorn_report.json` (confidence 0.86) all exist, but `materials[]` holds 20 entries
   and `clothWorn` is not among them. `apply_material_analysis` adds it as the 21st.

7. **Reference camera.** Spec: `projection: "orthographic"`, `fovDegrees: null`.
   `solve_camera_pose.py` returns perspective **38.0°** at confidence 0.35 for all six views.
   Reported for completeness only — the tool's own `limitations` block disclaims the number and
   the spec's orthographic reasoning (mirror-silhouette degeneracy, 22-bit pHash separation) is
   the stronger evidence. **Do not apply.** Worth keeping from it: exact panel dimensions
   (`body_2` 377×1299, aspect 0.2902), which the spec does not currently record.

8. **Intake never confirmed.** `check_intake_correctness` returns `confirmed: false` against both
   `assessment.json` and the spec. The spec presents `preSpecAssessment.objectClass` without a
   matching "confirmation deferred" marker.

## (b) The single most valuable change

**Re-cut the 21 PBR evidence crops with alpha-aware, silhouette-verified rectangles, and re-derive
every material through `material_region_analysis.py` → `apply_material_analysis.py`.**

Finding 5 is upstream of findings 2, 4, and most of the `analyze_texture` and
`extract_part_color_recipe` weirdness. Fifteen of twenty materials — including every head
material, both metals, and the glass tank — currently carry albedo/roughness/normal/AO/palette
derived from the wrong pixels, and the near-constant 0.69 roughness is the signature of that
contamination rather than a measurement. Repainting individual numbers fixes symptoms; re-cutting
the crops fixes the cause.

The machinery is already proven on this project: `analysis/stage1/material_region_manifest.json`
runs 21 regions to `status: proceed` at 0.77–0.86 confidence, and
`analysis/stage1/spec_after_material_analysis.json` shows the resulting spec. Doing it properly
adds three things the spec does not have today: per-material **provenance** (`materialEvidence`
carries the crop path, bbox, coverage and the extractor report, so a bad crop is visible instead
of silent), **registry-bound render contracts** (`profileId`, `renderPrior`, `requiredMaps`,
`needsEnvironment` — which is what forces `glassTank` onto a transmissive physical material and
the metals onto metalness 1.0), and **component↔material bindings** (`materialRegions` +
`uvContract` on 18 components).

Two conditions before applying it:

- The bboxes must be re-authored first. The manifest above reuses the same rectangles that are
  wrong; re-running it as-is would only relocate the same bad pixels. Each rect needs to be
  checked for ≥95% alpha coverage and median-colour agreement with the material's intent.
- `apply_material_analysis` overwrites `roughness.base` with the registry's generic prior
  (every fabric → 0.85, every skin → 0.52). That is a *prior*, not a measurement — it re-creates
  the uniformity problem at different values. Take its structure, provenance and bindings; keep
  per-material roughness from the re-cut pixel evidence.

Second-most valuable, and cheap: honour `extract_gradient_stops`' `blue-collapse` flags on
`hair`/`hairDark` (5 of 5 stops on `hairDark`) with the magenta-lean corrections it supplies —
that is Jinx's single most recognisable feature.
