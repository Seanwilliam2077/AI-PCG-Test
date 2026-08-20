# Viewer and headless renderer

The viewer is the other half of the loop the parts are authored against: it is
the thing that turns `src/generated/lod_*.ts` back into pixels, and
`tools/render.mjs` is what feeds `tools/compare.py`. Everything here is built so
that two renders taken a week apart differ **only** because the geometry
changed.

```
npm run dev        # http://127.0.0.1:5173  -- interactive page
npm run build      # dist/
npm run render     # == node tools/render.mjs
npx tsc --noEmit   # typecheck
```

Owned files: `index.html`, `vite.config.ts`, `src/viewer/*`, `tools/render.mjs`,
this document.

---

## 1. The page

A gallery-detail layout: a fixed 480 px panel on the left carrying the entry
metadata (eyebrow, title, byline, the `ref/views/body_2.png` source thumbnail,
tags including the live triangle count, and a description), and the 3D viewport
filling everything to its right.

**Viewport controls** (bottom-right cluster):

| Group | What it does |
| --- | --- |
| Level of detail | Switches between the LODs that are actually present in `src/generated`. A LOD that has not been baked is simply not offered. |
| Display | `Wireframe` (also flips to double-sided so the far shell reads), `Turntable` (orbits the camera about the framing centre at 0.45 rad/s). |
| Canonical views | Jumps the camera to yaw 0/45/90/135/180/270 and re-derives the frustum. |

Mouse: left-drag orbits, right-drag pans, wheel zooms (`OrbitControls` driving
an orthographic camera, so the wheel changes `camera.zoom`, not distance).

### Narrow windows

The panel is a fixed pixel width, so it has to be told to stop competing with
the canvas. It steps down 480 → 400 → 340 px at 1180 px and 1000 px, and below
**820 px the layout stacks**: the 3D view takes the top of the page at `62vh`
(min 320 px) and the detail text scrolls underneath it. Measured canvas sizes,
no horizontal scroll at any of them:

| window | canvas | panel |
| --- | --- | --- |
| 1600 x 1000 | 1120 x 1000 | 480 |
| 1280 x 800 | 800 x 800 | 480 |
| 1024 x 720 | 624 x 720 | 400 |
| 900 x 640 | 560 x 640 | 340 |
| 760 x 900 | 760 x 557 | stacked |
| 420 x 780 | 420 x 483 | stacked |

The viewport sizes itself from `stage.clientWidth/Height` under a
`ResizeObserver`, so the camera frustum re-derives on every one of those
transitions without a reload.

### Materials

Every encoded geometry group carries a *material name* that is a key of
`spec.materials`. `src/viewer/materials.ts` memoises one Three material per name
and hands `Mesh` the array in group order — `decodeMesh` already numbers each
geometry group with its own index, so group *i* draws with
`groups[i].material`.

**The spec's colour table is sRGB, not linear.** The numbers were authored by
eye against the reference sheets, so they are display values and are decoded
with `Color.setRGB(r, g, b, SRGBColorSpace)`. Note that `src/mesh/format.ts`
still documents `MaterialSpec.color` as linear — that comment is wrong and the
spec is the authority. Reading the table as linear is not a subtle error:
`skin` `[0.913, 0.784, 0.706]` taken as linear is very nearly white, and the
whole figure renders as paper with the hair pale cyan, the trousers bright pink
and the boots tan.

A material that declares `sheen` or `transmission` is built as a
`MeshPhysicalMaterial` (which *is* a `MeshStandardMaterial`); `sheen` becomes a
restrained rim tint at `sheen = 0.55`, `sheenRoughness = 0.45`.

### Lighting

Nothing casts a shadow: the reference sheets have no contact shadow, and a
ground shadow would corrupt the silhouette matte `tools/compare.py` scores.
Beyond that, three decisions, all of them measured rather than eyeballed — see
§5 for the numbers.

**The rig turns with the camera.** A `Group` parented to the framing centre and
yawed to follow the camera holds the key/fill/rim, all aimed at a shared target
at the group's origin. Only the yaw follows; pitch stays put, so orbiting up and
down still changes the modelling. The reason is in the reference: its six panels
measure within 2.6 L of each other (mean 34.2–36.8, p10 12.3–13.6, p90
70.4–74.7), i.e. the artist spun the model inside a fixed studio. A world-fixed
rig does the opposite — measured at yaw 90 it put the key behind the subject and
the panel came out at mean 13.8 against the front's 26.9, which makes the panels
incomparable and the colour term meaningless.

