#!/usr/bin/env python
"""width-profile patch: per-component width / depth / radius corrections.

WHAT WAS MEASURED
-----------------
I rebuilt an analytic silhouette simulator (replaying emitter rules 1-4) that reproduces
the six real clay renders' 40-band width profiles to 0.11-0.25 %H mean absolute band
error, and used it to price every candidate edit without re-rendering.

The first thing it turned up is that most of the reported width error is not a geometry
defect at all.  `tools/evaluate.py` pins VIEW_MAP = {0:2, 45:1, 90:0, 180:5, 270:4,
315:3}.  Under orthographic projection a render at yaw t and yaw t+180 have IDENTICAL
silhouette width profiles, so each opposite pair is scored against two reference panels
at once.  Those panels do not agree:

    clay_2 vs clay_5   mean |diff| 1.28 %H, max  5.25 %H
    clay_0 vs clay_4   mean |diff| 4.41 %H, max 11.96 %H
    clay_1 vs clay_3   mean |diff| 4.62 %H, max 12.80 %H

(clay_0 and clay_4 are 0.226 and 0.292 in bbox W/H -- they cannot be 180 deg apart.)
No geometry can satisfy both panels of a pair.  The best any model can do is sit at the
pair mean, which leaves a floor of 2.411 %H against the six-view band RMS of 3.888 %H
that the current build scores.  Only 1.477 %H of that 3.888 is reachable by ANY change
to this model, and the yaw-270 view's headline 6.0 %H is mostly this artefact.

So the honest objective is the INTERVAL RESIDUAL: per band, the render is provably wrong
only when it falls outside [min, max] of the two panels of its pair, and then it is wrong
by at least the distance to the nearer panel, whichever panel is right.  The build scores
1.951 %H on that residual, with 52 of 120 bands provably outside both panels by >1 %H.

Then I measured the reference's parts directly instead of trusting the band totals.  In
clay_5 the two legs separate cleanly, and in clay_2/clay_5 the free-hanging right arm
separates from the torso, so real diameters can be read off (all converted to the render's
1.792 m metric frame):

    upper arm, f 0.30-0.34   reference 67-77 mm     model 72 mm    -> ALREADY CORRECT
    hand/wrist, f 0.45-0.51  reference 35-60 mm     model 52 mm    -> ALREADY CORRECT
    braid, clay_0 f 0.62     reference 49 mm        model 57 mm    -> ALREADY TOO THICK
    trouser, y 0.627         reference 94-115 mm    model 152 mm   -> 37-58 mm TOO FAT
    trouser, y 0.484         reference 106-107 mm   model 136 mm   -> 29 mm TOO FAT
    shin at knee, y 0.591    reference 89-109 mm    model 132 mm   -> 23 mm TOO FAT
    head depth (side)        reference 213-258 mm   model 305 mm   -> 47-92 mm TOO DEEP
    boot shaft, clay_2 f0.83 reference 293 mm       model 240 mm   -> 53 mm TOO NARROW

That kills the obvious "the model is too narrow, scale it up" reading.  An unconstrained
bounded fit over all 68 width/depth/radius knobs drives ten of them to their bounds and
buys only 0.43 %H -- it is the same global inflation a previous pass already applied
(blob depth x1.33, blob width x1.12, limb radius x1.19), and it would fatten arms and
braids that direct measurement says are already right or already too thick.  This patch
therefore ships only edits with an independent per-part measurement behind them.

WHAT THIS CHANGES
-----------------
Ten components, absolute values (so re-running is a no-op):

  hair        width 0.19774 -> 0.21225, depth 0.30498 -> 0.24780
              The head's PLAN aspect is wrong, not its size: front bands 1-3 are 21-34 mm
              too narrow while side bands 2-4 are 33-58 mm too deep, both determinate.
              hair is unattached (rule 3) so width and depth move independently.
  chest       depth 0.29702 -> 0.25167.  Side bands 9-10 are +28/+29 mm outside both
              panels; chest owns both side edges there, so depth maps 1:1 onto the error.
  neck        radius 0.04689 -> 0.05252.  Side bands 6-8 are 21-36 mm too shallow and the
              neck owns the front edge; 105 mm is a neck with a trapezius, 94 mm is not.
              Attached (rule 2): circular, so this also widens the neck in front, where
              band 6 is 28 mm too narrow anyway.
  shin-l/r    baseRadius 0.06589 -> 0.05550, endRadius 0.02374 -> 0.03300.  Fits the
              measured leg envelope at five heights (see table above) instead of the
              current 132 mm knee / 47 mm ankle cone.
  thigh-r     endRadius 0.06589 -> 0.05550.  thigh-l already ends at 0.05342; the right
              thigh's 132 mm knee was an unexplained left/right asymmetry.
  pants-l/r   baseRadius 0.09735 -> 0.09100, endRadius 0.06886 -> 0.06000.  Brought in as
              far as clearance allows: the trouser must stay outside thigh and shin, which
              is why it is shrunk together with them and not alone.
  boot-l/r    baseRadius 0.06886 -> 0.07850, endRadius 0.05936 -> 0.06767.  The only
              growth in the patch, and capped: at +14 % the two shafts span 261 mm, still
              inside the reference's own boot mass (293 mm main run at f 0.83, 254 mm at
              f 0.85) rather than standing in for the detached cuff flaps.

WHAT IT DOES NOT TOUCH, AND WHY
-------------------------------
Front band 7 (f 0.175) is 125 mm narrow and front band 8 is 67 mm narrow.  That is the
shoulder line sitting 3.1-4.0 %H low because `hair.dimensions.height` 0.3 puts the crown
at 1.790 m against a declared 1.72 m figure.  It is a vertical-registration defect; no
width can fix it and inflating the clavicles to 290 mm would fake it.

Front bands 13-19 are 31-62 mm narrow over seven consecutive bands.  The arms are the
right thickness (measured above) and hang ~25 mm too close to the body; that is lateral
placement, not girth.

Front bands 33-35 and three-quarter bands 32-33 are 43-112 mm narrow.  The reference's
width there is folded-over pointed boot-cuff flaps standing clear of the shaft across a
real air gap.  This build has no component for them -- and its own `boot-cuff` sits at
y 0.539-0.601, up at the knee instead of on the boot.

Side bands 38-39 are 61-71 mm narrow: the boot sole is 165-195 mm front-to-back where the
reference's is 235-254 mm.  `foot-l/r` are attached components, so by rule 2 they are
circular cylinders whose length front-to-back cannot be changed without widening them by
the same amount -- and front band 39 is already 28 mm TOO wide.  A correct boot sole needs
`foot-*` re-authored without an attachment (rule 3, independent depth) or given an SDF.

Front band 21 is 91 mm too wide: fingertip cylinders reaching |x| 0.246 at y 0.807-0.862
where the reference's hands have finished.  Finger radius is 9.5 mm; shrinking it moves
the extreme 2 mm.  Placement again.

EXPECTED MEASURABLE EFFECT
--------------------------
All figures below are simulator predictions, measured by re-running the analytic
projection on the patched spec.  The simulator tracks the six real clay renders to
0.11-0.25 %H mean absolute band error, so treat each as +/- ~0.2 %H.

  * interval-residual RMS over 120 bands: 1.951 -> 1.794 %H, and the count of bands
    provably outside BOTH reference panels by more than 1 %H falls from 52 to 42.
  * six-view 40-band RMS against the pinned panels (the scoreboard's widthBandRmsAll;
    the real renders measure 3.888 %H, the simulator 3.782 %H on the same geometry):
    3.782 -> 3.644 %H simulated, so expect the scoreboard number to fall by about
    0.14 %H, from ~4.08 to ~3.94.
  * six bands move from outside the reference interval to inside it: front/back 25 and
    32, three-quarter 2 and 3, side 1 and 4.  Two move out, both marginally: front/back
    23 by 7 mm and side 0 by 13 mm (the crown, where an ellipsoid cannot hold width to
    the pole).  Net -10 on the >1 %H count.
  * ratio against the pair mean, band by band:
      side 2/3/4 (head depth)        1.287 / 1.364 / 1.260  ->  1.115 / 1.110 / 1.040
      side 9/10  (ribcage depth)     1.135 / 1.132          ->  0.963 / 1.047
      front 1/2/3 (head width)       0.840 / 0.844 / 0.888  ->  0.901 / 0.905 / 0.953
      front 26/27/28/29 (trousers)   1.210 / 1.116 / 1.102 / 1.111 -> 1.176 / 1.067 /
                                     1.030 / 1.036
      front 33/34 (boot shaft)       0.824 / 0.707          ->  0.889 / 0.762
  * model bounding extent is UNCHANGED: x +/-0.2459 (set by the fingertips), y
    -0.0130..1.7900, z -0.1681..+0.1962 (set by hip-belt and diagonal-strap, neither of
    which this patch touches).  Nothing here moves the overall silhouette box; the patch
    only redistributes width inside it.

The two head bands the patch cannot reach illustrate the shape limit: `hair` is a single
ellipsoid, so narrowing its depth to fix bands 2-4 necessarily thins the crown at band 0,
and widening it to fix bands 1-3 necessarily over-widens the jaw at bands 4-5.  Getting
both ends right needs the head split or given an SDF, not a different width number.

TRIANGLE COST
-------------
Zero.  No SDF is added, no `geometryDescriptor.subdivide` is added, no primitive type
changes, and no `decimate.targetRatio` is touched.  Tessellation comes from the fixed
per-tier table in forge/_shared/subdivision.py (hero tier), which is keyed on primitive
type, not on physical size, so scaling `dimensions` and `attachment` radii cannot move the
count.  Triangles stay at the measured 128,833 of the 250,000 budget.

TRADE-OFF
---------
This patch is small on purpose.  A saturated fit reaches 1.53 %H on the interval residual
instead of 1.83 %H, but it gets there by fattening the forearms 12 %, the neck 10 %, the
braids 15 % and the clavicles 25 % -- all of which direct measurement of the reference
contradicts.  The remaining 1.83 %H is dominated by vertical registration, lateral arm
placement, the missing boot-cuff flaps and the circular-cylinder foot, none of which is a
width or a depth.
"""
import io
import json
import sys

