"""pants: side-by-side A/B of two metrics jsons, per view and per width band."""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
lo = float(sys.argv[3]) if len(sys.argv) > 3 else 0.26
hi = float(sys.argv[4]) if len(sys.argv) > 4 else 0.56
H = 1.72

print(f"A = {sys.argv[1]}  score {a['score']:.2f}")
print(f"B = {sys.argv[2]}  score {b['score']:.2f}")
print()
print(f"{'yaw':>5} {'panel':>10} | {'IoU A':>6} {'IoU B':>6} {'d':>6} | "
      f"{'wrms A':>6} {'wrms B':>6} {'d':>6} | {'score A':>7} {'score B':>7}")
for va, vb in zip(a["views"], b["views"]):
    ga, gb = va["geometry"], vb["geometry"]
    print(f"{va['yaw']:5.0f} {va['panel_name']:>10} | {ga['full']['iou']:6.3f} {gb['full']['iou']:6.3f} "
          f"{gb['full']['iou']-ga['full']['iou']:+6.3f} | "
          f"{ga['width_rms_core_pct']:6.2f} {gb['width_rms_core_pct']:6.2f} "
          f"{gb['width_rms_core_pct']-ga['width_rms_core_pct']:+6.2f} | "
          f"{va['score']['total'] if isinstance(va['score'],dict) and 'total' in va['score'] else 0:7.2f} "
          f"{vb['score']['total'] if isinstance(vb['score'],dict) and 'total' in vb['score'] else 0:7.2f}")

for va, vb in zip(a["views"], b["views"]):
    ba = va["geometry"]["profile"]["bands"]
    bb = vb["geometry"]["profile"]["bands"]
    print(f"\n=== yaw {va['yaw']:.0f}  {va['panel_name']}")
    print(f"   {'t':>6} {'y(m)':>6} {'ref':>7} | {'A ren':>7} {'A d':>7} {'nA':>3} | "
          f"{'B ren':>7} {'B d':>7} {'nB':>3}")
    for x, y in zip(ba, bb):
        if lo <= x["t"] <= hi:
            print(f"   {x['t']:6.3f} {x['t']*H:6.3f} {x['core']['ref_pct']:7.2f} | "
                  f"{x['core']['render_pct']:7.2f} {x['core']['d_pct']:+7.2f} {x['nrun_render']:3.0f} | "
                  f"{y['core']['render_pct']:7.2f} {y['core']['d_pct']:+7.2f} {y['nrun_render']:3.0f}")