**The indirect term is a PMREM of `RoomEnvironment`.** Procedural, so nothing is
fetched, and `fromScene` is deterministic for a fixed renderer. This is not
decoration: with no `envMap`, `RE_IndirectSpecular` contributes nothing, and
every dark material renders as flat dead albedo. Cloth sits at 0.0097 linear
reflectance — no amount of key light makes it read — and what actually lifts it
is the 4 % Fresnel floor every dielectric has, which needs an environment to
reflect. Adding the IBL moved p10 from 2.1 to 17.6 in one step.

**Tone mapping is `NeutralToneMapping`, not ACES.** ACES crushes the bottom
hard: scene-linear 0.01 leaves the tone mapper at 0.0024, so with these albedos
the shadow end fell to L 2 while lit skin sat at 76 — a range no exposure change
could close, because ACES compresses top and bottom together. Khronos PBR
Neutral leaves mid-tones essentially untouched and rolls off only the
highlights, which both matches the reference's near-albedo look and preserves
hue and saturation for the scoreboard's Lab comparison. `outputColorSpace` is
`SRGBColorSpace`.

The backdrop is a radial gradient drawn to a canvas and used as
`scene.background`, so it is part of the rendered buffer (which is what makes
`bg=dark` work in a PNG) rather than a CSS layer behind a transparent canvas.

---

## 2. URL parameters

| Param | Values | Default | Meaning |
| --- | --- | --- | --- |
| `shot` | `1` | off | Offscreen mode: hide all chrome, exact canvas size, render one frame, publish the hooks below. |
| `yaw` | degrees, any real number | `0` | Camera yaw about Y. **Yaw 0 puts the camera on +Z**, which the part contract defines as the character's front. Increasing yaw walks the camera from +Z toward +X (her left). |
| `lod` | `high` \| `medium` \| `low` | `high` in shot mode, `low` otherwise | Which baked LOD to load. If it is not baked the viewer falls back to the finest one that is, and reports both names in `window.__INFO__`. |
| `w`, `h` | pixels | `900`, `1500` | Drawing-buffer size in shot mode. Pixel ratio is forced to 1, so these are the exact PNG dimensions. |
| `bg` | `transparent` \| `dark` | `dark` | `transparent` sets clear alpha 0 and drops the backdrop, giving a matte you can composite or measure coverage on. |
| `expose` | stops, signed | `0` | Exposure trim on top of `BASE_EXPOSURE`. **For iterating only** — a render taken at a non-zero trim is not comparable with the calibrated band. Fold a result you like back into `BASE_EXPOSURE` in `src/viewer/main.ts`. |

Example:

```
http://127.0.0.1:5173/?shot=1&yaw=45&lod=low&w=600&h=1000&bg=transparent&expose=-0.5
```

### Shot-mode hooks

The WebGL context is always created with `preserveDrawingBuffer: true`, so
read-back after the frame is legal.

| Global | Type | Notes |
| --- | --- | --- |
| `window.__READY__` | `boolean` | `true` once the first frame is on screen. Also set on failure — check `__ERROR__`. |
| `window.__SHOT__()` | `() => string` | PNG data URL of the current drawing buffer. |
| `window.__VIEW__(yawDeg)` | `(number) => void` | Re-aims and renders one frame **without a reload**, so a turnaround costs one WebGL context instead of N. |
| `window.__INFO__` | object | `{ requestedLod, lod, lods, triangles, width, height, background, exposure, exposeStops, frustumHeight, center }`. |
| `window.__ERROR__` | `string?` | Set if boot threw, so a driver can fail loudly rather than writing an empty PNG. |

---

## 3. How framing is derived

Implemented in `src/viewer/camera.ts`. Three decisions, all in service of
comparability:

**Orthographic, always.** A perspective camera changes the foreshortening of the
legs as the camera walks around the figure, so panel *n* and panel *n+1* of a
turnaround are not the same projection of the same body. Any silhouette IoU
measured against a flat reference sheet then bakes that error in. Orthographic
removes the variable.

**The camera lives on a circle about Y.** For yaw θ,

```
dir      = ( sin θ, 0, cos θ )         # θ = 0  ->  ( 0, 0, 1 ), the front
position = center + dir * (radius * 3 + 1)
lookAt(center)                          # up = +Y
```

Distance is irrelevant to an orthographic projection; it only has to clear the
model, hence the `radius * 3 + 1`. Near/far are derived from the same radius.

**The frustum is fitted to the world bounding box.**

```
box    = Box3().setFromObject(model)   # whatever is actually baked
center = box.center
height = box.size.y
top / bottom = ± height * 1.06 / 2     # FRAME_PAD = 1.06
left / right = ± height * 1.06 * aspect / 2
```