# component id -> list of (json path within the component, old value we expect, new value)
# Absolute targets, so applying twice is identical to applying once.
CHANGES = [
    # --- head plan shape: front too narrow, side too deep (both determinate) -----------
    ('hair', ('dimensions', 'width'), 0.19774, 0.21225,
     'front bands 1-3 are 21-34 mm narrower than BOTH clay_2 and clay_5'),
    ('hair', ('dimensions', 'depth'), 0.30498, 0.24780,
     'side bands 2-4 are 33-58 mm deeper than BOTH clay_0 and clay_4; 248 mm lands '
     'inside the 213-258 mm the two panels bracket'),

    # --- ribcage depth ----------------------------------------------------------------
    ('chest', ('dimensions', 'depth'), 0.29702, 0.25167,
     'side bands 9-10 are +28/+29 mm outside both panels; chest owns both side edges'),

    # --- neck front-to-back -----------------------------------------------------------
    ('neck', ('attachment', 'baseRadius'), 0.04689, 0.05252,
     'side bands 6-8 are 21-36 mm too shallow with neck owning the front edge'),
    ('neck', ('attachment', 'endRadius'), 0.04689, 0.05252,
     'same, keeps the neck a straight column'),

    # --- lower leg: measured against clay_5 where the two legs separate ----------------
    ('shin-l', ('attachment', 'baseRadius'), 0.06589, 0.05550,
     'knee 132 mm -> 111 mm; reference reads 89-109 mm at y 0.591'),
    ('shin-l', ('attachment', 'endRadius'), 0.02374, 0.03300,
     'ankle 47 mm -> 66 mm; the old cone was too steep to follow the calf'),
    ('shin-r', ('attachment', 'baseRadius'), 0.06589, 0.05550, 'mirror of shin-l'),
    ('shin-r', ('attachment', 'endRadius'), 0.02374, 0.03300, 'mirror of shin-l'),
    ('thigh-r', ('attachment', 'endRadius'), 0.06589, 0.05550,
     'thigh-l already ends at 0.05342; the 132 mm right knee was an unexplained asymmetry'),

    # --- trouser column, brought in as far as leg clearance permits --------------------
    ('pants-l', ('attachment', 'baseRadius'), 0.09735, 0.09100,
     'trouser 195 mm -> 182 mm at the hip; reference leg column reads 149 mm at y 0.806'),
    ('pants-l', ('attachment', 'endRadius'), 0.06886, 0.06000,
     'trouser 138 mm -> 120 mm below the knee; reference reads 106-107 mm at y 0.484'),
    ('pants-r', ('attachment', 'baseRadius'), 0.09735, 0.09100, 'mirror of pants-l'),
    ('pants-r', ('attachment', 'endRadius'), 0.06886, 0.06000, 'mirror of pants-l'),

    # --- boot shaft: the only growth, capped at the reference's own boot mass ----------
    ('boot-l', ('attachment', 'baseRadius'), 0.06886, 0.07850,
     'two shafts span 242 mm -> 261 mm; clay_2 reads a 293 mm boot run at f 0.83'),
    ('boot-l', ('attachment', 'endRadius'), 0.05936, 0.06767, 'same taper ratio'),
    ('boot-r', ('attachment', 'baseRadius'), 0.06886, 0.07850, 'mirror of boot-l'),
    ('boot-r', ('attachment', 'endRadius'), 0.05936, 0.06767, 'mirror of boot-l'),
]


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else 'object-sculpt-spec.json'
    with io.open(path, encoding='utf-8') as fh:
        spec = json.load(fh)

    by_id = {c['id']: c for c in spec.get('componentTree', [])}

    applied, already, missing = [], [], []
    for cid, keypath, expect, target, why in CHANGES:
        comp = by_id.get(cid)
        if comp is None:
            missing.append((cid, '.'.join(keypath), 'component not in componentTree'))
            continue
        node = comp
        for k in keypath[:-1]:
            node = node.get(k) if isinstance(node, dict) else None
            if not isinstance(node, dict):
                break
        leaf = keypath[-1]
        if not isinstance(node, dict) or leaf not in node:
            missing.append((cid, '.'.join(keypath), 'field absent'))
            continue
        cur = node[leaf]
        if isinstance(cur, (int, float)) and abs(float(cur) - target) < 1e-9:
            already.append((cid, '.'.join(keypath), target))
            continue
        node[leaf] = target
        applied.append((cid, '.'.join(keypath), cur, target, expect, why))

    # the spec on disk is pure ASCII with \u escapes (json.dump's default), so keep
    # ensure_ascii at its default -- writing raw UTF-8 would rewrite 47 unrelated strings
    # and collide with the other agents sharing this file.
    with io.open(path, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, indent=1)

    print(f'patch_width.py -> {path}')
    print(f'  {len(applied)} field(s) changed, {len(already)} already at target, '
          f'{len(missing)} not found')
    if applied:
        print(f'  {"component":10s} {"field":24s} {"from":>9s} {"to":>9s} {"delta":>9s}  '
              f'{"dia mm":>8s}')
        for cid, field, cur, target, expect, why in applied:
            try:
                d = float(target) - float(cur)
                dia = f'{d * 2000:+.1f}' if 'Radius' in field else f'{d * 1000:+.1f}'
            except (TypeError, ValueError):
                d, dia = float('nan'), '-'
            drift = '' if abs(float(cur) - expect) < 1e-9 else f'   [was {expect}, drifted]'
            print(f'  {cid:10s} {field:24s} {float(cur):9.5f} {float(target):9.5f} '
                  f'{d:+9.5f}  {dia:>8s}{drift}')
        print()
        for cid, field, cur, target, expect, why in applied:
            print(f'  - {cid}.{field}: {why}')
    for cid, field, target in already:
        print(f'  = {cid}.{field} already {target} (idempotent re-run)')
    for cid, field, note in missing:
        print(f'  ! {cid}.{field}: {note}')
    print('\n  triangle cost: 0 (no SDF, no subdivide, no primitive change, '
          'no decimate change; tessellation is size-independent)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
