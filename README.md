# jinx3js — a Three.js character with no assets

Arcane's Jinx, rebuilt to match [Thibaut Granet's character
turnaround](https://thibaut_granet.artstation.com/projects/X1aWVw) as closely as
measurement allows, using the technique the brief named: **procedural TypeScript
Surface Nets**. There is no mesh file, no texture, and no material library. The
character is a signed distance field written in TypeScript, meshed at build
time, and shipped as base64 typed arrays inside `.ts` files.

## How it is put together

```
spec/jinx.json          every number the character is made of
spec/parts/*.json       per-author overlays, merged into spec/resolved.json
src/sdf/                primitives, booleans, transforms, swept curves
src/mesh/surfacenets.ts the mesher
src/parts/*.ts          one file per part: body, head, hair, top, pants, boots…
src/scene.ts            the part registry
tools/bake.ts           field -> mesh -> encoded TypeScript
src/viewer/             the Three.js page
tools/render.mjs        headless Chromium turnaround renders
tools/preview.ts        a dependency-free software rasteriser
tools/compare.py        the scoreboard against the reference
ref/                    the reference sheets and the per-view panels cut from them
```

### Fields, not meshes

Every part returns **shells** — closed surfaces — rather than one merged blob.
A garment is its own shell sitting just outside the skin, which is both cheaper
(the boots do not pay for the head's voxel size) and truer: cloth is a separate
surface, not a bump on a body. Blending with `smoothUnion` happens *inside* a
shell only.

Each field carries its own bounds and a **Lipschitz bound** — how badly it
under-estimates true distance, which smooth operators and non-uniform scale
both do. The mesher divides by that bound before trusting a value, which is what
lets it skip empty space honestly instead of by guesswork.

### The mesher

Naive Surface Nets: one vertex per sign-changing cell placed at the mean of the
cell's edge crossings, quads emitted around every sign-changing grid edge. On
organic shapes it gives evenly sized quads and, unlike marching cubes, has no
ambiguous cases.

The grid is sampled a z-layer at a time, and each layer in blocks: one probe at
the block centre, and if the Lipschitz-corrected value clears the block's
half-diagonal the whole block is filled with that sign without another
evaluation. On a character that skips most of the volume, which is what makes a
3.5 mm voxel affordable in plain TypeScript with no GPU and no WASM.

### Shipping as code

Positions are quantised to 16 bits inside each mesh's own bounds (a 28 µm step
at this scale), normals to 8 bits, and every buffer is deflated before base64.
The index buffer of a Surface Nets mesh is extremely regular and compresses
about 4:1 — without that step a high LOD is tens of megabytes of base64 and
"ships as code" stops being a real claim. The browser inflates with
`DecompressionStream`.

## The review loop

Likeness is not asserted, it is measured.

1. `tools/fetch_ref.mjs` pulls the artist's sheets. ArtStation is behind a
   Cloudflare challenge that plain HTTP clients cannot pass, so this drives a
   real Chromium and reuses the page's cookies for the asset downloads.
2. `tools/slice_ref.py` cuts each sheet into per-view panels with an alpha
   matte. The backdrop is not flat — it carries a soft elliptical spotlight that
   is *contiguous with the figure*, and a contact shadow painted between the
   legs — so thresholding does not work. The backdrop is flooded inward from the
   image border through a gradient barrier, and pockets the flood cannot reach
   are classified by chromaticity: a shadow keeps the backdrop's hue and only
   loses luminance, a braid does not.
3. `tools/bake.ts` meshes; `tools/render.mjs` (browser) or `tools/preview.ts`
   (software) renders a turnaround.
4. `tools/compare.py` scores render against reference — silhouette IoU, contour
   Chamfer, tolerant edge F, a width profile at 40 heights, landmark positions,
   and per-region colour — and says *where* and *by how much*, because that is
   what a fix needs.

Renders for measurement use `--frame <metres>`, which fixes pixels-per-metre
rather than fitting the bounding box. A bbox fit is useless while the model is
half-built: adding the hair would rescale everything, and every earlier
measurement with it.

See `docs/MEASUREMENTS.md` for what has been measured off the reference and what
the numbers cost. Round 1 on the bare body went from **+59 % at the shoulder** to
a mean absolute width error of **2.7 %**.

## Working in parallel

Several authors sculpt at once. Three things keep them out of each other's way:

- one part, one file, and nobody edits `src/sdf`, `src/mesh`, `src/scene.ts` or
  another author's part;
- `spec/parts/<id>.json` fragments merged into `spec/resolved.json`, so nobody
  rewrites the shared spec;
- `tools/bake.ts --gen out/gen_<id>`, so nobody clobbers `src/generated`.

`tools/preview.ts` exists so an author can *look* at their work every iteration
without a GPU, a build step or a browser. It is also a second opinion: if a
shape is wrong in both renderers the field is wrong; if it is wrong in only one,
the renderer is.

## Running it

```bash
npm install
npx playwright install chromium

npx tsx tools/bake.ts                 # all three LODs into src/generated
npm run dev                           # the viewer

node tools/render.mjs --lod high      # turnaround PNGs into out/views
python tools/compare.py --tag r1      # the scoreboard
```

Fast loop while sculpting one part:

```bash
npx tsx tools/bake.ts --lod low --only hair --gen out/gen_hair
npx tsx tools/preview.ts --lod low --gen out/gen_hair --yaw 0,90,180 --frame 1.80
```

## Credit

The reference turnaround is © Riot Games, modelled and textured by Thibaut
Granet, and is used here only as a measurement target — it is not redistributed
and none of its pixels end up in the model. Jinx and Arcane are Riot Games
property; this is a fan reconstruction of the *form*, built from code.

## What the loop actually caught

Worth writing down, because none of these were visible by looking at the model
and several were wrong the *other* way from how they looked.

**A sign error in `smoothSubtract` deleted the entire skull.** The formula used
`A − B` where it needed `A + B`, so the first head bake produced two eyeballs
floating above a slab. The test that would have caught it in a line: as the
blend radius goes to zero the operator must collapse to `max(A, −B)`.

**Stacking capsule sections with `smoothUnion` inflates the whole surface.** At
almost every point two or three sections report nearly the same distance, `smin`
subtracts up to `k` each time, and the fixed point of that over a long stack is
a full `k` of radius everywhere — measured at +13 mm of half-width at every
height. That is what welded the arms to the ribs, filled in the waist, and grew
a 137 mm ball at the throat that swallowed the choker whole. Rebuilding the
trunk as one lofted-ellipse field fixed all four at once, and only then did the
real error appear: the torso was 29–38 % too shallow, which the inflation had
been hiding.

**The braids were never too thick — they were hanging in the air.** The
scoreboard's braid-mass metric read 3× the reference, which reads as "too fat".
Measured row by row, the braid's own width matched to a millimetre; what was
wrong was standoff. The reference's silhouette is one run from the hips to the
crown because the rope lies *on* the back; ours split into body-gap-braid at
almost every height. The fix was to ray-march the assembled body's rearmost
surface and set the braid's depth column from it.

**Two of the scoreboard's own tests were measuring nothing.** The renderer is
orthographic by design, and under orthographic projection the silhouette of any
solid seen from +d and from −d are exact mirrors — so the "is the model
laterally symmetric" test read 0.997 for every model, forever. It was verified
directly: adding the pistol put 1924 px into the yaw 90 silhouette and *the
identical 1924 px* into yaw 270. Two rounds were steered off that number before
an adversarial pass caught it. The replacement flips a single view against
itself, which is not degenerate: reference 0.754, render 0.874.

The second was worse because it came from a bad measurement of the reference. A
"the boots merge at the floor" finding turned out to be an artefact — the
reference has *one* silhouette run at the floor, because she stands with one
foot 47 mm above the other. An author spent a round chasing it and made the
boots worse.

**The pose was the thing.** Her left foot sits 2.74 % of figure height above her
right. A symmetric skeleton cannot fit that turnaround at all: the two side
panels are genuinely different shapes (the reference's own mirror IoU is 0.65)
while an orthographic render of a symmetric model produces two exactly mirrored
silhouettes, so at best one of the two views can ever fit. And when the
contrapposto was finally added it did not reach the feet, because `body.ts` was
building them from an absolute floor height instead of from the ankle joint —
a 47 mm lift came out as 6 mm.

**A per-view luminance spread caught a geometry error that silhouette IoU could
not see.** The reference's six panels sit within 2.6 L of each other; ours spanned
10.0 L with the back 6.9 L dark. It was not lighting — the rig turns with the
camera, and flattening it moved the spread 0.3 L. It was hair covering skin the
reference leaves bare, *inside* the silhouette where IoU is blind.

### What the score cannot see

The colour term sits near a structural ceiling. Mean per-region deltas are small
once exposure is accounted for, but per-pixel ΔE stays at 18–30 because the
reference is a painted texture — weave, dirt, seams, freckles, a specular
highlight in the eye — and this model has no textures at all. Read `dL_rel` and
the hue columns; treat ΔE as a ceiling.

The same caution applies to the silhouette. Measured against the artist's own
mattes, IoU 0.97 is the hard ceiling: that is what one pixel of genuinely
ambiguous matte boundary costs. Treat 0.95 as "as good as this instrument can
see" and read the width, landmark and colour tables past that point.
