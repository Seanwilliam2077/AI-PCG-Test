# Measurements taken off the reference

Provenance for the numbers in `spec/jinx.json`. Anything not recorded here is a
guess and should be treated as such by the review loop.

## Method

`tools/slice_ref.py` cuts each ArtStation sheet into per-view panels with an
alpha matte; `tools/grid.py` draws a labelled grid over a panel, where the
labels are fractions of **panel** height. The figure does not fill the panel
exactly, so a panel fraction `t` converts to a **figure** fraction `f` by

```
f = (t - t_top) / (t_bot - t_top)
```

and to a height above the floor by `y = (1 - f) * height`.

For `ref/views/clay_2.png` (the front view, 378 x 1302) the figure occupies rows
12 to 1289, so `t_top = 0.0092`, `t_bot = 0.990`.

`meta.height = 1.72 m` is the **total silhouette height**, hair-crest tip to boot
sole. It is a choice, not a measurement — the sheets carry no scale. Everything
else is a measured ratio against it, so changing it rescales the character
consistently.

## Landmark heights (front view, clay_2)

| landmark | panel t | figure f | y (m) | how it was read |
|---|---|---|---|---|
| hair crest tip | 0.012 | 0.003 | 1.715 | topmost pixel of the silhouette |
| skull crown | — | — | 1.674 | inferred: the hair cap sits ~40 mm over the skull |
| brow | 0.077 | 0.069 | 1.600 | brow ridge line, `grid_head.png` |
| eye centre | 0.087 | 0.079 | 1.584 | pupil centre |
| nose base | 0.108 | 0.101 | 1.546 | |
| mouth | 0.118 | 0.111 | 1.528 | lip seam |
| chin | 0.132 | 0.125 | 1.505 | lowest point of the jaw |
| neck base | 0.175 | 0.169 | 1.429 | clavicle pit |
| shoulder | 0.190 | 0.185 | 1.402 | top of the deltoid |
| bust | 0.225 | 0.220 | 1.342 | |
| crop-top hem | 0.285 | 0.281 | 1.237 | |
| waist (narrowest) | 0.300 | 0.297 | 1.209 | |
| navel | 0.315 | 0.312 | 1.183 | |
| waistband / iliac | 0.375 | 0.373 | 1.078 | top edge of the trousers |
| hip (widest) | 0.410 | 0.409 | 1.016 | |
| crotch | 0.455 | 0.454 | 0.940 | where the silhouette splits in two |
| knee | 0.630 | 0.633 | 0.580 | patella, read on `grid_low.png` |
| trouser hem | 0.710 | 0.714 | 0.492 | tattered edge |
| calf | 0.760 | 0.766 | 0.402 | widest point of the calf |
| boot cuff | 0.825 | 0.831 | 0.291 | top of the folded cuff |
| ankle | 0.900 | 0.908 | 0.158 | |
| sole | 0.990 | 1.000 | 0.000 | |

**Head unit.** Hair-top to chin is 0.122 of figure height — about 8.2 head units
to the whole figure, which is the stylisation, not an error.

**The legs are long.** Crotch at 0.543 of height against a real figure's
0.47–0.49, and knee at 0.337 against ~0.285. Shin measures slightly longer than
thigh (0.42 against 0.36). That is unusual anatomically and was re-checked
against `grid_low.png` before being accepted; it is what the sheet shows.

## Head proportions (head_1, head_2)

Face width is roughly **0.80** of chin-to-crown height — a narrow face on a
large cranium. That ratio set `widths.skullHalfW = 0.068` and
`widths.headHalfW = 0.058`.

Head depth was initially set at 0.180 m, which is wrong — deeper than the skull
is tall. Corrected to `headHalfD = 0.064` (0.128 m front to back, ~0.76 of skull
height).

## Known limits of the reference prep

- The sheets render a soft contact shadow onto the backdrop between the legs and
  under the boots. `tools/slice_ref.py` flood-fills the backdrop through a
  gradient barrier and classifies enclosed pockets by chromaticity, which
  removes almost all of it; a thin wedge survives in one or two panels.
- `body_*` panels keep a few JPEG-block pin-holes inside the braids, because the
  braid there sits close to the backdrop's own chromaticity. `clay_*` is clean
  and is therefore the geometry target.
- Panel index 2 is the front view. The yaw of every other panel is **not**
  assumed — `tools/compare.py` fits the mapping and writes `out/view_map.json`.

## Body width calibration (round 1)

Measured by rendering the bare body with `tools/preview.ts --frame 1.80`, which
fixes pixels-per-metre instead of fitting the bounding box, and sampling the
silhouette's horizontal extent at the same absolute heights on `clay_2.png`
(scaled so its figure height is 1.72 m).

A bbox fit cannot be used for this: the model is half-built, so adding the hair
would rescale it and every previous measurement with it.

First pass was far too heavy:

| y (m) | band | ref | render | error |
|---|---|---|---|---|
| 1.40 | shoulder | 0.272 | 0.432 | **+59 %** |
| 1.34 | bust | 0.301 | 0.432 | +43 % |
| 1.28 | ribcage | 0.304 | 0.446 | +47 % |
| 0.45 | calf (bare) | 0.218 | 0.261 | +20 % |

The arms were thick enough to merge with the torso — the reference shows three
separate runs at the waist (arm, torso, arm) where the render showed one — which
inflated every width below the shoulder as well. After narrowing the upper body
and thinning the arms, mean absolute error over the bands where skin is bare
(shoulder, bust, ribcage, waist, navel, knee, calf) is **2.7 %**.

The reference figure is genuinely slight: about **0.30 m across the ribcage
including both arms** at a 1.72 m height, against ~0.40 m for a realistic figure.

## Body depth calibration

Side view, `clay_0.png`. The bare calf at y = 0.45 is the only clean band — the
braid is a separate silhouette run there, so it can be excluded:

- reference calf depth 0.114 m against a measured width of 0.094 m, so a calf is
  **1.2 times deeper than it is wide**. The first pass squashed it to 0.90 and
  the side view read flat.

Above the waist the braid touches the back and merges into one run, so the
reference's core depth over-reads the body by roughly the braid's diameter
(~0.05 m). Torso depths were raised until the residual matched that allowance;
this band should be re-measured properly once the hair part lands and the
comparison becomes like for like.

### Side profile, front and back edges measured separately

Total depth alone is ambiguous, because the braid hangs behind the back and the
sash hangs in front. Measuring the front and back edges of the silhouette
separately, both referred to the knee centreline, separates them:

| y (m) | ref front | ref back | model front | model back |
|---|---|---|---|---|
| 1.21 | −0.087 | +0.165 | −0.094 | +0.086 |
| 1.18 | −0.089 | +0.168 | −0.101 | +0.086 |
| 0.94 | −0.131 | +0.192 | −0.107 | +0.105 |

The **front** edges agree to within about 10 mm over the whole torso. The
**back** edge is 0.08 m short at every height — which is exactly one braid.
Allowing ~0.07 m for it gives a reference torso depth of 0.182 m at the waist
against the model's 0.180 m, so the torso depth after the correction above is
right and must not be pushed further. The remaining gap closes when the hair
part lands, not by fattening the body.

Below the hip the model's front edge sits 20–50 mm *behind* the reference's,
which is the sash and the trouser bulk, not the body.

## The two renderers agree

`tools/render.mjs` (Three.js in headless Chromium) and `tools/preview.ts` (the
dependency-free software rasteriser) were run on the same bake and their
silhouettes compared after normalising to a common height:

| view | silhouette IoU | area ratio browser / software |
|---|---|---|
| yaw 0 | 0.988 | 1.006 |
| yaw 90 | 0.986 | 1.005 |

The residual is edge antialiasing, not geometry. This matters because the whole
review loop rests on measuring renders: if the two disagreed, a scoreboard
finding could be a renderer artefact rather than a modelling error. They do not,
so either renderer can be scored and the software one can stand in whenever
headless WebGL is unavailable.

## pants / sash

| what | panel | value |
| --- | --- | --- |
| waistband, top of the purple on the +X hip | body_2 | y = 1.086 |
| hem, her right leg, front arc | body_2 | y = 0.462 .. 0.520, ~5 teeth across the front |
| hem, her left leg, front arc | body_2 | y = 0.545 .. 0.568 |
| hem, her left leg, side | body_4 | y = 0.450 .. 0.490 (so the front rides ~35 mm high) |
| tooth depth | body_2/4 | 25 .. 45 mm, ~9 teeth per leg |
| pinstripe pitch, mid-thigh | body_2 | light band 12-18 mm + dark band 14-15 mm, bright seam every 21 mm |
| stripe colours | body_2 | ground RGB 84,50,74; stripe RGB 48,30,42 |
| trouser outer edge, her right | clay_2 | y=0.84: -0.165, y=0.78: -0.156, y=0.72: -0.150, y=0.60: -0.144 |
| gap between the trouser legs | body_2 | y=0.90: 20 mm, 0.80: 38 mm, 0.72: 62 mm, 0.56: 63 mm |
| sash top edge, her right hip | body_3 | y = 1.091 |
| sash hem, her right side (bearing ~-1.5) | body_4 | y = 0.910, mauve/stripe boundary |
| sash hem, her right rear (bearing ~-2.2) | body_3 | y = 0.954, flap lower edge |
| sash hem, her left rear (bearing ~+2.4) | clay_5 | y = 0.994 |
| sash hem, front and back centre | body_1/clay_5 | y ~ 1.00; the mauve never crosses either centre line lower than that |
| canvas apron, top | body_1 | tucked under the hip belt; near level, 1.044 on her right, 1.035 on her left |
| canvas apron, lower edge | body_2 | (x -0.086, y 0.991), (+0.077, 0.939), (+0.113, 0.948) |
| canvas apron, deepest point | body_1 | y = 0.930 on her left front |
| pocket on the apron | body_1 | a soft patch on the canvas, not a leather box; the dark diagonal over it is the drop strap |
| sash cloth colour | body_2 / body_4 | 0.373 0.216 0.337 and 0.341 0.212 0.333 sRGB, unstriped; striped pants read 0.310 0.180 0.275 |

The first three sash rows in an earlier round (lowest point y = 0.845, top
1.076, a pouch at x = +0.108) were read off `body_2`, where her right hand, the
slung strap and the drop strap all cross the cloth. `body_3` and `body_4` show
the same panel unoccluded and put its low corner 65 mm higher, on her right
side rather than at the front. Read the flap off those two, not the front.

Two numbers in `spec/jinx.json` disagree with the panels and are left alone
because they are not this part's to change:

- `pose.stanceHalfW = 0.07`. The trousered leg centre in body_2 is at
  x = -0.0885 at the knee on her right and about +0.048 on her left; the
  reference stance is both wider and asymmetric.
- `widths.thighR = 0.078`. The reference's *trousered* thigh half-width at
  y = 0.80 is 0.0675, which is less than body.ts's bare thigh radius there, so
  the leg under the cloth is roughly 12 mm fat.

## hair

Panel scales used below, from the alpha bounding box of each clay panel with
the top of the box taken as `landmarks.hairTop = 1.715`:

| panel | size | figure rows | mm/px |
| --- | --- | --- | --- |
| clay_2 (front, yaw 0) | 378 x 1302 | 12 .. 1289 | 1.343 |
| clay_1 (front 3/4, yaw -60) | 381 x 1280 | 12 .. 1267 | 1.367 |
| clay_5 (back, yaw 180) | 377 x 1227 | 12 .. 1214 | 1.427 |
| clay_4 (rear 3/4, yaw +120) | 371 x 1213 | 12 .. 1200 | 1.444 |

The three-quarter panels were read with `screen_x = x*cos(yaw) + z*sin(yaw)`,
so a feature located in clay_2 gives its x and the same feature in clay_1 then
solves for z. That is the only way to get the crest's depth: there is no true
profile in the clay turnaround (panels are 60 deg apart and index 2 is the
front, so 0 and 4 are rear three-quarters, 1 and 3 front three-quarters).

| what | panel | value |
| --- | --- | --- |
| crest tip, outer | clay_2 | x = -0.076, y = 1.710 |
| crest tip, inner | clay_2 | x = -0.026, y = 1.705 |
| notch between the two tips | clay_2 | x = -0.049, y = 1.679 (30 mm deep) |
| crest tip depth | clay_1 + clay_2 | screen -0.103 and -0.077 solve to **z = +0.075** for both -- the flicks go FORWARD over the brow, not back |
| scalp dome, top at x = +0.03 | clay_2 | y = 1.682 (so the crest stands 28 mm proud of the cap, not 17) |
| hair mass, rearmost at the crown | clay_4 | screen -0.077 -> z = -0.089 |
| hair mass, rearmost, upper | clay_1 | screen +0.105 -> z ~ -0.12 at y ~ 1.66 |
| centre-part apex | clay_2 | (0, 1.661, ~0.045); hairline drops to y ~ 1.63 at x = +-0.06 |
| hairline slope | clay_2 | passes (0, 1.660, 0.048) and (0, 1.500, -0.030), dz/dy = 0.49 |
| face-framing lock, her right | clay_2 | tip at x = -0.055, y = 1.437 |
| face-framing lock, her left | clay_2 | tip at x = +0.045, y = 1.457 |
| braid centre, her left | clay_5 | y=1.56: +0.053, y=1.47: +0.060, y=1.21: +0.040, y=1.03: +0.035, y=0.68: +0.061, y=0.33: +0.079, y=0.24: +0.081 |
| braid centre, her right | clay_5 | y=1.56: -0.027, y=1.38: -0.011, y=1.21: -0.024, y=1.03: -0.035, y=0.68: -0.046, y=0.33: -0.060, y=0.24: -0.067 |
| braid depth | clay_4 + clay_5 | z = -0.11 .. -0.14 the whole length; they hang 40-70 mm clear of the back, they do not lie on it |
| braid envelope diameter | clay_5 | 0.054 at the nape (y 1.55), 0.034 at the waist (y 1.21), 0.027 at the hip (y 1.02) |
| lobe pitch | clay_5 | 12 lobes between y = 1.29 and y = 0.94, so 0.029 m |
| plait end / last tie | clay_4 | y = 0.30 (far braid), y = 0.25 (near braid) |
| frayed tuft | clay_4 | fan of 4-5 flat blades from the last tie down to y = 0.09 .. 0.12 |
| ties per braid | clay_5, clay_4 | rings at y ~ 1.41, 1.20, 0.99, 0.68, 0.25 -- five, not the three in the base spec |

Numbers in `spec/jinx.json` that the panels disagree with. They are overridden
in `spec/parts/hair.json` rather than edited in place:

- `hair.braidTurns = 26`. A 3-strand plait shows three lobes per turn, so a
  0.029 m lobe pitch over a 1.55 m braid is `3*turns = 53`, i.e. **18 turns**.
- `hair.tieCount = 3`. The panels show five bands per braid.
- `hair.braidRoot = [0.085, 1.612, -0.052]` sits 12 mm outside the scalp cap at
  that height, so the plait would start in mid-air; moved to
  `[0.056, 1.585, -0.070]`, which is inside the mass.

And one the brief disagrees with rather than the spec: the task sheet asks for
face-framing locks reaching y = 1.30 and a crest trailing to z = -0.16. Those
are the *painted* head (`ref/views/head_1.png`, `head_2.png`), which has a
noticeably taller pouf and longer locks than the sculpt. Against the clay the
locks stop at y = 1.437 and the mass ends around z = -0.12; the part builds
y = 1.435 and z = -0.108 as a compromise.

## belts / gloves

Read with a metre grid keyed to each panel's alpha bbox (figure height 1.72 m),
at 3x for the hip runs and 9x for the arm bands. Panels used: `clay_2` /
`body_2` (front), `body_0` (her left side -- the side with the pistol),
`clay_5` (back), `body_4` (her right side).

**Sides.** Confirms `docs/HANDEDNESS.md` independently: `body_0` shows the
pistol *and* an untattooed upper arm carrying both black bands with their brass
buckles; `body_4` shows the cloud sleeve and no bands. So the bands, the
Zapper and the drop-leg rig are all on the same side -- her **left, +X** -- and
the tattooed arm is the bare one on **-X**. `belts.rigSide` carries this for the
thigh strap, holster, arm bands and the long glove sleeve.

| feature | measured | where |
|---|---|---|
| hip belt, front run | y 1.020 at image-left rising to 1.100 at image-right | `clay_2` 3x |
| hip belt centre / tilt | y 1.062 at x = 0, plane tilt 0.29 about z | derived from the two ends |
| hip belt width | 33-35 mm (band spans 1.070-1.105) | `body_0` |
| slung strap, back run | (rig hip, 1.045) to (other hip, 0.90) | `clay_5` |
| drop-strap keepers | y 0.985 and 0.930 | `body_2` |
| thigh strap | band between 0.845 and 0.875, so centre 0.855 | `body_0` |
| arm band, upper | spans 1.250-1.283, centre **1.266**, 33 mm | `clay_2` 9x |
| arm band, lower | spans 1.213-1.247, centre **1.230**, 34 mm | `clay_2` 9x |
| sleeve top, banded arm | 1.208, immediately under the lower band | `clay_2` 9x |
| sleeve top, tattooed arm | 1.115 | `body_2` 4x |
| glove wrist cuff | rolled band 0.945-0.990 | `body_2` 4x |
| bare fingers begin | y 0.885 | `body_2` 4x |

Two numbers in `spec/jinx.json` disagree with the sheet and are overridden in
`spec/parts/belts.json` and `spec/parts/gloves.json`:

* `belts.armBandLowerY` 1.196 is 34 mm low. That height is the **top hem of the
  sleeve** on that arm (measured 1.208), not the second band; the band's centre
  is 1.230 and the two bands are only a 4 mm groove apart, not 72 mm.
* `gloves.topY` 1.052 is a third of the way up the forearm -- the wrist joint is
  at 0.988 and the elbow at 1.181. The sleeve on the tattooed arm is cut at
  1.115 and the one on the banded arm runs over the elbow to 1.208.

`belts.hipR` (0.148) is unused: the loops are `torsoHalfWidth(y)` plus a pad and
are then pushed out until they clear the trousers and the hip wrap, because a
belt is worn over whatever is there and both of those shells are still moving.
The thigh strap and the arm bands are fitted to the dressed limb the same way --
the dressed thigh measures 0.095 m in radius against the body's 0.070, and the
upper arm at the band heights measures 0.036-0.044 against `upperArmR` 0.042.

## top and choker

Measured off `ref/views/body_2.png` and `ref/views/clay_2.png` with a metre grid
anchored on the panel's alpha bbox (bbox bottom = sole 0, bbox top = hairTop
1.715, giving 742.9 px/m on the front panel).  x is taken from the bbox centre,
so absolute x carries a few mm of bias from the pose; heights are solid.

| what | where read | value |
| --- | --- | --- |
| top, hem (bottom edge of the black at x = 0) | body_2 front | y = 1.220 |
| top, buckled band under the bust | body_2 front | y = 1.220 .. 1.244, keeper at x = +0.044 |
| top, cut edge on the front surface | body_2 front | (x 0.058, y 1.437) to (x 0.101, y 1.300) |
| top, neckline U, bottom of the opening | body_2 front | y = 1.385, half-width 0.027 |
| X lacing, eyelet centres | body_2 front | x = +-0.030, y = 1.3088 and 1.3523 |
| X lacing, eyelet outer diameter | body_2 front | 0.031, annulus 0.0067 |
| X lacing, crossing strap width | body_2 front | 0.012 |
| back, bare skin from the band to the nape | clay_5 back | y = 1.245 .. 1.40, full width |
| choker, three wraps | body_2 front | 1.478..1.466, 1.462..1.448, 1.444..1.432 |
| neck half-width just above the choker | body_2 front | 0.040 at y = 1.49 |

The choker stack is authored 6 mm higher than measured (1.4318..1.4772) so its
bottom wrap clears the top's collar instead of interpenetrating it.

### top, round 2 — the halter, remeasured by colour mask

The round-1 rows above were read by eye off a gridded crop.  Round 2 classifies
`body_2.png` into skin / black cloth / cream webbing / brass by colour and reads
the runs off the mask, which is what turned up the two things the eye had
missed: the neckline is not a notch in a band, and the eyelets are 4 mm bigger
than they looked.  Calibration: figure bbox y 12..1286, so 0.0013451 m/px; the
body centreline is at x = 195 px, taken as the mean of the midriff silhouette
centre over y = 1.15..1.20 rather than the bbox centre (the arms bias the bbox).

Black-cloth runs across the chest, per row:

| y | runs (x) |
| --- | --- |
| 1.420 | -0.040..+0.005, +0.048..+0.066 |
| 1.410 | -0.042..-0.012, +0.044..+0.065 |
| 1.400 | -0.044..-0.005, +0.040..+0.063 |
| 1.390 | -0.051..+0.003, +0.035..+0.060 |
| 1.380 | -0.059..+0.060 (single run) |
| 1.360 | -0.074..+0.066 |
| 1.340 | -0.085..+0.073 |
| 1.320 | -0.093..+0.078 |
| 1.300 | -0.098..+0.085 |
| 1.280 | -0.100..+0.089 |

