# Zapper — frozen constraint contract

Object: Jinx's pistol ("Zap!"), long-barrelled stylised revolver-form sidearm.
Purpose: the pre-build contract. Everything here is stated so that a built model can be
measured against it and **fail**. Nothing has been modelled.

Frozen from six independent measurement reports:
`analysis/recon_barrel.md`, `recon_frame_action.md`, `recon_grip.md`,
`recon_joints_handles.md`, `recon_materials.md`, `recon_scale_silhouette.md`.

Every value below is one of three things, and is always labelled:

* **measured** — a number read off pixels, with the pixels named.
* **derived** — arithmetic on measured numbers.
* **DECLARED** — a choice. Not measurable from this reference. Falsifiable against the
  built model but not against the imagery.

Where the six reports disagreed, §4 records both numbers, the cause, and the decision.
Where two or more agreed independently, §5 records that; it is the strongest evidence in
the document.

---

## 1. The scale chain

**Read this first: the entire absolute scale of this object rests on one declared number
inside a different model, and that number was never measured from anything.**

`../jinx-i2t/baseline/spec_baseline.json`, field `coordinateFrame.scaleReference`, says in
its own words: *"1.72 m total height, hair-crest tip to sole. DECLARED, not measured — the
reference sheet carries no dimension. Every other length is a measured ratio against it."*

That is the root. It cannot be checked. Every millimetre in §6 inherits it. Every **ratio**
in §6 survives it being wrong.

### Link 0 — the root (DECLARED, unfalsifiable)

`stature = 1.715 m` (hair-crest to sole). Source: `spec_baseline.json`. Confidence: n/a —
this is an axiom, not a measurement.

### Link 1 — stature in sheet pixels (measured, 4 independent times)

| report | method | px | mm/px |
|---|---|---|---|
| barrel | 6 sheet windows, took the largest (crest least foreshortened) | 1278 ± 30 | 1.342 |
| frame-action | figs 1/2/5, background-subtracted connected components | 1220 | 1.406 |
| grip | figure 5, y 128 → y 1325 | 1197 | 1.433 |
| scale-silhouette | panel 1, y 107 → y 1324 | 1217 | 1.409 |

Mean **1228 px, sd 30, report-to-report spread 6.8 %**. Within any one report the five
panel heights agree to 1.5 %; the spread is between reports, and is caused by hair-crest
foreshortening (barrel corrects *upward* on the px, scale-silhouette corrects *downward*
on the mm because a posed figure is 2–3 % shorter than a standing one). The two
corrections point opposite ways and are of similar size, so neither is applied.

**Adopted: `stature_px = 1225 ± 45`.**

### Link 2 — three spec-internal cross-checks (measured)

Anchors that do **not** use stature, taken from `spec_baseline.json`'s own component sizes
plus one anthropometric anchor:

| anchor | mm | px | mm/px |
|---|---|---|---|
| head crown → chin | 169 | 124.5 | 1.357 |
| ear height | 36 | 25 | 1.440 |
| boot length (~285 mm combat boot) | 285 | 205 | 1.390 |

All three land in 1.36–1.44, on top of the stature anchor's 1.34–1.43. Seven readings,
four methods, one range.

### Link 3 — the broken link, recorded

The brief's chain is `hand-l.width = 0.044 m` → 52.5 px in pose1 → **0.838 mm/px**. It
fails twice, and the two failures are independent:

**(a) Wrong field.** `hand-l.width = 0.044` is the **palm block**. The four fingers are
separate components at `width 0.016` each, so the spec's own four-finger span is
**0.064 m**, not 0.044 — a ×1.45 error before any pixel is read. *(frame-action)*

**(b) Internally inconsistent even at face value.** Four-finger breadth ÷ stature:

* the spec asserts 0.044 / 1.715 = **0.0257**
* the sheet itself shows 43 / 1225 = **0.0351**
* human anthropometry gives 0.078 / 1.72 = **0.0453**

The spec's hand is ~63 % of what its own sheet shows. It is self-consistent in *shape*
(length/breadth 2.09 vs a real 2.26) but uniformly about half adult size for its own
declared stature. *(barrel, grip, scale-silhouette — three independent derivations.)*

**The pixel half of the brief's chain is fine.** 52.5 px sits inside the range of honest
readings (§4, D2). The metre half is what breaks.

### Link 4 — adopted scale

> **`scale.mmPerPixel = 1.400 ± 0.10 mm/px`** in the native sheet
> `../jinx-i2t/ref/pose_gun_5view.jpg`, **conditional on the DECLARED 1.715 m.**
>
> This **supersedes 0.838 mm/px. Every absolute length in the brief is too small by 1.67×.**

Four of the six reports derived this correction independently and got 1.60×, 1.66×, 1.67×
and 1.70×. The fifth (materials) found no anchor and said so. The sixth (joints-handles)
could not replace the root and reported the chain as "not obviously wrong, also not
confirmed" — its own bracket for muzzle/tube diameter contains the brief's value, which
tests self-consistency, not scale.

### Link 5 — the residual that ratios avoid

pose3's out-of-plane axis angle φ is **not pinned**: the muzzle-collar step-edge bow gives
17.3°, the bore ellipse gives 32°. Absolute **axial** lengths therefore carry a further
+4 % to +18 %. Perpendicular measurements (all diameters) are unaffected.

**Consequence, and the reason §6 is mostly ratios: use ratios. Absolute millimetres in
this contract carry ±15 % at best and rest on an axiom.**

---

## 2. Canonical measurement frame

Every report used a different origin and a different normaliser; several apparent
disagreements in §4 are nothing but that. One frame is frozen here and all of §6 uses it.

**Image frame.** The native sheet `../jinx-i2t/ref/pose_gun_5view.jpg` (3000×1462). The
four crops in `ref/` are byte-exact sub-rectangles of it — `cv2.matchTemplate` returns
**1.0000** at pose0 (42,150), pose1 (642,192), pose2 (1650,203), pose3 (2421,214). Five of
the six reports verified this separately. `ref/_gun_views.png` is a 2.7× bicubic upscale
(its radial power spectrum matches pose3-upscaled, not pose3) — **do not measure off it.**

**Primary view: pose3.** It is the only near-orthographic view — its tube's projected
diameter changes only +2.8 % over 39 px, against −10 % for pose0; pose1 is 27° out of
plane and pose2 is 64°. pose1 is the *character's* side view and is the trap for anyone
reaching for "the side view".

**Model frame (DECLARED).** Origin at the breech face on the bore axis. `+X` forward
(muzzle), `+Y` up (toward the rail), `+Z = X × Y`. All joints are declared at `z = 0`:
every usable view is near-abeam or near-axial, so **no lateral offset of anything is
measurable at all.**

