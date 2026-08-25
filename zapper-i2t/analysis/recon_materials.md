# Zapper — MATERIALS subsystem measurement report

Source: `ref/gun_pose{0,1,2,3}.png`, verified by template match to be exact,
loss-free native-resolution crops of `../jinx-i2t/ref/pose_gun_5view.jpg` at sheet
origins (42,150), (642,192), (1650,203), (2421,214) — all four match with
TM_CCOEFF_NORMED = 1.0000. Going back to the sheet therefore gains **no** extra
resolution; it only gains context. The 5th figure on the sheet holds no gun, so
there are exactly four gun views available.

All coordinates below are **crop-local pixel coordinates (x,y)** of the named pose.
Colour is reported as median BGR (as stored) and as CIE L\*a\*b\* (D65, via
`cv2.COLOR_BGR2LAB`, rescaled to L\*∈[0,100], a\*,b\*∈[−128,127]). Chroma
C\* = sqrt(a\*²+b\*²); hue angle h = atan2(b\*,a\*) in degrees.

Scripts written for this subsystem: `analysis/sample.py`, `analysis/parts.py`,
`analysis/regions_p3.py`, `analysis/families.py`, `analysis/graffiti.py`,
`analysis/graffiti2.py`, `analysis/graffiti3.py`, `analysis/_gunmask.py`,
`analysis/_mask.py`, `analysis/_grid.py`, `analysis/probe.py`. Background plane fits
in `analysis/_bgdist_*.npy`, gun masks in `analysis/_gun_*.npy`, pose3 part label map
in `analysis/_labmap_p3.npy`, sampled palette in `analysis/_parts.json`, graffiti
components in `analysis/_graffiti.json`.

---

## 0. Headline finding: no whole part is a flat colour sample

The instruction "reject any sample spanning more than about 14 L" rejects **every
whole part in this reference**. Per-part p5–p95 L\* spans in pose3:

| part | L\* p5 | L\* p50 | L\* p95 | span | highlight BGR / L\* | shadow BGR / L\* |
|---|---|---|---|---|---|---|
| lattice.collar   | 7.8  | 34.9 | 59.6 | **51.8** | (147,159,166) 65.1 | (3,14,28) 5.5 |
| rail.bar         | 18.0 | 34.1 | 61.2 | **43.1** | (85,152,174) 63.1 | (17,36,53) 16.7 |
| muzzle.bore      | 16.1 | 32.2 | 56.5 | **40.4** | (111,141,168) 59.6 | (35,32,30) 12.9 |
| muzzle.collar    | 20.0 | 37.6 | 60.0 | **40.0** | (127,155,171) 64.1 | (23,38,59) 17.8 |
| tube.copper      | 21.6 | 36.9 | 61.2 | **39.6** | (134,153,165) 63.5 | (31,37,52) 16.5 |
| tube.paint_blue  | 20.9 | 36.5 | 55.7 | **34.8** | (155,154,136) 62.7 | (50,42,44) 17.6 |

This is not sampling error — it is the texture. The artist has painted a 35–50 L\*
terminator ramp into every cylinder. Consequence: **lightness is not a material
identifier in this reference; hue angle and chroma are.** Every colour claim below is
therefore anchored on (a\*, b\*) at matched lightness, with L\* reported but never
used to discriminate.

The compliant samples in §1 were found automatically, not by eye: for each part
region, `best_patch()` in `analysis/sample.py` scans L\* windows of width 14 in 1 L\*
steps and returns the **largest 4-connected component** that fits inside one such
window. That is a genuine uniform-illumination patch, and its span is ≤ 14 by
construction rather than by selection bias in where I put the rectangle.

---

## 1. Material palette

### 1a. Compliant samples (L\* span ≤ 14)

