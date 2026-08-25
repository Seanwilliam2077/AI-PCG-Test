# Barrel assembly — measurement report

Subsystem: **barrel** (muzzle collar, muzzle liner + bore, main tube, copper rear section,
mid-band + lug, lattice collar).
Primary view: `ref/gun_pose3.png` (236x118). Cross-checks: `gun_pose0/1/2.png`.
Nothing was modelled. No number below is invented; anything chosen rather than measured is
marked DECLARED. Scripts are in `analysis/work/`. Pixel coordinates are in the named crop's
own frame.

---

## 0. What the reference can and cannot support

### 0.1 Resolution ceiling — confirmed, and `_gun_views.png` is not a way past it

`ref/gun_pose{0..3}.png` template-match into `../jinx-i2t/ref/pose_gun_5view.jpg` at
**correlation 1.0000** at sheet coords (42,150), (642,192), (1650,203), (2421,214).
They are byte-exact copies. Going back to the 3000x1462 sheet buys nothing.

`ref/_gun_views.png` (2548x480) *looks* like a higher-resolution set of the same four views.
It is not. Its radial power spectrum matches `gun_pose3.png` upscaled 2.7x bicubic almost
exactly, and is nothing like the native crop:

| image | energy r<0.25 | 0.25-0.5 | 0.5-0.75 | 0.75-1.2 |
|---|---|---|---|---|
| `_gun_views.png` panel 4 | 0.599 | 0.233 | 0.074 | 0.058 |
| `gun_pose3.png` native | 0.243 | 0.256 | 0.234 | 0.222 |
| `gun_pose3.png` x2.7 cubic | 0.610 | 0.256 | 0.057 | 0.044 |

**Do not measure anything off `_gun_views.png`.** It carries no information the 236-px crop
does not, and its smooth edges invite false precision.

The sheet holds six figures; four carry a readable gun, and those four are exactly the four
crops. There is no fifth gun view to recover.

### 0.2 Which view is metrically usable

A cylinder of constant true diameter must project to a constant apparent diameter under
orthographic projection. Measuring the steel tube's projected diameter along its own length:

| pose | dia. at rear of section | at front | change |
|---|---|---|---|
| pose3 | 35.5 px (x=108) | 36.5 px (x=147) | **+2.8 % over 39 px** |
| pose0 | 39 px (x=38) | 35 px (x=68) | -10 % over 30 px |
| pose1 | strongly oblique, muzzle face very large | | not usable |

pose3 is the only near-orthographic view. Extrapolating +2.8 %/39 px over the 160-px barrel
gives ~12 % depth scaling end to end, so **axial fractions from pose3 carry a systematic
error of about ±0.02 absolute**. I computed the perspective correction explicitly (log map,
k = 7.2e-4 /px): every fraction moved by < 0.017, so uncorrected numbers are reported.

pose2 is used only for the muzzle-face circles and for circularity. pose0/pose1 are used only
as sign-of-agreement cross-checks, never as primary numbers.

---

## 1. Barrel axis in pose3

The tube's lower silhouette over x = 107..144 (excluding the x = 123..129 bump, sect. 6.3)
fits a straight line:

```
bottom edge:  y = 0.04770 x + 71.310     residual rms 0.36 px, n = 32
axis:         y = 0.04770 x + 53.06      2.73 deg below image horizontal
```

Straight to 0.36 px rms over 38 px, so the tube is a true cylinder in this view, not a taper.

