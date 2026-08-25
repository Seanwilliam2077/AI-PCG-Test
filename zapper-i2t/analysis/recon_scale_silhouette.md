# Zapper — scale and overall silhouette

Subsystem: `scale-silhouette`. Measurement only; nothing here is a spec and nothing was modelled.
All pixel coordinates are in the **native sheet** `../jinx-i2t/ref/pose_gun_5view.jpg` (3000x1462).
The four crops in `ref/` were located in that sheet by exact template match
(`cv2.matchTemplate`, TM_CCOEFF_NORMED = **1.0000** for all four), so a crop pixel is a sheet pixel:

| crop | sheet x0,y0 | size |
|---|---|---|
| gun_pose0.png | 42, 150 | 225x160 |
| gun_pose1.png | 642, 192 | 215x150 |
| gun_pose2.png | 1650, 203 | 160x129 |
| gun_pose3.png | 2421, 214 | 236x118 |

---

## 1. The scale chain in the brief is wrong by a factor of ~1.66

### 1.1 The 52.5 px is approximately right

Measured in `gun_pose1` (sheet region x 780-880, y 270-370, read at 12x with a labelled ruler,
`analysis/_p1_hand2.png`). The gun hand shows the index finger separated onto the trigger and
three curled fingers stacked below it:

| finger | sheet y span | width |
|---|---|---|
| index (on trigger) | 284.6 - 297.5 | 12.9 px |
| second | 308.3 - 320.8 | 12.5 px |
| third | 320.8 - 332.1 | 11.3 px |
| little | 332.1 - 342.1 | 10.0 px |

- four contiguous finger widths = **46.7 px**
- top of index to bottom of little (spans the trigger-guard gap) = **57.5 px**

The brief's 52.5 px sits between those two readings. **The pixel measurement is not the error.**

Corroboration from the *free* (right) hand in the same panel, hanging unforeshortened
(sheet x 1190-1290, y 700-820, `analysis/_hand_free.png`): three fingers at
x 1240-1252, 1254-1266, 1267-1280, i.e. a pitch of **12.3 px**, four fingers = **49 px**.

### 1.2 The 44 mm is the error

`hand-l` in `../jinx-i2t/baseline/spec_baseline.json` is `width 0.044, height 0.092, depth 0.028` m.
Its own height/width ratio (92:44) is a plausible hand, but 44 mm across four fingers implies
**11 mm per finger**. Four independent anchors from the *same* baseline file disagree with it:

