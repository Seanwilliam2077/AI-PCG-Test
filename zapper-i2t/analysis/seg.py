import cv2, numpy as np, json
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
h,w = S.shape[:2]
lab = cv2.cvtColor(S, cv2.COLOR_BGR2LAB).astype(np.float32)
# background model: per-row median over the whole row (bg dominates each row)
bg = np.zeros_like(lab)
for y in range(h):
    bg[y,:,:] = np.median(lab[y,:,:], axis=0)
d = np.linalg.norm(lab-bg, axis=2)
print("dist stats", d.min(), np.percentile(d,[50,80,90,95,99]), d.max())
np.save(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d.npy", d)
for T in [6,8,10,12,15,20]:
    m = (d>T).astype(np.uint8)
    print(T, m.sum())
