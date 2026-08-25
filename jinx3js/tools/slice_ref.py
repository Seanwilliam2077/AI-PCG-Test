"""Split an ArtStation turnaround sheet into per-view panels with an alpha matte.

The sheets are figures on a smooth radial grey gradient with a watermark bar at
the bottom.  Background is recovered by iteratively fitting a 2nd-order
polynomial to the pixels that currently look like background, so the matte does
not depend on a hand-picked grey.  Panels are then the connected components,
left to right.

    python tools/slice_ref.py --sheet ref/body_6view.jpg --tag body --n 6
"""
import argparse
import json
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fit_background(img, iters=6, exclude=None):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xs, ys = xs / w, ys / h
    basis = np.stack([np.ones_like(xs), xs, ys, xs * xs, xs * ys, ys * ys], -1).reshape(-1, 6)
    flat = img.reshape(-1, 3).astype(np.float32)
    keep = np.ones(flat.shape[0], bool)
    if exclude is not None:
        keep &= ~(exclude.reshape(-1) > 0)
        if keep.sum() < 6 * 50:
            keep = np.ones(flat.shape[0], bool)
    bg = None
    for _ in range(iters):
        coef, *_ = np.linalg.lstsq(basis[keep], flat[keep], rcond=None)
        bg = basis @ coef
        resid = np.linalg.norm(flat - bg, axis=1)
        lim = max(6.0, np.percentile(resid[keep], 70))
        keep = resid < lim
        if exclude is not None:
            keep &= ~(exclude.reshape(-1) > 0)
    return bg.reshape(h, w, 3)


def matte(img, low=10.0, high=22.0, hole_resid=11.0, exclude=None):
    """Separate figure from the painted backdrop by flooding the backdrop.

    Thresholding a background fit does not work: the sheets paint a soft
    elliptical spotlight behind each figure whose residual overlaps the
    figure's own antialiased edge, and it is contiguous with the figure, so
    hysteresis grows straight into it.  What separates them is that the
    backdrop is smooth while the figure is walled off by a strong gradient, so
    the backdrop is flooded inward from the image border instead.

    The sheets also render a contact shadow onto the backdrop between the legs
    and under the boots.  That pocket is enclosed by the figure, so the flood
    cannot reach it and it survives as a wedge of false silhouette.  A shadow
    is the backdrop scaled down, so it keeps the backdrop's chromaticity and
    only loses luminance -- that is the test used to let the flood through it.
    """
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 1.2)
    grad = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3),
                         cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))

    bg = fit_background(img, exclude=exclude)
    resid = np.linalg.norm(img.astype(np.float32) - bg, axis=2)

    f = img.astype(np.float32) + 1e-3
    k = (f * bg).sum(2) / (bg * bg).sum(2)                 # best scale onto the bg colour
    chroma = np.linalg.norm(f - k[..., None] * bg, axis=2)  # residual off that ray
    shadow = (chroma < 6.0) & (k > 0.45) & (k < 1.04)

    passable = ((grad <= low) | shadow).astype(np.uint8)

    # The flood alone still loses the pocket between the legs: near the crotch
    # and again between the boots the channel pinches shut, so that stretch of
    # plain backdrop is enclosed and never reached.  Judge every passable
    # component on its own colour instead of on whether a path exists -- a
    # component sitting on the background fit is backdrop wherever it is.
    n, lab, stats, _ = cv2.connectedComponentsWithStats(passable, 8)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    is_bg = np.zeros(n, bool)
    for i in range(1, n):
        if i in border:
            is_bg[i] = True
        elif stats[i, cv2.CC_STAT_AREA] >= 300:
            sel = lab == i
            # Enclosed backdrop is backdrop-coloured throughout.  Test that on
            # chromaticity, not on the residual: a braid lying in shadow can sit
            # as close to the fit in absolute terms as the backdrop does, but it
            # is blue, and the backdrop and its shadow never are.
            if shadow[sel].mean() > 0.90:
                is_bg[i] = True
    reached = is_bg[lab]

    m = (~reached).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m, resid


