# How these were built

Three builds of two subjects, all measured against the same reference material, all
generated from code rather than modelled by hand. What follows is the method, and it is
mostly a method for **not fooling yourself**.

The short version: every claim in these projects is a number something measured, every
change had to prove itself against a judge it did not own, and the record of what was
tried and rejected is kept because the rejections carry most of the information.

---

## 1. Measure first, and say where every number came from

Nothing in the reference material carries a dimension. Not one. Everything metric in
these builds is inferred, and the inference chain is written down every time:

> The character's hand measures 44 mm across the four fingers in the companion build.
> In one reference pose the four curled fingers span roughly 52.5 px. Therefore
> 0.838 mm/px, giving a pistol tube outside diameter near 30 mm.

That chain rests on one derived number from another model and one span read off curled,
foreshortened fingers. Writing it as a chain is what makes it attackable — and it was
attacked, deliberately, by an agent whose only job was to try to break it.

The same discipline produced the character's `coordinateFrame.scaleReference`:

> "1.72 m total height, hair-crest tip to sole. **DECLARED, not measured** — the
> reference sheet carries no dimension."

A declared number is legitimate. An undeclared one pretending to be measured is not.

## 2. A guess dressed as a measurement is worse than no measurement

The most expensive class of bug in this project was never a crash. It was a plausible
number sitting in a field, doing damage silently.

Twenty PBR material samples were cut from the reference by hand-placing rectangles as
fractions of the panel. Fifteen of the twenty sampled the wrong pixels. All five head
materials landed on bare cheek. The fingernail crop sat 30.4% inside the silhouette.
`eye.png` and `sclera.png` were **byte-identical**. And the extractor reported 0.75
confidence on every one of them, because it reports 0.75 confidence on a crop of
backdrop just as happily as on a crop of skin.

The fix was to stop placing rectangles and start searching for them, against two
criteria rather than one:

- **colour** — the median must match a target measured elsewhere on the body;
- **homogeneity** — the patch's own p5-p95 lightness span must be under about 14 L.

The second criterion was the one that mattered, and it took two failed attempts to find.
Searching on colour alone returned, for the black crop top, a rect that was half dark
cloth and half bright buckle. Its median was exactly the near-black that was asked for.
It was not a material sample at all.

Homogeneity also has to be an **admissibility criterion, not a cost term**. Weighted
against colour at 1.6, a flat patch of the wrong colour beat a slightly varying patch of
the right one, and one material came back 134 dLab from its target. Colour is the
measurement; homogeneity decides whether a rect is a sample.

## 3. Fill a field only when you know what reads it

Nine separate bugs in the character build were the same mistake: a spec field filled to
satisfy a validator, without knowing what consumes it. Every one passed strict
validation. Every one was found by rendering and measuring.

| what was written | what actually reads it | what happened |
|---|---|---|
| `transform.position` on an attached part | the generator reads `attachment.localStart` | every component collapsed onto its parent's origin; the figure rendered as a pole |
| `primitive: capsule` on an attached part | the generator sweeps a tapered cylinder from the attachment radii | `primitive` was never consulted; everything came out a cone |
| `scale: [1,1,1]` written to normalise | `transform.scale` **overrides** `dimensions` outright | 101 measured dimensions discarded, every primitive at unit size |
| absolute world heights | positions are parent-local and **accumulate** | a crest at y 8.6 on a 1.72 m figure |
| trousers as one component | one component is one swept solid | one tube swallowing both legs and the gap between them |
| `materialRef` carrying the right material | the generator reads `material` | 14 of 20 measured materials orphaned; the whole figure rendered in two colours |
| `appliesTo: "pants-l, pants-r"` | the emitter reads `parent`, `placement`, `instanceScale` | 26 pinstripes and 9 buckles piled up at the world origin as 0.1 m cubes |
| `pivot.mode: "center"` on all 103 parts | nothing objected | a forearm pivoting about a point that is not on the body |
| `uvStrategy` | **nothing** | the field is decorative; the seams it was supposed to fix are structural |

The tell was never in the spec. It was in the numbers coming back from the render — a
bounding box topping out at 8.638, a mesh 15,552 triangles heavy sitting at the origin.

