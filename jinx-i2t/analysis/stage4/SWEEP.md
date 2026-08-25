# stage4_review sweep — jinx-i2t

Every `forge/stage4_review/` tool listed in the assignment, run against this build on 2026-08-20.
Tool source: `C:/Users/lvhaochen/.claude/skills/img2threejs/forge/stage4_review/`.
Raw outputs: `analysis/stage4/raw/`. Framing-normalised images: `analysis/stage4/norm/`.
Region crops: `analysis/stage4/crops/`. Harness used to extract the built mesh:
`analysis/stage4/dump_entry.ts` + `analysis/stage4/dump_run.mjs` (esbuild + headless Chromium;
no dev server, nothing under `src/`, `tools/`, `out/` or the spec was written).

`object-sculpt-spec.json` was **not** modified. `--in-place` was never passed to any tool
(`materialGate` is absent from the spec, which is the proof: `material_gate --in-place` is the
only thing in this sweep that would have added it).

**Provenance.** `src/createJinxModel.ts` last written 11:45:16, `out/lighting-pass/` renders
11:47:01, mesh dump 11:53:48 — one consistent set, the mesh measured here is the factory that
produced those renders. A concurrent process rewrote `object-sculpt-spec.json` at 12:04:54 while
this sweep was running; every spec-derived number below was re-verified against that later file
and all of them still hold.

## Inputs that had to be manufactured first

Three families of tools need a *built mesh* or a *runtime part tree*, and the project ships
neither (the model is a 978 KB procedural TS factory, `src/createJinxModel.ts`; there is no GLB
anywhere in the repo). Rather than skip five tools, the factory was bundled with esbuild and run
in headless Chromium, and the resulting `THREE.Group` was traversed to world space:

* `analysis/stage4/raw/parts_manifest.json` — 108 named parts, 198,912 triangles, model bbox.
* `analysis/stage4/raw/meshes.json` — 108 meshes, 115,344 vertices, world-space positions,
  indices and normals (7.9 MB).

Everything reported below from those two files is measured off the *same factory* that produced
`out/lighting-pass/`, so the numbers describe the build under review, not a proxy.

## Result table