The consequence that matters: **the vertical scale never depends on what has
been baked.** A body-only bake and a fully dressed one both put the figure at
the same fraction of frame height, so a render from before the boots landed is
still comparable with one from after. Horizontal extent follows from the
viewport aspect alone, so an image is only ever cropped or letterboxed
sideways — the vertical scale is invariant.

Two things to know about that:

- The frame is centred on the **bounding-box** centre, not on the skeleton. A
  stray blob from a half-finished part (a mesher artefact 40 cm in front of the
  face, say) drags the centre toward it and the figure shifts off-centre. That
  is intended — it makes the artefact obvious instead of hiding it — but if a
  turnaround suddenly looks off-axis, check `out/bake_report.json` and the
  `center` field of `window.__INFO__` before blaming the camera.
- `FRAME_PAD` is the *only* magic number in the framing path. If the reference
  panels turn out to be cropped tighter or looser, change it in one place
  (`src/viewer/camera.ts`) and every render moves together.

---

## 4. `tools/render.mjs`

```bash
node tools/render.mjs                          # 8 yaws, lod high, 900x1500, transparent
node tools/render.mjs --lod low --size 600x1000
node tools/render.mjs --yaw 0,45,90 --out out/views
node tools/render.mjs --expose -0.5            # exposure trim, in stops
node tools/render.mjs --bg dark --no-build     # reuse an existing dist/
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--yaw` | `0,45,90,135,180,225,270,315` | Comma-separated yaws in degrees. |
| `--lod` | `high` | Passed straight through; the page falls back and the script warns. |
| `--size` | `900x1500` | `<w>x<h>`, the exact PNG size. |
| `--out` | `out/views` | Output directory; files are `render_yaw<deg>.png`. |
| `--bg` | `transparent` | `transparent` or `dark`. |
| `--expose` | none | Exposure trim in stops. Iteration only — see the `expose` param above. |
| `--no-build` | off | Skip `vite build` if `dist/index.html` already exists. |

**Why 8 yaws by default.** The reference turnaround has 6 panels and their exact
angles are not known yet — `tools/compare.py` fits the mapping. Rendering every
45° gives that fit a superset to choose from. Once the mapping is pinned, pass
`--yaw` with the 6 that matter.

**How it runs.** `vite build`, then an in-process `http.createServer` over
`dist/` on an ephemeral port, then Playwright Chromium against
`http://127.0.0.1:<port>/?shot=1&...`. Chromium is launched with
`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader` because
there is no GPU in a headless run and Chrome has refused WebGL on SwiftShader by
default since 119. The page is loaded **once**; subsequent yaws go through
`window.__VIEW__`, since creating a SwiftShader context per view dominates the
runtime.

**Blank-render detection.** A failed WebGL context does not throw — it produces a
perfectly transparent or perfectly uniform buffer, which would silently poison
the scoreboard. So every frame is measured in-page before it is written:

```
render_yaw45.png       400x680     122 kB  opaque  23.87%  L mean  30.7  p10   3.9  p50  20.0  p90  74.5
```

`opaque` is the fraction of pixels with alpha > 8. A frame is rejected — not
written, and the run exits non-zero — if fewer than 0.5 % of pixels are opaque,
if the whole image quantises to fewer than 3 distinct colours, or (on a dark
background) if mean luminance is essentially zero. The canvas size is checked
against the request too, so a silently clamped buffer cannot slip through.

Sanity band: a full-height figure at a 0.6 aspect frame covers roughly
**10–25 %** of the image — narrow at a side view, widest at front and back.
Anything at 0 % or 100 % is a bug, not a pose.

---

## 5. Colour calibration

`L mean / p10 / p50 / p90` on each line is **CIE L\* over the alpha** — pixels
with alpha > 128, so half-covered edge pixels do not drag the distribution down.
That is the axis the scoreboard's colour term lives on, so the run prints a
summary against the reference band at the end.

### The reference

All six panels, measured the same way:

| panel | L mean | p10 | p50 | p90 |
| --- | --- | --- | --- | --- |
| `body_0` | 34.3 | 12.5 | 27.3 | 74.6 |
| `body_1` | 35.8 | 13.2 | 30.5 | 73.5 |
| `body_2` | 36.7 | 12.3 | 28.5 | 74.7 |
| `body_3` | 36.8 | 12.8 | 29.2 | 74.1 |
| `body_4` | 34.5 | 12.6 | 27.8 | 70.4 |
| `body_5` | 34.2 | 13.6 | 28.4 | 71.4 |

