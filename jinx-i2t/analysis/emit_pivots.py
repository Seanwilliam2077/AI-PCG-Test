"""Give every component a pivot at its JOINT and expose sockets at both ends.

All 103 components carried `pivot.mode: "center"` and an empty `sockets` list.
That is not a rig -- a forearm whose pivot is its own midpoint bends around a
point that does not exist on the body, and a prop with no socket has nothing to
attach to. It is the same failure as the five in docs/GENERATOR_CONTRACT.md: a
field filled with a harmless-looking default that reads downstream as
"specified".

The skeleton already holds the right answer. Each of the 49 bones carries
`jointPos` and `tipPos` in world metres and names the component it drives, so the
pivot is the joint, the axis is the bone direction, and the two sockets are the
bone's own ends. Component-local coordinates come from walking the tree and
accumulating `transform.position`, because positions are parent-local and
accumulate (GENERATOR_CONTRACT bug 4).
"""
import json
import math

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
comps = {c['id']: c for c in d['componentTree']}
rig = d.get('skeleton') or d.get('rig') or d.get('rigSpec') or {}
bones = rig.get('bones') or []
assert bones, f'no bones found; top-level keys are {sorted(d)}'

# world position of every component, by accumulating parent-local transforms
world = {}
def solve(cid, guard=()):
    if cid in world:
        return world[cid]
    c = comps.get(cid)
    if c is None or cid in guard:
        return [0.0, 0.0, 0.0]
    p = c.get('parent')
    base = solve(p, guard + (cid,)) if p and p in comps else [0.0, 0.0, 0.0]
    pos = c['transform']['position']
    world[cid] = [base[i] + pos[i] for i in range(3)]
    return world[cid]
for cid in comps:
    solve(cid)

# A bone's proximal joint has an anatomical name that its component id does not
# carry: the top of upper-arm-l IS the shoulder, the top of forearm-l IS the
# elbow. The interaction-pass asks for those joints by name, and naming a socket
# `upper-arm-l-joint` hides the shoulder from anything looking for one.
JOINT_NAME = {
    'upper-arm': 'shoulder', 'forearm': 'elbow', 'hand': 'wrist',
    'thigh': 'hip', 'shin': 'knee', 'foot': 'ankle',
    'clavicle': 'clavicle', 'head': 'head', 'neck': 'neck',
    'chest': 'spine-chest', 'abdomen': 'spine-abdomen', 'pelvis': 'root-hips',
}


def joint_id(bone_id):
    for stem, name in JOINT_NAME.items():
        if bone_id == stem or bone_id.startswith(stem + '-'):
            side = bone_id[len(stem):]
            return f'{name}{side}' if side else name
    return bone_id


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [round(x / n, 5) for x in v] if n > 1e-9 else [0.0, 1.0, 0.0]

made_pivot = made_socket = 0
for b in bones:
    cid = b.get('component')
    c = comps.get(cid)
    if not c:
        continue
    ap = c.setdefault('actionProfile', {})
    j, t = b['jointPos'], b.get('tipPos') or b['jointPos']
    w = world[cid]
    local_joint = [round(j[i] - w[i], 5) for i in range(3)]
    local_tip = [round(t[i] - w[i], 5) for i in range(3)]
    ap['pivot'] = {
        'mode': 'joint',
        'localPosition': local_joint,
        'axis': unit([t[i] - j[i] for i in range(3)]),
        'confidence': 0.85,
        'note': f"pivot at the {b['id']} joint, not the component centre; "
                f"axis is the bone direction",
    }
    made_pivot += 1
    ap['sockets'] = [
        {'id': f"{joint_id(b['id'])}-joint", 'localPosition': local_joint, 'localRotation': [0, 0, 0],
         'kind': 'joint', 'chain': b.get('chain'), 'role': b.get('role')},
        {'id': f"{joint_id(b['id'])}-tip", 'localPosition': local_tip, 'localRotation': [0, 0, 0],
         'kind': 'tip', 'chain': b.get('chain'), 'role': b.get('role')},
    ]
    made_socket += 2
    ch = ap.setdefault('transformChannels', {})
    ch['rotate'] = True

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)

REQUIRED = {'head', 'neck', 'shoulder', 'elbow', 'hip', 'knee'}
have = set()
for c in d['componentTree']:
    for s in (c.get('actionProfile') or {}).get('sockets') or []:
        for k in REQUIRED:
            if k in s['id'].lower():
                have.add(k)
print(f'{made_pivot} pivots moved to their joint, {made_socket} sockets exposed')
print('named joints the interaction-pass asks for:',
      ', '.join(sorted(have)) or 'none', '| missing:', sorted(REQUIRED - have) or 'none')
