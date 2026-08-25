import cv2, numpy as np
s=cv2.imread('../jinx-i2t/ref/pose_gun_5view.jpg').astype(np.float32)
h,w=s.shape[:2]
yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
mb=np.zeros((h,w),bool); mb[0:20,:]=True; mb[600:1200,600:640]=True; mb[600:1200,1250:1300]=True
A=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
pred=np.zeros_like(s)
for c in range(3):
    co,*_=np.linalg.lstsq(A[mb],s[...,c][mb],rcond=None); pred[...,c]=A@co
d=np.abs(s-pred).max(-1)
fg=(d>14)[0:1390,:]          # crop off the footer bar
fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,ce=cv2.connectedComponentsWithStats(fg,8)
big=[i for i in range(1,n) if st[i,4]>40000]
big.sort(key=lambda i: st[i,0])
print('figure  x0   x1    yTop  yBot  heightPx')
hs=[]
for i in big:
    x0,y0,ww,hh,a=st[i]
    print('  %d    %4d %4d   %4d  %4d   %4d   (area %d)'%(len(hs)+1,x0,x0+ww,y0,y0+hh-1,hh,a))
    hs.append(hh)
hs=np.array(hs,float)
print('\nheights: %s'%hs)
print('mean=%.1f  std=%.1f  spread=%.1f%%'%(hs.mean(),hs.std(),100*(hs.max()-hs.min())/hs.mean()))
np.save('analysis/work/sheet_fg.npy',(lab>0)&(lab!=0))