**Where the axis is relative to the tube's outer surface — the rail problem.** In *every*
side view the tube's *upper* silhouette is hidden: the brass top rail sits directly on the
tube's top tangent, with no background gap anywhere along its length in pose0, pose1 or
pose3. The tube's top edge can only be read as *the rail's underside*. That is defensible (a
bar resting tangentially on a cylinder has its underside on the cylinder's silhouette) but it
is an assumption, and it is the single largest contributor to the diameter error bars below.
Tested against the mid-band, whose ring overhangs the tube by +3.3 px at the bottom and 1-3
px at the top — consistent, not contradicted, but not tight.

---

## 2. Axial map (pose3)

Warm/cool classification (HSV: warm = H<62 and S>65; cool = 78<=H<=132), fraction of
foreground rows 42..80 that are warm:

| x (px) | warm fraction | reading |
|---|---|---|
| 24..51 | 0.85-1.00 | lattice collar (brass, pierced) |
| 52..56 | 0.49-0.62 | lattice front rim + specular streak on copper (**not** a material change) |
| 57..88 | 0.68-0.90 | copper / warm-brown tube section |
| 89..93 | 0.34-0.58 | mid-band |
| 94..144 | 0.00-0.29 | pale steel-blue tube |
| 145..167 | 0.46-1.00 | muzzle collar (brass) |
| 168..182 | 0.28 -> 0.00 | muzzle liner + bore (cool) |

Barrel span in pose3: lattice rear face **x = 23 ± 4** (occluded by the hand; recovered as
lattice-front minus the measured 29-px sleeve length, cross-checked against pose0's lattice
fraction), muzzle tip **x = 183**. **Total barrel length L = 160 ± 8 px.**

A fully-measured secondary reference: **L_f = lattice front face to muzzle tip = 52 -> 183 =
131 px**, no occlusion anywhere.

### Axial positions, fraction of L (0 = lattice rear face, 1 = muzzle tip)

| feature | pose3 x | fraction of L | cross-check |
|---|---|---|---|
| lattice collar rear face | 23 ± 4 | 0.000 | — |
| lattice front face / copper starts | 52 ± 3 | 0.181 | pose0 0.190 |
| mid-band rear edge | 88 ± 1.5 | 0.406 | — |
| mid-band centre | 91.2 ± 1.5 | 0.426 | — |
| mid-band front edge | 94.5 ± 1.5 | 0.447 | pose0 0.473 |
| lug, axial span | 95..107 | 0.450..0.525 | see 6.4 |
| tube -> muzzle collar step | **145.0 ± 0.5** | 0.763 | pose0 0.881, pose1 0.682 |
| muzzle collar front lip | 167.5 ± 1.5 | 0.903 | — |
| muzzle tip (liner end) | 183 ± 1 | 1.000 | — |

### Section lengths as fraction of L

| section | fraction | pose0 cross-check |
|---|---|---|
| lattice collar | 0.181 ± 0.030 | 0.190 |
| copper tube | 0.225 ± 0.030 | 0.242 (band removed) |
| mid-band | 0.041 ± 0.010 | not separable |
| steel tube | 0.316 ± 0.030 | 0.351 |
| muzzle collar | 0.140 ± 0.020 | 0.119 |
| liner protrusion | 0.097 (pose3 upper bound) | 0.057 |

Copper:steel length ratio is the best-behaved axial number in the set:
**pose3 0.225/0.316 = 0.712; pose0 0.242/0.351 = 0.689.** Two independent views, 3 % apart.

The **tube -> muzzle collar step at x = 145.0 is the sharpest edge on the barrel** (warm
fraction 0.03 at x=144, 0.46 at x=145). It is the best axial datum available and any checking
script should key off it.

---

## 3. Diameters and diameter steps

Method: fit the steel tube's bottom silhouette (sect. 1), then measure every other section's
bottom edge as a signed offset `dy` from that line. For a coaxial stack,
`dy = (D_section - D_tube)/2` in projected px. This sidesteps the occluded top edge for
*steps*, though not for absolute diameters.

| x range | section | dy (px) | radial offset |
|---|---|---|---|
| 67..86 | copper tube | -0.89 .. +0.54, mean -0.25 | **flush with steel tube** |
| 87..94 | mid-band | plateau +3.3 | +3.3 ± 0.7 |
| 95..107 | lug | +3.7 .. +4.97 | +4.9 ± 0.6 |
| 107..146 | steel tube | 0 (reference) | 0 |
| 147..168 | muzzle collar | plateau +2.4 | +2.4 ± 0.6 |
| 169..183 | liner / bore | falling to -18 | tapers in |

Extrapolation error on the fitted line at x = 67 (40 px outside the fit window) is ±0.23 px,
so copper-vs-steel is flush to **±0.5 px on the radius = ±2.7 % of OD**.

### Absolute projected diameters (pose3)

| part | measurement | projected OD (px) | note |
|---|---|---|---|
| main tube (steel) | rail underside 40.5 -> bottom 76.5 at x=110 | **36.3 ± 1.0** | top edge = rail underside (sect. 1) |
| copper rear section | flush with above | **36.3 ± 1.0** | |
| mid-band | tube + 2 x 3.3 | 42.9 ± 1.7 | |
| muzzle collar | tube + 2 x 2.4 | 41.1 ± 1.5 | |
| lattice collar | top 27 ± 1.5, bottom 83 ± 1.5 at x=33..35 | **56 ± 3** | both edges directly visible |
| muzzle liner (steel ring) | y 51..73 at x=176 | 23 ± 1.5 | pose1 24, pose2 26.2 (own scale) |
| bore | max vertical run of V<80 | 17 ± 1.5 | pose1 18, pose2 18.9 (own scale) |

The lattice collar's two independently-measured edges imply a centre at y = 55.0; the axis
extrapolated from the tube gives y = 54.7 at that station. **Agreement to 0.3 px** — the
lattice collar is coaxial with the tube, and the 56-px OD is trustworthy.

### Diameter ratios (these survive the scale chain being wrong)

| ratio | value | source |
|---|---|---|
| lattice collar OD / tube OD | **1.54 ± 0.10** | both from pose3 silhouette |
| mid-band OD / tube OD | **1.18 ± 0.07** | bottom-edge step |
| muzzle collar OD / tube OD | **1.13 ± 0.07** | bottom-edge step; pose1 1.10-1.20, pose0 ~1.00 |
| liner OD / tube OD | **0.63 ± 0.05** | pose3; pose1 0.62 |
| bore / tube OD | **0.47 ± 0.05** | pose3 0.466, pose1 0.46 |
| bore / liner OD | **0.73 ± 0.03** | pose3 0.74, pose1 0.75, pose2 0.72 |

**The muzzle collar is only ~13 % fatter than the tube.** It reads as much fatter because it
is bright polished brass against a matt painted tube; the silhouette says otherwise, in three
views, and pose0 puts the step at zero. This is a place a modeller will over-build.

---

## 4. Muzzle: collar, liner, bore

pose2 is near muzzle-on and settles the cross-section. A radial scan of pose2 outward from
the bore centre (104.2, 89.2) over 36 directions:

- bore edge radius: median **9.50 px**, range 8.25-10.5 excluding one shadow outlier at 120 deg
- liner outer radius: median **13.12 px**, range 11.5-15.5
- fitted bore ellipse: major 18.19, minor 16.14, **minor/major = 0.887** -> the muzzle is
  within ~28 deg of face-on in pose2 and the aperture is **circular**, not oval.

**The tube's cross-section is circular.** pose2's bore ellipse ratio 0.887 and liner ratio
0.894 are equal within noise — which is what a pair of concentric circles viewed obliquely
does. An oval bore in a round tube would show different ratios.

### The muzzle collar is stepped — three rings, two grooves

Mean V along a 10-row band through the bore centre, in two independent poses:

- **pose3** (muzzle at +x): bright 145-146, groove 147-148, bright 149-160, groove 161-163,
  bright 164-166, then the cool liner from 168.
- **pose1** (muzzle at -x): bright 59-61, groove 62-63, bright 64-65, groove 66-67, bright
  70-71, collar body 72-79, groove at 83 where the collar meets the tube.

Both give **3 raised brass rings separated by 2 circumferential grooves**. Ring axial
positions in pose3, as fraction of L: 0.763-0.769, [groove], 0.788-0.856, [groove],
0.881-0.894.

### The liner protrudes

pose3's cool (steel) region at the muzzle spans x 168..183 = 15 px horizontally with a
vertical extent of only 23 px. A flat annular face of OD 23 px at the pose3 obliquity would
project 7-12 px wide, not 15. In pose1 the object is only 24 px tall at x=38..44 and jumps to
44+ px at x>=46; in pose0 the same 6-px step appears. So the pale steel liner **stands
forward of the collar's front face**, by 0.057 L (pose1 and pose0 agree exactly) to 0.097 L
(pose3 upper bound).

### Bore concentricity — the reference cannot settle it

Three attempts:

1. pose3: bore centroid y = 63.2-63.7 at x=176; axis extrapolated to that station gives
   y = 61.5. Offset **1.7-2.2 px low**, on a tube radius of 18.15 -> 10 % of radius. The axis
   extrapolation itself carries ±1 px there.
2. pose2, bore centre vs liner centre by contour ellipse fit: offset **1.55 px** on a 25.6-px
   liner = 6 %.
3. pose2, collar outer edge fitted as `r = R + dx cos + dy sin` from the bore centre over 20
   clean directions: R = 21.04, offset 3.06 px = **14.6 % of R**, bootstrap 95 % CI
   [2.23, 4.21] px, residual rms 0.94 px. But the muzzle disc is an *ellipse* and only its
   right/top/bottom are unoccluded, so a circle+offset model absorbs the ellipticity as a
   spurious offset. Upper bound, not a detection.

**Verdict: the bore is concentric with the tube to within the resolution of the reference,
about ±10 % of the tube radius (±1.8 px). There is a weak, repeatable hint of the bore
sitting low in pose3 and left in pose2, but it does not clear the noise. A concentric bore
must be DECLARED, not claimed as measured.** Anyone who models a deliberately offset bore is
inventing it; anyone who models a perfectly concentric one is making a legitimate choice they
should mark as such.

---

## 5. Lattice collar

The signature feature. Best view is pose3, x 24..51.

### Cutout detection

Thresholding V inside x 26..50, y 28..84, connected components with area >= 3. At V<55 and
V<62 the same seven large, well-formed openings appear, at image y:

```
32.7   40.2   49.8   60.0   69.2   76.1   82.2
```

with vertical gaps 7.5, 9.7, 10.1, 9.3, 7.2, 5.7 px — **wide in the middle, compressed at top
and bottom.** That is the projection signature of a row of holes evenly spaced *around* a
cylinder, not of a row spaced *along* the axis.

### Solving for the count

Model `y_k = y_c - R cos(theta_0 + k * 2pi/N)`, fitted over y_c, R, theta_0 for each integer N:

| N | rms (px) | implied R | implied OD |
|---|---|---|---|
| 14 | 0.957 | 24.50 | 49.0 |
| 16 | 0.531 | 26.50 | 53.0 |
| 17 | 0.412 | 27.50 | 55.0 |
| **18** | **0.327** | **28.75** | **57.5** |
| 19 | 0.304 | 30.00 | 60.0 |
| 20 | 0.305 | 31.25 | 62.5 |
| 24 | 0.451 | 36.50 | 73.0 |

The fit alone is degenerate — N and R trade off along a shallow valley. It is broken by the
**independently measured** collar OD of 56 ± 3 px (sect. 3, two directly visible silhouette
edges whose midpoint lands 0.3 px from the tube axis). That selects **N = 18**, with 16 and
20 inside the error bar and 14 and 24 excluded.

Independent support: the projected pitch nearest the axis (least distorted) is 10.2 px; with
R = 28 that is 20.9 deg per hole, N = 17.2.

### Other lattice numbers

- **Angular pitch: 20.0 ± 2.5 deg** (360/18).
- **Openings resolved in the near-side profile: 7.** With N = 18 that is 140 deg of arc,
  consistent with what a cylinder shows before the holes go grazing.
- **Hole axial length: 11 ± 1.5 px = 0.069 L** (components measure w = 10-12 px).
- **Open fraction around the circumference: 0.55-0.70** (hole height 7 px against a 10.2-px
  pitch at the axis; merging inflates the upper end).
- **Sleeve axial length: 28 ± 4 px = 0.181 L.** Cutouts occupy x 29..46, leaving solid rims of
  roughly 5 px at each end.
- Hole x-centres drift from 37 (top) to 34 (middle) to 30.5 (bottom) — the ring lean, i.e. the
  near side of the collar bowing toward the breech, consistent with the muzzle-collar step
  edge in sect. 7.

### One row or two?

At y = 40, 50, 60 the openings detect as single wide blobs (w = 10-12 px). At y = 32, 69, 76
they detect as *pairs* at different x (e.g. x = 31.6 and 38.3 at y = 69.4). Equally consistent
with (a) one row of axially long lozenges crossed by an occasional strut, or (b) two staggered
rows. **236 px cannot separate these.** I report one row; a second staggered row is not
excluded, and any constraint should tolerate it.

---

## 6. Bands, steps, lug — the count inventory

### 6.1 Distinct circumferential brass bands on the barrel

| # | band | fraction of L | confidence |
|---|---|---|---|
| 1 | lattice collar rear rim | 0.00-0.03 | 0.35 — occluded by hand/hair in every view |
| 2 | lattice sleeve (pierced) | 0.03-0.15 | 0.90 |
| 3 | lattice collar front rim | 0.15-0.18 | 0.80 |
| 4 | mid-band | 0.406-0.447 | 0.90 |
| 5 | muzzle collar ring, rear | 0.763-0.769 | 0.70 |
| 6 | muzzle collar ring, middle | 0.788-0.856 | 0.80 |
| 7 | muzzle collar ring, front | 0.881-0.894 | 0.80 |

**Confident count: 5 bands.** **Most likely: 6-7.** The muzzle collar's 3-ring structure is
confirmed in two independent poses; the lattice collar's rear rim is never unoccluded.

### 6.2 Diameter steps along the barrel exterior

Forward from the lattice: lattice collar (large) -> **down** to tube -> mid-band **up** ->
**down** to tube -> muzzle collar **up** -> **down** to liner -> bore.
**5 exterior diameter steps**, plus the bore aperture.

Critically, there is **no step at the copper/steel colour boundary**. That boundary is
paint/material, not geometry (sect. 3, flush to ±2.7 % of OD).

### 6.3 The x = 123..129 bump

The bottom silhouette drops +3.7 px for six columns at x = 124..127 and returns to zero. It is
4 px deep and 5 px long. Hanger, shadow or graffiti cluster — indistinguishable. **Below the
resolution of the reference.** Noted so nobody mistakes it for noise; it was excluded from the
axis fit window.

### 6.4 The lug below the mid-band

Present in all four views, but the poses disagree about how far it hangs:

| pose | protrusion below the tube silhouette | scaled to pose3 |
|---|---|---|
| pose3 | 4.9 ± 0.6 px (radius 1.27 x tube radius) | 4.9 px |
| pose1 | ~6-9 px on a 140-px barrel | 7-10 px |
| pose0 | ~7-11 px on a 105-px barrel | 11-17 px |

Its axial position is solid (0.45-0.53 L, immediately forward of the mid-band in pose3, at or
just behind the band in pose0). **Its depth is not.** It is 8 x 5 px in the best view.

---

## 7. View geometry — an unresolved conflict, stated rather than papered over

Two ways of getting pose3's out-of-plane axis angle phi disagree:

1. The **tube -> muzzle collar step edge** is a circle around the tube. Traced row by row it
   runs x = 152 at y = 43, x = 145 at y = 58..73, x = 149 at y = 79 — a clean elliptical arc
   bowing 5.5 px toward the breech at mid-height. With tube radius 18.5,
   `sin phi = 5.5/18.5 = 0.30`, **phi = 17.3 deg**.
2. The **bore aperture** at V<80 measures 17 px tall by 9 px wide, ratio 0.53, **phi = 32
   deg**; the liner ring measures 23 x 15, ratio 0.65, **phi = 41 deg**.

Reconcilable only if the liner protrudes (sect. 4) so its horizontal extent is protrusion plus
half-ellipse, not half-ellipse alone — which pose0 and pose1 independently support. But phi is
not pinned, and it is what converts projected axial px into true axial px. Since
`cos(17 deg) = 0.956` and `cos(32 deg) = 0.848`, **absolute axial lengths in pose3 could be
under-read by 4 % to 15 %.** All *ratios* of axial lengths are unaffected — another reason the
constraints below are written as ratios.

---

## 8. The scale chain — it is wrong by about 1.6x

The stated chain: `hand-l` width = 0.044 m in `../jinx-i2t/baseline/spec_baseline.json`; four
curled fingers span ~52.5 px in pose1; therefore 0.838 mm/px.

I reproduce the pixel half. My independent measurement of the four exposed fingertips of the
gripping hand (sheet y 255..400, x 780..900 at 7x) puts the finger bands at sheet y 284-297,
309-320, 322-332, 333-341: **57 px** from the top of the index to the bottom of the pinky, or
**43 px** for four fingers packed at the 10.7-px pitch of the three adjacent ones. 52.5 px
sits inside that range. The pixel measurement is fine.

The metre half is not.

**8.1 The spec says so itself.** `coordinateFrame.scaleReference` reads: *"1.72 m total
height, hair-crest tip to sole. DECLARED, not measured -- the reference sheet carries no
dimension. Every other length is a measured ratio against it."* So 0.044 m is a ratio measured
off this same sheet against a declared stature. It is checkable against the sheet.

**8.2 It fails that check.** Figure pixel height, hair-crest tip to sole, measured in six
windows on the sheet: 1287, 1276, 1240, 1220, 1287, 1264 px. The spread is hair-crest
foreshortening view to view; the largest values (side-on views, crest least foreshortened) are
the best estimate. Take **1278 ± 30 px** for 1.715 m.

- measured on the sheet: four-finger span / stature = 52.5 / 1278 = **0.0411**
- the spec asserts: 0.044 / 1.715 = **0.0257**
- human anthropometry, hand breadth / stature = 0.078 / 1.72 = **0.045**

The sheet's own geometry agrees with human proportion to 9 %. The spec's number is **63 % of
what the sheet shows**. The spec's `hand-l` is internally consistent in *shape*
(0.092 / 0.044 = 2.09, against a real hand-length/breadth of ~2.26) but is uniformly about
half adult size for its own declared 1.72 m figure: hand length / stature = 0.092/1.715 =
0.054 against a human 0.105.

**8.3 Consequence.** `mm/px = 1715/1278 = 1.342`, against the chain's 0.838.
**Every barrel dimension derived through `hand-l` is too small by a factor of 1.60.**

That the old chain reproduces the brief's quoted results is a good sign my pixel work matches
theirs: 36.3 px x 0.838 = 30.4 mm, and the brief says "near 30 mm". The pixels agree. The
metres do not.

**8.4 Error budget on the corrected scale.**

| source | effect |
|---|---|
| figure pixel height 1220-1290 px | ±3 % |
| declared 1.72 m stature | unbounded — a declaration, not a measurement |
| depth between body plane and outstretched gun | ±8 % (bounded by 8.5) |

**mm/px = 1.34 ± 0.15**, *conditional on the declared 1.72 m*.

**8.5 Is the sheet orthographic?** The tube's projected diameter never foreshortens with the
axis angle, so under orthographic projection it must be identical in every view: measured
36.3 px (pose3), ~39 px (pose1), 35-39 px (pose0) — **agreement within ±8 %** despite the gun
being at very different depths. With sect. 0.2's within-pose result, the sheet is
near-orthographic and one mm/px applies across it, to about ±8 %.

**8.6 A better anchor than either.** The strongest scale statement available needs no metres:
**barrel length / four-finger hand breadth = 160 / 52.5 = 3.05 ± 0.25**, both measured in
pixels on the same sheet. Any check of a built model can measure both and compare. It is
immune to the 1.72 m declaration collapsing.

### Barrel dimensions under both scales

| part | px | at 0.838 mm/px (old) | at 1.34 mm/px (corrected) |
|---|---|---|---|
| barrel length L | 160 | 134 mm | **215 mm** |
| tube OD | 36.3 | 30.4 mm | **48.7 mm** |
| lattice collar OD | 56 | 46.9 mm | **75 mm** |
| mid-band OD | 42.9 | 36.0 mm | **57.5 mm** |
| muzzle collar OD | 41.1 | 34.4 mm | **55 mm** |
| liner OD | 23 | 19.3 mm | **30.8 mm** |
| bore | 17 | 14.2 mm | **22.8 mm** |

---

## 9. Proposed constraints

All checkable by script against a built scene. "AABB" = per-mesh world-space axis-aligned
bounding box with the barrel axis on +X. "Silhouette" = orthographic render along -Z with the
barrel axis on +X. Ratios preferred throughout; only three absolutes appear, all DECLARED.

### Counts

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.lattice.cutout.count` | count | **18**, accept 16-20 | count distinct hole meshes / boolean cuts in the lattice component; or cast 360 rays radially outward from the axis at the lattice's axial centre and count contiguous miss-arcs | pose3 x26..50: 7 openings resolved at y 32.7/40.2/49.8/60.0/69.2/76.1/82.2; N-vs-R fit (sect. 5) intersected with the independently measured collar OD 56 ± 3 px | 0.55 |
| `barrel.muzzle.ring.count` | count | **3**, accept 2-4 | count local maxima of the radial profile r(x) over the muzzle collar's axial span, sampled from the silhouette | pose3 V-scan bright at x145-146/149-160/164-166, grooves 147-148/161-163; pose1 independently bright at 59-61/64-65/70-71, grooves 62-63/66-67 | 0.75 |
| `barrel.band.count` | count | **>= 5**, expected 6-7 | count meshes in the barrel subtree whose AABB X-extent < 0.08 L and whose max radius exceeds the local tube radius by > 2 % | inventory, sect. 6.1 | 0.65 |
| `barrel.step.count` | count | **5** exterior diameter steps | sample max radius r(x) along the axis from the silhouette at 200 stations; count sign changes of dr/dx exceeding 2 % of tube radius | sect. 6.2, from the de-trended bottom silhouette | 0.70 |
| `barrel.tube.step.none_at_paint_line` | count | **0** steps between 0.20 L and 0.40 L | same r(x) sampling; require max abs(r(x)-r_tube) < 0.03 r_tube over that span | copper section bottom edge sits -0.25 px (mean) from the steel tube's fitted line over x 67..86; extrapolation error ±0.23 px | 0.85 |

### Ratios — diameters

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.lattice.od_over_tube_od` | ratio | **1.54 ± 0.10** | (lattice AABB max(Y,Z) extent) / (tube AABB max(Y,Z) extent) | pose3 lattice top y=27±1.5, bottom y=83±1.5 at x=33..35 -> 56±3 px; tube 36.3±1.0 px; lattice edge midpoint y=55.0 vs axis 54.7 | 0.70 |
| `barrel.midband.od_over_tube_od` | ratio | **1.18 ± 0.07** | as above for the mid-band mesh | bottom-edge step dy=+3.3±0.7 px on tube radius 18.15 | 0.70 |
| `barrel.muzzlecollar.od_over_tube_od` | ratio | **1.13 ± 0.07** | as above | dy=+2.4±0.6 px (pose3); pose1 1.10-1.20; pose0 ~1.00 | 0.60 |
| `barrel.liner.od_over_tube_od` | ratio | **0.63 ± 0.05** | as above for the protruding liner mesh | pose3 23/36.3; pose1 24/39 | 0.65 |
| `barrel.bore.d_over_tube_od` | ratio | **0.47 ± 0.05** | ray-fan down the axis from outside; bore diameter = 2 x the largest radius at which the fan still misses geometry at the muzzle face | pose3 17/36.3=0.466; pose1 18/39=0.46 | 0.70 |
| `barrel.bore.d_over_liner_od` | ratio | **0.73 ± 0.04** | as above / liner AABB | pose3 0.74, pose1 0.75, pose2 0.72 — three views | **0.85** |
| `barrel.tube.circular` | relation | tube AABB Y-extent == Z-extent within 4 % | compare AABB Y and Z extents of the tube mesh | pose2 bore ellipse minor/major 0.887, liner 0.894 — equal within noise, i.e. concentric circles viewed obliquely | 0.75 |
| `barrel.tube.constant_od` | relation | max radius varies < 3 % over 0.20 L .. 0.75 L | sample r(x) from the silhouette | pose3 bottom silhouette straight to 0.36 px rms over 38 px; projected diameter 35.5 -> 36.5 px, and that +2.8 % is perspective, not taper | 0.80 |

### Ratios — axial

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.copper_over_steel.length` | ratio | **0.71 ± 0.08** | (X-extent of warm-material tube section) / (X-extent of pale tube section), from material assignment or the two meshes' AABBs | pose3 0.225/0.316 = 0.712; pose0 0.242/0.351 = 0.689 — two views, 3 % apart | **0.80** |
| `barrel.muzzlecollar.step.axial_pos` | ratio | **0.763 ± 0.030** of L from the lattice rear face | find the largest positive dr/dx in the forward half of r(x); its x divided by L | pose3 x=145.0±0.5, sharpest edge on the barrel (warm frac 0.03 -> 0.46 in one column) | **0.85** |
| `barrel.midband.axial_pos` | ratio | **0.426 ± 0.040** of L | mid-band mesh AABB X-centre / L | pose3 x=91.2±1.5; pose0 front-edge crossing 0.473 vs pose3 0.447 | 0.70 |
| `barrel.lattice.length_over_L` | ratio | **0.181 ± 0.030** | lattice mesh AABB X-extent / L | pose3 28±4 px / 160 px; pose0 0.190 | 0.70 |
| `barrel.muzzlecollar.length_over_L` | ratio | **0.140 ± 0.025** | collar AABB X-extent / L | pose3 22.5/160; pose0 0.119 | 0.60 |
| `barrel.lattice.cutout.length_over_L` | ratio | **0.069 ± 0.012** | mean X-extent of the cutout volumes / L | pose3 components w = 10-12 px | 0.55 |
| `barrel.liner.protrudes` | relation | liner AABB X-max > muzzle-collar AABB X-max, by 0.06 ± 0.03 L | compare the two AABBs | pose1 and pose0 both show a 6-px step to a 24-px-tall section ahead of a 44-px collar; pose3 cool region 15 px wide against a 23-px face | 0.70 |
| `barrel.lug.axial_pos` | ratio | **0.49 ± 0.05** of L | lug mesh AABB X-centre / L | pose3 x 95..107; forward of the band in pose3, at/behind it in pose0 | 0.55 |
| `barrel.lug.radial_reach` | ratio | 1.2-1.8 x tube radius | lug AABB max radial extent / tube radius | pose3 1.27; pose1 ~1.4-1.5; pose0 ~1.6-1.9 — the poses disagree | **0.30** |

### Angles

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.lattice.cutout.pitch` | angle | **20.0 ± 2.5 deg** | angle between adjacent cutout centroids about the barrel axis | 360/18; direct: projected pitch nearest the axis 10.2 px on R=28 px gives 20.9 deg | 0.55 |
| `barrel.lattice.open_fraction` | ratio | 0.55-0.70 | at the lattice's axial mid-station, fraction of 360 radial rays that miss geometry | pose3 hole height 7 px against a 10.2-px pitch at the axis; merging inflates the top of the range | 0.40 |

### Relations

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.bore.concentric` | relation | bore axis within **0.10 x tube radius** of the tube axis | fit the bore cylinder's axis; compare to the tube's AABB centre line | DECLARED as concentric. Three measurements (sect. 4) give offsets of 6 %, 10 % and 14.6 % of radius, all within their own noise; the reference cannot resolve better than ±10 % | 0.50 |
| `barrel.lattice.coaxial` | relation | lattice axis within 0.03 x tube radius of the tube axis | compare AABB centre lines | pose3 lattice silhouette midpoint y=55.0 vs axis extrapolated 54.7 — 0.3 px on an 18-px radius | **0.85** |
| `barrel.rail.tangent` | relation | rail's minimum radius <= tube radius x 1.02 | min radial distance from the axis to the rail mesh | in pose0, pose1 and pose3 no background pixel ever appears between the rail's underside and the tube; a standoff would show one | 0.65 |
| `barrel.midband.is_paint_boundary` | relation | the copper/steel material boundary lies inside the mid-band's X-extent | compare the material-assignment X-boundary with the mid-band's AABB | pose3 warm fraction falls 0.90 -> 0.08 across x 88..96, exactly the band's span | 0.75 |

### Absolutes — all DECLARED

| id | kind | value | check | evidence | conf |
|---|---|---|---|---|---|
| `barrel.scale.mm_per_px` | dimension | **1.34 mm/px ± 0.15** on the pose3 crop | n/a — this is the conversion, not a model property | DECLARED, conditional on the spec's declared 1.72 m stature. Derived as 1715 mm / 1278 px figure height. **Supersedes 0.838 mm/px, which is 1.60x too small** (sect. 8) | 0.55 |
| `barrel.tube.od` | dimension | **48.7 mm ± 6 mm** | tube mesh AABB max(Y,Z) extent | 36.3 ± 1.0 px x the DECLARED scale above. Under the old chain, 30.4 mm | 0.45 |
| `barrel.length` | dimension | **215 mm ± 25 mm** | barrel subtree AABB X-extent | 160 ± 8 px x the DECLARED scale | 0.45 |
| `barrel.length_over_hand_breadth` | ratio | **3.05 ± 0.25** | barrel AABB X-extent / hand mesh AABB breadth across the four fingers | 160 px / 52.5 px, both on the same sheet. Prefer this to the two rows above — it survives the 1.72 m declaration being wrong | **0.75** |

---

## 10. What I could not measure, and why

| item | why |
|---|---|
| Lattice collar rear face position | Occluded by the hand and hair in pose3, by the frame/hammer in pose1; never unoccluded in any of the four views. L's rear end is inferred, not measured, so L carries ±8 px. |
| Lattice: one row of holes or two staggered rows | At y=40/50/60 the openings merge into single 10-12 px blobs; at y=32/69/76 they resolve as pairs at different x. Both readings fit. Needs > ~2x the resolution. |
| Tube's true upper silhouette | The top rail rests on the tube's top tangent in all four views with no background gap anywhere. Every tube OD here reads the top edge as the rail's underside. |
| Muzzle collar's true OD independent of the rail | Same reason. The 1.13 ratio comes from the bottom-edge step alone, and pose0 puts that step at zero. |
| Lug depth | 8 x 5 px at best. pose3 says it reaches 1.27 x tube radius, pose0 says up to 1.9. Position is solid, depth is not. |
| Bore concentricity better than ±10 % of tube radius | Sect. 4. Three methods, three answers, all inside their own noise. |
| Out-of-plane view angle phi for pose3 | Sect. 7. The collar step-edge bow gives 17 deg, the bore ellipse gives 32 deg. Reconcilable only via the protruding liner, which is supported but not measured to a length. Costs 4-15 % on absolute axial lengths; costs nothing on ratios. |
| The x=123..129 bump | 4 px deep, 5 px long. Hanger, shadow or graffiti — indistinguishable. |
| Whether the muzzle collar's 3 rings differ in diameter | The grooves are resolved; ring-to-ring radius differences are under 1 px. |
| Bore interior (rifling, liner depth, internal step) | The bore is 17 px across and its interior is 3-4 V-levels above black. Nothing inside is resolvable. |
| Any absolute dimension in millimetres | The sheet carries no dimension; the spec says so explicitly. Every millimetre in sect. 9 is conditional on a declared stature. |
