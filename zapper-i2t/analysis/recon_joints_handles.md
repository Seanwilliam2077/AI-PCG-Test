# Zapper — joints, edit handles, locality test

Subsystem: `joints-handles`. Nothing here is a spec and nothing was modelled.
Every number below carries its method and the pixels it came from, or the word DECLARED.

---

## 0. Sources actually used

| tag | file | note |
|---|---|---|
| `p0` `p1` `p2` `p3` | `ref/gun_pose{0..3}.png` | the supplied crops |
| `sheet` | `../jinx-i2t/ref/pose_gun_5view.jpg` 3000x1462 | crops located in it by `cv2.matchTemplate`, score 1.000: p0@(42,150) p1@(642,192) p2@(1650,203) p3@(2421,214). A crop pixel *is* a sheet pixel, so `sheet_x = crop_x + origin_x`. Used to see past the crop edges — p3's frame, grip and hammer are all outside the crop. |
| `clay` | `../jinx-i2t/ref/pose_gun_clay_6view.jpg` 3000x1462 | **read-only, not named in the brief.** The untextured turnaround of the same asset. It resolves no more pixels than the colour sheet (the gun is ~190 px in both) but it removes the graffiti and the brass/steel colour breaks, which is what made the rear of the frame readable at all. Poses referred to as `c0..c4`, left to right. |

Working images under `analysis/work/` (gridded zooms, silhouette masks). Nothing under `ref/` was touched.

**Resolution ceiling.** The gun is 160-236 px long in every source, colour and clay alike. A trigger blade is ~8x15 px; a hinge pin would be 1-2 px. Anything I claim below about a *pivot pin*, a *latch*, or a *gap* is inference from the object's type, not from the reference, and is marked so.

---

## 1. Frame of reference (DECLARED)

- Origin **O** = centre of the **breech face**: the point on the bore axis at the rear end of the barrel bore.
- **+X** forward along the bore, toward the muzzle.
- **+Y** up, toward the top rail.
- **+Z** = X x Y, i.e. to the gun's **left**. Gun's right is -Z.
- `L` = barrel length, muzzle face to breech face, along X.
- `R` = half the main-tube outside diameter.

Positions are given as multiples of `L` and `R` in preference to mm. A ratio survives the scale chain being wrong; an absolute does not. Provisional mm are shown in brackets using the brief's `L~120`, `R~15`, and are the weakest numbers on the page.

**Everything is DECLARED to lie in the sagittal plane, z = 0.** I have no view that resolves lateral offsets: every usable pose is near-abeam or near-axial. `c2` weakly hints the hammer may be offset to one side. If it is, that is a 1-2 mm error I cannot detect and did not try to.

---

## 2. Axial landmarks

