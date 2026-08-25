"""The scoreboard: measure a render turnaround against the artist's own.

    python tools/compare.py --tag r1
    python tools/compare.py --tag r1 --renders out/views --views 2,5
    python tools/compare.py --tag r1 --pin      # force the known-good view map
    python tools/compare.py --tag r1 --refit    # re-solve the view map from IoU
    python tools/compare.py --ceiling           # what the mattes allow at best
    python tools/compare.py --selftest          # validate the tool itself

Reads ``out/views/render_yaw<deg>.png`` or ``preview_yaw<deg>.png`` (RGBA,
transparent background) and ``ref/views/clay_{0..5}.png`` / ``body_{0..5}.png``,
pairs each render with its reference panel, normalises the two cameras onto a
common canvas and reports *where* the render is wrong.

The pairing is PINNED from docs/HANDEDNESS.md by default, not fitted: silhouette
IoU cannot see the pistol or the tattoos, and on this character yaw 0 scores the
same against the front panel and the back panel.  The IoU fit is still computed
every run and any disagreement is reported.

Outputs
    out/view_map.json      render -> panel assignment, reused unless --refit
    out/metrics_<tag>.json every number below, machine readable
    out/compare_<tag>.png  ref | render | overlay | width profile, per view
    out/profiles_<tag>.png width profiles, all views, larger

See docs/SCOREBOARD.md for what the single `score` is made of and for the
ceiling the reference mattes put on IoU.
"""
import argparse
import glob
import json
import os
import re
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silhouette as S                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_H = S.FIG_H

# docs/PART_CONTRACT.md: "index 2 is the front".  Used only as a cross-check on
# the fitted mapping -- the contract also says the exact yaw per index must be
# measured, not assumed, so this never constrains the fit.
FRONT_PANEL = 2

# docs/HANDEDNESS.md, established from features rather than silhouettes: the
# pistol is visible in body_0 and absent in body_4, the tattoos the other way
# round, and body_2 is the front.  Note this is NOT a uniform rotation -- five
# views sweep around the front and a back view is appended -- which is why both
# the free and the order-preserving fits fight it.  Silhouette IoU genuinely
# cannot resolve it: with the arms down, yaw 0 scores about 0.80 against the
# front panel and against the back panel alike.
PINNED_PANEL_YAW = {0: 90.0, 1: 45.0, 2: 0.0, 3: 315.0, 4: 270.0, 5: 180.0}

# Yaws that look at mirror-image sides of the figure.  y pairs with 360-y; 0 and
# 180 are their own mirrors and carry no lateral information.
def mirror_yaw(y):
    return None if y is None else (360.0 - (y % 360.0)) % 360.0


MIRROR_GAP_ALARM = 0.08     # IoU gap between two mirrored views
MIRROR_DE_ALARM = 6.0       # Lab dE gap between the same two views
SELF_MIRROR_ALARM = 0.06    # how far self-symmetry may drift from the sculpt's
STAGGER_ALARM = 1.0         # %H of stance-stagger error worth naming

# Figure height in metres, so stance numbers can be quoted in mm like the spec.
FIG_M = 1.72

# Which part owns the silhouette at a given height, so a width finding names a
# file instead of a number.  Boundaries are spec/jinx.json landmarks / 1.72 m.
PARTS = [
    (0.860, 1.001, "head/hair"),
    (0.815, 0.860, "neck/choker"),
    (0.755, 0.815, "shoulder/top"),
    (0.690, 0.755, "midriff (body)"),
    (0.585, 0.690, "hips/sash/belts"),
    (0.460, 0.585, "thigh (pants)"),
    (0.330, 0.460, "knee (pants)"),
    (0.280, 0.330, "pant hem"),
    (0.170, 0.280, "calf (boots/pants)"),
    (0.000, 0.170, "boots"),
]

# Colour bands.  Order is priority: a pixel joins the first region it matches,
# so the blue hair mass is taken out before "head" claims the whole skull.
# "core" is the widest run of the reference row, i.e. the body without its
# lateral appendages; "blue" is measured on the *reference*, never the render,
# so a render whose hair came out grey still gets scored inside the hair band.
COLOUR_REGIONS = [
    ("hair_mass", 0.830, 1.001, "blue"),
    ("head",      0.865, 1.001, "core"),
    ("neck",      0.815, 0.865, "any"),
    ("chest_top", 0.755, 0.815, "core"),
    ("midriff",   0.690, 0.755, "core"),
    ("hips_sash", 0.585, 0.690, "core"),
    ("thighs",    0.460, 0.585, "core"),
    ("knees",     0.330, 0.460, "core"),
    ("calves",    0.195, 0.330, "core"),
    ("boots",     0.000, 0.195, "any"),
    ("braids",    0.000, 0.830, "blue"),
    ("arms",      0.440, 0.830, "any"),
]

# Score weights.  Rationale lives in docs/SCOREBOARD.md; change both together.
WEIGHTS = {"shape": 0.30, "edge": 0.15, "chamfer": 0.10,
           "width": 0.20, "landmark": 0.15, "colour": 0.10}