| id | pose | region box (x0,y0)-(x1,y1) + predicate | n px | median BGR | L\* | a\* | b\* | C\* | h° | L\* span |
|---|---|---|---|---|---|---|---|---|---|---|
| brass.aged (muzzle collar) | p3 | (144,38)-(178,88), h 35–105, C≥7 | 387 | (63,87,113) | 39.6 | 7.0 | 18.0 | 20.2 | 69.0 | 12.5 |
| brass.aged (muzzle collar) | p1 | (40,62)-(78,106), same | 215 | (53,76,102) | 34.5 | 7.0 | 17.0 | 18.7 | 67.2 | 12.5 |
| brass.aged (lattice collar) | p3 | (20,26)-(52,88), h 35–105, C≥5, L≥24 | 392 | (55,80,107) | 36.5 | 7.0 | 19.0 | 21.2 | 67.6 | 12.5 |
| brass.yellow (top rail) | p3 | (114,30)-(172,40), h 45–110, C≥10 | 69 | (28,51,67) | 22.4 | 5.0 | 16.0 | 16.8 | 71.6 | 12.8 |
| brass.yellow (rear sight) | p3 | (14,17)-(36,31), h 35–110, C≥8 | 19 | (44,72,94) | 30.6 | 3.0 | 18.0 | 18.4 | 81.3 | 11.0 |
| tube.copper (warm tube) | p3 | (52,40)-(92,80), h 35–105, C≥5 | 524 | (59,78,99) | 34.9 | 6.0 | 15.0 | 16.2 | 67.6 | 12.9 |
| tube.copper (warm tube) | p1 | (128,64)-(152,96), same | 297 | (45,63,84) | 28.2 | 7.0 | 13.0 | 16.1 | 60.3 | 11.8 |
| paint.tube_blue | p3 | (102,42)-(152,80), h 190–320 | 389 | (87,77,69) | 32.5 | −1.0 | −7.0 | 7.1 | 260.5 | 12.5 |
| paint.tube_blue | p1 | (78,66)-(124,98), same | 523 | (92,83,73) | 34.5 | −1.0 | −7.0 | 7.3 | 256.0 | 11.8 |
| paint.frame_teal | p0 | (120,56)-(162,92), h 170–265, C≥4 | 310 | (74,68,55) | 28.2 | −3.5 | −5.0 | 6.4 | 236.3 | 10.6 |
| bore.liner | p3 | (160,42)-(190,84), h 180–300, L 28–66 | 53 | (119,109,94) | 44.7 | −4.0 | −6.0 | 7.8 | 234.5 | 11.9 |
| bore.liner | p1 | (42,66)-(78,104), same | 70 | (110,102,87) | 42.0 | −3.0 | −6.0 | 7.8 | 244.7 | 12.9 |
| bore.interior | p3 | (163,44)-(190,84), L ≤ 26 | 98 | (63,53,47) | 22.0 | 1.0 | −7.0 | 7.1 | 277.1 | 9.8 |
| bore.interior | p1 | (44,70)-(74,100), L ≤ 26 | 165 | (63,51,49) | 21.6 | 2.0 | −8.0 | 8.2 | 284.0 | 11.0 |
| mount.red (rail block) | p3 | (86,28)-(116,38), h 5–40, C≥10 | 25 | (78,86,139) | 41.6 | 21.0 | 14.0 | 24.4 | 34.3 | 6.4 |
| port.cylinder.tan | p0 | (133,48)-(152,80), h 30–95, C≥5 | 93 | (42,60,88) | 28.6 | 11.0 | 15.0 | 18.4 | 55.5 | 11.9 |
| knob.magenta | p3 | (32,78)-(44,90), h 300–15, C≥18 | 11 | (118,62,133) | 37.6 | 39.0 | −20.0 | 43.8 | 334.4 | 12.0 |

### 1b. Non-compliant but unavoidable: the accent paints

| accent | pose | n | median BGR | L\* | a\* | b\* | C\* | h° | span |
|---|---|---|---|---|---|---|---|---|---|
| accent.teal core (top-30 % C) | p3 | 43 | (197,210,71) | 76.9 | −40.0 | −3.0 | 40.0 | 184.3 | 27.0 ✗ |
| accent.teal core | p1 | 24 | (180,193,52) | 71.0 | −38.0 | −3.0 | 38.1 | 184.9 | 24.6 ✗ |
| accent.teal core | p0 | 19 | (187,188,56) | 70.2 | −37.0 | −4.0 | 37.1 | 186.2 | 26.0 ✗ |
| accent.magenta core | p3 | 22 | (136,71,194) | 49.8 | 54.5 | −11.0 | 57.2 | 349.2 | 27.2 ✗ |
| accent.magenta core | p1 | 13 | (127,72,198) | 49.0 | 54.0 | −5.0 | 54.1 | 353.0 | 10.3 |
| accent.magenta core | p0 | 13 | (121,71,172) | 45.5 | 47.0 | −7.0 | 47.4 | 351.3 | 19.8 |

Marked ✗ because they fail the ≤14 L\* rule. They fail it irreducibly: the marks are
2–7 px across, so **every** graffiti pixel is partly the substrate showing through
antialiasing, and no sub-patch of any mark is both pure and large enough to measure.
The values above are the top-30 %-chroma core of the accent mask, which is the closest
attainable estimate of the pure pigment. The reason to trust them anyway is cross-pose
agreement (hue reproduces to ±2° across three poses), not the span.

### 1c. Cross-pose reproducibility — the real evidence

Medians with 2000-sample bootstrap 95 % CIs, computed only over pixels inside a matched
lightness window, so lighting cannot drive any difference.

**Warm metals**, matched window L\* 30–42, hue predicate 35–110°, C\*≥8:

| region | box | n | b\* [95 % CI] | h° [95 % CI] | C\* |
|---|---|---|---|---|---|
| p3 rail + rear sight | (116,31)-(172,40) + (14,17)-(36,31) | 84 | 21.0 [19.0, 22.0] | **81.1 [79.0, 82.7]** | 21.4 |
| p1 rail | (56,56)-(128,70) | 204 | 22.0 [21.0, 23.0] | **77.7 [76.0, 79.1]** | 22.9 |
| p3 muzzle collar | (146,40)-(174,86) | 376 | 18.0 [18.0, 18.0] | 68.2 [66.8, 69.8] | 20.2 |
| p1 muzzle collar | (42,64)-(78,106) | 281 | 17.0 [17.0, 18.0] | 68.6 [67.2, 69.5] | 18.8 |
| p3 lattice collar | (22,28)-(52,88) | 522 | 19.0 [19.0, 20.0] | 64.6 [63.4, 65.8] | 21.6 |
| p1 lattice collar | (150,52)-(186,112) | 415 | 18.0 [18.0, 18.0] | 65.0 [64.7, 66.0] | 20.2 |
| p3 warm tube | (56,40)-(86,82) | 418 | 15.0 [15.0, 16.0] | 67.2 [66.8, 68.2] | **16.8** |
| p1 warm tube | (128,64)-(152,96) | 197 | 15.0 [14.0, 16.0] | 71.6 [67.6, 74.1] | **16.8** |

