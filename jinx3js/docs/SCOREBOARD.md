# The scoreboard

`tools/compare.py` measures a render turnaround against Thibaut Granet's own
turnaround and says **where** the model is wrong, not just that it is. The
review loop reads its output; a part author reads the width table and the
contact sheet and changes one number in `spec/jinx.json`.

```bash
python tools/compare.py --tag r1                       # everything in out/views
python tools/compare.py --tag r1 --views 2,5           # only those ref panels
python tools/compare.py --tag r1 --pin                 # force the known-good view map
python tools/compare.py --tag r1 --map out/view_map_pinned.json
python tools/compare.py --tag r1 --refit               # re-solve the map from IoU
python tools/compare.py --ceiling                      # what the mattes allow
python tools/compare.py --selftest                     # validate the tool itself
```

Renders are found as `render_yaw<deg>.png` (from `tools/render.mjs`) **or**
`preview_yaw<deg>.png` (from `tools/preview.ts`). The yaw number is the
identity, not the prefix; if both spellings of one yaw are present the
`render_` one is used and the duplicate is reported.

Outputs, all under `out/`:

| file | what |
|---|---|
| `view_map.json` | which render yaw belongs to which reference panel, with its `mode` (`pinned`, `pinned-file`, `reused`, `cyclic`, `free`) |
| `metrics_<tag>.json` | every number below, machine readable |
| `compare_<tag>.png` | per view: reference │ render │ overlay │ width profile |
| `profiles_<tag>.png` | width profiles for all views, larger |

A run over six views takes about 3 seconds. It never crashes on missing,
blank, alpha-less or single renders; it says what it skipped and carries on.

---

## 1. Which render is which panel — pinned, not fitted

**The map is knowledge, not a measurement.** `docs/HANDEDNESS.md` establishes it
from features that silhouettes cannot see: the pistol is visible in `body_0` and
absent in `body_4`, the tattoos the other way round, and `body_2` is the front.

| panel | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| yaw | 90 | 45 | 0 | 315 | 270 | 180 |

That is **not a uniform rotation** — five views sweep around the front and a back
view is appended — which is why both the free and the order-preserving fits
fight it. And silhouette IoU genuinely cannot resolve it: with the arms down,
yaw 0 scores about 0.80 against the front panel *and* against the back panel.

So the precedence is:

1. `--refit` — re-solve from IoU, ignoring everything else.
2. `--map <file>` — a pinned panel→yaw map from JSON.
3. `--pin` — the built-in map above.
4. `out/view_map.json`, if it exists.
5. Otherwise **the built-in pin**, not a fit.

A wrong map silently mis-pairs every per-view number below it, which is worse
than a map that is occasionally stale — so the fallback is the pin and the fit
has to be asked for. A pin fixes only **which** render goes with **which**
panel; every IoU beside it is still measured on the current run, so a pin can
never launder a bad render into a good number. (That is also why a `null` IoU in
a pinned file is ignored rather than copied through.) Renders are matched by
yaw, so a map written against `preview_yaw*.png` pins `render_yaw*.png` too.

`--map` accepts any of:

```json
{"pairs": [{"panel": 0, "yaw": 90}, ...]}      // out/view_map_pinned.json, as written
{"panel_yaw": {"0": 90, "1": 45, ...}}
{"0": 90, "1": 45, ...}
```

**The fit is computed anyway, every run, and the disagreement is reported.**
While the character is undressed the fit will disagree and that means nothing;
once it is fully dressed and the fit *still* disagrees, that is evidence of a
modelling error and the tool says so. If a cached `view_map.json` disagrees with
the pin, the run prints a warning naming `docs/HANDEDNESS.md` and telling you to
delete the cache or pass `--pin`.

For completeness the fitter is still there and still constrained: it solves the
best **turnaround-order-preserving** matching by DP over (start panel,
direction), because a camera walking around a model may start anywhere and run
either way but may not jump about, and reports the unconstrained best-IoU
alternative whenever the two differ (`--free-assign` removes the constraint).
Extra renders are dropped rather than forced — a 45-degree sweep against a
six-panel turnaround leaves two unmatched, and they are listed.

