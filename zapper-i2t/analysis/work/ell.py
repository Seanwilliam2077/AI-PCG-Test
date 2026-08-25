import cv2, numpy as np
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
box=np.zeros_like(fg); box[35:90,160:186]=True
cool = fg & box & (H>=78)&(H<=140)
dark = fg & box & (V<72)
for name,m in [('cool muzzle-face region',cool),('dark bore region',dark)]:
    mm=(m*255).astype(np.uint8)
    mm=cv2.morphologyEx(mm,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,lab,st,ce=cv2.connectedComponentsWithStats(mm,8)
    k=1+np.argmax(st[1:,4]) if n>1 else None
    if k is None: print(name,'none'); continue
    ys,xs=np.nonzero(lab==k)
    print('%-24s area=%d  x[%d..%d] w=%d  y[%d..%d] h=%d  centroid=(%.1f,%.1f)'%(
        name,st[k,4],xs.min(),xs.max(),xs.max()-xs.min()+1,ys.min(),ys.max(),ys.max()-ys.min()+1,xs.mean(),ys.mean()))
    if len(xs)>=5:
        e=cv2.fitEllipse(np.stack([xs,ys],1).astype(np.float32).reshape(-1,1,2))
        print('    fitEllipse center=(%.2f,%.2f) axes=(%.2f,%.2f) ang=%.1f  minor/major=%.3f'%(
            e[0][0],e[0][1],min(e[1]),max(e[1]),e[2],min(e[1])/max(e[1])))
