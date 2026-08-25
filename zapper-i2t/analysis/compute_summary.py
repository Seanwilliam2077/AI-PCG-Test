import json, numpy as np
# ---- measured pixel landmarks (sheet coords, textured 5-view) ----
R = {  # muzzle-rim x, lattice-front x, tube OD (tube only, px), gun projected length px
 "pose0": dict(muz=58.0, lat=138.0, rear=200.0, tube=31.0, sil=34.5),
 "pose1": dict(muz=682.0, lat=800.0, rear=None, tube=36.0, sil=43.0),
 "pose2": dict(muz=1772.0, lat=1700.0, rear=None, tube=45.0, sil=46.0),
 "pose3": dict(muz=2603.0, lat=2472.0, rear=2410.0, tube=37.0, sil=42.6),
}
axis_deg = {"pose0":-1.1,"pose1":-3.7,"pose2":11.3,"pose3":-2.7}
seg = {}
for k,v in R.items():
    L = abs(v["muz"]-v["lat"])/np.cos(np.radians(axis_deg[k]))
    seg[k] = dict(muz_to_lat_px=round(L,1), tube_px=v["tube"], ratio=round(L/v["tube"],3))
base = seg["pose3"]["ratio"]
phi3 = 16.0
out={}
for k,v in seg.items():
    c = v["ratio"]/base*np.cos(np.radians(phi3))
    c = min(c,1.0)
    out[k]=dict(**v, phi_deg=round(float(np.degrees(np.arccos(c))),1),
                phi_lower_bound_deg=round(float(np.degrees(np.arccos(min(v['ratio']/base,1.0)))),1))
print(json.dumps(out, indent=1))
# total length via pose0 proportion
tot_frac = (200.0-58.0)/(138.0-58.0)
print("pose0 total/(muz->lat) =", round(tot_frac,3))
L3 = seg["pose3"]["muz_to_lat_px"]
tot_proj = L3*tot_frac
tot_true = tot_proj/np.cos(np.radians(phi3))
print("pose3 total projected px", round(tot_proj,1), " true-axial px", round(tot_true,1))
MMPX = 1.39
print("total mm", round(tot_true*MMPX))
for nm,px in [("tube OD",37),("muzzle collar OD",42),("lattice collar OD",51),
              ("bore opening",23),("max height",116),("axis->grip heel",80.6),
              ("muzzle->lattice front (true axial)",L3/np.cos(np.radians(phi3))),
              ("lattice axial len",(163-131)/np.cos(np.radians(phi3)))]:
    print(f"  {nm:38s} {px:6.1f} px  = {px*MMPX:6.1f} mm   /tubeOD = {px/37:5.3f}")