**Mirrored fits are always computed.** If the whole turnaround fits better
mirrored, `+X` is not her left and the model's handedness is inverted. The alarm
needs the mirrored mean to beat the as-rendered mean by `max(0.02, 3%)`; a
near-symmetric blockout flips by a percent or two from matte noise alone.
`--use-mirror` scores the mirrored renders so you can see what the numbers
*would* be once handedness is fixed.

`docs/PART_CONTRACT.md` says panel index 2 is the front; the tool prints a note
when the map in use puts yaw 0 somewhere else.

## 1a. Asymmetry: what can and cannot be measured

### The degeneracy that has to be designed around

`src/viewer/camera.ts` renders **orthographically**, on purpose — a perspective
camera would poison silhouette IoU. That choice has a consequence:

> Under orthographic projection the silhouette along **−d** is *exactly* the
> mirror of the silhouette along **+d**, for any solid whatsoever. A shadow does
> not depend on which side of the object you stand.

So for opposite views, `R(y+180) ≡ flip(R(y))` identically. Any statistic
comparing yaw *y* with a mirrored yaw *y+180* is a **constant**, not a
measurement. Measured on the current build, `IoU(R(y), flip(R(y+180)))`:

| pair | 0/180 | 45/225 | 90/270 | 135/315 |
|---|---|---|---|---|
| value | 0.9972 | 0.9971 | 0.9970 | 0.9974 |

An earlier version of this tool computed exactly that for the 90/270 pair, read
0.997 as "the model is perfectly symmetric, so it has no lateral geometry", and
that conclusion was reported twice and acted on. It was an artefact. The test
was measuring the projection, not the model — adding the Zapper puts the *same*
1924 px into both views. It is now printed as `const` with the reason attached
and is excluded from every verdict.

### Self-mirror — the replacement, and it does work

Flip **one** view about its own vertical axis and match it against itself,
searching for the best axis position. There is no degeneracy: it is a property
of the object's silhouette in that projection. Only the **front and back** views
are reported — a side view's left-right axis is the depth axis, where symmetry
means nothing anatomical.

Measured on `out/views`:

| view | reference | render | delta |
|---|---|---|---|
| yaw 0 / `clay_2` | 0.754 | 0.874 | **+0.120** |
| yaw 180 / `clay_5` | 0.736 | 0.875 | **+0.140** |

That gap is the real statement: **the render is too symmetric.** The sculpt is
asymmetric because of the contrapposto, the holstered Zapper, the low sash
corner and the braids falling to one side; closing the gap means building those.

It measures the *amount* of asymmetry, never which side it is on. For side, read
the per-panel IoUs and the colour ΔE gap.

### The mirror-pair IoU gap — kept, but re-read

Yaw *y* and yaw *360−y* still get compared against their own panels, and a gap
over 0.08 IoU is still a headline. What changed is the interpretation, which now
depends on whether the two yaws are also 180° apart:

- **45/315, 135/225** — genuine mirror-image viewpoints, not opposite
  directions. `symMdl` is informative here, and a large gap with
  `symMdl ≈ symRef` means a lateral feature is on the **wrong side**.
- **90/270** — also opposite views. The two renders are *forced* to be exact
  mirrors, while `clay_0` and `clay_4` mirrored against each other agree only
  **0.650**. One render cannot fit both. The gap is real and worth watching, but
  it says her **pose** is asymmetric — not that a feature is on the wrong side.

The same test runs on **colour** (`dEgap`, 6 ΔE) with the worst-split region
named, because the cloud tattoos are a texture-only lateral feature: a mirrored
tattoo does not move the silhouette at all.

One caveat: the check only sees views that were scored. A fit that assigns one
side of a pair and drops the other hides the finding — another reason the pinned
map, which places all six panels deliberately, is the default.

## 1b. Ground contact — she does not stand square

For each view, the height of the lowest pixel on each side of the figure's
midline, reported relative to whichever foot is on the floor, in %H and mm.

**The reference stagger at the front view is −2.74 %H = −47 mm**, her left foot
(image-right, `+X`) raised. Sign convention follows `docs/HANDEDNESS.md`:
`stagger = t_image_left − t_image_right`, so negative means her left is higher.