Two conclusions, each reproduced independently in two poses with non-overlapping CIs:

1. **There are two brass tones, not one.** Top rail + rear-sight hook sit at
   h ≈ 78–81°; muzzle collar + lattice collar sit at h ≈ 65–69°. The rail is the
   cleaner, yellower gold; the collars are the redder, patinated brass. Δh = 16.5° in
   pose3 and 12.7° in pose1.
2. **The warm tube section is not brass.** Its hue is inside the collar-brass band
   (67–72°) but its chroma is 16.8 in *both* poses against 19–22 for every brass part.
   It is a **desaturated warm brown**, distinguished from brass by chroma, not hue.

**Cool paints**, matched window L\* 28–44, C\* 3–16, h 180–310:

| region | box | n | a\* [95 % CI] | b\* [95 % CI] | h° | C\* |
|---|---|---|---|---|---|---|
| p3 tube blue | (104,42)-(152,80) | 559 | −2.0 [−2.0, −1.0] | −7.0 [−7.0, −7.0] | 256.0 | 7.3 |
| p1 tube blue | (78,66)-(124,98) | 570 | −2.0 [−2.0, −1.0] | −7.0 [−7.0, −7.0] | 254.1 | 7.3 |
| p0 tube blue | (38,58)-(72,88) | 405 | −1.0 [−2.0, −1.0] | −7.0 [−7.0, −7.0] | 256.0 | 7.2 |
| p0 frame body | (120,56)-(162,92) | 408 | **−4.0 [−4.0, −3.0]** | **−5.0 [−5.0, −5.0]** | 236.3 | 7.2 |
| p3 bore liner | (162,44)-(188,84) | 91 | −1.0 [−1.0, −1.0] | −6.0 [−6.0, −6.0] | 261.9 | 6.4 |
| p1 bore liner | (42,66)-(78,104) | 109 | −2.0 [−3.0, −1.0] | −7.0 [−7.0, −6.0] | 254.7 | 7.6 |

3. The tube paint is the most reproducible number in the whole reference:
   a\* = −1 to −2, b\* = −7 in **three** independent poses.
4. **The frame is a different paint from the tube.** a\* = −4 vs −1, measured in the
   *same image* under the *same light* (pose0), CIs disjoint. The frame is the greener,
   teal-leaning one; the tube is the bluer one.
5. **The bore liner cannot be separated from the tube paint by colour.** Δa\* ≤ 1,
   Δb\* ≤ 1. Only L\* differs (42–45 vs 33–36), and lighting alone explains that.
   Whether the liner is bare steel or the same paint is below the resolution of the
   reference.

**Red rail-mount block**, corroborated in three poses (h 5–45, C\*≥12):

| pose | box | n | L\* | a\* | b\* | C\* | h° |
|---|---|---|---|---|---|---|---|
| p3 | (86,28)-(116,38) | 25 | 41.6 | 21.0 | 14.0 | 24.4 | 34.3 |
| p1 | (96,52)-(124,64) | 46 | 24.7 | 17.0 | 14.0 | 21.7 | 39.3 |
| p0 | (78,48)-(104,58) | 22 | 26.3 | 16.0 | 13.0 | 19.8 | 38.9 |

### 1d. Is there bare steel anywhere? No.

Achromatic pixels (C\* < 3) are 3.0 % of the pose3 gun mask and 3.3 % of pose1, and
they are **not spatially clustered**: 5.3 % of `tube.paint_blue`, 7.8 % of
`tube.midband`, 4.6 % of `rail.mount.red`, 3.8 % of `rearsight.hook`, 2.3 % of
`rail.bar`, 1.4 % of `lattice.collar`, 1.2 % of `tube.copper`, 0.2 % of
`muzzle.collar`. Their median L\* (33.7) is essentially the gun's own median L\*
(35.3), so they are not simply specular highlights either — they are the low-chroma
tail of the blue paint along its specular streak. **There is no achromatic bare-metal
material zone on this gun.**

### 1e. Is the warm tube section wood? No evidence for it.

Removing the smooth cross-axis shading (per-row median along the barrel axis) and
measuring the residual:

| region | box | row-profile L\* range | residual sd | \|R\| p95 |
|---|---|---|---|---|
| tube.copper | (58,44)-(86,78) | 37.6 | **7.18** | 17.06 |
| tube.paint_blue | (104,46)-(150,78) | 34.1 | **9.19** | 17.25 |
| lattice.collar | (24,34)-(48,78) | 23.1 | 13.57 | 27.25 |
| muzzle.collar | (150,46)-(168,80) | 28.4 | 9.78 | 20.28 |