So the cloth **splits in two between y = 1.380 and 1.390** and stays split up to
the choker: this is a halter with a neck strap, not a bandeau with a scooped
top.  The gap between the straps is off centre — exposed skin runs -0.015..+0.046
at y = 1.415 — and it is *narrower* than the straps are far apart at y = 1.42,
where the outboard strap sits at +0.048..+0.066.  That last row is the one that
forces the strap to be built as a band round the neck rather than as more of the
front panel: by 1.42 the panel's own cut edge has already come inboard of 0.048.

| what | where read | value |
| --- | --- | --- |
| eyelet centres (brass mask centroids) | body_2 | (-0.034, 1.358) (+0.029, 1.351) (-0.040, 1.316) (+0.033, 1.308) |
| eyelet outer diameter | body_2 | 0.029 x 0.030 |
| lace strap width, perpendicular | body_2 | 0.012 .. 0.0145 |
| lace crossing centre | body_2 | (-0.001, 1.338) |
| neckline, bottom of the throat opening | body_2 | y = 1.386 |
| cut edge, front-view trace | body_2 | 0.0915 at y 1.30, 0.079 at 1.34, 0.070 at 1.36, 0.0595 at 1.38 |

Lifting that last row onto the torso ellipse gives the 3D edge points
(0.0915, 1.30, 0.045), (0.079, 1.34, 0.068), (0.0595, 1.38, 0.071).  Fitting a
plane through them needs the **z coefficient to be positive** — the coverage
grows towards the front.  Fitting it with the opposite sign, as round 1 did,
puts the widest coverage at the side of the ribs, which then has to be sawn back
off with a constant-z cut, and that cut's face is what showed up as a hard
vertical line down the flank in the three-quarter views.

