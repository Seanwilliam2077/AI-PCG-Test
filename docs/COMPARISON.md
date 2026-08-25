# Two pipelines, one reference

Both builds target the same thing: a Three.js Jinx measured against Thibaut
Granet's six-panel turnaround. They were built by completely different routes and
scored on the same scoreboard, against the same reference panels, at the same
metric framing.

| | `jinx3js` | `jinx-i2t` |
|---|---|---|
| geometry | signed distance fields, polygonised with naive Surface Nets | primitive assembly from a validated spec: tapered cylinders between joints, ellipsoids elsewhere |
| authoring | hand-written TypeScript SDF operators, tuned by measurement sweeps | `object-sculpt-spec.json`, 103 components, driven through the img2threejs 8-pass ladder |
| surface | procedural, per-part material terms in code | 20 materials, each with albedo/roughness/normal/height/AO extracted from reference pixels |
| rig | none | 49 bones, 49 joint pivots, 98 sockets |
| triangles | 501,068 high / 280,092 medium / 88,628 low | 128,833 near / 66,713 mid / 37,308 far |
| **scoreboard, first complete build** | **41.21 / 100** | 35.35 / 100 |
| **scoreboard, after two iterations** | 41.21 / 100 | **38.68 / 100** |

## Where the points went, first build and after two iterations

The table below is the FIRST complete build, kept because the shape of that gap is what
drove everything afterwards. The current standing follows it.

## Where the 5.86 points went at first build

| term | weight | `jinx3js` | `jinx-i2t` | delta points |
|---|---|---|---|---|
| shape (silhouette IoU) | 0.30 | 0.7051 | 0.7061 | **+0.03** |
| edge F (tolerant) | 0.15 | 0.3833 | 0.3421 | -0.62 |
| contour chamfer | 0.10 | 0.4021 | 0.3787 | -0.23 |
| width profile | 0.20 | 0.2393 | 0.1390 | **-2.01** |
| landmark height | 0.15 | 0.2393 | 0.0655 | **-2.61** |
| region colour | 0.10 | 0.1913 | 0.1488 | -0.43 |

Raw: width RMS 3.13% vs 4.08% of figure height, landmark RMS 2.44% vs 4.76%,
region colour dE 24.87 vs 28.62.

**The two builds are tied on silhouette.** Mean IoU 0.7114 against 0.7086 — a gap
of 0.003 — and the spec-driven build wins three of the six views (yaw 45, 270,
315). Four fifths of the score difference is width profile plus landmark
placement: *where* things sit along the figure, not what its outline is.

## What silhouette IoU cannot see

Put the two geometries side by side with the textures stripped and they are not
remotely the same object. One is sculpted; the other is a mannequin of stacked
primitives with the head floating clear of the neck in profile. Yet the shape term
separates them by 0.001.

Two measurements do see it:

* **Visual hull, carved from the reference's own silhouettes.** Volumetric IoU
  0.6507. 23.9% of the model's hull lies outside the volume the reference
  silhouettes permit (28.1 L), and 18.2% of the reference's hull is unfilled
  (19.9 L) — while the two hulls differ in total volume by only 7.4%. The mass is
  right; its distribution is not. A per-view IoU cannot report this, because a
  silhouette says nothing about how the views must agree in depth.
* **Landmark RMS.** 4.76% against 2.44% — the composite score's largest single
  term gap, and the one the eye reads first.

Both hulls carry the carver's own caveat, worth repeating: a visual hull is the
intersection of silhouette cones, so it is an upper bound and can never contain a
concavity that no supplied view sees as background. With only front and side
panels it also extrudes along the vertical axis.

## What the img2threejs route bought

Things `jinx3js` does not have and would have to grow from scratch:

* **A rig.** 49 bones with pivots at the joints rather than at component centres,
  and 98 sockets. Every joint socket reads back within 0.0 mm of its bone.
* **Measured materials.** Twenty materials with five reference-derived maps each,
  carrying their own extraction confidence and warnings.
* **A budget it can meet.** 128,833 triangles at 51.5% of a declared budget, with
  three LOD tiers each generated and counted rather than estimated.
* **Gates that fail closed.** Strict spec validation, per-pass acceptance criteria
  stated as numbers, and a review ladder that will not unlock the next pass
  without a recorded score.

## What it cost

* **Surface coherence.** Box-projected UVs put a seam at every component boundary.
  This is the largest visual defect and it is structural: the generator emits
  `uvStrategy: "generated procedural coordinates"`, so there is no unwrap to
  improve.
* **The face.** `face-landmark-placement` scores 0.15 against a 0.80 threshold —
  the worst feature in the build, in every pass.
* **Form.** A component with an attachment is a tapered cylinder; a component
  without one is an ellipsoid. There is no third option, so anything that is
  neither gets approximated by one of them.

## Bugs the loop caught that neither the spec nor the validator could

Every one of these passed strict validation. Every one was found by rendering and
measuring.

1. `createJinxArcaneLookDevLights()` returns a `Group`. The harness iterated it
   with `for...of`, which throws; the `catch` swallowed it, so every pass up to
   `material-pass` rendered on a two-light fallback at linear exposure.
