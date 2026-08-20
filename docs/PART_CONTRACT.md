# Part contract

Read this before touching anything under `src/parts/`.

## Goal

Rebuild Thibaut Granet's Arcane Jinx as a code-only Three.js character: a signed
distance field authored in TypeScript, meshed with Surface Nets at three LODs,
baked into `src/generated/lod_*.ts` as encoded typed arrays, and drawn by a
viewer that loads no assets. Likeness is measured against the artist's own
turnaround, sliced into `ref/views/`.

## Frame and units

Metres. **Y up.** Origin on the floor midway between the feet. The character
faces **+Z**, so a default Three.js camera on +Z sees her front.

**+X is her LEFT**, which is screen-right in the front view.

**Read `docs/HANDEDNESS.md` before placing anything asymmetric.** The first
version of this section had two features on the wrong side. Verified off the
front panel at 3x:

| feature | her side | axis | front-view image side |
|---|---|---|---|
| cloud tattoos | right | **−X** | left |
| Zapper pistol | left | **+X** | right |
| black arm bands | left | **+X** | right |
| sash low corner | right | **−X** | left |

The tattooed arm is the bare one; the banded arm is the clean one. They are on
opposite sides.

That file also records the reference panel to camera-yaw mapping, which is
**knowledge, not a fit** — front and back silhouettes of this figure differ by
about 0.01 IoU, so a scoreboard fit cannot resolve it.

## Files you own

One part, one file. Never edit another part's file, `src/scene.ts`,
`src/spec.ts`, `src/sdf/*`, or `src/mesh/*` — other authors are working in the
same checkout. If you need a new SDF operator, say so in your report instead of
adding it.

**Never edit `spec/jinx.json` or `spec/resolved.json`.** You own exactly one
spec fragment, `spec/parts/<your-part>.json`, holding only your own top-level
key:

```json
{ "hair": { "braidR0": 0.030, "braidTurns": 26 } }
```

`tools/merge_spec.ts` folds every fragment onto the base into
`spec/resolved.json`, which is what `src/spec.ts` imports; the bake runs the
merge itself, so your numbers are live in the same command that meshes your
shell. Never change `landmarks`, `widths` or `pose` — they are measured off the
reference and everything is authored against them. If you believe one is wrong,
report it with the measurement rather than editing it.

## What a part returns

```ts
import { PartModule, Shell, constMaterial } from './types.js';

export const hairPart: PartModule = {
  id: 'hair',
  build(ctx) {
    const { spec, skel, mat } = ctx;
    return [{ name: 'hair', field, material: constMaterial(mat.hair), voxelScale: 1 }];
  },
};
```

- `ctx.spec` — the parsed `spec/jinx.json`.
- `ctx.skel` — resolved joint positions (`skel.wristL`, `skel.kneeR`, …), see
  `src/spec.ts`.
- `ctx.mat` — material name to index, e.g. `mat.leather`. Names are the keys of
  `spec.materials`; add a material there if you genuinely need a new one.
- `voxelScale` multiplies the LOD voxel for that shell: `0.5` for the face,
  `1.6` for boot soles. Use it — it is the whole budget lever.

Return **one shell per closed surface**. Clothing is a separate shell from the
skin, not a bump on it. Blending with `smoothUnion` happens *inside* a shell
only.

## Building fields

`src/sdf/ops.ts` — `sphere ellipsoid roundBox capsule capsuleOval cylinder
torus halfSpace`, `union smoothUnion subtract smoothSubtract intersect
smoothIntersect shell offset`, `translate rotateX/Y/Z scale mirrorX transform
displace`.

`src/sdf/curve.ts` — `tube braid strap lacing orientedBox catmullRom
resample frameAt`. The braids, belt runs, choker wraps and boot laces are all
curves; use these rather than open-coding capsule chains.

`src/sdf/solids.ts` — `revolveY profileBox profileUnion loftY repeatAngularY
repeatLinear twistY elongate cut cutSoft rotateAbout`. Reach for these before
stacking capsules by hand:

- a boot sole, a gun barrel, a buckle, a belt eyelet are all **lathes**
  (`revolveY` with `profileBox`/`profileUnion`);
- a trouser leg, a sleeve, a braid envelope is a **loft** (`loftY`, which
  samples a half-width/half-depth function every ~12 mm — sample finely or you
  get a visible ring at every joint);
- a boot tread, a revolver chamber, eyelets round a cuff are **angular
  repeats** (`repeatAngularY`); rivets and lace rows are `repeatLinear`.

## Four traps that cost the first round real time

**1. Cutting has a sign, and getting it wrong fails silently.** `intersect` is a
`max`, so a cut plane must be **negative on the side you keep**. Writing
`y - hemY` the natural way round gives a shell with zero triangles and no
diagnostic beyond "produced no geometry". Use `cut(field, 1, hemY, 'below')`
from `solids.ts` — it takes the side as a word and shrinks the bounds, which
`halfSpace` does not.

