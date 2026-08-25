# recon: GRIP subsystem — Jinx "Zap!" pistol

Measurement only. Nothing modelled, no spec written. All pixel coordinates are in the
**full 3000x1462 sheet** `../jinx-i2t/ref/pose_gun_5view.jpg` unless prefixed `clay:`,
which means `../jinx-i2t/ref/pose_gun_clay_6view.jpg` (also 3000x1462).

The four crops in `ref/` are byte-identical sub-rectangles of the colour sheet
(verified with `cv2.matchTemplate`, score 1.000):

| crop | sheet rect |
|---|---|
| `ref/gun_pose0.png` | x 42-267, y 150-310 |
| `ref/gun_pose1.png` | x 642-857, y 192-342 |
| `ref/gun_pose2.png` | x 1650-1810, y 203-332 |
| `ref/gun_pose3.png` | x 2421-2657, y 214-332 |

## 0. Extra reference found, and used

The brief lists four colour poses. There is also a **clay turnaround** at
`../jinx-i2t/ref/pose_gun_clay_6view.jpg` — the same character, untextured, six poses,
five of which hold the gun. Clay removes all colour ambiguity and is the only place the
grip's butt appears as an unambiguous closed silhouette. It is used throughout below.
`ref/_gun_views.png` is just the four colour crops pasted side by side; nothing new.

---

## 1. HEADLINE: the scale chain in the brief is wrong by a factor of ~1.7

The brief's chain is: `spec_baseline.json` hand-l width = 0.044 m; four curled fingers
span 52.5 px in pose1; therefore 0.838 mm/px. **Both links fail.**

### 1a. The 52.5 px finger span is not four fingers

In pose1 the index finger is **extended forward onto the trigger**, separated from the
other three by a ~10 px gap. Measured off `analysis/_p1_rear_boost.png`: index occupies
y 283-297, then a break, then three curled fingers at y 305-320, 320-331, 331-343. Any
span reaching 52.5 px in pose1 has crossed that break.

Measured instead on a **clean four-finger stack**, all four curled and touching:

| view | four-finger stack | per finger |
|---|---|---|
| colour pose3, x 2404-2460 | y 296 → 336 = **40 ± 3 px** | 10.0 px |
| clay B, x 699-736 | y 269 → 314 = **45 ± 3 px** | 11.2 px |
| clay B rescaled to pose3 (clay gun is 5% larger, tube OD 43 vs 41 px) | **42.8 px** | |

So the stack is **41 ± 3 px**, not 52.5 px. That link alone is 25-30% too large.

### 1b. `spec_baseline.json` contradicts itself: 44 mm hand vs 1.72 m stature

`spec_baseline.json.coordinateFrame.scaleReference` reads
*"1.72 m total height, hair-crest tip to sole. DECLARED, not measured"*, and
`silhouette.landmarks` puts hairTop at 1.715 m and sole at 0.

Measured on the colour sheet, figure 5 (rightmost; the only figure cleanly separable by
connected components, x 2613-3000, and the most upright):

* hair-crest top **y = 128**
* lowest boot pixel **y = 1325**
* **stature = 1197 px** (vertical extent; the lean makes this a slight underestimate)

Two absolute anchors:

| anchor | mm/px |
|---|---|
| declared stature 1715 mm / 1197 px | **1.433** |
| boot toe-to-heel, figure 5 side view, 205 px; combat boot on a 0.152 x stature foot (261 mm) plus ~25 mm sole/toe ≈ 285 mm | **1.39** |

**mm/px for the colour gun sheet = 1.43 ± 0.10.**

Push the spec's hand through that: four-finger stack 41 px x 1.433 = **58.7 mm**. The
spec says 44 mm. For 44 mm to be right the sheet would be 1.073 mm/px and figure 5 would
be 1197 x 1.073 = **1285 mm tall** — a 1.29 m character, not 1.72 m. The spec cannot
have both numbers.

Independent confirmation using proportion only, no absolute units:
`fourFingerStack / stature = 41 / 1197 = 0.0343`. Real adult female hand breadth /
stature is 0.043-0.047. Jinx is drawn with hands ~22% narrower than anthropometric —
stylisation, not a factor of two. A 44 mm hand on a 1.72 m frame would be ratio 0.0256,
off the human chart entirely.

### 1c. Consequence

| quantity | brief's chain (0.838 mm/px) | this report (1.433 mm/px) |
|---|---|---|
| barrel tube OD | ~30 mm | **59 ± 6 mm** |
| gun length, muzzle tip to frame heel (pose3, x 2415→2603) | 158 mm | **269 ± 20 mm** |
| hand breadth | 44 mm | **59 ± 5 mm** |

