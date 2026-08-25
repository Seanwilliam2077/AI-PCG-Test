# References and provenance

## The pipeline

**img2threejs** — <https://github.com/img2threejs/img2threejs>

A staged pipeline that turns reference imagery into a Three.js asset by way of a single
validated spec. Its shape, as used here:

| stage | what it does |
|---|---|
| stage1 intake | probe the image, admit or refuse the reference, extract PBR evidence, de-light albedo, locate landmarks, build a detail inventory |
| stage2 spec | pre-spec assessment, then author and strictly validate `object-sculpt-spec.json` |
| stage3 build | generate a TypeScript factory from the spec, one pass at a time; decimate; carve visual hulls |
| stage4 review | diagnose renders against the reference, gate on per-pass acceptance criteria, record a review before the next pass unlocks |
| stage5 rig | derive a skeleton, joints and skinning from the spec |

Eight build passes, each with numeric acceptance criteria, each refusing to unlock the
next without a recorded review. Both character builds and the pistol went through it.

The generator's real contract — as opposed to its schema — is written up in
`jinx-i2t/docs/GENERATOR_CONTRACT.md`, because none of it is discoverable from the
schema and every item cost a pass to learn.

## The idea behind the hard-surface build

**Nova3D: Code-Native Generation of Programmable 3D Assets** — <https://arxiv.org/abs/2607.22738>
Nimra Noor, Muhammad Bilal, Abdullah Hussain, Hassan Baig

> Current 3D generative models mostly produce a final surface: a visually strong but
> largely opaque mesh. Interactive 3D worlds need more than a surface. They need named
> parts, an assembly hierarchy, measurable constraints, local edit handles, and joints
> for articulation. We present Nova3D, a system that generates 3D assets as executable
> Blender source code; the compiled mesh, a binary glTF (GLB), is treated as the
> artifact, not the asset. Because the output is a program, semantic handles exist at
> generation time rather than being recovered afterward by segmentation or rigging.

Reported on Nova3D-Bench, 54 items across six domains against eleven baselines in four
families:

- an executable program and a valid artifact for **54/54** items;
- named parts in a parent-child assembly tree on **every** asset, where no mesh-native,
  CAD or segmentation baseline exposes either;
- **51/52** prompt-stated numeric and count constraints satisfied, best baseline 11/52;
- **14/18** blinded local edits passed, with locality preserved in **18/18**;
- **59 joints across 12 assets at 98.3%** geometric validity, where every baseline
  exposes zero native joints;
- geometry competitive — winning the structured domains in a pairwise shape-quality
  tournament, second only to the strongest mesh-native model — while conceding texture
  realism to baked-PBR systems.

Nova3D targets Blender Python; img2threejs targets TypeScript. The claim is the same
one, and it maps onto the img2threejs spec almost field for field:

| Nova3D's claim | where it lives in an img2threejs spec |
|---|---|
| named parts, parent-child assembly tree | `componentTree`, each entry with `id`, `name`, `parent` |
| measurable constraints | `dimensions`, `attachment.localStart`/`localEnd`/`baseRadius` |
| local edit handles | `actionProfile.transformChannels`, `geometryDescriptor` parameters |
| joints for articulation | `actionProfile.pivot` with an axis, `actionProfile.sockets`, `rig.bones` |
| the program is the asset | the generated factory; the mesh is built at load time |

The pistol build takes Nova3D's discipline literally: **the constraints were frozen
before the model existed.** `zapper-i2t/docs/CONTRACT.md` states the assembly tree, the
numeric and count constraints with their check procedures, the joints with axes and
limits, the edit handles with their locality expectations, and — the section that makes
the rest trustworthy — an explicit list of what the reference cannot settle. The build is
then scored against that frozen contract, the way Nova3D scores against prompt-stated
constraints.

## Reference imagery — and why none of it is in this repository

The Jinx turnaround, the head close-ups and the five-pose sheet the pistol was measured
from are © Riot Games, modelled and textured by **Thibaut Granet**
(<https://thibaut_granet.artstation.com/projects/X1aWVw>).

They are used here as a **measurement target only**. They are not redistributed.
Specifically excluded from this repository:

- `ref/*.jpg` and `ref/views/*.png` — the reference sheets and their mattes;
- `pbr/**` and `public/**` — every albedo, roughness, normal, height and AO map, because
  each is extracted from those pixels and inherits their provenance;
- any render that displays those maps.

Every image published here is **geometry-only**: the same models with materials replaced
by a uniform grey. The measurements derived from the reference — proportions, landmark
heights, colour medians — are reported as numbers, which is what a measurement target is
for.

Reproducing the builds requires supplying your own copy of the reference and placing it
at the paths named in each project's README.

## Rendering and tooling

- **three.js** — <https://threejs.org/>
- **Playwright** with headless Chromium and SwiftShader, for deterministic WebGL captures
  at a fixed metric frame
- **OpenCV** and **NumPy**, for every measurement in these projects
