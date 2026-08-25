"""Tile the reference crops densely instead of stretching one across each part.

What the seams actually are: every material's albedo is a 96 px patch cut from
the reference sheet, and `textureProjection.repeat` defaults to [2, 2]. A
primitive's UVs run 0..1 over the whole primitive, so each component shows the
same patch stretched twice across itself — including whatever lighting gradient
the patch happened to contain. Two adjacent components carrying the same material
therefore show the same gradient at different scales and orientations, and the
boundary between them reads as a hard seam. That is the collage look, and it is
the largest remaining visual defect in the build.

The patch cannot be made to align across a component boundary: the generator has
no UV unwrap and `uvStrategy` is not read at all, so there is no shared parametric
space to align in. What CAN be done is to make the patch small enough that no
single feature in it survives to be recognised across a boundary. At repeat 8 a
96 px crop covers about 25 mm of a limb, which is the scale at which a photographic
patch stops reading as a photograph and starts reading as material.

Repeat is set per material from the physical size of the largest component that
uses it, so a boot and a fingernail end up with comparable texel density rather
than comparable tile counts. Face materials are excluded: the eye, sclera, pupil,
brow and lip crops are the one place where the patch's own structure IS the
feature, and tiling them would destroy it.

Expected measurable effect: silhouette IoU, width and landmark terms are
geometry-only and should not move at all — if any of them does, something else
changed and this patch is not what it claims. Region colour dE should move
slightly (tiling changes which pixels average into each region). The real effect
is visual and belongs in the side-by-side sheet, not in a scalar.
"""
from __future__ import annotations

import json
import sys

SPEC = sys.argv[1] if len(sys.argv) > 1 else 'object-sculpt-spec.json'

# The face reads at close range and its crops carry structure, not texture.
KEEP_STRETCHED = {'eye', 'sclera', 'pupil', 'brow', 'lip'}

# target tile footprint on the model, in metres: how much surface one copy of the
# crop should cover. Small enough that no feature in the patch is recognisable.
TARGET_TILE_M = 0.025
MIN_REPEAT, MAX_REPEAT = 2.0, 16.0


def main() -> int:
    spec = json.load(open(SPEC, encoding='utf-8'))

    # largest component dimension per material, so density follows physical size
    largest: dict[str, float] = {}
    for c in spec['componentTree']:
        mat = c.get('material')
        if not mat:
            continue
        dim = c.get('dimensions') or {}
        size = max((dim.get(k) or 0.0) for k in ('width', 'height', 'depth'))
        att = c.get('attachment') or {}
        if att.get('baseRadius') is not None:
            # an attached component is a cylinder: its longest run is the span
            s, e = att.get('localStart') or [0, 0, 0], att.get('localEnd') or [0, 0, 0]
            span = sum((e[i] - s[i]) ** 2 for i in range(3)) ** 0.5
            size = max(size, span)
        largest[mat] = max(largest.get(mat, 0.0), size)

    changed = []
    for m in spec['materials']:
        mid = m['id']
        proj = m.setdefault('textureProjection', {})
        was = proj.get('repeat')
        if mid in KEEP_STRETCHED:
            proj['repeat'] = [1.0, 1.0]
            proj['tilingRationale'] = (
                'left untiled: this crop carries facial structure, and tiling it would '
                'repeat an eye or a lip across the surface')
        else:
            size = largest.get(mid, 0.10)
            r = round(min(MAX_REPEAT, max(MIN_REPEAT, size / TARGET_TILE_M)), 1)
            proj['repeat'] = [r, r]
            proj['tilingRationale'] = (
                f'largest component using this material spans {size * 1000:.0f} mm; at repeat '
                f'{r} one copy of the 96 px crop covers about {size / r * 1000:.0f} mm, below '
                f'the scale at which a photographic patch is recognisable across a seam')
        proj.setdefault('mode', 'uv')
        proj.setdefault('anisotropy', 8)
        if was != proj['repeat']:
            changed.append((mid, was, proj['repeat'][0], largest.get(mid, 0.0)))

    json.dump(spec, open(SPEC, 'w', encoding='utf-8'), indent=1)

    print(f'texture tiling set on {len(spec["materials"])} materials, '
          f'{len(changed)} changed')
    for mid, was, now, size in sorted(changed, key=lambda r: -r[2])[:12]:
        old = was[0] if isinstance(was, list) else was
        print(f'  {mid:13s} repeat {str(old):>5s} -> {now:<5}  '
              f'largest component {size * 1000:.0f} mm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
