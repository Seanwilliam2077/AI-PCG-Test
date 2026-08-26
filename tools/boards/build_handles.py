#!/usr/bin/env python
"""
Board 4 - the edit handles.

Four of the eight handles CONTRACT.md section 8 declares, each swept across three values.
Every cell is the same TypeScript factory called with one number changed; nothing is
posed, retouched or hand-placed between columns.

This is the board that shows what a code-native asset buys, because the interesting part
of each row is what does NOT change. The lattice row varies the opening count and the
collar's outer envelope holds to under half a millimetre. The ring row varies the muzzle
ring count and the collar's axial extent is identical to the micron. That invariance is
the whole claim, and it is measurable rather than a matter of looking -- the figures under
each row come from `zapper-i2t/tools/locality_test.py`, not from this script.

Unlike the character boards there is no `_full` / `_pub` split here. The pistol's finish
is generated from measured CIE Lab scalars: every texture on it is a CanvasTexture or a
DataTexture drawn in TypeScript, and no image file is loaded anywhere in `src/`. So the
fully textured renders are publishable as they stand, which is not true of the character.
That is asserted at build time below rather than trusted.

    python tools/boards/build_handles.py
"""

import json
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "out", "boards")
SWEEP = os.path.join(ROOT, "zapper-i2t", "out", "sweep")
LOCALITY = os.path.join(ROOT, "zapper-i2t", "out", "locality_report.json")
SRC = os.path.join(ROOT, "zapper-i2t", "src")

F_REG = "C:/Windows/Fonts/segoeui.ttf"
F_SB = "C:/Windows/Fonts/seguisb.ttf"

TITLE_PX, SUB_PX, LABEL_PX, CAP_PX, FOOT_PX = 26, 14, 16, 13, 13
C_TITLE = (0xE8, 0xE8, 0xEE)
C_SUB = (0x76, 0x76, 0x86)
C_LABEL = (0xA6, 0xA6, 0xB6)
C_CAP = (0x82, 0x82, 0x90)
C_HOLD = (0x7C, 0x94, 0x88)     # the "what did not move" figure, faintly green
C_FOOT = (0x6E, 0x6E, 0x7E)
GROUND = (0x0E, 0x0F, 0x13)

COLS = 3
FIG_BUDGET_H = 250    # tallest a cell may be; the real height falls out of the scale
CELL_W = 470
CELL_PAD = 18         # keeps neighbouring cells from touching at the widest column
MARGIN = 96
TOP = 76
TITLE_H = 34
TITLE_GAP = 12
SUB_H = 19
HEAD_GAP = 44
LABEL_H = 22
CAP_GAP = 13
CAP_H = 19
ROW_GAP = 40
FOOT_GAP = 40
BOTTOM = 74


ROWS = [
    {
        "label": "H4   lattice.opening.count",
        "cells": [("lat12", "12 openings"), ("lat16", "16  \u2014  contract default"),
                  ("lat20", "20 openings")],
        "hold": "collar envelope unchanged: rim faces move 0.00 mm across all three",
    },
    {
        "label": "H6   muzzle.collar.rings",
        "cells": [("ring2", "2 rings"), ("ring3", "3  \u2014  contract default"),
                  ("ring4", "4 rings")],
        "hold": "collar axial extent 179.8\u2013212.0 mm in all three, to the micron",
    },
    {
        "label": "H3   grip.rake",
        "cells": [("rakeN", "\u221210\u00b0"), ("rake0", "0\u00b0  \u2014  contract default"),
                  ("rakeP", "+10\u00b0")],
        "hold": "frame, trigger, guard and barrel all hold; pivot is DECLARED, not fitted",
    },
    {
        "label": "H1   barrel.length",
        "cells": [("len0", "+0 mm"), ("len15", "+15 mm"), ("len30", "+30 mm")],
        "hold": "deformation confined to the one plain cylinder; lattice and frame hold",
    },
]


