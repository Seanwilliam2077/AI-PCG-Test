"""sash: dump the compare.py width profile ('sum' = all runs) for a t band."""
import json
import sys

m = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'out/metrics_sash.json'))
lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.42
hi = float(sys.argv[3]) if len(sys.argv) > 3 else 0.66
key = sys.argv[4] if len(sys.argv) > 4 else 'sum'
H = 1.72

rows = {}
yaws = []
for v in m['views']:
    y = v['yaw']
    yaws.append(y)
    for b in v['geometry']['profile']['bands']:
        if lo <= b['t'] <= hi:
            rows.setdefault(b['t'], {})[y] = (b[key]['ref_pct'], b[key]['render_pct'], b['part'])

yaws = sorted(set(yaws))
print(f"width profile '{key}' (% of figure height)")
print('   t   y(m)   band       ' + ''.join(f'|  yaw{int(y):<3} ref  ren   d ' for y in yaws))
for t in sorted(rows, reverse=True):
    cells, band = [], ''
    for y in yaws:
        e = rows[t].get(y)
        if not e:
            cells.append('|        -         ')
            continue
        r, d, band = e
        cells.append(f'|{r:8.2f}{d:6.2f}{d - r:+6.2f}')
    print(f'{t:5.3f} {t * H:5.3f} {band[:10]:<11}' + ''.join(cells))
