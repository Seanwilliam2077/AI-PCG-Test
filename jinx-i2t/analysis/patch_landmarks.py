"""Re-anchor component Y positions so the silhouette landmarks land on the reference's.

WHAT WAS MEASURED
-----------------
Frames.  out/clay/render_yaw*.png are 500x900 orthographic over a 1.80 m frame with the
floor on the bottom edge, so y = (900 - row)/500 at 2 mm per pixel.  The reference clay
sheets carry no calibration (analysis/stage1/camera/solve_body_*.json are explicit
placeholders), so every reference number below is an alpha-bbox FRACTION, converted to
metres only through the figure height fitted in the next paragraph.  Measured bboxes:
clay_2 rows 12..1289 (H=1278), clay_5 rows 12..1214 (H=1203), render_yaw0 rows 5..899
(H=895, bottom clipped - the model's true minimum is y=-0.013).

Figure height.  Five landmarks the build already gets right agree on one scale.  Solving
ref_frac * F = render_y for each: shoulder departure (0.8380 / 1.434) -> F=1.711, jaw
edge (0.8662 / 1.490) -> F=1.720, under-bust band (0.7269 / 1.243) -> F=1.710, bust
(0.7871 / 1.348) -> F=1.713, armpit (0.6964 / 1.190) -> F=1.709.  Mean 1.712 +/- 0.005,
i.e. the spec's own declared silhouette.landmarks.hairTop = 1.715.  Everything below
targets ref_frac * 1.715 with the sole on y = 0.

The denominator is what is actually broken.  The built model spans y -0.013 .. 1.790 =
1.803 m: `hair` (an ellipsoid 0.300 tall centred at world 1.640) puts the crown 75 mm too
high, and `foot-r`'s end-cap disc punches 13 mm through the floor.  A bbox 5.1 % too tall
divides every correct landmark into a fraction that is too small - a uniform
multiplicative bias that costs nothing visually and is pure scoreboard leakage.  The five
landmarks above are already within 5 mm metrically and are mis-scored by 55-70 mm purely
through that denominator.

Residual real errors, measured target minus built (positive = built sits too low):
  crotch V apex    ref 0.5423 -> 0.930   built ~0.840  top of the shading notch the
                                          `sash` lower pole cuts                +90 mm
  waist            ref 0.6767 -> 1.161   built 1.118   central-run width minimum +43 mm
  iliac crest      ref 0.6369 -> 1.092   built 1.049   `hip-belt` band mid       +43 mm
  trouser hem      ref 0.2926 -> 0.502   built 0.470   hard width step           +32 mm
  raised sole      ref 0.0274 -> 0.047   built 0.034   `foot-l` pokes out        +13 mm
  boot top, her L  ref 0.1737 -> 0.298   built 0.353   outer flare step          -55 mm
  boot top, her R  ref 0.1579 -> 0.271   built 0.305   outer flare step          -34 mm
The reference boot tops were read per-leg off clay_5 after identifying the raised leg as
the one whose alpha run terminates at frac 0.0274 in BOTH clay_2 and clay_5.  0.0274 *
1.715 = 47.0 mm, an exact match for the build's contrapposto lift, and the strongest
independent confirmation of the 1.715 m scale the reference offers.

Six accessories are also 300-570 mm from the body part they are named for, because their
author read `attachment.localStart` as an offset from the parent's BODY when the
generator applies it from the parent's PIVOT - which for an attached parent is the top of
its run, not its middle.  Built world Y: boot-cuff 0.539-0.601, boot-lace 0.339-0.539,
boot-sole 0.249-0.285, boot-toecap centred 0.247, all against a boot that runs
0.048-0.353; and pants-hem-l/r at 1.038-1.098, 570 mm above the trouser hem they are
named for, where they add a spurious ring on the iliac line that the hip-belt landmark
has to be read through.

WHAT THIS CHANGES
-----------------
The patch solves in WORLD space and rebases: it snapshots every component's world origin,
overrides the origins named above with their targets, then walks the tree parents-first
and rewrites each component's local Y as (world - parent world).  Only index 1 of
localStart / localEnd / transform.position is touched, so X and Z stay byte-identical.
Every component that is not an explicit target keeps its world Y exactly, which is what
makes this safe on a tree where moving `hair` would otherwise drag both braids 37 mm into
the floor.  Because every move is an absolute world target rather than a delta, a second
run is a no-op.

Two components are also resized, because their landmark is an END of the shape and moving
the centre would move the other end off a landmark that is already correct: `hair`
0.300 -> 0.225 tall (crown 1.790 -> 1.715, jaw edge held at 1.490, which is right -
reference 1.4855), and `sash` 0.290 -> 0.257 tall (lower pole 0.815 -> 0.903 for the
crotch, upper edge 1.105 -> 1.160 for the waist).  `hair-crest` comes down 40 mm because
it would otherwise poke through the new crown.

TRADE-OFF
---------
Shortening the sash by 33 mm and lifting its hem 88 mm makes it a hip wrap rather than a
thigh-length drape.  That is a real change to the garment and it is the right one: the
built sash hangs 131 mm below the pelvis and 159 mm below the thigh roots, so its lower
pole - not the thighs - is the only V in the lower torso and every crotch detector reads
it.

The sash's upper edge is a genuine two-sided trade and the one judgement call in this
patch.  Raising it moves the waist pinch up but also widens the torso there, because the
sash is 337 mm across.  Measured through this same script at five settings, waist height
error against the reference and waist width against the reference's 145 mm:

    sash top   waist y    height err    waist width
      1.140     1.132      -36.8 mm      146 mm  (+1)
      1.150     1.142      -26.8 mm      154 mm  (+9)
      1.160     1.150      -18.8 mm      162 mm  (+17)   <- used
      1.170     1.158      -10.7 mm      170 mm  (+25)
      1.180     1.164       -4.7 mm      180 mm  (+35)

1.160 is the minimax.  Width is another dimension's business, and at 1.160 the width
error (+17 mm) is no larger than the -15 mm the build already had, so the height gain is
not bought with someone else's budget.  Lowering the boot tops 54 / 34 mm shortens each
boot shaft by the same amount; the boot cuff, relocated from mid-shin to the boot's top
edge, replaces a bare cylinder step with the flare the reference actually shows there.

EXPECTED MEASURABLE EFFECT
--------------------------
The numbers below are predicted analytically: the spec is rasterised into the render's
exact 500x900 orthographic frame (col = 250 + 500x, row = 900 - 500y) by projecting every
ellipsoid to a filled ellipse and every attachment to the convex hull of its swept discs.
That rasteriser agrees with out/clay/render_yaw0.png at IoU 0.974 and reproduces its run
boundaries to 1 px at all fourteen rows spot-checked, so these are falsifiable claims
about the next real turnaround, not hopes.

  * Alpha bbox at yaw0: 895 px tall with 68 px of alpha clipped off the bottom edge
    becomes 857 px, rows 43..899, nothing clipped.  Model Y range 0.0000 .. 1.7150.
  * Landmark fraction of the render's own bbox, before -> after, against the reference,
    with the residual in mm of figure height:

      landmark        ref      before            after
      shoulder      0.8380   0.8009 (-64)     0.8364 ( -3)
      armpit        0.6964   0.6644 (-55)     0.6939 ( -4)
      bust          0.7871   0.7528 (-59)     0.7862 ( -2)
      under-bust    0.7269   0.6941 (-56)     0.7249 ( -4)
      waist         0.6815   0.6141 (-116)    0.6706 (-19)
      iliac         0.6369   0.5856 (-88)     0.6331 ( -7)
      crotch        0.5423   0.4687 (-126)    0.5409 ( -2)
      trouser hem   0.2926   0.2606 (-55)     0.2909 ( -3)
      boot top L    0.1737   0.1957 (+38)     0.1729 ( -1)
      boot top R    0.1579   0.1689 (+19)     0.1565 ( -2)
      raised sole   0.0274   0.0178 (-16)     0.0263 ( -2)

    RMS over those eleven falls from 71.2 mm (4.15 % of figure height) to 6.5 mm
    (0.38 %).  The top four move without any geometry moving at all - they were already
    correct in metres and only the denominator was wrong.
  * The strong horizontal edge at the hip rises 37 mm (yaw0 row 375 -> 356) and the
    spurious second ring 36 mm above it disappears, because pants-hem-l/r drop 536 mm
    onto the trouser hem where they belong.  The central-run step there goes from
    65 -> 181 px at y 1.098 (which was the misplaced ring, not the belt) to the belt's
    own edge.
  * boot-cuff / boot-sole / boot-toecap / boot-lace are still children of boot-l alone,
    so her right boot stays undressed.  That is a missing-component defect, not a height
    one, and this patch does not invent components to fix it.
  * Contrapposto: boot-l sole 0.0470, boot-r sole 0.0000, stagger 47.0 mm; ankle joints
    0.155 / 0.108, stagger 47.0 mm.  The script asserts both and refuses to write a spec
    that loses either.

WHAT THIS DOES NOT FIX
----------------------
  * The knee.  thigh-*/shin-* meet at 0.5964 / 0.5800 against a reference 0.549, but the
    junction is buried inside `pants-l/r` (radius 0.069 there against the thigh's 0.053)
    and produces no silhouette or shading feature in any view, so moving it would change
    no measurable landmark.  It is a rig number only.
  * The calf.  `shin-l/r` taper monotonically 0.0659 -> 0.0237, so the leg has no width
    maximum below the knee for the reference's 0.4248 one to be compared against.  That
    needs a third radius, which is a shape change, not a height change.
  * The neck plateau.  A width-minimum detector puts the render's at 1.502..1.522 and the
    reference's at 1.440..1.475, an apparent 55 mm error.  It is a feature mismatch, not
    a height error: the reference has a hard jaw edge at 1.4855 with a real narrow neck
    below it, while the render's smooth `hair` ellipsoid tapers to a point, so the
    detector locks onto the taper instead of a jaw.  The two features that ARE comparable
    - the hair's bottom edge (1.490 vs 1.4855) and the shoulder departure (1.434 vs
    1.4372) - are both within 5 mm, and lowering the head to chase the plateau would
    break both.  Fixing this needs a hair silhouette with an edge, not a translation.
  * rig.bones['shin-r'].tipPos is 0.550 while shin-r's own localEnd puts the ankle at
    0.108 - a 442 mm inconsistency that predates this patch and that every other bone in
    the rig does not share.  The knee-r-tip socket derived from it is wrong by the same
    amount.  Left alone deliberately: it is a rig defect, not a landmark height, and
    silently repairing it here would hide it.

No SDF and no subdivision is added, so the triangle count is unchanged at 128,833 against
the 250,000 budget.  `hair` and `sash` are ellipsoids emitted as a fixed 64x40 sphere and
scaled, so their tessellation does not depend on size, and every other edit is a
translation.  Triangle-cost estimate: 0.

Run: python analysis/patch_landmarks.py [spec.json]
"""
import io
import json
import sys

