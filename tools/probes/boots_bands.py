"""boots: print the low-t width bands from a compare.py metrics json."""
import json
import sys

path = sys.argv[1]
tmax = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
d = json.load(open(path))
H = 1.72
for v in sorted(d["views"], key=lambda v: v["yaw"]):
    g = v["geometry"]
    print("yaw %-4s panel %-12s widRMS %.2f  IoU %.3f"
          % (v["yaw"], v.get("panel_name", v.get("panel")),
             g["width_rms_core_pct"], g["full"]["iou"]))
    print("    t     y(m)  part            ref%H  ren%H    d%H   |  refm   renm  nrunR nrunN")
    for b in g["profile"]["bands"]:
        if b["t"] > tmax:
            continue
        c = b["core"]
        print("  %.3f  %.3f  %-14s %6.2f %6.2f %+6.2f  | %.3f  %.3f   %.1f   %.1f"
              % (b["t"], b["t"] * H, b["part"], c["ref_pct"], c["render_pct"],
                 c["d_pct"], c["ref_pct"] * H / 100, c["render_pct"] * H / 100,
                 b["nrun_ref"], b["nrun_render"]))
    print()
