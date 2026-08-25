import cv2, numpy as np
im=cv2.imread('ref/gun_pose1.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]; h,w=V.shape
yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
mb=np.zeros((h,w),bool); mb[0:30,:]=True; mb[:,0:30]=True; mb[120:,0:120]=True
A=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
pred=np.zeros_like(im,np.float32)
for c in range(3):
    co,*_=np.linalg.lstsq(A[mb],im[...,c][mb].astype(np.float32),rcond=None); pred[...,c]=A@co
d=np.abs(im.astype(np.float32)-pred).max(-1)
print('bg resid p99=%.1f'%np.percentile(d[mb],99))
fg=d>10
fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)).astype(bool)
np.save('analysis/work/p1_fg.npy',fg)
warm=fg&(H<62)&(S>65); cool=fg&(H>=78)&(H<=132)
np.save('analysis/work/p1_warm.npy',warm); np.save('analysis/work/p1_cool.npy',cool)
print('\n x   fgTop fgBot | coolTop coolBot coolN | warmfrac(rows45..105)')
for x in range(34,185):
    f=np.flatnonzero(fg[:,x]); c=np.flatnonzero(cool[30:110,x])
    if len(f)==0: continue
    band=slice(45,106); nb=fg[band,x].sum(); wf=warm[band,x].sum()/max(nb,1)
    ct=cb=cn=-1
    if len(c): ct,cb,cn=c[0]+30,c[-1]+30,len(c)
    print('%3d   %3d %3d  |  %3d %3d %3d |  %4.2f %s'%(x,f[0],f[-1],ct,cb,cn,wf,'#'*int(20*wf)))
