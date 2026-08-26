"""Perturb one edit handle, rebuild, and check that nothing outside its scope moved.

Nova3D (arXiv 2607.22738) reports 14/18 blinded local edits succeeding with locality
preserved in 18/18, and contrasts that with mesh-native output, where an edit has no
local scope at all because there are no parts to scope it to. Locality is the claim that
makes a generated asset editable rather than merely inspectable, so it is measured here
directly rather than assumed to follow from having a part tree.

CONTRACT.md section 8 declares eight handles, and for each one a `moves` list and a
`must not move` list, written before any geometry existed. Its own words: "the must-not
list *is* the locality specification". The table below transcribes those lists. It is the
spec, not a description of the build -- three of its rows were written knowing they might
fail, and section 8 says outright that if H2 has no locality "the honest report is to say
so rather than loosen the tolerance until it passes".

Both halves of each row matter. A handle that moves nothing is as broken as one that
moves everything, and checking only the must-not half would score a no-op handle as a
perfect pass -- so a `moves` entry that does not move is a failure here.

Names in `moves` are read as SUBTREE ROOTS: their descendants are expected to travel with
them and are excluded from the must-not set. That is what an assembly tree is for.

    python tools/locality_test.py
    python tools/locality_test.py --handle grip.rake
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MESHES = ROOT / 'out' / '_meshes.json'

# Below this a bbox difference is float noise from a rebuild, not motion.
TOL_MM = 0.5
# Above this a part has genuinely moved.
MOVED_MM = 1.0


# --------------------------------------------------------------------------- the spec

MUZZLE_RINGS = ['barrel.muzzle-collar.ring-fore', 'barrel.muzzle-collar.ring-mid',
                'barrel.muzzle-collar.ring-aft']
FRAME_ALL = ['frame.receiver', 'frame.port', 'frame.port.flange', 'frame.trigger-guard',
             'frame.hammer-spur', 'frame.trigger']
GRIP_ALL = ['grip.body', 'grip.butt-cap', 'grip.butt-cap.toe-stud']
BARREL_TUBES = ['barrel.tube-aft', 'barrel.tube-fore', 'barrel.mid-band']
LATTICE_ALL = ['barrel.lattice-collar.rim-fore', 'barrel.lattice-collar.rim-aft']

HANDLES = [
    {
        'id': 'barrel.length', 'section': 'H1', 'value': 0.012,
        'kind': 'transform',
        'moves': [*MUZZLE_RINGS, 'barrel.liner', 'barrel.bore', 'barrel.rail.stud.2'],
        'stretch': ['barrel.tube-fore', 'barrel.rail'],
        'fixed': [*LATTICE_ALL, 'barrel.tube-aft', *FRAME_ALL, *GRIP_ALL,
                  'barrel.rail.rear-hook', 'barrel.rail.mount-block',
                  'barrel.rail.stud.0', 'barrel.rail.stud.1'],
        # Section 8 also lists `mid-band` under moves and `lug` under moves. `lug` is not a
        # part in the built tree at all, and mid-band cannot move -- see the note printed
        # for this handle. Both are reported rather than dropped.
        'contractDefect': (
            'section 8 H1 lists mid-band as moving AND fixes tube-fore min.x, which is '
            'the mid-band own front face (both at 110.3 mm). The two rows cannot both '
            'hold in any model. It also lists `lug`, which no part in the tree is named. '
            'Resolved by holding mid-band fixed; the row is scored against that reading '
            'and the conflict is reported, not hidden.'),
        'note': 'stretch anchored at the mid-band front face',
    },
    {
        'id': 'barrel.tube.od', 'section': 'H2', 'value': 0.003,
        'kind': 'transform',
        # Section 8 writes "lattice-collar" here, which is a Group and has no geometry of
        # its own, so it never appears in a mesh dump. Transcribed to the collar's own
        # meshes -- the rims. This was a defect in this file, caught by the first run
        # reporting a `moves` entry that is not a part.
        'moves': [*BARREL_TUBES, *LATTICE_ALL, *MUZZLE_RINGS, 'barrel.rail'],
        # ...and the rest of what the group holds. Section 8 named the whole collar, so
        # its openings ride with it; they are only listed separately because the group
        # itself carries no geometry for the subtree rule to find.
        'alsoMoves': 'barrel.lattice-collar.',
        'stretch': [],
        'fixed': [*FRAME_ALL, *GRIP_ALL],
        # Section 8 H2 pre-declares the trap: if the frame wraps the barrel's rear as one
        # solid, changing tube OD legitimately changes the frame and the test fails by
        # construction. This row is the one the contract said to report honestly either way.
        'note': 'section 8 pre-declared that this handle may have no locality at all',
    },
    {
        'id': 'grip.rake', 'section': 'H3', 'value': 6.0,
        'kind': 'transform',
        'moves': GRIP_ALL, 'stretch': [],
        'fixed': [*FRAME_ALL, *BARREL_TUBES, *MUZZLE_RINGS, *LATTICE_ALL, 'barrel.rail'],
        'note': 'pivot DECLARED at the guard rear attach; any other pivot makes H3 non-local',
    },
    {
        'id': 'lattice.opening.count', 'section': 'H4', 'value': 20,
        'kind': 'generation',
        'moves': [], 'stretch': [],
        'movesByCount': 'barrel.lattice-collar.cutout',
        # Section 8 H4's move list says "only the cutout instances". Incomplete: the struts
        # ARE the solid arcs between the openings, so N of them is exactly what N openings
        # leaves behind and a count change must rebuild them. Added to the scope, and
        # recorded as an incompleteness in the contract rather than as motion the test
        # decided to tolerate.
        'alsoMoves': 'barrel.lattice-collar.strut',
        'fixed': [*LATTICE_ALL, *BARREL_TUBES, *MUZZLE_RINGS, *FRAME_ALL, *GRIP_ALL,
                  'barrel.rail'],
        'contractDefect': (
            'section 8 H4 lists only the cutouts as moving. The struts are the arcs '
            'between them and cannot survive a count change; the move list is incomplete, '
            'not the build.'),
        'note': 'the best locality test on the object: the expected bbox delta is zero '
                'even for the part that changed',
    },
    {
        'id': 'rail.length', 'section': 'H5', 'value': 0.010,
        'kind': 'transform',
        'moves': ['barrel.rail.stud.2'], 'stretch': ['barrel.rail'],
        'fixed': ['barrel.rail.rear-hook', 'barrel.rail.mount-block', 'barrel.rail.stud.0',
                  'barrel.rail.stud.1', *BARREL_TUBES, *MUZZLE_RINGS, *LATTICE_ALL,
                  *FRAME_ALL, *GRIP_ALL, 'barrel.liner', 'barrel.bore'],
        'note': 'the rail is stretchy and carries a fixed rear hook, so a whole-bbox '
                'invariant on `rail` fails by construction (section 9.6)',
    },
    {
        'id': 'muzzle.collar.rings', 'section': 'H6', 'value': 4,
        'kind': 'generation',
        'moves': [], 'stretch': [],
        'movesByCount': 'barrel.muzzle-collar.ring',
        'fixed': ['barrel.liner', 'barrel.bore', *BARREL_TUBES, *LATTICE_ALL, *FRAME_ALL,
                  *GRIP_ALL, 'barrel.rail'],
        'envelope': MUZZLE_RINGS,
        'note': 'ring instances only; the collar envelope must not change',
    },
    {
        'id': 'hammer.angle', 'section': 'H7', 'value': 12.0,
        'kind': 'transform',
        'moves': ['frame.hammer-spur'], 'stretch': [],
        'fixed': ['frame.receiver', 'frame.port', 'frame.trigger-guard', 'frame.trigger',
                  *GRIP_ALL, *BARREL_TUBES, *MUZZLE_RINGS, *LATTICE_ALL, 'barrel.rail'],
        'note': 'J1 doubling as a pose handle',
    },
    {
        'id': 'trigger.angle', 'section': 'H8', 'value': 10.0,
        'kind': 'transform',
        'moves': ['frame.trigger'], 'stretch': [],
        'fixed': ['frame.trigger-guard', 'frame.receiver', 'frame.port',
                  'frame.hammer-spur', *GRIP_ALL, *BARREL_TUBES, *MUZZLE_RINGS,
                  *LATTICE_ALL, 'barrel.rail'],
        'note': 'must not move INCLUDING the guard, which the guard shares an edge with',
    },
]


# --------------------------------------------------------------------------- machinery

def build(edits: str | None) -> dict[str, dict]:
    cmd = ['node', 'tools/render.mjs', '--out', 'out/_loc', '--size', '200x100',
           '--yaw', '0', '--allmeshes']
    if edits:
        cmd += ['--edits', edits]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0 or 'threw' in (r.stdout + r.stderr):
        raise SystemExit(f'build failed for edits={edits}:\n'
                         f'{(r.stdout + r.stderr)[-600:]}')
    return {m['name']: m for m in json.loads(MESHES.read_text(encoding='utf-8'))}


def box(m: dict) -> tuple[float, ...]:
    return (m['x0'], m['x1'], m['minY'], m['maxY'], m['z0'], m['z1'])


def delta_mm(a: dict, b: dict) -> float:
    return max(abs(u - v) for u, v in zip(box(a), box(b))) * 1000


def subtree(names: list[str], all_names: list[str]) -> set[str]:
    """A name in `moves` covers everything under it, which is what a tree is for."""
    out = set()
    for n in names:
        out.add(n)
        out.update(k for k in all_names if k.startswith(n + '.'))
    return out


def run_handle(h: dict, base: dict) -> dict:
    edits = f"{h['id']}:{h['value']}"
    after = build(edits)
    names = sorted(set(base) | set(after))
    scope = subtree([*h['moves'], *h['stretch'], *h.get('envelope', [])], names)
    for key in ('movesByCount', 'alsoMoves'):
        if h.get(key):
            scope |= {n for n in names if n.startswith(h[key])}

    fails: list[str] = []
    unconstrained: list[str] = []

    # must-move half
    for n in h['moves']:
        if n not in base or n not in after:
            fails.append(f'{n}: named in `moves` but not a part in the tree')
        elif delta_mm(base[n], after[n]) < MOVED_MM:
            fails.append(f'{n}: named in `moves` but did not move')

    for n in h['stretch']:
        if n not in base or n not in after:
            fails.append(f'{n}: named in `stretch` but not a part in the tree')
            continue
        if abs(after[n]['x1'] - base[n]['x1']) * 1000 < MOVED_MM:
            fails.append(f'{n}: named in `stretch` but its forward face did not move')
        if abs(after[n]['x0'] - base[n]['x0']) * 1000 > TOL_MM:
            fails.append(f'{n}: stretched from the wrong end -- its min.x moved')

    if h.get('movesByCount'):
        pre = sum(1 for n in base if n.startswith(h['movesByCount']))
        post = sum(1 for n in after if n.startswith(h['movesByCount']))
        if pre == post:
            fails.append(f'{h["movesByCount"]}*: the count did not change ({pre})')

    # the envelope half: parts that changed internally but must not change outwardly
    for n in h.get('envelope', []):
        if n in base and n in after and delta_mm(base[n], after[n]) > TOL_MM:
            fails.append(f'{n}: envelope moved {delta_mm(base[n], after[n]):.2f} mm')
    if h.get('envelope'):
        common = [n for n in h['envelope'] if n in base and n in after]
        if common:
            b0 = (min(base[n]['x0'] for n in common), max(base[n]['x1'] for n in common))
            a0 = (min(after[n]['x0'] for n in common), max(after[n]['x1'] for n in common))
            d = max(abs(a0[i] - b0[i]) for i in (0, 1)) * 1000
            if d > TOL_MM:
                fails.append(f'collar envelope moved {d:.2f} mm')

    # must-not-move half
    for n in h['fixed']:
        if n not in base or n not in after:
            continue          # section 8 names a few parts the tree does not have
        d = delta_mm(base[n], after[n])
        if d > TOL_MM:
            fails.append(f'{n}: must not move, moved {d:.2f} mm')

    # anything section 8 puts in neither list
    accounted = scope | subtree(h['fixed'], names)
    for n in names:
        if n in accounted or n.endswith('__pivot') or n.startswith('socket.'):
            continue
        if n in base and n in after and delta_mm(base[n], after[n]) > TOL_MM:
            unconstrained.append(f'{n} moved {delta_mm(base[n], after[n]):.2f} mm')

    return {'id': h['id'], 'section': h['section'], 'kind': h['kind'],
            'value': h['value'], 'pass': not fails, 'failures': fails,
            'unconstrainedMotion': unconstrained,
            'note': h.get('note', ''), 'contractDefect': h.get('contractDefect')}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--handle')
    ap.add_argument('--out', default='out/locality_report.json')
    a = ap.parse_args()

    base = build(None)
    todo = [h for h in HANDLES if not a.handle or h['id'] == a.handle]
    results = [run_handle(h, base) for h in todo]

    strong = [r for r in results if r['kind'] == 'generation']
    weak = [r for r in results if r['kind'] == 'transform']
    ok = sum(1 for r in results if r['pass'])

    print(f'locality           {ok}/{len(results)} handles preserved locality')
    print(f'  generation handles (the strong form)  '
          f'{sum(1 for r in strong if r["pass"])}/{len(strong)}')
    print(f'  scoped transforms (the weak form)     '
          f'{sum(1 for r in weak if r["pass"])}/{len(weak)}')
    print()
    for r in results:
        mark = 'ok  ' if r['pass'] else 'FAIL'
        print(f'  {mark} {r["section"]:3s} {r["id"]:22s} {r["note"]}')
        for f in r['failures']:
            print(f'         - {f}')
        for u in r['unconstrainedMotion'][:4]:
            print(f'         ? outside both lists: {u}')
        if r['contractDefect']:
            print(f'         ! contract defect: {r["contractDefect"]}')

    (ROOT / a.out).write_text(json.dumps(
        {'handles': len(results), 'passed': ok, 'results': results}, indent=1),
        encoding='utf-8')
    print(f'\nwritten {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