K_WIDTH = 2.0      # width rms in %H that costs a factor e
K_LAND = 1.5       # landmark rms in %H that costs a factor e
K_CHAM = 1.0       # chamfer in %H at which the term is 1/2
K_COLOUR = 15.0    # mean Lab dE that costs a factor e
EDGE_TOL_FOR_SCORE = "8"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def jsonify(o):
    if isinstance(o, dict):
        return {str(k): jsonify(v) for k, v in o.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(o, (list, tuple)):
        return [jsonify(v) for v in o]
    if isinstance(o, np.ndarray):
        return [jsonify(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        v = float(o)
        return None if not np.isfinite(v) else round(v, 5)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def part_at(t):
    t = min(0.9999, max(0.0, float(t)))
    for lo, hi, name in PARTS:
        if lo <= t < hi:
            return name
    return "?"


def fmt(x, n=3, w=0):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-".rjust(w)
    return ("%.*f" % (n, x)).rjust(w)


def load_spec():
    p = os.path.join(ROOT, "spec", "jinx.json")
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

YAW_RE = re.compile(r"yaw\s*(-?\d+(?:\.\d+)?)", re.I)


def find_renders(dirpath):
    """Every turnaround image in a directory, keyed on its yaw.

    ``tools/render.mjs`` writes ``render_yaw<deg>.png`` and ``tools/preview.ts``
    writes ``preview_yaw<deg>.png``; both are valid and their silhouettes agree
    to about 0.99 IoU, so the yaw number is the identity and the prefix is not.
    If a directory holds both spellings of the same yaw, the ``render_`` one
    wins and the duplicate is reported rather than silently scored twice.
    """
    if not os.path.isdir(dirpath):
        return []
    files = sorted(glob.glob(os.path.join(dirpath, "render_yaw*.png")) +
                   glob.glob(os.path.join(dirpath, "preview_yaw*.png")))
    if not files:
        files = sorted(glob.glob(os.path.join(dirpath, "*.png")))
    out, dupes = [], []
    by_yaw = {}
    for f in files:
        base = os.path.basename(f)
        m = YAW_RE.search(base)
        yaw = float(m.group(1)) % 360.0 if m else None
        rec = {"file": f, "name": base, "yaw": yaw,
               "rank": 0 if base.startswith("render_") else 1}
        if yaw is None:
            out.append(rec)
            continue
        prev = by_yaw.get(yaw)
        if prev is None:
            by_yaw[yaw] = rec
        elif rec["rank"] < prev["rank"]:
            by_yaw[yaw] = rec
            dupes.append(prev["name"])
        else:
            dupes.append(base)
    out.extend(by_yaw.values())
    out.sort(key=lambda r: (r["yaw"] is None, r["yaw"] if r["yaw"] is not None else 0,
                            r["name"]))
    return out, sorted(dupes)


def load_pinned(path=None):
    """Panel index -> camera yaw, from a file or from PINNED_PANEL_YAW.

    Accepted file shapes:
      {"pairs": [{"panel": 0, "yaw": 90, ...}, ...]}   <- out/view_map_pinned.json
      {"panel_yaw": {"0": 90, ...}}
      {"0": 90, "1": 45, ...}

    A pinned map fixes only *which* render belongs to *which* panel.  The IoU
    beside it is still measured on this run, so a pin can never launder a bad
    render into a good number -- which is also why a null IoU in the file is
    ignored rather than copied through.  Renders are resolved by yaw, not by
    filename, so a file written for preview_yaw*.png also pins render_yaw*.png.
    """
    if path is None:
        return dict(PINNED_PANEL_YAW), "built-in (docs/HANDEDNESS.md)"
    with open(path) as f:
        raw = json.load(f)
    out = {}
    if isinstance(raw, dict) and isinstance(raw.get("pairs"), list):
        for p in raw["pairs"]:
            y = p.get("yaw")
            if y is None:
                m = YAW_RE.search(str(p.get("render", "")))
                y = float(m.group(1)) if m else None
            if y is not None and p.get("panel") is not None:
                out[int(p["panel"])] = float(y) % 360.0
    else:
        src = raw.get("panel_yaw", raw) if isinstance(raw, dict) else {}
        for k, v in src.items():
            try:
                out[int(k)] = float(v) % 360.0
            except (TypeError, ValueError):
                continue
    if not out:
        raise ValueError("no usable panel->yaw pairs in %s" % path)
    return out, os.path.relpath(path, ROOT)


def find_panels(dirpath, tag="clay"):
    out = []
    for f in sorted(glob.glob(os.path.join(dirpath, "%s_*.png" % tag))):
        m = re.search(r"_(\d+)\.png$", os.path.basename(f))
        if m:
            out.append({"file": f, "name": os.path.basename(f),
                        "index": int(m.group(1))})
    out.sort(key=lambda p: p["index"])
    return out


def prep(path, want_rgb=True):
    """Load, clean and normalise one silhouette onto the shared canvas."""
    bgr, alpha = S.load_rgba(path)
    mask, info = S.clean_mask(alpha)
    if not mask.any():
        return None, info
    n = S.normalize(mask, bgr if want_rgb else None)
    if n is None:
        return None, info
    n["matte"] = info
    n["path"] = path
    st = S.row_stats(n["mask"])
    n["stats"] = st
    dst, dmask = S.debraid_stats(n["mask"], st, braid_px=0.042 * FIG_H)
    n["debraid"] = dmask
    n["debraid_stats"] = dst
    return n, info


# --------------------------------------------------------------------------
# view assignment
# --------------------------------------------------------------------------

def cyclic_assignment(mat):
    """Best matching that keeps turnaround order.  Rows must be yaw-sorted.

    A turnaround walks around the model once, so the map from yaw order to
    panel order has to advance consistently: it may start at any panel and run
    either way round, but it may not jump about.  A free assignment happily
    produces an order no camera could have taken -- which is exactly what
    happens while the model is still a featureless blockout and every
    silhouette scores about the same.  Extra renders (a 45-degree sweep against
    a 60-degree turnaround) are skipped rather than forced onto a panel.

    Returns (pairs, n_matched, total_iou).  O(2 * P * R * P), i.e. nothing.
    """
    R, P = mat.shape
    if R == 0 or P == 0:
        return [], 0, 0.0
    best = None
    for direction in (1, -1):
        for off in range(P):
            order = [(off + direction * j) % P for j in range(P)]
            dp = [[(0, 0.0)] * (P + 1) for _ in range(R + 1)]
            bk = [[0] * (P + 1) for _ in range(R + 1)]
            for i in range(1, R + 1):
                for j in range(1, P + 1):
                    cand, src = dp[i - 1][j], 1            # skip this render
                    if dp[i][j - 1] > cand:
                        cand, src = dp[i][j - 1], 2        # skip this panel
                    take = (dp[i - 1][j - 1][0] + 1,
                            dp[i - 1][j - 1][1] + float(mat[i - 1, order[j - 1]]))
                    if take > cand:
                        cand, src = take, 3
                    dp[i][j], bk[i][j] = cand, src
            score = dp[R][P]
            if best is None or score > best[0]:
                pairs, i, j = [], R, P
                while i > 0 and j > 0:
                    s = bk[i][j]
                    if s == 3:
                        pairs.append((i - 1, order[j - 1]))
                        i, j = i - 1, j - 1
                    elif s == 2:
                        j -= 1
                    else:
                        i -= 1
                best = (score, sorted(pairs))
    (n, tot), pairs = best
    return pairs, n, tot


def fit_assignment(renders, panels, max_shift):
    """Score every (render, panel) pair both ways round and pick one-to-one.

    The reference panel angles are unknown, the render yaws are known, so the
    mapping has to be measured.  It is measured twice -- as rendered and
    mirrored -- because if the mirrored turnaround fits better then the model's
    handedness is inverted, and that is a bug in the model that a per-view IoU
    would quietly average away.
    """
    nr, np_ = len(renders), len(panels)
    normal = np.zeros((nr, np_))
    mirror = np.zeros((nr, np_))
    off = {}
    for i, r in enumerate(renders):
        rm = r["norm"]["mask"]
        rf = np.ascontiguousarray(rm[:, ::-1])
        for j, p in enumerate(panels):
            pm = p["norm"]["mask"]
            dx, dy, v = S.coarse_fit(pm, rm, max_shift)
            normal[i, j] = v
            off[(i, j, 0)] = (dx, dy)
            dx, dy, v = S.coarse_fit(pm, rf, max_shift)
            mirror[i, j] = v
            off[(i, j, 1)] = (dx, dy)

    def solve(mat):
        pick = S.hungarian(-mat)
        prs = [(i, pick[i]) for i in range(nr) if pick[i] >= 0]
        tot = sum(mat[i, j] for i, j in prs)
        return prs, tot

    free_n, tot_n = solve(normal)
    free_m, tot_m = solve(mirror)
    ordered = all(r["yaw"] is not None for r in renders)
    cyc_n = cyclic_assignment(normal) if ordered else (free_n, len(free_n), tot_n)
    cyc_m = cyclic_assignment(mirror) if ordered else (free_m, len(free_m), tot_m)
    return {
        "normal": normal, "mirror": mirror, "offsets": off, "ordered": ordered,
        "free_normal": free_n, "free_mirror": free_m,
        "free_mean_normal": tot_n / max(1, len(free_n)),
        "free_mean_mirror": tot_m / max(1, len(free_m)),
        "cyclic_normal": cyc_n[0], "cyclic_mirror": cyc_m[0],
        "cyclic_mean_normal": cyc_n[2] / max(1, cyc_n[1]),
        "cyclic_mean_mirror": cyc_m[2] / max(1, cyc_m[1]),
    }


# --------------------------------------------------------------------------
# per-view geometry metrics
# --------------------------------------------------------------------------

def ground_stagger(mask, band=0.15, min_run=0.030, axial=True):
    """Height of the lowest pixel each side of the midline, and the difference.

    She does not stand square: in clay_2 one foot sits 2.74 %H above the other,
    so the bottom of the silhouette is a *single* run belonging to the lower
    boot.  Reading that as "the reference's boots are merged" is wrong -- there
    is only one foot down there -- and this measure exists because that misread
    cost a round.

    Measured on runs at least ``min_run`` of the figure height wide, so a braid
    tip (about 1.7 %H) can never be mistaken for a sole (about 6 %H).  Sides are
    reported relative to whichever foot is on the floor, which makes the pair
    immune to the residual alignment shift applied to the render.

    Sign follows docs/HANDEDNESS.md: +X is her LEFT and lands image-RIGHT in a
    front view, so a NEGATIVE stagger means her left foot is the raised one.

    Only meaningful in the front and back views: obliquely, "each side of the
    midline" mixes the lateral split with depth, so ``axial`` is carried through
    to the report rather than letting an oblique row read as a measurement.
    """
    if mask is None or not mask.any():
        return {"valid": False, "why": "empty silhouette"}
    sr, sc, ec = S.runs_of(mask)
    if sr.size == 0:
        return {"valid": False, "why": "empty silhouette"}
    wide = (ec - sc) >= min_run * FIG_H
    if not wide.any():
        return {"valid": False, "why": "no run wide enough to be a sole"}

    # Keep whole connected pieces that contain a sole-width run, rather than
    # only the wide rows themselves: a boot narrows to a few pixels at its toe,
    # and filtering row by row clipped that tip and cost a pixel of stagger.
    n, lab, _, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    mid = ((sc[wide] + ec[wide]) // 2).astype(np.int64)
    keep = np.zeros(n, bool)
    keep[np.unique(lab[sr[wide], mid])] = True
    keep[0] = False
    solid = keep[lab]
    if not solid.any():
        return {"valid": False, "why": "no piece wide enough to be a foot"}

    rows, x0, x1 = sr[wide], sc[wide], ec[wide]
    tw = S.T_ROWS[rows]
    floor_band = tw < (tw.min() + band)
    if not floor_band.any():
        return {"valid": False, "why": "no foot-level pixels"}
    cx = float(np.average(0.5 * (x0[floor_band] + x1[floor_band]),
                          weights=(x1 - x0)[floor_band]))

    ys, xs = np.nonzero(solid)
    t = S.T_ROWS[ys]
    left, right = xs < cx, xs > cx
    if not left.any() or not right.any():
        return {"valid": False, "why": "silhouette does not straddle its midline"}
    tl, tr = float(t[left].min()), float(t[right].min())
    base = min(tl, tr)
    if max(tl, tr) - base > 0.08:
        return {"valid": False,
                "why": "sides differ by more than a stance could (%.1f%%H)"
                       % (100 * (max(tl, tr) - base))}
    d = tl - tr
    return {
        "valid": True, "axial": bool(axial), "midline_x": cx,
        "t_low_image_left": tl - base, "t_low_image_right": tr - base,
        "stagger_pct": 100.0 * d,
        "stagger_mm": 1000.0 * d * FIG_M,
        "higher_side": ("her left (image-right)" if d < 0 else
                        "her right (image-left)" if d > 0 else "level"),
        "t_high_sole": max(tl, tr),
    }


def components_of(mask):
    """Disconnected pieces of a silhouette, biggest first, in canvas terms.

    A shell that floats free of the body -- a boot sole detached from the leg,
    a braid that never reaches the head -- is invisible in IoU but obvious
    here, and it is nearly always a build bug rather than a shape error.
    """
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        a = int(st[i, cv2.CC_STAT_AREA])
        y0 = int(st[i, cv2.CC_STAT_TOP])
        y1 = y0 + int(st[i, cv2.CC_STAT_HEIGHT])
        out.append({"area_px": a,
                    "area_frac": a / max(1, int(mask.sum())),
                    "t_top": float(S.T_ROWS[max(0, y0)]),
                    "t_bottom": float(S.T_ROWS[min(S.CANVAS_H - 1, y1 - 1)])})
    out.sort(key=lambda c: -c["area_px"])
    return out[:8]


def profile_delta(pr_ref, pr_ren, nbands):
    """Signed width difference per band, as %H and as % of the ref width."""
    t = S.band_centres(nbands)
    out = []
    for k in range(nbands):
        row = {"t": float(t[k]), "part": part_at(float(t[k]))}
        for key in ("full", "core", "sum"):
            a, b = float(pr_ref[key][k]), float(pr_ren[key][k])
            d = b - a
            row[key] = {
                "ref_pct": 100.0 * a / FIG_H,
                "render_pct": 100.0 * b / FIG_H,
                "d_pct": 100.0 * d / FIG_H,
                "d_rel_pct": (100.0 * d / a) if a > 4.0 else None,
            }
        row["nrun_ref"] = float(pr_ref["nrun"][k])
        row["nrun_render"] = float(pr_ren["nrun"][k])
        out.append(row)
    return out


def rms_of(bands, key="core", field="d_pct", tmin=0.0, tmax=1.0):
    v = [b[key][field] for b in bands
         if b[key][field] is not None and tmin <= b["t"] <= tmax
         and (b[key]["ref_pct"] > 0.4 or b[key]["render_pct"] > 0.4)]
    if not v:
        return None
    return float(np.sqrt(np.mean(np.square(v))))


def view_geometry(ref, ren, nbands, max_shift, axial=True):
    """Everything measurable from two normalised silhouettes."""
    dx, dy, _ = S.refine_offset(ref["mask"], ren["mask"], max_shift)
    m_ren = S.shift(ren["mask"], dx, dy)
    st_ren = S.row_stats(m_ren)
    dst_ren, dm_ren = S.debraid_stats(m_ren, st_ren, braid_px=0.042 * FIG_H)

    m_ref = ref["mask"]
    st_ref = ref["stats"]
    dm_ref, dst_ref = ref["debraid"], ref["debraid_stats"]

    out = {"align": {
        "scale_ref": ref["scale"], "scale_render": ren["scale"],
        "ref_src_size": ref["src_size"], "render_src_size": ren["src_size"],
        "aspect_ref": ref["aspect"], "aspect_render": ren["aspect"],
        "d_aspect_pct": 100.0 * (ren["aspect"] - ref["aspect"]) / ref["aspect"],
        "residual_dx_px": int(dx), "residual_dy_px": int(dy),
        "residual_dx_pct": 100.0 * dx / FIG_H,
        "residual_dy_pct": 100.0 * dy / FIG_H,
        "render_clipped": bool(ren["clipped"]),
    }}

    out["full"] = S.overlap_metrics(m_ref, m_ren)
    out["full"].update(S.contour_metrics(m_ref, m_ren))
    out["debraid"] = S.overlap_metrics(dm_ref, dm_ren)
    out["debraid"].update(S.contour_metrics(dm_ref, dm_ren))
    ar_f, ar_d = out["full"]["area_ref_px"], out["debraid"]["area_ref_px"]
    an_f, an_d = out["full"]["area_render_px"], out["debraid"]["area_render_px"]
    out["braid_area_frac_ref"] = (ar_f - ar_d) / ar_f if ar_f else 0.0
    out["braid_area_frac_render"] = (an_f - an_d) / an_f if an_f else 0.0
    out["components"] = {"ref": components_of(m_ref), "render": components_of(m_ren)}

    sm_ref, ax_ref = S.self_mirror_iou(m_ref)
    sm_ren, ax_ren = S.self_mirror_iou(m_ren)
    out["self_mirror"] = {
        "ref": sm_ref, "render": sm_ren,
        "delta": None if (sm_ref is None or sm_ren is None) else sm_ren - sm_ref,
        "axis_offset_ref_px": ax_ref, "axis_offset_render_px": ax_ren,
    }
    g_ref = ground_stagger(m_ref, axial=axial)
    g_ren = ground_stagger(m_ren, axial=axial)
    out["ground"] = {"ref": g_ref, "render": g_ren, "axial": bool(axial)}
    if g_ref.get("valid") and g_ren.get("valid"):
        out["ground"]["delta_pct"] = g_ren["stagger_pct"] - g_ref["stagger_pct"]
        out["ground"]["delta_mm"] = g_ren["stagger_mm"] - g_ref["stagger_mm"]

    pr_ref = S.width_profile(st_ref, nbands)
    pr_ren = S.width_profile(st_ren, nbands)
    out["profile"] = {"nbands": nbands,
                      "t": S.band_centres(nbands),
                      "ref": pr_ref, "render": pr_ren,
                      "bands": profile_delta(pr_ref, pr_ren, nbands)}
    out["width_rms_core_pct"] = rms_of(out["profile"]["bands"], "core")
    out["width_rms_full_pct"] = rms_of(out["profile"]["bands"], "full")
    out["width_bias_core_pct"] = float(np.mean(
        [b["core"]["d_pct"] for b in out["profile"]["bands"]]))

    lr = S.row_series(st_ref)
    ln = S.row_series(st_ren)
    lm_ref, fl_ref = S.landmarks(lr, S.row_series(dst_ref))
    lm_ren, fl_ren = S.landmarks(ln, S.row_series(dst_ren),
                                 window=dict(lm_ref, _w=0.10))
    lm_ref_full, _ = S.landmarks({"core": lr["full"], "full": lr["full"],
                                  "sum": lr["sum"], "nrun": lr["nrun"]},
                                 S.row_series(dst_ref))
    lm_ren_full, _ = S.landmarks({"core": ln["full"], "full": ln["full"],
                                  "sum": ln["sum"], "nrun": ln["nrun"]},
                                 S.row_series(dst_ren),
                                 window=dict(lm_ref_full, _w=0.10))
    out["landmarks"] = {}
    ds = []
    for k in S.LANDMARK_ORDER:
        a, b = lm_ref.get(k), lm_ren.get(k)
        af, bf = lm_ref_full.get(k), lm_ren_full.get(k)
        d = None if (a is None or b is None) else (b - a)
        # A landmark the reference itself could not resolve (its search clamped
        # on a window edge) is not ground truth, so it is reported but kept out
        # of the score.
        if d is not None and k != "sole" and not fl_ref.get(k, {}).get("at_edge"):
            ds.append(d)
        out["landmarks"][k] = {
            "ref": a, "render": b,
            "delta": d, "delta_pct": None if d is None else 100.0 * d,
            "ref_full": af, "render_full": bf,
            "delta_full_pct": None if (af is None or bf is None) else 100.0 * (bf - af),
            "ref_at_edge": fl_ref.get(k, {}).get("at_edge", False),
            "render_at_edge": fl_ren.get(k, {}).get("at_edge", False),
        }
    out["landmark_rms_pct"] = (float(np.sqrt(np.mean(np.square(ds))) * 100.0)
                               if len(ds) >= 3 else None)
    out["landmarks_scored"] = len(ds)
    out["_masks"] = {"ref": m_ref, "render": m_ren,
                     "ref_db": dm_ref, "render_db": dm_ren}
    out["_rgb"] = {
        "ref": ref.get("rgb"),
        "render": (None if ren.get("rgb") is None else
                   np.dstack([_shift_plane(ren["rgb"][:, :, c], dx, dy)
                              for c in range(3)])),
    }
    out["_shift"] = (dx, dy)
    return out


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------

def to_lab(bgr):
    return cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)


def circ_hue(a, b, w=None):
    """Chroma-weighted circular mean hue in degrees, 0 = +a* (red-ish)."""
    if a.size == 0:
        return None
    if w is None:
        w = np.sqrt(a * a + b * b)
    sw = w.sum()
    if sw <= 1e-6:
        return None
    return float(np.degrees(np.arctan2((w * b).sum() / sw, (w * a).sum() / sw)))


def build_colour_regions(mask, lab, st):
    """Cut the reference figure into named bands.

    Every predicate is evaluated on the *reference*, never on the render, so a
    render whose hair came out grey is still measured inside the hair band
    instead of quietly escaping into 'other'.
    """
    core = S.core_mask(mask, st)
    blue = (lab[:, :, 2] < -12.0) & (lab[:, :, 0] < 82.0) & mask
    t = S.T_ROWS[:, None]
    free = mask.copy()
    regions = {}
    for name, lo, hi, kind in COLOUR_REGIONS:
        band = (t >= lo) & (t < hi) & mask
        if kind == "core":
            sel = band & core
        elif kind == "blue":
            sel = band & blue
        else:
            sel = band
        sel = sel & free
        regions[name] = sel
        free &= ~sel
    regions["other"] = free
    return regions


def view_colour(body_path, ren_path, max_shift, mirror=False):
    """Lab difference inside the intersection, overall and per named band."""
    bref, iref = prep(body_path, want_rgb=True)
    bren, iren = prep(ren_path, want_rgb=True)
    if bref is None or bren is None:
        return None
    if mirror:
        bren["mask"] = np.ascontiguousarray(bren["mask"][:, ::-1])
        bren["rgb"] = np.ascontiguousarray(bren["rgb"][:, ::-1])
    dx, dy, _ = S.refine_offset(bref["mask"], bren["mask"], max_shift)
    m_ren = S.shift(bren["mask"], dx, dy)
    rgb_ren = np.dstack([_shift_plane(bren["rgb"][:, :, c], dx, dy) for c in range(3)])

    m_ref = bref["mask"]
    inter = m_ref & m_ren
    if inter.sum() < 500:
        return {"pixels": int(inter.sum()), "status": "intersection too small"}

    lab_ref = to_lab(bref["rgb"])
    lab_ren = to_lab(rgb_ren)
    d = lab_ren - lab_ref
    de = np.linalg.norm(d, axis=2)

    gl = float(d[:, :, 0][inter].mean())
    out = {
        "pixels": int(inter.sum()),
        "mean_dE": float(de[inter].mean()),
        "p90_dE": float(np.percentile(de[inter], 90)),
        "dL": gl,
        "da": float(d[:, :, 1][inter].mean()),
        "db": float(d[:, :, 2][inter].mean()),
        "hue_ref": circ_hue(lab_ref[:, :, 1][inter], lab_ref[:, :, 2][inter]),
        "hue_render": circ_hue(lab_ren[:, :, 1][inter], lab_ren[:, :, 2][inter]),
        "global_L_offset": gl,
        "regions": {},
        "align": {"dx": int(dx), "dy": int(dy)},
        "matte_ref": iref, "matte_render": iren,
    }
    out["hue_delta"] = (None if out["hue_ref"] is None or out["hue_render"] is None
                        else ((out["hue_render"] - out["hue_ref"] + 180) % 360) - 180)

    regions = build_colour_regions(m_ref, lab_ref, bref["stats"])
    for name, sel in regions.items():
        s = sel & inter
        n = int(s.sum())
        if n < 80:
            out["regions"][name] = {"pixels": n}
            continue
        ar, br = lab_ref[:, :, 1][s], lab_ref[:, :, 2][s]
        an, bn = lab_ren[:, :, 1][s], lab_ren[:, :, 2][s]
        hr, hn = circ_hue(ar, br), circ_hue(an, bn)
        out["regions"][name] = {
            "pixels": n,
            "dL": float(d[:, :, 0][s].mean()),
            "dL_rel": float(d[:, :, 0][s].mean() - gl),
            "da": float(d[:, :, 1][s].mean()),
            "db": float(d[:, :, 2][s].mean()),
            "dE": float(de[s].mean()),
            "L_ref": float(lab_ref[:, :, 0][s].mean()),
            "L_render": float(lab_ren[:, :, 0][s].mean()),
            "hue_ref": hr, "hue_render": hn,
            "hue_delta": (None if hr is None or hn is None
                          else ((hn - hr + 180) % 360) - 180),
        }
    return out


def _shift_plane(p, dx, dy):
    out = np.zeros_like(p)
    H, W = p.shape
    sy0, sy1 = max(0, -dy), min(H, H - dy)
    dy0, dy1 = max(0, dy), min(H, H + dy)
    sx0, sx1 = max(0, -dx), min(W, W - dx)
    dx0, dx1 = max(0, dx), min(W, W + dx)
    if sy1 > sy0 and sx1 > sx0:
        out[dy0:dy1, dx0:dx1] = p[sy0:sy1, sx0:sx1]
    return out


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

def mirror_pair_check(views):
    """Do the two sides of the figure agree with the two sides of the sculpt?

    Yaw y and 360-y look at mirror-image halves.  If the model's lateral
    features are on the correct sides, both should score about the same against
    their own panels; a large gap is the signature of a feature built on the
    wrong side, and it is invisible in the mean IoU because one view gains
    exactly what the other loses.

    Two extra columns separate the two ways of getting it wrong:

      sym_render  IoU of view a against view b mirrored -- how symmetric the
                  MODEL is between the pair.
      sym_ref     the same for the two reference panels -- how symmetric the
                  SCULPT is.

    A mirrored feature keeps the model as asymmetric as the sculpt, so
    sym_render stays close to sym_ref while the per-panel IoUs diverge.  A
    feature that is simply missing makes the model more symmetric than the
    sculpt, so sym_render climbs well above sym_ref.
    """
    by_yaw = {v["yaw"]: v for v in views if v["yaw"] is not None}
    out, seen = [], set()
    for y, va in sorted(by_yaw.items()):
        m = mirror_yaw(y)
        if m is None or m == y or m not in by_yaw:
            continue                    # 0 and 180 are their own mirrors
        key = tuple(sorted((y, m)))
        if key in seen:
            continue
        seen.add(key)
        vb = by_yaw[m]
        ma, mb = va["geometry"]["_masks"], vb["geometry"]["_masks"]
        fa = np.ascontiguousarray(mb["render"][:, ::-1])
        fr = np.ascontiguousarray(mb["ref"][:, ::-1])
        sym_render = S.refine_offset(ma["render"], fa, 40)[2]
        sym_ref = S.refine_offset(ma["ref"], fr, 40)[2]
        ia = va["geometry"]["full"]["iou"]
        ib = vb["geometry"]["full"]["iou"]
        gap = abs(ia - ib)

        # THE TRAP.  y and 360-y are mirror viewpoints, but when y is 90 the
        # partner is also y+180 -- the *opposite* direction.  Under the
        # orthographic camera this project renders with, the silhouette along
        # -d is exactly the mirror of the silhouette along +d for any solid
        # whatever, because a shadow does not depend on which side you stand.
        # So sym_render is identically 1 and cannot discriminate.  Measured on
        # this build: 0.997 at every one of yaw 0, 45, 90 and 135.  It was
        # reported as evidence twice before this was caught; it is now printed
        # as a constant and excluded from every verdict.
        opposite = abs(((va["yaw"] - vb["yaw"] - 180.0) % 360.0)) < 1e-6 or \
            abs(((vb["yaw"] - va["yaw"] - 180.0) % 360.0)) < 1e-6

        # Tattoos, sash colour and arm bands are lateral features that live only
        # in the texture, so the same test is run on colour.  Without it a
        # mirrored tattoo is invisible: the silhouette is identical either way.
        ca = (va.get("colour") or {}) if isinstance(va.get("colour"), dict) else {}
        cb = (vb.get("colour") or {}) if isinstance(vb.get("colour"), dict) else {}
        dea, deb = ca.get("mean_dE"), cb.get("mean_dE")
        de_gap = None if (dea is None or deb is None) else abs(dea - deb)
        worst_region = None
        ra, rb = ca.get("regions") or {}, cb.get("regions") or {}
        for name in ra:
            x, y = ra.get(name) or {}, rb.get(name) or {}
            if x.get("dE") is None or y.get("dE") is None:
                continue
            if min(x.get("pixels", 0), y.get("pixels", 0)) < 400:
                continue
            d = abs(x["dE"] - y["dE"])
            if worst_region is None or d > worst_region["gap"]:
                worst_region = {"region": name, "gap": d,
                                "dE_a": x["dE"], "dE_b": y["dE"]}

        if gap <= MIRROR_GAP_ALARM:
            dx = "ok"
        elif opposite:
            # The two panels are genuinely different shapes (clay_0 vs
            # flip(clay_4) is only 0.65), and one orthographic render can only
            # equal one of them, so the gap is real -- it just says the sculpt's
            # pose is asymmetric, not that a feature is on the wrong side.
            dx = "sculpt's pose is asymmetric; one silhouette cannot fit both"
        elif sym_render - sym_ref < 0.05:
            dx = "lateral feature on the WRONG SIDE"
        else:
            dx = "lateral feature too weak on one side"
        out.append({
            "yaw_a": va["yaw"], "panel_a": va["panel"], "iou_a": ia,
            "yaw_b": vb["yaw"], "panel_b": vb["panel"], "iou_b": ib,
            "gap": gap,
            "worse_side": va["yaw"] if ia < ib else vb["yaw"],
            "sym_render": float(sym_render), "sym_ref": float(sym_ref),
            "opposite_views": bool(opposite),
            "sym_render_discriminating": bool(not opposite),
            "sym_render_note": (
                "constant by construction: orthographic projection makes the "
                "yaw %d and yaw %d silhouettes exact mirrors for ANY object"
                % (va["yaw"], vb["yaw"]) if opposite else None),
            "suspect": bool(gap > MIRROR_GAP_ALARM),
            "diagnosis": dx,
            "dE_a": dea, "dE_b": deb, "dE_gap": de_gap,
            "colour_suspect": bool(de_gap is not None and de_gap > MIRROR_DE_ALARM),
            "worst_colour_region": worst_region,
        })
    return out


def view_score(g, c):
    """Per-view 0..100.  A term that could not be measured is dropped and its
    weight shared out, rather than scored as zero -- otherwise a missing colour
    target or an undetectable landmark would read as a modelling failure."""
    ef = g["full"].get("edge_f", {}).get(EDGE_TOL_FOR_SCORE)
    cham = g["full"].get("chamfer_pct")
    wr = g.get("width_rms_core_pct")
    lr = g.get("landmark_rms_pct")
    de = c.get("mean_dE") if c else None
    terms = {
        "shape": 0.5 * g["full"]["iou"] + 0.5 * g["debraid"]["iou"],
        "edge": ef["f"] if ef else None,
        "chamfer": None if cham is None else 1.0 / (1.0 + cham / K_CHAM),
        "width": None if wr is None else float(np.exp(-wr / K_WIDTH)),
        "landmark": None if lr is None else float(np.exp(-lr / K_LAND)),
        "colour": None if de is None else float(np.exp(-de / K_COLOUR)),
    }
    live = {k: v for k, v in terms.items() if v is not None}
    w = {k: WEIGHTS[k] for k in live}
    tot = sum(w.values()) or 1.0
    w = {k: v / tot for k, v in w.items()}
    return {"score": 100.0 * sum(w[k] * live[k] for k in w),
            "terms": terms, "weights": w}


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------

BG = (24, 24, 28)
FG = (215, 215, 220)
GREEN = (90, 220, 90)
RED = (80, 80, 245)
YELLOW = (60, 225, 235)
BLUE = (235, 170, 70)


def put(img, text, x, y, col=FG, sc=0.40, th=1):
    cv2.putText(img, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, sc, col, th,
                cv2.LINE_AA)


def tile_of(mask, w, h, col=(210, 210, 215)):
    v = np.zeros((S.CANVAS_H, S.CANVAS_W, 3), np.uint8)
    v[mask] = col
    return cv2.resize(v, (w, h), interpolation=cv2.INTER_AREA)


def tile_rgb(rgb, mask, w, h):
    v = np.full((S.CANVAS_H, S.CANVAS_W, 3), 40, np.uint8)
    v[mask] = rgb[mask]
    return cv2.resize(v, (w, h), interpolation=cv2.INTER_AREA)


def tile_overlay(ref, ren, w, h):
    v = np.zeros((S.CANVAS_H, S.CANVAS_W, 3), np.uint8)
    v[ref & ~ren] = GREEN
    v[ren & ~ref] = RED
    v[ref & ren] = (70, 150, 155)
    return cv2.resize(v, (w, h), interpolation=cv2.INTER_AREA)


def draw_ribbon(bands, w, h, key="core", label="core", show_axis=True):
    """Half-width ribbons around a shared centre line: shape you can read."""
    img = np.full((h, w), 0, np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img[:] = (18, 18, 22)
    mx = 1.0
    for b in bands:
        mx = max(mx, b[key]["ref_pct"], b[key]["render_pct"])
    sc = (0.86 * w) / max(mx, 1e-6)
    cx = w // 2

    def yof(t):
        return int(round((h - 12) - t * (h - 24)))

    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = yof(t)
        cv2.line(img, (0, y), (w, y), (48, 48, 54), 1)
        if show_axis:
            put(img, "%.2f" % t, 2, y - 2, (110, 110, 118), 0.32)
    cv2.line(img, (cx, 0), (cx, h), (48, 48, 54), 1)

    def poly(field, colour, thick):
        pts_l, pts_r = [], []
        for b in bands:
            y = yof(b["t"])
            half = 0.5 * b[key][field] * sc
            pts_l.append((int(cx - half), y))
            pts_r.append((int(cx + half), y))
        for pts in (pts_l, pts_r):
            cv2.polylines(img, [np.array(pts, np.int32)], False, colour, thick,
                          cv2.LINE_AA)

    # shade the disagreement first so the outlines stay on top
    for b in bands:
        y = yof(b["t"])
        a = 0.5 * b[key]["ref_pct"] * sc
        c = 0.5 * b[key]["render_pct"] * sc
        lo, hi = sorted((a, c))
        col = (60, 60, 120) if c > a else (60, 100, 60)
        cv2.line(img, (int(cx + lo), y), (int(cx + hi), y), col, 4)
        cv2.line(img, (int(cx - hi), y), (int(cx - lo), y), col, 4)
    poly("ref_pct", GREEN, 1)
    poly("render_pct", RED, 1)
    put(img, label, max(4, w - 8 * len(label) - 6), 12, (150, 150, 160), 0.36)
    return img


def draw_delta_strip(bands, w, h, key="core"):
    img = np.full((h, w, 3), (18, 18, 22), np.uint8)
    cx = w // 2
    mx = max(1e-6, max(abs(b[key]["d_pct"]) for b in bands))
    mx = max(mx, 0.5)
    sc = (0.45 * w) / mx

    def yof(t):
        return int(round((h - 12) - t * (h - 24)))

    cv2.line(img, (cx, 0), (cx, h), (70, 70, 78), 1)
    for b in bands:
        y = yof(b["t"])
        d = b[key]["d_pct"] * sc
        col = RED if b[key]["d_pct"] > 0 else BLUE
        cv2.line(img, (cx, y), (int(cx + d), y), col, 3)
    put(img, "d%%H +-%.1f" % mx, 3, 11, (140, 140, 150), 0.33)
    return img


def contact_sheet(views, tag, header):
    tw, th = 230, 360
    pw = 300
    rowh = th + 26
    W = tw * 3 + 18 + pw + 12
    H = 40 + rowh * max(1, len(views))
    img = np.full((H, W, 3), BG, np.uint8)
    put(img, header, 8, 24, (240, 240, 245), 0.5)
    for i, v in enumerate(views):
        y = 40 + i * rowh
        g = v["geometry"]
        m = g["_masks"]
        cap = ("%-16s yaw %s -> %s   IoU %.3f  db %.3f  P %.3f R %.3f  cham %.2f%%"
               % (v["render"][:16], fmt_yaw(v["yaw"]), v["panel_name"],
                  g["full"]["iou"], g["debraid"]["iou"], g["full"]["precision"],
                  g["full"]["recall"], g["full"]["chamfer_pct"] or 0.0))
        put(img, cap, 8, y + 16, (225, 225, 230), 0.42)
        yy = y + 22
        x = 8
        rgb = g.get("_rgb") or {}

        def shown(which, col):
            if rgb.get(which) is not None:
                return tile_rgb(rgb[which], m[which], tw, th)
            return tile_of(m[which], tw, th, col)

        for tile, name in ((shown("ref", (200, 200, 205)), "reference"),
                           (shown("render", (200, 160, 160)), "render"),
                           (tile_overlay(m["ref"], m["render"], tw, th), "overlay")):
            img[yy:yy + th, x:x + tw] = tile
            put(img, name, x + 4, yy + 12, (150, 150, 158), 0.35)
            x += tw + 6
        rib = draw_ribbon(g["profile"]["bands"], pw - 90, th, "core", "core width")
        img[yy:yy + th, x:x + pw - 90] = rib
        img[yy:yy + th, x + pw - 90:x + pw] = draw_delta_strip(
            g["profile"]["bands"], 90, th, "core")
    put(img, "green = reference only   red = render only   teal = agreement",
        8, H - 8, (140, 140, 150), 0.38)
    return img


def profiles_sheet(views, tag):
    pw, ph = 240, 660
    sw = 130
    W = max(1, len(views)) * (pw + sw + 10) + 10
    H = ph + 60
    img = np.full((H, W, 3), BG, np.uint8)
    put(img, "width profiles  tag=%s   green = reference, red = render, "
             "bars = render - reference (%% of figure height)" % tag,
        8, 22, (240, 240, 245), 0.45)
    for i, v in enumerate(views):
        x = 10 + i * (pw + sw + 10)
        g = v["geometry"]
        put(img, "%s -> %s" % (fmt_yaw(v["yaw"]), v["panel_name"]), x + 4, 42,
            (220, 220, 228), 0.42)
        img[50:50 + ph, x:x + pw] = draw_ribbon(g["profile"]["bands"], pw, ph,
                                                "core", "core (largest run)")
        img[50:50 + ph, x + pw + 2:x + pw + 2 + sw] = draw_delta_strip(
            g["profile"]["bands"], sw, ph, "core")
    return img


def fmt_yaw(y):
    return "  ?" if y is None else "%3d" % int(round(y))


# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------

def hr(c="="):
    print(c * 100)


def is_axial(yaw):
    """Front or back -- the two views where left-right symmetry means something."""
    return yaw is not None and (round(yaw) % 180 == 0)


def blind_spots(res):
    """Every quantity this run is structurally incapable of measuring.

    Both bugs the verifier found had the same shape: a number that looked like a
    measurement but could only ever come out one way.  Rather than trusting
    reviewers to remember which those are, the tool states them.
    """
    out = []
    mp = res.get("mirror_pairs") or []
    opp = [m for m in mp if m.get("opposite_views")]
    if opp:
        out.append(("mirror-pair symMdl",
                    "constant ~0.997 for %s: orthographic projection makes yaw y and"
                    " y+180 exact mirrors for any object. Excluded from verdicts."
                    % ", ".join("%d/%d" % (m["yaw_a"], m["yaw_b"]) for m in opp)))
    if not [v for v in res["views"] if is_axial(v["yaw"])]:
        out.append(("self-mirror symmetry",
                    "no front or back view scored; left-right symmetry is only"
                    " anatomically meaningful there."))
    ungrounded = [v for v in res["views"]
                  if not v["geometry"]["ground"]["ref"].get("valid")
                  or not v["geometry"]["ground"]["render"].get("valid")]
    if ungrounded:
        why = ", ".join(sorted({(v["geometry"]["ground"]["ref"].get("why")
                                 or v["geometry"]["ground"]["render"].get("why")
                                 or "?") for v in ungrounded}))
        out.append(("ground-contact stagger",
                    "unmeasurable in %d view(s) (%s)" % (len(ungrounded), why)))
    oblique = [v for v in res["views"] if not is_axial(v["yaw"])
               and v["geometry"]["ground"]["ref"].get("valid")]
    if oblique:
        out.append(("ground stagger, oblique",
                    "%d view(s) marked '~': off-axis the left/right split mixes in"
                    " depth, so only the front and back rows are load-bearing."
                    % len(oblique)))
    nocrotch = [v for v in res["views"]
                if v["geometry"]["landmarks"]["crotch"]["ref"] is None]
    if nocrotch:
        out.append(("crotch landmark",
                    "the legs never separate in %d view(s); reported as '-', not zero."
                    % len(nocrotch)))
    clamped = sum(1 for v in res["views"] for k, L in v["geometry"]["landmarks"].items()
                  if L.get("ref_at_edge"))
    if clamped:
        out.append(("landmarks marked '?'",
                    "%d reading(s) clamped on a search boundary; reported but kept out"
                    " of the score." % clamped))
    if not [v for v in res["views"] if (v.get("colour") or {}).get("mean_dE") is not None]:
        out.append(("colour",
                    "no usable body_* target; the colour weight is shared out rather"
                    " than scored as zero."))
    if res.get("coverage", 1.0) < 0.999:
        out.append(("unscored panels",
                    "%d of %d reference panels had no render; the score is a mean over"
                    " what was scored, so only compare like view sets."
                    % (int(round(len(res["views"]) / max(res["coverage"], 1e-9)))
                       - len(res["views"]),
                       int(round(len(res["views"]) / max(res["coverage"], 1e-9))))))
    return out


def print_self_mirror(res):
    """Is the model as left-right asymmetric as the sculpt?

    This is the test that replaced comparing yaw 90 with yaw 270.  Flipping one
    view against ITSELF has no projection degeneracy, so the number is about the
    object.  Only the front and back views are reported: a side view's
    left-right axis is the depth axis, where symmetry means nothing anatomical.
    """
    rows = [v for v in res["views"] if is_axial(v["yaw"])
            and v["geometry"]["self_mirror"]["ref"] is not None]
    if not rows:
        return
    print("\nSELF-MIRROR  (each view flipped about its own axis and matched to itself:")
    print("              1.000 = perfectly symmetric.  Front and back views only.)")
    print("  %-6s %-9s %9s %9s %8s   %s"
          % ("yaw", "panel", "reference", "render", "delta", "reading"))
    for v in rows:
        s = v["geometry"]["self_mirror"]
        d = s["delta"]
        if d > SELF_MIRROR_ALARM:
            note = "render TOO SYMMETRIC -- pose/lateral kit missing"
        elif d < -SELF_MIRROR_ALARM:
            note = "render MORE lopsided than the sculpt"
        else:
            note = "asymmetry budget about right"
        print("  %-6s %-9s %9.3f %9.3f %+8.3f   %s"
              % (fmt_yaw(v["yaw"]).strip(), v["panel_name"], s["ref"], s["render"],
                 d, note))
    worst = max(rows, key=lambda v: v["geometry"]["self_mirror"]["delta"])
    if worst["geometry"]["self_mirror"]["delta"] > SELF_MIRROR_ALARM:
        print("  The sculpt is asymmetric because of the contrapposto, the holstered")
        print("  Zapper, the low sash corner and the braids falling to one side. Closing")
        print("  this gap means building those, not widening anything.")
    print("  It measures the AMOUNT of asymmetry, never which side it is on -- for that")
    print("  read the per-panel IoUs and the colour dE gap above.")


def print_stance(res):
    """Ground contact, one line per view, both feet reported."""
    rows = [v for v in res["views"]
            if v["geometry"]["ground"]["ref"].get("valid")
            and v["geometry"]["ground"]["render"].get("valid")]
    if not rows:
        return
    print("\nGROUND CONTACT  (how far each foot sits above the lower one, %H of figure")
    print("                 height; stagger = image-left minus image-right, so NEGATIVE")
    print("                 means her LEFT foot -- image-right -- is the raised one)")
    print("  %-7s %-9s %15s %15s %17s"
          % ("yaw", "panel", "reference L/R", "render L/R", "stagger ref/ren"))
    for v in rows:
        g = v["geometry"]["ground"]
        a, b = g["ref"], g["render"]
        ax = is_axial(v["yaw"])
        print("  %-7s %-9s %6.2f /%6.2f %6.2f /%6.2f %7.2f /%7.2f  d %+.2f%%H (%+.0f mm)"
              % (fmt_yaw(v["yaw"]).strip() + ("" if ax else "~"), v["panel_name"],
                 100 * a["t_low_image_left"], 100 * a["t_low_image_right"],
                 100 * b["t_low_image_left"], 100 * b["t_low_image_right"],
                 a["stagger_pct"], b["stagger_pct"],
                 g["delta_pct"], g["delta_mm"]))
    if any(not is_axial(v["yaw"]) for v in rows):
        print("  '~' marks an oblique view, where 'each side of the midline' mixes the")
        print("  lateral split with depth. Those rows are shown, never acted on; the")
        print("  front and back rows are the measurement.")
    front = [v for v in rows if is_axial(v["yaw"])]
    for v in front:
        g = v["geometry"]["ground"]
        a, b = g["ref"], g["render"]
        if abs(g["delta_pct"]) > STAGGER_ALARM:
            if abs(b["stagger_pct"]) < 0.2:
                got = "the render stands DEAD LEVEL"
            elif b["higher_side"] == a["higher_side"]:
                got = ("the render raises the same foot by only %.2f%%H (%.0f mm)"
                       % (abs(b["stagger_pct"]), abs(b["stagger_mm"])))
            else:
                got = ("the render raises the OTHER foot -- %s -- by %.2f%%H (%.0f mm)"
                       % (b["higher_side"], abs(b["stagger_pct"]),
                          abs(b["stagger_mm"])))
            print("  yaw %s: the sculpt raises %s by %.2f%%H (%.0f mm); %s"
                  % (fmt_yaw(v["yaw"]).strip(), a["higher_side"],
                     abs(a["stagger_pct"]), abs(a["stagger_mm"]), got))
            print("     -- %+.0f mm out. If spec/jinx.json already carries footLift, it"
                  % g["delta_mm"])
            print("     is not reaching the boot shells: the soles are still both on the")
            print("     floor, so the lift is being applied above them or clamped there.")
        else:
            print("  yaw %s: stance stagger lands within %.2f%%H of the sculpt (%s raised"
                  % (fmt_yaw(v["yaw"]).strip(), abs(g["delta_pct"]), b["higher_side"]))
            print("     in both) -- the contrapposto is holding.")


def mean_angle(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return None
    r = np.radians(v)
    return float(np.degrees(np.arctan2(np.sin(r).mean(), np.cos(r).mean())))


def print_report(res, args):
    hr()
    print(" jinx3js scoreboard   tag=%s   renders=%s   %d view(s)"
          % (res["tag"], res["renders_dir"], len(res["views"])))
    hr()

    vm = res["view_map"]
    mode = vm.get("mode", "cyclic")
    how = {
        "pinned": "PINNED to %s -- not fitted" % (vm.get("pin_source") or "built-in"),
        "pinned-file": "PINNED to %s -- not fitted" % (vm.get("pin_source") or "file"),
        "reused": ("REUSED from view_map.json%s"
                   % (" -- agrees with docs/HANDEDNESS.md"
                      if vm.get("map_agrees_with_pin") else
                      " -- DISAGREES with docs/HANDEDNESS.md")),
        "free": "FITTED, free one-to-one best IoU",
        "cyclic": "FITTED, turnaround-order-preserving best IoU",
    }.get(mode, mode)
    print("\nVIEW MAP  (render -> reference clay panel)\n           %s" % how)
    if mode.startswith("pinned"):
        print("           the pin fixes only WHICH pair; every IoU below is measured"
              " on this run")
    for p in vm["pairs"]:
        print("  %-22s yaw %s  ->  %-8s  IoU %.3f    mirrored %.3f"
              % (p["render"], fmt_yaw(p["yaw"]), p["panel_name"], p["iou"],
                 p["iou_mirrored"]))
    for u in vm.get("pin_unmatched", []):
        print("  %-22s yaw %s  ->  %-8s  no render at that yaw"
              % ("(none)", fmt_yaw(u["yaw"]), "clay_%d.png" % u["panel"]))
    print("  mean IoU over the pairs used %.4f   |  best refit: as-rendered %.4f, "
          "mirrored %.4f  (%s)"
          % (vm.get("mean_used", vm["mean_normal"]), vm["mean_normal"],
             vm["mean_mirror"],
             "reused from view_map.json" if vm.get("reused") else "fitted now"))
    if vm.get("cache_stale"):
        print("  NOTE: the reused map is not what a fresh fit would choose now. The")
        print("        model has changed shape enough to move the mapping; re-run with")
        print("        --refit once you trust the new silhouettes.")
    if mode == "reused" and not vm.get("map_agrees_with_pin", True):
        print("  WARNING: the reused map DISAGREES with docs/HANDEDNESS.md. That file")
        print("        is feature evidence and this cache is an old silhouette fit;")
        print("        delete out/view_map.json or pass --pin to trust the evidence.")
    if not vm.get("fit_agrees_with_map", True):
        pm = vm.get("pin_mean")
        print("  the %s fit would pair differently (mean IoU %.4f vs %s for the map"
              % (vm.get("fitted_mode", "cyclic"), vm.get("fitted_mean", 0.0),
                 fmt(pm, 4)))
        print("  in use): " + ", ".join(
            "yaw %s->clay_%d(%.3f)" % (fmt_yaw(a["yaw"]), a["panel"], a["iou"])
            for a in vm.get("fitted_alternative", [])))
        if mode.startswith("pinned") and not vm.get("fit_agrees_with_pin", True):
            print("  Silhouette IoU cannot see the pistol or the tattoos, so a fit that")
            print("  disagrees with the pin is expected while the margins are thin. Once")
            print("  the character is fully dressed and the fit still disagrees, that is")
            print("  a modelling error -- read the mirror-pair table below first.")
    front = [p for p in vm["pairs"] if p["yaw"] is not None
             and abs(((p["yaw"] + 180) % 360) - 180) < 1e-6]
    if front and front[0]["panel"] != FRONT_PANEL:
        print("  NOTE: docs/PART_CONTRACT.md says panel index %d is the front, but the"
              % FRONT_PANEL)
        print("        map puts yaw 0 on panel %d.  Either the mapping is unresolved"
              % front[0]["panel"])
        print("        (see the IoUs above) or the model's facing axis is wrong.")
    if vm.get("unassigned"):
        print("  %d render(s) had no panel left to match (the turnaround has %d):"
              % (len(vm["unassigned"]), len(vm["pairs"])))
        for u in vm["unassigned"]:
            print("      %-22s yaw %s  best any-panel IoU %.3f  (not scored)"
                  % (u["render"], fmt_yaw(u["yaw"]), u["best_iou"]))
    if vm.get("order_conflict"):
        print("  NOTE: the unconstrained best-IoU assignment disagrees with turnaround")
        print("        order (mean %.3f vs %.3f).  It would pair:"
              % (vm["free_mean_normal"], vm["cyclic_mean_normal"]))
        print("        " + ", ".join("yaw %s->clay_%d(%.3f)"
                                     % (fmt_yaw(a["yaw"]), a["panel"], a["iou"])
                                     for a in vm.get("free_alternative", [])))
        print("        A turnaround cannot jump about, so the ordered map is used.")
        print("        Margins this thin mean the silhouettes are not yet distinct")
        print("        enough to resolve the mapping -- treat per-view numbers as")
        print("        provisional until the IoUs separate.  --free-assign overrides.")
    if vm.get("handedness_suspect"):
        hr("!")
        print("!! HANDEDNESS: the whole turnaround fits BETTER MIRRORED "
              "(%.3f vs %.3f, +%.1f%%)." % (vm["mean_mirror"], vm["mean_normal"],
                                            100.0 * (vm["mean_mirror"] / max(vm["mean_normal"], 1e-6) - 1)))
        print("!! +X must be her LEFT (screen-right in the front view). This is a bug")
        print("!! in the model or the camera, not in the scoreboard. Fix it before")
        print("!! reading any of the numbers below -- tattoos, pouch and Zapper are")
        print("!! all on the wrong side.")
        hr("!")

    mt = res.get("matte", {})
    if mt:
        bad = [k for k, v in mt.items() if v["hole_px"] or v["speck_px"]]
        if bad:
            print("\n  matte repairs applied to the reference (reported, not hidden):")
            for k in sorted(bad):
                v = mt[k]
                print("    %-10s filled %2d pin-hole(s) = %5d px, dropped %d speck(s) = %5d px"
                      % (k, v["hole_n"], v["hole_px"], v["speck_n"], v["speck_px"]))

    mp = res.get("mirror_pairs") or []
    if mp:
        bad = [m for m in mp if m["suspect"]]
        cbad = [m for m in mp if m.get("colour_suspect")]
        sided = [m for m in bad if not m.get("opposite_views")]
        posed = [m for m in bad if m.get("opposite_views")]
        if bad or cbad:
            hr("!")
            if sided:
                print("!! MIRROR-PAIR MISMATCH: %d pair(s) of mirror-image viewpoints"
                      " disagree by" % len(sided))
                print("!! more than %.2f IoU with no projection excuse. A lateral feature"
                      % MIRROR_GAP_ALARM)
                print("!! -- pistol, pouch, arm bands, sash corner -- is on the wrong side")
                print("!! or missing. The mean IoU hides it: one view gains exactly what")
                print("!! the other loses.")
            if posed:
                print("!! STANCE ASYMMETRY: %d pair(s) of OPPOSITE views (yaw y and y+180)"
                      % len(posed))
                print("!! disagree by more than %.2f IoU. Orthographically these two"
                      % MIRROR_GAP_ALARM)
                print("!! renders are forced to be exact mirrors of each other, while the")
                print("!! two reference panels are not, so one render cannot fit both.")
                print("!! This is about her POSE, not about which side anything is on.")
                print("!! Read SELF-MIRROR and GROUND CONTACT below, not this gap.")
            if cbad:
                print("!! MIRROR-PAIR COLOUR MISMATCH on %d pair(s): the two sides differ"
                      % len(cbad))
                print("!! by more than %.0f dE. The tattoos are a texture-only lateral"
                      % MIRROR_DE_ALARM)
                print("!! feature, so this is how a mirrored tattoo shows up at all.")
            hr("!")
        print("\nMIRROR-PAIR CONSISTENCY  (yaw y vs yaw 360-y; 0 and 180 are self-mirrored)")
        print("  %-6s %-7s %6s   %-6s %-7s %6s %6s  %8s %6s  %6s  %s"
              % ("yaw a", "panel a", "IoU a", "yaw b", "panel b", "IoU b", "gap",
                 "symMdl", "symRef", "dEgap", "verdict"))
        for m in mp:
            sm = ("  const" if m.get("opposite_views")
                  else "%8.3f" % m["sym_render"])
            print("  %-6s clay_%-2d %6.3f   %-6s clay_%-2d %6.3f %6.3f  %8s %6.3f  "
                  "%6s  %s%s"
                  % (fmt_yaw(m["yaw_a"]).strip(), m["panel_a"], m["iou_a"],
                     fmt_yaw(m["yaw_b"]).strip(), m["panel_b"], m["iou_b"],
                     m["gap"], sm, m["sym_ref"], fmt(m.get("dE_gap"), 2),
                     "<< " if m["suspect"] or m.get("colour_suspect") else "",
                     m["diagnosis"]))
            wr = m.get("worst_colour_region")
            if wr and wr["gap"] > MIRROR_DE_ALARM:
                print("         worth a look: '%s' differs %.1f dE between the two sides"
                      " (%.1f at yaw %s vs %.1f at yaw %s)"
                      % (wr["region"], wr["gap"], wr["dE_a"],
                         fmt_yaw(m["yaw_a"]).strip(), wr["dE_b"],
                         fmt_yaw(m["yaw_b"]).strip()))
        if any(m.get("opposite_views") for m in mp):
            print("  symMdl reads 'const' where the two yaws are 180 apart. Under the")
            print("  orthographic camera the silhouette along -d is EXACTLY the mirror of")
            print("  the one along +d for any object, so that number is ~0.997 whatever")
            print("  the model is. It cannot discriminate and is excluded from verdicts.")
            print("  Use SELF-MIRROR below for 'is the model too symmetric'.")
        for m in bad:
            if m.get("opposite_views"):
                print("  yaw %s/%s: clay_%d and clay_%d are genuinely different shapes"
                      % (fmt_yaw(m["yaw_a"]).strip(), fmt_yaw(m["yaw_b"]).strip(),
                         m["panel_a"], m["panel_b"]))
                print("     (mirrored against each other they agree only %.3f), and one"
                      % m["sym_ref"])
                print("     orthographic render is forced to be the exact mirror of the")
                print("     other, so it can only fit one of them. The gap measures how")
                print("     asymmetric her POSE is, not which side a feature is on.")
            elif m["sym_render"] - m["sym_ref"] < 0.05:
                print("  yaw %s/%s: the render is as asymmetric as the sculpt (symMdl %.3f"
                      % (fmt_yaw(m["yaw_a"]).strip(), fmt_yaw(m["yaw_b"]).strip(),
                         m["sym_render"]))
                print("     vs symRef %.3f) yet scores %.3f against one panel and %.3f"
                      % (m["sym_ref"], m["iou_a"], m["iou_b"]))
                print("     against the other. That is a feature on the WRONG SIDE: yaw %s"
                      % fmt_yaw(m["worse_side"]).strip())
                print("     is missing what its panel has. See docs/HANDEDNESS.md -- +X is")
                print("     her LEFT and appears on the RIGHT of a front view.")

    print_self_mirror(res)
    print_stance(res)

    print("\nPER-VIEW  (worst first by IoU)")
    print("  %-6s %-4s %-8s %6s %6s %6s %6s %7s %7s %8s %8s %7s %6s"
          % ("yaw", "pan", "render", "IoU", "IoU-db", "prec", "recall", "cham%",
             "F@.78%", "widRMS%", "lmRMS%", "dE", "score"))
    order = sorted(res["views"], key=lambda v: v["geometry"]["full"]["iou"])
    for v in order:
        g, c = v["geometry"], v.get("colour")
        ef = g["full"]["edge_f"].get(EDGE_TOL_FOR_SCORE, {})
        print("  %-6s %-4d %-8s %6.3f %6.3f %6.3f %6.3f %7s %7s %8s %8s %7s %6.1f"
              % (fmt_yaw(v["yaw"]), v["panel"], v["render"][:8],
                 g["full"]["iou"], g["debraid"]["iou"], g["full"]["precision"],
                 g["full"]["recall"], fmt(g["full"]["chamfer_pct"], 2),
                 fmt(ef.get("f"), 3), fmt(g["width_rms_core_pct"], 2),
                 fmt(g["landmark_rms_pct"], 2),
                 fmt(c.get("mean_dE") if c else None, 1), v["score"]["score"]))
    print("    precision < recall  => the render is too FAT there;  "
          "recall < precision => too THIN")

    print("\nNORMALISATION  (scale applied to make each silhouette %d px tall)" % FIG_H)
    print("  %-6s %-8s %9s %9s %9s %9s %9s %8s %6s %6s"
          % ("yaw", "panel", "ref_h_px", "ren_h_px", "scale_ref", "scale_ren",
             "aspect_r", "aspect_n", "dx_px", "dy_px"))
    for v in res["views"]:
        a = v["geometry"]["align"]
        print("  %-6s %-8s %9d %9d %9.3f %9.3f %9.4f %8.4f %6d %6d"
              % (fmt_yaw(v["yaw"]), v["panel_name"], a["ref_src_size"][1],
                 a["render_src_size"][1], a["scale_ref"], a["scale_render"],
                 a["aspect_ref"], a["aspect_render"], a["residual_dx_px"],
                 a["residual_dy_px"]))
    small = [v for v in res["views"]
             if v["geometry"]["align"]["render_src_size"][1] < 400]
    if small:
        h = min(v["geometry"]["align"]["render_src_size"][1] for v in small)
        print("  the render is only %d px tall; normalising it to %d invents detail the"
              % (h, FIG_H))
        print("  render never had. Chamfer and edge-F below are optimistic by roughly"
              " %.1f px." % (FIG_H / float(h) / 2.0))
    sc = [v["geometry"]["align"]["scale_render"] for v in res["views"]]
    if len(sc) > 1:
        spread = 100.0 * (max(sc) - min(sc)) / max(1e-9, float(np.mean(sc)))
        note = "  <- camera or figure height is not constant across views" if spread > 2.0 else ""
        print("  render scale spread %.2f%%%s" % (spread, note))
    da = [abs(v["geometry"]["align"]["d_aspect_pct"]) for v in res["views"]]
    if da and max(da) > 6.0:
        print("  bbox aspect differs from the reference by up to %.1f%% -- the render is"
              " wider/narrower than the sculpt at the same height" % max(da))

    print("\nTOP WIDTH DEVIATIONS  (core profile, worst 10; + = render too WIDE)")
    dev = []
    for v in res["views"]:
        gr = v["geometry"]["ground"]["ref"]
        floor = gr["t_high_sole"] if gr.get("valid") else 0.0
        for b in v["geometry"]["profile"]["bands"]:
            if b["core"]["ref_pct"] < 0.6 and b["core"]["render_pct"] < 0.6:
                continue
            dev.append((abs(b["core"]["d_pct"]), v, b, b["t"] < floor))
    dev.sort(key=lambda x: -x[0])
    if not dev:
        print("  (nothing to report)")
    ground_hit = False
    for i, (_, v, b, in_ground) in enumerate(dev[:10]):
        rel = b["core"]["d_rel_pct"]
        word = "WIDE" if b["core"]["d_pct"] > 0 else "NARROW"
        relw = ("%.0f%% too %s" % (abs(rel), word)) if rel is not None else "n/a"
        ground_hit = ground_hit or in_ground
        print("  %2d. yaw %s  t=%.3f  %-16s ref %5.2f%%H  render %5.2f%%H  "
              "%+6.2f%%H  -> %s%s"
              % (i + 1, fmt_yaw(v["yaw"]), b["t"], b["part"],
                 b["core"]["ref_pct"], b["core"]["render_pct"], b["core"]["d_pct"],
                 relw, "  [under her raised foot]" if in_ground else ""))
    if ground_hit:
        print("    [under her raised foot] = below the reference's higher sole, where the")
        print("    sculpt has ONE boot on the ground and a square-stanced render has two.")
        print("    Fix the stance (see GROUND CONTACT) before touching a boot width here.")

    print("\nLANDMARK HEIGHTS  (fraction of figure height; + = render's feature sits HIGHER)")
    head = "  %-10s" % "landmark"
    for v in res["views"]:
        head += " %15s" % ("yaw " + fmt_yaw(v["yaw"]).strip())
    print(head)
    for k in S.LANDMARK_ORDER:
        if k == "sole":
            continue
        line = "  %-10s" % k
        for v in res["views"]:
            L = v["geometry"]["landmarks"][k]
            if L["ref"] is None or L["render"] is None:
                line += " %14s" % "-"
            else:
                mark = "?" if (L["ref_at_edge"] or L["render_at_edge"]) else " "
                line += " %6.3f/%5.3f%+5.1f%s" % (L["ref"], L["render"],
                                                  L["delta_pct"], mark)
        print(line)
    print("    reads ref/render+delta(%H).  core profile (braid-blind); the "
          "'_full' variant incl. braids is in the JSON.")
    print("    '?' = the search hit its own window edge, so that row is a clamp, "
          "not a measurement.")

    loose = [(v, v["geometry"]["components"]["render"]) for v in res["views"]
             if len(v["geometry"]["components"]["render"]) > 1]
    if loose:
        print("\nDISCONNECTED GEOMETRY  (the render's silhouette is not one piece)")
        for v, comps in loose:
            extra = comps[1:]
            print("  yaw %s  %d pieces; %d loose covering %.1f%% of the area:"
                  % (fmt_yaw(v["yaw"]), len(comps), len(extra),
                     100.0 * sum(c["area_frac"] for c in extra)))
            for c in extra[:4]:
                print("      %5.2f%% of area at t %.3f..%.3f  (%s)"
                      % (100.0 * c["area_frac"], c["t_bottom"], c["t_top"],
                         part_at(0.5 * (c["t_bottom"] + c["t_top"]))))
        print("  A loose piece is almost always a shell placed in the wrong frame,")
        print("  and it drags the bbox -- which sets the normalisation scale -- with it.")
        print("  Fix this before reading the width or landmark tables.")

    watch = []
    for v in res["views"]:
        # Below the reference's HIGHER sole only one foot exists, so a single
        # run there is anatomy, not a bridged matte.  Getting this wrong sent an
        # author chasing a "boots merged, 181% too wide" finding that was never
        # in the reference; the floor of the band now comes from the measured
        # stagger instead of an assumption.
        gr = v["geometry"]["ground"]["ref"]
        floor = (gr["t_high_sole"] + 0.01) if gr.get("valid") else 0.12
        for b in v["geometry"]["profile"]["bands"]:
            if floor < b["t"] < 0.60 and b["nrun_ref"] < b["nrun_render"]:
                gap = b["full"]["render_pct"] - b["sum"]["render_pct"]
                if 0.0 < gap < 3.0:      # a shadow wedge is thin; a real pose
                    watch.append((v, b, gap))   # difference is not
    if watch:
        print("\nREFERENCE MATTE WATCH  (rows where the reference silhouette is CLOSED but")
        print("the render's is OPEN -- the backdrop shadow between the legs survives in")
        print("some panels, so do not close your legs to chase it.  Rows below the")
        print("reference's raised foot are excluded: one run there is her stance.)")
        for v, b, gap in watch[:8]:
            print("  yaw %s  t=%.3f  %-16s reference merged, render splits by %.2f%%H"
                  % (fmt_yaw(v["yaw"]), b["t"], b["part"], gap))
        nb = res["views"][0]["geometry"]["profile"]["nbands"]
        band_h = FIG_H / float(nb)
        extra = sum((g / 100.0 * FIG_H) * band_h for _, _, g in watch)
        per_view = extra / max(1, len(res["views"]))
        aref = float(np.mean([v["geometry"]["full"]["area_ref_px"]
                              for v in res["views"]]))
        print("  up to ~%.0f px per view (%.2f%% of the silhouette) may be matte "
              "bridging rather\n  than model error; that would cap IoU near %.3f on "
              "its own.  Cross-check a band\n  here against out/compare_%s.png before "
              "changing anything."
              % (per_view, 100.0 * per_view / aref, 1.0 - per_view / aref, res["tag"]))

    braids = [(v, v["geometry"]) for v in res["views"]]
    print("\nBRAID MASS  (area outside the de-braided body, as a fraction of the silhouette)")
    line = "  "
    for v, g in braids:
        line += "yaw %s ref %.3f ren %.3f | " % (fmt_yaw(v["yaw"]),
                                                 g["braid_area_frac_ref"],
                                                 g["braid_area_frac_render"])
    print(line)

    cviews = [v for v in res["views"] if v.get("colour") and v["colour"].get("regions")]
    if cviews:
        print("\nCOLOUR  (render - reference, CIE Lab, inside the intersection only)")
        print("  overall: " + "  ".join(
            "yaw %s dE %.1f (dL %+.1f da %+.1f db %+.1f)"
            % (fmt_yaw(v["yaw"]), v["colour"]["mean_dE"], v["colour"]["dL"],
               v["colour"]["da"], v["colour"]["db"]) for v in cviews))
        names = [n for n, _, _, _ in COLOUR_REGIONS] + ["other"]
        print("  %-11s %7s %7s %7s %7s %7s %8s %8s %7s"
              % ("region", "px", "dL", "dL_rel", "da", "db", "hue_ref", "hue_ren", "dE"))
        for n in names:
            acc = [v["colour"]["regions"].get(n) for v in cviews]
            acc = [a for a in acc if a and a.get("pixels", 0) >= 80]
            if not acc:
                print("  %-11s %7s" % (n, "-"))
                continue
            wgt = np.array([a["pixels"] for a in acc], np.float64)
            wgt /= wgt.sum()

            def mm(k):
                return float(np.sum(wgt * np.array([a[k] for a in acc])))
            hr_ = mean_angle([a["hue_ref"] for a in acc])
            hn_ = mean_angle([a["hue_render"] for a in acc])
            print("  %-11s %7d %7.2f %7.2f %7.2f %7.2f %8s %8s %7.2f"
                  % (n, int(sum(a["pixels"] for a in acc)), mm("dL"), mm("dL_rel"),
                     mm("da"), mm("db"), fmt(hr_, 0), fmt(hn_, 0), mm("dE")))
        print("    dL_rel removes the render's global exposure offset (%.1f L), so a "
              "row that is\n    still dark there is genuinely the wrong material, not "
              "just lit differently." % np.mean([v["colour"]["global_L_offset"] for v in cviews]))

    blind = blind_spots(res)
    if blind:
        print("\nWHAT THIS RUN CANNOT SEE  (terms that are structurally blind here, so")
        print("that a constant or an absence is never read as a measurement)")
        for name, why in blind:
            print("  %-24s %s" % (name, why))

    print()
    hr("-")
    print(" SCORE  %.1f / 100      (mean over %d view(s); weights: %s)"
          % (res["score"], len(res["views"]),
             ", ".join("%s %.2f" % (k, v) for k, v in WEIGHTS.items())))
    w = res["worst"]
    print(" worst view: yaw %s (%s) at %.1f -- %s"
          % (fmt_yaw(w["yaw"]), w["panel_name"], w["score"]["score"],
             min(w["score"]["terms"].items(),
                 key=lambda kv: 1e9 if kv[1] is None else kv[1])[0]
             + " is its weakest term"))
    if res["coverage"] < 0.999:
        print(" coverage %d/%d panels -- compare rounds only against the same view set"
              % (len(res["views"]), int(round(len(res["views"]) / res["coverage"]))))
    hr("-")
    for k, v in res["artifacts"].items():
        print(" %-10s %s" % (k, v))


# --------------------------------------------------------------------------
# main comparison
# --------------------------------------------------------------------------

def run(args):
    t0 = time.time()
    renders_dir = args.renders if os.path.isabs(args.renders) \
        else os.path.join(ROOT, args.renders)
    ref_dir = args.ref if os.path.isabs(args.ref) else os.path.join(ROOT, args.ref)
    outdir = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(outdir, exist_ok=True)

    rends, dupes = find_renders(renders_dir)
    panels = find_panels(ref_dir, "clay")
    if not panels:
        print("no reference panels in %s -- run tools/slice_ref.py first" % ref_dir)
        return 1
    res = {"tag": args.tag, "renders_dir": os.path.relpath(renders_dir, ROOT),
           "ref_dir": os.path.relpath(ref_dir, ROOT), "views": [], "matte": {},
           "artifacts": {}, "generated": time.strftime("%Y-%m-%d %H:%M:%S")}
    res["duplicate_renders_dropped"] = dupes
    if dupes:
        print("  same yaw present under two prefixes; ignoring %s"
              % ", ".join(dupes))
    if not rends:
        print("no renders found in %s (looked for render_yaw*.png and "
              "preview_yaw*.png)." % renders_dir)
        print("nothing to score. run `node tools/render.mjs` first, or pass "
              "--renders <dir>.")
        res["status"] = "no-renders"
        res["score"] = 0.0
        path = os.path.join(outdir, "metrics_%s.json" % args.tag)
        with open(path, "w") as f:
            json.dump(jsonify(res), f, indent=1)
        print("wrote %s" % os.path.relpath(path, ROOT))
        return 0

    # ---- load
    for p in panels:
        n, info = prep(p["file"])
        p["norm"] = n
        res["matte"][p["name"]] = info
    panels = [p for p in panels if p["norm"] is not None]
    live = []
    for r in rends:
        try:
            n, info = prep(r["file"])
        except IOError as e:
            print("  skipping %s: %s" % (r["name"], e))
            continue
        if n is None:
            print("  skipping %s: render is blank (no opaque pixels)" % r["name"])
            continue
        r["norm"] = n
        live.append(r)
    if not live:
        print("every render was blank or unreadable; nothing to score.")
        res["status"] = "blank-renders"
        res["score"] = 0.0
        with open(os.path.join(outdir, "metrics_%s.json" % args.tag), "w") as f:
            json.dump(jsonify(res), f, indent=1)
        return 0
    rends = live

    # ---- assignment
    map_path = os.path.join(outdir, "view_map.json")
    cached = None
    if not args.refit and os.path.exists(map_path):
        try:
            with open(map_path) as f:
                cached = json.load(f)
        except Exception:
            cached = None
    fit = fit_assignment(rends, panels, args.max_shift)
    kind = "free" if args.free_assign else "cyclic"
    fitted = fit["%s_normal" % kind]
    mean_n = fit["%s_mean_normal" % kind]
    mean_m = fit["%s_mean_mirror" % kind]

    # Panel index -> yaw, applied by yaw so the prefix (render_/preview_) does
    # not matter.  Returns the pairs it could place and the panels it could not.
    def pairs_from_pin(pin):
        by_yaw = {}
        for i, r in enumerate(rends):
            if r["yaw"] is not None:
                by_yaw.setdefault(r["yaw"] % 360.0, i)
        got, miss = [], []
        for j, p in enumerate(panels):
            y = pin.get(p["index"])
            if y is None:
                continue
            i = by_yaw.get(y % 360.0)
            if i is None:
                miss.append((p["index"], y))
            else:
                got.append((i, j))
        return got, miss

    by_name = {p["render"]: p for p in (cached or {}).get("pairs", [])}
    known = set(by_name) | {u["render"] for u in (cached or {}).get("unassigned", [])}
    use_cache = bool(by_name) and all(r["name"] in known for r in rends)

    cache_pairs = []
    if use_cache:
        idx = {p["index"]: j for j, p in enumerate(panels)}
        for i, r in enumerate(rends):
            if r["name"] not in by_name:
                continue                      # was unassigned last time, still is
            j = idx.get(by_name[r["name"]]["panel"])
            if j is None:
                use_cache = False
                break
            cache_pairs.append((i, j))
        if len(set(j for _, j in cache_pairs)) != len(cache_pairs) or not cache_pairs:
            use_cache = False                       # cached map is not one-to-one

    # Precedence.  A wrong map silently mis-pairs every per-view number below,
    # which is worse than a map that is occasionally stale -- so a fit is only
    # adopted when it is asked for, and the feature-derived pin is the fallback
    # rather than the fit.
    pin_missing, pin_source = [], None
    if args.refit:
        pairs, mode = list(fitted), kind
    elif args.map:
        pin, pin_source = load_pinned(args.map if os.path.isabs(args.map)
                                      else os.path.join(ROOT, args.map))
        pairs, pin_missing = pairs_from_pin(pin)
        mode = "pinned-file"
    elif args.pin:
        pin, pin_source = load_pinned(None)
        pairs, pin_missing = pairs_from_pin(pin)
        mode = "pinned"
    elif use_cache:
        pairs, mode = cache_pairs, "reused"
    else:
        pin, pin_source = load_pinned(None)
        pairs, pin_missing = pairs_from_pin(pin)
        mode = "pinned"
    if not pairs:
        print("  the pinned map placed no renders (no yaw matched a panel); "
              "falling back to the fit")
        pairs, mode, pin_source = list(fitted), kind, None

    # Whichever map is in use, the fit is computed anyway and the disagreement
    # reported: once the character is dressed, a fit that still disagrees with
    # the feature-derived pin is evidence of a modelling error, not of a bad fit.
    pin_ref, _ = load_pinned(None)
    pin_pairs, _ = pairs_from_pin(pin_ref)
    vm = {
        "version": 3, "fitted_at": res["generated"], "mode": mode,
        "pin_source": pin_source,
        "renders_dir": res["renders_dir"], "reused": bool(mode == "reused"),
        "mean_normal": mean_n, "mean_mirror": mean_m,
        "free_mean_normal": fit["free_mean_normal"],
        "cyclic_mean_normal": fit["cyclic_mean_normal"],
        "order_conflict": bool(fit["ordered"] and
                               set(fit["cyclic_normal"]) != set(fit["free_normal"])),
        # Absolute *and* relative margin: a near-symmetric blockout flips by a
        # percent or two from matte noise alone, and a false handedness alarm
        # would send a part author chasing a bug that is not there.
        "handedness_suspect": bool(mean_m > mean_n + max(0.02, 0.03 * mean_n)),
        "pairs": [],
    }
    if vm["order_conflict"]:
        vm["free_alternative"] = [
            {"render": rends[i]["name"], "yaw": rends[i]["yaw"],
             "panel": panels[j]["index"], "iou": float(fit["normal"][i, j])}
            for i, j in fit["free_normal"]]
    for i, j in pairs:
        vm["pairs"].append({
            "render": rends[i]["name"], "yaw": rends[i]["yaw"],
            "panel": panels[j]["index"], "panel_name": panels[j]["name"],
            "iou": float(fit["normal"][i, j]),
            "iou_mirrored": float(fit["mirror"][i, j]),
        })
    taken = set(i for i, _ in pairs)
    vm["unassigned"] = [{"render": r["name"], "yaw": r["yaw"],
                         "best_iou": float(fit["normal"][i].max())}
                        for i, r in enumerate(rends) if i not in taken]
    vm["pin_unmatched"] = [{"panel": p, "yaw": y} for p, y in pin_missing]
    vm["mean_used"] = (float(np.mean([p["iou"] for p in vm["pairs"]]))
                       if vm["pairs"] else 0.0)
    vm["cache_stale"] = bool(mode == "reused" and set(pairs) != set(fitted))

    # How far the fit is from the map actually in use, and from the pin.
    def describe(prs):
        return [{"render": rends[i]["name"], "yaw": rends[i]["yaw"],
                 "panel": panels[j]["index"], "iou": float(fit["normal"][i, j])}
                for i, j in sorted(prs)]

    used_set = set(pairs)
    vm["fit_agrees_with_map"] = bool(set(fitted) == used_set)
    vm["fit_agrees_with_pin"] = bool(set(fitted) == set(pin_pairs))
    vm["map_agrees_with_pin"] = bool(used_set == set(pin_pairs))
    vm["fitted_alternative"] = describe(fitted)
    vm["fitted_mode"] = kind
    vm["fitted_mean"] = mean_n
    vm["pin_mean"] = (float(np.mean([fit["normal"][i, j] for i, j in pin_pairs]))
                      if pin_pairs else None)
    if mode == "reused" and cached:
        vm["handedness_suspect"] = bool(cached.get("handedness_suspect",
                                                   vm["handedness_suspect"]))
    res["view_map"] = vm
    if mode != "reused":
        with open(map_path, "w") as f:
            json.dump(jsonify(vm), f, indent=1)
    res["artifacts"]["view_map"] = os.path.relpath(map_path, ROOT)

    want = None
    if args.views:
        want = set(int(x) for x in re.split(r"[,\s]+", args.views) if x != "")

    use_mirror = args.use_mirror or (vm["handedness_suspect"] and args.follow_mirror)

    # ---- per view
    for i, j in pairs:
        r, p = rends[i], panels[j]
        if want is not None and p["index"] not in want:
            continue
        ren = dict(r["norm"])
        if use_mirror:
            fm = np.ascontiguousarray(ren["mask"][:, ::-1])
            ren["mask"] = fm
            if ren.get("rgb") is not None:
                ren["rgb"] = np.ascontiguousarray(ren["rgb"][:, ::-1])
            ren["stats"] = S.row_stats(fm)
            dst, dm = S.debraid_stats(fm, ren["stats"], braid_px=0.042 * FIG_H)
            ren["debraid"], ren["debraid_stats"] = dm, dst
        g = view_geometry(p["norm"], ren, args.bands, args.max_shift,
                          axial=is_axial(r["yaw"]))
        c = None
        if not args.no_colour:
            body = os.path.join(ref_dir, "body_%d.png" % p["index"])
            if os.path.exists(body):
                try:
                    c = view_colour(body, r["file"], args.max_shift, use_mirror)
                except Exception as e:                       # never kill a run
                    c = {"status": "colour failed: %s" % e}
        v = {"render": r["name"], "yaw": r["yaw"], "panel": p["index"],
             "panel_name": p["name"], "mirrored": bool(use_mirror),
             "geometry": g, "colour": c}
        v["score"] = view_score(g, c)
        res["views"].append(v)

    if not res["views"]:
        print("no views left after --views filter %s" % args.views)
        res["status"] = "no-views"
        res["score"] = 0.0
        return 0

    res["views"].sort(key=lambda v: (v["yaw"] is None, v["yaw"] or 0))
    res["score"] = float(np.mean([v["score"]["score"] for v in res["views"]]))
    res["worst"] = min(res["views"], key=lambda v: v["score"]["score"])
    res["score_weights"] = WEIGHTS
    res["score_constants"] = {"K_width_pct": K_WIDTH, "K_landmark_pct": K_LAND,
                              "K_chamfer_pct": K_CHAM, "K_colour_dE": K_COLOUR,
                              "edge_tol_px": int(EDGE_TOL_FOR_SCORE)}
    res["views_scored"] = len(res["views"])
    res["coverage"] = len(res["views"]) / float(len(panels))
    res["mirror_pairs"] = mirror_pair_check(res["views"])

    # ---- artifacts
    cs = os.path.join(outdir, "compare_%s.png" % args.tag)
    ps = os.path.join(outdir, "profiles_%s.png" % args.tag)
    mp = os.path.join(outdir, "metrics_%s.json" % args.tag)
    res["artifacts"]["contact"] = os.path.relpath(cs, ROOT)
    res["artifacts"]["profiles"] = os.path.relpath(ps, ROOT)
    res["artifacts"]["metrics"] = os.path.relpath(mp, ROOT)
    hdr = ("tag=%s   score %.1f/100   %d view(s)   %s"
           % (args.tag, res["score"], len(res["views"]),
              "MIRRORED RENDERS -- handedness bug" if use_mirror else ""))
    cv2.imwrite(cs, contact_sheet(res["views"], args.tag, hdr))
    cv2.imwrite(ps, profiles_sheet(res["views"], args.tag))
    res["elapsed_s"] = time.time() - t0
    with open(mp, "w") as f:
        json.dump(jsonify(res), f, indent=1)

    print_report(res, args)
    print(" %-10s %.2f s" % ("elapsed", res["elapsed_s"]))
    return 0


# --------------------------------------------------------------------------
# ceiling probe
# --------------------------------------------------------------------------

def run_ceiling(args):
    """How well can any render possibly do, given the mattes?

    clay_i and body_i are the same camera on the same sculpt, so their
    silhouettes should be identical; whatever they disagree about is matte
    noise, and no render can score above it.
    """
    ref_dir = os.path.join(ROOT, args.ref)
    print("MATTE CEILING")
    print("  cross-matte : clay_i vs body_i -- same camera, same sculpt, so every")
    print("                disagreement is matte error (plus hair the texture pass")
    print("                resolves and the clay does not).")
    print("  1px         : IoU of the clay matte against itself grown/shrunk by one")
    print("                pixel -- what a single pixel of edge doubt costs.")
    print("  %-8s %9s %7s %7s %8s %9s %9s %9s"
          % ("panel", "cross-IoU", "prec", "recall", "cham%", "IoU+1px",
             "IoU-1px", "holes_px"))
    ious, d1s = [], []
    k3 = np.ones((3, 3), np.uint8)
    for p in find_panels(ref_dir, "clay"):
        a, ia = prep(p["file"])
        if a is None:
            continue
        am = a["mask"].astype(np.uint8)
        gi = S.iou_of(a["mask"], cv2.dilate(am, k3).astype(bool))
        ei = S.iou_of(a["mask"], cv2.erode(am, k3).astype(bool))
        d1s.append(min(gi, ei))
        b = os.path.join(ref_dir, "body_%d.png" % p["index"])
        if not os.path.exists(b):
            print("  %-8s %9s %7s %7s %8s %9.4f %9.4f %9d"
                  % (p["name"], "-", "-", "-", "-", gi, ei, ia["hole_px"]))
            continue
        c, ic = prep(b)
        if c is None:
            continue
        dx, dy, _ = S.refine_offset(a["mask"], c["mask"], args.max_shift)
        m = S.shift(c["mask"], dx, dy)
        o = S.overlap_metrics(a["mask"], m)
        cm = S.contour_metrics(a["mask"], m)
        ious.append(o["iou"])
        print("  %-8s %9.4f %7.4f %7.4f %8.3f %9.4f %9.4f %9d"
              % (p["name"], o["iou"], o["precision"], o["recall"],
                 cm["chamfer_pct"], gi, ei, ia["hole_px"] + ic["hole_px"]))
    if ious:
        print("\n  cross-matte mean %.4f  min %.4f" % (float(np.mean(ious)), float(min(ious))))
    if d1s:
        print("  one-pixel   mean %.4f  min %.4f" % (float(np.mean(d1s)), float(min(d1s))))
    print("\n  Read the one-pixel row as the hard ceiling for a clay comparison: the")
    print("  matte boundary is a threshold on a soft edge, so anything above it is")
    print("  measuring the matte, not the model.  The cross-matte row is the ceiling")
    print("  you would hit if you scored geometry against the textured panels; it is")
    print("  lower, which is exactly why clay_* is the geometry target.")
    return 0


# --------------------------------------------------------------------------
# selftest: perturb the reference by a known amount, check we recover it
# --------------------------------------------------------------------------

def _rgba(bgr, mask):
    return np.dstack([bgr, (mask.astype(np.uint8) * 255)])


def _from_panel(path):
    bgr, alpha = S.load_rgba(path)
    m, _ = S.clean_mask(alpha)
    x0, y0, x1, y1 = S.bbox_of(m)
    return bgr[y0:y1, x0:x1], m[y0:y1, x0:x1]


def _pad(bgr, m, pad=20):
    return (cv2.copyMakeBorder(bgr, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0),
            cv2.copyMakeBorder(m.astype(np.uint8), pad, pad, pad, pad,
                               cv2.BORDER_CONSTANT, value=0).astype(bool))


def make_synthetic(ref_dir, dstdir, mapping, mirror_all=False):
    """Write six stand-in renders with known, analytically predictable errors."""
    os.makedirs(dstdir, exist_ok=True)
    truth = {}
    for yaw, (idx, kind) in mapping.items():
        clay = os.path.join(ref_dir, "clay_%d.png" % idx)
        body = os.path.join(ref_dir, "body_%d.png" % idx)
        if kind == "darkpants" and os.path.exists(body):
            # the colour case must start from a pixel-exact copy of the colour
            # target, or the round-trip error swamps the shift being measured
            bgr, m = _from_panel(body)
        else:
            bgr, m = _from_panel(clay)
            if os.path.exists(body):
                cb, _ = _from_panel(body)
                bgr = cv2.resize(cb, (m.shape[1], m.shape[0]),
                                 interpolation=cv2.INTER_AREA)
        H0, W0 = m.shape
        info = {"kind": kind, "panel": idx, "src_h": H0, "src_w": W0}

        if kind == "identity":
            pass
        elif kind == "wide108":
            s = 1.08
            m = cv2.resize(m.astype(np.uint8), (int(round(W0 * s)), H0),
                           interpolation=cv2.INTER_NEAREST).astype(bool)
            bgr = cv2.resize(bgr, (m.shape[1], H0), interpolation=cv2.INTER_AREA)
            info["stretch_x"] = s
        elif kind == "scale115":
            s = 1.15
            m = cv2.resize(m.astype(np.uint8), (int(round(W0 * s)), int(round(H0 * s))),
                           interpolation=cv2.INTER_NEAREST).astype(bool)
            bgr = cv2.resize(bgr, (m.shape[1], m.shape[0]), interpolation=cv2.INTER_AREA)
            info["scale"] = s
        elif kind == "shift":
            bgr, m = _pad(bgr, m, 60)
            M = np.float32([[1, 0, 37], [0, 1, -23]])
            m = cv2.warpAffine(m.astype(np.uint8), M, (m.shape[1], m.shape[0]),
                               flags=cv2.INTER_NEAREST).astype(bool)
            bgr = cv2.warpAffine(bgr, M, (bgr.shape[1], bgr.shape[0]))
            info["shift"] = [37, -23]
        elif kind == "thinlegs":
            k = 4
            cut = int(round(H0 * (1.0 - 0.55)))     # rows below t=0.55
            mm = m.copy().astype(np.uint8)
            low = cv2.erode(mm[cut:], np.ones((1, 2 * k + 1), np.uint8))
            mm[cut:] = low
            m = mm.astype(bool)
            info["erode_px_per_side"] = k
            info["below_t"] = 0.55
        elif kind == "shortlegs":
            f = 0.93
            cut = int(round(H0 * (1.0 - 0.547)))    # spec crotch height
            top, bot = m[:cut], m[cut:]
            tb, bb = bgr[:cut], bgr[cut:]
            nb = max(1, int(round(bot.shape[0] * f)))
            bot = cv2.resize(bot.astype(np.uint8), (W0, nb),
                             interpolation=cv2.INTER_NEAREST).astype(bool)
            bb = cv2.resize(bb, (W0, nb), interpolation=cv2.INTER_AREA)
            m = np.vstack([top, bot])
            bgr = np.vstack([tb, bb])
            info["leg_scale"] = f
            info["cut_t"] = 0.547
            info["leg_rows_before"] = H0 - cut
            info["leg_rows_after"] = nb
            info["h_before"], info["h_after"] = H0, m.shape[0]
        elif kind == "darkpants":
            lab = to_lab(bgr)
            before = lab[:, :, 0].copy()
            t = (np.arange(m.shape[0])[::-1]) / float(m.shape[0] - 1)
            sel = ((t >= 0.33) & (t < 0.585))[:, None] & m
            lab[:, :, 0][sel] = np.clip(lab[:, :, 0][sel] - 10.0, 0, 100)
            bgr = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR) * 255.0,
                          0, 255).astype(np.uint8)
            after = to_lab(bgr)[:, :, 0]
            info["dL_nominal"] = -10.0
            info["dL_applied"] = float((after - before)[sel].mean())
            info["t_range"] = [0.33, 0.585]
        else:
            raise ValueError(kind)

        if mirror_all:
            m = np.ascontiguousarray(m[:, ::-1])
            bgr = np.ascontiguousarray(bgr[:, ::-1])
            info["mirrored"] = True
        bgr = bgr.copy()
        bgr[~m] = 0
        cv2.imwrite(os.path.join(dstdir, "render_yaw%03d.png" % yaw), _rgba(bgr, m))
        truth[yaw] = info
    with open(os.path.join(dstdir, "truth.json"), "w") as f:
        json.dump(jsonify(truth), f, indent=1)
    return truth


SELFTEST_MAP = {0: (2, "thinlegs"), 60: (3, "wide108"), 120: (4, "darkpants"),
                180: (5, "scale115"), 240: (0, "shift"), 300: (1, "shortlegs")}


def run_selftest(args):
    ref_dir = os.path.join(ROOT, args.ref)
    dst = os.path.join(ROOT, "out", "selftest")
    views = os.path.join(dst, "views")
    print("SELFTEST  synthetic renders in %s" % os.path.relpath(views, ROOT))
    truth = make_synthetic(ref_dir, views, SELFTEST_MAP)

    sub = argparse.Namespace(**vars(args))
    sub.renders = os.path.relpath(views, ROOT)
    sub.out = os.path.relpath(dst, ROOT)
    sub.tag = "selftest"
    sub.refit = True          # the selftest is about the fit, so pin is bypassed
    sub.pin = False
    sub.map = None
    sub.views = None
    sub.no_colour = False
    sub.use_mirror = False
    sub.follow_mirror = False
    run(sub)

    with open(os.path.join(dst, "metrics_selftest.json")) as f:
        met = json.load(f)
    by_yaw = {int(round(v["yaw"])): v for v in met["views"]}

    hr()
    print(" SELFTEST CHECKS   applied perturbation  vs  what the tool recovered")
    hr()
    ok = True

    def check(name, got, want, tol, unit=""):
        nonlocal ok
        good = got is not None and abs(got - want) <= tol
        ok = ok and good
        print("  [%s] %-42s applied %+8.3f%s   measured %+8.3f%s   tol %.3f"
              % ("PASS" if good else "FAIL", name, want, unit,
                 (got if got is not None else float("nan")), unit, tol))

    # assignment
    got_map = {int(round(p["yaw"])): p["panel"] for p in met["view_map"]["pairs"]}
    want_map = {y: v[0] for y, v in SELFTEST_MAP.items()}
    good = got_map == want_map
    ok = ok and good
    print("  [%s] view assignment recovered %s (wanted %s)"
          % ("PASS" if good else "FAIL", got_map, want_map))
    print("  [%s] handedness alarm silent on un-mirrored renders (mean %.3f vs %.3f)"
          % ("PASS" if not met["view_map"]["handedness_suspect"] else "FAIL",
             met["view_map"]["mean_normal"], met["view_map"]["mean_mirror"]))
    ok = ok and not met["view_map"]["handedness_suspect"]

    # identity-ish invariances
    for yaw, label, tol_iou in ((180, "uniform scale 1.15", 0.985),
                                (240, "translation (+37,-23) px", 0.985)):
        v = by_yaw[yaw]
        good = v["geometry"]["full"]["iou"] >= tol_iou
        ok = ok and good
        print("  [%s] %-42s IoU %.4f (want >= %.3f)  width rms %.3f%%H"
              % ("PASS" if good else "FAIL", label + " is normalised away",
                 v["geometry"]["full"]["iou"], tol_iou,
                 v["geometry"]["width_rms_core_pct"]))

    # horizontal stretch: every band should read +8% relative
    v = by_yaw[60]
    rel = [b["core"]["d_rel_pct"] for b in v["geometry"]["profile"]["bands"]
           if b["core"]["d_rel_pct"] is not None and 0.05 < b["t"] < 0.95]
    check("horizontal stretch, median band width error", float(np.median(rel)),
          8.0, 1.5, "%")

    # thin legs: -2k px below t=0.55, nothing above
    v = by_yaw[0]
    k = truth[0]["erode_px_per_side"]
    sc = FIG_H / float(truth[0]["src_h"])
    want_lo = -2.0 * k * sc / FIG_H * 100.0
    lo = [b["core"]["d_pct"] for b in v["geometry"]["profile"]["bands"]
          if 0.08 < b["t"] < 0.53]
    hi = [b["core"]["d_pct"] for b in v["geometry"]["profile"]["bands"]
          if 0.60 < b["t"] < 0.90]
    check("legs eroded 4 px/side: width error below t=0.55",
          float(np.median(lo)), want_lo, 0.20, "%H")
    check("legs eroded 4 px/side: width error above t=0.60",
          float(np.median(hi)), 0.0, 0.20, "%H")

    # short legs: the whole figure re-normalises, so every landmark moves by a
    # predictable amount -- below the cut it scales, above it it rides down.
    v = by_yaw[300]
    ti = truth[300]
    f, h0, h1, cut_t = (ti["leg_scale"], ti["h_before"], ti["h_after"],
                        ti["cut_t"])
    for name in ("crotch", "hip", "waist", "shoulder", "knee", "ankle"):
        L = v["geometry"]["landmarks"][name]
        if L["ref"] is None or L["render"] is None:
            print("  [SKIP] legs x%.2f: landmark %s not detected in both" % (f, name))
            continue
        tr = L["ref"]
        want = (tr * h0 * f / h1) if tr <= cut_t else (1.0 - h0 * (1.0 - tr) / h1)
        check("legs x%.2f: landmark %-8s height" % (f, name),
              100.0 * L["render"], 100.0 * want, 2.5, "%H")

    # colour: a known L drop on the trouser bands and nowhere else
    v = by_yaw[120]
    applied = truth[120].get("dL_applied", -10.0)
    if v.get("colour") and v["colour"].get("regions"):
        for nm in ("thighs", "knees"):
            r = v["colour"]["regions"].get(nm)
            if r and r.get("pixels", 0) > 500:
                check("pants darkened: %-14s dL" % nm, r["dL"], applied, 1.5, " L")
        for nm in ("chest_top", "boots", "head"):
            r = v["colour"]["regions"].get(nm)
            if r and r.get("pixels", 0) > 500:
                check("untouched band %-18s dL" % nm, r["dL"], 0.0, 1.0, " L")

    # handedness alarm must fire when everything is mirrored
    mviews = os.path.join(dst, "views_mirror")
    make_synthetic(ref_dir, mviews, {y: (i, "identity") for y, (i, _) in SELFTEST_MAP.items()},
                   mirror_all=True)
    sub2 = argparse.Namespace(**vars(sub))
    sub2.renders = os.path.relpath(mviews, ROOT)
    sub2.tag = "selftest_mirror"
    sub2.no_colour = True
    print("\n  --- mirrored-turnaround run (the alarm must fire) ---")
    run(sub2)
    with open(os.path.join(dst, "metrics_selftest_mirror.json")) as f:
        mm = json.load(f)
    good = bool(mm["view_map"]["handedness_suspect"])
    ok = ok and good
    print("  [%s] handedness alarm fires on a mirrored turnaround "
          "(mirrored %.3f vs as-rendered %.3f)"
          % ("PASS" if good else "FAIL", mm["view_map"]["mean_mirror"],
             mm["view_map"]["mean_normal"]))

    hr()
    print(" SELFTEST %s" % ("PASSED" if ok else "FAILED"))
    hr()
    return 0 if ok else 1


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="r1", help="names the output files")
    ap.add_argument("--renders", default="out/views")
    ap.add_argument("--ref", default="ref/views")
    ap.add_argument("--out", default="out")
    ap.add_argument("--views", default=None,
                    help="comma separated reference panel indices to score, e.g. 2,5")
    ap.add_argument("--bands", type=int, default=40,
                    help="width-profile sample count (default 40)")
    ap.add_argument("--max-shift", type=int, default=40, dest="max_shift",
                    help="cap on the residual alignment search, canvas px")
    ap.add_argument("--refit", action="store_true",
                    help="re-solve the render->panel assignment from silhouette IoU, "
                         "ignoring both the pin and out/view_map.json")
    ap.add_argument("--pin", action="store_true",
                    help="use the built-in feature-derived map from docs/HANDEDNESS.md "
                         "(this is also the default when out/view_map.json is absent)")
    ap.add_argument("--map", default=None,
                    help="use a pinned panel->yaw map from a JSON file, e.g. "
                         "out/view_map_pinned.json")
    ap.add_argument("--free-assign", action="store_true", dest="free_assign",
                    help="allow a view map that breaks turnaround order (pure best-IoU)")
    ap.add_argument("--no-colour", "--no-color", action="store_true", dest="no_colour")
    ap.add_argument("--use-mirror", action="store_true",
                    help="score the mirrored renders (only to inspect a handedness bug)")
    ap.add_argument("--follow-mirror", action="store_true",
                    help="if the mirrored fit wins, score mirrored instead of as-rendered")
    ap.add_argument("--ceiling", action="store_true",
                    help="report the matte-quality IoU ceiling and exit")
    ap.add_argument("--selftest", action="store_true",
                    help="perturb the reference by known amounts and check recovery")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.ceiling:
        return run_ceiling(args)
    if args.selftest:
        return run_selftest(args)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