The warm tube section is **smoother** than the blue-painted section, not rougher.
There is no grain signal. The test rules out wood grain; it cannot separate copper
from worn or dirty brown paint, since both would be smooth.

---

## 2. Spatial distribution

### 2a. Part-by-part area, pose3 (the barrel is almost fully clear of the hand)

Nine hand-drawn polygons (`analysis/regions_p3.py`) intersected with the gun mask,
overlay verified visually. 8020 of 8517 mask pixels assigned; the 497 unassigned are
the JPEG ringing fringe hugging the silhouette.

| part | material | n px | % of assigned | median BGR | L\* | a\* | b\* | C\* | h° |
|---|---|---|---|---|---|---|---|---|---|
| tube.paint_blue | paint.tube_blue | 2186 | **27.3 %** | (89,85,84) | 36.5 | −1 | −5 | 7.8 | 239.0 |
| lattice.collar | brass.aged | 1954 | **24.4 %** | (57,77,100) | 34.9 | 8 | 17 | 20.1 | 66.8 |
| tube.copper | tube.copper | 1231 | **15.3 %** | (64,83,101) | 36.9 | 5 | 14 | 16.2 | 69.4 |
| rail.bar | brass.yellow | 857 | **10.7 %** | (59,79,96) | 34.1 | 3 | 20 | 21.2 | 83.2 |
| muzzle.bore | bore.liner + interior | 526 | 6.6 % | (72,73,78) | 32.2 | 1 | −4 | 8.5 | 225.0 |
| muzzle.collar | brass.aged | 523 | 6.5 % | (63,83,107) | 37.6 | 6 | 17 | 19.0 | 72.5 |
| tube.midband | brass.aged | 372 | 4.6 % | (80,85,97) | 37.3 | 3 | 6 | 9.2 | 79.6 |
| rail.mount.red | mount.red | 238 | 3.0 % | (58,76,108) | 36.3 | 9 | 17 | 23.9 | 57.2 |
| rearsight.hook | brass.yellow | 133 | 1.7 % | (75,72,70) | 30.6 | 1 | −2 | 10.6 | 216.9 |

Two of these polygon medians are contaminated and must **not** be read as material
colour: `tube.midband` (a 7–9 px wide ring; the polygon still swallows the tube's
specular streak) and `rearsight.hook` (a 1–2 px wide bar). Their material colours are
the compliant samples in §1a.

Rolling up by material: **brass 47.9 %** (lattice 24.4 + rail 10.7 + collar 6.5 +
midband 4.6 + rear sight 1.7), **blue tube paint 27.3 %**, **warm-brown tube 15.3 %**,
**bore 6.6 %**, **red mount 3.0 %**.

### 2b. Hue-family fractions — independent, polygon-free cross-check

Classifying every gun-mask pixel by hue and chroma only (`analysis/families.py`):

| family | pose3 | pose1 | pose0 | pose2 |
|---|---|---|---|---|
| warm metal (h 30–110, C≥10) | **54.5 %** | **55.3 %** | 44.4 % | 46.7 % |
| cool paint (h 190–300, 3≤C<16) | **24.9 %** | **24.9 %** | 28.1 % | 32.0 % |
| teal accent (h 150–215, C≥16, L>35) | 1.64 % | 1.06 % | 1.04 % | 1.16 % |
| magenta accent (h 300–15, C≥24) | 0.85 % | 0.58 % | 0.68 % | 0.37 % |
| red/orange (h 5–40, C≥12) | 1.66 % | 1.54 % | 1.63 % | 0.52 % |
| near-neutral (C<3) | 2.98 % | 3.29 % | 3.82 % | 3.81 % |
| unclassified (low-chroma darks, terminators) | 14.6 % | 14.4 % | 21.4 % | 15.9 % |
| gun-mask px | 8517 | 7200 | 6072 | 2675 |

warm-metal : cool-paint = **2.19 (p3), 2.22 (p1)** for the barrel assembly alone;
**1.58 (p0), 1.46 (p2)** for views that include the frame. The drop is explained
entirely by the frame being cool-painted — consistent, and a useful internal check.

### 2c. Where the material seams are along the barrel

Per-column median hue/chroma over a 16 px band centred on the tube axis (pose3 axis
tilt +2.8°, pose1 −8.0°). Seams are where the warm-pixel fraction flips:

| zone | pose3 x-range | px | pose1 x-range | px |
|---|---|---|---|---|
| lattice collar (brass, C≈21) | 21 → 54 | 33 | 151 → 179 | 28 |
| warm tube (C≈17) | 54 → 85 | 31 | 127 → 151 | 24 |
| brass mid-band (narrow) | 85 → 93 | 8 | 121 → 127 | 6 |
| blue painted tube | 93 → 145 | 52 | 83.5 → 121 | 37.5 |
| muzzle collar (brass) | 145 → 167 | 22 | 63 → 83.5 | 20.5 |
| bore (liner + interior) | 167 → 184 | 17 | 44 → 60 | 16 |

