import cv2, numpy as np
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
h,w = S.shape[:2]
small = cv2.resize(S,(w//8,h//8),interpolation=cv2.INTER_AREA)
bgs = small.copy()
for _ in range(4):
    bgs = cv2.medianBlur(bgs, 61)
    # re-inject: pixels close to model keep original, far ones keep model
    dd = np.linalg.norm(small.astype(np.float32)-bgs.astype(np.float32),axis=2)
    keep = dd < 12
    bgs = np.where(keep[...,None], small, bgs).astype(np.uint8)
bg = cv2.resize(bgs,(w,h),interpolation=cv2.INTER_CUBIC).astype(np.float32)
d = np.linalg.norm(S.astype(np.float32)-bg,axis=2)
np.save(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy", d)
print(np.percentile(d,[50,60,70,80,90,95,99]))
m = (d>16).astype(np.uint8)
m[1370:,:]=0
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
col=m.sum(axis=0)
low = col<4
runs=[];s=None
for x in range(w):
    if low[x] and s is None: s=x
    if not low[x] and s is not None:
        if x-s>5: runs.append((s,x-1,x-s)); 
        s=None
if s is not None: runs.append((s,w-1,w-s))
print("gaps:",runs)
cv2.imwrite(r"C:/AI Pipeline Test/zapper-i2t/analysis/_mask.png", m*255)
