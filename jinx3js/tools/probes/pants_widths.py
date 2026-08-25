"""pants: print the per-band width table (ref vs render) out of a metrics json.

    python out/pants_widths.py out/metrics_pinned.json 0.25 0.60
"""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "out/metrics_pinned.json"
lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
hi = float(sys.argv[3]) if len(sys.argv) > 3 else 0.60
d = json.load(open(path))
H = 1.72

print(f"{path}   score {d.get('score')}")
for v in d["views"]:
    bands = v["geometry"]["profile"]["bands"]
    print(f"=== yaw {v['yaw']:.0f}  panel {v['panel_name']}  IoU {v['geometry']['full']['iou']:.3f}"
          f"  width_rms_core {v['geometry']['width_rms_core_pct']:.2f}")
    print(f"   {'t':>6} {'y(m)':>6}  {'core ref':>8} {'core ren':>8} {'d%':>7}   "
          f"{'full ref':>8} {'full ren':>8}  {'nrun r/m':>9}  part")
    for b in bands:
        if lo <= b["t"] <= hi:
            c, f = b["core"], b["full"]
            print(f"   {b['t']:6.3f} {b['t']*H:6.3f}  {c['ref_pct']:8.2f} {c['render_pct']:8.2f} "
                  f"{c['d_rel_pct']:+7.1f}   {f['ref_pct']:8.2f} {f['render_pct']:8.2f}  "
                  f"{b['nrun_ref']:4.1f}/{b['nrun_render']:4.1f}  {b['part']}")
