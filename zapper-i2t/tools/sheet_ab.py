"""Reference, before and after, side by side at a common figure height.

The numeric gate in `tools/try_patch.py` cannot see everything that matters. It
accepted a texture-tiling patch on a +0.10 scoreboard move that turned the whole
figure into basket weave, and it rejected an albedo fix that visibly removed the
collage look. Both calls were settled by looking. So every patch gets a sheet, and
the sheet is part of the verdict, not decoration.

    python tools/sheet_ab.py out/patch_head_face --before baseline/render_baseline
    python tools/sheet_ab.py out/patch_head_face --clay        # geometry only

Figures are scaled so each one's own alpha height fills the cell, so nothing is
flattered by framing.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

BG = (246, 246, 248)
VIEWS = ((0, 2, 'front'), (90, 0, 'her left'), (180, 5, 'back'))


def cell(path: Path, h: int, label: str) -> np.ndarray:
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        out = np.full((h, 210, 3), BG, np.uint8)
        cv2.putText(out, f'{label} (missing)', (6, h - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (90, 90, 96), 1)
        return out
    a = im[:, :, 3:4].astype(float) / 255
    rgb = (im[:, :, :3] * a + np.array(BG) * (1 - a)).astype(np.uint8)
    ys, _ = (im[:, :, 3] > 128).nonzero()
    if not len(ys):
        return np.full((h, 210, 3), BG, np.uint8)
    top, bot = ys.min(), ys.max()
    k = (h * 0.90) / (bot - top + 1)
    small = cv2.resize(rgb, (max(1, int(rgb.shape[1] * k)), max(1, int(rgb.shape[0] * k))))
    W = max(210, small.shape[1] + 14)
    out = np.full((h, W, 3), BG, np.uint8)
    y0 = int(h * 0.04)
    src = small[int(top * k):]
    n = min(h - y0 - 15, src.shape[0])
    x0 = (W - src.shape[1]) // 2
    out[y0:y0 + n, x0:x0 + src.shape[1]] = src[:n]
    cv2.putText(out, label, (6, h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (60, 60, 66), 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('after')
    ap.add_argument('--before', default='baseline/render_baseline')
    ap.add_argument('--ref', default='ref/views')
    ap.add_argument('--clay', action='store_true', help='geometry only, no reference')
    ap.add_argument('--height', type=int, default=520)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    after, before, ref = Path(a.after), Path(a.before), Path(a.ref)
    rows = []
    for yaw, panel, name in VIEWS:
        row = []
        if not a.clay:
            row.append(cell(ref / f'body_{panel}.png', a.height, f'reference {name}'))
        row.append(cell(before / f'render_yaw{yaw}.png', a.height, f'before {name}'))
        row.append(cell(after / f'render_yaw{yaw}.png', a.height, f'after {name}'))
        rows.append(row)

    widths = [max(r[i].shape[1] for r in rows) for i in range(len(rows[0]))]
    sheet = np.vstack([
        np.hstack([np.pad(c, ((0, 6), (0, w - c.shape[1]), (0, 0)), constant_values=246)
                   for c, w in zip(row, widths)])
        for row in rows
    ])
    dest = Path(a.out or f'out/sheet_{after.name}.png')
    cv2.imwrite(str(dest), sheet)
    print(f'{dest}  {sheet.shape[1]}x{sheet.shape[0]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