**Axial parameter `u`.** `u = 0` at the frontmost gun vertex (the liner tip, sheet
x = 2604); `u = 1` at the rearmost gun vertex (the butt's rear, sheet x = 2406).
`A = 198 px` projected. On a built model: project every gun vertex on the barrel-tube
mesh's principal axis; `u = (x_max − x) / (x_max − x_min)`.

| landmark | sheet x | `u` | agreement |
|---|---|---|---|
| muzzle / liner tip | 2604 | 0.000 | 3 reports within 1 px |
| muzzle-collar front lip | 2588.5 | 0.078 | 1 report |
| rail forward stud | 2584 | 0.101 | 2 reports within 1 px |
| muzzle-collar rear step | 2567 | 0.187 | 2 reports within 2 px |
| hanging lug (centre) | 2523.5 | 0.407 | 2 reports |
| mid-band (centre) | 2515 | 0.449 | 2 reports within 3 px |
| lattice-collar front face | 2473 | 0.662 | 2 reports within 0.1 px |
| **lattice rear = barrel/frame junction** | **2444** | **0.808** | 4 reports, spread 8 px |
| port (centre) | 2429 | 0.884 | 2 reports within 7 px |
| hammer-spur forward end | 2422 | 0.919 | 1 report |
| receiver rear face | 2415 | 0.955 | 1 report |
| butt rear | 2406 | 1.000 | 1 report |

**Barrel length `L = 160 px` (u 0.000 → 0.808).** The brief's ±8 px on this is halved to
**±4 px**: barrel *inferred* the lattice rear face (occluded in its crop) at 2444, and
frame-action then *measured* it directly in the sheet at 2445 ± 1.5 as a silhouette step,
corroborated by the rail bar and the first lozenge both starting at x 2446.

**Tube diameter `D` = 37 ± 3 px = 52 ± 7 mm.** See §4 D3 — this is the most contested
number in the document and it is the denominator of nearly every ratio.
`R = D/2 = 18.5 px`.

**Barrel axis in pose3:** slope +0.052 ± 0.006 (3.0° ± 0.4° nose-down in the image),
passing through sheet (2431, 265 ± 3).

---

## 3. The assembly tree

Complete, acyclic, single-rooted. One line each. Bracketed counts are instanced children.
`[?]` marks a part whose existence is inferred, not resolved — see §10.

```
zapper                                   root; the whole sidearm
├── barrel                               forward assembly, muzzle to the lattice's rear face (u 0.000-0.808)
│   ├── barrel.liner                     pale steel sleeve, stands PROUD of the collar face
│   │   └── barrel.bore                  the cut cylinder; darkest material on the object
│   ├── barrel.muzzle-collar             stepped brass ring at the muzzle (u 0.078-0.187)
│   │   ├── .ring-fore                   forward raised ring
│   │   ├── .ring-mid                    middle raised ring (the widest)
│   │   └── .ring-aft                    rear raised ring, at the sharpest step on the barrel
│   ├── barrel.tube-fore                 pale steel-blue painted cylinder (u 0.187-0.449)
│   ├── barrel.mid-band                  narrow brass ring encircling the tube (u ~0.449)
│   │   └── barrel.lug                   small tab hanging below the tube, just forward of the band
│   ├── barrel.tube-aft                  warm-brown section, SAME diameter — a paint change, not a step (u 0.449-0.662)
│   ├── barrel.lattice-collar            wide pierced brass sleeve; the signature feature (u 0.662-0.808)
│   │   ├── .rim-fore                    solid forward rim
│   │   ├── .rim-aft            [?]      solid rear rim; never unoccluded in any of nine views
│   │   └── .cutout[0..N-1]              the lozenge openings, N = 16 (accept 12-20)
│   └── barrel.rail                      brass bar lying tangent on the tube's top, no standoff anywhere
│       ├── .mount-block                 reddish block partway along
│       ├── .stud[0..2]                  three small round studs; two inside the mount block, one near the muzzle
│       └── .rear-hook                   hooked tab at the rail's rear; reads as a rear sight but curves FORWARD
├── frame                                receiver group (u 0.808-0.955)
│   ├── frame.receiver                   pale-teal painted body; greener paint than the tube
│   ├── frame.port                       short brass cylinder standing up off the receiver (u 0.884)
│   │   └── .flange             [?]      orange base flange, ~1.4x port OD; pose0 only
│   ├── frame.hammer-spur                elongated brass piece, rearward-up over the breech (u 0.919-0.990)
│   │   └── .rib[0..5]          [?]      5-6 ribs at 4 px pitch; count is 6 ± 2
│   ├── frame.trigger                    blade inside the guard; 8x15 px in the only view that shows it
│   └── frame.trigger-guard              bow from the frame's underside to the grip root
├── grip                                 raked handle (u 0.808-1.000, dropping below the axis)
│   ├── grip.body                        lateral surface: ZERO unoccluded pixels in nine views
│   └── grip.butt-cap                    the only visible grip surface; 23 % of the grip's height
│       └── .toe-stud           [?]      2x3 px warm cluster at the butt's forward-lower corner
└── graffiti.mark[0..k]                  teal and magenta accent marks; may be texture rather than geometry
```

**Named parts: 33** — 29 singular plus 4 instanced families
(`lattice-collar.cutout`, `rail.stud`, `hammer-spur.rib`, `graffiti.mark`). Maximum depth 4
levels (`zapper → barrel → lattice-collar → cutout`). Every node has exactly one parent;
no cycles.

Two parenting decisions are choices, not readings, and are marked so:

* `barrel.lug` under `barrel.mid-band` — **DECLARED.** Two of three readings put them
  touching (their axial spans overlap over u 0.419–0.434); barrel's primary view puts the
  lug immediately *forward* of the band with no overlap. Parenting it to
  `barrel.tube-fore` is equally defensible and changes nothing in §6.
* `barrel.bore` under `barrel.liner` — **DECLARED.** The bore is a void; whichever mesh
  owns the cut is a modelling choice.

---

## 4. Disagreements, and how each was resolved

Twenty. Each gives both numbers, the cause, and the decision. A contract that hid these
would be worth less than one that records them.

**D1 — mm/px: 0.838 (brief) vs 1.34–1.43 (four reports).**
Cause: the brief read `hand-l.width` (a palm block) as a four-finger span, and that field
is itself inconsistent with the same file's declared stature. Decision: **1.400 ± 0.10**,
§1. The brief's value is superseded, not merely widened.

**D2 — four-finger stack: 40 / 43 / 45 / 46.7 / 49 / 52.5 / 57.5 px.**
Cause: two different features and two different poses. In pose1 the index finger is
extended onto the trigger and split from the other three by a ~10 px gap, so
"index-top to little-bottom" (57.5) crosses a gap and "four contiguous widths" (46.7) does
not. In pose3 the four fingers are a clean curled stack. Decision: use pose3 only —
readings 40, 43, 45 → **43 ± 4 px**. This falsifies the brief's 52.5 px *as a pose3
measurement* while confirming it as a plausible pose1 reading.

**D3 — tube OD: 36.3 / 37 / 37 px vs 41 / 41 px. The most load-bearing disagreement here.**
Cause: located precisely. All five reports agree the tube's *bottom* edge is at sheet
y ≈ 290 in pose3. They disagree about a **5-px seam band at sheet y 252–256** lying under
the rail. Barrel puts the tube's top at 253 (the rail's underside; the seam is the tube's
own shaded flank), frame-action puts it at 257 (the seam belongs to the rail). Nobody can
see the tube's true upper silhouette: the rail is tangent along its whole length with **no
background gap in any of four views.**
Arbitration: the lattice collar is the only barrel feature whose **top and bottom edges are
both directly visible** (crop y 27 and y 83). If it is coaxial with the tube — safe for a
sleeve on a cylinder — its silhouette midpoint locates the axis, and the tube's bottom line
then gives `D = 2 × (72.93 − 55.0) = 35.9 px`. A D of 41 would put the axis 2.6 px off that
midpoint. Decision: **D = 37 ± 3 px**, the median, with the tolerance spanning both camps.
**Every ratio that grip and frame-action computed against 41 has been rescaled by 41/37 in
§6 and its tolerance widened by 8 % to carry this.** Rescaled: grip length, grip depth,
grip circumference, port OD, receiver top-above-axis, receiver height.

**D4 — overall projected axial length: 198 px vs 232.7 px.**
Cause: scale-silhouette recovered pose3's frame rear *indirectly*, through a ratio (1.775)
measured in pose0, and got a rear at sheet x ≈ 2370. Frame-action measured the receiver
rear directly in the sheet at 2415, and grip measured the butt rear at 2406 — 36 px
forward of the extrapolation. Decision: the direct measurements win, three reports agreeing
on all the intermediate landmarks. **A = 198 ± 8 px.** scale-silhouette's own caveat
anticipated a possible error here but expected the opposite sign.

**D5 — barrel : frame split, 0.81 vs 0.70.**
Pure consequence of D4. With the corrected overall length the split is **0.808 / 0.192**,
not 0.702 / 0.298. frame-action's own 0.840 is the same quantity measured to the receiver
rear rather than to the butt, and is consistent.

**D6 — bore diameter: 17 vs 21 vs 23 px.**
Cause: a definition, not a measurement. Barrel thresholded at V<80 (the actually-black
hole); the other two read a looser dark region that includes the shadowed inner wall.
Their liner readings differ by the same 1.22× factor, so the *ratio* is stable. Decision:
freeze the ratio that both methods agree on — **bore/liner = 0.74 ± 0.04** (barrel 0.73
over three views, joints 0.75) — and derive the rest. Consistency check:
0.74 × 0.69 = 0.51, and the adopted bore/tube is 0.52. It closes.

**D7 — lattice OD: 51 / 54 / 56 px.**
Cause: where the collar's silhouette edges sit against a dark background above and the
hand below. Decision: **53.5 ± 2.5 px → 1.45 ± 0.12 × D**, the midpoint, containing all
three. This is not cosmetic: it feeds D8.

**D8 — lattice openings: 18 vs 12 vs 9.**
Cause: found, and it is not a measurement conflict at all. Barrel and joints measured the
**same six features** — their y-lists agree to 0.4–1.8 px, and their mean adjacent gaps are
8.25 and 8.40 px. They disagree only on **what one repeat contains**: barrel reads every
dark feature as an opening (→ 360/20° = 18); joints reads dark features as alternating with
solid brown diamonds at the half-pitch (→ 9 X-crossings). scale-silhouette counted only
*complete* lozenges (5 over half the circumference → 10–14).
Decision: freeze the quantity that was actually measured — the **angular pitch of adjacent
dark openings** — and re-run barrel's N-vs-R fit against the *reconciled* lattice OD from
D7 (R = 26.75 px, not 28.75). That moves the fit from N = 18 to **N = 16–17**, and the
direct pitch near the axis (10.2 px on R = 26.75) gives 21.8° → N = 16.5.
**Adopted: 16 openings, accept 12–20, pitch 22 ± 3°, confidence 0.35.** The wide,
asymmetric acceptance band is deliberate: it admits joints' and scale-silhouette's halving.
A separate count for strap crossings is *not* frozen — it is a different quantity and must
not be conflated with this one.

**D9 — muzzle-collar OD / tube OD: 1.13 / 1.13 vs 1.25.**
Two reports independently got 1.13; the third gave 1.25 as the midpoint of an explicit
bracket [1.08 (pose3, muzzle nearer, inflated), 1.37 (pose1, muzzle farther, deflated)]
that contains 1.13. Decision: **1.14 ± 0.08.** Note for whoever builds it: **the collar is
only ~14 % fatter than the tube.** It reads far fatter because it is polished brass against
matt paint, and pose0 puts the step at zero. This is the single place a modeller will
over-build.