Scale-free ratios (these survive the scale chain being wrong):

- blue zone / warm tube zone = 52/31 = **1.68** (p3), 37.5/24 = **1.56** (p1)
- warm tube zone / mid-band width = 31/8 = **3.9** (p3), 24/6 = **4.0** (p1)
- lattice / warm tube = 1.06 (p3), 1.17 (p1)
- axial fractions of the 163 px lattice-rear → bore-rim length (p3): lattice 0.20,
  warm tube 0.19, mid-band 0.05, blue 0.32, collar 0.14, bore 0.10

Ordering is identical in both poses, so the material zoning along the barrel is:
lattice brass → warm brown → thin brass ring → blue paint → brass collar → dark bore.

### 2d. Parts whose material cannot be measured at all

- **Grip.** Occluded by the black glove in poses 0, 1 and 2, and by hand + shirt in
  pose 3. The 5th figure on the sheet holds no gun. Zero usable pixels. The brief's
  "dark red-brown wood with brass pins and a lighter grey inlaid panel" is **not
  verifiable from this reference**.
- What is visible in pose1 at (190,45)-(215,70) is a tan slab with light chevron
  notches floating above the wrist. I cannot determine whether it belongs to the gun,
  the glove or the costume, and I have deliberately excluded it from every measurement.
- **Trigger, trigger guard, hammer.** ≤ 4 px each, all partly behind fingers.
- **Rail studs / grip pins.** 1–2 px each; below the resolution that can settle colour.
- **Frame paint** is measurable in pose0 only (n=408, a single lighting condition).
- **Cylindrical top port** (pose0, x 133–152, y 48–80): tan, h 55.5, C\* 18.4, n=93.
  One pose only; statistically indistinguishable from `brass.aged` at this sample size.

---

## 3. The graffiti marks

### 3a. Pigments

See §1b. Both accents are far more chromatic than anything structural on the gun: the
most chromatic structural material is lattice brass at C\* = 21.6, against teal 37–40
and magenta 47–57. The teal is consistently about 24 L\* lighter than the magenta:
27.1 (p3), 22.0 (p1), 24.7 (p0).

### 3b. Count and size

Connected components ≥ 3 px in the accent masks:

| pose | teal px | magenta px | coverage of gun mask | teal/magenta area | marks ≥3 px | component areas (px) |
|---|---|---|---|---|---|---|
| p3 | 140 | 72 | **2.49 %** | 1.94 | **16** | 38,33,25,21,13,12,11,8,7,7,7,6,6,4,4,4 |
| p1 | 76 | 42 | 1.64 % | 1.81 | 10 | 27,17,13,13,10,7,7,6,4,4 |
| p0 | 63 | 41 | 1.71 % | 1.54 | 12 | 24,12,12,8,8,6,5,5,4,4,3,3 |
| p2 | 31 | 10 | 1.53 % | 3.10 | 4 | 16,14,5,5 |

Equivalent circular diameters in pose3: 7.0, 6.5, 5.6, 5.2, 4.1, 3.9, 3.7, 3.2, 3.0,
3.0, 3.0, 2.8, 2.8, 2.3, 2.3, 2.3 px — a steep, roughly power-law size distribution.
Median 3.0 px, max 7.0 px, max/median = 2.33. At the brief's provisional 0.838 mm/px
that is a median mark ≈ 2.5 mm and a largest mark ≈ 5.9 mm across.

Pose2's teal/magenta ratio of 3.10 comes from a 4-mark sample and should be ignored;
the three usable poses give 1.54–1.94.

Mark positions in pose3 (bbox origin, w×h, centroid) — teal: (23,34) 4×4 (24.3,35.6);
(17,38) 4×3 (18.8,38.7); (168,42) 5×2 (169.8,42.8); (82,45) 6×3 (84.7,45.9);
(75,52) 3×4 (76.0,53.7); (46,59) 3×6 (47.5,62.0); (52,59) 6×10 (53.6,63.4);
(124,68) 9×9 (128.3,71.3); (55,70) 2×3 (55.5,71.0); (118,70) 5×5 (120.6,71.4).
Magenta: (103,47) 11×4 (108.2,48.1); (119,50) 5×3 (121.3,50.7); (108,52) 2×3
(108.8,53.0); (153,67) 3×3 (153.7,67.9); (157,66) 2×2 (157.5,66.5); (37,81) 6×5
(39.6,83.0) — the last of these is the knob discussed in §3d, not a splatter.

### 3c. Do the marks follow the form, or ignore it?

Three independent tests, all pointing the same way: **they ignore it.**

**(i) Orientation is uncorrelated with the barrel axis.** For each mark ≥3 px, the
principal axis was found by PCA on its pixel coordinates and compared to the projected
barrel axis in that pose (p3 +2.8°, p1 −8.0°, p0 −6.0°). Pose3, all 16 marks,
|Δangle| in degrees: 52, 19, 2, 22, 59, 75, 90, 22, 55, 57 (teal) and 4, 7, 87, 62,
87, 38 (magenta). Mean 46°. A uniform random distribution gives 45°. There is no
preference for the axis and none for the circumferential direction either.

