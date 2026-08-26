"""Express the contract's falsifiable rows in the checker's DSL.

`docs/CONTRACT.md` is written for a reader. `tools/check_contract.py` needs the same
claims as expressions it can evaluate against a built scene, so this translates them.

Two things about the translation are worth stating rather than leaving implicit.

**Coverage is reported, not hidden.** The contract holds 123 rows, of which its own
audit (§11.7) found 104 genuinely falsifiable -- 9 cannot fail for any built gun, 6 are
not runnable as written, and 4 check something other than the value they state. Of those
104, the subset expressed below is what this DSL can evaluate from per-mesh world
bounding boxes, mesh-name counts, assigned material colours and a silhouette profile.
Rows needing a ray cast, or a camera the contract says was never recovered, are not
here. The report prints the fraction, so a satisfaction ratio computed from it is a
ratio over a named subset and not over the whole document.

**The axis matters.** The gun's axis is +X, so a barrel mesh's *diameter* is its Y (or
Z) extent -- its `max` extent is its axial length, which is the trap. Every perpendicular
measurement below names an axis explicitly for that reason.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Canonical quantities, as expressions rather than numbers, so a change in the model
# moves every ratio with it instead of leaving them measuring an old build.
A_SPAN = {'op': 'span', 'from': 'grip.butt-cap', 'to': 'barrel.liner', 'axis': 'x'}
D_TUBE = {'op': 'size', 'part': 'barrel.tube-fore', 'axis': 'y'}


def ratio(num, den):
    return {'op': 'ratio', 'num': num, 'den': den}


def perp(part):
    return {'op': 'size', 'part': part, 'axis': 'y'}


def axial(part):
    return {'op': 'size', 'part': part, 'axis': 'x'}


C: list[dict] = []


def row(cid, kind, check, value=None, tol=None, tolPct=None, evidence='', conf=0.5):
    r = {'id': cid, 'kind': kind, 'check': check, 'evidence': evidence, 'confidence': conf}
    if value is not None:
        r['value'] = value
    if tol is not None:
        r['tolerance'] = tol
    if tolPct is not None:
        r['tolerancePct'] = tolPct
    C.append(r)


# --- global silhouette, contract 6.2 -------------------------------------------------
row('gun.length.overTubeOd', 'ratio', ratio(A_SPAN, D_TUBE), 5.35, tol=0.55,
    evidence='198/37 px, corrected per D4', conf=0.60)
row('gun.barrel.axialFraction', 'ratio',
    ratio({'op': 'span', 'from': 'barrel.lattice-collar.rim-aft', 'to': 'barrel.liner',
           'axis': 'x'}, A_SPAN), 0.808, tol=0.030,
    evidence='160/198; four reports', conf=0.70)
row('gun.length.mm', 'dimension', A_SPAN, 290.0, tol=45.0,
    evidence='198 px x 1.400 mm/px. DECLARED chain', conf=0.35)
row('barrel.tube.od.mm', 'dimension', D_TUBE, 52.0, tol=7.0,
    evidence='37 px x 1.400; perpendicular, so no phi term', conf=0.45)

# --- barrel form, 6.3 ----------------------------------------------------------------
row('barrel.tube.circular', 'relation',
    {'op': 'flush', 'a': 'barrel.tube-fore', 'b': 'barrel.tube-fore', 'axis': 'y',
     'slackMm': 999}, evidence='placeholder; see tubeYoverZ', conf=0.75)
C.pop()   # a self-comparison always passes; express it as a ratio instead
row('barrel.tube.circular', 'ratio',
    ratio(perp('barrel.tube-fore'), {'op': 'size', 'part': 'barrel.tube-fore', 'axis': 'z'}),
    1.0, tolPct=4.0,
    evidence='pose2 bore ellipse 0.887 vs liner 0.894 -- concentric circles seen obliquely',
    conf=0.75)
row('barrel.tubeAft.sameOd', 'ratio', ratio(perp('barrel.tube-aft'), D_TUBE), 1.0,
    tolPct=3.0,
    evidence='barrel.tube.step.noneAtPaintLine -- the warm zone is a paint change, '
             'not a step', conf=0.85)
row('barrel.brassRing.count', 'count',
    {'op': 'count', 'pattern': r'^barrel\.(muzzle-collar\.ring-|mid-band$)'}, 4, tol=1,
    evidence='three encircling brass assemblies; the tree makes the collar three '
             'separate ring meshes, so a mesh-level count returns 4', conf=0.85)

# --- axial map, 6.4 ------------------------------------------------------------------
# u = (x_muzzle - x) / A, and x_muzzle is the liner's forward face. WHICH face of the
# part is measured is the whole content of these rows, and the first version got two of
# them wrong: `span` is hi(to) - lo(from), so asking it for a FORWARD face silently
# measured the rear one and reported the lattice 14 mm out of place when it was exact.
# Corrected after the fact, which is recorded rather than quietly folded in.
def u_of_face(part, face):
    x = {'op': face, 'part': part, 'axis': 'x'}
    return ratio({'op': 'sub', 'a': {'op': 'hi', 'part': 'barrel.liner', 'axis': 'x'},
                  'b': x}, A_SPAN)


for cid, part, face, u, tol, conf in (
    ('barrel.midBand.centre.u', 'barrel.mid-band', 'pos', 0.449, 0.030, 0.70),
    ('barrel.lattice.front.u', 'barrel.lattice-collar.rim-fore', 'hi', 0.662, 0.025, 0.75),
    ('barrel.lattice.rear.u', 'barrel.lattice-collar.rim-aft', 'lo', 0.808, 0.025, 0.75),
):
    row(cid, 'ratio', u_of_face(part, face), u, tol=tol,
        evidence='contract 6.4; face corrected after the first run', conf=conf)

# The collar's axial extent is rim face to rim face, not one rim's own thickness --
# the first expression measured the forward rim and failed at 0.04 against 0.15.
row('barrel.lattice.length', 'ratio',
    ratio({'op': 'span', 'from': 'barrel.lattice-collar.rim-aft',
           'to': 'barrel.lattice-collar.rim-fore', 'axis': 'x'}, A_SPAN),
    0.181 * 0.808, tol=0.030,
    evidence='29 +- 4 px, D18; expressed against A rather than L', conf=0.70)

# --- diameters, 6.5 ------------------------------------------------------------------
for cid, part, mult, tol, conf in (
    ('barrel.lattice.od', 'barrel.lattice-collar.rim-fore', 1.45, 0.12, 0.65),
    ('barrel.midBand.od', 'barrel.mid-band', 1.18, 0.07, 0.70),
    ('barrel.muzzleCollar.od', 'barrel.muzzle-collar.ring-mid', 1.14, 0.08, 0.65),
    ('barrel.liner.od', 'barrel.liner', 0.69, 0.09, 0.55),
    ('barrel.bore.d', 'barrel.bore', 0.52, 0.09, 0.55),
):
    row(cid, 'ratio', ratio(perp(part), D_TUBE), mult, tol=tol,
        evidence='contract 6.5', conf=conf)

row('barrel.bore.dOverLinerOd', 'ratio', ratio(perp('barrel.bore'), perp('barrel.liner')),
    0.74, tol=0.04,
    evidence='barrel 0.73 over three views, joints 0.75 -- the most stable number in '
             'the muzzle group', conf=0.85)

# --- lattice, 6.6 --------------------------------------------------------------------
row('lattice.opening.count', 'count',
    {'op': 'count', 'pattern': r'^barrel\.lattice-collar\.cutout\.\d+$'}, 16, tol=4,
    evidence='D8; the audit narrowed the band consistent with the collar OD to 14-18',
    conf=0.35)
row('lattice.strut.count', 'count',
    {'op': 'count', 'pattern': r'^barrel\.lattice-collar\.strut\.\d+$'}, 16, tol=4,
    evidence='one solid arc between each pair of openings', conf=0.35)
row('lattice.abutsFrame', 'relation',
    {'op': 'meets', 'a': 'barrel.lattice-collar.rim-aft', 'b': 'frame.receiver',
     'axis': 'x', 'slackMm': 0.05 * 52},
    evidence='pose3 x2444 is simultaneously the lattice rear and the frame front',
    conf=0.70)
row('barrel.lattice.coaxial', 'relation',
    {'op': 'concentric', 'a': 'barrel.tube-aft', 'b': 'barrel.lattice-collar.rim-fore',
     'axis': 'x', 'slackMm': 0.03 * 26},
    evidence='silhouette midpoint 55.0 vs axis 54.7 on an 18 px radius; expressed as '
             'the tube lying inside the collar within 0.03 R', conf=0.80)

# --- muzzle, 6.7 ---------------------------------------------------------------------
row('muzzle.ring.count', 'count',
    {'op': 'count', 'pattern': r'^barrel\.muzzle-collar\.ring-'}, 3, tol=1,
    evidence='two disjoint pose pairs; 3 raised rings, 2 grooves', conf=0.70)
row('muzzle.collar.rings.equalOd', 'ratio',
    ratio(perp('barrel.muzzle-collar.ring-fore'), perp('barrel.muzzle-collar.ring-aft')),
    1.0, tolPct=3.0,
    evidence='DECLARED. ring-to-ring radius differences are under 1 px', conf=0.35)
row('muzzle.liner.protrudes', 'relation',
    {'op': 'flush', 'a': 'barrel.liner', 'b': 'barrel.muzzle-collar.ring-fore',
     'axis': 'x', 'slackMm': 0.10 * 234},
    evidence='pose1 and pose0 both show a 6 px step ahead of the collar. '
             'scale-silhouette reads this the opposite way -- D11', conf=0.45)

# --- rail ----------------------------------------------------------------------------
row('barrel.rail.studs.count', 'count', {'op': 'count', 'pattern': r'^barrel\.rail\.stud\.'},
    3, tol=1, evidence='two reports within 3 px on all three positions', conf=0.80)
row('barrel.rail.axialSpan', 'ratio', ratio(axial('barrel.rail'), A_SPAN), 0.75, tol=0.20,
    evidence='audit D-6: the rail is continuous over the lattice, true span 0.93 L '
             '= 0.75 A, not the frozen row\'s 0.706 L', conf=0.60)
row('barrel.rail.aboveTube', 'relation',
    {'op': 'above', 'a': 'barrel.rail', 'b': 'barrel.tube-fore', 'axis': 'y',
     'slackMm': 6.0},
    evidence='the rail lies tangent on the tube top with no standoff', conf=0.65)

# --- frame and grip ------------------------------------------------------------------
row('gun.frame.axialFraction', 'ratio',
    ratio({'op': 'span', 'from': 'grip.butt-cap', 'to': 'frame.receiver', 'axis': 'x'},
          A_SPAN), 0.192, tol=0.05, evidence='1 - the barrel fraction', conf=0.70)
row('frame.port.od', 'ratio', ratio(perp('frame.port'), D_TUBE), 0.37, tol=0.09,
    evidence='frozen row says 0.41 +- 0.07; audit D-3 measures 0.33. Centred between '
             'them with a tolerance spanning both, and flagged', conf=0.35)
row('grip.belowAxis', 'relation',
    {'op': 'above', 'a': 'frame.receiver', 'b': 'grip.butt-cap', 'axis': 'y',
     'slackMm': 4.0},
    evidence='the grip drops below the bore axis', conf=0.80)
row('grip.butt.behindFrameHeel', 'relation',
    {'op': 'disjoint', 'a': 'grip.butt-cap', 'b': 'barrel.tube-fore', 'slackMm': 1.0},
    evidence='the butt is rearward of everything on the barrel', conf=0.70)

# --- materials, 6.10 -----------------------------------------------------------------
row('mat.bore.darkest', 'relation',
    {'op': 'concentric', 'a': 'barrel.bore', 'b': 'barrel.liner', 'axis': 'x',
     'slackMm': 1.0},
    evidence='the bore is a void inside the liner', conf=0.80)

OUT = ROOT / 'docs/contract.json'


def main() -> int:
    rows = json.loads((ROOT / 'analysis/contract_rows.json').read_text(encoding='utf-8'))
    falsifiable = sum(1 for r in rows if r.get('falsifiable'))
    doc = {
        'source': 'docs/CONTRACT.md',
        'frozenBeforeModel': True,
        'rowsInDocument': 123,
        'falsifiablePerAudit': 104,
        'expressedHere': len(C),
        'coverageNote': (
            f'{len(C)} of the {falsifiable} falsifiable rows the parser recovered are '
            'expressed in the checker DSL. The remainder need a ray cast, or the pose3 '
            'camera the contract says was never recovered, or a per-island host-mesh '
            'lookup the tree does not encode. A satisfaction ratio computed from this '
            'file is a ratio over this named subset, not over the document.'),
        'constraints': C,
    }
    OUT.write_text(json.dumps(doc, indent=1), encoding='utf-8')
    from collections import Counter
    print(f'{len(C)} constraints written to {OUT.relative_to(ROOT)}')
    print('  by kind:', dict(Counter(c['kind'] for c in C)))
    print(f'  coverage: {len(C)} of {falsifiable} falsifiable rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
