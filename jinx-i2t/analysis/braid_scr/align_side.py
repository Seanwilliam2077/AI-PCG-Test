import cv2, numpy as np
def loadmask(p):
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED); return (im[:,:,3]>127)
def norm(p):
    m=loadmask(p); ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max()
    H=y1-y0+1; s=1024.0/H
    return m,y0,y1,H,s,xs.min(),xs.max()
for p in ['ref/views/clay_0.png','out/final_clay/render_yaw90.png']:
    m,y0,y1,H,s,xmin,xmax=norm(p)
    ys,xs=np.nonzero(m)
    print(p,'H',H,'scale',round(s,5),'bboxx',xmin,xmax,'bbox_cx',round((xmin+xmax)/2,2),'centroid_x',round(xs.mean(),2))
    # centroid restricted to torso band t 0.60..0.85 (body only, less braid)
    for lo,hi in [(0.0,1.0),(0.60,0.85),(0.70,0.80)]:
        sel=( (y1-ys)/(H-1)>=lo ) & ( (y1-ys)/(H-1)<=hi )
        print('   band %.2f-%.2f centroid_x %.2f  n=%d'%(lo,hi,xs[sel].mean(),sel.sum()))