**(ii) Marks sit on brass as readily as on paint — they are not confined to the
painted tube.** Assigning each graffiti pixel to the pose3 part label map:

| substrate | part area share | graffiti px on it | graffiti px per 100 substrate px |
|---|---|---|---|
| brass (lattice + collars + mid-band + rail) | 47.9 % | 67 (88 incl. the knob) | **1.74** |
| blue tube paint | 27.3 % | 95 | **4.34** |
| warm tube | 15.3 % | 24 | **1.96** |

Marks confirmed sitting entirely on brass: teal at (24.3, 35.6) inside the lattice
collar; teal at (169.8, 42.8) on the muzzle-collar face; magenta at (157.5, 66.5) on
the muzzle collar. So there **is** a density bias toward the painted tube — about
2.5× — but graffiti on brass is not rare: it is roughly a third of the total.

**(iii) At least two marks straddle a component seam.** Magenta A=7 at (153.7, 67.9)
has 3 px on `tube.paint_blue` and 4 px on `muzzle.collar`. Teal A=33 at (53.6, 63.4)
sits on the lattice collar with a dilated ring landing 63 px on the collar and 18 px
on the warm tube. A decal that respected the assembly could not do this. The marks
read as applied to the finished object, across seams.

### 3d. One magenta element that is probably not graffiti

Pose3 (37,81)-(42,85), 21 px, median Lab (37.6, 39.0, −20.0), C\* 43.8. It is a
compact rounded blob with its own specular rim — (162,147,204) at (37,83) and
(155,154,186) at (37,84) — sitting at the 7-o'clock position of the lattice collar,
and it recurs in pose2 at (78,93). Splatters elsewhere in this reference do not carry
specular rims. It reads as a **magenta-painted knob or bolt head**, roughly 5×5 px
(≈ 4 mm at the provisional scale). I cannot rule out a large paint dab on a rounded
surface; confidence is low, and I have excluded it from the graffiti counts wherever
noted.

---

## 4. Falsifiable constraints

Checking-method abbreviations:

- **[MAT]** read the named material's baseColor from the built scene, convert
  sRGB→CIE Lab (D65), compare. No render needed.
- **[SIL]** render the built model from a camera reproducing the named pose, downsample
  the silhouette to the reference's pixel count, classify pixels by the hue/chroma
  predicates in §2b, compare fractions/counts.
- **[BBOX]** take per-mesh world-space axis-aligned bounding boxes, project their
  extents onto the barrel axis, compare lengths.

