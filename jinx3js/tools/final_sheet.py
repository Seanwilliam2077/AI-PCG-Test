"""Presentation sheet: the reference turnaround above the reconstruction.

    python tools/final_sheet.py --renders out/final --out out/final_turnaround.png

Unlike tools/compare.py this makes no judgement -- it exists so a human can put
the two side by side at a matched physical scale and see for themselves.  Both
rows are scaled so 1.72 m of figure is the same number of pixels and both stand
on the same floor line, so nothing is flattered by framing.

The sheet embeds the artist's reference and is therefore for local review only.
It must not go into anything published; tools/pack.mjs deliberately strips the
reference from the shipped viewer.
"""
import argparse
import glob
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT_M = 1.72
BG = (26, 26, 30)


def composite(path, bg=BG):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None, None
    if im.shape[2] == 3:
        return im, np.ones(im.shape[:2], bool)
    a = im[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (im[:, :, :3].astype(np.float32) * a + np.array(bg) * (1 - a)).astype(np.uint8)
    return rgb, im[:, :, 3] > 0


def place(rgb, mask, px_per_m, cell_w, cell_h, floor_px):
    """Scale so the figure is `px_per_m`, and stand it on `floor_px`."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return np.full((cell_h, cell_w, 3), BG, np.uint8)
    top, bot = ys.min(), ys.max()
    scale = (px_per_m * HEIGHT_M) / max(1, bot - top + 1)
    small = cv2.resize(rgb, (max(1, int(rgb.shape[1] * scale)), max(1, int(rgb.shape[0] * scale))))
    m2 = cv2.resize(mask.astype(np.uint8), (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    ys2, xs2 = np.nonzero(m2)
    cell = np.full((cell_h, cell_w, 3), BG, np.uint8)
    if len(ys2) == 0:
        return cell
    cx = int((xs2.min() + xs2.max()) / 2)
    dy = floor_px - int(ys2.max())
    dx = cell_w // 2 - cx
    ys0, ys1 = max(0, dy), min(cell_h, dy + small.shape[0])
    xs0, xs1 = max(0, dx), min(cell_w, dx + small.shape[1])
    if ys1 <= ys0 or xs1 <= xs0:
        return cell
    cell[ys0:ys1, xs0:xs1] = small[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return cell


def label(img, text, colour=(150, 210, 255)):
    cv2.putText(img, text, (8, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.44, colour, 1, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default="out/final")
    ap.add_argument("--out", default="out/final_turnaround.png")
    ap.add_argument("--cell", type=int, nargs=2, default=(340, 720))
    ap.add_argument("--rows", default="body,clay,render",
                    help="which rows, in order: body (textured ref), clay (sculpt ref), render")
    args = ap.parse_args()

    cell_w, cell_h = args.cell
    floor_px = cell_h - 26
    px_per_m = (cell_h - 70) / HEIGHT_M

    renders = sorted(glob.glob(os.path.join(ROOT, args.renders, "*yaw*.png")))
    if not renders:
        raise SystemExit(f"no renders in {args.renders}")

    # Reference panels are a turnaround left to right with the front at index 2.
    # Renders are named by yaw; pair them by the mapping the scoreboard fitted,
    # falling back to the obvious one if it has not run yet.
    view_map_path = os.path.join(ROOT, "out", "view_map.json")
    order = None
    if os.path.exists(view_map_path):
        try:
            import json
            vm = json.load(open(view_map_path))
            pairs = vm.get("pairs") or vm.get("mapping") or vm
            if isinstance(pairs, dict):
                order = [(int(k), v) for k, v in pairs.items()]
        except Exception:
            order = None
    if order is None:
        yaw_for_panel = {0: 90, 1: 45, 2: 0, 3: 315, 4: 270, 5: 180}
        order = sorted(yaw_for_panel.items())

    rows = args.rows.split(",")
    grid = []
    for row in rows:
        cells = []
        for panel, yaw in order:
            if row == "render":
                cand = [r for r in renders if f"yaw{yaw}." in os.path.basename(r) or f"yaw{yaw}_" in os.path.basename(r)]
                path = cand[0] if cand else None
                text = f"model {yaw}deg"
            else:
                path = os.path.join(ROOT, "ref", "views", f"{row}_{panel}.png")
                text = f"ref {row}_{panel}"
            if path and os.path.exists(path):
                rgb, mask = composite(path)
                cell = place(rgb, mask, px_per_m, cell_w, cell_h, floor_px)
            else:
                cell = np.full((cell_h, cell_w, 3), BG, np.uint8)
                text += " (missing)"
            cells.append(label(cell, text))
        grid.append(np.hstack(cells))

    sheet = np.vstack(grid)
    out = os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cv2.imwrite(out, sheet)
    print(f"{args.out}  {sheet.shape[1]}x{sheet.shape[0]}  rows={rows}  panels={len(order)}")


if __name__ == "__main__":
    main()