This replaced a run-count test at the floor that had a false premise. `clay_2`'s
bottom 2 % is **one** silhouette run, not two, because only the lower boot is
touching the ground. The old test read that single run as "the reference's boots
are merged by the matte", produced a "181 % too wide" finding, and an author
spent a round chasing it and regressed. There was never anything wrong with the
matte — she is standing in contrapposto.

Two consequences elsewhere in the report:

- **REFERENCE MATTE WATCH** now takes its lower bound from the *measured* higher
  sole rather than a constant. Below that height a single run is her stance, and
  is no longer flagged as a bridged matte.
- **TOP WIDTH DEVIATIONS** marks any band below the reference's higher sole with
  `[under her raised foot]`, because there the sculpt has one boot on the ground
  and a square-stanced render has two. Fix the stance before touching a width.

Measured on runs at least 3 %H wide, and then on the whole connected piece those
runs belong to, so a braid tip (1.7 %H) can never be mistaken for a sole while a
boot's narrow toe is still counted. Oblique views are printed with `~` and never
acted on: off-axis the left/right split mixes in depth.

## 1c. Saying when a term cannot discriminate

Both bugs above had the same shape — a number that looked like a measurement but
could only ever come out one way. So the report ends with **WHAT THIS RUN CANNOT
SEE**, listing every quantity that is structurally blind for the current inputs
and why: the constant `symMdl`, oblique stagger rows, landmarks clamped on a
search boundary, an undetectable crotch in side views, missing colour targets,
unscored panels. A constant is printed as `const`, never as a number.

## 2. Normalisation

The render camera and the artist's camera do not match, so nothing is
comparable until both are put on the same canvas:

- **Scale** from the silhouette's bbox **height** to a fixed 1024 px. Height,
  not area or width: the braids and the A-pose make width unreliable, but the
  figure stands on the floor in every panel and the top of the head is
  unambiguous.
- **Vertical anchor**: the bbox bottom (the soles) on a fixed row.
- **Horizontal anchor**: the silhouette's own **centroid**, which is steadier
  than the bbox centre — one splayed braid drags the bbox centre 20 px.
- **Then** a residual (dx, dy) search of up to 40 px maximising IoU, reported
  separately. Centroid-and-soles alignment is deliberately dumb so it cannot
  launder a real error; the refinement is applied afterwards and printed on its
  own line, so a figure that is merely mounted off-centre reads as an offset
  finding instead of smearing into all forty width bands.

Because the figure is always 1024 px tall, **one canvas pixel is one permille
of figure height**, and every length in the report is quoted as `%H`, percent of
figure height. At the reference's 1.72 m that makes 1 %H ≈ 17 mm.

Three normalisation numbers are findings in their own right:

- **scale spread** across views. The reference figure is the same height in
  every panel; if the render's is not, the camera or the rig is moving.
- **bbox aspect** (width/height), which is scale-free and directly comparable.
  A large delta means the render is a different shape at the same height.
- **render source height**. Below 400 px the tool warns: normalising a 640 px
  render up to 1024 invents detail it never had, and chamfer and edge-F become
  optimistic by roughly half the upscale factor in pixels.

## 3. Metrics

All silhouette metrics are computed on two mask variants:

- **full** — the whole silhouette.
- **debraid** — thin lateral runs removed. At each row a run survives if it is
  the row's widest, or at least 4.2 %H wide, or at least 45 % of the widest run
  in its row. Arms (about 5 %H) survive the first clause; the far leg in a
  three-quarter view survives the second; a braid is 1.7–3.5 %H and fails both.
  It cannot separate a braid lying *on* the body, which is the back view — there
  `debraid ≈ full`, and that is why both are reported.

| metric | reads as |
|---|---|
| **IoU** | overall agreement |
| **precision** | share of the *render* that is right. Low ⇒ the render is too **fat** |
| **recall** | share of the *reference* that is covered. Low ⇒ too **thin** |
| **chamfer** | symmetric mean contour distance, in %H, plus its p95 |
| **edge F** | tolerant boundary F-score at 2, 4, 8 and 16 px (0.2 / 0.4 / 0.8 / 1.6 %H) |