**Any harness driving a generator you did not write should print named per-object
extents from the very first render.** That one probe named a bug in a single run after
two rounds of guessing from the spec.

## 4. Give the loop a judge it does not own

Every change to the character build after the first iteration had to pass a gate:

```
apply patch → strict validation → regenerate → render six canonical views
            → local metrics → INDEPENDENT scoreboard → keep or revert
```

The scoreboard lives in a sibling project and is not reimplemented in the thing it
judges. The local metrics — silhouette IoU, a 40-band width profile, landmark heights,
a lightness envelope, a volumetric visual-hull IoU — are cheap and fast; the scoreboard
is the arbiter.

The verdict rule was written before any result was seen:

> A patch is accepted when the independent scoreboard does not fall, AND either the
> scoreboard rises or one local term improves beyond its own noise floor.

It was amended exactly once, and the amendment is documented in the tool itself: the
four local terms are all geometry, so a patch that only touches materials cannot move
them **by construction**. The first patch through the gate proved it, leaving all four
bit-identical while the scoreboard rose 0.10. Requiring a geometry improvement from a
material patch is a broken rule, not a strict one.

Twenty-six attempts, nine accepted.

## 5. The gate is not enough — look at the render

The gate was fooled twice, in opposite directions, and both times the eye settled it.

**It accepted something worse.** Tiling the material crops more densely scored +0.10.
The render turned into basket weave: at repeat 8-16 the blurred 96 px crops read as a
regular woven grid across the entire figure. The colour term carries weight 0.10 and
cannot see a moiré.

**It rejected something better.** Re-cutting the crops so they were actual material
samples scored −0.10 — and visibly removed the collage look that was the single largest
complaint about the build. That one was accepted over the gate's objection, with the
reasoning recorded in the ledger: the regressions were all in skin *bands*, and the band
is not skin. The reference's midriff band reads L 39.3 while its bare skin medians
L 69.6, because the band is mostly garment. Honest skin makes the band too bright. That
is a coverage defect, not a colour defect, and keeping smeared crops would only hide it
— every geometry measurement afterwards would be taken through mush.

Every patch now gets a reference-before-after sheet, and the sheet is part of the
verdict.

## 6. Do not optimise against your own bad ruler

The largest remaining gap in the character score was landmark placement. Three attempts
failed before one worked, and the first two failed the same way.

A patch with hard-coded deltas died on `KeyError: 'hair-crest'` — a component an earlier
patch had consolidated away. A replacement re-measured every run, but measured with a
detector written for the occasion, which located landmarks as extrema of the width
profile inside a window. That detector asked for the knee to drop 60 mm and the calf to
rise 60 mm **in the same pass**. The calf is below the knee. Those were not model
defects; they were two bad readings, and acting on them made every term worse, including
the landmark RMS the patch existed to fix.

The independent scoreboard already measured the same landmarks properly: semantically
named, reported from as many of the six views as each could be located in, and each
reading flagged when it landed on a search boundary so it could be excluded rather than
quietly contributing a fabricated pair. Read off the build, its table told one coherent
story instead of eight contradictory ones:

```
crotch    +8.41 %   1 view          waist     -0.33 %   3 views
hip       +4.25 %   6 views         neck      -0.16 %   6 views
chin      +1.91 %   2 views         head_top  -0.02 %   6 views
ankle     +1.61 %   4 views         shoulder  +1.22 %   6 views
```

The crown, neck and waist are right; everything from the hip down sits too high. One
monotone piecewise-linear warp, damped per landmark by how many views actually saw it,
pushed the whole figure through at once. The most corroborated landmark went from
+4.25% to +1.68%.

**Weight each correction by the evidence behind it.** The crotch is worth 8% and is seen
once, because the legs only separate in one view; it moves a third as far as the hip
does on the same nominal error.

## 7. Patches must re-measure, not remember

Two patches were rejected purely for carrying stale numbers — deltas measured against a
build that three later patches had already changed. Once several corrections are landing
in sequence, a hard-coded delta is a lie with a timestamp.

Every corrective patch now re-derives its correction at runtime, from the judge's own
tables and the reference panels, and the state it measures against is refreshed by the
gate on every acceptance.

## 8. Converge, do not leap

The map from a declared width to the silhouette it produces is not the identity: a limb
is a circular cylinder seen at an angle, a garment overlaps its neighbours. A full
correction overshoots.

