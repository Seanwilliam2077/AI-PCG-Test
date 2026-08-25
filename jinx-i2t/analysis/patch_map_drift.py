"""Hold each generated albedo map to the colour of the pixels it was made from.

`extract_pbr_evidence.py` does more than resize a crop: it estimates a de-lighting,
synthesises macro/meso/micro frequency bands and builds a palette. For eighteen of
the twenty materials here that pipeline is faithful -- the generated map's median
sits within 4 dLab of its crop's. For three it is not, and one of those three is
the most visible material on the figure:

    cloth       crop BGR (52, 53, 57)   map BGR (41, 64, 84)   23.0 dLab
    glassTank   crop BGR (125,141,162)  map BGR (104,137,153)  11.5 dLab
    sclera      crop BGR (234,204,212)  map BGR (237,214,225)   9.8 dLab

`cloth` is the halter crop top, the choker and the neck strap. The reference's top
is near-black; the drifted map renders it warm olive-brown, and that single wrong
colour is the most obviously incorrect thing in the front view. The crop is right,
so this is not a sampling failure -- it is the synthesis stage pulling a very dark,
low-chroma sample toward its own palette.

The correction is the smallest one that fixes it: shift the whole map in CIE Lab
by the difference between its median and its crop's median. The extractor's
de-lighting and its high-frequency detail both survive, because only the constant
term moves. Nothing is re-synthesised and no colour is invented -- the target is
the median of the pixels the map was already claiming to represent.

Idempotent: after a shift the map's median equals the crop's, so a second run
computes a zero offset and writes the same bytes.

Applied only above a threshold, because a 1-4 dLab difference is the extractor
doing its job and forcing it to zero would discard the de-lighting.

Expected measurable effect: the front view's chest_top region colour dE falls; the
top reads black instead of olive. Geometry terms cannot move.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
THRESHOLD = 8.0        # dLab below which the difference is the extractor working


def lab_of(bgr) -> np.ndarray:
    return cv2.cvtColor(np.uint8([[np.asarray(bgr, dtype=np.uint8)]]),
                        cv2.COLOR_BGR2LAB)[0, 0].astype(float)


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    rows, fixed = [], 0
    for m in spec['materials']:
        mid = m['id']
        crop_path = ROOT / f'pbr/crops/{mid}.png'
        map_path = ROOT / f'pbr/{mid}/{mid.lower()}_albedo.png'
        if not crop_path.exists() or not map_path.exists():
            rows.append((mid, None, None, 'missing'))
            continue
        crop = cv2.imread(str(crop_path))
        amap = cv2.imread(str(map_path))
        crop_med = np.median(crop.reshape(-1, 3), axis=0)
        map_med = np.median(amap.reshape(-1, 3), axis=0)
        d = float(np.linalg.norm(lab_of(crop_med) - lab_of(map_med)))
        if d < THRESHOLD:
            rows.append((mid, round(d, 1), None, 'within tolerance'))
            continue

        # shift the constant term in Lab, leaving every local variation intact
        lab_img = cv2.cvtColor(amap, cv2.COLOR_BGR2LAB).astype(np.float32)
        offset = lab_of(crop_med) - lab_of(map_med)
        lab_img += offset.astype(np.float32)
        corrected = cv2.cvtColor(np.clip(lab_img, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        cv2.imwrite(str(map_path), corrected)
        (ROOT / 'public' / map_path.name).write_bytes(map_path.read_bytes())

        new_med = np.median(corrected.reshape(-1, 3), axis=0)
        after = float(np.linalg.norm(lab_of(crop_med) - lab_of(new_med)))
        rows.append((mid, round(d, 1), round(after, 1), 'corrected'))
        fixed += 1

        # keep the declared colours honest about what now renders
        hexcol = '#%02X%02X%02X' % (int(new_med[2]), int(new_med[1]), int(new_med[0]))
        if isinstance(m.get('albedo'), dict):
            m['albedo']['dominant'] = hexcol
        m['baseColor'] = hexcol
        m['color'] = hexcol

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    print(f'{fixed} albedo maps re-anchored to their crop median '
          f'(threshold {THRESHOLD} dLab)')
    print(f'  {"material":13s} {"dLab before":>12s} {"after":>7s}  status')
    for mid, before, after, status in sorted(rows, key=lambda r: -(r[1] or 0)):
        b = f'{before:.1f}' if before is not None else '-'
        a = f'{after:.1f}' if after is not None else '-'
        print(f'  {mid:13s} {b:>12s} {a:>7s}  {status}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
