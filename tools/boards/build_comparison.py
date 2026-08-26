#!/usr/bin/env python
"""
Board 1 - the three-column comparison.

Builds two versions of the same design:

  comparison_full.png  rows front / her left / back  x  cols reference / jinx3js / img2threejs
                       LOCAL REVIEW ONLY. Contains the artist's reference turnaround and
                       route 2's textured renders, which bake albedo extracted from it.

  comparison_pub.png   the same design with every reference-derived panel gone: the
                       reference column is dropped and route 2 is shown geometry-only.
                       A footer on the board states why.

Composition is numpy/cv2. Text is PIL only because cv2's Hershey vector fonts are not
legible at the 11-13px caption size the house style calls for.

Run from anywhere; paths resolve relative to the project root inferred from this file.
"""

import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = HERE


def P(*parts):
    return os.path.join(ROOT, *parts)


# ---------------------------------------------------------------- design constants
# Ground: a warm near-white "paper". Deliberately NOT #ffffff -- the geometry-only clay
# renders peak at luminance ~229 and sit at ~190 median, so a pure-white ground would let
# their lit faces dissolve into it. 243/242/239 keeps ~50 levels under the clay's mass
# while still reading as a white board, and its warmth sits well against the character's
# cool blue/purple palette.
GROUND_RGB = (243, 242, 239)

CAPTION_RGB = (124, 121, 114)   # muted warm grey, ~4.4:1 on the ground
TITLE_RGB = (88, 86, 80)
FOOTER_RGB = (138, 135, 128)

FIG_H = 480          # pixels per figure height -- IDENTICAL on both boards, every cell
CAP_GAP = 15         # figure bottom -> caption top
CAP_SIZE = 12
CAP_LINE = 15
ROW_GAP = 46
MARGIN_TOP = 76
MARGIN_BOT = 76
TITLE_SIZE = 13
TITLE_BLOCK = 53     # title line + gap down to the first row of figures
FOOTER_SIZE = 12
FOOTER_LINE = 17
FOOTER_GAP = 42

# Segoe UI: humanist sans, hinted, stays legible down at 12px. Title uses the same face
# as the captions -- hierarchy comes from colour, not from a second weight.
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEMI = r"C:\Windows\Fonts\segoeui.ttf"

# ---------------------------------------------------------------- view mapping (pinned)
# reference panel _2 = front, _0 = her left, _5 = back
# render yaw 0 = front, yaw 90 = her left, yaw 180 = back
ROWS = [
    ("front",    "body_2", 0),
    ("her left", "body_0", 90),
    ("back",     "body_5", 180),
]

# Scores are fixed by the independent scoreboard. Route 1 = 41.21, route 2 = 38.53.
SCORE_R1 = "41.2"
SCORE_R2 = "38.5"


# ---------------------------------------------------------------- image helpers
# Any source path containing one of these segments is reference-derived and must never
# reach the published board. Checked as a hard assertion at build time rather than left
# to the correctness of the column table above.
REF_DERIVED = (
    os.path.join("jinx-i2t", "ref"),
    os.path.join("jinx-i2t", "out", "final") + os.sep,   # textured route 2
    os.path.join("jinx-i2t", "delit"),
)


def assert_publishable(path):
    norm = os.path.normpath(path)
    for bad in REF_DERIVED:
        if bad in norm:
            raise AssertionError(
                "reference-derived panel would reach the published board: %s" % norm)