| Tool | Ran? | Headline number / verdict | What it means for this build |
|---|---|---|---|
| `geometry_integrity.py` | yes (library module — no CLI; driven via `measure_geometry_integrity()` in `analysis/stage4/run_gi_full.py`) | **FAIL**, 6 failures, all on two meshes. 198,912 tris vs 250,000 budget = OK. `lodPlanValid: false`. 106/108 meshes watertight (boundaryEdges 0, nonManifoldEdges 0). | Only `Eye cavity L` and `Eye cavity R` are broken, and they are broken three ways at once: `nonManifoldEdges=12`, inconsistent face/vertex normals, and 158 of 862 vertices inside their own surface. Run against the *spec* `componentTree` instead of the built mesh it returns `passed: true` — vacuously, because 103/103 components carry no `vertices`/`indices`/`triangleCount`, so 0 seams and 0 topology checks actually execute. |
| `self_intersection.py` | yes | **FAIL** — `selfIntersecting: true`, 2 of 108 meshes, 14 inside-vertices over 4,308 sampled | `Eye cavity L` / `Eye cavity R`, 7 of 40 sampled vertices each inside their own surface, worst region at `[±0.03, 1.584, 0.062]` — eye height, front of the skull. This is verbatim the defect the module was written for: an eye-socket recess pushed through the surface behind it. At full sampling (via `geometry_integrity`) it is 158/862 = 18.3 % of each cavity's vertices. |
| `pairwise_penetration.py` | yes (two runs, ~5 min each: `pairwise.json`, then `pairwise_named.json` with part names attached) | **FAIL** (`passed: false`) — 1,542 pairs have overlapping bounds, **785 of them penetrate**; median penetration depth 0.0435 m | Mostly by construction, and the gate cannot tell: **no `allowedPairs` are declared anywhere in the project**, while `geometry_integrity`'s own seam contract *requires* 2–5 cm of overlap between adjacent components. Filtering out the 6 whole-limb detail groups (`trouser-pinstripe` alone has a 0.170×0.560×0.169 m bbox, so its "depth" number is a bbox artefact) leaves 410 pairs, headed by `Pelvis`×`Hip sash` 0.123 m, `Scalp cap`×`Hair` 0.088 m, `Boot (her left)`×`Foot L` 0.068 m — garment-over-body, all intended. The one result that corroborates another tool: `Zapper pistol` penetrates `Thigh L` (3/30 samples), `Trouser leg (her left)` (7/30), `Thigh strap` (6/30) and `Glove (her left)` (2/30) — a held item passing through the body it hangs beside, which is exactly the component `attachment_anchor` says has no anchor. |
| `objectness.py` | yes | 0.6123 front (`body_2` vs yaw0), 0.6174 clay front, 0.6016 back | OSIM-lite gradient-structure agreement sits in the low 0.6s at every angle. Consistent with `divine_eye`'s own objectness signal; no angle is an outlier, so this is a uniform shape-detail gap, not one broken view. |
| `check_part_coverage.py` | yes (manifest built from the runtime dump) | **PASS** — 102 specified, 108 built, 0 errors, 0 warnings, 6 notes | The assembly contract holds: every specified component exists as a named, selectable part, nothing is fused, `unnamedMeshes: 0`, and every `detailInventory` entry still resolves. The 6 notes are extra built parts with no spec component (`belt-hardware`, `boot-lacing`, `braid-plait`, `trouser-pinstripe`, `trouser-pinstripe-r`, `Character (root)`) — mild spec drift, not a defect. |
| `diagnose_render_multi_angle.py` | yes | **PASS** — `degenerate: false`; worst orbit ratio 0.8105 at yaw 90 (collapse threshold 0.15) | Nothing in the model is a billboard. The side views hold 81 % of the front silhouette area, which is a real volume. Note this is exactly the check that *cannot* see the depth defect below — 0.81 is well inside its tolerance. |
| `turntable_gate.py` | yes | **FAIL** (`passed: false`) — coverage `covered: true`, `degenerate: false`, but `holed: true` at yaw 0, 90, 180, 270 | Largest enclosed background region: 3,079 px at yaw 90, bbox 31×305 px at y 538–843 (world y 0.11–0.72 m — between the calves), mirrored at yaw 270. Front/back holes are 375–377 px, bbox 6×69 px at world y 1.10–1.24 m — between arm and ribs. **Both locations are declared legitimate negative space in `spec.silhouette.negativeSpaces`** ("between arm and ribs", "between the calves"). So the correct invocation for this subject is `--allow-holes`, under which the gate passes. Recorded as a fail because the flag was not set in the gate's own contract anywhere in the project. |
| `validate_render_profile.py` | N/A — no input exists | Control run on the skill's own `docs/specs/render-profile.v2.example.json`: `passed: true`. Against this project: no `render-profile.v2` artifact exists anywhere in the repo. | This build never authored the v2 browser render profile; it renders through `src/main.ts` + a `tools/render.mjs` the repo no longer contains. Worse, the validator hard-codes `REGION_IDS = (face, kasa, scarf, tunic, staff, tail, feet, materials)` — a different character's regions — so a conforming profile is not authorable for Jinx without editing the tool. |
| `material_gate.py` | yes (no `--in-place`) | **FAIL** — 2 failures: `spec is not wired to materialPipeline`, `no material regions are available for gating` | The spec has no `materialPipeline` block at all, so the blocking material gate has never been able to run in anger. Its embedded compatibility check *did* run and produced the sharpest material finding in the sweep: `referencedMaterialCount: 6` of `materialCount: 20`, warning `materials not referenced by componentTree: [brass, brow, canvas, cloth, glassTank, hairDark, laceMagenta, leather, nailTeal, pantsDark, pupil, sclera, skinShade, steel]`. Also `collisionPresent: false`. |
| `material_comparator.py` | yes, 4 crops | All **PASS**, no mismatches. `deltaE00`: head 3.618, torso 8.182, legs 6.805, whole front figure 7.185. Overall 0.8928 / 0.8135 / 0.9186 / 0.8945. | Colour and tone of the material pass are genuinely close to reference — this is the healthiest signal in the sweep. Weakest sub-score is `directionalResponse` on the head (0.6823): the face is not reacting to light the way the reference does. |
| `material_feedback.py` | yes (`--out`, never `--in-place`) | `hair`: `{"stop": true, "action": "continue", "reason": "fidelity target met, no open defects"}`, empty patch. `torso`: `error: material 'torso' not found in spec` | Working as designed and correctly refusing to invent a patch — because `material_comparator` reported no mismatches there is nothing for it to bound-correct. It only accepts real material ids from `spec.materials`. |
| `material_views.py` | yes | Emitted a 40-view plan for `hair-crest`/`hair` (5 validation views × 8 azimuths), `capturePassed: true`, `environment.required: true` | The camera contract is authorable and valid. `captureValidation` is empty — no browser adapter has ever captured against this plan, so the microscope/grazing evidence `material_gate` wants does not exist. |
| `mesh_reference_compare.py` | N/A — no reference mesh | Actual output when fed the available mesh JSON: `analysis\stage4\raw\meshes.json is not a GLB` | GLB-only, and requires a *reference mesh*. This project's reference is six PNG turnaround panels; there is no ground-truth mesh to compare against and no GLB anywhere in the repo. Its band-by-band proportion analysis was reproduced by hand instead — see defect #1. |
| `per_feature.py` | yes (targets = `spec.featureReviewTargets`, scores = latest per id from `spec.visualEvidence[].featureReviews`) | **FAIL**, `action: refine-code`. 4 of 9 gating/declared features not met. | `face-landmark-placement` **0.12** vs threshold 0.80 (critical), `crest-shape` **0.38** vs 0.80 (critical), `handedness` 0.78 vs 0.80 (critical), plus `x-lacing` and `outfit-and-palette` never scored at all. `braid-contact` 0.82, `contrapposto` 0.92, `anatomy-proportion` 0.88, `pose-silhouette` 0.82 pass. |
| `joint_loops.py` | yes (bones = `spec.rig.bones`, 49) | **GATE FAILURE** — 48/49 joints ok, `shin-r` has **2 loops** where 3 are required | The failure is not topology, it is the rig: `shin-r` runs `jointPos [-0.06, 0.580, 0.006] → tipPos [-0.06, 0.550, 0.006]` = **30 mm long**, against `shin-l`'s 441 mm. Its child `foot-r` starts at y 0.108, i.e. **442 mm below its parent's tip**. The right leg's bone chain is severed. |
| `attachment_anchor.py` | yes | **FAIL** — 4 errors, 4 attachments, 0 unmeasured | All four `zapper` parts (`zapper`, `zapper-tank`, `zapper-barrel`, `zapper-grip`) are marked worn/held/hung and declare no `attachment.anchor` at all: `ANCHOR_DECLARED` fires on every one. The held weapon is parented to nothing that ties it to the hand. |
| `divine_eye.py` | yes, 10 pairs | As shipped: **reject** everywhere, fidelity 0.30–0.33, `silhouette IoU 0.374–0.459`, `scaleDelta 0.462–0.644`. Framing-normalised: fidelity 0.56–0.72, IoU 0.62–0.78, `scaleDelta 0.018` front, 0.076 back, **0.220 side**. | The as-shipped numbers are not measuring the model — see the framing caveat below. On framing-normalised inputs the real picture appears: front silhouette is right (scale delta 1.8 %), back is close (7.6 %), and the **side profile is 22 % too narrow**. `hueZoneParity` is 0.0 on every textured comparison (report-only, not yet in the weighted score). |
| `multi_pass.py` | yes (library module — no CLI; driven from `analysis/stage4/run_lib_tools.py`) | 6 errors — every one of `beauty`, `alpha-silhouette`, `semantic-id`, `depth`, `normal`, `roughness-material-id` is `not recorded` | The v2 browser multi-pass evidence contract is entirely unmet. `out/lighting-pass/` holds beauty-style RGBA frames only, with no manifest, no hashes, and none of the five diagnostic passes. |
| `compare_region_passes.py` | N/A — no GLB capture | Actual output against a manifest built from the existing beauty renders: `{"passed": false, "error": "capture has no GLB reference record"}` | Structurally inapplicable: it compares a browser-rendered GLB against a browser-rendered procedural build, and there is no GLB route here. Per-region scoring additionally needs the `semantic-id` pass, which `multi_pass` just confirmed does not exist. |
| `correction_loop.py` | yes (history built from `spec.reviewHistory`, 5 iterations) | At the spec's own `targetFidelity` 0.70: `{"stop": true, "action": "continue", "reason": "fidelity target met, no open defects"}`. At divine_eye's 0.85: `{"stop": true, "action": "request-input", "reason": "progress plateaued below target"}` | The recorded history is 0.72 → 0.78 → 0.80 → 0.78 → **0.73** — the last two passes went *down*, and `material-pass` recorded **zero** mismatches, which is what makes the 0.70 run return a green "continue". That green is an artefact of an empty defect list, not of a fixed model: every `tier1Results` entry in the same spec is `passed: false`. |