def load_rgba(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    if im.ndim != 3 or im.shape[2] != 4:
        raise ValueError("expected RGBA: %s" % path)
    return im


def assert_no_sampled_pixels():
    """The pistol's publishability rests on one fact, so check it rather than recite it.

    Every material in `src/` must be generated. A single image import would mean these
    renders carry reference-derived pixels, and the whole board would have to be rebuilt
    the way the character's face figure was.
    """
    bad = []
    for dirpath, _, names in os.walk(SRC):
        for n in names:
            if not n.endswith(".ts"):
                continue
            text = open(os.path.join(dirpath, n), encoding="utf-8").read()
            for marker in ("TextureLoader", "ImageBitmapLoader", ".jpg", ".png",
                           "ref/", "pbr/", "delit/"):
                if marker in text:
                    bad.append("%s: %s" % (n, marker))
    if bad:
        raise AssertionError(
            "the pistol's sources reference image data, so its textured renders are not "
            "publishable as they stand: " + "; ".join(bad))


def crop(tag, thresh=8):
    """Crop one render to its own alpha bbox. No scaling -- see `common_scale`."""
    im = load_rgba(os.path.join(SWEEP, tag, "render_yaw0.png"))
    a = im[:, :, 3]
    ys, xs = np.where(a > thresh)
    if len(ys) == 0:
        raise ValueError("empty render: %s" % tag)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def common_scale(crops):
    """ONE scale factor for every cell on the board.

    Per-cell normalisation is wrong here and not just untidy. Fitting each figure to a
    common height would shrink the +30 mm barrel back to its neighbour's size and erase
    the only thing the H1 row exists to show; fitting to a common width would do the same
    to the grip rake. A single pixels-per-metre across the whole board means a difference
    in the image is a difference in the model, which is the claim being made.
    """
    wmax = max(c.shape[1] for c in crops)
    hmax = max(c.shape[0] for c in crops)
    return min((CELL_W - CELL_PAD * 2) / float(wmax), FIG_BUDGET_H / float(hmax))


def scaled(im, s):
    w = max(1, int(round(im.shape[1] * s)))
    h = max(1, int(round(im.shape[0] * s)))
    im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    al = (im[:, :, 3:4].astype(np.float32) / 255.0)
    return im[:, :, :3].astype(np.float32) * al, al


def wrap(d, text, font, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def paste(canvas, pre, al, cx, top):
    h, w = al.shape[:2]
    x0 = int(round(cx - w / 2.0))
    y0, y1 = top, top + h
    x1 = x0 + w
    if x0 < 0:
        pre, al, x0 = pre[:, -x0:], al[:, -x0:], 0
        w = al.shape[1]
        x1 = x0 + w
    if x1 > canvas.shape[1]:
        cut = x1 - canvas.shape[1]
        pre, al = pre[:, :w - cut], al[:, :w - cut]
        x1 = canvas.shape[1]
    dst = canvas[y0:y1, x0:x1].astype(np.float32)
    canvas[y0:y1, x0:x1] = np.clip(pre + dst * (1.0 - al), 0, 255).astype(np.uint8)


def main():
    assert_no_sampled_pixels()

    loc = json.load(open(LOCALITY, encoding="utf-8"))
    passed, total = loc["passed"], loc["handles"]

    crops = {tag: crop(tag) for r in ROWS for tag, _ in r["cells"]}
    s = common_scale(list(crops.values()))
    fig_h = int(round(max(c.shape[0] for c in crops.values()) * s))

    W = MARGIN * 2 + CELL_W * COLS
    row_h = LABEL_H + fig_h + CAP_GAP + CAP_H + 6 + CAP_H
    grid_top = TOP + TITLE_H + TITLE_GAP + SUB_H + HEAD_GAP
    grid_h = row_h * len(ROWS) + ROW_GAP * (len(ROWS) - 1)

    foot_src = [
        "Jinx's Zapper, rebuilt as a code-native asset. Every cell above is the same "
        "TypeScript factory with one parameter changed — nothing between columns is "
        "posed or retouched, and every cell is drawn at the same pixels-per-metre, so a "
        "difference in the image is a difference in the model.",
        "%d of %d declared edit handles preserve locality under test. Two of them "
        "(lattice, rings) are generation parameters: the handle is a term in the code that "
        "produces the geometry. The other six are transforms scoped to named subtrees, "
        "which is the weaker form and is reported as the weaker form."
        % (passed, total),
        "The must-move and must-not-move lists were written into CONTRACT.md before any "
        "geometry existed. Implementing them falsified two of its own rows — H1 fixes "
        "a face it also asks to move, and H4's move list omits the struts — both "
        "recorded in the locality report rather than quietly resolved.",
        "Finish is generated from measured CIE Lab scalars. No image file is loaded "
        "anywhere in the pistol's sources, which is asserted at build time, so these "
        "textured renders carry no reference pixel.",
    ]

    # Type is measured before the canvas is sized: the footer wraps to the board width, and
    # a board sized before wrapping is how the last version ran a line off its own edge.
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f_foot = ImageFont.truetype(F_REG, FOOT_PX)
    foot = []
    for para in foot_src:
        foot.extend(wrap(probe, para, f_foot, W - MARGIN * 2))
        foot.append("")
    foot = foot[:-1]

    H = grid_top + grid_h + FOOT_GAP + len(foot) * 19 + BOTTOM

    canvas = np.zeros((H, W, 3), np.uint8)
    canvas[:, :] = GROUND[::-1]

    y = grid_top
    for r in ROWS:
        top = y + LABEL_H
        for i, (tag, _) in enumerate(r["cells"]):
            pre, al = scaled(crops[tag], s)
            cx = MARGIN + CELL_W * i + CELL_W / 2.0
            # Bottom-aligned, not centred: the grip is the lowest thing on the object in
            # every cell, so a common baseline keeps the rake row from appearing to bob.
            paste(canvas, pre, al, cx, top + fig_h - al.shape[0])
        y += row_h + ROW_GAP

    img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(F_SB, TITLE_PX)
    f_sub = ImageFont.truetype(F_REG, SUB_PX)
    f_lab = ImageFont.truetype(F_SB, LABEL_PX)
    f_cap = ImageFont.truetype(F_REG, CAP_PX)

    d.text((MARGIN, TOP), "Edit handles", font=f_title, fill=C_TITLE)
    d.text((MARGIN, TOP + TITLE_H + TITLE_GAP),
           "one parameter at a time, and what holds still while it moves",
           font=f_sub, fill=C_SUB)

    y = grid_top
    for r in ROWS:
        d.text((MARGIN, y), r["label"], font=f_lab, fill=C_LABEL)
        cap_y = y + LABEL_H + fig_h + CAP_GAP
        for i, (_, cap) in enumerate(r["cells"]):
            w = d.textlength(cap, font=f_cap)
            d.text((MARGIN + CELL_W * i + CELL_W / 2.0 - w / 2.0, cap_y),
                   cap, font=f_cap, fill=C_CAP)
        d.text((MARGIN, cap_y + CAP_H + 6), "held:  " + r["hold"],
               font=f_cap, fill=C_HOLD)
        y += row_h + ROW_GAP

    fy = grid_top + grid_h + FOOT_GAP
    for line in foot:
        if line:
            d.text((MARGIN, fy), line, font=f_foot, fill=C_FOOT)
        fy += 19

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "handles.png")
    cv2.imwrite(path, cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    print("wrote", path, img.size, "| scale %.3f px/px, figure %d px tall" % (s, fig_h))


if __name__ == "__main__":
    main()
