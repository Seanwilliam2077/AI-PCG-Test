import cv2, numpy as np
im=cv2.imread('ref/gun_pose2.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
fg=np.load('analysis/work/p2_fg.npy')
def seeded(m,sy,sx):
    n,lab,st,ce=cv2.connectedComponentsWithStats((m*255).astype(np.uint8),8)
    k=lab[sy,sx]
    if k==0: return None
    return lab==k, st[k,4]
def rep(name,m,sy,sx):
    r=seeded(m,sy,sx)
    if r is None: print('%-18s seed not in mask'%name); return
    L,a=r
    Lf=cv2.morphologyEx((L*255).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    cs,_=cv2.findContours(Lf,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=cv2.contourArea); e=cv2.fitEllipse(c)
    ys,xs=np.nonzero(L)
    print('%-18s area=%4d bbox x[%d..%d]w=%2d y[%d..%d]h=%2d | c=(%.1f,%.1f) maj=%.2f min=%.2f ang=%.0f ratio=%.3f'%(
        name,a,xs.min(),xs.max(),xs.max()-xs.min()+1,ys.min(),ys.max(),ys.max()-ys.min()+1,
        e[0][0],e[0][1],max(e[1]),min(e[1]),e[2],min(e[1])/max(e[1])))
    return e
box=np.zeros_like(fg); box[62:118,86:126]=True
for t in (70,75,80,85):
    rep('bore V<%d'%t, fg&box&(V<t), 90,104)
cool=fg&box&(H>=80)&(H<=140)
rep('liner+bore cool', (cool|(fg&box&(V<80))), 90,104)
warm=fg&box&(H<62)&(S>55)
rep('collar warm ring', warm, 72,100)
box2=np.zeros_like(fg); box2[58:122,80:130]=True
rep('collar+all outer', fg&box2, 72,100)