269 mm is a long-barrelled hand cannon (a 6-inch Colt Python is 279 mm). 158 mm is a
snub pocket pistol. The silhouette measured against a 41 px hand says the former.

**Recommendation: do not carry any absolute mm into the grip spec.** Everything below is
given first as a ratio to the barrel tube outside diameter, which is measurable in the
same images and in the built scene; mm conversions are shown but are derived from a
DECLARED 1.72 m in a sibling project.

Reference denominator, measured on the colour sheet:
`barrel.tube.od` = silhouette height 45 px over x 2530-2590 in pose3, minus ~4 px for
the top rail standing proud = **41 ± 2 px**.

---

## 2. Occlusion audit — how much grip is actually visible

**The sides of the grip are visible in zero of the nine available views.** In every pose
the hand closes completely around it between the frame's underside and the butt. What is
visible:

| view | visible grip surface | extent |
|---|---|---|
| clay A (rear 3/4) | **butt face**, closed convex silhouette | x 114-153, y 328-339 = 39 x 11 px |
| colour pose0 (rear 3/4) | same butt, pale blue-grey band under the fist | x 166-206, y 289-300 = 40 x 11 px |
| colour pose3 (side) | butt edge-on, desaturated band (HSV S 5-7, V 100-150) | x 2406-2442, y 346-351 |
| colour pose1 (side) | butt edge-on, ambiguous — merges with glove cuff / forearm underside | x ~833-875, y ~340-353 |
| colour pose2 (near muzzle-on) | a few dark unresolvable pixels between fingers | x 1698-1720, y 305-335 |
| clay B, C, D, E | nothing; hand covers the grip entirely | 0 px |

Quantified: in clay A the grip's vertical run from the frame's underside (y ≈ 292) to
the butt's lowest pixel (y = 339) is 47 px. The fist covers y 292-328. **Visible
fraction of the grip's height = 11/47 = 23%, and that 23% is the end cap, not the side.
Visible fraction of the grip's lateral surface = 0%.**

**Best view for the grip: clay A** (clay sheet x 20-210, y 240-340), the only view where
the butt reads as a bounded, closed shape that cannot be confused with glove leather.
Colour pose0 shows the same feature at the same offset and corroborates it.

### Identification caveat, stated plainly

In the colour side views the pale desaturated band below the fist could also be the
glove's lower cuff edge. Three things resolve it in favour of "gun":

1. In **clay A** the shape is a closed convex oval, disconnected from the arm silhouette
   (the arm continues separately at y 293-325, x 155-210). A cuff would be continuous.
2. It sits ~50 px below the frame's underside in pose0, pose1 and pose3 alike — a fixed
   offset from the gun.
3. In pose3 it extends *forward* past the fingertips (to x 2442), away from the wrist.
   A cuff cannot.

Confidence that this feature is the grip's butt: **0.75**. In pose1 it is confounded with
the forearm, so pose1 contributes no grip number in this report.

---

## 3. Measurements

### 3.1 Bore axis (the reference direction for the rake)

Fitted to the tube silhouette, colour pose3, columns x 2500-2590: top edge y 246 → 251,
bottom edge y 289 → 295. Both give slope +0.055 px/px.
**Bore axis = 3.2° ± 0.5° below image-horizontal, descending toward the muzzle (right).**

clay B tube midline: x 604 → y 212.4, x 671 → y 219.7, slope 0.109 → **6.2°**, muzzle
up-left. clay E tube midline over x 2590-2650: slope −0.083 → **4.8°**, muzzle up-right.

### 3.2 Grip axis and rake — the one grip angle that IS measurable

The grip's own long axis is hidden, so I use the **knuckle line**: the stack of four
curled fingers lies along the front strap, and the line through the fingers' proximal
ends is parallel to the grip axis to within a finger's taper.

**colour pose3** — knuckle ends read off `analysis/_p3_rear_boost.png`:
(2416, 300), (2410, 312), (2406, 322), (2406, 332). Slope dx/dy = −10/32 →
**17.4° from image-vertical, leaning rearward.** Bore-perpendicular is 3.2° from vertical
the same way, so rake past perpendicular = 14.2° → **grip-to-bore = 104.2°**

**clay B** — finger left edges (1250, 885), (1265, 980), (1280, 1085), (1300, 1195) in
the 9x crop of sheet (560,175). Slope 50/310 → 9.2° from vertical rearward; bore
perpendicular is 6.2° the other way → rake 15.4° → **grip-to-bore = 105.4°**

