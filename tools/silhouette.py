"""Silhouette normalisation, run decomposition and shape metrics.

Shared by ``tools/compare.py``.  Nothing in here knows about renders or
reference panels -- it all works on a boolean mask and, optionally, the BGR
image behind it.

Everything downstream lives in one fixed canvas so that a pixel is the same
physical size in every view and in every round:

    figure height  = FIG_H px, always
    sole row       = BASE_Y - 1
    horizontal     = the mask's own centroid placed on CENTER_X

so a length reported in px is directly a permille of the figure's height, and
``pct`` in this module always means *percent of the figure height*.
"""
import os

import cv2
import numpy as np

CANVAS_W = 768
CANVAS_H = 1200
FIG_H = 1024
BASE_Y = 1104            # exclusive bottom of the figure bbox in canvas rows
CENTER_X = CANVAS_W // 2
TOP_Y = BASE_Y - FIG_H   # 80

# t is the height fraction of the figure: 0 at the soles, 1 at the very top.
T_ROWS = (BASE_Y - 1 - np.arange(CANVAS_H)) / float(FIG_H - 1)


# --------------------------------------------------------------------------
# loading and matte cleanup
# --------------------------------------------------------------------------

def load_rgba(path):
    """Return (bgr uint8, alpha uint8).  Missing alpha is treated as opaque."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise IOError("cannot read %s" % path)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 3:
        return im, np.full(im.shape[:2], 255, np.uint8)
    return np.ascontiguousarray(im[:, :, :3]), np.ascontiguousarray(im[:, :, 3])


def clean_mask(alpha, thresh=127, speck_frac=0.004, hole_frac=6e-4):
    """Threshold an alpha channel and report -- never hide -- what was fixed.

    The reference mattes carry JPEG pin-holes inside the braids and the odd
    speck of backdrop.  Both are removed here because they are certainly not
    geometry, but the amount removed is returned so ``compare.py`` can print it
    and so the IoU ceiling it implies stays visible.
    """
    m = (alpha > thresh).astype(np.uint8)
    info = {"fg_px": int(m.sum()), "speck_px": 0, "speck_n": 0,
            "hole_px": 0, "hole_n": 0, "kept_components": 0}
    if info["fg_px"] == 0:
        return m.astype(bool), info

    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        areas = st[1:, cv2.CC_STAT_AREA]
        big = areas.max()
        keep = np.zeros(n, bool)
        keep[1:] = areas >= speck_frac * big
        info["speck_n"] = int((~keep[1:]).sum())
        info["speck_px"] = int(areas[~keep[1:]].sum())
        info["kept_components"] = int(keep[1:].sum())
        m = keep[lab].astype(np.uint8)

    # Interior holes.  A hole that is *large* is real -- the triangle between a
    # relaxed arm and the ribs is enclosed background -- so only pin-holes are
    # filled.
    inv = (1 - m).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
    border = np.zeros(n2, bool)
    for row in (lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]):
        border[np.unique(row)] = True
    lim = max(24.0, hole_frac * m.sum())
    fill = np.zeros(n2, bool)
    for i in range(1, n2):
        if not border[i] and st2[i, cv2.CC_STAT_AREA] <= lim:
            fill[i] = True
    if fill.any():
        sel = fill[lab2]
        info["hole_n"] = int(fill.sum())
        info["hole_px"] = int(sel.sum())
        m[sel] = 1
    return m.astype(bool), info


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------

def bbox_of(mask):
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def normalize(mask, bgr=None):
    """Scale the silhouette to FIG_H tall, drop it on the fixed canvas.

    Height, not area or width, sets the scale: the braids and the A-pose make
    width unreliable, but the figure stands on the floor in every panel and the
    top of the head is unambiguous.  The horizontal anchor is the silhouette's
    own centroid (steadier than the bbox centre, which one splayed braid can
    drag 20 px), and the vertical anchor is the soles.
    """
    box = bbox_of(mask)
    if box is None:
        return None
    x0, y0, x1, y1 = box
    src_h, src_w = y1 - y0, x1 - x0
    scale = FIG_H / float(src_h)
    new_w = max(1, int(round(src_w * scale)))

    crop = mask[y0:y1, x0:x1].astype(np.float32)
    small = cv2.resize(crop, (new_w, FIG_H), interpolation=cv2.INTER_AREA)
    sm = small >= 0.5
    if not sm.any():                       # degenerate sliver
        sm = small > 0.0
    ys, xs = np.nonzero(sm)
    cx = xs.mean()
    ox = int(round(CENTER_X - cx))

    out = np.zeros((CANVAS_H, CANVAS_W), bool)
    dx0, dx1 = ox, ox + new_w
    sx0, sx1 = 0, new_w
    if dx0 < 0:
        sx0, dx0 = -dx0, 0
    if dx1 > CANVAS_W:
        sx1 -= dx1 - CANVAS_W
        dx1 = CANVAS_W
    if sx1 > sx0:
        out[TOP_Y:BASE_Y, dx0:dx1] = sm[:, sx0:sx1]

    rgb = None
    if bgr is not None:
        c = bgr[y0:y1, x0:x1]
        cs = cv2.resize(c, (new_w, FIG_H), interpolation=cv2.INTER_AREA)
        rgb = np.zeros((CANVAS_H, CANVAS_W, 3), np.uint8)
        if sx1 > sx0:
            rgb[TOP_Y:BASE_Y, dx0:dx1] = cs[:, sx0:sx1]

    return {
        "mask": out,
        "rgb": rgb,
        "scale": float(scale),
        "src_bbox": [x0, y0, x1, y1],
        "src_size": [int(src_w), int(src_h)],
        "aspect": float(src_w) / float(src_h),
        "offset_x": int(ox),
        "clipped": bool(sx0 > 0 or sx1 < new_w),
    }


def shift(mask, dx, dy):
    out = np.zeros_like(mask)
    H, W = mask.shape
    sy0, sy1 = max(0, -dy), min(H, H - dy)
    dy0, dy1 = max(0, dy), min(H, H + dy)
    sx0, sx1 = max(0, -dx), min(W, W - dx)
    dx0, dx1 = max(0, dx), min(W, W + dx)
    if sy1 > sy0 and sx1 > sx0:
        out[dy0:dy1, dx0:dx1] = mask[sy0:sy1, sx0:sx1]
    return out


def iou_of(a, b):
    inter = np.count_nonzero(a & b)
    union = np.count_nonzero(a | b)
    return inter / union if union else 0.0


def _iou_shift(a, b, dx, dy, aa=None, ab=None):
    """IoU of a against b shifted by (dx, dy), without materialising a copy."""
    H, W = a.shape
    ay0, ay1 = max(0, dy), min(H, H + dy)
    by0, by1 = ay0 - dy, ay1 - dy
    ax0, ax1 = max(0, dx), min(W, W + dx)
    bx0, bx1 = ax0 - dx, ax1 - dx
    if ay1 <= ay0 or ax1 <= ax0:
        return 0.0
    inter = np.count_nonzero(a[ay0:ay1, ax0:ax1] & b[by0:by1, bx0:bx1])
    aa = np.count_nonzero(a) if aa is None else aa
    ab = np.count_nonzero(b) if ab is None else ab
    union = aa + ab - inter
    return inter / union if union else 0.0


def coarse_fit(ref, ren, max_shift=40):
    """Cheap (dx, dy) search at quarter resolution, scored at full resolution.

    Used for the view assignment, where 72 candidate pairings have to be scored
    and a two-pixel error in the offset cannot change which panel wins.
    """
    if not ref.any() or not ren.any():
        return 0, 0, 0.0
    f = 4
    r4, n4 = np.ascontiguousarray(ref[::f, ::f]), np.ascontiguousarray(ren[::f, ::f])
    a4, b4 = np.count_nonzero(r4), np.count_nonzero(n4)
    rad = max(1, max_shift // f)
    best = (0, 0, _iou_shift(r4, n4, 0, 0, a4, b4))
    for dy in range(-rad, rad + 1, 2):
        for dx in range(-rad, rad + 1, 2):
            v = _iou_shift(r4, n4, dx, dy, a4, b4)
            if v > best[2]:
                best = (dx, dy, v)
    for dy in (best[1] - 1, best[1], best[1] + 1):
        for dx in (best[0] - 1, best[0], best[0] + 1):
            v = _iou_shift(r4, n4, dx, dy, a4, b4)
            if v > best[2]:
                best = (dx, dy, v)
    dx, dy = best[0] * f, best[1] * f
    return dx, dy, _iou_shift(ref, ren, dx, dy)


def self_mirror_iou(mask, max_shift=40):
    """How left-right symmetric one silhouette is, against itself.

    Flip the mask about a vertical axis and find the axis position that fits it
    best.  Unlike comparing two *different* viewpoints, this says something
    about the object: 1.0 means perfectly symmetric in this projection, and the
    reference's contrapposto, holstered Zapper and swung braids pull the sculpt
    well below that.

    This exists because the obvious test does not work.  Under an orthographic
    camera the silhouette at yaw y+180 is *exactly* the mirror of the one at
    yaw y for any object whatsoever -- the shadow of a solid does not depend on
    which side of it you stand -- so comparing opposite views measures the
    projection, not the model.  Comparing a single view with itself does not
    have that degeneracy.

    Returns (iou, axis_offset_px) where the offset is how far the best mirror
    axis sits from the silhouette's centroid; shifting the flipped copy by dx
    moves the axis by dx/2.
    """
    if mask is None or not mask.any():
        return None, 0.0
    flipped = np.ascontiguousarray(mask[:, ::-1])
    a = np.count_nonzero(mask)
    best_dx, best = 0, _iou_shift(mask, flipped, 0, 0, a, a)
    for dx in range(-max_shift, max_shift + 1):
        v = _iou_shift(mask, flipped, dx, 0, a, a)
        if v > best:
            best_dx, best = dx, v
    return float(best), best_dx / 2.0


def refine_offset(ref, ren, max_shift=40):
    """Best (dx, dy) for the render, in canvas px, maximising IoU.

    Centroid + sole alignment is deliberately dumb so that it cannot launder a
    real error; this refinement is applied *afterwards* and reported on its own
    so a figure that is simply mounted off-centre reads as an offset finding
    rather than smearing into every width band.
    """
    if not ref.any() or not ren.any():
        return 0, 0, 0.0
    aa, ab = np.count_nonzero(ref), np.count_nonzero(ren)
    cx, cy, _ = coarse_fit(ref, ren, max_shift)
    bx, by, bv = cx, cy, _iou_shift(ref, ren, cx, cy, aa, ab)
    for step in (2, 1):
        improved = True
        while improved:
            improved = False
            for dy in (by - step, by, by + step):
                for dx in (bx - step, bx, bx + step):
                    if abs(dx) > max_shift or abs(dy) > max_shift:
                        continue
                    v = _iou_shift(ref, ren, dx, dy, aa, ab)
                    if v > bv + 1e-9:
                        bx, by, bv, improved = dx, dy, v, True
    return bx, by, bv


# --------------------------------------------------------------------------
# run decomposition
# --------------------------------------------------------------------------

def runs_of(mask):
    """Every horizontal run as parallel arrays (row, x0, x1_exclusive)."""
    H, W = mask.shape
    p = np.zeros((H, W + 2), np.int8)
    p[:, 1:-1] = mask
    d = np.diff(p, axis=1)
    sr, sc = np.nonzero(d == 1)
    er, ec = np.nonzero(d == -1)
    return sr, sc, ec


def row_stats(mask):
    """Per-row extent, largest run, total material and run count."""
    H, W = mask.shape
    sr, sc, ec = runs_of(mask)
    w = (ec - sc).astype(np.int32)
    st = {
        "nrun": np.bincount(sr, minlength=H).astype(np.int32),
        "sum_w": np.bincount(sr, weights=w, minlength=H).astype(np.float32),
        "full_x0": np.zeros(H, np.int32), "full_x1": np.zeros(H, np.int32),
        "core_x0": np.zeros(H, np.int32), "core_x1": np.zeros(H, np.int32),
        "full_w": np.zeros(H, np.float32), "core_w": np.zeros(H, np.float32),
        "_runs": (sr, sc, ec, w),
    }
    if sr.size == 0:
        return st
    first = np.nonzero(np.diff(sr, prepend=-1) != 0)[0]
    last = np.nonzero(np.diff(sr, append=-1) != 0)[0]
    st["full_x0"][sr[first]] = sc[first]
    st["full_x1"][sr[last]] = ec[last]
    st["full_w"] = (st["full_x1"] - st["full_x0"]).astype(np.float32)

    order = np.lexsort((w, sr))
    sr2, sc2, ec2, w2 = sr[order], sc[order], ec[order], w[order]
    big = np.nonzero(np.diff(sr2, append=-1) != 0)[0]
    st["core_x0"][sr2[big]] = sc2[big]
    st["core_x1"][sr2[big]] = ec2[big]
    st["core_w"][sr2[big]] = w2[big]
    st["_core_idx"] = order[big]
    return st


def _mask_from_runs(sr, sc, ec, shape):
    H, W = shape
    acc = np.zeros((H, W + 1), np.int32)
    np.add.at(acc, (sr, sc), 1)
    np.add.at(acc, (sr, ec), -1)
    return np.cumsum(acc, axis=1)[:, :W] > 0


def core_mask(mask, st=None):
    """Only the widest run of each row: torso and head above the crotch, the
    nearer leg below it.  Braid-blind by construction."""
    st = st or row_stats(mask)
    sr, sc, ec, _ = st["_runs"]
    if sr.size == 0:
        return np.zeros_like(mask)
    idx = st["_core_idx"]
    return _mask_from_runs(sr[idx], sc[idx], ec[idx], mask.shape)


def debraid_mask(mask, st=None, braid_px=43.0, ratio=0.45):
    """Drop thin lateral runs -- in practice the braids, the Zapper and the
    loose straps -- while keeping arms and both legs.

    A run survives if it is the row's widest, or at least ``braid_px`` wide, or
    at least ``ratio`` of the widest run in its row.  The first clause keeps
    arms (about 50 px at FIG_H=1024) and the second keeps the far leg in a
    three-quarter view; a braid is 17-36 px and fails both.  It cannot separate
    a braid that lies *on* the body, which is the back view -- see SCOREBOARD.
    """
    st = st or row_stats(mask)
    sr, sc, ec, w = st["_runs"]
    if sr.size == 0:
        return np.zeros_like(mask)
    cw = st["core_w"][sr]
    keep = (w >= braid_px) | (w >= ratio * cw) | (w >= cw)
    if not keep.any():
        return np.zeros_like(mask)
    return _mask_from_runs(sr[keep], sc[keep], ec[keep], mask.shape)


def debraid_stats(mask, st=None, braid_px=43.0, ratio=0.45):
    st = st or row_stats(mask)
    sr, sc, ec, w = st["_runs"]
    if sr.size == 0:
        return st, np.zeros_like(mask)
    cw = st["core_w"][sr]
    keep = (w >= braid_px) | (w >= ratio * cw) | (w >= cw)
    m = _mask_from_runs(sr[keep], sc[keep], ec[keep], mask.shape) if keep.any() \
        else np.zeros_like(mask)
    return row_stats(m), m


# --------------------------------------------------------------------------
# width profiles
# --------------------------------------------------------------------------

def band_edges(nbands):
    return np.linspace(0.0, 1.0, nbands + 1)


def band_centres(nbands):
    e = band_edges(nbands)
    return 0.5 * (e[:-1] + e[1:])


def _fig_rows():
    """Canvas rows covering the figure, ordered bottom (t=0) to top (t=1)."""
    return np.arange(BASE_Y - 1, TOP_Y - 1, -1)


def width_profile(st, nbands=40):
    """Median width in each of ``nbands`` equal height slabs, bottom-up.

    Median, not mean: a single row that clips a boot lace or a stray matte
    speck should not move a band.  Widths come back in px on the FIG_H canvas,
    which is also permille of figure height.
    """
    rows = _fig_rows()
    full = st["full_w"][rows]
    core = st["core_w"][rows]
    tot = st["sum_w"][rows]
    nrn = st["nrun"][rows].astype(np.float32)
    k = np.minimum((np.arange(FIG_H) * nbands) // FIG_H, nbands - 1)
    out = {"full": np.zeros(nbands), "core": np.zeros(nbands),
           "sum": np.zeros(nbands), "nrun": np.zeros(nbands)}
    for i in range(nbands):
        sel = k == i
        if not sel.any():
            continue
        out["full"][i] = float(np.median(full[sel]))
        out["core"][i] = float(np.median(core[sel]))
        out["sum"][i] = float(np.median(tot[sel]))
        out["nrun"][i] = float(np.median(nrn[sel]))
    return out


def row_series(st):
    """Full-resolution bottom-up per-row arrays, for landmark detection."""
    rows = _fig_rows()
    return {"full": st["full_w"][rows].astype(np.float32),
            "core": st["core_w"][rows].astype(np.float32),
            "sum": st["sum_w"][rows].astype(np.float32),
            "nrun": st["nrun"][rows].astype(np.int32)}


def _smooth(a, k=15):
    if k <= 1:
        return a
    ker = np.ones(k, np.float32) / k
    pad = k // 2
    return np.convolve(np.pad(a, pad, mode="edge"), ker, mode="valid")[:a.size]


# --------------------------------------------------------------------------
# landmarks
# --------------------------------------------------------------------------

# Priors are the *search windows*, not the answers.  They come from
# spec/jinx.json heights divided by the 1.72 m figure height, opened up wide
# enough that a badly proportioned render still lands inside them.
PRIOR = {
    "shoulder": (0.70, 0.885),
    "waist":    (0.60, 0.780),
    "hip":      (0.45, 0.680),
    "crotch":   (0.40, 0.640),
    "knee":     (0.25, 0.430),
    "ankle":    (0.05, 0.170),
}

LANDMARK_ORDER = ["head_top", "chin", "neck", "shoulder", "waist", "hip",
                  "crotch", "knee", "ankle", "sole"]


def _idx(t):
    return int(round(np.clip(t, 0.0, 1.0) * (FIG_H - 1)))


def _t(i):
    return float(np.clip(i, 0, FIG_H - 1)) / (FIG_H - 1)


def _extremum(a, lo, hi, mode):
    """Middle of the extremal plateau, not the first pixel that touches it.

    A waist or a hip is a broad flat stretch of the profile; a bare argmin can
    sit anywhere along it, so one pixel of matte doubt makes the landmark jump
    ten percent of the figure.  Taking the centre of the contiguous run that is
    within a whisker of the extreme value makes the reading repeatable.
    """
    i0, i1 = _idx(lo), _idx(hi)
    if i1 <= i0:
        return None
    seg = np.asarray(a[i0:i1 + 1], np.float64)
    if seg.size == 0 or seg.max() <= 0:
        return None
    if mode == "max":
        v = float(seg.max())
        ok = seg >= v - max(0.5, 0.005 * v)
        star = int(np.argmax(seg))
    else:
        v = float(seg.min())
        ok = seg <= v + max(0.5, 0.005 * max(v, 1.0))
        star = int(np.argmin(seg))
    idx = np.nonzero(ok)[0]
    if idx.size == 0:
        return i0 + star
    groups = np.split(idx, np.nonzero(np.diff(idx) != 1)[0] + 1)
    g = next((gr for gr in groups if gr[0] <= star <= gr[-1]), groups[0])
    return i0 + int(round(0.5 * (float(g[0]) + float(g[-1]))))


def _argmin_band(a, lo, hi):
    return _extremum(a, lo, hi, "min")


def _argmax_band(a, lo, hi):
    return _extremum(a, lo, hi, "max")


def landmarks(series, dbr_series=None, window=None):
    """Read the classic proportion landmarks off one width profile.

    ``window`` narrows every search to +/- that much around a previously
    measured value (used to hunt the render inside the band the reference
    landed in) so the deltas stay like-for-like instead of the render's search
    latching onto a different feature.
    """
    core = _smooth(series["core"], 15)
    dbr = dbr_series["nrun"] if dbr_series is not None else series["nrun"]
    out = {}
    bnd = {}          # the search window each landmark actually used

    half = (window or {}).get("_w", 0.10)

    def band(name, default):
        """Narrow -- never widen -- the prior around a measured reference value.

        Widening is what makes a render's search latch onto a *different*
        feature and report a bogus 10%-of-height jump, so the window is always
        intersected with the prior.
        """
        if not window or window.get(name) is None:
            return default
        c = float(window[name])
        lo = max(default[0], c - half)
        hi = min(default[1], c + half)
        return (lo, hi) if hi > lo else default

    # Shoulder: the highest row still carrying most of the upper body's width.
    lo, hi = band("shoulder", PRIOR["shoulder"])
    bnd["shoulder"] = (lo, hi)
    i0, i1 = _idx(max(0.50, lo - 0.12)), _idx(hi)
    cmax = float(core[i0:i1 + 1].max()) if i1 > i0 else 0.0
    sh = None
    if cmax > 0:
        j0, j1 = _idx(lo), _idx(hi)
        cand = np.nonzero(core[j0:j1 + 1] >= 0.72 * cmax)[0]
        if cand.size:
            sh = j0 + int(cand.max())
    out["shoulder"] = sh

    # Neck: the pinch just above the shoulder line.
    nk = None
    if sh is not None:
        lo, hi = _t(sh) + 0.005, min(1.0, _t(sh) + 0.105)
        bnd["neck"] = (lo, hi)
        nk = _argmin_band(core, lo, hi)
    if window is not None and window.get("neck") is not None:
        lo, hi = band("neck", (0.80, 0.90))
        nk2 = _argmin_band(core, lo, hi)
        if nk2 is not None:
            nk, bnd["neck"] = nk2, (lo, hi)
    out["neck"] = nk

    # Chin: where the head flares back out above the neck.
    ch = None
    if nk is not None:
        a, b = _idx(_t(nk)), _idx(min(1.0, _t(nk) + 0.085))
        bnd["chin"] = (_t(a + 1), _t(b))
        if b > a + 2:
            g = np.diff(core[a:b + 1])
            ch = a + int(np.argmax(g)) + 1
    out["chin"] = ch

    # Head top: highest row still half as wide as the head's widest point.
    ht = None
    ref_i = nk if nk is not None else _idx(0.83)
    seg = core[ref_i:]
    if seg.size:
        hw = float(seg.max())
        if hw > 0:
            cand = np.nonzero(seg >= 0.5 * hw)[0]
            if cand.size:
                ht = ref_i + int(cand.max())
    out["head_top"] = ht

    lo, hi = band("hip", PRIOR["hip"])
    bnd["hip"] = (lo, hi)
    hip = _argmax_band(core, lo, hi)
    out["hip"] = hip

    # Waist, knee and ankle are all "the narrowest row between two bulges".
    # Defined that way they survive a badly proportioned render, where a fixed
    # window would slide off the pinch and report a phantom 10%-of-height move.
    def pinch(name, lo_i, hi_i, fallback):
        if lo_i is not None and hi_i is not None and hi_i > lo_i + 4:
            lo, hi = _t(lo_i), _t(hi_i)
        else:
            lo, hi = fallback
        # Between the calf and the thigh a profile view often has two almost
        # equal minima -- the boot cuff and the knee -- and one pixel of matte
        # doubt flips which one wins.  Once the reference has chosen, hold the
        # render to the same neighbourhood so the delta stays like-for-like.
        if window and window.get(name) is not None:
            c = float(window[name])
            lo2, hi2 = max(lo, c - half), min(hi, c + half)
            if hi2 > lo2:
                lo, hi = lo2, hi2
        bnd[name] = (lo, hi)
        return _argmin_band(core, lo, hi)

    out["waist"] = pinch("waist", hip, sh, PRIOR["waist"])
    calf = _argmax_band(core, 0.17, 0.31)
    thigh = _argmax_band(core, 0.40, 0.55)
    out["knee"] = pinch("knee", calf, thigh, PRIOR["knee"])
    foot = _argmax_band(core, 0.0, 0.06)
    cuff = _argmax_band(core, 0.14, 0.30)
    out["ankle"] = pinch("ankle", foot, cuff, PRIOR["ankle"])

    # Crotch: the highest sustained row where the de-braided silhouette splits
    # into two runs.  Side views never split, and that is reported as absent
    # rather than guessed.
    lo, hi = band("crotch", PRIOR["crotch"])
    if out["hip"] is not None:
        hi = min(hi, _t(out["hip"]))
    bnd["crotch"] = (lo, hi)
    i0, i1 = _idx(lo), _idx(hi)
    i1 = max(i1, i0 + 1)
    # Scan upward and keep the highest row that still has 18 unbroken split
    # rows beneath it: that is the top of the leg split, not the bottom.
    split = dbr >= 2
    cr = None
    run = 0
    for i in range(i0, min(i1 + 1, FIG_H)):
        run = run + 1 if split[i] else 0
        if run >= 18:
            cr = i
    out["crotch"] = cr

    out["sole"] = 0
    res, flags = {}, {}
    for k in LANDMARK_ORDER:
        v = out.get(k)
        res[k] = None if v is None else _t(v)
        # A result sitting on its own search boundary has not been *found*, it
        # has been clamped; say so rather than letting it read as a measurement.
        edge = False
        if v is not None and k in bnd:
            lo, hi = bnd[k]
            edge = (abs(_t(v) - lo) < 0.012) or (abs(_t(v) - hi) < 0.012)
        flags[k] = {"missing": v is None, "at_edge": bool(edge)}
    return res, flags


# --------------------------------------------------------------------------
# contour metrics
# --------------------------------------------------------------------------

def contour_of(mask):
    m = mask.astype(np.uint8)
    er = cv2.erode(m, np.ones((3, 3), np.uint8), iterations=1)
    return (m - er).astype(bool)


def distance_to(mask_contour):
    src = np.where(mask_contour, 0, 255).astype(np.uint8)
    return cv2.distanceTransform(src, cv2.DIST_L2, 3)


def contour_metrics(ref, ren, tols=(2, 4, 8, 16)):
    """Symmetric Chamfer + tolerant edge F, both in FIG_H px (= permille)."""
    cr, cn = contour_of(ref), contour_of(ren)
    out = {"chamfer_px": None, "chamfer_pct": None, "edge_f": {}}
    if not cr.any() or not cn.any():
        return out
    dr, dn = distance_to(cr), distance_to(cn)
    a = float(dn[cr].mean())          # ref -> render
    b = float(dr[cn].mean())          # render -> ref
    out["chamfer_ref_to_render_px"] = a
    out["chamfer_render_to_ref_px"] = b
    out["chamfer_px"] = 0.5 * (a + b)
    out["chamfer_pct"] = 100.0 * out["chamfer_px"] / FIG_H
    out["chamfer_p95_px"] = float(max(np.percentile(dn[cr], 95),
                                      np.percentile(dr[cn], 95)))
    out["chamfer_p95_pct"] = 100.0 * out["chamfer_p95_px"] / FIG_H
    for t in tols:
        p = float((dr[cn] <= t).mean())
        r = float((dn[cr] <= t).mean())
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        out["edge_f"]["%d" % t] = {"tol_px": int(t),
                                   "tol_pct": 100.0 * t / FIG_H,
                                   "precision": p, "recall": r, "f": f}
    return out


def overlap_metrics(ref, ren):
    inter = np.count_nonzero(ref & ren)
    ar, an = np.count_nonzero(ref), np.count_nonzero(ren)
    union = ar + an - inter
    return {
        "iou": inter / union if union else 0.0,
        "precision": inter / an if an else 0.0,   # low => render too fat
        "recall": inter / ar if ar else 0.0,      # low => render too thin
        "dice": 2 * inter / (ar + an) if (ar + an) else 0.0,
        "area_ref_px": int(ar), "area_render_px": int(an),
        "area_ratio": an / ar if ar else 0.0,
    }


# --------------------------------------------------------------------------
# assignment
# --------------------------------------------------------------------------

def hungarian(cost):
    """Minimum-cost one-to-one assignment, rows -> columns.

    Written out because scipy is not available here.  This is the O(n^3)
    potentials form; n is at most a handful of views so it is instant.
    Returns a list of length n_rows with the chosen column, or -1.
    """
    cost = np.asarray(cost, dtype=np.float64)
    n, m = cost.shape
    transposed = False
    if n > m:
        cost = cost.T
        n, m = m, n
        transposed = True
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    res = [-1] * n
    for j in range(1, m + 1):
        if p[j] > 0:
            res[p[j] - 1] = j - 1
    if transposed:
        back = [-1] * m
        for i, j in enumerate(res):
            if j >= 0:
                back[j] = i
        return back
    return res
