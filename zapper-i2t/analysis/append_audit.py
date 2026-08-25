"""Append the adversarial audit to the frozen contract, and mark the padding.

The contract was frozen from six independent measurement reports, then handed to an
agent whose only instruction was to refute it. It re-measured 18 constraints from the
sheet pixels; 13 reproduced, several to within a pixel. It also found 25 defects.

Nothing in the contract is rewritten here. The rows stay as they were frozen, and the
audit is appended beside them, because a contract that quietly edits away what an
audit found is worth less than one that records both. What DOES change is the
scoring: 19 rows are marked `falsifiable: false`, so `check_contract.py` scores 104
rather than 123.

That distinction is the whole point. Nova3D's headline is "51/52 prompt-stated
constraints satisfied", and the auditor's closing finding is that a score computed on
this document as frozen would have been inflated by about 15 percent before any
modelling began -- not by cheating, but because nine rows cannot fail for any built
gun, six are not runnable as written, and four check something other than the value
they state.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / 'docs/CONTRACT.md'

# --- rows the audit found cannot fail, are not runnable, or test the wrong thing ---
NOT_FALSIFIABLE = {
    # cannot fail for any built gun -- properties of the reference, of the character,
    # or of another document, not of this object
    'scale.mmPerPixel': 'the contract itself says "not a model property"',
    'scale.stature.px': 'a property of the reference sheet, and of a character',
    'scale.handBreadth.px': 'a property of a character; the gun has no fingers',
    'scale.brief.superseded': 'arithmetic between two documents',
    'gun.length.overCharacterHeight': 'needs a character mesh that is not in the tree',
    'gun.length.overHandBreadth': 'needs a hand mesh that is not in the tree',
    'grip.length.overHandBreadth': 'needs a hand mesh that is not in the tree',
    'grip.butt.toeStud.count': '0, 1 and 2 all pass; nothing specified could produce 3',
    'shading.ramp': 'measures the light rig, not the object',
    # not runnable as written
    'barrel.tube.od.px': 'needs "the pose3 camera", which S10.3 says was never recovered',
    'barrel.axis.imageSlope': 'needs the pose3 camera; and D-7, the tolerance is 3.5x '
                              'tighter than the 1 px quantisation floor',
    'area.brassShare': 'needs the pose3 camera',
    'graffiti.count.perView': 'needs the pose3 camera',
    'graffiti.onMetal': 'needs a per-island host-mesh lookup the tree does not encode',
    'graffiti.crossesSeam': 'needs a per-island host-mesh lookup the tree does not encode',
    # the check tests something other than the stated value
    'grip.fingerCourse.count': 'value is "4, exact"; the check never counts four courses',
    'grip.root.flushWithFrame': 'the check implements only the gap clause, so its '
                                'contradiction with grip.butt.behindFrameHeel is invisible',
    'barrel.rail.studs.count': 'the check demands 0.5 stud diameters; its own evidence '
                               'is 8 px apart, about 2.3 stud diameters',
    'frame.top.aboveAxis': 'the value is a local reading at the receiver rear; the check '
                           'is an AABB maximum, which is 0.47-0.67 D',
}

AUDIT = """

---

## 11. Adversarial audit

The contract above was frozen first. It was then handed to an agent whose only
instruction was to **refute** it: re-measure its constraints from the sheet pixels
independently, attack the scale chain, and find every row a built model could not
fail. Its working is under `analysis/audit2/`.

**Verdict: SOUND WITH CAVEATS.** Eighteen constraints were re-measured from the
pixels; **thirteen reproduce**, several to within one pixel — including the ones most
likely to break: the lattice-hole fit, the material seams, the liner step, the
port/collar gap, the grip heel drop, the stature span, and the 1.67x scale
correction.

Nothing below is edited out of sections 1-10. The rows stand as frozen and the audit
stands beside them, because a contract that quietly deletes what an audit found is
worth less than one that carries both.

### 11.1 The one fabrication, and it is not in the measurements

> "No fabricated *measurements*. Every number I spot-checked traces to real pixels
> ... The fabrication in this document is not in the measurements; it is in **D-19**,
> where a joint-limit verification is reported as having been performed on geometry
> that the same document says does not exist."

**D-19.** Joint J1's limit reads "at the low limit the child's forward-most vertex is
within 1.0 mm of the breech-face plane and penetrates nothing"; J2's reads "20 sampled
intermediate poses interpenetrate nothing". Interpenetration over sampled poses is a
mesh computation. This document's own §Purpose, line 5, says: **"Nothing has been
modelled."** Both limits assert the result of a test that could not have been run.

