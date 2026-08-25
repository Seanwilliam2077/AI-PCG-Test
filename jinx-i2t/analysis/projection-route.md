# Projection route decision

Reference: `grimoire/character/likeness_maximization.md`, steps (b) camera match, (c) de-light,
(d) project and bake.

## Verdict: **projection required — and split into two outputs**

The route the rubric selects for this brief is `character-conditional → maximum likeness`, and
the doc is blunt about why freehand sculpting alone cannot get there:

> Hand-authored primitives can approximate proportions but cannot reproduce the exact geometry
> and surface information encoded in a photo. The two levers that actually move likeness are
> (1) aligning mesh and camera precisely with the photo, and (2) putting the photo's own pixels
> onto that mesh as texture.

That is corroborated independently. The previous reconstruction of this subject took the
freehand-primitive path, was measured every round, and converged at **41.2 / 100** with front-view
silhouette IoU 0.864 — with the largest remaining term being surface detail the model has no
mechanism to carry.

So projection is required to reach the stated goal. But it is not free of consequence:

**Step (d) bakes the artist's own pixels into the model's texture.** The reference is
© Riot Games, modelled and textured by Thibaut Granet. Using it locally as a measurement and
derivation target is one thing; shipping a model whose texture *is* their artwork, transformed,
is redistribution. The public repository already excludes the reference sheets for exactly this
reason.

Therefore this build produces **two outputs from one geometry**:

| output | materials | where it may go |
|---|---|---|
| `jinx-likeness` | projected + baked from the de-lit reference | **local only** — never published, never committed |
| `jinx-procedural` | procedural materials from the measured palette | publishable, as the previous build was |

The geometry, rig and spec are shared. Only the material stage forks. If the user wants the
projected build published, that is their call to make with the rights in hand, not a default.

## Camera match — stronger than the script assumes

`solve_camera_pose.py` states plainly that it emits "a reasonable default guess (FOV) plus
image-derived facts", because a single photo under-constrains the pose. That caveat does not bind
here, and it would be wrong to accept its guess:

The reference is **not a photograph**. It is an orthographic-ish turnaround sheet from a 3D
package. There is no focal length to recover, and the pose is not one unknown but six known ones:

| panel | yaw | how it is known |
|---|---|---|
| `clay_0` / `body_0` | 90° | her left side; the pistol is visible here and absent from `body_4` |
| `clay_1` / `body_1` | 45° (fitted 35° ± 10°) | torso width at two bare-midriff heights |
| `clay_2` / `body_2` | 0° | front |
| `clay_3` / `body_3` | 315° (fitted 310–320°) | torso width fit, residual 3 mm |
| `clay_4` / `body_4` | 270° | her right side; the tattoos are visible here and absent from `body_0` |
| `clay_5` / `body_5` | 180° | back |

`referenceCamera` is therefore authored as `projection: orthographic` with that yaw table, not
solved. Recorded already in `assessment.json → preSpecAssessment.referenceCamera`.

Two corollaries that matter downstream:

- **Six-view projection, not one.** The doc's step (e) — "request an additional view; always try
  this first" — is already satisfied. Every region except true interiors is observed by at least
  one panel, so almost nothing needs mirroring or palette-continuation.
- **An orthographic pair 180° apart carries no extra silhouette information.** The projection of
  a solid along +d and along −d are exact mirrors, for any object. This is why the previous
  build's asymmetry gate read a constant 0.997 for two rounds. For *texture* projection the two
  views are entirely distinct and both are needed — it is only the outline that is degenerate.

## De-lighting — required, with a measured reason

Not optional here, and the cost of skipping it has already been measured on this exact reference:
the material palette was first authored from medians sampled off the *rendered* sheet, which
carries its lighting; lighting those values again put the hair **+14.65 L** too bright once the
global exposure offset was removed. `delight_albedo.py` normalises against a low-frequency
luminance estimate, which is an approximation and is documented as one — it will not remove
specular hotspots or deep occlusion. Regions where it fails get their own confidence entry rather
than being presented as albedo.