Back, `body_5` classified the same way (bbox y 12..1206; the panel is not at the
front panel's scale, so heights there are ±10 mm): skin from the spine out to
the silhouette at every height between the band and the shoulders, on the +X
side where neither braid nor tattoo confuses the mask — no top material is
visible from directly behind above y ≈ 1.27.  The dark strip that runs down the
spine from the nape to the belt carries brass clasps at y ≈ 1.355 and 1.325 and
a steel keeper at 1.253..1.297, and merges into the belt rig at y ≈ 1.19; it
reads as part of the harness rather than of the top, but nothing else in the
build claims it.

## body (round 2)

All read off `ref/views/clay_2.png` (front) and `clay_0.png` (her left side)
with the alpha-bbox metre grid (bbox top = 1.72 m, bottom = 0). `%H` below is a
percentage of that 1.72 m, so the numbers are directly comparable with
`tools/compare.py`'s width profile.

### The previous build's torso was 13 mm fatter than the spec it was built from

Root-finding the body field along +X (`out/probe_body.ts`) against
`torsoHalfWidth(y)`:

| y (m) | torsoHalfWidth.x | old surface | error | torsoHalfWidth.z*2 | old depth |
|---|---|---|---|---|---|
| 1.342 | 0.1040 | 0.1177 | +13.7 mm | 0.1880 | 0.2079 |
| 1.237 | 0.0959 | 0.1072 | +11.3 mm | 0.1617 | 0.1840 |
| 1.183 | 0.0865 | 0.1004 | +13.8 mm | 0.1496 | — |
| 1.120 | 0.0964 | 0.1101 | +13.7 mm | 0.1601 | 0.1830 |
| 1.016 | 0.1180 | 0.1385 | +20.5 mm | 0.2000 | 0.2192 |

The cause is the loft, not the widths. `smoothUnion(k, ...)` over a stack of
overlapping capsule sections sees two or three sections at nearly the same
distance at every point; `smin` subtracts up to `k` per fold and the fixed point
of that recursion is `delta = k` of extra radius, uniformly. With `k = 0.018`
the measured excess is 11-14 mm, which is the predicted number. `src/parts/top.ts`
had already found the same 15 mm empirically and reproduces the loft to
compensate; that workaround is now unnecessary (`top.proxyBlend` / `proxyStep`).

The corrected build lands on the profile to within 0.3 mm from y = 1.078 to
1.30, and stays wider only where the bust, trapezius, glute and thigh masses are
deliberately added.

### Reference torso width, isolated from the arms

In `clay_2` the arms merge with the torso at almost every height. The one clean
band is her **left** flank (screen-right), where the silhouette splits between
y = 1.14 and y = 1.21:

| y (m) | torso edge (%H from bbox centre) | half-width (m) |
|---|---|---|
| 1.209 | +5.21 | 0.0896 |
| 1.190 | +4.89 | 0.0841 |
| 1.180 | +4.58 | 0.0788 |
| 1.170 | +4.58 | 0.0788 |
| 1.150 | +4.74 | 0.0815 |

The midline is at the bbox centre to within 0.2 %H (the top's lacing eyelets sit
symmetric about it at ±0.030, and the linea alba reads at panel x 0.505 against
the bbox centre's 0.4987). So the reference waist is **0.158-0.170 m across**,
against `waistHalfW * 2 = 0.170` — the spec is right and the old surface's
0.201 was 18-27 % over.

### Shoulder ramp, front silhouette

Read below y = 1.443, where the hair lock beside the jaw has ended. Half-width
from the midline on her left:

| y (m) | 1.440 | 1.429 | 1.420 | 1.410 | 1.402 | 1.390 | 1.375 | 1.360 |
|---|---|---|---|---|---|---|---|---|
| reference | 0.0747 | 0.0997 | 0.1152 | 0.1266 | 0.1334 | 0.1428 | 0.1502 | 0.1515 |
| round 1 | — | 0.1209 | — | — | 0.1448 | — | 0.1490 | — |
| round 2 | 0.0703 | 0.0914 | 0.1062 | 0.1322 | 0.1406 | 0.1490 | 0.1533 | 0.1533 |

Round 1 had no trapezius at all: above y = 1.43 its width came from the torso
column's spherical top cap (radius `neckR * 1.9` plus the loft's 13 mm), which
is why it reads 0.121 at 1.429 where the reference is 0.100, is *right* by
accident at 1.375, and swallowed the neck between the two.

The top of that ramp is nearly horizontal — the mass tops out at y = 1.443 and
is already 150 mm across 3 mm below it — so it is built as an ellipsoid, not as
a neck-to-shoulder capsule; a capsule steep enough to reach 0.088 at 1.429 could
not also reach 0.150 at 1.375.

### Throat, side view

`clay_0` front edges, quoted as a recession behind the chest front at y = 1.360
(this is anchor-free, so it does not depend on pinning the panel's z origin):

| y (m) | 1.429 | 1.402 | 1.375 |
|---|---|---|---|
| reference | 51 mm | 31 mm | 6 mm |
| round 1 | 17 mm | 6 mm | 2 mm |
| round 2 | 50 mm | 24 mm | — |

The neck column itself is `head.json`'s, extended down to y = 1.420 with
`r = 0.0435`, `squashZ = 1.1`, centre z `+0.0076 -> -0.012` — the same column
`top.json`'s `neckCol*` and `choker.json`'s `neck*` were already written
against, so the collar and the three choker wraps now grip a neck instead of
floating on a cone. Cross-checked against the sheet: the neck reads 0.041
half-width just above the choker on `clay_2`, against MEASUREMENTS' earlier
0.040 and this column's 0.0427 at y = 1.450.

### Buttock depth

`clay_0` at the hip is a single silhouette run (the braid touches the seat), so
the only clean read is the braid's inner boundary in the shaded crop, at panel
x ≈ 0.575, which puts the buttock's back edge ~0.097 m behind the knee
centreline at y = 0.963. Bare-body depth there measures 0.215 m in round 2
against 0.216 in round 1: the trunk lost 27 mm of spurious depth and the glute
was given 12 mm more (`glute.back` 0.34 -> 0.40, `glute.rz` 0.68 -> 0.74), so
the sacrum sits 4 mm further back than before, not less.

### Numbers in `spec/jinx.json` this part disagrees with

None. `widths` and `landmarks` are all reproduced exactly; everything added
lives in `spec/parts/body.json` under the `body` key, above `landmarks.bust`
where `torsoHalfWidth`'s own table has only one key left (`neckR * 1.9` at
`neckBase`) and cannot describe a neck.

## Trunk depth, re-measured after the trunk was rebuilt

The first depth calibration was made against a trunk built as a stack of capsule
sections joined with `smoothUnion`. That construction **inflates**: at almost
every point two or three sections report nearly the same distance, `smin`
subtracts up to `k` each time, and the fixed point of that recursion over a long
stack is a full `k` of radius everywhere — measured at +13 mm of half-width and
+14 mm of half-depth at every height. It is also what welded the arms to the
ribs and put a 220 mm ball where the neck should be.

Rebuilt as a single lofted-ellipse field, the trunk lands *on* its profile, and
the real depth error appeared: **29–38 % too shallow** through the midriff.

Measuring it needs care, because the braid lies against the back and merges into
one silhouette run at every midriff height on both sides. `clay_4` (her right)
is the cleaner of the two — the braid mass drapes away from that side — and it
reads 0.231–0.249 m through y = 1.14…1.26. Allowing ~0.040 m for the braid puts
the reference body at about 0.19–0.21 m deep.

| y (m) | reference, braid allowed for | before | after |
|---|---|---|---|
| 1.26 | 0.210 | 0.172 | 0.194 |
| 1.20 | 0.202 | 0.172 | 0.180 |
| 1.14 | 0.193 | 0.176 | 0.184 |

Mean absolute depth error **32 % → 8.0 %**, with front widths unchanged at
within 5 %. The residual sits inside the uncertainty of that 0.040 m braid
allowance, so it should be re-measured once the braid geometry is settled rather
than tuned further now.

## top and choker (round 2) — the cut edge is a curve, and the centreline is not the feet

Calibration for everything below: `ref/views/body_2.png`, figure alpha rows
12..1286 against a 1.715 m figure, so **743.44 px/m**; body centreline **x = 195
px**. That centreline is confirmed independently by the choker, which is
symmetric about the neck: its dark run is -0.048..+0.046 at y = 1.450 and
-0.058..+0.062 at 1.440, i.e. centred on -0.001.

**The boots are not on that centreline.** Their midpoint is at 171 px — 32 mm to
her right — at y = 0.10 (runs 0.1141..0.2174 and 0.2523..0.3610 from the panel's
left edge), at 0.15 and at 0.40. Deriving an upper-body x from the feet, or from
the alpha bbox centre at 188 px, biases every reading by 1.5–3 cm.

### The garment's cut edge

Read two ways off the colour mask, which agree to a pixel. Rows (outer edge of
the black cloth at each height) and columns (highest cloth in each column):

| y | her right, -x | her left, +x |
| --- | --- | --- |
| 1.26 | 0.098 | (arm merged) |
| 1.28 | 0.100 | 0.090 |
| 1.30 | 0.098 | 0.086 |
| 1.32 | 0.093 | 0.079 |
| 1.34 | 0.085 | 0.074 |
| 1.36 | 0.074 | 0.067 |
| 1.38 | 0.059 | 0.063 |
| 1.40 | 0.044 | 0.065 |
| 1.41 | 0.042 | 0.066 |

| x | her right, top of the cloth |
| --- | --- |
| -0.100 | 1.293 |
| -0.090 | 1.328 |
| -0.080 | 1.351 |
| -0.070 | 1.367 |
| -0.060 | 1.379 |
| -0.050 | 1.393 |

So the edge's **slope is ~0 below y = 1.30 and 0.75 by y = 1.38** — a curve, not
the constant-slope plane round 1 fitted through three points. Round 1's baked
edge was 8–15 mm outboard of it across the whole ribcage.

The two sides disagree by 10–14 mm below y = 1.36 because her left arm hangs
against the ribs and occludes the cloth there, so her left reading is a lower
bound; above y = 1.38 the difference is real, her left strap genuinely sitting
further out. The build takes the (2·right + left)/3 weighting, and lands within
1.5 mm of it at every height from 1.27 to 1.37.

### Where the cloth is at the throat

Skin (the neck opening) between the two straps, from the same mask:

| y | opening | half-width | centre |
| --- | --- | --- | --- |
| 1.390 | +0.004..+0.035 | 0.0155 | +0.020 |
| 1.400 | -0.004..+0.040 | 0.022 | +0.018 |
| 1.410 | -0.011..+0.044 | 0.0275 | +0.0165 |

and the **whole cloth span** at those heights is -0.051..+0.062, -0.044..+0.065,
-0.042..+0.066 — centred on +0.006..+0.012, not on the spine. Both offsets are
needed: with the opening off centre and the strap slab centred on x = 0, her left
strap comes out 5 mm wide instead of 20.

### Hem, band and fittings

Bottom edge of the cloth, per column: 1.2246 at x = 0, 1.2246 at -0.020, 1.2259
at -0.045, 1.2219 at -0.065 — flat, at **y = 1.224**, not the 1.218 round 1 used.
The band's seam is at y = 1.250. On the band:

| fitting | x | y |
| --- | --- | --- |
| brass keeper loop (was never modelled) | -0.048..-0.039 | 1.231..1.251 |
| steel buckle frame | +0.018..+0.046 | 1.220..1.250 |

The reference's band edge is at |x| = 0.101 — the same as the bib's, i.e. the
band is flush, not proud, so `underBandProud` is 3 mm and not 8.

### Choker

Wrap centres **1.4385, 1.4545, 1.4685**, each ~9 mm tall, so the stack is
1.4335..1.4735 (40 mm, against the 45 mm round 1 built). Half-width 0.047 at the
wraps against a bare neck of 0.044 just above them: the leather is only ~3 mm
proud. The gaps between wraps are 4–6 mm, which is why the choker needs a voxel
under 5 mm — at round 1's 5.3 mm the three wraps and the X baked as one lump.

### Result

Baked shell against the reference edge, front-view half-width sampled on the
field (`out/top_probe.ts silh`) at 20 mm steps: y = 1.26…1.38 against the
(2·right + left)/3 weighting, y = 1.39…1.42 against each side separately, since
the two straps are genuinely different widths there. 13 samples.

| | round 1 | round 2 |
| --- | --- | --- |
| RMS edge error | 9.7 mm | 2.0 mm |
| worst | 18 mm (her right strap, y = 1.41) | 4 mm (her left strap, y = 1.39) |

Straps, the part round 1 built symmetric at |x| = 0.060:

| y | ref right / built | ref left / built |
| --- | --- | --- |
| 1.39 | 0.051 / 0.053 | 0.062 / 0.066 |
| 1.40 | 0.044 / 0.046 | 0.065 / 0.0635 |
| 1.41 | 0.042 / 0.045 | 0.066 / 0.063 |

and the black-cloth mask IoU over the chest box (y 1.232..1.425, |x| <= 0.099,
render and reference resampled onto a common metre grid) **0.768 → 0.783**.

## Zapper and tattoos (round 2)

### Which side, measured three ways

Segmenting the gun's brass+steel and the tattoos' pale blue-grey out of the
textured panels (`out/zapper_gun_extent.py`, `out/zapper_tattoo_extent.py`):

| panel | gun | ink |
| --- | --- | --- |
| `body_2` front | image-**right** | image-**left** arm and flank |
| `body_5` back | image-**left** | image-**right** back and arm |
| `body_0` her left side | 5002 px of gun | ~none |
| `body_4` her right side | only the far edge | 11 403 px = 5.2 % of the figure |

In a back view her right IS image-right, so all four readings agree: **gun on
her left, +X; ink on her right, -X**, exactly as `docs/HANDEDNESS.md` says.
Round 1 had both mirrored.

### Zapper: where the assembly sits on the outline

Front view `body_2`, x in metres from the leg centreline, +X = her left. The
"assembly" column is the hue-segmented gun; the "leg" column is her right
trouser edge at the same height, which is the same leg without a gun on it.

| y | assembly [inner, outer] | leg alone | round-2 render [inner, outer] |
| --- | --- | --- | --- |
| 0.82 | 0.162, 0.232 | 0.142 | 0.161, 0.216 |
| 0.78 | 0.152, 0.205 | 0.132 | 0.147, 0.204 |
| 0.74 | 0.144, 0.190 | 0.128 | 0.135, 0.189 |
| 0.70 | 0.132, 0.178 | 0.123 | 0.123, 0.180 |
| 0.68 | 0.125, 0.173 | 0.122 | 0.121, 0.171 |
| 0.66 | — (ended) | 0.124 | 0.121 (leg only) |

So the assembly is ~50 mm across, it reaches 55–75 mm outboard of the trouser,
and its axis leans **outboard going up** at dx/dy = 0.31 — which is why the
muzzle end vanishes inside the leg's outline below y = 0.67 even though the
side view still shows the tank at y = 0.61. `body_0` gives the matching forward
lean, dz/dy = 0.28, a gun depth of 74 mm against a 50 mm width (it is a slab
pressed on a thigh, not a rod), and puts the gun's centre 45 mm in front of the
thigh axis.

### The preview is orthographic, so `symMdl` at yaw 90/270 is a constant

`tools/preview.ts` projects with `col = W/2 + v[0]*scale` and no perspective
divide. Projecting along +X and along -X collapses X entirely, so the yaw 90
and yaw 270 silhouettes are **exact mirrors of each other for any model**.
Measured on the raw previews:

| | mirror IoU, view vs flipped partner |
| --- | --- |
| zapper shell alone, all its mass at +X | **1.0000** |
| whole figure, yaw 90 vs flip(yaw 270) | **1.0000** |
| whole figure, yaw 45 vs flip(yaw 315) | 0.9226 |

A body that exists only on one side still scores 1.0000 on that pair. So the
scoreboard's "render has NO lateral geometry at all" on the 90/270 row is a
false positive on this renderer, and `symMdl` there cannot be moved by any part.
The 45/315 pair is the one that responds: it went 0.947 -> 0.921 as the Zapper
moved to the correct side and grew a holster. `symRef` is 0.650 because the
reference sheets are perspective renders.

### Result

Same tree, same instant, flipping only `spec.zapper.anchor.x` and `roll`:

| | gun on her left (+X) | gun mirrored to -X |
| --- | --- | --- |
| yaw 0 vs `clay_2` | **0.823** | 0.786 |
| yaw 180 vs `clay_5` | **0.816** | 0.767 |
| yaw 90 vs `clay_0` | **0.763** | 0.755 |
| yaw 270 vs `clay_4` | **0.559** | 0.554 |
| yaw 45 vs `clay_1` | 0.609 | **0.634** |
| yaw 315 vs `clay_3` | 0.672 | **0.678** |
| mean IoU | **0.707** | 0.696 |
| turnaround refit | as-rendered 0.730 > mirrored 0.719 | mirrored 0.724 > as-rendered 0.716 |
| score | **41.4** | 39.1 |

The refit row is an independent check: with the gun on the wrong side the whole
turnaround preferred to be read mirrored, and with it on the right side it does
not. Flipping the ink is worth a further +0.3 score, with midriff dE
25.5 -> 25.1, arms 21.1 -> 20.8 and chest_top 26.9 -> 26.5.

## Boots, round 2: the cross-section of the boot pair (`boots`)

Method: `python out/boots_runs.py` decomposes each row of a panel's alpha into
runs and reports them in metres, using the panel's alpha bbox as sole-to-hair-tip
= 1.72 m — the same scale `tools/grid.py --metres` draws. Renders are measured
from `--frame 1.80` previews, where a pixel is 1/555.6 m and the floor is the
bottom row, so ref and render are directly comparable.

### The two boots separate downwards and merge upwards

Per-row runs, in metres, at the height given:

| y | `clay_2` runs / gap | `clay_5` runs / gap | render before / after |
|---|---|---|---|
| 0.06 | 0.117, 0.093 / **0.071** | — | 0.038 / **0.057** |
| 0.10 | 0.104, 0.109 / 0.035 | 0.120, 0.134 / 0.019 | 0.033 / 0.038 |
| 0.15 | 0.085, 0.093 / 0.015 | 0.104, 0.119 / 0.033 | 0.033 / 0.033 |
| 0.21 | **one run 0.198** | **one run 0.293** | two runs 0.139 / one run 0.308 |
| 0.25 | one run 0.238 | one run 0.316 | two runs 0.122 / one run 0.294 |
| 0.29 | one run 0.285 | one run 0.272 | two runs 0.113 / one run 0.275 |

The sculpt's collars **touch** from y ≈ 0.196 (both panels) to the top of the
fold. The model kept a 0.03 m gap the whole way, which halved the widest run of
every row in that band: yaw 180, t = 0.138 read ref 18.95 %H against render
7.57 %H, the largest single width deviation in the round-1 report after the
boots' own floor band. `cuffOutset` 0.030 → 0.008 with `cuffHalfX` 0.070 → 0.088
holds the outboard reach at 0.096 and takes the inboard reach from 0.040 to
0.080, past the 0.062 half-stance.

The two panels disagree about absolute width by up to 40 % (0.246 vs 0.330 at
y = 0.23) because the turnaround is a perspective render; every target above is
the mean of the two.

### Cuff depth vs cuff width: one number cannot do both

Side profile from `clay_0`, boot mass only (the runs behind it at z > +0.13 are
braid and hand, not boot):

| y | `clay_0` | render before | render after |
|---|---|---|---|
| 0.195 | 0.231 | 0.159 + a **detached** 0.038 | 0.218 |
| 0.235 | 0.199 | 0.216 | 0.206 |
| 0.275 | 0.179 | 0.187 | 0.189 |
| 0.295 | 0.176 | 0.173 | 0.173 |

The 0.195 row was the "18 % too shallow" reading: the only facets hanging that
low were the two either side of dead aft, and a lone arc of plates at radius
0.11 projects as a blob separated from the shaft by 0.026 m. A hollow ring
projects solid from −R to +R, but only if the ring goes most of the way round at
that height, so the fix is a more even hem: drop weight 0.35 + 0.65 g →
0.45 + 0.55 g, with g driven by the facet's reach past the shaft rather than by
its flare past the fold.

Across, the fold is 0.076 from the boot axis (clay_2 0.285 and clay_5 0.272 at
y = 0.29) where the shaft is 0.046 — nearly no taper. Fore-and-aft it *is* a
taper: 0.176 deep at the fold against 0.231 at the rim. So the fold radius is
interpolated toward the rim by a weight that is 0.25 across and 0.05
fore-and-aft. A single isotropic fraction big enough to fix the width put 15 %
too much depth into y = 0.235…0.295, costing yaw 90 more than yaw 0 gained.

### What the floor band cannot be fixed

`clay_1` (yaw 45) at y = 0.022 has two runs 0.097 and 0.105 wide with **0.111 m
of daylight** between them; the render has one run of 0.30. That is a camera
difference, not a modelling error. A boot 0.21 m long and 0.09 m wide projects
L·|sin(φ+ψ)| + W·|cos(φ+ψ)| = 0.20–0.22 m wide at ψ = 45°, so two of them split
only if their screen centres are more than 0.21 m apart; ours are
0.124·cos 45° = 0.088 apart, fixed by the stance the calf calibration sets.
The reference splits because it is a perspective camera looking down on a near
boot and a far one — which is also why only one boot touches the floor in every
reference panel below y ≈ 0.045. Reproducing it would need the stance widened
by 0.17 m, which `docs/PART_CONTRACT.md` and the round-1 findings both forbid.

### Score, same tree, same hour

| | yaw 0 | 45 | 90 | 180 | 270 | 315 | score |
|---|---|---|---|---|---|---|---|
| before | 44.3 | 31.0 | 49.9 | 47.5 | 31.2 | 34.9 | 39.80 |
| after | 46.4 | 31.1 | 52.0 | 50.5 | 31.6 | 34.1 | **40.95** |

widRMS core: yaw 90 2.62 → 1.76, yaw 180 3.35 → 2.49, yaw 270 3.88 → 3.19,
yaw 0 4.59 → 4.15. The splay is worth about +0.25 of that on its own (it lifts
yaw 0/90/180/270 and costs yaw 45/315, which merge either way).

## Pants, round 2: the trouser is 6 mm of cloth, not 17 (`pants`)

### The +156 % at the knee was mostly the braids, not the trouser

`out/findings_round1.md` lists the back view at t = 0.338 as ref 6.10 %H against
render 15.62 %H. The width term reads the *widest run*, and at that height the
round-1 braids hung down the centre line and welded the two leg runs into one.
Re-measured on the same tree after the braids were thinned, the same band reads
render 7.42 %H against ref 6.10 — a real error of **+22 %, not +156 %**. Worth
saying out loud: a width finding that is really a *run-count* finding names the
wrong part, and this one named pants for a hair defect.

The trouser was still too fat. Its own numbers, probed off the field rather than
the render (`out/pants_probe.ts`), gave a half-width of 0.0728 at y = 0.58 where
the spec asked for 0.0660: `smoothUnion(0.03)` over ten stacked capsules is a
max-radius blend on nearly colinear solids and inflated the tube by a further
3–7 mm. `loftY` at a 10 mm step with `blend: 0.006` puts the spec number on the
surface (probe: 0.0561 against 0.0550 asked).

### What the reference's trousered leg actually measures

**`clay_2` cannot be used for this.** Its matte bridges the gap between the legs
from y ≈ 0.42 to 0.90 — alpha 255 across the whole inseam, carrying the
backdrop's own colour (105,112,120) against the clay's 175. `body_2`, matted
from the same frame, keeps the gap open. That is why the front panel reports one
run 13.4 %H wide at the knee where the back panel reports two runs of 6.1: the
front number is matte damage, and no correct geometry can score against it.

Half-widths off `body_2` (front, model x = image x), against the radius
`body.ts` carries at the same height. Note `capsuleOval(a, b, r0, r1, squashZ,
squashX)` takes the **z** squash fifth and body.ts passes squashX = 1, so the
body's leg half-width *is* its radius and its depth is that times 1.06 (thigh) /
1.18 (calf):

| y | her right leg | her left leg | body radius | flare needed (right) |
|---|---|---|---|---|
| 0.50 | 0.0530 | 0.0479 | 0.0464 | +0.0066 |
| 0.58 | 0.0546 | 0.0421 | 0.0490 | +0.0056 |
| 0.62 | 0.0563 | 0.0446 | 0.0506 | +0.0057 |
| 0.66 | 0.0580 | 0.0437 | 0.0523 | +0.0057 |
| 0.70 | 0.0572 | (pistol) | 0.0539 | +0.0033 |
| 0.74 | 0.0622 | (pistol) | 0.0556 | +0.0066 |

**So: neither "the flare is negative" nor "the body is fat".** The body's leg
radius sits *between* the reference's two legs — 5 mm inside her right, 5 mm
outside her left. The round-1 note that the trousered thigh is "smaller than the
bare thigh radius the body carries" was measured against her left leg, and it is
true of that leg only. The width term scores the widest run, which is her right
leg, and reaching it takes a flat **+6 mm** standoff. That is what the table now
carries below y = 0.72; above it the reference's outline is the sash's low
corner, not the trouser, so the blouse over the seat stays where round 1 put it.

### Depth, and why the flare could not simply be turned down

Round 1 lofted the leg at a flat z-squash of 1.05 while the body runs 1.18
through the calf, so below the knee the cloth was 6 mm *shallower* than the shin
inside it — hidden only by the 17 mm flare. Matching `bodySquashZ` and adding
the flare as a standoff after the squash (not a scale) is what lets the flare
come down to 6 mm with no skin breaking out; checked by eye at the low LOD's
16.3 mm voxel in all six yaws.

Depth then lands on its own: leg depth at y = 0.62 comes out 0.125 against
`clay_0`'s 0.116, where round 1 measured 0.160.

### The inseam closed 100 mm too high

`body_2` shows the leg gap still open at y = 0.82 (18.5 mm) and closed by 0.86,
so the crotch point is at ~0.84. `inseamApexY` was 0.955, which cut a 24 mm slot
straight through the seat and left the buttocks bare in the back view. Moved to
0.865; the slot now measures 23 mm at y = 0.78 against the reference's 27, and
44 mm at y = 0.70 against 49.

The *visible* gap is still not the reference's. The reference's inseam gap at the
knee runs from −0.0286 to +0.0118 (40 mm, off-centre); ours is 26 mm and centred,
because the body's own legs come within 13 mm of the centre line and fill the
slot. That is the stance, not the garment.

### Result, both builds baked minutes apart off the same tree

| | yaw 0 | 45 | 90 | 180 | 270 | 315 | score |
|---|---|---|---|---|---|---|---|
| round-1 pants | 0.831 | 0.621 | 0.767 | 0.824 | 0.558 | 0.669 | 40.51 |
| round-2 pants | 0.824 | 0.609 | 0.763 | 0.817 | 0.559 | 0.673 | **41.45** |

(IoU per view; the score is the whole-character number.) Core width rms improved
in four views (45: 4.75→4.54, 270: 3.29→3.21, 315: 4.54→4.23, and the leg bands
of 180 from +1.3/+0.7 %H to +0.4/−0.3) and worsened only on `clay_2`, whose
bridged matte rewards a trouser that welds the legs together. The gain is mostly
the **landmark** term: yaw 90's landmark rms falls 5.90 → 1.52 and yaw 315's
4.60 → 3.05, because a leg with a real taper finally has a findable knee.

The shape term costs 0.006 of IoU per view. That is the round-1 trouser having
been fat enough to bridge the two legs at y = 0.75–0.88, which happened to
imitate the reference's single 0.39 m run there. The reference's run at that
height is sash, braid and hand — `clay_5` at y = 0.80 reaches x = −0.168 on the
braid side and +0.220 on the pistol side, where the trouser itself ends at
0.136. Inflating cloth to stand in for other parts' missing mass is not a fix,
so it was not made.

### Not fixable from this part

- **Leg axes.** Measured off `clay_5` and `body_2` alike, the reference's leg
  centres are at x = −0.086 and +0.052 (her right leg 34 mm further out than her
  left), against a symmetric `pose.stanceHalfW` of 0.062. A symmetric garment can
  match one leg's width or the other's, not both; it is matched to her right,
  which is the one the width term reads.
- **`clay_1` (yaw 45) wants the legs at different depths.** Its two leg runs are
  0.084 m apart, where two legs both at z = 0 and 0.138 m apart in x project to a
  0.098 m separation and therefore overlap. Reproducing it needs one foot forward
  of the other, i.e. a z stagger the skeleton does not have.
- **Below the hem** (t = 0.263–0.312) the render is 13 % narrow in the back view:
  that is bare calf. `body.ts` carries 0.0464 half-width at y = 0.50 where the
  reference has 0.0530.


## Hair, round 2: the braids were not too fat, they were hanging in the air (`hair`)

`braid_area_frac` — the share of the silhouette that `debraid` throws away —
was **0.127 at yaw 90 and 270** against a reference **0.044 / 0.034**, and
round 1 had *raised* it from 0.069 while trying to lower it. Measuring the
runs rather than the area says why. At yaw 90, row by row, in metres from the
frontmost pixel of each row:

| y | `clay_0` runs | round-1 render runs |
|---|---|---|
| 1.45 | one run, 0.188 | 0.102 + gap 0.058 + 0.049 |
| 1.40 | one run, 0.208 | 0.186 + gap 0.007 + 0.060 |
| 1.20 | one run, 0.255 | 0.191 + gap 0.037 + 0.047 |
| 0.80 | one run, 0.289 | 0.200 + gap 0.022 + 0.037 |
| 0.50 | 0.131 + gap 0.015 + **0.034** | 0.118 + gap 0.026 + **0.037** |

The braid's own width was already right — 0.034–0.060 against the reference's
0.034–0.049. What was wrong is that the render's plait was a **separate run**
at nearly every height from y 0.3 to 1.5, and `debraid` drops any run under
0.042 H (0.072 m) that is not 45 % of the row's core. `clay_0` is **one
continuous run from y 0.70 to the crown**: the reference plait *lies on* the
back. It only hangs free below the hip, and there it is 34 mm across.

Binding the area to height confirms it — the dropped area, by 0.1 m band:

| band | `clay_0` | round 1 | now |
|---|---|---|---|
| 0.10–0.30 | 0.0207 | 0.0043 | 0.0137 |
| 0.30–0.71 | 0.0220 | 0.0378 | 0.0225 |
| 0.71–1.01 | 0.0000 | 0.0235 | 0.0000 |
| 1.01–1.52 | 0.0000 | 0.0392 | 0.0028 |
| **total** | **0.0438** | **0.1145** | **0.0432** |

So the fix is the **z column of `BRAID_ROWS`**, not `braidR0`. It is set from
the body's own rearmost surface, probed shell by shell (`out/hair_backz.ts`
ray-marches every shell except `braids` and prints `backZ(x, y)`), as
`z = backZ − r + ~0.012`: the plait's front face overlaps the back by a
centimetre from the crown to the hip, rides the sash bustle at z −0.140 near
y 1.00, and only clears the calf below y 0.62. Round 1's two thin bands that
could not be closed this way — behind the neck at y 1.44–1.50, where the
reference packs the gathered plaits into the hollow — are filled by two extra
gather ellipsoids instead.

