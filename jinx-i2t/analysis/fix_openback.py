"""Open the halter's back, and put the tattoo region where the tattoos are.

Measured from the reference turnaround: her back is BARE from the shoulder blades
to the waist -- the top is a halter, tied at the neck, with the whole back open and
the cloud tattoos reading directly on skin. The spec had `top` at depth 0.230
against a chest of depth 0.224, i.e. a tube fully enclosing the torso, and
`tattoo-region` carrying the `pants` material on the FRONT of the chest.

The consequence was measurable, not just wrong-looking: the render's back view came
out at L 21.3 against the reference's 34.2, and no lighting change could close it --
a sweep over key/ambient/environment moved the six-view L spread only between 16.7
and 20.6 against the reference's 2.61, because the deficit is albedo, not light.
"""
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
c = {x['id']: x for x in d['componentTree']}

def edit(cid, *, depth=None, z=None, width=None, height=None, y=None, x=None, material=None, note=None):
    t = c[cid]
    if depth is not None:
        t['dimensions']['depth'] = depth
    if width is not None:
        t['dimensions']['width'] = width
    if height is not None:
        t['dimensions']['height'] = height
    p = t['transform']['position']
    if x is not None:
        p[0] = x
    if y is not None:
        p[1] = y
    if z is not None:
        p[2] = z
    if material is not None:
        t['material'] = material
        t['materialLayers'] = [material]
    if note:
        t['notes'] = note
    print(f"  {cid:14s} dims {t['dimensions']['width']}/{t['dimensions']['height']}/"
          f"{t['dimensions']['depth']}  pos {p}  mat {t['material']}")

# chest half-depth is 0.112, so a top of depth 0.140 centred at z +0.048 spans
# chest-local z -0.022..0.118: the front 60 percent covered, the back 40 open.
edit('top', depth=0.140, z=0.048,
     note='Halter: open-backed. Depth 0.140 at z +0.048 covers the front of a '
          '0.224-deep chest and leaves the back bare, as the reference does.')
edit('top-band', depth=0.135, z=0.048,
     note='Under-bust band follows the halter and stops at the same back opening.')

# the cloud tattoos sit across the bare back, on skin -- not as a purple slab on
# the front of the ribcage
edit('tattoo-region', x=0.0, z=-0.070, width=0.180, height=0.300, depth=0.090,
     material='tattoo',
     note='Cloud tattoos across the bare back, from the shoulder blades to the '
          'waist. Was authored on the FRONT of the chest carrying the trouser '
          'material, which put a dark slab over the sternum and none on the back.')

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
