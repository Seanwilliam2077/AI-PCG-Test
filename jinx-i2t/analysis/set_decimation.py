"""Spend the triangle budget where the reference can actually be seen.

The build sits at 202,656 triangles against a 250,000 budget and 104 draw calls
against 160, so it is inside both. It is inside them badly, though: the
tessellation tier is global, so a 20 mm nose and a 300 mm ribcage are both
tessellated at 4,992 triangles. Twenty-three parts carry 4,000+ triangles each
and together account for 125,376 -- most of them features no wider than a thumb.

`geometryDescriptor.decimate.targetRatio` is the per-component lever the pipeline
provides for exactly this, and its docstring says why it exists separately from
the tier: a tier dials primitives that have segment counts, while an implicit
surface's density comes from a quantised sampling grid, so only a ratio can land
on a number.

Ratios are set from the part's largest dimension, because triangle density should
track screen area, and screen area tracks size. Nothing is decimated below a floor
that would show facets on a curved surface.
"""
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))

# largest dimension (m) -> ratio of the tier's density to keep
TIERS = ((0.20, None), (0.10, 0.50), (0.05, 0.28), (0.00, 0.15))
# the face reads at close range in the reference's head panels; do not thin it
KEEP_FULL = {'head', 'hair', 'hair-crest', 'hair-fringe', 'hair-cap', 'eye-l', 'eye-r',
             'chest', 'abdomen', 'pelvis', 'top'}

set_count = 0
for c in d['componentTree']:
    if c['id'] in KEEP_FULL:
        continue
    dim = c.get('dimensions') or {}
    size = max((dim.get(k) or 0) for k in ('width', 'height', 'depth'))
    ratio = next(r for lo, r in TIERS if size >= lo)
    if ratio is None:
        continue
    gd = c.setdefault('geometryDescriptor', {})
    gd['decimate'] = {
        'targetRatio': ratio,
        'reason': f'largest dimension {size * 1000:.0f} mm; density tracks screen area',
    }
    set_count += 1

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
print(f'decimation ratio set on {set_count} of {len(d["componentTree"])} components; '
      f'{len(KEEP_FULL)} kept at full density')