The braid also starts at the **crown**, y 1.695 rather than 1.620, and stands
~25 mm proud of the cap there, which is what makes the plait *visible* from
y 1.69 as `clay_5` has it instead of emerging from under the mass at y 1.55.

### The head volume, anchored on the nose rather than on the figure

Comparing head bands against the whole-figure centroid is useless here — the
assembled head sits ~60 mm behind where the reference's does, so every row
reads as displaced. Anchored instead on the frontmost pixel at y 1.56 (the
nose, z +0.0575 in this model), the depth of the head-and-hair band is:

| y | `clay_0` | round 1 | now |
|---|---|---|---|
| 1.70 | 0.1545 | 0.1361 | 0.1495 |
| 1.68 | 0.1764 | 0.1596 | 0.1730 |
| 1.66 | 0.1898 | 0.1730 | 0.1898 |
| 1.64 | 0.1915 | 0.1814 | 0.1999 |

and the whole band's area, y 1.44–1.72, in cm² of silhouette:

| view | reference | round 1 | now |
|---|---|---|---|
| yaw 0 (`clay_2`) | 464.7 | 470.6 | 471 |
| yaw 45 (`clay_1`) | 544.6 | 528 | 562 |
| yaw 90 (`clay_0`) | 503.9 | 459.2 | 508 |
| yaw 270 (`clay_4`) | 575.8 | 459.2 | 508 |