Measured in `p3` (the brief's cleanest side view) and converted to sheet x. Bore axis in `p3` runs from sheet (2449,270) to (2597,276) — slope 0.04, effectively horizontal, which is why `p3` is the metric view.

| landmark | sheet x | x/L from breech | method |
|---|---|---|---|
| muzzle face | 2602 | +1.00 | rightmost brass, silhouette mask ends at p3 x=183 |
| muzzle collar front rim | 2587-2593 | +0.92 | step edge, p3 x 166-172 |
| muzzle collar rear step | 2568 | +0.79 | p3 x 147 |
| rail forward stud | 2584 | +0.89 | blue dot p3 (161-166, 41-46) |
| red rail mount block | 2505-2524 | +0.41...+0.53 | p3 x 84-103 |
| brass mid-band | 2509-2521 | +0.44...+0.51 | p3 x 88-100 |
| hanging lug (under barrel) | 2518-2529 | +0.49...+0.56 | p3 x 97-108, y 77-83 |
| lattice collar | 2437-2463 | 0.00...+0.16 | p3 x 16-42 |
| **breech face** (collar rear) | **2437** | **0.00** | +/-5 px; the collar may overhang the true bore end |
| rail rear hook base | 2444 | +0.04 | sheet (2444,244) |
| hammer base | 2428 | -0.055 | sheet, `g_p3_ham.png` |
| trigger blade | — | -0.02 | clay c1 x 695 vs breech 692 |

`L = 2602 - 2437 = 165 px` in `p3`. Tube OD at p3 x=120 = 37 px. **L/D_tube = 4.46**, and because L is foreshortened while D is not, 4.46 is a **lower bound**.

---

## 3. The top-rear feature is a hammer, not a port

The brief calls it "a small cylindrical port on top toward the rear". I think that is wrong, and the evidence is an aspect-ratio argument that needs no absolute scale.

Apparent length : width of the piece, measured in five independent views:

| view | camera | measured px | aspect |
|---|---|---|---|
| clay `c1` | abeam | 28 x 13 | 2.15 |
| `p1` | abeam | 29 x 11 | 2.64 |
| clay `c2` | near muzzle-on | ~50 x 20 | 2.5 |
| `p0` | from behind | 24 x 14 | 1.71 |
| `p3` (sheet) | from behind | ~14 x 16 | 0.88 |

A cylinder appears **shortest when viewed along its own axis**. It is short from behind and long from abeam and from the front, so its axis points **rearward**. In the abeam views it also rises: `c1` (713,216)->(739,205) = 23 deg above the bore; `p1` (189,67)->(212,49) = 38 deg. So the axis is **rearward and up, ~30 deg +/- 8 deg above the bore axis**.

That also explains `p0`, where I first read a "vertical open-mouthed stub": the dark ellipse at p0 (140-150, 53-58) is the piece's rear **end face in shadow**, seen nearly on-axis — not a bore.

In `p1` at px (175-190, 55-75) there is **background sky between the piece and the frame**. It is cantilevered, on a neck ~8 px across against a body ~13 px across (clay c1, neck base ~(703,218)). Ribbed: 5-6 transverse rib lines at ~4 px pitch in clay c1, 5 in p1.

A ribbed thumb-piece on a neck, standing clear of the frame, raked rearward-up off the top rear: that is a **hammer or cocking piece**. Confidence 0.65 that it articulates; 0.9 that the part is there and shaped as described. The live alternative is a **screwed-in canister** (Hextech cell), which would swap J1's revolute for a screw joint along the same axis. I could not find a pivot pin — at 1-2 px, I could not have.

**There is no separate top port.** If one exists it is below resolution.

---

## 4. Joints

Ranges are given as *geometric* rules wherever possible — "drive to the limit and assert this contact" — because a degrees number I invent is unfalsifiable, while a contact condition is checkable and *derives* the degrees.

### J1 `frame.hammer` — SHIP, confidence 0.65
- **type** revolute · **axis** (0,0,1) +/- 3 deg (DECLARED: a piece in the sagittal plane can only swing about Z)
- **pivot** (-0.07 L, +0.78 R, 0) +/- (0.04 L, 0.20 R) -> [-8.4, +11.7, 0] mm
  - p3 sheet: base (2428,253), breech 2437, axis y 269, R 18.5 px -> (-0.055 L, +0.86 R)
  - clay c1: neck base (703,218), breech 692, axis y 231, R 20 px -> (-0.086 L, +0.65 R)
- **rest** = the reference pose: piece axis at 150 deg +/- 8 deg from +X in the XY plane (rearward-up 30 deg above bore)
- **range** [-55 deg, +20 deg] about -Z, DECLARED, *verified geometrically*: at the low limit the child's forward-most vertex is within 1.0 mm of the breech-face plane and penetrates nothing; at the high limit no child vertex lies below the frame's top bbox face.
- **for** cocking and dry-firing the prop; the one animation this object obviously owes an audience.

### J2 `frame.trigger` — SHIP, confidence 0.85
- **type** revolute · **axis** (0,0,1) +/- 2 deg
- **pivot** (-0.02 L, -1.40 R, 0) +/- (0.04 L, 0.20 R) -> [-2.4, -21, 0] mm
  - clay c1: blade top (695,257), bore axis y 228 at that x, R 20 px, breech x 692
- **range** 0 deg (forward) to +14 deg rearward, DECLARED, *verified geometrically*: at each limit the blade's extreme vertex is within 0.5 mm of the guard's inner surface, and 20 sampled intermediate poses interpenetrate nothing.
- **for** the trigger pull.
- The blade is 8x15 px and its rear clearance inside the guard is ~3 px. **A travel figure read off the reference would be invention.** 14 deg comes from a 0.75 R blade in a 0.9 R opening (clay c1 guard inner height 18 px), not from the image.

### J3 `barrel.lattice-collar` — OPTIONAL, confidence 0.35
- **type** revolute about the bore · **axis** (1,0,0) +/- 0.5 deg · **pivot** (+0.08 L, 0, 0)
- **range** continuous, indexed 360/N with N = the lattice repeat (section 5)
- **for** the collar being a skeletonised revolver cylinder rather than a fixed pierced sleeve.
- **Do not ship this without a decision.** I found **no** cylinder gap, crane, ejector rod, chamber mouth, or loading gate. All of those are 1-3 px features here, so their absence is not evidence — but neither is their absence evidence *for* the joint. A fabricated joint is worse than a missing one.

### J4 `rail.rear-sight` — OPTIONAL, confidence 0.30
- revolute, axis (0,0,1), pivot (+0.04 L, +1.35 R, 0) — p3 sheet hook base (2444,244), axis 269, R 18.5
- range 0 deg (folded forward along the rail) to +90 deg (erect); reference shows erect
- The shape is a **hook curving forward**, not a notch. It may be a lanyard hook or a finial and not a sight at all. No hinge line at 19x13 px.

### J5 `barrel.lanyard-lug` — OPTIONAL, confidence 0.25
- revolute, axis (0,0,1), pivot (+0.52 L, -0.95 R, 0) — p3 lug (97-108, 77-83), axis y 59, R 19
- range +/-45 deg
- 11x6 px. Whether it is a closed loop (swivels) or a solid tab (does not) is below resolution.

### J6 `frame.barrel-hinge` (break-open) — OPTIONAL, confidence 0.20, DECLARED
- revolute, axis (0,0,1), pivot (+0.10 L, -1.0 R, 0), range 0 deg to -40 deg
- clay c1 shows a small bright tab under the barrel at the frame junction, ~(690-700, 236-243). That is *consistent with* a hinge lug or a latch, and equally consistent with a barrel band.
- **What the breech actually implies about loading: nothing I can defend.** No hinge, latch, gate, ejector, or magazine well is resolvable. If the answer must be chosen, break-open is the cheapest reading that gives the object a way to load.

### Sockets (Nova3D `actionProfile.sockets`, not articulation)
`socket.grip` at the grip's mid-front, aligned to the grip axis · `socket.muzzle` on the bore axis at x = +1.00 L, +X forward · `socket.rail` on the red mount block's top face, +Y up.

---

## 5. Counts (cheap to check, so worth stating)

**`lattice.repeat` = 9 X-crossings (and 9 lozenge holes), range 8-12, confidence 0.4.**
Method — worth spelling out because it is the only count I got non-visually. In `p3` (`analysis/work/g_p3_lat.png`) the dark cavity centres in the near-face column at x 29-42 are at y = 34.5, 41.5, 50.5, 59.5, 67.5, 76.5, alternating with mid-brown diamonds at the half-pitch. The collar spans y 28-84, so y0 = 56, R = 26-28. Fitting `y = y0 + R cos(theta)`:

| R | theta per alternating feature | N features | N X-crossings |
|---|---|---|---|
| 24 | 21.9 deg | 16.4 | 8.2 |
| 26 | 21.6 deg | 16.7 | 8.4 |
| 28 | 18.5 deg | 19.5 | 9.7 |
| 30 | 17.1 deg | 21.0 | 10.5 |

The per-step angles are consistent to +/-2 deg across the whole visible arc (deltas 19.0, 19.9, 18.5, 17.1, 22.8 at R=28), which is what a single evenly-spaced circumferential row looks like. `p0` (`g_p0_lat.png`) confirms the *structure*: an unambiguous **X** at (102-110, 78-84) with a dark lozenge above and below, so the alternating dark/brown features are the two halves of one repeat. **The exact integer is not settleable at this resolution.**

Others: **`muzzle.steps` = 3** (p3 x 147-153 / 153-166 / 166-172 with y-extents 34 / 37 / 40 px; p2 shows 3 concentric rings) · **`rail.studs` = 3** (two blue dots inside the red block at p3 x~90 and x~98, y 37-40; one at p3 (161-166, 41-46)); a fourth may be hidden, confidence 0.4 · **`hammer.ribs` = 6 +/- 2** (5-6 lines at 4 px pitch, clay c1; 5 in p1) · **grip pins**: not counted, the grip is behind fingers in every view.

---

## 6. Scale-free ratios

These matter more than the mm. Most are measured perpendicular to the bore at one depth, so they carry no perspective bias.

| id | value | tol | method | conf |
|---|---|---|---|---|
| `muzzle.bore/collar.od` | 0.53 | +/-0.06 | p3: bore y 52-73 = 21 px, collar OD 40 px. Both perpendicular to the axis at the same depth — **no perspective bias. The strongest number here.** | 0.65 |
| `muzzle.liner/collar.od` | 0.70 | +/-0.06 | p3: liner y 49-77 = 28 px / 40 px | 0.60 |
| `muzzle.collar.od/tube.od` | 1.25 | +/-0.15 | **bracketed**: p3 (muzzle nearer camera, inflated) 40/37 = 1.08; p1 (muzzle farther, deflated) 41/30 = 1.37. True value lies between. | 0.60 |
| `lattice.od/tube.od` | 1.45 | +/-0.15 | p3: collar 54 px (y 30-84) / tube 37 px; collar is at the far end so this is a lower bound | 0.55 |
| `L/tube.od` | >=4.46, best 4.7 | +0.6/-0.2 | p3: L 165 px / D 37 px; L foreshortened, D not | 0.55 |
| `grip.rake` (to bore axis) | 62 deg | **+/-12 deg** | clay c1 gives ~50 deg, p3 sheet gives ~74 deg. The two views disagree by 24 deg and I cannot arbitrate. The wide tolerance is the honest answer. | 0.35 |

### The scale chain, attacked

The brief invited an attack on `44 mm hand -> 52.5 px in p1 -> 0.838 mm/px`. I could not replace the 44 mm — nothing in any reference carries a dimension — but I can report two things about the chain's *stability*:

1. **The muzzle/tube ratio brackets the brief's own numbers.** The brief's 38 mm / 30 mm = 1.27 sits inside my bracket [1.08, 1.37]. The diameters are self-consistent.
2. **The hand anchor reproduces to ~10% across two independent renders.** Barrel length / four-finger span: clay c1 = 128/49 = **2.61**; p1 = 130/55 = **2.36**. Both are projected, both foreshortened, and they agree to 10%. So the *reading* of the anchor is reproducible even though the 44 mm itself remains untested. My first pass on the clay fingers gave 39 px and a 39% disagreement; re-reading `g_c1_grip.png` showed I had missed the index finger, which sits partly on the trigger at y 256-268. The corrected span is y 256->305 = 49 +/- 4 px.

Combining: L ~ 2.5 x hand breadth ~ 110 mm as a **lower bound** (projection), and L >= 4.46 D_tube, so D_tube ~ 25-29 mm once 10-15% foreshortening is allowed. That lands on the brief's 30 mm from below. **The chain is not obviously wrong. It is also not confirmed — every step still hangs off one derived number in a different model.**

---

## 7. Edit handles

For each: what must move, what must not. The "must not" list *is* the locality test.

### H1 `barrel.length` (mm) — the obvious one
**Policy (DECLARED): stretch, don't translate.** The pale-blue tube section between the mid-band and the muzzle collar is the only plain cylinder on the object; put all the deformation there. Scaling the whole barrel would distort the muzzle collar's three steps, which are the most detailed thing on it.

- **must move** (translate +delta along X, rigid, no shape change): muzzle collar + all 3 steps + liner, brass mid-band, hanging lug, rail forward stud
- **must stretch**: `barrel.tube.fore` (`min.x` face fixed, `max.x` face +delta); `rail` (`min.x` face fixed, `max.x` face +delta)
- **must NOT move, at all**: lattice collar, frame, hammer + neck, trigger, trigger guard, grip, grip panel/pins, butt cap, rail rear hook, copper tube section
- **trap**: the rail is stretchy *and* has a fixed rear hook. A whole-bbox invariant on `rail` fails by construction. **The locality test must be stated per bbox face for stretchy parts** — see 8.6.

### H2 `barrel.tube.od` (mm)
- **must move**: main tube (both sections) radially; mid-band, lattice collar and muzzle collar offset radially by the same delta-R — offset, not scale, so their wall thicknesses survive; rail rises by delta-R/2
- **must NOT move**: frame, hammer, trigger, guard, grip, butt cap — everything from the breech face rearward
- **trap, and it is a real one**: if the frame is authored as a solid that wraps the barrel's rear, changing tube OD legitimately changes the frame and the test fails by construction. **The frame's barrel-facing bore must be its own parameter, driven by this handle, with the frame's outer envelope independent of it.** If it isn't, H2 has no locality and the honest thing is to say so rather than loosen the tolerance until it passes.

### H3 `grip.rake` (degrees, about Z)
- **pivot**: DECLARED at the trigger guard's rear attach, clay c1 ~(702,276) -> (-0.08 L, -2.4 R, 0)
- **must move**: grip body, grip panel, grip pins, butt cap
- **must NOT move**: frame, trigger, trigger guard, barrel, everything above
- **the one genuine conflict in the set**: the guard is attached to the frame at its front and to the grip at its rear. Either it moves with the grip and its front joint tears, or it stays and its rear joint tears. Resolution (DECLARED): **the guard belongs to the frame, and the rake pivot is placed exactly at the guard's rear attach point**, so the guard's rear tip is the rotation's invariant point and nothing tears. Any other pivot placement makes this handle non-local no matter how the test is written.

### H4 `lattice.count` (integer, 8-12)
- **must move**: only the cutout instances inside the collar
- **must NOT move**: the collar's own outer envelope — its world bbox must be **unchanged** — the tube, and everything else
- This is the best locality test on the object, because the expected bbox delta is zero *even for the part that changed*. If changing the count moves the collar's bbox, the collar's outer shell is being rebuilt from the cutouts, which is a bug.

### H5 `rail.length` · H6 `muzzle.collar.steps` (integer 2-4) · H7 `hammer.angle` / `trigger.angle`
H7 are the joints doubling as pose handles; their invariant set is "everything except this part and its children".

---

## 8. The locality test

### 8.1 Procedure
1. Build at nominal parameters. Traverse the scene graph. For **every named mesh** record: its **world-space AABB** computed from transformed vertex positions (never a cached geometry bbox), its **world matrix** (16 floats), and a **vertex checksum** (vertex count + centroid rounded to 1e-6 + sorted-position hash). Call this `B0`.
2. Perturb **one** handle.
3. **Rebuild from scratch** — a fresh factory call, not a mutation of the existing scene. A shared-mutable-state bug only shows up if the second build is independent.
4. Recompute `B1`.
5. **Invariant set** — for every part the handle declares untouched, assert all three of: `|B1.aabb - B0.aabb| <= tol` on all 6 components; `|B1.matrix - B0.matrix| <= tol`; checksum identical. Bbox alone is not enough — it misses a rotation in place and a reshape that preserves extents.
6. **Moving set** — for every part the handle declares as moving, assert it moved by **at least 10x tol** on at least one component, and where the motion is predictable (a rigid translate of delta), assert it equals delta within tol. **A locality test that only checks the invariants passes trivially when the handle does nothing.** Half of this test's value is asserting the handle works.
7. **Topology** — assert the part-name set and the parent-child edge set are unchanged, except for count handles, where only the count-instanced children may differ in number.

### 8.2 Perturbation sizes
+10% of nominal, floored at 2 mm for lengths and 5 deg for angles, +/-1 for counts. Large against tol, small against the feature.

### 8.3 Also test at the range ends
Non-locality usually appears at extremes, not at nominal +10% — a stretched tube finally reaching the frame, a raked grip finally clipping the guard. Run the same test at each handle's declared min and max.

### 8.4 Tolerance — and why
**Start at `tol = 0`.** Same parameters, same traversal, deterministic builder: the correct answer is bit-identical, and any nonzero delta is information.

If tol = 0 fails, relax to **`tol = 1e-4 mm` (1e-7 m)** and record why. The justification is that this number is set by *numerical noise*, not by modelling slop:
- float32 positions at ~100 mm scale have an ULP of ~6e-6 mm; accumulated error down a 3-4 deep transform chain is ~1e-4 mm
- the smallest *meaningful* leak — a handle actually reaching a part it shouldn't — is at least ~0.1 mm, because you cannot move something a useful amount by less
- so 1e-4 mm sits ~4 orders above float noise and ~3 below the smallest real leak

**If the test needs 0.1 mm to pass, the tolerance is not the problem — the builder is not deterministic, and that is the finding.** Do not tune tol upward until green. The whole point of the check is that it can fail.

### 8.5 Report shape
Per handle: `{handle, delta, invariant_violations: [{part, component, magnitude}], moving_set_no_ops: [part], topology_delta}`. 18/18 means 18 handle-perturbations with empty violation lists **and** empty no-op lists.

### 8.6 Stretchy parts
`rail`, `barrel.tube.fore`, `grip` under some handles change extent by design. For these the invariant is stated **per bbox face**, e.g. for H1: `rail.min.x` invariant, `rail.max.x` moves by delta, `rail.min.y/max.y/min.z/max.z` invariant. A whole-bbox rule would fail by construction and would train whoever runs it to ignore the result.

---

## 9. Falsifiable constraint list

| id | kind | value | tol | how a script checks it against the built model | evidence | conf |
|---|---|---|---|---|---|---|
| `joint.trigger.exists` | count | 1 | exact | joint list contains `trigger`, parent `frame`; its child mesh's world AABB lies wholly inside the guard's world AABB | clay c1 (692-700, 256-272) inside the guard bow; also c3, c4 | 0.90 |
| `joint.trigger.axis` | relation | parallel to Z | 2 deg | `dot(normalize(axis),(0,0,1)) > 0.9994` | DECLARED | 0.95 |
| `joint.trigger.pivot.y` | ratio | -1.40 R | +/-0.20 R | pivot -> world, Y relative to bore axis, / (0.5 x tube AABB y-extent) | clay c1 blade top y 256, axis y 228, R 20 px | 0.60 |
| `joint.trigger.pivot.x` | ratio | -0.02 L | +/-0.04 L | same along X, L from barrel AABB | clay c1 x 695 vs breech 692 | 0.50 |
| `joint.trigger.range` | angle | 14 deg total, rest 0 | +/-6 deg | drive to both limits; min distance blade->guard inner surface <= 0.5 mm at each; 20 intermediate poses collision-free | DECLARED from guard opening 18 px = 0.9 R vs blade 0.75 R | 0.45 |
| `joint.hammer.exists` | count | 1 | exact | joint named `hammer`, parent `frame` | p1 (188-212,48-70); clay c1 (711-740,203-217) | 0.65 |
| `joint.hammer.axis` | relation | parallel to Z | 3 deg | as above | DECLARED | 0.80 |
| `joint.hammer.pivot` | ratio | (-0.07 L, +0.78 R) | (0.04 L, 0.20 R) | pivot -> world, decomposed on bore axis | p3 sheet (2428,253); clay c1 (703,218) | 0.50 |
| `joint.hammer.rest` | angle | 150 deg from +X in XY | +/-8 deg | largest eigenvector of the child's vertex covariance in gun-local coords at rest; angle to +X | clay c1 23 deg, p1 38 deg | 0.60 |
| `joint.hammer.range` | angle | [-55, +20] | derived | at low limit: forward-most child vertex within 1.0 mm of breech plane, no penetration; at high limit: no child vertex below frame top face | DECLARED | 0.35 |
| `joint.hammer.aspect` | ratio | 2.35 | +/-0.25 | child OBB longest/shortest edge | c1 2.15, p1 2.64, c2 2.5 | 0.60 |
| `joint.hammer.clearance` | relation | disjoint from frame in silhouette | 1 px | orthographic side render (camera along -Z): the piece's rendered region separated from the frame's by >=1 px of background everywhere except a neck of width <= 0.45 x the piece's diameter | p1 background visible at (175-190, 55-75) | 0.75 |
| `hammer.ribs` | count | 6 | +/-2 | sample surface radius along the piece's own axis; count local maxima | clay c1 5-6 at 4 px pitch; p1 5 | 0.50 |
| `joint.cylinder.axis` | relation | = bore axis | 0.5 deg | IF J3 shipped: joint axis vs the line through the muzzle bore centre and the breech centre; index step = 360/N | NOT ESTABLISHED (section 9 item 3) | 0.35 |
| `lattice.repeat` | count | 9 | 8-12 | 720 rays inward from radius 1.2 x collar OD in the collar's axial midplane, plane normal to the bore; count runs of "miss" | projection fit, section 5 | 0.40 |
| `lattice.od/tube.od` | ratio | 1.45 | +/-0.15 | world AABB yz-extents | p3 54 px / 37 px | 0.55 |
| `muzzle.collar.od/tube.od` | ratio | 1.25 | +/-0.15 | world AABB yz-extents | bracketed p3 1.08, p1 1.37 | 0.60 |
| `muzzle.bore/collar.od` | ratio | 0.53 | +/-0.06 | liner mesh inner radius x2 / collar AABB y-extent | p3 21 px / 40 px | 0.65 |
| `muzzle.liner/collar.od` | ratio | 0.70 | +/-0.06 | as above | p3 28 px / 40 px | 0.60 |
| `muzzle.steps` | count | 3 | exact | sample collar radius at 200 stations along X; count monotone-increasing plateaus | p3 34/37/40 px; p2 3 rings | 0.60 |
| `barrel.L/tube.od` | ratio | 4.7 | +0.6/-0.2 | world AABBs | p3 165/37, lower bound | 0.55 |
| `rail.studs` | count | 3 | +1/-0 | count children matching `rail.stud.*` | p3 x~90, x~98, x~163 | 0.40 |
| `lug.position` | ratio | +0.52 L | +/-0.05 L | AABB centre along X / L | p3 (97-108) -> sheet 2518-2529 | 0.60 |
| `lug.flush` | relation | lug top flush with tube underside | 0.5 mm | lug AABB max.y vs tube surface at that x | p3 lug top y 77, tube bottom y 76-77 | 0.55 |
| `sight.pivot` | ratio | (+0.04 L, +1.35 R) | (0.03 L, 0.2 R) | as J1 | p3 sheet (2444,244) | 0.45 |
| `grip.rake` | angle | 62 deg to bore | +/-12 deg | grip mesh principal axis vs bore axis | clay c1 50 deg, p3 74 deg | 0.35 |
| `socket.grip.exists` | count | 1 | exact | `actionProfile.sockets` contains `grip` | DECLARED | — |
| `socket.muzzle.exists` | count | 1 | exact | contains `muzzle`, origin within 1 mm of the bore axis at x=+1.00 L | DECLARED | — |
| `locality.H1..H7` | relation | invariant sets unmoved | see 8.4 | the procedure in section 8 | DECLARED | — |

---

## 10. What I could not measure, and why

1. **Whether the hammer articulates.** The aspect-ratio argument (section 3) fixes its *orientation* across five views. It says nothing about a hinge. No pivot pin or screw head is resolvable — at this scale one would be 1-2 px.
2. **The exact lattice count.** The projection fit gives 8-12 X-crossings; the integer depends on the assumed collar radius (24->8.2, 30->10.5) and I cannot pin the radius better than +/-4 px.
3. **Whether the lattice collar rotates.** No cylinder gap, crane, ejector rod, chamber mouths, or loading gate anywhere in nine views. All would be 1-3 px. Absence is not evidence either way.
4. **How the gun loads.** Same reason. J6 is a design choice, not a reading.
5. **Trigger travel.** Blade 8x15 px, rear clearance ~3 px. Any degrees figure would be invented; J2 derives it from the guard opening instead.
6. **Whether the hanging lug is a loop or a tab** (11x6 px), and whether the rear hook folds (19x13 px, no hinge line).
7. **Any lateral (Z) offset of any joint.** Every usable view is near-abeam or near-axial. All joints are DECLARED at z = 0. `c2` weakly suggests the hammer may sit off-centre; I could not confirm it and did not build on it.
8. **Grip rake better than +/-12 deg.** Two views, 24 deg apart, no way to arbitrate.
9. **Hammer rib count better than +/-2.**
10. **Grip pins.** Fingers cover the grip in every pose in both sheets.
11. **Absolute millimetres for anything.** Section 6 shows the chain is self-consistent and reproducible to ~10%; it does not show it is right. It still rests on one derived number in a different model.