| id | kind | value | tol | how checked | evidence | conf |
|---|---|---|---|---|---|---|
| `mat.brass.yellow.hue` | angle | h = 79° | ±6° | [MAT] on `rail.bar`, `rearsight.hook` | p3 (116,31)-(172,40)+(14,17)-(36,31), L\* 30–42, n=84, boot median 81.1 [79.0,82.7]; p1 (56,56)-(128,70), n=204, 77.7 [76.0,79.1] | 0.75 |
| `mat.brass.aged.hue` | angle | h = 66.5° | ±5° | [MAT] on `muzzle.collar`, `lattice.collar`, `barrel.midband` | p3 collar n=376 68.2 [66.8,69.8], lattice n=522 64.6 [63.4,65.8]; p1 collar n=281 68.6 [67.2,69.5], lattice n=415 65.0 [64.7,66.0] | 0.80 |
| `mat.brass.two_tones` | relation | h(yellow brass) − h(aged brass) ≥ 8° | — | [MAT], difference of the two above | Δ = 16.5° (p3), 12.7° (p1); bootstrap CIs disjoint in both poses | 0.85 |
| `mat.brass.count` | count | 2 distinct brass materials | exact | [MAT] count materials with h ∈ [55,95] and C\* > 15 | as above | 0.70 |
| `mat.warm_tube.chroma_ratio` | ratio | C\*(yellow brass) / C\*(warm tube) = 1.31 | ±0.15 | [MAT] | p3 21.4/16.8 = 1.27; p1 22.9/16.8 = 1.36 | 0.70 |
| `mat.warm_tube.not_brass` | relation | C\*(warm tube) ≤ C\*(aged brass) − 2.0 | — | [MAT] | p3 16.8 vs 20.2; p1 16.8 vs 18.8 | 0.75 |
| `mat.warm_tube.hue` | angle | h = 68° | ±6° | [MAT] | p3 67.2 [66.8,68.2]; p1 71.6 [67.6,74.1] | 0.70 |
| `mat.paint.tube.ab` | dimension (Lab units) | a\* = −1.5, b\* = −7.0 | ±1.5 each | [MAT] on the blue tube material | p3 n=559, p1 n=570, p0 n=405; bootstrap CI a\* [−2,−1], b\* [−7,−7] in all three | **0.90** |
| `mat.paint.frame.greener` | relation | a\*(frame paint) ≤ a\*(tube paint) − 1.5 | — | [MAT], difference of the two paints | pose0 frame a\* = −4.0 [−4,−3] vs pose0 tube a\* = −1.0 [−2,−1], same image, same light, n = 408 / 405 | 0.70 |
| `mat.paint.count` | count | 2 distinct body paints (blue tube, teal frame) | exact | [MAT] count materials with C\* < 12 and h ∈ [200,300] | as above | 0.60 |
| `mat.bore.interior.L` | dimension (L\*) | L\* = 21.5 | ±3 | [MAT] on the innermost bore mesh | p3 n=98 L\* = 22.0; p1 n=165 L\* = 21.6 | 0.80 |
| `mat.bore.darkest` | relation | L\*(bore interior) ≤ min(L\* of every exterior material) − 8 | — | [MAT] over all materials | exterior minimum 34.1 (rail); 34.1 − 21.6 = 12.5 | 0.80 |
| `mat.no_bare_steel` | relation | no material with C\* < 3 covers > 2 % of visible area | — | [SIL] | achromatic px = 3.0 % (p3) / 3.3 % (p1), spread over every part, max 5.3 % within any one part, median L\* 33.7 ≈ gun median 35.3 | 0.70 |
| `mat.accent.teal.hue` | angle | h = 185° | ±6° | [MAT] | 184.3 (p3) / 184.9 (p1) / 186.2 (p0) | 0.80 |
| `mat.accent.magenta.hue` | angle | h = 351° | ±6° | [MAT] | 349.2 / 353.0 / 351.3 | 0.80 |
| `mat.accent.teal.chroma` | dimension (C\*) | C\* = 38 at L\* ≈ 73 | ±5 | [MAT] | 40.0 / 38.1 / 37.1 | 0.75 |
| `mat.accent.magenta.chroma` | dimension (C\*) | C\* = 53 at L\* ≈ 48 | ±8 | [MAT] | 57.2 / 54.1 / 47.4 | 0.70 |
| `mat.accent.L_gap` | dimension (L\*) | L\*(teal) − L\*(magenta) = +24 | ±6 | [MAT] | 27.1 (p3), 22.0 (p1), 24.7 (p0) | 0.75 |
| `mat.accent.outchroma` | relation | C\* of each accent ≥ 1.7 × C\* of every structural material | — | [MAT] | max structural C\* = 21.6; teal/21.6 = 1.76, magenta/21.6 = 2.45 | 0.75 |
| `mat.mount.red.hue` | angle | h = 37° | ±7° | [MAT] on the rail mount block | p3 34.3 (n=25), p1 39.3 (n=46), p0 38.9 (n=22) | 0.70 |
| `mat.count.total` | count | 7 structural materials + 2 accent paints = 9 | — | [MAT] count material slots | DECLARED split (the material / material-variant boundary is a choice). Measured clusters: yellow brass, aged brass, warm brown tube, blue paint, teal paint, red mount, dark bore, + teal and magenta accents | 0.50 |
| `zone.blue_over_warm.length` | ratio | 1.62 | ±0.12 | [BBOX] axial extent of the blue-paint tube mesh ÷ that of the warm tube mesh | p3 seams x = 93,145 (52 px) and x = 54,85 (31 px) → 1.68; p1 (37.5)/(24) → 1.56 | 0.75 |
| `zone.warm_over_midband.length` | ratio | 3.95 | ±0.50 | [BBOX] | p3 31/8 = 3.9; p1 24/6 = 4.0 | 0.65 |
| `zone.axial_fractions` | ratio (6-vector) | lattice 0.20, warm 0.19, midband 0.05, blue 0.32, collar 0.14, bore 0.10 | ±0.03 each | [BBOX], normalised by the lattice-rear → bore-rim axial length | p3 seam scan, 163 px total | 0.60 |
| `zone.order` | relation | along the barrel axis, muzzle → breech: brass collar, blue paint, thin brass ring, warm brown, brass lattice | — | [BBOX] sort meshes by axial centroid, compare material sequence | identical ordering measured in p3 and p1 seam scans | 0.85 |
| `area.warm_to_cool` | ratio | visible warm-metal area ÷ visible cool-paint area = 2.20 for a barrel-only view | ±0.25 | [SIL] from a pose3 or pose1 camera, using the §2b predicates | 2.19 (p3), 2.22 (p1) | 0.75 |
| `area.brass_share` | ratio | brass parts = 0.48 of assigned visible area from a pose3 camera | ±0.05 | [SIL] | §2a rollup, 3839/8020 | 0.65 |
| `graffiti.coverage` | ratio | graffiti area ÷ visible gun area = 0.019 | ±0.008 | [SIL] classify by the accent predicates, divide by silhouette area | 0.0249 / 0.0164 / 0.0171 / 0.0153 across the four poses | 0.75 |
| `graffiti.count.per_view` | count | 13 marks ≥ 3 px in a 236×118 render | ±5 | [SIL] connected components of the accent mask, ≥ 3 px | 16 (p3), 10 (p1), 12 (p0) | 0.70 |
| `graffiti.teal_magenta_area` | ratio | 1.8 | ±0.5 | [SIL] | 1.94 / 1.81 / 1.54 (p2's 3.10 is a 4-mark sample, excluded) | 0.65 |
| `graffiti.size_max_over_median` | ratio | max equivalent diameter ÷ median = 1.9 | ±0.6 | [SIL] connected components, sqrt(4A/π) | p3 7.0/3.0 = 2.33; p1 5.9/3.6 = 1.64; p0 5.5/3.2 = 1.72 | 0.50 |
| `graffiti.on_metal` | relation | ≥ 25 % of graffiti area lies on brass parts | — | in-scene: for each paint island, look up the host mesh; or [SIL] intersect the accent mask with per-part masks | p3: 67/212 = 32 % excluding the knob (41 % including it); individually confirmed marks at (24.3,35.6), (169.8,42.8), (157.5,66.5) | 0.80 |
| `graffiti.density_bias` | ratio | density on blue paint ÷ density on brass = 2.5 | ±1.0 | [SIL] graffiti px per substrate px, per material | p3: 4.34 % vs 1.74 % = 2.49 | 0.55 |
| `graffiti.orientation_random` | angle | mean \|mark axis − barrel axis\| ∈ [35°, 55°] | — | [SIL] PCA per connected component, compare to the projected barrel axis | p3, 16 marks, mean 46.0° (uniform expectation 45°) | 0.60 |
| `graffiti.crosses_seam` | count | ≥ 1 paint island spans two different meshes | — | in-scene: per paint island, count distinct host meshes | p3 magenta A=7 at (153.7,67.9): 3 px on tube paint + 4 px on muzzle collar; teal A=33 at (53.6,63.4) ring spans lattice collar and warm tube | 0.70 |
| `knob.magenta.count` | count | 1 discrete magenta-painted solid element on the lattice collar | ±1 | [SIL] find a magenta region ≥ 15 px containing an interior specular highlight | p3 (37,81)-(42,85), 21 px, specular rim (162,147,204) at (37,83); recurs p2 (78,93) | 0.50 |
| `shading.ramp` | dimension (L\*) | p5 → p95 L\* range of any single-material cylinder ≥ 30 | — | [SIL] render under the reference key light, take per-part L\* percentiles | measured 34.8 (blue tube) … 51.8 (lattice); but this is as much a property of the reference render's lighting as of the material, so DECLARED as a target conditional on reproducing that lighting | 0.45 |

---

## 5. What I could not measure, and why

1. **Grip material — wood, brass pins, grey inlay panel.** Fully occluded in all four
   gun views; the fifth figure holds no gun. Zero pixels. Not measurable from this
   reference at any confidence. Anything a spec says about grip material is a choice,
   not a measurement, and should be marked DECLARED.
2. **Trigger, trigger guard, hammer materials.** ≤ 4 px each, all partly behind a
   finger. Below the resolution that can settle a colour.
3. **Rail studs and grip pins.** 1–2 px each. Their existence is a geometry question;
   their material is not measurable.
4. **Bore liner: bare steel or the same paint as the tube?** Their a\* and b\* agree
   within 1 unit in both poses (liner a\* −1/−2, b\* −6/−7; tube a\* −1/−2, b\* −7).
   Only L\* separates them (42–45 vs 33–36) and lighting fully explains that. Cannot
   be decided.
5. **Warm tube zone: copper, or worn/dirty paint?** The chroma test proves it is not
   the same material as the brass (C\* 16.8 vs 19–22, in both poses). The texture test
   rules out wood grain. Nothing in the reference separates "copper" from "brown paint".
6. **Metalness, roughness, or any other PBR parameter.** The reference is a hand-painted
   stylised texture; highlight shapes are 2–6 px. No inference is possible.
7. **The tan cylindrical port** (pose0, x 133–152, y 48–80). One pose, n = 93, h 55.5,
   C\* 18.4 — inside the `brass.aged` band. Cannot be shown to be a separate material.
8. **Whether the two brass tones are two materials or one material plus a hue shift
   baked into ambient occlusion.** The matched-lightness test controls for brightness
   but not for a hue shift correlated with occlusion. I consider this unlikely at
   Δh = 13–17° with disjoint CIs, but it is not excluded.
9. **The tan notched slab in pose1 at (190,45)-(215,70).** Cannot determine whether it
   belongs to the gun. Excluded from every measurement above.
10. **Anything about the gun's right side.** Poses 0 and 3 show one side, 1 and 2 the
    other-ish; but no view is a clean orthographic side of the opposite face, so the
    graffiti counts are per-view, never per-object.

### On the scale chain (offered, not claimed)

I found no independent scale anchor in the materials. One weak observation: the
graffiti marks have equivalent diameters of 2.0–7.0 px, i.e. **1.7–5.9 mm** at the
brief's provisional 0.838 mm/px, median 2.5 mm. Hand-flicked paint marks on a real
object typically run 3–30 mm, so the chain puts these at the small end of plausible
but does **not** contradict it. This is weak corroboration at best and must not be
treated as a second anchor: the argument is about what a painter's flick looks like,
not about a measured dimension. The chain still rests entirely on the 44 mm hand width
imported from `../jinx-i2t/baseline/spec_baseline.json`.

Every ratio constraint in §4 is stated so that it survives the chain being wrong. Only
`mat.bore.interior.L`, `mat.paint.tube.ab` and the accent colour constraints are
absolute, and none of those is a length.