Corrections are damped and re-run. The width corrector converged after one pass and was
then rejected three times in a row, identically — deterministic renders make that a
clean convergence signal rather than noise. The landmark warp at damping 0.75 gained on
its own term and lost exactly as much on width, leaving the composite flat; at 0.28 it
gained 0.20 points and then overshot on the second pass.

## 9. Let an adversary check the work

Every patch authored in these projects was verified by a separate agent whose only
instruction was to **refute** it: run it, run it twice and diff for idempotence,
validate, recompute its stated numbers from the reference, estimate its cost
independently, and check it against the generator contract rule by rule.

They earned their place. One verifier reproduced an existing descriptor's exact
2.4 × 1.6 × 2.1 mm output to prove that a briefing given to all seven authors was
**wrong**: implicit-surface bounds are normalised, not metric, because the emitter
multiplies the result by `dimensions` afterwards. The same pass established that
subdividing an implicit surface is a hard validation error, not a warning — so the
voxel blockiness of that path is a cost to be budgeted, not something smoothing would
fix later.

Two premises stated with confidence in a brief, both false, both caught before they
cost a build.

## 10. Keep the rejections

`baseline/ledger.json` records every attempt, accepted or not, with its numbers and, for
the interesting ones, why. The reverted texture-tiling patch carries this:

> Accepted by the numeric gate on a +0.10 scoreboard move, then reverted on looking at
> the render: at repeat 8-16 the blurred 96 px crops read as a regular woven grid across
> the whole figure. The colour term carries weight 0.10 and cannot see a moiré. The gate
> needs an eye on the sheet, which is what caught this.

Seventeen rejections, nine acceptances. The rejections are where the method came from.

---

## What this buys, and what it does not

The measured result is on the record: the spec-driven character build reached **86% of a
hand-tuned build's likeness score on its first complete run**, then closed to within 9%
of it over one iteration — while leading on four of the six scored terms, and carrying a
rig, a measured material set and a triangle budget it meets, none of which the hand-tuned
build has.

What it does not buy is likeness by itself. The hand-tuned build still wins on width
profile and landmark placement, which are the two terms the eye reads first. A pipeline
that measures everything will find its own errors; it will not, on its own, have taste.

The honest reading is that these are not competing at the same thing. One is a likeness.
The other is a program that produces a likeness, and can be inspected, measured, edited
and animated — which is the argument Nova3D makes, and the reason the pistol was built
the same way.

## 11. Read what the tool's own reference implementation does

The hardest defect in the character build resisted eight passes and a full round of
geometry work: `face-landmark-placement` scored 0.15 against a 0.80 critical threshold
and would not move. Eyes, brows and mouth were each modelled as their own mesh, placed
by measurement, and none of it read.

The answer was in the pipeline's own showcase. `createGirlCharacterModel.ts` builds its
head as a contoured implicit surface and its **face as a canvas texture** — soft-edged
ellipse blobs for the oval, brows, eyes with sclera/iris/pupil/lid layers, a lit nose
bridge with nostrils, split upper and lower lips. No facial geometry at all.

The reason is scale, and it is arithmetic rather than taste. In a 500 x 900 render of a
1.72 m figure the whole head is about 50 px. An eye is three pixels. No amount of
correctly placing a three-pixel sphere makes an eye legible; a painted one is.

The same file contradicts two other things this project had been doing. Its body is
**lofted from cross-sections** — rings of points chained by centroid proximity and
subdivided with centripetal Catmull-Rom to a 2 mm target edge — where this build stacks
tapered cylinders between joints, which is most of why it reads as a mannequin. And its
header states a rule this project had been breaking for two full iterations:

> DIMENSIONS ARE FROZEN. Proportions were accepted; nothing may be resized or moved.
> Detail work adds geometry on top of existing forms.

Two rounds of width and landmark patches had been doing exactly the opposite: resizing
and moving parts to chase metric terms, for a combined gain smaller than the single
change of painting the face.

**A reference implementation is evidence about the tool, not decoration.** It is the one
place where the pipeline's authors show what the fields are *for*, and reading it is
cheaper than nine rounds of inferring it from a schema.

---

## What this buys, and what it does not
