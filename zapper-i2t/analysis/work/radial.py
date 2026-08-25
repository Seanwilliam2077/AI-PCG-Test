import cv2, numpy as np
im=cv2.imread('ref/gun_pose2.png').astype(np.float32); hsv=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_BGR2HSV).astype(int)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
fg=np.load('analysis/work/p2_fg.npy')
cy,cx=89.2,104.2
def sample(a,r,arr):
    y=cy+r*np.sin(a); x=cx+r*np.cos(a)
    yi,xi=int(round(y)),int(round(x))
    if 0<=yi<arr.shape[0] and 0<=xi<arr.shape[1]: return arr[yi,xi]
    return None
print('ang  r_bore_edge  r_liner_out  r_fg_out   (px from bore centre)')
res=[]
for deg in range(0,360,10):
    a=np.radians(deg)
    rb=rl=rf=None
    for r in np.arange(0.5,40,0.25):
        v=sample(a,r,V); c=sample(a,r,H); s=sample(a,r,S); f=sample(a,r,fg)
        if v is None: break
        if rb is None and v>=88: rb=r
        if rb is not None and rl is None and (c is not None and c<62 and s>55): rl=r
        if f: rf=r
    res.append((deg,rb,rl,rf))
    print('%3d  %s  %s  %s'%(deg,'%5.2f'%rb if rb else '  -  ','%5.2f'%rl if rl else '  -  ','%5.2f'%rf if rf else '  -  '))
import statistics as st
for i,nm in [(1,'bore edge'),(2,'liner outer'),(3,'fg outer')]:
    v=[r[i] for r in res if r[i]]
    print('%-12s n=%2d  mean=%.2f  median=%.2f  min=%.2f max=%.2f'%(nm,len(v),sum(v)/len(v),st.median(v),min(v),max(v)))
