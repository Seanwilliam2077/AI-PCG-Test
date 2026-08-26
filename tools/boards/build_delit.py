"""
Board 3 - the de-lighting strip.

Two versions of one plate, on the same saturated magenta ground:

  delit_full.png  four panels: front original / front de-lit /
                  her left side original / her left side de-lit.
                  Every panel is derived from the artist's turnaround.
                  LOCAL REVIEW ONLY - must not be published.

  delit_pub.png   the publishable equivalent. De-lighting is applied to the
                  artist's pixels, so it cannot ship in any form. What ships
                  instead is the same kind of texture plate built around the
                  one texture in this project that is generated rather than
                  sampled: the painted face albedo, shown as the map and as
                  it lands on the model.

Reads only. Writes only into out/boards/.

Run:  python "out/boards/build_delit.py"
"""

import os
import cv2
import numpy as np

# ---------------------------------------------------------------- paths ----

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "out", "boards")


def src(*parts):
    return os.path.join(ROOT, *parts)


# ------------------------------------------------------------ house style --

# One flat ground, filling the canvas. Magenta is the convention for a
# texture-work plate: it is picked precisely because it appears nowhere in
# the subject, so any spill or matte fringe is obvious. Measured against the
# four reference panels, fewer than 0.01% of subject pixels come within a
# euclidean distance of 60 of this value; against the two publishable
# sources, the nearest subject pixel is 90 away.
GROUND = (0x8A, 0x20, 0xE0)          # #E0208A, BGR

# Muted against the ground: same hue family, dropped in value. Contrast with
# the ground is about 4.0:1, which holds at 11-13 px.
INK = (0x22, 0x01, 0x3D)             # #3D0122, BGR
INK_SOFT = (0x3A, 0x0A, 0x5C)        # #5C0A3A, BGR - second caption line

W = 1720                             # both versions share the canvas width,
MARGIN = 110                         # the margins, the column pitch and the
GUTTER = 72                          # type, so they read as one plate.
COLS = 4
COL_W = (W - 2 * MARGIN - (COLS - 1) * GUTTER) // COLS   # 321
FILL = 0.88                          # widest panel as a fraction of the column

TOP = 128                            # top of the content box
CAP_1 = 36                           # first caption baseline below the box
CAP_2 = 58                           # second caption baseline below the box
FOOT_GAP = 74                        # from the second caption to the footer
FOOT_LEAD = 20                       # footer line spacing
BOTTOM = 76                          # below the last footer line

SZ_TITLE = 20
SZ_CAP = 13
SZ_SUB = 11
SZ_FOOT = 12

FONT = cv2.FONT_HERSHEY_DUPLEX
SS = 4                               # text supersampling factor


# ------------------------------------------------------------------ type --

def _scale_for(px):
    """cv2 Hershey ascender height is ~22 px at fontScale 1.0."""
    return px / 22.0


def text(board, s, x, baseline, px, color):
    """Draw ASCII text supersampled and downsampled, so small type stays dense.

    Hershey fonts have no glyphs outside ASCII; anything else silently turns
    into a box. Assert rather than ship a broken caption.
    """
    assert all(ord(c) < 128 for c in s), "non-ascii in caption: %r" % s
    scale = _scale_for(px) * SS
    thick = max(1, int(round(SS * 0.30 * (px / 12.0))))
    (tw, th), base = cv2.getTextSize(s, FONT, scale, thick)
    pad = SS * 4
    buf = np.zeros((th + base + 2 * pad, tw + 2 * pad), np.uint8)
    cv2.putText(buf, s, (pad, pad + th), FONT, scale, 255, thick, cv2.LINE_AA)
    small = cv2.resize(buf, (buf.shape[1] // SS, buf.shape[0] // SS),
                       interpolation=cv2.INTER_AREA)
    a = small.astype(np.float32) / 255.0

    x0 = int(round(x - pad / SS))
    y0 = int(round(baseline - th / SS - pad / SS))
    h, w = small.shape
    H_, W_ = board.shape[:2]
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(W_, x0 + w), min(H_, y0 + h)
    if xs1 <= xs0 or ys1 <= ys0:
        return
    sub_a = a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0][:, :, None]
    col = np.array(color, np.float32)[None, None, :]
    roi = board[ys0:ys1, xs0:xs1].astype(np.float32)
    board[ys0:ys1, xs0:xs1] = (roi * (1 - sub_a) + col * sub_a).astype(np.uint8)


