"""sash: write the round-1-equivalent spec (A) or restore round 2 (B).

    python out/sash_ab.py save          # copy the live spec to out/sash_new.json
    python out/sash_ab.py A             # write the round-1 numbers
    python out/sash_ab.py B             # restore out/sash_new.json

Only spec numbers differ between A and B; the round-1 wrap is reproducible from
the round-2 code by disabling the midline cut (splitX beyond the body), putting
the flap's hem back where the old `fold` had it, and shrinking the apron's
bearing band back to its old end.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'spec', 'parts', 'sash.json')
KEEP = os.path.join(ROOT, 'out', 'sash_new.json')

OLD_HEM = [[-3.1416, 0.998], [-2.6, 0.972], [-2.1, 0.947], [-1.55, 0.912],
           [-1.1, 0.928], [-0.7, 0.972], [-0.3, 1.002], [0.0, 1.008],
           [1.2, 1.010], [2.4, 1.004], [3.1416, 0.998]]
OLD_FOLD = [[-3.1416, 1.115], [-2.45, 1.11], [-1.55, 0.966], [-0.65, 1.11],
            [3.1416, 1.115]]
OLD_CANVAS_HEM = [[-3.1416, 1.06], [-1.05, 1.056], [-0.75, 1.008], [-0.45, 0.982],
                  [-0.1, 0.966], [0.3, 0.948], [0.55, 0.937], [0.75, 0.946],
                  [1.15, 1.0], [1.6, 1.03], [2.0, 1.062], [3.1416, 1.06]]

mode = sys.argv[1]
if mode == 'save':
    shutil.copyfile(LIVE, KEEP)
elif mode == 'B':
    shutil.copyfile(KEEP, LIVE)
elif mode == 'A':
    d = json.load(open(KEEP))
    s = d['sash']
    s['splitX'] = 10.0
    s['hem'] = OLD_HEM
    s['flapHem'] = OLD_FOLD
    s['flapOut'] = 0.008
    s['flapFloor'] = 0.90
    s['canvas']['wedge'] = [-0.68, 1.85]
    s['canvas']['hem'] = OLD_CANVAS_HEM
    s['canvas']['round'] = 0.014
    json.dump(d, open(LIVE, 'w'), indent=2)
else:
    raise SystemExit('save | A | B')
print(mode, 'ok')
