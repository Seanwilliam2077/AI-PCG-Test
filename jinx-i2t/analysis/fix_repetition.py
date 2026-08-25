"""Author the repetition systems against the contract the generator actually reads.

The four systems were written descriptively -- `appliesTo: "pants-l, pants-r"`,
`axis: "around the leg"` -- which reads well and emits nothing. The emitter reads
`parent` (a component id), `placement.{mode,axis,radius,startAngleDeg}`,
`instanceScale`, `primitive` and `material`; with none of those present every
system fell back to `nodes["root"]` at radius 0, so 26 pinstripes and 9 buckles
piled up as 0.1 m skin-coloured cubes straddling the floor. That is what put the
model's bounding box at y -0.071.

Two further constraints, found by reading the emitter rather than the schema:

  * placement is RADIAL ONLY. `mode` is captured into a comment and then the loop
    computes `ang = start + i*360/count` unconditionally. A cross-lace or a helix
    cannot be expressed; both are reduced here to the ring that best approximates
    them, and the reduction is recorded in the system's own `notes`.
  * `radius` is halved before use (`dir * radius * 0.5`), so the value written
    here is twice the intended metric radius.
"""
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
comps = {c['id']: c for c in d['componentTree']}
assert 'pants-l' in comps and 'hip-belt' in comps

SYSTEMS = {
    'trouser-pinstripe': dict(
        parent='pants-l', level='micro', primitive='box', material='pantsDark',
        count=26, instanceScale=[0.006, 0.560, 0.004],
        placement={'mode': 'radial', 'axis': [0, 1, 0], 'radius': 0.164, 'startAngleDeg': 0},
        notes='26 stripes at 21.5 mm pitch read as a ring around one trouser leg; '
              'the emitter is radial-only so the second leg needs its own system.'),
    'belt-hardware': dict(
        parent='hip-belt', level='meso', primitive='box', material='brass',
        count=9, instanceScale=[0.020, 0.016, 0.011],
        placement={'mode': 'radial', 'axis': [0, 1, 0], 'radius': 0.300, 'startAngleDeg': 0},
        notes='buckles, rings and rivets distributed around the hip belt run.'),
    'boot-lacing': dict(
        parent='boot-l', level='micro', primitive='cylinder', material='leather',
        count=8, instanceScale=[0.010, 0.008, 0.008],
        placement={'mode': 'radial', 'axis': [0, 1, 0], 'radius': 0.132, 'startAngleDeg': 22.5},
        notes='REDUCED: the reference has 6 cross-lace ROWS up the shaft. The emitter '
              'places radially only, so this is authored as one ring of 8 eyelets at the '
              'cuff -- an honest ring, not the cross-lace it stands for.'),
    'braid-plait': dict(
        parent='braid-l', level='micro', primitive='sphere', material='hair',
        count=3, instanceScale=[0.014, 0.014, 0.014],
        placement={'mode': 'radial', 'axis': [0, 1, 0], 'radius': 0.020, 'startAngleDeg': 0},
        notes='REDUCED: a 3-lobe helix over 26 turns cannot be expressed radially. '
              'Authored as the 3 lobes of a single turn; the helical run is carried by '
              'the braid component geometry itself.'),
}

for sysdef in d['repetitionSystems']:
    fix = SYSTEMS.get(sysdef['id'])
    if not fix:
        continue
    if fix['parent'] not in comps:
        raise SystemExit(f"{sysdef['id']}: parent {fix['parent']} is not a component id")
    sysdef.pop('appliesTo', None)
    sysdef.pop('axis', None)
    sysdef.update(fix)

# the pinstripe ring only covers her left leg; mirror it onto the right
mirror = json.loads(json.dumps(next(s for s in d['repetitionSystems'] if s['id'] == 'trouser-pinstripe')))
mirror.update(id='trouser-pinstripe-r', parent='pants-r',
              notes='mirror of trouser-pinstripe onto her right leg.')
d['repetitionSystems'].append(mirror)

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
for s in d['repetitionSystems']:
    print(f"  {s['id']:24s} parent={s['parent']:10s} level={s['level']:6s} "
          f"count={s['count']:3d} r={s['placement']['radius']}")
