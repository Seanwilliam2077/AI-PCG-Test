import cv2, numpy as np, sys, json
def seg(path, bgboxes):
    im=cv2.imread(path); h,w=im.shape[:2]
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    mb=np.zeros((h,w),bool)
    for (y0,y1,x0,x1) in bgboxes: mb[y0:y1,x0:x1]=True
    A=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
    pred=np.zeros_like(im,np.float32)
    for c in range(3):
        co,*_=np.linalg.lstsq(A[mb],im[...,c][mb].astype(np.float32),rcond=None); pred[...,c]=A@co
    d=np.abs(im.astype(np.float32)-pred).max(-1)
    return im, d>10, np.percentile(d[mb],99)
if __name__=='__main__':
    im,fg,r=seg('ref/gun_pose0.png',[(0,40,0,225),(0,160,150,225),(100,160,0,60)])
    print('pose0 bg resid p99=%.2f'%r)
    fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)).astype(bool)
    np.save('analysis/work/p0_fg.npy',fg)
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int); H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
    warm=fg&(H<62)&(S>65); cool=fg&(H>=78)&(H<=132)
    print(' x  fgTop fgBot  warmfrac(rows 58..92)')
    for x in range(12,132):
        f=np.flatnonzero(fg[:,x])
        if len(f)==0: continue
        b=slice(58,93); n=fg[b,x].sum(); wf=warm[b,x].sum()/max(n,1)
        print('%3d  %3d %3d  %4.2f %s'%(x,f[0],f[-1],wf,'#'*int(20*wf)))