Precision and recall are kept apart precisely so "too fat" and "too thin" are
distinguishable; IoU alone cannot tell them apart.

**Disconnected geometry.** The render's silhouette is decomposed into connected
components. A shell that floats free of the body — a boot sole detached from the
leg — barely moves IoU but is nearly always a build bug, and it drags the bbox,
which sets the normalisation scale, with it. Loose pieces are listed with their
area and height range, and the report says to fix them before reading anything
else.

### The width profile — the number to act on

At 40 evenly spaced height bands, for both images:

- `full` — total horizontal extent of the row.
- `core` — the **widest single run**, which is the trunk and head above the
  crotch and the nearer leg below it. Braid-blind by construction.
- `sum` — total material across all runs.
- `nrun` — how many runs, which is what detects the leg split.

Each band is a **median** over the rows in its slab, not a mean: one row that
clips a boot lace or a matte speck should not move a band.

Reported per band: reference width, render width, signed difference in `%H`,
and the same difference relative to the reference width. The printed table
ranks the ten largest deviations across all views, names the height, names the
part that owns it, and phrases the fix:

```
 1. yaw  60  t=0.512  thigh (pants)  ref 17.87%H  render 19.24%H  +1.37%H -> 8% too WIDE
```

Two ways to read a deviation:

- A **broad** run of same-signed bands is a width error. Change the radius.
- A **single huge spike** at a silhouette discontinuity — the crotch, the pant
  hem, the boot cuff — is usually a **height** error, not a width one: the step
  is in the right shape but at the wrong height, so at one band you are
  comparing hips against thigh. Check the landmark table before touching a
  radius. The selftest's `shortlegs` case produces exactly this signature.

### Landmark heights

Read off the smoothed core profile and reported as a fraction of figure height,
reference vs render, with the delta in `%H`. Both the core profile (braid-blind)
and the full profile are measured; the full variant is in the JSON as `*_full`.

| landmark | how it is found |
|---|---|
| `head_top` | highest row still half as wide as the head's widest point |
| `chin` | steepest widening above the neck |
| `neck` | the pinch just above the shoulder line |
| `shoulder` | highest row still carrying 72 % of the upper body's width |
| `waist` | narrowest row **between** the hip and the shoulder |
| `hip` | widest row of the pelvis |
| `crotch` | highest row with 18 unbroken split rows beneath it, on the debraid mask |
| `knee` | narrowest row **between** the calf bulge and the thigh |
| `ankle` | narrowest row **between** the sole flare and the boot cuff |
| `sole` | 0 by construction |

Three things make these repeatable rather than merely computable:

1. **Minimum-between-two-maxima**, not a fixed window. A window slides off the
   pinch when a render's proportions are off and reports a phantom jump.
2. **Plateau centres.** A waist is a broad flat stretch; a bare `argmin` can sit
   anywhere along it, so one pixel of matte doubt moves the landmark ten percent
   of the figure. The tool takes the centre of the contiguous run within a
   whisker of the extreme value.
3. **The reference chooses first.** The render's search is the reference's
   interval intersected with ±10 %H around the reference's answer, so the two
   are measured like for like. Between the calf and the thigh a profile view
   often has two nearly equal minima — the boot cuff notch and the knee — and
   without this the two images pick different ones and the delta is nonsense.

A landmark whose search **hit its own window edge** is a clamp, not a
measurement. It is printed with `?`, flagged in the JSON as `ref_at_edge` /
`render_at_edge`, and if the *reference* clamped it is excluded from the score.
A landmark absent from a view — there is no crotch split in a side view — is
reported as `-`, never guessed.

`crotch` is deliberately conservative: side views never split and say so.

### Braids

Braids reach the ankles and swing wide in three-quarter views, where they
dominate the bbox width. Everything above is therefore reported twice, `full`
and `debraid`, and `braid_area_frac` gives the share of the silhouette outside
the de-braided body for reference and render side by side — that is the number
that says whether the braids themselves are too heavy or too light.