| anchor | baseline value | pixels measured (panel 1) | mm/px |
|---|---|---|---|
| hair-crest tip to sole | 1715 mm (DECLARED) | 1217 (y 107 to y 1324) | **1.409** |
| head, crown to chin | 169 mm (`crown` 1.674 - `chin` 1.505) | 124.5 (brow y198, chin y268, scaled by the baseline's own brow:chin:crown ratio 0.562) | **1.357** |
| ear height | 36 mm (`ear-l.height`) | 25 (y 240 to y 265, `analysis/_head1.png`) | **1.440** |
| four-finger breadth | 44 mm (`hand-l.width`) | 46.7 - 52.5 | **0.84 - 0.94** |

Three anchors cluster at 1.36-1.44 mm/px. Only the hand-width anchor gives 0.84-0.94.
`hand-l.width` is internally inconsistent with the rest of that file by ~1.6x, and the brief's
chain inherits that error whole.

Plausibility check, independent of any file: at 1.39 mm/px a finger is 12.3 px = **17.1 mm**
(a real adult finger is 17-19 mm). At the brief's 0.838 mm/px it is **10.3 mm** — a doll.

### 1.3 Adopted scale

> **1.39 mm/px on the 5-view sheet, +/-5%** (i.e. 1.32 - 1.46).

Bias note: the sheet figure is *posed* (legs apart, knees soft), so its hair-top-to-sole pixel
height is 2-3% shorter than the standing 1.715 m the landmark ladder describes. That pushes the
first anchor from 1.409 down toward ~1.37 and is why the adopted value is below the raw 1.409.

**Everything absolute below still rests on a DECLARED 1.715 m.** No dimension exists anywhere in
the reference. Nothing measured here can validate that root — only the *chain from it*.

Secondary corroboration: the baseline's own `zapper` placeholder is 0.30 m long. My measurement
gives 0.336 m — 12% apart, inside the combined error. The brief's chain would give 0.16 m, which
that same file contradicts by 2x.

---

## 2. The sheet is not orthographic

`referenceCamera.projection` in the baseline says `"orthographic"`. It is not, at least not for
the gun.

Under orthographic projection the silhouette width of a body of revolution measured
**perpendicular to its projected axis** equals its true diameter and cannot change with view.
Measured tube-only outside diameter (gold rail excluded, read from pixel columns):

| pose | tube OD (px) | figure height in same panel (px) |
|---|---|---|
| pose0 | 31.0 | 1214 |
| pose1 | 36.0 | 1222 |
| pose2 | 45.0 | 1226 |
| pose3 | 37.0 | 1232 |

Bodies agree to 1.5%; the gun spreads 31 to 45 px, i.e. 45%. That is a perspective camera
watching the gun swing ~0.8 m toward and away from it on the end of an extended arm, while the
body stays near the turn axis. Implied camera: ~3 m subject distance, ~30-35 deg vertical FOV.

**Consequence:** ratios taken *within* one panel are safe. Raw pixel distances *between* panels
are not, without renormalising by a feature measured in both.

Note also that the hair is not rigid across panels — the back-view panel (fig 4) tops out 24 px
lower than the others (y 129 vs y 105-107) although a pure yaw rotation must preserve every
point's Y. Use the body, never the hair crest, for any cross-panel height work.

---

## 3. Per-pose view angle

Written out in full, with method, in **`analysis/pose_view_angles.json`**.

phi = angle between the gun's long axis and the image plane; 0 deg = true side-on.

R = (muzzle rim to lattice-collar front edge, measured along the projected axis) / (tube OD).
R is proportional to cos(phi) and is free of both mm/px and of the per-panel size change above.

| pose | muzzle rim x | lattice front x | axial px | tube OD px | R | phi | lower bound |
|---|---|---|---|---|---|---|---|
| pose3 | 2603 | 2472 | 131.1 | 37.0 | 3.544 | **16 deg** +/-10 | 0 |
| pose1 | 682 | 800 | 118.2 | 36.0 | 3.285 | **27 deg** +/-5 | 22 |
| pose0 | 58 | 138 | 80.0 | 31.0 | 2.581 | **46 deg** +/-6 | 43 |
| pose2 | 1772 | 1700 | 73.4 | 45.0 | 1.632 | **64 deg** +/-8 | 63 |

The *relative* ordering is solid (confidence 0.9). The absolute anchor is weak (0.45): it comes
from pose3 still showing an open bore ellipse of aspect ~0.5, and R only ever fixes ratios of
cos(phi). The "lower bound" column is what you get assuming pose3 is exactly side-on.

**pose3 is the closest thing to an orthographic side view in this reference, and it is still
~16 deg off.** Its projected axis runs at -2.7 deg to the sheet x axis, muzzle to the right.

Worth stating plainly: pose1 is the *character's* side view but not the *gun's* — the aiming arm
carries the gun ~27 deg out of plane. Anyone who reaches for "the side view" will reach for the
wrong crop.

---

## 4. Overall silhouette

All read from pose3 (`analysis/_c_p3wide.png`, `analysis/_c_p3grip.png`, `analysis/_ruler_p3.png`),
axial distances divided by cos(16 deg) to undo foreshortening, then x 1.39 mm/px.

### 4.1 Axial stations, measured from the muzzle rim

| station | sheet x | projected px | true axial px | fraction of length |
|---|---|---|---|---|
| muzzle rim (front-most point) | 2603 | 0 | 0 | 0.00 |
| rear of muzzle collar | 2568 | 35 | 36.4 | 0.15 |
| front of mid brass band | 2516 | 87 | 90.5 | 0.37 |
| rear of mid brass band | 2500 | 103 | 107.2 | 0.44 |
| front of lattice collar | 2472 | 131 | 136.4 | 0.56 |
| rear of lattice collar | 2440 | 163 | 169.6 | 0.70 |
| rearmost point of frame | (occluded) | 232.7 | 242.1 | 1.00 |

The rearmost point is occluded by the glove in pose3. It is recovered from pose0, where the
frame's rear cheek IS clear of the glove: there muzzle rim x=58, lattice front x=138, frame rear
x=200, so **overall / (muzzle-to-lattice-front) = 1.775**. That ratio is internal to one panel and
therefore immune to both the scale chain and the perspective problem. Cross-check: taking pose0's
raw projected length 142 px, undoing its own phi=46 deg and renormalising by the tube OD ratio
gives 243 px in pose3's scale, against 242 px derived above.

### 4.2 Headline silhouette numbers

| quantity | ratio (primary) | px | mm at 1.39 mm/px |
|---|---|---|---|
| overall length (along barrel axis) | 6.54 x tube OD | 242 | **336** |
| max height (rear-sight/port top to grip heel) | 0.48 x length | 116 | **161** |
| max width (= largest diameter, lattice collar) | 1.38 x tube OD | 51 | **71** |
| barrel-axis to grip heel | 2.18 x tube OD | 80.6 | **112** |
| tube outside diameter | 1.00 | 37 | **51** |
| muzzle collar OD | 1.13 x tube OD | 42 | **58** |
| bore opening (dark, at muzzle) | 0.62 x tube OD | 23 | **32** |
| lattice collar axial length | 0.65 x its own OD | 33.3 | **46** |
| top rail stands proud of tube by | 0.12 x tube OD | 4.4 | **6** |
| length as a fraction of character height | 0.199 | 242 / 1217 | — |

Height was read as: top of the ribbed rear port y=234, grip heel (butt cap underside) y=350,
both in pose3; 116 px, x cos(2.7 deg) for the axis tilt = 115.9.

Barrel-axis-to-grip-heel: the axis line through (2594, 276.5) with direction (-0.999, -0.047)
passes y = 269.3 at the grip station x=2440; the grip butt cap bottoms at y = 350.

### 4.3 Length split

Along the barrel axis, out of 242 px total:

- **barrel assembly** (muzzle rim to rear face of lattice collar): 169.6 px = **70.2%**
- **frame / action** (rear of lattice collar to rearmost point): 71.8 px = **29.8%**

The **grip is not a third slice of that length** — it hangs below and its axial footprint
(x 2405-2465, i.e. axial 143.6-206) overlaps the frame slice entirely. Reporting a
barrel:frame:grip length triple would be a fabrication; the honest split is 70:30 with the grip
described as a drop of 2.18 tube diameters below the axis.

### 4.4 The tube is a cylinder, not a cone

Perpendicular width profile along the pose3 axis (`analysis/perp.py`), sampled every 4 px from
the muzzle rim rearward: 43, 44, 43, 43, 43, 43, 44, 44, 43, 43 px across s = 24 to 104, spanning
both the pale steel section and the copper section. Constant to +/-1.2%.

This matters because pose0 *on its own* reads 31 px at the muzzle end and ~38 px at the lattice
end and would tempt anyone into modelling a tapered barrel. That taper is the perspective
artefact of section 2, not geometry.

---

## 5. Counts

Counts are cheap to check and survive low resolution better than lengths.

| feature | count | evidence |
|---|---|---|
| encircling brass rings on the barrel | **3** | muzzle collar / mid band / lattice collar. pose0 x 58-78, 112-125, 138-158; pose1 x 682-712, 762-800, 800-835; pose3 x 2568-2603, 2500-2516, 2440-2472. Same three, same order, three poses. |
| studs on the top rail | **3** | 2 blue studs side by side on the reddish mount block + 1 near the muzzle end of the rail. pose0: x~76, and x~120.7 / 125.7 (`analysis/_rail0.png`). pose3: x~2583, and x~2511 / 2516 (`analysis/_rail3.png`). |
| lugs hanging below the barrel | **1** | small lug under the mid band, pose3 x 2505-2512 y 290-294; same lug visible pose1 x~780 y~297. |
| lattice lozenges visible on the near half (side view) | **5 clear, up to 7 with partials** | pose3 `analysis/_lat3.png`: five light lozenges down the visible face; pose1 `analysis/_lat1.png`: five along the visible arc. |
| lattice lozenges around the circumference | **10-14, best guess 12** | 5 in ~half the circumference (pose3) and 5 in ~45% of it (pose1). See section 7 — this is at the edge of what the reference can settle. |
| stacked steps in the muzzle collar | **2-3** | pose3 perpendicular width profile 37 to 40 to 47 to 48 px over s = 0 to 12 gives two clear steps; pose1's muzzle at 18x (`analysis/_muz1.png`) reads as bore + pale liner ring + 2 brass steps. Low confidence. |
| brass pins in the grip | **not measurable** | grip is inside the fist in all five panels. |

---

## 6. Proposed constraints

Format: id | kind | value +/-tol | how a script checks it against the built model | evidence | confidence.
"World AABB" means the axis-aligned bounding box of a named mesh in world space after the factory
runs. "Axis" means the fitted axis of the `barrel.tube` mesh (its principal component).

**Ratios first — these survive the scale chain being wrong.**

1. `gun.ratio.length_over_tube_od` | ratio | **6.54 +/-0.50** | extent of the union of all gun meshes projected on the axis, divided by the mean of `barrel.tube`'s two AABB extents perpendicular to the axis | pose3: 242.1 axial px / 37.0 px | 0.75
2. `gun.ratio.height_over_length` | ratio | **0.48 +/-0.05** | (extent of the whole-gun AABB perpendicular to the axis, in the plane that contains the grip) / (extent along the axis) | pose3: y234 (port top) to y350 (grip heel) = 116 px, vs 242 px | 0.70
3. `grip.ratio.heel_drop_over_tube_od` | ratio | **2.18 +/-0.20** | perpendicular distance from the axis line to the lowest point of the `grip` AABB, / tube OD | pose3: axis y=269.3 at x=2440; butt cap bottom y=350 gives 80.6 px / 37.0 | 0.60
4. `muzzle.ratio.collar_od_over_tube_od` | ratio | **1.13 +/-0.06** | max perpendicular extent of `muzzle-collar` / tube OD | pose3 perpendicular width profile: 42 px at the collar vs 37 px on the plain tube | 0.65
5. `lattice.ratio.od_over_tube_od` | ratio | **1.38 +/-0.08** | max perpendicular extent of `lattice-collar` / tube OD | pose3 contour x2440-2472: y245 to y296 = 51 px vs 37 px | 0.60
6. `lattice.ratio.axial_len_over_od` | ratio | **0.65 +/-0.08** | axial extent of `lattice-collar` / its max perpendicular extent | pose3: x2440 to 2472 = 32 projected px, 33.3 true, / 51 px | 0.60
7. `barrel.ratio.assembly_fraction` | ratio | **0.702 +/-0.04** | (axial distance from the front-most gun vertex to the rear face of `lattice-collar`) / (overall axial extent) | pose3 station table, 169.6 / 241.4 | 0.60
8. `barrel.tube.taper` | ratio | **1.00 +/-0.05** | tube AABB diameter measured at 10% and 90% along its own axis; report the ratio | pose3 perpendicular width constant 43-44 px over 80 px of axis | 0.70
9. `bore.ratio.d_over_tube_od` | ratio | **0.62 +/-0.08** | inner diameter of the `muzzle-liner` (or the bore cylinder's radius x2) / tube OD | pose3 dark opening major axis 23 px; pose2 25 px; both against a 37 px tube | 0.45
10. `rail.ratio.proud_over_tube_od` | ratio | **0.12 +/-0.04** | (distance from the axis to the top of `top-rail` minus tube radius) / tube OD | pose3 x2554: rail top +26.0 from axis, tube top +21.6, gives 4.4 px / 37 | 0.50
11. `port.ratio.axial_position` | ratio | **0.77 +/-0.05** from the muzzle | centre of `rear-port` projected on the axis, / overall axial extent | pose3 x2418-2430 gives 0.75-0.80; pose1 x835-857 gives 0.73-0.84 (two poses, two view angles, same answer) | 0.55
12. `gun.ratio.length_over_character_height` | ratio | **0.199 +/-0.012** | if the gun is placed in the character scene: gun axial extent / character world height | 242.1 px / 1217 px, one panel, no scale chain involved | 0.70

**Counts.**

13. `barrel.brassRings.count` | count | **3** | number of meshes tagged as an encircling brass ring between the muzzle rim and the frame; also assert their axial centres are ordered muzzle-collar < mid-band < lattice-collar | three poses agree (section 5) | 0.85
14. `rail.studs.count` | count | **3** | number of stud meshes parented to `top-rail`; additionally exactly 2 of them share the axial position of `rail-mount-block` to within 0.5 x stud diameter | pose0 x~76 / 120.7 / 125.7; pose3 x~2583 / 2511 / 2516 | 0.80
15. `barrel.underLug.count` | count | **1** | meshes whose AABB centre is below the axis and between the mid band's axial bounds | pose3 x2505-2512 y290-294; pose1 x~780 | 0.70
16. `lattice.cutouts.count` | count | **12 (accept 10-14)** | length of the repetition system's instance array around `lattice-collar`. Secondary render check: an orthographic side render must show **5 +/-1** complete lozenges between the underside of the top rail and the collar's lower silhouette edge | 5 clear lozenges over ~half the circumference in pose3, 5 over ~45% in pose1 | 0.40
17. `muzzle.collar.steps` | count | **2 (accept 2-3)** | number of distinct diameter plateaus in the perpendicular width profile of `muzzle-collar` sampled every 1 mm along the axis | pose3 profile 37 to 40 to 47 to 48 px | 0.35

**Absolute dimensions — all inherit the DECLARED 1.715 m body height; tolerances are wide on purpose.**

18. `gun.dimension.length` | dimension | **336 mm +/-8%** (309-363) | axial extent of the union of gun meshes | 242.1 px x 1.39 mm/px | 0.55
19. `barrel.tube.od` | dimension | **51 mm +/-10%** | mean of `barrel.tube`'s two perpendicular AABB extents; also assert those two agree within 2% of each other (roundness) | 37 px x 1.39 | 0.50
20. `gun.dimension.height` | dimension | **161 mm +/-10%** | as constraint 2 but absolute | 116 px x 1.39 | 0.50
21. `scale.mmPerPixel` | dimension | **1.39 mm/px +/-5%** | DECLARED anchor for this whole document; check by re-deriving it from any body landmark in a render of the character at 3000x1462 | DECLARED (rooted on the baseline's declared 1.715 m); measured chain in section 1.2 | 0.60

**Relations.**

22. `rail.relation.flush_on_tube` | relation | `top-rail` sits ON the tube: its lowest perpendicular coordinate is within +/-0.02 x tube OD of the tube's outer surface, and its axial span covers at least 0.55 of the barrel assembly | rail base merges with the tube's top edge everywhere in pose3; rail spans x 2479-2592 of the 2440-2603 barrel | 0.65
23. `lattice.relation.abuts_frame` | relation | rear face of `lattice-collar` is coincident with the front face of the frame to within 0.05 x tube OD | pose3 x2440 is simultaneously the lattice rear and the frame front; pose0 x138/x158 likewise | 0.60
24. `muzzle.relation.liner_recessed` | relation | the bore liner's front face is BEHIND the muzzle collar's front face along the axis (recessed, not proud) | in pose1 and pose2 the dark bore sits inside a brass rim on every side | 0.75
25. `port.relation.above_axis` | relation | `rear-port` centre is above the axis and its own axis is roughly perpendicular to the barrel axis (80-100 deg) | pose0 x 180-192 y 205-230 shows it standing up off the frame; pose3 x 2418-2430 y 234-247 | 0.55

---

## 7. What I could not measure, and why

1. **The absolute scale root.** Nothing in the reference carries a dimension. Every millimetre here
   descends from a DECLARED 1.715 m. I improved the *chain* by ~10x (a 1217 px span replaces a
   52.5 px one) and corrected a 1.66x error in it, but I cannot validate the root.
2. **Grip length, grip rake angle, grip cross-section, grip pins, the grey inlay panel.** The fist
   covers the grip in all five panels. Only the butt cap's underside outline is visible
   (pose3 x 2412-2465, y 345-352). The grip's drop below the axis is measurable; nothing else is.
3. **True maximum width.** There is no top view and no orthographic muzzle-on view. Pose2 is the
   closest but is 64 deg off and perspective-inflated. I report max width = max diameter = the
   lattice collar, which assumes nothing on the gun is wider than the barrel group. The rear sight
   hook and the frame cheeks could break that and I cannot see them from above.
4. **The bore ellipse aspect, hence an absolute view angle.** The muzzle opening is 17-25 px across
   in a 3000 px sheet. Its aspect cannot be read better than +/-0.15, which maps to +/-25 deg of view
   angle — useless. It is also not a clean ellipse: looking into a tube at an angle, the dark
   region is bounded partly by the near rim and partly by the interior wall. This is why section 3's
   absolute angles carry confidence 0.45 while its ordering carries 0.9.
5. **The exact lattice cutout count around the circumference.** 5 lozenges are clear on the near
   half in pose3; whether the top and bottom partials are two more lozenges or the same ones
   foreshortened is below the resolution. 10-14 is the honest range.
6. **Trigger, trigger guard, hammer.** Occluded or under 6 px in every panel.
7. **The rearmost point of the frame in pose3.** Recovered indirectly through a within-panel ratio
   measured in pose0 (1.775). If pose0's frame rear is itself clipped by the glove, my overall
   length is an underestimate, not an overestimate.
8. **Whether the panels share one camera.** They do not share one *projection* (section 2). I did
   not recover per-panel camera yaw; the clay 6-view `../jinx-i2t/ref/pose_gun_clay_6view.jpg`
   would support that work but its panels are vertically offset from one another on the sheet
   (figure heights 1165 / 1168 / 1206 / >1225 / 1203 / 1164 px), so it is not a clean turnaround
   either and I did not chase it further.
9. **The copper vs steel section boundary as geometry.** It reads as a paint change, not a step —
   the perpendicular width is continuous across it (section 4.4). I cannot rule out a 1-2 px step.

---

## 8. Files produced

| file | what it is |
|---|---|
| `analysis/recon_scale_silhouette.md` | this report |
| `analysis/pose_view_angles.json` | per-pose view angle, method, and the perspective finding, machine-readable |
| `analysis/seg3.py`, `analysis/clay_seg.py` | background model + figure segmentation for both sheets |
| `analysis/locate.py` | template match placing the four crops in the sheet |
| `analysis/perp.py` | perpendicular width profile along a given barrel axis |
| `analysis/contour.py`, `analysis/ruler.py` | annotated enlargements used for every reading above |
| `analysis/compute_summary.py` | the view-angle and dimension arithmetic |
| `analysis/_*.png` | the annotated enlargements themselves |

Nothing under `ref/` was modified. Nothing in `../jinx-i2t` was written to.
