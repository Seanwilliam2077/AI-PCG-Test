import cv2, numpy as np
im=cv2.imread('ref/gun_pose2.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
h,w=V.shape
# background model
yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
mb=np.zeros((h,w),bool); mb[0:25,60:160]=True; mb[:,145:]=True; mb[100:129,120:160]=True
A=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
pred=np.zeros_like(im,np.float32)
for c in range(3):
    co,*_=np.linalg.lstsq(A[mb],im[...,c][mb].astype(np.float32),rcond=None); pred[...,c]=A@co
fg=(np.abs(im.astype(np.float32)-pred).max(-1)>10)
print('V map pose2 muzzle x=72..124 y=64..116')
print('     '+''.join('%d'%(x//10%10) for x in range(72,125)))
print('     '+''.join('%d'%(x%10) for x in range(72,125)))
for y in range(64,117):
    print('%3d  %s'%(y,''.join(('%X'%min(15,V[y,x]//10)) if fg[y,x] else '.' for x in range(72,125))))
np.save('analysis/work/p2_fg.npy',fg)
