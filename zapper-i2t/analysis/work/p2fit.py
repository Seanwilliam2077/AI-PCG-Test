import cv2, numpy as np
im=cv2.imread('ref/gun_pose2.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
fg=np.load('analysis/work/p2_fg.npy')
box=np.zeros_like(fg); box[60:120,70:128]=True
def big(m, op=None):
    mm=(m*255).astype(np.uint8)
    if op: mm=cv2.morphologyEx(mm,op,np.ones((3,3),np.uint8))
    n,lab,st,ce=cv2.connectedComponentsWithStats(mm,8)
    if n<2: return None
    k=1+np.argmax(st[1:,4]); return (lab==k),st[k,4]
def rep(name,m):
    r=big(m,cv2.MORPH_CLOSE)
    if r is None: print(name,'none'); return None
    L,a=r; ys,xs=np.nonzero(L)
    Lf=cv2.morphologyEx((L*255).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(Lf,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=cv2.contourArea)
    e=cv2.fitEllipse(c)
    print('%-16s area=%4d bbox x[%d..%d]w=%2d y[%d..%d]h=%2d | ellipse c=(%.1f,%.1f) axes=%.2f x %.2f ang=%.0f ratio=%.3f'%(
        name,a,xs.min(),xs.max(),xs.max()-xs.min()+1,ys.min(),ys.max(),ys.max()-ys.min()+1,
        e[0][0],e[0][1],max(e[1]),min(e[1]),e[2],min(e[1])/max(e[1])))
    return e
bore = fg&box&(V<78)
rep('bore(V<78)',bore)
rep('bore(V<72)',fg&box&(V<72))
rep('bore(V<85)',fg&box&(V<85))
# liner: cool ring -> take cool|bore union outer boundary
cool = fg&box&(H>=80)&(H<=140)
rep('liner+bore',cool|bore)
warm = fg&box&(H<62)&(S>60)
rep('collar outer',warm|cool|bore)
