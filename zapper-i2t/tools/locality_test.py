"""Perturb one edit handle, rebuild, and check that nothing else moved.

Nova3D (arXiv 2607.22738) reports 14/18 blinded local edits passed with locality
preserved in 18/18, and contrasts that with mesh-native output where an edit has
no local scope at all because there are no parts to scope it to. Locality is the
claim that makes a generated asset editable rather than merely inspectable, so it
is worth measuring directly rather than assuming it follows from having a part
tree.

For each handle the contract declares, this:

  1. records every mesh's world bounding box in the unedited build;
  2. applies the handle's perturbation to a scratch copy of the spec;
  3. regenerates the factory and re-renders;
  4. compares the two bbox sets.

A handle passes when every part the contract lists under `moves` actually moved,
and every part NOT listed moved by less than the tolerance. Both halves matter:
a handle that moves nothing is as broken as one that moves everything, and only
checking the second half would score a no-op handle as a perfect pass.

Parts that are children of a moved part are expected to move with it -- that is
what an assembly tree is for -- so the contract's `moves` list is read as a set of
SUBTREE roots, and their descendants are excluded from the must-not-move set.

    python tools/locality_test.py --contract docs/contract.json
    python tools/locality_test.py --contract docs/contract.json --handle barrel.length
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = Path.home() / '.claude' / 'skills' / 'img2threejs'
SPEC = ROOT / 'object-sculpt-spec.json'
TOLERANCE_MM = 0.5     # below this, a bbox difference is float noise, not motion
MOVED_MM = 1.0         # above this, a part genuinely moved


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def build(tag: str) -> dict[str, dict] | None:
    gen = run([sys.executable, str(SK / 'forge/stage3_build/generate_threejs_factory.py'),
               str(SPEC), '--out', 'src/createZapperModel.ts',
               '--pass-id', 'optimization-pass', '--force'])
    if gen.returncode != 0:
        print('  generate failed:', (gen.stderr or gen.stdout).strip()[-300:])
        return None
    r = run(['node', 'tools/render.mjs', '--out', f'out/_loc_{tag}',
             '--size', '200x200', '--yaw', '0', '--allmeshes'])
    if r.returncode != 0:
        print('  render failed:', (r.stdout + r.stderr).strip()[-300:])
        return None
    meshes = json.loads((ROOT / 'out/_meshes.json').read_text(encoding='utf-8'))
    return {str(m['name']): m for m in meshes}


def descendants(spec: dict, roots: list[str]) -> set[str]:
    """Every component at or under any of `roots`, by NAME, since bboxes key on name."""
    comps = {c['id']: c for c in spec['componentTree']}
    kids: dict[str, list[str]] = {}
    for c in comps.values():
        kids.setdefault(c.get('parent') or '', []).append(c['id'])
    out, stack = set(), list(roots)
    while stack:
        cid = stack.pop()
        if cid in out or cid not in comps:
            continue
        out.add(cid)
        stack.extend(kids.get(cid, []))
    return {comps[c].get('name') or c for c in out if c in comps}


def apply_edit(spec: dict, edit: dict) -> bool:
    """Apply one handle's perturbation. Returns False if the target is not there."""
    comps = {c['id']: c for c in spec['componentTree']}
    c = comps.get(edit['component'])
    if c is None:
        return False
    path, delta = edit['field'].split('.'), float(edit['delta'])
    node: dict = c
    for key in path[:-1]:
        node = node.get(key)
        if not isinstance(node, dict):
            return False
    leaf = path[-1]
    if leaf not in node:
        return False
    cur = node[leaf]
    if isinstance(cur, list):
        idx = int(edit.get('index', 1))
        cur[idx] = cur[idx] + delta
    else:
        node[leaf] = cur + delta
    return True


def displacement(a: dict, b: dict) -> float:
    """How far a mesh's bbox moved or resized, in mm: the worst corner displacement."""
    keys = (('x0', 'x0'), ('x1', 'x1'), ('minY', 'minY'), ('maxY', 'maxY'),
            ('z0', 'z0'), ('z1', 'z1'))
    worst = 0.0
    for ka, kb in keys:
        if ka in a and kb in b:
            worst = max(worst, abs(a[ka] - b[kb]) * 1000)
    return worst


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', default='docs/contract.json')
    ap.add_argument('--handle', default=None, help='test only this handle id')
    ap.add_argument('--out', default='out/locality_report.json')
    a = ap.parse_args()

    contract = json.loads(Path(a.contract).read_text(encoding='utf-8'))
    handles = [h for h in contract.get('handles', [])
               if a.handle is None or h['id'] == a.handle]
    if not handles:
        print('no handles to test')
        return 1

    original = SPEC.read_text(encoding='utf-8')
    base_spec = json.loads(original)
    print('building the unedited reference...')
    base = build('base')
    if base is None:
        return 1
    print(f'  {len(base)} meshes')

    rows = []
    try:
        for h in handles:
            print(f"\n=== {h['id']} : {h.get('note', '')}")
            spec = json.loads(original)
            if not apply_edit(spec, h['edit']):
                print('  SKIP — the handle names a component or field that is not there')
                rows.append({'id': h['id'], 'passed': False,
                             'reason': 'handle target missing'})
                continue
            SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')
            after = build(h['id'].replace('.', '_'))
            if after is None:
                rows.append({'id': h['id'], 'passed': False, 'reason': 'build failed'})
                continue

            expect_move = descendants(base_spec, h.get('moves', []))
            moved, stuck, leaked = [], [], []
            for name, mb in base.items():
                ma = after.get(name)
                if ma is None:
                    leaked.append((name, 'part disappeared'))
                    continue
                d = displacement(mb, ma)
                if name in expect_move:
                    (moved if d >= MOVED_MM else stuck).append((name, round(d, 2)))
                elif d > TOLERANCE_MM:
                    leaked.append((name, round(d, 2)))
            gained = [n for n in after if n not in base]

            ok = not leaked and not stuck and not gained and bool(moved)
            print(f"  moved as intended : {len(moved)} of {len(expect_move)}")
            if stuck:
                print(f'  DID NOT MOVE      : {stuck[:6]}')
            if leaked:
                print(f'  LEAKED            : {leaked[:6]}')
            if gained:
                print(f'  appeared          : {gained[:6]}')
            print(f'  {"LOCAL" if ok else "NOT LOCAL"}')
            rows.append({'id': h['id'], 'passed': ok, 'moved': moved,
                         'stuck': stuck, 'leaked': leaked, 'appeared': gained})
    finally:
        SPEC.write_text(original, encoding='utf-8')
        run([sys.executable, str(SK / 'forge/stage3_build/generate_threejs_factory.py'),
             str(SPEC), '--out', 'src/createZapperModel.ts',
             '--pass-id', 'optimization-pass', '--force'])

    ok = sum(1 for r in rows if r['passed'])
    print(f'\nlocality preserved in {ok}/{len(rows)} handles')
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({'handles': rows, 'passed': ok,
                                       'total': len(rows)}, indent=1), encoding='utf-8')
    print(f'written {a.out}   (spec restored)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
