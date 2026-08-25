import cv2, numpy as np
im = cv2.imread('ref/gun_pose3.png').astype(np.float32)
h,w = im.shape[:2]
yy,xx = np.mgrid[0:h,0:w].astype(np.float32)
# fit plane+quad to background using top strip + right strip (known bg)
mask_bg = np.zeros((h,w),bool)
mask_bg[0:10,:] = True
mask_bg[:,w-25:] = True
mask_bg[h-6:,140:] = True
A = np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
res = np.zeros((h,w),np.float32)
pred = np.zeros_like(im)
for c in range(3):
    coef,*_ = np.linalg.lstsq(A[mask_bg], im[...,c][mask_bg], rcond=None)
    pred[...,c] = A@coef
d = np.abs(im-pred).max(-1)
print('resid on bg samples: p99=%.1f max=%.1f'%(np.percentile(d[mask_bg],99), d[mask_bg].max()))
fg = (d>10).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
n,lab,stats,cent = cv2.connectedComponentsWithStats(fg,8)
order=np.argsort(-stats[1:,4])+1
for i in order[:5]:
    print('comp',i,'area',stats[i,4],'bbox x',stats[i,0],stats[i,0]+stats[i,2],'y',stats[i,1],stats[i,1]+stats[i,3])
np.save('analysis/work/p3_fg.npy', fg)
cv2.imwrite('analysis/work/p3_fg.png', fg*255)
