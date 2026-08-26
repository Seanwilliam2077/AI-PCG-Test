# What is in here, and what is deliberately not

Every image in this directory is safe to redistribute. That is a decision made per
image, not a blanket one, and the rule differs between the two character builds because
their materials have different origins.

## Published

| file | what it shows | why it is publishable |
|---|---|---|
| `jinx3js_yaw*.png` | the SDF + Surface Nets character, textured | its materials are procedural terms authored in TypeScript. No reference pixel is in them. |
| `jinx-i2t_yaw*.png` | the spec-driven character, **geometry only** | its textured renders bake albedo extracted from the reference, so only the material-stripped pass is published |
| `characters-side-by-side.png` | the two builds at a common figure height | same rule, applied per column |
| `face-painted-vs-sculpted.png` | the modelled skull against the painted face | the "before" panel is the geometry-only render; the texture panel is generated from measured scalars and contains no reference pixel; the three "painted" panels use a render mode that flattens every material EXCEPT the generated face texture (`--flat 1 --keep head`) |
| `board-comparison.png` | the two routes side by side, three views | the reference column is absent, and route 2 is shown geometry-only; the board says so on its own face |
| `board-turnaround.png` | three turnarounds, six yaws each, on a dark ground | route 1 textured (procedural materials), route 2 geometry-only, route 2's generated face pass. The artist's two turnarounds are in the local version only |

### One clearance decision, and how it was settled

The face row was built three yaws wide, then widened to six, then reverted, then widened
again. The middle step is the one worth keeping.

The build agent found its own clearance list edited on disk from three yaws to six, with
a comment claiming the extra renders "arrived afterwards", and **reverted it**. Its
reasoning: a file existing on disk and a file being cleared to leave the machine are
different facts, and a comment in a source file is not clearance from whoever owns the
reference material. On the evidence it had -- an unattributed edit to a provenance
whitelist -- that was the right call, and it flagged the edit rather than complying.

What it lacked was the attribution, which is supplied as evidence rather than as an
assertion. All six come from `render.mjs --flat 1 --keep head`, which replaces every
material with a uniform grey except the generated face texture. The three contested yaws
carry **0, 0 and 18 chromatic pixels** against **26, 20 and 0** for the three already
cleared -- the same signature -- and template-matching every reference panel into them
at six scales peaks at **0.585-0.645**, inside the same coincidental band as the boards
themselves.

The board also carried a caption saying the remaining yaws were "not cleared for
publication". That was an unsupported provenance claim in the opposite direction, and it
shipped once before being caught. It now says what is actually true: the painted island
is only visible in the forward half, because at 180 and 270 the head has turned away.
| `board-painted-face.png` | the generated face map and the three views it produces | the de-lighting plate this is modelled on cannot ship in any form, because de-lighting is applied to the artist's pixels. Rebuilt around the one texture in the project that is generated rather than sampled |
| `img2threejs-gallery.png` | a screenshot of the img2threejs gallery, showing the reconstruction that named the technique | a credited citation of the method's origin — see the attribution below |

## Not published, anywhere in this repository

- The Jinx turnaround, the head close-ups and the five-pose sheet the pistol was
  measured from. © Riot Games, modelled and textured by **Thibaut Granet**
  (<https://thibaut_granet.artstation.com/projects/X1aWVw>).
- Every PBR map extracted from those pixels — albedo, roughness, normal, height,
  ambient occlusion, twenty materials each — and the served copies of them.
- Any render that displays those maps.

Each board exists in two versions. The `_full` ones under `out/boards/` carry the
reference columns and the extracted textures and are **not** in this repository; the
`_pub` ones published here are built by the same scripts (`tools/boards/build_*.py`)
with those panels removed or replaced, and each states on its own face what is missing
and why.

Verified by pixels rather than by filename: every reference panel, every de-lit albedo
and every route 2 textured render was template-matched into all three published boards
across six scales. Peak normalised correlations were 0.51, 0.73 and 0.74 -- the residual
is coincidental structure between renders of the same character at the same framing, not
a source present in the image.

That earlier row is where this rule nearly slipped. The first version of that figure used
the ordinary textured renders, which carry the extracted hair and skin maps, and a
reference head crop as its left column. Both were caught on review and the figure was
rebuilt; the render harness gained a `--keep` flag so a single generated texture can be
shown without publishing the extracted ones alongside it.

The distinction being drawn: a reference used as a **measurement target** is not
redistributed at full fidelity, and neither is anything derived pixel-wise from it. What
leaves this project from that source is *measurements* — proportions, landmark heights,
colour medians in CIE Lab — which are reported as numbers in the docs.

## Attribution for `img2threejs-gallery.png`

A screenshot of the img2threejs project gallery
(<https://github.com/img2threejs/img2threejs>), showing the entry
**"Dual-Sword Warrior — TypeScript procedural surfaces" by Hoài Nhớ**, tagged
`img2threejs v1.5.1 · procedural TypeScript Surface Nets`.

It is included because it is the origin of the method these projects use, and because
naming a technique without showing where it came from is worse citation than showing it.
The reconstruction is Hoài Nhớ's work and the thumbnail marked SOURCE REFERENCE within
it is a third party's character art; neither is claimed here, and both are reproduced
only at the size and fidelity of the original screenshot, for attribution.

If either author would prefer it removed, it will be.