The front view was never short; the deficit was all depth, and it is closed by
the crest wave (which overhangs the brow to z +0.058) plus the plait now
starting at the crown. `clay_4` is still 12 % short and is left that way — see
below.

### The crest is a fin, and it points at her right front

`clay_1` and `clay_3` disagree about the crown by a factor of 2.4: at y 1.70
the top of the head is **0.161 m** wide seen from yaw 45 and **0.067 m** seen
from yaw 315. A blade is edge-on from 315 and broadside from 45 when its plane
contains the (−0.707, 0, +0.707) direction, i.e. when it runs from her left-
back to her right-front. `CREST_ROWS` is built along exactly that line
(x +0.014, z −0.086 at the root to x −0.045, z +0.058 at the tip) and kept thin
across it (`crestWideX` 1.3). Measured at y 1.70: yaw 45 0.161 against the
reference's 0.161, yaw 315 0.094 against 0.067. Round 1's three crown needles
gave 0.171 / 0.171 — no directionality at all — and separated at their roots
in the three-quarter views because each was its own solid; the crest is now one
mass smooth-unioned at k 0.022 with the strand read cut back into it as
grooves.

### The two side panels of the reference cannot both be satisfied

`clay_0` and `clay_4` are not consistent about the braid. At y 0.70 the braid
mass sits 0.07 m behind the leg's back edge in `clay_0` and 0.19 m behind it in
`clay_4`, and a silhouette is a union of projections, so no single static
object gives both. The drape here follows `clay_0` — hugging above the hip,
34–40 mm and clear of the calf below it — because that is the one that also
satisfies `braid_area_frac` on **both** panels: `clay_4`'s braid mass is
0.10–0.15 m across and therefore survives `debraid`, so it costs the reference
almost nothing there (0.034) either. Reproducing `clay_4` would add mass that
`clay_0` says is not there and would put yaw 90 back where round 1 had it.

### Not fixable from this part

- **`clay_4` (yaw 270) is 12 % short in the head band and 20 % short overall.**
  Band by band the deficit is in `boots` (−9 to −17 %H) and `knee/calf/pant hem`
  (−6 to −9 %H), not in hair. Adding braid mass to chase the total would land it
  in the wrong place.
- **The head sits ~60 mm behind the reference's** relative to the torso, so
  every side-view head metric taken against the whole silhouette reads as
  "the hair is missing its forward mass". Measured against the nose it is not,
  and growing the hair forward to chase the whole-figure alignment would detach
  it from the skull.
- **`braid_area_frac` at yaw 0 and 180 is 0.045 against 0.025 / 0.018**, and it
  is identical in the two views to four decimals — because in the front and back
  views what `debraid` drops is the **arms**, not the braids. The reference's
  arms touch the body at y 1.11–1.21 and 0.71–0.91; the render's hang clear.


## sash, round 2 -- read off the TEXTURED panels, not the clay

The clay turnaround cannot separate the mauve wrap from the striped trousers,
and round 1's three worst sash numbers all came from trying. Re-read at 4x on
`body_2` and `body_5` with `tools/grid.py --metres`:

| what | panel | value |
|---|---|---|
| mauve wrap, lateral extent | body_2 + body_5 | **her RIGHT only**; her left hip is striped trousers in front and khaki behind |
| flap low corner, her right front | body_2 4x | **y = 0.815**, a rounded corner ON the silhouette, cream-piped hem climbing inboard to the belt at about (x -0.06, y 1.03) |
| flap hem, her right rear | body_5 4x | y = 0.945 at the outer edge, ~1.02 near the spine |
| khaki apron, her left rear | body_5 4x | present from her left flank to the spine, hem y = 0.985; her x spans about +0.037 .. +0.145, i.e. bearing 1.9 .. 2.87 |

Round 1 had the flap corner at y = 0.912. That reading came from the second
silhouette run `body_2` carries at x = -0.17 .. -0.23 between y = 0.94 and
0.84: it is her right forearm hanging free, and the gap between it and the
body was taken for the hem.

### The front silhouette does NOT split between the thighs

Scanning the alpha of `clay_2` row by row (`out/sash_split.py`): from the
crotch at y = 0.94 down to **y = 0.19** the front silhouette is a single run.
The first genuine centre gap is y = 0.12, at the boot tops. The dark wedge
visible between the thighs on the panel is inside the alpha -- it is the
backdrop shadow `compare.py`'s REFERENCE MATTE WATCH warns about, not
background. The render splits at y = 0.71 (pants + sash alone: y = 0.82, gap
32 mm widening to 54 mm by y = 0.74), so the build has too MUCH daylight
between the legs, not too little, and the gap belongs to `pants.inseam`.

### The hip width deficit is the arms, not the cloth

`elongate` along x was tried on the whole sash at 10 mm and 18 mm per side to
close the 15-36 mm the front and back views are narrow across the hip band.
The full-figure outline did not move **at all** above y = 0.92: her forearms
sit 20-40 mm outside the wrap there and they, not the garment, are the
silhouette. Only below y = 0.89 did anything change. Anything aimed at the hip
band's width has to be the arms or `widths`, not a hip layer.

### compare.py's landmark term is knife-edged around this part

Sweeping only `sash.flapOut` (0 / 2 / 4 / 7 mm), seven bakes back to back with
round 1 and round 2 repeated as drift sentinels (they reproduced to 0.00):
score 41.37 / 41.40 / 40.89 / 41.03. The 4 mm dip is the **shoulder** landmark
at yaw 45 flipping by 4.8 %H -- 82 mm of figure height -- in response to a hip
apron that cannot touch it. The same flip is the entire cost of running the
khaki round to her left rear (41.40 with `canvas.wedge[1] = 2.90`, 41.53 with
1.85, IoU and colour both preferring 2.90). Treat a landmark move at one view
with no width or IoU move beside it as a detector flip, and check it before
reshaping anything to chase it.

### Method note: do not centre a panel on its alpha median

`sash_split.py` first took the median alpha column as x = 0. Braids and the
pistol pull that by ~15-20 mm, which is the same size as the flap being
measured, and it inverted the sign of the front-view comparison. Anchor on the
midpoint of the shin run at a fixed height (0.55 m works: only legs are there
in every view), or compare spans, which need no centre at all.

## The colour term is close to its structural ceiling

Worth recording, because the score makes it look like 8 of 10 points are lying
on the floor.

After the materials were re-authored from medians sampled off the reference and
the exposure re-calibrated, the *mean* colour deltas are small: `dL_rel` (the
global exposure offset removed) sits within ±5 L for most regions. But the
reported per-region ΔE is 18–30 everywhere, with almost no spread between views.

Those two facts together say the error is not in the average colour, it is in
the **spatial distribution**. The reference is a painted texture — weave in the
black fabric, dirt, seams, freckles, a specular highlight in the eye, gloss on
the lip. This model has no textures at all; every surface is one flat material
per geometry group. A per-pixel ΔE between a painted surface and a flat one
cannot go to zero however well the average is matched.

So the colour term behaves like SSIM does on a photograph of a cluttered room:
it rewards agreement in high-frequency detail that a reconstruction of this kind
does not attempt. Read `dL_rel` and the hue columns, which measure what the
materials actually control, and treat the ΔE column as a ceiling rather than a
target.

One real finding did come out of it: `hair_mass` read `dL_rel` +14.65, i.e. the
hair was 15 L too light once exposure was accounted for. The albedo had been
sampled off a *lit* part of the reference's crown and was then lit again by the
renderer. Scaling the hair albedo by 0.653 in sRGB took it to +8.3. The same
trap applies to every colour sampled from a render rather than from an albedo.

