import cv2, numpy as np
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
m = (d>25).astype(np.uint8); m[1345:,:]=0
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
col = m.sum(axis=0)
# smooth
k=np.ones(9)/9; cs=np.convolve(col,k,mode='same')
prev=None
for x in range(0,3000,1):
    pass
# report local minima regions
lows=[x for x in range(3000) if cs[x]<20]
runs=[];s=None
for x in range(3000):
    if x in set(lows): pass
runs=[]
s=None
low=cs<20
for x in range(3000):
    if low[x] and s is None: s=x
    if not low[x] and s is not None:
        runs.append((s,x-1,x-s)); s=None
if s is not None: runs.append((s,2999,3000-s))
print([r for r in runs if r[2]>=4])
