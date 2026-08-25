import cv2, numpy as np
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
H,V=hsv[...,0],hsv[...,2]
box=np.zeros_like(fg); box[35:90,160:186]=True
for thr in (65,72,80,88):
    m = fg&box&(V<thr)
    mm=cv2.morphologyEx((m*255).astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,lab,st,ce=cv2.connectedComponentsWithStats(mm,8)
    if n<2: print('thr',thr,'none'); continue
    k=1+np.argmax(st[1:,4]); L=(lab==k)
    vr=max((L[:,x].sum() for x in range(160,186)))
    hr=max((L[y,:].sum() for y in range(35,90)))
    ys,xs=np.nonzero(L)
    print('bore V<%d: area=%3d  maxVrun=%2d maxHrun=%2d  bboxW=%2d bboxH=%2d  ratio(H/V)=%.3f  cx=%.1f cy=%.1f'%(
        thr,st[k,4],vr,hr,xs.max()-xs.min()+1,ys.max()-ys.min()+1,hr/vr,xs.mean(),ys.mean()))
# cool face outer: vertical extent per column
cool=fg&box&(H>=78)&(H<=140)
cm=cv2.morphologyEx((cool*255).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))>0
print('\ncool-face vertical runs by column:')
for x in range(166,186):
    idx=np.flatnonzero(cm[:,x])
    if len(idx): print('  x=%d  y[%d..%d] n=%d'%(x,idx[0],idx[-1],len(idx)))
print('\ncool-face horizontal runs by row:')
for y in range(48,80):
    idx=np.flatnonzero(cm[y,160:186])
    if len(idx): print('  y=%d  x[%d..%d] n=%d'%(y,160+idx[0],160+idx[-1],len(idx)))
