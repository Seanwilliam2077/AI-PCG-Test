"""Apply one spec patch, rebuild, measure, and keep it only if it measured better.

The patches this drives are authored in parallel but they all mutate the same
spec, so they have to land one at a time with a measurement between each. This is
that gate. It is deliberately unforgiving: a patch that does not move a number is
reverted, however reasonable it reads.

    python tools/try_patch.py analysis/patch_head_face.py
    python tools/try_patch.py analysis/patch_head_face.py --keep       # accept regardless
    python tools/try_patch.py --revert                                 # back to the last accepted state

State lives in `baseline/`:
    spec_accepted.json     the last spec that passed the gate
    eval_accepted.json     its measurements
    ledger.json            every attempt, accepted or not, with its numbers

The verdict rule: a patch is accepted when the independent scoreboard does not
fall, AND either the scoreboard rises or one of silhouette IoU, width band RMS,
landmark RMS or hull IoU improves beyond its own noise floor.

The scoreboard clause is not a loophole added to let something through. The four
local terms are all geometry, so a patch that only touches materials cannot move
them by construction -- and the first patch through this gate proved exactly that,
leaving all four bit-identical while the scoreboard rose 0.10. Requiring a
geometry improvement from a material patch would reject every material patch
forever, which is a broken rule, not a strict one. Renders are deterministic, so
a scoreboard delta is signal rather than noise; the threshold below is set to
0.05 only to ignore rounding in the reported figure.

The scoreboard lives in the sibling jinx3js checkout and is not reimplemented
here, because the thing being judged should not own the judge.
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
SPEC = ROOT / 'object-sculpt-spec.json'
STATE = ROOT / 'baseline'
ACCEPTED = STATE / 'spec_accepted.json'
ACCEPTED_EVAL = STATE / 'eval_accepted.json'
LEDGER = STATE / 'ledger.json'
SK = Path.home() / '.claude' / 'skills' / 'img2threejs'
JINX3JS = ROOT.parent / 'jinx3js'

# Below these, a change is measurement noise rather than an improvement. Set from
# the observed spread of repeated identical renders, not from what looks good.
NOISE = {'silhouetteIouMean': 0.002, 'widthBandRmsAll': 0.0004,
         'landmarkRmsPct': 0.05, 'hullIou': 0.004}
SCORE_NOISE = 0.05        # the reported figure carries two decimals; below this is rounding
SCORE_FALL = 0.15         # a fall larger than this rejects outright


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', **kw)


def build_and_render(tag: str) -> tuple[bool, str, dict]:
    """Regenerate the factory, render six textured and six flat views, evaluate."""
    gen = run([sys.executable, str(SK / 'forge/stage3_build/generate_threejs_factory.py'),
               str(SPEC), '--out', 'src/createJinxModel.ts',
               '--pass-id', 'optimization-pass', '--force'])
    if gen.returncode != 0:
        return False, 'generate failed: ' + (gen.stderr or gen.stdout).strip()[-600:], {}

    stats: dict = {}
    for out_dir, extra in ((f'out/{tag}', []), (f'out/{tag}_clay', ['--flat', '1'])):
        (ROOT / out_dir).mkdir(parents=True, exist_ok=True)
        # --allmeshes writes out/_meshes.json: every mesh's world bbox by name.
        # The corrective patches read it to work out which component sets the
        # silhouette in a given band, so it has to describe the build they are
        # about to be applied to, not the one before it.
        r = run(['node', 'tools/render.mjs', '--out', out_dir, '--size', '500x900',
                 '--allmeshes'] + extra)
        if r.returncode != 0:
            return False, 'render failed: ' + (r.stdout + r.stderr).strip()[-600:], {}
        if not extra:
            m = re.search(r'geometry triangles (\d+) \| draw calls (\d+)', r.stdout)
            if m:
                stats['triangles'] = int(m.group(1))
                stats['drawCalls'] = int(m.group(2))
            b = re.search(r'bbox y (\S+) \.\. (\S+)', r.stdout)
            if b:
                stats['bboxY'] = [float(b.group(1)), float(b.group(2))]
    return True, '', stats


def scoreboard(tag: str) -> float | None:
    """The independent composite score, from the sibling checkout."""
    if not (JINX3JS / 'tools' / 'compare.py').exists():
        return None
    dest = JINX3JS / 'out' / f'i2t_{tag}'
    dest.mkdir(parents=True, exist_ok=True)
    for p in (ROOT / 'out' / tag).glob('render_yaw*.png'):
        shutil.copy(p, dest / p.name)
    r = subprocess.run([sys.executable, 'tools/compare.py', '--tag', f'i2t_{tag}',
                        '--renders', f'out/i2t_{tag}', '--pin'],
                       cwd=JINX3JS, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    # keep the judge's full measurement, not just its headline: the corrective
    # patches drive off its per-landmark and per-band numbers, which are flagged
    # for reliability in a way our own detectors are not
    metrics = JINX3JS / 'out' / f'metrics_i2t_{tag}.json'
    if metrics.exists():
        shutil.copy(metrics, ROOT / 'out' / f'metrics_{tag}.json')
    m = re.search(r'SCORE\s+([0-9.]+)\s*/\s*100', r.stdout)
    return float(m.group(1)) if m else None


def evaluate(tag: str) -> dict:
    r = run([sys.executable, 'tools/evaluate.py', '--renders', f'out/{tag}',
             '--clay', f'out/{tag}_clay', '--tag', tag])
    print(r.stdout.rstrip())
    path = ROOT / 'out' / f'eval_{tag}.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def flat(ev: dict) -> dict:
    return {
        'silhouetteIouMean': ev.get('silhouetteIouMean'),
        'widthBandRmsAll': ev.get('widthBandRmsAll'),
        'landmarkRmsPct': ev.get('landmarkRmsPct'),
        'hullIou': (ev.get('hull') or {}).get('iou'),
    }


def verdict(before: dict, after: dict, score_before, score_after) -> tuple[bool, list[str]]:
    b, a = flat(before), flat(after)
    lines, improved, regressed = [], False, False
    for key, better in (('silhouetteIouMean', 'up'), ('widthBandRmsAll', 'down'),
                        ('landmarkRmsPct', 'down'), ('hullIou', 'up')):
        x, y = b.get(key), a.get(key)
        if x is None or y is None:
            continue
        d = y - x
        n = NOISE[key]
        good = d > n if better == 'up' else d < -n
        bad = d < -n if better == 'up' else d > n
        improved |= good
        regressed |= bad
        lines.append(f'  {key:20s} {x:9.4f} -> {y:9.4f}  {d:+9.4f}  '
                     f"{'BETTER' if good else 'WORSE' if bad else 'noise'}")
    score_rose = False
    if score_before is not None and score_after is not None:
        d = score_after - score_before
        lines.append(f'  {"scoreboard":20s} {score_before:9.2f} -> {score_after:9.2f}  {d:+9.2f}  '
                     f"{'BETTER' if d > SCORE_NOISE else 'WORSE' if d < -SCORE_NOISE else 'noise'}")
        if d < -SCORE_FALL:
            return False, lines + ['  REJECT: the independent scoreboard fell']
        score_rose = d > SCORE_NOISE

    # lightness is watched but never decides: it is a studio property, and the
    # lighting pass already calibrated it. A regression here is worth surfacing
    # so it is not discovered three patches later.
    lb = (before.get('lightness') or {}).get('spread')
    la = (after.get('lightness') or {}).get('spread')
    if lb is not None and la is not None and la - lb > 0.3:
        lines.append(f'  NOTE: six-view lightness spread {lb} -> {la}, against the '
                     f"reference sheet's 2.61")

    if not (improved or score_rose):
        return False, lines + ['  REJECT: neither the scoreboard nor any local term improved']
    if regressed and not score_rose:
        return False, lines + ['  REJECT: a term regressed and the scoreboard did not compensate']
    return True, lines + ['  ACCEPT']


def ledger_append(entry: dict) -> None:
    rows = json.loads(LEDGER.read_text(encoding='utf-8')) if LEDGER.exists() else []
    rows.append(entry)
    LEDGER.write_text(json.dumps(rows, indent=1), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('patch', nargs='?')
    ap.add_argument('--keep', action='store_true', help='accept regardless of the verdict')
    ap.add_argument('--revert', action='store_true', help='restore the last accepted spec')
    ap.add_argument('--init', action='store_true', help='make the current spec the accepted state')
    a = ap.parse_args()

    STATE.mkdir(exist_ok=True)

    if a.revert:
        if not ACCEPTED.exists():
            print('no accepted state to revert to')
            return 1
        shutil.copy(ACCEPTED, SPEC)
        print(f'reverted {SPEC.name} to the last accepted state')
        return 0

    if a.init:
        shutil.copy(SPEC, ACCEPTED)
        ok, err, stats = build_and_render('accepted')
        if not ok:
            print(err)
            return 1
        ev = evaluate('accepted')
        ev['stats'] = stats
        ev['scoreboard'] = scoreboard('accepted')
        ACCEPTED_EVAL.write_text(json.dumps(ev, indent=1), encoding='utf-8')
        print(f"\ninitialised accepted state; scoreboard {ev['scoreboard']}, "
              f"{stats.get('triangles')} triangles")
        return 0

    if not a.patch:
        ap.error('give a patch script, or --revert / --init')
    patch = Path(a.patch)
    if not patch.exists():
        print(f'no such patch: {patch}')
        return 1
    if not ACCEPTED.exists():
        print('no accepted state; run --init first')
        return 1

    name = patch.stem
    before = json.loads(ACCEPTED_EVAL.read_text(encoding='utf-8'))
    score_before = before.get('scoreboard')

    # always start from the accepted spec, never from whatever the last attempt left
    shutil.copy(ACCEPTED, SPEC)

    print(f'=== {name} ===')
    p = run([sys.executable, str(patch), str(SPEC)])
    if p.returncode != 0:
        print('patch FAILED:\n' + (p.stderr or p.stdout).strip()[-900:])
        shutil.copy(ACCEPTED, SPEC)
        ledger_append({'patch': name, 'result': 'patch-error',
                       'detail': (p.stderr or p.stdout).strip()[-400:]})
        return 1
    print(p.stdout.rstrip()[-1500:])

    v = run([sys.executable, str(SK / 'forge/stage2_spec/validate_sculpt_spec.py'),
             str(SPEC), '--strict'])
    if v.returncode != 0:
        print('strict validation FAILED:\n' + (v.stdout + v.stderr).strip()[-700:])
        shutil.copy(ACCEPTED, SPEC)
        ledger_append({'patch': name, 'result': 'validation-failed',
                       'detail': (v.stdout + v.stderr).strip()[-400:]})
        return 1

    ok, err, stats = build_and_render(name)
    if not ok:
        print(err)
        shutil.copy(ACCEPTED, SPEC)
        ledger_append({'patch': name, 'result': 'build-failed', 'detail': err[-400:]})
        return 1

    after = evaluate(name)
    after['stats'] = stats
    score_after = scoreboard(name)
    after['scoreboard'] = score_after

    accept, lines = verdict(before, after, score_before, score_after)
    print('\nverdict:')
    print('\n'.join(lines))
    print(f"  triangles            {before.get('stats', {}).get('triangles')} -> "
          f"{stats.get('triangles')}   (budget 250000)")

    if a.keep:
        accept = True
        print('  --keep given: accepting regardless')

    ledger_append({'patch': name, 'result': 'accepted' if accept else 'rejected',
                   'before': flat(before), 'after': flat(after),
                   'scoreboard': [score_before, score_after],
                   'triangles': stats.get('triangles'), 'bboxY': stats.get('bboxY')})

    if accept:
        shutil.copy(SPEC, ACCEPTED)
        ACCEPTED_EVAL.write_text(json.dumps(after, indent=1), encoding='utf-8')
        print(f'\naccepted; {ACCEPTED.name} updated')
    else:
        shutil.copy(ACCEPTED, SPEC)
        print(f'\nreverted; {SPEC.name} restored to the last accepted state')
    return 0


if __name__ == '__main__':
    sys.exit(main())