## Trouser leg section (round 3)

Read off the **clay** panels, which are the geometry target, with
`tools/pants_probe.py` (it puts a panel and a render through
`silhouette.normalize`, so a width in %H means what it means in `compare.py`)
and off a pants-only render in world metres with `tools/pants_abs.py`
(`tools/preview.ts --frame 1.80` fixes the mapping, so no normalisation is
involved on the render side).

Two readings that were being made wrongly before:

* **`clay_4`'s second run at leg height is a braid, not a second leg.** From
  t = 0.29 to 0.41 that panel shows two masses ~38 mm apart totalling
  0.33 m, which reads as a wide fore-aft stride. `clay_0`, the mirrored view,
  shows the legs as one 0.10-0.12 m run with a separate 0.03-0.06 m run behind
  it. A stride would appear in both. The wide run in `clay_4` carries visible
  plaiting at 3x and ends in a tassel at y = 0.20.
* **Hip-height side readings are not the garment.** At t = 0.44-0.51 `clay_4`
  is a single 0.33-0.39 m run holding the braids, the Zapper and both hands as
  well as the hip, so "the side view is 40 % narrow there" is a statement about
  the braids.

| y (m) | leg pair, across (clay_2 / clay_5) | leg pair, deep (clay_4 / clay_0) | her right leg alone (clay_5) | gap between the legs (clay_5) |
|---|---|---|---|---|
| 0.50 | 0.232 / 0.237 | 0.099 / - | 0.106 | 0.044 |
| 0.55 | 0.229 / 0.234 | 0.101 / - | 0.106 | 0.045 |
| 0.60 | 0.234 / 0.240 | 0.099 / 0.114 | 0.108 | 0.042 |
| 0.65 | 0.239 / - | 0.116 / 0.123 | 0.104 | 0.052 |
| 0.70 | - | 0.138 / - | 0.118 | 0.037 |

`clay_2` bridges the inseam and `clay_5` does not, but the two agree on the
outer-edge span to within 5 mm, which is what makes that column trustworthy.

Against those, the round-2 trousers measured 0.209 / 0.209 / 0.218 / 0.227 /
0.234 across and a flat 0.133 deep from y = 0.55 to 0.65: **25 mm narrow across
and 26-32 mm too deep at the calf**, i.e. the section was too round-and-fat
rather than too flat. The depth error survives at ~25 mm after the trouser is
brought down onto the skin, because `body.ts` builds the shin at squashZ 1.18
and the trouser cannot go inside it without showing skin through the cloth.

### The reference turnaround is not a consistent orthographic set

Under an orthographic camera the 45-degree span of a leg pair is fixed by the
front and side spans: `0.7071 * (dx + dz + 2*sqrt(a^2 + b^2))`. The front and
side panels above predict 0.195 m at y = 0.55; `clay_3` measures 0.155 m, and
`clay_0` and `clay_4` disagree with each other by 15 mm at the same height.
So the yaw 45 and yaw 315 leg-width columns cannot be driven to zero at the
same time as yaw 0/90/180/270, and chasing them breaks the four that agree.

## Boots, round 3 (`clay_0..clay_5`, per-row run decomposition)

Method: `out/boots_probe.py` normalises a reference panel exactly the way
`tools/silhouette.py` does (figure to 1024 px, soles on the base row, centroid
centred) and prints every horizontal run of a chosen row in metres.
`out/boots_raw.py` does the same for a `tools/preview.ts --frame 1.80` render,
which is already a metric frame, so the two are directly comparable without
normalising the render. `out/boots_fast.py` is the same comparison reduced to
one RMS number.

### The stagger is visible in the boot runs, not just in the lowest pixel

`clay_2` bottom-up: one run from y = 0.00 to 0.047 (her right boot alone,
0.103 m wide at 0.02 and 0.114 at 0.04), two runs from 0.06 up. That is
`pose.footLift` = 0.047 seen sideways, and it is the cleanest check that a part
is hanging off `skel.ankleL/R` rather than off an absolute height: a boot built
on `landmarks.footBed` puts two runs at y = 0.02 and merges them at every
three-quarter yaw.

### Per-boot width against the boot's OWN local height

Each panel's runs, with the lifted boot's heights reduced by its own lift, so
the two boots can be read as one shape. The near boot is inflated by perspective
in every panel, by up to 40 %, so the mean of the four readings is the target:

| local y | clay_2 planted / lifted | clay_5 planted / lifted | mean |
|---|---|---|---|
| 0.04 | 0.114 / 0.108 | 0.081 / 0.108 | 0.103 |
| 0.06 | 0.118 / 0.109 | 0.124 / 0.135 | 0.121 |
| 0.08 | 0.118 / 0.114 | 0.126 / 0.136 | 0.123 |
| 0.10 | 0.104 / 0.099 | 0.121 / 0.123 | 0.112 |
| 0.12 | 0.092 / 0.084 | 0.114 / 0.114 | 0.101 |
| 0.16 | 0.081 / -     | 0.101 / -     | 0.091 |

The boot is a compact block with a **ball** in it -- widest at 0.122 around
60-80 mm of local height, tapering to 0.091 at the ankle. The round-2 model was
a flat 0.096-0.104 from the floor to the fold, i.e. a tube.

### The cuff is widest at the FOLD, not at the hem

Following the planted boot's own axis on `clay_2` (it drifts from x = -0.066 at
y = 0.16 to -0.055 at 0.30 as the leg closes):

| y | panel run | boot axis | outer reach |
|---|---|---|---|
| 0.20 | -0.123 .. +0.061 | -0.060 | 0.063 (the hem) |
| 0.30 | -0.146 .. +0.126 | -0.055 | 0.091 (the fold) |

so laterally the collar *grows* on the way up. Fore and aft `clay_0` says the
opposite: 0.230 deep at y = 0.195 against 0.178 at 0.295. Both previous
versions had the lateral relation inverted and flared the collar downward and
outward into a bell.

`clay_2` also shows a **single** run of 0.171-0.183 at y = 0.18-0.20, so the two
hems meet across the 0.104 m stance rather than hanging clear of each other.

### Two rows the mirrored side panels agree on

`clay_0` and `clay_4` differ by up to 90 % through the cuff, but they agree
within 5 % at exactly two heights, and those are worth trusting:

| y | clay_0 | clay_4 | what it fixes |
|---|---|---|---|
| 0.02 | 0.222 | 0.220 | the sole slab is nearly as long as the leather, not 18 mm shorter |
| 0.14-0.16 | 0.187 / 0.171 | 0.198 / 0.170 | the shaft and instep were 19 % too deep fore-and-aft |

### The three-quarter panels are not at 45 degrees

Same conclusion the trouser section reaches, from the boot instead of the leg.
A boot 0.20 m long and 0.09 m wide cannot project narrower than about 0.19 m at
45 degrees off its own axis; `clay_1` and `clay_3` both read the boot at
0.10-0.11 m through the bottom 0.08 m, which is the width `clay_2` reads dead
ahead. Solving for the view angle from the boot's own plan outline puts
`clay_3` within about 15 degrees of frontal. The two side panels disagree the
same way: `clay_0` shows the two boots almost coincident fore-and-aft (0.239 m
total at y = 0.04) and `clay_4` shows them 0.15 m apart (0.361 m).

`clay_2` and `clay_5` also disagree about **which** foot is raised: `clay_2`
puts the lower run on image-left (her right, planted) and `clay_5` puts it on
image-left too, which in a back view is her *left*. `spec.pose.footLift` was
measured off `clay_2`, so the boots follow `clay_2`; the scoreboard's GROUND
CONTACT row for yaw 180 reports the resulting ref/render mismatch, and its
wording there assumes image-right is her left in every view, which is only true
in front views.

## Hair, round 3: the crown is an ellipse per height, and it can be solved (`hair`)

The six panels do not give six independent measurements of a horizontal slice
of the head. `tools/preview.ts` projects with `screen_x = cos(a)*x - sin(a)*z`,
so yaw 0 and yaw 180 both measure the support width along **X**, yaw 90 and
yaw 270 both measure it along **Z**, and the two three-quarter views measure
the diagonals. Four directions, and an ellipse has three parameters — so the
measurement is over-determined and carries its own check: for an ellipse

```
w45^2 + w315^2  ==  wX^2 + wZ^2
```

Off `ref/views/clay_*.png` that identity holds to **1 %** at y 1.64 and 1.66
and **2 %** at 1.68. The crown really is an ellipse per height, and its axes
and heading follow from the four widths rather than from sculpting.

Widths in metres, wX the mean of `clay_2`/`clay_5` and wZ the mean of
`clay_0`/`clay_4` (each pair shares a projection axis, so an orthographic
render gives them exactly mirrored silhouettes and the mean is the only
fittable target), with the ellipse solved from them:

| y | wX | wZ | w45 | w315 | long | short | heading |
|---|---|---|---|---|---|---|---|
| 1.600 | 0.2135 | 0.2196 | 0.2344 | 0.1904 | 0.2374 | 0.1936 | 41° |
| 1.620 | 0.2165 | 0.2174 | 0.2344 | 0.1850 | 0.2396 | 0.1916 | 44° |
| 1.640 | 0.2053 | 0.2124 | 0.2344 | 0.1796 | 0.2347 | 0.1794 | 41° |
| 1.660 | 0.1819 | 0.2103 | 0.2248 | 0.1662 | 0.2270 | 0.1610 | 32° |
| 1.680 | 0.1514 | 0.1953 | 0.2015 | 0.1394 | 0.2092 | 0.1319 | 27° |
| 1.700 | 0.1134 | 0.1581 | 0.1686 | 0.0724 | 0.1791 | 0.0759 | 31° |
| 1.710 | 0.0632 | 0.1265 | 0.1096 | 0.0362 | 0.1344 | 0.0436 | 21° |

Heading is degrees from straight ahead (+Z) toward her right (−X): a blade from
her left-back to her right-front, staying ~0.23 m long from y 1.60 to 1.66 and
thinning from 0.19 m across to 0.04 m by 1.71. That is the breaking wave.

### What it was, and what it is

Measured on the assembled render at 1000 px/m, in millimetres (render − ref):