**D10 — muzzle-collar rings: 3 / 3 vs 2.**
Two reports got 3 from independent pose pairs (barrel: pose3 + pose1 V-scans; joints:
pose3 + pose2). The third read 2 at confidence 0.35 and accepted 2–3. Decision:
**3, accept 2–4.**

**D11 — liner protrudes vs liner recessed. A direct contradiction.**
barrel: the liner stands **forward** of the collar face — pose1 shows a 24-px-tall section
at x 38–44 jumping to 44+ px at x ≥ 46, and pose0 shows the same 6-px step.
scale-silhouette: the liner is **recessed** — "in pose1 and pose2 the dark bore sits inside
a brass rim on every side".
Decision: **protrudes**, at reduced confidence **0.45** (from 0.70). barrel's is a measured
silhouette step in two poses; scale-silhouette's is an appearance argument about what
surrounds the dark hole, which an oblique view of a *protruding* narrow cylinder also
produces. The contradiction is recorded rather than averaged: these two cannot both be
true, and a builder who chooses "recessed" is choosing against the better evidence, not
against a consensus.

**D12 — the top-rear feature: port or hammer?**
frame-action names two objects above the receiver: a forward cylinder (the "port", OD
15 px, vertical sides to ±1 px in two poses) and a rear elongated brass slab (the "spur",
PCA over 238 px: axis 34.3° above horizontal, aspect 2.77). joints argues from aspect
ratios across five views that the top-rear piece is a **hammer** whose axis points
rearward-up 30°, and that its dark top is a shadowed rear end-face, not an open mouth.
Resolution: the two reports are largely measuring **different objects** — joints' pose1
hammer at sheet x 830–854 is frame-action's spur at x 824–860. Both agree the rear piece is
elongated and points rearward-up at 30–34°. Decision: keep **two** parts —
`frame.port` (forward, near-vertical axis, non-articulating) and `frame.hammer-spur` (rear,
elongated, carrying the hammer joint). Count of protrusions above the receiver = **2**, at
reduced confidence **0.65** (from 0.75), because joints' alternative reading collapses them
to one. The hammer joint is assigned to the rear spur: frame-action's PCA over 238 pixels
is the more quantitative attitude measurement.

**D13 — grip rake: 108° vs 62°.**
Mostly a convention clash. In one convention (bore-forward to grip-down) the readings are
pose3 104.2°, clay B 105.4°, clay E 110.0°; joints' pose3 "74° between the lines" is the
same thing (→ 106°). Only joints' clay c1 (50° → 130°) is a genuine outlier, and it is a
different clay panel from the two the grip report used. Decision: **107° ± 10°**, tolerance
widened from ±8° to admit the outlier's direction. Recorded: every projected reading is a
**lower bound** — the bore is open in all nine views, so the barrel tilts toward camera in
all of them and projection pulls the angle toward 90°.

**D14 — port axial position: 0.90 vs 0.77.**
Not a disagreement about the port. The two reports normalised by different axial spans
(188 px vs 242 px). Their measured sheet positions agree to 7 px. In the frozen frame the
port centre is at **u = 0.884 ± 0.030**. This is exactly what §2 exists to prevent.

**D15 — lattice rear / frame junction: 2437 / 2441 / 2444 / 2445.**
Spread 8 px, one outlier (joints, whose whole axial frame is shifted ~8 px rearward).
Decision: **2444 ± 4**, the value three reports cluster on, one of them a direct
silhouette-step measurement with two corroborating features.

**D16 — barrel brass rings: 3 vs "confident 5, likely 6–7".**
Granularity, not conflict. Decision: three separate constraints —
**3 encircling brass assemblies** (collar, mid-band, lattice), **5 exterior diameter
steps**, **3 rings within the muzzle collar**.

**D17 — grip material: "dark red-brown wood with brass pins and a grey inlaid panel"
(brief) vs pale steel-blue matching the frame (grip report).**
The grip report found the butt reads pale desaturated blue-grey in two poses (pose3 S 5–7;
pose0 hue 105–125), matching the frame and nothing else; the tan band that resembles an
inlaid panel tracks the *hand*, not the gun, and is the glove's palm patch; the gold
triangles are glove studs (they appear on the non-gun hand too). The materials report
independently found **zero measurable grip pixels**. Decision: **grip material = frame
material**, confidence 0.55. **The brief's grip description is not supported by a single
pixel and every part of it must be marked DECLARED if used.**

**D18 — lattice axial length: 26 / 28 / 32 px.** Decision: **29 ± 4 px = 0.181 ± 0.025 L.**

**D19 — trigger and guard: "zero usable pixels in all five figures" (frame-action) vs
measured (joints, grip).**
Cause: frame-action worked only from the four colour crops named in the brief; joints and
grip additionally read `../jinx-i2t/ref/pose_gun_clay_6view.jpg`, an untextured clay
turnaround of the same asset, where clay panel c1 shows the trigger blade
(692–700, 256–272) inside the guard bow. Decision: **the trigger and guard exist and are
measurable, but only in the clay sheet, at 8×15 px.** Every guard *dimension* remains
DECLARED. Recorded as a methodological finding: three of six reports used the clay sheet
and it is the only place the grip butt, the trigger and the guard read at all.

**D20 — mid-band axial length: 6.5 / 8 / 12 px.** Decision: **8 ± 2 px = 0.050 ± 0.013 L.**

---

## 5. Independent agreements

Where two reports reached the same number by different methods, that is evidence, and it is
what the high-confidence rows in §6 are built on.

1. **Crop → sheet registration at correlation 1.0000**, verified separately by five of the
   six reports at the same four coordinates. The crops are byte-exact; the sheet buys no
   detail.
2. **The scale correction**, derived four times independently: ×1.60, ×1.66, ×1.67, ×1.70.
3. **The muzzle-collar rear step.** barrel 0.763 L, joints 0.775 L — **0.012 apart**, two
   different methods (warm-fraction column scan vs landmark table). The sharpest edge on
   the barrel and the best axial datum available.
4. **The axial zone lengths**, by two unrelated methods — barrel's silhouette + warm-fraction
   classification and materials' per-column median-hue seam scan. Every zone agrees within
   5 px: collar 22.4/22, blue 50.6/52, band 6.6/8, warm 36/31, lattice 29/33.
5. **The rail studs.** joints sheet x 2511 / 2519 / 2584; scale-silhouette 2511 / 2516 /
   2583 — **within 3 px on all three**, from different poses.
6. **The lattice front face.** barrel 2473.0 (crop arithmetic); scale-silhouette 2472.9
   (axial station ÷ cos 16° from the muzzle) — **0.1 px apart**, methods with nothing in
   common.
7. **Three muzzle-collar rings**, from two disjoint pose pairs (pose3+pose1, pose3+pose2).
8. **bore / liner = 0.73** (barrel, three views) and **0.75** (joints, pose3).
9. **Copper : steel length = 0.712** (pose3) and **0.689** (pose0) — 3 % apart.
10. **The tube is a cylinder, not a cone**: barrel's bottom silhouette is straight to
    0.36 px rms over 38 px; scale-silhouette's perpendicular width is constant at 43–44 px
    over 80 px of axis. pose0 alone reads 31→38 px and would have produced a false taper.
11. **Port forward of spur**, confirmed in pose0 and pose3 — two poses that view *opposite*
    ends of the gun, so it is not one camera's artefact.
12. **Tube paint a\* = −1, b\* = −7** reproduced in three poses (n = 559 / 570 / 405); the
    single most reproducible number in the document.
13. **Barrel and joints measured the same six lattice features** to within 0.4–1.8 px — see
    D8. Their famous factor-of-two disagreement contains no measurement conflict at all.

---

## 6. Constraints

**123 constraints.** Kinds: `ratio` 54, `relation` 30, `count` 18, `angle` 11,
`dimension` 10. Ten carry a **DECLARED** marker — they are choices the reference cannot
adjudicate, and they are named as such rather than dressed as measurements.

Only the 10 `dimension` rows depend on the scale chain of §1. **The other 113 survive the
declared 1.715 m being wrong**, which is the whole reason they are written as ratios.

Checking conventions, assumed once:

* **AABB** = per-mesh **world-space** axis-aligned bounding box computed from *transformed*
  vertices — never a cached geometry bbox.
* **axis** = the principal axis of the `barrel.tube-fore` mesh, muzzle-forward.
  **`D`** = that mesh's largest extent perpendicular to axis. **`R` = D/2.**
  **`L`** = the barrel group's axial extent. **`A`** = the whole gun's axial extent.
  **`u`** as defined in §2.
* **[SIL]** needs an orthographic side render along −Z. **[MAT]** reads assigned material
  base colours, converted to CIE L\*a\*b\*, hue `h = atan2(b*, a*)`, chroma
  `C* = hypot(a*, b*)`. **[RAY]** needs a ray cast. Everything else reads AABBs.
* **conf** is confidence that the constraint is *true of the object*, not that the number is
  precise.