# ---------------------------------------------------------------- pixels ---

def load(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit("missing source: %s" % path)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def alpha_bbox(im, thr=16):
    ys, xs = np.where(im[:, :, 3] > thr)
    return ys.min(), ys.max(), xs.min(), xs.max()


def trim(im, thr=16):
    """Crop to the alpha extent. Every figure must be normalised on its own
    alpha height before it can sit beside another - the reference panels are
    cropped to their subject at varying sizes."""
    y0, y1, x0, x1 = alpha_bbox(im, thr)
    return im[y0:y1 + 1, x0:x1 + 1]


def head_crop(im, frac=0.20, thr=16):
    """Top `frac` of the figure's alpha height, and the alpha's horizontal
    extent inside that band."""
    y0, y1, _, _ = alpha_bbox(im, thr)
    band_h = int(round((y1 - y0 + 1) * frac))
    band = im[y0:y0 + band_h]
    cols = np.where(band[:, :, 3].max(axis=0) > thr)[0]
    return band[:, cols.min():cols.max() + 1]


def scale_to_h(im, h):
    s = h / im.shape[0]
    w = max(1, int(round(im.shape[1] * s)))
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    return cv2.resize(im, (w, h), interpolation=interp)


def paste(board, im, x, y):
    """Straight-alpha composite over the ground."""
    h, w = im.shape[:2]
    a = im[:, :, 3:4].astype(np.float32) / 255.0
    fg = im[:, :, :3].astype(np.float32)
    roi = board[y:y + h, x:x + w].astype(np.float32)
    board[y:y + h, x:x + w] = (fg * a + roi * (1 - a)).astype(np.uint8)


def new_board(h):
    b = np.empty((h, W, 3), np.uint8)
    b[:, :] = GROUND
    return b


def cell_x(i):
    return MARGIN + i * (COL_W + GUTTER)


def draw_cells(board, panels, box_h, captions):
    """panels: list of BGRA images, already at a common scale.
    Each is centred in its column; captions left-align to the column."""
    for i, (im, cap) in enumerate(zip(panels, captions)):
        x = cell_x(i) + (COL_W - im.shape[1]) // 2
        paste(board, im, x, TOP + (box_h - im.shape[0]))
        text(board, cap[0], cell_x(i), TOP + box_h + CAP_1, SZ_CAP, INK)
        text(board, cap[1], cell_x(i), TOP + box_h + CAP_2, SZ_SUB, INK_SOFT)


def board_height(box_h, n_foot):
    return TOP + box_h + CAP_2 + FOOT_GAP + (n_foot - 1) * FOOT_LEAD + BOTTOM


def footer(board, box_h, lines, tag):
    base = TOP + box_h + CAP_2 + FOOT_GAP
    for i, ln in enumerate(lines):
        text(board, ln, MARGIN, base + i * FOOT_LEAD, SZ_FOOT, INK_SOFT)
    # right-aligned series tag, on the last footer line
    scale = _scale_for(SZ_FOOT) * SS
    thick = max(1, int(round(SS * 0.30 * (SZ_FOOT / 12.0))))
    tw = cv2.getTextSize(tag, FONT, scale, thick)[0][0] // SS
    text(board, tag, W - MARGIN - tw, base + (len(lines) - 1) * FOOT_LEAD,
         SZ_FOOT, INK_SOFT)


# ------------------------------------------------------------ full board ---

def build_full():
    """front / front de-lit / her left side / her left side de-lit.

    Which panel is which:
      - body_2 is the straight-on frontal view of the six-view turnaround.
      - body_0 is a pure profile whose face points to the image left. A
        figure facing image-left presents its LEFT flank to camera, so
        body_0 is her left side.
      - the source->output mapping is not guessed: delit/report_N.json
        records sourceImage body_N.png -> outputImage albedo_N.png, and the
        alpha channel of albedo_N is byte-identical to that of body_N.
    """
    FIG_H = 900

    panels = [scale_to_h(trim(load(p)), FIG_H) for p in (
        src("jinx-i2t", "ref", "views", "body_2.png"),
        src("jinx-i2t", "delit", "albedo_2.png"),
        src("jinx-i2t", "ref", "views", "body_0.png"),
        src("jinx-i2t", "delit", "albedo_0.png"),
    )]

    captions = [
        ("front, original",          "ref/views/body_2.png"),
        ("front, de-lit",            "delit/albedo_2.png"),
        ("her left side, original",  "ref/views/body_0.png"),
        ("her left side, de-lit",    "delit/albedo_0.png"),
    ]

    foot = [
        "local review only. every panel on this board is derived from the artist's turnaround, so none of it may be published.",
        "de-lit is a per-pixel normalisation against a blurred luminance proxy at strength 0.6 - an approximation, not inverse rendering.",
        "the ground is a colour that appears nowhere in the subject, so matte faults show: the gaps in the braid are holes in the source alpha, not de-lighting.",
    ]
    board = new_board(board_height(FIG_H, len(foot)))
    text(board, "de-lighting - the artist's panels, before and after", MARGIN, 76, SZ_TITLE, INK)
    draw_cells(board, panels, FIG_H, captions)
    footer(board, FIG_H, foot, "route 2")

    p = os.path.join(OUT, "delit_full.png")
    cv2.imwrite(p, board)
    return p, board.shape


# ------------------------------------------------------------- pub board ---

def build_pub():
    """The publishable equivalent: the generated face texture, map and applied.

    The face albedo is painted from measured scalars rather than sampled, so
    it carries no reference pixel. Panel 1 is the face island of the 1024x1024
    map. Panels 2-4 are the face_only renders - every material flattened to
    grey except that one texture - cropped to the head by the top-20%-of-alpha
    rule, all three at one scale (they share an alpha height of 860 px).
    """
    heads = [head_crop(load(src("jinx-i2t", "out", "face_only", "render_yaw%d.png" % y)))
             for y in (0, 45, 90)]
    # ONE scale for all three heads - they share a figure alpha height of
    # 860 px, so a single factor keeps them at the same pixels-per-head.
    k = min(COL_W * FILL / h.shape[1] for h in heads)
    heads = [cv2.resize(h, (int(round(h.shape[1] * k)), int(round(h.shape[0] * k))),
                        interpolation=cv2.INTER_CUBIC) for h in heads]
    box_h = max(h.shape[0] for h in heads)

    # The face island. The brief locates it around u 0.15-0.35, v 0.34-0.80
    # (v measured down from the top of the map); measuring where the map
    # actually departs from its flat base gives x 118-394, y 303-875, which
    # is that region tightened onto the painted oval. Use the measurement.
    tex = load(src("jinx-i2t", "pbr", "face", "face_albedo.png"))
    tex = tex[296:882, 112:400]
    tex = scale_to_h(tex, box_h)

    panels = [tex] + heads
    captions = [
        ("the map, face island",            "pbr/face/face_albedo.png, enlarged"),
        ("applied, front",                  "out/face_only/render_yaw0.png"),
        ("applied, yaw 45",                 "out/face_only/render_yaw45.png"),
        ("applied, yaw 90, face occluded",  "out/face_only/render_yaw90.png"),
    ]

    foot = [
        "the de-lighting plate cannot ship in any form: de-lighting is applied to the artist's own pixels, so there is no honest published version of it.",
        "this is the same plate built on the one texture that is generated rather than sampled. every other material is flattened to a uniform grey.",
        "the map is enlarged; at yaw 90 the head has turned and the face island is entirely occluded, which is why that panel carries no skin at all.",
    ]
    board = new_board(board_height(box_h, len(foot)))
    text(board, "the one generated texture - the painted face, map and applied", MARGIN, 76, SZ_TITLE, INK)
    draw_cells(board, panels, box_h, captions)
    footer(board, box_h, foot, "route 2, 38.53")

    p = os.path.join(OUT, "delit_pub.png")
    cv2.imwrite(p, board)
    return p, board.shape


# -------------------------------------------------------------------- go ---

if __name__ == "__main__":
    for path, shape in (build_full(), build_pub()):
        print("%s  %dx%d  %.1f KB" % (path, shape[1], shape[0],
                                      os.path.getsize(path) / 1024.0))