**2. `nearestMaterial` is for materials *beside* each other, never *stacked*.**
It picks the tagged field with the smallest SDF, so when a canvas panel lies on
top of a wrap, every point on the panel's surface is deep inside the wrap and
the wrap wins — the panel comes out the wrong colour. For layers, chain
`paint()` calls outermost last.

**3. `shell(f, t)` is a trap at coarse LODs.** The reference cloth is 10–14 mm;
at the low LOD's voxel that is under one sample and Surface Nets returns a chain
of blobs rather than a wall. Author garments as **solids whose outer surface is
the cloth**, and let the body sit inside.

**4. `transform()` rotates about the *world* axes**, in X-then-Y-then-Z order, so
"spin this about its own barrel" is not expressible with it. Use
`rotateAbout(field, axis, angle, pivot)`.

A fifth, for free: a part that fails to **import** used to kill the bake for
every author at once. `src/scene.ts` now loads parts dynamically with a
try/catch each, so a broken part costs only its own shells and the bake reports
it. You still cannot break another author's file, but you can no longer block
them.

They are also cheaper to evaluate and they keep the Lipschitz bound right,
which a hand-rolled pile of primitives usually does not.

Two rules that keep the mesher fast:

1. **Keep bounds tight.** Every constructor propagates `bounds`; if you write a
   raw `field(...)` give it real bounds, not the whole body.
2. **Keep `lip` honest.** It is a bound on the field's gradient magnitude. The
   mesher skips a block when `|f| / lip` exceeds the block radius, so a field
   that claims `lip: 1` while actually varying faster than distance will punch
   holes in the mesh. `smoothUnion` and `scale` already account for themselves.

Symptom of a wrong `lip`: speckled holes or missing chunks that appear at coarse
LODs and vanish at fine ones.

## Materials

`constMaterial(mat.cloth)` for a single-material shell. `nearestMaterial([...])`
picks per point by whichever tagged field is closest — use it for a shell that
mixes, e.g. a belt with brass buckles. `paint(base, whereField, mat.brass)`
overrides inside a region, which is how trims, stripes and tattoos are applied
without adding geometry.

## Loop

Bake into **your own** generated directory so parallel authors do not clobber
each other's output, then look at it with the software rasteriser:

```bash
npx tsx tools/bake.ts --lod low --only hair --gen out/gen_hair
npx tsx tools/preview.ts --lod low --gen out/gen_hair --yaw 0,45,90,180 --size 380x640
```

`tools/preview.ts` needs no GPU, no build step and no browser; it writes
transparent-background PNGs you can open directly with the Read tool. Look at
your work every iteration — this is a sculpting job, and the numbers alone will
not tell you the nose is a beak.

To see your part in context, bake the whole character to your own directory:

```bash
npx tsx tools/bake.ts --lod low --gen out/gen_hair
npx tsx tools/preview.ts --lod low --gen out/gen_hair --yaw 0,90,180
```

The default `src/generated` is the integration build; leave it to the
integrator.

`out/bake_report.json` lists per-shell triangle counts, timings and empty
shells. A shell that produced no geometry is reported, not silently dropped.

## Budget

At `--lod high` the whole character should stay under roughly 400 k triangles
and 12 MB of encoded data. Check your shell's line in the bake report; if it is
eating the budget, raise its `voxelScale` rather than simplifying the shape.

## Measuring against the reference

`ref/views/clay_{0..5}.png` — the untextured sculpt turnaround, 6 views, matted
to alpha. **This is the geometry target.**
`ref/views/body_{0..5}.png` — the same 6 views textured. **Colour target.**
`ref/views/head_{0..3}.png` — head close-ups, 4 views.

Panel order left to right is a turnaround, but not a uniform rotation: panels 0
to 5 are yaws 90, 45, 0, 315, 270, 180. Panel 2 is the front. See
`docs/HANDEDNESS.md`; do not let `tools/compare.py` refit this from IoU, because
it cannot.

`tools/grid.py` draws a labelled grid over any panel. **Pass `--metres`** and
the rows are labelled in metres above the floor, taking the panel's alpha bbox
as sole to hair tip — that removes the panel-fraction arithmetic that produced
several wrong numbers in the first round:

```bash
python tools/grid.py --panel ref/views/clay_2.png --rows 0.30 0.55 --zoom 3 --metres
```

Use it to justify a number, and record what you measured in
`docs/MEASUREMENTS.md`.

Scratch files: prefix anything you write under `out/` or the scratchpad with
your part id. Authors run concurrently and two of them lost work last round to
same-named scratch scripts.