2. `scene.environment` was the only part of the studio left in world space while
   every light followed the camera. A uniform-albedo probe measured a six-view L
   spread of **14.38** with it on and **2.19** with it off, against the reference
   sheet's 2.61. Rotating `environmentRotation` with the rig fixed it.
3. **14 of 20 materials were orphaned.** Every component already carried its
   correct assignment in `materialRef`; the generator reads `material`, which had
   been blanket-set to `pants` or `skin`. The whole figure rendered in two colours
   while 70 measured PBR maps sat unused.
4. **15 of 20 PBR crops sampled the wrong pixels.** All five head materials landed
   on bare cheek, `nailTeal` sat 30.4% inside the silhouette, and `eye.png` and
   `sclera.png` were byte-identical. The rects had been hand-placed as panel
   fractions — a guess dressed as a measurement, and silent when wrong, because
   the extractor reports 0.75 confidence on a crop of backdrop just as happily as
   on a crop of skin.
5. **The pinstripe was authored as "the darker pinstripe".** Measured over the
   trouser band, the base median is BGR (71,47,82) and the brightest 3% is
   (106,105,122): the stripe is *lighter* than the cloth.
6. **`shin-r` was 30 mm long** where `shin-l` runs 441 mm, with `foot-r` hanging
   442 mm below its parent's tip.
7. **`renderer.info.render.triangles` reported 400,320 against an actual 202,656.**
   It is a per-frame *rendered* count and accumulates across draw calls.
8. **All 103 components had `pivot.mode: "center"` and no sockets.** A forearm
   whose pivot is its own midpoint bends around a point that is not on the body.
9. **The repetition systems emitted nothing useful.** `appliesTo: "pants-l, pants-r"`
   is prose; the emitter reads `parent`, `placement` and `instanceScale`, so all
   26 pinstripes and 9 buckles piled up at the world origin as 0.1 m cubes
   straddling the floor — which is what put the model's bounding box below y=0.

## Which one is better

For **likeness to this reference**, `jinx3js`: 41.21 against 35.35, and the
untextured comparison is not close.

For **anything that has to be animated, budgeted, or rebuilt from a changed
reference**, `jinx-i2t`: it has a rig, a measured material set, a triangle budget
it meets, and a spec that regenerates the whole model in one command. `jinx3js`
has none of that, and its likeness lives in hand-tuned constants.

They are not really competing at the same thing. The spec-driven route reached
86% of the hand-tuned route's score on its first complete run of the ladder, with
a rig and a material pipeline the hand-tuned route never had — and it did that
while every one of the nine bugs above was live for at least one pass.

## Reproducing

```bash
node tools/render.mjs --out out/optimization-pass --size 500x900
```

```bash
python analysis/hull_compare.py
```

Scoreboard, from the `jinx3js` checkout with these renders copied in:

```bash
python tools/compare.py --tag i2t_final --renders out/i2t_final --pin
```

## Provenance

The reference turnaround is © Riot Games, modelled and textured by Thibaut
Granet. It is used here only as a measurement target. It is excluded from the
repository, and so are the PBR maps extracted from it and any render that
displays them. Comparison imagery published from this build is geometry-only.


---

## After two iterations

Twenty-six gated attempts in the first round and six in the second; eleven accepted.

| term | weight | `jinx3js` | `jinx-i2t` first | `jinx-i2t` now | gained | remaining gap |
|---|---|---|---|---|---|---|
| shape, silhouette IoU | 0.30 | 0.7051 | 0.7061 | **0.7208** | +0.44 | −0.47 *(i2t leads)* |
| edge F, tolerant | 0.15 | 0.3833 | 0.3421 | **0.4157** | +1.10 | −0.49 *(i2t leads)* |
| contour chamfer | 0.10 | 0.4021 | 0.3787 | **0.4248** | +0.46 | −0.23 *(i2t leads)* |
| width profile | 0.20 | 0.2393 | 0.1390 | 0.1814 | +0.85 | +1.16 |
| landmark height | 0.15 | 0.2393 | 0.0655 | 0.0587 | −0.10 | +2.71 |
| region colour | 0.10 | 0.1913 | 0.1488 | **0.2065** | +0.58 | −0.15 *(i2t leads)* |
| **total** | | **41.21** | **35.35** | **38.68** | **+3.33** | **+2.53** |

Raw: silhouette IoU **0.7249** against 0.7114 — the spec-driven build now leads outright
on the single heaviest term. Width RMS 3.58 % against 3.13 %; landmark RMS 4.53 % against
2.44 %.

**The gap closed by 57 %, and what is left is one term.** Landmark placement alone is
worth 2.71 of the remaining 2.53 points; every other term is at or ahead of the
hand-authored build. That term resisted three separate attempts, and the reason is
recorded in [../METHOD.md](../METHOD.md) §6: the detector written to chase it asked for
the knee to drop 60 mm and the calf to rise 60 mm in the same pass, and the calf is below
the knee.

What finally moved it was giving up on our own ruler and warping the figure through the
independent judge's landmark table instead, damped per landmark by how many of the six
views actually saw it. The most corroborated landmark, the hip, went from +4.25 % to
+1.68 % of figure height.