def load_rgba(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    if im.ndim != 3 or im.shape[2] != 4:
        raise ValueError("expected RGBA: %s" % path)
    return im


def normalise(path, fig_h=FIG_H, thresh=8):
    """Crop to the alpha bbox and scale so the figure is exactly fig_h tall.

    Every source has a different native size and crop -- reference panels are cropped to
    their subject at ~1200-1300px, route 1 is 620x1100, route 2 is 500x900 -- so each
    figure has to be normalised on its own alpha extent before it can sit beside another.

    Returns (premultiplied_bgr_float, alpha_float), both already scaled.
    """
    im = load_rgba(path)
    a = im[:, :, 3]
    ys, xs = np.where(a > thresh)
    if len(ys) == 0:
        raise ValueError("empty alpha: %s" % path)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    crop = im[y0:y1 + 1, x0:x1 + 1].astype(np.float32) / 255.0

    bgr = crop[:, :, :3]
    al = crop[:, :, 3:4]
    pre = bgr * al                      # premultiply BEFORE resampling so the soft edge
                                        # does not drag in whatever RGB sits under a=0

    h = crop.shape[0]
    scale = fig_h / float(h)
    w = max(1, int(round(crop.shape[1] * scale)))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    pre = cv2.resize(pre, (w, fig_h), interpolation=interp)
    al = cv2.resize(al, (w, fig_h), interpolation=interp)
    if al.ndim == 2:
        al = al[:, :, None]
    return pre, al


def paste(canvas, pre, al, cx, top):
    """Composite a premultiplied figure onto the canvas, centred on cx, top at `top`."""
    h, w = al.shape[:2]
    x = int(round(cx - w / 2.0))
    y = int(top)
    H, W = canvas.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sp = pre[y0 - y:y1 - y, x0 - x:x1 - x]
    sa = al[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = canvas[y0:y1, x0:x1]
    canvas[y0:y1, x0:x1] = sp + dst * (1.0 - sa)


# ---------------------------------------------------------------- text helpers
def _font(path, size):
    """Load a TTF. A silent fallback to PIL's default bitmap face would wreck the
    typography without failing, so say so loudly instead of swallowing it."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        print("    WARNING: font not found, falling back to bitmap default: %s" % path)
        return ImageFont.load_default()


def draw_text(draw, xy, text, font, rgb, track=0.0):
    """Draw text with optional letter tracking. Small type reads better with a little."""
    x, y = xy
    if track == 0.0:
        draw.text((x, y), text, font=font, fill=rgb)
        return
    for ch in text:
        draw.text((x, y), ch, font=font, fill=rgb)
        x += draw.textlength(ch, font=font) + track


# ---------------------------------------------------------------- board builder
def build(kind):
    """kind == 'full' or 'pub'."""
    pub = (kind == "pub")

    if pub:
        # Reference column dropped entirely. Route 2 shown geometry-only.
        cols = [
            ("jinx3js", lambda yaw: P("jinx3js", "out", "views", "render_yaw%d.png" % yaw)),
            ("img2threejs geometry",
             lambda yaw: P("jinx-i2t", "out", "final_clay", "render_yaw%d.png" % yaw)),
        ]
        col_w = 260
        margin_x = 110
        title = "two reconstruction routes  ·  front, her left, back"
    else:
        cols = [
            ("reference", lambda yaw: None),   # filled per-row from the panel index
            ("jinx3js", lambda yaw: P("jinx3js", "out", "views", "render_yaw%d.png" % yaw)),
            ("img2threejs",
             lambda yaw: P("jinx-i2t", "out", "final", "render_yaw%d.png" % yaw)),
        ]
        col_w = 200
        margin_x = 92
        title = "reference against two reconstruction routes  ·  front, her left, back"

    ncol = len(cols)
    row_block = FIG_H + CAP_GAP + CAP_LINE
    grid_h = row_block * len(ROWS) + ROW_GAP * (len(ROWS) - 1)

    # Resolve every panel up front. The widest figure on the board (at FIG_H) defines the
    # cell box; the cell is centred in the column pitch and captions left-align to the
    # CELL, not to the pitch. Anchoring captions to the pitch leaves them stranded far to
    # the left of the narrower side views.
    panels = {}
    missing = []
    for ri, (view, ref_stem, yaw) in enumerate(ROWS):
        for ci, (label, resolver) in enumerate(cols):
            if label == "reference":
                path = P("jinx-i2t", "ref", "views", ref_stem + ".png")
            else:
                path = resolver(yaw)
            if pub:
                assert_publishable(path)
            try:
                panels[(ci, ri)] = normalise(path)
            except Exception as exc:            # noqa: BLE001
                missing.append((path, str(exc)))
    cell_w = max((al.shape[1] for _, al in panels.values()), default=FIG_H // 3)

    footer_lines = []
    if pub:
        footer_lines = [
            "the reference turnaround is a measurement target and is not redistributed.",
            "route 2's textures bake albedo extracted from it, so only its geometry ships here.",
            "route 1's materials are procedural terms written in typescript, so it is shown textured.",
        ]
    else:
        footer_lines = [
            "full version. contains the reference turnaround and route 2's reference-derived",
            "textures. local review only -- not for redistribution.",
        ]

    W = col_w * ncol + margin_x * 2
    footer_h = FOOTER_GAP + FOOTER_LINE * len(footer_lines)
    H = MARGIN_TOP + TITLE_BLOCK + grid_h + footer_h + MARGIN_BOT

    ground = np.array(GROUND_RGB[::-1], np.float32) / 255.0   # BGR
    canvas = np.ones((H, W, 3), np.float32) * ground

    cells = []   # (caption_x, caption_y, caption)

    grid_top = MARGIN_TOP + TITLE_BLOCK
    for ri, (view, ref_stem, yaw) in enumerate(ROWS):
        top = grid_top + ri * (row_block + ROW_GAP)
        for ci, (label, resolver) in enumerate(cols):
            cell_x = margin_x + ci * col_w + (col_w - cell_w) / 2.0
            cx = cell_x + cell_w / 2.0
            got = panels.get((ci, ri))
            if got is not None:
                paste(canvas, got[0], got[1], cx, top)

            cap = "%s  %s" % (label, view)
            # The score belongs to the route, not to a view, so it is stated once per
            # route -- in the top row, where the route is first named.
            if ri == 0 and label == "jinx3js":
                cap += "   " + SCORE_R1
            elif ri == 0 and label.startswith("img2threejs"):
                cap += "   " + SCORE_R2
            cells.append((cell_x, top + FIG_H + CAP_GAP, cap))

    # ---- text pass
    img = Image.fromarray(cv2.cvtColor((np.clip(canvas, 0, 1) * 255).astype(np.uint8),
                                       cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    f_cap = _font(FONT_REG, CAP_SIZE)
    f_title = _font(FONT_SEMI, TITLE_SIZE)
    f_foot = _font(FONT_REG, FOOTER_SIZE)

    draw_text(d, (margin_x, MARGIN_TOP), title, f_title, TITLE_RGB, track=0.25)

    for cap_x, cap_y, cap in cells:
        draw_text(d, (cap_x, cap_y), cap, f_cap, CAPTION_RGB, track=0.2)

    fy = grid_top + grid_h + FOOTER_GAP
    for i, line in enumerate(footer_lines):
        draw_text(d, (margin_x, fy + i * FOOTER_LINE), line, f_foot, FOOTER_RGB, track=0.2)

    out_path = os.path.join(OUT, "comparison_%s.png" % kind)
    Image.Image.save(img, out_path)
    return out_path, img.size, missing


def main():
    os.makedirs(OUT, exist_ok=True)
    for kind in ("full", "pub"):
        path, size, missing = build(kind)
        on_disk = os.path.getsize(path)
        print("%-24s %s  %dx%d px  %.1f KB" % (
            os.path.basename(path), path, size[0], size[1], on_disk / 1024.0))
        for m in missing:
            print("    COULD NOT SOURCE: %s  (%s)" % m)


if __name__ == "__main__":
    main()
