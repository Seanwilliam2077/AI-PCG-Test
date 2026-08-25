"""Reference-beside-render comparison sheet for one pass.

Both figures are scaled so 1.72 m of figure is the same number of pixels and
both stand on a common floor line, so nothing is flattered by framing.

    python tools/sheet.py structural-pass
"""
import sys

import cv2
import numpy as np

H = 1.72
FRAME = 1.80
CELL_H = 900
CELL_W = 500
BG = (25, 25, 30)


def composite(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None, None
    if im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        return (im[:, :, :3].astype(np.float32) * a + np.array(BG) * (1 - a)).astype(np.uint8), im[:, :, 3] > 0
    return im[:, :, :3], np.ones(im.shape[:2], bool)


def ref_cell(name, label):
    rgb, mask = composite(f'ref/views/{name}.png')
    ys, _ = np.nonzero(mask)
    top, bot = ys.min(), ys.max()
    scale = (CELL_H / FRAME * H) / (bot - top + 1)
    small = cv2.resize(rgb, (int(rgb.shape[1] * scale), int(rgb.shape[0] * scale)))
    cell = np.full((CELL_H, CELL_W, 3), BG, np.uint8)
    sole = int(bot * scale)
    dy = CELL_H - sole
    ys0, yr0 = max(0, dy), max(0, -dy)
    hh = min(CELL_H - ys0, small.shape[0] - yr0)
    x0 = max(0, (CELL_W - small.shape[1]) // 2)
    ww = min(CELL_W - x0, small.shape[1])
    cell[ys0:ys0 + hh, x0:x0 + ww] = small[yr0:yr0 + hh, :ww]
    cv2.putText(cell, label, (6, CELL_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
    return cell


def main():
    pass_id = sys.argv[1]
    tiles = []
    for yaw, ref_name, label in ((0, 'clay_2', 'front'), (90, 'clay_0', 'her left'), (180, 'clay_5', 'back')):
        tiles.append(ref_cell(ref_name, f'REF {label}'))
        rgb, _ = composite(f'out/{pass_id}/render_yaw{yaw}.png')
        if rgb is None:
            tiles.append(np.full((CELL_H, CELL_W, 3), BG, np.uint8))
            continue
        cv2.putText(rgb, f'{pass_id} {yaw}deg', (6, CELL_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
        tiles.append(rgb)
    cv2.imwrite(f'out/{pass_id}_sheet.png', np.hstack(tiles))
    print(f'out/{pass_id}_sheet.png')


if __name__ == '__main__':
    main()
