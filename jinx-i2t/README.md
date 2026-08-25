# jinx-i2t

A Three.js Jinx rebuilt through the [img2threejs](https://github.com/img2threejs/img2threejs)
pipeline: one validated `object-sculpt-spec.json` driven through eight gated build
passes, measured at every step against a six-panel reference turnaround.

The point of this build is not that it is the closest likeness — it is not; see
[COMPARISON.md](COMPARISON.md) for the head-to-head against the hand-written SDF
build. The point is that everything in it is derived from a spec that regenerates
the whole model in one command, and that every claim about it is a number
something measured.

## State

| | |
|---|---|
| passes | 8 of 8 complete, each with a recorded review and a comparison sheet |
| components | 103, in a parent-local hierarchy |
| materials | 20, each with albedo / roughness / normal / height / AO extracted from reference pixels |
| rig | 49 bones, 49 joint pivots, 98 sockets — every joint socket within 0.0 mm of its bone |
| triangles | 128,833 near / 66,713 mid / 37,308 far, against a 250,000 budget |
| draw calls | 104, against 160 |
| six-view lightness spread | 1.945 L, against the reference sheet's 2.61 |
| scoreboard | 35.35 / 100 |

## Layout

```
object-sculpt-spec.json   the single source of truth; strict validation passes
src/createJinxModel.ts    generated, never edited by hand
src/main.ts               the review harness: fixed metric frame, six canonical yaws
tools/render.mjs          headless Chromium capture + per-mesh probes
tools/lstats*.py          lightness statistics inside the alpha
tools/profile_ratio.py    width-over-height profile against the reference
analysis/                 every spec mutation, as a script with its reasoning
review/                   layer and per-feature scores fed to append_review.py
docs/GENERATOR_CONTRACT.md  what the generator actually reads, and the bugs that cost
```

Everything under `analysis/` is a script rather than a hand edit, so each change to
the spec carries the measurement that motivated it and can be re-run.

## Build

```bash
python ~/.claude/skills/img2threejs/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createJinxModel.ts --pass-id optimization-pass --force
```

```bash
node tools/render.mjs --out out/optimization-pass --size 500x900
```

Useful harness flags: `--flat 1` strips every material to a uniform grey (the probe
that found the lighting bug), `--tris` dumps per-mesh triangle counts, `--sockets`
dumps every socket's world position, and `--key`/`--amb`/`--env`/`--exp` scale the
lighting for calibration sweeps.

## What the loop caught

Nine bugs, every one of which passed strict spec validation and was found only by
rendering and measuring. They are listed with their numbers in
[COMPARISON.md](COMPARISON.md#nine-bugs-the-loop-caught-that-the-validator-could-not);
[docs/GENERATOR_CONTRACT.md](docs/GENERATOR_CONTRACT.md) covers the five earliest,
which are all the same mistake — filling a spec field to satisfy the validator
without knowing how the generator consumes it.

The one worth repeating here: a uniform-albedo probe measured a six-view lightness
spread of **14.38** with `scene.environment` on and **2.19** with it off. Every
light in the rig followed the camera; the environment did not, and it was the whole
of the front-to-back falloff. No amount of tuning the lights could have found that,
because the lights were not the problem.

## Provenance

The reference turnaround is © Riot Games, modelled and textured by Thibaut Granet.
It is used here only as a measurement target. `ref/`, `pbr/` and `public/` are
excluded from the repository, and so is any render that displays the extracted
maps; published comparison imagery is geometry-only.
