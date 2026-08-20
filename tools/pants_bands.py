"""pants: dump the compare.py width bands for the leg region, per view.

    python tools/pants_bands.py out/metrics_r3pants_base.json
"""
import json
import sys

path = sys.argv[1]
lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10
hi = float(sys.argv[3]) if len(sys.argv) > 3 else 0.62
m = json.load(open(path))
print("score %.2f  width_rms/view:" % m["score"])
for v in m["views"]:
    g = v["geometry"]
    print("  yaw %3s iou %.4f  width_rms_core %.2f  bias %.2f  landmark_rms %.2f"
          % (v["yaw"], g["full"]["iou"], g["width_rms_core_pct"],
             g["width_bias_core_pct"], g["landmark_rms_pct"]))

ts = [b["t"] for b in m["views"][0]["geometry"]["profile"]["bands"]
      if lo <= b["t"] <= hi]
hdr = "  %-6s" % "t"
for v in m["views"]:
    hdr += " | yaw%-3s ref  ren   d%%" % v["yaw"]
print(hdr)
for t in ts:
    line = "  %-6.3f" % t
    for v in m["views"]:
        b = next(x for x in v["geometry"]["profile"]["bands"] if x["t"] == t)
        c = b["core"]
        line += " | %5.2f %5.2f %+5.0f" % (c["ref_pct"], c["render_pct"],
                                           c["d_rel_pct"])
    print(line)

print("\nrun counts (ref/render)")
for t in ts:
    line = "  %-6.3f" % t
    for v in m["views"]:
        b = next(x for x in v["geometry"]["profile"]["bands"] if x["t"] == t)
        line += " | %d/%d" % (b["nrun_ref"], b["nrun_render"])
    print(line)
