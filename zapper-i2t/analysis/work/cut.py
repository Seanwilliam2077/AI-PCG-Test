import cv2, numpy as np
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
V=hsv[...,2]
sub=V[28:84,26:50]
for thr in (48,55,62,70):
    m=(sub<thr).astype(np.uint8)
    n,lab,st,ce=cv2.connectedComponentsWithStats(m,8)
    comps=[(st[i,4],ce[i][0]+26,ce[i][1]+28,st[i,2],st[i,3]) for i in range(1,n) if st[i,4]>=3]
    comps.sort(key=lambda c:c[2])
    print('--- V<%d : %d components (area>=3) ---'%(thr,len(comps)))
    for a,cx,cy,w,h in comps: print('    area=%2d  centre=(%5.1f,%5.1f)  w=%d h=%d'%(a,cx,cy,w,h))
    if len(comps)>1:
        ys=np.array([c[2] for c in comps]); d=np.diff(ys)
        print('    y-gaps: %s   mean=%.2f'%(np.round(d,2), d.mean()))
