"""pants: per-view score terms for two metrics files, side by side."""
import json
import sys

A = json.load(open(sys.argv[1]))
B = json.load(open(sys.argv[2]))
keys = None
print("%-6s %-22s %8s %8s %8s" % ("yaw", "term", sys.argv[1][-14:], sys.argv[2][-14:], "delta"))
for va, vb in zip(A["views"], B["views"]):
    sa, sb = va["score"], vb["score"]
    if keys is None:
        keys = [k for k in sa if isinstance(sa[k], (int, float))]
    for k in keys:
        d = sb[k] - sa[k]
        flag = " <<<" if abs(d) > 0.01 else ""
        print("%-6s %-22s %8.4f %8.4f %+8.4f%s" % (va["yaw"], k, sa[k], sb[k], d, flag))
    print()
print("total %.3f -> %.3f" % (A["score"], B["score"]))