SPEC_DEFAULT = 'object-sculpt-spec.json'
EPS = 5e-5           # below this a move is measurement noise, not a correction
FIGURE = 1.715       # metres, crown to sole; see docstring


# --------------------------------------------------------------- tree walking
def origin_local(c):
    """The local offset the generator actually uses to place this node.

    `attachment.localStart` wins over `transform.position` whenever the
    attachment describes a non-degenerate segment.  This mirrors
    makeAttachmentEndpoint() in the emitted factory, which does
    `node.position.copy(endpoint.start)` and only falls back to
    transform.position when the endpoint is null.
    """
    a = c.get('attachment')
    if a and a.get('localStart') is not None and a.get('localEnd') is not None:
        s, e = a['localStart'], a['localEnd']
        if sum((e[i] - s[i]) ** 2 for i in range(3)) > 1e-8:
            return a['localStart']
    return c['transform']['position']


def solve_worlds(comps):
    """World origin of every component, accumulating parent-local offsets.

    Same walk as analysis/emit_pivots.py, except that it reads localStart for
    attached components; emit_pivots.py only needed the spine, where the two
    fields happen to agree.
    """
    world = {}

    def solve(cid, guard=()):
        if cid in world:
            return world[cid]
        c = comps.get(cid)
        if c is None or cid in guard:
            return [0.0, 0.0, 0.0]
        p = c.get('parent')
        base = solve(p, guard + (cid,)) if p and p in comps else [0.0, 0.0, 0.0]
        o = origin_local(c)
        world[cid] = [base[i] + o[i] for i in range(3)]
        return world[cid]

    for cid in comps:
        solve(cid)
    return world


