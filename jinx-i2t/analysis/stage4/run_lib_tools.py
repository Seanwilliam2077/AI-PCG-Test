import json, sys, io
from pathlib import Path
sys.path.insert(0, r"C:/Users/lvhaochen/.claude/skills/img2threejs/forge/stage4_review")
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r"C:/AI Pipeline Test/jinx-i2t")
OUT = ROOT/"analysis/stage4/raw"
spec = json.loads((ROOT/"object-sculpt-spec.json").read_text(encoding="utf-8"))

# ---- geometry_integrity ----
from geometry_integrity import measure_geometry_integrity
payload = {"components": spec["componentTree"],
           "performanceBudget": {"triangleBudget": spec["performanceBudget"]["targetTriangles"]},
           "lodPlan": spec.get("lodPlan")}
gi = measure_geometry_integrity(payload)
(OUT/"geometry_integrity.json").write_text(json.dumps(gi, indent=1), encoding="utf-8")
print("=== geometry_integrity ===")
print("passed:", gi["passed"], "| meshes:", len(gi["meshes"]), "| triangleCount:", gi["triangleCount"],
      "budget:", gi["triangleBudget"], "| lodPlanPresent:", gi["lodPlanPresent"], "lodPlanValid:", gi["lodPlanValid"])
print("seams checked:", len(gi["seams"]), "| failures:", len(gi["failures"]), "| issues:", len(gi["issues"]))
for f in gi["failures"][:12]: print("  !", f)
notop = sum(1 for m in gi["meshes"] if m.get("note") == "mesh topology not supplied")
print("meshes with no topology supplied:", notop, "/", len(gi["meshes"]))
notri = sum(1 for m in gi["meshes"] if m.get("triangleCount") is None)
print("meshes with no triangleCount:", notri)
from collections import Counter
print("issue codes:", Counter(i["code"] for i in gi["issues"]))
if gi["seams"]:
    bad=[s for s in gi["seams"] if s["overlap"]<s["minimum"]]
    print("seams below minimum:", len(bad), bad[:5])

# ---- multi_pass ----
print()
print("=== multi_pass ===")
import multi_pass
print("PASS_IDS:", multi_pass.PASS_IDS)
recs = multi_pass.default_pass_records("out/lighting-pass")
def probe(p):
    from PIL import Image
    im = Image.open(p); return {"type":"png","width":im.width,"height":im.height}
errs = multi_pass.validate_pass_records(ROOT/"manifest.json", recs, probe, require_complete=True, label="lighting-pass")
print("validate_pass_records errors:", len(errs))
for e in errs: print("  !", e)
(OUT/"multi_pass.json").write_text(json.dumps({"passIds":list(multi_pass.PASS_IDS),"errors":errs}, indent=1), encoding="utf-8")

# ---- correction_loop history ----
print()
print("=== correction_loop history build ===")
hist=[]
for r in spec["reviewHistory"]:
    mism = r.get("mismatches") or []
    tags = [m if isinstance(m,str) else (m.get("id") or m.get("issue") or json.dumps(m))[:60] for m in mism]
    hist.append({"fidelity": float(r.get("estimatedFidelity") or 0.0), "defectTags": tags, "reverted": False,
                 "_pass": r.get("passId"), "_action": r.get("action")})
for h in hist: print(" ", h["_pass"], h["fidelity"], "defects:", len(h["defectTags"]), "action:", h["_action"])
clean=[{k:v for k,v in h.items() if not k.startswith("_")} for h in hist]
(OUT/"correction_history.json").write_text(json.dumps(clean, indent=1), encoding="utf-8")