## The framing caveat that invalidates the recorded silhouette numbers

Every silhouette gate in this pipeline routes through `diagnose_render.load_mask()`, which
nearest-neighbour resamples the **whole PNG canvas** onto a 224×224 grid before measuring the
bounding box. It never crops to the subject. The reference panels are tight crops
(`body_2.png` is 377×1299, subject fills 95 % of the frame); the renders are 500×900 with the
subject only 246 px wide. So `aspectRatioDelta` and `scaleDelta` are dominated by canvas padding.

The proof is in the spec itself: across five completed passes — blockout, structural-pass,
proportion-lock, feature-placement, material-pass — `spec.tier1Results[].checks` records
`aspectRatioDelta: 0.4761` and `scaleDelta: 0.4616` **identically, to four decimal places, every
time**, while `silhouetteIoU` wobbles 0.4561–0.4603. A model property does not stay bit-identical
across five rebuilds; a constant framing ratio does.

After cropping both sides to the subject and re-padding to a common 500×900 frame
(`analysis/stage4/norm/`), the front-view scale delta drops from 0.4616 to **0.018** and IoU rises
from 0.423 to **0.749**. Those are the numbers that describe the model.

## The three most actionable defects

**1. The side profile is 20.6 % too shallow, and the figure is 4.2 % too tall.**
On framing-normalised captures `divine_eye` reports `scaleDelta 0.2198` (clay_0 vs yaw 90) and
`0.2111` (body_0 vs yaw 90), against 0.018 for the front — the error is confined to the depth axis.
The runtime bbox confirms it in metres: the built model spans z −0.1485 → +0.1735 = **0.322 m
deep**, where the reference side-view ratio (202/892 of height) implies **0.406 m** at the same
height. Front width is fine — 245 px against the reference's 247, i.e. 99.2 %. Separately the
model measures **1.792 m** tall against `spec.coordinateFrame.scaleReference`'s declared **1.72 m**,
a 72 mm overshoot, with `Foot R` sitting 2 mm below the y=0 ground plane. Jinx is currently a
correctly-proportioned front elevation extruded too thin, scaled 4 % large.