**clay E** — fingertip ends (700, 960), (690, 1030), (660, 1100), (640, 1180) in the 8x
crop of sheet (2420,150). Slope −60/220 → 15.2°; bore perpendicular 4.8° → rake 20.0°
→ **grip-to-bore = 110.0°**

Three views, mean **106.5°**, spread 5.8°.

**All three are lower bounds.** Every view shows the muzzle bore open, so the barrel is
angled toward the camera in all of them; foreshortening of the fore-aft axis pulls the
projected grip toward 90°. The true rake is at or above the largest projected value.
**Adopted: 108° ± 8° (raked back 18° ± 8° from perpendicular to the bore).**

### 3.3 Grip length

Root = the frame's underside where the grip emerges. In pose3 this is a dark navy line
at y 288-293 spanning x 2417-2445; take **y = 291 ± 2**.
Bottom = lowest gun pixel, **y = 351 ± 1**, verified from an HSV dump: at x 2406-2442 the
value rises to 100-150 at y 347-350 against a background of V=80, and is background again
at y 352.

Vertical drop 60 px; along the grip axis (17.4° from vertical) = 60/cos 17.4° =
**62.9 px = 1.53 x tube OD.**

clay A cross-check: frame underside y ≈ 292, butt bottom y = 339 → 47 px against a local
tube OD of 34 px → **1.38 x tube OD.** (clay A's gun is further from camera and its grip
is foreshortened differently, so exact agreement is not expected.)

**Adopted: grip length = 1.45 ± 0.15 x tube OD.** At 41 px OD and 1.433 mm/px that is
**85 ± 9 mm** — long, consistent with a large-frame revolver grip.

Sanity check: the four-finger stack is 41 px of a 63 px grip = **65%**, leaving 35% for
the thumb web above and the butt overhang below. That is the normal proportion for a
pistol and is itself an independent check on the 63 px.

### 3.4 Grip cross-section — bounded, not measured

**Fore-aft depth (front strap to back strap).** The fist's fore-aft extent at mid-finger
level in pose3 is x 2402 (glove back) to 2457 (fingertips) = 55 px. Subtract one finger
thickness at the front (10 px, from the 41 px / 4 stack) and the palm plus knuckle at the
back (~14 px):
**grip depth ≈ 31 ± 6 px = 0.75 ± 0.15 x tube OD ≈ 44 ± 9 mm.**

**Width across.** No view shows this dimension unoccluded. The only bound is the clay A
butt oval's short axis, 11 px against a local OD of 34 px = **≥ 0.32 x tube OD**, and
that is a projected (compressed) value, so it is a floor only. Pistol grips run
depth:width ≈ 1.5-1.7:1. **Declared 0.47 ± 0.15 x tube OD ≈ 28 ± 9 mm — an inference,
not a measurement.**

**Circumference — the hand-closure bound the brief asked for.** In pose3 the visible
finger run from knuckle to tip is x 2406 → 2457 = 51 ± 4 px = 1.24 x tube OD. For the
fingertips to reach the thumb pad the grip's cross-sectional perimeter cannot exceed
roughly twice the finger wrap length:

> **grip circumference ≤ 2.45 x tube OD (≈ 144 mm at 1.433 mm/px).**

The depth/width estimate above gives a rounded-rectangle perimeter of about
2(31+19) minus corner relief ≈ 92 px = **2.24 x tube OD ≈ 132 mm** — inside the bound,
i.e. the hand can close. Under the brief's 0.838 mm/px the same grip would be 77 mm
around, which a hand does not so much grip as pinch; a further sign the chain is wrong.

### 3.5 Butt geometry

The clay A butt oval is 39 x 11 px, aspect 3.5:1 **as projected from an oblique
rear-quarter angle I cannot recover.** Do not read that as the true aspect. Two honest
statements survive:

* the butt's largest dimension is ≥ 39/34 = **1.15 x tube OD** (47 px at pose3 scale —
  larger than the 31 px depth estimate, so the butt is almost certainly flared, or
  carries a toe/heel spur, rather than being a plain section cut);
* the butt face is **smooth in clay**: at 20x (`analysis/_clayA_butt.png`) there is no
  relief, groove, screw boss or panel edge anywhere on it.

Butt overhang past the frame's heel: in pose3 the frame's rear edge is x 2415 ± 2 and the
butt band's rear end is x 2406 → the butt sits **9 px = 0.22 x tube OD behind** the frame
heel. The direction is consistent with a rearward rake. Confidence 0.5 — the rear end of
the band is the confusable end.