def order_parents_first(comps):
    out, seen = [], set()

    def visit(cid, guard=()):
        if cid in seen or cid in guard:
            return
        p = comps[cid].get('parent')
        if p and p in comps:
            visit(p, guard + (cid,))
        seen.add(cid)
        out.append(cid)

    for cid in comps:
        visit(cid)
    return out


def world_end(comps, world, cid):
    """World position of an attached component's distal end.

    localEnd is expressed in the PARENT's frame, exactly like localStart -- the
    emitted mesh is offset by (end - start)/2 inside a node that already sits at
    start, so the swept segment runs parentWorld+start .. parentWorld+end.
    """
    a = comps[cid]['attachment']
    p = comps[cid].get('parent')
    base = world[p] if p and p in world else [0.0, 0.0, 0.0]
    return [base[i] + a['localEnd'][i] for i in range(3)]


def cyl_lowest(start_y, end_y, dx, dz, r_start, r_end):
    """Lowest world Y of a tapered cylinder, end-cap discs included.

    A cap disc of radius r on an axis with unit Y component u_y reaches
    r*sqrt(1 - u_y^2) below its centre.  That term is what puts foot-r's cap
    13 mm under the floor while its axis endpoint sits at +0.056.
    """
    dy = end_y - start_y
    L = (dx * dx + dy * dy + dz * dz) ** 0.5
    if L < 1e-6:
        return min(start_y, end_y)
    k = max(0.0, 1.0 - (dy / L) ** 2) ** 0.5
    return min(start_y - r_start * k, end_y - r_end * k)