Those two limits are hereby **downgraded to DECLARED intent**. They state what the
joint should satisfy once a mesh exists, and `tools/locality_test.py` plus
`check_contract.py`'s joint check are what will actually establish it.

### 11.2 The refuted claim

**D-1. The grip is not the frame's paint.** §10.7 asserted "the grip's lateral
surface — zero unoccluded pixels in nine views", and `mat.grip.notWood` concluded the
brief's "dark red-brown wood" was unsupported by a single pixel.

There is a clean unoccluded lateral grip face in pose3 at sheet **x 2409-2435,
y 326-345**, bounded by background on the left, the butt cap below and the fingers on
the right. **388 of 540 pixels** classify warm:

| region | n | L* | a* | b* | h |
|---|---|---|---|---|---|
| **grip body** | 388 | 28.2 | **+6.48** | **+11.44** | 60.5 deg |
| butt cap | 240 | 35.2 | -0.96 | -7.35 | 258 deg |
| tube paint | — | — | -1.5 | -7.0 | — |

The butt cap matches the frame paint to within 0.5 a* and 0.35 b* — the original
evidence was correct *for the butt cap*, and was generalised to the whole grip. A
shadow on a cool blue-grey goes bluer, not to b* +11.4. **`mat.grip.notWood` is
false**, §10.7's premise is false, and the brief's grip description is partly
vindicated.

### 11.3 Contradictions between rows

| id | what collides |
|---|---|
| **D-2** | `barrel.copperOverSteel.length` (0.71 ± 0.08) and `barrel.zone.blueOverWarm` (1.62 ± 0.15) are the same ratio inverted. They overlap only over warm/pale ∈ [0.63, 0.68]; a builder hitting either centre fails the other. Measured: 38 px / 51 px = **0.745**, which satisfies the first and fails the second. |
| **D-11** | `grip.root.flushWithFrame` requires the grip's footprint inside the frame's (u 0.808-0.955); `grip.butt.behindFrameHeel` requires the butt rearward of it, and the tree gives the grip u 0.808-**1.000**. Both cannot hold. |
| **D-12** | `barrel.step.count` = 5 counts dr/dx sign changes over 2 % of R = 0.37 px. §6.5-6.7 specify three muzzle rings with two grooves, a proud rail and a lug — a model built to satisfy them registers **11-13 steps** and fails the count. |
| **D-13** | `lattice.opening.count`'s accept band 12-20 admits builds violating `barrel.lattice.od`: N = 12 needs OD below its floor, N = 20 above its ceiling. The band consistent with both is **14-18**. |
| **D-14** | `barrel.rail.studs.count`'s check requires two studs within 0.5 stud diameters; its own evidence puts them 8 px apart, about 2.3 diameters. |
| **D-22** | H3's rake pivot is at u 0.815 and J2 puts the trigger at u 0.824 — rearward of the guard's declared rear attach, so `frame.trigger.insideGuard` cannot hold. |

### 11.4 Evidence that does not support its row

