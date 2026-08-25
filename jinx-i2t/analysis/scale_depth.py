"""Recover the measured depth and width deficit, respecting how each part is built.

Two independent measurements agree: at a common frame the render's side silhouette
is 0.790 of the reference's maximum width-over-height and the front is 0.900. The
figure is too shallow front-to-back and slightly too narrow across.

The correction cannot be one global scale, because the generator builds two kinds
of part (docs/GENERATOR_CONTRACT.md):

  * a component WITH an attachment is a tapered CYLINDER between two joints, driven
    by baseRadius/endRadius. Its cross-section is circular, so it has no separate
    depth to scale -- widening it moves front and side together.
  * a component WITHOUT an attachment falls back to primitive + dimensions, where
    width and depth are independent.

So limbs take a single radius factor and torso/head/hair take separate width and
depth factors. Run with the factors as arguments so the result can be measured and
the factors revised rather than guessed once.

    python analysis/scale_depth.py 1.30 1.05 1.12
"""
import json
import sys

SPEC = 'object-sculpt-spec.json'
depth_k = float(sys.argv[1]) if len(sys.argv) > 1 else 1.30
width_k = float(sys.argv[2]) if len(sys.argv) > 2 else 1.05
radius_k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.12

d = json.load(open(SPEC, encoding='utf-8'))
blob = cyl = 0
for c in d['componentTree']:
    if c['id'] == 'root':
        continue
    att = c.get('attachment')
    if att and att.get('baseRadius') is not None:
        att['baseRadius'] = round(att['baseRadius'] * radius_k, 5)
        att['endRadius'] = round(att['endRadius'] * radius_k, 5)
        cyl += 1
    else:
        dim = c.get('dimensions') or {}
        if 'depth' in dim:
            dim['depth'] = round(dim['depth'] * depth_k, 5)
        if 'width' in dim:
            dim['width'] = round(dim['width'] * width_k, 5)
        blob += 1
json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
print(f'{blob} blob parts: depth x{depth_k}, width x{width_k}   |   '
      f'{cyl} limb parts: radius x{radius_k}')