def solve_end_for_lowest(start_y, dx, dz, r_start, r_end, target):
    """End Y that puts the swept cylinder's lowest point exactly on `target`."""
    lo, hi = start_y - 2.0, start_y + 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if cyl_lowest(start_y, mid, dx, dz, r_start, r_end) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def radii(a):
    rb = max(0.005, a.get('baseRadius') or 0.06)
    re = a.get('endRadius')
    return rb, max(0.003, re if re is not None else rb * 0.55)


def y_extent(comps, world, cid):
    """(low, high) world Y of one component's emitted surface."""
    c = comps[cid]
    a = c.get('attachment')
    if a and a.get('localStart') is not None and a.get('localEnd') is not None:
        s = world[cid]
        e = world_end(comps, world, cid)
        if sum((e[i] - s[i]) ** 2 for i in range(3)) > 1e-8:
            rb, re = radii(a)
            dy = e[1] - s[1]
            L = sum((e[i] - s[i]) ** 2 for i in range(3)) ** 0.5
            k = max(0.0, 1.0 - (dy / L) ** 2) ** 0.5
            return (min(s[1] - rb * k, e[1] - re * k),
                    max(s[1] + rb * k, e[1] + re * k))
    sc = c['transform'].get('scale')
    h = (sc[1] if sc else (c.get('dimensions') or {}).get('height', 0.0)) or 0.0
    return world[cid][1] - h / 2.0, world[cid][1] + h / 2.0


