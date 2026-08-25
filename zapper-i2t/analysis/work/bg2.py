import cv2, numpy as np
s=cv2.imread('../jinx-i2t/ref/pose_gun_5view.jpg').astype(np.float32)
h,w=s.shape[:2]
s=s[:1395]        # drop footer bar
h=1395
yy,xx=np.mgrid[0:h,0:w].astype(np.float32)/1000.0
# broad background sample: vertical gutters between figures + top strip
mb=np.zeros((h,w),bool)
for a,b in [(600,660),(1230,1300),(1620,1680),(1980,2020),(2300,2420),(2880,3000),(0,40)]:
    mb[:,a:b]=True
mb[0:60,:]=True
terms=[]
for i in range(5):
    for j in range(5-i): terms.append(xx**i*yy**j)
A=np.stack(terms,-1)
pred=np.zeros_like(s)
for c in range(3):
    co,*_=np.linalg.lstsq(A[mb],s[...,c][mb],rcond=None); pred[...,c]=A@co
d=np.abs(s-pred).max(-1)
print('bg resid p99=%.2f  p999=%.2f'%(np.percentile(d[mb],99),np.percentile(d[mb],99.9)))
fg=d>12
fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)
np.save('analysis/work/sheet_fg3.npy',fg)
wins={'fig1':(300,560),'fig2':(880,1150),'fig3':(1300,1560),'fig4':(1700,1960),'fig5':(2020,2280),'fig6':(2560,2830)}
print('\nfig    yTop  yBot   heightPx   mm/px(@1715)')
for k,(a,b) in wins.items():
    col=fg[:,a:b].sum(1); rows=np.flatnonzero(col>3)
    t,bt=rows[0],rows[-1]
    print('%-5s  %4d  %4d   %5d      %.4f'%(k,t,bt,bt-t+1,1715.0/(bt-t+1)))
