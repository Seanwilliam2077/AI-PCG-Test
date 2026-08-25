"""Re-derive the rig from the components that actually exist.

The interaction pass exposed 49 joint pivots and 98 sockets, and every joint socket
read back within 0.0 mm of its bone. The extremity patch then collapsed the 30
finger phalanges into a mitten-plus-thumb form -- defensibly, since a phalanx covers
about a pixel in a 900 px render -- and the shape patches moved most of what was
left. Probing the built scene afterwards finds 38 sockets, not 98, and 19 of 49
bones still matching. The arithmetic is exact: 49 bones minus 30 finger bones is 19,
so every joint that still has geometry is still correct, and the 30 that are not are
bones for components that no longer exist.

That is not a broken rig, but it is a dishonest one: `rig.bones` asserts 49 bones
and the model can only skin 19 of them. A downstream animator reading the spec would
bind to joints that never move anything.

So this prunes bones whose component is gone, re-parents any orphan onto its nearest
surviving ancestor so the chains stay connected, and re-derives every pivot and
socket from the current component world positions -- the same derivation
`analysis/emit_pivots.py` performed, re-run against the moved geometry rather than
patched incrementally, because every shape patch since has changed those positions.

Idempotent: bones and sockets are re-derived from the component tree each run, so a
second run reproduces the first exactly.

Expected measurable effect: none on any rendered metric -- pivots and sockets are
Object3D nodes carrying no geometry. What changes is that probing the built scene
returns one joint socket per bone, all within a millimetre of it, and that
`rig.bones` stops naming components that are not there.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'

# a bone's proximal joint has an anatomical name its component id does not carry
JOINT_NAME = {
    'upper-arm': 'shoulder', 'forearm': 'elbow', 'hand': 'wrist',
    'thigh': 'hip', 'shin': 'knee', 'foot': 'ankle',
    'clavicle': 'clavicle', 'head': 'head', 'neck': 'neck',
    'chest': 'spine-chest', 'abdomen': 'spine-abdomen', 'pelvis': 'root-hips',
}


def joint_id(bone_id: str) -> str:
    for stem, name in JOINT_NAME.items():
        if bone_id == stem or bone_id.startswith(stem + '-'):
            side = bone_id[len(stem):]
            return f'{name}{side}' if side else name
    return bone_id


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [round(x / n, 5) for x in v] if n > 1e-9 else [0.0, 1.0, 0.0]


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    comps = {c['id']: c for c in spec['componentTree']}
    rig = spec.get('rig') or {}
    bones = rig.get('bones') or []

    # 1. drop bones whose component is gone, keeping the chains connected
    alive = {b['id']: b for b in bones if b.get('component') in comps}
    dropped = [b['id'] for b in bones if b['id'] not in alive]
    for b in alive.values():
        p = b.get('parent')
        seen = set()
        while p and p not in alive and p not in seen:
            seen.add(p)
            parent_bone = next((x for x in bones if x['id'] == p), None)
            p = parent_bone.get('parent') if parent_bone else None
        b['parent'] = p
    rig['bones'] = list(alive.values())

    # 2. world position of every component: parent-local, accumulating
    world: dict[str, list[float]] = {}

    def solve(cid: str, guard: tuple = ()) -> list[float]:
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

    # 3. re-derive pivots and sockets against the geometry as it stands now
    for c in spec['componentTree']:
        ap = c.get('actionProfile')
        if isinstance(ap, dict):
            ap.pop('sockets', None)

    pivots = sockets = 0
    for b in rig['bones']:
        cid = b['component']
        c = comps[cid]
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
                    f'axis is the bone direction',
        }
        ap['sockets'] = [
            {'id': f"{joint_id(b['id'])}-joint", 'localPosition': local_joint,
             'localRotation': [0, 0, 0], 'kind': 'joint',
             'chain': b.get('chain'), 'role': b.get('role')},
            {'id': f"{joint_id(b['id'])}-tip", 'localPosition': local_tip,
             'localRotation': [0, 0, 0], 'kind': 'tip',
             'chain': b.get('chain'), 'role': b.get('role')},
        ]
        ap.setdefault('transformChannels', {})['rotate'] = True
        pivots += 1
        sockets += 2

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    required = {'head', 'neck', 'shoulder', 'elbow', 'hip', 'knee'}
    have = {k for c in spec['componentTree']
            for s in (c.get('actionProfile') or {}).get('sockets') or []
            for k in required if k in s['id'].lower()}
    print(f'{len(dropped)} bones pruned (component removed): '
          f'{", ".join(dropped[:6])}{" ..." if len(dropped) > 6 else ""}')
    print(f'{len(rig["bones"])} bones remain; {pivots} pivots and {sockets} sockets re-derived')
    print(f'named joints the interaction pass requires: {", ".join(sorted(have)) or "none"}'
          f' | missing: {sorted(required - have) or "none"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