### 3.6 Brass pins — count

**Counted: 0 confirmed.** There is exactly one warm-hued pixel cluster anywhere on the
whole grip assembly, in colour pose0 at **x 168-169, y 293-295**: hue 12-19, S 64-116,
V 106-155, against a hue 105-125 blue-grey surround (HSV dump reproduced in the working
notes). It sits at the **forward-lower corner, the toe, of the butt**. It is 2 x 3 px ≈
3-4 mm. At that size a pin head, a screw, a lanyard stud and a specular highlight on a
chamfer are indistinguishable. I will not report a count.

The gold triangles running down the left edge of the fist in pose0 (y ≈ 243, 258, 268,
285) are **glove studs**, not grip pins — they follow the glove's outline and appear on
the non-gun hand as well.

### 3.7 Lighter inlaid panel

**Not observable.** The panel would live on the grip's lateral face, which has 0 visible
pixels in all nine views. The tan/khaki band at x 2410-2436, y 326-333 in pose3, which
could be mistaken for it, is the same colour and position as the glove's brown leather
palm patch and moves with the hand, not the gun.

### 3.8 Front and back strap curvature

**Not measurable.** Both straps are covered by the fingers (front) and the palm (back)
along their entire length in every view. The clay sheet, which would have shown the
profile as pure form, occludes them just as completely.

---

## 4. What I could not measure, and why

| quantity | why |
|---|---|
| grip width across | 0 unoccluded pixels in 9 views; only a projected floor from the clay A butt |
| front strap curvature | covered by four fingers in every view |
| back strap curvature | covered by the palm in every view |
| finger grooves / checkering | ditto; the grip's lateral surface is never seen |
| inlaid panel extent | ditto; the panel's face is never seen |
| brass pin count | ditto; one 2x3 px warm cluster at the butt toe is below the resolution that separates a pin from a highlight |
| grip material / colour | the only grip pixels are the butt, which reads pale desaturated blue-grey (S 5-7 in pose3, hue 105-125 in pose0) — **metal, not wood.** The "dark red-brown wood" in the brief is not supported by any pixel I can attribute to the gun |
| true (un-foreshortened) rake | no view is orthographic side-on; the bore is open in all four colour poses and all five clay poses, so every projected angle is a lower bound |
| absolute mm for anything | the sheet carries no dimension; every absolute here descends from a DECLARED 1.72 m in a sibling project |

---

## 5. Proposed constraints

`OD` = the barrel tube outside diameter, measured on the built model as the barrel mesh's
world-bbox extent perpendicular to the bore axis. Ratios are preferred throughout because
the scale chain is unsafe (section 1).