**D-6** is the largest single correction. `barrel.rail.axialSpan`'s evidence said the
rail spans x 2479-2592. The rail is continuous **over** the lattice: a bar at y 237-245
runs from x **2443**, stepping down 8 px at x 2482 onto the plain tube — exactly the
difference between the lattice top and the tube top, i.e. it sits tangent on both.
Colour confirms it is rail and not collar (h 87.9 deg, the yellow-brass family, against
the lattice body's 61.1 deg). True span **149 px = 0.93 L**, not 0.706 L. The `>= 0.55 L`
constraint survives; the number behind it does not.

Also: **D-3** `frame.port.od` measures 0.33 D against a stated 0.41 ± 0.07;
**D-4** `frame.protrusionsAbove.count` = 2 cites three poses but pose3 shows one;
**D-8** `barrel.rail.proud`'s evidence uses R = 21.6 px, from the superseded D = 43
camp, and was missed by D3's rescale; **D-9** `mat.paint.tube.ab`'s b* reproduces as
-4.56 (CI [-4.77, -4.33]) against a stated -7.0 ± 1.5 — the integer median is -6.0 and
inside, so the row flips on the choice of mean versus median and does not deserve
conf 0.90; **D-10** `frame.top.aboveAxis` states a local reading and checks an AABB
maximum.

### 11.5 The joints are not all geometrically valid

**D-20.** J1's pivot is at +0.6 R and `frame.top.aboveAxis` puts the receiver top at
+0.64 R, with 0.37 R of receiver behind the pivot. Below roughly +7 deg the spur lies
inside the receiver's footprint, so **the whole negative half of the declared
[-55 deg, +20 deg] range interpenetrates** unless the receiver carries a slot, which
`frame.surfaceFeatures.count = 0` denies. This is precisely the failure mode Nova3D's
98.3 % geometric-validity figure measures.

**D-21.** J1's high-limit condition — "no child vertex lies below the frame's top
face" — is unsatisfiable at rest, because the pivot itself sits below that face.

J3 (lattice rotation) and J5 (lug swivel) check out: J3's pivot is the lattice's exact
axial midpoint and lies on the axis; J5's sits at a lug the auditor independently
confirms as a 5 px bulge over x 2516-2529, reach 1.27 R.

### 11.6 The scale chain survives, but its independence does not

**D-17.** §1's "three spec-internal cross-checks" are not independent of the stature
anchor. `spec_baseline.json` says every length in it is *"a measured ratio against"*
its declared stature, so for any spec length `L_spec / px = 1715 / stature_px` — the
cross-check returns the anchor by algebra. "Seven readings, four methods" is really
four readings of one method plus one outside assumption. The third anchor is worse: the
boot-length figure of 285 mm contradicts the same file's `Boot` component depth of
0.200 m.

**None of this changes the answer.** The auditor independently derives
**1720 / 1230 = 1.398 mm/px** and the same **1.67x** correction over the brief. What
changes is the honesty of the confidence attached to it.

**D-18.** `scale.handBreadth.px` = 43 ± 4 px is tighter than the feature's definitional
ambiguity: four contiguous finger bands give 38 px, the full skin stack 49 px. The
honest interval is 38-49, about ±13 %, not ±9 %.

### 11.7 Falsifiability: 104, not 123

This is the finding that matters most for how any result is reported.

| category | rows |
|---|---|
| cannot fail for any built gun | **9** |
| not runnable as written | **6** |
| the check tests something other than the stated value | **4** |
| **genuinely falsifiable and runnable** | **104** |
| of those, bands so wide almost any plausible build passes | ~10 |

> "A 51/52-style score computed on this document would be inflated by roughly **15 %**
> before any modelling begins. The right presentation is **104 falsifiable /
> 94 meaningfully tight**."

`docs/contract.json` therefore marks those 19 rows `falsifiable: false`, and
`tools/check_contract.py` scores against **104**. A constraint that cannot fail is not
evidence that a pipeline satisfies constraints; it is padding, and reporting it inside
a satisfaction ratio is the exact failure mode that makes such ratios worth
distrusting.

### 11.8 Bookkeeping

**D-16.** §6's header says ten rows carry DECLARED; the count is **nine**. And "only
the 10 dimension rows depend on the scale chain" is false in both directions: six of
the ten are pixels or CIE Lab and touch no millimetre, so only **three** rows are
scale-exposed — while the *handles* (H1, H2), §9.2's 2 mm floor, §9.4's 1e-4 mm
tolerance and J1/J2's 1.0 / 0.5 mm clearances are all absolute millimetres and do not
survive the axiom being wrong. The exposure was mislocated, not merely miscounted.

**D-24, D-25.** `graffiti.mark[*]` is parented to the root while three of its
constraints presuppose a host-mesh relation the tree does not encode; and the three
sockets named in §7 appear nowhere in §3, so §9.1's topology assertion does not cover
them.

**D-5, D-15.** §2's landmark table mixes pose3-measured with pose1-mapped stations
without distinguishing them — the error §2 exists to prevent. §9.6 lists `grip` as a
stretchy part, but no handle in §8 stretches it.
"""


def main() -> int:
    text = CONTRACT.read_text(encoding='utf-8')
    if '## 11. Adversarial audit' in text:
        text = text[:text.index('\n---\n\n## 11. Adversarial audit')]
    CONTRACT.write_text(text.rstrip() + AUDIT, encoding='utf-8')

    rows = json.loads((ROOT / 'analysis/contract_rows.json').read_text(encoding='utf-8'))
    hit = 0
    for r in rows:
        why = NOT_FALSIFIABLE.get(r['id'])
        r['falsifiable'] = why is None
        if why:
            r['notFalsifiableBecause'] = why
            hit += 1
    (ROOT / 'analysis/contract_rows.json').write_text(json.dumps(rows, indent=1),
                                                      encoding='utf-8')

    named = set(NOT_FALSIFIABLE) - {r['id'] for r in rows}
    print(f'CONTRACT.md: audit appended, {len(AUDIT.splitlines())} lines')
    print(f'contract rows: {len(rows)} total, {hit} marked not falsifiable, '
          f'{len(rows) - hit} scoreable')
    if named:
        print(f'  audit named {len(named)} rows the parsed table does not contain: '
              f'{sorted(named)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
