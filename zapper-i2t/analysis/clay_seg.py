import cv2, numpy as np
from scipy import ndimage
P = r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_clay_6view.jpg"
S = cv2.imread(P); h,w = S.shape[:2]
small = cv2.resize(S,(w//8,h//8),interpolation=cv2.INTER_AREA)
bgs = small.copy()
for _ in range(4):
    bgs = cv2.medianBlur(bgs,61)
    dd = np.linalg.norm(small.astype(np.float32)-bgs.astype(np.float32),axis=2)
    bgs = np.where((dd<12)[...,None], small, bgs).astype(np.uint8)
bg = cv2.resize(bgs,(w,h),interpolation=cv2.INTER_CUBIC).astype(np.float32)
d = np.linalg.norm(S.astype(np.float32)-bg,axis=2)
np.save(r"C:/AI Pipeline Test/zapper-i2t/analysis/_dclay.npy", d)
m=(d>20).astype(np.uint8); m[1350:,:]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
cv2.imwrite(r"C:/AI Pipeline Test/zapper-i2t/analysis/_claymask.png", m*255)
col=m.sum(axis=0)
cs=np.convolve(col,np.ones(7)/7,mode='same')
low=cs<8; runs=[];s=None
for x in range(w):
    if low[x] and s is None: s=x
    if not low[x] and s is not None:
        runs.append((s,x-1,x-s)); s=None
if s is not None: runs.append((s,w-1,w-s))
print([r for r in runs if r[2]>=5])