| id | kind | value | tol | how a script checks it against the built model | evidence | conf |
|---|---|---|---|---|---|---|
| `grip.axis.rakeFromBore` | angle | 108° | ±8° | bore axis = principal axis of the barrel mesh's vertices; grip axis = (grip bbox top-face centre) − (bottom-face centre) in world space; report the angle between the bore's forward direction and the grip's downward direction | knuckle-line vs tube-silhouette slope: pose3 104.2°, clay B 105.4°, clay E 110.0°; all lower bounds | 0.7 |
| `grip.length.overTubeOd` | ratio | 1.45 | ±0.15 | grip mesh world-bbox extent projected on the grip axis, divided by OD | pose3 y 291→351 = 60 px vertical → 62.9 px on axis / 41 px OD = 1.53; clay A 47/34 = 1.38 | 0.6 |
| `grip.depth.overTubeOd` | ratio | 0.75 | ±0.15 | grip mesh cross-section at 50% height; extent along the bore direction / OD | pose3 fist fore-aft 55 px (x 2402-2457) minus 10 px finger minus 14 px palm = 31 px / 41 | 0.45 |
| `grip.width.overTubeOd` | ratio | 0.47 | ±0.15 | same cross-section; extent perpendicular to both the bore and the grip axis / OD | DECLARED. Floor 0.32 from clay A butt short axis 11/34; the rest is a 1.6:1 depth:width assumption | 0.3 |
| `grip.circumference.overTubeOd` | ratio | ≤ 2.45 | upper bound, no lower | convex-hull perimeter of the grip's mid-height cross-section / OD; PASS if ≤ 2.45 | 2x the pose3 knuckle-to-tip finger run, 51 px / 41 px OD = 1.24 | 0.65 |
| `grip.butt.majorAxis.overTubeOd` | ratio | 1.15 | +0.25 / −0.10 | grip mesh bottom face: longest chord / OD | clay A butt oval major axis 39 px / local OD 34 px | 0.5 |
| `grip.root.flushWithFrame` | relation | grip top face coincident with the frame underside, gap ≤ 0.03 OD | — | abs(grip.bbox.max.y − frame.bbox.min.y) ≤ 0.03 x OD in world space, AND the grip's footprint along the bore lies wholly inside the frame's | pose3: the frame underside is a single unbroken dark line at y 288-293 with no gap or step before the hand | 0.8 |
| `grip.butt.behindFrameHeel` | relation | butt's rearmost point is rearward of the frame's rearmost point by 0.05-0.35 OD | — | project both bboxes on the bore axis; (frame.min − butt.min)/OD in [0.05, 0.35] | pose3 frame heel x 2415, butt rear x 2406 → 9 px / 41 = 0.22 | 0.5 |
| `grip.length.overHandBreadth` | ratio | 1.55 | ±0.20 | if a hand is present: grip on-axis length / hand mesh bbox breadth. Scale-chain-free | pose3: 63 px grip / 41 px four-finger stack | 0.6 |
| `grip.fingerCourse.count` | count | 4 | exact | the clear, uninterrupted run of the front strap must accommodate 4 finger courses: on-axis length x 0.65 ≥ 4 x (OD/4), and no transverse feature interrupts the front strap between 12% and 77% of the grip's height | pose3: the four-finger stack occupies y 296-336, i.e. 8%-75% of the y 291-351 run, unbroken | 0.7 |
| `grip.material.notWood` | relation | the butt face carries the same pale steel-blue material as the frame, not the barrel brass and not a wood tone | — | compare the butt face's material id to the frame's; PASS if identical | butt HSV in pose0 hue 105-125 / S 25-70 / V 55-80, matching the frame; pose3 butt S 5-7 | 0.55 |
| `grip.butt.toeStud.present` | count | 1 | ±1 (0, 1 or 2 all pass) | count sub-meshes of a different material whose centroid lies within 0.15 OD of the butt's forward-lower corner | one 2x3 px hue-12-19 cluster at pose0 x 168-169, y 293-295 — the only warm pixels on the grip | 0.35 |
| `barrel.tube.od.px` | dimension | 41 px in the pose3 image frame | ±2 px | render the built model from the pose3 camera at the same framing, measure the tube silhouette height, subtract the rail | pose3 silhouette 45 px over x 2530-2590; the rail stands ~4 px proud | 0.75 |
| `scale.mmPerPixel.colourSheet` | dimension | 1.433 mm/px | ±7% | not a model check — it is the conversion any absolute constraint must use; falsifiable by re-measuring figure 5's hair-crest-to-sole span | 1715 mm DECLARED / 1197 px measured (y 128 → 1325, sheet x 2613-3000); the boot-length anchor gives 1.39 | 0.55 |
| `hand.fourFingerStack.px` | dimension | 41 px in the pose3 image frame | ±3 px | measure the stack of four curled fingers in a clean grip pose | pose3 y 296 → 336; clay B 45 px rescaled to 42.8. **Directly falsifies the brief's 52.5 px** | 0.8 |

### Constraints I decline to propose

`grip.pins.count`, `grip.panel.lengthFraction`, `grip.panel.widthFraction`,
`grip.frontStrap.radius`, `grip.backStrap.radius`, `grip.palmSwell.*` — every one of
these depends on the grip's lateral surface, which has zero unoccluded pixels in nine
views. Any number would be invented, and an invented number that cannot fail is worse
than no number.

---

## 6. Artefacts written

All under `analysis/`. Nothing under `ref/` was touched.

* `_grip_annot_pose3.png` — the primary measurement figure: pose3 at 7x with the bore
  axis, frame underside, grip axis, four-finger stack and butt marked
* `_clayA_butt.png` — 20x of the only closed butt silhouette in the reference
* `_p3_rear_boost.png`, `_p3_gripzoom.png`, `_p3_frame.png`, `_p3_butt.png`,
  `_p3_full_grid.png` — pose3
* `_p0_rear_boost.png`, `_p0_butt.png`, `_p1_rear_boost.png`, `_p1_butt.png`,
  `_p2_rear_boost.png` — the other colour poses
* `_clayA.png` … `_clayE.png`, `_clayB_all.png`, `_clayB_grip.png`, `_clayE_all.png`,
  `_clayD_grip.png` — clay sheet
* `_fig5.png`, `_fig4b.png`, `_figA0.png`, `_sheet_overview.png` — figure crops with
  y rulers, used for the stature anchor
