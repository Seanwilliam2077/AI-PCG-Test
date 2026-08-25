"""Split wrap garments per limb and route blob parts off the attachment path.

Two things the first blockout made obvious, neither of which is visible in the
spec on its own:

1. A component WITH an attachment is emitted as a single tapered cylinder
   between localStart and localEnd. So a garment authored as one component
   spanning both legs becomes one tube swallowing both -- which is exactly what
   the trousers did. Wrap garments have to be per-limb.

2. A component WITHOUT an attachment falls back to primitive + dimensions. That
   is the right path for anything blob-shaped -- head, ribcage, pelvis, eyes --
   which read as cones on the cylinder path.
"""
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
comps = {c['id']: c for c in d['componentTree']}
pos = {k: v['transform']['position'] for k, v in comps.items()}

# ---- 1. blob parts: drop the attachment so primitive + dimensions drive them --
BLOB = {
    'pelvis', 'abdomen', 'chest', 'head', 'hair', 'hair-cap', 'hair-crest', 'hair-fringe',
    'eye-l', 'eye-r', 'eye-cavity-l', 'eye-cavity-r', 'brow-l', 'brow-r',
    'ear-l', 'ear-r', 'nose', 'mouth',
    'top', 'top-band', 'x-lacing', 'choker', 'choker-straps',
    'pouch', 'canvas-panel', 'zapper-tank', 'tattoo-region', 'shin-patch', 'nails',
    'boot-toecap', 'sash', 'braid-tassel',
}
PRIM = {
    'head': 'ellipsoid', 'chest': 'ellipsoid', 'pelvis': 'ellipsoid', 'abdomen': 'ellipsoid',
    'hair': 'ellipsoid', 'hair-cap': 'ellipsoid', 'hair-crest': 'ellipsoid', 'hair-fringe': 'ellipsoid',
    'eye-l': 'sphere', 'eye-r': 'sphere', 'eye-cavity-l': 'ellipsoid', 'eye-cavity-r': 'ellipsoid',
    'brow-l': 'box', 'brow-r': 'box', 'ear-l': 'ellipsoid', 'ear-r': 'ellipsoid',
    'nose': 'ellipsoid', 'mouth': 'ellipsoid',
    'top': 'ellipsoid', 'top-band': 'ellipsoid', 'x-lacing': 'box', 'choker': 'ellipsoid',
    'choker-straps': 'box', 'pouch': 'box', 'canvas-panel': 'box', 'zapper-tank': 'sphere',
    'tattoo-region': 'ellipsoid', 'shin-patch': 'box', 'nails': 'box',
    'boot-toecap': 'ellipsoid', 'sash': 'ellipsoid', 'braid-tassel': 'ellipsoid',
}
blobbed = 0
for cid in BLOB:
    c = comps.get(cid)
    if not c:
        continue
    c['attachment'] = None
    c['primitive'] = PRIM.get(cid, 'ellipsoid')
    blobbed += 1

# ---- 2. the trousers become one leg each -------------------------------------
def clone(src, new_id, name, parent, position, dims, start, end, rb, re):
    c = json.loads(json.dumps(comps[src]))
    c.update({
        'id': new_id, 'name': name, 'parent': parent,
        'transform': {'position': [round(v, 4) for v in position], 'rotation': [0, 0, 0]},
        'dimensions': {'width': dims[0], 'height': dims[1], 'depth': dims[2],
                       'units': 'metres', 'confidence': 0.85},
        'attachment': {'parentSocket': parent,
                       'localStart': [round(v, 4) for v in start],
                       'localEnd': [round(v, 4) for v in end],
                       'contactType': 'overlap', 'embedDepth': 0.004,
                       'gapTolerance': 0.002, 'baseRadius': rb, 'endRadius': re},
    })
    return c

new = []
for side, sx in (('l', 1), ('r', -1)):
    thigh = f'thigh-{side}'
    tp = pos[thigh]
    hip_y, hem_y = 1.078, 0.470
    leg_x = pos[thigh][0]
    # trouser leg: baggy at the hip, tapering hard below the sash, ending in the
    # tattered hem below the knee
    new.append(clone('pants', f'pants-{side}', f'Trouser leg (her {"left" if side=="l" else "right"})',
                     thigh, [leg_x, (hip_y + hem_y) / 2, 0.004], (0.150, hip_y - hem_y, 0.140),
                     [leg_x - tp[0], hip_y - tp[1], 0.004 - tp[2]],
                     [leg_x - tp[0], hem_y - tp[1], 0.004 - tp[2]], 0.082, 0.058))
    new.append(clone('pants-hem', f'pants-hem-{side}', f'Tattered hem (her {"left" if side=="l" else "right"})',
                     f'pants-{side}', [leg_x, hem_y - 0.02, 0.004], (0.140, 0.060, 0.130),
                     [0.0, 0.02, 0.0], [0.0, -0.04, 0.0], 0.060, 0.056))

keep = [c for c in d['componentTree'] if c['id'] not in ('pants', 'pants-hem')]
d['componentTree'] = keep + new

# repetition + detail references follow the split
for r in d['repetitionSystems']:
    if r.get('appliesTo') == 'pants':
        r['appliesTo'] = 'pants-l, pants-r'
for det in d['preSpecAssessment']['detailInventory']['details']:
    ref = det.get('mapsTo', {}).get('ref')
    if ref == 'pants-hem':
        det['mapsTo']['ref'] = 'pants-hem-l'
    elif ref == 'pinstripe':
        det['mapsTo']['ref'] = 'pants-l'

# localFeatures moved off the deleted 'pants'
for c in d['componentTree']:
    if c['id'] == 'pants-l':
        c['localFeatures'] = [
            {"id": "pinstripe", "kind": "linework", "note": "vertical stripe, 21.5 mm pitch, duty 0.44", "confidence": 0.9},
            {"id": "knee-crease", "kind": "fold", "note": "fold lines at the knee", "confidence": 0.6},
        ]

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
print('blob parts routed off the attachment path:', blobbed)
print('components:', len(d['componentTree']), '| trousers split into', [c['id'] for c in new])
