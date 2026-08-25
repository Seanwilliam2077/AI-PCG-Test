"""The integration sheet: each reference panel beside the matching render.

    python tools/integration_sheet.py --renders out/round1 --lod medium \
        --rows clay --out out/integration_sheet.png

Three pairs -- front, her left side, back -- because those are the three views
that carry the whole costume between them.  Both images in a pair are scaled so
the *figure* is the same number of pixels tall, and stand on the same floor
line, so nothing is flattered by framing.  The width caption underneath is the
silhouette bbox width at that matched height, which makes "too wide" readable
without a scoreboard.

Local review only: it embeds the artist's reference.
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (30, 26, 26)          # BGR
CELL_W, CELL_H = 328, 1042
FIG_H = 880                # matched figure height, px
TOP = 62                   # floor = TOP + FIG_H

PAIRS = [("FRONT", 2, 0), ("HER LEFT SIDE", 0, 90), ("BACK", 5, 180)]


def composite(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None, None
    if im.shape[2] == 3:
        return im, np.ones(im.shape[:2], bool)
    a = im[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (im[:, :, :3].astype(np.float32) * a + np.array(BG) * (1 - a)).astype(np.uint8)
    return rgb, im[:, :, 3] > 8


def place(path):
    """Scale so the silhouette is FIG_H tall, centre it, stand it on the floor."""
    cell = np.full((CELL_H, CELL_W, 3), BG, np.uint8)
    rgb, mask = composite(path)
    if rgb is None:
        return cell, 0
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return cell, 0
    s = FIG_H / (ys.max() - ys.min() + 1)
    small = cv2.resize(rgb, (max(1, round(rgb.shape[1] * s)), max(1, round(rgb.shape[0] * s))),
                       interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    m2 = cv2.resize(mask.astype(np.uint8), (small.shape[1], small.shape[0]),
                    interpolation=cv2.INTER_NEAREST) > 0
    ys2, xs2 = np.nonzero(m2)
    width_px = int(xs2.max() - xs2.min() + 1)
    dy = (TOP + FIG_H) - int(ys2.max())
    dx = CELL_W // 2 - int((xs2.min() + xs2.max()) / 2)
    ys0, ys1 = max(0, dy), min(CELL_H, dy + small.shape[0])
    xs0, xs1 = max(0, dx), min(CELL_W, dx + small.shape[1])
    if ys1 > ys0 and xs1 > xs0:
        cell[ys0:ys1, xs0:xs1] = small[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return cell, width_px


def text(img, s, org, colour, scale=0.44):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, colour, 1, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default="out/round1")
    ap.add_argument("--rows", default="clay", choices=["clay", "body"])
    ap.add_argument("--lod", default="medium")
    ap.add_argument("--out", default="out/integration_sheet.png")
    args = ap.parse_args()

    REF = (150, 190, 255)      # BGR, warm
    MINE = (150, 255, 170)     # BGR, green
    HEAD = (255, 200, 120)

    cols, notes = [], []
    for title, panel, yaw in PAIRS:
        ref_path = os.path.join(ROOT, "ref", "views", f"{args.rows}_{panel}.png")
        mine_path = os.path.join(ROOT, args.renders, f"preview_yaw{yaw}.png")
        ref_cell, ref_w = place(ref_path)
        mine_cell, mine_w = place(mine_path)

        text(ref_cell, f"REF {args.rows}_{panel}.png", (10, 30), REF, 0.46)
        text(mine_cell, f"MINE preview_yaw{yaw}.png", (10, 30), MINE, 0.46)
        text(ref_cell, f"w {ref_w}px", (10, CELL_H - 18), REF)
        pct = round(100 * mine_w / ref_w) if ref_w else 0
        text(mine_cell, f"w {mine_w}px = {pct}%", (10, CELL_H - 18), MINE)

        pair = np.hstack([ref_cell, mine_cell])
        pair[:, 0] = (70, 62, 62)
        cols.append(pair)
        notes.append((title, yaw, ref_w, mine_w, pct))

    sheet = np.hstack(cols)
    band = np.full((34, sheet.shape[1], 3), (22, 19, 19), np.uint8)
    what = "clay reference" if args.rows == "clay" else "colour reference"
    x = 0
    for title, yaw, *_ in notes:
        text(band, f"{title} / YAW {yaw}", (x + 10, 24), HEAD, 0.5)
        x += 2 * CELL_W

    title_band = np.full((34, sheet.shape[1], 3), (22, 19, 19), np.uint8)
    text(title_band, f"jinx3js integration  -  {what} vs baked LOD {args.lod}  ({len(PAIRS)} views, matched figure height {FIG_H}px)",
         (10, 24), (255, 255, 255), 0.58)
    sheet = np.vstack([title_band, band, sheet])
    out = os.path.join(ROOT, args.out)
    cv2.imwrite(out, sheet)
    print(f"{args.out}  {sheet.shape[1]}x{sheet.shape[0]}")
    for title, yaw, rw, mw, pct in notes:
        print(f"  {title:<14} yaw {yaw:<4} ref {rw}px  mine {mw}px  {pct}%")


if __name__ == "__main__":
    main()
