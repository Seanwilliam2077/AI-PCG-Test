# Reference suitability verdict

Rubric: `grimoire/intake/validation_rubric.md`.

## Verdict: **PASS**, routed `character-conditional → maximum likeness`

Against the rubric's Pass criteria:

- one obvious target object — yes, a single figure per panel;
- occupies enough of the frame — foreground coverage 0.476–0.546 across all twelve panels;
- at least one strong silhouette — **six**, plus six textured and four head close-ups;
- major materials visible — skin, hair, black cloth, trousers, leather, canvas, brass, steel;
- hidden side reasonably inferred — better than that, it is **observed**: front, both
  three-quarters, both sides and back are all present;
- approximable with procedural primitives — yes, with the character track's stylised-clump
  treatment for hair.

The rubric's own character clause is the operative one:

> **character-conditional → maximum likeness**: user explicitly wants the closest possible match
> to a specific person/character. Confirm this intent before starting.

Intent is explicit and on the record — the brief was "as close as possible to the reference".
Stylisation level is **measured, not assumed**: 8.2 head-units, which is neither realistic (7.5)
nor anime-adjacent (5–6). The rubric's instruction to "request front, side, and back views"
is already satisfied.

## Deterministic admission gate

`forge/stage1_intake/check_reference_admission.py`, all twelve panels:

- **admitted: true** for all twelve, no failure reasons;
- `largestComponentFraction` **1.000** everywhere — every matte is a single connected component,
  no fragments or specks;
- foreground coverage 0.476–0.546;
- **zero duplicate pHashes.** Closest pair is `clay_1` vs `clay_2` at 18 bits.

One result worth recording: `clay_2` (front) and `clay_5` (back) are **22 bits apart** on pHash,
i.e. perceptually distinct — even though their *silhouettes* are nearly identical (measured at
0.01 IoU apart, which is what made silhouette-only view fitting fail in the previous build).
Pixels can separate front from back; outlines cannot.

## Stated limits, per the honesty rule

A turnaround is still a set of projections. It cannot supply hair microstructure or skin pores at
this resolution (377 px across the front figure), it does not settle absolute scale, and its two
side panels disagree about the braid drape by 0.12 m. Those are recorded in
`analysis/image-analysis.md` Layer 8 and will be reported as per-region confidence rather than
smoothed over.