**2. Both eye cavities have folded through the face.**
`self_intersection` flags `Eye cavity L` and `Eye cavity R` and nothing else out of 108 meshes;
at full sampling `geometry_integrity` measures **158 of 862 vertices (18.3 %) inside their own
surface** on each, plus `nonManifoldEdges = 12` and inconsistent face/vertex normals on both.
Worst regions sit at `[±0.03, 1.584, 0.062]` — eye height, front of the skull. Independently,
`per_feature` scores `face-landmark-placement` at **0.12 against a 0.80 critical threshold**, the
lowest score of any feature in the spec, and `material_comparator` finds the head crop's
`directionalResponse` at 0.6823, its weakest sub-metric. Three unrelated tools all point at the
face; the geometry gate says why.

**3. The right leg's rig chain is severed and the held weapon is anchored to nothing.**
`joint_loops` fails `shin-r` with **2 loops against a minimum of 3**, but the loop count is a
symptom: `shin-r` is `[-0.06, 0.580, 0.006] → [-0.06, 0.550, 0.006]`, a **30 mm** bone, against
`shin-l`'s **441 mm** — a 14.7× discrepancy — and its child `foot-r` begins at y 0.108, **442 mm
below its parent's tip**. Nothing connects the right knee to the right foot. In the same family of
defect, `attachment_anchor` returns **4 errors on 4 attachments**: `zapper`, `zapper-tank`,
`zapper-barrel` and `zapper-grip` are all declared worn/held and all declare no
`attachment.anchor`, so the weapon's transform carries no relationship to the hand holding it —
and `pairwise_penetration` shows the consequence, with `Zapper pistol` inside `Thigh L`,
`Trouser leg (her left)`, `Thigh strap` and `Glove (her left)`. Neither defect is visible from the
reference camera, which is precisely why both survived five recorded passes.

## Secondary findings worth recording

* **14 of 20 declared materials are assigned to zero components.** `material_gate`'s compatibility
  check names them: brass, brow, canvas, cloth, glassTank, hairDark, laceMagenta, leather,
  nailTeal, pantsDark, pupil, sclera, skinShade, steel. All 14 have extracted PBR reports in
  `pbr/` and five texture PNGs each in `public/`. `componentTree[].material` uses only skin (50),
  pants (46), hair (3), eye (2), lip (1), tattoo (1).
* **36 components have `material` disagreeing with `materialRef`.** All nine hair/braid components
  carry `material: "pants"` (#54324B plum) with `materialRef: "hair"` (#274E69 blue); `braid-ties`
  is `pants`/`leather`. Which field the factory honours could not be settled from the runtime dump
  — every resolved material returns `#ffffff` with a texture map — so this is recorded as a
  spec-internal contradiction, not a proven render defect.
* **`per_feature` targets and recorded scores only partly overlap.** `x-lacing` and
  `outfit-and-palette` have never been scored; conversely `palette-match`, `material-assignment`,
  `uv-projection` (0.34), `metalness-roughness`, `tone-mapping` and `tattoo-readability` (0.20) are
  scored but are not declared targets, so nothing gates on them.
* **`spec.tier1Results[].checks.colorDelta.perComponent`** carries 103 entries with
  `componentId: null` on every one, max ΔE 41.72 against a 20.0 threshold — the gate knows a
  component is 41 ΔE off and cannot say which.