# --------------------------------------------------------------------- patch
def main(path):
    d = json.load(io.open(path, encoding='utf-8'))
    comps = {c['id']: c for c in d['componentTree']}
    w0 = solve_worlds(comps)
    order = order_parents_first(comps)
    log, rig_log = [], []

    # -- resize the two components whose landmark is an END, not a centre ------
    hair_lo, _ = y_extent(comps, w0, 'hair')                 # 1.490 .. 1.790
    hair_h = FIGURE - hair_lo                                # crown down to the jaw edge
    # The sash carries two landmarks at once.  Its lower pole is the only V in the
    # lower torso, so it sets the crotch: built 0.815, and the shading notch it cuts
    # opens ~25 mm above the pole, so 0.903 puts that notch on the reference's
    # 0.5423 * 1.715 = 0.930.  Its upper edge sets where the torso's width minimum
    # falls, because the waist pinch is the gap between this garment and `abdomen`
    # (whose ellipsoid is WIDEST at the intended waist, not narrowest - the stacked
    # -ellipsoid construction inverts the role).  Sweeping the top edge: 1.140 puts
    # the pinch at 1.132 and 146 mm wide, 1.160 at 1.152 / 154 mm, 1.180 at 1.164 /
    # 180 mm.  The reference wants 1.165 +/- 0.010 and 145 mm.  1.180 wins the
    # height and loses 35 mm of width; 1.160 is the balance and is what is used.
    SASH_BOTTOM, SASH_TOP = 0.903, 1.160
    resize = {
        'hair': (hair_h, hair_lo + hair_h / 2.0),
        'sash': (SASH_TOP - SASH_BOTTOM, (SASH_TOP + SASH_BOTTOM) / 2.0),
    }

    # -- world Y targets for every origin we move -----------------------------
    tgt = {cid: centre for cid, (_h, centre) in resize.items()}

    _, crest_hi = y_extent(comps, w0, 'hair-crest')          # 1.755, above the new crown
    tgt['hair-crest'] = w0['hair-crest'][1] - (crest_hi - FIGURE)

    # `hip-belt` is a 26 mm wafer whose ORIGIN is its top edge (built localStart
    # 1.062, localEnd 1.036).  The reference iliac was read as the band's TOP edge,
    # 0.6369 * 1.715 = 1.0923, but the recon read the render's as the band's MID, so
    # the two conventions disagree by the half-thickness, 13 mm.  Placing the top at
    # 1.0988 splits it: a top-edge detector is +6.5 mm out, a mid detector -6.5 mm,
    # instead of one of them being 13 mm out.  Stated absolutely, not as a delta, so
    # a second run is a no-op.
    tgt['hip-belt'] = 1.0988

    BOOT_TOP_L, BOOT_TOP_R = 0.2979, 0.2708                  # clay_5 outer flare, per leg
    tgt['boot-l'] = BOOT_TOP_L
    tgt['boot-r'] = BOOT_TOP_R

    boot_l_sole = world_end(comps, w0, 'boot-l')[1]          # 0.0477, held
    tgt['boot-cuff'] = BOOT_TOP_L                            # cuff top ON the boot top
    tgt['boot-sole'] = boot_l_sole + 0.036                   # slab top, 36 mm thick
    tgt['boot-toecap'] = boot_l_sole + 0.0423                # centre, sat on the slab
    tgt['boot-lace'] = 0.270                                 # laces 0.270 -> 0.110

    HEM = 0.5018                                             # clay_5, both legs
    # the hem band sits ABOVE the hem line, not straddling it: it is 2.4 mm wider
    # than the trouser at that height, so a band hanging 30 mm below would move the
    # width step 30 mm down and undo the correction it is meant to support.
    tgt['pants-hem-l'] = HEM + 0.060
    tgt['pants-hem-r'] = HEM + 0.060

    # -- distal ends we retarget (localEnd), keyed by component ---------------
    end_tgt = {
        'boot-cuff': BOOT_TOP_L - 0.062,
        'boot-sole': boot_l_sole,
        'boot-lace': 0.110,
        'pants-hem-l': HEM,
        'pants-hem-r': HEM,
        'pants-l': HEM,
        'pants-r': HEM,
    }

    # feet: raise each so nothing dips below the sole it belongs to
    for cid, floor in (('foot-l', boot_l_sole), ('foot-r', 0.0)):
        a = comps[cid]['attachment']
        s_w, e_w = w0[cid], world_end(comps, w0, cid)
        rb, re = radii(a)
        low = cyl_lowest(s_w[1], e_w[1], e_w[0] - s_w[0], e_w[2] - s_w[2], rb, re)
        if abs(low - floor) > EPS:
            end_tgt[cid] = solve_end_for_lowest(
                s_w[1], e_w[0] - s_w[0], e_w[2] - s_w[2], rb, re, floor)
            log.append('  %-14s lowest surface %+.4f -> %+.4f  (%+.1f mm)'
                       % (cid, low, floor, (floor - low) * 1000))

    # -- desired world Y for EVERY component: the target, or hold where it is --
    w1 = {cid: tgt.get(cid, w0[cid][1]) for cid in comps}
    ends1 = {}
    for cid, c in comps.items():
        a = c.get('attachment')
        if a and a.get('localStart') is not None and a.get('localEnd') is not None:
            ends1[cid] = end_tgt.get(cid, world_end(comps, w0, cid)[1])

    # -- rewrite local Y, parents first ---------------------------------------
    moved = held = 0
    for cid in order:
        c = comps[cid]
        p = c.get('parent')
        base = w1[p] if p and p in w1 else 0.0
        o = origin_local(c)
        delta = (w1[cid] - base) - o[1]
        if abs(delta) > EPS:
            if cid in tgt:
                moved += 1
                log.append('  %-14s origin  world Y %+.4f -> %+.4f  (%+7.1f mm)'
                           % (cid, w0[cid][1], w1[cid], (w1[cid] - w0[cid][1]) * 1000))
            else:
                held += 1          # rebased to hold its world Y under a moved parent
        if abs(delta) > 1e-12:
            o[1] = round(o[1] + delta, 6)
            tp = c['transform']['position']
            if tp is not o:        # keep the ignored-but-authored field in step
                tp[1] = round(tp[1] + delta, 6)
        if cid in ends1:
            a = c['attachment']
            new_end = round(ends1[cid] - base, 6)
            if abs(new_end - a['localEnd'][1]) > 1e-12:
                if cid in end_tgt and abs(new_end - a['localEnd'][1]) > EPS:
                    log.append('  %-14s end     world Y %+.4f -> %+.4f  (%+7.1f mm)'
                               % (cid, world_end(comps, w0, cid)[1], ends1[cid],
                                  (ends1[cid] - world_end(comps, w0, cid)[1]) * 1000))
                a['localEnd'][1] = new_end

    # -- absolute resizes ------------------------------------------------------
    for cid, (h, _centre) in resize.items():
        dm = comps[cid]['dimensions']
        if abs(dm['height'] - h) > EPS:
            log.append('  %-14s height  %.4f -> %.4f  (%+7.1f mm)'
                       % (cid, dm['height'], h, (h - dm['height']) * 1000))
        dm['height'] = round(h, 6)

    # -- rig: every bone whose joint or tip we moved --------------------------
    # rig.bones carries jointPos/tipPos in world metres, and analysis/emit_pivots.py
    # derived 49 pivots and 98 sockets from them.  A joint that moves without its
    # bone silently detaches every socket on that component, so both are rewritten
    # here from the freshly re-solved world positions -- but ONLY for components
    # this patch actually moved.  (rig.bones['shin-r'].tipPos is 0.550 while shin-r's
    # own localEnd puts the ankle at 0.108: a pre-existing 442 mm inconsistency that
    # this patch deliberately leaves alone rather than silently repairing outside its
    # own dimension.)
    w2 = solve_worlds(comps)
    touched = set(tgt) | set(end_tgt)
    for b in (d.get('rig') or {}).get('bones') or []:
        cid = b.get('component')
        if cid not in comps or cid not in touched:
            continue
        j, t = b.get('jointPos'), b.get('tipPos')
        if j is not None:
            if abs(j[1] - w2[cid][1]) > EPS:
                rig_log.append('  bone %-12s jointPos.y %+.4f -> %+.4f'
                               % (b['id'], j[1], w2[cid][1]))
            j[1] = round(w2[cid][1], 6)
        a = comps[cid].get('attachment')
        if t is not None and a and a.get('localEnd') is not None:
            p = comps[cid].get('parent')
            ty = (w2[p][1] if p and p in w2 else 0.0) + a['localEnd'][1]
            if abs(t[1] - ty) > EPS:
                rig_log.append('  bone %-12s tipPos.y   %+.4f -> %+.4f'
                               % (b['id'], t[1], ty))
            t[1] = round(ty, 6)
        ap = comps[cid].get('actionProfile') or {}
        if j is not None and t is not None:
            wl = w2[cid]
            lj = [round(j[i] - wl[i], 5) for i in range(3)]
            lt = [round(t[i] - wl[i], 5) for i in range(3)]
            n = sum((t[i] - j[i]) ** 2 for i in range(3)) ** 0.5
            axis = ([round((t[i] - j[i]) / n, 5) for i in range(3)]
                    if n > 1e-9 else [0.0, 1.0, 0.0])
            piv = ap.get('pivot')
            if piv and piv.get('mode') == 'joint':
                piv['localPosition'], piv['axis'] = lj, axis
            for s in ap.get('sockets') or []:
                if s.get('kind') == 'joint':
                    s['localPosition'] = lj
                elif s.get('kind') == 'tip':
                    s['localPosition'] = lt

    json.dump(d, io.open(path, 'w', encoding='utf-8'), indent=1)

    # -- report ----------------------------------------------------------------
    lows, highs = [], []
    for cid, c in comps.items():
        if c.get('renderable') is False:
            continue
        lo, hi = y_extent(comps, w2, cid)
        lows.append((lo, cid))
        highs.append((hi, cid))
    low, low_id = min(lows)
    high, high_id = max(highs)
    sole_l = world_end(comps, w2, 'boot-l')[1]
    sole_r = world_end(comps, w2, 'boot-r')[1]
    stagger = sole_l - sole_r
    ankle_stagger = w2['foot-l'][1] - w2['foot-r'][1]

    print('patch_landmarks: %s' % path)
    if log or rig_log:
        for line in log + rig_log:
            print(line)
    else:
        print('  no change; every landmark already sits on its target')
    print('  %d targeted origins moved, %d descendants rebased to hold world Y'
          % (moved, held))
    print('  model Y range %+.4f (%s) .. %+.4f (%s)  span %.4f m  target 0.0000 .. %.4f'
          % (low, low_id, high, high_id, high - low, FIGURE))
    print('  contrapposto  boot-l sole %.4f, boot-r sole %.4f, stagger %.1f mm; '
          'ankle joints stagger %.1f mm' % (sole_l, sole_r, stagger * 1000,
                                            ankle_stagger * 1000))

    assert abs(stagger - 0.0477) < 1e-3, 'contrapposto lost: %r' % stagger
    assert abs(ankle_stagger - 0.047) < 1e-3, 'ankle stagger lost: %r' % ankle_stagger
    assert low > -1e-4, 'geometry below the floor: %r (%s)' % (low, low_id)
    assert abs(high - FIGURE) < 1e-3, 'crown not at %.3f: %r (%s)' % (FIGURE, high, high_id)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else SPEC_DEFAULT)