| y | X before/after | Z before/after | 45 before/after | 315 before/after |
|---|---|---|---|---|
| 1.60 | −0.6 / −1.6 | −19.8 / −1.6 | +13.6 / +20.6 | +20.2 / +6.6 |
| 1.62 | −2.5 / −3.5 | −17.6 / −0.4 | +8.6 / +11.6 | +18.4 / +7.0 |
| 1.64 | −3.3 / −7.3 | −14.4 / +0.6 | −9.4 / +3.6 | +9.4 / −2.6 |
| 1.66 | −12.9 / −0.9 | −17.7 / −2.3 | −13.8 / +4.2 | +28.2 / −1.2 |
| 1.68 | −7.4 / −1.4 | −18.9 / −0.3 | −5.5 / +4.5 | +31.6 / −2.4 |
| 1.70 | −5.4 / −6.4 | −6.9 / +2.9 | +2.4 / +0.4 | +64.4 / +11.6 |

Mean |error| **14.7 mm → 4.4 mm**. Round 2 recorded the front view being
~13 mm narrow at y 1.66–1.68 and yaw 315 ~28 mm wide at the same heights as a
trade it could not win. It was not a trade: it was one error — a crown too fat
*across* its own blade and too short *along* it — and both ends of it close
together once the section is solved instead of sculpted.

### Three traps between a solved section and the surface

1. **`ellipsoid`'s field is only as good as its aspect ratio.** It reports
   `lip = max(r)/min(r)`, and a crown section is 0.11 m long by 0.012 m tall,
   so the field can under-report distance eightfold. `smoothUnion(k)` blends on
   *reported* distance, so a chain of ten such sections pushes the surface out
   by far more than k: the loft ended at y 1.7195 and the finished mass ran to
   y 1.734 with a **0.14 m-deep cap at y 1.72**, where the reference has a
   0.01 m point. A hard `union` at 8 mm spacing has no such term and its
   scallop is under 4 mm — a third of the low LOD's voxel.
2. **Anything unioned onto the crown is measured as crown.** The fringe's two
   locks on her left ran to (x +0.072, z +0.054), 37 mm outside the ellipse
   across the blade and therefore 26 mm of yaw-315 width; the axis-square cap
   sections carried material at (x +0.07, z +0.03) that a blade tilted 42°
   does not, worth 10 mm at every height from 1.61 to 1.67; and the plait
   standing 25 mm proud of the crown was 24 mm of yaw-315 width at y 1.70. The
   fringe is now `intersect`ed with the blade grown 3 mm, the cap stops at
   y 1.6050, and the plait root came down to y 1.686.
3. **The crown's layers run along the blade, not up it.** Grooves sunk to 0.8
   of the half thickness cut an 11 mm channel under a 35 mm half thickness and
   serrated the top of the head; riding them on the surface takes a scallop
   about one radius deep and leaves the silhouette alone.

### Asymmetric braids: measured, and it does not work

`braid_area_frac` cannot differ between yaw 90 and yaw 270 **for any object**.
An orthographic projection along +d and along −d gives exactly mirrored
silhouettes, and that metric is computed from the render alone, so the two
views return the same number whatever the geometry — symmetric or not. Only
the reference numbers differ (0.044 against 0.034), and they differ because
`clay_0` and `clay_4` are not a mirrored pair: at y 0.62 `clay_4` puts 0.19 m
of braid behind the leg where `clay_0` puts 0.07 m, and 0.14 m of z-extent
cannot be present and absent in one object. What asymmetry *can* do is move
mass in the plane, since yaw 45 measures (x − z)/√2 and yaw 315 measures
(x + z)/√2. Four drapes, each baked and scored against the same build of every
other part:

| drape | score | mean IoU | braid_area 90/270 |
|---|---|---|---|
| round-2, symmetric | **41.70** | **0.7092** | 0.034 / 0.034 |
| her left plait carried out in x only | 40.73 | 0.7092 | 0.034 / 0.034 |
| 15 mm further back, symmetric | 41.65 | 0.7080 | 0.048 / 0.048 |
| back + out in x | 40.63 | 0.7077 | 0.048 / 0.048 |
| 30 mm back + out and back | 41.35 | 0.7050 | 0.068 / 0.068 |

The x-only variant is the one that lands `braid_area_frac` on `clay_4`'s
number, and it is a full point **worse**. The yaw-45 deficit it was chasing is
not hair: `clay_1`'s two silhouette runs at y 0.4–0.8 are the two **legs**,
0.09 m apart in a projection where two legs at the same depth would overlap,
so that view is short of a z stagger in the stance. `BRAID_L_DELTA` keeps the
mechanism at zero, tunable from `spec/parts/hair.json`.

Tools: `out/hair_probe.ts` prints the four support widths of the assembled head
against the reference at any height without baking (a second or two per row);
`out/hair_meas.py` reads the same widths straight off a `--frame 1.80` render
or a reference panel; `out/hair_headcmp2.py` puts the six reference head bands
beside the render's at one metres-per-pixel.

## Head, round 3: the eye is drawn twice, and the second drawing has to fit (`head`)

### What the reference eye actually measures

`ref/views/head_1.png` at 2646 px/m, her left eye (image-right), read off a 5x
grid (`out/r3_head_refeye.png`):

| feature | columns / rows | mm |
|---|---|---|
| visible globe, inner to outer canthus | x 458 → 528 | **26.5** |
| visible globe, top of white to lower lid, at the pupil | y 327 → 353 | **9.8** |
| upper liner band, at the pupil | y 316 → 327 | **4.2** |
| liner, canthus to canthus (incl. the outer flick) | x 452 → 548 | 36.3 |
| iris | x 470 → 510 | 15.1 |

The number `spec.head.$comment` records as "eye aperture 0.0299 x 0.0121" is
the **liner** corner to corner, not the opening. That distinction cost a whole
iteration: the liner sits on the lid, *above* the opening, so an eye built to
show 12 mm of white and then darkened at the top for the lash comes out 4 mm
short. The opening has to be liner + white: 13.6 mm here, of which the top
3.4 mm is painted `brow`.

### Where the socket actually was

Measured by marching the head field itself rather than reading a render
(`tools/head_field.ts`, ~40 s, no bake):

| build | visible globe (w x h, mm) |
|---|---|
| round 2 (globe unioned into the head shell) | 20.5 x 11.0 |
| globe r 17 mm, orbit deepened to rz 20 mm | 21.8 x 12.0 |
| + `socketCut` | 22.0 x 12.0 (single row); 25.3 corner to corner |
| final (globe r 18 mm, aperture 36 x 13.6) | 24.0 x 12.0; **26.6 corner to corner** |

Deepening `orbit` alone cannot open the eye. Inside the opening the skin
climbs from z 0.0357 on the eye axis to 0.0424 eleven millimetres out — the
loft's own `smoothUnion` blends, not the orbit — and overtakes the globe there.
The orbit big enough to fix that hollows the brow and the cheekbone with it.
`socketCut` (the aperture lens intersected with the globe grown 1.2 mm, cut out
of the finished head) fixes it locally and changes nothing outside the opening.

### The skin is 3–5 mm in front of where the slice arithmetic puts it

`tools/head_brow.ts` rebuilds the head with the brow ridge and the lips set to
zero radius and marches for the bare surface. Along the brow line:

| x | y | z from the frontLoft ellipse | z measured |
|---|---|---|---|
| 0.0150 | 1.6045 | 0.0434 | **0.0467** |
| 0.0250 | 1.6068 | 0.0411 | **0.0442** |
| 0.0350 | 1.6058 | 0.0371 | **0.0401** |
| 0.0435 | 1.6025 | 0.0316 | **0.0352** |
| 0.0495 | 1.5992 | 0.0245 | **0.0298** |

Twenty-two smooth-unioned slices add 3.3–5.3 mm. A ridge authored by burying a
tube 6.6 mm below the *computed* surface is therefore flush with the real one,
which is exactly what happened: the first brow ridge painted two 4 mm squares
at the inner ends and nothing else. The lip curves were 4 mm out the same way
and the mouth corners vanished entirely. Both are now authored on the measured
column.

### What a 4.4 mm voxel will and will not hold

Materials are per **vertex**, so a band's edge is quantised to the voxel and a
band needs relief for the vertices to land on. Measured off `--matmap` renders
(`tools/head_preview.ts --matmap`, flat unlit one colour per material):

| feature | relief | painted band | verdict |
|---|---|---|---|
| brow ridge, 1.5 mm proud | 1.5 mm | 11 mm but **broken**, tail detached | too shallow to hold |
| brow ridge, 2.2 mm proud | 2.2 mm | 13 mm, continuous | keep |
| brow, no relief (round 2) | 0 | ragged blocks | the round-1 complaint |
| lip seam groove 3.2 mm deep into a 6 mm lip | — | lip torn into strips | trap 3 |
| lip seam groove 1.8 mm deep, 3.8 mm wide | — | reads as a seam | keep |
| nostril pit 4 mm | — | ragged black gash across the nose base | remove |
| nostril dimple, blend 4 mm, painted `skinShade` | soft | reads | keep |
| mentolabial crease 5 mm deep, 6 mm wide | — | black trench, ragged | too narrow |
| crease 1.5 mm deep, 8.3 mm wide | — | reads as a shadow | keep |
| ear helix / antihelix tubes at r 2.4–3.3 mm | — | shredded into facets | under one voxel |
| same at r 3.6–4.2 mm, blend 4 mm | — | reads as an ear | keep |

The rule that falls out: **at this voxel a crease has to be widened, not
deepened**, and a painted band needs about 2 mm of relief under it.

### Cost

`head.voxelScale` 0.42 and `head.eyeVoxelScale` 0.20; the globes are cut to a
front cap at `eye.backCut` (12 mm behind anything the skin ever exposes), which
is 40 % of their triangles for nothing visible.

| lod | head | eyes | total | round 2 head |
|---|---|---|---|---|
| low (4.4 / 2.1 mm) | 11 712 | 2 664 | 14 376 | 8 208 |
| medium (2.5 / 1.2 mm) | 36 420 | 8 452 | 44 872 | ~25 000 |
| high (1.9 / 0.9 mm) | 64 944 | 15 188 | 80 132 | ~44 700 |

## The leg-split height is confounded by the braids

A metric that looked decisive and was not. The front silhouette of `clay_2` is a
single run from the crotch down to y = 0.28, while the model splits into two
legs at y = 0.67. Read naively that says the reference's legs touch and ours do
not, and it drove both a stance change and a brief to fill the trousers between
the thighs.

Zooming `clay_2` between y = 0.62 and y = 0.22 shows the backdrop clearly
visible between the calves. **The reference's legs do not touch.** A braid hangs
down between them and bridges the gap, so the silhouette reads as one run.

The lesson generalises: any metric built on *run count* is really measuring
"is anything at all in the way", and on this character something usually is —
a braid, a sash corner, a boot cuff. Where a gap matters, measure the gap's
width directly at a stated height rather than counting runs.