Where the braid lies on the body (the back view) it cannot be separated from a
silhouette at all, and the two variants converge. Read `debraid` as "body
without thin lateral appendages" and not as an anatomical mask: it also drops
the Zapper, the loose straps and the hands.

### Colour

Against `body_*`, inside the intersection of the two masks only. The reference
body panel is normalised on its own silhouette and re-aligned against the
render, so a colour reading is never displaced by a geometry error more than the
geometry metrics already report.

Reported overall and over twelve named bands: `hair_mass, head, neck,
chest_top, midriff, hips_sash, thighs, knees, calves, boots, braids, arms`,
plus `other` for whatever is left. Each band gives ΔL, Δa, Δb, mean ΔE, and the
chroma-weighted circular mean hue for reference and render, so "the trousers are
too blue and too dark" is one row.

Two details that make the table honest:

- **Regions are defined on the reference, never on the render.** The hair band
  is "pixels the *reference* says are blue", so a render whose hair came out
  grey is still scored inside the hair band instead of escaping into `other`.
- **`dL_rel` removes the render's global exposure offset.** The renderer's
  lighting will not match the artist's, and a uniform ΔL of +33 says nothing
  about materials. A band that is still dark after the global offset is removed
  is genuinely the wrong material.

Bands are height ranges intersected with the reference's own core/blue masks
and assigned in priority order, so no pixel is counted twice. `arms` is
everything lateral between t 0.44 and 0.83 that the reference does not call
blue; in views where a braid hangs beside the torso and is not blue enough, it
will contaminate that row.

## 4. The score

One scalar per view, 0–100, averaged over the views scored.

```
score = 100 * Σ wᵢ · sᵢ

s_shape    = ½·IoU(full) + ½·IoU(debraid)        w = 0.30
s_edge     = edge F at 8 px (0.78 %H)            w = 0.15
s_chamfer  = 1 / (1 + chamfer%H / 1.0)           w = 0.10
s_width    = exp(−width_rms_core%H / 2.0)        w = 0.20
s_landmark = exp(−landmark_rms%H / 1.5)          w = 0.15
s_colour   = exp(−mean ΔE / 15)                  w = 0.10
```

**Why these weights.**

- Geometry gets 0.90 and colour 0.10. This is an SDF reconstruction: the
  geometry is the hard, slow, many-rounds problem, while colour is a handful of
  constants in `spec.materials` that one edit fixes. Colour is in the score so
  it cannot be forgotten, weighted low so it cannot dominate a round.
- **Shape 0.30** is the headline agreement and the thing everyone recognises,
  but it is a single blunt number, so it does not get a majority.
- **Width 0.20** is the largest single non-IoU weight because it is the only
  metric that is *localised*: it is what turns "this view is wrong" into "the
  thigh is 12 % too narrow at t=0.55", which is what a part author can act on.
- **Landmark 0.15** carries proportion, which IoU is remarkably tolerant of —
  a figure with the right area and the wrong leg length can still score a
  respectable IoU.
- **Edge 0.15 and chamfer 0.10** together cover boundary quality, which IoU
  under-weights on thin features: getting the braids, fingers and boot laces on
  the right line barely moves IoU but moves chamfer a lot.
- Half the shape term uses the **de-braided** mask so that a view whose braids
  are wrong cannot swamp the body's own error, and vice versa.

**Why exponentials for width and landmarks.** Both are RMS errors in %H where
zero is the target and there is no natural upper bound. The constants set what
"one factor of e worse" means: 2 %H (≈34 mm) of width RMS, 1.5 %H (≈26 mm) of
landmark RMS. Chamfer uses `1/(1+x)` instead, which has a fatter tail, because a
single bad view should not zero out an otherwise good round.

**A term that cannot be measured is dropped and its weight shared out**, rather
than scored as zero: no `body_*` panel, `--no-colour`, or fewer than three
usable landmarks. A missing measurement is not a modelling failure.

**Calibration anchors**, all measured with this tool:

| what was scored | score |
|---|---|
| `clay_*` panels fed back in as the renders (identity) | **99.8** |
| the same, eroded by 1 px — i.e. correct to within one pixel of the matte | **94.7** |
| `body_*` panels scored against `clay_*` — a *perfect* model seen through a second matte | **68.0** |
| the dressed build in `out/peek8`, pinned map | **37.4** |
| the same build, `--refit` (map fitted from IoU) | **40.3** |
| the earlier blockout in `out/views` (nude, no hair, no boots, feet detached) | **29.8** |

Note that the fitted map scores the *same build* three points higher than the
pinned one. That is not a better model, it is the fitter choosing whichever
pairing maximises IoU — including yaw 0 against the **back** panel. It is the
clearest possible argument for pinning: **never compare a pinned round against a
fitted one.** `view_map.json` records its `mode`, and the report header states
whether the map was pinned or fitted.

The third row is the important one: **68 is roughly what a flawless
reconstruction would score if it were rendered the way the textured sheet was.**
Scored against `clay_*` with a clean render it would be much closer to 95.
Do not read the score as a percentage of correctness; read it as a rank between
rounds, using the same view set both times. `views_scored` and `coverage` are in
the JSON for exactly that reason, and the per-term breakdown in
`views[].score.terms` is the finer-grained signal — on an early blockout the
width and landmark terms sit near their floor and the per-term values move
before the total does.

## 5. What the mattes allow — the IoU ceiling

`ref/views/*.png` were matted out of JPEG turnaround sheets by
`tools/slice_ref.py`. They are good but not perfect, and `python tools/compare.py
--ceiling` measures how imperfect:

```
panel      cross-IoU    prec  recall   cham%   IoU+1px  IoU-1px  holes_px
clay_0        0.9002  0.9886  0.9096   0.565    0.9734   0.9726         0
clay_1        0.9207  0.9271  0.9926   0.667    0.9722   0.9712         0
clay_2        0.9409  0.9859  0.9537   0.562    0.9774   0.9768       121
clay_3        0.9574  0.9674  0.9893   0.157    0.9714   0.9706       121
clay_4        0.9743  0.9819  0.9921   0.090    0.9712   0.9702         0
clay_5        0.9013  0.9341  0.9625   0.906    0.9744   0.9737         0
cross-matte mean 0.9325  min 0.9002
one-pixel   mean 0.9725  min 0.9702
```

**Use `clay_*` for geometry.** It is the cleaner matte, and it is the only one
the tool scores geometry against.

**The hard ceiling against `clay_*` is about IoU 0.97.** The matte boundary is a
threshold on an antialiased edge; moving it by one pixel — which is genuinely
ambiguous — costs about 0.027 of IoU on this figure. Anything above 0.97 is
measuring the matte, not the model. In score terms that is the 94.7 anchor
above.

**Scoring geometry against `body_*` would cap you near IoU 0.93**, and as low as
0.90 on `clay_0` and `clay_5`. That is not all matte error: the textured render
resolves hair the clay sculpt does not have, so the two silhouettes genuinely
differ around the braids. It is exactly why the geometry target is the clay
sheet.

Three specific defects, all of which the tool reports rather than absorbs:

1. **A wedge of backdrop shadow survives between the legs** on the front and
   three-quarter panels. `clay_1` and `clay_2` both keep it: the legs read as
   merged from the crotch down to mid-thigh where the sculpt clearly separates
   them. The report has a **REFERENCE MATTE WATCH** section listing the bands
   where the reference is closed and the render is open, with an upper bound on
   the area involved. Do not close your model's legs to chase it. The heuristic
   cannot tell a matte wedge from a genuinely wrong stance, so it only counts
   gaps narrower than 3 %H and phrases the result as "may be".
2. **JPEG pin-holes inside the braids.** These are filled — an enclosed hole
   smaller than 0.06 % of the figure's area cannot be real geometry at this
   resolution — but the count and area are printed every run (`clay_2`: one
   hole, 121 px) and stored in `metrics.matte`. Larger enclosed regions are kept:
   the triangle between a relaxed arm and the ribs is real background.
3. **`body_0` is speckled with pin-holes along the braid**, which is most of why
   its recall against `clay_0` is only 0.91. Colour readings for that panel over
   the braid are correspondingly thin.