### Where the render lands

`node tools/render.mjs --lod low --size 400x680`, 83.7 k tris, `BASE_EXPOSURE
0.41`:

| yaw | L mean | p10 | p50 | p90 |
| --- | --- | --- | --- | --- |
| 0 | 32.9 | 3.6 | 20.3 | 76.1 |
| 45 | 30.7 | 3.9 | 20.0 | 74.5 |
| 90 | 27.0 | 3.3 | 16.7 | 64.2 |
| 135 | 25.1 | 3.3 | 15.0 | 61.2 |
| 180 | 25.3 | 3.5 | 16.1 | 58.5 |
| 225 | 25.3 | 4.1 | 15.4 | 57.2 |
| 270 | 27.7 | 4.9 | 17.3 | 62.1 |
| 315 | 29.9 | 3.5 | 18.5 | 71.2 |
| **mean of 8** | **28.0** | **3.8** | — | **65.6** |

Front view against `body_2`: mean 32.9 vs 36.7, p90 76.1 vs 74.7, p10 3.6 vs
12.3.

### How `BASE_EXPOSURE` was chosen

Exposure was scanned from −2.4 to +0.2 stops and scored as the mean absolute
difference over the 19 quantiles p5…p95 against `body_2`. The curve has a flat
minimum at −1.05 stops (mean |ΔL| 5.91, max |ΔL| 9.5), which is folded into
`BASE_EXPOSURE = 0.41`. That setting also puts front p90 (76.1) inside the
72–78 band.

Per-region spot checks at that exposure, sampled at matched silhouette-relative
coordinates, are what actually matter for a per-region Lab comparison:

| region | reference L | render L | Δ |
| --- | --- | --- | --- |
| midriff skin | 78.4 | 77.9 | −0.4 |
| upper-arm skin | 77.4 | 78.7 | +1.4 |
| hair | 41.1 | 39.8 | −1.4 |
| face skin | 57.5 | 60.4 | +2.9 |
| boot | 15.3 | 18.6 | +3.3 |
| shin skin | 52.8 | 58.5 | +5.7 |

The large-area skin regions sit within 3 L of the reference, which is the result
the colour term cares about.

### The residual, and why it is not an exposure problem

The requested band (mean 36–38 **and** p10 12–16 **and** p90 72–78) is not
reachable with the current material table, and the reason is measurable rather
than a matter of tuning.

A grid over key / fill / rim / ambient / env intensity — 64 rigs, each with
exposure solved so that `mean == 36.7` — produces the *same* histogram every
time: p10 ≈ 5, p25 ≈ 12.5, p50 ≈ 24, p90 ≈ 82.5, varying by less than 1 L across
the whole grid. Normalising on p90 = 75 instead gives p10 ≈ 3.5, mean ≈ 32 for
every rig. **The rig has essentially no influence on the distribution's shape.**

What sets the shape is the albedo spread of the material table. Rendered flat,
the spec's own colours span

```
cloth  L  8.5      pantsDark L 15.3    leather L 19.3    pants L 28.3
hair   L 46.6      canvas    L 48.3    skin    L 82.8
```

— a range of 74 L from `cloth` to `skin`. The reference's range from p10 to p90
is 62 L. So the render cannot be simultaneously as bright in the mean and as
tight in spread as the reference: hitting the mean pushes p90 to ~82, and
hitting p90 pulls the mean to ~32.

The specific culprit is the dark end. The reference's darkest decile sits at
L 12.3, which corresponds to an albedo of about L 20 under this lighting —
`leather` or `pantsDark` territory. The spec's `cloth` at L 8.5 is well below
that, and it covers a large area (top, gloves, and much of the pants at low
LOD), so it dominates the render's bottom decile in a way it does not dominate
the reference's. In the sheet, the black fabric is painted with visible sheen
and weave detail and reads far lighter than a flat 0.098 grey.

Two things would close it, neither of them viewer-side:

1. Lift `cloth` (and `pantsDark`, `brow`, `pupil`) in `spec/jinx.json` toward
   what the sheet actually measures — the black top reads around L 20–33 there,
   not 8.5.
2. Give the fabric materials a `sheen` entry. `MaterialSpec` already supports
   it and `src/viewer/materials.ts` already honours it; only `hair` declares one
   today.

If you would rather have the mean in band and accept blown highlights, the
single change is `BASE_EXPOSURE = 0.505` in `src/viewer/main.ts` — that gives
front-view mean 36.7, p10 5.1, p90 82.5, and a worse quantile fit (mean |ΔL|
6.33, max 14.4).