def despeckle(mask, min_area=250):
    out = mask.copy()
    for value, target in ((255, 0), (0, 255)):
        sel = (out == value).astype(np.uint8)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(sel, 8)
        order = np.argsort(-stats[1:, cv2.CC_STAT_AREA]) + 1 if n > 1 else []
        biggest = order[0] if len(order) else -1
        for i in range(1, n):
            if i != biggest and stats[i, cv2.CC_STAT_AREA] < min_area:
                out[lab == i] = target
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--bottom-crop", type=float, default=0.045)
    ap.add_argument("--min-area", type=int, default=12000)
    ap.add_argument("--low", type=float, default=6.0)
    ap.add_argument("--high", type=float, default=22.0)
    ap.add_argument("--speckle", type=int, default=250)
    ap.add_argument("--hole-resid", type=float, default=11.0)
    ap.add_argument("--cut-rows", type=float, nargs=2, default=(0.04, 0.62))
    args = ap.parse_args()

    img = cv2.imread(os.path.join(ROOT, args.sheet))
    h, w = img.shape[:2]
    img = img[: int(h * (1 - args.bottom_crop))]
    h = img.shape[0]

    m, _ = matte(img, args.low, args.high, args.hole_resid)
    n_lab, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n_lab, bool)
    for i in range(1, n_lab):
        if stats[i, cv2.CC_STAT_AREA] >= args.min_area:
            keep[i] = True
    m = np.where(keep[lab], m, 0)

    # Figures in a turnaround are near-evenly spaced but their braids overlap the
    # neighbour, so connected components merge.  Cut at the emptiest column inside
    # a window around each expected boundary instead.
    W = m.shape[1]
    # Place the cuts from the upper body only.  Near the feet the front view's
    # braids splay wide enough to touch the neighbour, so the full-height
    # profile has no gap there at all and the cut lands inside a figure.
    band = m[int(m.shape[0] * args.cut_rows[0]):int(m.shape[0] * args.cut_rows[1])]
    col = cv2.blur((band > 0).astype(np.float32).sum(0).reshape(1, -1), (31, 1)).ravel()
    step = W / args.n
    cuts = [0]
    for i in range(1, args.n):
        c = int(i * step)
        lo, hi = max(1, int(c - 0.34 * step)), min(W - 1, int(c + 0.34 * step))
        cuts.append(lo + int(np.argmin(col[lo:hi])))
    cuts.append(W)

    merged = []
    for i in range(args.n):
        band = m[:, cuts[i]:cuts[i + 1]]
        ys, xs = np.nonzero(band)
        if xs.size < args.min_area // 4:
            continue
        merged.append([cuts[i] + xs.min(), ys.min(), cuts[i] + xs.max() + 1, ys.max() + 1, None])

    # Re-matte each band against a background fit of that band alone.  One fit
    # across all 3000 px cannot track the backdrop closely enough for the
    # colour test below to be sharp, which showed up as holes punched into
    # braids and boots wherever the figure happened to sit near the sheet mean.
    local = np.zeros_like(m)
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        # Fit that band's backdrop from pixels the global pass already called
        # backdrop.  A band is mostly figure, so an unguided robust fit drifts
        # onto figure colour and then the chromaticity test eats holes out of
        # the braids.
        lm, _ = matte(img[:, a:b], args.low, args.high, args.hole_resid,
                      exclude=cv2.dilate(m[:, a:b], np.ones((25, 25), np.uint8)))
        local[:, a:b] = lm
    m = local
    merged = []
    for i in range(args.n):
        band = m[:, cuts[i]:cuts[i + 1]]
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(band, 8)
        big = [j for j in range(1, n2) if st2[j, cv2.CC_STAT_AREA] >= args.min_area]
        if not big:
            continue
        keep2 = np.isin(lab2, big)
        band[~keep2] = 0
        ys, xs = np.nonzero(band)
        merged.append([cuts[i] + xs.min(), ys.min(), cuts[i] + xs.max() + 1, ys.max() + 1, None])

    outdir = os.path.join(ROOT, "ref", "views")
    os.makedirs(outdir, exist_ok=True)
    meta = {"sheet": args.sheet, "tag": args.tag, "sheet_size": [w, h], "panels": []}
    for k, (x0, y0, x1, y1, _ids) in enumerate(merged):
        pad = 12
        X0, Y0 = max(0, x0 - pad), max(0, y0 - pad)
        X1, Y1 = min(img.shape[1], x1 + pad), min(h, y1 + pad)
        crop = img[Y0:Y1, X0:X1]
        sub = m[Y0:Y1, X0:X1].copy()
        rgba = np.dstack([crop, sub])
        # JPEG blocking leaves pin-holes in the braids and pin-dots in the
        # backdrop; both are smaller than any real feature at this resolution.
        sub = despeckle(sub, args.speckle)
        name = f"{args.tag}_{k}.png"
        cv2.imwrite(os.path.join(outdir, name), rgba)
        meta["panels"].append({
            "index": k, "file": f"ref/views/{name}",
            "box": [int(X0), int(Y0), int(X1), int(Y1)],
            "size": [int(X1 - X0), int(Y1 - Y0)],
            "fg_px": int((sub > 0).sum()),
        })
        print(f"{name}  box=({X0},{Y0})-({X1},{Y1})  {X1-X0}x{Y1-Y0}  fg={(sub>0).sum()}")

    with open(os.path.join(ROOT, "ref", f"panels_{args.tag}.json"), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