A practical reading: **treat IoU 0.95 as "as good as this measurement can see"
and stop optimising it**; past that point the width profile, the landmark table
and the colour table are the only things still saying something real.

## 6. How the tool was validated

`python tools/compare.py --selftest` builds six synthetic renders by perturbing
the reference panels in ways whose effect can be predicted analytically, runs
the full pipeline against them, and checks that what comes out matches what went
in. All 19 checks pass; the numbers below are from a run:

| perturbation | prediction | measured |
|---|---|---|
| view assignment of all six | `{0:2, 60:3, 120:4, 180:5, 240:0, 300:1}` | recovered exactly |
| uniform scale ×1.15 | normalised away, IoU → 1 | IoU 0.994, width RMS 0.07 %H |
| translation (+37, −23) px | normalised away, IoU → 1 | IoU 1.000, width RMS 0.00 %H |
| horizontal stretch ×1.08 | +8.0 % at every band | +8.06 % median |
| legs eroded 4 px/side below t=0.55 | −0.626 %H below, 0 above | −0.659 %H below, +0.000 %H above |
| legs scaled ×0.93 (crotch at t=0.547) | crotch → 47.17 %H | 47.51 %H |
| " | hip 47.92, waist 79.98, knee 20.42, ankle 10.11 %H | 48.29, 80.35, 20.82, 10.46 |
| trousers darkened by 10 L | `thighs` and `knees` ΔL = −9.99 | −10.02, −10.15 |
| " | untouched `chest_top` / `boots` / `head` ΔL = 0 | −0.46, −0.51, −0.67 |
| whole turnaround mirrored | handedness alarm fires | fires (0.981 mirrored vs 0.803) |
| nothing mirrored | alarm stays silent | silent (0.962 vs 0.799) |

The residual tenths in the last colour row are the Lab→BGR→uint8 round trip in
the synthetic generator, not measurement error.

The tool was also run against deliberately broken inputs — an empty renders
directory, a fully transparent render alongside a good one, a single view, a
render with no alpha channel at all, and a 4×4 px speck — and handles all of
them with a message and a zero exit rather than a traceback.

## 7. Known limitations

- **A fitted view map is only as good as the silhouettes**, and on this
  character they are not good enough: front and back differ by about 0.01 IoU
  with the arms down. That is why the map is pinned from `docs/HANDEDNESS.md` by
  default and the fit is reported only as a cross-check. If the pin is ever
  wrong, every per-view number is wrong with it — it is the one input the tool
  takes on trust.
- **The mirror-pair check needs both sides of a pair present.** It is silent on
  a `--views` filter that keeps only one, and on a fit that drops one.
- **Nothing here can tell you which *side* a lateral feature is on from geometry
  alone.** Self-mirror gives the amount of asymmetry; the 90/270 gap is
  confounded by the orthographic mirror identity. Side is only recoverable from
  colour (the tattoos) or from the 45/315 pair. If a test claims to know the
  side, check it against the identity in §1a before believing it.
- **Any statistic comparing two views 180° apart is a constant.** If a future
  test needs "how asymmetric is the model", it must be built from a single view
  flipped against itself, never from a pair of opposite views.
- **`debraid` is a heuristic**, tuned on the reference's proportions
  (braid 1.7–3.5 %H, arm ≈ 5 %H). A render with implausibly thick braids or
  spindly arms will confuse it. Compare `braid_area_frac` between reference and
  render before trusting a `debraid` number.
- **Landmarks are 1-D features of a 2-D projection.** In a profile view the
  "waist" is a depth minimum, not a circumference minimum, and in this costume
  the trousers end just below the knee, so the knee pinch is genuinely
  ambiguous. What is guaranteed is that reference and render are measured with
  the same operator, so the *delta* is meaningful even where the absolute value
  is arguable.
- **Colour cannot separate lighting from material.** `dL_rel` removes a global
  offset, which handles exposure, but not a different key direction. Δa and Δb
  are the trustworthy columns.
- **Everything is silhouette-based.** Interior form — the abs, the face, the
  braid's twist — is invisible to this tool. The clay panels' shading carries it
  and `tools/grid.py` is how you read it.
