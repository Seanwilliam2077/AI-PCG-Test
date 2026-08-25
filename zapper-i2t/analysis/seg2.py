import cv2, numpy as np
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
h,w = S.shape[:2]
lab = cv2.cvtColor(S, cv2.COLOR_BGR2LAB).astype(np.float32)
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d.npy")
m0 = (d>18).astype(np.uint8)
m0[1380:,:]=0   # strip watermark band
col = m0.sum(axis=0)
# print runs of low activity
low = col < 6
runs=[];s=None
for x in range(w):
    if low[x] and s is None: s=x
    if not low[x] and s is not None:
        if x-s>8: runs.append((s,x-1,x-s))
        s=None
if s is not None: runs.append((s,w-1,w-s))
print("gap runs:", runs)
