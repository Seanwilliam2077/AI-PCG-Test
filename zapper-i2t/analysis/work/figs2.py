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
fg=(d>14); fg[1392:,:]=False
np.save('analysis/work/sheet_fgmask.npy',fg)
wins={'fig1':(300,560),'fig2':(880,1150),'fig3':(1300,1560),'fig4':(1700,1960),'fig5':(2020,2280),'fig6':(2560,2830)}
print('fig    xwin        yTop  yBot   heightPx   mm/px@1715mm')
res={}
for k,(a,b) in wins.items():
    sub=fg[:,a:b]
    rows=np.flatnonzero(sub.sum(1)>2)
    t,bt=rows[0],rows[-1]
    hh=bt-t+1
    res[k]=hh
    print('%-5s %4d-%4d   %4d  %4d   %5d      %.4f'%(k,a,b,t,bt,hh,1715.0/hh))
v=np.array(list(res.values()),float)
print('\nmean=%.1f std=%.1f  max-min=%.0f px (%.2f%%)'%(v.mean(),v.std(),v.max()-v.min(),100*(v.max()-v.min())/v.mean()))