### 6.1 Scale — all conditional on the DECLARED 1.715 m

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `scale.mmPerPixel` | dimension | 1.400 ± 0.10 mm/px | not a model property; the conversion any absolute below must use. Falsifiable by re-measuring any body landmark in a 3000×1462 render | 7 readings, 4 methods, 1.34–1.44 (§1). **DECLARED root.** Supersedes 0.838 | 0.55 |
| `scale.stature.px` | dimension | 1225 ± 45 px | re-measure hair-crest to sole in the sheet | 1278/1220/1197/1217, four reports | 0.70 |
| `scale.handBreadth.px` | dimension | 43 ± 4 px (pose3 frame) | measure the four curled fingers in a clean grip pose | pose3 readings 40/43/45. **Falsifies the brief's 52.5 px as a pose3 measurement** | 0.65 |
| `scale.brief.superseded` | relation | every absolute length = 1.67 × the brief's chain | recompute any mm value both ways; the contract's must be the larger | §1 link 3, four independent derivations | 0.75 |

### 6.2 Global silhouette

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `gun.length.overTubeOd` | ratio | 5.35 ± 0.55 | union of all gun meshes projected on axis, ÷ D | 198/37, corrected per D4 (scale-silhouette's 6.54 superseded) | 0.60 |
| `gun.height.overTubeOd` | ratio | 3.11 ± 0.35 | whole-gun AABB extent in the grip plane ÷ D | port top y236 → grip heel y351 = 115 px | 0.55 |
| `gun.height.overLength` | ratio | 0.58 ± 0.06 | as above ÷ axial extent | 115/198 (was 0.48 on the old length) | 0.55 |
| `gun.barrel.axialFraction` | ratio | 0.808 ± 0.030 | (axial extent from frontmost vertex to `lattice-collar` rear face) ÷ A | 160/198; frame-action's 0.840 is the same to the receiver rear | 0.70 |
| `gun.frame.axialFraction` | ratio | 0.192 ± 0.030 | 1 − above | derived | 0.70 |
| `gun.length.overCharacterHeight` | ratio | 0.162 ± 0.015 | if placed in the character scene: gun axial extent ÷ character height | 198/1220, one panel, no scale chain | 0.60 |
| `gun.length.overHandBreadth` | ratio | 3.3 ± 0.8 | gun axial extent ÷ hand-mesh four-finger breadth | pose3 3.72, pose1 3.13, clay 2.61. **Downgraded** — barrel offered 3.05 ± 0.25 at conf 0.75, but it mixed poses, and the finger stack is not a repeatable landmark (D2) | 0.40 |
| `gun.maxWidth.isLatticeCollar` | relation | no mesh's perpendicular extent exceeds `lattice-collar`'s | compare max perpendicular extents | no top view and no orthographic muzzle-on view exists; the sight hook and frame cheeks could break this | 0.40 |
| `gun.length.mm` | dimension | 290 ± 45 mm | axial extent | 198 px × 1.400 × 1/cos φ, φ ∈ [16°,32°]. **DECLARED chain** | 0.35 |
| `barrel.tube.od.mm` | dimension | 52 ± 7 mm | D | 37 px × 1.400; perpendicular, so no φ term | 0.45 |
| `barrel.tube.od.px` | dimension | 37 ± 3 px (pose3 frame) | re-render from the pose3 camera; measure the tube silhouette minus the rail | D3 arbitration | 0.65 |

### 6.3 Barrel — form and axis

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.tube.constantOd` | relation | max radius varies < 3 % over u 0.10–0.66 | [SIL] sample r(x) at 200 stations | bottom silhouette straight to 0.36 px rms; the +2.8 % is perspective | 0.80 |
| `barrel.tube.circular` | relation | tube AABB Y-extent = Z-extent within 4 % | compare AABB extents | pose2 bore ellipse 0.887 vs liner 0.894 — equal within noise, i.e. concentric circles seen obliquely | 0.75 |
| `barrel.tube.step.noneAtPaintLine` | count | 0 steps in u 0.45–0.66 | require max abs(r(x) − r_tube) < 0.03 r_tube there | copper section's bottom edge sits −0.25 px mean off the steel tube's fitted line; extrapolation error ±0.23 px | 0.85 |
| `barrel.step.count` | count | 5 exterior diameter steps | [SIL] sample r(x) at 200 stations; count dr/dx sign changes exceeding 2 % of R | lattice↓tube, band↑, ↓tube, collar↑, ↓liner | 0.70 |
| `barrel.brassRing.count` | count | 3 encircling brass assemblies | count meshes forming a full ring with OD > 1.05 D; assert axial order collar < mid-band < lattice | three poses agree | 0.85 |
| `barrel.lattice.coaxial` | relation | lattice axis within 0.03 R of the tube axis | compare AABB centre lines | silhouette midpoint 55.0 vs axis 54.7 on an 18-px radius. **This is also the arbitration in D3** | 0.80 |
| `barrel.rail.tangent` | relation | rail's min radius ≤ 1.02 R | [RAY] min radial distance from axis to the rail mesh | no background pixel between rail underside and tube in any of four views; a standoff would show one | 0.65 |
| `barrel.rail.proud.overTubeOd` | ratio | 0.12 ± 0.04 | (axis→rail top − R) ÷ D | pose3 x2554: rail top +26.0, tube top +21.6 | 0.50 |
| `barrel.rail.axialSpan` | ratio | ≥ 0.55 of L | rail AABB axial extent ÷ L | rail spans 2479–2592 of the 2444–2604 barrel | 0.60 |
| `barrel.rail.studs.count` | count | 3, accept 3–4 | count `rail.stud.*` children; exactly 2 must share the mount block's axial position to within 0.5 stud diameters | **two reports within 3 px on all three positions** (§5.5) | 0.80 |
| `barrel.underLug.count` | count | 1 | meshes whose AABB centre is below the axis, in u 0.38–0.48 | pose3, pose1 | 0.70 |
| `barrel.axis.imageSlope` | angle | 3.0° ± 0.4° nose-down in a pose3-matched render | [SIL] fit the tube's bottom silhouette | three reports: 0.0477, 0.052, 0.055 | 0.75 |

### 6.4 Barrel — axial map (fractions of `L` unless stated)

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.muzzleCollar.step.u` | ratio | 0.187 ± 0.020 of A (= 0.232 L) | [SIL] largest positive dr/dx in the forward half of r(x) | **barrel and joints 0.012 apart** (§5.3); sharpest edge on the object | 0.85 |
| `barrel.midBand.centre.u` | ratio | 0.449 ± 0.030 of A | mid-band AABB axial centre | barrel 2512.2, joints 2515 | 0.70 |
| `barrel.lattice.front.u` | ratio | 0.662 ± 0.025 of A | lattice AABB forward face | **barrel 2473.0, scale-silhouette 2472.9** (§5.6) | 0.75 |
| `barrel.lattice.rear.u` | ratio | 0.808 ± 0.025 of A | lattice AABB rear face; also the barrel/frame junction | four reports, D15 | 0.75 |
| `barrel.lug.centre.u` | ratio | 0.407 ± 0.030 of A | lug AABB axial centre | pose3 2518–2529 | 0.55 |
| `barrel.railFwdStud.u` | ratio | 0.101 ± 0.020 of A | forward stud AABB centre | two reports within 1 px | 0.60 |
| `barrel.lattice.length` | ratio | 0.181 ± 0.025 L | lattice AABB axial extent ÷ L | 29 ± 4 px, D18 | 0.70 |
| `barrel.midBand.length` | ratio | 0.050 ± 0.013 L | as above | 8 ± 2 px, D20 | 0.55 |
| `barrel.muzzleCollar.length` | ratio | 0.140 ± 0.025 L | as above | pose3 22.5 px; pose0 0.119 | 0.60 |
| `barrel.copperOverSteel.length` | ratio | 0.71 ± 0.08 | warm-material section axial extent ÷ pale section's | **pose3 0.712, pose0 0.689** | 0.80 |
| `barrel.zone.axialFractions` | ratio (6-vec) | lattice 0.19, warm 0.21, band 0.05, blue 0.32, collar 0.14, liner 0.10; each ± 0.035 | sort meshes by axial centroid, take extents ÷ L | **two unrelated methods agree within 5 px on every zone** (§5.4) | 0.65 |
| `barrel.zone.order` | relation | muzzle→breech: brass collar, blue paint, brass ring, warm brown, brass lattice | sort meshes by axial centroid, compare material ids | identical in pose3 and pose1 seam scans | 0.85 |
| `barrel.zone.blueOverWarm` | ratio | 1.62 ± 0.15 | axial extents | 52/31 pose3, 37.5/24 pose1 | 0.75 |
| `barrel.zone.warmOverMidBand` | ratio | 3.95 ± 0.60 | axial extents | 31/8 pose3, 24/6 pose1 | 0.65 |
| `barrel.midBand.isPaintBoundary` | relation | the warm/pale material boundary lies inside the mid-band's axial extent | compare the material boundary with the band's AABB | warm fraction falls 0.90→0.08 across exactly the band's span | 0.75 |

### 6.5 Barrel — diameters (all ÷ D)

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.lattice.od` | ratio | 1.45 ± 0.12 | lattice AABB max perpendicular extent ÷ D | 53.5 ± 2.5 px, D7 (readings 51/54/56) | 0.65 |
| `barrel.midBand.od` | ratio | 1.18 ± 0.07 | as above | bottom-edge step +3.3 ± 0.7 px on R 18.15 | 0.70 |
| `barrel.muzzleCollar.od` | ratio | 1.14 ± 0.08 | as above | **two reports at 1.13**; third brackets [1.08, 1.37]. D9 | 0.65 |
| `barrel.liner.od` | ratio | 0.69 ± 0.09 | as above | barrel 0.63, joints 0.76 — a threshold difference, D6 | 0.55 |
| `barrel.bore.d` | ratio | 0.52 ± 0.09 | [RAY] axial ray-fan at the muzzle face | 0.47/0.57/0.62; derived cross-check 0.74×0.69 = 0.51 ✓ | 0.55 |
| `barrel.bore.dOverLinerOd` | ratio | 0.74 ± 0.04 | [RAY] fan ÷ liner AABB | **barrel 0.73 over three views, joints 0.75.** The most stable number in the muzzle group | 0.85 |
| `barrel.lattice.axialLenOverOd` | ratio | 0.55 ± 0.10 | lattice axial extent ÷ its own OD | 29/53.5; scale-silhouette 0.65, barrel 0.50 | 0.55 |
| `barrel.lug.radialReach` | ratio | 1.2–1.8 R | lug AABB max radial extent ÷ R | pose3 1.27, pose1 ~1.45, pose0 ~1.75 — **the poses disagree**; 8×5 px in the best view | 0.25 |

### 6.6 Lattice collar

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `lattice.opening.count` | count | **16, accept 12–20** | [RAY] cast 720 rays outward from the axis in the collar's axial midplane; count contiguous miss-arcs | D8. Barrel's N-vs-R fit re-run against the reconciled OD (R = 26.75) gives 16–17; direct pitch gives 16.5. Acceptance band admits the halving readings | 0.35 |
| `lattice.opening.pitch` | angle | 22 ± 3° | angle between adjacent cutout centroids about the axis | 10.2 px projected pitch nearest the axis on R 26.75 = 21.8°; barrel measured 20.0–20.9° on R 28 | 0.50 |
| `lattice.opening.axialLen` | ratio | 0.069 ± 0.012 L | mean axial extent of the cutout volumes ÷ L | components measure 10–12 px | 0.55 |
| `lattice.openFraction` | ratio | 0.55–0.70 | [RAY] fraction of 360 rays at the axial mid-station that miss geometry | hole height 7 px against a 10.2-px pitch at the axis | 0.40 |
| `lattice.rows` | count | 1 — **DECLARED** | count distinct axial bands of cutouts | at y 40/50/60 the openings merge into 10–12 px blobs; at y 32/69/76 they resolve as pairs. Two staggered rows fit equally well and are **not excluded** | 0.40 |
| `lattice.abutsFrame` | relation | lattice rear face coincident with the frame's forward face within 0.05 D | compare AABB faces | pose3 x2444 is simultaneously the lattice rear and the frame front; pose0 likewise | 0.70 |

### 6.7 Muzzle

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `muzzle.ring.count` | count | 3, accept 2–4 | [SIL] count local maxima of r(x) over the collar's axial span | **two disjoint pose pairs** (§5.7); 3 raised rings, 2 grooves | 0.70 |
| `muzzle.liner.protrudes` | relation | liner AABB axial max exceeds the collar's by 0.05 ± 0.03 L | compare AABBs | pose1 and pose0 both show a 6-px step to a 24-px section ahead of a 44-px collar. **scale-silhouette reads this the opposite way — D11** | 0.45 |
| `muzzle.bore.concentric` | relation | bore axis within 0.10 R of the tube axis | fit the bore cylinder's axis; compare to the tube's centre line | **DECLARED.** Three methods give 6 %, 10 %, 14.6 % — all inside their own noise. A deliberately offset bore would be invention; a perfectly concentric one is a legitimate choice that must be marked | 0.50 |
| `muzzle.collar.rings.equalOd` | relation | the 3 rings' ODs differ by < 0.03 D — **DECLARED** | compare ring AABBs | grooves resolve; ring-to-ring radius differences are under 1 px | 0.35 |

### 6.8 Frame and action

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `frame.protrusionsAbove.count` | count | 2 | count meshes whose AABB min-up exceeds receiver max-up − 0.10 D, restricted to u > 0.81 | one brass cylinder + one brass slab in each of three poses. **Downgraded from 0.75 — D12** | 0.65 |
| `frame.portForwardOfSpur` | relation | u(port centre) < u(spur centre) | AABB centres | pose0 and pose3 agree, and they view **opposite ends** | 0.70 |
| `frame.port.centre.u` | ratio | 0.884 ± 0.030 of A | port AABB centre projected on axis | two reports within 7 px; the 0.90-vs-0.77 gap was a normaliser artefact — D14 | 0.65 |
| `frame.port.od` | ratio | 0.41 ± 0.07 of D | port lateral extent ÷ D | 15 px pose3, 12 px pose0. **Rescaled from 0.34 per D3** | 0.55 |
| `frame.port.heightOverOd` | ratio | 1.3 ± 0.4 | (port max-up − receiver max-up) ÷ port OD | pose3 1.0; pose0 1.5, or 1.7 after correcting for the 29° camera elevation implied by the rim ellipse (minor/major 0.50) | 0.50 |
| `frame.port.gapToCollar` | relation + ratio | axially disjoint from the lattice; gap 0.037 ± 0.020 L | AABB overlap on axis must be empty | 7 px of clean background at pose3 x 2438–2445 | 0.70 |
| `frame.port.axisPerpendicular` | angle | within 15° of `up`; lateral component < 0.26 | dot the port's principal axis against `up` and the lateral vector | port sides vertical to ±1 px over 10 rows in **two** poses | 0.60 |
| `frame.port.hollow` | relation + ratio | top face recessed; bore/OD 0.45 ± 0.15 | [RAY] a ray down the port axis must enter more than one surface | **5 interior pixels against a 2-px rim, in one pose.** A domed solid with a specular ring looks identical, and joints reads the same pixels as a shadowed end-face | 0.30 |
| `frame.spur.aspect` | ratio | 2.8 ± 0.7 | spur AABB longest ÷ second-longest extent | PCA over 238 brass px: 32.7 × 11.8; also clay 2.15, pose0 1.71, pose2 2.5 | 0.55 |
| `frame.spur.lengthOverTubeOd` | ratio | 0.82 ± 0.20 | spur longest extent ÷ D | 32.7 px against pose1's tube. **Rescaled from 0.73 per D3** | 0.45 |
| `frame.spur.attitude` | angle | 32 ± 8° above the bore axis, pointing rearward | angle of the spur's principal axis to `axis` in the sagittal plane | PCA 34.3° (pose1); clay 23°, pose1 38° | 0.55 |
| `frame.spur.clearance` | relation | separated from the frame in a side silhouette except at a neck ≤ 0.45 × its own diameter | [SIL] the spur's rendered region must be ≥1 px of background from the frame's | pose1 background sky visible at (175–190, 55–75) between the piece and the frame | 0.70 |
| `frame.hammer.ribs.count` | count | 6 ± 2 | sample surface radius along the spur's own axis; count local maxima | clay 5–6 at 4 px pitch; pose1 5. What pose3 seemed to show is JPEG chroma noise, not ribs | 0.45 |
| `frame.top.aboveAxis` | ratio | 0.32 ± 0.10 of D | receiver AABB max-up ÷ D, axis at up = 0 | 12 ± 3 px. Chosen because it avoids the occluded underside. **Rescaled from 0.29 per D3** | 0.55 |
| `frame.topBelowBarrelTop` | relation + ratio | receiver max-up < tube max-up; drop 0.13 ± 0.09 D | compare AABBs | pose3 drop 5 ± 3 px | 0.50 |
| `frame.heightOverTubeOd` | ratio | ≥ 1.05 (**lower bound, not a target**) | receiver up-extent ÷ D | visible height 41 ± 5 px; the lower edge is where the hand starts, so the true frame can only be taller. **Rescaled from ≥0.95 per D3** | 0.45 |
| `frame.rearFace.angle` | angle | within 15° of the axis normal over its lower 60 % | [SIL] fit a line to the rearmost receiver boundary between 20 % and 80 % of its height | pose3 holds x 2414–2416 from y 266 to 290 — 2 px over 25 px = 4.6° | 0.50 |
| `frame.receiverRear.u` | ratio | 0.955 ± 0.020 of A | rearmost receiver vertex | pose3 x 2415, direct | 0.60 |
| `frame.surfaceFeatures.count` | count | 0 — **DECLARED** | count receiver children with AABB diagonal > 0.02 L, excluding port and spur | nothing on the receiver exceeds 3 px in any pose; the orange marks there classify in the graffiti hue band, i.e. paint. **The reference cannot distinguish "smooth" from "detailed below 3 px"; this constraint chooses smooth.** 0.5 as a choice, 0.0 as a measurement | 0.50 |
| `action.nothingBelowBarrelForward` | relation | no mesh extends below the tube's lower surface at u < 0.66 | for every mesh with u(centre) < 0.66, AABB min-up > tube min-up − 0.05 D | the region below the barrel forward of pose3 x 2470 is clean background. **The only hard statement available about the guard's forward reach** | 0.70 |
| `frame.trigger.insideGuard` | relation | the trigger mesh's AABB lies wholly inside the guard's | AABB containment | clay c1 (692–700, 256–272) inside the bow; also clay c3, c4 | 0.85 |

### 6.9 Grip

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `grip.rakeFromBore` | angle | 107 ± 10° | angle between the bore's forward direction and the grip's downward axis (grip AABB top-face centre − bottom-face centre) | pose3 104.2°, clay B 105.4°, clay E 110.0°, joints pose3 ≈106°; joints clay c1 130° is the outlier. **All projected readings are lower bounds** — D13 | 0.60 |
| `grip.length.overTubeOd` | ratio | 1.55 ± 0.20 | grip AABB extent along the grip axis ÷ D | pose3 62.9 px (= 1.70 at D 37); clay A 1.38 in its own frame. **Rescaled per D3** | 0.55 |
| `grip.depth.overTubeOd` | ratio | 0.84 ± 0.18 | grip cross-section at 50 % height, extent along the bore ÷ D | pose3 fist 55 px − 10 finger − 14 palm = 31 px. **Rescaled per D3** | 0.40 |
| `grip.width.overTubeOd` | ratio | 0.47 ± 0.15 — **DECLARED** | same section, extent perpendicular to bore and grip axis ÷ D | **zero unoccluded pixels in nine views.** Floor 0.32 from the clay butt's short axis; the rest is a 1.6:1 depth:width assumption | 0.25 |
| `grip.circumference.overTubeOd` | ratio | ≤ 2.75 (**upper bound only**) | convex-hull perimeter of the mid-height section ÷ D | 2 × the pose3 knuckle-to-tip finger wrap. The hand must close on it. **Rescaled per D3.** Under the brief's 0.838 mm/px the grip is 77 mm around — a hand pinches that, it does not grip it | 0.60 |
| `grip.butt.majorAxis.overTubeOd` | ratio | 1.15 +0.25 / −0.10 | longest chord of the grip's bottom face ÷ D | clay A 39/34, its own frame — no rescale. Exceeds the depth, so the butt is flared or spurred | 0.50 |
| `grip.heelDrop.overTubeOd` | ratio | 2.19 ± 0.20 | perpendicular distance from the axis to the grip AABB's lowest point ÷ D | axis y 269.3 at x2440, butt bottom y 350 → 80.6 px | 0.60 |
| `grip.root.flushWithFrame` | relation | gap ≤ 0.03 D, and the grip's axial footprint lies inside the frame's | abs(grip max-up − frame min-up) ≤ 0.03 D | pose3's frame underside is one unbroken dark line at y 288–293 with no gap or step | 0.80 |
| `grip.butt.behindFrameHeel` | relation | butt rearmost is 0.05–0.35 D rearward of the frame's rearmost | project both AABBs on axis | pose3 frame heel 2415, butt rear 2406 → 0.22 D | 0.50 |
| `grip.length.overHandBreadth` | ratio | 1.47 ± 0.20 | grip on-axis length ÷ hand-mesh four-finger breadth. **Scale-chain-free** | pose3 63 px / 43 px | 0.55 |
| `grip.fingerCourse.count` | count | 4, exact | on-axis length × 0.65 ≥ 4 × (D/4), and no transverse feature interrupts the front strap between 12 % and 77 % of grip height | pose3 stack occupies 8 %–75 % of the grip's run, unbroken | 0.70 |
| `grip.butt.toeStud.count` | count | 1 ± 1 (0, 1, 2 all pass) | count differently-materialled sub-meshes with centroid within 0.15 D of the butt's forward-lower corner | one 2×3 px warm cluster at pose0 (168–169, 293–295) — the only warm pixels on the whole grip assembly. At 3–4 mm a pin, a screw and a chamfer highlight are the same thing | 0.30 |

### 6.10 Materials

Hue and chroma, not lightness: **no whole part on this object is a flat colour sample.**
The p5–p95 L\* span of every part is 35–52, which is painted terminator ramp, not sampling
error. Every colour claim below is anchored on (a\*, b\*) inside a matched-L window.

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `mat.paint.tube.ab` | dimension | a\* = −1.5, b\* = −7.0, each ± 1.5 | [MAT] on the tube paint | CI a\*[−2,−1] b\*[−7,−7] in **three** poses, n = 559/570/405. The most reproducible number in the document | 0.90 |
| `mat.brass.twoTones` | relation | h(yellow) − h(aged) ≥ 8° | [MAT] difference | Δ16.5° pose3, Δ12.7° pose1; bootstrap CIs disjoint in both | 0.85 |
| `mat.brass.aged.hue` | angle | 66.5 ± 5° | [MAT] on collar / lattice / mid-band | 68.2 / 64.6 (pose3), 68.6 / 65.0 (pose1) | 0.80 |
| `mat.brass.yellow.hue` | angle | 79 ± 6° | [MAT] on rail + rear hook | 81.1 [79.0, 82.7] pose3 n=84; 77.7 [76.0, 79.1] pose1 n=204 | 0.75 |
| `mat.brass.count` | count | 2 | [MAT] count materials with h ∈ [55°, 95°], C\* > 15 | as above | 0.70 |
| `mat.warmTube.notBrass` | relation | C\*(warm tube) ≤ C\*(aged brass) − 2.0 | [MAT] | 16.8 vs 20.2 (pose3), 16.8 vs 18.8 (pose1) — same hue family, lower chroma in both | 0.75 |
| `mat.warmTube.chromaRatio` | ratio | 1.31 ± 0.15 | [MAT] C\*(yellow brass) ÷ C\*(warm tube) | 1.27 pose3, 1.36 pose1 | 0.70 |
| `mat.warmTube.notWood` | relation | no grain texture; residual sd after removing cross-axis shading < that of the plain painted tube | [MAT]/[SIL] | warm 7.18 vs blue 9.19 — the warm zone is **smoother**, not grainier | 0.65 |
| `mat.paint.frame.greener` | relation | a\*(frame) ≤ a\*(tube) − 1.5 | [MAT] difference | pose0 −4.0 [−4,−3] vs −1.0 [−2,−1], **same image, same light** | 0.70 |
| `mat.bore.interior.L` | dimension | L\* 21.5 ± 3 | [MAT] innermost bore mesh | 22.0 pose3 n=98, 21.6 pose1 n=165 | 0.80 |
| `mat.bore.darkest` | relation | L\*(bore) ≤ min(exterior L\*) − 8 | [MAT] over all materials | exterior min 34.1 (rail); gap 12.5 | 0.80 |
| `mat.noBareSteel` | relation | no material with C\* < 3 covers > 2 % of visible area | [SIL] + [MAT] | 3.0 % / 3.3 %, unclustered across every part, median L\* ≈ the gun's median — the low-chroma tail of the blue paint, not a zone | 0.70 |
| `mat.mount.red.hue` | angle | 37 ± 7° | [MAT] on the rail mount block | 34.3 / 39.3 / 38.9 across three poses | 0.70 |
| `mat.accent.hues` | angle | teal 185 ± 6°, magenta 351 ± 6° | [MAT] on the accent materials | 184.3 / 184.9 / 186.2 and 349.2 / 353.0 / 351.3 — ±2° cross-pose. **Fails the L-span rule irreducibly** (marks are 2–7 px); trust rests on cross-pose agreement, not span | 0.80 |
| `mat.accent.L_gap` | dimension | L\*(teal) − L\*(magenta) = +24 ± 6 | [MAT] | 27.1 / 22.0 / 24.7 | 0.75 |
| `mat.accent.outchroma` | relation | C\* of each accent ≥ 1.7 × C\* of every structural material | [MAT] | max structural 21.6; accents 1.76× and 2.45× | 0.75 |
| `mat.grip.notWood` | relation | grip material id == frame material id | compare ids | butt HSV matches the frame in two poses; not brass, not wood. **Contradicts the brief — D17** | 0.55 |
| `mat.count.total` | count | 7 structural + 2 accent = 9 — **DECLARED** | count material slots | the material/variant boundary is a choice; the measured clusters are listed above | 0.50 |
| `area.warmToCool` | ratio | 2.20 ± 0.25 in a barrel-only view | [SIL] hue-family predicates on a rendered view | 2.19 pose3, 2.22 pose1 (drops to 1.5 when the cool-painted frame is in view — which is itself the check that the frame is cool) | 0.75 |
| `area.brassShare` | ratio | 0.48 ± 0.05 of assigned visible area, pose3 camera | [SIL] | 3839 / 8020 px | 0.65 |
| `shading.ramp` | dimension | p5→p95 L\* of any single-material cylinder ≥ 30 | [SIL] per-part percentiles under the reference key light | 34.8 (blue) … 51.8 (lattice). **Partly DECLARED** — conditional on reproducing that lighting | 0.45 |

### 6.11 Graffiti — all per-view, never per-object

There is no clean orthographic view of either face, so no mark count can be stated for the
whole object. Every row below is a property of a *rendered view*.

| id | kind | value ± tol | check | evidence | conf |
|---|---|---|---|---|---|
| `graffiti.onMetal` | relation | ≥ 25 % of graffiti area sits on brass parts | per-island host-mesh lookup | 32 % (41 % including the knob); marks confirmed wholly on brass at (24.3, 35.6), (169.8, 42.8), (157.5, 66.5) | 0.80 |
| `graffiti.coverage` | ratio | 0.019 ± 0.008 of silhouette area | [SIL] accent mask ÷ silhouette | 0.0249 / 0.0164 / 0.0171 / 0.0153 across four poses | 0.75 |
| `graffiti.count.perView` | count | 13 ± 5 marks ≥ 3 px at 236×118 | [SIL] connected components | 16 / 10 / 12 | 0.70 |
| `graffiti.crossesSeam` | count | ≥ 1 island spanning 2 meshes | per-island host-mesh count | 2 found: magenta at (153.7, 67.9) spans tube paint + muzzle collar; teal at (53.6, 63.4) spans lattice + warm tube | 0.70 |
| `graffiti.tealMagentaArea` | ratio | 1.8 ± 0.5 | [SIL] area ratio | 1.94 / 1.81 / 1.54 | 0.65 |
| `graffiti.orientationRandom` | angle | mean abs(mark axis − barrel axis) ∈ [35°, 55°] | [SIL] PCA per island | 46.0° over 16 marks (uniform would be 45°) — **the marks ignore the form** | 0.60 |
| `graffiti.densityBias` | ratio | 2.5 ± 1.0 (paint ÷ brass density) | [SIL] marked px per substrate px | 4.34 % vs 1.74 % — biased toward paint, but a third of all graffiti sits on brass | 0.55 |
| `graffiti.sizeMaxOverMedian` | ratio | 1.9 ± 0.6 | [SIL] sqrt(4A/π) per island | 2.33 / 1.64 / 1.72 | 0.50 |
| `knob.magenta.count` | count | 1 ± 1 | count magenta regions ≥ 15 px that carry an interior specular highlight | pose3 (37,81)–(42,85), 21 px, with its own specular rim; recurs in pose2 at (78,93). **A painted knob, not a splatter** — excluded from the counts above | 0.50 |

---

## 7. Joints

Ranges are stated as **geometric contact rules** wherever possible. A degrees figure
invented from nothing is unfalsifiable; a contact condition is checkable and *derives* the
degrees.

**All joints are DECLARED at z = 0.** Every usable view is near-abeam or near-axial, so no
lateral offset of any joint is measurable. One clay panel weakly hints the hammer sits
off-centre; it could not be confirmed and nothing here is built on it.

### Shipped

**J1 `frame.hammer`** — parent `frame`, child `frame.hammer-spur` — **confidence 0.45**
* type revolute; **axis** (0,0,1) ± 3° — DECLARED (a piece in the sagittal plane can only
  swing about Z)
* **pivot** at the spur's forward-lower corner: `u = 0.92 ± 0.04`, `+0.6 ± 0.3 R`, `z = 0`
* **rest** = the reference pose: the spur's axis 32 ± 8° above the bore, pointing rearward
* **range** [−55°, +20°] about −Z — **DECLARED, verified geometrically**: at the low limit
  the child's forward-most vertex is within 1.0 mm of the breech-face plane and penetrates
  nothing; at the high limit no child vertex lies below the frame's top face
* Confidence is 0.45, not joints-handles' 0.65, because D12 leaves the part's identity
  contested and the pivot had to be re-derived onto the rear spur.

**J2 `frame.trigger`** — parent `frame`, child `frame.trigger` — **confidence 0.75**
* type revolute; **axis** (0,0,1) ± 2°
* **pivot** `u = 0.824 ± 0.030`, `−1.40 ± 0.20 R`, `z = 0` — clay c1 blade top (695, 257),
  bore axis y 228, R 20 px, breech x 692
* **rest** 0° (forward)
* **range** 0° → +14° rearward — **DECLARED, verified geometrically**: at each limit the
  blade's extreme vertex is within 0.5 mm of the guard's inner surface, and 20 sampled
  intermediate poses interpenetrate nothing. The blade is 8×15 px with ~3 px of rear
  clearance; **a travel figure read off the image would be invention.** 14° comes from a
  0.75 R blade in a 0.9 R opening.

### Optional — do not ship without an explicit decision

| id | type | axis / pivot | range | why it is optional | conf |
|---|---|---|---|---|---|
| **J3 `barrel.lattice-collar`** | revolute about the bore | (1,0,0); pivot (u 0.735, 0, 0) | continuous, indexed 360/N | It would make the collar a skeletonised revolver cylinder. **No cylinder gap, crane, ejector rod, chamber mouth or loading gate appears in any of nine views** — but all of those are 1–3 px features here, so their absence is evidence neither for nor against. A fabricated joint is worse than a missing one | 0.35 |
| **J4 `rail.rear-hook`** | revolute | (0,0,1); pivot (u 0.79, +1.35 R) | 0° folded → +90° erect; reference shows erect | The shape is a hook **curving forward**, not a notch. It may be a lanyard hook or a finial and not a sight at all. No hinge line at 19×13 px | 0.30 |
| **J5 `barrel.lug`** | revolute | (0,0,1); pivot (u 0.41, −0.95 R) | ±45° | 11×6 px. Loop (swivels) vs solid tab (does not) is below resolution | 0.25 |
| **J6 `frame.barrel-hinge`** | revolute (break-open) | (0,0,1); pivot (u 0.72, −1.0 R) | 0° → −40° | **DECLARED.** A clay panel shows a bright tab under the barrel at the frame junction, equally consistent with a hinge lug, a latch, or a barrel band. **What the breech implies about loading: nothing defensible.** If an answer is required, break-open is the cheapest reading that gives the object a way to load | 0.20 |

### Sockets (attachment frames, not articulation)

`socket.grip` at the grip's mid-front, aligned to the grip axis ·
`socket.muzzle` on the bore axis at u = 0, +X forward ·
`socket.rail` on the mount block's top face, +Y up.

**Totals: 2 shipped joints, 4 optional, 3 sockets.**

---

## 8. Edit handles

For each: what **must move** and what **must not**. The must-not list *is* the locality
specification.

**H1 `barrel.length`** (mm) — **policy DECLARED: stretch, do not translate.** The
pale-blue tube between the mid-band and the muzzle collar is the only plain cylinder on the
object; all deformation goes there. Scaling the whole barrel would distort the collar's
three rings, the most detailed thing on it.
* *move rigidly* (+Δ along X, no shape change): `muzzle-collar` and all 3 rings, `liner`,
  `bore`, `mid-band`, `lug`, `rail.stud[2]` (the forward one)
* *stretch*: `barrel.tube-fore` (`min.x` fixed, `max.x` +Δ); `barrel.rail` (`min.x` fixed,
  `max.x` +Δ)
* *must not move at all*: `lattice-collar` and all cutouts, `tube-aft`, `frame` and all its
  children, `grip` and all its children, `rail.rear-hook`, `rail.mount-block`,
  `rail.stud[0..1]`
* **trap**: the rail is stretchy *and* carries a fixed rear hook. A whole-bbox invariant on
  `rail` fails by construction — see §9.6.

**H2 `barrel.tube.od`** (mm) — radial **offset**, not scale, so wall thicknesses survive.
* *move*: both tube sections radially; `mid-band`, `lattice-collar`, `muzzle-collar` offset
  radially by the same ΔR; `rail` rises by ΔR/2
* *must not move*: everything from the breech face rearward — `frame`, `port`,
  `hammer-spur`, `trigger`, `trigger-guard`, `grip`, `butt-cap`
* **trap, and it is a real one**: if the frame is authored as a solid wrapping the barrel's
  rear, changing the tube OD legitimately changes the frame and **the test fails by
  construction**. The frame's barrel-facing bore must be its own parameter driven by this
  handle, with the frame's outer envelope independent of it. If it is not, H2 has no
  locality, and the honest report is to say so rather than loosen the tolerance until it
  passes.

**H3 `grip.rake`** (degrees about Z) — **pivot DECLARED at the trigger guard's rear
attach**, (u 0.815, −2.4 R, 0).
* *move*: `grip.body`, `grip.butt-cap`, `toe-stud`
* *must not move*: `frame`, `trigger`, `trigger-guard`, `barrel` and everything above
* **the one genuine topological conflict in the set**: the guard attaches to the frame at
  its front and to the grip at its rear, so one end must tear. Resolution (DECLARED): the
  guard belongs to the frame, and the rake pivot sits exactly at the guard's rear attach,
  making that point the rotation's invariant. **Any other pivot placement makes H3
  non-local however the test is written.**

**H4 `lattice.opening.count`** (integer, 12–20)
* *move*: only the cutout instances inside the collar
* *must not move*: the collar's **own outer envelope — its world bbox must be unchanged** —
  the tube, and everything else
* **This is the best locality test on the object**, because the expected bbox delta is zero
  *even for the part that changed*. If changing the count moves the collar's bbox, the
  collar's outer shell is being rebuilt from the cutouts, which is a bug.

**H5 `rail.length`** — the rail's rear end is its breech end (`min.x`, where the hook
sits); it grows forward.
* *stretch*: `barrel.rail` — `min.x` fixed, `max.x` +Δ
* *move*: `rail.stud[2]` (the forward stud) translates with `max.x`
* *must not move*: `rail.rear-hook` (it is fixed at `min.x`), `rail.mount-block`,
  `rail.stud[0..1]`, and everything not parented to `rail`

**H6 `muzzle.collar.rings`** (integer 2–4) — *move*: ring instances only. *Must not move*:
the collar's outer envelope, the `liner`, `bore`, and everything aft of the collar.

**H7 `hammer.angle`** — J1 doubling as a pose handle. *Move*: `frame.hammer-spur` and its
ribs. *Must not move*: everything else.

**H8 `trigger.angle`** — J2 as a pose handle. *Move*: `frame.trigger`. *Must not move*:
everything else, **including the guard**.

**Total: 8 handles.**

---

## 9. The locality test

Specific enough to implement. The perturbation count that matters is **8 handles × 3 points
(nominal +10 %, range min, range max) = 24 runs.**

**9.1 Procedure**
1. Build at nominal parameters. Traverse the scene graph. For **every named mesh** record:
   its **world-space AABB computed from transformed vertex positions** (never a cached
   geometry bbox); its **world matrix** (16 floats); and a **vertex checksum** (vertex
   count + centroid rounded to 1e-6 + sorted-position hash). Call this `B0`.
2. Perturb **exactly one** handle.
3. **Rebuild from scratch** — a fresh factory call, not a mutation of the existing scene. A
   shared-mutable-state bug only surfaces if the second build is independent.
4. Recompute `B1`.
5. **Invariant set** — for every part the handle declares untouched, assert **all three**:
   `|B1.aabb − B0.aabb| ≤ tol` on all 6 components; `|B1.matrix − B0.matrix| ≤ tol`;
   checksum identical. Bbox alone is not enough — it misses a rotation in place and a
   reshape that preserves extents.
6. **Moving set** — for every part the handle declares as moving, assert it moved by
   **at least 10 × tol** on at least one component; where the motion is predictable (a rigid
   translate of Δ), assert it equals Δ within tol. **A locality test that checks only the
   invariants passes trivially when the handle is a no-op, and that is half its value.**
7. **Topology** — assert the part-name set and the parent-child edge set are unchanged,
   except for the count handles (H4, H6), where only the instanced children may differ in
   number.

**9.2 Perturbation size** — +10 % of nominal, floored at 2 mm for lengths and 5° for
angles, ±1 for counts. Large against tol, small against the feature.

**9.3 Also test at the range ends.** Non-locality appears at extremes, not at nominal
+10 % — a stretched tube finally reaching the frame, a raked grip finally clipping the
guard. Run the same test at each handle's declared min and max.

**9.4 Tolerance — start at 0.** Same parameters, same traversal, deterministic builder: the
correct answer is **bit-identical**, and any nonzero delta is information.

If `tol = 0` fails, relax to **`tol = 1e-4 mm` (1e-7 m)** and record why. That number is set
by *numerical noise*, not by modelling slop:
* float32 positions at ~100 mm scale have an ULP of ~6e-6 mm; accumulated error down a 3–4
  deep transform chain is ~1e-4 mm
* the smallest *meaningful* leak — a handle reaching a part it should not — is at least
  ~0.1 mm, because you cannot move something a useful amount by less
* so 1e-4 mm sits ~4 orders above float noise and ~3 below the smallest real leak

**If the test needs 0.1 mm to pass, the tolerance is not the problem — the builder is not
deterministic, and that is the finding. Do not tune `tol` upward until green.**

**9.5 Report shape** —
`{handle, delta, invariant_violations: [{part, component, magnitude}], moving_set_no_ops: [part], topology_delta}`.
24/24 means 24 perturbations with empty violation lists **and** empty no-op lists.

**9.6 Stretchy parts.** `barrel.rail`, `barrel.tube-fore` and `grip` change extent by design
under some handles. For these the invariant is stated **per bbox face** — e.g. for H1:
`rail.min.x` invariant, `rail.max.x` moves by Δ, `rail.min.y/max.y/min.z/max.z` invariant.
A whole-bbox rule would fail by construction and would train whoever runs it to ignore the
result.

---

## 10. What the reference cannot settle

Union of all six reports' negative findings. **This section is what makes the rest
trustworthy.**

### Absolute scale
1. **The root.** No dimension exists anywhere in the reference; `spec_baseline.json` says
   so in its own text. The chain was improved ~10× (a 1225 px span replaces a 43 px one)
   and a 1.67× error was corrected, but 1.715 m remains an axiom.
2. **pose3's out-of-plane angle φ.** The collar step-edge bow gives 17.3°, the bore ellipse
   gives 32°; reconcilable only through the protruding liner, which is itself contested
   (D11). Costs 4–18 % on absolute *axial* lengths, nothing on ratios.
3. **Per-panel camera yaw.** Not recovered. The sheet is **not orthographic** — tube-only OD
   reads 31 / 36 / 45 / 37 px across four poses, a 45 % spread, while figure heights agree
   to 1.5 %. Ratios within one panel are safe; raw pixels between panels are not.

### Geometry that is occluded in every view
4. **The tube's true upper silhouette.** The rail is tangent along its whole length with no
   background gap in any of four views. Every tube OD in this document reads the top edge
   as the rail's underside — this is D3, the largest single systematic here.
5. **The muzzle collar's OD independent of the rail.** Same cause.
6. **The lattice collar's rear face.** Occluded by hand and hair in pose3, by the frame in
   pose1; never unoccluded. Recovered indirectly, then confirmed by frame-action's direct
   step measurement — the one occlusion that was beaten.
7. **The grip's lateral surface — zero unoccluded pixels in nine views.** Only the butt end
   cap shows, and only 23 % of the grip's height. Consequently **grip width across, front-
   and back-strap curvature, finger grooves, the inlaid panel's extent, and the pin count
   are all unmeasurable.** They were declined rather than invented.
8. **The receiver's underside and true height, its forward face, and any rivet, pin or panel
   line on it** — nothing on the receiver exceeds 3 px in any pose.
9. **The trigger guard's shape.** Present in clay c1 at ~8×16 px; every dimension of it is
   DECLARED.

### Features below the resolution of the reference
10. **Whether the lattice is one row or two staggered rows.** At y 40/50/60 the openings
    merge into 10–12 px blobs; at y 32/69/76 they resolve as pairs. Both readings fit.
    Needs roughly 2× the resolution.
11. **The exact lattice opening count.** 12–20 is the honest range (D8).
12. **Whether the lattice collar rotates, and how the gun loads.** No cylinder gap, crane,
    ejector, chamber mouth or loading gate anywhere in nine views — all 1–3 px features, so
    absence is evidence neither way.
13. **Whether the hammer articulates.** Its orientation is fixed across five views; a hinge
    pin would be 1–2 px.
14. **Trigger travel.** Blade 8×15 px, rear clearance ~3 px.
15. **Loop vs solid tab on the lug** (11×6 px); **whether the rear hook folds** (19×13 px,
    no hinge line).
16. **Lug depth.** pose3 says 1.27 R, pose0 says up to 1.9 R. Position is solid; depth is
    not.
17. **Bore concentricity better than ±10 % of R.** Three methods, three answers, all inside
    their own noise.
18. **Whether the three muzzle rings differ in diameter** (< 1 px), and **anything inside
    the bore** — rifling, liner depth, internal step.
19. **The port's hollowness.** 5 interior pixels against a 2 px rim, in one pose, read
    oppositely by two reports.
20. **Port ribs.** What first read as ribs in pose3 is shaded-edge pixels plus JPEG chroma
    noise. Not ribs. Hammer rib count no better than ±2.
21. **The pose3 bump at crop x 123–129** — 4 px deep, 5 px long. Hanger, shadow or graffiti,
    indistinguishable. Excluded from the axis fit; noted so nobody mistakes it for noise.
22. **Whether the copper/steel boundary is a step.** It reads as paint and the perpendicular
    width is continuous across it, but a 1–2 px step cannot be excluded.
23. **Any lateral (Z) offset of any joint or feature.**

### Materials
24. **Bore liner: bare steel or tube paint?** a\* and b\* agree within 1 unit; only L\*
    differs, and lighting explains that.
25. **Warm tube section: copper or worn brown paint?** Chroma proves it is not brass;
    texture rules out wood; nothing separates the remaining two.
26. **Any PBR parameter** — metalness, roughness. The texture is hand-painted and stylised;
    highlights are 2–6 px.
27. **Whether the two brass tones are two materials or one plus an AO-correlated hue
    shift.** Unlikely at Δh 13–17° with disjoint CIs, but not excluded.
28. **The tan top port's material** — pose0 only, n = 93, indistinguishable from aged brass
    at that n.
29. **True maximum width.** No top view and no orthographic muzzle-on view.
30. **Any per-object graffiti count.** No clean orthographic view of either face exists, so
    every graffiti number is per-view.

### Flatly contradicted by the reference, and worth stating
31. **The brief's grip description** — "dark red-brown wood with brass pins and a lighter
    grey inlaid panel". No pixel supports the wood; the panel is the glove's leather palm
    patch tracking the hand; the gold studs appear on the **non-gun** hand too.
32. **The brief's 0.838 mm/px.** Superseded, ×1.67.
33. **`ref/_gun_views.png`.** A 2.7× bicubic upscale carrying no information the 236-px crop
    does not, with smooth edges that invite false precision.
</content>
</invoke>
