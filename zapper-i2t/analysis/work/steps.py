import cv2, numpy as np
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
h,w=fg.shape
# robust bottom edge: lowest fg row per column, but require 3 consecutive fg above it
bot=np.full(w,np.nan); top=np.full(w,np.nan)
for x in range(w):
    idx=np.flatnonzero(fg[:,x])
    if len(idx)<4: continue
    for y in idx[::-1]:
        if y>=3 and fg[y-1,x] and fg[y-2,x]: bot[x]=y; break
    for y in idx:
        if y+2<h and fg[y+1,x] and fg[y+2,x]: top[x]=y; break
ref=[x for x in range(107,145) if x not in range(123,130)]
A=np.stack([np.ones(len(ref)),np.array(ref,float)],1)
co,*_=np.linalg.lstsq(A,bot[ref],rcond=None)
print('steel-tube bottom-edge fit: y = %.4f*x + %.3f   (slope %.4f px/px = %.2f deg)'%(co[1],co[0],co[1],np.degrees(np.arctan(co[1]))))
resid=bot[ref]-(co[0]+co[1]*np.array(ref,float)); print('  fit residual rms=%.2f px'%np.sqrt((resid**2).mean()))
print('\n  x   botEdge  detrended(dy vs tube line)  topEdge  totalH')
for x in range(22,186):
    if np.isnan(bot[x]): continue
    d=bot[x]-(co[0]+co[1]*x)
    tt='%3d'%top[x] if not np.isnan(top[x]) else '  -'
    th='%5.1f'%(bot[x]-top[x]) if not np.isnan(top[x]) else '   - '
    print('%3d   %5.1f   %+5.2f   %s  %s %s'%(x,bot[x],d,tt,th,'>'*int(max(0,round(d*2)))))
