"""Let the measured material assignment reach the generator.

Every component already carried the right answer in `materialRef` -- boots
`leather`, lacing `laceMagenta`, tank `glassTank`, nails `nailTeal`, hair
`hair`. The generator reads `material`, and `material` had been blanket-set to
`pants` on all 46 garment/prop/hair components and `skin` on 50 body ones. So 14
of the 20 measured materials were orphaned: they had crops, five PBR maps each
and a confidence report, and nothing on screen ever asked for them.

That is why the render read as two colours. The fix is to stop keeping the answer
in a field nobody reads.

The bare legs are the one case `materialRef` does not cover: the trousers end
below the knee, so shin and thigh are skin, not trouser fabric.
"""
import collections
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
known = {m['id'] for m in d['materials']}

BARE = {'shin-l': 'skin', 'shin-r': 'skin', 'thigh-l': 'skin', 'thigh-r': 'skin'}

moved, skipped = 0, []
for c in d['componentTree']:
    want = BARE.get(c['id']) or c.get('materialRef')
    if not want:
        continue
    if want not in known:
        skipped.append((c['id'], want))
        continue
    if c.get('material') != want:
        c['material'] = want
        c['materialLayers'] = [want]
        moved += 1

use = collections.Counter(c.get('material') for c in d['componentTree'])
json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)

print(f'reassigned {moved} components')
if skipped:
    print('materialRef naming a material that does not exist:', skipped)
print('\nmaterial usage now:')
orphan = []
for m in d['materials']:
    n = use.get(m['id'], 0)
    print(f"  {m['id']:13s} {n:3d}")
    if n == 0:
        orphan.append(m['id'])
print('still orphaned:', orphan or 'none')
